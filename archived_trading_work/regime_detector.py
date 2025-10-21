"""
Unified Regime-Aware Phase Transition Detector
===============================================
ONE system that adapts to market conditions.

The key insight: Phase transitions are universal, but their resolution
direction is biased by the underlying market regime.

Think of it like this:
- In a hot room, ice is more likely to melt (upward transition)
- In a cold room, water is more likely to freeze (downward transition)
- At perfect equilibrium, both are equally likely
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf


class RegimeAwarePhaseDetector:
    """
    Unified detector that adjusts phase transition interpretation based on market regime.
    
    Core Principle: The memory factor tells us WHEN a phase transition occurs,
    but the market regime tells us HOW it will likely resolve.
    """
    
    def __init__(
        self,
        lookback_days: int = 30,
        threshold_days: int = 5,
        memory_threshold: float = 1.25,
        regime_lookback: int = 50  # For trend detection
    ):
        self.lookback_days = lookback_days
        self.threshold_days = threshold_days
        self.memory_threshold = memory_threshold
        self.regime_lookback = regime_lookback
        
    def calculate_memory_factor(self, prices: np.ndarray, current_idx: int) -> float:
        """Calculate memory factor (unchanged - this works perfectly)"""
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
    
    def calculate_regime_bias(self, prices: np.ndarray, current_idx: int) -> float:
        """
        Calculate market regime bias (-1 to +1).
        
        +1.0 = Strong bull regime (CASCADE more likely)
        0.0 = Neutral regime (both equally likely)
        -1.0 = Strong bear regime (CRYSTALLIZE more likely)
        
        This uses multiple factors:
        1. Short-term trend (20-day)
        2. Medium-term trend (50-day)
        3. Momentum consistency
        """
        if current_idx < self.regime_lookback:
            return 0.0
        
        # Factor 1: Price relative to moving averages
        ma20 = np.mean(prices[current_idx-20:current_idx])
        ma50 = np.mean(prices[current_idx-50:current_idx])
        current_price = prices[current_idx]
        
        # How far above/below MAs are we?
        ma20_distance = (current_price - ma20) / ma20
        ma50_distance = (current_price - ma50) / ma50
        
        # Factor 2: Trend strength (MA alignment)
        ma_alignment = (ma20 - ma50) / ma50
        
        # Factor 3: Recent momentum consistency
        # Count how many of last 10 days were positive
        recent_changes = np.diff(prices[current_idx-10:current_idx])
        positive_days = np.sum(recent_changes > 0) / len(recent_changes)
        momentum_consistency = (positive_days - 0.5) * 2  # Scale to -1 to +1
        
        # Factor 4: Volatility regime
        # High volatility in uptrend = more bullish
        # High volatility in downtrend = more bearish
        returns = np.diff(prices[current_idx-20:current_idx]) / prices[current_idx-20:current_idx-1]
        volatility = np.std(returns)
        trend_direction = 1 if ma20 > ma50 else -1
        volatility_factor = volatility * trend_direction * 10  # Scale appropriately
        
        # Combine factors with weights
        regime_bias = (
            ma20_distance * 0.25 +      # Price vs short MA
            ma50_distance * 0.25 +      # Price vs medium MA
            ma_alignment * 0.25 +       # Trend alignment
            momentum_consistency * 0.15 + # Recent consistency
            volatility_factor * 0.10     # Volatility adjustment
        )
        
        # Clip to [-1, 1] range
        return np.clip(regime_bias, -1.0, 1.0)
    
    def detect_phase_transition(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        current_idx: int
    ) -> tuple:
        """
        Detect phase transition with regime awareness.
        
        Returns:
            (signal, confidence, regime_bias)
            signal: 'LONG', 'SHORT', or None
            confidence: 0.0 to 1.0
            regime_bias: -1.0 to 1.0 (bear to bull)
        """
        # Calculate memory factor (phase transition detector)
        memory_factor = self.calculate_memory_factor(prices, current_idx)
        
        # No phase transition
        if memory_factor < self.memory_threshold:
            return None, 0, 0
        
        # Calculate regime bias
        regime_bias = self.calculate_regime_bias(prices, current_idx)
        
        # Calculate volume confirmation
        recent_volume = np.mean(volumes[current_idx-5:current_idx])
        baseline_volume = np.mean(volumes[current_idx-30:current_idx-5])
        volume_surge = recent_volume / max(baseline_volume, 1)
        
        # Unified decision logic
        # The key insight: regime bias adjusts the interpretation threshold
        
        # Base cascade threshold (for neutral market)
        base_cascade_threshold = 2.0
        
        # Adjust threshold based on regime
        # In bull market: easier to cascade (lower threshold)
        # In bear market: harder to cascade (higher threshold)
        cascade_threshold = base_cascade_threshold * (1 - regime_bias * 0.5)
        
        # Memory strength affects confidence
        memory_strength = min(memory_factor / self.memory_threshold - 1, 2.0) / 2.0
        
        # Decision with regime awareness
        if regime_bias > 0.3:  # Bull regime
            # In bull markets, phase transitions likely resolve upward
            if volume_surge > cascade_threshold * 0.7:  # Lower threshold
                confidence = min(0.5 + memory_strength * 0.3 + regime_bias * 0.2, 1.0)
                return 'LONG', confidence, regime_bias
            elif volume_surge < cascade_threshold * 0.5 and regime_bias < 0.5:
                # Only short if not too bullish and volume is really low
                confidence = min(0.3 + memory_strength * 0.2, 0.6)
                return 'SHORT', confidence, regime_bias
                
        elif regime_bias < -0.3:  # Bear regime
            # In bear markets, phase transitions likely resolve downward
            if volume_surge < cascade_threshold * 1.3:  # Higher threshold for longs
                confidence = min(0.5 + memory_strength * 0.3 + abs(regime_bias) * 0.2, 1.0)
                return 'SHORT', confidence, regime_bias
            elif volume_surge > cascade_threshold * 1.5 and regime_bias > -0.5:
                # Only long if really strong volume and not too bearish
                confidence = min(0.3 + memory_strength * 0.2, 0.6)
                return 'LONG', confidence, regime_bias
                
        else:  # Neutral regime (-0.3 to 0.3)
            # Original logic works best here
            if volume_surge > cascade_threshold:
                confidence = min(0.5 + memory_strength * 0.5, 1.0)
                return 'LONG', confidence, regime_bias
            else:
                confidence = min(0.5 + memory_strength * 0.5, 1.0)
                return 'SHORT', confidence, regime_bias
        
        return None, 0, regime_bias
    
    def get_regime_description(self, regime_bias: float) -> str:
        """Convert regime bias to human-readable description"""
        if regime_bias > 0.6:
            return "STRONG BULL"
        elif regime_bias > 0.3:
            return "BULL"
        elif regime_bias > -0.3:
            return "NEUTRAL"
        elif regime_bias > -0.6:
            return "BEAR"
        else:
            return "STRONG BEAR"


def test_regime_detector():
    """Test the unified regime-aware detector"""
    
    print("="*70)
    print("TESTING UNIFIED REGIME-AWARE PHASE DETECTOR")
    print("="*70)
    
    detector = RegimeAwarePhaseDetector()
    
    # Test on key periods (need earlier start for 50-day MA)
    test_cases = [
        ('SPY', '2019-12-01', '2020-04-01', 'COVID Crash'),
        ('SPY', '2020-02-01', '2020-05-01', 'Recovery'),
        ('SPY', '2022-10-01', '2023-02-01', 'Early 2023'),
        ('SPY', '2023-08-01', '2023-12-01', 'Late 2023 Rally'),
        ('COIN', '2023-03-01', '2023-07-01', 'COIN Bull Run'),
        ('COIN', '2022-02-01', '2022-06-01', 'Crypto Winter')
    ]
    
    for symbol, start, end, description in test_cases:
        print(f"\n{description}: {symbol} ({start} to {end})")
        print("-"*40)
        
        # Fetch data
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start, end=end)
        
        if len(data) < 50:
            print("Insufficient data")
            continue
            
        prices = data['Close'].values
        volumes = data['Volume'].values
        
        # Test at the end of the period
        idx = len(prices) - 1
        
        memory_factor = detector.calculate_memory_factor(prices, idx)
        regime_bias = detector.calculate_regime_bias(prices, idx)
        signal, confidence, bias = detector.detect_phase_transition(prices, volumes, idx)
        
        print(f"Memory Factor: {memory_factor:.2f}")
        print(f"Regime: {detector.get_regime_description(regime_bias)} ({regime_bias:+.2f})")
        
        if signal:
            print(f"Signal: {signal} (Confidence: {confidence:.1%})")
        else:
            print("No signal")
    
    print("\n" + "="*70)
    print("UNIFIED SYSTEM BENEFITS:")
    print("1. Single detector adapts to all regimes")
    print("2. Confidence scores help with position sizing")
    print("3. Regime bias can be used for risk management")
    print("4. No need to switch strategies")
    print("="*70)


if __name__ == "__main__":
    test_regime_detector()