import os
import sys
import django
from django.conf import settings

# Добавляем путь к src в PYTHONPATH для правильного импорта модулей
sys.path.insert(0, '/home/ilya/code/webapps/task_manager_brain_api/src')

# Устанавливаем переменную окружения для Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Инициализируем Django для работы type checker
if not settings.configured:
    django.setup()