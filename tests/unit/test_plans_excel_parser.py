from __future__ import annotations

from datetime import date
from io import BytesIO

import pytest
from openpyxl import Workbook

from app.domain.exceptions import InvalidPlansFileError
from app.infrastructure.excel.plans_parser import PlansExcelParser


def _workbook(rows: list[tuple[object, ...]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    for row in rows:
        ws.append(list(row))
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


async def test_parses_date_strings_in_multiple_formats() -> None:
    parser = PlansExcelParser()
    content = _workbook(
        [
            ("period", "category", "sum"),
            ("01.04.2024", "видача", 100),
            ("2024-05-01", "збір", 200),
        ]
    )
    rows = parser.parse(content)
    assert [r.period for r in rows] == [date(2024, 4, 1), date(2024, 5, 1)]


async def test_missing_required_columns_raises() -> None:
    parser = PlansExcelParser()
    content = _workbook([("period", "category")])

    with pytest.raises(InvalidPlansFileError) as excinfo:
        parser.parse(content)
    assert any("missing column" in i.message for i in excinfo.value.issues)


async def test_negative_sum_is_rejected() -> None:
    parser = PlansExcelParser()
    content = _workbook(
        [
            ("period", "category", "sum"),
            (date(2024, 1, 1), "видача", -1),
        ]
    )
    with pytest.raises(InvalidPlansFileError) as excinfo:
        parser.parse(content)
    assert any("non-negative" in i.message for i in excinfo.value.issues)


async def test_empty_data_rows_rejected() -> None:
    parser = PlansExcelParser()
    content = _workbook([("period", "category", "sum")])
    with pytest.raises(InvalidPlansFileError):
        parser.parse(content)


async def test_collects_all_issues_before_raising() -> None:
    parser = PlansExcelParser()
    content = _workbook(
        [
            ("period", "category", "sum"),
            (date(2024, 1, 15), "видача", 100),
            (date(2024, 2, 1), None, 200),
            (None, "збір", 300),
        ]
    )
    with pytest.raises(InvalidPlansFileError) as excinfo:
        parser.parse(content)
    assert len(excinfo.value.issues) >= 3
