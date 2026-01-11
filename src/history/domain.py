from dataclasses import dataclass
from datetime import timedelta, date
from typing import NoReturn, Optional, Union
from uuid import UUID

from task.domain import TaskEntityProtocol
from .constants.choices import HistoryTaskStatusChoices


class HistoryEntity:
    def __init__(
        self,
        id: Optional[int],
        name: str,
        user_id: UUID,
        execution_time: timedelta,
        status: str,
        planned_time: Optional[timedelta] = None,
        execution_date: Optional[date] = None,
        category_id: Optional[int] = None,
    ):
        self.id = id
        self.name = name
        self.category_id = category_id
        self.user_id = user_id
        self.planned_time = planned_time
        self.execution_time = execution_time
        self.execution_date = execution_date
        self.status = self._validate_status(status)
    
    def _validate_name(self, name: str) -> Union[str, NoReturn]:
        if not name:
            raise ValueError('Название задачи не может быть пустым')
        if len(name) > 290:
            raise ValueError('Название задачи не может быть длиннее 290 символов')
        return name
    
    def _validate_status(self, status: str) -> Union[str, NoReturn]:
        if not status in HistoryTaskStatusChoices.values:
            raise ValueError('Недопустимый статус задачи в истории')
        return status

    @classmethod
    def from_task(cls, task: TaskEntityProtocol, execution_time: timedelta, is_successful: bool) -> "HistoryEntity":
        return cls(
            id=None,
            name=task.name,
            category_id=task.category_id,
            user_id=task.user_id,
            planned_time=task.planned_time,
            execution_time=execution_time,
            status=cls._get_status(is_successful, task.deadline, date.today()),
        )

    @classmethod
    def _get_status(cls, is_successful: bool, task_deadline: Optional[date], execution_date: date) -> str:
        is_successful = cls._parse_is_successful(str(is_successful).lower())
        if is_successful and cls._is_out_of_deadline(task_deadline, execution_date):
            return HistoryTaskStatusChoices.OUT_OF_DEADLINE
        elif is_successful:
            return HistoryTaskStatusChoices.SUCCESSFUL
        elif not is_successful:
            return HistoryTaskStatusChoices.FAILED

    @classmethod
    def _parse_is_successful(cls, status: str) -> bool:
        if status == 'true':
            return True
        elif status == 'false':
            return False
        else:
            raise ValueError('Недопустимое значение для is_successful')

    @classmethod
    def _is_out_of_deadline(cls, task_deadline: Optional[date], execution_date: date) -> bool:
        if task_deadline and execution_date > task_deadline:
            return True
        return False
    

@dataclass
class SharedHistoryEntity:
    key: int
    user_id: int
    from_date: date
    to_date: date
    history_statistics: dict

