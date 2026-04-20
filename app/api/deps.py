from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import OAuth2PasswordBearer

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.use_cases.auth import IssueAccessTokenUseCase
from app.application.use_cases.get_user_credits import GetUserCreditsUseCase
from app.application.use_cases.insert_plans import InsertPlansUseCase
from app.application.use_cases.plans_performance import PlansPerformanceUseCase
from app.application.use_cases.year_performance import YearPerformanceUseCase
from app.core.config import AuthMode, Settings, get_settings
from app.infrastructure.auth.authenticator import Authenticator, Principal
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_current_settings() -> Settings:
    return get_settings()


async def get_uow(request: Request) -> AsyncIterator[UnitOfWork]:
    factory: type[SqlAlchemyUnitOfWork] = request.app.state.uow_factory
    async with factory(request.app.state.session_factory) as uow:
        yield uow


async def require_principal(
    request: Request,
    token: Annotated[str | None, Depends(_oauth2_scheme)] = None,
    api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> Principal:
    authenticator: Authenticator = request.app.state.authenticator
    return await authenticator.authenticate(token=token, api_key=api_key)


def get_issue_access_token_use_case(request: Request) -> IssueAccessTokenUseCase:
    return request.app.state.issue_access_token_use_case


def get_user_credits_use_case(request: Request) -> GetUserCreditsUseCase:
    return request.app.state.get_user_credits_use_case


def get_insert_plans_use_case(request: Request) -> InsertPlansUseCase:
    return request.app.state.insert_plans_use_case


def get_plans_performance_use_case(request: Request) -> PlansPerformanceUseCase:
    return request.app.state.plans_performance_use_case


def get_year_performance_use_case(request: Request) -> YearPerformanceUseCase:
    return request.app.state.year_performance_use_case


__all__ = [
    "AuthMode",
    "get_current_settings",
    "get_insert_plans_use_case",
    "get_issue_access_token_use_case",
    "get_plans_performance_use_case",
    "get_uow",
    "get_user_credits_use_case",
    "get_year_performance_use_case",
    "require_principal",
]
