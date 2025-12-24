import random
from datetime import timedelta
from typing import Union, NoReturn
from abc import ABC, abstractmethod
from decimal import Decimal

from django.db import transaction

from task.helpers.date import is_out_of_deadline
from task.infrastructure.database_repository import TaskDatabaseRepositoryInterface
from user.domain.entities import UserEntity
from ..infrastructure.database_repository import HistoryDatabaseRepositoryInterface
from ..domain.entities import SharedHistoryEntity
from ..constants.choices import HistoryTaskStatusChoices


class HistoryUseCaseInterface(ABC):

    @abstractmethod
    def move_task_to_history(
        self, 
        user: UserEntity, 
        task_id: int, 
        execution_time: timedelta,
        successful: str
    ) -> Union[None, NoReturn]:
        pass

    @abstractmethod
    def save_user_shared_history(
                self, 
                user: UserEntity, 
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
                user: UserEntity
            ) -> list[SharedHistoryEntity]:
        pass

    @abstractmethod
    def delete_user_shared_history_by_key(
                self, 
                history_id: int, 
                user: UserEntity
            ) -> SharedHistoryEntity:
        pass

    @abstractmethod
    def delete_user_history_by_id(
                self, 
                history_id: int,
                user: UserEntity
            ) -> Union[None, NoReturn]:
        pass

    @abstractmethod
    def get_user_history_statistics(self, user: UserEntity) -> dict:
        pass


class HistoryUseCase(HistoryUseCaseInterface):

    def __init__(
                self, 
                history_database_repository: HistoryDatabaseRepositoryInterface,
                task_database_repository: TaskDatabaseRepositoryInterface = None,
            ) -> None:
        self._history_database_repository = history_database_repository
        self._task_database_repository = task_database_repository

    @transaction.atomic
    def move_task_to_history(
            self, 
            user: UserEntity, 
            task_id: int, 
            execution_time: timedelta,
            successful: str
        ) -> Union[None, NoReturn]:
        task = self._task_database_repository.get_task_by_id(task_id)
        if task.user_id != user.id:
            raise PermissionError()
        status: str

        if successful == 'false':
            status = HistoryTaskStatusChoices.FAILED
        elif is_out_of_deadline(task.deadline):
            status = HistoryTaskStatusChoices.OUT_OF_DEADLINE
        elif successful == 'true':
            status = HistoryTaskStatusChoices.SUCCESSFUL

        self._task_database_repository.delete_task(task)
        self._history_database_repository.save_task_to_history(task, execution_time, status)

    def save_user_shared_history(
                self, 
                user: UserEntity, 
                from_date: str, 
                to_date: str
            ) -> str:
        key = self._generate_random_string()
        user_history_statistics = self.get_user_history_statistics(
                user, from_date, to_date
            )
        self._history_database_repository.save_user_shared_history(
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
        saved_history_object = self._history_database_repository.get_shared_history_by_key(key)
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
                user: UserEntity
            ) -> list[SharedHistoryEntity]:
        return self._history_database_repository.get_user_shared_histories(user)

    def delete_user_shared_history_by_key(
                self, 
                history_id: int, 
                user: UserEntity
            ) -> Union[None, NoReturn]:
        history = self._history_database_repository.get_shared_history_by_key(history_id)
        if history.user != user:
            raise PermissionError
        self._history_database_repository.delete_shared_history(history)

    def delete_user_history_by_id(
                self, 
                history_id: int, 
                user: UserEntity
            ) -> Union[None, NoReturn]:
        history = self._history_database_repository.get_history_by_id(history_id)
        if history.user != user:
            raise PermissionError
        self._history_database_repository.delete_history(history)   

    def get_user_history_statistics(
                self, 
                user: UserEntity, 
                from_date: str, 
                to_date: str
            ) -> dict:
        raw_count_user_tasks_in_categories = self._history_database_repository.get_count_user_tasks_in_categories(
                user, from_date, to_date
            )
        raw_common_user_accuracy = self._history_database_repository.get_common_user_accuracy(
                user, from_date, to_date
            )
        raw_user_accuracy_by_categories = self._history_database_repository.get_user_accuracy_by_categories(
                user, from_date, to_date
            )
        raw_common_user_success_rate = self._history_database_repository.get_user_common_success_rate(
                user, from_date, to_date
            )
        raw_user_success_rate_by_categories = self._history_database_repository.get_user_success_rate_by_categories(
                user, from_date, to_date
            )
        raw_count_user_tasks_by_weekdays = self._history_database_repository.get_count_user_tasks_by_weekdays(
                user, from_date, to_date
            )   
        raw_common_count_successful_planned_tasks = self._history_database_repository.get_common_count_user_successful_planned_tasks(
                user, from_date, to_date
            )
        raw_count_successful_planned_tasks_by_categories = self._history_database_repository.get_count_user_successful_planned_tasks_by_categories(
                user, from_date, to_date
            )

        history = self._history_database_repository.get_user_history(
                user, from_date, to_date
            )

        statistics = {
            'count_user_tasks_in_categories': self._format_count_user_tasks_in_categories(
                raw_count_user_tasks_in_categories
            ),
            'common_user_accuracy': self._format_common_user_accuracy(
                raw_common_user_accuracy
            ),
            'user_accuracy_by_categories': self._format_user_accuracy_by_categories(
                raw_user_accuracy_by_categories
            ),
            'common_user_success_rate': self._format_common_user_success_rate(
                raw_common_user_success_rate
            ),
            'user_success_rate_by_categories':
                self._format_user_success_rate_by_categories(
                    raw_user_success_rate_by_categories
                ),
            'count_user_tasks_by_weekdays': self._format_count_user_tasks_by_weekdays(
                raw_count_user_tasks_by_weekdays
            ),
            'common_count_user_successful_planned_tasks': self._format_common_count_user_successful_planned_tasks(
                raw_common_count_successful_planned_tasks
            ),
            'count_user_successful_planned_tasks_by_categories': self._format_count_user_successful_planned_tasks_by_categories(
                raw_count_successful_planned_tasks_by_categories
            ),

        }
        return {
            'history': history,
            'statistics': statistics
        }

    def _format_count_user_tasks_in_categories(
                self, 
                raw_count_user_tasks_in_categories: list[tuple[str, int]]
            ) -> dict[int, Union[list[int], list[str]]]:
        count_user_tasks_in_categories = {
                'labels': [], 'colors': [], 'data': []
            }
        for row in raw_count_user_tasks_in_categories:
            count_user_tasks_in_categories['labels'].append(row[0])
            count_user_tasks_in_categories['colors'].append(row[1])
            count_user_tasks_in_categories['data'].append(row[2])
        print(count_user_tasks_in_categories)
        return count_user_tasks_in_categories

    def _format_common_user_accuracy(
                self, 
                raw_common_user_accuracy: list[tuple[Decimal]]
            ) -> dict[str, Union[list[str], list[float]]]:
        try:
            return {
                    'labels': ['Точность', 'Точность'],
                    'colors': ['rgba(0, 255, 0, 0.4)', 'rgba(255, 0, 0, 0.4)'],
                    'data': [
                        float(raw_common_user_accuracy[0][0]), 
                        round(100.0 - float(raw_common_user_accuracy[0][0]), 2)
                    ]
                }
        except TypeError:
            return {}

    def _format_user_accuracy_by_categories(
                self, 
                raw_user_accuracy_by_categories: list[tuple[str, Decimal]]
            ) -> dict[str, Union[list[str], list[float]]]:
        user_accuracy_by_categories = {'labels': [], 'colors': [], 'data': []}
        for row in raw_user_accuracy_by_categories:
            user_accuracy_by_categories['labels'].append(row[0])
            user_accuracy_by_categories['colors'].append(row[1])
            user_accuracy_by_categories['data'].append(float(row[2]))
        return user_accuracy_by_categories

    def _format_common_user_success_rate(
                self, 
                raw_common_user_success_rate: list[tuple[int]]
            ) -> dict[str, Union[list[str], list[float]]]:
        return {
            'labels': ['Выполненные задачи', 'Проваленные задачи'],
            'colors': ['rgba(0, 255, 0, 0.4)', 'rgba(255, 0, 0, 0.4)'],
            'data': [
                raw_common_user_success_rate[0][0], 
                raw_common_user_success_rate[0][1]
            ]
        }

    def _format_user_success_rate_by_categories(
                self, 
                raw_user_success_rate_by_categories: list[tuple[str, int]]
            ) -> dict[str, Union[list[str], list[int]]]:
        user_success_rate_by_categories = {
                'labels': [], 'colors': [], 'data': []
            }
        for row in raw_user_success_rate_by_categories:
            user_success_rate_by_categories['labels'].append(row[0])
            user_success_rate_by_categories['colors'].append(row[1])
            user_success_rate_by_categories['data'].append(row[2]) 
        return user_success_rate_by_categories

    def _format_count_user_tasks_by_weekdays(
                self, 
                raw_count_user_tasks_by_weekdays: list[tuple[str, int]]
            ) -> dict[str, Union[list[str], list[int]]]:
        count_user_tasks_by_weekdays = {'labels': [], 'data': []}
        for row in raw_count_user_tasks_by_weekdays:
            count_user_tasks_by_weekdays['labels'].append(row[0])
            count_user_tasks_by_weekdays['data'].append(row[1]) 
        return count_user_tasks_by_weekdays

    def _format_common_count_user_successful_planned_tasks(
                self, 
                raw_common_count_successful_planned_tasks: list[tuple[int]]
            ) -> dict[str, Union[list[str], list[int]]]:
        return {
            'labels': [
                'Успешно запланированные задачи', 
                'Неправильно запланированные задачи'
            ],
            'colors': ['rgba(0, 255, 0, 0.4)', 'rgba(255, 0, 0, 0.4)'],
            'data': [
                raw_common_count_successful_planned_tasks[0][0], 
                raw_common_count_successful_planned_tasks[0][1]
            ]
        } 

    def _format_count_user_successful_planned_tasks_by_categories(
                self, 
                raw_count_successful_planned_tasks_by_categories: list[tuple[str, int]]
            ) -> dict[str, Union[list[str], list[int]]]:
        count_successful_planned_tasks_by_categories = {
                'labels': [], 'colors': [], 'data': []
            }
        for row in raw_count_successful_planned_tasks_by_categories:
            count_successful_planned_tasks_by_categories['labels'].append(row[0])
            count_successful_planned_tasks_by_categories['colors'].append(row[1])
            count_successful_planned_tasks_by_categories['data'].append(row[2]) 
        return count_successful_planned_tasks_by_categories

