from __future__ import annotations

import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.db.models import (
    CreditModel,
    DictionaryModel,
    PaymentModel,
    PlanModel,
    UserModel,
)

_logger = get_logger(__name__)


def _parse_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"cannot parse date: {value!r}")


def _parse_decimal(value: str) -> Decimal | None:
    value = value.strip()
    if not value:
        return None
    return Decimal(value.replace(",", "."))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters="\t,;")
        reader = csv.DictReader(fh, dialect=dialect)
        return [{k: (v or "") for k, v in row.items()} for row in reader]


class CsvSeedLoader:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    async def load_all(self, session: AsyncSession) -> None:
        await self._load_users(session)
        await self._load_dictionary(session)
        await self._load_credits(session)
        await self._load_plans(session)
        await self._load_payments(session)
        await session.flush()

    async def _load_users(self, session: AsyncSession) -> None:
        path = self._data_dir / "users.csv"
        if not path.exists():
            return
        existing = set((await session.scalars(select(UserModel.id))).all())
        rows = _read_rows(path)
        new_rows = [
            UserModel(
                id=int(row["id"]),
                login=row["login"],
                registration_date=_parse_date(row["registration_date"]),
            )
            for row in rows
            if int(row["id"]) not in existing
        ]
        if new_rows:
            session.add_all(new_rows)
            _logger.info("seed.users", inserted=len(new_rows))

    async def _load_dictionary(self, session: AsyncSession) -> None:
        path = self._data_dir / "dictionary.csv"
        if not path.exists():
            return
        existing = set((await session.scalars(select(DictionaryModel.id))).all())
        rows = _read_rows(path)
        new_rows = [
            DictionaryModel(id=int(row["id"]), name=row["name"])
            for row in rows
            if int(row["id"]) not in existing
        ]
        if new_rows:
            session.add_all(new_rows)
            _logger.info("seed.dictionary", inserted=len(new_rows))

    async def _load_credits(self, session: AsyncSession) -> None:
        path = self._data_dir / "credits.csv"
        if not path.exists():
            return
        existing = set((await session.scalars(select(CreditModel.id))).all())
        rows = _read_rows(path)
        new_rows = [
            CreditModel(
                id=int(row["id"]),
                user_id=int(row["user_id"]),
                issuance_date=_parse_date(row["issuance_date"]),
                return_date=_parse_date(row["return_date"]),
                actual_return_date=_parse_date(row["actual_return_date"]),
                body=_parse_decimal(row["body"]) or Decimal(0),
                percent=_parse_decimal(row["percent"]) or Decimal(0),
            )
            for row in rows
            if int(row["id"]) not in existing
        ]
        if new_rows:
            session.add_all(new_rows)
            _logger.info("seed.credits", inserted=len(new_rows))

    async def _load_plans(self, session: AsyncSession) -> None:
        path = self._data_dir / "plans.csv"
        if not path.exists():
            return
        existing = set((await session.scalars(select(PlanModel.id))).all())
        rows = _read_rows(path)
        new_rows = [
            PlanModel(
                id=int(row["id"]),
                period=_parse_date(row["period"]),
                sum=_parse_decimal(row["sum"]) or Decimal(0),
                category_id=int(row["category_id"]),
            )
            for row in rows
            if int(row["id"]) not in existing
        ]
        if new_rows:
            session.add_all(new_rows)
            _logger.info("seed.plans", inserted=len(new_rows))

    async def _load_payments(self, session: AsyncSession) -> None:
        path = self._data_dir / "payments.csv"
        if not path.exists():
            return
        existing = set((await session.scalars(select(PaymentModel.id))).all())
        rows = _read_rows(path)
        new_rows = [
            PaymentModel(
                id=int(row["id"]),
                credit_id=int(row["credit_id"]),
                payment_date=_parse_date(row["payment_date"]),
                type_id=int(row["type_id"]),
                sum=_parse_decimal(row["sum"]) or Decimal(0),
            )
            for row in rows
            if int(row["id"]) not in existing
        ]
        if new_rows:
            session.add_all(new_rows)
            _logger.info("seed.payments", inserted=len(new_rows))
