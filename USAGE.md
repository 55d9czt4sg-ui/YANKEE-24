# USAGE.md - Complete CLI Reference & Examples

This guide covers every command-line flag, output format, and practical usage pattern for the Core Market Regime Framework screener.

## Table of Contents

1. [CLI Reference](#cli-reference)
2. [Usage Examples](#usage-examples)
3. [Output Formats](#output-formats)
4. [Watchlist Format](#watchlist-format)
5. [Configuration](#configuration)
6. [Status Badges & Recommendations](#status-badges--recommendations)
7. [Troubleshooting](#troubleshooting)

---

## CLI Reference

### Command Structure

```
python main.py [OPTIONS]
```

### All 12 Flags

#### `--watchlist PATH`
**Purpose:** Use a custom ticker list instead of the default SPX+NDX universe.

**Data type:** File path (string)

**Default:** None (uses default config.ALL_TICKERS)

**Examples:**
```bash
python main.py --watchlist my_watchlist.json
python main.py --watchlist my_watchlist.txt
```

**Supported formats:**
- `.json`: `["AAPL", "MSFT", "NVDA"]` (JSON array)
- `.txt`: One ticker per line
- See [Watchlist Format](#watchlist-format) section

**Notes:**
- If file not found, error is displayed and scan exits
- Duplicates are automatically deduplicated
- Case-insensitive (AAPL = aapl)

---

#### `--export-json`
**Purpose:** Export scan results to JSON file in the `scans/` directory.

**Data type:** Boolean flag (no value required)

**Default:** False (no JSON export)

**Examples:**
```bash
python main.py --export-json
python main.py --top-n 10 --export-json
python main.py --export-json --quiet
```

**Output location:** `scans/{TIMESTAMP}.json` (e.g., `scans/2026-10-01-14-30.json`)

**Notes:**
- Includes full metadata (timestamp, universe, cache stats)
- Contains all ranked candidates with filter results
- Machine-readable for downstream processing

---

#### `--export-csv`
**Purpose:** Export scan results to CSV file in the `scans/` directory.

**Data type:** Boolean flag (no value required)

**Default:** False (no CSV export)

**Examples:**
```bash
python main.py --export-csv
python main.py --min-dealer-score 75 --export-csv
python main.py --export-json --export-csv
```

**Output location:** `scans/{TIMESTAMP}.csv` (e.g., `scans/2026-10-01-14-30.csv`)

**Notes:**
- Headers: Rank, Ticker, Price, Target, Bull/Bear, Gamma, Composite, Status, Recommendation
- Spreadsheet-friendly (opens in Excel, Google Sheets, etc.)
- One row per candidate

---

#### `--top-n N`
**Purpose:** Show only the top N ranked candidates (by composite rank).

**Data type:** Integer

**Default:** None (show all passing candidates)

**Examples:**
```bash
python main.py --top-n 10
python main.py --top-n 5 --min-dealer-score 80
python main.py --top-n 20 --export-json
```

**Notes:**
- Applied AFTER filtering
- If 50 candidates pass but --top-n 10, shows only top 10 of the 50
- Useful for focusing on best setups in large scans

---

#### `--min-gamma-buildup PERCENT`
**Purpose:** Filter results to only those with gamma buildup >= specified percentage.

**Data type:** Float

**Default:** None (no minimum gamma filter)

**Examples:**
```bash
python main.py --min-gamma-buildup 100
python main.py --min-gamma-buildup 200.5 --top-n 15
```

**Typical values:**
- `50`: Minimum PRIME status
- `150`: Minimum HOT status
- `200`: Strong gamma candidates only
- `500`: Extreme (EXPLOSIVE) candidates only

**Notes:**
- Filters BEFORE applying --top-n
- Gamma buildup is dealer-short magnitude

---

#### `--min-dealer-score SCORE`
**Purpose:** Filter results to only those with dealer score >= specified value (0-100).

**Data type:** Integer (0-100)

**Default:** None (no minimum dealer score)

**Examples:**
```bash
python main.py --min-dealer-score 70
python main.py --min-dealer-score 80 --top-n 10
python main.py --min-dealer-score 50 --export-json
```

**Typical values:**
- `50`: Baseline acceptable (all conditions met)
- `70`: Good (most factors aligned)
- `80`: Strong (excellent alignment)
- `90+`: Elite (maximum positioning)

**Notes:**
- Filters BEFORE applying --top-n
- Dealer score = composite positioning metric (see README for calculation)

---

#### `--max-price PRICE`
**Purpose:** Filter results to only those with price <= specified value.

**Data type:** Float (currency)

**Default:** None (no maximum price)

**Examples:**
```bash
python main.py --max-price 100
python main.py --max-price 250.50 --top-n 20
```

**Use cases:**
- Prefer smaller-cap names: `--max-price 50`
- Avoid mega-cap: `--max-price 500`
- Mid-cap focus: `--max-price 300`

**Notes:**
- Filters BEFORE applying --top-n
- Price is current market price

---

#### `--min-bull-bear RATIO`
**Purpose:** Filter results to only those with bull/bear ratio >= specified value.

**Data type:** Float

**Default:** None (no minimum ratio)

**Examples:**
```bash
python main.py --min-bull-bear 1.5
python main.py --min-bull-bear 2.0 --top-n 10
```

**Typical values:**
- `1.0`: Neutral (equal bullish/bearish)
- `1.5`: Moderately bullish
- `2.0`: Very bullish
- `2.5+`: Extremely bullish

**Notes:**
- Filters BEFORE applying --top-n
- Bull/bear ratio = indicator of vanna positioning strength

---

#### `--no-cache`
**Purpose:** Skip the cache layer and fetch all data fresh from QuantWheel.

**Data type:** Boolean flag (no value required)

**Default:** False (use cache)

**Examples:**
```bash
python main.py --no-cache
python main.py --no-cache --top-n 5
```

**When to use:**
- You need fresh data immediately (market just opened)
- Cache may be stale (more than 5 minutes old)
- Debugging cache issues
- First run of the day

**Notes:**
- Slower (hits API for every ticker)
- Without --no-cache: 80%+ cache hit rate (5-min TTL)

---

#### `--cache-ttl MINUTES`
**Purpose:** Override the default cache TTL (time-to-live) in minutes.

**Data type:** Integer (minutes)

**Default:** 5 (from config.CACHE_TTL_MINUTES)

**Examples:**
```bash
python main.py --cache-ttl 10
python main.py --cache-ttl 1 --no-cache
python main.py --cache-ttl 30
```

**Typical values:**
- `1`: Very fresh (high API load)
- `5`: Default (good balance)
- `10`: Less fresh, fewer API calls
- `30`: Stale data OK, minimal API load

**Notes:**
- Only applies if cache exists (ignored with --no-cache)
- Extends expiry only for NEW cache entries
- Does NOT affect already-cached entries

---

#### `--quiet`
**Purpose:** Suppress CLI output. Export to files only (JSON/CSV).

**Data type:** Boolean flag (no value required)

**Default:** False (show CLI table + summary)

**Examples:**
```bash
python main.py --export-json --quiet
python main.py --export-csv --quiet
python main.py --export-json --export-csv --quiet
```

**When to use:**
- Automated/scheduled scans
- Running as a background job
- Only care about file output
- Piping to other scripts

**Notes:**
- Still prints export paths (file created at X)
- Doesn't suppress warnings
- If no --export-json or --export-csv, output goes nowhere (be careful!)

---

#### `--debug`
**Purpose:** Enable debug logging for troubleshooting.

**Data type:** Boolean flag (no value required)

**Default:** False (normal output)

**Examples:**
```bash
python main.py --debug
python main.py --debug --top-n 5
```

**What it shows:**
- Detailed error messages for each ticker
- API call statistics
- Cache hit/miss details
- Filter condition results per ticker

**When to use:**
- Debugging missing candidates
- Tracking down API errors
- Understanding why a ticker was skipped
- Performance profiling

**Notes:**
- Verbose output (harder to read)
- Slower (more logging overhead)
- Only for troubleshooting, not daily use

---

## Usage Examples

### Basic Scan (No Filters)

```bash
python main.py
```

**What it does:**
1. Loads all 600 tickers (SPX 500 + NDX 100)
2. Fetches GEX, Vanna, Quote for each
3. Applies 6-condition filter
4. Ranks all passing candidates
5. Displays CLI table
6. Shows summary stats

**Sample output:**
```
BULLISH DRIFT SCAN - SPX + NDX
═══════════════════════════════════════════════════════════════════════════════════════════════

Rank  Ticker    Price     Target    Bull/Bear  Gamma ↑     Composite  Status
────  ─────────  ────────  ────────  ─────────  ──────────  ─────────  ──────────
1     NVDA      $120.45   $130.00   2.15x      +240.5%     9.2/10     HOT
2     META      $445.20   $460.00   1.98x      +185.3%     8.9/10     HOT
3     MSFT      $380.15   $395.00   1.85x      +156.2%     8.7/10     HOT
4     AAPL      $228.90   $240.00   1.72x      +125.8%     8.3/10     PRIME
5     AMZN      $185.60   $200.00   1.65x      +89.4%      7.8/10     PRIME

📊 SUMMARY
────────────────────────────────────────────────────────────────────────────────
Tickers Scanned:        600
Passed Filters:         5
Top Candidate:          NVDA (composite rank 9.2/10)
Cache Hit Rate:         81.5%
Data Freshness:         2 minutes
```

---

### Top-N High Gamma Candidates

```bash
python main.py --top-n 10 --min-gamma-buildup 150
```

**What it does:**
1. Loads default 600 tickers
2. Applies filtering
3. Filters to gamma >= 150% (HOT status minimum)
4. Shows only top 10 by composite rank

**Use case:** Find the 10 hottest gamma plays right now.

---

### Filter by Dealer Score

```bash
python main.py --min-dealer-score 75 --top-n 20
```

**What it does:**
1. Loads default 600 tickers
2. Applies filtering
3. Filters to dealer score >= 75 (strong alignment)
4. Shows top 20 of qualifying candidates

**Use case:** Only trade when dealer positioning is optimal.

---

### Price-Based Filtering

```bash
python main.py --max-price 300 --top-n 15
```

**What it does:**
1. Loads default 600 tickers
2. Applies filtering
3. Filters to price <= $300
4. Shows top 15 of qualifying candidates

**Use case:** Focus on mid-cap names under $300.

---

### Bull/Bear Ratio Filter

```bash
python main.py --min-bull-bear 2.0 --top-n 10
```

**What it does:**
1. Loads default 600 tickers
2. Applies filtering
3. Filters to bull/bear >= 2.0 (very bullish)
4. Shows top 10 of qualifying candidates

**Use case:** Only trade extremely bullish vanna setups.

---

### Multiple Filters Combined

```bash
python main.py \
  --min-gamma-buildup 150 \
  --min-dealer-score 70 \
  --max-price 400 \
  --min-bull-bear 1.8 \
  --top-n 15
```

**What it does:**
1. Loads default 600 tickers
2. Applies filtering (6 conditions must pass)
3. Filters to:
   - Gamma >= 150% (HOT status)
   - Dealer score >= 70 (strong)
   - Price <= $400 (large-cap)
   - Bull/bear >= 1.8 (bullish)
4. Shows top 15 of qualifying candidates

**Use case:** Find the most carefully curated setups.

---

### Export to JSON

```bash
python main.py --export-json
```

**Output:** `scans/2026-10-01-14-30.json`

**Sample JSON structure:**
```json
{
  "timestamp": "2026-10-01T14:30:00Z",
  "universe": ["SPX", "NDX"],
  "tickers_scanned": 600,
  "candidates_passed": 5,
  "data_freshness_minutes": 2,
  "cache_hit_rate": 0.815,
  "ranked_list": [
    {
      "ticker": {
        "name": "NVDA",
        "current_price": 120.45,
        "current_iv": 0.32,
        "bullish_target": 130.00,
        "put_wall": 115.00,
        "call_wall": 135.00
      },
      "gex": {
        "net_gamma": 0.045,
        "gamma_buildup_pct": 240.5
      },
      "vanna": {
        "vanna_regime": "positive",
        "bull_bear_ratio": 2.15,
        "bullish_target": 130.00
      },
      "filters_passed": {
        "positive_gamma": true,
        "positive_vanna": true,
        "iv_dropping": true,
        "put_wall_proximity": true,
        "dte_range": true,
        "bullish_drift": true
      },
      "composite_rank": 9.2,
      "status": "HOT",
      "trade_recommendation": "MOMENTUM_SCALP"
    }
  ]
}
```

**Use case:** API integration, downstream processing, data analysis.

---

### Export to CSV

```bash
python main.py --export-csv
```

**Output:** `scans/2026-10-01-14-30.csv`

**Sample CSV structure:**
```
Rank,Ticker,Price,Target,Bull/Bear,Gamma,Composite,Status,Recommendation
1,NVDA,120.45,130.00,2.15,240.5,9.2,HOT,MOMENTUM_SCALP
2,META,445.20,460.00,1.98,185.3,8.9,HOT,MOMENTUM_SCALP
3,MSFT,380.15,395.00,1.85,156.2,8.7,HOT,MOMENTUM_SCALP
4,AAPL,228.90,240.00,1.72,125.8,8.3,PRIME,BUY_DIPS
5,AMZN,185.60,200.00,1.65,89.4,7.8,PRIME,BUY_DIPS
```

**Use case:** Open in Excel, Google Sheets, or spreadsheet tools.

---

### Export Both Formats

```bash
python main.py --export-json --export-csv
```

**Output:**
- `scans/2026-10-01-14-30.json` (machine-readable)
- `scans/2026-10-01-14-30.csv` (human-readable/spreadsheet)

**Use case:** Dual output for API + manual analysis.

---

### Custom Watchlist

```bash
python main.py --watchlist tech_stocks.json
```

**tech_stocks.json:**
```json
["AAPL", "MSFT", "NVDA", "GOOGL", "META", "TSLA", "AMD"]
```

**What it does:**
1. Loads 7 tickers from file
2. Applies filtering
3. Shows results

**Use case:** Focus on specific sectors or holdings.

---

### Quiet Mode (Automated)

```bash
python main.py --export-json --export-csv --quiet
```

**Output:**
- `scans/2026-10-01-14-30.json`
- `scans/2026-10-01-14-30.csv`
- Console: Only file paths (no table)

**Use case:** Scheduled jobs, cron tasks, no human monitoring.

---

### Debug Mode

```bash
python main.py --debug --top-n 5
```

**Prints:**
- Detailed error messages for each ticker
- API call timing
- Cache hit/miss for each lookup
- Filter results per ticker

**Use case:** Troubleshooting why candidates were filtered out.

---

### Fresh Data Only

```bash
python main.py --no-cache
```

**What it does:**
1. Skips cache entirely
2. Fetches all data from QuantWheel
3. (Slower but guaranteed fresh)

**Use case:** Market opened, need latest positioning.

---

### Extended Cache TTL

```bash
python main.py --cache-ttl 30
```

**What it does:**
1. Uses existing cache (if any)
2. Extends TTL to 30 minutes
3. Minimal API load

**Use case:** Running multiple scans in a short window.

---

## Output Formats

### CLI Table Format

```
BULLISH DRIFT SCAN - SPX + NDX
═════════════════════════════════════════════════════════════════════════════════════

Rank  Ticker  Price     Target   Bull/Bear  Gamma ↑     Composite  Status
────  ──────  ────────  ───────  ─────────  ──────────  ─────────  ──────────
1     NVDA    $120.45   $130.00  2.15x      +240.5%     9.2/10     HOT
2     META    $445.20   $460.00  1.98x      +185.3%     8.9/10     HOT
3     MSFT    $380.15   $395.00  1.85x      +156.2%     8.7/10     HOT

📊 SUMMARY
────────────────────────────────────────────────────────────────────────────────
Tickers Scanned:        600
Passed Filters:         3
Top Rank Candidate:     NVDA (9.2/10)
Cache Hit Rate:         81.5%
Data Freshness:         2 minutes
```

**Columns:**
- **Rank**: Position by composite rank (1 = best)
- **Ticker**: Stock symbol
- **Price**: Current market price
- **Target**: Bullish target from vanna analysis
- **Bull/Bear**: Bull/bear ratio (higher = more bullish)
- **Gamma ↑**: Gamma buildup percentage
- **Composite**: Composite rank out of 10
- **Status**: EXPLOSIVE / HOT / PRIME / SOLID / CAUTION

---

### JSON Format

**Structure:**
```json
{
  "timestamp": "ISO-8601",
  "universe": ["SPX", "NDX"],
  "tickers_scanned": 600,
  "candidates_passed": 5,
  "data_freshness_minutes": 2,
  "cache_hit_rate": 0.815,
  "ranked_list": [
    {
      "ticker": {...},
      "gex": {...},
      "vanna": {...},
      "filters_passed": {...},
      "composite_rank": 9.2,
      "status": "HOT",
      "trade_recommendation": "MOMENTUM_SCALP"
    }
  ]
}
```

**Use case:** API integration, downstream data processing, programmatic analysis.

---

### CSV Format

**Headers:**
```
Rank,Ticker,Price,Target,Bull/Bear,Gamma,Composite,Status,Recommendation
```

**One row per candidate:**
```
1,NVDA,120.45,130.00,2.15,240.5,9.2,HOT,MOMENTUM_SCALP
2,META,445.20,460.00,1.98,185.3,8.9,HOT,MOMENTUM_SCALP
```

**Use case:** Excel, Google Sheets, spreadsheet analysis.

---

## Watchlist Format

### JSON Format (Recommended)

**File: my_watchlist.json**
```json
["AAPL", "MSFT", "NVDA", "GOOGL", "META", "TSLA", "AMD"]
```

**Usage:**
```bash
python main.py --watchlist my_watchlist.json
```

**Pros:**
- Structured, easy to parse
- Can add comments with tools like JSON5
- Sortable, mergeable with scripts

---

### Text Format (Simple)

**File: my_watchlist.txt**
```
AAPL
MSFT
NVDA
GOOGL
META
TSLA
AMD
```

**Usage:**
```bash
python main.py --watchlist my_watchlist.txt
```

**Pros:**
- Human-readable
- Editable in any text editor
- One ticker per line

**Notes:**
- Blank lines and whitespace are ignored
- Case-insensitive (AAPL = aapl)

---

### Dynamic Watchlist Generation

**Generate from text:**
```bash
# Create a list of tech stocks
echo -e "AAPL\nMSFT\nNVDA" > tech.txt
python main.py --watchlist tech.txt
```

**Generate from JSON:**
```bash
# Python script to generate
python -c "import json; print(json.dumps(['AAPL', 'MSFT', 'NVDA']))" > tech.json
python main.py --watchlist tech.json
```

---

## Configuration

### Custom Configuration (config.py)

**Location:** `config.py`

**Key settings:**

**Cache:**
```python
CACHE_TTL_MINUTES = 5
CACHE_BACKEND = "memory"  # "memory" or "sqlite"
```

**Filtering thresholds:**
```python
IV_DROP_THRESHOLD = "3day_avg"
PUT_WALL_PROXIMITY_PCT = 3.0  # 3% of put wall
DTE_MIN = 0
DTE_MAX = 21  # Near-term only
```

**Dealer scoring weights (must sum to 1.0):**
```python
DEALER_SCORE_WEIGHTS = {
    "gamma_buildup": 0.30,
    "bull_bear_ratio": 0.25,
    "dealer_positioning": 0.25,
    "put_wall_proximity": 0.20,
}
```

**Status badge breakpoints:**
```python
GAMMA_BUILDUP_THRESHOLDS = {
    "EXPLOSIVE": 500,      # > 500%
    "HOT": 150,            # 150-500%
    "PRIME": 50,           # 50-150%
    "SOLID": 0,            # 0-50%
    "CAUTION": float("-inf"),  # < 0%
}
```

**Adjusting thresholds:**
```python
# Make filtering stricter (fewer candidates)
PUT_WALL_PROXIMITY_PCT = 2.0  # Closer to wall
GAMMA_BUILDUP_THRESHOLDS["HOT"] = 200  # Higher threshold

# Make filtering looser (more candidates)
PUT_WALL_PROXIMITY_PCT = 5.0  # Further from wall
DTE_MAX = 35  # Include more expirations
```

---

## Status Badges & Recommendations

### Status Badges

| Status | Gamma Buildup | Color | Interpretation |
|--------|---------------|-------|-----------------|
| **EXPLOSIVE** | > 500% | 🔴 Red | Extreme dealer short gamma; every dip is buoyant |
| **HOT** | 150-500% | 🟠 Orange | Strong gamma buildup; solid support |
| **PRIME** | 50-150% | 🟡 Yellow | Good gamma position; decent setup |
| **SOLID** | 0-50% | 🟢 Green | Baseline passing; acceptable |
| **CAUTION** | < 0% | 🔵 Blue | Dealer long gamma; avoid or hedge |

---

### Trade Recommendations

| Recommendation | When | Strategy | Holding | Risk |
|---------------|------|----------|---------|------|
| **MOMENTUM_SCALP** | HOT/EXPLOSIVE + 2.0+ bull/bear | Ride momentum, tight stops | 1-3 days | Low-medium |
| **BUY_DIPS** | PRIME + put wall support | Wait for pullback, buy dip | 3-5 days | Medium |
| **SHORT_PUTS** | SOLID + clear support level | Sell puts at wall, collect | Until expiry | Medium-high |
| **SKIP** | CAUTION or dealer score < 50 | Don't trade | N/A | High |

---

## Troubleshooting

### No Candidates Found

**Symptoms:**
```
Tickers Scanned: 600
Passed Filters: 0
(No candidates found)
```

**Possible causes:**
1. Market regime doesn't support bullish drift (choppy, reversion)
2. Filters are too strict
3. API data is stale or missing

**Solutions:**
```bash
# Relax gamma buildup filter
python main.py --min-gamma-buildup 50

# Relax dealer score filter
python main.py --min-dealer-score 50

# Fetch fresh data
python main.py --no-cache

# Check API connectivity
python main.py --debug
```

---

### Cache Issues

**Symptom: "Cache miss on every run"**

**Solution:**
```bash
# Verify cache is working
python main.py --debug | grep cache

# Reset cache (clear old entries)
# (No built-in command; cache clears on new run)

# Extend TTL to increase hit rate
python main.py --cache-ttl 10
```

---

### Missing Data (Warnings)

**Symptoms:**
```
⚠️  WARNINGS
────────────────────────────────────────────────────────────────
AAPL: GEX/Vanna data missing (skipped)
MSFT: Quote data missing (skipped)
```

**Possible causes:**
1. QuantWheel API timeout or down
2. Ticker not found in QuantWheel database
3. No option data available for ticker

**Solutions:**
```bash
# Retry with fresh API calls
python main.py --no-cache

# Check API logs
python main.py --debug

# Wait a few minutes (API might be recovering)
sleep 60 && python main.py
```

---

### API Timeout

**Symptoms:**
```
Error: QuantWheel API timeout (10 seconds)
```

**Cause:** API is slow or unreachable

**Solutions:**
```bash
# Use cached data if available
python main.py

# Wait and retry
sleep 30 && python main.py

# Check API status (manual check of QuantWheel docs)
```

---

### Export Failed

**Symptoms:**
```
Error: Cannot write to scans/ directory
```

**Cause:** Permission issue or scans/ doesn't exist

**Solutions:**
```bash
# Create scans directory
mkdir -p scans

# Check permissions
ls -la scans/

# Fix permissions (if needed)
chmod 755 scans/
```

---

### Too Many Results

**Symptoms:**
```
Tickers Scanned: 600
Passed Filters: 150
(Table is huge)
```

**Solution:**
```bash
# Limit to top 20
python main.py --top-n 20

# Add minimum dealer score
python main.py --min-dealer-score 75 --top-n 20

# Raise gamma threshold
python main.py --min-gamma-buildup 200 --top-n 20
```

---

### Confusing Recommendations

**Issue:** Understand why a setup got a certain recommendation

**Solution:**
```bash
# Check the dealer score
python main.py --debug | grep "dealer_score"

# Check the status badge (gamma %)
python main.py | grep "Status"

# Check filters passed
python main.py --export-json | grep "filters_passed"
```

---

## Command Cheat Sheet

```bash
# Basic scan
python main.py

# Top 10, hot setups
python main.py --top-n 10 --min-gamma-buildup 150

# Strong dealer alignment
python main.py --min-dealer-score 80 --top-n 15

# Price filter (under $300)
python main.py --max-price 300 --top-n 20

# Export for analysis
python main.py --export-json --export-csv

# Quiet mode for automation
python main.py --export-json --quiet

# Fresh data (skip cache)
python main.py --no-cache

# Debug missing candidates
python main.py --debug --top-n 5

# Custom watchlist
python main.py --watchlist my_stocks.txt
```

---

For questions or issues, see README.md for system overview and Architecture.md for design details.
