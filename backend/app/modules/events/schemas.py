from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict

from app.core.types import Importance
from app.modules.events.models import Event


class CalendarEvent(BaseModel):
    """
    One row of the economic calendar.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    occurred_at: datetime
    country: str | None
    importance: Importance | None
    category: str | None
    actual: float | None
    previous: float | None
    unit: str | None

    @classmethod
    def from_event(cls, event: Event) -> Self:
        return cls(
            id=event.id,
            title=event.title,
            occurred_at=event.occurred_at,
            country=event.country,
            importance=event.importance,
            category=event.category,
            actual=event.payload.get("actual"),
            previous=event.payload.get("previous"),
            unit=event.payload.get("unit"),
        )


class NewsEvent(BaseModel):
    """
    One article of the news feed.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    summary: str | None
    url: str | None
    occurred_at: datetime
    provider: str | None

    @classmethod
    def from_event(cls, event: Event) -> Self:
        return cls(
            id=event.id,
            title=event.title,
            summary=event.summary,
            url=event.url,
            occurred_at=event.occurred_at,
            provider=event.payload.get("provider"),
        )


class CalendarWeek(BaseModel):
    """
    Every calendar event of one week, Monday to Sunday, in UTC.
    """

    week_start: date
    week_end: date
    events: list[CalendarEvent]


class NewsPage(BaseModel):
    """
    One page of the news feed. `next_cursor` is None on the last page.
    """

    events: list[NewsEvent]
    next_cursor: datetime | None
