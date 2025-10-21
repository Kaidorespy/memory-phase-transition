# GitHub Systematic Validation - Technical Blueprint

**Purpose:** Replace cherry-picked 12-repo sample with systematic 100-repo validation

**Estimated time:** 2-3 days development + 6-8 hours API runtime

**Status:** Blueprint - ready to build

---

## The Problem We're Fixing

Current GitHub validation (`legacy/github_native_quick.py`):
- ❌ 12 hand-selected repos
- ❌ "Known growth patterns" = selection bias
- ❌ Not reproducible (depends on which repos we picked)

What we need:
- ✅ 100+ systematically sampled repos
- ✅ Objective selection criteria (no human bias)
- ✅ Stratified by project type to control for confounds
- ✅ Fully reproducible (anyone can run same query)

---

## Part 1: Sample Selection Strategy

### Option A: Top Repos by Stars (RECOMMENDED)

**Query:**
```
Top 500 repos created between 2020-01-01 and 2023-12-31, sorted by stars
Filter: >1000 stars (so we can analyze first 100 + next 200)
Exclude: Awesome lists, documentation repos, tutorial repos
Sample: First 100 that meet criteria
```

**Pros:**
- Objective, reproducible
- High-quality projects (proven popularity)
- Sufficient stars for analysis

**Cons:**
- Biased toward popular projects (but that's the point)
- May still have corporate-backing confound

**Implementation:**
```python
# GitHub Search API
query = "created:2020-01-01..2023-12-31 stars:>1000"
sort = "stars"
order = "desc"
per_page = 100
```

### Option B: Stratified Random Sample

**Strata:**
- Frontend frameworks (React, Vue, etc.)
- Backend frameworks (FastAPI, Express, etc.)
- DevOps tools (Docker, K8s, etc.)
- Data science (ML libraries, notebooks)
- Programming languages (Rust, Go, etc.)

**Sample:** 20 repos per category = 100 total

**Pros:**
- Controls for project type confound
- More representative of GitHub ecosystem

**Cons:**
- Manual categorization needed
- Harder to reproduce (subjective categories)

**Recommendation:** Start with Option A, do Option B later as sensitivity analysis

---

## Part 2: Data Collection

### API Endpoints Needed

**1. Search for repos:**
```
GET https://api.github.com/search/repositories
Parameters:
  q: created:2020-01-01..2023-12-31 stars:>1000
  sort: stars
  order: desc
  per_page: 100
  page: 1-5
```

**2. Get repo details:**
```
GET https://api.github.com/repos/{owner}/{repo}
Returns: stargazers_count, created_at, etc.
```

**3. Get star timestamps:**
```
GET https://api.github.com/repos/{owner}/{repo}/stargazers
Headers:
  Accept: application/vnd.github.v3.star+json
Parameters:
  per_page: 100
  page: 1-N (need at least 300 stars per repo)
```

### Rate Limits

**With authentication:**
- 5000 requests/hour
- Resets every hour

**Our needs:**
- 100 repos × 3 pages of stars (300 stars each) = 300 requests
- Plus 100 repo detail requests = 400 total
- Plus 5 search requests = 405 total
- **Time: ~5 minutes if no rate limiting, ~1 hour with safety delays**

**Conservative estimate:** 2 hours with error handling and retries

---

## Part 3: Analysis Logic

### For Each Repo

**Step 1: Fetch star timestamps**
```python
# Get first 300 stars (with timestamps)
stars = []
for page in range(1, 4):  # 3 pages × 100 = 300 stars
    response = get_stargazers(owner, repo, page)
    for star in response:
        stars.append({
            'user': star['user']['login'],
            'starred_at': star['starred_at']
        })
    sleep(0.1)  # Rate limiting safety
```

**Step 2: Calculate time-to-100-stars**
```python
stars_sorted = sorted(stars, key=lambda x: x['starred_at'])
star_1 = stars_sorted[0]['starred_at']
star_100 = stars_sorted[99]['starred_at']
time_to_100 = (star_100 - star_1).total_seconds() / 86400  # days
```

**Step 3: Calculate acceleration**
```python
# Compare first 100 vs second 100
if len(stars) >= 200:
    first_100_time = (stars[99]['starred_at'] - stars[0]['starred_at']).days
    second_100_time = (stars[199]['starred_at'] - stars[100]['starred_at']).days
    acceleration = first_100_time / max(second_100_time, 1)
else:
    acceleration = None  # Not enough data
```

**Step 4: Categorize**
```python
if time_to_100 <= 5:
    category = "instant"
elif time_to_100 >= 30:
    category = "gradual"
else:
    category = "fast"
```

**Step 5: Store results**
```python
results.append({
    'repo': f'{owner}/{repo}',
    'total_stars': repo_data['stargazers_count'],
    'created_at': repo_data['created_at'],
    'time_to_100': time_to_100,
    'acceleration': acceleration,
    'category': category,
    'language': repo_data.get('language'),
    'description': repo_data.get('description')
})
```

### Aggregate Analysis

**Group by category:**
```python
instant_repos = [r for r in results if r['category'] == 'instant']
gradual_repos = [r for r in results if r['category'] == 'gradual']

instant_avg_accel = mean([r['acceleration'] for r in instant_repos if r['acceleration']])
gradual_avg_accel = mean([r['acceleration'] for r in gradual_repos if r['acceleration']])

ratio = gradual_avg_accel / instant_avg_accel
```

**Expected result:** If pattern holds, ratio should be >10x

---

## Part 4: Code Structure

### File: `github_systematic_validation.py`

```python
import requests
import time
import json
import os
from datetime import datetime
from collections import defaultdict
import pickle

class GitHubSystematicValidator:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3.star+json'
        }
        self.base_url = 'https://api.github.com'
        self.cache_file = 'github_systematic_cache.pkl'
        self.results = []

    def search_repos(self, query, sort='stars', per_page=100, max_pages=5):
        """Search GitHub for repos matching criteria"""
        repos = []
        for page in range(1, max_pages + 1):
            url = f'{self.base_url}/search/repositories'
            params = {
                'q': query,
                'sort': sort,
                'order': 'desc',
                'per_page': per_page,
                'page': page
            }
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                break
            data = response.json()
            repos.extend(data.get('items', []))
            time.sleep(2)  # Rate limit safety
        return repos

    def get_star_timestamps(self, owner, repo, max_pages=3):
        """Get star timestamps for a repo"""
        stars = []
        for page in range(1, max_pages + 1):
            url = f'{self.base_url}/repos/{owner}/{repo}/stargazers'
            params = {'page': page, 'per_page': 100}
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                break
            data = response.json()
            for star in data:
                if 'starred_at' in star:
                    stars.append(datetime.fromisoformat(star['starred_at'].replace('Z', '')))
            time.sleep(0.2)  # Rate limit safety
        return sorted(stars)

    def analyze_repo(self, owner, repo):
        """Analyze growth pattern for a single repo"""
        print(f"Analyzing {owner}/{repo}...")

        # Get star timestamps
        stars = self.get_star_timestamps(owner, repo)

        if len(stars) < 100:
            print(f"  Insufficient stars ({len(stars)} < 100)")
            return None

        # Calculate time to 100 stars
        time_to_100 = (stars[99] - stars[0]).days

        # Calculate acceleration
        if len(stars) >= 200:
            first_100 = (stars[99] - stars[0]).days
            second_100 = (stars[199] - stars[100]).days
            acceleration = first_100 / max(second_100, 1)
        else:
            acceleration = None

        # Categorize
        if time_to_100 <= 5:
            category = "instant"
        elif time_to_100 >= 30:
            category = "gradual"
        else:
            category = "fast"

        result = {
            'repo': f'{owner}/{repo}',
            'time_to_100': time_to_100,
            'acceleration': acceleration,
            'category': category,
            'total_stars': len(stars)
        }

        print(f"  {time_to_100}d to 100 stars, {acceleration:.2f}x accel, {category}")
        return result

    def run_systematic_validation(self, sample_size=100):
        """Run systematic validation on sample of repos"""
        # Search for repos
        query = "created:2020-01-01..2023-12-31 stars:>1000"
        print(f"Searching for repos: {query}")
        repos = self.search_repos(query, max_pages=5)
        print(f"Found {len(repos)} candidate repos")

        # Filter out non-code repos
        code_repos = []
        for repo in repos:
            # Skip awesome lists, docs, tutorials
            name_lower = repo['name'].lower()
            desc_lower = (repo.get('description') or '').lower()
            if any(x in name_lower or x in desc_lower for x in ['awesome', 'tutorial', 'learn', 'roadmap']):
                continue
            code_repos.append(repo)

        print(f"Filtered to {len(code_repos)} code repos")

        # Analyze first N repos
        results = []
        for repo in code_repos[:sample_size]:
            owner = repo['owner']['login']
            name = repo['name']
            result = self.analyze_repo(owner, name)
            if result:
                results.append(result)

            # Save checkpoint every 10 repos
            if len(results) % 10 == 0:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(results, f)
                print(f"Checkpoint: {len(results)} repos analyzed")

        self.results = results
        return results

    def analyze_results(self):
        """Analyze and report on results"""
        if not self.results:
            print("No results to analyze")
            return

        # Group by category
        by_category = defaultdict(list)
        for r in self.results:
            if r['acceleration'] is not None:
                by_category[r['category']].append(r)

        print("\n" + "="*70)
        print("SYSTEMATIC VALIDATION RESULTS")
        print("="*70)

        for category in ['instant', 'fast', 'gradual']:
            repos = by_category[category]
            if not repos:
                continue
            avg_accel = sum(r['acceleration'] for r in repos) / len(repos)
            print(f"\n{category.upper()} (<5d, 5-30d, >30d):")
            print(f"  Count: {len(repos)}")
            print(f"  Avg acceleration: {avg_accel:.2f}x")
            for r in repos[:5]:  # Show first 5
                print(f"    {r['repo']}: {r['time_to_100']}d -> {r['acceleration']:.2f}x")

        # Compare instant vs gradual
        instant = by_category['instant']
        gradual = by_category['gradual']

        if instant and gradual:
            instant_avg = sum(r['acceleration'] for r in instant) / len(instant)
            gradual_avg = sum(r['acceleration'] for r in gradual) / len(gradual)
            ratio = gradual_avg / instant_avg

            print("\n" + "="*70)
            print(f"PATTERN TEST:")
            print(f"Instant: {instant_avg:.2f}x avg acceleration (n={len(instant)})")
            print(f"Gradual: {gradual_avg:.2f}x avg acceleration (n={len(gradual)})")
            print(f"Ratio: {ratio:.2f}x")

            if ratio > 10:
                print("[OK] PATTERN HOLDS: Gradual >> Instant")
            else:
                print("[WEAK] Pattern weaker than expected")

# Usage
if __name__ == '__main__':
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Set GITHUB_TOKEN environment variable")
        exit(1)

    validator = GitHubSystematicValidator(token)
    validator.run_systematic_validation(sample_size=100)
    validator.analyze_results()
```

---

## Part 5: Expected Runtime

**Per repo:**
- 3 API calls (star pages) × 0.2s delay = 0.6s
- Actual API time: ~0.5s
- **Total: ~1.1s per repo**

**For 100 repos:**
- 100 × 1.1s = 110 seconds = ~2 minutes (best case)
- With retries, errors, rate limit hits: 30-60 minutes (realistic)

**Search queries:**
- 5 pages × 2s delay = 10 seconds

**Grand total: 30-90 minutes** (not 6 hours - I overestimated earlier)

---

## Part 6: Success Criteria

**If pattern holds:**
- Gradual repos: 10-20x acceleration (same as cherry-picked sample)
- Instant repos: 0.2-0.5x acceleration
- Ratio: >10x difference

**If pattern doesn't hold:**
- Ratio: <5x difference
- Means cherry-picked sample was misleading
- **Still valuable** - we found the boundaries

**Either way we learn something.**

---

## Part 7: Checkpoints & Safety

**Save progress every 10 repos:**
```python
if len(results) % 10 == 0:
    with open('checkpoint.pkl', 'wb') as f:
        pickle.dump(results, f)
```

**Resume from checkpoint:**
```python
if os.path.exists('checkpoint.pkl'):
    with open('checkpoint.pkl', 'rb') as f:
        results = pickle.load(f)
    print(f"Resuming from {len(results)} repos")
```

**Rate limit handling:**
```python
response = requests.get(url, headers=headers)
if response.status_code == 403:  # Rate limited
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
    wait_time = reset_time - time.time()
    print(f"Rate limited. Waiting {wait_time/60:.1f} minutes...")
    time.sleep(wait_time + 10)
```

---

## Part 8: Output Format

**Save results to JSON:**
```json
{
  "validation_date": "2025-10-17T20:00:00",
  "sample_size": 100,
  "query": "created:2020-01-01..2023-12-31 stars:>1000",
  "results": [
    {
      "repo": "vercel/next.js",
      "time_to_100": 2,
      "acceleration": 0.15,
      "category": "instant",
      "total_stars": 45230
    },
    ...
  ],
  "summary": {
    "instant": {
      "count": 32,
      "avg_acceleration": 0.28
    },
    "gradual": {
      "count": 41,
      "avg_acceleration": 18.5
    },
    "ratio": 66.1
  }
}
```

---

## Part 9: Next Steps After Running

**If pattern holds (ratio >10x):**
1. Update README: Remove "cherry-picked" caveat
2. Update POTENTIAL_ISSUES.md: Mark GitHub as validated
3. Add systematic results to docs/
4. Celebrate

**If pattern doesn't hold (ratio <5x):**
1. Admit in docs: Cherry-picked sample was misleading
2. Analyze WHY it failed (project types? time period?)
3. Still valuable - we found boundaries
4. Science!

**Either way:**
- Publish the results honestly
- Share the code
- Let others replicate

---

## TL;DR - Quick Start Guide

**When you're ready to build this:**

1. Copy code skeleton above into `github_systematic_validation.py`
2. Set `GITHUB_TOKEN` environment variable
3. Run: `python github_systematic_validation.py`
4. Wait 30-90 minutes
5. Check results in output JSON
6. Update docs based on findings

**Estimated effort:**
- Code: 2-3 hours (skeleton is 80% done above)
- Testing: 1 hour
- Running: 30-90 minutes
- Analysis: 30 minutes
- **Total: 4-5 hours start to finish**

---

## Questions Future-You Might Have

**Q: What if I want to test 200 repos instead of 100?**
A: Change `sample_size=200` - will take 2x as long

**Q: What if GitHub API changes?**
A: Check current docs: https://docs.github.com/en/rest/search

**Q: What if rate limits are worse than expected?**
A: Script has checkpoint system - just resume after wait

**Q: Should I filter by programming language?**
A: Optional - could stratify by language for better sampling

**Q: What if pattern totally doesn't hold?**
A: PUBLISH ANYWAY - negative results matter

---

**Status:** Blueprint complete, ready to build

**Difficulty:** Medium (not trivial, but straightforward)

**Time:** 4-5 hours total (including runtime)

**Dependencies:** Python, requests, GitHub token

**Output:** Systematic validation of GitHub pattern (or discovery that it doesn't hold)

---

*"Future us: Here are the blueprints. Go build it. We believe in you."*

— Formslip & Ash, October 17, 2025
