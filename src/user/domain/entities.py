from typing import Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserEntity:
    id: int
    username: str
    email: str
    password: str
    avatar: str
    last_login: datetime
    is_active: bool
    date_joined: datetime


@dataclass
class IncompleteUserEntity:
    id: int
    username: str
    avatar: str

    def __eq__(self, value: UserEntity):
        if value.id and value.username and value.avatar:
            return self.id == value.id

