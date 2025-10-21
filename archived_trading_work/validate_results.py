"""
Validate CASCADE Results
========================
Re-run backtests with the exact parameters from cascade_optimal_params.json
to verify the win rates match.
"""

import json
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def backtest_cascade(symbol, start_date, end_date, lookback, threshold, memory_thresh, volume_thresh):
    """Run backtest with specific parameters"""

    # Fetch data with buffer
    buffer_start = pd.to_datetime(start_date) - pd.Timedelta(days=250)
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=buffer_start, end=end_date)

    if len(data) < lookback + threshold + 50:
        return None

    # Find start index
    start_idx = None
    start_date_ts = pd.to_datetime(start_date).tz_localize(None) if pd.to_datetime(start_date).tz is None else pd.to_datetime(start_date)
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

            # Calculate memory factor
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

            # Check for CASCADE signal
            if memory_factor > memory_thresh:
                # Calculate volume surge
                recent_volume = np.mean(volumes[i-5:i+1])
                baseline_volume = np.mean(volumes[i-30:i-5])
                volume_surge = recent_volume / max(baseline_volume, 1)

                if volume_surge > volume_thresh:
                    position_open = True
                    entry_price = current_price
                    entry_date = current_date
        else:
            # Exit logic
            days_held = (current_date - entry_date).days
            pnl_pct = (current_price / entry_price - 1) * 100

            # Exit: 20 days, +30% profit, or -15% loss
            if days_held >= 20 or pnl_pct >= 30 or pnl_pct <= -15:
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct,
                    'days_held': days_held,
                    'win': pnl_pct > 0
                })
                position_open = False

    if not trades:
        return None

    winners = [t for t in trades if t['win']]
    win_rate = len(winners) / len(trades) * 100
    total_pnl = sum(t['pnl_pct'] for t in trades)

    return {
        'symbol': symbol,
        'trades': trades,
        'total_trades': len(trades),
        'winners': len(winners),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_pnl': total_pnl / len(trades)
    }


def main():
    # Load the optimal parameters
    with open('cascade_optimal_params.json', 'r') as f:
        params = json.load(f)

    print("="*70)
    print("CASCADE RESULTS VALIDATION")
    print("="*70)
    print("\nRe-running backtests with optimal parameters from json...\n")

    # Date ranges (adjust if needed)
    test_configs = {
        'COIN': ('2021-04-14', '2023-01-01'),
        'RIOT': ('2020-01-01', '2024-01-01'),  # Extended to 2024
        'PLTR': ('2020-09-30', '2023-01-01'),
        'NVDA': ('2020-01-01', '2023-01-01'),
        'META': ('2020-01-01', '2023-01-01')
    }

    results = []

    for asset_params in params['by_asset']:
        symbol = asset_params['symbol']
        p = asset_params['params']
        expected_wr = asset_params['win_rate']

        if symbol not in test_configs:
            continue

        start_date, end_date = test_configs[symbol]

        print(f"\n{symbol}:")
        print(f"  Parameters: lookback={p['lookback']}, threshold={p['threshold']}")
        print(f"              memory>{p['memory_thresh']}, volume>{p['volume_thresh']}")
        print(f"  Expected WR: {expected_wr:.1f}%")

        result = backtest_cascade(
            symbol, start_date, end_date,
            p['lookback'], p['threshold'],
            p['memory_thresh'], p['volume_thresh']
        )

        if result:
            print(f"  ACTUAL: {result['total_trades']} trades, {result['win_rate']:.1f}% WR")
            print(f"          {result['total_pnl']:.1f}% total PnL")

            match = "[MATCH]" if abs(result['win_rate'] - expected_wr) < 1 else "[MISMATCH]"
            print(f"  {match}")

            results.append(result)
        else:
            print(f"  No trades found")

    # Overall stats
    if results:
        print("\n" + "="*70)
        print("OVERALL RESULTS")
        print("="*70)
        total_trades = sum(r['total_trades'] for r in results)
        total_winners = sum(r['winners'] for r in results)
        overall_wr = total_winners / total_trades * 100

        print(f"Total trades: {total_trades}")
        print(f"Total winners: {total_winners}")
        print(f"Overall win rate: {overall_wr:.1f}%")
        print(f"Expected: 80.8%")

        match = "[MATCH]" if abs(overall_wr - 80.8) < 2 else "[MISMATCH]"
        print(f"{match}")


if __name__ == '__main__':
    main()
