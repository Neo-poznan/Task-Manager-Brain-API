from typing import Optional, Protocol
from dataclasses import dataclass
from datetime import datetime


class CategoryEntityProtocol(Protocol):
    id: int
    name: str
    description: Optional[str]
    color: str
    user_id: Optional[int]
    is_custom: bool


class TaskEntityProtocol(Protocol):
    id: int
    name: str
    description: Optional[str]
    order: int
    category_id: Optional[int]
    user_id: int
    deadline: Optional[datetime]
    planned_time: str


@dataclass
class CategoryEntity:
    id: int
    name: str
    description: Optional[str]
    color: str
    user_id: Optional[int]
    is_custom: bool


@dataclass
class TaskEntity:
    id: int
    name: str
    description: Optional[str]
    order: int
    category_id: Optional[int]
    user_id: int
    deadline: Optional[datetime]
    planned_time: str

