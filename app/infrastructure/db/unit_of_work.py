from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.repositories.auth_users import SqlAlchemyAuthUserRepository
from app.infrastructure.repositories.credits import SqlAlchemyCreditRepository
from app.infrastructure.repositories.dictionary import SqlAlchemyDictionaryRepository
from app.infrastructure.repositories.payments import SqlAlchemyPaymentRepository
from app.infrastructure.repositories.plans import SqlAlchemyPlanRepository
from app.infrastructure.repositories.users import SqlAlchemyUserRepository


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

        self.users: SqlAlchemyUserRepository
        self.credits: SqlAlchemyCreditRepository
        self.payments: SqlAlchemyPaymentRepository
        self.plans: SqlAlchemyPlanRepository
        self.dictionary: SqlAlchemyDictionaryRepository
        self.auth_users: SqlAlchemyAuthUserRepository

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self._session)
        self.credits = SqlAlchemyCreditRepository(self._session)
        self.payments = SqlAlchemyPaymentRepository(self._session)
        self.plans = SqlAlchemyPlanRepository(self._session)
        self.dictionary = SqlAlchemyDictionaryRepository(self._session)
        self.auth_users = SqlAlchemyAuthUserRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            if exc_type is not None:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        assert self._session is not None
        await self._session.commit()

    async def rollback(self) -> None:
        assert self._session is not None
        await self._session.rollback()
