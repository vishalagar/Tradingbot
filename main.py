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
        
    notifier.notify(f"Starting Trading Bot for {args.symbol} using {strategy.name} on {args.timeframe} timeframe.")
    
    while True:
        try:
            # Fetch data
            df = exchange_client.fetch_ohlcv(args.symbol, args.timeframe)
            
            if not df.empty:
                # Analyze
                signal = strategy.generate_signal(df)
                current_price = df.iloc[-1]['close']
                
                print(f"[{time.strftime('%H:%M:%S')}] Price: {current_price} | Signal: {signal}")
                
                if signal == 'buy':
                    notifier.alert_buy(args.symbol, current_price, strategy.name)
                elif signal == 'sell':
                    notifier.alert_sell(args.symbol, current_price, strategy.name)
            
            # Rate limit / Wait for next candle
            # For 1h candle, you might want to sleep longer, but for testing we check often.
            # In production, you'd align this with the timeframe.
            time.sleep(10) # check everyone 10 seconds for testing
            
        except KeyboardInterrupt:
            notifier.notify("Stopping Trading Bot...")
            break
        except Exception as e:
            notifier.notify(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
