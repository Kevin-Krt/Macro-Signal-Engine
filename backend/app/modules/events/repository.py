from collections.abc import Sequence

import structlog
from sqlalchemy import func
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


async def upsert_events(session: AsyncSession, drafts: Sequence[EventDraft]) -> int:
    """
    Insert every draft, updating the rows that already exist.

    Conflicts are detected on (source, external_id). The caller owns the
    transaction: this function never commits.
    """
    deduplicated = _deduplicate(drafts)
    if not deduplicated:
        return 0

    stmt = insert(Event).values([draft.model_dump() for draft in deduplicated])
    stmt = stmt.on_conflict_do_update(
        constraint="uq_events_source_external_id",
        set_={column: stmt.excluded[column] for column in _UPDATABLE_COLUMNS}
        | {"updated_at": func.now()},
    )

    await session.execute(stmt)

    log.info("events_upserted", received=len(drafts), upserted=len(deduplicated))
    return len(deduplicated)
