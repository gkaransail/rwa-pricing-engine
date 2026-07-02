"""
Fetch on-chain NAV prices for tokenized treasury assets via Alchemy.

API key: free at https://dashboard.alchemy.com/ (300M compute units/month)

Contract addresses are Ethereum mainnet. Verify against issuer docs before
using in production:
  OUSG — https://docs.ondo.finance/contracts
  BUIDL — https://securitize.io/  (NAV maintained at $1.00 by design)
  USYC  — https://hashnote.com/
"""

import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"

# Ondo's IRWAOracle interface — getPrice() returns (price, timestamp)
ORACLE_ABI = [
    {
        "inputs": [],
        "name": "getPrice",
        "outputs": [
            {"name": "price", "type": "uint256"},
            {"name": "timestamp", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

# OUSGInstantManager exposes a public `oracle` variable we use to resolve
# the oracle address dynamically instead of hardcoding it.
INSTANT_MANAGER_ABI = [
    {
        "inputs": [],
        "name": "oracle",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

CONTRACTS = {
    "OUSG": {
        # OUSGInstantManager on Ethereum mainnet — verify at docs.ondo.finance/contracts
        "instant_manager": "0x95d5b42dB00d08B9B43E05c2CD5DcB5e05D32dA1",
        "description": "Ondo US Dollar Yield — tokenized short-term US Treasuries",
        "strategy": "via_manager",
    },
    "BUIDL": {
        # BlackRock BUIDL NAV is maintained at exactly $1.00 by Securitize
        # No public price oracle; track AUM/transfer events instead
        "description": "BlackRock USD Institutional Digital Liquidity Fund",
        "strategy": "fixed_nav",
        "fixed_nav": 1.0,
    },
    "USYC": {
        # Hashnote USYC price oracle — verify at hashnote.com
        # TODO: confirm oracle address from Hashnote docs
        "oracle": "0x4c48bcb2160F8e0aDbf9D4d8e4C1b9E2B3b1c3a1",  # VERIFY
        "description": "Hashnote US Yield Coin",
        "strategy": "direct_oracle",
    },
}

PRICE_DECIMALS = 18  # Ondo-style oracles use 18-decimal fixed point


def get_web3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
    if not w3.is_connected():
        raise ConnectionError("Cannot connect to Alchemy — check ALCHEMY_API_KEY in .env")
    return w3


def fetch_via_manager(w3: Web3, manager_address: str) -> tuple[float, str, int]:
    """Resolve oracle address from InstantManager, then read price."""
    manager = w3.eth.contract(
        address=Web3.to_checksum_address(manager_address),
        abi=INSTANT_MANAGER_ABI,
    )
    oracle_address = manager.functions.oracle().call()
    oracle = w3.eth.contract(address=oracle_address, abi=ORACLE_ABI)
    price_raw, ts = oracle.functions.getPrice().call()
    return price_raw / 10**PRICE_DECIMALS, oracle_address, ts


def fetch_direct_oracle(w3: Web3, oracle_address: str) -> tuple[float, int]:
    oracle = w3.eth.contract(
        address=Web3.to_checksum_address(oracle_address),
        abi=ORACLE_ABI,
    )
    price_raw, ts = oracle.functions.getPrice().call()
    return price_raw / 10**PRICE_DECIMALS, ts


def fetch_nav(asset: str, w3: Web3) -> dict:
    cfg = CONTRACTS[asset]
    strategy = cfg["strategy"]

    if strategy == "fixed_nav":
        return {
            "asset": asset,
            "nav": cfg["fixed_nav"],
            "note": "NAV fixed at $1.00 by fund design; track AUM via transfer events",
        }

    if strategy == "via_manager":
        nav, oracle_addr, ts = fetch_via_manager(w3, cfg["instant_manager"])
        return {"asset": asset, "nav": nav, "oracle_address": oracle_addr, "timestamp": ts}

    if strategy == "direct_oracle":
        nav, ts = fetch_direct_oracle(w3, cfg["oracle"])
        return {"asset": asset, "nav": nav, "oracle_address": cfg["oracle"], "timestamp": ts}

    raise ValueError(f"Unknown strategy: {strategy}")


def fetch_all() -> list[dict]:
    w3 = get_web3()
    results = []
    for asset in CONTRACTS:
        try:
            results.append(fetch_nav(asset, w3))
        except Exception as e:
            results.append({"asset": asset, "nav": None, "error": str(e)})
    return results


if __name__ == "__main__":
    from pprint import pprint
    pprint(fetch_all())
