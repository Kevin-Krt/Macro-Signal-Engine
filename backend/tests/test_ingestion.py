from collections.abc import Sequence
from datetime import UTC, datetime

import httpx

from app.modules.events.ingestion.base import EventDraft, SourceConnector


class FakeConnector:
    """A connector that satisfies SourceConnector without inheriting from it."""

    name = "fake"

    async def fetch(self, client: httpx.AsyncClient) -> Sequence[EventDraft]:
        return [
            EventDraft(
                source=self.name,
                external_id="FAKE-1",
                event_type="calendar",
                title="Fake release",
                occurred_at=datetime(2026, 9, 10, 12, 30, tzinfo=UTC),
            )
        ]


# Structural typing check: pyrefly fails here if FakeConnector drifts
# from the protocol, even though it inherits from nothing.
CONNECTORS: list[SourceConnector] = [FakeConnector()]


async def test_fake_connector_returns_drafts() -> None:
    connector = CONNECTORS[0]
    async with httpx.AsyncClient() as client:
        drafts = await connector.fetch(client)

    assert len(drafts) == 1
    assert drafts[0].source == connector.name
    assert drafts[0].event_type == "calendar"
