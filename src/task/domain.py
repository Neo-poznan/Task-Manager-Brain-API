import re
from uuid import UUID
from typing import Optional, Protocol, Union, NoReturn, runtime_checkable
from datetime import timedelta, date


@runtime_checkable
class CategoryEntityProtocol(Protocol):
    @property
    def id(self) -> Optional[int]: ...

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> Optional[str]: ...

    @property
    def color(self) -> str: ...

    @property
    def user_id(self) -> Optional[UUID]: ...

    @property
    def is_custom(self) -> bool: ...


@runtime_checkable
class TaskEntityProtocol(Protocol):
    @property
    def id(self) -> Optional[int]: ...

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> Optional[str]: ...

    @property
    def order(self) -> int: ...

    @property
    def category_id(self) -> Optional[int]: ...

    @property
    def user_id(self) -> UUID: ...

    @property
    def deadline(self) -> Optional[date]: ...

    @property
    def planned_time(self) -> timedelta: ... 


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
    
    def _validate_color(self, color: Optional[str]) -> Union[str, NoReturn]:
        if color is None:
            raise ValueError('Цвет категории не может быть пустым')
        if not any(
            (
                self._color_is_hex(color),
                self._color_is_rgb(color),
                self._color_is_rgba(color)
            )
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
        is_match = bool(re.fullmatch(template, color))
        if not is_match:
            return is_match
        rgb_elements = color.replace('rgb(', '').replace(')', '').split(',')
        r, g, b = tuple(int(element.strip()) for element in rgb_elements)
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            return False
        return True

    def _color_is_rgba(self, color: str) -> bool:
        template = r'^rgba\((\s*\d{1,3}\s*,){3}\s*(0(\.\d+)?|1(\.0+)?)\s*\)$'
        is_match = bool(re.fullmatch(template, color))
        if not is_match:
            return is_match
        rgba_elements = color.replace('rgba(', '').replace(')', '').split(',')
        r, g, b = tuple(int(element.strip()) for element in rgba_elements[0:3])
        alpha = float(rgba_elements[3].strip())
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            return False
        if not (0.0 <= alpha <= 1.0):
            return False
        return True
        
    
    def _hex_to_rgba(self, color: str) -> str:
        value = color.lstrip('#')
        lv = len(value)
        rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        rgba = f'rgba{rgb}'[0:-1]
        rgba += f', {self.DEFAULT_COLOR_TRANSPARENCY})'
        return rgba
    
    def _rgb_to_rgba(self, color: str) -> str:
        rgb_elements = color.replace('rgb(', '').replace(')', '')
        r, g, b = tuple(int(element) for element in rgb_elements.split(','))
        rgba = f'rgba({r}, {g}, {b}'
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
        rgb_elements = rgb_elements.replace(f', {self.DEFAULT_COLOR_TRANSPARENCY})', '')

        rgb_tuple = tuple(int(element.strip()) for element in rgb_elements.split(',')[0:3])
        return '#' + ''.join(f'{i:02X}' for i in rgb_tuple)
    
    def __repr__(self):
        return f'CategoryEntity(id={self.id}, name="{self.name}", description="{self.description}", color="{self.color}", user_id={self.user_id}, is_custom={self.is_custom})'

    @classmethod
    def from_dict(cls, data: dict) -> 'CategoryEntity':
        return CategoryEntity(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            color=data.get('color'),
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
            deadline:Optional[date] = None,
        ):

        self._id = id
        self._name = self._validate_name(name)
        self._description = description
        self._order = order
        self._category_id = category_id
        self._user_id = user_id
        self._deadline = self._validate_deadline(deadline)
        self._planned_time = self._validate_planned_time(planned_time)

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
    def deadline(self) -> Optional[date]:
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
    def deadline(self, value: Optional[date]) -> None:
        self._deadline = self._parse_deadline(value)
    
    @planned_time.setter
    def planned_time(self, value: timedelta) -> None:
        self._planned_time = self._parse_planned_time(value)

    def _validate_name(self, name: str) -> Union[str, NoReturn]:
        if not name:
            raise ValueError('Название задачи не может быть пустым')
        if len(name) > 290:
            raise ValueError('Название задачи не может быть длиннее 290 символов')
        return name
    
    def _validate_planned_time(self, planned_time: timedelta) -> Union[timedelta, NoReturn]:
        if not isinstance(planned_time, timedelta):
            raise ValueError('Некорректный формат запланированного времени задачи')
        if planned_time.total_seconds() < 1800:
            raise ValueError('Запланированное время не может быть меньше 30 минут')
        return planned_time
    
    def _validate_deadline(self, deadline: Optional[date]) -> Union[date, None, NoReturn]:
        if deadline is None:
            return deadline
        if not isinstance(deadline, date):
            raise ValueError('Некорректный формат дедлайна задачи')
        return deadline
    
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
        category_id = data.get('category_id') or data.get('category')
        if not category_id:
            raise ValueError('Поле category_id не может быть пустым при создании задачи')
        return TaskEntity(
            id=data.get('id'),
            name=data['name'],
            description=data.get('description'),
            order=data['order'],
            category_id=data.get('category_id') or data.get('category'),
            user_id=data['user_id'],
            deadline=cls._parse_deadline(data.get('deadline')),
            planned_time=cls._parse_planned_time(data.get('planned_time')),
        )
    
    @classmethod
    def _parse_planned_time(cls, value: Union[timedelta, str, None]) -> timedelta:
        if isinstance(value, timedelta):
            return value
        if isinstance(value, str):
            return cls._parse_duration(value)
        raise ValueError('Некорректный формат запланированного времени задачи')

    @classmethod 
    def _parse_duration(cls, value: Union[timedelta, str, None]) -> timedelta:

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
        else:
            raise ValueError('Некорректный формат запланированного времени задачи')
        
    @classmethod
    def _parse_deadline(cls, deadline: Union[date, None, str]) -> Union[date, None, NoReturn]:
        if not deadline:
            return None
        if isinstance(deadline, date):
            return deadline
        try:
            parsed_deadline = date.fromisoformat(deadline)
            return parsed_deadline
        except Exception:
            raise ValueError('Некорректный формат дедлайна задачи')

