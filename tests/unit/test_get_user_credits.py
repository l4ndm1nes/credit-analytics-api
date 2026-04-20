from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.application.dto import ClosedCreditDTO, OpenCreditDTO
from app.application.use_cases.get_user_credits import GetUserCreditsUseCase
from app.domain.entities import Credit, DictionaryEntry, Payment, User
from app.domain.enums import PaymentType
from app.domain.exceptions import UserNotFoundError
from tests.unit.fakes import FakeUnitOfWork, InMemoryStore


def _seed_dictionary(store: InMemoryStore) -> None:
    store.dictionary[1] = DictionaryEntry(id=1, name=PaymentType.body)
    store.dictionary[2] = DictionaryEntry(id=2, name=PaymentType.interest)


async def test_raises_when_user_missing() -> None:
    uow = FakeUnitOfWork()
    use_case = GetUserCreditsUseCase()

    with pytest.raises(UserNotFoundError):
        await use_case.execute(uow, user_id=42, today=date(2024, 1, 1))


async def test_closed_credit_returns_total_payments() -> None:
    store = InMemoryStore()
    _seed_dictionary(store)
    store.users[1] = User(id=1, login="u1", registration_date=date(2023, 1, 1))
    store.credits[10] = Credit(
        id=10,
        user_id=1,
        issuance_date=date(2023, 5, 1),
        return_date=date(2023, 6, 1),
        actual_return_date=date(2023, 5, 28),
        body=Decimal("1000.00"),
        percent=Decimal("50.00"),
    )
    store.payments[100] = Payment(
        id=100, credit_id=10, type_id=1, payment_date=date(2023, 5, 15), sum=Decimal("600")
    )
    store.payments[101] = Payment(
        id=101, credit_id=10, type_id=2, payment_date=date(2023, 5, 20), sum=Decimal("450")
    )

    uow = FakeUnitOfWork(store)
    result = await GetUserCreditsUseCase().execute(uow, user_id=1, today=date(2024, 1, 1))

    assert len(result) == 1
    closed = result[0]
    assert isinstance(closed, ClosedCreditDTO)
    assert closed.total_payments == Decimal("1050")
    assert closed.return_date == date(2023, 5, 28)


async def test_open_credit_calculates_overdue_and_buckets() -> None:
    store = InMemoryStore()
    _seed_dictionary(store)
    store.users[1] = User(id=1, login="u1", registration_date=date(2023, 1, 1))
    store.credits[20] = Credit(
        id=20,
        user_id=1,
        issuance_date=date(2024, 1, 1),
        return_date=date(2024, 2, 1),
        actual_return_date=None,
        body=Decimal("2000.00"),
        percent=Decimal("300.00"),
    )
    store.payments[200] = Payment(
        id=200, credit_id=20, type_id=1, payment_date=date(2024, 1, 10), sum=Decimal("500")
    )
    store.payments[201] = Payment(
        id=201, credit_id=20, type_id=2, payment_date=date(2024, 1, 20), sum=Decimal("75")
    )

    uow = FakeUnitOfWork(store)
    result = await GetUserCreditsUseCase().execute(uow, user_id=1, today=date(2024, 2, 15))

    assert len(result) == 1
    opened = result[0]
    assert isinstance(opened, OpenCreditDTO)
    assert opened.overdue_days == 14
    assert opened.body_payments == Decimal("500")
    assert opened.interest_payments == Decimal("75")


async def test_open_credit_without_overdue_returns_zero_days() -> None:
    store = InMemoryStore()
    _seed_dictionary(store)
    store.users[1] = User(id=1, login="u1", registration_date=date(2023, 1, 1))
    store.credits[30] = Credit(
        id=30,
        user_id=1,
        issuance_date=date(2024, 1, 1),
        return_date=date(2024, 3, 1),
        actual_return_date=None,
        body=Decimal("500"),
        percent=Decimal("25"),
    )

    uow = FakeUnitOfWork(store)
    result = await GetUserCreditsUseCase().execute(uow, user_id=1, today=date(2024, 2, 10))

    assert len(result) == 1
    opened = result[0]
    assert isinstance(opened, OpenCreditDTO)
    assert opened.overdue_days == 0
    assert opened.body_payments == Decimal(0)
    assert opened.interest_payments == Decimal(0)


async def test_user_without_credits_returns_empty_list() -> None:
    store = InMemoryStore()
    _seed_dictionary(store)
    store.users[7] = User(id=7, login="u7", registration_date=date(2023, 1, 1))

    uow = FakeUnitOfWork(store)
    result = await GetUserCreditsUseCase().execute(uow, user_id=7, today=date(2024, 1, 1))

    assert result == []
