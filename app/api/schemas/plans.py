from __future__ import annotations

from pydantic import BaseModel


class PlansInsertResponse(BaseModel):
    inserted: int
    message: str = "plans uploaded successfully"
