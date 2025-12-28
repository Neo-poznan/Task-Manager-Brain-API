from pprint import pprint
import random
from datetime import date, timedelta
from typing import Iterable, Union, NoReturn
from abc import ABC, abstractmethod
from copy import deepcopy

from django.db import transaction

from task.infrastructure import TaskRepositoryInterface
from task.domain import TaskEntityProtocol
from user.domain.entities import UserEntityProtocol
from .infrastructure import HistoryRepositoryInterface, SharedHistoryRepositoryInterface
from .domain import HistoryEntity, SharedHistoryEntity
from .constants.choices import HistoryTaskStatusChoices


class HistoryServiceInterface(ABC):

    @abstractmethod
    def save_user_shared_history(
                self, 
                user: UserEntityProtocol, 
                from_date: str, 
                to_date: str
            ) -> str:
        pass

    @abstractmethod
    def get_shared_history_by_key(self, key: str) -> dict:
        pass

    @abstractmethod
    def get_user_shared_histories(
                self, 
                user: UserEntityProtocol
            ) -> list[SharedHistoryEntity]:
        pass

    @abstractmethod
    def delete_user_shared_history_by_key(
                self, 
                history_id: int, 
                user: UserEntityProtocol
            ) -> SharedHistoryEntity:
        pass


class MoveTaskToHistoryUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self, 
            user: UserEntityProtocol, 
            task_id: int, 
            execution_time: timedelta,
        ) -> Union[None, NoReturn]:
        pass


class GetUserHistoryUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self, 
            user: UserEntityProtocol, 
            from_date: str, 
            to_date: str
        ) -> dict:
        pass


class HistoryService(HistoryServiceInterface):

    def __init__(
            self, 
            _shared_history_repository: SharedHistoryRepositoryInterface,
        ) -> None:
        self._shared_history_repository = _shared_history_repository

    def save_user_shared_history(
                self, 
                user: UserEntityProtocol, 
                user_history_statistics: dict,
                from_date: str, 
                to_date: str
            ) -> str:
        key = self._generate_random_string()
        self._shared_history_repository.save_user_shared_history(
                key, user, user_history_statistics, from_date, to_date
            )
        return key
    
    def _generate_random_string(self) -> str:
        string = ''
        chars = '1234567890-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for i in range(12):
            string += random.choice(chars)
        return string

    def get_shared_history_by_key(self, key: str) -> dict:
        saved_history_object = self._shared_history_repository.get_shared_history_by_key(key)
        saved_history = saved_history_object.history_statistics
        history_metadata = {
            'from_date': saved_history_object.from_date,
            'to_date': saved_history_object.to_date,
            'owner': saved_history_object.user
        }
        saved_history.update(history_metadata)
        return saved_history

    def get_user_shared_histories(
                self, 
                user: UserEntityProtocol
            ) -> list[SharedHistoryEntity]:
        return self._shared_history_repository.get_user_shared_histories(user)

    def delete_user_shared_history_by_key(
                self, 
                history_id: int, 
                user: UserEntityProtocol
            ) -> Union[None, NoReturn]:
        history = self._shared_history_repository.get_shared_history_by_key(history_id)
        if history.user != user:
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
                user: UserEntityProtocol, 
                from_date: str, 
                to_date: str
            ) -> dict:
        count_tasks_in_categories = self._history_repository.get_count_tasks_in_categories(
                user, from_date, to_date
            )
        common_accuracy = self._history_repository.get_common_accuracy(
                user, from_date, to_date
            )
        accuracy_by_categories = self._history_repository.get_accuracy_by_categories(
                user, from_date, to_date
            )
        common_success_rate = self._history_repository.get_common_success_rate(
                user, from_date, to_date
            )
        success_rate_by_categories = self._history_repository.get_success_rate_by_categories(
                user, from_date, to_date
            )
        count_tasks_by_weekdays = self._history_repository.get_count_tasks_by_weekdays(
                user, from_date, to_date
            )   
        common_successful_planning_rate = self._history_repository.get_common_successful_planning_rate(
                user, from_date, to_date
            )
        count_successful_planned_tasks_by_categories = self._history_repository.get_count_successful_planned_tasks_by_categories(
                user, from_date, to_date
            )

        history = self._history_repository.get_history(
                user, from_date, to_date
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
            user: UserEntityProtocol, 
            task_id: int, 
            execution_time: timedelta,
            successful: str
        ) -> Union[None, NoReturn]:
    
        task = self._task_repository.get_task_by_id(task_id)
        self._user_task_owner(user, task)
        status = self._get_history_task_status(task, successful)

        history_task = HistoryEntity.from_task(
                task, 
                execution_time, 
                status
            )
        self._task_repository.delete_task(task)
        self._history_repository.save_history(history_task)

    def _user_task_owner(self, user: UserEntityProtocol, task: TaskEntityProtocol) -> Union[None, NoReturn]:
        if not task.user_id == user.id:
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

