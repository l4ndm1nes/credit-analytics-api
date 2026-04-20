from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.application.use_cases.plans_performance import PlansPerformanceUseCase
from app.domain.entities import Credit, DictionaryEntry, Payment, Plan
from app.domain.enums import PlanCategory
from tests.unit.fakes import FakeUnitOfWork, InMemoryStore


def _seed(store: InMemoryStore) -> None:
    store.dictionary[3] = DictionaryEntry(id=3, name=PlanCategory.issuance)
    store.dictionary[4] = DictionaryEntry(id=4, name=PlanCategory.collection)


async def test_returns_empty_when_no_plans() -> None:
    uow = FakeUnitOfWork()
    result = await PlansPerformanceUseCase().execute(uow, check_date=date(2024, 1, 15))
    assert result == []


async def test_issuance_performance_uses_credit_body_sum() -> None:
    store = InMemoryStore()
    _seed(store)
    store.plans[1] = Plan(id=1, period=date(2024, 1, 1), sum=Decimal("10000"), category_id=3)
    store.credits[1] = Credit(
        id=1,
        user_id=1,
        issuance_date=date(2024, 1, 5),
        return_date=date(2024, 2, 5),
        actual_return_date=None,
        body=Decimal("3000"),
        percent=Decimal(0),
    )
    store.credits[2] = Credit(
        id=2,
        user_id=1,
        issuance_date=date(2024, 1, 20),
        return_date=date(2024, 2, 20),
        actual_return_date=None,
        body=Decimal("2000"),
        percent=Decimal(0),
    )

    uow = FakeUnitOfWork(store)
    result = await PlansPerformanceUseCase().execute(uow, check_date=date(2024, 1, 25))

    assert len(result) == 1
    assert result[0].actual_sum == Decimal("5000")
    assert result[0].completion_percent == Decimal("50.00")


async def test_collection_performance_uses_payment_sum() -> None:
    store = InMemoryStore()
    _seed(store)
    store.plans[1] = Plan(id=1, period=date(2024, 2, 1), sum=Decimal("1000"), category_id=4)
    store.payments[1] = Payment(
        id=1, credit_id=1, type_id=1, payment_date=date(2024, 2, 10), sum=Decimal("700")
    )
    store.payments[2] = Payment(
        id=2, credit_id=1, type_id=2, payment_date=date(2024, 2, 15), sum=Decimal("100")
    )

    uow = FakeUnitOfWork(store)
    result = await PlansPerformanceUseCase().execute(uow, check_date=date(2024, 2, 28))

    assert result[0].actual_sum == Decimal("800")
    assert result[0].completion_percent == Decimal("80.00")


async def test_zero_plan_sum_produces_zero_percent() -> None:
    store = InMemoryStore()
    _seed(store)
    store.plans[1] = Plan(id=1, period=date(2024, 3, 1), sum=Decimal(0), category_id=3)

    uow = FakeUnitOfWork(store)
    result = await PlansPerformanceUseCase().execute(uow, check_date=date(2024, 3, 31))

    assert result[0].completion_percent == Decimal(0)


async def test_check_date_before_period_filters_plan_out() -> None:
    store = InMemoryStore()
    _seed(store)
    store.plans[1] = Plan(id=1, period=date(2024, 5, 1), sum=Decimal(100), category_id=3)

    uow = FakeUnitOfWork(store)
    result = await PlansPerformanceUseCase().execute(uow, check_date=date(2024, 4, 1))

    assert result == []
