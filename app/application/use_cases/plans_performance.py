from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from app.application.dto import PlanPerformanceDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.enums import PlanCategory
from app.domain.exceptions import DomainError

_HUNDRED = Decimal(100)


class PlansPerformanceUseCase:
    async def execute(self, uow: UnitOfWork, check_date: date) -> list[PlanPerformanceDTO]:
        plans = await uow.plans.list_up_to(check_date)
        if not plans:
            return []

        dictionary = await uow.dictionary.list_all()
        name_by_id = {entry.id: entry.name for entry in dictionary}

        result: list[PlanPerformanceDTO] = []
        for plan in plans:
            category_name = name_by_id.get(plan.category_id)
            if category_name is None:
                raise DomainError(
                    f"plan id={plan.id} references unknown category_id={plan.category_id}"
                )

            period_end = min(check_date, self._end_of_month(plan.period))

            if category_name == PlanCategory.issuance:
                actual = await uow.credits.sum_body_between(plan.period, period_end)
            elif category_name == PlanCategory.collection:
                actual = await uow.payments.sum_between(plan.period, period_end)
            else:
                continue

            completion = (actual / plan.sum * _HUNDRED) if plan.sum > 0 else Decimal(0)
            result.append(
                PlanPerformanceDTO(
                    period=plan.period,
                    category=category_name,
                    plan_sum=plan.sum,
                    actual_sum=actual,
                    completion_percent=completion.quantize(Decimal("0.01")),
                )
            )

        return result

    @staticmethod
    def _end_of_month(period: date) -> date:
        _, last_day = monthrange(period.year, period.month)
        return date(period.year, period.month, last_day)
