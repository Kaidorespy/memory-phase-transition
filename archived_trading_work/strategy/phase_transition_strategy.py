"""
Phase Transition Trading Strategy
==================================
A physics-based approach to identifying critical points in market behavior.

This strategy is based on the theory that markets undergo phase transitions
similar to physical systems (like water turning to ice). When price momentum
accumulates too rapidly relative to baseline movement, the system becomes
unstable and must either:
- CASCADE: Continue explosive growth (like avalanche)
- CRYSTALLIZE: Freeze and reverse (like supercooled water suddenly freezing)

Author: Memory Phase Transition Research
License: MIT
Version: 2.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, List, Optional, Tuple


class PhaseTransitionStrategy:
    """
    Implements the memory-induced phase transition trading strategy.
    
    The strategy identifies critical points where rapid momentum accumulation
    forces a market to undergo a phase transition, either cascading (continuation)
    or crystallizing (reversal).
    
    Key Concepts:
        - Memory Factor: Ratio of recent vs baseline price movement
        - Volume Surge: Confirms the phase transition direction
        - Asset Type: Different markets have different transition characteristics
    """
    
    def __init__(
        self,
        lookback_days: int = 30,
        threshold_days: int = 5,
        volume_surge_threshold: float = 2.0,
        memory_threshold: float = 1.25
    ):
        """
        Initialize the phase transition strategy.
        
        Args:
            lookback_days: Period for calculating baseline behavior (default: 30)
            threshold_days: Recent period for detecting momentum surge (default: 5)
            volume_surge_threshold: Multiplier to detect volume spikes (default: 2.0)
            memory_threshold: Minimum memory factor to trigger signal (default: 1.25)
        """
        self.lookback_days = lookback_days
        self.threshold_days = threshold_days
        self.volume_surge_threshold = volume_surge_threshold
        self.memory_threshold = memory_threshold
        self.trades = []
        
    def calculate_memory_factor(
        self,
        prices: np.ndarray,
        current_idx: int
    ) -> float:
        """
        Calculate the memory factor at a given point.
        
        Memory factor represents how much faster prices are moving recently
        compared to the baseline period. A high memory factor indicates
        the system is accumulating "stress" that must be released.
        
        Args:
            prices: Array of historical prices
            current_idx: Current position in the price array
            
        Returns:
            Memory factor (recent_rate / baseline_rate), or 0 if invalid
        """
        # Ensure we have enough data
        if current_idx < self.lookback_days + self.threshold_days:
            return 0
        
        # Calculate recent price movement rate
        recent_start = current_idx - self.threshold_days
        recent_return = (prices[current_idx] / prices[recent_start]) - 1
        recent_daily_rate = recent_return / self.threshold_days
        
        # Calculate baseline price movement rate
        baseline_start = current_idx - self.lookback_days
        baseline_end = current_idx - self.threshold_days
        baseline_return = (prices[baseline_end] / prices[baseline_start]) - 1
        baseline_daily_rate = baseline_return / (self.lookback_days - self.threshold_days)
        
        # Avoid division by zero or negative baseline
        if baseline_daily_rate <= 0:
            return 0
            
        # Memory factor is the ratio of recent to baseline movement
        memory_factor = recent_daily_rate / baseline_daily_rate
        return memory_factor
    
    def calculate_volume_surge(
        self,
        volumes: np.ndarray,
        current_idx: int
    ) -> float:
        """
        Calculate the volume surge factor.
        
        Volume surge helps determine the direction of the phase transition.
        High volume confirms a cascade (continuation), while normal volume
        suggests crystallization (reversal).
        
        Args:
            volumes: Array of historical volumes
            current_idx: Current position in the volume array
            
        Returns:
            Volume surge factor (recent_volume / baseline_volume)
        """
        # Recent average volume (last 5 days)
        recent_volume = np.mean(volumes[current_idx-5:current_idx])
        
        # Baseline average volume (previous 25 days)
        baseline_volume = np.mean(volumes[current_idx-30:current_idx-5])
        
        # Avoid division by zero
        if baseline_volume == 0:
            return 1.0
            
        return recent_volume / baseline_volume
    
    def detect_phase_transition(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        current_idx: int,
        asset_type: str = 'unknown'
    ) -> Optional[str]:
        """
        Detect if a phase transition is occurring.
        
        Args:
            prices: Array of historical prices
            volumes: Array of historical volumes
            current_idx: Current position in the arrays
            asset_type: Type of asset ('ipo', 'crypto', 'growth', 'tech', etc.)
            
        Returns:
            'cascade' for continuation signal (go long)
            'crystallize' for reversal signal (go short)
            None if no phase transition detected
        """
        # Calculate memory factor
        memory_factor = self.calculate_memory_factor(prices, current_idx)
        
        # No signal if memory factor is too low
        if memory_factor < self.memory_threshold:
            return None
            
        # Calculate volume surge
        volume_surge = self.calculate_volume_surge(volumes, current_idx)
        
        # Asset-specific thresholds
        # IPOs and crypto tend to cascade more easily
        if asset_type in ['crypto', 'ipo', 'growth']:
            cascade_threshold = 1.5  # Lower threshold for volatile assets
        else:
            cascade_threshold = 2.0  # Higher threshold for stable assets
            
        # Determine phase transition type based on volume
        if volume_surge > cascade_threshold:
            return 'cascade'  # High volume = continuation
        else:
            return 'crystallize'  # Normal volume = reversal
    
    def execute_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        asset_type: str = 'unknown',
        verbose: bool = True
    ) -> Optional[Dict]:
        """
        Backtest the strategy on historical data.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            asset_type: Type of asset for parameter tuning
            verbose: Print trade details during backtest
            
        Returns:
            Dictionary containing trade results and statistics
        """
        if verbose:
            print(f"\nBacktesting {symbol} ({asset_type}) from {start_date} to {end_date}")
            print("-" * 60)
        
        # Fetch historical data
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
        
        # Ensure sufficient data
        if len(data) < self.lookback_days + 10:
            print(f"Insufficient data for {symbol}")
            return None
            
        # Extract arrays
        prices = data['Close'].values
        volumes = data['Volume'].values
        dates = data.index
        
        # Trading state
        position = 0  # 0: flat, 1: long, -1: short
        entry_price = 0
        entry_date = None
        
        # Results storage
        trades = []
        signals = []
        
        # Scan through historical data
        for i in range(self.lookback_days + self.threshold_days, len(prices) - 1):
            current_price = prices[i]
            current_date = dates[i]
            
            # Check for phase transition
            transition = self.detect_phase_transition(prices, volumes, i, asset_type)
            
            # Entry logic: Enter position on phase transition
            if transition and position == 0:
                memory_factor = self.calculate_memory_factor(prices, i)
                volume_surge = self.calculate_volume_surge(volumes, i)
                
                if transition == 'cascade':
                    # Go long on cascade
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    if verbose:
                        print(f"  LONG @ ${current_price:.2f} on {current_date.date()}")
                        print(f"    Memory Factor: {memory_factor:.2f}, Volume Surge: {volume_surge:.2f}")
                    
                elif transition == 'crystallize':
                    # Go short on crystallization
                    position = -1
                    entry_price = current_price
                    entry_date = current_date
                    if verbose:
                        print(f"  SHORT @ ${current_price:.2f} on {current_date.date()}")
                        print(f"    Memory Factor: {memory_factor:.2f}, Volume Surge: {volume_surge:.2f}")
                
                # Record signal
                signals.append({
                    'date': current_date,
                    'type': transition,
                    'memory_factor': memory_factor,
                    'volume_surge': volume_surge
                })
            
            # Exit logic: Time-based and stop-loss/take-profit
            if position != 0:
                days_held = (current_date - entry_date).days
                price_change = (current_price / entry_price - 1) * position
                
                # Different exit rules for longs vs shorts
                if position == 1:  # Long position
                    # Exit if: held 20+ days, +30% profit, or -15% loss
                    exit_signal = (
                        days_held >= 20 or
                        price_change >= 0.30 or
                        price_change <= -0.15
                    )
                else:  # Short position
                    # Exit if: held 30+ days, +25% profit, or -20% loss
                    exit_signal = (
                        days_held >= 30 or
                        price_change >= 0.25 or
                        price_change <= -0.20
                    )
                
                if exit_signal:
                    exit_price = current_price
                    pnl = (exit_price / entry_price - 1) * position
                    
                    # Record trade
                    trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': 'LONG' if position == 1 else 'SHORT',
                        'pnl_pct': pnl * 100,
                        'days_held': days_held
                    })
                    
                    if verbose:
                        print(f"  CLOSE @ ${exit_price:.2f} ({pnl*100:+.1f}% in {days_held} days)")
                    
                    # Reset position
                    position = 0
                    entry_price = 0
                    entry_date = None
        
        # Compile results
        results = {
            'symbol': symbol,
            'trades': trades,
            'signals': signals,
            'asset_type': asset_type
        }
        
        # Calculate statistics if trades exist
        if trades:
            df = pd.DataFrame(trades)
            winners = df[df['pnl_pct'] > 0]
            losers = df[df['pnl_pct'] < 0]
            
            results['statistics'] = {
                'total_trades': len(df),
                'win_rate': len(winners) / len(df) * 100,
                'avg_win': winners['pnl_pct'].mean() if len(winners) > 0 else 0,
                'avg_loss': losers['pnl_pct'].mean() if len(losers) > 0 else 0,
                'avg_pnl': df['pnl_pct'].mean(),
                'total_pnl': df['pnl_pct'].sum(),
                'avg_days_held': df['days_held'].mean(),
                'best_trade': df['pnl_pct'].max(),
                'worst_trade': df['pnl_pct'].min()
            }
            
            if verbose:
                print(f"\nSummary: {len(df)} trades, {results['statistics']['win_rate']:.1f}% win rate")
                print(f"         Avg P&L: {results['statistics']['avg_pnl']:+.1f}%")
        
        return results
    
    def check_current_signal(
        self,
        symbol: str,
        asset_type: str = 'unknown'
    ) -> Optional[Dict]:
        """
        Check for current trading signal on a given symbol.
        
        Args:
            symbol: Stock ticker symbol
            asset_type: Type of asset for parameter tuning
            
        Returns:
            Dictionary with signal details or None if no signal
        """
        # Fetch recent data (60 days to ensure enough history)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
        
        if len(data) < self.lookback_days + self.threshold_days:
            return None
            
        prices = data['Close'].values
        volumes = data['Volume'].values
        
        # Check most recent data point
        current_idx = len(prices) - 1
        transition = self.detect_phase_transition(prices, volumes, current_idx, asset_type)
        
        if transition:
            memory_factor = self.calculate_memory_factor(prices, current_idx)
            volume_surge = self.calculate_volume_surge(volumes, current_idx)
            
            return {
                'symbol': symbol,
                'date': data.index[-1],
                'signal': transition,
                'memory_factor': memory_factor,
                'volume_surge': volume_surge,
                'current_price': prices[-1],
                'recommendation': 'LONG' if transition == 'cascade' else 'SHORT'
            }
        
        return None


def display_backtest_results(results: List[Dict]) -> None:
    """
    Display comprehensive backtest results.
    
    Args:
        results: List of backtest result dictionaries
    """
    all_trades = []
    
    for result in results:
        if result and result['trades']:
            all_trades.extend(result['trades'])
    
    if not all_trades:
        print("No trades generated in backtest")
        return
    
    df = pd.DataFrame(all_trades)
    
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 70)
    
    # Overall statistics
    total_trades = len(df)
    winners = df[df['pnl_pct'] > 0]
    win_rate = len(winners) / total_trades * 100
    
    print(f"\nTotal Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Average P&L: {df['pnl_pct'].mean():+.1f}%")
    print(f"Total P&L: {df['pnl_pct'].sum():+.1f}%")
    
    if len(winners) > 0:
        print(f"Average Win: {winners['pnl_pct'].mean():+.1f}%")
    if len(winners) < total_trades:
        losers = df[df['pnl_pct'] < 0]
        print(f"Average Loss: {losers['pnl_pct'].mean():+.1f}%")
    
    # Performance by symbol
    print("\nPerformance by Symbol:")
    print("-" * 40)
    for symbol in df['symbol'].unique():
        symbol_trades = df[df['symbol'] == symbol]
        symbol_wr = len(symbol_trades[symbol_trades['pnl_pct'] > 0]) / len(symbol_trades) * 100
        symbol_pnl = symbol_trades['pnl_pct'].mean()
        print(f"{symbol:6s}: {len(symbol_trades):3d} trades, {symbol_wr:5.1f}% WR, {symbol_pnl:+6.1f}% avg")
    
    # Best and worst trades
    print("\nTop 5 Best Trades:")
    print("-" * 40)
    for _, trade in df.nlargest(5, 'pnl_pct').iterrows():
        print(f"{trade['symbol']:6s}: {trade['pnl_pct']:+6.1f}% ({trade['position']}, {trade['days_held']} days)")
    
    print("\nTop 5 Worst Trades:")
    print("-" * 40)
    for _, trade in df.nsmallest(5, 'pnl_pct').iterrows():
        print(f"{trade['symbol']:6s}: {trade['pnl_pct']:+6.1f}% ({trade['position']}, {trade['days_held']} days)")
    
    # Position type analysis
    longs = df[df['position'] == 'LONG']
    shorts = df[df['position'] == 'SHORT']
    
    print("\nPosition Analysis:")
    print("-" * 40)
    if len(longs) > 0:
        long_wr = len(longs[longs['pnl_pct'] > 0]) / len(longs) * 100
        print(f"Longs:  {len(longs):3d} trades, {long_wr:5.1f}% WR, {longs['pnl_pct'].mean():+6.1f}% avg")
    if len(shorts) > 0:
        short_wr = len(shorts[shorts['pnl_pct'] > 0]) / len(shorts) * 100
        print(f"Shorts: {len(shorts):3d} trades, {short_wr:5.1f}% WR, {shorts['pnl_pct'].mean():+6.1f}% avg")
    
    print("\n" + "=" * 70)