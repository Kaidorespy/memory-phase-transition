"""
Test Unified Regime-Aware System
=================================
Full backtest comparing original vs regime-aware approach.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
from regime_detector import RegimeAwarePhaseDetector
from trading_strategy_v2 import PhaseTransitionTraderV2


def backtest_unified_system(symbol, start_date, end_date, asset_type='unknown'):
    """Backtest using the unified regime-aware detector"""
    
    print(f"Testing {symbol} from {start_date} to {end_date}")
    
    detector = RegimeAwarePhaseDetector()
    
    # Fetch data with extra buffer for regime calculation
    ticker = yf.Ticker(symbol)
    buffer_start = pd.to_datetime(start_date) - pd.Timedelta(days=100)
    data = ticker.history(start=buffer_start, end=end_date)
    
    if len(data) < 100:
        print(f"  Insufficient data for {symbol}")
        return None
    
    # Find actual start index
    start_idx = None
    start_date_ts = pd.to_datetime(start_date).tz_localize(None)
    for i, date in enumerate(data.index):
        if date.tz_localize(None) >= start_date_ts:
            start_idx = i
            break
    
    if start_idx is None:
        print(f"  Cannot find valid start date")
        return None
    
    # Need at least 50 days of history for regime detection
    if start_idx < 50:
        start_idx = 50
    
    prices = data['Close'].values
    volumes = data['Volume'].values
    dates = data.index
    
    trades = []
    position = None
    entry_price = 0
    entry_date = None
    entry_confidence = 0
    
    for i in range(start_idx, len(prices) - 1):
        current_price = prices[i]
        current_date = dates[i]
        
        # Check for signal
        signal, confidence, regime_bias = detector.detect_phase_transition(prices, volumes, i)
        
        # Entry logic with confidence threshold
        if signal and position is None and confidence > 0.4:  # Min 40% confidence
            position = signal
            entry_price = current_price
            entry_date = current_date
            entry_confidence = confidence
            
            regime_desc = detector.get_regime_description(regime_bias)
            print(f"  {signal} @ ${current_price:.2f} on {current_date.date()}")
            print(f"    Regime: {regime_desc}, Confidence: {confidence:.1%}")
        
        # Exit logic
        elif position:
            days_held = (current_date - entry_date).days
            
            if position == 'LONG':
                pnl_pct = (current_price / entry_price - 1) * 100
                # Tighter stops for low confidence
                stop_loss = -15 if entry_confidence > 0.6 else -10
                take_profit = 30 if entry_confidence > 0.6 else 20
            else:  # SHORT
                pnl_pct = (1 - current_price / entry_price) * 100
                stop_loss = -20 if entry_confidence > 0.6 else -15
                take_profit = 25 if entry_confidence > 0.6 else 20
            
            # Exit conditions
            exit_signal = (
                days_held >= 30 or
                pnl_pct >= take_profit or
                pnl_pct <= stop_loss
            )
            
            if exit_signal:
                trades.append({
                    'symbol': symbol,
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'position': position,
                    'pnl_pct': pnl_pct,
                    'days_held': days_held,
                    'confidence': entry_confidence
                })
                
                print(f"  CLOSE @ ${current_price:.2f} ({pnl_pct:+.1f}% in {days_held}d)")
                
                position = None
                entry_price = 0
                entry_date = None
                entry_confidence = 0
    
    return trades


def main():
    print("="*70)
    print("UNIFIED REGIME-AWARE SYSTEM TEST")
    print("="*70)
    
    # Test periods
    test_periods = [
        ("2020-01-01", "2023-01-01", "Training Period"),
        ("2023-01-01", "2024-12-31", "Out-of-Sample")
    ]
    
    test_stocks = [
        ('COIN', 'crypto'),
        ('RIOT', 'crypto'),
        ('PLTR', 'ipo'),
        ('META', 'tech'),
        ('NVDA', 'growth')
    ]
    
    for start, end, period_name in test_periods:
        print(f"\n{'='*70}")
        print(f"{period_name}: {start} to {end}")
        print(f"{'='*70}")
        
        all_trades = []
        
        for symbol, asset_type in test_stocks:
            print(f"\n{'-'*40}")
            
            # Skip COIN before IPO
            if symbol == 'COIN' and start < "2021-04-14":
                test_start = "2021-04-14"
            elif symbol == 'PLTR' and start < "2020-09-30":
                test_start = "2020-09-30"
            else:
                test_start = start
            
            trades = backtest_unified_system(symbol, test_start, end, asset_type)
            
            if trades:
                all_trades.extend(trades)
                df = pd.DataFrame(trades)
                win_rate = len(df[df['pnl_pct'] > 0]) / len(df) * 100
                avg_pnl = df['pnl_pct'].mean()
                total_pnl = df['pnl_pct'].sum()
                avg_conf = df['confidence'].mean()
                
                print(f"  Summary: {len(df)} trades, {win_rate:.1f}% WR")
                print(f"           Avg P&L: {avg_pnl:+.1f}%, Total: {total_pnl:+.1f}%")
                print(f"           Avg Confidence: {avg_conf:.1%}")
        
        # Period summary
        if all_trades:
            df_all = pd.DataFrame(all_trades)
            total_trades = len(df_all)
            winners = len(df_all[df_all['pnl_pct'] > 0])
            win_rate = winners / total_trades * 100
            avg_pnl = df_all['pnl_pct'].mean()
            total_pnl = df_all['pnl_pct'].sum()
            
            print(f"\n{period_name} SUMMARY:")
            print(f"  Total Trades: {total_trades}")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  Average P&L: {avg_pnl:+.1f}%")
            print(f"  Total P&L: {total_pnl:+.1f}%")
            
            # Breakdown by confidence
            high_conf = df_all[df_all['confidence'] > 0.7]
            if len(high_conf) > 0:
                print(f"\n  High Confidence (>70%):")
                print(f"    {len(high_conf)} trades, {len(high_conf[high_conf['pnl_pct'] > 0])/len(high_conf)*100:.1f}% WR")
                print(f"    Avg P&L: {high_conf['pnl_pct'].mean():+.1f}%")
    
    print("\n" + "="*70)
    print("UNIFIED SYSTEM VERDICT")
    print("="*70)
    print("The regime-aware system should:")
    print("1. Maintain performance in normal markets")
    print("2. Avoid disaster in trending markets")
    print("3. Provide confidence scores for position sizing")
    print("4. Work as ONE elegant solution")


if __name__ == "__main__":
    main()