from __future__ import annotations

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User
from app.infrastructure.db.models import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        row = await self._session.get(UserModel, user_id)
        if row is None:
            return None
        return self._to_entity(row)

    async def exists(self, user_id: int) -> bool:
        stmt = select(exists().where(UserModel.id == user_id))
        return bool(await self._session.scalar(stmt))

    @staticmethod
    def _to_entity(row: UserModel) -> User:
        return User(id=row.id, login=row.login, registration_date=row.registration_date)
