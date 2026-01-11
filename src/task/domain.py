import re
from uuid import UUID
from typing import Optional, Protocol, Union, NoReturn
from datetime import datetime, timedelta


class CategoryEntityProtocol(Protocol):
    id: Optional[int]
    name: str
    description: Optional[str]
    color: str
    user_id: Optional[UUID]
    is_custom: bool


class TaskEntityProtocol(Protocol):
    id: Optional[int]
    name: str
    description: Optional[str]
    order: int
    category_id: Optional[int]
    user_id: UUID
    deadline: Optional[datetime]
    planned_time: timedelta


class CategoryEntity:

    DEFAULT_COLOR_TRANSPARENCY = 0.4

    def __init__(
        self,
        name: str,
        color: str,
        is_custom: bool = True,
        user_id: Optional[UUID] = None,
        id: Optional[int] = None,
        description: Optional[str] = None,
    ):
        self._id = id
        self._name = self._validate_name(name)
        self._description = description
        self._color = self._validate_color(color)
        self._user_id = user_id
        self._is_custom = is_custom

    @property
    def id(self) -> Optional[int]:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def color(self) -> str:
        return self._color
    
    @property
    def user_id(self) -> Optional[UUID]:
        return self._user_id
    
    @property
    def is_custom(self) -> bool:
        return self._is_custom
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = self._validate_name(value)

    @color.setter
    def color(self, value: str) -> None:
        self._color = self._validate_color(value)
    
    @description.setter
    def description(self, value: Optional[str]) -> None:
        self._description = value

    def _validate_name(self, name: str) -> Union[str, NoReturn]:
        if not name:
            raise ValueError('Название категории не может быть пустым')
        if len(name) > 100:
            raise ValueError('Название категории не может быть длиннее 100 символов')
        return name
    
    def _validate_color(self, color: str) -> Union[str, NoReturn]:
        if not (
            self._color_is_hex(color) or
            self._color_is_rgb(color) or
            self._color_is_rgba(color)
        ):
            raise ValueError('Цвет категории должен быть в формате HEX, RGB или RGBA')
        return self._get_color_in_rgba(color)
    
    def _get_color_in_rgba(self, color: str) -> str:
        if self._color_is_rgba(color):
            return color
        elif self._color_is_hex(color):
            return self._hex_to_rgba(color)
        elif self._color_is_rgb(color):
            return self._rgb_to_rgba(color)

    def _color_is_hex(self, color: str) -> bool:
        template = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return bool(re.fullmatch(template, color))

    def _color_is_rgb(self, color: str) -> bool:
        template = r'^rgb\((\s*\d{1,3}\s*,){2}\s*\d{1,3}\s*\)$'
        return bool(re.fullmatch(template, color))

    def _color_is_rgba(self, color: str) -> bool:
        template = r'^rgba\((\s*\d{1,3}\s*,){3}\s*(0(\.\d+)?|1(\.0+)?)\s*\)$'
        return bool(re.fullmatch(template, color))
    
    def _hex_to_rgba(self, color: str) -> str:
        value = color.lstrip('#')
        lv = len(value)
        rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        rgba = f'rgba{rgb}'[0:-1]
        rgba += f', {self.DEFAULT_COLOR_TRANSPARENCY})'
        return rgba
    
    def _rgb_to_rgba(self, color: str) -> str:
        rgb_elements = color.replace('rgb(', '').replace(')', '')
        rgb_tuple = tuple(int(element) for element in rgb_elements.split(', '))
        rgba = f'rgba{rgb_tuple}'[0:-1]
        rgba += f', {self.DEFAULT_COLOR_TRANSPARENCY})'
        return rgba

    def to_dict(self, for_form: bool = False) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self._rgba_to_hex(self.color) if for_form else self.color,
            'user_id': self.user_id,
            'is_custom': self.is_custom,
        }

    def _rgba_to_hex(self, rgba: str) -> str:
        rgb_elements = rgba.replace('rgba(', '')
        rgb_elements = rgb_elements.replace(', 0.4)', '')

        rgb_tuple = tuple(int(element) for element in rgb_elements.split(', '))
        return '#' + ''.join(f'{i:02X}' for i in rgb_tuple)
    
    def __repr__(self):
        return f'CategoryEntity(id={self.id}, name="{self.name}", description="{self.description}", color="{self.color}", user_id={self.user_id}, is_custom={self.is_custom})'

    @classmethod
    def from_dict(cls, data: dict) -> 'CategoryEntity':
        return CategoryEntity(
            id=data.get('id'),
            name=data['name'],
            description=data.get('description'),
            color=data['color'],
            user_id=data['user_id'],
            is_custom=data.get('is_custom', True),
        )


class TaskEntity:
    def __init__(
            self,
            name: str,
            planned_time: timedelta,
            user_id: UUID,
            order: int,
            id: Optional[int] = None,
            category_id: Optional[int] = None,
            description: Optional[str] = None,
            deadline: Optional[datetime] = None,
        ):

        self._id = id
        self._name = self._validate_name(name)
        self._description = description
        self._order = order
        self._category_id = category_id
        self._user_id = user_id
        self._deadline = deadline or None
        self._planned_time = planned_time

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def order(self) -> int:
        return self._order
    
    @property
    def category_id(self) -> Optional[int]:
        return self._category_id
    
    @property
    def user_id(self) -> UUID:
        return self._user_id
    
    @property
    def deadline(self) -> Optional[datetime]:
        return self._deadline
    
    @property
    def planned_time(self) -> timedelta:
        return self._planned_time
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = self._validate_name(value)

    @description.setter
    def description(self, value: Optional[str]) -> None:
        self._description = value

    @order.setter
    def order(self, value: int) -> None:
        self._order = value

    @category_id.setter
    def category_id(self, value: Optional[int]) -> None:
        self._category_id = value

    @deadline.setter
    def deadline(self, value: Optional[datetime]) -> None:
        self._deadline = value
    
    @planned_time.setter
    def planned_time(self, value: timedelta) -> None:
        self._planned_time = value

    def _validate_name(self, name: str) -> Union[str, NoReturn]:
        if not name:
            raise ValueError('Название задачи не может быть пустым')
        if len(name) > 290:
            raise ValueError('Название задачи не может быть длиннее 290 символов')
        return name
    
    def _validate_planned_time(self, planned_time: timedelta) -> Union[timedelta, NoReturn]:
        if planned_time.total_seconds() < 1800:
            raise ValueError('Запланированное время не может быть меньше 30 минут')
        return planned_time
    
    def to_dict(self) -> dict:
        return {
            'id': self._id,
            'name': self._name,
            'description': self._description,
            'order': self._order,
            'category_id': self._category_id,
            'user_id': self._user_id,
            'deadline': self._deadline,
            'planned_time': self._serialize_duration_with_days(self._planned_time),
        }
    
    def _serialize_duration_with_days(self, value: timedelta) -> str:
        default_parsed_duration = str(value)
        if re.findall(r'^\d+ day', default_parsed_duration):
            days_count = re.findall(r'^(\d+) day', default_parsed_duration)[0]
            time_part = re.findall(r'\d+:\d+:\d+$', default_parsed_duration)[0]
            hours, minutes, seconds = map(int, time_part.split(':'))
            time_part_with_days = f"{int(days_count) * 24 + hours:02}:{minutes:02}:{seconds:02}"
            return time_part_with_days
        else:
            return default_parsed_duration
        
    def __repr__(self):
        return f'TaskEntity(id={self.id}, name="{self.name}", description="{self.description}", order={self.order}, category_id={self.category_id}, user_id={self.user_id}, deadline={self.deadline}, planned_time="{self.planned_time}")'

    @classmethod
    def from_dict(cls, data: dict) -> 'TaskEntity':
        return TaskEntity(
            id=data.get('id'),
            name=data['name'],
            description=data.get('description'),
            order=data['order'],
            category_id=data.get('category_id') or data.get('category'),
            user_id=data['user_id'],
            deadline=data.get('deadline'),
            planned_time=cls._parse_duration(data['planned_time']),
        )

    @classmethod 
    def _parse_duration(cls, value: str):
        default_duration_re = re.compile(
            r"^"
            r"(?:(?P<days>-?\d+) (days?, )?)?"
            r"(?P<sign>-?)"
            r"((?:(?P<hours>\d+):)(?=\d+:\d+))?"
            r"(?:(?P<minutes>\d+):)?"
            r"(?P<seconds>\d+)"
            r"(?:[.,](?P<microseconds>\d{1,6})\d{0,6})?"
            r"$"
        )

        match = default_duration_re.match(value)

        if match:
            kw = match.groupdict()
            sign = -1 if kw.pop("sign", "+") == "-" else 1
            if kw.get("microseconds"):
                kw["microseconds"] = kw["microseconds"].ljust(6, "0")
            kw = {k: float(v.replace(",", ".")) for k, v in kw.items() if v is not None}
            days = timedelta(kw.pop("days", 0.0) or 0.0)
            return days + sign * timedelta(**kw)

