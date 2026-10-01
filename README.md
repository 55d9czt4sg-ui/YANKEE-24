# Core Market Regime Framework

A production-grade screener for identifying dealer-aligned bullish drift candidates in the S&P 500 and Nasdaq-100. Built with options positioning data, gamma exposure analysis, and vanna charm dynamics from QuantWheel.

## Overview

The Core Market Regime Framework is designed for traders who want to identify high-probability bullish setups by aligning with dealer positioning, not against it. Rather than betting on contrarian reversals, this system detects when dealers are **short gamma** and **long volatility skew** (positive vanna), creating smooth uptrends.

**Use case**: Swing traders and momentum scalpers seeking 2-5 week holding horizons on the most technically sound bullish drift candidates from SPX+NDX.

## Key Features

- **6-condition filtering pipeline**: All conditions must pass simultaneously (AND logic, not OR)
  - Dealer short gamma buildup (positive gamma exposure for us)
  - Positive vanna positioning (bullish volatility skew)
  - Dropping IV regime (smoother trend conditions)
  - Distance to put walls (support/psychological levels)
  - DTE range validation (0-21 days, focusing on near-term drivers)
  - Bullish drift detection (price > bullish_target from vanna)

- **Dealer score (0-100)**: Composite positioning metric
  - Positive gamma: +25 points
  - Positive vanna: +20 points
  - IV dropping: +20 points
  - Bull/bear ratio bonus: 0-20 points (scaled to 1.0-3.0 range)
  - Bullish drift detected: +15 points

- **Composite ranking (0-10 deciles)**: Normalizes across candidate universe
  - Gamma buildup (30% weight)
  - Bull/bear ratio (25% weight)
  - Dealer score (25% weight)
  - Put wall proximity (20% weight)

- **3 output formats**: CLI table, JSON (API-friendly), CSV (spreadsheet-ready)

- **Real-time QuantWheel API integration**: Fetch GEX, Vanna, and Quote data live

- **5-minute caching layer**: 80%+ cache hit rate across consecutive scans
  - In-memory LRU with TTL-based expiry
  - Optional `--no-cache` flag for fresh data
  - Configurable TTL via `--cache-ttl` flag

- **Custom watchlist support**: JSON or .txt ticker files
  - Default: SPX 500 + NDX 100 (full universe scan)
  - Supply your own: `python main.py --watchlist my_tickers.txt`

- **12 CLI flags** for filtering, export, and configuration
  - Price caps, minimum dealer scores, gamma thresholds
  - Debug mode with detailed logs

## Installation

### Requirements
- Python 3.9+
- pip

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd trading-market-regime-framework

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# (Future) Configure QuantWheel API key in .env
# QUANTWHEEL_API_KEY=your_key_here
```

## Quick Start

```bash
# Basic scan: default SPX+NDX, CLI output
python main.py

# Top 10 high-gamma candidates
python main.py --top-n 10

# Filter by minimum dealer score (75/100)
python main.py --min-dealer-score 75 --top-n 20

# Use a custom watchlist
python main.py --watchlist my_watchlist.txt

# Export to JSON and CSV
python main.py --export-json --export-csv

# Combine multiple filters
python main.py \
  --min-gamma-buildup 150 \
  --min-dealer-score 70 \
  --max-price 300 \
  --top-n 15

# Quiet mode (output to files only)
python main.py --export-json --quiet

# Debug mode (detailed logs)
python main.py --debug
```

## Architecture Overview

### Data Pipeline

```
Load Tickers (SPX+NDX or Custom)
    ↓
For Each Ticker: Fetch Live Data
  ├─ Quote (price, IV)
  ├─ GEX (gamma exposure, buildup %)
  └─ Vanna Charm (bull/bear ratio, bullish target)
    ↓
Apply 6 Filtering Conditions (ALL must pass)
  ├─ Positive gamma (dealer short)
  ├─ Positive vanna (bullish skew)
  ├─ IV dropping (smooth trend)
  ├─ Put wall proximity (psychological support)
  ├─ DTE range (0-21 days)
  └─ Bullish drift (price > vanna target)
    ↓
Calculate Dealer Score (0-100)
    ↓
Normalize All Candidates to Deciles
    ↓
Calculate Composite Rank (0-10)
    ↓
Sort by Composite Rank (Descending)
    ↓
Apply CLI Filters (--top-n, --min-*, --max-*)
    ↓
Format Output (CLI / JSON / CSV)
    ↓
Export to scans/ Directory
```

### Module Breakdown

**config.py** - Central configuration hub
- Cache settings (TTL, backend)
- Filtering thresholds (gamma, IV, DTE)
- Dealer scoring weights (must sum to 1.0)
- Status badge breakpoints (EXPLOSIVE, HOT, PRIME, SOLID, CAUTION)
- Hardcoded ticker lists (SPX 500 + NDX 100)

**models.py** - Data class definitions
- `Ticker`: Price, IV, bullish target, put/call walls
- `GEXData`: Net gamma, gamma buildup percentage
- `VannaData`: Vanna regime, bull/bear ratio, bullish target
- `Setup`: A single candidate with all metadata
- `ScanResult`: Complete scan with rankings and metadata

**quantwheel_client.py** - QuantWheel MCP API client with caching
- `Cache` class: In-memory TTL-based cache
- `QuantWheelClient` class: Fetch GEX, Vanna, Quote with automatic caching
- Cache stats tracking (hits, misses, freshness)

**screener.py** - Filtering engine and scoring logic
- `IVTrendAnalyzer`: Detects rising/dropping/flat IV conditions
- `ScreeningEngine`: 6-condition filter checker
- `DealerScorer`: Calculates dealer score (0-100) and composite rank (0-10)

**output.py** - Result formatters
- `CLIFormatter`: Pretty ASCII table with summary stats
- `JSONExporter`: Machine-readable JSON with full metadata
- `CSVExporter`: Spreadsheet-friendly CSV for Excel/Sheets

**main.py** - CLI orchestration
- Argument parsing (12 flags)
- Ticker loading (from default or custom watchlist)
- Pipeline execution
- Export handling

### Filtering Conditions

All 6 conditions must pass for a candidate to qualify. Here's what each measures:

1. **Positive Gamma (Dealer Short)**
   - Gamma exposure > 0 means dealers are short gamma
   - When price rises, dealers buy (supporting momentum)
   - Smoother, less reversionary trends

2. **Positive Vanna (Bullish Skew)**
   - Vanna > 0 = positive convexity on upside
   - Put skew < call skew = buyers paying for upside
   - Market expects higher prices

3. **IV Dropping**
   - Current IV < 3-day average IV
   - Lower volatility = trend continuation (not reversal)
   - Comfier risk environment for longs

4. **Put Wall Proximity**
   - Price within 3% of put wall (configurable)
   - Put walls = dealer hedges / technical support
   - Close proximity suggests limited downside

5. **DTE Range (0-21 days)**
   - Focus on near-term drivers, skip far-dated noise
   - 0-7 DTE: Immediate catalysts
   - 8-14 DTE: Earnings, economic data
   - 15-21 DTE: Next rotation windows

6. **Bullish Drift Detection**
   - Price > bullish_target from vanna analysis
   - Confirms upward momentum has already begun
   - Catches early momentum, not contrarian reversals

### Dealer Scoring Methodology

The dealer score (0-100) measures how aligned a setup is with dealer positioning:

```
Dealer Score Calculation:
  Base = 0
  + 25 if positive gamma
  + 20 if positive vanna
  + 20 if IV dropping
  + 15 if bullish drift detected
  + 0-20 interpolated from bull/bear ratio (1.0 → 0, 2.5+ → 20)
  ─────
  Capped at 100
```

**Interpretation:**
- 90-100: Elite (all conditions + strong bull/bear ratio)
- 75-89: Strong (most conditions, solid ratio)
- 60-74: Solid (baseline passing)
- 45-59: Weak (borderline, few factors)
- 0-44: Very weak (don't trade)

### Composite Ranking with Deciles

After screening, all candidates are ranked against each other using decile normalization:

```
For each candidate, convert to deciles:
  Gamma buildup → 0-10 decile (30% weight)
  Bull/bear ratio → 0-10 decile (25% weight)
  Dealer score → 0-10 decile (25% weight)
  Put wall proximity → 0-10 decile (20% weight)

Composite Rank = sum of weighted deciles
Result: 0-10 final ranking
```

Higher composite rank = better relative positioning in your filtered universe.

### Caching Strategy

**How caching works:**
- Each API call (GEX, Vanna, Quote) is cached with a 5-minute TTL
- Cache key format: `{data_type}:{ticker}:{expiration}` (e.g., `gex:AAPL:2026-10-18`)
- On repeat scans, 80%+ of data comes from cache (avoiding API overhead)

**TTL explanation:**
- 5 minutes is the default, fits intra-day scan frequency
- Longer TTL (10-60 min) = stale data but fewer API calls
- Shorter TTL (1-2 min) = fresh data but higher API load

**Cache statistics:**
```bash
# Printed after each scan (if not --quiet)
Cache Stats:
  Valid entries: 489/600
  Hit rate: 81.5%
  API calls: 109
```

**Bypass caching:**
```bash
python main.py --no-cache          # Fresh fetch only
python main.py --cache-ttl 10      # Extend to 10 minutes
```

## Concepts & Glossary

### Gamma Exposure (GEX)

**What it is:** The rate at which dealers' delta changes as the stock price moves.

**Positive gamma (GEX > 0):**
- Dealers are short gamma (short straddles, short vega)
- As price rises, dealers buy to hedge (long delta)
- Supports momentum, smoother trends

**Negative gamma (GEX < 0):**
- Dealers are long gamma (long calls/puts, long straddles)
- As price rises, dealers sell to hedge (reduce delta)
- Reverses momentum, choppy trends

**For this screener:** We want positive gamma (dealer short) because it supports our bullish drift.

### Vanna Positioning

**What it is:** The sensitivity of options gamma to changes in volatility (third-order Greek).

**Positive vanna:**
- Upside calls have high gamma, downside puts have low gamma
- Bullish skew in option prices
- Dealers profitable when volatility drops AND price rises
- Signal: market expecting higher prices

**Negative vanna:**
- Downside puts have high gamma, upside calls have low gamma
- Bearish skew
- Dealers profitable when volatility drops AND price falls

**For this screener:** We want positive vanna (bullish skew) because it aligns with upside targets.

### IV Regime (Implied Volatility Trend)

**Dropping IV:** Current IV < 3-day average IV
- Market uncertainty decreasing
- Trends tend to continue (not reverse)
- Lower volatility = better reward/risk for directional bets

**Rising IV:** Current IV > 3-day average IV
- Market uncertainty increasing
- Reversions more likely
- Choppy, rangy markets

**For this screener:** We want dropping IV because smooth IV environment supports momentum.

### Dealer Alignment (Why NOT Contrarian)

**Traditional contrarian view:**
- "Dealers are always wrong, trade the opposite"
- True sometimes, but expensive and choppy

**Dealer-aligned view (this system):**
- "Trade WITH dealers when they're set up for profit"
- Dealers profit when you win: smooth uptrend, vol compression
- Naturally smoother because they're hedging into the trade

**Example scenario:**
- Dealer is short gamma + long vanna (this setup)
- Dealer hedges by buying calls on the way up
- Your bullish position rides their hedging demand
- Trend is self-supporting

### Put Walls & Call Walls

**Put wall:** Concentration of put option open interest at a price level (usually below current price)
- Acts as psychological support
- Dealers' hedge against downside
- Price near put wall = limited downside risk

**Call wall:** Concentration of call option open interest above current price
- Acts as resistance
- Dealers' cap on upside profits
- Price approaching call wall = where profit-taking happens

**For this screener:** We check distance to put walls to ensure support cushion.

### Bullish Drift

**What it is:** Price > bullish_target from vanna analysis

**Why it matters:**
- Not a contrarian setup (price already moving)
- Catches momentum continuation, not reversals
- Earlier entries have better R:R than waiting for reversal

**Interpretation:**
- Price is already above dealer's computed bullish target
- Momentum is established
- Setup is confirmation-based, not prediction-based

## Test Coverage

The system includes 69 passing unit and integration tests covering:

- Data model validation
- Filtering engine logic (all 6 conditions)
- Dealer scoring calculations
- Composite ranking and decile normalization
- CLI argument parsing
- Output formatters (CLI, JSON, CSV)
- Caching layer (hits, misses, TTL expiry)
- End-to-end pipeline

Run tests:
```bash
pytest -v                  # Verbose output
pytest -k test_filters    # Run only filter tests
pytest --cov             # Coverage report
```

## Status Badges

The system assigns each candidate a **status badge** based on gamma buildup percentage:

| Status | Gamma Buildup | Interpretation |
|--------|---------------|-----------------|
| **EXPLOSIVE** | > 500% | Extreme dealer short gamma; buy every dip |
| **HOT** | 150-500% | Strong gamma buildup; significant support |
| **PRIME** | 50-150% | Solid gamma position; good setup |
| **SOLID** | 0-50% | Baseline passing; acceptable |
| **CAUTION** | < 0% | Dealer long gamma; choppy / reverting |

## Trade Recommendations

Based on status and technical setup, the system recommends actions:

| Recommendation | When | Strategy |
|---------------|------|----------|
| **MOMENTUM_SCALP** | HOT/EXPLOSIVE + strong bull/bear | Ride the momentum wave, 1-3 day holds |
| **BUY_DIPS** | PRIME + nearby support | Wait for pullback to support (put wall), buy dip |
| **SHORT_PUTS** | SOLID + defined support | Sell puts at put wall, collect premium |
| **SKIP** | CAUTION or low dealer score | Avoid; not aligned with dealer positioning |

## License

MIT License - See LICENSE file for details.

---

**Questions or issues?** See USAGE.md for detailed CLI reference and troubleshooting, or Architecture.md for system design deep-dives.
