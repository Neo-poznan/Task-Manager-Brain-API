from abc import ABC, abstractmethod
from typing import Union, Type

from django.utils.connection import ConnectionProxy

from ..models import Category, Task
from user.models import User
from user.domain.entities import UserEntity
from ..domain.entities import TaskEntity, CategoryEntity


class TaskDatabaseRepositoryInterface(ABC):
    @abstractmethod
    def get_ordered_user_tasks_json(self, user: UserEntity) -> list[dict[str, Union[str, int]]]:
        pass

    @abstractmethod
    def get_ordered_user_tasks(self, user: UserEntity) -> list[TaskEntity]:
        pass

    @abstractmethod
    def get_task_by_id(self, task_id: int) -> TaskEntity:
        pass

    @abstractmethod
    def get_count_user_tasks_in_categories(
                self, 
                user: UserEntity
            ) -> dict[str, Union[list[int], list[str]]]:
            pass

    @abstractmethod
    def get_count_user_tasks_in_categories_by_deadlines(
                self, 
                user: UserEntity
            ) -> dict[str, list[dict[str, Union[str, int]]]]:
        pass

    @abstractmethod
    def save_task(self, task: TaskEntity) -> None:
        pass

    @abstractmethod
    def get_next_task_order(self, user: UserEntity) -> int:
        pass

    @abstractmethod
    def update_user_task_order(self, user: UserEntity, new_order: list[str]) -> None:
        pass


class CategoryDatabaseRepositoryInterface(ABC):
    @abstractmethod
    def get_category_by_id(self, category_id: int) -> CategoryEntity:
        pass   

    @abstractmethod
    def get_ordered_user_categories_json(
                self, 
                user: UserEntity
            ) -> list[dict[str, Union[str, int]]]:
        pass

    @abstractmethod
    def delete_category(self, category_entity: CategoryEntity) -> None:
        pass


class TaskDatabaseRepository(TaskDatabaseRepositoryInterface):
    def __init__(self, model: Type[Task], connection: ConnectionProxy):
        self._model = model
        self._connection = connection

    def get_ordered_user_tasks_json(self, user: UserEntity) -> list[dict[str, Union[str, int]]]:
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
            [user.id]
        )
        rows = cursor.fetchall()
        return rows[0][0] if len(rows) > 0 else []
    
    def get_ordered_user_tasks(self, user: UserEntity) -> list[TaskEntity]:
        return self._model.objects.filter(user_id=user.id).order_by('order').to_entity_list()

    def get_task_by_id(self, task_id: int) -> TaskEntity:
        return self._model.objects.get(id=task_id).to_domain()

    def get_count_user_tasks_in_categories(
                self, user: UserEntity
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
            [user.id]
        )
        return cursor.fetchall()[0][0]

    def get_count_user_tasks_in_categories_by_deadlines(
                self, 
                user: UserEntity
            ) -> dict[str, list[dict[str, Union[str, int]]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT json_object_agg(deadline_date, tasks_count_by_category_by_date)
            FROM 
            (
                SELECT to_char(task_deadline, 'YYYY-MM-DD') AS deadline_date, json_agg(json_build_object(
                    'count', task_count, 'category', category_name, 'color', color
                )) AS tasks_count_by_category_by_date
                FROM 
                (
                    SELECT count(tt.id) AS task_count, tt.deadline AS task_deadline,
                    tc.name AS category_name,  tc.color AS color
                    FROM task_task tt join task_category tc on tt.category_id = tc.id 
                    WHERE tt.user_id = %s AND tt.deadline IS NOT NULL
                    GROUP BY tt.deadline, tc.id, tc.name, tc.color
                )
                GROUP BY task_deadline
            );
            ''',
            [user.id]
        )
        return cursor.fetchall()[0][0]

    def save_task(self, task: TaskEntity) -> None:
        Task.from_domain(task).save()

    def update_user_task_order(self, user: UserEntity, new_order: list[str]) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            WITH order_cte AS (
                select order_array.id, order_array.new_order from
                unnest(%s::int[]) with ordinality as order_array(id, new_order)
            )
            UPDATE task_task tt
            SET "order" = order_cte.new_order
            FROM order_cte
            WHERE tt.id = order_cte.id AND tt.user_id = %s;
            ''',
            [new_order, user.id]
        )

    def get_next_task_order(self, user: UserEntity) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT coalesce(max(tt.order) + 1, 1)
            FROM task_task tt
            where tt.user_id = %s;
            ''',
            [user.id]
        )
        return cursor.fetchall()[0][0]


class CategoryDatabaseRepository(CategoryDatabaseRepositoryInterface):
    def __init__(self, model: Type[Category], connection: ConnectionProxy):
        self._model = model
        self._connection = connection

    def get_category_by_id(self, category_id: int) -> CategoryEntity:
        return self._model.objects.get(id=category_id).to_domain()

    def get_ordered_user_categories_json(self, user: UserEntity) -> list[dict[str, Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT array_agg(
                json_build_object('id', tc.id, 'name', tc.name, 'is_custom', tc.is_custom, 'color', tc.color) ORDER BY "is_custom"
            )
            FROM task_category tc
            WHERE tc.user_id = %s OR NOT tc.is_custom;
            ''',
            [user.id]
        )
        return cursor.fetchall()[0][0]

    def delete_category(self, category_entity: CategoryEntity) -> None:
        self._model.from_domain(category_entity).delete()

