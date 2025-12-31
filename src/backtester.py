import pandas as pd
from .strategy import BaseStrategy

class Backtester:
    def __init__(self, strategy: BaseStrategy, initial_capital=10000.0, fee_rate=0.001):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.equity_curve = []
        self.trades = []

    def run(self, df):
        """
        Run the strategy on historical data.
        Assumes df has 'open', 'high', 'low', 'close', 'volume', 'timestamp'.
        """
        if df.empty:
            print("Empty dataframe provided to backtester.")
            return

        capital = self.initial_capital
        position = 0 # 0: flat, >0: long (amount of asset)
        entry_price = 0
        
        print(f"Starting backtest for {self.strategy.name}...")
        
        # Iterate through the DataFrame
        # Note: Iterating rows is slow in Pandas, but simplest for event-driven simulation.
        # Vectorization is faster but harder to implement complex logic.
        
        for i in range(len(df)):
            # We need a window of data for the strategy to work.
            # Passing the full dataframe up to index i is inefficient for large datasets,
            # but usually necessary for indicators.
            # Optimization: Pre-calculate indicators on the whole DF before looping.
            pass

        # Optimized Approach:
        # 1. Calculate Signals on the whole DF
        df_analyzed = df.copy()
        
        # We need to simulate "streaming" data or just calculate indicators at once.
        # Most indicators (RSI, MACD) can be calculated on the whole column safely (no lookahead bias if shifted correctly).
        # We need to generate signals row by row OR verify the strategy implementation supports full DF.
        
        # Our BaseStrategy.generate_signal currently takes a DF and looks at the last row.
        # This is good for real-time but slow for backtesting if we slice df.iloc[:i] every time.
        
        # For this version, let's accept the inefficiency for correctness and code reuse,
        # but we can optimize by pre-calculating indicators if the strategy allows.
        
        # Actually, let's implement a 'analyze' method in Strategy if possible, or just hack it here.
        # For simplicity/robustness, we will simulate the loop.
        
        # To speed this up, let's just use a sliding window if the strategy needs it, 
        # or better: MODIFY the Strategy to process the WHOLE dataframe and add a 'signal' column.
        # But our current Strategy.generate_signal is designed for real-time 'last candle'.
        
        signals = []
        # Pre-calculating indicators (Hack for speed: Instantiate strategy and verify if it can add columns)
        # We will iterate row by row.
        
        current_data_slice = None
        
        # Let's handle generic case:
        for i in range(50, len(df)): # Start at 50 to have enough data for indicators
             window = df.iloc[:i+1]
             signal = self.strategy.generate_signal(window)
             
             price = window.iloc[-1]['close']
             timestamp = window.iloc[-1]['timestamp']
             
             if signal == 'buy' and position == 0:
                 # Buy
                 cost = capital * (1 - self.fee_rate)
                 position = cost / price
                 capital = 0
                 entry_price = price
                 self.trades.append({'type': 'buy', 'price': price, 'time': timestamp, 'equity': cost})
                 
             elif signal == 'sell' and position > 0:
                 # Sell
                 revenue = position * price * (1 - self.fee_rate)
                 capital = revenue
                 position = 0
                 self.trades.append({'type': 'sell', 'price': price, 'time': timestamp, 'equity': capital, 'pnl': (price - entry_price)/entry_price})
            
             # Mark to market equity
             current_equity = capital + (position * price)
             self.equity_curve.append({'time': timestamp, 'equity': current_equity})

        final_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.initial_capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        print(f"Backtest complete.")
        print(f"Final Equity: ${final_equity:.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Trades: {len(self.trades)}")
        
        return pd.DataFrame(self.equity_curve)

    def print_performance(self):
        pass # Already printed in run
