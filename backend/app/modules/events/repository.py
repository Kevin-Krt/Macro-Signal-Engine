from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.ingestion.base import EventDraft
from app.modules.events.models import Event

log = structlog.get_logger(__name__)

# Columns the source owns
_UPDATABLE_COLUMNS = (
    "event_type",
    "title",
    "summary",
    "url",
    "occurred_at",
    "category",
    "country",
    "importance",
    "payload",
)


def _deduplicate(drafts: Sequence[EventDraft]) -> list[EventDraft]:
    """
    Keep one draft per (source, external_id), the last one wins.
    """
    by_key: dict[tuple[str, str], EventDraft] = {}

    for draft in drafts:
        key = (draft.source, draft.external_id)
        if key in by_key:
            log.warning(
                "duplicate_key_in_batch",
                source=draft.source,
                external_id=draft.external_id,
            )
        by_key[key] = draft

    return list(by_key.values())


async def upsert_events(
    session: AsyncSession, drafts: Sequence[EventDraft], *, freeze_payload: bool = False
) -> int:
    """
    Insert every draft, updating the rows that already exist.

    Conflicts are detected on (source, external_id). The caller owns the
    transaction: this function never commits.

    With `freeze_payload`, a row whose payload already holds an `actual`
    value is left untouched — calendar figures must keep the number that was
    announced, not a later revision. Note this freezes the whole row, title
    and category included.
    """
    deduplicated = _deduplicate(drafts)
    if not deduplicated:
        return 0

    stmt = insert(Event).values([draft.model_dump() for draft in deduplicated])
    stmt = stmt.on_conflict_do_update(
        constraint="uq_events_source_external_id",
        set_={column: stmt.excluded[column] for column in _UPDATABLE_COLUMNS}
        | {"updated_at": func.now()},
        where=Event.payload["actual"].astext.is_(None) if freeze_payload else None,
    )

    await session.execute(stmt)

    log.info("events_upserted", received=len(drafts), upserted=len(deduplicated))
    return len(deduplicated)


async def list_calendar_week(
    session: AsyncSession, week_start: date
) -> Sequence[Event]:
    week_start_at = datetime.combine(week_start, time.min, tzinfo=UTC)
    week_end_at = datetime.combine(week_start + timedelta(days=7), time.min, tzinfo=UTC)

    stmt = (
        select(Event)
        .where(
            Event.event_type == "calendar",
            Event.occurred_at >= week_start_at,
            Event.occurred_at < week_end_at,
        )
        .order_by(Event.occurred_at)
    )

    events = (await session.scalars(stmt)).all()
    return events


async def list_news(
    session: AsyncSession,
    *,
    limit: int = 50,
    before: datetime | None = None,
    query: str | None = None,
) -> tuple[Sequence[Event], datetime | None]:

    stmt = (
        select(Event)
        .where(Event.event_type == "news")
        .order_by(Event.occurred_at.desc())
        .limit(limit + 1)
    )

    if before is not None:
        stmt = stmt.where(Event.occurred_at < before)
    if query:
        stmt = stmt.where(Event.title.ilike(f"%{query}%"))

    rows = (await session.scalars(stmt)).all()

    has_more = len(rows) > limit
    events = rows[:limit]
    next_cursor = events[-1].occurred_at if has_more else None

    return events, next_cursor
