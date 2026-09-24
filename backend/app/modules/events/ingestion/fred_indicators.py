"""Which FRED series we turn into calendar events, and how to present them.

`release_id`, `series_id` and `units` were checked against the API with
`scripts/check_fred.py`. `title`, `release_time`, `importance` and `category`
are editorial choices: FRED knows none of them.

Release times come from the publishing agency (BLS, BEA, Census, Fed) and are
expressed in local time, so daylight saving is handled by `zoneinfo`.
"""

from dataclasses import dataclass
from datetime import time

from app.core.types import Country, FredUnits, Importance


@dataclass(frozen=True)
class Indicator:
    title: str
    release_id: int
    series_id: str
    units: FredUnits
    release_time: time
    time_zone: str
    country: Country
    importance: Importance
    category: str


_NY = "America/New_York"
_FF = "Europe/Berlin"
_0830 = time(8, 30)
_0915 = time(9, 15)
_1000 = time(10, 0)
_1200 = time(12, 0)
_1500 = time(15, 0)

INDICATORS: tuple[Indicator, ...] = (
    # ── inflation ──────────────────────────────────────────────
    Indicator(
        "CPI (YoY)", 10, "CPIAUCSL", "pc1", _0830, _NY, "US", "high", "inflation"
    ),
    Indicator(
        "Core CPI (YoY)", 10, "CPILFESL", "pc1", _0830, _NY, "US", "high", "inflation"
    ),
    Indicator(
        "PPI (YoY)", 46, "PPIFIS", "pc1", _0830, _NY, "US", "medium", "inflation"
    ),
    Indicator(
        "Core PCE (YoY)", 54, "PCEPILFE", "pc1", _0830, _NY, "US", "high", "inflation"
    ),
    Indicator(
        "Import Prices (MoM)", 188, "IR", "pch", _0830, _NY, "US", "low", "inflation"
    ),
    # ── employment ─────────────────────────────────────────────
    Indicator(
        "Non-Farm Payrolls", 50, "PAYEMS", "chg", _0830, _NY, "US", "high", "employment"
    ),
    Indicator(
        "Unemployment Rate", 50, "UNRATE", "lin", _0830, _NY, "US", "high", "employment"
    ),
    Indicator(
        "Average Hourly Earnings (YoY)",
        50,
        "CES0500000003",
        "pc1",
        _0830,
        _NY,
        "US",
        "medium",
        "employment",
    ),
    Indicator(
        "Initial Jobless Claims",
        180,
        "ICSA",
        "lin",
        _0830,
        _NY,
        "US",
        "medium",
        "employment",
    ),
    Indicator(
        "Continuing Claims", 180, "CCSA", "lin", _0830, _NY, "US", "low", "employment"
    ),
    Indicator(
        "JOLTS Job Openings",
        192,
        "JTSJOL",
        "lin",
        _1000,
        _NY,
        "US",
        "medium",
        "employment",
    ),
    # ── growth ─────────────────────────────────────────────────
    Indicator(
        "Industrial Production (MoM)",
        13,
        "INDPRO",
        "pch",
        _0915,
        _NY,
        "US",
        "medium",
        "growth",
    ),
    Indicator(
        "Capacity Utilization", 13, "TCU", "lin", _0915, _NY, "US", "low", "growth"
    ),
    Indicator(
        "Chicago Fed National Activity",
        219,
        "CFNAI",
        "lin",
        _0830,
        _NY,
        "US",
        "low",
        "growth",
    ),
    # ── consumer ───────────────────────────────────────────────
    Indicator(
        "Retail Sales (MoM)", 9, "RSAFS", "pch", _0830, _NY, "US", "high", "consumer"
    ),
    Indicator(
        "Personal Income (MoM)", 54, "PI", "pch", _0830, _NY, "US", "medium", "consumer"
    ),
    Indicator(
        "Personal Spending (MoM)",
        54,
        "PCE",
        "pch",
        _0830,
        _NY,
        "US",
        "medium",
        "consumer",
    ),
    Indicator(
        "Consumer Credit", 14, "TOTALSL", "chg", _1500, _NY, "US", "low", "consumer"
    ),
    # ── housing ────────────────────────────────────────────────
    Indicator(
        "Housing Starts", 27, "HOUST", "lin", _0830, _NY, "US", "medium", "housing"
    ),
    Indicator(
        "Building Permits", 27, "PERMIT", "lin", _0830, _NY, "US", "medium", "housing"
    ),
    Indicator(
        "Existing Home Sales",
        291,
        "EXHOSLUSM495S",
        "lin",
        _1000,
        _NY,
        "US",
        "medium",
        "housing",
    ),
    Indicator(
        "New Home Sales", 97, "HSN1F", "lin", _1000, _NY, "US", "medium", "housing"
    ),
    Indicator(
        "Construction Spending (MoM)",
        229,
        "TTLCONS",
        "pch",
        _1000,
        _NY,
        "US",
        "low",
        "housing",
    ),
    Indicator(
        "30-Year Mortgage Rate",
        190,
        "MORTGAGE30US",
        "lin",
        _1200,
        _NY,
        "US",
        "low",
        "housing",
    ),
    # ── manufacturing & trade ──────────────────────────────────
    Indicator(
        "Durable Goods Orders (MoM)",
        95,
        "DGORDER",
        "pch",
        _0830,
        _NY,
        "US",
        "medium",
        "manufacturing",
    ),
    Indicator(
        "Empire State Manufacturing",
        321,
        "GACDISA066MSFRBNY",
        "lin",
        _0830,
        _NY,
        "US",
        "medium",
        "manufacturing",
    ),
    Indicator(
        "Philadelphia Fed Manufacturing",
        351,
        "GACDFSA066MSFRBPHI",
        "lin",
        _0830,
        _NY,
        "US",
        "medium",
        "manufacturing",
    ),
    Indicator(
        "Business Inventories (MoM)",
        25,
        "BUSINV",
        "pch",
        _1000,
        _NY,
        "US",
        "low",
        "manufacturing",
    ),
    Indicator(
        "Trade Balance", 51, "BOPGSTB", "lin", _0830, _NY, "US", "medium", "trade"
    ),
)


# Indicators the rank-based matching cannot handle yet.
#
# The first four publish several times for the same period — GDP has three
# estimates per quarter, Michigan a preliminary and a final each month — so
# pairing the n-th release date with the n-th observation shifts the values
# by one period. They need `output_type=4`, which returns each observation
# with its own publication date.
#
# The last two are policy rates: their series is daily, so `release/dates`
# returns one date per day instead of the meeting dates. They need the
# official meeting calendars.
DEFERRED_INDICATORS: tuple[Indicator, ...] = (
    Indicator(
        "GDP (QoQ, annualized)",
        53,
        "A191RL1Q225SBEA",
        "lin",
        _0830,
        _NY,
        "US",
        "high",
        "growth",
    ),
    Indicator(
        "Employment Cost Index (QoQ)",
        11,
        "ECIALLCIV",
        "pch",
        _0830,
        _NY,
        "US",
        "medium",
        "employment",
    ),
    Indicator(
        "Nonfarm Productivity (QoQ, ann.)",
        47,
        "OPHNFB",
        "pca",
        _0830,
        _NY,
        "US",
        "low",
        "employment",
    ),
    Indicator(
        "Michigan Consumer Sentiment",
        91,
        "UMCSENT",
        "lin",
        _1000,
        _NY,
        "US",
        "medium",
        "consumer",
    ),
    Indicator(
        "Fed Interest Rate Decision",
        101,
        "DFEDTARU",
        "lin",
        time(14, 0),
        _NY,
        "US",
        "high",
        "central_bank",
    ),
    Indicator(
        "ECB Deposit Facility Rate",
        484,
        "ECBDFR",
        "lin",
        time(14, 15),
        _FF,
        "EU",
        "high",
        "central_bank",
    ),
)
