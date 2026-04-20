from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from app.core.config import AuthMode, Settings
from app.core.security import JWTService, constant_time_compare
from app.domain.exceptions import InvalidCredentialsError


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    method: AuthMode


class Authenticator(Protocol):
    async def authenticate(self, token: str | None, api_key: str | None) -> Principal: ...


class JWTAuthenticator:
    def __init__(self, jwt_service: JWTService) -> None:
        self._jwt = jwt_service

    async def authenticate(self, token: str | None, api_key: str | None) -> Principal:
        if not token:
            raise InvalidCredentialsError("missing bearer token")
        payload = await asyncio.to_thread(self._jwt.decode, token)
        return Principal(subject=payload.subject, method=AuthMode.jwt)


class ApiKeyAuthenticator:
    def __init__(self, settings: Settings) -> None:
        self._expected = settings.api_key.get_secret_value()

    async def authenticate(self, token: str | None, api_key: str | None) -> Principal:
        if not api_key:
            raise InvalidCredentialsError("missing api key")
        if not constant_time_compare(api_key, self._expected):
            raise InvalidCredentialsError("invalid api key")
        return Principal(subject="api-key", method=AuthMode.api_key)


def build_authenticator(settings: Settings, jwt_service: JWTService) -> Authenticator:
    if settings.auth_mode is AuthMode.api_key:
        return ApiKeyAuthenticator(settings)
    return JWTAuthenticator(jwt_service)
