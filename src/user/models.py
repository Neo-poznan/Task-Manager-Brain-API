from typing import Union
from uuid import uuid4

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist

from .domain.entities import UserEntity, IncompleteUserEntity
from .validators import email_validator


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
    
    def clean(self):
        try:
            if User.objects.get(id=self.id).email == self.email:
                return
        except ObjectDoesNotExist:
            pass

        email_validator(self.email)

