import ta
import pandas as pd

class BaseStrategy:
    def __init__(self, name):
        self.name = name

    def generate_signal(self, df):
        """
        Analyze the DataFrame and return a signal.
        For real-time usage (checks last row).
        """
        df_analyzed = self.analyze(df)
        return df_analyzed.iloc[-1]['signal']

    def analyze(self, df):
        """
        Analyze the full DataFrame and add a 'signal' column.
        For backtesting (vectorized).
        """
        raise NotImplementedError("Subclasses must implement analyze")

class RSIStrategy(BaseStrategy):
    def __init__(self, period=14, buy_threshold=30, sell_threshold=70):
        super().__init__("RSI Strategy")
        self.period = period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def analyze(self, df):
        if df.empty:
            return df
        
        df = df.copy()
        # Calculate RSI
        rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=self.period)
        df['rsi'] = rsi_indicator.rsi()
        
        # Vectorized Signal
        df['signal'] = None
        df.loc[df['rsi'] < self.buy_threshold, 'signal'] = 'buy'
        df.loc[df['rsi'] > self.sell_threshold, 'signal'] = 'sell'
        
        return df

class MACDStrategy(BaseStrategy):
    def __init__(self, fast=12, slow=26, signal=9):
        super().__init__("MACD Strategy")
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def analyze(self, df):
        if df.empty:
            return df
        
        df = df.copy()
        # Calculate MACD
        macd_indicator = ta.trend.MACD(close=df['close'], window_slow=self.slow, window_fast=self.fast, window_sign=self.signal)
        df['macd'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()
        
        # Vectorized crossover is tricky without loop or shift
        # Buy: Prev MACD < Prev Sig AND Curr MACD > Curr Sig
        prev_macd = df['macd'].shift(1)
        prev_sig = df['macd_signal'].shift(1)
        curr_macd = df['macd']
        curr_sig = df['macd_signal']
        
        buy_cond = (prev_macd < prev_sig) & (curr_macd > curr_sig)
        sell_cond = (prev_macd > prev_sig) & (curr_macd < curr_sig)
        
        df['signal'] = None
        df.loc[buy_cond, 'signal'] = 'buy'
        df.loc[sell_cond, 'signal'] = 'sell'
        
        return df

class BollingerRSIStrategy(BaseStrategy):
    def __init__(self, bb_window=20, bb_std=2, rsi_window=14, rsi_buy=30, rsi_sell=70):
        super().__init__("Bollinger+RSI Scalping")
        self.bb_window = bb_window
        self.bb_std = bb_std
        self.rsi_window = rsi_window
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell

    def analyze(self, df):
        if df.empty:
            return df
        
        df = df.copy()
        
        # Calculate Bollinger Bands
        bb_indicator = ta.volatility.BollingerBands(close=df['close'], window=self.bb_window, window_dev=self.bb_std)
        df['bb_high'] = bb_indicator.bollinger_hband()
        df['bb_low'] = bb_indicator.bollinger_lband()
        
        # Calculate RSI
        rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=self.rsi_window)
        df['rsi'] = rsi_indicator.rsi()
        
        # Vectorized Logic
        buy_cond = (df['close'] <= df['bb_low']) & (df['rsi'] < self.rsi_buy)
        sell_cond = (df['close'] >= df['bb_high']) & (df['rsi'] > self.rsi_sell)
        
        df['signal'] = None
        df.loc[buy_cond, 'signal'] = 'buy'
        df.loc[sell_cond, 'signal'] = 'sell'
        
        return df

class EnhancedTrendRSIStrategy(BaseStrategy):
    def __init__(self, rsi_period=14, ema_period=200, buy_threshold=30, sell_threshold=70, vol_ma=20):
        super().__init__("Enhanced Trend RSI")
        self.rsi_period = rsi_period
        self.ema_period = ema_period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.vol_ma = vol_ma

    def analyze(self, df):
        if df.empty:
            return df
        
        df = df.copy()
        
        # 1. RSI
        rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=self.rsi_period)
        df['rsi'] = rsi_indicator.rsi()
        
        # 2. EMA Trend
        ema_indicator = ta.trend.EMAIndicator(close=df['close'], window=self.ema_period)
        df['ema_trend'] = ema_indicator.ema_indicator()
        
        # 3. Volume Average
        df['vol_avg'] = df['volume'].rolling(window=self.vol_ma).mean()
        
        # Vectorized Logic
        is_oversold = df['rsi'] < self.buy_threshold
        is_bullish_trend = df['close'] > df['ema_trend']
        is_high_volume = df['volume'] > (1.5 * df['vol_avg'])
        
        buy_cond = is_oversold & is_bullish_trend & is_high_volume
        sell_cond = df['rsi'] > self.sell_threshold
        
        df['signal'] = None
        df.loc[buy_cond, 'signal'] = 'buy'
        df.loc[sell_cond, 'signal'] = 'sell'
        
        return df
