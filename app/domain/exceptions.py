from __future__ import annotations

from dataclasses import dataclass


class DomainError(Exception):
    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    code = "not_found"


class UserNotFoundError(NotFoundError):
    code = "user_not_found"


class InvalidCredentialsError(DomainError):
    code = "invalid_credentials"


class AuthorizationError(DomainError):
    code = "unauthorized"


class ConflictError(DomainError):
    code = "conflict"


class PlanAlreadyExistsError(ConflictError):
    code = "plan_already_exists"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    location: str
    message: str


class ValidationError(DomainError):
    code = "validation_error"

    def __init__(self, message: str, issues: list[ValidationIssue] | None = None) -> None:
        super().__init__(message)
        self.issues: list[ValidationIssue] = issues or []


class InvalidPlansFileError(ValidationError):
    code = "invalid_plans_file"
