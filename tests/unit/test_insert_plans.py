from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import Workbook

from app.application.use_cases.insert_plans import InsertPlansUseCase
from app.domain.entities import DictionaryEntry, Plan
from app.domain.enums import PlanCategory
from app.domain.exceptions import InvalidPlansFileError
from app.infrastructure.excel.plans_parser import PlansExcelParser
from tests.unit.fakes import FakeUnitOfWork, InMemoryStore


def _seed_categories(store: InMemoryStore) -> None:
    store.dictionary[3] = DictionaryEntry(id=3, name=PlanCategory.issuance)
    store.dictionary[4] = DictionaryEntry(id=4, name=PlanCategory.collection)


def _workbook_bytes(rows: list[tuple[object, object, object]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["period", "category", "sum"])
    for row in rows:
        ws.append(list(row))
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


async def test_inserts_valid_rows() -> None:
    store = InMemoryStore()
    _seed_categories(store)
    uow = FakeUnitOfWork(store)
    use_case = InsertPlansUseCase(PlansExcelParser())

    content = _workbook_bytes(
        [
            (date(2024, 1, 1), PlanCategory.issuance.value, 100000),
            (date(2024, 1, 1), PlanCategory.collection.value, "50000.50"),
        ]
    )

    result = await use_case.execute(uow, content)

    assert result.inserted == 2
    assert uow.commits == 1
    assert len(store.plans) == 2


async def test_rejects_duplicate_existing_in_db() -> None:
    store = InMemoryStore()
    _seed_categories(store)
    store.plans[1] = Plan(id=1, period=date(2024, 1, 1), sum=Decimal(100), category_id=3)
    uow = FakeUnitOfWork(store)
    use_case = InsertPlansUseCase(PlansExcelParser())

    content = _workbook_bytes([(date(2024, 1, 1), PlanCategory.issuance.value, 200)])

    with pytest.raises(InvalidPlansFileError) as excinfo:
        await use_case.execute(uow, content)

    assert any("already exists" in issue.message for issue in excinfo.value.issues)
    assert uow.commits == 0


async def test_rejects_period_not_first_of_month() -> None:
    store = InMemoryStore()
    _seed_categories(store)
    uow = FakeUnitOfWork(store)
    use_case = InsertPlansUseCase(PlansExcelParser())

    content = _workbook_bytes([(date(2024, 1, 15), PlanCategory.issuance.value, 200)])

    with pytest.raises(InvalidPlansFileError) as excinfo:
        await use_case.execute(uow, content)

    assert any("first day" in issue.message for issue in excinfo.value.issues)


async def test_rejects_unknown_category() -> None:
    store = InMemoryStore()
    _seed_categories(store)
    uow = FakeUnitOfWork(store)
    use_case = InsertPlansUseCase(PlansExcelParser())

    content = _workbook_bytes([(date(2024, 1, 1), "unknown", 100)])

    with pytest.raises(InvalidPlansFileError) as excinfo:
        await use_case.execute(uow, content)

    messages = " | ".join(issue.message for issue in excinfo.value.issues)
    assert "unknown category" in messages


async def test_rejects_empty_sum_at_parse_time() -> None:
    store = InMemoryStore()
    _seed_categories(store)
    uow = FakeUnitOfWork(store)
    use_case = InsertPlansUseCase(PlansExcelParser())

    content = _workbook_bytes([(date(2024, 2, 1), PlanCategory.issuance.value, None)])

    with pytest.raises(InvalidPlansFileError) as excinfo:
        await use_case.execute(uow, content)

    assert any("required" in issue.message for issue in excinfo.value.issues)


async def test_allows_zero_sum() -> None:
    store = InMemoryStore()
    _seed_categories(store)
    uow = FakeUnitOfWork(store)
    use_case = InsertPlansUseCase(PlansExcelParser())

    content = _workbook_bytes([(date(2024, 3, 1), PlanCategory.collection.value, 0)])

    result = await use_case.execute(uow, content)

    assert result.inserted == 1
    assert next(iter(store.plans.values())).sum == Decimal(0)


async def test_rejects_duplicate_inside_same_file() -> None:
    store = InMemoryStore()
    _seed_categories(store)
    uow = FakeUnitOfWork(store)
    use_case = InsertPlansUseCase(PlansExcelParser())

    content = _workbook_bytes(
        [
            (date(2024, 1, 1), PlanCategory.issuance.value, 100),
            (date(2024, 1, 1), PlanCategory.issuance.value, 200),
        ]
    )

    with pytest.raises(InvalidPlansFileError) as excinfo:
        await use_case.execute(uow, content)

    assert any("duplicate" in issue.message for issue in excinfo.value.issues)
