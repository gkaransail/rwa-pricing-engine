"""
Phase 0 data spike — verifies all three data sources return clean numbers.

Setup:
  pip install -r requirements.txt
  cp .env.example .env        # fill in FRED_API_KEY and ALCHEMY_API_KEY
  python spike/run_spike.py

Goal: confirm fred.py, onchain.py, and market.py all return data before
building the full pipeline in Phase 1.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fred import fetch_all as fetch_fred
from onchain import fetch_all as fetch_onchain
from market import fetch_all as fetch_market

ASSETS = ["OUSG", "BUIDL", "USYC"]
ANNUALIZATION_DAYS = 90  # rough: OUSG holds ~90-day T-bills


def main():
    print("\n── FRED: Benchmark Yields ─────────────────────────────────")
    fred_data = {}
    try:
        fred_data = fetch_fred()
        for sid, obs in fred_data.items():
            print(f"  {sid:<8} {obs['value']:>7.4f}%   ({obs['description']}, {obs['date']})")
    except Exception as e:
        print(f"  ERROR: {e}")

    benchmark_yield = fred_data.get("TB3MS", {}).get("value")

    print("\n── ON-CHAIN: NAV Prices ───────────────────────────────────")
    nav_data = {}
    try:
        for r in fetch_onchain():
            nav_data[r["asset"]] = r
            if r.get("nav") is not None:
                note = f"  ({r.get('note', '')})" if r.get("note") else f"  oracle: {r.get('oracle_address', '')}"
                print(f"  {r['asset']:<8} NAV = ${r['nav']:.6f}{note}")
            else:
                print(f"  {r['asset']:<8} ERROR — {r.get('error', 'unknown')}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n── MARKET: Secondary Prices ───────────────────────────────")
    market_data = {}
    try:
        for r in fetch_market():
            market_data[r["asset"]] = r
            if r.get("market_price") is not None:
                print(f"  {r['asset']:<8} Market = ${r['market_price']:.6f}")
            else:
                print(f"  {r['asset']:<8} N/A — {r.get('error', 'unknown')}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n── SPREAD SUMMARY ─────────────────────────────────────────")
    any_spread = False
    for asset in ASSETS:
        nav = nav_data.get(asset, {}).get("nav")
        market = market_data.get(asset, {}).get("market_price")

        if nav is None or market is None:
            print(f"  {asset:<8} skipped (missing NAV or market price)")
            continue

        spread_bps = (market - nav) / nav * 10_000
        implied_yield = (nav / market - 1) * (365 / ANNUALIZATION_DAYS) * 100

        vs_benchmark = ""
        if benchmark_yield is not None:
            diff = implied_yield - benchmark_yield
            vs_benchmark = f"   vs TB3MS: {diff:+.2f}%"

        print(f"  {asset:<8} spread: {spread_bps:+.1f} bps   implied yield: {implied_yield:.4f}%{vs_benchmark}")
        any_spread = True

    if not any_spread:
        print("  No spreads calculated — check errors above.")
        print("\n  Next steps:")
        print("  1. Verify ALCHEMY_API_KEY in .env")
        print("  2. Verify FRED_API_KEY in .env")
        print("  3. Confirm contract addresses in onchain.py against issuer docs")

    print()


if __name__ == "__main__":
    main()
