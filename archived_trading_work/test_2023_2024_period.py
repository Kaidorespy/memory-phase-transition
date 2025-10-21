"""
Test CASCADE on 2023-2024 period
Maybe ghost-us combined multiple periods?
"""

import json
import pandas as pd
import numpy as np
import yfinance as yf

def backtest_cascade(symbol, start_date, end_date, lookback, threshold, memory_thresh, volume_thresh):
    """Run backtest with specific parameters"""

    buffer_start = pd.to_datetime(start_date) - pd.Timedelta(days=250)
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=buffer_start, end=end_date)

    if len(data) < lookback + threshold + 50:
        return None

    start_idx = None
    start_date_ts = pd.to_datetime(start_date)
    for i, date in enumerate(data.index):
        date_naive = date.tz_localize(None) if date.tz is not None else date
        start_date_naive = start_date_ts.tz_localize(None) if start_date_ts.tz is not None else start_date_ts
        if date_naive >= start_date_naive:
            start_idx = i
            break

    if not start_idx or start_idx < lookback + threshold:
        start_idx = lookback + threshold

    prices = data['Close'].values
    volumes = data['Volume'].values
    dates = data.index

    trades = []
    position_open = False
    entry_price = 0
    entry_date = None

    for i in range(start_idx, len(prices) - 1):
        current_price = prices[i]
        current_date = dates[i]

        if not position_open:
            if i < lookback + threshold:
                continue

            recent_start = i - threshold
            recent_return = (prices[i] / prices[recent_start]) - 1
            recent_daily_rate = recent_return / threshold

            baseline_start = i - lookback
            baseline_end = i - threshold
            baseline_return = (prices[baseline_end] / prices[baseline_start]) - 1
            baseline_daily_rate = baseline_return / (lookback - threshold)

            if baseline_daily_rate <= 0:
                continue

            memory_factor = recent_daily_rate / baseline_daily_rate

            if memory_factor > memory_thresh:
                recent_volume = np.mean(volumes[i-5:i+1])
                baseline_volume = np.mean(volumes[i-30:i-5])
                volume_surge = recent_volume / max(baseline_volume, 1)

                if volume_surge > volume_thresh:
                    position_open = True
                    entry_price = current_price
                    entry_date = current_date
        else:
            days_held = (current_date - entry_date).days
            pnl_pct = (current_price / entry_price - 1) * 100

            if days_held >= 20 or pnl_pct >= 30 or pnl_pct <= -15:
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'pnl_pct': pnl_pct,
                    'days_held': days_held,
                    'win': pnl_pct > 0
                })
                position_open = False

    return trades


# Load optimal params
with open('cascade_optimal_params.json', 'r') as f:
    params = json.load(f)

print("="*70)
print("CASCADE TEST: 2023-2024 PERIOD")
print("="*70)

test_configs_2023_24 = {
    'COIN': ('2023-01-01', '2025-01-01'),
    'RIOT': ('2023-01-01', '2025-01-01'),
    'PLTR': ('2023-01-01', '2025-01-01'),
    'NVDA': ('2023-01-01', '2025-01-01'),
    'META': ('2023-01-01', '2025-01-01')
}

all_results = {}

for asset_params in params['by_asset']:
    symbol = asset_params['symbol']
    p = asset_params['params']

    if symbol not in test_configs_2023_24:
        continue

    start_date, end_date = test_configs_2023_24[symbol]

    print(f"\n{symbol} (2023-2024):")

    trades = backtest_cascade(
        symbol, start_date, end_date,
        p['lookback'], p['threshold'],
        p['memory_thresh'], p['volume_thresh']
    )

    if trades and len(trades) > 0:
        winners = [t for t in trades if t['win']]
        win_rate = len(winners) / len(trades) * 100
        print(f"  {len(trades)} trades, {win_rate:.1f}% WR")
        all_results[symbol] = {'trades': len(trades), 'wr': win_rate, 'period': '2023-24'}
    else:
        print(f"  No trades found")
        all_results[symbol] = {'trades': 0, 'wr': 0, 'period': '2023-24'}

print("\n" + "="*70)
print("WHAT IF GHOST-US COMBINED 2020-2023 + 2023-2024?")
print("="*70)

# Original results from 2020-2023
original_results = {
    'COIN': {'trades': 3, 'wr': 66.7, 'period': '2020-23'},
    'RIOT': {'trades': 8, 'wr': 87.5, 'period': '2020-22'},
    'PLTR': {'trades': 4, 'wr': 75.0, 'period': '2020-23'},
    'NVDA': {'trades': 4, 'wr': 75.0, 'period': '2020-23'},
    'META': {'trades': 3, 'wr': 100.0, 'period': '2020-23'}
}

for symbol in ['COIN', 'RIOT', 'PLTR', 'NVDA', 'META']:
    orig = original_results[symbol]
    new = all_results.get(symbol, {'trades': 0, 'wr': 0})

    total_trades = orig['trades'] + new['trades']

    print(f"\n{symbol}:")
    print(f"  2020-2023: {orig['trades']} trades")
    print(f"  2023-2024: {new['trades']} trades")
    print(f"  COMBINED: {total_trades} trades")

    if symbol == 'RIOT' and total_trades == 14:
        print(f"  *** THIS MATCHES THE DOCS (14 trades)! ***")
