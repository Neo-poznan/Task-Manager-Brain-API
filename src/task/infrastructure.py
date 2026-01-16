from abc import ABC, abstractmethod
from typing import Union, Type
from uuid import UUID

from django.utils.connection import ConnectionProxy

from .models import Category, Task
from .domain import TaskEntity, CategoryEntity


class TaskRepositoryInterface(ABC):
    @abstractmethod
    def get_ordered_user_tasks_json(self, user_id: UUID) -> list[dict[str, Union[str, int]]]:
        pass

    @abstractmethod
    def get_ordered_user_tasks(self, user_id: UUID) -> list[TaskEntity]:
        pass

    @abstractmethod
    def get_task_by_id(self, task_id: int) -> TaskEntity:
        pass

    @abstractmethod
    def get_count_user_tasks_in_categories(
                self, 
                user_id: UUID
            ) -> dict[str, Union[list[int], list[str]]]:
            pass

    @abstractmethod
    def get_user_tasks_by_deadlines(
                self, 
                user_id: UUID
            ) -> dict[str, list[dict[str, Union[str, int]]]]:
        pass

    @abstractmethod
    def save_task(self, task_entity: TaskEntity) -> None:
        pass

    @abstractmethod
    def get_next_task_order(self, user_id: UUID) -> int:
        pass

    @abstractmethod
    def update_user_tasks_order(self, user_id: UUID, new_order: list[str]) -> None:
        pass

    @abstractmethod
    def get_count_user_tasks_in_categories_for_today(self, user_id: UUID) -> list[dict[str, Union[str, int]]]:
        pass

    @abstractmethod
    def get_user_tasks_for_today_json(self, user_id: UUID) -> list[dict[str, Union[str, int]]]:
        pass

    @abstractmethod
    def delete_task(self, task: TaskEntity) -> None:
        pass

    @abstractmethod
    def get_tasks_bulk(self, task_ids: list[int]) -> list[TaskEntity]:
        pass


class CategoryRepositoryInterface(ABC):
    @abstractmethod
    def get_category_by_id(self, category_id: int) -> CategoryEntity:
        pass   

    @abstractmethod
    def get_ordered_user_categories_json(
                self, 
                user_id: UUID
            ) -> list[dict[str, Union[str, int]]]:
        pass

    @abstractmethod
    def delete_category(self, category_entity: CategoryEntity) -> None:
        pass

    @abstractmethod
    def save_category(self, category_entity: CategoryEntity) -> None:
        pass

class TaskRepository(TaskRepositoryInterface):
    def __init__(self, model: Type[Task], connection: ConnectionProxy):
        self._model = model
        self._connection = connection

    def get_ordered_user_tasks_json(self, user_id: UUID) -> list[dict[str, Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT array_agg(
                json_build_object('id', tt.id, 'name', tt.name) ORDER BY "order"
            )
            FROM task_task tt
            WHERE tt.user_id = %s
            GROUP BY tt.user_id;
            ''',
            [user_id]
        )
        rows = cursor.fetchall()
        return rows[0][0] if len(rows) > 0 else []
    
    def get_ordered_user_tasks(self, user_id: UUID) -> list[TaskEntity]:
        return self._model.objects.filter(user_id=user_id).order_by('order').to_entity_list()

    def get_task_by_id(self, task_id: int) -> TaskEntity:
        return self._model.objects.get(id=task_id).to_domain()

    def get_count_user_tasks_in_categories(
                self, user_id: UUID
            ) -> dict[str, Union[list[int], list[str]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT json_build_object(
                'counts', array_agg(task_count), 
                'categories', array_agg(subquery.name), 
                'colors', array_agg(subquery.color)
            )
            FROM (
                SELECT 
                    tc.name,
                    tc.color,
                    count(tt.id) AS task_count
                FROM task_task tt
                JOIN task_category tc
                ON tt.category_id = tc.id
                WHERE tt.user_id = %s
                GROUP BY tc.id
            ) subquery;
            ''', 
            [user_id]
        )
        return cursor.fetchall()[0][0]

    def get_user_tasks_by_deadlines(
            self, 
            user_id: UUID
        ) -> dict[str, list[dict[str, Union[str, int]]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT json_object_agg(subquery.deadline, subquery.tasks) 
            FROM
            (
                SELECT tt.deadline AS deadline, array_agg(
                    json_build_object('id', tt.id, 'name', tt.name, 'color', tc.color)
                ) AS tasks 
                FROM task_task tt 
                JOIN task_category tc ON tc.id = tt.category_id 
                WHERE tt.user_id = %s AND tt.deadline IS NOT NULL
                GROUP BY tt.deadline
            ) AS subquery;
            ''',
            [user_id]
        )
        return cursor.fetchall()[0][0]

    def save_task(self, task_entity: TaskEntity) -> None:
        task = Task.from_domain(task_entity)
        task.clean_fields(exclude=['id'])
        task.save()

    def update_user_tasks_order(self, user_id: UUID, new_order: list[str]) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            WITH order_cte AS (
                SELECT order_array.id, order_array.new_order FROM
                unnest(%s::int[]) WITH ordinality AS order_array(id, new_order)
            )
            UPDATE task_task tt
            SET "order" = order_cte.new_order
            FROM order_cte
            WHERE tt.id = order_cte.id AND tt.user_id = %s;
            ''',
            [new_order, user_id]
        )

    def get_next_task_order(self, user_id: UUID) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT coalesce(max(tt.order) + 1, 1)
            FROM task_task tt
            where tt.user_id = %s;
            ''',
            [user_id]
        )
        return cursor.fetchall()[0][0]
    
    def get_count_user_tasks_in_categories_for_today(self, user_id: UUID) -> list[dict[str, Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT coalesce(array_agg(
                category_stats
            ), '{}') FROM (
                SELECT 
                json_build_object('id', tc.id, 'name', tc.name, 'color', tc.color, 'taskCount', count(tt.id)) AS category_stats
                FROM task_task tt
                JOIN task_category tc
                ON tt.category_id = tc.id
                WHERE tt.user_id = %s AND tt.deadline = CURRENT_DATE
                GROUP BY tc.id
            ) AS subquery;
            ''',
            [user_id]
        )
        return cursor.fetchall()[0][0]
    
    def get_user_tasks_for_today_json(self, user_id: UUID) -> list[dict[str, Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT array_agg(
                json_build_object('id', tt.id, 'name', tt.name, 'color', tc.color) ORDER BY "order"
            )
            FROM task_task tt
            JOIN task_category tc ON tc.id = tt.category_id
            WHERE tt.user_id = %s AND tt.deadline = CURRENT_DATE
            GROUP BY tt.user_id;
            ''',
            [user_id]
        )
        rows = cursor.fetchall()
        return rows[0][0] if len(rows) > 0 else []
    
    def delete_task(self, task: TaskEntity) -> None:
        self._model.from_domain(task).delete()

    def get_tasks_bulk(self, task_ids: list[int]) -> list[TaskEntity]:
        return self._model.objects.filter(id__in=task_ids).to_entity_list()


class CategoryRepository(CategoryRepositoryInterface):
    def __init__(self, model: Type[Category], connection: ConnectionProxy):
        self._model = model
        self._connection = connection

    def get_category_by_id(self, category_id: int) -> CategoryEntity:
        return self._model.objects.get(id=category_id).to_domain()

    def get_ordered_user_categories_json(self, user_id: UUID) -> list[dict[str, Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT array_agg(
                json_build_object('id', tc.id, 'name', tc.name, 'is_custom', tc.is_custom, 'color', tc.color) ORDER BY "is_custom"
            )
            FROM task_category tc
            WHERE tc.user_id = %s OR NOT tc.is_custom;
            ''',
            [user_id]
        )
        return cursor.fetchall()[0][0]
    
    def save_category(self, category_entity: CategoryEntity) -> None:
        category = Category.from_domain(category_entity)
        category.clean_fields(exclude=['id'])
        category.save()

    def delete_category(self, category_entity: CategoryEntity) -> None:
        self._model.from_domain(category_entity).delete()

