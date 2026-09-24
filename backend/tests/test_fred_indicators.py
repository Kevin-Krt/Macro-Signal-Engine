from collections import Counter
from typing import get_args
from zoneinfo import ZoneInfo

from app.core.types import Country, FredUnits, Importance
from app.modules.events.ingestion.fred_indicators import DEFERRED_INDICATORS, INDICATORS

KNOWN_CATEGORIES = {
    "inflation",
    "employment",
    "growth",
    "consumer",
    "housing",
    "manufacturing",
    "trade",
    "central_bank",
}

ALL = INDICATORS + DEFERRED_INDICATORS


def test_whitelist_is_not_empty() -> None:
    assert ALL


def test_series_ids_are_unique() -> None:
    counts = Counter(indicator.series_id for indicator in ALL)
    duplicates = [series for series, n in counts.items() if n > 1]
    assert not duplicates, f"series listed twice: {duplicates!r}"


def test_titles_are_unique() -> None:
    counts = Counter(indicator.title for indicator in ALL)
    duplicates = [title for title, n in counts.items() if n > 1]
    assert not duplicates, f"titles listed twice: {duplicates!r}"


def test_release_ids_are_positive() -> None:
    for indicator in ALL:
        assert indicator.release_id > 0, indicator.title


def test_time_zones_are_valid() -> None:
    for indicator in ALL:
        ZoneInfo(indicator.time_zone)


def test_units_are_allowed() -> None:
    allowed = set(get_args(FredUnits))
    for indicator in ALL:
        assert indicator.units in allowed, indicator.title


def test_importance_is_allowed() -> None:
    allowed = set(get_args(Importance))
    for indicator in ALL:
        assert indicator.importance in allowed, indicator.title


def test_countries_are_allowed() -> None:
    allowed = set(get_args(Country))
    for indicator in ALL:
        assert indicator.country in allowed, indicator.title


def test_categories_are_known() -> None:
    for indicator in ALL:
        assert indicator.category in KNOWN_CATEGORIES, (
            f"{indicator.title!r} has unknown category {indicator.category!r}"
        )


def test_deferred_are_not_active() -> None:
    overlap = {i.series_id for i in INDICATORS} & {
        i.series_id for i in DEFERRED_INDICATORS
    }
    assert not overlap, f"listed in both lists: {sorted(overlap)!r}"
