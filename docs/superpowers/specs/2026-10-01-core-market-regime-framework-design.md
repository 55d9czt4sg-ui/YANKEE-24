# Core Market Regime Framework — Design Specification

**Date:** 2026-10-01  
**Author:** Claude Haiku 4.5  
**Status:** Design Phase  
**Version:** 1.0

---

## 1. Executive Summary

A daily screening system that identifies high-probability bullish drift opportunities across SPX + NDX by analyzing dealer positioning through three flow pillars (Gamma, Vanna, IV) and selecting only setups aligned with dealer long gamma + positive vanna + dropping IV within 3% of put wall support.

The system ranks 600 stocks (SPX 500 + NDX 100), filters for 6 required conditions, scores by dealer alignment, and outputs a ranked CLI table. Results are cached, exportable (JSON/CSV), and historically logged for backtesting and refinement.

---

## 2. Problem Statement

**Current workflow:** Manual daily review of gamma/vanna/IV across multiple tickers, visual inspection of SMC levels, decision-making on whether conditions align for trading. Time-consuming, error-prone, inconsistent application of rules.

**Desired outcome:** Automated daily scan that:
- Identifies all tickers meeting your bullish drift criteria
- Ranks them by setup quality (dealer alignment strength)
- Provides actionable trade recommendations (buy dips, short puts)
- Logs historical data for performance tracking

**Success criteria:**
- All 6 filtering conditions applied consistently
- High-conviction setups ranked #1 (gamma buildup + bull/bear ratio + dealer score)
- Output matches your visual reference format
- Repeatable daily (< 2 min scan time)
- Exportable for personal spreadsheet workflows

---

## 3. System Architecture

### 3.1 Data Flow

```
Input: SPX 500 + NDX 100 (or custom watchlist via --watchlist flag)
   ↓
[CACHE CHECK] — Lookup ticker in QuantWheel cache (TTL: 5 min)
   ├→ CACHED (< 5 min old): Use stored data
   └→ STALE/MISSING: Fetch fresh from QuantWheel APIs
   ↓
Per-Ticker Analysis (with error handling):
   • get_gex(ticker, expiration) → gamma, put_wall, call_wall, net_gamma
   • get_vanna_charm(ticker) → bullDriftTarget, bullBearRatio, vannaRegime
   • get_quote(ticker) → current_price, current_iv
   • Calculate IV trend (3-day avg, 5-day avg, direction)
   • Build Dealer Positioning Score (0-100 composite)
   ↓
Apply 6 Required Filters (All must pass):
   1. Positive Gamma: net_gamma > 0
   2. Positive Vanna: vannaRegime == "positive"
   3. IV Dropping: current_iv < 3day_avg_iv
   4. Put Wall Proximity: price ≤ put_wall * 1.03
   5. DTE Range: At least one expiration in 0-21 days
   6. Bullish Drift Active: bullDriftTarget exists & > current_price
   ↓
Rank Remaining Candidates by Composite Score:
   • Gamma buildup % (5-day net gamma change): weight 30%
   • Bull/Bear ratio (vanna_charm): weight 25%
   • Dealer positioning score: weight 25%
   • Put wall proximity (% above): weight 20%
   ↓
Output:
   • CLI Table (sorted by composite score, descending)
   • JSON export (optional, --export-json flag)
   • CSV export (optional, --export-csv flag)
   • Auto-logged scan file (scans/YYYY-MM-DD-HH-MM.json)
   ↓
[WATCHLIST TRACKING] — Append scan result to watchlist tracker
```

### 3.2 Core Components

**A. QuantWheel Client (quantwheel_client.py)**
- Wrapper around QuantWheel MCP tools
- Caching layer (in-memory + optional SQLite)
- Batch ticker fetching (minimize API calls)
- Error handling (timeout, missing data, API rate limits)
- Returns standardized data structures

**B. Screener (screener.py)**
- Filter engine (apply 6 conditions)
- IV trend calculation (3-day/5-day rolling avg)
- Dealer positioning score calculation (0-100)
- Ranking/sorting logic
- Returns list of Setup objects (sorted by rank)

**C. Models (models.py)**
- `Ticker`: symbol, current_price, current_iv
- `GEXData`: net_gamma, put_wall, call_wall, gamma_buildup_pct
- `VannaData`: vannaRegime, bullDriftTarget, bullBearRatio
- `Setup`: ticker, scores, filters_passed, rank, trade_recommendation
- `ScanResult`: timestamp, tickers_scanned, candidates_passed, ranked_list

**D. Output Formatter (output.py)**
- CLI table (using tabulate library)
- JSON serializer (for export)
- CSV writer (for spreadsheet import)
- Summary stats (total scanned, passed, top rank)

**E. Configuration (config.py)**
- Cache TTL (default: 5 min)
- IV drop threshold (default: current < 3day_avg)
- Put wall proximity (default: ±3%)
- Min/max price filters (CLI-configurable)
- Dealer score weights (configurable, currently: gamma 30%, bull/bear 25%, dealer 25%, proximity 20%)

**F. Main CLI (main.py)**
- Entry point
- Argument parsing (--watchlist, --export-json, --export-csv, --top-n, --min-gamma, etc.)
- Orchestrates scan
- Calls screener → formatter → output

---

## 4. Filtering Rules (6 Required Conditions)

All must pass for a ticker to be included in results.

| # | Condition | Data Source | Pass Criteria | Fail Criteria | Severity |
|---|-----------|-------------|---------------|---------------|----------|
| 1 | **Positive Gamma** | get_gex() → net_gamma | net_gamma > 0 | net_gamma ≤ 0 | HARD |
| 2 | **Positive Vanna** | get_vanna_charm() → vannaRegime | vannaRegime == "positive" | vannaRegime == "negative" | HARD |
| 3 | **IV Dropping** | get_quote() → current_iv vs. 3-day avg | current_iv < avg_iv_3d | current_iv ≥ avg_iv_3d | HARD |
| 4 | **Put Wall Proximity** | get_gex() → put_wall | price ≤ put_wall × 1.03 | price > put_wall × 1.03 | HARD |
| 5 | **DTE Range** | Expiration lookup | At least one expiration 0-21 days | All expirations > 21 days | HARD |
| 6 | **Bullish Drift Active** | get_vanna_charm() → bullDriftTarget | bullDriftTarget exists & > price | No bullDriftTarget or ≤ price | HARD |

**Logic:** If any condition fails, ticker is excluded from final output (marked as "SKIP" in debug logs).

---

## 5. Scoring & Ranking

### 5.1 Gamma Buildup %
**Source:** get_gex() over 5-day period (current net_gamma vs. 5-day rolling average)

**Calculation:**
```
gamma_buildup_pct = ((current_net_gamma - avg_5d_net_gamma) / abs(avg_5d_net_gamma)) × 100
```

**Score mapping:**
- \> 500% → 🚀 EXPLOSIVE (10/10)
- 250-500% → 🔥 HOT (8-9/10)
- 100-250% → 🔥 HOT (7-8/10)
- 50-100% → ✅ PRIME (6-7/10)
- 0-50% → ✅ SOLID (5-6/10)
- < 0% → ⚠️ CAUTION (skip or low confidence)

### 5.2 Bull/Bear Ratio
**Source:** get_vanna_charm() → bullBearRatio

**Interpretation:**
- \> 2.5x → Extreme bullish skew (score +2)
- 2.0-2.5x → Strong bullish (score +1.5)
- 1.5-2.0x → Bullish (score +1)
- 1.0-1.5x → Weak bullish (score +0.5)
- < 1.0x → Bearish (fail filter)

### 5.3 Dealer Positioning Score (0-100)
**Composite score from 4 aligned signals:**

```
dealer_score = (
  (gamma_positive ? 25 : 0) +           # Net gamma > 0 = +25
  (vanna_positive ? 20 : 0) +           # Vanna regime positive = +20
  (iv_dropping ? 20 : 0) +              # IV trend down = +20
  (bullish_ratio_bonus) +               # Bull/bear ratio: 0-20 (interpolated)
  (drift_active ? 15 : 0)               # bullDriftTarget active = +15
)
```

**Range:** 0-100
- **90-100** 🔥 Extremely strong dealer alignment
- **80-89** 🔥 Strong dealer alignment
- **70-79** ✅ Solid dealer alignment
- **60-69** ✅ Moderate dealer alignment
- **< 60** ⚠️ Weak dealer alignment (may skip)

### 5.4 Put Wall Proximity Score
**Source:** get_gex() → put_wall vs. current price

**Calculation:**
```
proximity_pct = ((price - put_wall) / put_wall) × 100
proximity_score = 20 × (1 - (proximity_pct / 3))  # 0-20 scale
```

**Interpretation:**
- At put wall (0% above) → 20/20
- 1.5% above → 10/20
- 3% above → 0/20 (at the edge of our ±3% requirement)

### 5.5 Composite Rank Score (1-10)
**Weighted average of 4 components:**

```
composite_score = (
  (gamma_buildup_pct_decile × 0.30) +     # Gamma buildup: 30%
  (bull_bear_ratio_decile × 0.25) +      # Bull/bear ratio: 25%
  (dealer_score_decile × 0.25) +         # Dealer score: 25%
  (put_wall_proximity_decile × 0.20)     # Put wall proximity: 20%
)
```

**Decile conversion:** Convert each metric to 0-10 scale based on current scan results.

**Final rank:** Sort descending by composite_score.

---

## 6. Output Format

### 6.1 CLI Table (Default)

```
BULLISH DRIFT SCAN - SPX + NDX
═══════════════════════════════════════════════════════════════════════════════════════════════════
Rank | Ticker | Price  | Target | Put Wall | Call Wall | Bull/Bear | Gamma ↑  | Dealer Score | Status
-----|--------|--------|--------|----------|-----------|-----------|----------|--------------|----------
1️⃣   | TSLA   | 376.53 | 385.00 | 370.00   | 380.00    | 2.09x     | +681%    | 94/100 (🔥)   | 🚀 EXPLOSIVE
2️⃣   | QCOM   | 193.33 | 205.00 | 190.00   | 200.00    | 2.78x     | +150.7%  | 88/100 (🔥)   | 🔥 HOT
3️⃣   | OKTA   | 209.33 | 225.00 | 205.00   | 210.00    | 2.94x     | +609%    | 86/100 (🔥)   | 🚀 EXPLOSIVE
4️⃣   | NVDA   | 221.82 | 230.00 | 220.00   | 222.50    | 2.48x     | +50.7%   | 82/100 (✅)   | ✅ PRIME
5️⃣   | AAPL   | 336.24 | 345.00 | 335.00   | 340.00    | 3.27x     | +31.2%   | 78/100 (✅)   | ✅ SOLID
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

📊 SUMMARY
────────────────────────────────────────────────────────────────────
Tickers Scanned:        600 (SPX 500 + NDX 100)
Passed Filters:         23 (3.8%)
Top Ranked Setup:       TSLA (Rank 1, Score 9.4/10)
Scan Completed:         2026-10-01 13:35:22
Data Freshness:         ~2 min (cached from QuantWheel)
Cache Hit Rate:         85% (510/600 tickers)
Time Elapsed:           1.23 sec
Watchlist Tracked:      ✅ (appended to watchlist_history.json)
```

### 6.2 JSON Export (--export-json)

```json
{
  "scan": {
    "timestamp": "2026-10-01T13:35:22Z",
    "universe": ["SPX 500", "NDX 100"],
    "tickers_scanned": 600,
    "candidates_passed": 23,
    "data_freshness_minutes": 2,
    "cache_hit_rate": 0.85
  },
  "candidates": [
    {
      "rank": 1,
      "ticker": "TSLA",
      "current_price": 376.53,
      "bullish_target": 385.00,
      "put_wall": 370.00,
      "call_wall": 380.00,
      "bull_bear_ratio": 2.09,
      "gamma_buildup_pct": 681.0,
      "dealer_score": 94,
      "dealer_score_category": "EXTREMELY_STRONG",
      "composite_rank": 9.4,
      "status": "EXPLOSIVE",
      "filters_passed": {
        "positive_gamma": true,
        "positive_vanna": true,
        "iv_dropping": true,
        "put_wall_proximity": true,
        "dte_range": true,
        "bullish_drift": true
      },
      "trade_recommendation": "MOMENTUM_SCALP_OR_CALL_SPREAD",
      "risk_flags": []
    },
    ...
  ]
}
```

### 6.3 CSV Export (--export-csv)

```csv
rank,ticker,price,target,put_wall,call_wall,bull_bear_ratio,gamma_buildup_pct,dealer_score,status,trade_recommendation
1,TSLA,376.53,385.00,370.00,380.00,2.09,681.0,94,EXPLOSIVE,MOMENTUM_SCALP_OR_CALL_SPREAD
2,QCOM,193.33,205.00,190.00,200.00,2.78,150.7,88,HOT,BUY_DIPS_OR_SHORT_PUTS
3,OKTA,209.33,225.00,205.00,210.00,2.94,609.0,86,EXPLOSIVE,MOMENTUM_SCALP_OR_CALL_SPREAD
...
```

### 6.4 Scan Log (Auto-saved)

**File:** `scans/2026-10-01-13-35.json` (YYYY-MM-DD-HH-MM.json)

Identical to JSON export above, auto-created after each scan. Enables historical replay and backtesting.

---

## 7. CLI Interface

### 7.1 Basic Usage

```bash
# Full scan (all SPX + NDX)
python main.py

# Scan with custom watchlist
python main.py --watchlist my_favorites.json

# Export results
python main.py --export-json --export-csv

# Filter by setup quality
python main.py --min-gamma-buildup 100  # Only > 100% gamma buildup
python main.py --min-dealer-score 80    # Only dealer score > 80

# Show top N only
python main.py --top-n 10

# Combine filters
python main.py --min-gamma-buildup 200 --max-price 300 --top-n 15 --export-csv
```

### 7.2 Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--watchlist FILE` | str | None | Use custom ticker list (JSON or txt) instead of SPX+NDX |
| `--export-json` | bool | False | Export results to JSON |
| `--export-csv` | bool | False | Export results to CSV |
| `--top-n N` | int | None | Show only top N candidates |
| `--min-gamma-buildup PCT` | float | None | Filter: gamma buildup > PCT |
| `--min-dealer-score SCORE` | int | None | Filter: dealer score > SCORE |
| `--max-price PRICE` | float | None | Filter: price ≤ PRICE |
| `--min-bull-bear RATIO` | float | None | Filter: bull/bear ratio > RATIO |
| `--no-cache` | bool | False | Skip cache, fetch all fresh |
| `--cache-ttl MINUTES` | int | 5 | Cache time-to-live in minutes |
| `--quiet` | bool | False | Suppress CLI output (JSON/CSV only) |
| `--debug` | bool | False | Print detailed logs for each ticker |

---

## 8. Trade Recommendations

Based on **Status** (derived from gamma buildup %):

| Status | Gamma Buildup | Trade Recommendation | Instrument | Rationale |
|--------|---------------|----------------------|------------|-----------|
| 🚀 EXPLOSIVE | > 500% | Momentum scalp or call spread | Calls, call spreads | Acceleration building, upside breakout |
| 🔥 HOT | 150-500% | Buy dips or short puts | Shares, short puts | Dealers buying dips, premium selling |
| ✅ PRIME | 50-150% | Buy dips, strong support | Shares | Dealer support holding, smooth trend |
| ✅ SOLID | 0-50% | Dip buyer, lower conviction | Shares | Aligned, but less momentum |
| ⚠️ CAUTION | < 0% | SKIP | N/A | Negative gamma = avoid |

---

## 9. Risk Framework

**Do NOT trade if:**

- ❌ Gamma is negative (dealers hedging, not supporting)
- ❌ IV is rising (premium selling loses money)
- ❌ Price > 3% above put wall (no support, risky)
- ❌ Bull/Bear ratio < 1.0 (bearish skew, misaligned)
- ❌ No bullish drift target visible (setup inactive)

**Flag but allow:**

- ⚠️ Dealer score 60-70 (weak alignment, lower conviction)
- ⚠️ Call wall directly overhead (track for breakout, but resistance present)

---

## 10. Caching Strategy

**In-Memory Cache (SQLite optional)**

- **Data cached:** GEX (gamma, put_wall, call_wall), vanna_charm (bullDriftTarget, bullBearRatio), quote (price, IV)
- **TTL:** 5 minutes (configurable via --cache-ttl)
- **Invalidation:** Manual (--no-cache flag) or automatic upon TTL expiry
- **Hit rate goal:** 85%+ on repeat scans within same market session

**Cache key structure:**
```
ticker:expiration:timestamp
e.g., "NVDA:2026-10-18:1727804122"
```

**Benefits:**
- Reduce QuantWheel API calls by 80%+
- Faster repeat scans
- Handle API rate limits gracefully

---

## 11. Error Handling

**Ticker-level failures (non-blocking):**

- Missing GEX data → Skip ticker, log warning
- API timeout → Use cached data if available, else skip
- Missing vanna_charm data → Skip ticker
- Price data missing → Skip ticker

**System-level failures (should not occur):**

- QuantWheel API down → Exit with error message
- Invalid watchlist file → Exit with usage error
- Corrupt cache → Flush cache, restart

**Error output:**

```
⚠️  WARNINGS
──────────────────────────────────────────────────────────────────
MSFT: GEX data missing for 2026-10-18 expiration (skipped)
TSLA: API timeout (used cached data from 5 min ago)
INVALID_TICKER: Ticker not found (skipped)

✅ Scan completed with 3 warnings. 23 valid candidates returned.
```

---

## 12. Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.9+ | Core implementation |
| Data Fetching | QuantWheel MCP (Claude Code) | Gamma/vanna/IV data |
| Caching | SQLite (optional) or in-memory dict | Cache GEX/vanna data |
| CLI Output | tabulate | Pretty-print table |
| Export | json, csv modules | JSON/CSV export |
| Testing | pytest | Unit + integration tests |
| Configuration | YAML or .env | Settings management |

---

## 13. File Structure

```
trading-market-regime-framework/
├── main.py                           # CLI entry point
├── screener.py                       # Filter + ranking logic
├── models.py                         # Data classes (Ticker, Setup, etc.)
├── quantwheel_client.py              # QuantWheel API wrapper + caching
├── output.py                         # CLI/JSON/CSV formatting
├── config.py                         # Configuration + defaults
├── requirements.txt                  # Python dependencies
├── README.md                         # Quick start guide
├── .env.example                      # Example env vars
├── watchlist.json                    # Example custom watchlist
├── scans/                            # Historical scan logs
│   ├── 2026-10-01-13-35.json
│   └── 2026-10-01-14-00.json
├── tests/                            # Unit + integration tests
│   ├── test_screener.py
│   ├── test_quantwheel_client.py
│   └── test_output.py
└── docs/
    ├── README.md
    ├── USAGE.md
    └── superpowers/
        └── specs/
            └── 2026-10-01-core-market-regime-framework-design.md (this file)
```

---

## 14. Implementation Phases

**Phase 1 (MVP):** Core screening + CLI output
- QuantWheel client (fetch GEX, vanna_charm, quote)
- Filter engine (6 conditions)
- Basic ranking (composite score)
- CLI table output

**Phase 2:** Caching + export
- SQLite caching layer
- JSON export
- CSV export
- Scan history logging

**Phase 3:** Enhancement + tooling
- Custom watchlist support
- Advanced CLI filters (--min-gamma, etc.)
- Backtesting framework (replay scans)
- Alert system (email/Slack on new setup)

---

## 15. Success Metrics

- ✅ All 6 filtering conditions applied consistently
- ✅ Composite ranking matches manual best setups
- ✅ Scan completes in < 2 minutes (600 tickers)
- ✅ Cache hit rate > 80%
- ✅ Zero false positives (all passed tickers are tradeable)
- ✅ Output matches reference format
- ✅ Historical logs enable 30-day backtest

---

## 16. Appendix: Reference Data

**SPX 500 & NDX 100 constituents** (to be auto-fetched from QuantWheel or external source)

**Example thresholds (configurable):**
- Put wall proximity: ±3%
- IV drop threshold: current < 3-day avg
- Gamma buildup lookback: 5 days
- Dealer score weights: gamma 30%, bull/bear 25%, dealer 25%, proximity 20%
- Cache TTL: 5 minutes
- DTE range: 0-21 days

---

**End of Specification**
