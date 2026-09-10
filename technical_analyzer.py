import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

class TechnicalAnalyzer:
    def __init__(self, config):
        self.config = config
        
    def analyze(self, df):
        if df is None or df.empty:
            return None
            
        df = df.copy()
        df = self._calculate_rsi(df)
        df = self._calculate_macd(df)
        df = self._calculate_bollinger(df)
        df = self._calculate_ema(df)
        df = self._calculate_support_resistance(df)
        df = self._calculate_volume_analysis(df)
        
        return df
    
    def _calculate_rsi(self, df):
        rsi = RSIIndicator(close=df['close'], window=self.config.RSI_PERIOD)
        df['rsi'] = rsi.rsi()
        return df
    
    def _calculate_macd(self, df):
        macd = MACD(
            close=df['close'],
            window_fast=self.config.MACD_FAST,
            window_slow=self.config.MACD_SLOW,
            window_sign=self.config.MACD_SIGNAL
        )
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()
        return df
    
    def _calculate_bollinger(self, df):
        bb = BollingerBands(
            close=df['close'],
            window=self.config.BOLLINGER_PERIOD,
            window_dev=self.config.BOLLINGER_STD
        )
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        return df
    
    def _calculate_ema(self, df):
        ema_short = EMAIndicator(close=df['close'], window=self.config.EMA_SHORT)
        ema_long = EMAIndicator(close=df['close'], window=self.config.EMA_LONG)
        df['ema_short'] = ema_short.ema_indicator()
        df['ema_long'] = ema_long.ema_indicator()
        df['ema_cross'] = (df['ema_short'] > df['ema_long']).astype(int)
        return df
    
    def _calculate_support_resistance(self, df):
        window = 20
        df['support'] = df['low'].rolling(window=window).min()
        df['resistance'] = df['high'].rolling(window=window).max()
        return df
    
    def _calculate_volume_analysis(self, df):
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        return df
    
    def get_signal_strength(self, df):
        if df is None or df.empty:
            return 0
            
        latest = df.iloc[-1]
        strength = 0
        
        if latest['rsi'] < 30:
            strength += 2
        elif latest['rsi'] > 70:
            strength -= 2
        
        if latest['macd'] > latest['macd_signal']:
            strength += 1
        elif latest['macd'] < latest['macd_signal']:
            strength -= 1
        
        if latest['ema_cross'] == 1:
            strength += 1
        else:
            strength -= 1
        
        if latest['close'] < latest['bb_lower']:
            strength += 1
        elif latest['close'] > latest['bb_upper']:
            strength -= 1
        
        if latest['volume_ratio'] > 1.5:
            strength *= 1.2
        
        return strength
