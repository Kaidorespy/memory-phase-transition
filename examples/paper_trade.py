#!/usr/bin/env python3
"""
Paper Trading Bot
=================
Monitor multiple stocks for phase transition signals and track paper trades.

This script checks a portfolio of stocks daily for trading signals and
maintains a paper trading log to test the strategy without real money.

Usage:
    python paper_trade.py                  # Check default portfolio
    python paper_trade.py --symbols COIN,RIOT,PLTR  # Custom symbols
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.phase_transition_strategy import PhaseTransitionStrategy
from datetime import datetime, timedelta
import json
import argparse
from typing import List, Dict
import pandas as pd


class PaperTradingBot:
    """
    Manages paper trading using the phase transition strategy.
    """
    
    def __init__(self, capital: float = 10000.0, position_size: float = 0.1):
        """
        Initialize paper trading bot.
        
        Args:
            capital: Starting capital for paper trading
            position_size: Fraction of capital to use per trade (0.1 = 10%)
        """
        self.strategy = PhaseTransitionStrategy()
        self.starting_capital = capital
        self.current_capital = capital
        self.position_size = position_size
        self.positions = []  # Active positions
        self.closed_trades = []  # Completed trades
        self.trade_log_file = "paper_trades.json"
        self.load_trades()
    
    def load_trades(self):
        """Load existing paper trades from file."""
        if os.path.exists(self.trade_log_file):
            try:
                with open(self.trade_log_file, 'r') as f:
                    data = json.load(f)
                    self.positions = data.get('positions', [])
                    self.closed_trades = data.get('closed_trades', [])
                    self.current_capital = data.get('current_capital', self.starting_capital)
                    print(f"Loaded {len(self.positions)} open positions and {len(self.closed_trades)} closed trades")
            except Exception as e:
                print(f"Error loading trades: {e}")
    
    def save_trades(self):
        """Save paper trades to file."""
        data = {
            'positions': self.positions,
            'closed_trades': self.closed_trades,
            'current_capital': self.current_capital,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.trade_log_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def check_signals(self, symbols: List[str], asset_types: Dict[str, str] = None):
        """
        Check for trading signals on specified symbols.
        
        Args:
            symbols: List of stock symbols to check
            asset_types: Dictionary mapping symbols to asset types
        """
        asset_types = asset_types or {}
        signals_found = []
        
        print(f"\n{'='*60}")
        print(f"CHECKING SIGNALS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")
        
        for symbol in symbols:
            # Skip if we already have a position
            if any(p['symbol'] == symbol for p in self.positions):
                print(f"{symbol}: Already have open position")
                continue
            
            # Check for signal
            asset_type = asset_types.get(symbol, 'unknown')
            signal = self.strategy.check_current_signal(symbol, asset_type)
            
            if signal:
                signals_found.append(signal)
                print(f"{symbol}: {signal['signal'].upper()} signal detected!")
                print(f"  Memory Factor: {signal['memory_factor']:.2f}")
                print(f"  Volume Surge: {signal['volume_surge']:.2f}")
                print(f"  Recommendation: {signal['recommendation']}")
            else:
                print(f"{symbol}: No signal")
        
        return signals_found
    
    def enter_positions(self, signals: List[Dict]):
        """
        Enter paper positions based on signals.
        
        Args:
            signals: List of signal dictionaries
        """
        for signal in signals:
            # Calculate position size
            trade_capital = self.current_capital * self.position_size
            shares = int(trade_capital / signal['current_price'])
            
            if shares > 0:
                position = {
                    'symbol': signal['symbol'],
                    'entry_date': datetime.now().isoformat(),
                    'entry_price': signal['current_price'],
                    'shares': shares,
                    'position_type': signal['recommendation'],
                    'signal_type': signal['signal'],
                    'memory_factor': signal['memory_factor'],
                    'volume_surge': signal['volume_surge'],
                    'stop_loss': signal['current_price'] * (0.85 if signal['recommendation'] == 'LONG' else 1.20),
                    'take_profit': signal['current_price'] * (1.30 if signal['recommendation'] == 'LONG' else 0.75)
                }
                
                self.positions.append(position)
                print(f"\n📈 PAPER TRADE ENTERED:")
                print(f"  {position['symbol']}: {position['position_type']} {shares} shares @ ${position['entry_price']:.2f}")
                print(f"  Stop Loss: ${position['stop_loss']:.2f}")
                print(f"  Take Profit: ${position['take_profit']:.2f}")
    
    def update_positions(self):
        """
        Update existing positions and check for exits.
        """
        if not self.positions:
            return
        
        print(f"\n{'='*60}")
        print("UPDATING POSITIONS")
        print(f"{'='*60}")
        
        positions_to_close = []
        
        for position in self.positions:
            try:
                # Get current price
                import yfinance as yf
                ticker = yf.Ticker(position['symbol'])
                current_data = ticker.history(period='1d')
                if len(current_data) == 0:
                    continue
                    
                current_price = current_data['Close'].iloc[-1]
                
                # Calculate P&L
                if position['position_type'] == 'LONG':
                    pnl_pct = (current_price / position['entry_price'] - 1) * 100
                else:  # SHORT
                    pnl_pct = (1 - current_price / position['entry_price']) * 100
                
                # Check exit conditions
                days_held = (datetime.now() - datetime.fromisoformat(position['entry_date'])).days
                
                should_exit = False
                exit_reason = ""
                
                # Check stop loss
                if position['position_type'] == 'LONG' and current_price <= position['stop_loss']:
                    should_exit = True
                    exit_reason = "Stop Loss"
                elif position['position_type'] == 'SHORT' and current_price >= position['stop_loss']:
                    should_exit = True
                    exit_reason = "Stop Loss"
                
                # Check take profit
                elif position['position_type'] == 'LONG' and current_price >= position['take_profit']:
                    should_exit = True
                    exit_reason = "Take Profit"
                elif position['position_type'] == 'SHORT' and current_price <= position['take_profit']:
                    should_exit = True
                    exit_reason = "Take Profit"
                
                # Check time limit
                elif days_held >= 30:
                    should_exit = True
                    exit_reason = "Time Limit"
                
                # Display position status
                print(f"{position['symbol']} ({position['position_type']}): ${current_price:.2f} ({pnl_pct:+.1f}%) - {days_held} days")
                
                if should_exit:
                    # Close position
                    closed_trade = position.copy()
                    closed_trade['exit_date'] = datetime.now().isoformat()
                    closed_trade['exit_price'] = current_price
                    closed_trade['pnl_pct'] = pnl_pct
                    closed_trade['pnl_dollars'] = position['shares'] * (current_price - position['entry_price']) * (1 if position['position_type'] == 'LONG' else -1)
                    closed_trade['exit_reason'] = exit_reason
                    closed_trade['days_held'] = days_held
                    
                    self.closed_trades.append(closed_trade)
                    positions_to_close.append(position)
                    self.current_capital += closed_trade['pnl_dollars']
                    
                    print(f"  ❌ CLOSING: {exit_reason} - P&L: {pnl_pct:+.1f}% (${closed_trade['pnl_dollars']:+.2f})")
                    
            except Exception as e:
                print(f"Error updating {position['symbol']}: {e}")
        
        # Remove closed positions
        for position in positions_to_close:
            self.positions.remove(position)
    
    def display_summary(self):
        """Display paper trading performance summary."""
        print(f"\n{'='*60}")
        print("PAPER TRADING SUMMARY")
        print(f"{'='*60}")
        
        print(f"Starting Capital: ${self.starting_capital:,.2f}")
        print(f"Current Capital:  ${self.current_capital:,.2f}")
        print(f"Total P&L:        ${self.current_capital - self.starting_capital:+,.2f}")
        print(f"Return:           {(self.current_capital/self.starting_capital - 1)*100:+.1f}%")
        
        if self.positions:
            print(f"\nOpen Positions: {len(self.positions)}")
            for p in self.positions:
                print(f"  {p['symbol']}: {p['position_type']} @ ${p['entry_price']:.2f}")
        
        if self.closed_trades:
            df = pd.DataFrame(self.closed_trades)
            winners = df[df['pnl_pct'] > 0]
            
            print(f"\nClosed Trades: {len(self.closed_trades)}")
            print(f"Win Rate:      {len(winners)/len(df)*100:.1f}%")
            print(f"Avg P&L:       {df['pnl_pct'].mean():+.1f}%")
            
            print(f"\nLast 5 Trades:")
            for trade in self.closed_trades[-5:]:
                print(f"  {trade['symbol']}: {trade['pnl_pct']:+.1f}% ({trade['exit_reason']})")
    
    def run_daily_check(self, symbols: List[str], asset_types: Dict[str, str] = None):
        """
        Run daily paper trading routine.
        
        Args:
            symbols: List of symbols to monitor
            asset_types: Asset type classifications
        """
        # Check for new signals
        signals = self.check_signals(symbols, asset_types)
        
        # Enter new positions
        if signals:
            self.enter_positions(signals)
        
        # Update existing positions
        self.update_positions()
        
        # Display summary
        self.display_summary()
        
        # Save trades
        self.save_trades()
        print(f"\nTrades saved to {self.trade_log_file}")


def main():
    """Main entry point for paper trading bot."""
    parser = argparse.ArgumentParser(description='Paper Trading Bot for Phase Transition Strategy')
    parser.add_argument('--symbols', type=str, 
                       default='COIN,RIOT,PLTR,MARA,ABNB,SNOW',
                       help='Comma-separated list of symbols to monitor')
    parser.add_argument('--capital', type=float, default=10000,
                       help='Starting capital for paper trading')
    parser.add_argument('--position-size', type=float, default=0.1,
                       help='Fraction of capital per trade (0.1 = 10%)')
    
    args = parser.parse_args()
    
    # Parse symbols
    symbols = [s.strip().upper() for s in args.symbols.split(',')]
    
    # Define asset types for better signal detection
    asset_types = {
        'COIN': 'crypto',
        'RIOT': 'crypto',
        'MARA': 'crypto',
        'PLTR': 'ipo',
        'ABNB': 'ipo',
        'SNOW': 'ipo',
        'TSLA': 'growth',
        'NVDA': 'growth',
        'AMD': 'growth'
    }
    
    # Initialize bot
    bot = PaperTradingBot(capital=args.capital, position_size=args.position_size)
    
    # Run daily check
    bot.run_daily_check(symbols, asset_types)


if __name__ == "__main__":
    main()