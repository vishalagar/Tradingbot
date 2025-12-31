from src.data_loader import ExchangeClient
from src.strategy import BollingerRSIStrategy
from src.backtester import Backtester

def test_scalping():
    print("Fetching 5m data for scalping test...")
    client = ExchangeClient()
    # Fetching 2000 candles of 5m data (approx 7 days)
    df = client.fetch_ohlcv('BTC/USDT', timeframe='5m', limit=2000)
    
    if df.empty:
        print("FAIL: Could not fetch data.")
        return

    print(f"Data fetched: {len(df)} 5m candles.")
    
    # Initialize Scalping Strategy
    strategy = BollingerRSIStrategy()
    
    # Debug: Check signal generation on the dataframe manually to see stats
    # We call generate_signal row-by-row in backtester, but let's see stats first
    df_debug = df.copy()
    import ta
    bb = ta.volatility.BollingerBands(df_debug['close'], window=20, window_dev=2)
    df_debug['bb_low'] = bb.bollinger_lband()
    df_debug['bb_high'] = bb.bollinger_hband()
    df_debug['rsi'] = ta.momentum.RSIIndicator(df_debug['close'], window=14).rsi()
    
    print(f"RSI Min: {df_debug['rsi'].min()}")
    print(f"RSI Max: {df_debug['rsi'].max()}")
    print(f"Close < BB Low count: {(df_debug['close'] <= df_debug['bb_low']).sum()}")
    print(f"Close > BB High count: {(df_debug['close'] >= df_debug['bb_high']).sum()}")
    
    # Run Backtest
    backtester = Backtester(strategy, initial_capital=1000.0)
    backtester.run(df)

if __name__ == "__main__":
    test_scalping()
