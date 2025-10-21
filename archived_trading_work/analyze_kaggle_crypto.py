"""
Analyze Kaggle Crypto Data for Memory-Induced Phase Transitions
================================================================
Run this after downloading Kaggle cryptocurrency dataset
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import glob

def analyze_coin_csv(filepath, coin_name=None):
    """Analyze a single coin's CSV file"""
    try:
        # Read CSV - adjust column names based on actual format
        df = pd.read_csv(filepath)
        
        # Common column name variations
        date_cols = ['Date', 'date', 'time', 'timestamp']
        price_cols = ['Close', 'close', 'price', 'Price']
        
        # Find the right columns
        date_col = None
        price_col = None
        
        for col in date_cols:
            if col in df.columns:
                date_col = col
                break
                
        for col in price_cols:
            if col in df.columns:
                price_col = col
                break
                
        if not date_col or not price_col:
            return None
            
        # Parse dates and sort
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # Get prices
        prices = df[price_col].values
        dates = df[date_col].values
        
        # Look for pump patterns (3x moves)
        results = []
        
        for i in range(len(prices) - 60):  # Need 60 days ahead
            start_price = prices[i]
            if start_price <= 0:
                continue
                
            # Look for 3x within next 60 days
            for j in range(i+1, min(i+60, len(prices))):
                if prices[j] >= start_price * 3:
                    days_to_3x = j - i
                    
                    # Check what happened 30 days after 3x
                    if j + 30 < len(prices):
                        price_at_3x = prices[j]
                        price_30d_later = prices[j + 30]
                        post_3x_change = ((price_30d_later / price_at_3x) - 1) * 100
                        
                        result = {
                            'coin': coin_name or os.path.basename(filepath).replace('.csv', ''),
                            'date': dates[i],
                            'days_to_3x': days_to_3x,
                            'post_3x_change': post_3x_change,
                            'category': 'instant' if days_to_3x <= 5 else 'gradual' if days_to_3x >= 20 else 'medium'
                        }
                        results.append(result)
                        break  # Only take first 3x
                        
        return results
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def analyze_all_coins(data_folder):
    """Analyze all CSV files in folder"""
    csv_files = glob.glob(os.path.join(data_folder, '*.csv'))
    
    print(f"Found {len(csv_files)} CSV files")
    
    all_results = []
    
    for csv_file in csv_files[:50]:  # Limit to first 50 for speed
        coin_name = os.path.basename(csv_file).replace('.csv', '').upper()
        print(f"Analyzing {coin_name}...")
        
        results = analyze_coin_csv(csv_file, coin_name)
        if results:
            all_results.extend(results)
            print(f"  Found {len(results)} pump patterns")
            
    return all_results

def summarize_patterns(results):
    """Summarize the phase transition patterns"""
    if not results:
        print("No patterns found")
        return
        
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(results)
    
    # Filter to 2021 bull run if desired
    df['date'] = pd.to_datetime(df['date'])
    df_2021 = df[(df['date'] >= '2020-10-01') & (df['date'] <= '2021-12-31')]
    
    print("\n" + "="*70)
    print("KAGGLE CRYPTO ANALYSIS - MEMORY-INDUCED PHASE TRANSITIONS")
    print("="*70)
    
    # Analyze by category
    for period_df, period_name in [(df, 'All Time'), (df_2021, '2021 Bull Run')]:
        if len(period_df) == 0:
            continue
            
        print(f"\n{period_name.upper()} ({len(period_df)} patterns):")
        print("-"*50)
        
        instant = period_df[period_df['category'] == 'instant']
        gradual = period_df[period_df['category'] == 'gradual']
        
        if len(instant) > 0:
            avg_instant = instant['post_3x_change'].mean()
            print(f"\nINSTANT PUMPS (<5 days to 3x): {len(instant)} instances")
            print(f"  Average 30d after: {avg_instant:+.1f}%")
            
            # Show examples
            for _, row in instant.head(3).iterrows():
                print(f"    {row['coin']}: {row['days_to_3x']}d -> {row['post_3x_change']:+.1f}%")
                
        if len(gradual) > 0:
            avg_gradual = gradual['post_3x_change'].mean()
            print(f"\nGRADUAL GROWTH (>20 days to 3x): {len(gradual)} instances")
            print(f"  Average 30d after: {avg_gradual:+.1f}%")
            
            # Show examples
            for _, row in gradual.head(3).iterrows():
                print(f"    {row['coin']}: {row['days_to_3x']}d -> {row['post_3x_change']:+.1f}%")
                
        if len(instant) > 0 and len(gradual) > 0:
            diff = avg_gradual - avg_instant
            print(f"\n{'='*50}")
            print(f"PATTERN TEST for {period_name}:")
            print(f"  Instant pumps: {avg_instant:+.1f}%")
            print(f"  Gradual growth: {avg_gradual:+.1f}%")
            print(f"  DIFFERENCE: {diff:+.1f}%")
            
            if diff > 20:
                print(f"\n  [!!!] PATTERN CONFIRMED: Gradual beats instant by {diff:.0f}%!")
            elif diff < -20:
                print(f"\n  [X] Inverse pattern: Instant beats gradual")
            else:
                print(f"\n  [?] No clear pattern")

def main():
    print("="*70)
    print("KAGGLE CRYPTO DATA ANALYZER")
    print("="*70)
    
    # Look for data folder
    possible_folders = [
        'cryptocurrencypricehistory',
        'crypto_data',
        'kaggle_data',
        '.',  # Current directory
    ]
    
    data_folder = None
    for folder in possible_folders:
        if os.path.exists(folder):
            csv_files = glob.glob(os.path.join(folder, '*.csv'))
            if csv_files:
                data_folder = folder
                break
                
    if not data_folder:
        print("\nERROR: No CSV files found!")
        print("Please download Kaggle dataset and extract to current directory")
        print("\nExpected structure:")
        print("  memory-phase-transition/")
        print("    analyze_kaggle_crypto.py (this file)")
        print("    coin_Bitcoin.csv")
        print("    coin_Ethereum.csv")
        print("    etc...")
        return
        
    print(f"\nFound data in: {data_folder}")
    
    # Analyze all coins
    results = analyze_all_coins(data_folder)
    
    # Summarize findings
    summarize_patterns(results)
    
    # Save results
    if results:
        df = pd.DataFrame(results)
        df.to_csv('kaggle_analysis_results.csv', index=False)
        print(f"\n✓ Results saved to kaggle_analysis_results.csv")
        
    print("\n" + "="*70)
    print("HYPOTHESIS TEST:")
    print("If memory-induced phase transitions apply to crypto:")
    print("  - Instant pumps should show negative post-pump performance")
    print("  - Gradual growth should show positive continuation")
    print("  - The difference should be significant (>20%)")

if __name__ == "__main__":
    main()