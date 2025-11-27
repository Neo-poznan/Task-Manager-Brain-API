from datetime import date
from dataclasses import dataclass

from datetime import timedelta, date

from task.domain.entities import CategoryEntity
from user.domain.entities import UserEntity


@dataclass
class HistoryEntity:
    id: int
    name: str
    category: CategoryEntity
    user: UserEntity
    planned_time: timedelta
    execution_time: timedelta
    execution_date: date
    status: str


@dataclass
class IncompleteHistoryEntity:
    id: int
    name: str

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


@dataclass
class SharedHistoryEntity:
    key: int
    user: UserEntity
    from_date: date
    to_date: date
    history_statistics: dict


