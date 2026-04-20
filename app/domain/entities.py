from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DictionaryEntry:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class User:
    id: int
    login: str
    registration_date: date


@dataclass(frozen=True, slots=True)
class Credit:
    id: int
    user_id: int
    issuance_date: date
    return_date: date
    actual_return_date: date | None
    body: Decimal
    percent: Decimal

    @property
    def is_closed(self) -> bool:
        return self.actual_return_date is not None


@dataclass(frozen=True, slots=True)
class Payment:
    id: int
    credit_id: int
    type_id: int
    payment_date: date
    sum: Decimal


@dataclass(frozen=True, slots=True)
class Plan:
    id: int
    period: date
    sum: Decimal
    category_id: int


@dataclass(frozen=True, slots=True)
class AuthUser:
    id: int
    login: str
    hashed_password: str
