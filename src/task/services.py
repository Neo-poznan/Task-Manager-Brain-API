from abc import ABC, abstractmethod
from typing import Union, NoReturn
from uuid import UUID

from .infrastructure import TaskRepositoryInterface, CategoryRepositoryInterface
from .domain import CategoryEntity, TaskEntity, TaskEntityProtocol, CategoryEntityProtocol


class TaskServiceInterface(ABC):

    @abstractmethod
    def get_ordered_user_tasks(self, user_id: UUID) -> list[TaskEntityProtocol]:
        pass

    @abstractmethod
    def get_user_task_count_by_categories(self, user_id: UUID) -> dict[str, list]:
        pass

    @abstractmethod
    def get_user_statistics_for_today(self, user_id: UUID) -> dict[str, list]:
        pass

    @abstractmethod
    def get_user_tasks_by_deadlines(
            self, 
            user_id: UUID
        ) -> dict[str, list]:
        pass

    @abstractmethod
    def get_user_task_by_id(
            self, 
            task_id: int, 
            user_id: UUID
        ) -> Union[TaskEntityProtocol, NoReturn]:
        pass

    @abstractmethod
    def get_next_task_order(self, user_id: UUID) -> int:
        pass


class DeadlinesUpdateUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self,
            user_id: UUID,
            new_deadlines: dict[str, list]
        ) -> None:
        pass


class TaskOrderUpdateUseCaseInterface(ABC):

    @abstractmethod
    def execute(
            self, 
            user_id: UUID, 
            new_order: list[str]
        ) -> None:
        pass


class CategoryUseCaseInterface(ABC):

    @abstractmethod
    def get(
                self, 
                category_id: int, 
                user_id: UUID
            ) -> Union[CategoryEntityProtocol, NoReturn]:
        pass

    @abstractmethod
    def create(
                self, 
                user_id: UUID, 
                category_data: dict[str, Union[str, int, bool]]
            ) -> CategoryEntityProtocol:
        pass

    @abstractmethod
    def update(
                self, 
                user_id: UUID, 
                category_id: int, 
                category_data: dict[str, Union[str, int, bool]]
            ) -> CategoryEntityProtocol:
        pass


class TaskUseCaseInterface(ABC):

    @abstractmethod
    def get(
            self, 
            task_id: int, 
            user_id: UUID
        ) -> Union[TaskEntityProtocol, NoReturn]:
        pass

    @abstractmethod
    def create(
            self, 
            user_id: UUID, 
            task_data: dict[str, Union[str, int, bool]]
        ) -> TaskEntityProtocol:
        pass

    @abstractmethod
    def update(
            self, 
            user_id: UUID, 
            task_id: int, 
            task_data: dict[str, Union[str, int, bool]]
        ) -> TaskEntityProtocol:
        pass


class CategoryServiceInterface(ABC):
    
    @abstractmethod
    def get_user_category_by_id(
                self, 
                category_id: int, 
                user_id: UUID
            ) -> Union[CategoryEntityProtocol, NoReturn]:
        pass

    @abstractmethod
    def get_ordered_user_categories(
                self, 
                user_id: UUID
            ) -> list[CategoryEntityProtocol]:
        pass


class TaskService(TaskServiceInterface):

    def __init__(
            self, task_repository: TaskRepositoryInterface = None,
            category_repository: CategoryRepositoryInterface = None
        ):
        self._task_repository = task_repository
        self._category_repository = category_repository

    def get_ordered_user_tasks(self, user_id: UUID) -> list[TaskEntityProtocol]:
        return self._task_repository.get_ordered_user_tasks_json(user_id)
    
    def get_user_statistics_for_today(self, user_id: UUID) -> list[TaskEntityProtocol]:
        statistics = {
            'tasks': self._task_repository.get_user_tasks_for_today_json(user_id),
            'categories': self._task_repository.get_count_user_tasks_in_categories_for_today(user_id)
        }
        return statistics

    def get_user_task_count_by_categories(
                self, 
                user_id: UUID
            ) -> dict[str, Union[list[int], list[str]]]:
        task_count_statistics = self._task_repository.get_count_user_tasks_in_categories(user_id)
        return task_count_statistics

    def get_user_tasks_by_deadlines(
                self, 
                user_id: UUID
            ) -> dict[str, list[dict[str, Union[int, str]]]]:
        count_user_tasks_in_categories_by_deadlines = self._task_repository.get_user_tasks_by_deadlines(user_id)
        return count_user_tasks_in_categories_by_deadlines

    def get_user_task_by_id(
                self,
                task_id: int, 
                user_id: UUID
            ) -> Union[TaskEntityProtocol, NoReturn]:
        task = self._task_repository.get_task_by_id(task_id)
        if task.user == user_id:
            return task
        else:
            raise PermissionError

    def get_next_task_order(self, user_id: UUID) -> int:
        return self._task_repository.get_next_task_order(user_id)


class TaskUseCase(TaskUseCaseInterface):

    def __init__(self, task_repository: TaskRepositoryInterface):
        self._task_repository = task_repository  
    
    def get(
            self, 
            task_id: int, 
            user_id: UUID
        ) -> Union[TaskEntityProtocol, NoReturn]:
        task = self._task_repository.get_task_by_id(task_id)
        if task.user_id != user_id:
            raise PermissionError()
        return task.to_dict()
    
    def create(
            self, 
            user_id: UUID, 
            task_data: dict[str, Union[str, int, bool]]
        ) -> TaskEntityProtocol:
        task = TaskEntity.from_dict({**task_data, 'user_id': str(user_id), 'order': self._task_repository.get_next_task_order(user_id)})
        self._task_repository.save_task(task)
    
    def update(
            self, 
            user_id: UUID, 
            task_id: int, 
            task_data: dict[str, Union[str, int, bool]]
        ) -> TaskEntityProtocol:
        task = self._task_repository.get_task_by_id(task_id)
        if task.user_id != user_id:
            raise PermissionError()

        task.name = task_data.get('name')
        task.description = task_data.get('description')
        task.category_id = task_data.get('category')
        task.deadline = task_data.get('deadline')
        task.planned_time = task_data.get('planned_time')

        self._task_repository.save_task(task)
        return task

class TaskOrderUpdateUseCase(TaskOrderUpdateUseCaseInterface):
    def __init__(self, task_repository: TaskRepositoryInterface):
        self._task_repository = task_repository

    def execute(
            self, 
            user_id: UUID, 
            new_order: list[str]
        ) -> None:

        all_tasks_for_update = self._task_repository.get_tasks_bulk(new_order)
        user_tasks = self._task_repository.get_ordered_user_tasks(user_id)

        self._user_tasks_owner(all_tasks_for_update, user_tasks)

        self._task_repository.update_user_tasks_order(user_id, new_order)

    def _user_tasks_owner(
            self, 
            all_tasks_for_update: list[TaskEntityProtocol], 
            user_tasks: list[TaskEntityProtocol]
        ):
        user_tasks_ids = self._get_ids_from_entities(user_tasks)
        for task in all_tasks_for_update:
            if not task.id in user_tasks_ids:
                raise PermissionError()
    
    def _get_ids_from_entities(self, entity_list: list):
        return [entity.id for entity in entity_list]


class DeadlinesUpdateUseCase(DeadlinesUpdateUseCaseInterface):
    def __init__(self, task_repository: TaskRepositoryInterface):
        self._task_repository = task_repository

    def execute(
            self,
            user_id: UUID,
            new_deadlines: dict[str, list[dict[str, Union[int, str]]]]
        ) -> Union[None, NoReturn]:

        for date, tasks in new_deadlines.items():
            for task_json in tasks:
                task = self._task_repository.get_task_by_id(task_json['id'])
                self._user_task_owner(user_id, task)
                if self._deadline_has_changed(task, date):
                    self._update_deadline(task, date)

    def _user_task_owner(
            self,
            user_id: UUID,
            task: TaskEntityProtocol,
        ) -> Union[None, NoReturn]:
        if not task.user_id == user_id:
            raise PermissionError()

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

    
class CategoryUseCase(CategoryUseCaseInterface):
    def __init__(self, category_repository: CategoryRepositoryInterface):
        self._category_repository = category_repository

    def get(
            self, 
            category_id: int, 
            user_id: UUID
        ) -> Union[CategoryEntityProtocol, NoReturn]:
        category = self._category_repository.get_category_by_id(category_id)
        if category.user_id != user_id:
            raise PermissionError
        return category.to_dict(for_form=True)
    
    def create(
            self, 
            user_id: UUID, 
            category_data: dict[str, Union[str, int, bool]]
        ) -> CategoryEntityProtocol:
        category = CategoryEntity.from_dict({**category_data, 'user_id': str(user_id)})
        self._category_repository.save_category(category)
        print(f'Created category: {category}')  # Debug statement
        return category

    def update(
            self, 
            user_id: UUID, 
            category_id: int, 
            category_data: dict[str, Union[str, int, bool]]
        ) -> CategoryEntityProtocol:
        category = self._category_repository.get_category_by_id(category_id)
        if category.user_id != user_id:
            raise PermissionError

        category.name = category_data.get('name')
        category.color = category_data.get('color')
        category.description = category_data.get('description')

        self._category_repository.save_category(category)
        return category


class CategoryService(CategoryServiceInterface):
    def __init__(self, category_repository: CategoryRepositoryInterface):
        self._category_repository = category_repository

    def get_user_category_by_id(
                self, 
                category_id: int, 
                user_id: UUID
            ) -> Union[CategoryEntityProtocol, NoReturn]:
        category = self._category_repository.get_category_by_id(category_id)
        if category.user_id != user_id:
            raise PermissionError
        return category.to_dict(for_form=True)

    def get_ordered_user_categories(self, user_id: UUID) -> list[CategoryEntityProtocol]:
        return self._category_repository.get_ordered_user_categories_json(user_id)  

