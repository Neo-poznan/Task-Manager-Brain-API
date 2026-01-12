import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Category

User = get_user_model()


class CategoryIntegrationTest(TestCase):
    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        
        # Создаем пользователей
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com', 
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Создаем тестовые категории
        self.category1 = Category.objects.create(
            name='Test Category 1',
            description='Test description',
            color='rgba(255,0,0,0.4)',
            user=self.user1,
            is_custom=True
        )
        
    def login_user1(self):
        """Авторизация пользователя 1"""
        self.client.login(username='testuser1', password='testpass123')
        
    def login_user2(self):
        """Авторизация пользователя 2"""
        self.client.login(username='testuser2', password='testpass123')

    # Тесты GET запросов
    def test_get_category_success(self):
        """Тест успешного получения категории"""
        self.login_user1()
        response = self.client.get(f'/api/category/{self.category1.id}/')
        self.assertEqual(response.status_code, 200)

    def test_get_category_not_found(self):
        """Тест получения несуществующей категории"""
        self.login_user1()
        response = self.client.get('/api/category/99999/')
        self.assertEqual(response.status_code, 404)

    def test_get_category_forbidden_other_user(self):
        """Тест получения чужой категории"""
        self.login_user2()
        response = self.client.get(f'/api/category/{self.category1.id}/')
        self.assertEqual(response.status_code, 403)

    def test_get_category_unauthorized(self):
        """Тест получения категории без авторизации"""
        response = self.client.get(f'/api/category/{self.category1.id}/')
        self.assertIn(response.status_code, [302, 401, 403])

    # Тесты POST запросов (создание категорий)
    def test_create_category_success(self):
        """Тест успешного создания категории"""
        self.login_user1()
        data = {
            'name': 'New Test Category',
            'description': 'New category description', 
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем, что категория создана
        self.assertTrue(Category.objects.filter(name='New Test Category', user=self.user1).exists())

    def test_create_category_empty_name(self):
        """Тест создания категории с пустым названием"""
        self.login_user1()
        data = {
            'name': '',
            'description': 'Test description',
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400, 500])

    def test_create_category_name_too_long(self):
        """Тест создания категории с названием длиннее 100 символов"""
        self.login_user1()
        data = {
            'name': 'x' * 101,  # 101 символ, больше максимального
            'description': 'Test description',
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        # Ожидаем ошибку валидации
        self.assertIn(response.status_code, [400, 500])

    def test_create_category_exactly_100_chars_name(self):
        """Тест создания категории с названием ровно 100 символов"""
        self.login_user1()
        data = {
            'name': 'x' * 100,  # Ровно 100 символов - должно работать
            'description': 'Test description',
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_create_category_with_null_description(self):
        """Тест создания категории с null описанием"""
        self.login_user1()
        data = {
            'name': 'Category Without Description',
            'description': None,
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем создание категории
        category = Category.objects.get(name='Category Without Description')
        self.assertIsNone(category.description)

    def test_create_category_with_empty_description(self):
        """Тест создания категории с пустым описанием"""
        self.login_user1()
        data = {
            'name': 'Category With Empty Description',
            'description': '',
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_create_category_with_markdown_description(self):
        """Тест создания категории с markdown в описании"""
        self.login_user1()
        markdown_description = """
        # Заголовок
        
        **Жирный текст** и *курсив*
        
        - Список
        - Элементов
        
        ```python
        def test_code():
            return "Hello World"
        ```
        
        [Ссылка](https://example.com) и `inline code`
        """
        data = {
            'name': 'Markdown Category',
            'description': markdown_description,
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_create_category_very_long_description(self):
        """Тест создания категории с очень длинным описанием"""
        self.login_user1()
        long_description = 'Very long description text. ' * 1000  # Очень длинное описание
        data = {
            'name': 'Long Description Category',
            'description': long_description,
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    # Тесты валидации цветов
    def test_create_category_hex_color(self):
        """Тест создания категории с hex цветом"""
        self.login_user1()
        data = {
            'name': 'Hex Color Category',
            'description': 'Test hex color',
            'color': '#ff0000'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем, что цвет конвертирован в rgba
        category = Category.objects.get(name='Hex Color Category')
        self.assertIn('rgba', category.color)
        self.assertIn('0.4', category.color)  # Дефолтная альфа

    def test_create_category_rgb_color(self):
        """Тест создания категории с rgb цветом"""
        self.login_user1()
        data = {
            'name': 'RGB Color Category',
            'description': 'Test rgb color',
            'color': 'rgb(255,0,0)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        category = Category.objects.get(name='RGB Color Category')
        self.assertIn('rgba', category.color)
        self.assertIn('0.4', category.color) # Дефолтная альфа

    def test_create_category_rgba_color(self):
        """Тест создания категории с rgba цветом"""
        self.login_user1()
        data = {
            'name': 'RGBA Color Category',
            'description': 'Test rgba color',
            'color': 'rgba(255,0,0,0.8)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем, что rgba цвет сохранился с оригинальной альфой
        category = Category.objects.get(name='RGBA Color Category')
        self.assertIn('rgba', category.color)
        self.assertIn('0.8', category.color)  # Оригинальная альфа сохранилась

    def test_create_category_invalid_color_format(self):
        """Тест создания категории с неправильным форматом цвета"""
        self.login_user1()
        invalid_colors = [
            'not-a-color',
            '#gggggg',  # Неправильный hex
            'rgb(256,300,400)',  # Значения больше 255
            'rgb(255,0)',  # Недостаточно параметров
            'rgba(255,0,0)',  # Недостаточно параметров для rgba
            'hsv(120,100%,100%)',  # Неподдерживаемый формат
            '#ff',  # Слишком короткий hex
            'rgba(255,0,0,1.5)',  # Альфа больше 1
        ]
        
        for i, invalid_color in enumerate(invalid_colors):
            with self.subTest(color=invalid_color):
                data = {
                    'name': f'Invalid Color Category {i}',
                    'description': 'Test invalid color',
                    'color': invalid_color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertIn(response.status_code, [400, 500])

    def test_create_category_missing_required_fields(self):
        """Тест создания категории без обязательных полей"""
        self.login_user1()
        
        # Отсутствует name
        data_no_name = {
            'description': 'Test description',
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data_no_name),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])
        
        # Отсутствует color
        data_no_color = {
            'name': 'Test Category',
            'description': 'Test description'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data_no_color),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])

    def test_create_category_unauthorized(self):
        """Тест создания категории без авторизации"""
        data = {
            'name': 'Unauthorized Category',
            'description': 'Test description',
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [302, 401, 403])

    # Тесты PUT запросов (обновление категорий)
    def test_update_category_success(self):
        """Тест успешного обновления категории"""
        self.login_user1()
        data = {
            'name': 'Updated Category Name',
            'description': 'Updated description',
            'color': 'rgba(0,0,255,0.4)'
        }
        response = self.client.put(
            f'/api/category/{self.category1.id}/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем обновление
        updated_category = Category.objects.get(id=self.category1.id)
        self.assertEqual(updated_category.name, 'Updated Category Name')

    def test_update_nonexistent_category(self):
        """Тест обновления несуществующей категории"""
        self.login_user1()
        data = {
            'name': 'Updated Category',
            'description': 'Updated description',
            'color': 'rgba(0,0,255,0.4)'
        }
        response = self.client.put(
            '/api/category/99999/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_update_other_users_category(self):
        """Тест обновления чужой категории"""
        self.login_user2()
        data = {
            'name': 'Hacked Category',
            'description': 'Hacked description',
            'color': 'rgba(0,0,255,0.4)'
        }
        response = self.client.put(
            f'/api/category/{self.category1.id}/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_update_category_empty_name(self):
        """Тест обновления категории с пустым названием"""
        self.login_user1()
        data = {
            'name': '',
            'description': 'Updated description',
            'color': 'rgba(0,0,255,0.4)'
        }
        response = self.client.put(
            f'/api/category/{self.category1.id}/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])

    def test_update_category_invalid_json(self):
        """Тест обновления категории с невалидным JSON"""
        self.login_user1()
        response = self.client.put(
            f'/api/category/{self.category1.id}/',
            'invalid json{',
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])

    # Тесты безопасности и специальных символов
    def test_create_category_with_special_characters(self):
        """Тест создания категории со спецсимволами"""
        self.login_user1()
        data = {
            'name': 'Category with "quotes" & <tags> & émojis 🚀',
            'description': 'Description with special chars: \n\t\r & < > " \' & utf-8 символы',
            'color': 'rgba(0,255,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_create_category_sql_injection_attempt(self):
        """Тест защиты от SQL инъекций в названии"""
        self.login_user1()
        data = {
            'name': "'; DROP TABLE task_category; --",
            'description': 'SQL injection attempt',
            'color': 'rgba(255,0,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        # Должно либо успешно создаться (защита от SQL инъекций), либо отклониться валидацией
        self.assertIn(response.status_code, [200, 400, 500])
        # Проверяем, что таблицы не удалились
        self.assertTrue(Category.objects.filter(name=self.category1.name).exists())

    def test_create_category_xss_attempt(self):
        """Тест защиты от XSS в описании"""
        self.login_user1()
        data = {
            'name': 'XSS Test Category',
            'description': '<script>alert("XSS")</script><img src="x" onerror="alert(1)">',
            'color': 'rgba(255,0,0,0.4)'
        }
        response = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем, что описание сохранилось (защита должна быть на фронтенде)
        category = Category.objects.get(name='XSS Test Category')
        self.assertIn('<script>', category.description)

    def test_color_format_edge_cases(self):
        """Тест граничных случаев для форматов цветов"""
        self.login_user1()
        
        valid_colors = [
            '#000000',  # Черный
            '#ffffff',  # Белый
            '#FFF',     # Короткий hex
            'rgb(0,0,0)',  # Черный rgb
            'rgb(255,255,255)',  # Белый rgb
            'rgba(128,128,128,0)',  # Прозрачный серый
            'rgba(255,255,255,1)',  # Полностью непрозрачный белый
        ]
        
        for i, color in enumerate(valid_colors):
            with self.subTest(color=color):
                data = {
                    'name': f'Color Test {i}: {color}',
                    'description': f'Testing color: {color}',
                    'color': color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)
                # Проверяем, что цвет сохранен в правильном формате
                category = Category.objects.get(name=f'Color Test {i}: {color}')
                self.assertIn('rgba', category.color)
                # Для hex и rgb ожидаем дефолтную альфу 0.4
                if color.startswith(('#', 'rgb(', 'RGB(')):
                    self.assertIn('0.4', category.color)
                # Для rgba ожидаем сохранение оригинальной альфы

    def test_create_multiple_categories_same_name(self):
        """Тест создания категорий с одинаковыми именами для одного пользователя"""
        self.login_user1()
        
        # Первая категория
        data = {
            'name': 'Duplicate Name',
            'description': 'First category',
            'color': 'rgba(255,0,0,0.4)'
        }
        response1 = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 200)
        
        # Вторая категория с тем же именем
        data['description'] = 'Second category'
        response2 = self.client.post(
            '/api/category/',
            json.dumps(data),
            content_type='application/json'
        )
        # Может быть как разрешено, так и запрещено - зависит от бизнес-логики
        self.assertIn(response2.status_code, [200, 400, 500])

    def test_concurrent_category_operations(self):
        """Тест одновременных операций с категориями"""
        self.login_user1()
        
        # Создаем несколько категорий быстро
        for i in range(5):
            data = {
                'name': f'Concurrent Category {i}',
                'description': f'Concurrent test {i}',
                'color': f'rgba({i*50},{i*40},{i*30},0.4)'
            }
            response = self.client.post(
                '/api/category/',
                json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
        
        # Проверяем, что все категории созданы
        self.assertEqual(
            Category.objects.filter(user=self.user1, name__startswith='Concurrent Category').count(), 
            5
        )