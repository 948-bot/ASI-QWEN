import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Trading Configuration
    PAXG_SYMBOL = os.getenv('PAXG_SYMBOL', 'frxXAUUSD')
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 60))
    RISK_LEVEL = os.getenv('RISK_LEVEL', 'high') # ASI Level uses high precision
    MAX_SIGNALS_PER_HOUR = int(os.getenv('MAX_SIGNALS_PER_HOUR', 5)) # Lebih sedikit, lebih berkualitas
    
    # Timeframes
    TIMEFRAMES = ['5m', '15m']
    
    # Technical Analysis Parameters
    RSI_PERIOD = 14
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD = 2
    EMA_SHORT = 9
    EMA_LONG = 21
    ATR_PERIOD = 14
    
    # Intermarket & SMC Configuration (ASI LEVEL)
    DXY_SYMBOL = 'DX-Y.NYB' # Yahoo Finance ticker untuk US Dollar Index
    SMC_LOOKBACK = 20       # Periode untuk mencari Swing High/Low
    MIN_CONFIDENCE_ASI = 70 # Skor minimal untuk mengirim sinyal (Sangat Ketat)
    
    # Risk Management
    ATR_MULTIPLIER_SL = float(os.getenv('ATR_MULTIPLIER_SL', 1.5))
    ATR_MULTIPLIER_TP = float(os.getenv('ATR_MULTIPLIER_TP', 3.0))
    
    # Filters
    USE_NEWS_FILTER = os.getenv('USE_NEWS_FILTER', 'true').lower() == 'true'
    USE_MTF_CONFLUENCE = os.getenv('USE_MTF_CONFLUENCE', 'true').lower() == 'true'
    
    # Self-Learning & Anti-Spam
    LEARNING_RATE = 0.01
    HISTORY_SIZE = 1000
    MIN_SIGNAL_INTERVAL = 600 # 10 menit (Supaya tidak spam)
    
    # GitHub Actions
    IS_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'
    GITHUB_RUN_ID = os.getenv('GITHUB_RUN_ID')
    GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')
    DATA_DIR = 'data'
    LOG_DIR = 'logs'
    NEWS_BLACKOUT_HOURS = [13, 14, 19, 20] 
    
    @classmethod
    def validate(cls):
        errors = []
        if not cls.TELEGRAM_BOT_TOKEN: errors.append("TELEGRAM_BOT_TOKEN not set")
        if not cls.TELEGRAM_CHAT_ID: errors.append("TELEGRAM_CHAT_ID not set")
        if errors: raise ValueError(f"Configuration errors: {', '.join(errors)}")
        return True
