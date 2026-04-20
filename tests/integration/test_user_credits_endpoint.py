from __future__ import annotations

from httpx import AsyncClient


async def test_returns_credits_with_mixed_statuses(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await api_client.get("/api/v1/user_credits/1", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    closed = next(item for item in body if item["status"] == "closed")
    open_credit = next(item for item in body if item["status"] == "open")

    assert closed["is_closed"] is True
    assert closed["return_date"] == "2024-01-28"
    assert float(closed["total_payments"]) == 1100.0

    assert open_credit["is_closed"] is False
    assert float(open_credit["body_payments"]) == 300.0
    assert float(open_credit["interest_payments"]) == 40.0
    assert open_credit["overdue_days"] >= 0


async def test_returns_404_for_unknown_user(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await api_client.get("/api/v1/user_credits/9999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_user_without_credits_returns_empty_list(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await api_client.get("/api/v1/user_credits/2", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []
