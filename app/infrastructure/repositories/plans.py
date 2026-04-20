from __future__ import annotations

from datetime import date

from sqlalchemy import exists, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Plan
from app.infrastructure.db.models import PlanModel


class SqlAlchemyPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_for_period_category(self, period: date, category_id: int) -> bool:
        stmt = select(
            exists().where(
                PlanModel.period == period,
                PlanModel.category_id == category_id,
            )
        )
        return bool(await self._session.scalar(stmt))

    async def bulk_insert(self, plans: list[Plan]) -> None:
        if not plans:
            return
        self._session.add_all(
            [
                PlanModel(period=plan.period, sum=plan.sum, category_id=plan.category_id)
                for plan in plans
            ]
        )
        await self._session.flush()

    async def list_up_to(self, check_date: date) -> list[Plan]:
        stmt = (
            select(PlanModel)
            .where(PlanModel.period <= check_date)
            .order_by(PlanModel.period, PlanModel.category_id)
        )
        result = await self._session.scalars(stmt)
        return [self._to_entity(row) for row in result.all()]

    async def list_for_year(self, year: int) -> list[Plan]:
        stmt = (
            select(PlanModel)
            .where(extract("year", PlanModel.period) == year)
            .order_by(PlanModel.period, PlanModel.category_id)
        )
        result = await self._session.scalars(stmt)
        return [self._to_entity(row) for row in result.all()]

    @staticmethod
    def _to_entity(row: PlanModel) -> Plan:
        return Plan(id=row.id, period=row.period, sum=row.sum, category_id=row.category_id)
