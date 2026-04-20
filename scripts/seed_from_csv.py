from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infrastructure.db.session import create_engine, create_session_factory
from app.infrastructure.seed.csv_loader import CsvSeedLoader


_logger = get_logger(__name__)
_cli = typer.Typer(add_completion=False, help="Seed database from CSV files.")


async def _run(data_dir: Path) -> None:
    settings = get_settings()
    configure_logging(settings)

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    loader = CsvSeedLoader(data_dir)

    try:
        async with session_factory() as session:
            await loader.load_all(session)
            await session.commit()
    finally:
        await engine.dispose()

    _logger.info("csv_seed.completed", data_dir=str(data_dir))


@_cli.command()
def run(
    data_dir: Path = typer.Option(
        None,
        "--data-dir",
        "-d",
        help="Directory with CSV files. Defaults to settings.seed_data_dir.",
    ),
) -> None:
    target = data_dir or get_settings().seed_data_dir
    asyncio.run(_run(target))


if __name__ == "__main__":
    _cli()
