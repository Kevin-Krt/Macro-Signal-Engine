import asyncio

import httpx
import structlog

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import async_session_maker
from app.modules.events.ingestion.finnhub_news import FinnhubNewsConnector
from app.modules.events.repository import upsert_events

log = structlog.get_logger(__name__)


@celery_app.task(name="events.ingest_news")
def ingest_news() -> int:
    """
    Celery entry point: runs the async ingestion and returns the event count.
    """
    return asyncio.run(_ingest_news())


async def _ingest_news() -> int:
    """
    Fetch the latest news and upsert them.

    Connector failures are not caught here: Celery needs the exception to
    decide whether the task should be retried.
    """
    settings = get_settings()
    connector = FinnhubNewsConnector(settings.finnhub_api_key)

    async with httpx.AsyncClient() as client:
        drafts = await connector.fetch(client)

    async with async_session_maker() as session:
        count = await upsert_events(session, drafts)
        await session.commit()

    log.info("ingestion_completed", source=connector.name, events=count)
    return count
