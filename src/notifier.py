import logging
import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

class Notifier:
    def __init__(self):
        self._setup_logger()
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.email_host = os.getenv('EMAIL_HOST')
        self.email_port = os.getenv('EMAIL_PORT')
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_to = os.getenv('EMAIL_TO')

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
        self.logger.info(message)
        # self.send_telegram(message)
        # self.send_email("Trading Bot Notification", message)
        """

    def alert_buy(self, symbol, price, strategy_name):
        msg = f"BUY SIGNAL [{symbol}] @ {price} | Strategy: {strategy_name}"
        self.logger.warning(msg) 
        # self.send_telegram(msg)
        # self.send_email(f"BUY ALERT: {symbol}", msg)

    def alert_sell(self, symbol, price, strategy_name):
        msg = f"SELL SIGNAL [{symbol}] @ {price} | Strategy: {strategy_name}"
        self.logger.warning(msg)
        # self.send_telegram(msg)
        # self.send_email(f"SELL ALERT: {symbol}", msg)
        
    def send_telegram(self, message):
        if self.telegram_token and self.telegram_chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                payload = {
                    "chat_id": self.telegram_chat_id,
                    "text": message
                }
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                self.logger.error(f"Failed to send Telegram: {e}")

    def send_email(self, subject, body):
        if self.email_host and self.email_user and self.email_password and self.email_to:
            try:
                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = self.email_user
                msg['To'] = self.email_to
                
                # Assume TLS (587) or SSL (465) based on port, simple heuristic
                if str(self.email_port) == '465':
                    with smtplib.SMTP_SSL(self.email_host, self.email_port) as server:
                        server.login(self.email_user, self.email_password)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(self.email_host, self.email_port) as server:
                        server.starttls()
                        server.login(self.email_user, self.email_password)
                        server.send_message(msg)
            except Exception as e:
                self.logger.error(f"Failed to send Email: {e}")
