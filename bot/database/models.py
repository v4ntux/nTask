from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class User:
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None


@dataclass
class ConcreteBatch:
    id: int
    user_id: int
    grade: str
    location: str
    picket: str
    volume: float
    poured_at: str
    created_at: str


@dataclass
class TestSchedule:
    id: int
    batch_id: int
    days: int
    volume: float
    scheduled_at: str
    status: str


@dataclass
class TestResult:
    id: int
    schedule_id: int
    completed_at: str
    result: str
    comment: str | None
