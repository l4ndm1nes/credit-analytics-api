from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.application.dto import YearMonthPerformanceDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.enums import PlanCategory

_HUNDRED = Decimal(100)
_ZERO = Decimal(0)
_QUANTUM = Decimal("0.01")


class YearPerformanceUseCase:
    async def execute(self, uow: UnitOfWork, year: int) -> list[YearMonthPerformanceDTO]:
        dictionary = await uow.dictionary.list_all()
        id_by_name = {entry.name: entry.id for entry in dictionary}
        issuance_category_id = id_by_name.get(PlanCategory.issuance)
        collection_category_id = id_by_name.get(PlanCategory.collection)

        plans = await uow.plans.list_for_year(year)
        issuance_plan_by_month: dict[int, Decimal] = {}
        collection_plan_by_month: dict[int, Decimal] = {}
        for plan in plans:
            if plan.category_id == issuance_category_id:
                issuance_plan_by_month[plan.period.month] = (
                    issuance_plan_by_month.get(plan.period.month, _ZERO) + plan.sum
                )
            elif plan.category_id == collection_category_id:
                collection_plan_by_month[plan.period.month] = (
                    collection_plan_by_month.get(plan.period.month, _ZERO) + plan.sum
                )

        credit_stats = await uow.credits.monthly_stats(year)
        payment_stats = await uow.payments.monthly_stats(year)
        credits_by_month = {month: (count, total) for month, count, total in credit_stats}
        payments_by_month = {month: (count, total) for month, count, total in payment_stats}

        year_credits_total = sum(
            (total for _count, total in credits_by_month.values()), start=_ZERO
        )
        year_payments_total = sum(
            (total for _count, total in payments_by_month.values()), start=_ZERO
        )

        months = sorted(
            set(issuance_plan_by_month)
            | set(collection_plan_by_month)
            | set(credits_by_month)
            | set(payments_by_month)
        )

        result: list[YearMonthPerformanceDTO] = []
        for month in months:
            issuance_count, issuance_actual = credits_by_month.get(month, (0, _ZERO))
            payment_count, payment_actual = payments_by_month.get(month, (0, _ZERO))
            issuance_plan = issuance_plan_by_month.get(month, _ZERO)
            collection_plan = collection_plan_by_month.get(month, _ZERO)

            result.append(
                YearMonthPerformanceDTO(
                    period=date(year, month, 1),
                    issuance_count=issuance_count,
                    issuance_plan_sum=issuance_plan,
                    issuance_actual_sum=issuance_actual,
                    issuance_completion_percent=self._percent(issuance_actual, issuance_plan),
                    payment_count=payment_count,
                    collection_plan_sum=collection_plan,
                    collection_actual_sum=payment_actual,
                    collection_completion_percent=self._percent(payment_actual, collection_plan),
                    issuance_share_of_year_percent=self._percent(
                        issuance_actual, year_credits_total
                    ),
                    collection_share_of_year_percent=self._percent(
                        payment_actual, year_payments_total
                    ),
                )
            )

        return result

    @staticmethod
    def _percent(numerator: Decimal, denominator: Decimal) -> Decimal:
        if denominator <= 0:
            return _ZERO
        return (numerator / denominator * _HUNDRED).quantize(_QUANTUM)
