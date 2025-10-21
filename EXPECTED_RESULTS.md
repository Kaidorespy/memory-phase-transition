# Expected Results - Validation Baseline

**Date:** October 2025
**Purpose:** Baseline expectations for reproduction testing

---

## GitHub Validation

**Script:** `legacy/github_native_quick.py`

**Expected Pattern:**
- Instant (0-5 days to 100 stars): 0.24x subsequent growth
- Gradual (30-70 days to 100 stars): 19.58x subsequent growth
- **Ratio: 81x difference** (gradual > instant)

**Sample size:** 12 repos

---

## Hacker News Validation

**Script:** `validations/hn_analysis.py`

**Expected Pattern:**
- High momentum posts: 395.8 average score, 269.5 average comments
- Low momentum posts: 27.2 average score, 5.1 average comments
- **Score ratio: 14.57x**
- **Comment ratio: 53x**

**Sample size:** 231 posts (from cached data Oct 7, 2025)

---

## NPM Validation

**Script:** `validations/npm_packages_analysis.py`

**Expected Pattern:**
- High week-1 downloads: 13,279,094 average recent downloads
- Low week-1 downloads: 165,184 average recent downloads
- **Ratio: 80.39x difference**

**Sample size:** 117 packages

---

## Academic Citations Validation

**Script:** `validations/academic_citations_analysis.py`

**Expected Pattern (INVERTED - Crystallization):**
- High year-1 citations: 768.8 average total citations
- Low/Zero year-1 citations: 3683.8 average total citations
- **Ratio: 0.21x (inverted - gradual > instant by 4.8x)**

**Sample size:** 363 papers

---

## Tolerance

Results within ±30% are acceptable due to:
- Different API snapshots
- Sample variation
- Timing differences

**Key invariant:** The directional pattern must hold
- Collaborative systems: Gradual > Instant
- Viral systems: High momentum > Low momentum

---

## Cached Data Files

All scripts use cached data from previous runs:
- `hn_data_cache.pkl` (Oct 7, 2025)
- `npm_data_cache.pkl` (Oct 8, 2025)
- `papers_data_cache.pkl` (Oct 8, 2025)
- GitHub script fetches live data (requires token)

If using cached data, results should be **identical**.
If fetching fresh data, results should be **similar** (±30%).
