from django.test import TestCase
import json
from datetime import timedelta
from pprint import pprint
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import connection

from .models import Category
from history.models import SharedHistory, History


class HistoryTest(TestCase):

    def test_history(self):
        user = self._setUp()
        self.client.force_login(user)

        self._insert_history()

        from_date = '2025-02-01'
        to_date = '2025-07-13'

        print(self._calculate_history_accuracy())
        print(self._calculate_history_accuracy())
        print(self._calculate_history_accuracy())
        print(self._calculate_history_accuracy())

        get_history_response = self._get_history(from_date, to_date)
        self.assertEqual(get_history_response.status_code, 200)

        pprint(get_history_response.context[0])

        history_response_context = get_history_response.context

        self.assertEqual(json.loads(history_response_context['common_user_accuracy'])['data'][0], self._calculate_history_accuracy())

    def _setUp(self):
        user = get_user_model().objects.create(
            username= 'test_user',
            email='user123@example.com',

            password='test_password',
        )
        user.save()
        return user


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
            1 as user_id
            from generate_series(1, 20); 
            ''', [category_id]
        )   

    def _insert_history(self):
        cursor = connection.cursor()
        cursor.execute(
        '''
        INSERT INTO history_history(name, planned_time, execution_time, execution_date, status, category_id, user_id) 
        select
        'task_name_' || substring(md5(random()::text) || md5(random()::text) from 1 for (floor(random() * 46)::int + 5)) as name, 
        DATE_TRUNC('minutes', interval '6 hours' * random(0.75, 0.95)) as planned_time, 
        DATE_TRUNC('minutes', interval '6 hours' * random(0.75, 0.95)) as execution_time, 
        (timestamp '2025-01-01' + random() * (timestamp '2025-12-31' - timestamp '2025-01-01'))::date as execution_date, 
        'SUCCESS' as status, 
        floor(random() * (1-10+1) + 10)::int as category_id,
        1 as user_id 
        from generate_series(1, 100); 
        '''
        )


    def _get_history(self, from_date: str, to_date: str):
        response = self.client.get(f'/history/?from_date={from_date}&to_date={to_date}')
        return response
    
    def _share_history(self, from_date: str, to_date: str):
        response = self.client.post(f'/history/share/?from_date={from_date}&to_date={to_date}')
        return response     
    
    def _get_shared_history(self, key: str):
        response = self.client.get(f'/history/share/?key={key}')
        return response
    
    def _get_shared_histories(self):
        response = self.client.get(f'/history/my-shared-histories/')
        return response      

    def _delete_shared_history(self, key: str):
        response = self.client.delete(f'/history/delete-shared-history/{key}/')
        return response

    def _calculate_history_accuracy(self):
        tasks = History.objects.filter(execution_date__range=('2025-02-01', '2025-07-13')).order_by('-execution_date')
        print(len(tasks))
        print(tasks)
        tasks_accuracy = []
        for task in tasks:
            tasks_accuracy.append(self._calculate_task_accuracy(task))
        avg_history_accuracy = Decimal(sum(tasks_accuracy)) / Decimal(len(tasks_accuracy))
        return float(round(avg_history_accuracy, 2))

    def _calculate_category_accuracy(self, category_name: str):
        tasks_accuracy = []
        category_id = Category.objects.get(name=category_name)
        for task in History.objects.filter(category_id=category_id):
            tasks_accuracy.append(self._calculate_task_accuracy(task))
        avg_category_accuracy = Decimal(sum(tasks_accuracy)) / Decimal(len(tasks_accuracy))
        return float(round(avg_category_accuracy, 2))

    def _calculate_task_accuracy(self, task: History):
        if task.planned_time.total_seconds() / 60 == 0 or task.execution_time.total_seconds() / 60 == 0:
            return 0
        elif task.planned_time < task.execution_time:
            return Decimal(task.planned_time.total_seconds() // 60) / Decimal(task.execution_time.total_seconds() // 60) * Decimal(100)
        elif task.planned_time > task.execution_time:
            return Decimal(task.execution_time.total_seconds() // 60) / Decimal(task.planned_time.total_seconds() // 60) * Decimal(100)
        elif task.planned_time == task.execution_time:
            return Decimal(100)

    def _clear_database(self):
        print('clear history database')
        cursor = connection.cursor()
        cursor.execute(
        '''
        DELETE FROM history_history;
        '''            
        )

