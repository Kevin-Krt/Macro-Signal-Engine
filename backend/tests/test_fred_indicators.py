from collections import Counter
from datetime import date
from typing import get_args
from zoneinfo import ZoneInfo

from app.core.types import Importance
from app.modules.events.ingestion.fred_indicators import (
    FOMC_DECISION_DATES,
    FOMC_PROJECTION_DATES,
    INDICATORS,
)

KNOWN_CATEGORIES = {"inflation", "employment", "growth", "consumer", "central_bank"}

# Election week: the November 2024 meeting was moved to Wednesday-Thursday.
KNOWN_NON_WEDNESDAY_DECISIONS = {date(2024, 11, 7)}

# How much notice we want before the FOMC calendar runs out.
FOMC_CALENDAR_MIN_HORIZON_DAYS = 180


def test_whitelist_is_not_empty() -> None:
    assert INDICATORS


def test_series_ids_are_unique() -> None:
    counts = Counter(indicator.series_id for indicator in INDICATORS)
    duplicates = [series for series, n in counts.items() if n > 1]
    assert not duplicates, f"series listed twice: {duplicates!r}"


def test_titles_are_unique() -> None:
    counts = Counter(indicator.title for indicator in INDICATORS)
    duplicates = [title for title, n in counts.items() if n > 1]
    assert not duplicates, f"titles listed twice: {duplicates!r}"


def test_time_zones_are_valid() -> None:
    for indicator in INDICATORS:
        ZoneInfo(indicator.time_zone)


def test_importance_is_allowed() -> None:
    allowed = set(get_args(Importance))
    for indicator in INDICATORS:
        assert indicator.importance in allowed, indicator.title


def test_categories_are_known() -> None:
    for indicator in INDICATORS:
        assert indicator.category in KNOWN_CATEGORIES, (
            f"{indicator.title!r} has unknown category {indicator.category!r}"
        )


def test_fomc_decisions_fall_on_wednesdays() -> None:
    for decision in FOMC_DECISION_DATES:
        if decision in KNOWN_NON_WEDNESDAY_DECISIONS:
            continue
        assert decision.weekday() == 2, (
            f"{decision} is a {decision:%A}: typo, or a new exception to document"
        )


def test_fomc_dates_are_sorted_and_unique() -> None:
    assert list(FOMC_DECISION_DATES) == sorted(set(FOMC_DECISION_DATES))


def test_projection_dates_are_decision_dates() -> None:
    unknown = FOMC_PROJECTION_DATES - set(FOMC_DECISION_DATES)
    assert not unknown, f"projection dates without a meeting: {sorted(unknown)!r}"


def test_fomc_calendar_is_not_about_to_run_out() -> None:
    days_left = (FOMC_DECISION_DATES[-1] - date.today()).days
    assert days_left >= FOMC_CALENDAR_MIN_HORIZON_DAYS, (
        f"FOMC calendar ends on {FOMC_DECISION_DATES[-1]} ({days_left} days left): "
        "add next year's dates from federalreserve.gov/monetarypolicy/fomccalendars.htm"
    )
