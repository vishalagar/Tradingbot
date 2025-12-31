import ccxt
import pandas as pd
import time

class ExchangeClient:
    def __init__(self, exchange_id='binance'):
        self.exchange_class = getattr(ccxt, exchange_id)
        self.exchange = self.exchange_class()
        
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """
        Fetch OHLCV data from the exchange.
        Supports pagination to fetch more than exchange limit.
        
        :param symbol: Trading pair symbol (e.g., 'BTC/USDT')
        :param timeframe: Candle timeframe (e.g., '1h', '1m')
        :param limit: Number of candles to fetch
        :return: DataFrame with OHLCV data
        """
        try:
            all_ohlcv = []
            since = None
            
            # Estimate start time if limit is huge to optimize (optional, but good for 'since' based fetching)
            # For now, we'll fetch backwards or forwards depending on exchange capabilities.
            # Most reliable public method is usually fetching most recent, then finding previous.
            # But ccxt fetch_ohlcv with 'since' is standard. 
            
            # Let's simple loop: if we need 200,000, we can't just ask for it.
            # We will use the internal pagination if `since` is provided, OR
            # we simply call it multiple times.
            
            # Implementation: Fetch from most recent backwards (if supported) or just rely on 'since'.
            # A common pattern to get 'last N candles' is:
            # 1. CCXT usually doesn't support "backward pagination" easily across all exchanges.
            # 2. We can calculate 'since' = Now - (N * timeframe_duration)
            
            duration_seconds = self.exchange.parse_timeframe(timeframe)
            now = self.exchange.milliseconds()
            since = now - (limit * duration_seconds * 1000)
            
            fetched_count = 0
            while fetched_count < limit:
                # Max limit per call varies, usually 1000. Safe bet is 1000.
                fetch_limit = min(limit - fetched_count, 1000)
                
                # We need to provide 'since' to get older data
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=fetch_limit)
                
                if not ohlcv:
                    break
                    
                all_ohlcv.extend(ohlcv)
                fetched_count += len(ohlcv)
                
                # Update 'since' for next batch: last candle timestamp + 1 candle duration ?
                # Or simply take the last timestamp from the fetched data + 1ms
                last_timestamp = ohlcv[-1][0]
                since = last_timestamp + 1 
                
                # Rate limit safety
                time.sleep(self.exchange.rateLimit / 1000)
                print(f"Fetched {fetched_count} / {limit} candles...")
                
            print(f"\nFetch complete. Total: {fetched_count}")
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Remove duplicates just in case
            df = df.drop_duplicates(subset=['timestamp'])
            
            # Just return the number requested if we got more
            if len(df) > limit:
                df = df.iloc[-limit:]
                
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()

    def get_latest_price(self, symbol):
        """
        Fetch the latest ticker price.
        
        :param symbol: Trading pair symbol (e.g., 'BTC/USDT')
        :return: Latest price as float
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching ticker: {e}")
            return None
