from __future__ import annotations

from enum import StrEnum


class PlanCategory(StrEnum):
    issuance = "видача"
    collection = "збір"


class PaymentType(StrEnum):
    body = "тіло"
    interest = "відсотки"
