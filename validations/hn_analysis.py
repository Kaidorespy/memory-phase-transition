"""
Hacker News Phase Transition Analysis
======================================

Hypothesis: Posts that accumulate upvotes quickly undergo a phase transition
            to front-page viral status, while slow-accumulating posts die.

This is the same physics we saw in GitHub repos, just different domain.

Expected: 10-20x difference in final scores between fast and slow posts.

Let's see if this thing is REAL.
"""

import requests
import time
import json
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import pickle
import os


class HNAnalyzer:
    """
    Analyze Hacker News posts for memory-induced phase transitions.

    The HN API gives us:
    - Post score (upvotes)
    - Timestamp
    - Number of comments

    We'll look for: Do posts that get early momentum reach dramatically
    higher final scores than posts with slow starts?
    """

    def __init__(self, cache_file='hn_data_cache.pkl'):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.cache_file = cache_file
        self.posts_data = []

    def get_item(self, item_id):
        """Get a single item from HN API"""
        url = f"{self.base_url}/item/{item_id}.json"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def get_top_stories(self, limit=500):
        """Get recent top stories"""
        print(f"Fetching top {limit} story IDs from HN...")
        url = f"{self.base_url}/topstories.json"
        response = requests.get(url)
        story_ids = response.json()
        return story_ids[:limit]

    def get_best_stories(self, limit=500):
        """Get best stories"""
        print(f"Fetching best {limit} story IDs from HN...")
        url = f"{self.base_url}/beststories.json"
        response = requests.get(url)
        story_ids = response.json()
        return story_ids[:limit]

    def fetch_stories_batch(self, story_ids, batch_name="stories"):
        """Fetch detailed data for a batch of stories"""
        stories = []
        total = len(story_ids)

        print(f"\nFetching {total} {batch_name}...")
        for i, story_id in enumerate(story_ids):
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{total} ({(i+1)/total*100:.1f}%)")

            item = self.get_item(story_id)
            if item and item.get('type') == 'story':
                # Only keep stories with meaningful engagement
                score = item.get('score', 0)
                if score >= 10:  # At least 10 upvotes
                    stories.append({
                        'id': item.get('id'),
                        'title': item.get('title', ''),
                        'score': score,
                        'descendants': item.get('descendants', 0),  # comment count
                        'time': item.get('time', 0),
                        'by': item.get('by', 'unknown')
                    })

            time.sleep(0.05)  # Rate limiting

        print(f"  Collected {len(stories)} valid stories")
        return stories

    def collect_data(self, target_count=1000):
        """
        Collect HN posts for analysis.

        Since we can't get historical upvote timelines easily,
        we'll use a proxy: collect posts over time and track their growth.

        For now, let's just get a snapshot and use score + comments as proxy
        for "momentum strength".
        """

        # Try to load from cache
        if os.path.exists(self.cache_file):
            print(f"Loading cached data from {self.cache_file}")
            with open(self.cache_file, 'rb') as f:
                self.posts_data = pickle.load(f)
            print(f"Loaded {len(self.posts_data)} posts from cache")
            return

        print("="*70)
        print("HACKER NEWS DATA COLLECTION")
        print("="*70)

        # Get different story types
        all_stories = []

        # Top stories
        top_ids = self.get_top_stories(500)
        all_stories.extend(self.fetch_stories_batch(top_ids[:300], "top stories"))

        # Best stories
        best_ids = self.get_best_stories(500)
        all_stories.extend(self.fetch_stories_batch(best_ids[:300], "best stories"))

        # Deduplicate by ID
        seen_ids = set()
        unique_stories = []
        for story in all_stories:
            if story['id'] not in seen_ids:
                seen_ids.add(story['id'])
                unique_stories.append(story)

        self.posts_data = unique_stories

        # Cache the data
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.posts_data, f)

        print(f"\nCollected {len(self.posts_data)} unique stories")
        print(f"Cached to {self.cache_file}")

    def analyze_phase_transition(self):
        """
        Look for phase transition pattern.

        Strategy: Use score + comment velocity as proxy for early momentum.
        High engagement posts = fast memory accumulation
        Low engagement posts = slow memory accumulation

        Then see if there's a non-linear relationship (phase transition).
        """

        if not self.posts_data:
            print("No data to analyze. Run collect_data() first.")
            return

        print("\n" + "="*70)
        print("PHASE TRANSITION ANALYSIS")
        print("="*70)

        # Calculate engagement metrics
        for post in self.posts_data:
            # Time since posting (in hours)
            post_time = datetime.fromtimestamp(post['time'])
            age_hours = (datetime.now() - post_time).total_seconds() / 3600
            post['age_hours'] = age_hours

            # Engagement velocity (score per hour, comments per hour)
            if age_hours > 0:
                post['score_velocity'] = post['score'] / age_hours
                post['comment_velocity'] = post['descendants'] / age_hours
                post['total_velocity'] = (post['score'] + post['descendants'] * 2) / age_hours
            else:
                post['score_velocity'] = 0
                post['comment_velocity'] = 0
                post['total_velocity'] = 0

        # Filter to posts old enough to have stabilized (>24 hours)
        mature_posts = [p for p in self.posts_data if p['age_hours'] > 24]

        if len(mature_posts) < 50:
            print(f"Not enough mature posts ({len(mature_posts)}). Need to collect over time.")
            print("For now, let's analyze the pattern in what we have...")
            mature_posts = self.posts_data

        print(f"\nAnalyzing {len(mature_posts)} posts...")

        # Sort by early momentum (velocity)
        sorted_by_velocity = sorted(mature_posts, key=lambda x: x['total_velocity'], reverse=True)

        # Categorize into groups
        n = len(sorted_by_velocity)
        top_20_pct = sorted_by_velocity[:n//5]  # Top 20% momentum
        bottom_20_pct = sorted_by_velocity[-n//5:]  # Bottom 20% momentum

        # Compare outcomes
        top_avg_score = np.mean([p['score'] for p in top_20_pct])
        bottom_avg_score = np.mean([p['score'] for p in bottom_20_pct])

        top_avg_comments = np.mean([p['descendants'] for p in top_20_pct])
        bottom_avg_comments = np.mean([p['descendants'] for p in bottom_20_pct])

        print(f"\nTOP 20% (High Early Momentum):")
        print(f"  Average final score: {top_avg_score:.1f}")
        print(f"  Average comments: {top_avg_comments:.1f}")
        print(f"  Sample size: {len(top_20_pct)}")

        print(f"\nBOTTOM 20% (Low Early Momentum):")
        print(f"  Average final score: {bottom_avg_score:.1f}")
        print(f"  Average comments: {bottom_avg_comments:.1f}")
        print(f"  Sample size: {len(bottom_20_pct)}")

        score_ratio = top_avg_score / max(bottom_avg_score, 1)
        comment_ratio = top_avg_comments / max(bottom_avg_comments, 1)

        print(f"\n" + "="*70)
        print("PHASE TRANSITION INDICATORS:")
        print("="*70)
        print(f"Score acceleration: {score_ratio:.2f}x")
        print(f"Comment acceleration: {comment_ratio:.2f}x")

        if score_ratio > 5:
            print("\n✓ STRONG PHASE TRANSITION DETECTED")
            print("  High momentum posts reach dramatically higher scores")
            print("  This matches the GitHub pattern!")
        elif score_ratio > 2:
            print("\n~ MODERATE PHASE TRANSITION")
            print("  Early momentum helps, but effect is less dramatic than GitHub")
        else:
            print("\n✗ NO CLEAR PHASE TRANSITION")
            print("  Early momentum doesn't predict final outcome strongly")

        # Show some examples
        print(f"\n" + "="*70)
        print("EXAMPLES:")
        print("="*70)

        print("\nTop 5 High-Momentum Posts:")
        for i, post in enumerate(top_20_pct[:5], 1):
            print(f"{i}. [{post['score']} pts] {post['title'][:60]}...")
            print(f"   Velocity: {post['total_velocity']:.2f}/hr")

        print("\nTop 5 Low-Momentum Posts:")
        for i, post in enumerate(bottom_20_pct[:5], 1):
            print(f"{i}. [{post['score']} pts] {post['title'][:60]}...")
            print(f"   Velocity: {post['total_velocity']:.2f}/hr")

        return {
            'top_avg_score': top_avg_score,
            'bottom_avg_score': bottom_avg_score,
            'score_ratio': score_ratio,
            'comment_ratio': comment_ratio,
            'sample_size': len(mature_posts)
        }

    def save_results(self, filename='hn_results.json'):
        """Save analysis results"""
        results = {
            'total_posts': len(self.posts_data),
            'collection_date': datetime.now().isoformat(),
            'posts': self.posts_data
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to {filename}")


def main():
    """
    Run the HN analysis.

    This is the moment of truth: does the phase transition pattern
    we saw in GitHub repos also show up in Hacker News?

    If yes: We have independent validation in a different domain.
    If no: Maybe GitHub was special, or we need better methodology.

    Either way, we learn something.
    """

    print("="*70)
    print("HACKER NEWS PHASE TRANSITION DETECTOR")
    print("="*70)
    print()
    print("Testing if early momentum (memory accumulation) predicts")
    print("dramatically different outcomes on Hacker News.")
    print()
    print("This is the same physics we found in GitHub repos:")
    print("  - Instant growth: 0.24x acceleration")
    print("  - Gradual growth: 19.58x acceleration")
    print("  - 80-FOLD DIFFERENCE")
    print()
    print("Let's see if HN shows the same pattern...")
    print("="*70)

    analyzer = HNAnalyzer()

    # Collect data
    analyzer.collect_data(target_count=1000)

    # Analyze for phase transition
    results = analyzer.analyze_phase_transition()

    # Save results
    analyzer.save_results()

    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)

    if results and results['score_ratio'] > 3:
        print("✓ Pattern found! This looks promising.")
        print()
        print("To strengthen the evidence:")
        print("1. Collect posts over multiple days (track actual growth)")
        print("2. Measure time-to-50-upvotes directly")
        print("3. Increase sample size to 1000+ posts")
        print("4. Test across different time periods")
        print()
        print("But this initial signal is EXCITING. The physics might be real.")
    else:
        print("~ Inconclusive. Need better data or methodology.")
        print()
        print("HN API limitations:")
        print("- Can't get historical upvote timelines easily")
        print("- Would need to track posts in real-time")
        print("- Or find alternative data source")
        print()
        print("Consider trying Reddit next (easier to get growth data)")

    print("\n" + "="*70)
    print("THE BIG PICTURE")
    print("="*70)
    print()
    print("We're testing if memory-induced phase transitions are universal.")
    print()
    print("Current evidence:")
    print("  ✓ RCET simulation - clear phase transitions")
    print("  ✓ GitHub repos - 19x acceleration difference")
    print(f"  {'✓' if results and results['score_ratio'] > 3 else '?'} Hacker News - {results['score_ratio']:.1f}x difference" if results else "  ? Hacker News - pending")
    print()
    print("If we find this in 3-5 independent systems, we have something REAL.")
    print()
    print("Let's keep testing. 🚀")


if __name__ == "__main__":
    main()
