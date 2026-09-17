from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from pydantic import SecretStr, ValidationError

from app.modules.events.ingestion.base import EventDraft
from app.modules.events.ingestion.exceptions import (
    ConnectorFetchError,
    ConnectorParseError,
)

log = structlog.get_logger(__name__)

FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"
REQUEST_TIMEOUT_SECONDS = 10.0


class FinnhubNewsConnector:
    """Fetches general market news from Finnhub."""

    name = "finnhub_news"

    def __init__(self, finnhub_api_key: SecretStr) -> None:
        self._api_key = finnhub_api_key

    async def fetch(self, client: httpx.AsyncClient) -> Sequence[EventDraft]:
        articles = await self._fetch_raw(client)
        return self._parse(articles)

    async def _fetch_raw(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        try:
            response = await client.get(
                FINNHUB_NEWS_URL,
                params={
                    "category": "general",
                    "token": self._api_key.get_secret_value(),
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ConnectorFetchError(self.name, exc.response.status_code) from exc
        except httpx.RequestError as exc:
            raise ConnectorFetchError(self.name) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ConnectorParseError(self.name) from exc

        if not isinstance(payload, list):
            raise ConnectorParseError(self.name)

        return payload

    def _parse(self, articles: list[dict[str, Any]]) -> list[EventDraft]:
        drafts: list[EventDraft] = []
        rejected = 0

        for article in articles:
            external_id = str(article.get("id", ""))
            try:
                drafts.append(self._to_draft(article, external_id))
            except (KeyError, TypeError, ValueError, ValidationError) as exc:
                rejected += 1
                log.warning(
                    "draft_rejected",
                    source=self.name,
                    external_id=external_id or None,
                    reason=type(exc).__name__,
                )

        log.info(
            "articles_parsed",
            source=self.name,
            received=len(articles),
            parsed=len(drafts),
            rejected=rejected,
        )

        if articles and not drafts:
            raise ConnectorParseError(self.name)

        return drafts

    def _to_draft(self, article: dict[str, Any], external_id: str) -> EventDraft:
        return EventDraft(
            source=self.name,
            external_id=external_id,
            event_type="news",
            title=article["headline"],
            summary=article.get("summary") or None,
            url=article.get("url") or None,
            occurred_at=datetime.fromtimestamp(article["datetime"], UTC),
            payload={
                "provider": article.get("source"),
                "related": article.get("related"),
                "image": article.get("image"),
                "category": article.get("category"),
            },
        )
