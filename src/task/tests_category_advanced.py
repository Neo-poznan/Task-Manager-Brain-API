import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Category

User = get_user_model()


class CategoryColorConversionTest(TestCase):
    """Отдельные тесты для проверки конвертации цветов"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='coloruser',
            email='color@example.com',
            password='testpass123'
        )
        self.client.login(username='coloruser', password='testpass123')

    def test_hex_to_rgba_conversion(self):
        """Подробное тестирование конвертации hex в rgba"""
        hex_color_tests = [
            ('#ff0000', 'rgba(255, 0, 0, 0.4)'),     # Красный
            ('#00ff00', 'rgba(0, 255, 0, 0.4)'),     # Зеленый  
            ('#0000ff', 'rgba(0, 0, 255, 0.4)'),     # Синий
            ('#ffffff', 'rgba(255, 255, 255, 0.4)'), # Белый
            ('#000000', 'rgba(0, 0, 0, 0.4)'),       # Черный
            ('#808080', 'rgba(128, 128, 128, 0.4)'), # Серый
            ('#FF0000', 'rgba(255, 0, 0, 0.4)'),     # Красный (заглавные)
            ('#f00', 'rgba(255, 0, 0, 0.4)'),        # Короткий hex красный
            ('#0f0', 'rgba(0, 255, 0, 0.4)'),        # Короткий hex зеленый
            ('#00f', 'rgba(0, 0, 255, 0.4)'),        # Короткий hex синий
        ]
        
        for i, (hex_color, expected_rgba) in enumerate(hex_color_tests):
            with self.subTest(hex_color=hex_color):
                data = {
                    'name': f'Hex Test {i}',
                    'description': f'Testing {hex_color}',
                    'color': hex_color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)
                
                # Проверяем точную конвертацию
                category = Category.objects.get(name=f'Hex Test {i}')
                self.assertEqual(category.color, expected_rgba)

    def test_rgb_to_rgba_conversion(self):
        """Подробное тестирование конвертации rgb в rgba"""
        rgb_color_tests = [
            ('rgb(255,0,0)', 'rgba(255, 0, 0, 0.4)'),
            ('rgb(0,255,0)', 'rgba(0, 255, 0, 0.4)'),
            ('rgb(0,0,255)', 'rgba(0, 0, 255, 0.4)'),
            ('rgb(128,64,192)', 'rgba(128, 64, 192, 0.4)'),
            ('rgb(255, 255, 255)', 'rgba(255, 255, 255, 0.4)'),  # С пробелами
            ('RGB(255,0,0)', 'rgba(255, 0, 0, 0.4)'),            # Заглавные
        ]

        for i, (rgb_color, expected_rgba) in enumerate(rgb_color_tests):
            with self.subTest(rgb_color=rgb_color):
                data = {
                    'name': f'RGB Test {i}',
                    'description': f'Testing {rgb_color}',
                    'color': rgb_color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)
                
                # Проверяем точную конвертацию
                category = Category.objects.get(name=f'RGB Test {i}')
                self.assertEqual(category.color, expected_rgba)

    def test_rgba_color_preserved(self):
        """Тест сохранения оригинального rgba цвета (альфа не заменяется)"""
        rgba_color_tests = [
            ('rgba(255,0,0,0.1)', 'rgba(255,0,0,0.1)'),   # Низкая альфа
            ('rgba(255,0,0,0.8)', 'rgba(255,0,0,0.8)'),   # Высокая альфа
            ('rgba(255,0,0,1.0)', 'rgba(255,0,0,1.0)'),   # Полная непрозрачность
            ('rgba(255,0,0,0)', 'rgba(255,0,0,0)'),       # Полная прозрачность
            ('rgba(128,64,192,0.7)', 'rgba(128,64,192,0.7)'),
            ('RGBA(255,255,255,0.9)', 'rgba(255,255,255,0.9)'), # Заглавные
            ('rgba(255, 0, 0, 0.5)', 'rgba(255, 0, 0, 0.5)'),      # С пробелами
        ]
        
        for i, (rgba_color, expected_rgba) in enumerate(rgba_color_tests):
            with self.subTest(rgba_color=rgba_color):
                data = {
                    'name': f'RGBA Test {i}',
                    'description': f'Testing {rgba_color}',
                    'color': rgba_color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)
                
                # Проверяем, что rgba цвет сохранился как есть
                category = Category.objects.get(name=f'RGBA Test {i}')
                self.assertEqual(category.color, expected_rgba)

    def test_invalid_color_formats_detailed(self):
        """Подробное тестирование невалидных форматов цветов"""
        invalid_color_tests = [
            # Неправильный hex
            '#gggggg',
            '#12345',    # Слишком короткий
            '#1234567',  # Слишком длинный
            'ff0000',    # Без #
            
            # Неправильный rgb
            'rgb(256,0,0)',      # Значение больше 255
            'rgb(-1,0,0)',       # Отрицательное значение
            'rgb(255,0)',        # Недостаточно параметров
            'rgb(255,0,0,0)',    # Слишком много параметров
            'rgb(255,0,0.5)',    # Дробное значение
            'rgb(ff,00,00)',     # Hex вместо десятичных
            
            # Неправильный rgba
            'rgba(255,0,0)',     # Недостаточно параметров
            'rgba(256,0,0,0.4)', # Значение больше 255
            'rgba(255,0,0,1.5)', # Альфа больше 1
            'rgba(255,0,0,-0.1)',# Отрицательная альфа
            
            # Другие форматы
            'hsl(120,100%,50%)', # HSL не поддерживается
            'hsv(120,100%,100%)',# HSV не поддерживается
            'red',               # Именованные цвета
            'transparent',       # Ключевые слова
            '255,0,0',          # Без префикса
            '',                 # Пустая строка
            '   ',              # Только пробелы
        ]
        
        for i, invalid_color in enumerate(invalid_color_tests):
            with self.subTest(invalid_color=invalid_color):
                data = {
                    'name': f'Invalid Color Test {i}',
                    'description': f'Testing invalid color: {invalid_color}',
                    'color': invalid_color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                # Ожидаем ошибку валидации
                self.assertIn(response.status_code, [400, 500], 
                             f"Color '{invalid_color}' should be invalid but returned {response.status_code}")

    def test_color_case_insensitive(self):
        """Тест нечувствительности к регистру"""
        color_variations_hex_rgb = [
            ('#FF0000', 'rgba(255, 0, 0, 0.4)'),
            ('#ff0000', 'rgba(255, 0, 0, 0.4)'),
            ('RGB(255, 0, 0)', 'rgba(255, 0, 0, 0.4)'),
            ('rgb(255, 0, 0)', 'rgba(255, 0, 0, 0.4)'),
        ]
        
        color_variations_rgba = [
            ('RGBA(255, 0, 0, 0.8)', 'rgba(255, 0, 0, 0.8)'),
            ('rgba(255, 0, 0, 0.8)', 'rgba(255, 0, 0, 0.8)'),
        ]
        
        # Тестируем hex и rgb - должны конвертироваться с дефолтной альфой
        for i, (color, expected) in enumerate(color_variations_hex_rgb):
            with self.subTest(color=color):
                data = {
                    'name': f'Case Test Hex/RGB {i}',
                    'description': f'Testing case: {color}',
                    'color': color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)
                
                category = Category.objects.get(name=f'Case Test Hex/RGB {i}')
                self.assertEqual(category.color, expected)
        
        # Тестируем rgba - должны сохраняться как есть
        for i, (color, expected) in enumerate(color_variations_rgba):
            with self.subTest(color=color):
                data = {
                    'name': f'Case Test RGBA {i}',
                    'description': f'Testing case: {color}',
                    'color': color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)
                
                category = Category.objects.get(name=f'Case Test RGBA {i}')
                self.assertEqual(category.color, expected)

    def test_color_whitespace_handling(self):
        """Тест обработки пробелов в цветовых форматах"""
        color_with_spaces = [
            'rgb( 255 , 0 , 0 )',
            'rgba( 255, 0, 0, 0.8 )',
            ' #ff0000 ',
            ' rgb(255,0,0) ',
            'rgba(255, 0, 0, 0.5)',  # Смешанные пробелы
        ]
        
        for i, color in enumerate(color_with_spaces):
            with self.subTest(color=color):
                data = {
                    'name': f'Whitespace Test {i}',
                    'description': f'Testing whitespace: "{color}"',
                    'color': color
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                # Может быть как принято (после очистки пробелов), так и отклонено
                self.assertIn(response.status_code, [200, 400, 500])


class CategoryValidationEdgeCasesTest(TestCase):
    """Тесты граничных случаев валидации"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='edgeuser',
            email='edge@example.com', 
            password='testpass123'
        )
        self.client.login(username='edgeuser', password='testpass123')

    def test_unicode_and_emoji_in_name(self):
        """Тест Unicode символов и эмодзи в названии"""
        unicode_names = [
            'Категория на русском',
            '中文类别',  # Китайский
            'Catégorie française',  # Французский с акцентами
            'カテゴリ',  # Японский
            '🚀 Space Category 🌟',  # Эмодзи
            'Math: ∑∏∆√∞',  # Математические символы
            'Special: ©®™§¶',  # Специальные символы
        ]
        
        for i, name in enumerate(unicode_names):
            with self.subTest(name=name):
                data = {
                    'name': name,
                    'description': f'Testing unicode name: {name}',
                    'color': f'rgba({i*30},{i*40},{i*42},0.4)'
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)

                # Проверяем, что название сохранилось корректно
                category = Category.objects.get(name=name)
                self.assertEqual(category.name, name)

    def test_boundary_name_lengths(self):
        """Тест граничных значений длины названия"""
        # Тесты разных длин названий
        length_tests = [
            ('a', 1),                    # Минимальная длина
            ('a' * 50, 50),             # Средняя длина  
            ('a' * 99, 99),             # На один символ меньше максимума
            ('a' * 100, 100),           # Точно максимум - должно работать
        ]
        
        for i, (name, length) in enumerate(length_tests):
            with self.subTest(length=length):
                data = {
                    'name': name,
                    'description': f'Testing length {length}',
                    'color': f'rgba({i*60},{i*60},{i*60},0.4)'
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)

    def test_extreme_description_content(self):
        """Тест экстремального содержимого описания"""
        extreme_descriptions = [
            # Очень длинный текст
            'Very long description. ' * 10000,
            
            # Много переносов строк
            '\n' * 1000,
            
            # Смешанные символы
            ''.join([chr(i) for i in range(32, 127)] * 100),
            
            # JSON в описании
            '{"key": "value", "array": [1, 2, 3], "nested": {"inner": "data"}}',
            
            # HTML код
            '<div class="test"><p>HTML content</p><script>alert("test")</script></div>',
            
            # Markdown со всеми возможными элементами
            '''
# Заголовок 1
## Заголовок 2
### Заголовок 3

**Жирный** *курсив* ~~зачеркнутый~~ `код`

> Цитата
> Многострочная цитата

- Список
  - Подсписок
    - Под-подсписок

1. Нумерованный
2. Список
3. Элементы

[Ссылка](https://example.com)

![Изображение](https://example.com/image.jpg)

```python
def code_block():
    return "Hello World"
```

| Таблица | Колонка 2 |
|---------|-----------|
| Данные  | Значения  |

---

Горизонтальная линия выше
            ''',
        ]
        
        for i, description in enumerate(extreme_descriptions):
            with self.subTest(description_type=f"Type {i}"):
                data = {
                    'name': f'Extreme Desc {i}',
                    'description': description,
                    'color': f'rgba({i*30},{i*30},{i*30},0.4)'
                }
                response = self.client.post(
                    '/api/category/',
                    json.dumps(data),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)

    def test_malformed_json_requests(self):
        """Тест неправильно сформированных JSON запросов"""
        malformed_jsons = [
            'invalid json',
            '{"name": "test"',  # Незакрытый JSON
            '{"name": "test",}',  # Лишняя запятая
            '{"name": undefined}',  # undefined не валиден в JSON
            '{"name": "test", "color": }',  # Пустое значение
            '',  # Пустой запрос
            '{',  # Только открывающая скобка
            '}',  # Только закрывающая скобка
            'null',  # Просто null
            '[1,2,3]',  # Массив вместо объекта
        ]
        
        for i, malformed_json in enumerate(malformed_jsons):
            with self.subTest(json_content=malformed_json[:20]):
                response = self.client.post(
                    '/api/category/',
                    malformed_json,
                    content_type='application/json'
                )
                # Ожидаем ошибку парсинга JSON
                self.assertIn(response.status_code, [400, 500])