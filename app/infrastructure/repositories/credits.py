from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Credit
from app.infrastructure.db.models import CreditModel


class SqlAlchemyCreditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user(self, user_id: int) -> list[Credit]:
        stmt = (
            select(CreditModel)
            .where(CreditModel.user_id == user_id)
            .order_by(CreditModel.issuance_date)
        )
        result = await self._session.scalars(stmt)
        return [self._to_entity(row) for row in result.all()]

    async def sum_body_between(self, start: date, end: date) -> Decimal:
        stmt = select(func.coalesce(func.sum(CreditModel.body), 0)).where(
            CreditModel.issuance_date >= start,
            CreditModel.issuance_date <= end,
        )
        value = await self._session.scalar(stmt)
        return Decimal(value or 0)

    async def monthly_stats(self, year: int) -> list[tuple[int, int, Decimal]]:
        month_expr = extract("month", CreditModel.issuance_date).label("month")
        stmt = (
            select(
                month_expr,
                func.count(CreditModel.id),
                func.coalesce(func.sum(CreditModel.body), 0),
            )
            .where(extract("year", CreditModel.issuance_date) == year)
            .group_by(month_expr)
        )
        result = await self._session.execute(stmt)
        return [
            (int(month), int(count), Decimal(total or 0)) for month, count, total in result.all()
        ]

    @staticmethod
    def _to_entity(row: CreditModel) -> Credit:
        return Credit(
            id=row.id,
            user_id=row.user_id,
            issuance_date=row.issuance_date,
            return_date=row.return_date,
            actual_return_date=row.actual_return_date,
            body=row.body,
            percent=row.percent,
        )
