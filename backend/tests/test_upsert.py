from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.ingestion.base import EventDraft
from app.modules.events.models import Event
from app.modules.events.repository import upsert_events


def make_draft(**kw: Any) -> EventDraft:
    defaults: dict[str, Any] = {
        "source": "finnhub_news",
        "external_id": "8482443",
        "event_type": "news",
        "title": "US CPI",
        "occurred_at": datetime(2026, 9, 10, 12, 30, tzinfo=UTC),
    }
    return EventDraft(**(defaults | kw))


async def count_events(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Event)) or 0


async def test_upsert_inserts_new_events(session: AsyncSession) -> None:
    inserted = await upsert_events(
        session, [make_draft(), make_draft(external_id="8479729")]
    )
    await session.commit()

    assert inserted == 2
    assert await count_events(session) == 2


async def test_upsert_twice_does_not_duplicate(session: AsyncSession) -> None:
    drafts = [make_draft(), make_draft(external_id="8479729")]

    await upsert_events(session, drafts)
    await session.commit()
    await upsert_events(session, drafts)
    await session.commit()

    assert await count_events(session) == 2


async def test_upsert_updates_the_changed_fields(session: AsyncSession) -> None:
    await upsert_events(session, [make_draft(title="US CPI")])
    await session.commit()

    await upsert_events(session, [make_draft(title="US CPI (revised)")])
    await session.commit()

    event = await session.scalar(select(Event))
    assert event is not None
    assert event.title == "US CPI (revised)"


async def test_upsert_keeps_the_first_ingested_at(session: AsyncSession) -> None:
    await upsert_events(session, [make_draft()])
    await session.commit()
    first = await session.scalar(select(Event.ingested_at))

    await upsert_events(session, [make_draft(title="changed")])
    await session.commit()
    second = await session.scalar(select(Event.ingested_at))

    assert first == second


async def test_upsert_never_changes_the_key(session: AsyncSession) -> None:
    await upsert_events(session, [make_draft()])
    await session.commit()
    event_id = await session.scalar(select(Event.id))

    await upsert_events(session, [make_draft(title="changed")])
    await session.commit()

    assert await session.scalar(select(Event.id)) == event_id


async def test_upsert_deduplicates_within_a_batch(session: AsyncSession) -> None:
    inserted = await upsert_events(
        session, [make_draft(title="first"), make_draft(title="last")]
    )
    await session.commit()

    assert inserted == 1
    assert await count_events(session) == 1
    event = await session.scalar(select(Event))
    assert event is not None
    assert event.title == "last"


async def test_upsert_accepts_an_empty_batch(session: AsyncSession) -> None:
    assert await upsert_events(session, []) == 0
    assert await count_events(session) == 0


async def test_upsert_keeps_sources_apart(session: AsyncSession) -> None:
    await upsert_events(
        session,
        [make_draft(), make_draft(source="fred_calendar", event_type="calendar")],
    )
    await session.commit()

    assert await count_events(session) == 2
