
import itertools
import pandas as pd
from src.data_loader import ExchangeClient
from src.strategy import RSIStrategy, EnhancedTrendRSIStrategy
from src.backtester import Backtester

def optimize_rsi():
    client = ExchangeClient()
    # Fetch data once (large history)
    print("Fetching data for optimization...")
    # Fetching 10000 candles for optimization speed (use database cache if available)
    df = client.fetch_ohlcv('BTC/USDT', '1h', limit=10000)
    
    if df.empty:
        print("No data fetched.")
        return

    # Parameter Ranges
    periods = [10, 14, 20]
    buy_thresholds = [20, 25, 30, 35]
    sell_thresholds = [65, 70, 75, 80]
    
    best_return = -9999
    best_params = None
    
    print(f"Starting optimization across {len(periods)*len(buy_thresholds)*len(sell_thresholds)} combinations...")
    
    results = []

    for period, buy, sell in itertools.product(periods, buy_thresholds, sell_thresholds):
        if buy >= sell:
             continue
             
        strategy = RSIStrategy(period=period, buy_threshold=buy, sell_threshold=sell)
        backtester = Backtester(strategy, initial_capital=100, fee_rate=0.001)
        
        # Suppress prints by capturing stdout? Or just let it print?
        # Backtest prints a lot. We might want to silence it or modify backtester to be silent.
        # For now, let it run but maybe we only care about return.
        # To be cleaner, we access backtester internals or trust it returns the equity curve.
        # But we need the FINAL return.
        
        # HACK: Using a modified run that returns metrics would be better. 
        # But we can calculate from equity curve returned.
        
        equity_curve = backtester.run(df)
        final_val = equity_curve.iloc[-1]['equity'] if not equity_curve.empty else 100
        total_return = (final_val - 100) / 100 * 100
        
        results.append({
            'period': period,
            'buy': buy,
            'sell': sell,
            'return': total_return
        })
        
        if total_return > best_return:
            best_return = total_return
            best_params = (period, buy, sell)
            print(f"New Best: {total_return:.2f}% Params: {best_params}")

    print("\noptimization Complete.")
    print(f"Best Return: {best_return:.2f}%")
    print(f"Best Parameters: RSI Period={best_params[0]}, Buy={best_params[1]}, Sell={best_params[2]}")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('optimization_results.csv', index=False)
    print("Results saved to optimization_results.csv")

if __name__ == "__main__":
    optimize_rsi()
