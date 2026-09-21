"""
Check the FRED whitelist against the live API.

Run after editing the list:  uv run python scripts/verify_fred_indicators.py
"""

import asyncio
import sys

import httpx

from app.core.config import get_settings
from app.modules.events.ingestion.fred_indicators import INDICATORS, Indicator

FRED_URL = "https://api.stlouisfed.org/fred"


async def check(
    client: httpx.AsyncClient, api_key: str, indicator: Indicator
) -> str | None:
    base = {"api_key": api_key, "file_type": "json"}

    response = await client.get(
        f"{FRED_URL}/series/release",
        params=base | {"series_id": indicator.series_id},
    )
    if response.status_code != 200:
        return f"series {indicator.series_id} not found (HTTP {response.status_code})"

    release_ids = {release["id"] for release in response.json().get("releases", [])}
    if indicator.release_id not in release_ids:
        return (
            f"series {indicator.series_id} belongs to release {sorted(release_ids)}, "
            f"not {indicator.release_id}"
        )

    response = await client.get(
        f"{FRED_URL}/series/observations",
        params=base
        | {
            "series_id": indicator.series_id,
            "units": indicator.units,
            "sort_order": "desc",
            "limit": 1,
        },
    )
    observations = response.json().get("observations", [])
    if not observations or observations[0]["value"] == ".":
        return (
            f"series {indicator.series_id} returns no value "
            f"with units={indicator.units}"
        )

    return None


async def main() -> int:
    api_key = get_settings().fred_api_key.get_secret_value()
    failures = 0

    async with httpx.AsyncClient(timeout=15) as client:
        for indicator in INDICATORS:
            problem = await check(client, api_key, indicator)
            if problem is None:
                print(f"  ok    {indicator.title}")
            else:
                failures += 1
                print(f"  FAIL  {indicator.title}: {problem}")

    print(f"\n{len(INDICATORS) - failures}/{len(INDICATORS)} indicators verified")
    return failures


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
