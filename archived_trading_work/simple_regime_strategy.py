"""
Simple Regime-Aware Trading Strategy
=====================================
KISS principle: Keep It Simple, Stupid.

If the market is obviously trending up, don't fight it.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf


class SimpleRegimeTrader:
    """
    Phase transition detector with dead-simple regime filter.
    
    Philosophy: The phase transitions are real, but in strong trends
    they resolve in the direction of the trend.
    """
    
    def __init__(
        self,
        lookback_days: int = 30,
        threshold_days: int = 5,
        memory_threshold: float = 1.25,
        volume_surge: float = 2.0
    ):
        self.lookback_days = lookback_days
        self.threshold_days = threshold_days
        self.memory_threshold = memory_threshold
        self.volume_surge_threshold = volume_surge
        
    def calculate_memory_factor(self, prices: np.ndarray, current_idx: int) -> float:
        """Calculate memory factor (our proven edge)"""
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
            
        return recent_daily_rate / baseline_daily_rate
    
    def detect_regime(self, prices: np.ndarray, current_idx: int) -> str:
        """
        Dead simple regime detection.
        
        Returns: 'BULL', 'BEAR', or 'NEUTRAL'
        """
        if current_idx < 200:  # Need 200 days for MA
            return 'NEUTRAL'
        
        # Calculate moving averages
        ma50 = np.mean(prices[current_idx-50:current_idx])
        ma200 = np.mean(prices[current_idx-200:current_idx])
        current_price = prices[current_idx]
        
        # Also check recent momentum
        price_20d_ago = prices[current_idx-20]
        momentum_20d = (current_price / price_20d_ago - 1) * 100
        
        # Bull market conditions (multiple confirmations)
        if (current_price > ma50 > ma200 and  # Golden alignment
            momentum_20d > 5):                  # Positive momentum
            return 'BULL'
        
        # Bear market conditions
        elif (current_price < ma50 < ma200 and  # Death cross alignment
              momentum_20d < -5):                # Negative momentum
            return 'BEAR'
        
        # Everything else is neutral
        else:
            return 'NEUTRAL'
    
    def should_take_signal(
        self,
        signal_type: str,
        regime: str,
        memory_factor: float
    ) -> bool:
        """
        Decide whether to take a signal based on regime.
        
        The key insight: In strong trends, only take signals
        that align with the trend.
        """
        if regime == 'BULL':
            # In bull markets, only take LONG signals
            # Unless memory factor is EXTREME (>3.0) for shorts
            if signal_type == 'LONG':
                return True
            elif signal_type == 'SHORT' and memory_factor > 3.0:
                return True  # Extreme readings might still work
            else:
                return False
                
        elif regime == 'BEAR':
            # In bear markets, only take SHORT signals
            # Unless memory factor is EXTREME for longs
            if signal_type == 'SHORT':
                return True
            elif signal_type == 'LONG' and memory_factor > 3.0:
                return True
            else:
                return False
                
        else:  # NEUTRAL
            # In neutral markets, take all signals
            return True
    
    def backtest(self, symbol: str, start_date: str, end_date: str):
        """Run backtest with simple regime filter"""
        
        print(f"\nTesting {symbol} from {start_date} to {end_date}")
        
        # Fetch data with buffer for 200-day MA
        ticker = yf.Ticker(symbol)
        buffer_start = pd.to_datetime(start_date) - pd.Timedelta(days=250)
        data = ticker.history(start=buffer_start, end=end_date)
        
        if len(data) < 250:
            print(f"  Insufficient data for {symbol}")
            return None
        
        # Find actual start
        start_idx = None
        start_date_ts = pd.to_datetime(start_date).tz_localize(None)
        for i, date in enumerate(data.index):
            if date.tz_localize(None) >= start_date_ts:
                start_idx = i
                break
        
        if not start_idx or start_idx < 200:
            start_idx = 200
            
        prices = data['Close'].values
        volumes = data['Volume'].values
        dates = data.index
        
        trades = []
        position = None
        entry_price = 0
        entry_date = None
        signals_rejected = 0
        
        for i in range(start_idx, len(prices) - 1):
            current_price = prices[i]
            current_date = dates[i]
            
            # Check for phase transition
            memory_factor = self.calculate_memory_factor(prices, i)
            
            if memory_factor > self.memory_threshold and position is None:
                # Detect regime
                regime = self.detect_regime(prices, i)
                
                # Calculate volume for signal type
                recent_volume = np.mean(volumes[i-5:i])
                baseline_volume = np.mean(volumes[i-30:i-5])
                volume_surge = recent_volume / max(baseline_volume, 1)
                
                # Determine signal type
                if volume_surge > self.volume_surge_threshold:
                    signal_type = 'LONG'  # CASCADE
                else:
                    signal_type = 'SHORT'  # CRYSTALLIZE
                
                # Check if we should take this signal
                if self.should_take_signal(signal_type, regime, memory_factor):
                    position = signal_type
                    entry_price = current_price
                    entry_date = current_date
                    print(f"  {signal_type} @ ${current_price:.2f} on {current_date.date()}")
                    print(f"    Regime: {regime}, Memory: {memory_factor:.2f}, Volume: {volume_surge:.2f}")
                else:
                    signals_rejected += 1
                    # print(f"  [REJECTED {signal_type} - {regime} regime]")
            
            # Exit logic
            elif position:
                days_held = (current_date - entry_date).days
                
                if position == 'LONG':
                    pnl_pct = (current_price / entry_price - 1) * 100
                    exit_signal = days_held >= 20 or pnl_pct >= 30 or pnl_pct <= -15
                else:  # SHORT
                    pnl_pct = (1 - current_price / entry_price) * 100
                    exit_signal = days_held >= 30 or pnl_pct >= 25 or pnl_pct <= -20
                
                if exit_signal:
                    trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position': position,
                        'pnl_pct': pnl_pct,
                        'days_held': days_held
                    })
                    
                    print(f"  CLOSE @ ${current_price:.2f} ({pnl_pct:+.1f}% in {days_held}d)")
                    
                    position = None
                    entry_price = 0
                    entry_date = None
        
        if signals_rejected > 0:
            print(f"  [Rejected {signals_rejected} signals due to regime filter]")
            
        return trades


def run_comprehensive_test():
    """Test the simple regime strategy across all periods"""
    
    print("="*70)
    print("SIMPLE REGIME-AWARE STRATEGY TEST")
    print("="*70)
    print("Philosophy: Don't fight the trend.")
    
    trader = SimpleRegimeTrader()
    
    # Test periods
    test_configs = [
        # Training period
        ("2020-01-01", "2023-01-01", "Training", [
            ('COIN', '2021-04-14'),  # IPO date
            ('RIOT', '2020-01-01'),
            ('PLTR', '2020-09-30'),  # IPO date
            ('META', '2020-01-01'),
            ('NVDA', '2020-01-01')
        ]),
        # Out of sample
        ("2023-01-01", "2024-12-31", "Out-of-Sample", [
            ('COIN', '2023-01-01'),
            ('RIOT', '2023-01-01'),
            ('PLTR', '2023-01-01'),
            ('META', '2023-01-01'),
            ('NVDA', '2023-01-01')
        ])
    ]
    
    for period_start, period_end, period_name, stocks in test_configs:
        print(f"\n{'='*70}")
        print(f"{period_name}: {period_start} to {period_end}")
        print(f"{'='*70}")
        
        all_trades = []
        
        for symbol, start_override in stocks:
            trades = trader.backtest(symbol, start_override, period_end)
            if trades:
                all_trades.extend(trades)
                
                df = pd.DataFrame(trades)
                win_rate = len(df[df['pnl_pct'] > 0]) / len(df) * 100
                avg_pnl = df['pnl_pct'].mean()
                total_pnl = df['pnl_pct'].sum()
                
                print(f"  Summary: {len(df)} trades, {win_rate:.1f}% WR, {avg_pnl:+.1f}% avg, {total_pnl:+.1f}% total")
        
        # Period summary
        if all_trades:
            df_all = pd.DataFrame(all_trades)
            total_trades = len(df_all)
            winners = len(df_all[df_all['pnl_pct'] > 0])
            win_rate = winners / total_trades * 100
            avg_pnl = df_all['pnl_pct'].mean()
            total_pnl = df_all['pnl_pct'].sum()
            
            # Position breakdown
            longs = df_all[df_all['position'] == 'LONG']
            shorts = df_all[df_all['position'] == 'SHORT']
            
            print(f"\n{period_name} OVERALL:")
            print(f"  Total: {total_trades} trades, {win_rate:.1f}% WR")
            print(f"  P&L: {avg_pnl:+.1f}% avg, {total_pnl:+.1f}% total")
            
            if len(longs) > 0:
                print(f"  Longs: {len(longs)} trades, "
                      f"{len(longs[longs['pnl_pct'] > 0])/len(longs)*100:.1f}% WR, "
                      f"{longs['pnl_pct'].mean():+.1f}% avg")
            if len(shorts) > 0:
                print(f"  Shorts: {len(shorts)} trades, "
                      f"{len(shorts[shorts['pnl_pct'] > 0])/len(shorts)*100:.1f}% WR, "
                      f"{shorts['pnl_pct'].mean():+.1f}% avg")
    
    print("\n" + "="*70)
    print("SIMPLE REGIME FILTER VERDICT")
    print("="*70)
    print("Expected outcome:")
    print("- Should maintain performance in 2020-2022")
    print("- Should avoid SHORT disasters in 2023-2024")
    print("- Overall improvement in risk-adjusted returns")


if __name__ == "__main__":
    run_comprehensive_test()