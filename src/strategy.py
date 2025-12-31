import ta
import pandas as pd

class BaseStrategy:
    def __init__(self, name):
        self.name = name

    def generate_signal(self, df):
        """
        Analyze the DataFrame and return a signal.
        
        :param df: DataFrame with OHLCV data
        :return: 'buy', 'sell', or None
        """
        raise NotImplementedError("Subclasses must implement generate_signal")

class RSIStrategy(BaseStrategy):
    def __init__(self, period=14, buy_threshold=30, sell_threshold=70):
        super().__init__("RSI Strategy")
        self.period = period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def generate_signal(self, df):
        if df.empty:
            return None
            
        # sensitive to new data, so we copy to avoid warnings
        df = df.copy()
        
        # Calculate RSI
        rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=self.period)
        df['rsi'] = rsi_indicator.rsi()
        
        # Get the latest RSI value
        latest_rsi = df['rsi'].iloc[-1]
        
        if latest_rsi < self.buy_threshold:
            return 'buy'
        elif latest_rsi > self.sell_threshold:
            return 'sell'
        return None

class MACDStrategy(BaseStrategy):
    def __init__(self, fast=12, slow=26, signal=9):
        super().__init__("MACD Strategy")
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signal(self, df):
        if df.empty:
            return None
        
        df = df.copy()
        
        # Calculate MACD
        macd_indicator = ta.trend.MACD(close=df['close'], window_slow=self.slow, window_fast=self.fast, window_sign=self.signal)
        df['macd'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()
        
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # Crossover logic: 
        # Buy if MACD crosses above Signal
        # Sell if MACD crosses below Signal
        
        curr_macd = last_row['macd']
        curr_sig = last_row['macd_signal']
        prev_macd = prev_row['macd']
        prev_sig = prev_row['macd_signal']
        
        if prev_macd < prev_sig and curr_macd > curr_sig:
            return 'buy'
        elif prev_macd > prev_sig and curr_macd < curr_sig:
            return 'sell'
            
        return None

class BollingerRSIStrategy(BaseStrategy):
    def __init__(self, bb_window=20, bb_std=2, rsi_window=14, rsi_buy=30, rsi_sell=70):
        super().__init__("Bollinger+RSI Scalping")
        self.bb_window = bb_window
        self.bb_std = bb_std
        self.rsi_window = rsi_window
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell

    def generate_signal(self, df):
        if df.empty:
            return None
        
        df = df.copy()
        
        # Calculate Bollinger Bands
        bb_indicator = ta.volatility.BollingerBands(close=df['close'], window=self.bb_window, window_dev=self.bb_std)
        df['bb_high'] = bb_indicator.bollinger_hband()
        df['bb_low'] = bb_indicator.bollinger_lband()
        
        # Calculate RSI
        rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=self.rsi_window)
        df['rsi'] = rsi_indicator.rsi()
        
        curr = df.iloc[-1]
        
        # Logic: 
        # Buy if Price touches Lower Band AND RSI < Buy Threshold (Oversold)
        # Sell if Price touches Upper Band AND RSI > Sell Threshold (Overbought)
        
        if curr['close'] <= curr['bb_low'] and curr['rsi'] < self.rsi_buy:
             return 'buy'
        elif curr['close'] >= curr['bb_high'] and curr['rsi'] > self.rsi_sell:
             return 'sell'
             
        return None
