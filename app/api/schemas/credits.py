from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.application.dto import ClosedCreditDTO, OpenCreditDTO


class ClosedCreditResponse(BaseModel):
    status: Literal["closed"] = "closed"
    issuance_date: date
    is_closed: Literal[True] = True
    return_date: date
    body: Decimal
    percent: Decimal
    total_payments: Decimal

    @classmethod
    def from_dto(cls, dto: ClosedCreditDTO) -> ClosedCreditResponse:
        return cls(
            issuance_date=dto.issuance_date,
            return_date=dto.return_date,
            body=dto.body,
            percent=dto.percent,
            total_payments=dto.total_payments,
        )


class OpenCreditResponse(BaseModel):
    status: Literal["open"] = "open"
    issuance_date: date
    is_closed: Literal[False] = False
    return_date: date
    overdue_days: int
    body: Decimal
    percent: Decimal
    body_payments: Decimal
    interest_payments: Decimal

    @classmethod
    def from_dto(cls, dto: OpenCreditDTO) -> OpenCreditResponse:
        return cls(
            issuance_date=dto.issuance_date,
            return_date=dto.return_date,
            overdue_days=dto.overdue_days,
            body=dto.body,
            percent=dto.percent,
            body_payments=dto.body_payments,
            interest_payments=dto.interest_payments,
        )


UserCreditItem = Annotated[
    ClosedCreditResponse | OpenCreditResponse,
    Field(discriminator="status"),
]
