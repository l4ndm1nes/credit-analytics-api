from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import DictionaryEntry
from app.infrastructure.db.models import DictionaryModel


class SqlAlchemyDictionaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[DictionaryEntry]:
        stmt = select(DictionaryModel).order_by(DictionaryModel.id)
        result = await self._session.scalars(stmt)
        return [DictionaryEntry(id=row.id, name=row.name) for row in result.all()]

    async def get_by_name(self, name: str) -> DictionaryEntry | None:
        stmt = select(DictionaryModel).where(DictionaryModel.name == name)
        row = await self._session.scalar(stmt)
        if row is None:
            return None
        return DictionaryEntry(id=row.id, name=row.name)

    async def get_by_id(self, entry_id: int) -> DictionaryEntry | None:
        row = await self._session.get(DictionaryModel, entry_id)
        if row is None:
            return None
        return DictionaryEntry(id=row.id, name=row.name)
