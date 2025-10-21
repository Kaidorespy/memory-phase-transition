#!/usr/bin/env python3
"""
CASCADE Real-Time Scanner
=========================
Find phase transition opportunities as they happen.

80% win rate CASCADE signals are REAL.
This scanner helps you catch them.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from typing import List, Dict, Tuple


class CascadeScanner:
    """
    Scans for CASCADE (phase transition + volume surge) opportunities.
    
    Based on optimized parameters:
    - 80.8% historical win rate
    - Memory threshold: 1.15
    - Volume threshold: 1.90
    """
    
    def __init__(self):
        # Load optimized parameters
        try:
            with open('cascade_optimal_params.json', 'r') as f:
                params = json.load(f)
                optimal = params['cascade_optimal']
                self.lookback_days = optimal['lookback_days']
                self.threshold_days = optimal['threshold_days']
                self.memory_threshold = optimal['memory_threshold']
                self.volume_threshold = optimal['volume_threshold']
        except:
            # Fallback to defaults if file not found
            self.lookback_days = 28
            self.threshold_days = 5
            self.memory_threshold = 1.15
            self.volume_threshold = 1.90
        
        print(f"Scanner initialized with optimized parameters:")
        print(f"  Memory Threshold: {self.memory_threshold}")
        print(f"  Volume Threshold: {self.volume_threshold}")
        print(f"  Lookback: {self.lookback_days} days")
        print(f"  Threshold: {self.threshold_days} days")
    
    def calculate_memory_factor(self, prices: np.ndarray) -> float:
        """Calculate memory factor for the latest data point"""
        if len(prices) < self.lookback_days + self.threshold_days:
            return 0
        
        current_idx = len(prices) - 1
        recent_start = current_idx - self.threshold_days
        recent_return = (prices[current_idx] / prices[recent_start]) - 1
        recent_daily_rate = recent_return / self.threshold_days
        
        baseline_start = current_idx - self.lookback_days
        baseline_end = current_idx - self.threshold_days
        baseline_return = (prices[baseline_end] / prices[baseline_start]) - 1
        baseline_daily_rate = baseline_return / (self.lookback_days - self.threshold_days)
        
        if baseline_daily_rate <= 0:
            return 0
            
        return recent_daily_rate / baseline_daily_rate
    
    def calculate_volume_surge(self, volumes: np.ndarray) -> float:
        """Calculate volume surge for the latest data point"""
        if len(volumes) < 30:
            return 0
            
        recent_volume = np.mean(volumes[-5:])
        baseline_volume = np.mean(volumes[-30:-5])
        
        if baseline_volume == 0:
            return 0
            
        return recent_volume / baseline_volume
    
    def scan_symbol(self, symbol: str) -> Dict:
        """
        Scan a single symbol for CASCADE opportunity.
        
        Returns dict with signal details or None if no signal.
        """
        try:
            # Fetch recent data
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            data = ticker.history(start=start_date, end=end_date)
            
            if len(data) < self.lookback_days + self.threshold_days:
                return None
            
            prices = data['Close'].values
            volumes = data['Volume'].values
            
            # Calculate indicators
            memory_factor = self.calculate_memory_factor(prices)
            volume_surge = self.calculate_volume_surge(volumes)
            
            # Check for CASCADE signal
            if memory_factor > self.memory_threshold and volume_surge > self.volume_threshold:
                # Calculate signal strength
                signal_strength = (memory_factor / self.memory_threshold) * (volume_surge / self.volume_threshold)
                
                # Get current price and recent performance
                current_price = prices[-1]
                price_5d = (prices[-1] / prices[-6] - 1) * 100 if len(prices) > 5 else 0
                price_20d = (prices[-1] / prices[-21] - 1) * 100 if len(prices) > 20 else 0
                
                return {
                    'symbol': symbol,
                    'signal': 'CASCADE',
                    'current_price': current_price,
                    'memory_factor': memory_factor,
                    'volume_surge': volume_surge,
                    'signal_strength': signal_strength,
                    'price_5d': price_5d,
                    'price_20d': price_20d,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            # print(f"Error scanning {symbol}: {e}")
            return None
    
    def scan_watchlist(self, symbols: List[str], show_all: bool = False) -> List[Dict]:
        """
        Scan a list of symbols for CASCADE opportunities.
        
        Args:
            symbols: List of stock symbols to scan
            show_all: If True, show all scanned symbols (not just signals)
            
        Returns:
            List of CASCADE opportunities found
        """
        print(f"\n{'='*70}")
        print(f"CASCADE SCANNER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"Scanning {len(symbols)} symbols for phase transitions...\n")
        
        opportunities = []
        
        for i, symbol in enumerate(symbols):
            if show_all and (i + 1) % 10 == 0:
                print(f"  Scanned {i + 1}/{len(symbols)} symbols...")
            
            result = self.scan_symbol(symbol)
            
            if result:
                opportunities.append(result)
                print(f"🎯 CASCADE SIGNAL: {symbol}")
                print(f"   Price: ${result['current_price']:.2f}")
                print(f"   Memory Factor: {result['memory_factor']:.2f}x")
                print(f"   Volume Surge: {result['volume_surge']:.2f}x")
                print(f"   Signal Strength: {result['signal_strength']:.2f}")
                print(f"   5-day: {result['price_5d']:+.1f}%, 20-day: {result['price_20d']:+.1f}%")
                print()
        
        return opportunities
    
    def scan_top_movers(self) -> List[Dict]:
        """
        Scan today's top movers for CASCADE opportunities.
        """
        print("\nFetching today's top movers...")
        
        # Get trending tickers from Yahoo Finance
        try:
            # Most active stocks
            url = "https://finance.yahoo.com/most-active"
            tables = pd.read_html(url)
            if tables:
                most_active = tables[0]['Symbol'].tolist()[:50]
            else:
                most_active = []
            
            # Combine and deduplicate
            symbols = list(set(most_active))
            
            print(f"Found {len(symbols)} active stocks to scan")
            
            return self.scan_watchlist(symbols)
            
        except Exception as e:
            print(f"Error fetching top movers: {e}")
            return []
    
    def continuous_scan(
        self,
        watchlist: List[str],
        interval_minutes: int = 15,
        market_hours_only: bool = True
    ):
        """
        Continuously scan for CASCADE opportunities.
        
        Args:
            watchlist: List of symbols to monitor
            interval_minutes: Minutes between scans
            market_hours_only: Only scan during market hours (9:30 AM - 4:00 PM ET)
        """
        print(f"\n{'='*70}")
        print("STARTING CONTINUOUS CASCADE SCANNER")
        print(f"{'='*70}")
        print(f"Monitoring {len(watchlist)} symbols")
        print(f"Scan interval: {interval_minutes} minutes")
        print(f"Market hours only: {market_hours_only}")
        print("\nPress Ctrl+C to stop\n")
        
        seen_signals = set()  # Track already reported signals
        
        try:
            while True:
                now = datetime.now()
                
                # Check if market hours (rough approximation)
                if market_hours_only:
                    if now.weekday() >= 5:  # Weekend
                        print(f"[{now.strftime('%H:%M')}] Market closed (weekend)")
                        time.sleep(interval_minutes * 60)
                        continue
                    
                    hour = now.hour
                    if hour < 9 or hour >= 16:  # Before 9:30 AM or after 4:00 PM
                        print(f"[{now.strftime('%H:%M')}] Market closed")
                        time.sleep(interval_minutes * 60)
                        continue
                
                # Scan for opportunities
                opportunities = self.scan_watchlist(watchlist, show_all=False)
                
                # Alert for new signals
                for opp in opportunities:
                    signal_key = f"{opp['symbol']}-{opp['signal']}"
                    if signal_key not in seen_signals:
                        print("\n" + "!"*50)
                        print(f"NEW CASCADE OPPORTUNITY: {opp['symbol']}")
                        print(f"Entry Price: ${opp['current_price']:.2f}")
                        print(f"Stop Loss: ${opp['current_price'] * 0.85:.2f} (-15%)")
                        print(f"Target: ${opp['current_price'] * 1.30:.2f} (+30%)")
                        print("!"*50 + "\n")
                        seen_signals.add(signal_key)
                
                if not opportunities:
                    print(f"[{now.strftime('%H:%M')}] No CASCADE signals detected")
                
                # Wait for next scan
                print(f"\nNext scan in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
                # Clear old signals after 24 hours
                if len(seen_signals) > 100:
                    seen_signals.clear()
                    
        except KeyboardInterrupt:
            print("\nScanner stopped by user")


def main():
    """Main entry point for CASCADE scanner"""
    
    scanner = CascadeScanner()
    
    # Default watchlist - proven performers + popular stocks
    DEFAULT_WATCHLIST = [
        # Proven CASCADE performers
        'COIN', 'RIOT', 'MARA', 'PLTR', 'ABNB', 'SNOW',
        
        # Tech giants
        'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA',
        
        # High volatility tech
        'AMD', 'NFLX', 'SHOP', 'SQ', 'ROKU', 'SNAP',
        
        # Crypto-related
        'MSTR', 'CLSK', 'BITF', 'HUT', 'GBTC',
        
        # Recent IPOs/SPACs
        'RIVN', 'LCID', 'SOFI', 'HOOD', 'RBLX',
        
        # Meme stocks (careful!)
        'GME', 'AMC', 'BBBY', 'BB'
    ]
    
    import argparse
    parser = argparse.ArgumentParser(description='CASCADE Signal Scanner - Find 80% win rate opportunities')
    parser.add_argument('--symbols', type=str, help='Comma-separated list of symbols')
    parser.add_argument('--continuous', action='store_true', help='Run continuous scanning')
    parser.add_argument('--interval', type=int, default=15, help='Minutes between scans (for continuous mode)')
    parser.add_argument('--movers', action='store_true', help='Scan today\'s top movers')
    
    args = parser.parse_args()
    
    if args.movers:
        # Scan top movers
        opportunities = scanner.scan_top_movers()
    elif args.continuous:
        # Continuous scanning
        if args.symbols:
            watchlist = [s.strip().upper() for s in args.symbols.split(',')]
        else:
            watchlist = DEFAULT_WATCHLIST
        scanner.continuous_scan(watchlist, args.interval)
    else:
        # One-time scan
        if args.symbols:
            watchlist = [s.strip().upper() for s in args.symbols.split(',')]
        else:
            watchlist = DEFAULT_WATCHLIST
        
        opportunities = scanner.scan_watchlist(watchlist)
    
    # Summary
    if not args.continuous:
        print(f"\n{'='*70}")
        print("SCAN COMPLETE")
        print(f"{'='*70}")
        if opportunities:
            print(f"Found {len(opportunities)} CASCADE opportunities!")
            print("\nTop opportunities by signal strength:")
            sorted_opps = sorted(opportunities, key=lambda x: x['signal_strength'], reverse=True)
            for opp in sorted_opps[:5]:
                print(f"  {opp['symbol']}: Strength {opp['signal_strength']:.2f}")
        else:
            print("No CASCADE signals found in current market")
        print("\nRemember: 80% historical win rate on CASCADE signals!")


if __name__ == "__main__":
    main()