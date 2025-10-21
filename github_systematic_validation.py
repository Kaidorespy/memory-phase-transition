"""
GitHub Systematic Validation
=============================

Replaces cherry-picked 12-repo sample with systematic 100-repo validation.

Run time: ~30-90 minutes
Output: Systematic test of phase transition pattern across GitHub repos
"""

import requests
import time
import json
import os
from datetime import datetime
from collections import defaultdict
import pickle


class GitHubSystematicValidator:
    """
    Systematically validate GitHub phase transition pattern.

    Uses objective sampling (top repos by stars in 2020-2023)
    instead of hand-picked "known growth patterns" repos.
    """

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
        """
        Search GitHub for repos matching criteria.

        Returns list of repo objects from search API.
        """
        print(f"Searching GitHub: {query}")
        print(f"This will take ~{max_pages * 2} seconds (rate limiting)...")

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

            if response.status_code == 403:  # Rate limited
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))
                wait_time = reset_time - time.time()
                print(f"Rate limited. Waiting {wait_time/60:.1f} minutes...")
                time.sleep(wait_time + 10)
                continue

            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                break

            data = response.json()
            repos.extend(data.get('items', []))
            print(f"  Page {page}: {len(data.get('items', []))} repos")
            time.sleep(2)  # Rate limit safety

        return repos

    def get_star_timestamps(self, owner, repo, max_pages=3):
        """
        Get star timestamps for a repo.

        Returns sorted list of datetime objects.
        """
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
        """
        Analyze growth pattern for a single repo.

        Returns dict with time_to_100, acceleration, category, etc.
        """
        print(f"Analyzing {owner}/{repo}...")

        # Get star timestamps
        stars = self.get_star_timestamps(owner, repo)

        if len(stars) < 100:
            print(f"  Insufficient stars ({len(stars)} < 100) - skipping")
            return None

        # Calculate time to 100 stars
        time_to_100 = (stars[99] - stars[0]).days

        # Calculate acceleration (compare first 100 vs second 100)
        if len(stars) >= 200:
            first_100 = (stars[99] - stars[0]).days
            second_100 = (stars[199] - stars[100]).days
            acceleration = first_100 / max(second_100, 1)
        else:
            acceleration = None
            print(f"  Only {len(stars)} stars - can't calculate acceleration")
            return None

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
            'total_stars_analyzed': len(stars)
        }

        print(f"  {time_to_100}d to 100 stars -> {acceleration:.2f}x accel [{category}]")
        return result

    def run_systematic_validation(self, sample_size=100):
        """
        Run systematic validation on sample of repos.

        Main entry point for the validation.
        """
        print("="*70)
        print("GITHUB SYSTEMATIC VALIDATION")
        print("="*70)
        print(f"Target sample size: {sample_size}")
        print()

        # Check for checkpoint
        if os.path.exists(self.cache_file):
            print(f"Found checkpoint file: {self.cache_file}")
            with open(self.cache_file, 'rb') as f:
                self.results = pickle.load(f)
            print(f"Resuming from {len(self.results)} repos")
            print()

        # Search for repos
        query = "created:2020-01-01..2023-12-31 stars:>1000"
        repos = self.search_repos(query, max_pages=5)
        print(f"\nFound {len(repos)} total repos")

        # Filter out non-code repos (awesome lists, tutorials, etc.)
        code_repos = []
        for repo in repos:
            name_lower = repo['name'].lower()
            desc_lower = (repo.get('description') or '').lower()

            # Skip obvious non-code repos
            skip_terms = ['awesome', 'tutorial', 'learn', 'roadmap', 'interview', 'cheatsheet']
            if any(term in name_lower or term in desc_lower for term in skip_terms):
                continue

            code_repos.append(repo)

        print(f"Filtered to {len(code_repos)} code repos")
        print()

        # Skip repos we've already analyzed
        analyzed_names = {r['repo'] for r in self.results}

        # Analyze repos
        for i, repo in enumerate(code_repos):
            owner = repo['owner']['login']
            name = repo['name']
            repo_full = f'{owner}/{name}'

            # Skip if already analyzed
            if repo_full in analyzed_names:
                continue

            # Stop if we've hit sample size
            if len(self.results) >= sample_size:
                break

            print(f"[{len(self.results) + 1}/{sample_size}]")
            result = self.analyze_repo(owner, name)

            if result:
                self.results.append(result)

            # Save checkpoint every 10 repos
            if len(self.results) % 10 == 0:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.results, f)
                print(f"  Checkpoint saved: {len(self.results)} repos")

            print()

        print(f"\nCompleted analysis of {len(self.results)} repos")
        return self.results

    def analyze_results(self):
        """
        Analyze and report on results.

        Groups by category and compares instant vs gradual.
        """
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

        # Show each category
        for category in ['instant', 'fast', 'gradual']:
            repos = by_category[category]
            if not repos:
                continue

            avg_accel = sum(r['acceleration'] for r in repos) / len(repos)

            print(f"\n{category.upper()} {'(<5 days)' if category == 'instant' else '(5-30 days)' if category == 'fast' else '(>30 days)'}:")
            print(f"  Count: {len(repos)}")
            print(f"  Average acceleration: {avg_accel:.2f}x")

            # Show examples
            print(f"  Examples:")
            for r in repos[:5]:
                print(f"    {r['repo']}: {r['time_to_100']}d -> {r['acceleration']:.2f}x")

        # Compare instant vs gradual
        instant = by_category['instant']
        gradual = by_category['gradual']

        if instant and gradual:
            instant_avg = sum(r['acceleration'] for r in instant) / len(instant)
            gradual_avg = sum(r['acceleration'] for r in gradual) / len(gradual)
            ratio = gradual_avg / instant_avg

            print("\n" + "="*70)
            print("PATTERN TEST:")
            print("="*70)
            print(f"Instant repos (<5d): {instant_avg:.2f}x avg acceleration (n={len(instant)})")
            print(f"Gradual repos (>30d): {gradual_avg:.2f}x avg acceleration (n={len(gradual)})")
            print(f"Difference: {ratio:.2f}x")
            print()

            if ratio > 10:
                print("[OK] PATTERN HOLDS: Gradual growth >> Instant growth")
                print("  Systematic validation confirms cherry-picked sample finding")
            elif ratio > 5:
                print("[MODERATE] Pattern exists but weaker than expected")
                print("  Cherry-picked sample may have overstated effect size")
            else:
                print("[WEAK] Pattern does not strongly hold")
                print("  Cherry-picked sample was likely misleading")

        else:
            print("\n[WARNING] Not enough repos in both categories to compare")

        # Save results to JSON
        output = {
            'validation_date': datetime.now().isoformat(),
            'sample_size': len(self.results),
            'query': 'created:2020-01-01..2023-12-31 stars:>1000',
            'results': self.results,
            'summary': {
                cat: {
                    'count': len(by_category[cat]),
                    'avg_acceleration': sum(r['acceleration'] for r in by_category[cat]) / len(by_category[cat]) if by_category[cat] else 0
                }
                for cat in ['instant', 'fast', 'gradual']
            }
        }

        output_file = 'github_systematic_results.json'
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nResults saved to: {output_file}")


def main():
    """Main entry point"""
    # Get GitHub token
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        print("Set it with: export GITHUB_TOKEN='your_token_here'")
        print("Generate token at: https://github.com/settings/tokens")
        print("Required scope: public_repo")
        return

    # Create validator
    validator = GitHubSystematicValidator(token)

    # Run validation (default 100 repos)
    validator.run_systematic_validation(sample_size=100)

    # Analyze and report
    validator.analyze_results()


if __name__ == '__main__':
    main()
