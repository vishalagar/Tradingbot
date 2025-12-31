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
        
        :param symbol: Trading pair symbol (e.g., 'BTC/USDT')
        :param timeframe: Candle timeframe (e.g., '1h', '1m')
        :param limit: Number of candles to fetch
        :return: DataFrame with OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
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
