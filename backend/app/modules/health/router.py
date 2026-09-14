import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.exceptions import HealthCheckError

health_router = APIRouter()

HEALTH_TIMEOUT_SECONDS = 2


async def check_database(session: AsyncSession) -> bool:
    try:
        async with asyncio.timeout(HEALTH_TIMEOUT_SECONDS):
            result = await session.execute(text("SELECT 1"))
        return result.scalar() == 1
    except (SQLAlchemyError, TimeoutError):
        return False


async def check_redis(settings: Settings) -> bool:
    client = Redis.from_url(
        str(settings.redis_url),
        socket_connect_timeout=HEALTH_TIMEOUT_SECONDS,
        socket_timeout=HEALTH_TIMEOUT_SECONDS,
        decode_responses=True,
    )
    try:
        async with asyncio.timeout(HEALTH_TIMEOUT_SECONDS):
            await client.ping()
        return True
    except (RedisError, TimeoutError):
        return False
    finally:
        await client.aclose()


@health_router.get("/health")
async def health(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:

    checks: dict[str, bool] = {}

    checks["database"], checks["redis"] = await asyncio.gather(
        check_database(session), check_redis(settings)
    )

    if not all(checks.values()):
        raise HealthCheckError(checks)

    return JSONResponse(
        status_code=200, content={"status": "ok", "checks": checks}
    )
