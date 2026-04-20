from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Payment
from app.infrastructure.db.models import PaymentModel


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_credit(self, credit_id: int) -> list[Payment]:
        stmt = select(PaymentModel).where(PaymentModel.credit_id == credit_id)
        result = await self._session.scalars(stmt)
        return [self._to_entity(row) for row in result.all()]

    async def list_by_credits(self, credit_ids: list[int]) -> list[Payment]:
        if not credit_ids:
            return []
        stmt = select(PaymentModel).where(PaymentModel.credit_id.in_(credit_ids))
        result = await self._session.scalars(stmt)
        return [self._to_entity(row) for row in result.all()]

    async def sum_between(self, start: date, end: date) -> Decimal:
        stmt = select(func.coalesce(func.sum(PaymentModel.sum), 0)).where(
            PaymentModel.payment_date >= start,
            PaymentModel.payment_date <= end,
        )
        value = await self._session.scalar(stmt)
        return Decimal(value or 0)

    async def monthly_stats(self, year: int) -> list[tuple[int, int, Decimal]]:
        month_expr = extract("month", PaymentModel.payment_date).label("month")
        stmt = (
            select(
                month_expr,
                func.count(PaymentModel.id),
                func.coalesce(func.sum(PaymentModel.sum), 0),
            )
            .where(extract("year", PaymentModel.payment_date) == year)
            .group_by(month_expr)
        )
        result = await self._session.execute(stmt)
        return [
            (int(month), int(count), Decimal(total or 0)) for month, count, total in result.all()
        ]

    @staticmethod
    def _to_entity(row: PaymentModel) -> Payment:
        return Payment(
            id=row.id,
            credit_id=row.credit_id,
            type_id=row.type_id,
            payment_date=row.payment_date,
            sum=row.sum,
        )
