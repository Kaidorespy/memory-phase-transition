"""
Analyze 2021 bull run - when everything was pumping
Look at well-known pump cases from that era
"""

import requests
import numpy as np
from datetime import datetime
import time

api_key = 'CG-V4yuyGiomS6zdAXvehCWqpxX'
headers = {'x-cg-pro-api-key': api_key}
base_url = 'https://api.coingecko.com/api/v3'

def analyze_2021_pattern(coin_id, name):
    """Get 2021 data and analyze pump patterns"""
    # Get data from Jan 2021 to Dec 2021
    url = f'{base_url}/coins/{coin_id}/market_chart/range'
    
    # 2021 timestamps
    from_timestamp = int(datetime(2021, 1, 1).timestamp())
    to_timestamp = int(datetime(2021, 12, 31).timestamp())
    
    params = {
        'vs_currency': 'usd',
        'from': from_timestamp,
        'to': to_timestamp
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return None
        
    data = response.json()
    prices = data.get('prices', [])
    
    if len(prices) < 30:
        return None
    
    # Convert to daily prices
    daily_prices = []
    for i in range(0, len(prices), 24):
        if i < len(prices):
            daily_prices.append(prices[i][1])
    
    if len(daily_prices) < 30:
        return None
    
    # Find first major pump (3x)
    for start_idx in range(len(daily_prices) - 30):
        start_price = daily_prices[start_idx]
        if start_price <= 0:
            continue
            
        # Look for 3x from this point
        for i in range(start_idx + 1, min(start_idx + 60, len(daily_prices))):
            if daily_prices[i] >= start_price * 3:
                days_to_3x = i - start_idx
                
                # Check what happened after
                if i + 30 < len(daily_prices):
                    price_at_3x = daily_prices[i]
                    price_30d_later = daily_prices[i + 30]
                    post_3x_change = ((price_30d_later / price_at_3x) - 1) * 100
                    
                    return {
                        'coin': name,
                        'days_to_3x': days_to_3x,
                        'post_3x_change': post_3x_change,
                        'category': 'instant' if days_to_3x <= 5 else 'gradual' if days_to_3x >= 20 else 'medium'
                    }
    
    return None

# 2021 bull run tokens that had significant moves
tokens_2021 = [
    # Memecoins that exploded
    ('shiba-inu', 'SHIBA'),
    ('dogecoin', 'DOGE'),
    ('safemoon', 'SafeMoon'),
    
    # Gaming tokens
    ('axie-infinity', 'AXS'),
    ('the-sandbox', 'SAND'),
    ('decentraland', 'MANA'),
    ('enjincoin', 'ENJ'),
    ('gala', 'GALA'),
    
    # Layer 1s that pumped
    ('solana', 'SOL'),
    ('avalanche-2', 'AVAX'),
    ('terra-luna', 'LUNA'),
    ('fantom', 'FTM'),
    ('harmony', 'ONE'),
    
    # DeFi tokens
    ('pancakeswap-token', 'CAKE'),
    ('uniswap', 'UNI'),
    ('sushi', 'SUSHI'),
    
    # Metaverse
    ('stepn', 'GMT'),
    ('illuvium', 'ILV'),
]

print("2021 BULL RUN ANALYSIS")
print("="*60)
print("Testing memory-induced phase transitions in 2021 crypto pumps\n")

results = []
for coin_id, name in tokens_2021:
    print(f"Analyzing {name} (2021 data)...")
    result = analyze_2021_pattern(coin_id, name)
    if result:
        print(f"  Days to 3x: {result['days_to_3x']}")
        print(f"  30d after 3x: {result['post_3x_change']:+.1f}%")
        results.append(result)
    else:
        print(f"  No clear 3x pattern found")
    time.sleep(0.5)

# Analyze results
print("\n" + "="*60)
print("2021 BULL RUN PATTERNS:")
print("="*60)

instant = [r for r in results if r['category'] == 'instant']
gradual = [r for r in results if r['category'] == 'gradual']

if instant:
    avg_instant = np.mean([r['post_3x_change'] for r in instant])
    print(f"\nINSTANT PUMPS (<5 days to 3x): {len(instant)} tokens")
    print(f"Average 30d after 3x: {avg_instant:+.1f}%")
    for r in instant:
        print(f"  {r['coin']}: {r['days_to_3x']}d -> {r['post_3x_change']:+.1f}%")

if gradual:
    avg_gradual = np.mean([r['post_3x_change'] for r in gradual])
    print(f"\nGRADUAL GROWTH (>20 days to 3x): {len(gradual)} tokens")
    print(f"Average 30d after 3x: {avg_gradual:+.1f}%")
    for r in gradual:
        print(f"  {r['coin']}: {r['days_to_3x']}d -> {r['post_3x_change']:+.1f}%")

if instant and gradual:
    diff = avg_gradual - avg_instant
    print(f"\n" + "="*60)
    print(f"THE 2021 VERDICT:")
    print(f"Instant pumps (<5 days): {avg_instant:+.1f}% after")
    print(f"Gradual growth (>20 days): {avg_gradual:+.1f}% after")
    print(f"DIFFERENCE: {diff:+.1f}%")
    
    if diff > 20:
        print("\n[!!!] PATTERN CONFIRMED IN 2021 BULL RUN!")
        print("Even in a bull market, instant pumps underperformed gradual growth")
        print("Memory accumulation matters even when everything is mooning!")
    elif diff < -20:
        print("\n[X] Pattern reversed in bull market")
    else:
        print("\n[?] Mixed results")

print("\n" + "="*60)
print("IMPLICATIONS:")
print("If pattern holds: Buy the slow grind, sell the instant pump")
print("Memory-induced phase transitions apply to crypto markets!")