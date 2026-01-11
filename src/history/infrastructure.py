from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Type, Union, NoReturn

from django.utils.connection import ConnectionProxy

from .models import History, SharedHistory
from .domain import SharedHistoryEntity, HistoryEntity
from .constants.choices import HistoryTaskStatusChoices


class HistoryRepositoryInterface(ABC):

    @abstractmethod
    def get_history_by_id(
            self, 
            id: int
        ) -> HistoryEntity:
        pass

    @abstractmethod
    def delete_history(
            self, 
            history_entity: HistoryEntity
        ) -> None:
        pass

    @abstractmethod
    def get_count_tasks_in_categories(
            self,
            user_id: int
        ) -> dict[str, list[Union[str, int]]]:
        pass

    @abstractmethod
    def get_common_accuracy(
            self, 
            user_id: int
        ) -> tuple[Decimal]:
        pass

    @abstractmethod
    def get_accuracy_by_categories(
            self, 
            user_id: int
        ) -> dict[str, list[Union[str, Decimal]]]:
        pass

    @abstractmethod
    def get_common_success_rate(
            self, 
            user_id: int
        ) -> tuple[Decimal]:
        pass

    @abstractmethod
    def get_success_rate_by_categories(
            self, 
            user_id: int
        ) -> dict[str, list[Union[str, Decimal]]]:
        pass

    @abstractmethod
    def get_count_tasks_by_weekdays(
            self, 
            user_id: int
        ) -> dict[str, list[Union[str, int]]]:
        pass

    @abstractmethod
    def get_common_successful_planning_rate(
            self, 
            user_id: int
        ) -> tuple[int]:
        pass

    @abstractmethod
    def get_count_successful_planned_tasks_by_categories(
            self, 
            user_id: int
        ) -> dict[str, list[Union[str, int]]]:
        pass

    @abstractmethod
    def get_history(
            self, 
            user_id: int
        ) -> list:
        pass

    @abstractmethod
    def get_count_user_tasks_in_categories_for_today(
            self, 
            user_id: int
        ) -> list[dict[str, Union[str, int]]]:
        pass

    @abstractmethod
    def get_user_tasks_for_today_json(
            self, 
            user_id: int
        ) -> list[dict[str, Union[str, int]]]:
        pass

    @abstractmethod
    def save_history(
            self, 
            history_task_entity: HistoryEntity, 
        ) -> Union[None, NoReturn]:
        pass


class SharedHistoryRepositoryInterface(ABC):

    @abstractmethod
    def save_history(
            self, 
            history_task_entity: HistoryEntity, 
        ) -> Union[None, NoReturn]:
        pass

    @abstractmethod
    def save_user_shared_history(
            self, key: str, 
            history_statistics: dict
        ) -> None:
        pass

    @abstractmethod
    def get_shared_history_by_key(
            self, 
            key: str
        ) -> SharedHistoryEntity:
        pass

    @abstractmethod
    def get_user_shared_histories(
            self,
            user_id: int
        ) -> list[SharedHistoryEntity]:
        pass

    @abstractmethod
    def delete_shared_history(
            self, 
            history_entity: HistoryEntity
        ) -> None:
        pass


class HistoryRepository(HistoryRepositoryInterface):

    def __init__(
            self, 
            history_model: Type[History], 
            connection: ConnectionProxy
        ) -> None:
        self._history_model = history_model
        self._connection = connection

    def save_history(
            self, 
            history_task_entity: HistoryEntity, 
        ) -> Union[None, NoReturn]:
        history_task = self._history_model.from_domain(history_task_entity)
        history_task.full_clean()
        history_task.save()

    def get_history_by_id(self, id: int) -> HistoryEntity:
        return self._history_model.objects.get(id=id).to_domain()

    def delete_history(self, history_entity: HistoryEntity) -> None:
        self._history_model.from_domain(history_entity).delete()

    def get_count_tasks_in_categories(
            self, 
            user_id: int, 
            from_date: str, 
            to_date: str
        ) ->dict[str, list[Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT json_build_object(
                'labels', array_agg(subquery.name), 
                'colors', array_agg(subquery.color), 
                'data', array_agg(subquery.task_count)
            )
            FROM (
                SELECT tc.name, tc.color, count(hh.id) AS task_count
                FROM history_history hh
                JOIN task_category tc
                ON hh.category_id = tc.id
                WHERE hh.user_id = %s AND
                execution_date BETWEEN %s AND %s
                GROUP BY tc.name, tc.color
                ORDER BY count(hh.id)
            ) AS subquery;
            ''',
            [user_id, from_date, to_date]
        )
        return cursor.fetchall()[0][0]
    
    def get_common_accuracy(
            self, user_id: int, 
            from_date: str,
            to_date: str
        ) -> tuple[Decimal]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT round(avg(
            CASE 
                WHEN extract(epoch FROM planned_time) = 0 
                    OR extract(epoch FROM execution_time) = 0
                    THEN 0
                WHEN planned_time < execution_time 
                    THEN (extract(epoch FROM planned_time) /
                    extract(epoch FROM execution_time)) * 100
                WHEN planned_time > execution_time 
                    THEN (extract(epoch FROM execution_time) / 
                    extract(epoch FROM planned_time)) * 100
                WHEN planned_time = execution_time 
                    THEN 100
            END), 2) AS accuracy
            FROM history_history
            WHERE user_id = %s
            AND
            execution_date BETWEEN %s AND %s;
            ''',
            [user_id, from_date, to_date]
        )
        return cursor.fetchall()[0][0]

    def get_accuracy_by_categories(
            self, 
            user_id: int,
            from_date: str, 
            to_date: str
        ) -> dict[str, list[Union[str, Decimal]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT json_build_object(
                'labels', array_agg(subquery.name), 
                'colors', array_agg(subquery.color), 
                'data', array_agg(subquery.accuracy)
            )
            FROM (
                SELECT
                tc.name, tc.color,
                round(avg(
                CASE 
                    WHEN extract(epoch FROM planned_time) = 0 
                        OR extract(epoch FROM execution_time) = 0 
                        THEN 0
                    WHEN planned_time < execution_time 
                        THEN (extract(epoch FROM planned_time) / 
                        extract(epoch FROM execution_time)) * 100
                    WHEN planned_time > execution_time 
                        THEN (extract(epoch FROM execution_time) 
                        / extract(epoch FROM planned_time)) * 100
                    WHEN planned_time = execution_time 
                        THEN 100
                END), 2) AS accuracy
                FROM history_history hh
                JOIN task_category tc
                ON hh.category_id = tc.id
                WHERE hh.user_id = %s AND
                execution_date BETWEEN %s AND %s
                GROUP BY category_id, tc."name", tc.color
                ORDER BY accuracy
            ) AS subquery;
            ''',
            [user_id, from_date, to_date]
        )
        return cursor.fetchall()[0][0]

    def get_common_success_rate(
            self,
            user_id: int, 
            from_date: str, 
            to_date: str
        ) -> tuple[Decimal]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT count(*)-(
                    SELECT count(*) FROM history_history hh2 
                    WHERE hh2.status=%s
                    AND hh2.user_id = %s 
                    AND execution_date BETWEEN %s AND %s
                ) AS successful_tasks,
                count(*) AS total_tasks
            FROM history_history hh
            WHERE hh.user_id = %s AND execution_date BETWEEN %s AND %s;
            ''',
            [HistoryTaskStatusChoices.FAILED, user_id, from_date, to_date, user_id, from_date, to_date]
        )
        return cursor.fetchall()[0]

    def get_success_rate_by_categories(
            self, 
            user_id: int, 
            from_date: str, 
            to_date: str
        ) -> dict[str, list[Union[str, float]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT json_build_object(
                'labels', array_agg(subquery.name), 
                'colors', array_agg(subquery.color), 
                'data', array_agg(subquery.successful_tasks)
            )
            FROM (
                SELECT
                tc."name", tc.color,
                count(*)-(
                    SELECT 
                        count(*) 
                    FROM 
                        history_history hh2 
                    WHERE 
                        hh2.status= %s
                        AND hh2.category_id=hh.category_id 
                        AND hh2.user_id = %s AND execution_date BETWEEN %s AND %s
                    ) AS successful_tasks
                FROM history_history hh 
                join task_category tc 
                ON hh.category_id = tc.id
                WHERE hh.user_id = %s AND
                execution_date BETWEEN %s AND %s
                GROUP BY category_id, tc."name", tc.color
            ) AS subquery;
            ''',
            [HistoryTaskStatusChoices.FAILED, user_id, from_date, to_date, user_id, from_date, to_date]
        )
        return cursor.fetchall()[0][0]

    def get_count_tasks_by_weekdays(
            self, 
            user_id: int, 
            from_date: str, 
            to_date: str
        ) -> dict[str, list[Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT json_build_object(
                'labels', array_agg(day_name), 
                'data', array_agg(task_count)
            )
            FROM (
                SELECT day_name, count(hh.id) AS task_count FROM (VALUES
                    (1, 'Понедельник'),
                    (2, 'Вторник'),
                    (3, 'Среда'),
                    (4, 'Четверг'),
                    (5, 'Пятница'),
                    (6, 'Суббота'),
                    (7, 'Воскресенье')
                ) weekdays(day_index, day_name)
                LEFT join
                    history_history hh 
                ON 
                    day_index=extract(isodow FROM hh.execution_date)
                WHERE hh.user_id = %s AND
                execution_date BETWEEN %s AND %s
                GROUP BY day_index, day_name
                ORDER BY day_index) AS subquery;
            ''',
            [user_id, from_date, to_date]
        )
        return cursor.fetchall()[0][0]

    def get_common_successful_planning_rate(
            self,
            user_id: int,
            from_date: str,
            to_date: str
        ) -> tuple[int]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT (
                SELECT count(hh2.id) 
                FROM history_history hh2 
                WHERE hh2.user_id = %s AND hh2.planned_time = hh2.execution_time 
                AND execution_date BETWEEN %s AND %s
            ) AS successfully_planned,
            count(hh.id) AS total_planned
            FROM history_history hh 
            WHERE hh.user_id = %s AND execution_date BETWEEN %s AND %s; 
            ''',
            [user_id, from_date, to_date, user_id, from_date, to_date]
        )
        return cursor.fetchall()[0]

    def get_count_successful_planned_tasks_by_categories(
            self, user_id: int, 
            from_date: str, 
            to_date: str
        ) -> dict[str, list[Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT json_build_object(
                'labels', array_agg(subquery.name), 
                'colors', array_agg(subquery.color), 
                'data', array_agg(subquery.successful_planning)
            )
            FROM (
                SELECT
                tc."name",
                tc.color,
                count(hh.id) AS successful_planning
                from history_history hh 
                JOIN task_category tc 
                ON tc.id = hh.category_id 
                WHERE hh.user_id = %s AND hh.planned_time = hh.execution_time 
                AND execution_date BETWEEN %s AND %s
                GROUP BY hh.category_id, tc."name", tc.color
            ) AS subquery;
            ''',
            [user_id, from_date, to_date]
        )
        return cursor.fetchall()[0][0]

    def get_history(
            self, 
            user_id: int, 
            from_date: str, 
            to_date: str
        ) -> list:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT hh.id, hh.name
            FROM history_history hh
            WHERE hh.user_id = %s AND
            execution_date BETWEEN %s AND %s
            ORDER BY hh.execution_date DESC;
            ''',
            [user_id, from_date, to_date]
        )
        return [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    
    def get_count_user_tasks_in_categories_for_today(self, user_id: int) -> list[dict[str, Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT  coalesce(array_agg(
                category_stats
            ), '{}') FROM (
                SELECT 
                json_build_object('id', tc.id, 'name', tc.name, 'color', tc.color, 'taskCount', count(hh.id)) AS category_stats
                FROM history_history hh
                JOIN task_category tc
                ON hh.category_id = tc.id
                WHERE hh.user_id = %s AND hh.execution_date = CURRENT_DATE
                AND hh.status = %s
                GROUP BY tc.id
            ) AS subquery;
            ''',
            [user_id, HistoryTaskStatusChoices.SUCCESSFUL]
        )
        return cursor.fetchall()[0][0]
    
    def get_user_tasks_for_today_json(self, user_id: int) -> list[dict[str, Union[str, int]]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT array_agg(
                json_build_object('id', hh.id, 'name', hh.name, 'color', tc.color)
            )
            FROM history_history hh
            JOIN task_category tc ON tc.id = hh.category_id
            WHERE hh.user_id = %s AND hh.execution_date = CURRENT_DATE
            AND hh.status = %s
            GROUP BY hh.user_id;
            ''',
            [user_id, HistoryTaskStatusChoices.SUCCESSFUL]
        )
        rows = cursor.fetchall()
        return rows[0][0] if len(rows) > 0 else []

class SharedHistoryRepository(SharedHistoryRepositoryInterface):

    def __init__(
            self, 
            shared_history_model: Type[SharedHistory], 
            connection: ConnectionProxy
        ) -> None:
        self._shared_history_model = shared_history_model
        self._connection = connection

    def save_history(
            self, 
            history_task_entity: HistoryEntity, 
        ) -> Union[None, NoReturn]:
        history_task = self._history_model.from_domain(history_task_entity)
        history_task.full_clean()
        history_task.save()

    def save_user_shared_history(
            self, 
            key: str, 
            user_id: int, 
            history_statistics: dict, 
            from_date: str, 
            to_date: str
        ) -> None:
        self._shared_history_model.objects.create(
                key=key, 
                user_id=user_id,
                history_statistics=history_statistics, 
                from_date=from_date, 
                to_date=to_date
            )

    def get_shared_history_by_key(self, key: str) -> SharedHistoryEntity:
        return self._shared_history_model.objects.get(key=key).to_domain()

    def get_user_shared_histories(
                self, 
                user_id: int
            ) -> list[SharedHistoryEntity]:
        return self._shared_history_model.objects.filter(
                user_id=user_id
            ).only('key', 'from_date', 'to_date').to_entity_list()
    
    def delete_shared_history(self, history_entity: HistoryEntity) -> None:
        self._shared_history_model.from_domain(history_entity).delete()

