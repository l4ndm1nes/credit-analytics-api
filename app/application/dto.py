from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ClosedCreditDTO:
    issuance_date: date
    return_date: date
    body: Decimal
    percent: Decimal
    total_payments: Decimal


@dataclass(frozen=True, slots=True)
class OpenCreditDTO:
    issuance_date: date
    return_date: date
    overdue_days: int
    body: Decimal
    percent: Decimal
    body_payments: Decimal
    interest_payments: Decimal


@dataclass(frozen=True, slots=True)
class PlanRowDTO:
    period: date
    category_name: str
    sum: Decimal


@dataclass(frozen=True, slots=True)
class PlanPerformanceDTO:
    period: date
    category: str
    plan_sum: Decimal
    actual_sum: Decimal
    completion_percent: Decimal


@dataclass(frozen=True, slots=True)
class YearMonthPerformanceDTO:
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
