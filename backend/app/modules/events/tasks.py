import asyncio

import httpx
import structlog

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import async_session_maker
from app.modules.events.ingestion.base import REQUEST_TIMEOUT_SECONDS, SourceConnector
from app.modules.events.ingestion.exceptions import ConnectorFetchError
from app.modules.events.ingestion.finnhub_news import FinnhubNewsConnector
from app.modules.events.ingestion.fred_calendar import FredCalendarConnector
from app.modules.events.repository import upsert_events

log = structlog.get_logger(__name__)

# Only ConnectorFetchError is retried: it means the source was briefly
# unavailable. A ConnectorParseError means its format changed, and a 401 means
# the API key is wrong — neither is fixed by trying again.
RETRY_POLICY = {
    "autoretry_for": (ConnectorFetchError,),
    "retry_backoff": 5,
    "retry_backoff_max": 300,
    "retry_jitter": True,
    "max_retries": 3,
}


async def _ingest(connector: SourceConnector, *, freeze_payload: bool) -> int:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        drafts = await connector.fetch(client)

    async with async_session_maker() as session:
        count = await upsert_events(session, drafts, freeze_payload=freeze_payload)
        await session.commit()

    log.info("ingestion_completed", source=connector.name, events=count)
    return count


@celery_app.task(name="events.ingest_news", **RETRY_POLICY)
def ingest_news() -> int:
    """
    Ingest the latest market news from Finnhub.

    Articles are updated in place: a headline corrected by the source should
    reach the timeline, hence `freeze_payload=False`.
    """
    settings = get_settings()
    return asyncio.run(
        _ingest(FinnhubNewsConnector(settings.finnhub_api_key), freeze_payload=False)
    )


@celery_app.task(name="events.ingest_calendar", **RETRY_POLICY)
def ingest_calendar() -> int:
    """
    Ingest the US economic calendar from FRED.

    A published figure keeps the number that was announced that day:
    FRED revises its series afterwards — July payrolls went from -23k to
    +21k — and the timeline must show what the market saw.
    """
    settings = get_settings()
    return asyncio.run(
        _ingest(FredCalendarConnector(settings.fred_api_key), freeze_payload=True)
    )
