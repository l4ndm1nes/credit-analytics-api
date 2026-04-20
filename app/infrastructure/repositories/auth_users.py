from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import AuthUser
from app.infrastructure.db.models import AuthUserModel


class SqlAlchemyAuthUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_login(self, login: str) -> AuthUser | None:
        stmt = select(AuthUserModel).where(AuthUserModel.login == login)
        row = await self._session.scalar(stmt)
        if row is None:
            return None
        return self._to_entity(row)

    async def create(self, login: str, hashed_password: str) -> AuthUser:
        row = AuthUserModel(login=login, hashed_password=hashed_password)
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    @staticmethod
    def _to_entity(row: AuthUserModel) -> AuthUser:
        return AuthUser(id=row.id, login=row.login, hashed_password=row.hashed_password)
