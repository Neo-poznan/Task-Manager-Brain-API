import re
from typing import NoReturn, Union
from datetime import datetime

from django.core.exceptions import ValidationError


def history_query_params_validator(from_date: str, to_date: str) -> Union[None, NoReturn]:
    template = r'^\d\d\d\d-\d\d-\d\d$'
    if not re.fullmatch(template, from_date) or not re.fullmatch(template, to_date):
        raise ValidationError('Неправильный формат даты')


def history_dates_interval_validator(from_date: str, to_date:str) -> Union[None, NoReturn]:
    try:
        from_date_as_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date_as_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    except Exception as exc:
        raise ValidationError('Неправильный формат даты')
    
    if not from_date_as_date < to_date_as_date:
        raise ValidationError('Вторая дата должна быть больше первой')

