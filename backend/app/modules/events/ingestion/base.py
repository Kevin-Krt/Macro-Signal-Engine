from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.types import EventType, Importance


class EventDraft(BaseModel):
    """
    One event as returned by a connector, before it reaches the database.

    Connectors produce drafts; the upsert layer turns them into `Event` rows.
    Fields the source cannot know — `id`, `title_hash`, `ingested_at`,
    `updated_at` — are deliberately absent.
    """

    model_config = ConfigDict(extra="forbid")

    source: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="Connector that produced this draft, e.g. 'fred'.",
        ),
    ]
    external_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=255,
            description="Identifier of the event at the source. Unique per source.",
        ),
    ]
    event_type: Annotated[
        EventType,
        Field(
            max_length=20,
            description="'calendar' for a scheduled release, 'news' for an article.",
        ),
    ]
    title: Annotated[
        str,
        Field(
            min_length=1,
            max_length=500,
            description="Short human-readable label shown on the timeline.",
        ),
    ]
    summary: Annotated[
        str | None,
        Field(default=None, description="Longer description or article excerpt."),
    ]
    url: Annotated[
        str | None,
        Field(
            default=None,
            max_length=1000,
            description="Link to the event on the source website.",
        ),
    ]
    occurred_at: Annotated[
        datetime,
        Field(description="When the event happens or was published. Always UTC."),
    ]
    category: Annotated[
        str | None,
        Field(
            default=None,
            max_length=50,
            description="Source category, e.g. 'inflation'. None for news.",
        ),
    ]
    country: Annotated[
        str | None,
        Field(
            default=None,
            min_length=2,
            max_length=2,
            description="ISO 3166-1 alpha-2 country code, e.g. 'US'.",
        ),
    ]
    importance: Annotated[
        Importance | None,
        Field(
            default=None,
            description="Importance as announced by the source, not inferred.",
        ),
    ]
    payload: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="Source-specific extras: actual/forecast/previous, tickers…",
        ),
    ]


class SourceConnector(Protocol):
    name: str

    async def fetch(self, client: httpx.AsyncClient) -> Sequence[EventDraft]: ...
