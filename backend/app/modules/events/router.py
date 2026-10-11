from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.events.repository import list_calendar_week, list_news
from app.modules.events.schemas import CalendarEvent, CalendarWeek, NewsEvent, NewsPage

events_router = APIRouter(tags=["events"])


@events_router.get("/calendar", response_model=CalendarWeek)
async def get_calendar_week(
    session: Annotated[AsyncSession, Depends(get_session)], week: date | None = None
) -> CalendarWeek:

    week = week or date.today()
    week_start = week - timedelta(days=week.weekday())

    events = await list_calendar_week(session, week_start)

    return CalendarWeek(
        week_start=week_start,
        week_end=week_start + timedelta(days=6),
        events=[CalendarEvent.from_event(e) for e in events],
    )


@events_router.get("/news", response_model=NewsPage)
async def get_news(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100, description="Articles per page")] = 50,
    before: datetime | None = None,
    q: str | None = None,
) -> NewsPage:

    events, next_cursor = await list_news(session, limit=limit, before=before, query=q)
    return NewsPage(
        events=[NewsEvent.from_event(e) for e in events], next_cursor=next_cursor
    )
