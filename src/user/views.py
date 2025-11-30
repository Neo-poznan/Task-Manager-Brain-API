from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views.generic import CreateView, View
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.conf import settings
from django.db import connection

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, UserPasswordChangeForm, UserPasswordResetForm, UserPasswordResetConfirmForm
from task.mixins import ApiLoginRequiredMixin
from task.http import FormJsonResponse

from jwt import ExpiredSignatureError, DecodeError
from task.views import ModelApiView
from .services.use_cases import UserUseCase
from .infrastructure.database_repository import UserDatabaseRepository
from .models import RefreshToken, User


def get_user_info_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({}, status=401)

    return JsonResponse(
        {
            'username': request.user.username,
            'avatar': request.user.avatar.url,
        }
    )


def check_authentication_view(request):
    if not request.session.access_token_status:
        return HttpResponseForbidden()
    return JsonResponse({})


class RefreshSessionView(View):
    def get(self, request):
        return self._refresh()
    
    def post(self, request):
        return self._refresh()

    def put(self, request):
        return self._refresh()
    def delete(self, request):
        return self._refresh()

    def _refresh(self):
        current_refresh_token = self.request.session.refresh_token
        device_id = self.request.session.device_id 
        ip_address = self.request.META['HTTP_X_FORWARDED_FOR']
        user_agent = self.request.META['HTTP_USER_AGENT']
        host = self.request.get_host()

        if not device_id:
            raise JsonResponse({'message': 'device id not found'})

        use_case = UserUseCase(UserDatabaseRepository(connection=connection, refresh_token_model=RefreshToken))
            
        try:
            new_access_token, new_refresh_token = use_case.refresh_session(
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
            return JsonResponse({'message': 'no token in database'}, status=403)
        else:
            print('session refreshed successfully')
            self.request.session.access_token = new_access_token
            self.request.session.refresh_token = new_refresh_token
            return HttpResponseRedirect(self.request.GET['next'])


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
        use_case = UserUseCase(UserDatabaseRepository(connection=connection, refresh_token_model=RefreshToken))
        use_case.set_new_session(
            user=form.get_user(),
            refresh_token=self.request.session.refresh_token,
            device_id=self.request.session.device_id,
            ip_address=self.request.META['HTTP_X_FORWARDED_FOR'],
            user_agent=self.request.META['HTTP_USER_AGENT'],
            host=self.request.get_host(),
        )
        return JsonResponse({'redirectUrl': self.get_success_url()})

    def get_next_page(self):
        return self.request.GET.get('next')


class UserProfileView(
            ApiLoginRequiredMixin, 
            ModelApiView
        ):
    response_class = FormJsonResponse
    form_class = UserProfileForm

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse({'redirectUrl': self.get_success_url()})

    def get_object(self, queryset = ...):
        return self.request.user

    def get_success_url(self):
        return '/user/profile/'


class UserPasswordChangeView(
            ApiLoginRequiredMixin, 
            PasswordChangeView
        ):
    form_class = UserPasswordChangeForm
    response_class = FormJsonResponse

    def get_success_url(self):
        return reverse_lazy('user:password_change_done')


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('user:login')


class UserPasswordResetView(PasswordResetView):
    form_class = UserPasswordResetForm
    response_class = FormJsonResponse
    email_template_name = 'user/password_reset_message.html'

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse({})

    def get_success_url(self):
        return reverse_lazy('user:password_reset_done')


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'user/password_reset_done.html'


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = UserPasswordResetConfirmForm
    template_name = 'user/password_reset_confirm.html'

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


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'user/password_reset_complete.html'


def check_user_status(request):
    return JsonResponse({'status': request.user.is_authenticated})
   
