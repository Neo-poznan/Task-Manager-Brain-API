from abc import ABC, abstractmethod
from datetime import timedelta
from decimal import Decimal
from typing import Type, Union, NoReturn

from django.utils.connection import ConnectionProxy

from task.domain.entities import TaskEntity

from ..models import History, SharedHistory
from user.models import User
from user.domain.entities import UserEntity
from ..domain.entities import SharedHistoryEntity, HistoryEntity


class HistoryDatabaseRepositoryInterface(ABC):

    @abstractmethod
    def save_task_to_history(
            self, 
            task_id: int, 
            execution_time: timedelta,
            status: str
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
                user_entity: UserEntity
            ) -> list[SharedHistoryEntity]:
        pass

    @abstractmethod
    def delete_shared_history(
                self, 
                history_entity: HistoryEntity
            ) -> None:
        pass

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
    def get_count_user_tasks_in_categories(
                self,
                user: UserEntity
            ) -> list[tuple[int, str]]:
        pass

    @abstractmethod
    def get_common_user_accuracy(
                self, 
                user: UserEntity
            ) -> list[tuple[Decimal]]:
        pass

    @abstractmethod
    def get_user_accuracy_by_categories(
                self, 
                user: UserEntity
            ) -> list[tuple[str, Decimal]]:
        pass

    @abstractmethod
    def get_user_common_success_rate(
                self, 
                user: UserEntity
            ) -> list[tuple[Decimal]]:
        pass

    @abstractmethod
    def get_user_success_rate_by_categories(
                self, 
                user: UserEntity
            ) -> list[tuple[str, Decimal]]:
        pass

    @abstractmethod
    def get_count_user_tasks_by_weekdays(
                self, 
                user: UserEntity
            ) -> list[tuple[str, int]]:
        pass

    @abstractmethod
    def get_common_count_user_successful_planned_tasks(
                self, 
                user: UserEntity
            ) -> list[tuple[int]]:
        pass

    @abstractmethod
    def get_count_user_successful_planned_tasks_by_categories(
            self, 
            user: UserEntity
        ) -> list[tuple[str, int]]:
        pass

    @abstractmethod
    def get_user_history(
                self, 
                user: UserEntity
            ) -> list:
        pass


class HistoryDatabaseRepository(HistoryDatabaseRepositoryInterface):

    def __init__(
                self, 
                history_model: Type[History], 
                shared_history_model: Type[SharedHistory], 
                connection: ConnectionProxy
            ) -> None:
        self._history_model = history_model
        self._shared_history_model = shared_history_model
        self._connection = connection

    def save_task_to_history(
                self, 
                task: TaskEntity, 
                execution_time: timedelta,
                status: str
            ) -> Union[None, NoReturn]:
        history = self._history_model(
            name=task.name,
            category_id=task.category_id,
            user_id=task.user_id,
            planned_time=task.planned_time,
            execution_time=execution_time,
            status=status,
        )
        history.full_clean()
        history.save()

    def save_user_shared_history(
                self, 
                key: str, 
                user: UserEntity, 
                history_statistics: dict, 
                from_date: str, 
                to_date: str
            ) -> None:
        self._shared_history_model.objects.create(
                key=key, 
                user=User.from_domain(user), 
                history_statistics=history_statistics, 
                from_date=from_date, 
                to_date=to_date
            )

    def get_shared_history_by_key(self, key: str) -> SharedHistoryEntity:
        return self._shared_history_model.objects.get(key=key).to_domain()

    def get_user_shared_histories(
                self, 
                user: UserEntity
            ) -> list[SharedHistoryEntity]:
        return self._shared_history_model.objects.filter(
                user=User.from_domain(user)
            ).only('key', 'from_date', 'to_date').to_entity_list()
    
    def delete_shared_history(self, history_entity: HistoryEntity) -> None:
        self._shared_history_model.from_domain(history_entity).delete()

    def get_history_by_id(self, id: int) -> HistoryEntity:
        return self._history_model.objects.get(id=id).to_domain()

    def delete_history(self, history_entity: HistoryEntity) -> None:
        self._history_model.from_domain(history_entity).delete()

    def get_count_user_tasks_in_categories(
                self, 
                user: UserEntity, 
                from_date: str, 
                to_date: str
            ) -> list[tuple[int, str]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT tc.name, tc.color, count(hh.id)
            FROM history_history hh
            JOIN task_category tc
            ON hh.category_id = tc.id
            WHERE hh.user_id = %s AND
            execution_date BETWEEN %s AND %s
            GROUP BY tc.name, tc.color
            ORDER BY count(hh.id);
            ''',
            [user.id, from_date, to_date]
        )
        return cursor.fetchall()
    
    def get_common_user_accuracy(
                self, user: UserEntity, 
                from_date: str,
                to_date: str
            ) -> list[tuple[Decimal]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT
            round(avg(
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
            [user.id, from_date, to_date]
        )
        return cursor.fetchall()

    def get_user_accuracy_by_categories(
                self, 
                user: UserEntity,
                from_date: str, 
                to_date: str
            ) -> list[tuple[str, Decimal]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
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
            ORDER BY accuracy;
            ''',
            [user.id, from_date, to_date]
        )
        return cursor.fetchall()

    def get_user_common_success_rate(
                self,
                user: UserEntity, 
                from_date: str, 
                to_date: str
            ) -> list[tuple[Decimal]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT count(*)-(
                SELECT 
                    count(*) 
                FROM history_history hh2 
                WHERE 
                    hh2.status='FAILED' 
                AND 
                    hh2.user_id = %s 
                AND execution_date BETWEEN %s AND %s) AS successful_tasks,
                (
                SELECT 
                    count(*) 
                FROM 
                    history_history hh3 
                WHERE 
                    hh3.status='FAILED' 
                    AND hh3.user_id = %s 
                    AND execution_date BETWEEN %s AND %s
                ) AS failed_tasks 
            FROM history_history hh
            WHERE hh.user_id = %s AND execution_date BETWEEN %s AND %s;
            ''',
            [user.id, from_date, to_date, user.id, from_date, 
            to_date, user.id, from_date, to_date]
        )
        return cursor.fetchall()

    def get_user_success_rate_by_categories(
                self, 
                user: UserEntity, 
                from_date: str, 
                to_date: str
            ) -> list[tuple[str, float]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT
            tc."name", tc.color,
            count(*)-(
                SELECT 
                    count(*) 
                FROM 
                    history_history hh2 
                WHERE 
                    hh2.status='FAILED' 
                    AND hh2.category_id=hh.category_id 
                    AND hh2.user_id = %s AND execution_date BETWEEN %s AND %s
                ) AS successful_tasks
            FROM history_history hh 
            join task_category tc 
            ON hh.category_id = tc.id
            WHERE hh.user_id = %s AND
            execution_date BETWEEN %s AND %s
            GROUP BY category_id, tc."name", tc.color;
            ''',
            [user.id, from_date, to_date, user.id, from_date, to_date]
        )
        return cursor.fetchall()

    def get_count_user_tasks_by_weekdays(
                self, 
                user: UserEntity, 
                from_date: str, 
                to_date: str
            ) -> list[tuple[str, int]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
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
            ORDER BY day_index;
            ''',
            [user.id, from_date, to_date]
        )
        return cursor.fetchall()

    def get_common_count_user_successful_planned_tasks(
                self, 
                user: UserEntity, 
                from_date: str, 
                to_date: str
            ) -> list[tuple[int]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT
                (
                SELECT 
                    count(hh2.id) 
                FROM 
                    history_history hh2 
                WHERE 
                    hh2.user_id = %s AND hh2.planned_time = hh2.execution_time 
                    AND execution_date BETWEEN %s AND %s
                ) AS successful_planning,
            count(hh.id) AS failed_planning
            FROM history_history hh 
            WHERE hh.user_id = %s AND hh.planned_time != hh.execution_time 
            AND execution_date BETWEEN %s AND %s; 
            ''',
            [user.id, from_date, to_date, user.id, from_date, to_date]
        )
        return cursor.fetchall()

    def get_count_user_successful_planned_tasks_by_categories(
                self, user: UserEntity, 
                from_date: str, 
                to_date: str
            ) -> list[tuple[str, int]]:
        cursor = self._connection.cursor()
        cursor.execute(
            '''
            SELECT
            tc."name",
            tc.color,
            count(hh.id) AS successful_planning
            from history_history hh 
            JOIN task_category tc 
            ON tc.id = hh.category_id 
            WHERE hh.user_id = %s AND hh.planned_time = hh.execution_time 
            AND execution_date BETWEEN %s AND %s
            GROUP BY hh.category_id, tc."name", tc.color;
            ''',
            [user.id, from_date, to_date]
        )
        return cursor.fetchall()

    def get_user_history(
                self, 
                user: UserEntity, 
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
            [user.id, from_date, to_date]
        )
        return [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

