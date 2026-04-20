from __future__ import annotations

from datetime import date
from io import BytesIO

from httpx import AsyncClient
from openpyxl import Workbook

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx(rows: list[tuple[object, object, object]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["period", "category", "sum"])
    for row in rows:
        ws.append(list(row))
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


async def test_inserts_plans_for_new_months(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    payload = _xlsx(
        [
            (date(2025, 1, 1), "видача", 9000),
            (date(2025, 1, 1), "збір", 3000),
        ]
    )
    response = await api_client.post(
        "/api/v1/plans_insert",
        headers=auth_headers,
        files={"file": ("plans.xlsx", payload, _XLSX_MIME)},
    )
    assert response.status_code == 201
    assert response.json()["inserted"] == 2


async def test_rejects_existing_period_category(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    payload = _xlsx([(date(2024, 1, 1), "видача", 9999)])
    response = await api_client.post(
        "/api/v1/plans_insert",
        headers=auth_headers,
        files={"file": ("plans.xlsx", payload, _XLSX_MIME)},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "invalid_plans_file"
    assert any("already exists" in d["message"] for d in body["error"]["details"])


async def test_rejects_non_first_day_period(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    payload = _xlsx([(date(2025, 3, 10), "видача", 100)])
    response = await api_client.post(
        "/api/v1/plans_insert",
        headers=auth_headers,
        files={"file": ("plans.xlsx", payload, _XLSX_MIME)},
    )
    assert response.status_code == 422
