import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

import app.registry  # noqa: F401  imports every model so metadata is complete
from app.core.config import get_settings
from app.core.database import Base

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture
def finnhub_articles() -> list[dict[str, Any]]:
    """
    Three real articles, as returned by GET /api/v1/news.
    """
    return load_fixture("finnhub_news.json")


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    settings = get_settings()
    assert settings.test_database_url is not None, "APP_TEST_DATABASE_URL is required"

    engine = create_async_engine(str(settings.test_database_url), poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def connection(engine: AsyncEngine) -> AsyncGenerator[AsyncConnection]:
    async with engine.connect() as conn:
        transaction = await conn.begin()
        yield conn
        await transaction.rollback()


@pytest.fixture
async def session(connection: AsyncConnection) -> AsyncGenerator[AsyncSession]:
    maker = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    async with maker() as session:
        yield session
