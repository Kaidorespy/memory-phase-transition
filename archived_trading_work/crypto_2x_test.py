"""
Test with 2x moves instead of 10x (more common)
Look at recent launches that had clear pumps
"""

import requests
import numpy as np
from datetime import datetime
import time

api_key = 'CG-V4yuyGiomS6zdAXvehCWqpxX'
headers = {'x-cg-pro-api-key': api_key}
base_url = 'https://api.coingecko.com/api/v3'

def analyze_2x_pattern(coin_id, name):
    """Look for 2x pattern instead of 10x"""
    url = f'{base_url}/coins/{coin_id}/market_chart'
    params = {'vs_currency': 'usd', 'days': 180}  # 6 months
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return None
        
    data = response.json()
    prices = data.get('prices', [])
    
    if len(prices) < 30:
        return None
        
    # Convert to daily prices (roughly)
    daily_prices = []
    for i in range(0, len(prices), 24):  # Sample every 24 hours worth
        if i < len(prices):
            daily_prices.append(prices[i][1])
    
    if len(daily_prices) < 10:
        return None
        
    # Find first 2x move
    start_price = daily_prices[0]
    days_to_2x = None
    
    for i, price in enumerate(daily_prices):
        if price >= start_price * 2:
            days_to_2x = i
            break
    
    if not days_to_2x or days_to_2x >= len(daily_prices) - 15:
        return None
        
    # Check what happened after 2x
    price_at_2x = daily_prices[days_to_2x]
    price_15d_later = daily_prices[min(days_to_2x + 15, len(daily_prices)-1)]
    
    post_2x_change = ((price_15d_later / price_at_2x) - 1) * 100
    
    return {
        'coin': name,
        'days_to_2x': days_to_2x,
        'post_2x_change': post_2x_change,
        'category': 'instant' if days_to_2x <= 3 else 'gradual' if days_to_2x >= 15 else 'medium'
    }

# Get recent trending coins
def get_trending_coins():
    """Get currently trending coins (more likely to have recent moves)"""
    url = f'{base_url}/search/trending'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        coins = []
        for item in data.get('coins', [])[:15]:  # Top 15 trending
            coin = item.get('item', {})
            coins.append((coin.get('id'), coin.get('name')))
        return coins
    return []

print("CRYPTO 2X PATTERN TEST")
print("="*60)
print("Testing if tokens that 2x quickly tend to dump vs gradual growth\n")

# Get trending coins
print("Fetching trending coins...")
trending = get_trending_coins()

if not trending:
    # Fallback to known volatile coins
    trending = [
        ('pepe', 'PEPE'),
        ('bonk', 'BONK'),
        ('worldcoin-wld', 'WLD'),
        ('injective-protocol', 'INJ'),
        ('sei-network', 'SEI'),
    ]

results = []
for coin_id, name in trending[:10]:
    if not coin_id:
        continue
    print(f"\nAnalyzing {name}...")
    result = analyze_2x_pattern(coin_id, name)
    if result:
        print(f"  Days to 2x: {result['days_to_2x']}")
        print(f"  15d after 2x: {result['post_2x_change']:+.1f}%")
        results.append(result)
    else:
        print(f"  No 2x found or insufficient data")
    time.sleep(0.5)

# Test some known recent pumpers
recent_pumpers = [
    ('worldcoin-wld', 'Worldcoin'),
    ('arkham', 'Arkham'),
    ('sei-network', 'SEI'),
    ('cyber', 'Cyber'),
    ('pendle', 'Pendle'),
]

print("\n\nTesting recent launches...")
for coin_id, name in recent_pumpers:
    print(f"\nAnalyzing {name}...")
    result = analyze_2x_pattern(coin_id, name)
    if result:
        print(f"  Days to 2x: {result['days_to_2x']}")
        print(f"  15d after 2x: {result['post_2x_change']:+.1f}%")
        results.append(result)
    else:
        print(f"  No 2x found or insufficient data")
    time.sleep(0.5)

# Analyze results
print("\n" + "="*60)
print("RESULTS SUMMARY:")
print("="*60)

instant = [r for r in results if r['category'] == 'instant']
gradual = [r for r in results if r['category'] == 'gradual']
medium = [r for r in results if r['category'] == 'medium']

if instant:
    avg_instant = np.mean([r['post_2x_change'] for r in instant])
    print(f"\nINSTANT PUMPS (<3 days to 2x): {len(instant)} tokens")
    print(f"Average 15d after 2x: {avg_instant:+.1f}%")
    for r in instant:
        print(f"  {r['coin']}: {r['days_to_2x']}d -> {r['post_2x_change']:+.1f}%")

if gradual:
    avg_gradual = np.mean([r['post_2x_change'] for r in gradual])
    print(f"\nGRADUAL GROWTH (>15 days to 2x): {len(gradual)} tokens")
    print(f"Average 15d after 2x: {avg_gradual:+.1f}%")
    for r in gradual:
        print(f"  {r['coin']}: {r['days_to_2x']}d -> {r['post_2x_change']:+.1f}%")

if medium:
    avg_medium = np.mean([r['post_2x_change'] for r in medium])
    print(f"\nMEDIUM (3-15 days to 2x): {len(medium)} tokens")
    print(f"Average 15d after 2x: {avg_medium:+.1f}%")

if instant and gradual:
    diff = avg_gradual - avg_instant
    print(f"\n" + "="*60)
    print("THE VERDICT:")
    print(f"Instant pumps (< 3 days): {avg_instant:+.1f}% after")
    print(f"Gradual growth (>15 days): {avg_gradual:+.1f}% after")
    print(f"DIFFERENCE: {diff:+.1f}%")
    
    if diff > 10:
        print("\n[!!!] PATTERN CONFIRMED FOR CRYPTO!")
        print("Tokens that pump too fast tend to dump.")
        print("Gradual growers keep climbing.")
    elif diff < -10:
        print("\n[X] Opposite pattern in crypto?!")
    else:
        print("\n[?] No clear pattern")
        
print("\nImplication: Quick pumps = quick dumps. Slow growth = sustained gains.")
print("Memory accumulation matters in crypto too!")