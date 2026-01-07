# tw_stock_system/strategy/base.py
import pandas as pd

def run_strategy(db_manager):
    print("\n--- Strategy Mode ---")
    stock_id = input("Enter Stock ID to analyze: ")
    
    # 1. Fetch Data from DB
    query = "SELECT date, open, high, low, close, volume FROM prices WHERE stock_id=? ORDER BY date ASC"
    df = pd.read_sql_query(query, db_manager.conn, params=(stock_id,))
    
    if df.empty:
        print("No data found. Please update database first.")
        return

    # Convert date string to datetime
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    print(f"Loaded {len(df)} days of data.")
    
    # 2. Apply Strategy Logic (Example: MA Crossover)
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    print(f"Latest Close ({latest.name.date()}): {latest['close']}")
    print(f"MA5: {latest['MA5']:.2f} | MA20: {latest['MA20']:.2f}")
    
    # Check for Golden Cross (MA5 crosses above MA20)
    if prev['MA5'] <= prev['MA20'] and latest['MA5'] > latest['MA20']:
        print("\n>>> SIGNAL: GOLDEN CROSS (Buy) <<<")
    elif prev['MA5'] >= prev['MA20'] and latest['MA5'] < latest['MA20']:
        print("\n>>> SIGNAL: DEATH CROSS (Sell) <<<")
    else:
        print("\n>>> SIGNAL: HOLD (No Crossover) <<<")
        
    print("---------------------")