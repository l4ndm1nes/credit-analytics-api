from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.application.use_cases.year_performance import YearPerformanceUseCase
from app.domain.entities import Credit, DictionaryEntry, Payment, Plan
from app.domain.enums import PlanCategory
from tests.unit.fakes import FakeUnitOfWork, InMemoryStore


def _seed_dictionary(store: InMemoryStore) -> None:
    store.dictionary[3] = DictionaryEntry(id=3, name=PlanCategory.issuance)
    store.dictionary[4] = DictionaryEntry(id=4, name=PlanCategory.collection)


async def test_empty_year_returns_empty_list() -> None:
    store = InMemoryStore()
    _seed_dictionary(store)
    result = await YearPerformanceUseCase().execute(FakeUnitOfWork(store), year=2024)
    assert result == []


async def test_full_year_aggregation() -> None:
    store = InMemoryStore()
    _seed_dictionary(store)

    store.plans[1] = Plan(id=1, period=date(2024, 1, 1), sum=Decimal("10000"), category_id=3)
    store.plans[2] = Plan(id=2, period=date(2024, 1, 1), sum=Decimal("5000"), category_id=4)
    store.plans[3] = Plan(id=3, period=date(2024, 2, 1), sum=Decimal("20000"), category_id=3)

    store.credits[1] = Credit(
        id=1,
        user_id=1,
        issuance_date=date(2024, 1, 10),
        return_date=date(2024, 2, 10),
        actual_return_date=None,
        body=Decimal("2500"),
        percent=Decimal(0),
    )
    store.credits[2] = Credit(
        id=2,
        user_id=1,
        issuance_date=date(2024, 2, 20),
        return_date=date(2024, 3, 20),
        actual_return_date=None,
        body=Decimal("7500"),
        percent=Decimal(0),
    )
    store.payments[1] = Payment(
        id=1, credit_id=1, type_id=1, payment_date=date(2024, 1, 25), sum=Decimal("1000")
    )
    store.payments[2] = Payment(
        id=2, credit_id=2, type_id=2, payment_date=date(2024, 2, 26), sum=Decimal("3000")
    )

    result = await YearPerformanceUseCase().execute(FakeUnitOfWork(store), year=2024)

    assert len(result) == 2
    jan, feb = result
    assert jan.period == date(2024, 1, 1)
    assert jan.issuance_actual_sum == Decimal("2500")
    assert jan.issuance_plan_sum == Decimal("10000")
    assert jan.issuance_completion_percent == Decimal("25.00")
    assert jan.collection_plan_sum == Decimal("5000")
    assert jan.collection_actual_sum == Decimal("1000")
    assert jan.collection_completion_percent == Decimal("20.00")

    assert feb.period == date(2024, 2, 1)
    assert feb.issuance_actual_sum == Decimal("7500")
    assert feb.issuance_share_of_year_percent == Decimal("75.00")
    assert feb.collection_share_of_year_percent == Decimal("75.00")
