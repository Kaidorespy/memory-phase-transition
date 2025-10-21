"""
Memory-Induced Phase Transition Trading Strategy
=================================================
Backtesting framework for the discovered phase transition patterns

HYPOTHESIS:
- Assets crossing critical memory threshold undergo phase transitions
- Collaborative assets crystallize (short opportunity)
- Speculative assets cascade (long opportunity)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf  # You'll need: pip install yfinance

class PhaseTransitionTrader:
    def __init__(self, lookback_days=30, threshold_days=5):
        """
        Initialize the trading strategy
        
        lookback_days: Period to calculate baseline growth
        threshold_days: Days to reach 2x for "instant" classification
        """
        self.lookback_days = lookback_days
        self.threshold_days = threshold_days
        self.trades = []
        
    def calculate_memory_factor(self, prices, current_idx):
        """
        Calculate memory factor at a given point
        Memory factor = recent_growth_rate / baseline_growth_rate
        """
        if current_idx < self.lookback_days + self.threshold_days:
            return 0
            
        # Recent growth (last N days)
        recent_start = current_idx - self.threshold_days
        recent_return = (prices[current_idx] / prices[recent_start]) - 1
        recent_daily_rate = recent_return / self.threshold_days
        
        # Baseline growth (previous period)
        baseline_start = current_idx - self.lookback_days
        baseline_end = current_idx - self.threshold_days
        baseline_return = (prices[baseline_end] / prices[baseline_start]) - 1
        baseline_daily_rate = baseline_return / (self.lookback_days - self.threshold_days)
        
        if baseline_daily_rate <= 0:
            return 0
            
        memory_factor = recent_daily_rate / baseline_daily_rate
        return memory_factor
    
    def detect_phase_transition(self, prices, volumes, current_idx):
        """
        Detect if we're at a phase transition point
        Returns: ('crystallize', 'cascade', or None)
        """
        memory_factor = self.calculate_memory_factor(prices, current_idx)
        
        # Check if we've crossed critical threshold (1.0-1.25)
        if memory_factor < 1.0:
            return None
            
        # Determine system type using volume as proxy
        # High volume surge = speculative (crypto-like)
        # Normal volume = collaborative (GitHub-like)
        recent_volume = np.mean(volumes[current_idx-5:current_idx])
        baseline_volume = np.mean(volumes[current_idx-30:current_idx-5])
        volume_surge = recent_volume / max(baseline_volume, 1)
        
        if memory_factor > 1.25:
            if volume_surge > 3.0:  # Speculative system
                return 'cascade'  # Will continue up
            else:  # Collaborative system
                return 'crystallize'  # Will freeze/decline
                
        return None
    
    def backtest(self, symbol, start_date, end_date, asset_type='stock'):
        """
        Backtest the strategy on historical data
        """
        print(f"Backtesting {symbol} from {start_date} to {end_date}")
        
        # Get data
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        
        if len(data) < self.lookback_days + 10:
            print(f"Insufficient data for {symbol}")
            return None
            
        prices = data['Close'].values
        volumes = data['Volume'].values
        dates = data.index
        
        # Trading variables
        position = 0  # 1 = long, -1 = short, 0 = no position
        entry_price = 0
        entry_date = None
        
        results = {
            'trades': [],
            'signals': []
        }
        
        # Main backtest loop
        for i in range(self.lookback_days + self.threshold_days, len(prices) - 1):
            current_price = prices[i]
            current_date = dates[i]
            
            # Detect phase transition
            transition = self.detect_phase_transition(prices, volumes, i)
            
            if transition:
                memory_factor = self.calculate_memory_factor(prices, i)
                results['signals'].append({
                    'date': current_date,
                    'price': current_price,
                    'signal': transition,
                    'memory_factor': memory_factor
                })
                
                # Trading logic
                if position == 0:  # No position
                    if transition == 'cascade':
                        # Go long (buy)
                        position = 1
                        entry_price = current_price
                        entry_date = current_date
                        print(f"  LONG at {current_price:.2f} on {current_date.date()} (cascade)")
                        
                    elif transition == 'crystallize':
                        # Go short (sell)
                        position = -1
                        entry_price = current_price
                        entry_date = current_date
                        print(f"  SHORT at {current_price:.2f} on {current_date.date()} (crystallize)")
                        
            # Exit logic (simple: exit after 30 days or 20% move)
            if position != 0:
                days_held = (current_date - entry_date).days
                price_change = (current_price / entry_price - 1) * position
                
                if days_held >= 30 or abs(price_change) >= 0.20:
                    # Close position
                    exit_price = current_price
                    pnl = (exit_price / entry_price - 1) * position
                    
                    results['trades'].append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': 'LONG' if position == 1 else 'SHORT',
                        'pnl_pct': pnl * 100,
                        'days_held': days_held
                    })
                    
                    print(f"  CLOSE at {exit_price:.2f} on {current_date.date()}")
                    print(f"  P&L: {pnl*100:+.1f}% in {days_held} days")
                    
                    position = 0
                    entry_price = 0
                    entry_date = None
        
        return results
    
    def analyze_results(self, results):
        """
        Analyze backtest results
        """
        if not results or not results['trades']:
            print("No trades executed")
            return
            
        trades_df = pd.DataFrame(results['trades'])
        
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        
        # Overall stats
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl_pct'] > 0])
        losing_trades = len(trades_df[trades_df['pnl_pct'] < 0])
        win_rate = winning_trades / total_trades * 100
        
        avg_win = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl_pct'] < 0]['pnl_pct'].mean() if losing_trades > 0 else 0
        total_return = trades_df['pnl_pct'].sum()
        
        print(f"\nTotal Trades: {total_trades}")
        print(f"Winners: {winning_trades} ({win_rate:.1f}%)")
        print(f"Losers: {losing_trades}")
        print(f"\nAverage Win: {avg_win:+.1f}%")
        print(f"Average Loss: {avg_loss:+.1f}%")
        print(f"Total Return: {total_return:+.1f}%")
        
        # By position type
        long_trades = trades_df[trades_df['position'] == 'LONG']
        short_trades = trades_df[trades_df['position'] == 'SHORT']
        
        if len(long_trades) > 0:
            print(f"\nLONG trades (cascade): {len(long_trades)}")
            print(f"  Avg P&L: {long_trades['pnl_pct'].mean():+.1f}%")
            print(f"  Win Rate: {len(long_trades[long_trades['pnl_pct'] > 0])/len(long_trades)*100:.1f}%")
            
        if len(short_trades) > 0:
            print(f"\nSHORT trades (crystallize): {len(short_trades)}")
            print(f"  Avg P&L: {short_trades['pnl_pct'].mean():+.1f}%")
            print(f"  Win Rate: {len(short_trades[short_trades['pnl_pct'] > 0])/len(short_trades)*100:.1f}%")
        
        return trades_df


def main():
    """
    Run backtests on various assets
    """
    print("="*70)
    print("MEMORY-INDUCED PHASE TRANSITION TRADING STRATEGY")
    print("="*70)
    print("\nBacktesting on historical data...")
    
    trader = PhaseTransitionTrader(lookback_days=30, threshold_days=5)
    
    # Test on different asset types
    test_assets = [
        # Meme stocks (should cascade)
        ('GME', '2020-01-01', '2022-01-01', 'meme'),
        ('AMC', '2020-01-01', '2022-01-01', 'meme'),
        
        # Tech stocks (should crystallize)
        ('AAPL', '2020-01-01', '2023-01-01', 'tech'),
        ('MSFT', '2020-01-01', '2023-01-01', 'tech'),
        
        # Recent IPOs
        ('COIN', '2021-04-14', '2023-01-01', 'ipo'),
        ('RIVN', '2021-11-10', '2023-01-01', 'ipo'),
    ]
    
    all_results = []
    
    for symbol, start, end, asset_type in test_assets:
        print(f"\n{'='*40}")
        print(f"Testing {symbol} ({asset_type})")
        print('='*40)
        
        results = trader.backtest(symbol, start, end, asset_type)
        if results:
            all_results.append(results)
            trader.analyze_results(results)
    
    print("\n" + "="*70)
    print("STRATEGY SUMMARY")
    print("="*70)
    
    if all_results:
        all_trades = []
        for r in all_results:
            all_trades.extend(r['trades'])
        
        if all_trades:
            df = pd.DataFrame(all_trades)
            total_pnl = df['pnl_pct'].sum()
            avg_pnl = df['pnl_pct'].mean()
            win_rate = len(df[df['pnl_pct'] > 0]) / len(df) * 100
            
            print(f"\nAcross all {len(df)} trades:")
            print(f"  Total P&L: {total_pnl:+.1f}%")
            print(f"  Average P&L: {avg_pnl:+.1f}%")
            print(f"  Win Rate: {win_rate:.1f}%")
            
            if total_pnl > 0 and win_rate > 50:
                print("\n[!!!] STRATEGY SHOWS PROMISE!")
                print("Consider paper trading before going live")
                print("Ready to open-source if consistent profits")
            else:
                print("\n[?] Mixed results - needs refinement")
    
    print("\n" + "="*70)
    print("Next steps:")
    print("1. Refine memory factor calculation")
    print("2. Better distinguish collaborative vs speculative")
    print("3. Test on crypto data")
    print("4. If profitable, OPEN-SOURCE IT!")


if __name__ == "__main__":
    main()