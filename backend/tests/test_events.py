from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import Event


def make_event(**kw: object) -> Event:
    defaults = {
        "source": "fred",
        "external_id": "CPI-2026-09",
        "event_type": "calendar",
        "title": "US CPI",
        "occurred_at": datetime(2026, 9, 10, 12, 30, tzinfo=UTC),
    }
    return Event(**{**defaults, **kw})


async def test_insert_event(session: AsyncSession) -> None:
    session.add(make_event())
    await session.commit()
    assert await session.scalar(select(func.count()).select_from(Event)) == 1


async def test_same_source_and_external_id_is_rejected(session: AsyncSession) -> None:
    session.add(make_event())
    await session.commit()

    session.add(make_event(title="US CPI (revised)"))
    with pytest.raises(IntegrityError) as err:
        await session.commit()

    assert "uq_events_source_external_id" in str(err.value)


async def test_same_external_id_from_another_source_is_allowed(
    session: AsyncSession,
) -> None:
    session.add(make_event())
    session.add(make_event(source="finnhub"))
    await session.commit()
    assert await session.scalar(select(func.count()).select_from(Event)) == 2


async def test_isolation_between_tests(session: AsyncSession) -> None:
    assert await session.scalar(select(func.count()).select_from(Event)) == 0
