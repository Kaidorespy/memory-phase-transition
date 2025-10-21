"""
CASCADE-Only Parameter Optimization
====================================
Since CASCADE signals are the real edge, let's optimize specifically for them.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from itertools import product
import json


class CascadeOptimizer:
    """Optimize parameters specifically for CASCADE (long) signals"""
    
    def test_parameters(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        lookback: int,
        threshold: int,
        memory_thresh: float,
        volume_thresh: float
    ) -> dict:
        """Test specific parameter combination for CASCADE signals only"""
        
        # Fetch data
        ticker = yf.Ticker(symbol)
        buffer_start = pd.to_datetime(start_date) - pd.Timedelta(days=250)
        data = ticker.history(start=buffer_start, end=end_date)
        
        if len(data) < lookback + threshold + 50:
            return None
            
        # Find start index
        start_idx = None
        start_date_ts = pd.to_datetime(start_date).tz_localize(None)
        for i, date in enumerate(data.index):
            if date.tz_localize(None) >= start_date_ts:
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
                # Calculate memory factor
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
                
                # Check for CASCADE signal
                if memory_factor > memory_thresh:
                    # Calculate volume surge
                    recent_volume = np.mean(volumes[i-5:i])
                    baseline_volume = np.mean(volumes[i-30:i-5])
                    volume_surge = recent_volume / max(baseline_volume, 1)
                    
                    # CASCADE signal (volume surge)
                    if volume_surge > volume_thresh:
                        position_open = True
                        entry_price = current_price
                        entry_date = current_date
            else:
                # Exit logic
                days_held = (current_date - entry_date).days
                pnl_pct = (current_price / entry_price - 1) * 100
                
                # Simple exit: 20 days, +30% profit, or -15% loss
                if days_held >= 20 or pnl_pct >= 30 or pnl_pct <= -15:
                    trades.append({
                        'pnl_pct': pnl_pct,
                        'days_held': days_held
                    })
                    position_open = False
                    entry_price = 0
                    entry_date = None
        
        if len(trades) < 3:  # Need minimum trades for validity
            return None
            
        # Calculate metrics
        df = pd.DataFrame(trades)
        winners = df[df['pnl_pct'] > 0]
        
        return {
            'params': {
                'lookback': lookback,
                'threshold': threshold,
                'memory_thresh': memory_thresh,
                'volume_thresh': volume_thresh
            },
            'total_trades': len(df),
            'win_rate': len(winners) / len(df) * 100,
            'avg_pnl': df['pnl_pct'].mean(),
            'total_pnl': df['pnl_pct'].sum(),
            'sharpe': df['pnl_pct'].mean() / (df['pnl_pct'].std() + 0.001),
            'max_win': df['pnl_pct'].max(),
            'max_loss': df['pnl_pct'].min(),
            'avg_days': df['days_held'].mean()
        }
    
    def sweep(self, symbol: str, start_date: str, end_date: str):
        """Sweep parameters for CASCADE optimization"""
        
        print(f"\nSweeping CASCADE parameters for {symbol}")
        print("-" * 50)
        
        # Parameter ranges (focused on CASCADE)
        lookback_range = [20, 30, 40, 50]
        threshold_range = [3, 5, 7, 10]
        memory_range = [1.0, 1.25, 1.5, 1.75, 2.0]
        volume_range = [1.5, 2.0, 2.5, 3.0]
        
        best_by_wr = None
        best_by_pnl = None
        best_by_sharpe = None
        
        results = []
        total_combos = len(lookback_range) * len(threshold_range) * len(memory_range) * len(volume_range)
        tested = 0
        
        for lookback, threshold, memory, volume in product(
            lookback_range, threshold_range, memory_range, volume_range
        ):
            if lookback <= threshold:
                continue
                
            result = self.test_parameters(
                symbol, start_date, end_date,
                lookback, threshold, memory, volume
            )
            
            if result:
                results.append(result)
                
                # Track best
                if not best_by_wr or result['win_rate'] > best_by_wr['win_rate']:
                    best_by_wr = result
                if not best_by_pnl or result['total_pnl'] > best_by_pnl['total_pnl']:
                    best_by_pnl = result
                if not best_by_sharpe or result['sharpe'] > best_by_sharpe['sharpe']:
                    best_by_sharpe = result
                
                tested += 1
                if tested % 20 == 0:
                    print(f"  Tested {tested} combinations...")
        
        return {
            'symbol': symbol,
            'best_by_wr': best_by_wr,
            'best_by_pnl': best_by_pnl,
            'best_by_sharpe': best_by_sharpe,
            'all_results': results
        }


def main():
    """Run CASCADE parameter optimization"""
    
    print("="*70)
    print("CASCADE-ONLY PARAMETER OPTIMIZATION")
    print("="*70)
    print("Finding optimal parameters for the signals that work\n")
    
    optimizer = CascadeOptimizer()
    
    # Test on winners
    test_configs = [
        ('COIN', '2021-04-14', '2023-01-01'),
        ('RIOT', '2020-01-01', '2022-01-01'),
        ('PLTR', '2020-09-30', '2023-01-01'),
        ('NVDA', '2020-01-01', '2023-01-01'),
        ('META', '2020-01-01', '2023-01-01')
    ]
    
    all_best = []
    
    for symbol, start, end in test_configs:
        results = optimizer.sweep(symbol, start, end)
        
        if results['best_by_wr']:
            print(f"\n{symbol} Best by Win Rate:")
            best = results['best_by_wr']
            print(f"  Parameters: L{best['params']['lookback']}/T{best['params']['threshold']}")
            print(f"              Memory>{best['params']['memory_thresh']}, Volume>{best['params']['volume_thresh']}")
            print(f"  Performance: {best['win_rate']:.1f}% WR, {best['avg_pnl']:.1f}% avg")
            print(f"               {best['total_trades']} trades, {best['total_pnl']:.1f}% total")
            
            all_best.append(best)
    
    # Find consensus parameters
    if all_best:
        print("\n" + "="*70)
        print("CONSENSUS CASCADE PARAMETERS")
        print("="*70)
        
        # Average the best parameters
        avg_lookback = np.mean([b['params']['lookback'] for b in all_best])
        avg_threshold = np.mean([b['params']['threshold'] for b in all_best])
        avg_memory = np.mean([b['params']['memory_thresh'] for b in all_best])
        avg_volume = np.mean([b['params']['volume_thresh'] for b in all_best])
        
        print(f"Lookback: {avg_lookback:.0f} days")
        print(f"Threshold: {avg_threshold:.0f} days")
        print(f"Memory Threshold: {avg_memory:.2f}")
        print(f"Volume Threshold: {avg_volume:.2f}")
        
        # Performance stats
        avg_wr = np.mean([b['win_rate'] for b in all_best])
        avg_trades = np.mean([b['total_trades'] for b in all_best])
        
        print(f"\nExpected Performance:")
        print(f"  Win Rate: {avg_wr:.1f}%")
        print(f"  Trades per asset: {avg_trades:.0f}")
        
        # Save optimal parameters
        optimal = {
            'cascade_optimal': {
                'lookback_days': int(avg_lookback),
                'threshold_days': int(avg_threshold),
                'memory_threshold': round(avg_memory, 2),
                'volume_threshold': round(avg_volume, 2)
            },
            'expected_performance': {
                'win_rate': round(avg_wr, 1),
                'avg_trades': int(avg_trades)
            },
            'by_asset': [
                {
                    'symbol': test_configs[i][0],
                    'params': b['params'],
                    'win_rate': b['win_rate'],
                    'total_pnl': b['total_pnl']
                }
                for i, b in enumerate(all_best) if i < len(test_configs)
            ]
        }
        
        with open('cascade_optimal_params.json', 'w') as f:
            json.dump(optimal, f, indent=2)
        
        print("\nResults saved to cascade_optimal_params.json")


if __name__ == "__main__":
    main()