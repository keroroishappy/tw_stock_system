# tw_stock_system/database/fetcher.py
import yfinance as yf
import datetime

def fetch_history(stock_id, days=180):
    """
    Downloads last N days of data for a TW stock.
    Returns a DataFrame.
    """
    # Try .TW first (TSE), then .TWO (OTC) if empty
    tickers_to_try = [f"{stock_id}.TW", f"{stock_id}.TWO"]
    
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days + 10) # Buffer
    
    for ticker in tickers_to_try:
        print(f"[Data] Downloading {ticker}...")
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[Error] fetch failed for {ticker}: {e}")
            
    print(f"[Warning] No data found for {stock_id}")
    return None