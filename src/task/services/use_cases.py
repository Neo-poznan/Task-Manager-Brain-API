from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Union, NoReturn

from ..infrastructure.database_repository import TaskDatabaseRepositoryInterface, CategoryDatabaseRepositoryInterface
from user.domain.entities import UserEntity
from ..domain.entities import TaskEntity, CategoryEntity
from ..helpers.date import is_out_of_deadline
from history.infrastructure.database_repository import HistoryDatabaseRepositoryInterface

class TaskUseCaseInterface(ABC):

    @abstractmethod
    def get_ordered_user_tasks(self, user: UserEntity) -> list[TaskEntity]:
        pass

    @abstractmethod
    def get_user_task_count_by_categories(self, user: UserEntity) -> dict[str, list]:
        pass

    @abstractmethod
    def get_user_tasks_by_deadlines(
            self, 
            user: UserEntity
        ) -> dict[str, list]:
        pass

    @abstractmethod
    def update_user_deadlines(
            self,
            user: UserEntity,
            new_deadlines: dict[str, list]
        ) -> None:
        pass

    @abstractmethod
    def update_user_task_order(
                self, 
                user: UserEntity,
                new_order: list[str]
            ) -> None:
        pass

    @abstractmethod
    def get_user_task_by_id(
            self, 
            task_id: int, 
            user: UserEntity
        ) -> Union[TaskEntity, NoReturn]:
        pass

    @abstractmethod
    def get_next_task_order(self, user: UserEntity) -> int:
        pass

    @abstractmethod
    def get_user_category_by_id(
                self, 
                category_id: int, 
                user: UserEntity
            ) -> Union[CategoryEntity, NoReturn]:
        pass

    @abstractmethod
    def get_ordered_user_categories(
                self, 
                user: UserEntity
            ) -> list[CategoryEntity]:
        pass

    @abstractmethod
    def save_task_to_history(
                self, 
                user: UserEntity, 
                task_id: int, 
                execution_time: timedelta,
                successful: bool,
            ) -> None:
        pass


class TaskUseCase(TaskUseCaseInterface):
    def __init__(
                self, task_database_repository: TaskDatabaseRepositoryInterface = None,
                category_database_repository: CategoryDatabaseRepositoryInterface = None,
                history_database_repository: HistoryDatabaseRepositoryInterface = None
            ):
        self._task_database_repository = task_database_repository
        self._category_database_repository = category_database_repository
        self._history_database_repository = history_database_repository

    def get_ordered_user_tasks(self, user: UserEntity) -> list[TaskEntity]:
        return self._task_database_repository.get_ordered_user_tasks_json(user)

    def get_user_task_count_by_categories(
                self, 
                user: UserEntity
            ) -> dict[str, Union[list[int], list[str]]]:
        task_count_statistics = self._task_database_repository.get_count_user_tasks_in_categories(user)
        return task_count_statistics

    def get_user_tasks_by_deadlines(
                self, 
                user: UserEntity
            ) -> dict[str, list[dict[str, Union[int, str]]]]:
        count_user_tasks_in_categories_by_deadlines = self._task_database_repository.get_user_tasks_by_deadlines(user)
        return count_user_tasks_in_categories_by_deadlines
    
    def update_user_deadlines(
                self,
                user: UserEntity,
                new_deadlines: dict[str, list]
            ) -> None:
        for date, tasks in new_deadlines.items():
            self._task_database_repository.update_user_deadlines_by_date(user, date, tasks)

    def get_user_task_by_id(
                self,
                task_id: int, 
                user: UserEntity
            ) -> Union[TaskEntity, NoReturn]:
        task = self._task_database_repository.get_task_by_id(task_id)
        if task.user == user:
            return task
        else:
            raise PermissionError

    def get_next_task_order(self, user: UserEntity) -> int:
        return self._task_database_repository.get_next_task_order(user)

    def update_user_task_order(
            self, 
            user: UserEntity, 
            new_order: list[str]
        ) -> None:
        self._task_database_repository.update_user_task_order(user, new_order)

    def get_user_category_by_id(
                self, 
                category_id: int, 
                user: UserEntity
            ) -> Union[CategoryEntity, NoReturn]:
        category = self._category_database_repository.get_category_by_id(category_id)
        # Это исключение будет райзиться не только тогда, когда пользователь пытается редактировать чужую задачу, но и тогда, 
        # когда категория не является кастомной, и, соответственно не имеет пользователя
        if category.user != user:
            raise PermissionError
        return category

    def get_ordered_user_categories(self, user: UserEntity) -> list[CategoryEntity]:
        return self._category_database_repository.get_ordered_user_categories_json(user)

    def save_task_to_history(
                self, 
                user: UserEntity, 
                task_id: int, 
                execution_time: timedelta,
                successful: str
            ) -> None:
        task = self._task_database_repository.get_task_by_id(task_id)
        if task.user_id != user.id:
            raise PermissionError

        if not successful == 'true':
            self._history_database_repository.save_task_to_history_as_failed(task, execution_time)
        elif not is_out_of_deadline(task.deadline):
            self._history_database_repository.save_task_to_history_as_successful(task, execution_time)
        else:
            self._history_database_repository.save_task_to_history_as_outed_of_deadline(task, execution_time)

