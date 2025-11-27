import json
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model

from task.models import Task, Category
from history.models import History

class TaskTest(TestCase):

    def _setUp(self):
        user = get_user_model().objects.create(
            username= 'test_user',
            email='user123@example.com',

            password='test_password',
        )
        user.save()
        return user
    
    def _category_creation(self, post_data: dict[str, str]):
        response = self.client.post('/create-category/', post_data)
        return response       
    
    def _task_creation(self, post_data: dict[str, str]):
        response = self.client.post('/create-task/', post_data)
        return response
    
    def _task_update(self, post_data: dict[str, str]):
        response = self.client.post('/task/1/', post_data)
        return response
    
    def _category_update(self, post_data: dict[str, str]):
        response = self.client.post('/category/10/', post_data)
        return response
    
    def _task_order_update(self, post_data: dict[str, list[str]]):
        response = self.client.put('/update-order/', post_data)
        return response
    
    def _save_completed_task_to_history(
                self, 
                task_id: int, 
                execution_time: timedelta
            ):
        response = self.client.post(
                f'/complete-task/{task_id}/', 
                {'execution_time': execution_time}
            )
        return response

    def _save_failed_task_to_history(
                self, 
                task_id: int, 
                execution_time: timedelta
            ):
        response = self.client.post(
                f'/fail-task/{task_id}/', 
                {'execution_time': execution_time}
            )
        return response    

    def _delete_category(self, category_id: int):
        response = self.client.delete(f'/delete-category/{category_id}/')
        return response

    def _clear_database(self):
        History.objects.all().delete()
        get_user_model().objects.first().delete()


    def test_task(self):
        user = self._setUp()
        self.client.force_login(user)

        tasks_data = [
            {
                'name': 'test_task',
                'description': 'test_description',
                'category': '1',
                'planned_time': '2:51:10',
                'deadline': '20.08.2025',
            },
            {
                'name': 'test_task1',
                'description': 'test_description1',
                'category': '1',
                'planned_time': '2:51:10',
                'deadline': '20.12.2025',
            },
             {
                'name': 'test_task2',
                'description': 'test_description2',
                'category': '1',
                'planned_time': '2:51:10',
                'deadline': '30.07.2025',
            },
        ]

        task_update_data = {
            'name': 'test_task1',
            'description': 'test_description1',
            'category': '1',
            'planned_time': '2:41:10',
            'deadline': '21.08.2025',            
        }

        category_data = {
            'name': 'test_category',
            'description': 'test_description',
            'color': '#22a3c4',
        }

        category_update_data = {
            'name': 'test_category1',
            'description': 'test_description1',
            'color': "#1bdc31",
        }

        tasks_order = ['2', '1', '3']

        category_creation_response = self._category_creation(category_data)
        self.assertEqual(category_creation_response.status_code, 302)

        task_creation_response = self._task_creation(tasks_data[0])
        self.assertEqual(task_creation_response.status_code, 302)
        self.assertEqual(Task.objects.first().planned_time, timedelta(hours=2, minutes=50))  

        self._task_creation(tasks_data[1])  
        self._task_creation(tasks_data[2])  
        self.assertEqual(len(Task.objects.all()), 3) 

        task_update_response = self._task_update(task_update_data)
        self.assertEqual(task_update_response.status_code, 302) 
        self.assertEqual(Task.objects.first().planned_time, timedelta(hours=2, minutes=40))  

        category_update_response = self._category_update(category_update_data)
        self.assertEqual(category_update_response.status_code, 302)
        self.assertEqual(Category.objects.get(id=10).name, category_update_data['name'])

        order_update_response = self._task_order_update(json.dumps({'order': tasks_order}))
        self.assertEqual(order_update_response.status_code, 200)
        self.assertEqual([order[0] for order in Task.objects.all().order_by('id').values_list('order')], [2, 1, 3])

        task_complete_response = self._save_completed_task_to_history(Task.objects.first().id, '2:30:00')
        self.assertEqual(task_complete_response.status_code, 302)
        self.assertEqual(len(Task.objects.filter(id=1)), 0)
        self.assertEqual(len(History.objects.all()), 1)

        task_complete_response = self._save_completed_task_to_history(Task.objects.get(id=2).id, '2:30:00')
        self.assertEqual(task_complete_response.status_code, 302)
        self.assertEqual(len(Task.objects.filter(id=2)), 0)
        self.assertEqual(len(History.objects.all()), 2)
        self.assertEqual(History.objects.last().status, History.SUCCESSFUL) 

        self._save_completed_task_to_history(Task.objects.get(id=3).id, '2:30:00')
        self.assertEqual(History.objects.last().status, History.OUT_OF_DEADLINE)     

        category_deletion_response = self._delete_category(Category.objects.last().id)
        self.assertEqual(category_deletion_response.status_code, 203)
        self.assertEqual(len(Category.objects.all()), 9)

        self._clear_database()

