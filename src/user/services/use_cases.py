from typing import Union, NoReturn, Iterable

from user.models import RefreshToken, User
from user.jwt_auth import decode_jwt
from user.infrastructure.database_repository import UserDatabaseRepositoryInterface


class UserUseCase:
    def __init__(self, repository: UserDatabaseRepositoryInterface):
        self._repository = repository

    def refresh_session(
            self, 
            current_refresh_token: str,
            device_id: str,
            ip_address: str,
            user_agent: str,
            host: str,
        ) -> Union[Iterable[str], NoReturn]:

        payload = decode_jwt(current_refresh_token, audience=host)
        current_refresh_token_sub = payload['sub']
        current_refresh_token_jti = payload['jti']

        user = User.objects.get(id=current_refresh_token_sub)

        self._check_session_in_database(user, current_refresh_token_jti)

        new_access_token, new_refresh_token = self._get_new_tokens(user)
        new_refresh_token_payload = decode_jwt(new_refresh_token, audience=host)
        new_refresh_token_jti = new_refresh_token_payload['jti']
        self._repository.refresh_session_in_database(
            jti=new_refresh_token_jti,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            user=user,
        )
        return new_access_token, new_refresh_token

    def _get_new_tokens(self, user: User) -> Iterable[str]:
        new_jwt_tokens = user.get_session_auth_hash()
        new_refresh_token = new_jwt_tokens['refresh_token']
        new_access_token = new_jwt_tokens['access_token']
        return new_access_token, new_refresh_token

    def _check_session_in_database(
            self, 
            user: User,
            jti: str, 
        ) -> Union[None, NoReturn]:
 
        user_refresh_token_queryset = RefreshToken.objects.filter(
            user=user, 
            jti=jti, 
        )
        if not user_refresh_token_queryset.exists():
            raise PermissionError('jti not found in database')
        
    def set_new_session(self, user: User, refresh_token: str, device_id: str, ip_address: str, user_agent: str, host: str) -> None:
        payload = decode_jwt(refresh_token, audience=host)
        jti = payload['jti']
        self._repository.refresh_session_in_database(
            jti=jti,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            user=user,
        )

