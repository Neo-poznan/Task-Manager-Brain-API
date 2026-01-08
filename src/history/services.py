import re
import random
from datetime import date, timedelta, datetime
from typing import Iterable, Union, NoReturn
from abc import ABC, abstractmethod
from copy import deepcopy

from django.db import transaction
from django.core.exceptions import ValidationError

from task.infrastructure import TaskRepositoryInterface
from task.domain import TaskEntityProtocol
from .infrastructure import HistoryRepositoryInterface, SharedHistoryRepositoryInterface
from .domain import HistoryEntity, SharedHistoryEntity
from .constants.choices import HistoryTaskStatusChoices


class ShareHistoryServiceInterface(ABC):

    @abstractmethod
    def get_shared_history_by_key(self, key: str) -> dict:
        pass

    @abstractmethod
    def get_user_shared_histories(
                self, 
                user_id: int
            ) -> list[SharedHistoryEntity]:
        pass

    @abstractmethod
    def delete_user_shared_history_by_key(
                self, 
                history_id: int, 
                user_id: int
            ) -> SharedHistoryEntity:
        pass


class MoveTaskToHistoryUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self, 
            user_id: int, 
            task_id: int, 
            execution_time: timedelta,
        ) -> Union[None, NoReturn]:
        pass


class GetUserHistoryUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self, 
            user_id: int, 
            from_date: str, 
            to_date: str
        ) -> dict:
        pass


class HistoryServiceInterface(ABC):

    @abstractmethod
    def get_user_history_statistics_for_today(
            self, 
            user_id: int
        ) -> dict:
        pass

    @abstractmethod
    def delete_user_history_by_id(
            self, 
            history_id: int, 
            user_id: int
        ) -> Union[None, NoReturn]:
        pass


class ShareHistoryUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self, 
            user_id: int, 
            from_date: str, 
            to_date: str
        ) -> str:
        pass


class ShareHistoryService(ShareHistoryServiceInterface):

    def __init__(
            self, 
            _shared_history_repository: SharedHistoryRepositoryInterface,
        ) -> None:
        self._shared_history_repository = _shared_history_repository

    def get_shared_history_by_key(self, key: str) -> dict:
        shared_history = self._shared_history_repository.get_shared_history_by_key(key)
        shared_history = shared_history.history_statistics
        history_metadata = {
            'from_date': shared_history.from_date,
            'to_date': shared_history.to_date,
            'owner': shared_history.user
        }
        shared_history.update(history_metadata)
        return shared_history

    def get_user_shared_histories(
                self, 
                user_id: int
            ) -> list[SharedHistoryEntity]:
        return self._shared_history_repository.get_user_shared_histories(user_id)

    def delete_user_shared_history_by_key(
                self, 
                history_id: int, 
                user_id: int
            ) -> Union[None, NoReturn]:
        history = self._shared_history_repository.get_shared_history_by_key(history_id)
        if history.user_id != user_id:
            raise PermissionError
        self._shared_history_repository.delete_shared_history(history)


class GetUserHistoryUseCase(GetUserHistoryUseCaseInterface):

    def __init__(
            self, 
            history_repository: HistoryRepositoryInterface,
        ):
        self._history_repository = history_repository

    def execute(
            self, 
            user_id: int, 
            from_date: str, 
            to_date: str
        ) -> dict:
        
        self._validate_dates(from_date, to_date)
        self._validate_dates_range(from_date, to_date)

        count_tasks_in_categories = self._history_repository.get_count_tasks_in_categories(
            user_id, from_date, to_date
        )
        common_accuracy = self._history_repository.get_common_accuracy(
            user_id, from_date, to_date
        )
        accuracy_by_categories = self._history_repository.get_accuracy_by_categories(
            user_id, from_date, to_date
        )
        common_success_rate = self._history_repository.get_common_success_rate(
            user_id, from_date, to_date
        )
        success_rate_by_categories = self._history_repository.get_success_rate_by_categories(
            user_id, from_date, to_date
        )
        count_tasks_by_weekdays = self._history_repository.get_count_tasks_by_weekdays(
            user_id, from_date, to_date
        )   
        common_successful_planning_rate = self._history_repository.get_common_successful_planning_rate(
            user_id, from_date, to_date
        )
        count_successful_planned_tasks_by_categories = self._history_repository.get_count_successful_planned_tasks_by_categories(
            user_id, from_date, to_date
        )

        history = self._history_repository.get_history(
                user_id, from_date, to_date
            )
        
        common_successful_planning_rate = {'data': self._calculate_successful_planning_rate(common_successful_planning_rate[0], common_successful_planning_rate[1])}
        common_success_rate = {'data': self._calculate_success_rate(common_success_rate[0], common_success_rate[1])}
        common_accuracy = {'data': float(common_accuracy)}

        statistics = {
            'countUserTasksInCategories': count_tasks_in_categories,
            'commonUserAccuracy': common_accuracy,
            'userAccuracyByCategories': accuracy_by_categories, 
            'commonUserSuccessRate': common_success_rate,
            'userSuccessRateByCategories': success_rate_by_categories,
            'countUserTasksByWeekdays': count_tasks_by_weekdays,
            'commonUserSuccessfulPlanningRate': common_successful_planning_rate,
            'countUserSuccessfulPlannedTasksByCategories': count_successful_planned_tasks_by_categories,
        }
        cleaned_statistics = self._clean_statistics(statistics)
        return {
            'history': history,
            'statistics': cleaned_statistics
        }

    def _validate_dates(self, from_date_str: str, to_date_str: str) -> Union[None, NoReturn]:
        template = r'^\d\d\d\d-\d\d-\d\d$'
        if not re.fullmatch(template, from_date_str) or not re.fullmatch(template, to_date_str):
            raise ValidationError('Неправильный формат даты')
        try:
            datetime.strptime(from_date_str, '%Y-%m-%d').date()
            datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except Exception as exc:
            raise ValidationError('Неправильный формат даты')    

    def _validate_dates_range(self, from_date_str: str, to_date_str:str) -> Union[None, NoReturn]:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        if not from_date < to_date:
            raise ValidationError('Вторая дата должна быть больше первой')

    def _calculate_successful_planning_rate(
            self,
            successful_planned_tasks: int,
            total_planned_tasks: int
        ) -> float:
        if total_planned_tasks == 0:
            return 0.0
        return round(successful_planned_tasks / total_planned_tasks * 100, 2)

    def _calculate_success_rate(
            self,
            successful_tasks: int,
            total_tasks: int
        ) -> float:
        if total_tasks == 0:
            return 0.0
        return round(successful_tasks / total_tasks * 100, 2)

    def _clean_statistics(self, statistics: dict) -> dict:
        cleaned_statistics = deepcopy(statistics)
        for key in statistics.keys():
            if self._is_statistics_empty(statistics[key]):
                del cleaned_statistics[key]
        return cleaned_statistics
    
    def _is_statistics_empty(self, statistics: dict) -> bool:
        values = statistics['data']
        if not isinstance(values, Iterable):
            values = [values]
        if not values:
            return True
        if not any(values):
            print('empty', values)
            return True
        return False


class MoveTaskToHistoryUseCase(MoveTaskToHistoryUseCaseInterface):

    def __init__(
            self, 
            history_repository: HistoryRepositoryInterface,
            task_repository: TaskRepositoryInterface,
        ):
        self._history_repository = history_repository
        self._task_repository = task_repository
        
    @transaction.atomic
    def execute(
            self, 
            user_id: int, 
            task_id: int, 
            execution_time: timedelta,
            successful: str
        ) -> Union[None, NoReturn]:
    
        task = self._task_repository.get_task_by_id(task_id)
        self._user_task_owner(user_id, task)
        status = self._get_history_task_status(task, successful)

        history_task = HistoryEntity.from_task(
                task, 
                execution_time, 
                status
            )
        self._task_repository.delete_task(task)
        self._history_repository.save_history(history_task)

    def _user_task_owner(self, user_id: int, task: TaskEntityProtocol) -> Union[None, NoReturn]:
        if not task.user_id == user_id:
            raise PermissionError

    def _get_history_task_status(
            self, 
            task: TaskEntityProtocol, 
            successful: str
        ) -> str:
        if successful == 'false':
            return HistoryTaskStatusChoices.FAILED
        elif successful == 'true' and self._is_out_of_deadline(task.deadline):
            return HistoryTaskStatusChoices.OUT_OF_DEADLINE
        elif successful == 'true':
            return HistoryTaskStatusChoices.SUCCESSFUL
        else:
            raise TypeError('Status is incorrect!')

    def _is_out_of_deadline(self, deadline: date) -> bool:
        now = date.today()
        if deadline and deadline < now:
            return True
        return False
    

class HistoryService(HistoryServiceInterface):
    def __init__(
            self, 
            history_repository: HistoryRepositoryInterface,
        ):
        self._history_repository = history_repository

    def get_user_history_statistics_for_today(self, user_id: int) -> dict:
        statistics = {
            'tasks': self._history_repository.get_user_tasks_for_today_json(user_id),
            'categories' : self._history_repository.get_count_user_tasks_in_categories_for_today(user_id),
        }
        return statistics
    
    def delete_user_history_by_id(
            self, 
            history_id: int, 
            user_id: int
        ) -> Union[None, NoReturn]:
        history = self._history_repository.get_history_by_id(history_id)
        if history.user_id != user_id:
            raise PermissionError
        self._history_repository.delete_history(history)


class ShareHistoryUseCase(ShareHistoryUseCaseInterface):

    def __init__(
            self, 
            shared_history_repository: SharedHistoryRepositoryInterface,
            get_history_use_case: GetUserHistoryUseCaseInterface,
        ) -> None:
        self._shared_history_repository = shared_history_repository
        self._get_history_use_case = get_history_use_case

    def execute(
            self, 
            user_id: int, 
            from_date: str, 
            to_date: str
        ) -> str:
        
        history_statistics = self._get_history_use_case.execute(user_id=user_id, from_date=from_date, to_date=to_date)

        key = self._generate_random_string()
        self._shared_history_repository.save_user_shared_history(
            key, user_id, history_statistics, from_date, to_date
        )
        return key
    
    def _generate_random_string(self) -> str:
        string = ''
        chars = '1234567890-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for i in range(12):
            string += random.choice(chars)
        return string



