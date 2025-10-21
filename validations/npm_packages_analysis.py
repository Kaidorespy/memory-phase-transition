"""
NPM Package Downloads Phase Transition Analysis
================================================

Hypothesis: NPM packages that get high download velocity in their first week
            undergo phase transition to widespread adoption, while slow-start
            packages remain niche.

This is the same physics we found in GitHub and Hacker News.

Expected: Packages with high week-1 downloads reach 10-20x more total downloads
          than packages with low week-1 downloads.

Data source: NPM registry API (free, public)

Let's see if package adoption shows the same phase transitions.
"""

import requests
import time
import json
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import pickle
import os


class NPMAnalyzer:
    """
    Analyze NPM package downloads for memory-induced phase transitions.

    The pattern: Early downloads → visibility → more downloads → widespread adoption
                 Slow start → obscurity → stays niche

    Same physics, different domain (package ecosystems).
    """

    def __init__(self, cache_file='npm_data_cache.pkl'):
        self.registry_url = "https://registry.npmjs.org"
        self.downloads_api = "https://api.npmjs.org/downloads"
        self.cache_file = cache_file
        self.packages_data = []

    def search_packages(self, query, size=250):
        """Search for packages matching a query"""
        url = f"{self.registry_url}/-/v1/search"
        params = {
            'text': query,
            'size': size
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('objects', [])
        except Exception as e:
            print(f"  Search failed: {e}")

        return []

    def get_package_info(self, package_name):
        """Get package metadata"""
        url = f"{self.registry_url}/{package_name}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass

        return None

    def get_download_stats(self, package_name, start_date, end_date):
        """
        Get download counts for a date range.

        NPM API: https://github.com/npm/registry/blob/master/docs/download-counts.md
        """
        # Format: YYYY-MM-DD
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        url = f"{self.downloads_api}/point/{start_str}:{end_str}/{package_name}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('downloads', 0)
        except:
            pass

        return None

    def collect_packages(self, target_count=200):
        """
        Collect NPM packages for analysis.

        Strategy:
        - Sample popular packages from different categories
        - Get their publish dates and download stats
        - Focus on packages 2-4 years old (mature but not ancient)
        """

        # Try to load from cache
        if os.path.exists(self.cache_file):
            print(f"Loading cached data from {self.cache_file}")
            with open(self.cache_file, 'rb') as f:
                self.packages_data = pickle.load(f)
            print(f"Loaded {len(self.packages_data)} packages from cache")
            return

        print("="*70)
        print("NPM PACKAGES DATA COLLECTION")
        print("="*70)

        # Search different categories
        queries = [
            'react component',
            'vue component',
            'typescript utility',
            'build tool',
            'testing library',
            'api client',
            'cli tool',
            'webpack plugin'
        ]

        all_packages = []
        seen_names = set()

        for query in queries:
            print(f"\nSearching for: {query}")
            results = self.search_packages(query, size=50)

            for item in results:
                pkg = item.get('package', {})
                name = pkg.get('name')

                if name and name not in seen_names:
                    seen_names.add(name)
                    all_packages.append(pkg)

            print(f"  Found {len(results)} packages ({len(all_packages)} total unique)")
            time.sleep(1)  # Rate limiting

            if len(all_packages) >= target_count:
                break

        print(f"\nCollected {len(all_packages)} unique packages")

        # Now get detailed info and download stats
        print("\nFetching download statistics...")
        packages_with_stats = []

        for i, pkg in enumerate(all_packages[:target_count]):
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{min(len(all_packages), target_count)}")

            name = pkg.get('name')

            # Get full package info
            info = self.get_package_info(name)
            if not info:
                continue

            # Get publish date
            time_obj = info.get('time', {})
            created = time_obj.get('created')

            if not created:
                continue

            # Parse publish date
            try:
                publish_date = datetime.fromisoformat(created.replace('Z', ''))
            except:
                continue

            # Only include packages 0.5-5 years old (mature enough to analyze)
            age_years = (datetime.now() - publish_date).days / 365
            if age_years < 0.5 or age_years > 5:
                continue

            # Get download stats for first 7 days after publish
            week1_start = publish_date
            week1_end = publish_date + timedelta(days=7)
            week1_downloads = self.get_download_stats(name, week1_start, week1_end)

            # Get recent 30-day download stats (proxy for current popularity)
            recent_end = datetime.now()
            recent_start = recent_end - timedelta(days=30)
            recent_downloads = self.get_download_stats(name, recent_start, recent_end)

            if week1_downloads is not None and recent_downloads is not None:
                packages_with_stats.append({
                    'name': name,
                    'publish_date': publish_date.isoformat(),
                    'age_years': age_years,
                    'week1_downloads': week1_downloads,
                    'recent_30day_downloads': recent_downloads,
                    'description': pkg.get('description', '')[:100]
                })

            time.sleep(0.5)  # Rate limiting

        self.packages_data = packages_with_stats

        # Cache
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.packages_data, f)

        print(f"\nCollected {len(self.packages_data)} packages with download stats")
        print(f"Cached to {self.cache_file}")

    def analyze_phase_transition(self):
        """
        Look for phase transition pattern.

        High week-1 downloads = early momentum (memory accumulation)
        Low week-1 downloads = slow start

        Do they reach dramatically different adoption levels?
        """

        if not self.packages_data:
            print("No data to analyze. Run collect_packages() first.")
            return

        print("\n" + "="*70)
        print("PHASE TRANSITION ANALYSIS")
        print("="*70)

        print(f"\nAnalyzing {len(self.packages_data)} packages...")

        # Filter out packages with zero downloads (inactive)
        active_packages = [p for p in self.packages_data if p['recent_30day_downloads'] > 100]

        print(f"Active packages (>100 downloads/month): {len(active_packages)}")

        if len(active_packages) < 10:
            print("Not enough active packages for analysis (need at least 10)")
            return

        # Sort by week-1 downloads
        sorted_by_week1 = sorted(active_packages, key=lambda x: x['week1_downloads'], reverse=True)

        # Top 20% vs bottom 20%
        n = len(sorted_by_week1)
        top_20_pct = sorted_by_week1[:n//5]
        bottom_20_pct = sorted_by_week1[-n//5:]

        # Calculate averages
        top_week1_avg = np.mean([p['week1_downloads'] for p in top_20_pct])
        top_recent_avg = np.mean([p['recent_30day_downloads'] for p in top_20_pct])

        bottom_week1_avg = np.mean([p['week1_downloads'] for p in bottom_20_pct])
        bottom_recent_avg = np.mean([p['recent_30day_downloads'] for p in bottom_20_pct])

        print(f"\nHIGH EARLY MOMENTUM (Top 20% by week-1 downloads):")
        print(f"  Average week-1 downloads: {top_week1_avg:.1f}")
        print(f"  Average recent (30-day) downloads: {top_recent_avg:.1f}")
        print(f"  Sample size: {len(top_20_pct)}")

        print(f"\nLOW EARLY MOMENTUM (Bottom 20% by week-1 downloads):")
        print(f"  Average week-1 downloads: {bottom_week1_avg:.1f}")
        print(f"  Average recent (30-day) downloads: {bottom_recent_avg:.1f}")
        print(f"  Sample size: {len(bottom_20_pct)}")

        # Calculate ratios
        week1_ratio = top_week1_avg / max(bottom_week1_avg, 1)
        adoption_ratio = top_recent_avg / max(bottom_recent_avg, 1)

        print(f"\n" + "="*70)
        print("PHASE TRANSITION INDICATORS:")
        print("="*70)
        print(f"Week-1 download difference: {week1_ratio:.2f}x")
        print(f"Adoption acceleration: {adoption_ratio:.2f}x")

        if adoption_ratio > 10:
            print("\n[+] STRONG PHASE TRANSITION DETECTED")
            print("  Packages with early downloads achieve widespread adoption")
            print("  This matches the GitHub and HN pattern!")
        elif adoption_ratio > 5:
            print("\n[~] MODERATE PHASE TRANSITION")
            print("  Early momentum helps, but effect is less dramatic")
        else:
            print("\n[-] NO CLEAR PHASE TRANSITION")
            print("  Early downloads don't predict adoption strongly")

        # Show examples
        print(f"\n" + "="*70)
        print("EXAMPLES:")
        print("="*70)

        print("\nTop 5 High-Momentum Packages:")
        for i, pkg in enumerate(top_20_pct[:5], 1):
            print(f"{i}. {pkg['name']}")
            print(f"   Week-1: {pkg['week1_downloads']} downloads")
            print(f"   Recent: {pkg['recent_30day_downloads']} downloads/month")
            print(f"   Age: {pkg['age_years']:.1f} years")

        print("\nTop 5 Low-Momentum Packages:")
        for i, pkg in enumerate(bottom_20_pct[:5], 1):
            print(f"{i}. {pkg['name']}")
            print(f"   Week-1: {pkg['week1_downloads']} downloads")
            print(f"   Recent: {pkg['recent_30day_downloads']} downloads/month")
            print(f"   Age: {pkg['age_years']:.1f} years")

        return {
            'top_week1_avg': top_week1_avg,
            'top_recent_avg': top_recent_avg,
            'bottom_week1_avg': bottom_week1_avg,
            'bottom_recent_avg': bottom_recent_avg,
            'adoption_ratio': adoption_ratio,
            'sample_size': len(active_packages)
        }

    def save_results(self, filename='npm_results.json'):
        """Save analysis results"""
        results = {
            'total_packages': len(self.packages_data),
            'collection_date': datetime.now().isoformat(),
            'packages': self.packages_data
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to {filename}")


def main():
    """
    Test if NPM packages show memory-induced phase transitions.

    This is validation #4:
    - RCET simulation ✓
    - GitHub repos ✓
    - Hacker News ✓
    - NPM packages ?

    If this works, we're at 4 independent confirmations.
    """

    print("="*70)
    print("NPM PACKAGES PHASE TRANSITION DETECTOR")
    print("="*70)
    print()
    print("Testing if early downloads (memory accumulation) predict")
    print("dramatically different adoption in NPM packages.")
    print()
    print("Previous validations:")
    print("  [+] RCET simulation - phase transitions exist")
    print("  [+] GitHub repos - 19.58x acceleration")
    print("  [+] Hacker News - 14.57x score difference")
    print()
    print("Now testing: Package ecosystem adoption")
    print("="*70)

    analyzer = NPMAnalyzer()

    # Collect data
    analyzer.collect_packages(target_count=500)

    # Analyze
    results = analyzer.analyze_phase_transition()

    # Save
    analyzer.save_results()

    print("\n" + "="*70)
    print("THE BIG PICTURE")
    print("="*70)

    if results:
        print(f"\nNPM packages show {results['adoption_ratio']:.1f}x adoption difference")
        print("based on early download momentum.")
        print()

        if results['adoption_ratio'] > 5:
            print("[+] PATTERN CONFIRMED in package ecosystems!")
            print()
            print("We now have:")
            print("  [+] RCET simulation")
            print("  [+] GitHub repos (19.58x)")
            print("  [+] Hacker News (14.57x)")
            print(f"  [+] NPM packages ({results['adoption_ratio']:.1f}x)")
            print()
            print("Four independent confirmations. This is REAL.")
        else:
            print("~ Weaker pattern in package ecosystems")
            print()
            print("Possible reasons:")
            print("- Download counts are noisy")
            print("- Quality/utility matters more")
            print("- Package discovery works differently")

    print("\nMoving on to PyPI next...")


if __name__ == "__main__":
    main()
