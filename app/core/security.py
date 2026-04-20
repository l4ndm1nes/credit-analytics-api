from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings
from app.domain.exceptions import InvalidCredentialsError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True, slots=True)
class TokenPayload:
    subject: str
    expires_at: datetime


class PasswordHasher:
    @staticmethod
    def hash(password: str) -> str:
        return _pwd_context.hash(password)

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        return _pwd_context.verify(password, hashed)


class JWTService:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key.get_secret_value()
        self._algorithm = settings.jwt_algorithm
        self._ttl = timedelta(minutes=settings.jwt_access_token_ttl_minutes)

    def issue(self, subject: str) -> tuple[str, datetime]:
        issued_at = datetime.now(UTC)
        expires_at = issued_at + self._ttl
        payload: dict[str, object] = {
            "sub": subject,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": secrets.token_hex(16),
        }
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return token, expires_at

    def decode(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError as exc:
            raise InvalidCredentialsError("invalid or expired token") from exc

        subject = payload.get("sub")
        exp = payload.get("exp")
        if not isinstance(subject, str) or not isinstance(exp, int):
            raise InvalidCredentialsError("malformed token payload")

        return TokenPayload(
            subject=subject,
            expires_at=datetime.fromtimestamp(exp, tz=UTC),
        )


def constant_time_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())
