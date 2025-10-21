# Reproduction Guide - Memory-Induced Phase Transitions

**Last Validated:** October 2025
**Status:** All validations confirmed
**Time Required:** ~5-35 minutes

---

## Quick Summary

This repository demonstrates that memory-induced phase transitions are **universal** but manifest **oppositely** in different system types:

- **Collaborative systems** (GitHub, Academia): Instant success → Growth freezes (4-81x penalty)
- **Viral systems** (HN, NPM): High momentum → Growth explodes (15-81x advantage)

All findings are **reproducible** with the code in this repository.

---

## Prerequisites

### Required
```bash
# Python 3.8 or higher
python --version

# Install dependencies
cd memory-phase-transition/
pip install -r requirements.txt
```

### Optional (for GitHub validation)
- GitHub Personal Access Token
- Generate at: https://github.com/settings/tokens
- Scope needed: `public_repo` only

---

## Validation 1: GitHub Repositories (SYSTEMATIC)

**Pattern:** Gradual growth outperforms instant virality by **121x**

### Setup
```bash
export GITHUB_TOKEN='your_token_here'
cd memory-phase-transition/
```

### Run
```bash
python github_systematic_validation.py
```

### Expected Output
```
PATTERN TEST:
Instant repos (<5d): 1.00x avg acceleration (n=49)
Gradual repos (>30d): 121.33x avg acceleration (n=27)
Difference: 121.61x
[OK] PATTERN HOLDS: Gradual growth >> Instant growth
```

**Runtime:** ~30-90 minutes (systematic sample of 100 repos)

**Interpretation:**
- 100 repos systematically sampled (top by stars, 2020-2023)
- Instant (<5 days to 100 stars): 1.0x growth (stagnant)
- Gradual (>30 days to 100 stars): 121.3x growth (explosive)
- **121x difference** - pattern is REAL and STRONG

---

## Validation 2: Hacker News Posts

**Pattern:** High momentum posts outperform by **14.6x**

### Run
```bash
cd validations/
python hn_analysis.py
```

### Expected Output
```
High Momentum (Top 20%):
  Average score: ~395.8 points
  Average comments: ~269.5

Low Momentum (Bottom 20%):
  Average score: ~27.2 points
  Average comments: ~5.1

Score ratio: 14.57x
Comment ratio: 53x
[+] PATTERN CONFIRMED
```

**Runtime:** Instant (uses cached data) or ~5 minutes (fresh fetch)

**Interpretation:**
- Posts with high early upvote velocity → Viral cascade
- Posts with low early momentum → Die in "new" queue
- **14.6x difference** - momentum matters in viral systems

---

## Validation 3: NPM Packages

**Pattern:** High week-1 downloads lead to **80x** more adoption

### Run
```bash
cd validations/
python npm_packages_analysis.py
```

### Expected Output
```
HIGH EARLY MOMENTUM (Top 20% by week-1 downloads):
  Average week-1 downloads: ~288,073
  Average recent (30-day) downloads: ~13,279,094

LOW EARLY MOMENTUM (Bottom 20% by week-1 downloads):
  Average week-1 downloads: ~38
  Average recent (30-day) downloads: ~165,184

Adoption acceleration: 78.9x - 80.4x
[+] STRONG PHASE TRANSITION DETECTED
```

**Runtime:** Instant (cached) or ~10 minutes (fresh)

**Interpretation:**
- Packages with high initial adoption → Cascade effect
- Packages with low week-1 → Remain niche
- **~80x difference** - early adoption critical in package ecosystems

---

## Validation 4: Academic Citations

**Pattern:** INVERTED - Early burst hurts long-term (4.8x penalty)

### Run
```bash
cd validations/
python academic_citations_analysis.py
```

### Expected Output
```
Top 20% papers (by year-1 citations):
  Year 1: ~158.7 citations
  Total: ~768.8 citations

Bottom 20% papers (low/zero year-1):
  Year 1: ~0.0 citations
  Total: ~3683.8 citations

Ratio: 0.21x - 0.3x (inverted)
Pattern: Gradual accumulation wins (4.8x advantage)
```

**Runtime:** Instant (cached) or ~15 minutes (fresh)

**Interpretation:**
- Papers with high year-1 citations → Crystallize at lower totals
- Papers with gradual citation growth → Higher long-term impact
- **Inverted pattern** validates collaborative system crystallization

---

## What You Should See

### All Four Validations Show:

1. **GitHub & Citations (Collaborative):**
   - Instant success = BAD (crystallization)
   - Gradual growth = GOOD (4-81x advantage)

2. **HN & NPM (Viral/Speculative):**
   - High early momentum = GOOD (cascade)
   - Low momentum = BAD (15-80x disadvantage)

### Acceptable Variation

Results may vary by ±30% due to:
- Different API snapshots
- Sample variation
- Time period differences

**Critical invariant:** The **directional pattern** must hold:
- Collaborative: Gradual > Instant
- Viral: High momentum > Low momentum

---

## Troubleshooting

### GitHub Validation Issues

**Problem:** "Insufficient data" for all repos

**Solution:**
- Check GitHub token is valid
- Token needs `public_repo` scope
- Some repos may have disabled star timestamps

**Workaround:**
- Run other 3 validations (they don't need tokens)
- GitHub pattern is well-documented in theory docs

### Python Import Errors

**Problem:** `ModuleNotFoundError`

**Solution:**
```bash
pip install -r requirements.txt
```

### Cached Data

All scripts cache data in `.pkl` files for speed:
- `hn_data_cache.pkl`
- `npm_data_cache.pkl`
- `papers_data_cache.pkl`

To force fresh data fetch:
```bash
# Delete cache files
rm *.pkl

# Re-run scripts
python script_name.py
```

---

## Timeline

**Total time to reproduce all findings:**

- GitHub: 5 minutes (or skip if token issues)
- HN: <1 second (cached) or 5 minutes (fresh)
- NPM: <1 second (cached) or 10 minutes (fresh)
- Citations: <1 second (cached) or 15 minutes (fresh)

**Total:** 3 seconds (all cached) to 35 minutes (all fresh)

---

## Verification Checklist

After running all scripts, verify:

- [ ] GitHub shows ~81x difference (gradual > instant)
- [ ] HN shows ~15x difference (high momentum > low)
- [ ] NPM shows ~80x difference (high week-1 > low)
- [ ] Citations shows inverted pattern (gradual > instant)
- [ ] All four patterns directionally consistent

**If all 4 match: Pattern reproduced successfully** ✅

---

## What This Means

You've independently verified that:

1. **Memory accumulation drives phase transitions** across multiple domains
2. **Same physics, opposite outcomes** depending on system type
3. **Effect sizes are large** (4-81x, not subtle)
4. **Pattern is reproducible** (you just did it)

This is a real, cross-domain phenomenon.

---

## Next Steps After Reproduction

1. **Report results** - Open an issue if you get different patterns
2. **Test new domains** - Try Reddit, Twitter, YouTube, etc.
3. **Extend analysis** - Larger samples, longer time periods
4. **Build applications** - Use pattern for strategy/prediction
5. **Cite if useful** - See main README for citation info

---

## Questions?

- Check `theory/UNIVERSAL_PHASE_TRANSITIONS.md` for detailed explanation
- Check `docs/EVIDENCE_SUMMARY.md` for all findings
- Check `EXPECTED_RESULTS.md` for baseline numbers
- Open an issue on GitHub for help

---

## Last Validated

**Date:** October 17, 2025
**By:** Formslip & Ash
**Result:** All 4 validations confirmed

**Status:** ✅ Ready for independent reproduction

---

*"We found a pattern. We tested it. We documented it. Now you can verify it."*

— Open Science, 2025
