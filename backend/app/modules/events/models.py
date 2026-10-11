from datetime import datetime
from typing import Any

from sqlalchemy import (
    BIGINT,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import EventType, Importance


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[EventType] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1_000))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    category: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(2))
    importance: Mapped[Importance | None] = mapped_column(String(10))
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    title_hash: Mapped[str | None] = mapped_column(String(64))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_events_source_external_id"),
        CheckConstraint(
            "event_type IN ('calendar', 'news')", name="ck_events_event_type"
        ),
        CheckConstraint(
            "importance IN ('low', 'medium', 'high')", name="ck_events_importance"
        ),
        Index("ix_events_occurred_at", "occurred_at"),
        Index("ix_events_title_hash", "title_hash"),
    )
