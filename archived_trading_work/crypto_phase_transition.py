"""
Crypto Phase Transition Analysis
=================================
Testing if tokens that pump too fast crystallize and die,
while gradual growth tokens can moon later.

Holy shit this could be huge.
"""

import requests
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

class CryptoMemoryAnalyzer:
    def __init__(self, api_key: str = None):
        """Initialize with CoinGecko API"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {}
        if api_key:
            self.headers['x-cg-pro-api-key'] = api_key
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_token_list(self, category: str = None):
        """Get list of tokens to analyze"""
        # Get tokens sorted by market cap
        url = f"{self.base_url}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': 1,
            'sparkline': False
        }
        
        if category:
            params['category'] = category
            
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    
    def get_historical_data(self, coin_id: str, days: int = 365):
        """Get historical price data for a token"""
        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            # Returns {'prices': [[timestamp, price], ...]}
            return data.get('prices', [])
        return []
    
    def analyze_growth_pattern(self, coin_id: str, coin_name: str):
        """Analyze a single token's growth pattern"""
        print(f"  Analyzing {coin_name} ({coin_id})...")
        
        # Get historical data
        prices = self.get_historical_data(coin_id, days=365)
        
        if len(prices) < 30:
            print(f"    Insufficient data ({len(prices)} days)")
            return None
            
        # Find first significant pump (2x from starting price)
        start_price = prices[0][1]
        if start_price <= 0:
            return None
            
        # Look for 10x moment
        days_to_10x = None
        for i, (timestamp, price) in enumerate(prices):
            if price >= start_price * 10:
                days_to_10x = i
                break
                
        if not days_to_10x:
            print(f"    Never reached 10x")
            return None
            
        # Measure what happened after 10x
        if days_to_10x < len(prices) - 30:  # Need 30 days after
            price_at_10x = prices[days_to_10x][1]
            price_30d_later = prices[min(days_to_10x + 30, len(prices)-1)][1]
            price_now = prices[-1][1]
            
            # Calculate "acceleration" - did it keep pumping or dump?
            post_10x_change = (price_30d_later / price_at_10x - 1) * 100
            total_change = (price_now / start_price - 1) * 100
            
            result = {
                'coin': coin_name,
                'coin_id': coin_id,
                'days_to_10x': days_to_10x,
                'post_10x_change': post_10x_change,
                'total_change': total_change,
                'current_price': price_now,
                'category': 'instant' if days_to_10x <= 7 else 'gradual' if days_to_10x >= 30 else 'medium'
            }
            
            print(f"    Days to 10x: {days_to_10x}")
            print(f"    30d after 10x: {post_10x_change:+.1f}%")
            
            return result
        
        return None
    
    def analyze_multiple_tokens(self, limit: int = 50):
        """Analyze multiple tokens"""
        print("Fetching token list...")
        
        # Get mix of tokens - established and newer ones
        all_tokens = []
        
        # Get top 100-200 by market cap (not top 100 as they're too established)
        tokens = self.get_token_list()
        interesting_tokens = tokens[100:200]  # Skip BTC, ETH, etc.
        
        results = []
        analyzed = 0
        
        for token in interesting_tokens:
            if analyzed >= limit:
                break
                
            coin_id = token['id']
            coin_name = token['name']
            
            # Skip stablecoins
            if 'usd' in coin_id.lower() or 'tether' in coin_id.lower():
                continue
                
            result = self.analyze_growth_pattern(coin_id, coin_name)
            if result:
                results.append(result)
                analyzed += 1
                
            time.sleep(1)  # Rate limiting
            
        return results
    
    def summarize_findings(self, results: List[Dict]):
        """Summarize the patterns found"""
        if not results:
            print("\nNo results to analyze")
            return
            
        print("\n" + "="*70)
        print("CRYPTO MEMORY-INDUCED PHASE TRANSITION ANALYSIS")
        print("="*70)
        
        # Group by speed to 10x
        instant = [r for r in results if r['category'] == 'instant']
        gradual = [r for r in results if r['category'] == 'gradual']
        medium = [r for r in results if r['category'] == 'medium']
        
        print(f"\nTokens analyzed: {len(results)}")
        print(f"Instant pumps (<7 days to 10x): {len(instant)}")
        print(f"Gradual growth (>30 days to 10x): {len(gradual)}")
        
        if instant:
            avg_post_pump = np.mean([r['post_10x_change'] for r in instant])
            print(f"\n[INSTANT PUMPS]")
            print(f"Average 30d performance after 10x: {avg_post_pump:+.1f}%")
            for r in instant[:5]:
                print(f"  {r['coin']}: {r['days_to_10x']}d to 10x -> {r['post_10x_change']:+.1f}% after")
                
        if gradual:
            avg_post_gradual = np.mean([r['post_10x_change'] for r in gradual])
            print(f"\n[GRADUAL GROWTH]")
            print(f"Average 30d performance after 10x: {avg_post_gradual:+.1f}%")
            for r in gradual[:5]:
                print(f"  {r['coin']}: {r['days_to_10x']}d to 10x -> {r['post_10x_change']:+.1f}% after")
                
        # The moment of truth
        if instant and gradual:
            difference = avg_post_gradual - avg_post_pump
            print(f"\n" + "="*70)
            print(f"THE PATTERN TEST:")
            print(f"Instant pumps post-10x performance: {avg_post_pump:+.1f}%")
            print(f"Gradual growth post-10x performance: {avg_post_gradual:+.1f}%")
            print(f"DIFFERENCE: {difference:+.1f}%")
            
            if difference > 20:
                print("\n[!!!] PATTERN CONFIRMED: Gradual growth outperforms pumps!")
                print("Tokens that pump too fast tend to dump.")
                print("Tokens that grow gradually can keep mooning.")
            elif difference < -20:
                print("\n[X] INVERSE: Instant pumps keep pumping?!")
            else:
                print("\n[?] No clear pattern in this sample")
                
        return results


def main():
    """Test the crypto phase transition hypothesis"""
    
    print("="*70)
    print("TESTING MEMORY-INDUCED PHASE TRANSITIONS IN CRYPTO")
    print("="*70)
    print("\nHypothesis: Tokens that pump too fast (instant 10x) will")
    print("crystallize and dump, while gradual growth tokens can moon.\n")
    
    # Initialize analyzer
    api_key = 'CG-V4yuyGiomS6zdAXvehCWqpxX'
    
    analyzer = CryptoMemoryAnalyzer(api_key=api_key)
    
    # Analyze tokens
    print("Analyzing token growth patterns...")
    print("(This may take a few minutes due to rate limits)\n")
    
    results = analyzer.analyze_multiple_tokens(limit=30)
    
    # Summarize findings
    analyzer.summarize_findings(results)
    
    # Save results
    if results:
        with open('crypto_phase_transition_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to crypto_phase_transition_results.json")
        
    print("\n" + "="*70)
    print("IMPLICATIONS IF PATTERN HOLDS:")
    print("="*70)
    print("1. Avoid tokens that 10x in <7 days (will dump)")
    print("2. Look for steady growers (30+ days to 10x)")  
    print("3. Memory accumulation matters in crypto too")
    print("4. FOMO literally kills gains")
    print("\nThis could be a money printer if true...")


if __name__ == "__main__":
    main()