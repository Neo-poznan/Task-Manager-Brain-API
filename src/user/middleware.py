'''
Для того чтобы использовать JWT-токены вместо обычных session id
нужно переписать session и authentication middleware.
'''
import random
import time
from typing import NoReturn, Union

from jwt.exceptions import ExpiredSignatureError, DecodeError
from django.core.exceptions import ImproperlyConfigured
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.http import HttpResponseRedirect

from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.utils.http import http_date
import redis

from .models import User, RefreshToken
from .jwt_auth import decode_jwt
from django.contrib.auth.models import AnonymousUser

# Имена, которые использует django для работы с сессиями, 
# нужны чтобы наш движок сессий мог работать нативно
HASH_SESSION_KEY = '_auth_user_hash'
SESSION_KEY = "_auth_user_id"
INTERNAL_RESET_SESSION_TOKEN = "_password_reset_token"


class AuthenticationMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if not hasattr(request, "session"):
            raise ImproperlyConfigured(
                "The Django authentication middleware requires session "
                "middleware to be installed. Edit your MIDDLEWARE setting to "
                "insert "
                "'django.contrib.sessions.middleware.SessionMiddleware' before "
                "'django.contrib.auth.middleware.AuthenticationMiddleware'."
            )
        try:
            user_id = self._get_user_id(request)
        except DecodeError:
            request.user = AnonymousUser()
            request.session.access_token_status = False
            if not self._need_skip_request(request.path):
                return HttpResponseRedirect(f'/api/user/refresh/?next={request.get_full_path()}')
        except ExpiredSignatureError:
            request.session.access_token_status = False
            request.user = AnonymousUser()
            if not self._need_skip_request(request.path):
                return HttpResponseRedirect(f'/api/user/refresh/?next={request.get_full_path()}')
        else:
            request.session.access_token_status = True
            if not request.path in settings.SKIP_AUTH_MIDDLEWARE_URLS:
                request.user = SimpleLazyObject(lambda: User.objects.get(id=user_id))
                request.session[SESSION_KEY] = request.user.id

    def _get_user_id(self, request) -> Union[int, NoReturn]:
        user_id = decode_jwt(
                request.session.access_token, request.get_host()
            )['sub']
        return user_id

    def _need_skip_request(self, path: str) -> bool:
        return any(path.startswith(str(skip_path)) for skip_path in settings.SKIP_REFRESH_URLS)


class SessionMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.SessionStore = JWTSessionEngine

    def process_request(self, request):
        access_token = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        device_id = request.COOKIES.get(settings.DEVICE_ID_COOKIE_NAME)
        if device_id is None:
            device_id = request.META.get('HTTP_X_DEVICEID')
        request.session = self.SessionStore(
            request=request,
            access_token=access_token, 
            refresh_token=refresh_token,
            device_id=device_id,
        )

    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response
        # First check if we need to delete this cookie.
        # The session should be deleted only if the session is entirely empty.
        if settings.ACCESS_TOKEN_COOKIE_NAME in request.COOKIES and empty:
            print('access token deleted')
            response.delete_cookie(
                settings.ACCESS_TOKEN_COOKIE_NAME,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
        if (not request.session.refresh_token) and settings.REFRESH_TOKEN_COOKIE_NAME in request.COOKIES:
            print('refresh token deleted')
            response.delete_cookie(
                settings.REFRESH_TOKEN_COOKIE_NAME,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
            patch_vary_headers(response, ("Cookie",))
        else:
            if accessed:
                patch_vary_headers(response, ("Cookie",))
            if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
                if response.status_code < 500:
                    expires_time = time.time() + settings.SESSION_COOKIES_EXPIRED_TIME.total_seconds()
                    expires = http_date(expires_time)

                    response.set_cookie(
                        settings.ACCESS_TOKEN_COOKIE_NAME,
                        request.session.access_token,
                        domain=settings.SESSION_COOKIE_DOMAIN,
                        path=settings.SESSION_COOKIE_PATH,
                        secure=settings.SESSION_COOKIE_SECURE or None,
                        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                        samesite=settings.SESSION_COOKIE_SAMESITE,
                        expires=expires,
                    )
                    if request.session.refresh_token:
                        response.set_cookie(
                            settings.REFRESH_TOKEN_COOKIE_NAME,
                            request.session.refresh_token,
                            domain=settings.SESSION_COOKIE_DOMAIN,
                            path=settings.SESSION_COOKIE_PATH,
                            secure=settings.SESSION_COOKIE_SECURE or None,
                            httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                            samesite=settings.SESSION_COOKIE_SAMESITE,
                            expires=expires,
                        ) 
                    if request.session.device_id:
                        response.set_cookie(
                            settings.DEVICE_ID_COOKIE_NAME,
                            request.session.device_id,
                            domain=settings.SESSION_COOKIE_DOMAIN,
                            path=settings.SESSION_COOKIE_PATH,
                            secure=settings.SESSION_COOKIE_SECURE or None,
                            httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                            samesite=settings.SESSION_COOKIE_SAMESITE,
                            expires=expires,
                        )
        return response


class JWTSessionEngine:
    def __init__(
            self, 
            request, 
            access_token: str = None, 
            refresh_token: str = None,
            device_id: str = None,
        ): 
        self.__access_token = access_token
        self.__access_token_status = None
        self.__refresh_token = refresh_token
        self.__device_id = device_id
        self.accessed = False
        self.modified = False
        self._auth_user_id = None
        self._redis_client = redis.Redis()
        self.__cookies = request.COOKIES.copy()

        if not access_token:
            self._set_random_session_cookie()

        self._cached = {
                'session': self.access_token, 
                'accessed': False,
                'modified': False
            }           

        if request.path.startswith(settings.PASSWORD_RESET_URL):
            self._add_password_reset_token_to_instance()

    def _set_random_session_cookie(self):
        random_session_cookie = self._generate_random_session_cookie()
        self.access_token = random_session_cookie
        self.modified = True

    def _generate_random_session_cookie(self):
        length = 32
        ascii_letters = '1234567890-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(random.choice(ascii_letters) for i in range(length))
    
    def _add_password_reset_token_to_instance(self):
        reset_token = self._load_cache()
        if reset_token:
            self._cached[INTERNAL_RESET_SESSION_TOKEN] = reset_token.decode('utf-8')        

    def _load_cache(self):
        return self._redis_client.get(self._cached['session'])

    def __iter__(self):
        if self.access_token:
            yield SESSION_KEY
        else:
            yield None

    def __getitem__(self, key):
        if key == INTERNAL_RESET_SESSION_TOKEN:
            return self._cached.get(INTERNAL_RESET_SESSION_TOKEN)
        elif key == HASH_SESSION_KEY:
            return self.access_token
        elif key.startswith('_'):
            return getattr(self, key)
        elif self.__cookies.get(key):
            return self.__cookies[key]

    def __setitem__(self, key, value):
        if key == INTERNAL_RESET_SESSION_TOKEN:
            self._set_password_reset_token(value)
        elif key == HASH_SESSION_KEY: 
            self.access_token = value['access_token']
            self.refresh_token = value['refresh_token']
        elif key.startswith('_'):
            setattr(self, key, value)
        else:
            self.cookies[key] = value

    def _set_password_reset_token(self, password_reset_token: str):
        self._cached[INTERNAL_RESET_SESSION_TOKEN] = password_reset_token
        self._cached['modified'] = True
        self._save_cache()  

    def _save_cache(self):
        if self._cached['modified']:
            self._redis_client.set(
                self._cached['session'],
                self._cached[INTERNAL_RESET_SESSION_TOKEN]
            )
        print('saved in redis')

    def __delitem__(self, key):
        del self._cached[key]
        self._redis_client.delete(self.access_token)

    def __setattr__(self, name, value):
        return super().__setattr__(name, value)

    @property
    def access_token(self):
        self.accessed = True
        return self.__access_token

    @access_token.setter
    def access_token(self, value: str):
        self.accessed = True
        self.modified = True
        self.__cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = value
        self.__access_token = value

    @property
    def refresh_token(self):
        self.accessed = True
        return self.__refresh_token
    
    @refresh_token.setter
    def refresh_token(self, value: str):
        self.accessed = True
        self.modified = True
        self.__cookies[settings.REFRESH_TOKEN_COOKIE_NAME] = value
        self.__refresh_token = value

    @property
    def device_id(self):
        self.accessed = True
        return self.__device_id

    @device_id.setter
    def device_id(self, value: str):
        self.accessed = True
        self.modified = True
        self.__cookies[settings.DEVICE_ID_COOKIE_NAME] = value
        self.__device_id = value

    @property
    def access_token_status(self):
        return self.__access_token_status
    
    @access_token_status.setter
    def access_token_status(self, value: bool):
        self.__access_token_status = value

    def cycle_key(self):
        pass
    
    def flush(self):
        self.__access_token = None
        self.__refresh_token = None
        self.accessed = True
        self.modified = True
    
    def get(self, key, default = None):
        try: 
            return self[key]
        except AttributeError:
            pass
        try:
            return self._cached[key]
        except KeyError:
            pass
        return default

    def is_empty(self):
        return not bool(self.__access_token)

