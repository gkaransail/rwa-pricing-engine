"""
Fetch benchmark yield data from FRED (Federal Reserve Economic Data).

API key: free at https://fred.stlouisfed.org/docs/api/api_key.html
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "TB3MS": "3-Month Treasury Bill Secondary Market Rate",
    "GS1M": "1-Month Treasury Constant Maturity Rate",
    "DFF": "Federal Funds Effective Rate",
}


def fetch_latest(series_id: str) -> dict:
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 5,  # grab 5 in case the most recent has a "." (weekend/holiday)
    }
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()

    observations = resp.json()["observations"]
    # FRED uses "." for missing values (weekends, holidays)
    valid = [o for o in observations if o["value"] != "."]
    if not valid:
        raise ValueError(f"No valid observations found for {series_id}")

    latest = valid[0]
    return {
        "series_id": series_id,
        "description": SERIES[series_id],
        "date": latest["date"],
        "value": float(latest["value"]),  # percent, e.g. 5.25
    }


def fetch_all() -> dict[str, dict]:
    return {sid: fetch_latest(sid) for sid in SERIES}


if __name__ == "__main__":
    from pprint import pprint
    pprint(fetch_all())
