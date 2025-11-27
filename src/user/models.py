from typing import Union
from uuid import uuid4

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist

from .domain.entities import UserEntity, IncompleteUserEntity
from .validators import email_validator
from .jwt_auth import get_jwt, get_refresh_jwt


class User(AbstractUser):


    class Meta:
        verbose_name = '''
            Пользователи системы. Тут нет разделения на роли, роль одна - обычный пользователь. 
            Никто не имеет права просматривать и изменять информацию другого пользователя.
        '''


    id = models.UUIDField(primary_key=True, default=uuid4)
    avatar = models.ImageField(
            upload_to='user_images', 
            default='user_images/default_avatar.png',
        )
    first_name = None
    last_name = None
    is_superuser = None
    is_staff = None

    @classmethod
    def from_domain(cls, entity: Union[UserEntity, IncompleteUserEntity]):
        if isinstance(entity, IncompleteUserEntity):
            return cls.objects.get(id=entity.id)
        return cls(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            password=entity.password,
            last_login=entity.last_login,
            is_active=entity.is_active,
            date_joined=entity.date_joined,
            avatar=entity.avatar
        )
    
    def to_domain(self) -> UserEntity:
        return UserEntity(
            id=self.id,
            username=self.username,
            email=self.email,
            password=self.password,
            last_login=self.last_login,
            is_active=self.is_active,
            date_joined=self.date_joined,
            avatar=self.avatar
        )
    
    def to_incomplete_domain(self) -> IncompleteUserEntity:
        return IncompleteUserEntity(
            id=self.id,
            username=self.username,
            avatar=self.avatar
        )
    
    def get_session_auth_hash(self) -> dict:
        return {'access_token': get_jwt(self), 'refresh_token': get_refresh_jwt(self)}
    
    def clean(self):
        try:
            if User.objects.get(id=self.id).email == self.email:
                return
        except ObjectDoesNotExist:
            pass

        email_validator(self.email)


class RefreshToken(models.Model):
    jti = models.CharField(
        max_length=40, 
        verbose_name='Уникальный id токена',
        primary_key=True,
    )
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь, которому принадлежит токен',
    )
    device_id = models.CharField(
        max_length=40, 
        verbose_name='Уникальный id устройства сгенерированный на клиенте и хранящийся в cookie',
    )
    ip_address = models.CharField(
        max_length=15,
        verbose_name='Ip адрес устройства',
    )
    user_agent = models.CharField(
        max_length=100,
        verbose_name='Информация о браузере клиента',
    )

    def __str__(self):
        return f'JTI: {self.jti} Device id: {self.device_id} Ip address: {self.ip_address} User agent: {self.user_agent}'

