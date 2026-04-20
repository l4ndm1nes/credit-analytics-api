from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from app.application.interfaces.repositories import (
    AuthUserRepository,
    CreditRepository,
    DictionaryRepository,
    PaymentRepository,
    PlanRepository,
    UserRepository,
)


class UnitOfWork(Protocol):
    users: UserRepository
    credits: CreditRepository
    payments: PaymentRepository
    plans: PlanRepository
    dictionary: DictionaryRepository
    auth_users: AuthUserRepository

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
