from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model

from .validators import email_validator, password_reset_form_validator


class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'name': 'username',
        'id': 'username-id-for-label',
        'placeholder': 'Никнейм',
    }))

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'name': 'email',
        'id': 'email-id-for-label',
        'placeholder': 'Email',
    }))

    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'name': 'password',
        'id': 'password1-id-for-label',
        'placeholder': 'Пароль',
    }))

    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'name': 'password',
        'id': 'password2-id-for-label',
        'placeholder': 'Повтор пароля',
    }))


    def clean_email(self):
        return email_validator(self.cleaned_data.get('email'))


    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2']


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'name': 'username',
        'id': 'username-id-for-label',
        'placeholder': 'Никнейм или email',
    }))

    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'name': 'password',
        'id': 'password-id-for-label',
        'placeholder': 'Пароль',
    }))


    class Meta:
        model = get_user_model()
        fields = ['username', 'password']


class UserProfileForm(forms.ModelForm):
    avatar = forms.ImageField(widget=forms.FileInput(attrs={
        'name': 'avatar',
        'id': 'file-input',
    }))

    username = forms.CharField(widget=forms.TextInput(attrs={
        'name': 'username',
        'id': 'username-id-for-label',
        'placeholder': 'Никнейм',
    }))

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'name': 'email',
        'id': 'email-id-for-label',
        'placeholder': 'Email',
    }))


    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance.email == email:
            return email
        return email_validator(email)


    class Meta:
        model = get_user_model()
        fields = ['avatar', 'username', 'email']


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'name': 'password',
        'id': 'password-id-for-label',
        'placeholder': 'Старый пароль',
    }))

    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'name': 'password',
        'id': 'new-password1-id-for-label',
        'placeholder': 'Новый пароль',
    }))

    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'name': 'password',
        'id': 'new-password2-id-for-label',
        'placeholder': 'Повтор нового пароля',
    }))


    class Meta:
        model = get_user_model()
        fields = ['old_password', 'new_password1', 'new_password2']


class UserPasswordResetForm(PasswordResetForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'name': 'username',
        'id': 'username-id-for-label',
        'placeholder': 'Никнейм',
    }))

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'name': 'email',
        'id': 'email-id-for-label',
        'placeholder': 'Email',
    }))


    def clean(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        password_reset_form_validator(username, email)
        return super().clean()
    

class UserPasswordResetConfirmForm(SetPasswordForm):
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'name': 'password',
        'id': 'new-password1-id-for-label',
        'placeholder': 'Новый пароль',
    }))

    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'name': 'password',
        'id': 'new-password2-id-for-label',
        'placeholder': 'Повтор нового пароля',
    }))

