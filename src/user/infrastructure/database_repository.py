from typing import Type
from abc import ABC, abstractmethod
from django.db import transaction

from django.utils.connection import ConnectionProxy
from user.models import User, RefreshToken

class UserDatabaseRepositoryInterface(ABC):

    @abstractmethod
    def refresh_session_in_database(
            self,
            jti: str,
            device_id: str,
            ip_address: str,
            user_agent: str,
            user: User,
        ) -> None:
        cursor = self._connection.cursor()
        tokens = self._refresh_token_model.objects.filter(device_id=device_id, user=user)
        cursor.execute(
            '''
            SELECT jti, user_id, device_id, ip_address, user_agent 
            FROM user_refreshtoken
            WHERE user_id=%s AND device_id=%s
            FOR UPDATE;
            ''',
            [user.id, device_id]
            )
        tokens.delete()
        self._fer.objects.create(
            jti=jti, 
            user=user,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )


class UserDatabaseRepository(UserDatabaseRepositoryInterface):

    def __init__(self, connection: ConnectionProxy, refresh_token_model: Type[RefreshToken]):
        self._connection = connection
        self._refresh_token_model = refresh_token_model

    @transaction.atomic()
    def refresh_session_in_database(
            self,
            jti: str,
            device_id: str,
            ip_address: str,
            user_agent: str,
            user: User,
        ) -> None:
        cursor = self._connection.cursor()
        tokens = self._refresh_token_model.objects.filter(device_id=device_id, user=user)
        cursor.execute(
            '''
            SELECT jti, user_id, device_id, ip_address, user_agent 
            FROM user_refreshtoken
            WHERE user_id=%s AND device_id=%s
            FOR UPDATE;
            ''',
            [user.id, device_id]
            )
        tokens.delete()
        self._refresh_token_model.objects.create(
            jti=jti, 
            user=user,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

