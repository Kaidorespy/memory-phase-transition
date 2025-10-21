"""
Quick test with known pump tokens
"""

import requests
import numpy as np
from datetime import datetime

api_key = 'CG-V4yuyGiomS6zdAXvehCWqpxX'
headers = {'x-cg-pro-api-key': api_key}
base_url = 'https://api.coingecko.com/api/v3'

def analyze_token(coin_id, name):
    """Analyze a specific token"""
    # Get 1 year of data
    url = f'{base_url}/coins/{coin_id}/market_chart'
    params = {'vs_currency': 'usd', 'days': 365}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return None
        
    data = response.json()
    prices = data.get('prices', [])
    
    if len(prices) < 30:
        return None
        
    # Extract just prices
    price_values = [p[1] for p in prices]
    
    # Find first 10x from lowest point
    min_price = min(price_values[:30])  # Min in first month
    min_idx = price_values.index(min_price)
    
    # Look for 10x from that point
    days_to_10x = None
    for i in range(min_idx, len(price_values)):
        if price_values[i] >= min_price * 10:
            days_to_10x = i - min_idx
            break
    
    if not days_to_10x:
        return None
        
    # What happened after 10x?
    idx_10x = min_idx + days_to_10x
    if idx_10x + 30 < len(price_values):
        price_at_10x = price_values[idx_10x]
        price_30d_later = price_values[idx_10x + 30]
        post_10x_change = ((price_30d_later / price_at_10x) - 1) * 100
        
        return {
            'coin': name,
            'days_to_10x': days_to_10x,
            'post_10x_change': post_10x_change,
            'category': 'instant' if days_to_10x <= 7 else 'gradual' if days_to_10x >= 30 else 'medium'
        }
    
    return None

# Test with tokens known to have pumped
test_tokens = [
    # Meme coins that pumped
    ('pepe', 'PEPE'),
    ('shiba-inu', 'SHIBA'),
    ('dogecoin', 'DOGE'),
    ('bonk', 'BONK'),
    ('floki', 'FLOKI'),
    
    # AI tokens that grew
    ('render-token', 'RNDR'),
    ('fetch-ai', 'FET'),
    ('singularitynet', 'AGIX'),
    
    # Gaming tokens
    ('axie-infinity', 'AXS'),
    ('the-sandbox', 'SAND'),
    ('decentraland', 'MANA'),
    
    # Layer 2s
    ('arbitrum', 'ARB'),
    ('optimism', 'OP'),
    
    # Established but had runs
    ('solana', 'SOL'),
    ('avalanche-2', 'AVAX'),
    ('matic-network', 'MATIC'),
]

print("CRYPTO PHASE TRANSITION - QUICK TEST")
print("="*60)

results = []
for coin_id, name in test_tokens:
    print(f"\nAnalyzing {name}...")
    result = analyze_token(coin_id, name)
    if result:
        print(f"  Days to 10x: {result['days_to_10x']}")
        print(f"  Post-10x change: {result['post_10x_change']:+.1f}%")
        results.append(result)
    else:
        print(f"  No 10x found or insufficient data")

# Summarize
print("\n" + "="*60)
print("SUMMARY:")

instant = [r for r in results if r['category'] == 'instant']
gradual = [r for r in results if r['category'] == 'gradual']

if instant:
    avg_instant = np.mean([r['post_10x_change'] for r in instant])
    print(f"\nInstant pumps (<7 days to 10x): {len(instant)} tokens")
    print(f"  Average post-10x: {avg_instant:+.1f}%")
    for r in instant:
        print(f"    {r['coin']}: {r['days_to_10x']}d -> {r['post_10x_change']:+.1f}%")

if gradual:
    avg_gradual = np.mean([r['post_10x_change'] for r in gradual])
    print(f"\nGradual growth (>30 days to 10x): {len(gradual)} tokens")
    print(f"  Average post-10x: {avg_gradual:+.1f}%")
    for r in gradual:
        print(f"    {r['coin']}: {r['days_to_10x']}d -> {r['post_10x_change']:+.1f}%")

if instant and gradual:
    diff = avg_gradual - avg_instant
    print(f"\n" + "="*60)
    print(f"PATTERN TEST:")
    print(f"Instant pumps: {avg_instant:+.1f}% after 10x")
    print(f"Gradual growth: {avg_gradual:+.1f}% after 10x")
    print(f"Difference: {diff:+.1f}%")
    
    if diff > 20:
        print("\n[!!!] PATTERN HOLDS: Gradual growth keeps mooning!")
    elif diff < -20:
        print("\n[X] Inverse: Instant pumps keep going?!")
    else:
        print("\n[?] Mixed results")