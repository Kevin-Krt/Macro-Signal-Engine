from datetime import UTC, date, datetime
from typing import Any

import httpx
import pytest
import respx
from pydantic import SecretStr

from app.modules.events.ingestion.exceptions import (
    ConnectorFetchError,
    ConnectorParseError,
)
from app.modules.events.ingestion.fred_calendar import (
    FRED_API_URL,
    FredCalendarConnector,
    _to_float,
)
from app.modules.events.ingestion.fred_indicators import INDICATORS

API_KEY = SecretStr("test-key")
TODAY = date(2026, 9, 25)
NFP = next(i for i in INDICATORS if i.series_id == "PAYEMS")

RELEASE_DATES_URL = f"{FRED_API_URL}/release/dates"
OBSERVATIONS_URL = f"{FRED_API_URL}/series/observations"


@pytest.fixture
def connector() -> FredCalendarConnector:
    return FredCalendarConnector(API_KEY, today=TODAY)


# --------------------------------------------------------------- pure functions


def test_to_float_reads_a_number() -> None:
    assert _to_float("162") == 162.0


def test_to_float_turns_a_missing_value_into_none() -> None:
    assert _to_float(".") is None


def test_draft_of_a_published_release(connector: FredCalendarConnector) -> None:
    draft = connector._to_draft(NFP, date(2026, 9, 4), date(2026, 8, 1), 162.0, 21.0)

    assert draft.source == "fred_calendar"
    assert draft.external_id == "PAYEMS:2026-09-04"
    assert draft.event_type == "calendar"
    assert draft.title == "Non-Farm Payrolls"
    assert draft.country == "US"
    assert draft.importance == "high"
    assert draft.payload["actual"] == 162.0
    assert draft.payload["previous"] == 21.0
    assert draft.payload["unit"] == "chg"
    assert draft.payload["reference_period"] == "2026-08-01"


def test_draft_of_an_upcoming_release(connector: FredCalendarConnector) -> None:
    draft = connector._to_draft(NFP, date(2026, 10, 2), None, None, None)

    assert draft.payload["actual"] is None
    assert draft.payload["reference_period"] is None
    assert draft.occurred_at > datetime(2026, 9, 25, tzinfo=UTC)


def test_draft_converts_summer_time_to_utc(connector: FredCalendarConnector) -> None:
    draft = connector._to_draft(NFP, date(2026, 9, 4), None, None, None)

    assert draft.occurred_at == datetime(2026, 9, 4, 12, 30, tzinfo=UTC)


def test_draft_converts_winter_time_to_utc(connector: FredCalendarConnector) -> None:
    draft = connector._to_draft(NFP, date(2026, 12, 4), None, None, None)

    assert draft.occurred_at == datetime(2026, 12, 4, 13, 30, tzinfo=UTC)


def test_payload_is_json_serialisable(connector: FredCalendarConnector) -> None:
    import json

    draft = connector._to_draft(NFP, date(2026, 9, 4), date(2026, 8, 1), 162.0, 21.0)
    json.dumps(draft.payload)


# ------------------------------------------------------------------ one request


@respx.mock
async def test_release_dates_asks_for_the_window(
    connector: FredCalendarConnector, fred_release_dates: dict[str, Any]
) -> None:
    route = respx.get(RELEASE_DATES_URL).mock(
        return_value=httpx.Response(200, json=fred_release_dates)
    )

    async with httpx.AsyncClient() as client:
        dates = await connector._fetch_release_dates(client, 50, published_only=False)

    assert dates[0] == date(2026, 11, 6)
    params = route.calls.last.request.url.params
    assert params["realtime_start"] == "2026-08-11"
    assert params["realtime_end"] == "2026-11-24"
    assert params["include_release_dates_with_no_data"] == "true"


@respx.mock
async def test_release_dates_can_ask_for_published_only(
    connector: FredCalendarConnector, fred_release_dates_published: dict[str, Any]
) -> None:
    route = respx.get(RELEASE_DATES_URL).mock(
        return_value=httpx.Response(200, json=fred_release_dates_published)
    )

    async with httpx.AsyncClient() as client:
        dates = await connector._fetch_release_dates(client, 50, published_only=True)

    assert dates == [date(2026, 9, 4), date(2026, 8, 7)]
    params = route.calls.last.request.url.params
    assert params["include_release_dates_with_no_data"] == "false"


@respx.mock
async def test_observations_use_the_indicator_unit(
    connector: FredCalendarConnector, fred_observations: dict[str, Any]
) -> None:
    route = respx.get(OBSERVATIONS_URL).mock(
        return_value=httpx.Response(200, json=fred_observations)
    )

    async with httpx.AsyncClient() as client:
        obs = await connector._fetch_observations(client, "PAYEMS", "chg")

    assert obs[0] == (date(2026, 8, 1), 162.0)
    assert obs[-1] == (date(2026, 5, 1), 63.0)
    assert route.calls.last.request.url.params["units"] == "chg"


# ----------------------------------------------------------------------- errors


@respx.mock
async def test_http_error_keeps_the_api_key_out_of_the_logs(
    connector: FredCalendarConnector,
) -> None:
    respx.get(RELEASE_DATES_URL).mock(
        return_value=httpx.Response(401, json={"error_code": 401})
    )

    async with httpx.AsyncClient() as client:
        with pytest.raises(ConnectorFetchError) as err:
            await connector._fetch_release_dates(client, 50, published_only=False)

    assert err.value.status == 401
    assert err.value.__cause__ is None, "the httpx error embeds the API key"
    assert err.value.__suppress_context__


@respx.mock
async def test_network_error_raises_without_a_status(
    connector: FredCalendarConnector,
) -> None:
    respx.get(RELEASE_DATES_URL).mock(side_effect=httpx.ConnectError("boom"))

    async with httpx.AsyncClient() as client:
        with pytest.raises(ConnectorFetchError) as err:
            await connector._fetch_release_dates(client, 50, published_only=False)

    assert err.value.status is None


@respx.mock
async def test_unexpected_body_raises_a_parse_error(
    connector: FredCalendarConnector,
) -> None:
    respx.get(RELEASE_DATES_URL).mock(
        return_value=httpx.Response(200, json={"error_message": "Bad Request."})
    )

    async with httpx.AsyncClient() as client:
        with pytest.raises(ConnectorParseError):
            await connector._fetch_release_dates(client, 50, published_only=False)


# ------------------------------------------------------------------ full fetch


@respx.mock
async def test_fetch_pairs_dates_with_values(
    connector: FredCalendarConnector,
    fred_release_dates: dict[str, Any],
    fred_release_dates_published: dict[str, Any],
    fred_observations: dict[str, Any],
) -> None:
    def release_dates(request: httpx.Request) -> httpx.Response:
        published = request.url.params["include_release_dates_with_no_data"] == "false"
        body = fred_release_dates_published if published else fred_release_dates
        return httpx.Response(200, json=body)

    respx.get(RELEASE_DATES_URL).mock(side_effect=release_dates)
    respx.get(OBSERVATIONS_URL).mock(
        return_value=httpx.Response(200, json=fred_observations)
    )

    async with httpx.AsyncClient() as client:
        drafts = await connector.fetch(client)

    by_id = {d.external_id: d for d in drafts}

    assert by_id["PAYEMS:2026-09-04"].payload["actual"] == 162.0
    assert by_id["PAYEMS:2026-09-04"].payload["previous"] == 21.0
    assert by_id["PAYEMS:2026-09-04"].payload["reference_period"] == "2026-08-01"

    assert by_id["PAYEMS:2026-08-07"].payload["actual"] == 21.0
    assert by_id["PAYEMS:2026-08-07"].payload["reference_period"] == "2026-07-01"

    assert by_id["PAYEMS:2026-10-02"].payload["actual"] is None
    assert by_id["PAYEMS:2026-11-06"].payload["actual"] is None
