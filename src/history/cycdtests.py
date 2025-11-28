import json
from pprint import pprint

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import connection

from history.models import History
from task.models import Category, Task


class HistoryTest(TestCase):


    def test_history(self):
        user = self._setUp()
        self.client.force_login(user)

        self._insert_only_perfect_history(user)

        from_date = '2025-01-01'
        to_date = '2025-12-31'

        get_history_response = self._get_history(from_date, to_date)
        self.assertEqual(get_history_response.status_code, 200)

        body = json.loads(get_history_response.content)
        self.assertEqual(body['common_count_user_successful_planned_tasks']['data'], [90, 0])
        self.assertEqual(body['common_user_accuracy']['data'], [100.0, 0.0])
        self.assertEqual(body['common_user_success_rate']['data'], [90, 0])
        self.assertEqual(body['user_accuracy_by_categories']['data'], [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0])

        self._insert_20_tasks_in_every_category(user)

        get_history_response_2 = self._get_history(from_date, to_date)
        self.assertEqual(get_history_response_2.status_code, 200)

        body_2 = json.loads(get_history_response_2.content)

        self.assertEqual(body_2['common_count_user_successful_planned_tasks']['data'], [90, 180])
        self.assertEqual(body_2['common_user_success_rate']['data'], [270, 0])

        raw_accuracy_by_categories = body_2['user_accuracy_by_categories']
        accuracy_by_categories = {category: count for category, count in zip(raw_accuracy_by_categories['labels'], raw_accuracy_by_categories['data'])}

        for category_name in accuracy_by_categories.keys():
            self.assertEqual(accuracy_by_categories[category_name], self._calculate_category_accuracy(category_name))

        self.assertEqual(body_2['common_user_accuracy']['data'][0], self._calculate_history_accuracy())

        pprint(body_2)

        self._insert_tasks(user)

        deadlines_response = self._get_deadlines()
        self.assertEqual(deadlines_response.status_code, 200)

        pprint(json.loads(deadlines_response.content))

        self._clear_database()

    def _setUp(self):
        user = get_user_model().objects.create(
                username= 'test_user',
                email='user123@example.com',
                password='test_password',
            )
        user.save()
        return user

    def _insert_only_perfect_history(self, user):
        cursor = connection.cursor()     
        cursor.execute(
        '''
        INSERT INTO history_history(name, planned_time, execution_time, execution_date, status, category_id, user_id) 
        select  
        'task_name_' || substring(md5(random()::text) || md5(random()::text) from 1 for (floor(random() * 46)::int + 5)) as name, 
        '2 hours'::interval as planned_time, 
        '2 hours'::interval as execution_time, 
        (timestamp '2025-01-01' + random() * (timestamp '2025-12-31' - timestamp '2025-01-01'))::date as execution_date,
        'SUCCESS' as status,
        floor(random() * (0-10+1) + 10)::int as category_id,
        %s as user_id
        from generate_series(1, 9) AS category_id
        CROSS JOIN generate_series(1, 10) AS gs; 
        ''', [user.id]
        )

    def _insert_20_tasks_in_every_category(self, user):
        cursor = connection.cursor()
        categories_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        for category_id in categories_ids:
            cursor.execute(
            '''
            INSERT INTO history_history(name, planned_time, execution_time, execution_date, status, category_id, user_id) 
            select  
            'task_name_' || substring(md5(random()::text) || md5(random()::text) from 1 for (floor(random() * 46)::int + 5)) as name, 
            '2 hours'::interval as planned_time, 
            '2 hours 30 minutes'::interval as execution_time, 
            (timestamp '2025-01-01' + random() * (timestamp '2025-12-31' - timestamp '2025-01-01'))::date as execution_date, 
            'SUCCESS' as status,
            %s as category_id,
            %s as user_id
            from generate_series(1, 20); 
            ''', [category_id, user.id]
        )   

    def _get_history(self, from_date: str, to_date: str):
        response = self.client.get(f'/api/history/?from_date={from_date}&to_date={to_date}')
        return response
    
    def _insert_tasks(self, user):
        cursor = connection.cursor()
        cursor.execute(
            '''
            INSERT INTO task_task(name, deadline, planned_time, category_id, user_id, "order") 
            select  
            'task_name_' || substring(md5(random()::text) || md5(random()::text) from 1 for (floor(random() * 46)::int + 5)) as name, 
            (timestamp '2025-01-01' + random() * (timestamp '2025-12-31' - timestamp '2025-01-01'))::date as deadline, 
            '2 hours'::interval as planned_time, 
            1 as category_id,
            %s as user_id,
            "order"
            from generate_series(1, 5) as "order"; 
            ''', [user.id]
        )
        cursor.execute(
            '''
            INSERT INTO task_task(name, deadline, planned_time, category_id, user_id, "order") 
            select  
            'task_name_' || substring(md5(random()::text) || md5(random()::text) from 1 for (floor(random() * 46)::int + 5)) as name, 
            (timestamp '2025-01-01' + random() * (timestamp '2025-12-31' - timestamp '2025-01-01'))::date as deadline, 
            '2 hours'::interval as planned_time, 
            2 as category_id,
            %s as user_id,
            "order"
            from generate_series(6, 10) as "order"; 
            ''', [user.id]
        )
        cursor.execute(
            '''
            INSERT INTO task_task(name, deadline, planned_time, category_id, user_id, "order") 
            select
            'task_name_' || substring(md5(random()::text) || md5(random()::text) from 1 for (floor(random() * 46)::int + 5)) as name, 
            (timestamp '2025-01-01' + random() * (timestamp '2025-12-31' - timestamp '2025-01-01'))::date as deadline, 
            '2 hours'::interval as planned_time, 
            3 as category_id,
            %s as user_id,
            "order"
            from generate_series(11, 15) as "order"; 
            ''', [user.id]
        )
    
    def _get_deadlines(self):
        response = self.client.get('/api/deadlines/')
        return response

    def _calculate_history_accuracy(self):
        tasks = History.objects.all()
        tasks_accuracy = []
        for task in tasks:
            tasks_accuracy.append(self._calculate_task_accuracy(task))
        avg_history_accuracy = sum(tasks_accuracy) / len(tasks_accuracy)
        return round(avg_history_accuracy, 2)

    def _calculate_category_accuracy(self, category_name: str):
        tasks_accuracy = []
        category_id = Category.objects.get(name=category_name)
        for task in History.objects.filter(category_id=category_id):
            tasks_accuracy.append(self._calculate_task_accuracy(task))
        avg_category_accuracy = sum(tasks_accuracy) / len(tasks_accuracy)
        return round(avg_category_accuracy, 2)

    def _calculate_task_accuracy(self, task: History):
        if task.planned_time.total_seconds() / 60 == 0 or task.execution_time.total_seconds() / 60 == 0:
            return None
        elif task.planned_time < task.execution_time:
            return (task.planned_time.total_seconds() / 60) / (task.execution_time.total_seconds() / 60) * 100
        elif task.planned_time > task.execution_time:
            return (task.execution_time.total_seconds() / 60) / (task.planned_time.total_seconds() / 60) * 100
        elif task.planned_time == task.execution_time:
            return 100

    def _clear_database(self):
        print('clear history database')
        cursor = connection.cursor()
        cursor.execute(
        '''
        DELETE FROM history_history;
        '''
        )

