from dataclasses import dataclass
from datetime import date, time
from typing import Literal

from app.core.types import Importance

_NEW_YORK = "America/New_York"
_8_30 = time(8, 30)
_10_00 = time(10, 0)


@dataclass(frozen=True)
class Indicator:
    title: str
    release_id: int
    series_id: str
    units: Literal["lin", "chg", "pch", "pc1"]
    release_time: time
    time_zone: str
    importance: Importance
    category: str


INDICATORS: tuple[Indicator, ...] = (
    # ── inflation ──────────────────────────────────────────────
    Indicator(
        title="CPI (YoY)",
        release_id=10,
        series_id="CPIAUCSL",
        units="pc1",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="high",
        category="inflation",
    ),
    Indicator(
        title="Core CPI (YoY)",
        release_id=10,
        series_id="CPILFESL",
        units="pc1",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="high",
        category="inflation",
    ),
    Indicator(
        title="PPI Final Demand (YoY)",
        release_id=46,
        series_id="PPIFIS",
        units="pc1",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="medium",
        category="inflation",
    ),
    Indicator(
        title="Core PCE Price Index (YoY)",
        release_id=54,
        series_id="PCEPILFE",
        units="pc1",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="high",
        category="inflation",
    ),
    # ── employment ─────────────────────────────────────────────
    Indicator(
        title="Non-Farm Payrolls",
        release_id=50,
        series_id="PAYEMS",
        units="chg",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="high",
        category="employment",
    ),
    Indicator(
        title="Unemployment Rate",
        release_id=50,
        series_id="UNRATE",
        units="lin",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="high",
        category="employment",
    ),
    Indicator(
        title="Average Hourly Earnings (YoY)",
        release_id=50,
        series_id="CES0500000003",
        units="pc1",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="medium",
        category="employment",
    ),
    Indicator(
        title="Initial Jobless Claims",
        release_id=180,
        series_id="ICSA",
        units="lin",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="medium",
        category="employment",
    ),
    Indicator(
        title="JOLTS Job Openings",
        release_id=192,
        series_id="JTSJOL",
        units="lin",
        release_time=_10_00,
        time_zone=_NEW_YORK,
        importance="medium",
        category="employment",
    ),
    # ── growth & consumer ──────────────────────────────────────
    Indicator(
        title="GDP (QoQ, annualized)",
        release_id=53,
        series_id="A191RL1Q225SBEA",
        units="lin",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="high",
        category="growth",
    ),
    Indicator(
        title="Retail Sales (MoM)",
        release_id=9,
        series_id="RSAFS",
        units="pch",
        release_time=_8_30,
        time_zone=_NEW_YORK,
        importance="high",
        category="consumer",
    ),
    Indicator(
        title="Michigan Consumer Sentiment",
        release_id=91,
        series_id="UMCSENT",
        units="lin",
        release_time=_10_00,
        time_zone=_NEW_YORK,
        importance="medium",
        category="consumer",
    ),
)

# Source: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
# The decision is announced on the second day of each meeting, at 14:00
# New York time. Each date stays tentative until confirmed at the preceding
# meeting; unscheduled meetings are not listed.
FOMC_DECISION_DATES: tuple[date, ...] = (
    date(2026, 1, 28),
    date(2026, 3, 18),
    date(2026, 4, 29),
    date(2026, 6, 17),
    date(2026, 7, 29),
    date(2026, 9, 16),
    date(2026, 10, 28),
    date(2026, 12, 9),
    date(2027, 1, 27),
    date(2027, 3, 17),
    date(2027, 4, 28),
    date(2027, 6, 9),
    date(2027, 7, 28),
    date(2027, 9, 15),
    date(2027, 10, 27),
    date(2027, 12, 8),
    date(2028, 1, 26),
)

# Meetings that also publish the Summary of Economic Projections (the dot plot).
FOMC_PROJECTION_DATES: frozenset[date] = frozenset(
    {
        date(2026, 3, 18),
        date(2026, 6, 17),
        date(2026, 9, 16),
        date(2026, 12, 9),
        date(2027, 3, 17),
        date(2027, 6, 9),
        date(2027, 9, 15),
        date(2027, 12, 8),
    }
)
