from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from types import TracebackType
from typing import Self

from app.domain.entities import AuthUser, Credit, DictionaryEntry, Payment, Plan, User


@dataclass
class InMemoryStore:
    users: dict[int, User] = field(default_factory=dict)
    credits: dict[int, Credit] = field(default_factory=dict)
    payments: dict[int, Payment] = field(default_factory=dict)
    plans: dict[int, Plan] = field(default_factory=dict)
    dictionary: dict[int, DictionaryEntry] = field(default_factory=dict)
    auth_users: dict[str, AuthUser] = field(default_factory=dict)


class FakeUserRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def get_by_id(self, user_id: int) -> User | None:
        return self._store.users.get(user_id)

    async def exists(self, user_id: int) -> bool:
        return user_id in self._store.users


class FakeCreditRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def list_by_user(self, user_id: int) -> list[Credit]:
        return sorted(
            (c for c in self._store.credits.values() if c.user_id == user_id),
            key=lambda c: c.issuance_date,
        )

    async def sum_body_between(self, start: date, end: date) -> Decimal:
        return sum(
            (c.body for c in self._store.credits.values() if start <= c.issuance_date <= end),
            start=Decimal(0),
        )

    async def monthly_stats(self, year: int) -> list[tuple[int, int, Decimal]]:
        buckets: dict[int, tuple[int, Decimal]] = {}
        for credit in self._store.credits.values():
            if credit.issuance_date.year != year:
                continue
            month = credit.issuance_date.month
            count, total = buckets.get(month, (0, Decimal(0)))
            buckets[month] = (count + 1, total + credit.body)
        return [(month, count, total) for month, (count, total) in sorted(buckets.items())]


class FakePaymentRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def list_by_credit(self, credit_id: int) -> list[Payment]:
        return [p for p in self._store.payments.values() if p.credit_id == credit_id]

    async def list_by_credits(self, credit_ids: list[int]) -> list[Payment]:
        ids = set(credit_ids)
        return [p for p in self._store.payments.values() if p.credit_id in ids]

    async def sum_between(self, start: date, end: date) -> Decimal:
        return sum(
            (p.sum for p in self._store.payments.values() if start <= p.payment_date <= end),
            start=Decimal(0),
        )

    async def monthly_stats(self, year: int) -> list[tuple[int, int, Decimal]]:
        buckets: dict[int, tuple[int, Decimal]] = {}
        for payment in self._store.payments.values():
            if payment.payment_date.year != year:
                continue
            month = payment.payment_date.month
            count, total = buckets.get(month, (0, Decimal(0)))
            buckets[month] = (count + 1, total + payment.sum)
        return [(month, count, total) for month, (count, total) in sorted(buckets.items())]


class FakePlanRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self._counter = max(store.plans, default=0)

    async def exists_for_period_category(self, period: date, category_id: int) -> bool:
        return any(
            plan.period == period and plan.category_id == category_id
            for plan in self._store.plans.values()
        )

    async def bulk_insert(self, plans: list[Plan]) -> None:
        for plan in plans:
            self._counter += 1
            self._store.plans[self._counter] = Plan(
                id=self._counter,
                period=plan.period,
                sum=plan.sum,
                category_id=plan.category_id,
            )

    async def list_up_to(self, check_date: date) -> list[Plan]:
        return sorted(
            (p for p in self._store.plans.values() if p.period <= check_date),
            key=lambda p: (p.period, p.category_id),
        )

    async def list_for_year(self, year: int) -> list[Plan]:
        return sorted(
            (p for p in self._store.plans.values() if p.period.year == year),
            key=lambda p: (p.period, p.category_id),
        )


class FakeDictionaryRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def list_all(self) -> list[DictionaryEntry]:
        return sorted(self._store.dictionary.values(), key=lambda e: e.id)

    async def get_by_name(self, name: str) -> DictionaryEntry | None:
        for entry in self._store.dictionary.values():
            if entry.name == name:
                return entry
        return None

    async def get_by_id(self, entry_id: int) -> DictionaryEntry | None:
        return self._store.dictionary.get(entry_id)


class FakeAuthUserRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self._counter = len(store.auth_users)

    async def get_by_login(self, login: str) -> AuthUser | None:
        return self._store.auth_users.get(login)

    async def create(self, login: str, hashed_password: str) -> AuthUser:
        self._counter += 1
        user = AuthUser(id=self._counter, login=login, hashed_password=hashed_password)
        self._store.auth_users[login] = user
        return user


class FakeUnitOfWork:
    def __init__(self, store: InMemoryStore | None = None) -> None:
        self.store = store or InMemoryStore()
        self.commits = 0
        self.rollbacks = 0

        self.users = FakeUserRepository(self.store)
        self.credits = FakeCreditRepository(self.store)
        self.payments = FakePaymentRepository(self.store)
        self.plans = FakePlanRepository(self.store)
        self.dictionary = FakeDictionaryRepository(self.store)
        self.auth_users = FakeAuthUserRepository(self.store)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1
