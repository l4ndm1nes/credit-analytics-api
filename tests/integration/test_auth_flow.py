from __future__ import annotations

from httpx import AsyncClient


async def test_requires_auth_for_protected_endpoint(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/user_credits/1")
    assert response.status_code == 401


async def test_token_endpoint_returns_access_token(
    api_client: AsyncClient,
    admin_credentials: tuple[str, str],
) -> None:
    login, password = admin_credentials
    response = await api_client.post(
        "/api/v1/auth/token",
        json={"login": login, "password": password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)


async def test_token_endpoint_rejects_wrong_password(
    api_client: AsyncClient,
    admin_credentials: tuple[str, str],
) -> None:
    login, _ = admin_credentials
    response = await api_client.post(
        "/api/v1/auth/token",
        json={"login": login, "password": "definitely-wrong"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


async def test_protected_endpoint_accepts_valid_token(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await api_client.get("/api/v1/user_credits/1", headers=auth_headers)
    assert response.status_code == 200
