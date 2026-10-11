"""
Check the FRED whitelist against the live API.

    uv run python scripts/check_fred.py            # everything
    uv run python scripts/check_fred.py PAYEMS     # one series

Not part of the test suite: it calls the real API. Run it after editing
`fred_indicators.py`.
"""

import asyncio
import sys
from datetime import date

import httpx

from app.core.config import get_settings
from app.modules.events.ingestion.fred_indicators import (
    DEFERRED_INDICATORS,
    INDICATORS,
    Indicator,
)

FRED = "https://api.stlouisfed.org/fred"

# How stale a series may be before we flag it, by FRED frequency code.
MAX_STALE_DAYS = {"D": 10, "W": 30, "BW": 45, "M": 90, "Q": 200, "SA": 400, "A": 500}

# Series with no seasonality to correct: policy rates, market rates, an
# opinion survey, a composite index, and import prices, which the BLS
# publishes unadjusted.
EXPECTED_NSA = {"IR", "CFNAI", "UMCSENT", "MORTGAGE30US", "DFEDTARU", "ECBDFR"}


async def describe(client: httpx.AsyncClient, key: str, indicator: Indicator):
    base = {"api_key": key, "file_type": "json", "series_id": indicator.series_id}

    r = await client.get(f"{FRED}/series/release", params=base)
    if r.status_code != 200:
        raise LookupError(f"series unknown (HTTP {r.status_code})")
    releases = {x["id"]: x["name"] for x in r.json()["releases"]}

    r = await client.get(f"{FRED}/series", params=base)
    meta = r.json()["seriess"][0]

    r = await client.get(
        f"{FRED}/series/observations",
        params=base | {"units": indicator.units, "sort_order": "desc", "limit": 3},
    )
    if r.status_code != 200:
        raise LookupError(f"units={indicator.units} refused (HTTP {r.status_code})")
    rows = [o for o in r.json().get("observations", []) if o["value"] != "."]

    return releases, meta, rows


async def main() -> int:
    settings = get_settings()
    key = settings.fred_api_key.get_secret_value()
    wanted = sys.argv[1:]
    rows = [
        i
        for i in [*INDICATORS, *DEFERRED_INDICATORS]
        if not wanted or i.series_id in wanted
    ]
    problems = 0

    async with httpx.AsyncClient(timeout=20) as client:
        for indicator in rows:
            try:
                releases, meta, obs = await describe(client, key, indicator)
            except (LookupError, KeyError, IndexError) as exc:
                problems += 1
                print(f"FAIL  {indicator.title:32} {indicator.series_id:20} {exc}")
                continue

            flags = []
            if indicator.release_id not in releases:
                got = ", ".join(f"{i} {n}" for i, n in releases.items())
                flags.append(f"release is [{got}], not {indicator.release_id}")

            last = date.fromisoformat(meta["observation_end"])
            days = (date.today() - last).days
            if days > MAX_STALE_DAYS.get(meta["frequency_short"], 120):
                flags.append(f"stale: last {last} ({days} days ago)")

            if (
                meta["seasonal_adjustment_short"] not in {"SA", "SAAR"}
                and indicator.series_id not in EXPECTED_NSA
            ):
                flags.append(
                    f"not seasonally adjusted ({meta['seasonal_adjustment_short']})"
                )

            if not obs:
                flags.append(f"no value with units={indicator.units}")

            problems += bool(flags)
            sample = " ".join(f"{o['date'][:7]}={o['value']}" for o in obs[:3])
            print(
                f"{'FAIL' if flags else 'ok  '}  {indicator.title:32} "
                f"{indicator.series_id:20} {indicator.units:4} "
                f"{meta['frequency_short']:2} {sample}"
            )
            for flag in flags:
                print(f"        -> {flag}")

            await asyncio.sleep(0.3)

    print(f"\n{len(rows) - problems}/{len(rows)} clean")
    return problems


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
