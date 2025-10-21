"""
Alternating Year Training/Testing
==================================
Train on 2020+2022, test on 2021+2023, final validation on 2024

This tests if asset-specific parameters are capturing real regime differences
or just overfitting to specific periods.

Logic: If physics is real but assets have different volatility profiles,
       then training on 2020+2022 should generalize to 2021+2023
"""

import pandas as pd
import numpy as np
import yfinance as yf
from itertools import product
from datetime import datetime


class AlternatingYearTest:
    """Train on even years, test on odd years"""

    def __init__(self):
        self.lookback_range = [20, 30, 40, 50]
        self.threshold_range = [3, 5, 7, 10]
        self.memory_range = [1.0, 1.25, 1.5, 1.75, 2.0]
        self.volume_range = [1.5, 2.0, 2.5, 3.0]

    def get_year_ranges(self, symbol, ipo_date=None):
        """Get date ranges for training/testing"""

        # Adjust for IPO dates
        if ipo_date:
            base_start = max(pd.to_datetime('2020-01-01'), pd.to_datetime(ipo_date))
        else:
            base_start = pd.to_datetime('2020-01-01')

        # Training: 2020 + 2022 (even years)
        train_ranges = []
        if base_start <= pd.to_datetime('2020-12-31'):
            train_ranges.append(('2020-01-01', '2020-12-31'))
        train_ranges.append(('2022-01-01', '2022-12-31'))

        # Testing: 2021 + 2023 (odd years)
        test_ranges = []
        if base_start <= pd.to_datetime('2021-01-01'):
            test_ranges.append(('2021-01-01', '2021-12-31'))
        test_ranges.append(('2023-01-01', '2023-12-31'))

        # Validation: 2024
        validation_ranges = [('2024-01-01', '2024-12-31')]

        return train_ranges, test_ranges, validation_ranges

    def backtest_periods(self, symbol, date_ranges, lookback, threshold, memory_thresh, volume_thresh):
        """Run backtest across multiple date ranges"""

        all_trades = []

        for start_date, end_date in date_ranges:
            trades = self.backtest_single_period(
                symbol, start_date, end_date,
                lookback, threshold, memory_thresh, volume_thresh
            )
            all_trades.extend(trades)

        if len(all_trades) == 0:
            return None

        df = pd.DataFrame(all_trades)
        winners = df[df['pnl_pct'] > 0]

        return {
            'total_trades': len(df),
            'winners': len(winners),
            'win_rate': len(winners) / len(df) * 100,
            'total_pnl': df['pnl_pct'].sum(),
            'avg_pnl': df['pnl_pct'].mean(),
            'trades': all_trades
        }

    def backtest_single_period(self, symbol, start_date, end_date, lookback, threshold, memory_thresh, volume_thresh):
        """Backtest a single time period"""

        # Fetch data with buffer
        buffer_start = pd.to_datetime(start_date) - pd.Timedelta(days=250)
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=buffer_start, end=end_date)

        if len(data) < lookback + threshold + 50:
            return []

        # Find start index
        start_idx = None
        start_date_ts = pd.to_datetime(start_date).tz_localize(None)
        for i, date in enumerate(data.index):
            date_naive = date.tz_localize(None) if date.tz is not None else date
            if date_naive >= start_date_ts:
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
                        'pnl_pct': pnl_pct,
                        'days_held': days_held
                    })
                    position_open = False

        return trades

    def optimize_on_training(self, symbol, train_ranges):
        """Find best parameters on training data"""

        print(f"\n{'='*70}")
        print(f"TRAINING: {symbol}")
        print(f"{'='*70}")
        print(f"Training periods: {train_ranges}")

        best_result = None
        best_params = None
        tested = 0

        for lookback, threshold, memory, volume in product(
            self.lookback_range, self.threshold_range,
            self.memory_range, self.volume_range
        ):
            if lookback <= threshold:
                continue

            result = self.backtest_periods(
                symbol, train_ranges,
                lookback, threshold, memory, volume
            )

            if result and result['total_trades'] >= 3:
                tested += 1

                if not best_result or result['win_rate'] > best_result['win_rate']:
                    best_result = result
                    best_params = {
                        'lookback': lookback,
                        'threshold': threshold,
                        'memory_thresh': memory,
                        'volume_thresh': volume
                    }

                if tested % 50 == 0:
                    print(f"  Tested {tested} combinations...")

        if best_result:
            print(f"\nBest parameters found:")
            print(f"  L{best_params['lookback']}/T{best_params['threshold']}, " +
                  f"M>{best_params['memory_thresh']}, V>{best_params['volume_thresh']}")
            print(f"  Training: {best_result['total_trades']} trades, " +
                  f"{best_result['win_rate']:.1f}% WR, {best_result['total_pnl']:.1f}% total PnL")

        return best_params, best_result

    def test_on_validation(self, symbol, test_ranges, params, label="Test"):
        """Test optimized parameters on held-out data"""

        result = self.backtest_periods(
            symbol, test_ranges,
            params['lookback'], params['threshold'],
            params['memory_thresh'], params['volume_thresh']
        )

        if result:
            print(f"\n{label} periods: {test_ranges}")
            print(f"  {result['total_trades']} trades, " +
                  f"{result['win_rate']:.1f}% WR, {result['total_pnl']:.1f}% total PnL")
        else:
            print(f"\n{label}: No trades")

        return result


def main():
    """Run alternating year test"""

    print("="*70)
    print("ALTERNATING YEAR TRAINING/TESTING")
    print("="*70)
    print("Train: 2020 + 2022 (even years)")
    print("Test:  2021 + 2023 (odd years)")
    print("Final: 2024 (holdout)")
    print()
    print("Hypothesis: If asset-specific params capture real volatility differences,")
    print("            they should generalize across different years")
    print("="*70)

    tester = AlternatingYearTest()

    # Test on non-crypto stocks
    test_stocks = [
        ('PLTR', '2020-09-30'),
        ('META', None),
        ('NVDA', None),
        # Excluding COIN and RIOT (crypto-related)
    ]

    all_results = []

    for symbol, ipo_date in test_stocks:
        train_ranges, test_ranges, validation_ranges = tester.get_year_ranges(symbol, ipo_date)

        # Step 1: Optimize on training data
        best_params, train_result = tester.optimize_on_training(symbol, train_ranges)

        if not best_params:
            print(f"  Could not find valid parameters for {symbol}")
            continue

        # Step 2: Test on odd years (2021+2023)
        test_result = tester.test_on_validation(symbol, test_ranges, best_params, "Test (2021+2023)")

        # Step 3: Validate on 2024
        validation_result = tester.test_on_validation(symbol, validation_ranges, best_params, "Validation (2024)")

        all_results.append({
            'symbol': symbol,
            'params': best_params,
            'train': train_result,
            'test': test_result,
            'validation': validation_result
        })

        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)

    for r in all_results:
        print(f"\n{r['symbol']}:")
        print(f"  Params: L{r['params']['lookback']}/T{r['params']['threshold']}, " +
              f"M>{r['params']['memory_thresh']}, V>{r['params']['volume_thresh']}")

        if r['train']:
            print(f"  Train (2020+2022): {r['train']['total_trades']} trades, {r['train']['win_rate']:.1f}% WR")

        if r['test']:
            print(f"  Test  (2021+2023): {r['test']['total_trades']} trades, {r['test']['win_rate']:.1f}% WR")
            if r['train']:
                wr_diff = r['test']['win_rate'] - r['train']['win_rate']
                print(f"    Win rate change: {wr_diff:+.1f}%")

        if r['validation']:
            print(f"  Valid (2024):      {r['validation']['total_trades']} trades, {r['validation']['win_rate']:.1f}% WR")

    # Overall stats
    print(f"\n{'='*70}")
    print("AGGREGATE RESULTS")
    print("="*70)

    # Combine all test results
    test_trades = sum(r['test']['total_trades'] for r in all_results if r['test'])
    test_winners = sum(r['test']['winners'] for r in all_results if r['test'])

    # Combine all validation results
    val_trades = sum(r['validation']['total_trades'] for r in all_results if r['validation'])
    val_winners = sum(r['validation']['winners'] for r in all_results if r['validation'])

    if test_trades > 0:
        test_wr = test_winners / test_trades * 100
        print(f"Test (2021+2023):  {test_trades} trades, {test_wr:.1f}% WR")

    if val_trades > 0:
        val_wr = val_winners / val_trades * 100
        print(f"Validation (2024): {val_trades} trades, {val_wr:.1f}% WR")

    print("\nInterpretation:")
    if test_trades > 0 and test_wr >= 65:
        print("[+] Parameters generalize well across years")
        print("[+] Asset-specific optimization appears valid")
    elif test_trades > 0 and test_wr >= 55:
        print("[~] Moderate generalization")
        print("[~] Some overfitting, but edge remains")
    else:
        print("[-] Poor generalization")
        print("[-] Likely overfitting to training years")


if __name__ == "__main__":
    main()
