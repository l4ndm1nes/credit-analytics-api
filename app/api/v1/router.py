from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, credits, performance, plans

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(credits.router)
api_router.include_router(plans.router)
api_router.include_router(performance.router)
