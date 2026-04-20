from __future__ import annotations

from httpx import AsyncClient


async def test_plans_performance_returns_evaluated_plans(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await api_client.get(
        "/api/v1/plans_performance",
        headers=auth_headers,
        params={"check_date": "2024-02-28"},
    )
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 4
    categories = {item["category"] for item in body}
    assert categories == {"видача", "збір"}

    january_issuance = next(
        item for item in body if item["period"] == "2024-01-01" and item["category"] == "видача"
    )
    assert float(january_issuance["actual_sum"]) == 1000.0
    assert float(january_issuance["completion_percent"]) == 20.0


async def test_year_performance_aggregates_by_month(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await api_client.get(
        "/api/v1/year_performance",
        headers=auth_headers,
        params={"year": 2024},
    )
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 2
    jan = next(item for item in body if item["period"] == "2024-01-01")
    assert jan["issuance_count"] == 1
    assert float(jan["issuance_actual_sum"]) == 1000.0
    assert float(jan["collection_plan_sum"]) == 2000.0

    feb = next(item for item in body if item["period"] == "2024-02-01")
    assert feb["issuance_count"] == 1
    assert float(feb["issuance_actual_sum"]) == 2000.0


async def test_year_performance_requires_valid_year(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await api_client.get(
        "/api/v1/year_performance",
        headers=auth_headers,
        params={"year": 1800},
    )
    assert response.status_code == 422
