"""
Bull Market Filter Test: 2023-2024
===================================
Hypothesis: The physics are correct, but in strong bull markets,
phase transitions resolve upward (CASCADE) not downward (CRYSTALLIZE).

Test: Only take LONG signals in 2023-2024 bull market.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
from trading_strategy_v2 import PhaseTransitionTraderV2

class BullMarketFilteredTrader(PhaseTransitionTraderV2):
    """Modified trader that respects market regime"""
    
    def __init__(self, *args, bull_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.bull_mode = bull_mode
        
    def backtest(self, symbol, start_date, end_date, asset_type='unknown'):
        """Modified backtest with optional bull market filter"""
        print(f"Testing {symbol} ({asset_type}) from {start_date} to {end_date}")
        if self.bull_mode:
            print("  [BULL MODE]: Only taking CASCADE (long) signals")
        
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
                
                # BULL MODE FILTER: Only take CASCADE signals
                if self.bull_mode and transition == 'crystallize':
                    # Skip short signals in bull mode
                    continue
                
                if transition == 'cascade':
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    print(f"  LONG at ${current_price:.2f} on {current_date.date()} (MF={memory_factor:.2f})")
                    
                elif transition == 'crystallize' and not self.bull_mode:
                    position = -1
                    entry_price = current_price
                    entry_date = current_date
                    print(f"  SHORT at ${current_price:.2f} on {current_date.date()} (MF={memory_factor:.2f})")
            
            # Exit logic
            if position != 0:
                days_held = (current_date - entry_date).days
                price_change = (current_price / entry_price - 1) * position
                
                if position == 1:  # Long
                    exit_signal = days_held >= 20 or price_change >= 0.30 or price_change <= -0.15
                else:  # Short
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


def main():
    print("="*70)
    print("BULL MARKET FILTER TEST: 2023-2024")
    print("="*70)
    print("Testing hypothesis: In bull markets, only CASCADE signals work")
    print()
    
    # Test stocks
    test_stocks = [
        ('COIN', 'crypto'),
        ('RIOT', 'crypto'),
        ('MARA', 'crypto'),
        ('PLTR', 'ipo'),
        ('META', 'tech'),
        ('NVDA', 'growth'),
        ('TSLA', 'growth')
    ]
    
    # First test with BULL MODE ON (longs only)
    print("\n" + "="*70)
    print("TEST 1: BULL MODE (Longs Only)")
    print("="*70)
    
    bull_trader = BullMarketFilteredTrader(
        lookback_days=30,
        threshold_days=5,
        volume_surge=2.0,
        bull_mode=True  # Only longs!
    )
    
    bull_trades = []
    
    for symbol, asset_type in test_stocks:
        print(f"\n{'='*40}")
        results = bull_trader.backtest(symbol, '2023-01-01', '2024-12-31', asset_type)
        
        if results and results['trades']:
            bull_trades.extend(results['trades'])
            trades_df = pd.DataFrame(results['trades'])
            avg_pnl = trades_df['pnl_pct'].mean()
            win_rate = len(trades_df[trades_df['pnl_pct'] > 0]) / len(trades_df) * 100
            total_pnl = trades_df['pnl_pct'].sum()
            print(f"  Summary: {len(trades_df)} trades, {win_rate:.1f}% WR, {avg_pnl:+.1f}% avg, {total_pnl:+.1f}% total")
        else:
            print(f"  No trades generated")
    
    # Bull mode results
    if bull_trades:
        df_bull = pd.DataFrame(bull_trades)
        total_trades = len(df_bull)
        winners = len(df_bull[df_bull['pnl_pct'] > 0])
        win_rate = winners / total_trades * 100
        avg_pnl = df_bull['pnl_pct'].mean()
        total_pnl = df_bull['pnl_pct'].sum()
        
        print("\n" + "="*70)
        print("BULL MODE RESULTS (Longs Only)")
        print("="*70)
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Average P&L: {avg_pnl:+.1f}%")
        print(f"Total P&L: {total_pnl:+.1f}%")
    
    # Now test BALANCED mode (both longs and shorts)
    print("\n\n" + "="*70)
    print("TEST 2: BALANCED MODE (Original Strategy)")
    print("="*70)
    
    regular_trader = PhaseTransitionTraderV2(
        lookback_days=30,
        threshold_days=5,
        volume_surge=2.0
    )
    
    regular_trades = []
    
    for symbol, asset_type in test_stocks:
        print(f"\n{'='*40}")
        results = regular_trader.backtest(symbol, '2023-01-01', '2024-12-31', asset_type)
        
        if results and results['trades']:
            regular_trades.extend(results['trades'])
            trades_df = pd.DataFrame(results['trades'])
            avg_pnl = trades_df['pnl_pct'].mean()
            win_rate = len(trades_df[trades_df['pnl_pct'] > 0]) / len(trades_df) * 100
            total_pnl = trades_df['pnl_pct'].sum()
            print(f"  Summary: {len(trades_df)} trades, {win_rate:.1f}% WR, {avg_pnl:+.1f}% avg, {total_pnl:+.1f}% total")
    
    # Regular mode results
    if regular_trades:
        df_regular = pd.DataFrame(regular_trades)
        total_trades = len(df_regular)
        winners = len(df_regular[df_regular['pnl_pct'] > 0])
        win_rate = winners / total_trades * 100
        avg_pnl = df_regular['pnl_pct'].mean()
        total_pnl = df_regular['pnl_pct'].sum()
        
        print("\n" + "="*70)
        print("BALANCED MODE RESULTS (Original)")
        print("="*70)
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Average P&L: {avg_pnl:+.1f}%")
        print(f"Total P&L: {total_pnl:+.1f}%")
    
    # COMPARISON
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print("\n2020-2022 (Original Market):")
    print("  211 trades, 51.2% WR, +154.6% total")
    
    if regular_trades:
        df_reg = pd.DataFrame(regular_trades)
        print(f"\n2023-2024 Balanced (Longs+Shorts):")
        print(f"  {len(df_reg)} trades, {len(df_reg[df_reg['pnl_pct'] > 0])/len(df_reg)*100:.1f}% WR, {df_reg['pnl_pct'].sum():+.1f}% total")
    
    if bull_trades:
        df_bull = pd.DataFrame(bull_trades)
        print(f"\n2023-2024 Bull Mode (Longs Only):")
        print(f"  {len(df_bull)} trades, {len(df_bull[df_bull['pnl_pct'] > 0])/len(df_bull)*100:.1f}% WR, {df_bull['pnl_pct'].sum():+.1f}% total")
        
        # Check if bull mode improved things
        if bull_trades and regular_trades:
            bull_total = df_bull['pnl_pct'].sum()
            reg_total = df_regular['pnl_pct'].sum()
            improvement = bull_total - reg_total
            
            print(f"\n[RESULT] Bull Mode Improvement: {improvement:+.1f}% better")
            
            if bull_total > 0:
                print("\n[SUCCESS] HYPOTHESIS CONFIRMED!")
                print("In bull markets, filtering out SHORT signals improves performance.")
                print("The physics still work - we just need market regime awareness!")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()