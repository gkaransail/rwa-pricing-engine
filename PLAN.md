# RWA Pricing Engine — Build Plan

A real-time pricing and valuation engine for tokenized treasury assets (OUSG, BUIDL, USYC), tracking NAV vs. on-chain secondary market price discrepancies.

---

## Overview

**Core idea:** Tokenized treasuries (OUSG, BUIDL, sTBILL) have T+1/T+2 settlement, so secondary DEX prices drift from NAV intraday — especially around rate decisions or end-of-quarter flows. That discrepancy is actionable for institutional buyers and not tracked anywhere in real time.

**Go-to-market:** Public dashboard + weekly newsletter (credibility asset) → paid API/alerts tier.

**Data stack (free/cheap):**
- FRED — risk-free rate benchmarks (free, no API key)
- Alchemy — on-chain NAV oracle reads (free tier: 300M compute units/mo)
- CoinGecko — secondary market prices (free tier sufficient for MVP)

**Assets at launch:** OUSG (Ondo, Ethereum), BUIDL (BlackRock, Ethereum), USYC (Hashnote, Ethereum)

---

## Phase 0: Data Spike (Weekend 1)

**Goal:** Confirm all data sources return clean numbers before building infrastructure.

Write three standalone scripts:

- **`fred.py`** — Pull `TB3MS` (3-month T-bill yield) via `requests`
- **`onchain.py`** — `eth_call` on OUSG's `getAssetPrice()` / BUIDL's NAV oracle via Alchemy
- **`market.py`** — CoinGecko `/simple/price` for OUSG and BUIDL secondary market price

If all three return clean numbers in one script, the engine is viable. Ship nothing else this weekend.

---

## Phase 1: Data Pipeline (Weekend 2–3)

**Stack:** Python, SQLite (→ Postgres when paying users arrive), APScheduler for polling.

```
rwa_engine/
  collectors/
    fred.py       # T-bill yields — daily poll
    onchain.py    # NAV oracle reads — hourly poll
    market.py     # CoinGecko prices — hourly poll
  models.py       # SQLite schema
  scheduler.py    # APScheduler jobs
```

**Schema** (one row per asset per timestamp):

| Column | Type | Description |
|--------|------|-------------|
| asset | TEXT | e.g. "OUSG", "BUIDL" |
| timestamp | DATETIME | UTC |
| nav | FLOAT | NAV per token from oracle |
| market_price | FLOAT | Secondary market price |
| spread_bps | FLOAT | (market - nav) / nav * 10000 |
| implied_yield | FLOAT | Annualized yield from discount/premium |
| benchmark_yield | FLOAT | TB3MS from FRED |

---

## Phase 2: Pricing Logic (Weekend 3)

**Core math:**

```python
spread_bps = (market_price - nav) / nav * 10_000

# Annualize relative to days until next NAV reset
implied_yield = (nav / market_price - 1) * (365 / days_to_reset)

# Alert when spread crosses ±2σ of 30-day rolling history
z_score = (spread_bps - rolling_mean) / rolling_std
```

**Differentiator:** rwa.xyz and Steakhouse Financial show TVL and basic price — none publish spread-to-benchmark in real time. This is the moat.

---

## Phase 3: Public Dashboard (Weekend 4–5)

**Stack:** Next.js + Recharts (frontend, Vercel), FastAPI (backend, Railway free tier).

**Three views:**

1. **Live Spreads** — table: asset, NAV, market price, spread (bps), last updated
2. **Spread History** — 30/90-day rolling spread chart per asset
3. **Yield Comparison** — implied yield vs. 3-month T-bill, overlaid

Keep the design minimal. The data is the product.

---

## Phase 4: Weekly Newsletter (Week 5 onward)

**Platform:** Beehiiv (free to 2,500 subscribers)

**Automation:** Python script renders a Jinja2 template from the DB → paste into Beehiiv. Ship every Monday morning.

**Content:** Biggest spread of the week, any ±2σ events, yield vs. benchmark narrative.

**Distribution:** Submit to RWA-focused Substacks, DeFi podcasts, and tokenization Discords for cross-promotion.

---

## Phase 5: Paid Product (Month 3+)

Once newsletter hits ~500 engaged subscribers, layer on:

| Tier | Price | What |
|------|-------|------|
| Free | $0 | Dashboard + weekly newsletter |
| Pro | $99/mo | API access, 5-min refresh, email alerts on threshold breaches |
| Institutional | $500/mo | Historical CSV export, custom asset tracking, Slack/webhook alerts |

**First outbound targets:** Newsletter readers who work at allocators or tokenized fund issuers.

---

## Milestones

| Week | Deliverable |
|------|-------------|
| 1 | Data spike — three working collector scripts |
| 2–3 | Pipeline running, SQLite populated with 2 weeks of history |
| 3 | Pricing logic + ±2σ alert logic complete |
| 4–5 | Dashboard live at a real domain |
| 5 | First newsletter issue shipped |
| 12 | 500 subscribers, open Pro tier waitlist |

---

## Why This, Why Now

- Tokenized treasury market has grown from ~$100M (2023) to $5B+ AUM (2025) with continued institutional inflows
- No real-time NAV-vs-market spread tracker exists publicly
- Data costs are near-zero (FRED free, Alchemy free tier, CoinGecko free tier)
- Directly leverages pricing analytics expertise
- B2B revenue path is clear: issuers want third-party benchmarks; allocators want reconciliation tooling
