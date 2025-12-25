from typing import NoReturn, Union
from datetime import timedelta

from django.core.exceptions import ValidationError

def duration_validator(time_value: timedelta) -> Union[None, NoReturn]:
    if time_value < timedelta(minutes=30):
        raise ValidationError('Время не может быть меньше 30 минут')

