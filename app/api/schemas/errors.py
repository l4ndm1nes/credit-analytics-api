from __future__ import annotations

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    location: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []


class ErrorResponse(BaseModel):
    error: ErrorBody
