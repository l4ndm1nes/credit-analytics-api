from __future__ import annotations

from dataclasses import asdict
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.application.dto import PlanPerformanceDTO, YearMonthPerformanceDTO


class PlanPerformanceItem(BaseModel):
    period: date
    category: str
    plan_sum: Decimal
    actual_sum: Decimal
    completion_percent: Decimal

    @classmethod
    def from_dto(cls, dto: PlanPerformanceDTO) -> PlanPerformanceItem:
        return cls(
            period=dto.period,
            category=dto.category,
            plan_sum=dto.plan_sum,
            actual_sum=dto.actual_sum,
            completion_percent=dto.completion_percent,
        )


class YearMonthPerformanceItem(BaseModel):
    period: date
    issuance_count: int
    issuance_plan_sum: Decimal
    issuance_actual_sum: Decimal
    issuance_completion_percent: Decimal
    payment_count: int
    collection_plan_sum: Decimal
    collection_actual_sum: Decimal
    collection_completion_percent: Decimal
    issuance_share_of_year_percent: Decimal
    collection_share_of_year_percent: Decimal

    @classmethod
    def from_dto(cls, dto: YearMonthPerformanceDTO) -> YearMonthPerformanceItem:
        return cls(**asdict(dto))
