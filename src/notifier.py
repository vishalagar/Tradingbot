import logging
import os
from datetime import datetime

class Notifier:
    def __init__(self):
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger("TradingBot")
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        # File handler
        os.makedirs("logs", exist_ok=True)
        fh = logging.FileHandler(f"logs/trading_bot_{datetime.now().strftime('%Y%m%d')}.log")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def notify(self, message):
        """
        Send a generic notification.
        """
        self.logger.info(message)

    def alert_buy(self, symbol, price, strategy_name):
        msg = f"BUY SIGNAL [{symbol}] @ {price} | Strategy: {strategy_name}"
        self.logger.warning(msg) # Warning level to make it stand out
        # Here you could add Email/Telegram/SMS integration

    def alert_sell(self, symbol, price, strategy_name):
        msg = f"SELL SIGNAL [{symbol}] @ {price} | Strategy: {strategy_name}"
        self.logger.warning(msg)
