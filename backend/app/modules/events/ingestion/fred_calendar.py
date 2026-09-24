from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import structlog
from pydantic import BaseModel, ConfigDict, SecretStr

from app.core.types import FredUnits
from app.modules.events.ingestion.base import EventDraft
from app.modules.events.ingestion.exceptions import (
    ConnectorFetchError,
    ConnectorParseError,
)
from app.modules.events.ingestion.fred_indicators import INDICATORS, Indicator

log = structlog.get_logger(__name__)

FRED_API_URL = "https://api.stlouisfed.org/fred"
REQUEST_TIMEOUT_SECONDS = 10.0


def _to_float(raw: str) -> float | None:
    return None if raw == "." else float(raw)


class FredCalendarPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    actual: float | None = None
    previous: float | None = None
    unit: FredUnits
    reference_period: date | None = None
    series_id: str
    release_id: int


class FredCalendarConnector:
    name = "fred_calendar"

    def __init__(
        self,
        api_key: SecretStr,
        *,
        today: date | None = None,
        lookback_days: int = 45,
        lookahead_days: int = 60,
    ) -> None:
        self._api_key = api_key
        self._today = today or date.today()
        self._window_start = self._today - timedelta(days=lookback_days)
        self._window_end = self._today + timedelta(days=lookahead_days)

    async def _get(
        self, client: httpx.AsyncClient, path: str, params: Mapping[str, str | int]
    ) -> dict[str, Any]:

        base = {"api_key": self._api_key.get_secret_value(), "file_type": "json"}

        try:
            response = await client.get(
                f"{FRED_API_URL}/{path}",
                params={**base, **params},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ConnectorFetchError(self.name, exc.response.status_code) from None
        except httpx.RequestError:
            raise ConnectorFetchError(self.name) from None

        try:
            body = response.json()
        except ValueError as exc:
            raise ConnectorParseError(self.name) from exc

        if not isinstance(body, dict):
            raise ConnectorParseError(self.name)

        return body

    async def _fetch_release_dates(
        self, client: httpx.AsyncClient, release_id: int, *, published_only: bool
    ) -> list[date]:
        path = "release/dates"
        params = {
            "release_id": release_id,
            "realtime_start": self._window_start.isoformat(),
            "realtime_end": self._window_end.isoformat(),
            "order_by": "release_date",
            "sort_order": "desc",
            "include_release_dates_with_no_data": "false" if published_only else "true",
        }

        body = await self._get(client, path, params)
        try:
            return [date.fromisoformat(row["date"]) for row in body["release_dates"]]
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectorParseError(self.name) from exc

    async def _fetch_observations(
        self, client: httpx.AsyncClient, series_id: str, units: FredUnits
    ) -> list[tuple[date, float | None]]:

        path = "series/observations"
        params = {
            "series_id": series_id,
            "units": units,
            "order_by": "observation_date",
            "sort_order": "desc",
            "limit": 13,
        }

        body = await self._get(client, path, params)
        try:
            return [
                (date.fromisoformat(x["date"]), _to_float(x["value"]))
                for x in body["observations"]
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectorParseError(self.name) from exc

    def _to_draft(
        self,
        indicator: Indicator,
        release_date: date,
        period: date | None,
        actual: float | None,
        previous: float | None,
    ) -> EventDraft:

        payload = FredCalendarPayload(
            actual=actual,
            previous=previous,
            unit=indicator.units,
            reference_period=period,
            series_id=indicator.series_id,
            release_id=indicator.release_id,
        )
        return EventDraft(
            source=self.name,
            external_id=f"{indicator.series_id}:{release_date.isoformat()}",
            event_type="calendar",
            title=indicator.title,
            url=f"https://fred.stlouisfed.org/series/{indicator.series_id}",
            occurred_at=datetime.combine(
                release_date,
                indicator.release_time,
                tzinfo=ZoneInfo(indicator.time_zone),
            ).astimezone(UTC),
            category=indicator.category,
            country=indicator.country,
            importance=indicator.importance,
            payload=payload.model_dump(mode="json"),
        )

    async def fetch(self, client: httpx.AsyncClient) -> Sequence[EventDraft]:
        by_release: dict[int, list[Indicator]] = {}
        drafts: list[EventDraft] = []
        rejected = 0

        for indicator in INDICATORS:
            by_release.setdefault(indicator.release_id, []).append(indicator)

        for release_id, indicators in by_release.items():
            all_dates = await self._fetch_release_dates(
                client, release_id, published_only=False
            )
            published = await self._fetch_release_dates(
                client, release_id, published_only=True
            )

            for indicator in indicators:
                try:
                    obs = await self._fetch_observations(
                        client, indicator.series_id, indicator.units
                    )
                except ConnectorParseError as exc:
                    rejected += 1
                    log.warning(
                        "obs_parsing_rejected",
                        source=self.name,
                        external_id=indicator.series_id,
                        reason=type(exc).__name__,
                    )
                    continue

                if len(published) > len(obs):
                    log.warning(
                        "inconsistency_dates",
                        source=self.name,
                        external_id=indicator.series_id,
                        reason="InconsistencyObservedPublishedDatesError",
                    )
                    rejected += 1
                    continue

                for release_date in all_dates:
                    if release_date in published:
                        idx = published.index(release_date)

                        period, actual = obs[idx]
                        previous = obs[idx + 1][1] if (idx + 1) < len(obs) else None
                        drafts.append(
                            self._to_draft(
                                indicator=indicator,
                                release_date=release_date,
                                period=period,
                                actual=actual,
                                previous=previous,
                            )
                        )
                    else:
                        drafts.append(
                            self._to_draft(
                                indicator=indicator,
                                release_date=release_date,
                                period=None,
                                actual=None,
                                previous=None,
                            )
                        )
        log.info(
            "calendar_series_parsed",
            source=self.name,
            indicators=len(INDICATORS),
            drafts=len(drafts),
            rejected=rejected,
        )
        if INDICATORS and not drafts:
            raise ConnectorParseError(self.name)

        return drafts
