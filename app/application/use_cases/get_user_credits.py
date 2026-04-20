from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.application.dto import ClosedCreditDTO, OpenCreditDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.enums import PaymentType
from app.domain.exceptions import UserNotFoundError


class GetUserCreditsUseCase:
    async def execute(
        self,
        uow: UnitOfWork,
        user_id: int,
        today: date,
    ) -> list[ClosedCreditDTO | OpenCreditDTO]:
        if not await uow.users.exists(user_id):
            raise UserNotFoundError(f"user with id={user_id} not found")

        credits = await uow.credits.list_by_user(user_id)
        if not credits:
            return []

        dictionary = await uow.dictionary.list_all()
        name_by_id = {entry.id: entry.name for entry in dictionary}

        credit_ids = [credit.id for credit in credits]
        payments = await uow.payments.list_by_credits(credit_ids)

        totals_by_credit: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
        by_type: dict[int, dict[str, Decimal]] = defaultdict(
            lambda: {PaymentType.body: Decimal(0), PaymentType.interest: Decimal(0)}
        )
        for payment in payments:
            totals_by_credit[payment.credit_id] += payment.sum
            type_name = name_by_id.get(payment.type_id)
            if type_name in (PaymentType.body, PaymentType.interest):
                by_type[payment.credit_id][type_name] += payment.sum

        result: list[ClosedCreditDTO | OpenCreditDTO] = []
        for credit in credits:
            if credit.is_closed:
                assert credit.actual_return_date is not None
                result.append(
                    ClosedCreditDTO(
                        issuance_date=credit.issuance_date,
                        return_date=credit.actual_return_date,
                        body=credit.body,
                        percent=credit.percent,
                        total_payments=totals_by_credit.get(credit.id, Decimal(0)),
                    )
                )
            else:
                overdue = max(0, (today - credit.return_date).days)
                bucket = by_type.get(
                    credit.id,
                    {PaymentType.body: Decimal(0), PaymentType.interest: Decimal(0)},
                )
                result.append(
                    OpenCreditDTO(
                        issuance_date=credit.issuance_date,
                        return_date=credit.return_date,
                        overdue_days=overdue,
                        body=credit.body,
                        percent=credit.percent,
                        body_payments=bucket[PaymentType.body],
                        interest_payments=bucket[PaymentType.interest],
                    )
                )

        return result
