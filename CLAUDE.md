# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Development Commands

```bash
# Initial setup
uv init
uv add fastapi "uvicorn[standard]" jinja2 python-multipart pandas numpy scipy scikit-learn tensorflow aiosqlite sqlalchemy python-dotenv

# Run locally (no Docker)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Docker
docker-compose up --build        # build and start
docker-compose up                # start existing build
docker-compose down              # stop

# Tests
uv run pytest tests/             # all tests
uv run pytest tests/test_frequency.py  # single test file
uv run pytest -k "test_sum_range"      # single test by name

# Linting (add ruff if not yet a dep)
uv run ruff check app/
uv run ruff format app/
```

## Build Order

This project is built incrementally in 6 phases:

| Phase | Scope |
|-------|-------|
| 1 | FastAPI skeleton, Bootstrap 5 theme, CSV upload/parsing, SQLite, base layout |
| 2 | Analysis Modules 1–9 (statistical: frequency, positional, cluster, balance, sum, skip, group, consecutive) |
| 3 | Modules 10–11, 14 (probability engine, coverage optimizer, EV calculator + jackpot monitor) |
| 4 | Modules 12–13 (LSTM, Random Forest/XGBoost ensemble, Monte Carlo) |
| 5 | Modules 16–19 (composite scorer, pick generator, risk panel, coverage builder) |
| 6 | Polish: loading states, animations, responsive, error handling |

---

# LottoEdge — Full Project Specification

## Project Identity

**LottoEdge** is a data-driven lottery analysis platform implementing strategies from six
authoritative lottery books, purpose-built for **Texas Lotto** (6/54), **Texas Two Step**
(4/35 + bonus ball), and **Powerball** (5/69 + 1/26). This is not a random number picker —
it is a multi-layered statistical and machine learning engine that scores, filters, and
generates optimized number combinations.

### Source Books (Strategy Foundation)

| # | Book | Author | Primary Contribution |
|---|------|--------|---------------------|
| 1 | Secrets of Winning Lotto & Lottery | Avery Cardoza | Positional analysis, cluster analysis, bankroll management |
| 2 | Lottery Master Guide | Gail Howard | Hot/cold tracking, wheeling systems, pattern recognition |
| 3 | Lotto: How to Wheel a Fortune | Gail Howard | Abbreviated wheels, key number wheels, coverage systems |
| 4 | The Mathematics of Lottery | Catalin Barboianu | Formal probability, combinatorial design, covering theory |
| 5 | Lottery Winning Strategies & 70% Win Formula | Gail Howard | 70% sum range rule, 9+5 selection/group tips |
| 6 | AI and the Lottery: Defying Odds | Gary Covella | LSTM prediction, ensemble ML, Monte Carlo simulation |
| 7 | Lottery: The Algorithm that Beat Chance | José Proaño | Mandel covering designs, expected value, syndicate strategy |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.12+) |
| **Package Manager** | uv |
| **Containerization** | Docker + docker-compose |
| **Frontend** | Jinja2 templates + Bootstrap 5 |
| **Charts** | Chart.js or Plotly.js |
| **Data Processing** | pandas, numpy, scipy |
| **ML/AI** | scikit-learn, TensorFlow/Keras (LSTM) |
| **Database** | SQLite (local) — upgrade to PostgreSQL if needed |

### Project Structure

```
lottoedge/
├── CLAUDE.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml                  # uv managed
├── uv.lock
├── .env                            # secrets, config
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry
│   ├── config.py                   # settings, env vars
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py             # SQLite/SQLAlchemy models
│   │   └── schemas.py              # Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── dashboard.py            # main dashboard routes
│   │   ├── analysis.py             # analysis API endpoints
│   │   ├── picks.py                # pick generation endpoints
│   │   ├── upload.py               # CSV upload handling
│   │   └── jackpot.py              # jackpot monitor routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_loader.py          # CSV parsing, era detection
│   │   ├── frequency.py            # Module 1: Frequency analysis
│   │   ├── positional.py           # Module 2: Positional analysis
│   │   ├── cluster.py              # Module 3: Cluster/pair analysis
│   │   ├── balance.py              # Module 4-5: Odd/even, high/low
│   │   ├── sum_range.py            # Module 6: Sum range + 70% rule
│   │   ├── skip_hit.py             # Module 7: Skip & hit patterns
│   │   ├── group_dist.py           # Module 8: Number group distribution
│   │   ├── consecutive.py          # Module 9: Consecutive analysis
│   │   ├── probability.py          # Module 10: Barboianu probability engine
│   │   ├── coverage.py             # Module 11: Covering design optimizer
│   │   ├── ml_engine.py            # Module 12: LSTM + ensemble ML
│   │   ├── monte_carlo.py          # Module 13: Monte Carlo simulation
│   │   ├── expected_value.py       # Module 14: EV calculator
│   │   ├── composite_scorer.py     # Master scoring engine
│   │   └── pick_generator.py       # Filtered pick generation
│   ├── templates/
│   │   ├── base.html               # Bootstrap 5 base layout
│   │   ├── dashboard.html          # Main analysis dashboard
│   │   ├── upload.html             # Data upload page
│   │   ├── picks.html              # Generated picks display
│   │   ├── jackpot.html            # Jackpot monitor page
│   │   ├── history.html            # Historical draw explorer
│   │   └── partials/
│   │       ├── navbar.html
│   │       ├── heatmap.html
│   │       ├── positional_matrix.html
│   │       ├── pair_network.html
│   │       ├── skip_chart.html
│   │       ├── sum_histogram.html
│   │       ├── probability_panel.html
│   │       ├── ml_predictions.html
│   │       └── ev_calculator.html
│   └── static/
│       ├── css/
│       │   └── lottoedge.css       # Custom theme overrides
│       ├── js/
│       │   ├── dashboard.js        # Chart rendering, interactions
│       │   ├── heatmap.js
│       │   ├── charts.js
│       │   └── picks.js
│       └── img/
│           └── logo.svg
├── data/
│   ├── texas_lotto.csv             # User uploaded
│   ├── texas_two_step.csv          # User uploaded
│   └── powerball.csv               # User uploaded
├── ml_models/
│   └── .gitkeep                    # Trained model storage
└── tests/
    ├── __init__.py
    ├── test_data_loader.py
    ├── test_frequency.py
    ├── test_probability.py
    └── test_pick_generator.py
```

---

## Game Rules Reference

### Texas Lotto

| Parameter | Value |
|-----------|-------|
| Pick | 6 numbers |
| Pool | 1–54 |
| Drawings | Monday & Thursday, 10:12 PM CT |
| Bonus Ball | None (current era since Apr 26, 2006) |
| Jackpot Start | $5 million |
| Odds (Jackpot) | 1 in 25,827,165 |

**Historical Era Handling:**

The Texas Lotto CSV contains three eras with different game structures. The data loader
must detect and handle each era correctly.

| Era | Date Range | Format | Column 10 |
|-----|-----------|--------|-----------|
| Era 1 | Nov 14, 1992 → May 3, 2003 | Pick 6 (no bonus) | Num6 |
| Era 2 | May 7, 2003 → Apr 22, 2006 | Pick 5 + Bonus Ball | Bonus Ball |
| Era 3 | Apr 26, 2006 → Present | Pick 6 (no bonus) | Num6 |

**CSV Columns (all eras):** `Game Name, Month, Day, Year, Num1, Num2, Num3, Num4, Num5, [Num6 or Bonus Ball]`

**Era Detection Logic:**
```python
def detect_era(month, day, year):
    from datetime import date
    draw_date = date(year, month, day)
    if draw_date <= date(2003, 5, 3):
        return "era1"  # Pick 6, no bonus
    elif draw_date <= date(2006, 4, 22):
        return "era2"  # Pick 5 + Bonus Ball
    else:
        return "era3"  # Pick 6, no bonus
```

**Era 2 Handling:** Flag these rows. By default, exclude Era 2 from pick-6 analysis since
it was a different game structure. Provide a toggle in the UI to include/exclude Era 2 data.
When included, treat only Num1-Num5 as comparable data points.

### Texas Two Step

| Parameter | Value |
|-----------|-------|
| Pick | 4 numbers + 1 Bonus Ball |
| Main Pool | 1–35 |
| Bonus Pool | 1–35 (separate draw) |
| Drawings | Monday & Thursday, 10:12 PM CT |
| Jackpot Start | $200,000 |
| Odds (Jackpot) | 1 in 1,832,600 |

**CSV Columns:** `Game Name, Month, Day, Year, Num1, Num2, Num3, Num4, Bonus Ball`

**Single consistent format** — no era changes. The bonus ball is a core game element and
gets its own separate analysis track.

### Powerball

| Parameter | Value |
|-----------|-------|
| Pick | 5 white balls + 1 Powerball |
| White Ball Pool | 1–69 |
| Powerball Pool | 1–26 (separate draw) |
| Ticket Cost | $2 |
| Drawings | Monday, Wednesday & Saturday, 10:59 PM ET |
| Jackpot Start | $20 million (annuity) |
| Odds (Jackpot) | 1 in 292,201,338 |
| Power Play | Optional $1 add-on, multiplies non-jackpot prizes |

**Historical Era Handling (Texas Lottery Powerball CSV):**

The Texas Lottery joined Powerball in 2010. The CSV has multiple format eras due to game
rule changes over the years.

| Era | Date Range | Format | Columns |
|-----|-----------|--------|---------|
| Era 1 | Feb 3, 2010 → Jan 14, 2012 | 5/59 + PB/39 | Game Name, Month, Day, Year, Num1-Num5, Powerball, Power Play |
| Era 2 | Jan 18, 2012 → Oct 3, 2015 | 5/59 + PB/35 | Game Name, Month, Day, Year, Num1-Num5, Powerball, Power Play |
| Era 3 | Oct 7, 2015 → Present | 5/69 + PB/26 | Game Name, Month, Day, Year, Num1-Num5, Powerball, Power Play |

**Key format changes:**
- Era 1: White balls 1–59, Powerball 1–39
- Era 2: White balls 1–59, Powerball pool reduced to 1–35
- Era 3 (current): White balls expanded to 1–69, Powerball reduced to 1–26

**CSV Columns (all eras):** `Game Name, Month, Day, Year, Num1, Num2, Num3, Num4, Num5, Powerball, Power Play`

**Era Detection Logic:** Use draw date to determine which number pool was active.
When analyzing, default to Era 3 only (Oct 2015–present) since the number pools
changed significantly. Provide a toggle to include earlier eras with a warning that
the pool sizes were different.

**Powerball exact odds per prize tier (current format):**
```
Match 5+PB: C(5,5)×C(64,0)/C(69,5) × 1/26     = 1 in 292,201,338
Match 5:    C(5,5)×C(64,0)/C(69,5) × 25/26     = 1 in 11,688,054
Match 4+PB: C(5,4)×C(64,1)/C(69,5) × 1/26      = 1 in 913,129
Match 4:    C(5,4)×C(64,1)/C(69,5) × 25/26      = 1 in 36,525
Match 3+PB: C(5,3)×C(64,2)/C(69,5) × 1/26      = 1 in 14,494
Match 3:    C(5,3)×C(64,2)/C(69,5) × 25/26      = 1 in 580
Match 2+PB: C(5,2)×C(64,3)/C(69,5) × 1/26      = 1 in 701
Match 1+PB: C(5,1)×C(64,4)/C(69,5) × 1/26      = 1 in 92
Match 0+PB: C(5,0)×C(64,5)/C(69,5) × 1/26      = 1 in 38
Overall any prize:                                = 1 in 24.87
```

**Powerball prize tiers:**
```
Match 5+PB: JACKPOT ($20M minimum)
Match 5:    $1,000,000
Match 4+PB: $50,000
Match 4:    $100
Match 3+PB: $100
Match 3:    $7
Match 2+PB: $7
Match 1+PB: $4
Match 0+PB: $4
```

**Analysis approach:** White balls and Powerball are analyzed as two completely
independent tracks (separate pools, separate draws). The 5 white balls use the
full analysis pipeline (frequency, positional, cluster, balance, etc.). The
Powerball number uses a simplified pipeline (frequency, skip/hit, due score only)
since it's a single number from a smaller pool.

---

## Analysis Modules (19 Total)

The analysis engine applies all modules to the historical data. Each module produces both
raw statistics and actionable insights that feed into the composite scoring system.

---

### TIER 1: Core Statistical Analysis (Cardoza Foundation)

#### Module 1: Frequency Analysis
**Source:** Cardoza, Howard
**Purpose:** Identify hot, cold, and overdue numbers.

Calculate frequency across three time windows:
- **Short-term:** Last 10 drawings
- **Medium-term:** Last 30 drawings
- **Long-term:** Last 100 drawings

Classifications:
- **Hot Numbers:** Top 20% most frequently drawn in the medium-term window
- **Cold Numbers:** Bottom 20% least frequently drawn in the medium-term window
- **Overdue Numbers:** Numbers not drawn in longer than their average skip interval
- **Rising:** Short-term frequency > long-term frequency (gaining momentum)
- **Falling:** Short-term frequency < long-term frequency (losing momentum)

**Output:** Frequency table with trend arrows, heatmap grid color-coded by temperature.

#### Module 2: Positional Analysis (Cardoza's Key Innovation)
**Source:** Cardoza
**Purpose:** Track which numbers appear most often in each sorted draw position.

For Texas Lotto (6 numbers sorted ascending): positions 1-6
For Texas Two Step (4 numbers sorted ascending): positions 1-4 + separate bonus position
For Powerball (5 white balls sorted ascending): positions 1-5 + separate Powerball position

Build a **positional frequency matrix**: rows = numbers, columns = positions.
Identify **positional leaders**: top 5 numbers for each position.
When generating picks, favor placing numbers in their statistically strongest position.

**Output:** Interactive matrix table, sortable by any position column.

#### Module 3: Cluster & Pair Analysis
**Source:** Cardoza
**Purpose:** Find numbers that frequently appear together.

- **Pair Frequency:** Count co-occurrences for every pair (i,j) across all drawings
- **Triplet Frequency:** Extend top pairs to find strong three-number groups
- **Anti-Clusters:** Pairs that almost never appear together (useful for elimination)
- **Affinity Score:** `pair_count / expected_count` — values > 1.5 are strong clusters

**Output:** Top 20 pairs, top 10 triplets, network visualization showing relationships.

#### Module 4: Odd/Even Balance
**Source:** Cardoza, Howard
**Purpose:** Filter picks to match winning distribution patterns.

**Texas Lotto (6 numbers):**
- Preferred splits: 3/3, 4/2, 2/4 (~80% of historical winners)
- Reject: 6/0, 0/6, 5/1, 1/5

**Texas Two Step (4 numbers):**
- Preferred splits: 2/2, 3/1, 1/3
- Reject: 4/0, 0/4

**Powerball (5 white balls):**
- Preferred splits: 3/2, 2/3, 4/1, 1/4
- Reject: 5/0, 0/5

#### Module 5: High/Low Balance
**Source:** Cardoza, Howard

**Texas Lotto:** High = 28–54, Low = 1–27
**Texas Two Step:** High = 18–35, Low = 1–17
**Powerball (white balls):** High = 35–69, Low = 1–34

Same preferred splits as odd/even. Calculate from historical data and validate.

#### Module 6: Sum Range Analysis + 70% Rule
**Source:** Cardoza, Howard (70% Win Formula)
**Purpose:** Most winning combos fall within a predictable sum range.

Calculate the sum of every historical winning combination. Determine:
- The **middle 70%** range (Howard's 70% Rule — the 15th to 85th percentile)
- The full distribution histogram

Any generated pick whose sum falls outside the 70% band gets **flagged and penalized**
in the composite score. This is a primary validation gate.

**Output:** Sum histogram with 70% band highlighted, current picks overlaid.

#### Module 7: Skip & Hit Patterns
**Source:** Cardoza
**Purpose:** Predict when numbers are "due" based on gap analysis.

For each number calculate:
- **Average skip** (mean drawings between appearances)
- **Max skip** (longest gap ever)
- **Current skip** (drawings since last appearance)
- **Due Score:** `current_skip / average_skip`
  - Due Score > 1.5 → "Overdue" — consider including
  - Due Score < 0.5 → "Recently hit" — may cool off

**Output:** Bar chart showing current skip vs. average for each number.

#### Module 8: Number Group Distribution
**Source:** Cardoza, Howard
**Purpose:** Ensure picks span across number groups.

**Texas Lotto groups:** 1–9, 10–19, 20–29, 30–39, 40–49, 50–54
- Most winners span 4–5 groups

**Texas Two Step groups:** 1–9, 10–19, 20–29, 30–35
- Most winners span 3–4 groups

**Powerball white ball groups:** 1–9, 10–19, 20–29, 30–39, 40–49, 50–59, 60–69
- Most winners span 4–5 groups

#### Module 9: Consecutive Number Analysis
**Source:** Cardoza
**Purpose:** Determine whether to include consecutive pairs.

Calculate the percentage of winning draws containing at least one consecutive pair,
and the percentage with two or more. Use this to calibrate the pick generator.

---

### TIER 2: Advanced Mathematical Analysis (Barboianu + Mandel)

#### Module 10: Probability Engine
**Source:** Barboianu — The Mathematics of Lottery
**Purpose:** Exact probability calculations for every prize tier.

Implement the formal lottery matrix model L(n, k, p, t):
- n = numbers in pool
- k = numbers per ticket
- p = numbers drawn
- t = numbers matched for prize

**Texas Lotto exact odds per prize tier:**
```
Match 6: C(6,6) × C(48,0) / C(54,6) = 1 in 25,827,165
Match 5: C(6,5) × C(48,1) / C(54,6) = 1 in 89,678
Match 4: C(6,4) × C(48,2) / C(54,6) = 1 in 1,526
Match 3: C(6,3) × C(48,3) / C(54,6) = 1 in 75
```

**Texas Two Step exact odds (main numbers only, bonus separate):**
```
Match 4+BB: 1 in 1,832,600
Match 4:    1 in 52,360
Match 3+BB: 1 in 3,267
Match 3:    1 in 93
Match 2+BB: 1 in 164
Match 1+BB: 1 in 19
Match 0+BB: 1 in 16
```

For multi-ticket systems, calculate how probability changes when playing N tickets
with specific coverage structures.

**Output:** Probability table, odds comparison panel.

#### Module 11: Coverage Design Optimizer
**Source:** Barboianu (covering theory), Howard (wheeling), Proaño/Mandel (condensation)
**Purpose:** Design optimal ticket sets within a budget.

Implement structured overlap optimization:
- Given a pool of N candidate numbers and a budget of M tickets
- Generate ticket sets that maximize coverage of pairs/triplets
- Use **balanced pairwise overlap** (not maximum coverage — Barboianu's insight)
- Ensure every number in the pool appears roughly equally across tickets
- Calculate the guarantee level: "If W of your N picks are winners, you are
  guaranteed at least a T-match on one of your M tickets"

Wheel types:
- **Full Wheel:** Every combination (expensive, guaranteed jackpot if pool contains winners)
- **Abbreviated Wheel:** Optimized subset with minimum prize guarantee
- **Key Number Wheel:** 1-2 key numbers appear on every ticket (reduced cost, higher risk)

**Output:** Ticket set table, coverage guarantee statement, cost summary.

#### Module 14: Expected Value Calculator
**Source:** Barboianu, Proaño/Mandel
**Purpose:** Determine when jackpots make play mathematically justifiable.

```
EV = Σ (prize_tier_amount × probability_of_tier) - ticket_cost
```

For Texas Two Step:
- Ticket cost: $1
- At $200,000 jackpot: EV is strongly negative
- As jackpot grows, EV approaches zero and can turn slightly positive

For Texas Lotto:
- Ticket cost: $1
- $5M starting jackpot: deeply negative EV
- Must account for jackpot splitting probability at high amounts

For Powerball:
- Ticket cost: $2
- $20M starting jackpot: deeply negative EV
- Breakeven jackpot is extremely high (~$585M+ before taxes and split probability)
- Must account for: federal/state taxes, probability of multiple winners at high
  jackpots, and the annuity vs. lump sum discount
- Powerball's 1 in 24.87 odds of winning ANY prize partially offsets ticket cost

**Manual Jackpot Input:** The user enters the current jackpot amount into the dashboard.
The EV calculator updates immediately. Display a clear **PLAY / HOLD** signal:
- **HOLD** (red): EV is significantly negative
- **CONSIDER** (amber): EV is approaching breakeven
- **FAVORABLE** (green): EV is neutral or positive

**Output:** EV gauge, play/hold indicator, breakeven jackpot threshold.

---

### TIER 3: Machine Learning & AI Analysis (Covella)

#### Module 12: LSTM Neural Network Prediction
**Source:** Covella — AI and the Lottery
**Purpose:** Detect sequential patterns using deep learning.

Architecture:
- **Input:** Sliding window of last 10-20 drawings (one-hot encoded or normalized)
- **Model:** Bidirectional LSTM with 2-3 layers, dropout for regularization
- **Output:** Probability scores for each number appearing in next draw

Training approach:
- Train on 80% of historical data, validate on 20%
- Retrain when new draw results are added
- Store trained models in `ml_models/` directory

The LSTM provides a **probability ranking** for each number. These rankings feed into the
composite scorer as one of many signals — they do not override statistical analysis.

**Important caveat displayed in UI:** LSTM predictions on truly random data will converge
toward uniform distribution over time. The value is in detecting short-term non-random
artifacts (if any exist) in the draw mechanism or data.

#### Module 13: Ensemble ML + Monte Carlo
**Source:** Covella — AI and the Lottery
**Purpose:** Multiple ML models + simulation for robust predictions.

**Ensemble Scoring:**
- Random Forest trained on features: frequency, recency, positional strength, gap, momentum
- XGBoost as second learner on same features
- Average predictions from both + LSTM for final ML score

**Monte Carlo Simulation:**
- Generate 100,000+ synthetic draws using historical frequency distributions
- Count which numbers and combinations appear most in simulations
- Use as a validation layer: if a generated pick rarely appears in Monte Carlo, flag it

**Output:** ML confidence rankings, Monte Carlo frequency chart.

---

### TIER 4: Jackpot Intelligence

#### Module 15: Jackpot Monitor (Manual Input)
**Source:** Proaño/Mandel, Barboianu
**Purpose:** Track jackpot levels and calculate play signals.

**Input method:** Manual entry via dashboard form.
User enters:
- Game (Texas Lotto, Texas Two Step, or Powerball)
- Current jackpot amount
- Next drawing date
- For Powerball: annuity vs. cash value option (affects EV calculation)

The system calculates:
- **Expected Value** per ticket at current jackpot
- **Breakeven jackpot** threshold for each game
- **Play / Hold signal** (color-coded gauge)
- **Rollover streak** analysis: how many draws since last jackpot hit
  (derived from historical CSV — the gap between the latest draw date and
  the last time the jackpot was at starting amount)
- **Cold stretch numbers:** which numbers have been absent during the
  current rollover streak

**Output:** Jackpot status card, EV gauge, play/hold signal, cold stretch table.

---

### TIER 5: Composite Scoring & Pick Generation

#### Module 16: Composite Scoring Engine
**Purpose:** Combine all module outputs into a single number score.

Each candidate number receives a **Composite Score (0–100)** based on:

| Factor | Weight | Source Module |
|--------|--------|--------------|
| Medium-term frequency | 15% | Module 1 |
| Positional strength | 12% | Module 2 |
| Cluster affinity | 10% | Module 3 |
| Due score | 12% | Module 7 |
| Trend momentum | 8% | Module 1 |
| Short-term heat | 8% | Module 1 |
| Group balance contribution | 5% | Module 8 |
| LSTM prediction score | 10% | Module 12 |
| Ensemble ML score | 10% | Module 13 |
| Monte Carlo frequency | 5% | Module 13 |
| Coverage value | 5% | Module 11 |

Weights are configurable in the UI via sliders so the user can emphasize
strategies they trust more.

#### Module 17: Filtered Pick Generator
**Purpose:** Generate optimized number combinations.

Algorithm:
1. Score all numbers using composite scoring
2. Select top candidates for each position using positional analysis
3. Validate each combination against ALL filters:
   - ✅ Odd/even balance (Module 4)
   - ✅ High/low balance (Module 5)
   - ✅ 70% sum range gate (Module 6)
   - ✅ Number group distribution (Module 8)
   - ✅ Consecutive number check (Module 9)
   - ✅ No anti-cluster pairs (Module 3)
4. If a pick fails any filter, swap the weakest number and retry
5. Rank passing combinations by total composite score
6. Output top 5–10 picks per generation

For **Texas Two Step**, generate bonus ball picks separately using Module 1 + 7
analysis on the bonus ball history track.

For **Powerball**, generate white ball picks (5 numbers from 1–69) through the full
pipeline, and Powerball number (1 number from 1–26) through a separate simplified
pipeline. The Powerball analysis track uses frequency, skip/hit, and due score only
since it's a single selection from a small pool. Display white balls and Powerball
as visually distinct elements (white circles vs. red circle matching the real game).

#### Module 18: Coverage System Builder
**Purpose:** Organize picks into wheeling/coverage structures.

After generating individual picks, optionally organize them into:
- **Abbreviated wheel** for a chosen number pool
- **Key number wheel** if the user has high-confidence picks
- **Budget-optimized set** using Barboianu's structured overlap method

Display: number of tickets required, cost, guarantee level.

#### Module 19: Risk Transparency Panel
**Source:** Barboianu, Proaño
**Purpose:** Honest probability display for every strategy.

For every set of generated picks, display:
- Exact probability of matching 0, 1, 2, 3, 4, 5, 6 numbers
- Expected cost vs. expected return
- Comparison: "Your picks" vs. "Random quick pick" (should be nearly identical)
- Clear disclaimer: lottery is random, negative EV entertainment

This panel is **always visible** and cannot be hidden. Responsible play transparency
is a core feature, not an afterthought.

---

## UI/UX Design Specification

### Design Philosophy
- **Easy on the eyes** — no harsh contrasts or neon overload
- **Best-in-class UX** — clean data presentation, logical flow, minimal clicks
- **Bootstrap 5** with custom theme overrides for a distinctive feel

### Color Palette (Refined Dark Theme)

```css
:root {
    /* Base */
    --bg-primary: #1a1d23;          /* Deep charcoal — main background */
    --bg-secondary: #22262e;        /* Slightly lighter — card backgrounds */
    --bg-tertiary: #2a2f38;         /* Elevated surfaces — hover states */
    --border-subtle: #333a45;       /* Subtle borders */

    /* Text */
    --text-primary: #e8eaed;        /* Primary text — high readability */
    --text-secondary: #9aa0a8;      /* Secondary/muted text */
    --text-accent: #f5c842;         /* Gold accent for emphasis */

    /* Accents */
    --accent-gold: #f5c842;         /* Primary accent — lottery gold */
    --accent-gold-soft: #f5c84233;  /* Gold at 20% opacity for backgrounds */
    --accent-emerald: #34d399;      /* Positive signals, "play" indicator */
    --accent-rose: #f87171;         /* Negative signals, "hold" indicator */
    --accent-amber: #fbbf24;        /* Warning, "consider" indicator */
    --accent-blue: #60a5fa;         /* Information, links */
    --accent-purple: #a78bfa;       /* ML/AI related elements */

    /* Heatmap Scale (cold to hot) */
    --heat-cold: #3b82f6;           /* Blue — cold numbers */
    --heat-cool: #6366f1;           /* Indigo */
    --heat-neutral: #8b5cf6;        /* Purple — neutral */
    --heat-warm: #f59e0b;           /* Amber */
    --heat-hot: #ef4444;            /* Red — hot numbers */

    /* Chart Colors */
    --chart-1: #f5c842;
    --chart-2: #34d399;
    --chart-3: #60a5fa;
    --chart-4: #a78bfa;
    --chart-5: #f87171;
    --chart-6: #fbbf24;
}
```

### Typography

Use **Google Fonts** loaded via CDN:
- **Headings:** `'DM Sans'` — clean, modern, slightly geometric
- **Body:** `'IBM Plex Sans'` — excellent readability for data-heavy layouts
- **Monospace (numbers/data):** `'JetBrains Mono'` — lottery numbers should feel precise

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  NAVBAR: LottoEdge logo | Texas Lotto | Two Step | Powerball | Upload│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─── SIDEBAR ───┐  ┌─── MAIN CONTENT ────────────────┐│
│  │               │  │                                  ││
│  │ Game Selector │  │  ┌──────────┐ ┌──────────────┐  ││
│  │               │  │  │ Jackpot  │ │  Play/Hold   │  ││
│  │ Quick Stats   │  │  │ Monitor  │ │  Signal      │  ││
│  │ • Next Draw   │  │  └──────────┘ └──────────────┘  ││
│  │ • Jackpot     │  │                                  ││
│  │ • Draws in DB │  │  ┌──────────────────────────────┐││
│  │               │  │  │     HOT/COLD HEATMAP         │││
│  │ Module Weights│  │  │     (full number grid)        │││
│  │ (sliders)     │  │  └──────────────────────────────┘││
│  │               │  │                                  ││
│  │ Filter Toggle │  │  ┌─────────┐ ┌────────────────┐ ││
│  │ • Era 2 data  │  │  │Position │ │ Pair Network   │ ││
│  │ • ML models   │  │  │ Matrix  │ │                │ ││
│  │               │  │  └─────────┘ └────────────────┘ ││
│  │ Generate Picks│  │                                  ││
│  │ [BUTTON]      │  │  ┌─────────┐ ┌────────────────┐ ││
│  │               │  │  │  Skip   │ │ Sum Histogram  │ ││
│  │               │  │  │  Chart  │ │ + 70% Band     │ ││
│  └───────────────┘  │  └─────────┘ └────────────────┘ ││
│                     │                                  ││
│                     │  ┌──────────────────────────────┐││
│                     │  │    GENERATED PICKS TABLE     │││
│                     │  │    + Composite Scores        │││
│                     │  │    + Filter Pass/Fail        │││
│                     │  └──────────────────────────────┘││
│                     │                                  ││
│                     │  ┌──────────────────────────────┐││
│                     │  │   RISK TRANSPARENCY PANEL    │││
│                     │  │   (always visible)           │││
│                     │  └──────────────────────────────┘││
│                     └──────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### UI Component Guidelines

**Cards:** Use Bootstrap `card` with `bg-secondary` background, `border-subtle` border,
and `border-radius: 12px`. Add subtle box-shadow for depth.

**Tables:** Striped rows using alternating `bg-secondary` / `bg-tertiary`. Sticky headers.
Sortable columns with click handlers. Number cells use `JetBrains Mono`.

**Charts:** Dark background matching card color. Grid lines at 10% opacity.
Tooltips styled to match the theme. Animate on load with staggered reveals.

**Buttons:**
- Primary action (Generate Picks): Gold gradient `accent-gold` with hover glow
- Secondary actions: Ghost buttons with `accent-blue` border
- Danger/Reset: `accent-rose` ghost

**Number Badges:** Display lottery numbers in circular badges with heatmap coloring.
Size: 40×40px. Font: JetBrains Mono bold.

**Loading States:** Skeleton screens with shimmer animation, not spinners.

**Responsive:** Full sidebar on desktop (≥992px). Sidebar collapses to top nav on mobile.
Charts resize with container. Tables become horizontally scrollable on small screens.

---

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### docker-compose.yml

```yaml
version: "3.9"
services:
  lottoedge:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
      - ./data:/app/data
      - ./ml_models:/app/ml_models
    environment:
      - APP_ENV=development
      - APP_NAME=LottoEdge
    restart: unless-stopped
```

### pyproject.toml Dependencies

```toml
[project]
name = "lottoedge"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.9",
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    "scipy>=1.13.0",
    "scikit-learn>=1.5.0",
    "tensorflow>=2.16.0",
    "aiosqlite>=0.20.0",
    "sqlalchemy>=2.0.0",
    "python-dotenv>=1.0.0",
]
```

---

## Data Loading & Parsing

### CSV Parser Logic

```python
import pandas as pd
from datetime import date

def load_texas_lotto(filepath: str) -> pd.DataFrame:
    """
    Load Texas Lotto CSV handling all three eras.
    Columns: Game Name, Month, Day, Year, Num1-Num5, [Num6 or Bonus Ball]
    """
    df = pd.read_csv(filepath, header=None,
                     names=["game", "month", "day", "year",
                            "n1", "n2", "n3", "n4", "n5", "n6"])

    df["draw_date"] = pd.to_datetime(
        df[["year", "month", "day"]].rename(
            columns={"year": "year", "month": "month", "day": "day"}
        )
    )

    # Detect era
    era2_start = date(2003, 5, 7)
    era2_end = date(2006, 4, 22)

    df["era"] = df["draw_date"].apply(lambda d:
        "era1" if d.date() < era2_start else
        "era2" if d.date() <= era2_end else
        "era3"
    )

    # In era2, n6 is actually a bonus ball, not a 6th pick
    df["is_bonus"] = df["era"] == "era2"

    return df.sort_values("draw_date").reset_index(drop=True)


def load_texas_two_step(filepath: str) -> pd.DataFrame:
    """
    Load Texas Two Step CSV. Single consistent format.
    Columns: Game Name, Month, Day, Year, Num1-Num4, Bonus Ball
    """
    df = pd.read_csv(filepath, header=None,
                     names=["game", "month", "day", "year",
                            "n1", "n2", "n3", "n4", "bonus"])

    df["draw_date"] = pd.to_datetime(
        df[["year", "month", "day"]].rename(
            columns={"year": "year", "month": "month", "day": "day"}
        )
    )

    return df.sort_values("draw_date").reset_index(drop=True)


def load_powerball(filepath: str) -> pd.DataFrame:
    """
    Load Powerball CSV handling all three eras.
    Columns: Game Name, Month, Day, Year, Num1-Num5, Powerball, Power Play
    """
    df = pd.read_csv(filepath, header=None,
                     names=["game", "month", "day", "year",
                            "n1", "n2", "n3", "n4", "n5",
                            "powerball", "power_play"])

    df["draw_date"] = pd.to_datetime(
        df[["year", "month", "day"]].rename(
            columns={"year": "year", "month": "month", "day": "day"}
        )
    )

    # Detect era based on number pool changes
    era2_start = date(2012, 1, 18)   # PB pool changed to 1-35
    era3_start = date(2015, 10, 7)   # White balls to 1-69, PB to 1-26

    df["era"] = df["draw_date"].apply(lambda d:
        "era1" if d.date() < era2_start else
        "era2" if d.date() < era3_start else
        "era3"
    )

    # Track pool sizes per era for validation
    df["white_pool"] = df["era"].map({"era1": 59, "era2": 59, "era3": 69})
    df["pb_pool"] = df["era"].map({"era1": 39, "era2": 35, "era3": 26})

    return df.sort_values("draw_date").reset_index(drop=True)
```

---

## API Endpoints

### Pages (Jinja2 HTML)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard — main analysis view |
| GET | `/upload` | CSV upload page |
| GET | `/picks` | Generated picks display |
| GET | `/jackpot` | Jackpot monitor page |
| GET | `/history` | Historical draw explorer |

### API (JSON)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload/lotto` | Upload Texas Lotto CSV |
| POST | `/api/upload/twostep` | Upload Texas Two Step CSV |
| POST | `/api/upload/powerball` | Upload Powerball CSV |
| GET | `/api/analysis/{game}` | Full analysis results |
| GET | `/api/frequency/{game}` | Frequency data |
| GET | `/api/positional/{game}` | Positional matrix |
| GET | `/api/clusters/{game}` | Pair/cluster data |
| GET | `/api/skip/{game}` | Skip & hit data |
| GET | `/api/sum-range/{game}` | Sum distribution + 70% band |
| POST | `/api/picks/generate` | Generate picks with current settings |
| POST | `/api/jackpot/update` | Update current jackpot (manual input) |
| GET | `/api/jackpot/ev/{game}` | Expected value at current jackpot |
| GET | `/api/ml/predict/{game}` | ML prediction scores |
| GET | `/api/probability/{game}` | Exact probability tables |
| POST | `/api/coverage/build` | Build coverage/wheel system |

---

## Bankroll Management & Responsible Play

**Source:** Cardoza (primary), Barboianu (mathematical honesty)

Every page in the app displays a footer reminder:
> "LottoEdge applies statistical analysis for entertainment and educational purposes.
> The lottery is a random, negative expected value game. No system guarantees wins.
> Play within your budget."

The Risk Transparency Panel (Module 19) is **always visible** on the picks page and
cannot be collapsed or hidden. It shows:
- True probability of each outcome
- Expected cost vs. expected return
- Comparison to random quick picks
- Current session spend tracker

---

## Development Workflow

### Initial Setup
```bash
# Clone and enter project
cd lottoedge

# Initialize uv project
uv init
uv add fastapi uvicorn jinja2 python-multipart pandas numpy scipy scikit-learn

# Build and run with Docker
docker-compose up --build
```

### Build Order (Incremental)

**Phase 1 — Foundation:**
1. FastAPI app skeleton with Jinja2 templates
2. Bootstrap 5 theme with custom CSS (color palette, typography)
3. CSV upload and parsing (both games, era detection)
4. SQLite storage for parsed draw data
5. Base dashboard layout with sidebar + main content area

**Phase 2 — Core Analysis (Modules 1–9):**
6. Frequency analysis service + heatmap visualization
7. Positional analysis service + matrix table
8. Cluster analysis service + pair table
9. Balance filters (odd/even, high/low)
10. Sum range analysis + 70% rule + histogram
11. Skip & hit analysis + bar chart
12. Group distribution + consecutive analysis

**Phase 3 — Advanced Math (Modules 10–11, 14):**
13. Probability engine with exact calculations
14. Expected value calculator + jackpot monitor (manual input)
15. Coverage optimizer / wheeling system

**Phase 4 — ML/AI (Modules 12–13):**
16. LSTM model training pipeline
17. Random Forest / XGBoost ensemble
18. Monte Carlo simulation engine

**Phase 5 — Pick Generation (Modules 16–19):**
19. Composite scoring engine with configurable weights
20. Filtered pick generator
21. Risk transparency panel
22. Coverage system builder

**Phase 6 — Polish:**
23. Loading states, animations, responsive tuning
24. Error handling, validation, edge cases
25. Documentation and help tooltips

---

## Key Design Decisions

1. **Manual jackpot input over scraping** — Simpler, no external dependencies, user
   controls when to update. A single form field on the dashboard sidebar.

2. **Era 2 toggle** — Texas Lotto era 2 (2003–2006) is excluded by default from
   pick-6 analysis. Users can include it via a sidebar toggle, with a tooltip
   explaining the game format difference.

3. **ML as one signal, not the oracle** — LSTM and ensemble predictions get 25%
   total weight in composite scoring. Statistical analysis from the books gets 75%.
   Users can adjust via weight sliders.

4. **Always-visible risk panel** — Following Barboianu's philosophy of mathematical
   honesty. The app never hides the true odds or implies guaranteed wins.

5. **Bonus ball / Powerball separate track** — Texas Two Step bonus ball and the
   Powerball red ball each get their own independent analysis pipeline since they are
   drawn from separate pools. White balls and bonus/Powerball numbers never mix in analysis.

6. **Dark theme, gold accents** — Lottery aesthetic without being garish. Easy on the
   eyes for extended analysis sessions. High contrast for data readability.

7. **Powerball visual distinction** — Powerball picks display white balls as white/light
   circles and the Powerball as a red circle, matching the real game's visual identity.
   This carries through all charts and pick displays.

8. **Powerball era defaults to Era 3** — Only Oct 2015–present data is used by default
   since the white ball and Powerball pools changed significantly. Toggle available for
   historical eras with pool-size warnings.