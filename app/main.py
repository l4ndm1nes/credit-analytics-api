from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.errors import register_exception_handlers
from app.api.v1.router import api_router
from app.application.use_cases.auth import BootstrapAdminUseCase, IssueAccessTokenUseCase
from app.application.use_cases.get_user_credits import GetUserCreditsUseCase
from app.application.use_cases.insert_plans import InsertPlansUseCase
from app.application.use_cases.plans_performance import PlansPerformanceUseCase
from app.application.use_cases.year_performance import YearPerformanceUseCase
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.core.security import JWTService
from app.infrastructure.auth.authenticator import build_authenticator
from app.infrastructure.db.session import create_engine, create_session_factory
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.excel.plans_parser import PlansExcelParser
from app.infrastructure.seed.csv_loader import CsvSeedLoader

_logger = get_logger(__name__)


def _build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings)

        engine = create_engine(settings)
        session_factory = create_session_factory(engine)

        jwt_service = JWTService(settings)
        authenticator = build_authenticator(settings, jwt_service)

        app.state.settings = settings
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.uow_factory = SqlAlchemyUnitOfWork
        app.state.authenticator = authenticator
        app.state.jwt_service = jwt_service

        app.state.issue_access_token_use_case = IssueAccessTokenUseCase(jwt_service)
        app.state.get_user_credits_use_case = GetUserCreditsUseCase()
        app.state.insert_plans_use_case = InsertPlansUseCase(PlansExcelParser())
        app.state.plans_performance_use_case = PlansPerformanceUseCase()
        app.state.year_performance_use_case = YearPerformanceUseCase()

        bootstrap = BootstrapAdminUseCase()
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await bootstrap.execute(
                uow,
                login=settings.bootstrap_admin_login,
                password=settings.bootstrap_admin_password.get_secret_value(),
            )

        if settings.seed_on_startup:
            loader = CsvSeedLoader(settings.seed_data_dir)
            async with session_factory() as session:
                await loader.load_all(session)
                await session.commit()
            _logger.info("csv_seed.completed")

        _logger.info("application.started", env=settings.app_env.value)

        try:
            yield
        finally:
            await engine.dispose()
            _logger.info("application.stopped")

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="Credit Analytics API",
        version="1.0.0",
        debug=settings.app_debug,
        lifespan=_build_lifespan(settings),
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/health", include_in_schema=False)
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


app = create_app()
