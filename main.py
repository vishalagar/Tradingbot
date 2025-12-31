import time
import os
import argparse
from dotenv import load_dotenv
from src.data_loader import ExchangeClient
from src.strategy import RSIStrategy, MACDStrategy, BollingerRSIStrategy, EnhancedTrendRSIStrategy
from src.notifier import Notifier

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Bitcoin Trading Bot')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading Pair')
    parser.add_argument('--timeframe', type=str, default='1h', help='Candle Timeframe')
    parser.add_argument('--strategy', type=str, default='RSI', choices=['RSI', 'MACD', 'BOLLINGER_RSI', 'ENHANCED_RSI'], help='Strategy to use')
    # parser.add_argument('--live', action='store_true', help='Enable Live Trading (Real Money)')
    # parser.add_argument('--amount', type=float, default=0.0001, help='Amount to trade in base currency')
    # parser.add_argument('--stop-loss', type=float, default=0.02, help='Stop Loss percentage (e.g. 0.02 for 2%)')
    # parser.add_argument('--take-profit', type=float, default=0.04, help='Take Profit percentage (e.g. 0.04 for 4%)')
    
    args = parser.parse_args()
    
    # Initialize components
    exchange_client = ExchangeClient()
    notifier = Notifier()
    
    if args.strategy == 'RSI':
        strategy = RSIStrategy()
    elif args.strategy == 'MACD':
        strategy = MACDStrategy()
    elif args.strategy == 'BOLLINGER_RSI':
        strategy = BollingerRSIStrategy()
    elif args.strategy == 'ENHANCED_RSI':
        strategy = EnhancedTrendRSIStrategy()
    else:
        raise ValueError("Unknown strategy")
        
    notifier.notify(f"Starting {strategy.name} Indicator Scanner for {args.symbol} ({args.timeframe})")
    
    while True:
        try:
            # Fetch data
            df = exchange_client.fetch_ohlcv(args.symbol, args.timeframe)
            
            if not df.empty:
                # Analyze full dataframe to get indicators
                df_analyzed = strategy.analyze(df)
                
                # Get last row
                curr = df_analyzed.iloc[-1]
                
                # Extract key metrics based on strategy
                price = curr['close']
                signal = curr['signal']
                
                # Build Info String
                info = f"[{time.strftime('%H:%M:%S')}] Price: {price:.2f} | Signal: {signal}"
                
                if 'rsi' in curr:
                    info += f" | RSI: {curr['rsi']:.2f}"
                if 'ema_trend' in curr:
                    trend = "BULL" if price > curr['ema_trend'] else "BEAR"
                    info += f" | Trend: {trend}"
                if 'bb_high' in curr:
                     pass # Maybe too verbose
                if 'macd' in curr:
                     info += f" | MACD: {curr['macd']:.2f}"
                
                print(info)
                
                if signal == 'buy':
                     notifier.alert_buy(args.symbol, price, strategy.name)
                elif signal == 'sell':
                     notifier.alert_sell(args.symbol, price, strategy.name)
            
            # Rate limit
            time.sleep(10)
            
        except KeyboardInterrupt:
            notifier.notify("Stopping Trading Bot...")
            break
        except Exception as e:
            notifier.notify(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
