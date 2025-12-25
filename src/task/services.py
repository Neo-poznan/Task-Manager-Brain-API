from abc import ABC, abstractmethod
from typing import Union, NoReturn

from .infrastructure import TaskRepositoryInterface, CategoryRepositoryInterface
from user.domain.entities import UserEntityProtocol
from .domain import TaskEntityProtocol, CategoryEntityProtocol


class TaskServiceInterface(ABC):

    @abstractmethod
    def get_ordered_user_tasks(self, user: UserEntityProtocol) -> list[TaskEntityProtocol]:
        pass

    @abstractmethod
    def get_user_task_count_by_categories(self, user: UserEntityProtocol) -> dict[str, list]:
        pass

    @abstractmethod
    def get_user_tasks_by_deadlines(
            self, 
            user: UserEntityProtocol
        ) -> dict[str, list]:
        pass

    @abstractmethod
    def get_user_task_by_id(
            self, 
            task_id: int, 
            user: UserEntityProtocol
        ) -> Union[TaskEntityProtocol, NoReturn]:
        pass

    @abstractmethod
    def get_next_task_order(self, user: UserEntityProtocol) -> int:
        pass

    @abstractmethod
    def get_user_category_by_id(
                self, 
                category_id: int, 
                user: UserEntityProtocol
            ) -> Union[CategoryEntityProtocol, NoReturn]:
        pass

    @abstractmethod
    def get_ordered_user_categories(
                self, 
                user: UserEntityProtocol
            ) -> list[CategoryEntityProtocol]:
        pass


class DeadlinesUpdateUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self,
            user: UserEntityProtocol,
            new_deadlines: dict[str, list]
        ) -> None:
        pass


class TaskOrderUpdateUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self, 
            user: UserEntityProtocol, 
            new_order: list[str]
        ) -> None:
        pass


class TaskService(TaskServiceInterface):
    def __init__(
            self, task_repository: TaskRepositoryInterface = None,
            category_repository: CategoryRepositoryInterface = None
        ):
        self._task_repository = task_repository
        self._category_repository = category_repository

    def get_ordered_user_tasks(self, user: UserEntityProtocol) -> list[TaskEntityProtocol]:
        return self._task_repository.get_ordered_user_tasks_json(user)

    def get_user_task_count_by_categories(
                self, 
                user: UserEntityProtocol
            ) -> dict[str, Union[list[int], list[str]]]:
        task_count_statistics = self._task_repository.get_count_user_tasks_in_categories(user)
        return task_count_statistics

    def get_user_tasks_by_deadlines(
                self, 
                user: UserEntityProtocol
            ) -> dict[str, list[dict[str, Union[int, str]]]]:
        count_user_tasks_in_categories_by_deadlines = self._task_repository.get_user_tasks_by_deadlines(user)
        return count_user_tasks_in_categories_by_deadlines

    def get_user_task_by_id(
                self,
                task_id: int, 
                user: UserEntityProtocol
            ) -> Union[TaskEntityProtocol, NoReturn]:
        task = self._task_repository.get_task_by_id(task_id)
        if task.user == user:
            return task
        else:
            raise PermissionError

    def get_next_task_order(self, user: UserEntityProtocol) -> int:
        return self._task_repository.get_next_task_order(user)

    def get_user_category_by_id(
                self, 
                category_id: int, 
                user: UserEntityProtocol
            ) -> Union[CategoryEntityProtocol, NoReturn]:
        category = self._category_repository.get_category_by_id(category_id)
        if category.user != user:
            raise PermissionError
        return category

    def get_ordered_user_categories(self, user: UserEntityProtocol) -> list[CategoryEntityProtocol]:
        return self._category_repository.get_ordered_user_categories_json(user)
    

class TaskOrderUpdateUseCase(TaskOrderUpdateUseCaseInterface):
    def __init__(self, task_repository: TaskRepositoryInterface):
        self._task_repository = task_repository

    def execute(
            self, 
            user: UserEntityProtocol, 
            new_order: list[str]
        ) -> None:
        user_tasks = self._task_repository.get_ordered_user_tasks(user)
        existing_task_ids = self._get_ids_of_existing_tasks(user_tasks)
        cleaned_new_order = self._delete_from_new_order_tasks_that_cannot_be_updated(
            new_order, 
            existing_task_ids
        )
        self._task_repository.update_user_tasks_order(user, cleaned_new_order)

    def _get_ids_of_existing_tasks(self, existing_tasks: list[TaskEntityProtocol]) -> list[str]:
        return [str(task.id) for task in existing_tasks]

    def _delete_from_new_order_tasks_that_cannot_be_updated(
            self, 
            new_order: list[str], 
            existing_tasks: list[str]
        ) -> list[str]:
        '''
        Delete task ids from new_order that do not exist or do not belong to the user.
        '''
        return list(filter(lambda task_id: task_id in existing_tasks, new_order))


class DeadlinesUpdateUseCase(DeadlinesUpdateUseCaseInterface):
    def __init__(self, task_repository: TaskRepositoryInterface):
        self._task_repository = task_repository

    def execute(
            self,
            user: UserEntityProtocol,
            new_deadlines: dict[str, list[dict[str, Union[int, str]]]]
        ) -> Union[None, NoReturn]:

        for date, tasks in new_deadlines.items():
            for task_json in tasks:
                task = self._task_repository.get_task_by_id(task_json['id'])
                self._user_task_owner(user, task)
                if self._deadline_has_changed(task, date):
                    self._update_deadline(task, date)

    def _user_task_owner(
            self,
            user: UserEntityProtocol,
            task: TaskEntityProtocol,
        ) -> Union[None, NoReturn]:
        if not task.user_id == user.id:
            raise PermissionError

    def _deadline_has_changed(
            self,
            task: TaskEntityProtocol,
            new_deadline: str
        ) -> bool:
        return not str(task.deadline) == new_deadline

    def _update_deadline(
            self,
            task: TaskEntityProtocol,
            new_deadline: str
        ) -> None:
        task.deadline = new_deadline
        self._task_repository.save_task(task)

