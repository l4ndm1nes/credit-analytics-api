from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import get_insert_plans_use_case, get_uow, require_principal
from app.api.schemas.plans import PlansInsertResponse
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.use_cases.insert_plans import InsertPlansUseCase
from app.domain.exceptions import InvalidPlansFileError

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024


router = APIRouter(tags=["plans"], dependencies=[Depends(require_principal)])


@router.post(
    "/plans_insert",
    response_model=PlansInsertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def insert_plans(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    use_case: Annotated[InsertPlansUseCase, Depends(get_insert_plans_use_case)],
    file: Annotated[UploadFile, File(description="Excel file with planning data")],
) -> PlansInsertResponse:
    content = await file.read()
    if len(content) == 0:
        raise InvalidPlansFileError("uploaded file is empty")
    if len(content) > _MAX_UPLOAD_BYTES:
        raise InvalidPlansFileError("uploaded file exceeds maximum allowed size")

    result = await use_case.execute(uow, file_content=content)
    return PlansInsertResponse(inserted=result.inserted)
