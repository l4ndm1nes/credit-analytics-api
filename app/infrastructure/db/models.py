from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    registration_date: Mapped[date] = mapped_column(Date, nullable=False)

    credits: Mapped[list[CreditModel]] = relationship(back_populates="user")


class DictionaryModel(Base):
    __tablename__ = "dictionary"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class CreditModel(Base):
    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    issuance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    return_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    body: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    percent: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    user: Mapped[UserModel] = relationship(back_populates="credits")
    payments: Mapped[list[PaymentModel]] = relationship(
        back_populates="credit", cascade="all, delete-orphan"
    )


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    credit_id: Mapped[int] = mapped_column(
        ForeignKey("credits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type_id: Mapped[int] = mapped_column(
        ForeignKey("dictionary.id", ondelete="RESTRICT"), nullable=False
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    sum: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    credit: Mapped[CreditModel] = relationship(back_populates="payments")


class PlanModel(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period: Mapped[date] = mapped_column(Date, nullable=False)
    sum: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("dictionary.id", ondelete="RESTRICT"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("period", "category_id", name="uq_plans_period_category"),
        Index("ix_plans_period", "period"),
    )


class AuthUserModel(Base):
    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
