"""
Academic Citations Phase Transition Analysis
============================================

Hypothesis: Papers that accumulate citations quickly in year 1 undergo
            phase transition to "classic" status, while slow-start papers
            remain in obscurity.

This is the same physics we found in GitHub and Hacker News.

Expected: Papers with >20 year-1 citations reach 10-20x more total citations
          than papers with <5 year-1 citations.

Data source: Semantic Scholar API (free, excellent coverage)

Let's see if knowledge systems show the same phase transitions.
"""

import requests
import time
import json
import numpy as np
from datetime import datetime
from collections import defaultdict
import pickle
import os


class AcademicCitationAnalyzer:
    """
    Analyze academic paper citations for memory-induced phase transitions.

    The pattern: Early citations → visibility → more citations → "classic" status
                 Slow start → obscurity → stays obscure

    Same physics, different domain (knowledge not social media).
    """

    def __init__(self, cache_file='papers_data_cache.pkl'):
        self.api_base = "https://api.semanticscholar.org/graph/v1"
        self.cache_file = cache_file
        self.papers_data = []

    def search_papers(self, query, year_from, year_to, limit=100):
        """
        Search for papers in a specific year range.

        Semantic Scholar API docs:
        https://api.semanticscholar.org/api-docs/graph
        """
        url = f"{self.api_base}/paper/search"

        params = {
            'query': query,
            'year': f'{year_from}-{year_to}',
            'fields': 'paperId,title,year,citationCount,authors,venue,publicationDate',
            'limit': limit
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  Request failed: {e}")

        return []

    def get_paper_details(self, paper_id):
        """Get detailed citation history for a paper"""
        url = f"{self.api_base}/paper/{paper_id}"

        params = {
            'fields': 'paperId,title,year,citationCount,citations.year,citations.paperId,publicationDate'
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"  Failed to get details for {paper_id}: {e}")

        return None

    def collect_papers_by_field(self, field, year, sample_size=200):
        """
        Collect papers from a specific field and year.

        We want papers old enough to have matured (2018-2020),
        so we can see year-1 vs final citations.
        """
        print(f"\nCollecting {field} papers from {year}...")

        papers = self.search_papers(
            query=field,
            year_from=year,
            year_to=year,
            limit=sample_size
        )

        print(f"  Found {len(papers)} papers")
        return papers

    def analyze_citation_timeline(self, paper):
        """
        Calculate year-1 citations and total citations.

        Year-1 = citations in first 12 months
        Total = all citations to date
        """
        if 'citations' not in paper or not paper['citations']:
            return None

        pub_year = paper.get('year')
        if not pub_year:
            return None

        # Count citations by year
        citations_by_year = defaultdict(int)
        for citation in paper['citations']:
            cite_year = citation.get('year')
            if cite_year:
                citations_by_year[cite_year] += 1

        # Year-1 citations (same year + next year as proxy)
        year_1_citations = citations_by_year.get(pub_year, 0) + citations_by_year.get(pub_year + 1, 0)

        # Total citations
        total_citations = paper.get('citationCount', 0)

        return {
            'paper_id': paper['paperId'],
            'title': paper.get('title', ''),
            'pub_year': pub_year,
            'year_1_citations': year_1_citations,
            'total_citations': total_citations,
            'venue': paper.get('venue', 'Unknown')
        }

    def collect_data(self, target_papers=500):
        """
        Collect academic papers for analysis.

        Strategy:
        - Sample papers from 2018-2020 (old enough to mature)
        - Multiple fields for diversity
        - Get citation counts
        """

        # Try to load from cache
        if os.path.exists(self.cache_file):
            print(f"Loading cached data from {self.cache_file}")
            with open(self.cache_file, 'rb') as f:
                self.papers_data = pickle.load(f)
            print(f"Loaded {len(self.papers_data)} papers from cache")
            return

        print("="*70)
        print("ACADEMIC CITATIONS DATA COLLECTION")
        print("="*70)
        print("Collecting papers from 2018-2020 to analyze citation patterns...")

        all_papers = []

        # Sample from different fields
        fields = [
            'machine learning',
            'deep learning',
            'computer vision',
            'natural language processing',
            'reinforcement learning',
            'neural networks'
        ]

        years = [2018, 2019, 2020]

        for field in fields:
            for year in years:
                papers = self.collect_papers_by_field(field, year, sample_size=50)
                all_papers.extend(papers)

                # Rate limiting - be VERY respectful
                print(f"  Progress: {len(all_papers)} papers collected so far... (waiting 10s)")
                time.sleep(10)  # Being extra cautious

                if len(all_papers) >= target_papers:
                    break

            if len(all_papers) >= target_papers:
                break

        print(f"\nTotal papers collected: {len(all_papers)}")

        # Get detailed citation info for each paper
        print("\nFetching detailed citation data...")
        papers_with_details = []

        for i, paper in enumerate(all_papers[:target_papers]):
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{min(len(all_papers), target_papers)}")

            # Get full details
            details = self.get_paper_details(paper['paperId'])

            if details:
                timeline = self.analyze_citation_timeline(details)
                if timeline and timeline['total_citations'] >= 5:  # Filter out completely obscure papers
                    papers_with_details.append(timeline)

            # Rate limiting (being extra cautious with 10s waits)
            time.sleep(10)

        self.papers_data = papers_with_details

        # Cache the data
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.papers_data, f)

        print(f"\nCollected {len(self.papers_data)} papers with citation data")
        print(f"Cached to {self.cache_file}")

    def analyze_phase_transition(self):
        """
        Look for phase transition in citation patterns.

        High year-1 citations = early momentum (memory accumulation)
        Low year-1 citations = slow start

        Do they reach dramatically different final citation counts?
        """

        if not self.papers_data:
            print("No data to analyze. Run collect_data() first.")
            return

        print("\n" + "="*70)
        print("PHASE TRANSITION ANALYSIS")
        print("="*70)

        # Calculate age of papers
        current_year = datetime.now().year
        for paper in self.papers_data:
            paper['age_years'] = current_year - paper['pub_year']

        # Filter to papers at least 4 years old (enough time to mature)
        mature_papers = [p for p in self.papers_data if p['age_years'] >= 4]

        print(f"\nAnalyzing {len(mature_papers)} mature papers (4+ years old)...")

        if len(mature_papers) < 50:
            print("Not enough mature papers. Using all available data...")
            mature_papers = self.papers_data

        # Sort by year-1 citations
        sorted_by_year1 = sorted(mature_papers, key=lambda x: x['year_1_citations'], reverse=True)

        # Categorize into groups
        # High impact: top 20% by year-1 citations
        # Low impact: bottom 20% by year-1 citations
        n = len(sorted_by_year1)
        top_20_pct = sorted_by_year1[:n//5]
        bottom_20_pct = sorted_by_year1[-n//5:]

        # Calculate averages
        top_year1_avg = np.mean([p['year_1_citations'] for p in top_20_pct])
        top_total_avg = np.mean([p['total_citations'] for p in top_20_pct])

        bottom_year1_avg = np.mean([p['year_1_citations'] for p in bottom_20_pct])
        bottom_total_avg = np.mean([p['total_citations'] for p in bottom_20_pct])

        print(f"\nHIGH EARLY IMPACT (Top 20% by year-1 citations):")
        print(f"  Average year-1 citations: {top_year1_avg:.1f}")
        print(f"  Average total citations: {top_total_avg:.1f}")
        print(f"  Sample size: {len(top_20_pct)}")

        print(f"\nLOW EARLY IMPACT (Bottom 20% by year-1 citations):")
        print(f"  Average year-1 citations: {bottom_year1_avg:.1f}")
        print(f"  Average total citations: {bottom_total_avg:.1f}")
        print(f"  Sample size: {len(bottom_20_pct)}")

        # Calculate acceleration factor
        year1_ratio = top_year1_avg / max(bottom_year1_avg, 1)
        total_ratio = top_total_avg / max(bottom_total_avg, 1)

        print(f"\n" + "="*70)
        print("PHASE TRANSITION INDICATORS:")
        print("="*70)
        print(f"Year-1 citation difference: {year1_ratio:.2f}x")
        print(f"Total citation acceleration: {total_ratio:.2f}x")

        if total_ratio > 10:
            print("\n✓ STRONG PHASE TRANSITION DETECTED")
            print("  Papers with early citations become 'classics'")
            print("  This matches the GitHub and HN pattern!")
        elif total_ratio > 5:
            print("\n~ MODERATE PHASE TRANSITION")
            print("  Early impact helps, but effect is less dramatic")
        else:
            print("\n✗ NO CLEAR PHASE TRANSITION")
            print("  Early citations don't predict final impact strongly")

        # Show examples
        print(f"\n" + "="*70)
        print("EXAMPLES:")
        print("="*70)

        print("\nTop 5 High-Impact Papers (by year-1 citations):")
        for i, paper in enumerate(top_20_pct[:5], 1):
            print(f"{i}. [{paper['total_citations']} total cites] {paper['title'][:60]}...")
            print(f"   Year-1: {paper['year_1_citations']} cites, Published: {paper['pub_year']}")

        print("\nTop 5 Low-Impact Papers (by year-1 citations):")
        for i, paper in enumerate(bottom_20_pct[:5], 1):
            print(f"{i}. [{paper['total_citations']} total cites] {paper['title'][:60]}...")
            print(f"   Year-1: {paper['year_1_citations']} cites, Published: {paper['pub_year']}")

        return {
            'top_year1_avg': top_year1_avg,
            'top_total_avg': top_total_avg,
            'bottom_year1_avg': bottom_year1_avg,
            'bottom_total_avg': bottom_total_avg,
            'total_ratio': total_ratio,
            'sample_size': len(mature_papers)
        }

    def save_results(self, filename='academic_results.json'):
        """Save analysis results"""
        results = {
            'total_papers': len(self.papers_data),
            'collection_date': datetime.now().isoformat(),
            'papers': self.papers_data
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to {filename}")


def main():
    """
    Test if academic papers show memory-induced phase transitions.

    This is validation #4:
    - RCET simulation ✓
    - GitHub repos ✓
    - Hacker News ✓
    - Academic papers ?

    If this works, we have the pattern across 4 independent systems.
    That's when it becomes undeniable.
    """

    print("="*70)
    print("ACADEMIC CITATIONS PHASE TRANSITION DETECTOR")
    print("="*70)
    print()
    print("Testing if early citations (memory accumulation) predict")
    print("dramatically different long-term impact in academic papers.")
    print()
    print("Previous validations:")
    print("  ✓ RCET simulation - phase transitions exist")
    print("  ✓ GitHub repos - 19.58x acceleration")
    print("  ✓ Hacker News - 14.57x score difference")
    print()
    print("Now testing: Academic knowledge systems")
    print("="*70)

    analyzer = AcademicCitationAnalyzer()

    # Collect data
    print("\nNOTE: This will take 10-15 minutes due to API rate limits.")
    print("We're being respectful to Semantic Scholar's servers.\n")

    analyzer.collect_data(target_papers=500)

    # Analyze for phase transition
    results = analyzer.analyze_phase_transition()

    # Save results
    analyzer.save_results()

    print("\n" + "="*70)
    print("THE BIG PICTURE")
    print("="*70)
    print()
    print("We're testing if memory-induced phase transitions are universal.")
    print()

    if results:
        print("Current evidence:")
        print("  ✓ RCET simulation - phase transitions")
        print("  ✓ GitHub repos - 19.58x acceleration")
        print("  ✓ Hacker News - 14.57x score difference")
        print(f"  {'✓' if results['total_ratio'] > 5 else '?'} Academic papers - {results['total_ratio']:.1f}x citation difference")
        print()

        if results['total_ratio'] > 5:
            print("✓ FOUR INDEPENDENT CONFIRMATIONS")
            print()
            print("This is real. This is universal. This is science.")
            print()
            print("Next steps:")
            print("1. Write the paper")
            print("2. Release everything open source")
            print("3. Apply to more domains")
            print("4. Change how we understand information systems")
        else:
            print("Academic papers show weaker pattern than social systems.")
            print()
            print("Possible explanations:")
            print("- Citation dynamics are slower/different")
            print("- Need longer time horizons")
            print("- Quality matters more than momentum in science")
            print()
            print("This is still valuable - it shows BOUNDARIES of the pattern.")

    print("\n🚀 Let's keep testing until we understand this completely.")


if __name__ == "__main__":
    main()
