from dataclasses import dataclass

from datetime import timedelta, date


@dataclass
class HistoryEntity:
    id: int
    name: str
    category_id: int
    user_id: int
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
    user_id: int
    from_date: date
    to_date: date
    history_statistics: dict

