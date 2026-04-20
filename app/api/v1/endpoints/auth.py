from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_issue_access_token_use_case, get_uow
from app.api.schemas.auth import TokenRequest, TokenResponse
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.use_cases.auth import IssueAccessTokenUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def issue_token(
    payload: TokenRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    use_case: Annotated[IssueAccessTokenUseCase, Depends(get_issue_access_token_use_case)],
) -> TokenResponse:
    token = await use_case.execute(uow, login=payload.login, password=payload.password)
    return TokenResponse(access_token=token.token, expires_at=token.expires_at)
