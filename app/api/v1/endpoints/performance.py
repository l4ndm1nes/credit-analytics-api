from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_plans_performance_use_case,
    get_uow,
    get_year_performance_use_case,
    require_principal,
)
from app.api.schemas.performance import PlanPerformanceItem, YearMonthPerformanceItem
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.use_cases.plans_performance import PlansPerformanceUseCase
from app.application.use_cases.year_performance import YearPerformanceUseCase

router = APIRouter(tags=["performance"], dependencies=[Depends(require_principal)])


@router.get("/plans_performance", response_model=list[PlanPerformanceItem])
async def plans_performance(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    use_case: Annotated[PlansPerformanceUseCase, Depends(get_plans_performance_use_case)],
    check_date: Annotated[date, Query(description="Snapshot date for plans evaluation")],
) -> list[PlanPerformanceItem]:
    items = await use_case.execute(uow, check_date=check_date)
    return [PlanPerformanceItem.from_dto(item) for item in items]


@router.get("/year_performance", response_model=list[YearMonthPerformanceItem])
async def year_performance(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    use_case: Annotated[YearPerformanceUseCase, Depends(get_year_performance_use_case)],
    year: Annotated[int, Query(ge=1900, le=2100)],
) -> list[YearMonthPerformanceItem]:
    items = await use_case.execute(uow, year=year)
    return [YearMonthPerformanceItem.from_dto(item) for item in items]
