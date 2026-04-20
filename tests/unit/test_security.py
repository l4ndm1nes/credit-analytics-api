from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt
from pydantic import SecretStr

from app.core.config import Settings
from app.core.security import JWTService, PasswordHasher
from app.domain.exceptions import InvalidCredentialsError


def _settings(ttl_minutes: int = 5) -> Settings:
    return Settings(
        jwt_secret_key=SecretStr("unit-test-secret-at-least-16"),
        jwt_access_token_ttl_minutes=ttl_minutes,
    )


async def test_password_hasher_roundtrip() -> None:
    hashed = PasswordHasher.hash("qwerty123")
    assert PasswordHasher.verify("qwerty123", hashed)
    assert not PasswordHasher.verify("wrong", hashed)


async def test_jwt_issue_and_decode() -> None:
    service = JWTService(_settings())
    token, expires_at = service.issue("alice")
    assert expires_at > datetime.now(UTC)

    payload = service.decode(token)
    assert payload.subject == "alice"
    assert payload.expires_at == expires_at.replace(microsecond=0)


async def test_jwt_rejects_invalid_signature() -> None:
    service = JWTService(_settings())
    token, _ = service.issue("bob")
    tampered = token[:-3] + ("A" if token[-1] != "A" else "B") * 3

    with pytest.raises(InvalidCredentialsError):
        service.decode(tampered)


async def test_jwt_rejects_expired_token() -> None:
    settings = _settings(ttl_minutes=1)
    service = JWTService(settings)
    expired = jwt.encode(
        {
            "sub": "eve",
            "exp": int((datetime.now(UTC) - timedelta(minutes=5)).timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidCredentialsError):
        service.decode(expired)
