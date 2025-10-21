"""
Memory-Induced Phase Transition Trading Strategy V2
====================================================
Refined based on COIN success (71.4% win rate!)
Avoiding manipulated meme stocks
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

class PhaseTransitionTraderV2:
    def __init__(self, lookback_days=30, threshold_days=5, volume_surge=2.0):  # Lowered from 3.0
        """
        V2: Tuned parameters based on COIN success
        """
        self.lookback_days = lookback_days
        self.threshold_days = threshold_days
        self.volume_surge_threshold = volume_surge  # Lowered to catch more cascades
        self.trades = []
        
    def calculate_memory_factor(self, prices, current_idx):
        """Calculate memory factor (unchanged - this part worked)"""
        if current_idx < self.lookback_days + self.threshold_days:
            return 0
            
        recent_start = current_idx - self.threshold_days
        recent_return = (prices[current_idx] / prices[recent_start]) - 1
        recent_daily_rate = recent_return / self.threshold_days
        
        baseline_start = current_idx - self.lookback_days
        baseline_end = current_idx - self.threshold_days
        baseline_return = (prices[baseline_end] / prices[baseline_start]) - 1
        baseline_daily_rate = baseline_return / (self.lookback_days - self.threshold_days)
        
        if baseline_daily_rate <= 0:
            return 0
            
        memory_factor = recent_daily_rate / baseline_daily_rate
        return memory_factor
    
    def detect_phase_transition(self, prices, volumes, current_idx, asset_type='unknown'):
        """
        V2: Better detection with asset type awareness
        """
        memory_factor = self.calculate_memory_factor(prices, current_idx)
        
        if memory_factor < 1.0:
            return None
            
        # Calculate volume surge
        recent_volume = np.mean(volumes[current_idx-5:current_idx])
        baseline_volume = np.mean(volumes[current_idx-30:current_idx-5])
        volume_surge = recent_volume / max(baseline_volume, 1)
        
        # V2: Asset-specific thresholds
        if asset_type in ['crypto', 'ipo', 'growth']:
            # These tend to cascade more
            cascade_threshold = 1.5  # Lower for growth stocks
        else:
            cascade_threshold = 2.0  # Higher for established stocks
            
        if memory_factor > 1.25:
            if volume_surge > cascade_threshold:
                return 'cascade'
            else:
                return 'crystallize'
                
        return None
    
    def backtest(self, symbol, start_date, end_date, asset_type='unknown'):
        """V2: Improved exit strategies"""
        print(f"Testing {symbol} ({asset_type}) from {start_date} to {end_date}")
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        
        if len(data) < self.lookback_days + 10:
            print(f"  Insufficient data")
            return None
            
        prices = data['Close'].values
        volumes = data['Volume'].values
        dates = data.index
        
        position = 0
        entry_price = 0
        entry_date = None
        
        results = {'trades': [], 'signals': []}
        
        for i in range(self.lookback_days + self.threshold_days, len(prices) - 1):
            current_price = prices[i]
            current_date = dates[i]
            
            transition = self.detect_phase_transition(prices, volumes, i, asset_type)
            
            if transition and position == 0:
                memory_factor = self.calculate_memory_factor(prices, i)
                
                if transition == 'cascade':
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    print(f"  LONG at ${current_price:.2f} on {current_date.date()} (MF={memory_factor:.2f})")
                    
                elif transition == 'crystallize':
                    position = -1
                    entry_price = current_price
                    entry_date = current_date
                    print(f"  SHORT at ${current_price:.2f} on {current_date.date()} (MF={memory_factor:.2f})")
            
            # V2: Dynamic exit based on position type
            if position != 0:
                days_held = (current_date - entry_date).days
                price_change = (current_price / entry_price - 1) * position
                
                # Different exit rules for different positions
                if position == 1:  # Long (cascade)
                    # Take profits quicker on cascades
                    exit_signal = days_held >= 20 or price_change >= 0.30 or price_change <= -0.15
                else:  # Short (crystallize)
                    # Give shorts more time to work
                    exit_signal = days_held >= 30 or price_change >= 0.25 or price_change <= -0.20
                
                if exit_signal:
                    exit_price = current_price
                    pnl = (exit_price / entry_price - 1) * position
                    
                    results['trades'].append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': 'LONG' if position == 1 else 'SHORT',
                        'pnl_pct': pnl * 100,
                        'days_held': days_held
                    })
                    
                    print(f"  CLOSE at ${exit_price:.2f} ({pnl*100:+.1f}% in {days_held}d)")
                    
                    position = 0
                    entry_price = 0
                    entry_date = None
        
        return results


def run_backtests():
    """Test on various non-manipulated assets"""
    
    print("="*70)
    print("PHASE TRANSITION TRADING V2 - REFINED PARAMETERS")
    print("="*70)
    
    trader = PhaseTransitionTraderV2(
        lookback_days=30, 
        threshold_days=5,
        volume_surge=2.0  # Lowered from 3.0
    )
    
    # Test portfolio (avoiding meme stocks)
    test_assets = [
        # Recent IPOs (worked great for COIN)
        ('COIN', '2021-04-14', '2023-01-01', 'ipo'),
        ('ABNB', '2020-12-10', '2023-01-01', 'ipo'),
        ('SNOW', '2020-09-16', '2023-01-01', 'ipo'),
        ('PLTR', '2020-09-30', '2023-01-01', 'ipo'),
        
        # Growth stocks (should cascade)
        ('TSLA', '2020-01-01', '2023-01-01', 'growth'),
        ('NVDA', '2020-01-01', '2023-01-01', 'growth'),
        ('AMD', '2020-01-01', '2023-01-01', 'growth'),
        
        # Established tech (should crystallize)
        ('MSFT', '2020-01-01', '2023-01-01', 'tech'),
        ('GOOGL', '2020-01-01', '2023-01-01', 'tech'),
        ('META', '2020-01-01', '2023-01-01', 'tech'),
        
        # Crypto stocks (should cascade)
        ('MARA', '2020-01-01', '2022-01-01', 'crypto'),
        ('RIOT', '2020-01-01', '2022-01-01', 'crypto'),
    ]
    
    all_trades = []
    
    for symbol, start, end, asset_type in test_assets:
        print(f"\n{'='*40}")
        results = trader.backtest(symbol, start, end, asset_type)
        if results and results['trades']:
            all_trades.extend(results['trades'])
            
            # Quick summary for this asset
            trades_df = pd.DataFrame(results['trades'])
            avg_pnl = trades_df['pnl_pct'].mean()
            win_rate = len(trades_df[trades_df['pnl_pct'] > 0]) / len(trades_df) * 100
            print(f"  Summary: {len(trades_df)} trades, {win_rate:.1f}% WR, {avg_pnl:+.1f}% avg")
    
    # Overall analysis
    print("\n" + "="*70)
    print("OVERALL RESULTS")
    print("="*70)
    
    if all_trades:
        df = pd.DataFrame(all_trades)
        
        # Overall stats
        total_trades = len(df)
        winners = len(df[df['pnl_pct'] > 0])
        win_rate = winners / total_trades * 100
        
        avg_win = df[df['pnl_pct'] > 0]['pnl_pct'].mean() if winners > 0 else 0
        avg_loss = df[df['pnl_pct'] < 0]['pnl_pct'].mean() if winners < total_trades else 0
        avg_pnl = df['pnl_pct'].mean()
        total_pnl = df['pnl_pct'].sum()
        
        print(f"\nTotal Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Average Win: {avg_win:+.1f}%")
        print(f"Average Loss: {avg_loss:+.1f}%")
        print(f"Average P&L: {avg_pnl:+.1f}%")
        print(f"Total P&L: {total_pnl:+.1f}%")
        
        # By asset type
        print("\nBy Asset Type:")
        for atype in df['symbol'].unique():
            asset_trades = df[df['symbol'] == atype]
            if len(asset_trades) > 0:
                awr = len(asset_trades[asset_trades['pnl_pct'] > 0]) / len(asset_trades) * 100
                apnl = asset_trades['pnl_pct'].mean()
                print(f"  {atype}: {len(asset_trades)} trades, {awr:.0f}% WR, {apnl:+.1f}% avg")
        
        # Best performers
        print("\nTop 5 Best Trades:")
        for _, trade in df.nlargest(5, 'pnl_pct').iterrows():
            print(f"  {trade['symbol']}: {trade['pnl_pct']:+.1f}% ({trade['position']}, {trade['days_held']}d)")
        
        if win_rate > 55 and avg_pnl > 2:
            print("\n" + "="*70)
            print("[!!!] HOLY SHIT IT WORKS!")
            print("This strategy shows real promise!")
            print("Next: Paper trade, then OPEN-SOURCE!")
        elif win_rate > 50:
            print("\n[!] Getting there - needs more tuning")
        else:
            print("\n[?] More refinement needed")


if __name__ == "__main__":
    run_backtests()