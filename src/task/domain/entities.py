from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from user.domain.entities import UserEntity


@dataclass
class CategoryEntity:
    id: int
    name: str
    description: Optional[str]
    color: str
    user: Optional[UserEntity]
    is_custom: bool


@dataclass
class TaskEntity:
    id: int
    name: str
    description: Optional[str]
    order: int
    category: CategoryEntity
    user: UserEntity
    deadline: Optional[datetime]
    planned_time: str

