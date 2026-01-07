# tw_stock_system/interface/menu.py
import sys
import time
import datetime
import pandas as pd
from database.manager import DBManager
from monitor.group_watcher import GroupMonitor
from strategy.base import run_strategy

class CLI:
    def __init__(self):
        self.db = DBManager()
        self.monitor = GroupMonitor(self.db)

    # --- Helper: Check Market Hours ---
    def is_market_open(self):
        """
        Returns True if currently between 09:00 - 13:30 (Taiwan Time).
        Adjust logic if your VPS is not in UTC+8.
        """
        now = datetime.datetime.now()
        
        # 1. Check Weekend (Saturday=5, Sunday=6)
        if now.weekday() >= 5:
            return False, "Weekend"

        # 2. Check Time (09:00 to 13:30)
        current_time = now.time()
        start = datetime.time(9, 0)
        end = datetime.time(13, 30)

        if start <= current_time <= end:
            return True, "Open"
        
        return False, "Market Closed (09:00-13:30)"

    def main_loop(self):
        while True:
            print("\n" + "="*30)
            print(" TW STOCK SYSTEM (Ubuntu CLI)")
            print("="*30)
            print("[a]  Add Stock to Group")
            print("[u]  Update Database (Download History)")
            print("[s]  Run Strategy")
            print("[gi] Group Inform Monitor (Auto-Pause)")
            print("[vg] View Group Data (180 Days)")
            print("[q]  Quit")
            
            cmd = input("\nCommand > ").lower().strip()
            
            if cmd == 'a':
                self.add_mode()
            elif cmd == 'u':
                self.update_mode()
            elif cmd == 's':
                run_strategy(self.db)
            elif cmd == 'gi':
                self.group_inform_mode()
            elif cmd == 'vg':
                self.view_group_mode()
            elif cmd == 'q':
                print("Exiting...")
                self.db.close()
                sys.exit()
            else:
                print("Unknown command.")

    def add_mode(self):
        print("\n--- Add Stock Mode ---")
        groups = self.db.get_all_groups()
        print(f"Existing Groups: {groups}")
        
        g_name = input("Group Name (e.g. DRAM): ").strip()
        s_id = input("Stock ID (e.g. 2408): ").strip()
        
        if g_name and s_id:
            self.db.add_stock_to_group(g_name, s_id)

    def update_mode(self):
        print("\n--- Update All Stocks ---")
        stocks = self.db.get_all_stocks()
        if not stocks:
            print("Database is empty. Add stocks first.")
            return
            
        print(f"Updating {len(stocks)} stocks...")
        for s in stocks:
            print(f"Processing {s}...")
            self.db.update_single_stock(s)
        print("Update Complete.")

    # --- UPDATED MONITOR FUNCTION ---
    def group_inform_mode(self):
        print("\n--- Group Inform Monitor ---")
        groups = self.db.get_all_groups()
        print(f"Available Groups: {groups}")
        
        target = input("Target Group: ").strip()
        if target not in groups:
            print("Group not found.")
            return
            
        try:
            rise = float(input("Rise Threshold % (e.g. 3.0): "))
            coverage = float(input("Coverage % (e.g. 50): "))
            interval = int(input("Check Interval (seconds, min 10): "))
            if interval < 10: interval = 10
        except ValueError:
            print("Invalid number.")
            return

        print(f"\nStarting Monitor for '{target}'...")
        print("Note: Monitor will auto-pause outside 09:00-13:30.")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                # 1. Check Market Status
                is_open, reason = self.is_market_open()
                
                if is_open:
                    # Market is Open: Run Logic
                    self.monitor.check_group_performance(target, rise, coverage)
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Sleeping {interval}s...")
                    time.sleep(interval)
                else:
                    # Market is Closed: Sleep longer to save CPU
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {reason}. Paused for 60s...")
                    time.sleep(60) # Check status every minute
                    
        except KeyboardInterrupt:
            print("\nMonitor Stopped.")

    def view_group_mode(self):
        print("\n--- View Group Data ---")
        groups = self.db.get_all_groups()
        if not groups:
            print("No groups found.")
            return

        print("Available Groups:")
        for idx, g in enumerate(groups):
            print(f"  {idx+1}. {g}")

        try:
            g_idx = int(input("Select Group Number: ")) - 1
            if g_idx < 0 or g_idx >= len(groups): return
            selected_group = groups[g_idx]
        except ValueError: return

        stocks = self.db.get_group_stocks(selected_group)
        if not stocks:
            print(f"No stocks in {selected_group}.")
            return

        print(f"\nStocks in '{selected_group}':")
        for idx, s in enumerate(stocks):
            print(f"  {idx+1}. {s}")

        try:
            s_idx = int(input("Select Stock Number: ")) - 1
            if s_idx < 0 or s_idx >= len(stocks): return
            stock_id = stocks[s_idx]
        except ValueError: return

        print(f"\nFetching 180 days data for {stock_id}...")
        query = "SELECT date, open, high, low, close, volume FROM prices WHERE stock_id=? ORDER BY date DESC LIMIT 180"
        df = pd.read_sql_query(query, self.db.conn, params=(stock_id,))
        
        if df.empty:
            print("No data found.")
        else:
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            print(df)
            pd.reset_option('display.max_rows')
            pd.reset_option('display.max_columns')
            pd.reset_option('display.width')