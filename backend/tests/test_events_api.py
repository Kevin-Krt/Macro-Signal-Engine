from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import Event

# 2026-09-07 is a Monday, 2026-09-11 the Friday of the same week.
MONDAY = "2026-09-07"
FRIDAY = "2026-09-11"


def make_calendar_event(**kw: Any) -> Event:
    defaults: dict[str, Any] = {
        "source": "fred_calendar",
        "external_id": "CPIAUCSL:2026-09-11",
        "event_type": "calendar",
        "title": "CPI (YoY)",
        "occurred_at": datetime(2026, 9, 11, 12, 30, tzinfo=UTC),
        "country": "US",
        "importance": "high",
        "category": "inflation",
        "payload": {"actual": 3.35, "previous": 3.30, "unit": "pc1"},
    }
    return Event(**(defaults | kw))


def make_news_event(**kw: Any) -> Event:
    defaults: dict[str, Any] = {
        "source": "finnhub_news",
        "external_id": "8482443",
        "event_type": "news",
        "title": "Fed defies expectations",
        "summary": "Fed defies expectations  Reuters",
        "url": "https://news.google.com/rss/articles/CBM",
        "occurred_at": datetime(2026, 9, 11, 6, 0, tzinfo=UTC),
        "payload": {"provider": "Reuters"},
    }
    return Event(**(defaults | kw))


# ------------------------------------------------------------------- calendar


async def test_calendar_returns_the_events_of_the_week(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(make_calendar_event())
    await session.commit()

    response = await api_client.get(f"/api/events/calendar?week={FRIDAY}")

    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == MONDAY
    assert body["week_end"] == "2026-09-13"
    assert [event["title"] for event in body["events"]] == ["CPI (YoY)"]


async def test_calendar_flattens_the_payload(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(make_calendar_event())
    await session.commit()

    body = (await api_client.get(f"/api/events/calendar?week={MONDAY}")).json()
    event = body["events"][0]

    assert event["actual"] == 3.35
    assert event["previous"] == 3.30
    assert event["unit"] == "pc1"
    assert event["importance"] == "high"
    assert "payload" not in event


async def test_calendar_leaves_an_upcoming_event_without_a_value(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(
        make_calendar_event(payload={"actual": None, "previous": None, "unit": "pc1"})
    )
    await session.commit()

    body = (await api_client.get(f"/api/events/calendar?week={MONDAY}")).json()

    assert body["events"][0]["actual"] is None


async def test_calendar_ignores_news(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(make_news_event())
    await session.commit()

    body = (await api_client.get(f"/api/events/calendar?week={MONDAY}")).json()

    assert body["events"] == []


async def test_calendar_ignores_another_week(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(make_calendar_event())
    await session.commit()

    body = (await api_client.get("/api/events/calendar?week=2026-09-14")).json()

    assert body["events"] == []


async def test_calendar_sorts_by_date(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(
        make_calendar_event(
            external_id="b", occurred_at=datetime(2026, 9, 11, 12, 30, tzinfo=UTC)
        )
    )
    session.add(
        make_calendar_event(
            external_id="a",
            title="Retail Sales (MoM)",
            occurred_at=datetime(2026, 9, 8, 12, 30, tzinfo=UTC),
        )
    )
    await session.commit()

    body = (await api_client.get(f"/api/events/calendar?week={MONDAY}")).json()

    assert [event["title"] for event in body["events"]] == [
        "Retail Sales (MoM)",
        "CPI (YoY)",
    ]


async def test_calendar_without_a_week_uses_today(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/events/calendar")

    assert response.status_code == 200
    assert response.json()["week_start"] is not None


# ----------------------------------------------------------------------- news


async def test_news_returns_the_newest_first(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(
        make_news_event(
            external_id="old",
            title="Older",
            occurred_at=datetime(2026, 9, 10, 6, 0, tzinfo=UTC),
        )
    )
    session.add(
        make_news_event(
            external_id="new",
            title="Newer",
            occurred_at=datetime(2026, 9, 12, 6, 0, tzinfo=UTC),
        )
    )
    await session.commit()

    body = (await api_client.get("/api/events/news")).json()

    assert [event["title"] for event in body["events"]] == ["Newer", "Older"]


async def test_news_ignores_calendar_events(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(make_calendar_event())
    await session.commit()

    body = (await api_client.get("/api/events/news")).json()

    assert body["events"] == []


async def test_news_flattens_the_provider(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(make_news_event())
    await session.commit()

    event = (await api_client.get("/api/events/news")).json()["events"][0]

    assert event["provider"] == "Reuters"
    assert "payload" not in event


async def test_news_last_page_has_no_cursor(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(make_news_event())
    await session.commit()

    body = (await api_client.get("/api/events/news?limit=10")).json()

    assert body["next_cursor"] is None


async def test_news_pagination_never_repeats(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    for day in range(1, 6):
        session.add(
            make_news_event(
                external_id=f"n{day}",
                title=f"Article {day}",
                occurred_at=datetime(2026, 9, day, 6, 0, tzinfo=UTC),
            )
        )
    await session.commit()

    first = (await api_client.get("/api/events/news?limit=2")).json()
    assert len(first["events"]) == 2
    assert first["next_cursor"] is not None

    second = (
        await api_client.get(f"/api/events/news?limit=2&before={first['next_cursor']}")
    ).json()

    first_ids = {event["id"] for event in first["events"]}
    second_ids = {event["id"] for event in second["events"]}
    assert not first_ids & second_ids


async def test_news_search_is_case_insensitive(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    session.add(make_news_event(external_id="a", title="Fed defies expectations"))
    session.add(make_news_event(external_id="b", title="Oil slides on truce hopes"))
    await session.commit()

    body = (await api_client.get("/api/events/news?q=FED")).json()

    assert [event["title"] for event in body["events"]] == ["Fed defies expectations"]


@pytest.mark.parametrize("limit", [0, 101])
async def test_news_rejects_an_out_of_range_limit(
    api_client: AsyncClient, limit: int
) -> None:
    response = await api_client.get(f"/api/events/news?limit={limit}")

    assert response.status_code == 422
