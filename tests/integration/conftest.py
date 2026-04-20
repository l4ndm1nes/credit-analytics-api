from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.core.config import AuthMode, Settings
from app.domain.enums import PaymentType, PlanCategory
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import (
    CreditModel,
    DictionaryModel,
    PaymentModel,
    PlanModel,
    UserModel,
)
from app.infrastructure.db.session import create_engine, create_session_factory
from app.main import create_app


@pytest.fixture
def admin_credentials() -> tuple[str, str]:
    return "admin", "admin-password"


@pytest.fixture
def test_api_key() -> str:
    return "integration-test-api-key"


def _build_settings(
    tmp_path: Path,
    admin_login: str,
    admin_password: str,
    api_key: str,
) -> Settings:
    db_file = tmp_path / "test.db"
    return Settings(
        app_env="testing",
        app_debug=True,
        database_url=f"sqlite+aiosqlite:///{db_file}",
        database_echo=False,
        auth_mode=AuthMode.jwt,
        jwt_secret_key=SecretStr("integration-test-secret-key-123456"),
        jwt_access_token_ttl_minutes=60,
        api_key=SecretStr(api_key),
        bootstrap_admin_login=admin_login,
        bootstrap_admin_password=SecretStr(admin_password),
        seed_on_startup=False,
        seed_data_dir=tmp_path,
    )


async def _create_schema_and_seed(settings: Settings) -> None:
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        session.add_all(
            [
                DictionaryModel(id=1, name=PaymentType.body),
                DictionaryModel(id=2, name=PaymentType.interest),
                DictionaryModel(id=3, name=PlanCategory.issuance),
                DictionaryModel(id=4, name=PlanCategory.collection),
                UserModel(id=1, login="alice", registration_date=date(2023, 1, 1)),
                UserModel(id=2, login="bob", registration_date=date(2023, 2, 1)),
                CreditModel(
                    id=1,
                    user_id=1,
                    issuance_date=date(2024, 1, 1),
                    return_date=date(2024, 2, 1),
                    actual_return_date=date(2024, 1, 28),
                    body=Decimal("1000"),
                    percent=Decimal("100"),
                ),
                CreditModel(
                    id=2,
                    user_id=1,
                    issuance_date=date(2024, 2, 1),
                    return_date=date(2024, 3, 1),
                    actual_return_date=None,
                    body=Decimal("2000"),
                    percent=Decimal("200"),
                ),
                PaymentModel(
                    id=1,
                    credit_id=1,
                    type_id=1,
                    payment_date=date(2024, 1, 15),
                    sum=Decimal("500"),
                ),
                PaymentModel(
                    id=2,
                    credit_id=1,
                    type_id=2,
                    payment_date=date(2024, 1, 20),
                    sum=Decimal("600"),
                ),
                PaymentModel(
                    id=3,
                    credit_id=2,
                    type_id=1,
                    payment_date=date(2024, 2, 10),
                    sum=Decimal("300"),
                ),
                PaymentModel(
                    id=4,
                    credit_id=2,
                    type_id=2,
                    payment_date=date(2024, 2, 15),
                    sum=Decimal("40"),
                ),
                PlanModel(id=1, period=date(2024, 1, 1), sum=Decimal("5000"), category_id=3),
                PlanModel(id=2, period=date(2024, 1, 1), sum=Decimal("2000"), category_id=4),
                PlanModel(id=3, period=date(2024, 2, 1), sum=Decimal("10000"), category_id=3),
                PlanModel(id=4, period=date(2024, 2, 1), sum=Decimal("3000"), category_id=4),
            ]
        )
        await session.commit()

    await engine.dispose()


@pytest_asyncio.fixture
async def settings(
    tmp_path: Path,
    admin_credentials: tuple[str, str],
    test_api_key: str,
) -> Settings:
    login, password = admin_credentials
    return _build_settings(tmp_path, login, password, test_api_key)


@pytest_asyncio.fixture
async def api_client(settings: Settings) -> AsyncIterator[AsyncClient]:
    await _create_schema_and_seed(settings)
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as client,
        app.router.lifespan_context(app),
    ):
        yield client


@pytest_asyncio.fixture
async def auth_headers(
    api_client: AsyncClient,
    admin_credentials: tuple[str, str],
) -> dict[str, str]:
    login, password = admin_credentials
    response = await api_client.post(
        "/api/v1/auth/token",
        json={"login": login, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
