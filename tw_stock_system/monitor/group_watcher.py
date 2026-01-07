# tw_stock_system/monitor/group_watcher.py
import twstock
import time
from utils import email_sender

class GroupMonitor:
    def __init__(self, db_manager):
        self.db = db_manager

    def check_group_performance(self, group_name, rise_threshold, percent_coverage):
        stocks = self.db.get_group_stocks(group_name)
        if not stocks:
            print(f"[Monitor] Group {group_name} is empty.")
            return

        print(f"[Monitor] Scanning group '{group_name}' ({len(stocks)} stocks)...")
        
        triggered_count = 0
        total_checked = 0

        for stock_id in stocks:
            try:
                # Rate limit protection (simple sleep)
                time.sleep(1.5) 
                
                real = twstock.realtime.get(stock_id)
                if real['success']:
                    # Extract Data
                    current_price = float(real['realtime']['latest_trade_price'])
                    
                    # Calculate Change % (Using Open as proxy if Close not available, 
                    # ideally use previous close from history but simplified here)
                    # Use 'open' from realtime
                    open_price = float(real['realtime']['open'])
                    
                    if open_price == 0: continue # Data error
                    
                    change_pct = ((current_price - open_price) / open_price) * 100
                    
                    total_checked += 1
                    
                    # Check threshold (e.g., Rise > 3%)
                    if change_pct >= rise_threshold:
                        triggered_count += 1
                        print(f"  -> {stock_id}: {change_pct:.2f}% (Triggered)")
                    else:
                        print(f"  -> {stock_id}: {change_pct:.2f}%")
            except Exception as e:
                print(f"  [Error] {stock_id}: {e}")
                continue

        # Final Logic
        if total_checked > 0:
            trigger_ratio = (triggered_count / total_checked) * 100
            print(f"[Result] {trigger_ratio:.1f}% of stocks match criteria (Target: {percent_coverage}%)")
            
            if trigger_ratio >= percent_coverage:
                msg = f"Group {group_name} Alert! {trigger_ratio:.1f}% of stocks rose over {rise_threshold}%."
                email_sender.send_email(f"Group Alert: {group_name}", msg)