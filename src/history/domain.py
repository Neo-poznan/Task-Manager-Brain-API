from dataclasses import dataclass
from datetime import timedelta, date

from task.domain import TaskEntityProtocol


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

    @classmethod
    def from_task(cls, task: TaskEntityProtocol, execution_time: timedelta, status: str):
        return cls(
            id=None,
            name=task.name,
            category_id=task.category_id,
            user_id=task.user_id,
            planned_time=task.planned_time,
            execution_time=execution_time,
            execution_date=date.today(),
            status=status
        )


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

