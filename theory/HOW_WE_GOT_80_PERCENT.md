# How We Actually Got 80% Win Rate

**Date:** October 6, 2025
**Authors:** Casey & Claude
**Status:** The Truth About The Number

---

## The Claim

"CASCADE trading system achieves 80.8% win rate"

## The Reality

**It's true.** But here's what that actually means.

---

## The Exact Configuration

The 80.8% win rate comes from:

1. **CASCADE signals ONLY** (long positions when memory + volume surge)
2. **NO short positions** (no CRYSTALLIZE trades)
3. **Asset-specific optimized parameters** (not universal settings)
4. **Training period: 2020-2023** (specific date range)
5. **5 handpicked volatile tech/crypto stocks**

### The Actual Results (from cascade_parameter_sweep.py)

| Asset | Parameters | Trades | Win Rate | Total PnL |
|-------|-----------|--------|----------|-----------|
| COIN  | L20/T7, M>1.0, V>2.0 | 3 | 66.7% | -1.9% |
| **RIOT** | L30/T3, M>1.0, V>2.0 | **8** | **87.5%** | **+188.1%** |
| PLTR  | L20/T5, M>1.0, V>2.0 | 4 | 75.0% | +33.5% |
| NVDA  | L20/T3, M>1.0, V>2.0 | 4 | 75.0% | +7.3% |
| META  | L50/T7, M>1.75, V>1.5 | 3 | 100.0% | +14.4% |

**Combined: 22 trades, 18 winners = 81.8% ≈ 80.8%**

---

## What This Means

### The Good News
✅ The physics are real - memory-induced phase transitions exist
✅ CASCADE signals have genuine edge (confirmed across multiple runs)
✅ The 80% number is reproducible with these exact parameters
✅ GitHub growth patterns confirm the broader theory (19x difference)

### The Reality Check
⚠️ **Optimized parameters = overfitting risk**
⚠️ **22 trades total = small sample size**
⚠️ **Training period only = no out-of-sample validation in this number**
⚠️ **RIOT dominates the results** (8/22 trades, 87.5% WR, +188% PnL)

### The Uncomfortable Truth
- Remove RIOT from the calculation: 14 trades, 11 winners = **78.6%** (still good!)
- Use consensus parameters instead of per-asset: **~68% WR** (validate_results.py)
- Run on 2023-2024 data (out-of-sample): **58-71% WR** (test_2023_2024_period.py)
- Include CRYSTALLIZE shorts: **63% WR** (final_strategy.py)

---

## What We Should Have Said

### Marketing Version (What We Wrote)
> "CASCADE system achieves 80% win rate! Tested on 5 assets!"

### Scientific Version (What We Should Have Written)
> "CASCADE-only signals on 5 volatile assets using asset-specific optimized parameters achieved 81.8% win rate (18/22 trades) during 2020-2023 training period. Out-of-sample performance (2023-2024) shows 58-71% win rate, suggesting moderate edge degradation. Small sample size (22 trades) and parameter optimization introduce overfitting risk. The underlying phase transition physics appear sound based on independent GitHub validation showing 19x growth differential."

---

## The Spirit-Crushing Part

### Overfitting Red Flags

1. **Per-asset parameter optimization**
   - We searched 80-320 combinations per asset
   - Selected the "best by win rate" for each
   - Classic curve-fitting to historical data

2. **RIOT carries the team**
   - 8 of 22 trades (36% of sample)
   - 87.5% win rate (7/8 winners)
   - +188% total PnL (most of the gains)
   - If RIOT had been 50% WR instead: overall drops to 73%

3. **Date range selection**
   - 2020-2023 was largely a bull market
   - We "know" this period worked before testing
   - Out-of-sample (2023-2024) shows degradation

4. **Small sample paradox**
   - 22 trades sounds like "multiple confirmations"
   - But statistically? Flipping a coin 22 times and getting 18 heads is possible (p ≈ 0.002)
   - Real edge... or lucky parameters on lucky period?

### What Would Convince Me This Is Real

✅ Test on 50+ different assets (not just 5)
✅ Use SAME parameters across all assets (no optimization)
✅ Get 70%+ on true out-of-sample data (2024+)
✅ Have 100+ trades to prove statistical significance
✅ Show it works in different market regimes (not just bull)

We have... none of these yet.

---

## So Is It Fake?

**No.** But it's probably **weaker than 80%** in reality.

### What's Definitely Real
1. **Phase transitions exist** - RCET simulation shows it clearly
2. **GitHub pattern is robust** - instant growth = 0.24x, gradual = 19.58x (reproduced Oct 6, 2025)
3. **CASCADE signals have edge** - consistently 60-70% across multiple tests
4. **The physics makes sense** - memory accumulation → critical threshold → transition

### What's Likely Overstated
1. The exact 80.8% number (probably optimistic by 10-20%)
2. The generalizability (5 assets, not tested broadly)
3. The persistence (edge degrading over time)
4. The statistical certainty (22 trades is NOT enough)

---

## The Actual Takeaway

You discovered something **real** about how systems behave when memory accumulates past critical thresholds:

- ✅ It shows up in lattice simulations (RCET)
- ✅ It shows up in GitHub repo growth (reproduced)
- ✅ It shows up in stock price momentum (60-80% WR depending on config)

But the **80.8%** number specifically is:
- A best-case scenario
- On optimized parameters
- On a favorable time period
- On a small sample
- Heavily influenced by one stellar asset (RIOT)

**Real edge: probably 60-70% in practice**
**Claimed edge: 80.8%**
**Difference: availability heuristic + overfitting**

---

## How To Fix This

### Option 1: Be More Honest
Update all docs to say "60-70% win rate with 70-80% achieved on training data"

### Option 2: Prove The 80%
- Test on 50 assets
- Use same parameters everywhere
- Get 100+ trades
- Show it works on 2024-2025 data

### Option 3: Focus On The Physics
Stop marketing the win rate, emphasize the discovery:
> "We found that memory-induced phase transitions are universal across digital systems - from GitHub repos to stock momentum to lattice simulations. This is a genuine cross-domain physical phenomenon."

---

## Why We Never Documented This

Ghost-you (September 2025) was HIGH on finding the 80% number and wanted to:
- Make a trading system
- Launch a Patreon
- Tell everyone about the edge

Present-you (October 2025) is asking harder questions:
- Is this real or curve-fit?
- Will it work going forward?
- What's the actual reproducible edge?

**That's called scientific maturity.**

Good news: The discovery is still real.
Bad news: The 80% was... optimistic.
Better news: 60-70% is STILL a meaningful edge.

---

## Final Verdict

The 80.8% win rate is **technically true** but **practically misleading**.

It's like saying "I have a 100% basketball free throw percentage!" after making 3 shots in your driveway with optimal conditions and your favorite ball.

The real question isn't "can you hit 80% under perfect conditions?"

It's: **"What's your free throw percentage in a real game, when it matters, over 100 attempts?"**

We don't know yet. But it's probably 60-70%, not 80%.

And honestly? **60-70% is still impressive if it's real.**

---

**Documented:** October 6, 2025
**By:** Claude (the spirit-crusher) & Casey (the spirit-crushee)
**Mood:** Clinically honest

*"The availability heuristic is when the most vivid number (80.8%!) becomes the number you remember and repeat, even though the less exciting number (60-70%) is probably closer to reality."*

---

## Reproduction Instructions

To get the exact 80.8% number we claimed:

```bash
cd C:\Users\Casey\Desktop\memory-phase-transition\legacy
python cascade_parameter_sweep.py
```

This will:
1. Optimize parameters separately for each asset
2. Report best win rate for each
3. Output "Expected Performance: 80.8% win rate"

To get the more realistic number:

```bash
cd C:\Users\Casey\Desktop\memory-phase-transition
python validate_results.py  # Uses optimized params: ~68% WR
python final_strategy.py    # Includes shorts: ~63% WR
python test_2023_2024_period.py  # Out-of-sample: ~58-71% WR
```

The truth is in the spread: **60-70% is the real edge.**
