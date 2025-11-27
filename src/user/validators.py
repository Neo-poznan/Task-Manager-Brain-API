from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist


def email_validator(email: str):
    already_registered_emails = get_user_model().objects.all().values_list('email')
    for already_registered_email in already_registered_emails:
        if email == already_registered_email[0]:
            raise ValidationError('Такой email уже существует')
    return email


def password_reset_form_validator(username: str, email: str):
    try:
        user = get_user_model().objects.get(username=username)
    except ObjectDoesNotExist:
        raise ValidationError('Пользователя с таким именем не существует')
    if user.email != email:
        raise ValidationError('Не удалось найти совпадения между указанным именем и адресом электронной почты!')

