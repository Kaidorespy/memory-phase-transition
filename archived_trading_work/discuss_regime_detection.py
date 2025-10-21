#!/usr/bin/env python3
"""
Discuss regime detection with ChatGPT
=====================================
Get a second opinion on how to detect market regimes for our phase transition strategy.
"""

import sys
import os
sys.path.append(r'C:\Users\Casey\ORGANIZED_HOME\ChatGPT_Tools')

from chatgpt_cli import ChatGPTCLI

def main():
    # Initialize ChatGPT
    chat = ChatGPTCLI()
    
    # Our question about regime detection
    prompt = """
I've discovered that markets undergo memory-induced phase transitions similar to physical systems. 
When momentum accumulates too quickly (memory factor > 1.25), the system becomes unstable and either:
- CASCADES (continues up explosively) 
- CRYSTALLIZES (reverses/freezes)

The strategy works great in normal markets (51% win rate, +154% returns in 2020-2022).
But in the 2023-2024 bull market, SHORT signals failed badly while LONG signals thrived.

Key findings:
- In balanced markets: Both CASCADE (long) and CRYSTALLIZE (short) signals work
- In bull markets: Only CASCADE signals work (shorts get destroyed)
- The phase transitions ARE real, but resolution direction depends on market regime

I need a SINGLE unified detector that can:
1. Detect phase transitions (already have this - memory factor calculation)
2. Determine which direction they'll resolve based on market regime
3. Work across different market conditions

What's the most elegant way to build regime awareness into the phase transition detection?
Should I:
- Add a trend filter (like 50/200 MA)?
- Use market breadth indicators?
- Modify the memory factor calculation itself to account for regime?
- Something else?

The goal is ONE elegant system, not switching between multiple strategies.
What would you suggest?
"""
    
    print("="*70)
    print("CONSULTING CHATGPT ON REGIME DETECTION")
    print("="*70)
    print("\nOur question:")
    print("-"*40)
    print(prompt)
    print("-"*40)
    
    # Get ChatGPT's response
    print("\nChatGPT's response:")
    print("="*70)
    
    # Send the message
    chat.conversation = []  # Start fresh conversation
    chat.conversation.append({"role": "user", "content": prompt})
    
    try:
        response = chat.send_message("")  # Empty since we already added to conversation
        print(response)
    except Exception as e:
        print(f"Error communicating with ChatGPT: {e}")
        print("\nAlternative: Let's design our own regime detection...")
        
        # Our own ideas
        print("""
FALLBACK REGIME DETECTION IDEAS:

1. **Regime-Aware Memory Factor:**
   - In uptrends: Crystallization threshold increases (harder to short)
   - In downtrends: Cascade threshold increases (harder to long)
   
2. **Volatility-Adjusted Signals:**
   - High volatility + phase transition = higher confidence
   - Low volatility + phase transition = regime dependent
   
3. **Market Structure Filter:**
   - Count % of stocks above 50-day MA
   - >70% = Bull regime (CASCADE only)
   - <30% = Bear regime (CRYSTALLIZE only)  
   - 30-70% = Balanced (both signals)

4. **Dynamic Threshold Based on Trend:**
   memory_threshold = base_threshold * (1 + trend_strength)
   - Uptrend makes crystallization harder
   - Downtrend makes cascade harder
   
5. **Volume Confirmation Enhanced:**
   - Bull regime: Lower volume threshold for longs
   - Bear regime: Lower volume threshold for shorts
""")

if __name__ == "__main__":
    main()