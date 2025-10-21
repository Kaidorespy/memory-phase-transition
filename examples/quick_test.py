#!/usr/bin/env python3
"""
Quick Test Example
==================
Test the phase transition strategy on any stock in under 30 seconds.

Usage:
    python quick_test.py AAPL
    python quick_test.py COIN ipo
    python quick_test.py RIOT crypto
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.phase_transition_strategy import PhaseTransitionStrategy
from datetime import datetime, timedelta


def quick_test(symbol: str, asset_type: str = 'unknown'):
    """
    Run a quick backtest on the specified symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'COIN', 'RIOT')
        asset_type: Asset classification ('ipo', 'crypto', 'growth', 'tech')
    """
    print(f"\n{'='*60}")
    print(f"PHASE TRANSITION QUICK TEST: {symbol}")
    print(f"{'='*60}")
    
    # Initialize strategy with default parameters
    strategy = PhaseTransitionStrategy(
        lookback_days=30,
        threshold_days=5,
        volume_surge_threshold=2.0,
        memory_threshold=1.25
    )
    
    # Set test period (last 2 years)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    print(f"Testing period: {start_date} to {end_date}")
    print(f"Asset type: {asset_type}")
    print()
    
    # Run backtest
    results = strategy.execute_backtest(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        asset_type=asset_type,
        verbose=True
    )
    
    # Display results
    if results and results.get('statistics'):
        stats = results['statistics']
        print(f"\n{'='*60}")
        print("BACKTEST STATISTICS")
        print(f"{'='*60}")
        print(f"Total Trades:    {stats['total_trades']}")
        print(f"Win Rate:        {stats['win_rate']:.1f}%")
        print(f"Average P&L:     {stats['avg_pnl']:+.1f}%")
        print(f"Total P&L:       {stats['total_pnl']:+.1f}%")
        print(f"Best Trade:      {stats['best_trade']:+.1f}%")
        print(f"Worst Trade:     {stats['worst_trade']:+.1f}%")
        print(f"Avg Days Held:   {stats['avg_days_held']:.0f}")
        
        # Check current signal
        print(f"\n{'='*60}")
        print("CHECKING CURRENT SIGNAL")
        print(f"{'='*60}")
        current_signal = strategy.check_current_signal(symbol, asset_type)
        if current_signal:
            print(f"⚠️  ACTIVE SIGNAL DETECTED!")
            print(f"Signal Type:     {current_signal['signal'].upper()}")
            print(f"Recommendation:  {current_signal['recommendation']}")
            print(f"Memory Factor:   {current_signal['memory_factor']:.2f}")
            print(f"Volume Surge:    {current_signal['volume_surge']:.2f}")
            print(f"Current Price:   ${current_signal['current_price']:.2f}")
        else:
            print("No active signal at current price levels")
    else:
        print("\nNo trades generated or insufficient data")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py SYMBOL [asset_type]")
        print("Example: python quick_test.py COIN ipo")
        print("\nAsset types: ipo, crypto, growth, tech, unknown")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    asset_type = sys.argv[2].lower() if len(sys.argv) > 2 else 'unknown'
    
    # Run the quick test
    quick_test(symbol, asset_type)