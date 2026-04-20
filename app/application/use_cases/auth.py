from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.security import JWTService, PasswordHasher
from app.domain.exceptions import InvalidCredentialsError


@dataclass(frozen=True, slots=True)
class AccessToken:
    token: str
    expires_at: datetime


class IssueAccessTokenUseCase:
    def __init__(self, jwt_service: JWTService) -> None:
        self._jwt = jwt_service

    async def execute(self, uow: UnitOfWork, login: str, password: str) -> AccessToken:
        user = await uow.auth_users.get_by_login(login)

        def _sync() -> AccessToken:
            if user is None or not PasswordHasher.verify(password, user.hashed_password):
                raise InvalidCredentialsError("invalid login or password")
            token, expires_at = self._jwt.issue(subject=user.login)
            return AccessToken(token=token, expires_at=expires_at)

        return await asyncio.to_thread(_sync)


class BootstrapAdminUseCase:
    async def execute(self, uow: UnitOfWork, login: str, password: str) -> None:
        existing = await uow.auth_users.get_by_login(login)
        if existing is not None:
            return
        hashed_password = await asyncio.to_thread(PasswordHasher.hash, password)
        await uow.auth_users.create(login=login, hashed_password=hashed_password)
        await uow.commit()
