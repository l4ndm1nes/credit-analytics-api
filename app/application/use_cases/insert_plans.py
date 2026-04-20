from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities import Plan
from app.domain.exceptions import InvalidPlansFileError, ValidationIssue
from app.infrastructure.excel.plans_parser import PlansExcelParser


@dataclass(frozen=True, slots=True)
class InsertPlansResult:
    inserted: int


class InsertPlansUseCase:
    def __init__(self, parser: PlansExcelParser) -> None:
        self._parser = parser

    async def execute(self, uow: UnitOfWork, file_content: bytes) -> InsertPlansResult:
        rows = await asyncio.to_thread(self._parser.parse, file_content)

        dictionary = await uow.dictionary.list_all()
        category_id_by_name = {entry.name: entry.id for entry in dictionary}

        issues: list[ValidationIssue] = []
        to_insert: list[Plan] = []
        seen_keys: set[tuple[object, int]] = set()

        for index, row in enumerate(rows, start=1):
            category_id = category_id_by_name.get(row.category_name)
            if category_id is None:
                issues.append(
                    ValidationIssue(
                        location=f"row {index + 1}, category",
                        message=f"unknown category: {row.category_name!r}",
                    )
                )
                continue

            key = (row.period, category_id)
            if key in seen_keys:
                issues.append(
                    ValidationIssue(
                        location=f"row {index + 1}",
                        message="duplicate period/category inside file",
                    )
                )
                continue
            seen_keys.add(key)

            if await uow.plans.exists_for_period_category(row.period, category_id):
                issues.append(
                    ValidationIssue(
                        location=f"row {index + 1}",
                        message=(
                            f"plan already exists for period={row.period.isoformat()}, "
                            f"category={row.category_name!r}"
                        ),
                    )
                )
                continue

            to_insert.append(Plan(id=0, period=row.period, sum=row.sum, category_id=category_id))

        if issues:
            raise InvalidPlansFileError("plans file contains errors", issues=issues)

        await uow.plans.bulk_insert(to_insert)
        await uow.commit()
        return InsertPlansResult(inserted=len(to_insert))
