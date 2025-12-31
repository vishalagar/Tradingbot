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
    parser.add_argument('--live', action='store_true', help='Enable Live Trading (Real Money)')
    parser.add_argument('--amount', type=float, default=0.0001, help='Amount to trade in base currency')
    parser.add_argument('--stop-loss', type=float, default=0.02, help='Stop Loss percentage (e.g. 0.02 for 2%)')
    parser.add_argument('--take-profit', type=float, default=0.04, help='Take Profit percentage (e.g. 0.04 for 4%)')
    
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
    if args.live:
        notifier.notify("WARNING: LIVE TRADING ENABLED. REAL ORDERS WILL BE PLACED.")
    else:
        notifier.notify("Running in PAPER/SIMULATION mode.")
    
    # State tracking
    position = None # None, 'long'
    entry_price = 0.0
    
    while True:
        try:
            # Fetch data
            df = exchange_client.fetch_ohlcv(args.symbol, args.timeframe)
            
            if not df.empty:
                # Analyze
                # Using generate_signal which now calls analyze internally for optimization, 
                # but for real-time we just need the latest.
                # However, strategy.py implementation of generate_signal returns the string signal directly.
                signal = strategy.generate_signal(df)
                current_price = df.iloc[-1]['close']
                
                print(f"[{time.strftime('%H:%M:%S')}] Price: {current_price} | Signal: {signal} | Postion: {position}")
                
                # --- Risk Management Checks ---
                if position == 'long':
                    # Stop Loss
                    if current_price < entry_price * (1 - args.stop_loss):
                        notifier.notify(f"STOP LOSS TRIGGERED! Current: {current_price}, Entry: {entry_price}")
                        if args.live:
                            order = exchange_client.create_market_sell_order(args.symbol, args.amount)
                            if order:
                                notifier.notify(f"SL EXECUTED: SELL {args.amount} @ {current_price}")
                                position = None
                                entry_price = 0.0
                        else:
                            position = None
                            entry_price = 0.0
                            notifier.notify(f"SL SIMULATED: SELL @ {current_price}")
                            
                    # Take Profit
                    elif current_price > entry_price * (1 + args.take_profit):
                        notifier.notify(f"TAKE PROFIT TRIGGERED! Current: {current_price}, Entry: {entry_price}")
                        if args.live:
                            order = exchange_client.create_market_sell_order(args.symbol, args.amount)
                            if order:
                                notifier.notify(f"TP EXECUTED: SELL {args.amount} @ {current_price}")
                                position = None
                                entry_price = 0.0
                        else:
                            position = None
                            entry_price = 0.0
                            notifier.notify(f"TP SIMULATED: SELL @ {current_price}")

                # --- Signal Checks ---
                if signal == 'buy':
                    if position is None:
                        notifier.alert_buy(args.symbol, current_price, strategy.name)
                        if args.live:
                            order = exchange_client.create_market_buy_order(args.symbol, args.amount)
                            if order:
                                notifier.notify(f"ORDER EXECUTED: BUY {args.amount} {args.symbol} @ {current_price}")
                                position = 'long'
                                entry_price = current_price
                        else:
                            position = 'long' # Paper trade
                            entry_price = current_price
                            
                elif signal == 'sell':
                    if position == 'long':
                        notifier.alert_sell(args.symbol, current_price, strategy.name)
                        if args.live:
                            order = exchange_client.create_market_sell_order(args.symbol, args.amount)
                            if order:
                                notifier.notify(f"ORDER EXECUTED: SELL {args.amount} {args.symbol} @ {current_price}")
                                position = None
                                entry_price = 0.0
                        else:
                            position = None # Paper trade
                            entry_price = 0.0
            
            # Rate limit / Wait for next candle
            time.sleep(10) # check every 10 seconds
            
        except KeyboardInterrupt:
            notifier.notify("Stopping Trading Bot...")
            break
        except Exception as e:
            notifier.notify(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
