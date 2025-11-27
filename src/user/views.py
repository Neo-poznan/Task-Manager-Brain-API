from typing import Union, NoReturn, Iterable

from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views.generic import CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.conf import settings

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, UserPasswordChangeForm, UserPasswordResetForm, UserPasswordResetConfirmForm
from task.mixins import TitleMixin, LoginRequiredMixinWithRedirectMessage
from task.http import FormJsonResponse

from .models import RefreshToken, User
from .jwt_auth import decode_jwt
from jwt import ExpiredSignatureError, DecodeError


def reset_refresh_token_for_device(
        refresh_token: str,
        device_id: str,
        ip_address: str,
        user_agent: str,
        host: str,
        user: User,
    ) -> None:
    tokens = RefreshToken.objects.filter(device_id=device_id, user=user)
    tokens.delete()
    jti = decode_jwt(refresh_token, host)['jti']
    RefreshToken.objects.create(
        jti=jti, 
        user=user,
        device_id=device_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_user_info_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({}, status=401)

    return JsonResponse(
        {
            'username': request.user.username,
            'avatar': request.user.avatar.url,
        }
    )


def check_authentication(request):
    if not request.session.access_token_status:
        return HttpResponseForbidden()
    return JsonResponse({})


class RefreshSessionView(View):
    def get(self, request):
        return self.refresh()
    
    def post(self, request):
        return self.refresh()

    def put(self, request):
        return self.refresh()
    def delete(self, request):
        return self.refresh()

    def refresh(self):
        current_refresh_token = self.request.session.refresh_token
        device_id = self.request.session.device_id 
        ip_address = self.request.META['HTTP_X_FORWARDED_FOR']
        user_agent = self.request.META['HTTP_USER_AGENT']
        host = self.request.get_host()

        if not device_id:
            raise JsonResponse({'message': 'device id not found'})
            

        try:
            new_access_token, new_refresh_token = self._refresh_session(
                current_refresh_token=current_refresh_token,
                device_id=device_id,
                ip_address=ip_address,
                user_agent=user_agent,
                host=host,
            )
        except ExpiredSignatureError:
            self.request.session.flush()
            print('refresh token expired')
            return JsonResponse({'message': 'session expired'}, status=401)
        except DecodeError:
            print('refresh token not passed')
            return JsonResponse({'message': 'refresh token not found'}, status=401)
        except PermissionError:
            print('no token in database')
            return JsonResponse({'message': 'no token in database'})
        else:
            print('session refreshed successfully')
            self.request.session.access_token = new_access_token
            self.request.session.refresh_token = new_refresh_token
            return HttpResponseRedirect(self.request.GET['next'])

    def _refresh_session(
            self, 
            current_refresh_token: str,
            device_id: str,
            ip_address: str,
            user_agent: str,
            host: str,
        ) -> Union[Iterable[str], NoReturn]:
        payload = decode_jwt(current_refresh_token, host)
        sub = payload['sub']
        jti = payload['jti']
        user = User.objects.get(id=sub)
        self._check_refresh_token(user, jti, device_id)
        new_jwt_tokens = user.get_session_auth_hash()
        new_refresh_token = new_jwt_tokens['refresh_token']
        new_access_token = new_jwt_tokens['access_token']
        reset_refresh_token_for_device(
            refresh_token=new_refresh_token,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            host=host,
            user=user,
        )
        return new_access_token, new_refresh_token

    def _check_refresh_token(
            self, 
            user: User, 
            jti: str, 
            device_id: str
        ) -> Union[None, NoReturn]:
        user_refresh_token_queryset = RefreshToken.objects.filter(
            user=user, 
            jti=jti, 
            device_id=device_id,
        )
        if not user_refresh_token_queryset.exists():
            raise PermissionError('jti not found in database')


class UserRegistrationView(CreateView):
    form_class = UserRegistrationForm
    response_class = FormJsonResponse
    template_name = 'template/user/registration.html'

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse({'redirectUrl': self.get_success_url()})

    def get_success_url(self):
        return '/user/login/'


class UserLoginView(LoginView):
    form_class = UserLoginForm
    response_class = FormJsonResponse

    def get_success_url(self):
        next_page = self.get_next_page()
        if not next_page:
            return settings.LOGIN_REDIRECT_URL
        return resolve_url(self.get_next_page())

    def form_valid(self, form):
        super().form_valid(form)
        reset_refresh_token_for_device(
            refresh_token=self.request.session.refresh_token,
            device_id=self.request.session.device_id,
            ip_address=self.request.META['HTTP_X_FORWARDED_FOR'],
            user_agent=self.request.META['HTTP_USER_AGENT'],
            host=self.request.get_host(),
            user=form.get_user(),
        )
        return JsonResponse({'redirectUrl': self.get_success_url()})

    def get_next_page(self):
        return self.request.GET.get('next')


class UserProfileView(
            LoginRequiredMixinWithRedirectMessage, 
            UpdateView
        ):
    response_class = FormJsonResponse
    form_class = UserProfileForm
    title = 'Профиль'

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse({'redirectUrl': self.get_success_url()})

    def get_object(self, queryset = ...):
        return self.request.user

    def get_success_url(self):
        return '/user/profile/'


class UserPasswordChangeView(
            TitleMixin, 
            LoginRequiredMixinWithRedirectMessage, 
            PasswordChangeView
        ):
    form_class = UserPasswordChangeForm
    response_class = FormJsonResponse
    title = 'Смена пароля'

    def get_success_url(self):
        return reverse_lazy('user:password_change_done')


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('user:login')


class UserPasswordResetView(TitleMixin, PasswordResetView):
    form_class = UserPasswordResetForm
    response_class = FormJsonResponse
    email_template_name = 'user/password_reset_message.html'
    title = 'Сброс пароля'

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse({})

    def get_success_url(self):
        return reverse_lazy('user:password_reset_done')


class UserPasswordResetDoneView(TitleMixin, PasswordResetDoneView):
    template_name = 'user/password_reset_done.html'
    title = 'Сброс пароля'


class UserPasswordResetConfirmView(TitleMixin, PasswordResetConfirmView):
    form_class = UserPasswordResetConfirmForm
    template_name = 'user/password_reset_confirm.html'
    title = 'Сброс пароля'

    def get_success_url(self):
        return reverse_lazy('user:password_reset_complete')

    def render_to_response(self, context, **response_kwargs):
        '''
        Фреймворк принимает решение об отображении формы сброса пароля 
        на основе значения context['validlink']. Но в таком случае просто 
        отобразится та-же страница, но без формы. Я хочу возвращать именно
        403 статус, поэтому перехватываю это значение здесь. 
        '''
        if not context['validlink']:
            return HttpResponseForbidden(
                    '<h1>403 Недостаточно прав!</h1><p>Для посещения этой станицы требуется передать специальный одноразовый токен смены пароля!</p>'
                )
        else:
            return super().render_to_response(context, **response_kwargs)


class UserPasswordResetCompleteView(TitleMixin, PasswordResetCompleteView):
    template_name = 'user/password_reset_complete.html'
    title = 'Успешно'


def check_user_status(request):
    return JsonResponse({'status': request.user.is_authenticated})
   
