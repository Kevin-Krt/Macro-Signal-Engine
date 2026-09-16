from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
import respx
from pydantic import SecretStr

from app.modules.events.ingestion.exceptions import (
    ConnectorFetchError,
    ConnectorParseError,
)
from app.modules.events.ingestion.finnhub_news import (
    FINNHUB_NEWS_URL,
    FinnhubNewsConnector,
)

API_KEY = SecretStr("test-key")


@pytest.fixture
def connector() -> FinnhubNewsConnector:
    return FinnhubNewsConnector(API_KEY)


# ----------------------------------------------------------------- parsing only


def test_parse_maps_every_field(
    connector: FinnhubNewsConnector, finnhub_articles: list[dict[str, Any]]
) -> None:
    drafts = connector._parse(finnhub_articles)

    assert len(drafts) == 3
    first = drafts[0]
    assert first.source == "finnhub_news"
    assert first.external_id == "8482443"
    assert first.event_type == "news"
    assert first.title.startswith("New attacks in Hormuz")
    assert first.payload["provider"] == "Reuters"


def test_parse_returns_utc_datetimes(
    connector: FinnhubNewsConnector, finnhub_articles: list[dict[str, Any]]
) -> None:
    drafts = connector._parse(finnhub_articles)

    for draft in drafts:
        assert draft.occurred_at.tzinfo is not None
        assert draft.occurred_at.utcoffset() == UTC.utcoffset(None)

    assert drafts[0].occurred_at == datetime(2026, 9, 13, 2, 22, tzinfo=UTC)


def test_parse_turns_empty_strings_into_none(
    connector: FinnhubNewsConnector, finnhub_articles: list[dict[str, Any]]
) -> None:
    assert finnhub_articles[2]["summary"] == ""
    assert connector._parse(finnhub_articles)[2].summary is None


def test_parse_skips_a_broken_article(
    connector: FinnhubNewsConnector, finnhub_articles: list[dict[str, Any]]
) -> None:
    broken = {k: v for k, v in finnhub_articles[0].items() if k != "headline"}
    drafts = connector._parse([broken, finnhub_articles[1]])

    assert len(drafts) == 1
    assert drafts[0].external_id == "8479729"


def test_parse_raises_when_every_article_is_broken(
    connector: FinnhubNewsConnector, finnhub_articles: list[dict[str, Any]]
) -> None:
    broken = finnhub_articles[0] | {"datetime": "not a timestamp"}

    with pytest.raises(ConnectorParseError) as err:
        connector._parse([broken])

    assert err.value.source == "finnhub_news"


def test_parse_accepts_an_empty_list(connector: FinnhubNewsConnector) -> None:
    assert connector._parse([]) == []


# ------------------------------------------------------------------ full fetch


@respx.mock
async def test_fetch_returns_drafts(
    connector: FinnhubNewsConnector, finnhub_articles: list[dict[str, Any]]
) -> None:
    route = respx.get(FINNHUB_NEWS_URL).mock(
        return_value=httpx.Response(200, json=finnhub_articles)
    )

    async with httpx.AsyncClient() as client:
        drafts = await connector.fetch(client)

    assert len(drafts) == 3
    request = route.calls.last.request
    assert request.url.params["category"] == "general"
    assert request.url.params["token"] == "test-key"


@respx.mock
async def test_fetch_raises_on_http_error(connector: FinnhubNewsConnector) -> None:
    respx.get(FINNHUB_NEWS_URL).mock(
        return_value=httpx.Response(401, json={"error": "no access"})
    )

    async with httpx.AsyncClient() as client:
        with pytest.raises(ConnectorFetchError) as err:
            await connector.fetch(client)

    assert err.value.status == 401


@respx.mock
async def test_fetch_raises_on_network_error(connector: FinnhubNewsConnector) -> None:
    respx.get(FINNHUB_NEWS_URL).mock(side_effect=httpx.ConnectError("boom"))

    async with httpx.AsyncClient() as client:
        with pytest.raises(ConnectorFetchError) as err:
            await connector.fetch(client)

    assert err.value.status is None


@respx.mock
async def test_fetch_raises_when_body_is_not_a_list(
    connector: FinnhubNewsConnector,
) -> None:
    respx.get(FINNHUB_NEWS_URL).mock(
        return_value=httpx.Response(200, json={"error": "no access"})
    )

    async with httpx.AsyncClient() as client:
        with pytest.raises(ConnectorParseError):
            await connector.fetch(client)
