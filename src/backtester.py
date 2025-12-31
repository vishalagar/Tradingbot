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
        Optimized vectorized approach.
        """
        if df.empty:
            print("Empty dataframe provided to backtester.")
            return

        capital = self.initial_capital
        position = 0 # 0: flat, >0: long (amount of asset)
        entry_price = 0
        
        print(f"Starting backtest for {self.strategy.name}...")
        
        # 1. Analyze the whole dataframe once (Vectorized)
        df_analyzed = self.strategy.analyze(df)
        
        # 2. Iterate row by row ONLY for trade logic (much faster now)
        # We can iterate tuples which is faster than iterrows
        for row in df_analyzed.itertuples():
            # row.signal, row.close, row.timestamp
            
            # Skip if signal is nan
            if not isinstance(row.signal, str):
                # Update equity curve for this timestamp
                current_value = capital if position == 0 else (position * row.close)
                self.equity_curve.append({'time': row.timestamp, 'equity': current_value})
                continue
            
            if row.signal == 'buy' and position == 0:
                 # Buy
                 cost = capital * (1 - self.fee_rate)
                 position = cost / row.close
                 capital = 0
                 entry_price = row.close
                 self.trades.append({'type': 'buy', 'price': row.close, 'time': row.timestamp, 'equity': cost})
                 
            elif row.signal == 'sell' and position > 0:
                 # Sell
                 revenue = position * row.close * (1 - self.fee_rate)
                 capital = revenue
                 position = 0
                 self.trades.append({'type': 'sell', 'price': row.close, 'time': row.timestamp, 'equity': capital, 'pnl': (row.close - entry_price)/entry_price})
            
            # Mark to market equity
            current_value = capital if position == 0 else (position * row.close)
            self.equity_curve.append({'time': row.timestamp, 'equity': current_value})

        final_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.initial_capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        print(f"Backtest complete.")
        print(f"Final Equity: ${final_equity:.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Trades: {len(self.trades)}")
        
        return pd.DataFrame(self.equity_curve)

    def print_performance(self):
        pass # Already printed in run
