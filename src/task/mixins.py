from urllib.parse import urlparse, urlunparse

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.http import HttpResponseRedirect, QueryDict
from django.conf import settings
from django.contrib import messages
from user.domain.entities import UserEntity


def redirect_to_login(
            next, 
            login_url=None, 
            redirect_field_name=REDIRECT_FIELD_NAME, 
            message='', 
            request=None
        ):
    """
    Redirect the user to the login page, passing the given 'next' page.
    """
    resolved_url = resolve_url(login_url or settings.LOGIN_URL)

    login_url_parts = list(urlparse(resolved_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe="/")
    # if message:
        # messages.warning(request, message)
    return HttpResponseRedirect(urlunparse(login_url_parts))


class TitleMixin:

    def get_title(self):
        return self.title

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_title()
        return context


class UserEntityMixin:

    def get_user_entity(self) -> UserEntity:
        return self.request.user.to_domain()
    

class AccessMixinWithRedirectMessage(AccessMixin):

    def handle_no_permission(self, message):
        if self.raise_exception or self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())

        path = self.request.build_absolute_uri()
        resolved_login_url = resolve_url(self.get_login_url())

        login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
        current_scheme, current_netloc = urlparse(path)[:2]
        if (not login_scheme or login_scheme == current_scheme) and (
            not login_netloc or login_netloc == current_netloc
        ):
            path = self.request.get_full_path()
        return redirect_to_login(
            path,
            resolved_login_url,
            self.get_redirect_field_name(),
            message=message,
            request=self.request
        )


class LoginRequiredMixinWithRedirectMessage(AccessMixinWithRedirectMessage):
    """Verify that the current user is authenticated."""
    message = '''
        <div class="bug-icon-container">
            <i class="ri-bug-line" id="bug-icon"></i>
        </div>
        <h1>Чтобы посетить эту страницу сайта нужно сначала войти в аккаунт!<h1>
        '''

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission(message=self.message)
        return super().dispatch(request, *args, **kwargs)

