import json
from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Task, Category

User = get_user_model()


class TaskIntegrationTest(TestCase):
    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        
        # Создаем пользователей
        self.user1 = User.objects.create_user(
            username='testuser1', 
            email='test1@example.com',
            password='testpass123',
        )
        self.user2 = User.objects.create_user(
            username='testuser2', 
            email='test2@example.com', 
            password='testpass123',

        )
        
        # Создаем категории
        self.category1 = Category.objects.create(
            name='Test Category 1',
            description='Test description',
            color='rgba(255, 0, 0, 0.4)',
            user=self.user1,
            is_custom=True
        )
        self.category2 = Category.objects.create(
            name='Test Category 2',
            description='Another test description',
            color='rgba(0, 255, 0, 0.5)',
            user=self.user2,
            is_custom=True
        )
        
        # Создаем тестовые задачи
        self.task1 = Task.objects.create(
            name='Test Task 1',
            description='Test description',
            order=1,
            category=self.category1,
            user=self.user1,
            deadline=date.today() + timedelta(days=1),
            planned_time='02:30:00'
        )
        
    def login_user1(self):
        """Авторизация пользователя 1"""
        self.client.login(username='testuser1', password='testpass123')
        
    def login_user2(self):
        """Авторизация пользователя 2"""
        self.client.login(username='testuser2', password='testpass123')

    # Тесты GET запросов
    def test_get_task_success(self):
        """Тест успешного получения задачи"""
        self.login_user1()
        response = self.client.get(f'/api/task/{self.task1.id}/')
        self.assertEqual(response.status_code, 200)

    def test_get_task_not_found(self):
        """Тест получения несуществующей задачи"""
        self.login_user1()
        response = self.client.get('/api/task/99999/')
        self.assertEqual(response.status_code, 404)

    def test_get_task_forbidden_other_user(self):
        """Тест получения чужой задачи"""
        self.login_user2()
        response = self.client.get(f'/api/task/{self.task1.id}/')
        self.assertEqual(response.status_code, 403)

    def test_get_task_unauthorized(self):
        """Тест получения задачи без авторизации"""
        response = self.client.get(f'/api/task/{self.task1.id}/')
        # Проверяем редирект на страницу логина или 401/403
        self.assertIn(response.status_code, [302, 401, 403])

    # Тесты POST запросов (создание задач)
    def test_create_task_success(self):
        """Тест успешного создания задачи"""
        self.login_user1()
        data = {
            'name': 'New Test Task',
            'description': 'New task description',
            'category': self.category1.id,
            'deadline': '2026-01-13',
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем, что задача создана
        self.assertTrue(Task.objects.filter(name='New Test Task', user=self.user1).exists())

    def test_create_task_empty_name(self):
        """Тест создания задачи с пустым названием"""
        self.login_user1()
        data = {
            'name': '',
            'description': 'Test description',
            'category': self.category1.id,
            'deadline': '2026-01-13',
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400])

    def test_create_task_name_too_long(self):
        """Тест создания задачи с названием длиннее 290 символов"""
        self.login_user1()
        data = {
            'name': 'x' * 291,  # 291 символ, больше максимального
            'description': 'Test description',
            'category': self.category1.id,
            'deadline': '2026-01-13',
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400])

    def test_create_task_nonexistent_category(self):
        """Тест создания задачи с несуществующей категорией"""
        self.login_user1()
        data = {
            'name': 'Test Task',
            'description': 'Test description',
            'category': 99999,  # Несуществующая категория
            'deadline': '2026-01-13',
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400, 404])

    def test_create_task_other_users_category(self):
        """Тест создания задачи с категорией другого пользователя"""
        self.login_user1()
        data = {
            'name': 'Test Task',
            'description': 'Test description',
            'category': self.category2.id,  # Категория user2
            'deadline': '2026-01-13',
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку доступа
        self.assertIn(response.status_code, [400, 403])

    def test_create_task_invalid_date_format(self):
        """Тест создания задачи с неправильным форматом даты"""
        self.login_user1()
        data = {
            'name': 'Test Task',
            'description': 'Test description',
            'category': self.category1.id,
            'deadline': '13-01-2026',  # Неправильный формат
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400])

    def test_create_task_invalid_time_format(self):
        """Тест создания задачи с неправильным форматом времени"""
        self.login_user1()
        data = {
            'name': 'Test Task',
            'description': 'Test description',
            'category': self.category1.id,
            'deadline': '2026-01-13',
            'planned_time': '25h:70m:90s'  # Неправильное время
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400])

    def test_create_task_missing_required_fields(self):
        """Тест создания задачи без обязательных полей"""
        self.login_user1()
        data = {
            'name': 'Test Task',
            # Отсутствует planned_time - обязательное поле
            'description': 'Test description',
            'category': self.category1.id,
            'deadline': '2026-01-13'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400])

    def test_create_task_unauthorized(self):
        """Тест создания задачи без авторизации"""
        data = {
            'name': 'Test Task',
            'description': 'Test description',
            'category': self.category1.id,
            'deadline': '2026-01-13',
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем редирект или ошибку авторизации
        self.assertIn(response.status_code, [302, 401, 403])

    # Тесты PUT запросов (обновление задач)
    def test_update_task_success(self):
        """Тест успешного обновления задачи"""
        self.login_user1()
        data = {
            'name': 'Updated Task Name',
            'description': 'Updated description',
            'category': self.category1.id,
            'deadline': '2026-01-14',
            'planned_time': '03:00:00'
        }
        response = self.client.put(
            f'/api/task/{self.task1.id}/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем обновление
        updated_task = Task.objects.get(id=self.task1.id)
        self.assertEqual(updated_task.name, 'Updated Task Name')

    def test_update_nonexistent_task(self):
        """Тест обновления несуществующей задачи"""
        self.login_user1()
        data = {
            'name': 'Updated Task',
            'description': 'Updated description',
            'category': self.category1.id,
            'deadline': '2026-01-14',
            'planned_time': '03:00:00'
        }
        response = self.client.put(
            '/api/task/99999/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_update_other_users_task(self):
        """Тест обновления чужой задачи"""
        self.login_user2()
        data = {
            'name': 'Updated Task Name',
            'description': 'Updated description',
            'category': self.category2.id,
            'deadline': '2026-01-14',
            'planned_time': '03:00:00'
        }
        response = self.client.put(
            f'/api/task/{self.task1.id}/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_update_task_empty_name(self):
        """Тест обновления задачи с пустым названием"""
        self.login_user1()
        data = {
            'name': '',
            'description': 'Updated description',
            'category': self.category1.id,
            'deadline': '2026-01-14',
            'planned_time': '03:00:00'
        }
        response = self.client.put(
            f'/api/task/{self.task1.id}/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400])

    def test_update_task_name_too_long(self):
        """Тест обновления задачи с названием длиннее 290 символов"""
        self.login_user1()
        data = {
            'name': 'x' * 291,
            'description': 'Updated description',
            'category': self.category1.id,
            'deadline': '2026-01-14',
            'planned_time': '03:00:00'
        }
        response = self.client.put(
            f'/api/task/{self.task1.id}/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400])

    def test_update_task_with_immutable_fields(self):
        """Тест обновления задачи с попыткой изменить неизменяемые поля"""
        self.login_user1()
        original_user = self.task1.user
        original_order = self.task1.order
        
        data = {
            'name': 'Updated Task Name',
            'description': 'Updated description',
            'category': self.category1.id,
            'deadline': '2026-01-14',
            'planned_time': '03:00:00',
            # Попытка изменить неизменяемые поля
            'user': str(self.user2.id),
            'order': 999,
            'id': 99999
        }
        response = self.client.put(
            f'/api/task/{self.task1.id}/',
            json.dumps(data),
            content_type='application/json'
        )
        
        # Проверяем, что запрос прошел успешно или с ошибкой валидации
        self.assertIn(response.status_code, [200, 400])
        
        # Проверяем, что неизменяемые поля не изменились
        updated_task = Task.objects.get(id=self.task1.id)
        self.assertEqual(updated_task.user, original_user)
        self.assertEqual(updated_task.order, original_order)
        self.assertEqual(updated_task.id, self.task1.id)

    def test_update_task_invalid_json(self):
        """Тест обновления задачи с невалидным JSON"""
        self.login_user1()
        response = self.client.put(
            f'/api/task/{self.task1.id}/',
            'invalid json{',
            content_type='application/json'
        )
        # Ожидаем ошибку парсинга JSON
        self.assertIn(response.status_code, [400])

    def test_create_task_with_null_deadline(self):
        """Тест создания задачи с null deadline должно работать)"""
        self.login_user1()
        data = {
            'name': 'Task Without Deadline',
            'description': 'Test description',
            'category': self.category1.id,
            'deadline': None,
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем создание задачи
        task = Task.objects.get(name='Task Without Deadline')
        self.assertIsNone(task.deadline)

    def test_create_task_with_null_category(self):
        """Тест создания задачи с null category (не должно работать)"""
        self.login_user1()
        data = {
            'name': 'Task Without Category',
            'description': 'Test description',
            'category': None,
            'deadline': '2026-01-13',
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 404])

    def test_create_task_past_deadline(self):
        """Тест создания задачи с прошедшим deadline"""
        self.login_user1()
        data = {
            'name': 'Task With Past Deadline',
            'description': 'Test description',
            'category': self.category1.id,
            'deadline': '2020-01-01',  # Прошедшая дата
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        # Может быть как успешно, так и с ошибкой - зависит от бизнес-логики
        # Добавляем обе возможности
        self.assertIn(response.status_code, [200, 400])

    def test_create_task_with_special_characters(self):
        """Тест создания задачи со спецсимволами в названии"""
        self.login_user1()
        data = {
            'name': 'Task with "quotes" & <tags> & émojis 🚀',
            'description': 'Test description with special chars',
            'category': self.category1.id,
            'deadline': '2026-01-13',
            'planned_time': '01:30:00'
        }
        response = self.client.post(
            '/api/task/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

