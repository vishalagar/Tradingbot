import ccxt
import pandas as pd
import time
import sqlite3
import os
from datetime import datetime

class ExchangeClient:
    def __init__(self, exchange_id='binance'):
        self.exchange_class = getattr(ccxt, exchange_id)
        
        # User requested to disable API usage for now. 
        # Using public instance only. Explicitly disable keys.
        self.exchange = self.exchange_class({
            'apiKey': '', 
            'secret': '',
            'enableRateLimit': True
        })
            
        self.db_path = 'trading_data.db'
        self._init_db()
        
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ohlcv (
                symbol TEXT,
                timeframe TEXT,
                timestamp INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (symbol, timeframe, timestamp)
            )
        ''')
        conn.commit()
        conn.close()
        
    def _save_to_db(self, df, symbol, timeframe):
        if df.empty:
            return
        conn = sqlite3.connect(self.db_path)
        data = []
        for row in df.itertuples():
            ts = int(row.timestamp.timestamp() * 1000)
            data.append((symbol, timeframe, ts, row.open, row.high, row.low, row.close, row.volume))
            
        cursor = conn.cursor()
        cursor.executemany('''
            REPLACE INTO ohlcv (symbol, timeframe, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        conn.close()
        
    def _load_from_db(self, symbol, timeframe, limit):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ohlcv WHERE symbol=? AND timeframe=?", (symbol, timeframe))
        count = cursor.fetchone()[0]
        
        query = f'''
            SELECT timestamp, open, high, low, close, volume 
            FROM ohlcv 
            WHERE symbol=? AND timeframe=? 
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        cursor.execute(query, (symbol, timeframe, limit))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return pd.DataFrame(), 0
            
        rows = rows[::-1]
        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df, count

    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        # Fetch OHLCV data from the exchange.
        # Supports pagination to fetch more than exchange limit.
        # Checks DB first, updates with new data, or fetches full history if sufficient GAP.

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(timestamp), COUNT(*) FROM ohlcv WHERE symbol=? AND timeframe=?", (symbol, timeframe))
        max_ts, count = cursor.fetchone()
        conn.close()
        
        fetch_from_api = False
        since = None
        
        if max_ts is None or count < limit:
            # Not enough data or no data -> Generic Fetch (potentially large)
            # Logic: If we need 200k candles but have 10k, we basically need to fetch everything again 
            # or try to stitch. Unifying fetch_ohlcv logic:
            # Simplest for "speed up backtest": IF count < limit, do full fetch.
            fetch_from_api = True
            # Calculate since for full fetch
            duration_seconds = self.exchange.parse_timeframe(timeframe)
            now = self.exchange.milliseconds()
            since = now - (limit * duration_seconds * 1000)
        else:
            # We have enough history, just fetch NEW data since max_ts
            # Re-fetch the last candle to ensure it updates if it's still open
            fetch_from_api = True
            since = max_ts
            
        if fetch_from_api:
            # Perform API Fetch (Incremental or Full)
            new_data_limit = limit if (max_ts is None or count < limit) else 1000 # Just fetch recent if incremental
            
            # Helper to fetch with pagination (reusing logic, but adapted)
            # Note: We duplicate logic slightly or can refactor. I'll include the loop here.
            
            all_ohlcv = []
            fetched_count = 0
            curr_limit = new_data_limit
            # If incremental, we don't know exact 'limit' needed, loop until no more.
            # Safe bet: just loop with 'since'.
            
            while True:
                # If we have a hard limit (full fetch), respect it.
                # If incremental, stop when no new data.
                batch_limit = 1000
                if max_ts is None or count < limit:
                     batch_limit = min(curr_limit - fetched_count, 1000)
                     if batch_limit <= 0: break
                
                try:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=batch_limit)
                except Exception as e:
                    print(f"Fetch error: {e}")
                    break
                    
                if not ohlcv:
                    break
                
                all_ohlcv.extend(ohlcv)
                fetched_count += len(ohlcv)
                last_timestamp = ohlcv[-1][0]
                since = last_timestamp + 1
                time.sleep(self.exchange.rateLimit / 1000)
                
                # If incremental (only fetching new), break if we got less than requested (means we are at tip)
                if max_ts is not None and count >= limit and len(ohlcv) < batch_limit:
                    break
                    
            if all_ohlcv:
                df_new = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df_new['timestamp'] = pd.to_datetime(df_new['timestamp'], unit='ms')
                self._save_to_db(df_new, symbol, timeframe)
                print(f"Updated DB with {len(df_new)} new candles.")
                
        # 2. Load from DB
        df_final, _ = self._load_from_db(symbol, timeframe, limit)
        return df_final

    def get_latest_price(self, symbol):
        # Fetch the latest ticker price.
        # 
        # :param symbol: Trading pair symbol (e.g., 'BTC/USDT')
        # :return: Latest price as float
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching ticker: {e}")
            return None

    def create_market_buy_order(self, symbol, amount):
        # Place a market buy order.
        # :param symbol: Trading pair (e.g. 'BTC/USDT')
        # :param amount: Amount of base currency to buy
        # try:
        #     return self.exchange.create_market_buy_order(symbol, amount)
        # except Exception as e:
        #     print(f"Error placing buy order: {e}")
        #     return None
        print("Live trading disabled. Order ignored.")
        return None

    def create_market_sell_order(self, symbol, amount):
        # Place a market sell order.
        # :param symbol: Trading pair (e.g. 'BTC/USDT')
        # :param amount: Amount of base currency to sell
        # try:
        #     return self.exchange.create_market_sell_order(symbol, amount)
        # except Exception as e:
        #     print(f"Error placing sell order: {e}")
        #     return None
        print("Live trading disabled. Order ignored.")
        return None
