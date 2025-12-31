from src.data_loader import ExchangeClient
from src.strategy import EnhancedTrendRSIStrategy
from src.backtester import Backtester

def test_enhanced():
    print("Fetching 1h data for Enhanced Trend Strategy...")
    client = ExchangeClient()
    # Need sufficient data for EMA 200, so we fetch 2000 candles
    # Fetching 200000 candles (large history)
    # Note: This might take a while to download
    df = client.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=20000)
    
    if df.empty:
        print("FAIL: Could not fetch data.")
        return

    print(f"Data fetched: {len(df)} 1h candles.")
    
    # Initialize Enhanced Strategy
    # Using defaults: EMA 200, Vol MA 20, RSI 30/70
    strategy = EnhancedTrendRSIStrategy()
    
    # Debug: Check signal potential
    df_debug = df.copy()
    import ta
    df_debug['ema_trend'] = ta.trend.EMAIndicator(df_debug['close'], window=200).ema_indicator()
    df_debug['vol_avg'] = df_debug['volume'].rolling(window=20).mean()
    df_debug['rsi'] = ta.momentum.RSIIndicator(df_debug['close'], window=14).rsi()
    
    # Count conditions
    # 1. Price > EMA
    c1 = df_debug['close'] > df_debug['ema_trend']
    # 2. Volume > 1.5x Avg
    c2 = df_debug['volume'] > (1.5 * df_debug['vol_avg'])
    # 3. RSI < 30
    c3 = df_debug['rsi'] < 30
    
    potential_buys = (c1 & c2 & c3).sum()
    print(f"Potential Buy Signals in data: {potential_buys}")
    
    # Run Backtest
    backtester = Backtester(strategy, initial_capital=10.0)
    backtester.run(df)

if __name__ == "__main__":
    test_enhanced()
