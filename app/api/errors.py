from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse
from app.core.logging import get_logger
from app.domain.exceptions import (
    AuthorizationError,
    ConflictError,
    DomainError,
    InvalidCredentialsError,
    NotFoundError,
    ValidationError,
)

_logger = get_logger(__name__)


_DOMAIN_STATUS_MAP: tuple[tuple[type[DomainError], int], ...] = (
    (NotFoundError, status.HTTP_404_NOT_FOUND),
    (InvalidCredentialsError, status.HTTP_401_UNAUTHORIZED),
    (AuthorizationError, status.HTTP_403_FORBIDDEN),
    (ConflictError, status.HTTP_409_CONFLICT),
    (ValidationError, status.HTTP_422_UNPROCESSABLE_ENTITY),
)


def _status_for(exc: DomainError) -> int:
    for exc_type, status_code in _DOMAIN_STATUS_MAP:
        if isinstance(exc, exc_type):
            return status_code
    return status.HTTP_400_BAD_REQUEST


def _build_response(exc: DomainError) -> JSONResponse:
    details: list[ErrorDetail] = []
    if isinstance(exc, ValidationError):
        details = [ErrorDetail(location=i.location, message=i.message) for i in exc.issues]
    body = ErrorResponse(error=ErrorBody(code=exc.code, message=exc.message, details=details))
    return JSONResponse(
        status_code=_status_for(exc),
        content=jsonable_encoder(body),
    )


async def _handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    _logger.warning("domain_error", code=exc.code, message=exc.message, path=request.url.path)
    return _build_response(exc)


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        ErrorDetail(
            location=".".join(str(part) for part in err["loc"]),
            message=err["msg"],
        )
        for err in exc.errors()
    ]
    body = ErrorResponse(
        error=ErrorBody(code="request_validation_error", message="invalid request", details=details)
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(body),
    )


async def _handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
    _logger.exception("unhandled_error", path=request.url.path)
    body = ErrorResponse(
        error=ErrorBody(code="internal_error", message="internal server error", details=[])
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(body),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unhandled)
