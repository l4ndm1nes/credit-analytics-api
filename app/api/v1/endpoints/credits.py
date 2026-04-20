from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.deps import get_uow, get_user_credits_use_case, require_principal
from app.api.schemas.credits import ClosedCreditResponse, OpenCreditResponse, UserCreditItem
from app.application.dto import ClosedCreditDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.use_cases.get_user_credits import GetUserCreditsUseCase

router = APIRouter(tags=["credits"], dependencies=[Depends(require_principal)])


@router.get(
    "/user_credits/{user_id}",
    response_model=list[UserCreditItem],
)
async def get_user_credits(
    user_id: Annotated[int, Path(ge=1)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    use_case: Annotated[GetUserCreditsUseCase, Depends(get_user_credits_use_case)],
) -> list[UserCreditItem]:
    today = datetime.now(UTC).date()
    items = await use_case.execute(uow, user_id=user_id, today=today)
    return [
        ClosedCreditResponse.from_dto(item)
        if isinstance(item, ClosedCreditDTO)
        else OpenCreditResponse.from_dto(item)
        for item in items
    ]
