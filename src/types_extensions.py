"""
Дополнительные аннотации типов для лучшей работы с pyright
"""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.contrib.auth.models import AbstractBaseUser
    from uuid import UUID
    from user.models import User
    
    # Расширяем типы для HttpRequest
    class TypedHttpRequest(HttpRequest):
        user: User