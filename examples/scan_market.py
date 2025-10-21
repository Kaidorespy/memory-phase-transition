#!/usr/bin/env python3
"""
Market Scanner
===============
Scan multiple stocks to find current phase transition opportunities.

This script scans a predefined list of stocks to identify which ones
are currently showing phase transition signals.

Usage:
    python scan_market.py              # Scan default watchlist
    python scan_market.py --top-ipo    # Scan recent IPOs
    python scan_market.py --top-crypto # Scan crypto-related stocks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.phase_transition_strategy import PhaseTransitionStrategy
import argparse
from datetime import datetime
from typing import List, Tuple
import pandas as pd


# Predefined watchlists
WATCHLISTS = {
    'default': [
        ('COIN', 'crypto'),
        ('RIOT', 'crypto'),
        ('MARA', 'crypto'),
        ('PLTR', 'ipo'),
        ('ABNB', 'ipo'),
        ('SNOW', 'ipo'),
        ('TSLA', 'growth'),
        ('NVDA', 'growth'),
        ('AMD', 'growth'),
        ('META', 'tech'),
        ('GOOGL', 'tech'),
        ('MSFT', 'tech')
    ],
    
    'ipo': [
        ('COIN', 'ipo'),
        ('ABNB', 'ipo'),
        ('SNOW', 'ipo'),
        ('PLTR', 'ipo'),
        ('RBLX', 'ipo'),
        ('HOOD', 'ipo'),
        ('SOFI', 'ipo'),
        ('RIVN', 'ipo'),
        ('LCID', 'ipo'),
        ('NU', 'ipo')
    ],
    
    'crypto': [
        ('COIN', 'crypto'),
        ('RIOT', 'crypto'),
        ('MARA', 'crypto'),
        ('MSTR', 'crypto'),
        ('CLSK', 'crypto'),
        ('BITF', 'crypto'),
        ('HUT', 'crypto'),
        ('HIVE', 'crypto'),
        ('ARBK', 'crypto'),
        ('CIFR', 'crypto')
    ],
    
    'growth': [
        ('TSLA', 'growth'),
        ('NVDA', 'growth'),
        ('AMD', 'growth'),
        ('SHOP', 'growth'),
        ('SQ', 'growth'),
        ('ROKU', 'growth'),
        ('SNAP', 'growth'),
        ('PINS', 'growth'),
        ('TWLO', 'growth'),
        ('DDOG', 'growth')
    ]
}


def scan_market(watchlist: List[Tuple[str, str]], verbose: bool = False) -> pd.DataFrame:
    """
    Scan a watchlist for phase transition signals.
    
    Args:
        watchlist: List of (symbol, asset_type) tuples
        verbose: Print detailed progress
        
    Returns:
        DataFrame with scan results
    """
    strategy = PhaseTransitionStrategy()
    results = []
    
    print(f"\n{'='*70}")
    print(f"PHASE TRANSITION MARKET SCANNER")
    print(f"Scanning {len(watchlist)} stocks at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")
    
    for symbol, asset_type in watchlist:
        if verbose:
            print(f"Scanning {symbol}...", end=' ')
        
        try:
            # Check for current signal
            signal = strategy.check_current_signal(symbol, asset_type)
            
            if signal:
                results.append({
                    'Symbol': symbol,
                    'Signal': signal['signal'].upper(),
                    'Action': signal['recommendation'],
                    'Memory': f"{signal['memory_factor']:.2f}",
                    'Volume': f"{signal['volume_surge']:.2f}",
                    'Price': f"${signal['current_price']:.2f}",
                    'Type': asset_type
                })
                if verbose:
                    print(f"✓ {signal['signal'].upper()} signal!")
            else:
                if verbose:
                    print("No signal")
                    
        except Exception as e:
            if verbose:
                print(f"Error: {e}")
    
    return pd.DataFrame(results)


def display_results(df: pd.DataFrame):
    """
    Display scan results in a formatted table.
    
    Args:
        df: DataFrame with scan results
    """
    if df.empty:
        print("\n❌ No phase transition signals detected in current market")
        return
    
    print(f"\n{'='*70}")
    print(f"SIGNALS DETECTED: {len(df)} stocks showing phase transitions")
    print(f"{'='*70}\n")
    
    # Sort by signal strength (memory factor)
    df['_memory_sort'] = df['Memory'].astype(float)
    df = df.sort_values('_memory_sort', ascending=False)
    df = df.drop('_memory_sort', axis=1)
    
    # Display table
    print(df.to_string(index=False))
    
    # Summary by signal type
    print(f"\n{'='*70}")
    print("SUMMARY BY SIGNAL TYPE")
    print(f"{'='*70}")
    
    cascade_count = len(df[df['Signal'] == 'CASCADE'])
    crystallize_count = len(df[df['Signal'] == 'CRYSTALLIZE'])
    
    print(f"CASCADE signals (go long):      {cascade_count}")
    print(f"CRYSTALLIZE signals (go short): {crystallize_count}")
    
    # Strongest signals
    if len(df) > 0:
        print(f"\n{'='*70}")
        print("TOP 3 STRONGEST SIGNALS (by Memory Factor)")
        print(f"{'='*70}")
        
        for _, row in df.head(3).iterrows():
            print(f"\n{row['Symbol']} - {row['Action']} Signal")
            print(f"  Signal Type:   {row['Signal']}")
            print(f"  Memory Factor: {row['Memory']}x baseline")
            print(f"  Volume Surge:  {row['Volume']}x average")
            print(f"  Current Price: {row['Price']}")
            print(f"  Asset Type:    {row['Type']}")
            
            # Trading recommendation
            if row['Signal'] == 'CASCADE':
                stop = float(row['Price'].replace('$', '')) * 0.85
                target = float(row['Price'].replace('$', '')) * 1.30
                print(f"  📈 Go LONG with stop at ${stop:.2f}, target ${target:.2f}")
            else:
                stop = float(row['Price'].replace('$', '')) * 1.20
                target = float(row['Price'].replace('$', '')) * 0.75
                print(f"  📉 Go SHORT with stop at ${stop:.2f}, target ${target:.2f}")
    
    print(f"\n{'='*70}")
    print("⚠️  DISCLAIMER: These are algorithmic signals, not financial advice.")
    print("Always do your own research and use proper risk management.")
    print(f"{'='*70}\n")


def main():
    """Main entry point for market scanner."""
    parser = argparse.ArgumentParser(description='Scan market for phase transition signals')
    parser.add_argument('--watchlist', type=str, default='default',
                       choices=['default', 'ipo', 'crypto', 'growth'],
                       help='Predefined watchlist to scan')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed progress')
    parser.add_argument('--export', type=str,
                       help='Export results to CSV file')
    
    args = parser.parse_args()
    
    # Get watchlist
    watchlist = WATCHLISTS[args.watchlist]
    
    # Run scan
    results_df = scan_market(watchlist, verbose=args.verbose)
    
    # Display results
    display_results(results_df)
    
    # Export if requested
    if args.export and not results_df.empty:
        results_df.to_csv(args.export, index=False)
        print(f"Results exported to {args.export}")


if __name__ == "__main__":
    main()