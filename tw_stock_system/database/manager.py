# tw_stock_system/database/manager.py
import sqlite3
import datetime
import config
from . import fetcher

class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(config.DB_PATH)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        # Link Groups to Stocks
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_groups (
                group_name TEXT,
                stock_id TEXT,
                UNIQUE(group_name, stock_id)
            )
        ''')
        # Store Historical Prices
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                stock_id TEXT,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                UNIQUE(stock_id, date)
            )
        ''')
        self.conn.commit()

    def add_stock_to_group(self, group, stock_id):
        try:
            self.cursor.execute("INSERT OR IGNORE INTO stock_groups VALUES (?, ?)", (group, stock_id))
            self.conn.commit()
            print(f"[DB] Linked {stock_id} to group '{group}'")
            # Automatically fetch data when adding
            self.update_single_stock(stock_id)
        except Exception as e:
            print(f"[Error] DB Add failed: {e}")

    def update_single_stock(self, stock_id):
        df = fetcher.fetch_history(stock_id, days=config.HISTORY_DAYS)
        if df is not None and not df.empty:
            count = 0
            for index, row in df.iterrows():
                # Handling yfinance multi-index columns if present
                try:
                    o = float(row['Open'].iloc[0]) if hasattr(row['Open'], 'iloc') else float(row['Open'])
                    h = float(row['High'].iloc[0]) if hasattr(row['High'], 'iloc') else float(row['High'])
                    l = float(row['Low'].iloc[0]) if hasattr(row['Low'], 'iloc') else float(row['Low'])
                    c = float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close'])
                    v = int(row['Volume'].iloc[0]) if hasattr(row['Volume'], 'iloc') else int(row['Volume'])
                except:
                     # Fallback for simple series
                    o, h, l, c, v = float(row['Open']), float(row['High']), float(row['Low']), float(row['Close']), int(row['Volume'])

                d = index.date()
                self.cursor.execute('''
                    INSERT OR REPLACE INTO prices VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (stock_id, d, o, h, l, c, v))
                count += 1
            
            self.conn.commit()
            print(f"[DB] Updated {count} records for {stock_id}")
            self.prune_old_data(stock_id)

    def prune_old_data(self, stock_id):
        """Removes data older than HISTORY_DAYS"""
        cutoff = datetime.date.today() - datetime.timedelta(days=config.HISTORY_DAYS)
        self.cursor.execute("DELETE FROM prices WHERE stock_id=? AND date < ?", (stock_id, cutoff))
        deleted = self.cursor.rowcount
        self.conn.commit()
        if deleted > 0:
            print(f"[DB] Pruned {deleted} old records for {stock_id}")

    def get_all_stocks(self):
        self.cursor.execute("SELECT DISTINCT stock_id FROM stock_groups")
        return [row[0] for row in self.cursor.fetchall()]

    def get_group_stocks(self, group_name):
        self.cursor.execute("SELECT stock_id FROM stock_groups WHERE group_name=?", (group_name,))
        return [row[0] for row in self.cursor.fetchall()]
        
    def get_all_groups(self):
        self.cursor.execute("SELECT DISTINCT group_name FROM stock_groups")
        return [row[0] for row in self.cursor.fetchall()]
    
    def close(self):
        self.conn.close()