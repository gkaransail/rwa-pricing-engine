"""
Fetch secondary market prices for tokenized treasury assets via CoinGecko.

Free tier: 30 calls/min, no API key required.
Pro key via COINGECKO_API_KEY unlocks higher rate limits and historical data.

Note: BUIDL and USYC are permissioned tokens with thin secondary markets —
they may not be indexed by CoinGecko. The script handles missing coins gracefully.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
BASE_URL = "https://api.coingecko.com/api/v3"

# Verify IDs at https://api.coingecko.com/api/v3/coins/list
COIN_IDS = {
    "OUSG": "ondo-us-dollar-yield",
    "BUIDL": "blackrock-usd-institutional-digital-liquidity-fund",
    "USYC": "hashnote-us-yield-coin",
}


def _headers() -> dict:
    if COINGECKO_API_KEY:
        return {"x-cg-pro-api-key": COINGECKO_API_KEY}
    return {}


def fetch_prices(coin_ids: list[str]) -> dict:
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": "usd",
        "include_last_updated_at": "true",
    }
    resp = requests.get(
        f"{BASE_URL}/simple/price",
        params=params,
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_all() -> list[dict]:
    try:
        data = fetch_prices(list(COIN_IDS.values()))
    except requests.HTTPError as e:
        return [{"asset": a, "market_price": None, "error": str(e)} for a in COIN_IDS]

    results = []
    for asset, coin_id in COIN_IDS.items():
        if coin_id not in data:
            results.append({
                "asset": asset,
                "market_price": None,
                "coin_id": coin_id,
                "error": "Not listed on CoinGecko — permissioned token or insufficient liquidity",
            })
        else:
            entry = data[coin_id]
            results.append({
                "asset": asset,
                "coin_id": coin_id,
                "market_price": entry["usd"],
                "last_updated_at": entry.get("last_updated_at"),
            })
    return results


if __name__ == "__main__":
    from pprint import pprint
    pprint(fetch_all())
