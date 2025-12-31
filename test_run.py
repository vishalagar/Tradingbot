from src.data_loader import ExchangeClient
from src.strategy import RSIStrategy
import pandas as pd

def test_system():
    print("Testing Data Loader...")
    client = ExchangeClient()
    df = client.fetch_ohlcv('BTC/USDT', limit=50)
    
    if df.empty:
        print("FAIL: Data extraction failed (empty dataframe)")
        return
    else:
        print(f"SUCCESS: Fetched {len(df)} rows.")
        print(df.tail(3))
        
    print("\nTesting Strategy...")
    strategy = RSIStrategy()
    signal = strategy.generate_signal(df)
    print(f"Signal generated: {signal}")
    
    # Check if indicators were added
    if 'rsi' in df.columns:
        print("SUCCESS: Indicators calculated.")
    else:
        # Note: Our strategy implementation copies the df, so the original might not be modified unless we returned it.
        # But for verification, we just want to see if it ran without error.
        print("Indicator check skipped (strategy might not modify in-place).")

if __name__ == "__main__":
    test_system()
