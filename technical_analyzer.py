import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.trend import MACD

class TechnicalAnalyzer:
    def __init__(self, config):
        self.config = config
        
    def analyze(self, df):
        """Perform comprehensive technical analysis"""
        if df is None or df.empty:
            return None
            
        df = df.copy()
        
        # Calculate indicators
        df = self._calculate_rsi(df)
        df = self._calculate_macd(df)
        df = self._calculate_bollinger(df)
        df = self._calculate_ema(df)
        df = self._calculate_atr(df)
        df = self._calculate_support_resistance(df)
        df = self._calculate_volume_analysis(df)
        df = self._calculate_market_structure(df)
        
        return df
    
    def _calculate_rsi(self, df):
        """Calculate RSI"""
        rsi = RSIIndicator(close=df['close'], window=self.config.RSI_PERIOD)
        df['rsi'] = rsi.rsi()
        return df
    
    def _calculate_macd(self, df):
        """Calculate MACD"""
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
        """Calculate Bollinger Bands"""
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
        """Calculate EMA"""
        ema_short = EMAIndicator(close=df['close'], window=self.config.EMA_SHORT)
        ema_long = EMAIndicator(close=df['close'], window=self.config.EMA_LONG)
        df['ema_short'] = ema_short.ema_indicator()
        df['ema_long'] = ema_long.ema_indicator()
        df['ema_cross'] = (df['ema_short'] > df['ema_long']).astype(int)
        return df
    
    def _calculate_atr(self, df):
        """Calculate ATR for dynamic stop loss"""
        atr = AverageTrueRange(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=self.config.ATR_PERIOD
        )
        df['atr'] = atr.average_true_range()
        return df
    
    def _calculate_support_resistance(self, df):
        """Calculate support and resistance levels"""
        window = 20
        df['support'] = df['low'].rolling(window=window).min()
        df['resistance'] = df['high'].rolling(window=window).max()
        return df
    
    def _calculate_volume_analysis(self, df):
        """Analyze volume"""
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        return df
    
    def _calculate_market_structure(self, df):
        """Detect market structure (swing high/low)"""
        # Swing High: current high is higher than 2 candles before and after
        df['swing_high'] = (
            (df['high'] > df['high'].shift(1)) & 
            (df['high'] > df['high'].shift(2)) &
            (df['high'] > df['high'].shift(-1).fillna(df['high'].shift(1))) &
            (df['high'] > df['high'].shift(-2).fillna(df['high'].shift(2)))
        )
        
        # Swing Low: current low is lower than 2 candles before and after
        df['swing_low'] = (
            (df['low'] < df['low'].shift(1)) & 
            (df['low'] < df['low'].shift(2)) &
            (df['low'] < df['low'].shift(-1).fillna(df['low'].shift(1))) &
            (df['low'] < df['low'].shift(-2).fillna(df['low'].shift(2)))
        )
        
        # Detect trend structure
        df['higher_high'] = df['swing_high'] & (df['high'] > df['high'].shift(20).fillna(df['high'].min()))
        df['lower_low'] = df['swing_low'] & (df['low'] < df['low'].shift(20).fillna(df['low'].max()))
        
        return df
    
    def get_signal_strength(self, df):
        """Calculate overall signal strength"""
        if df is None or df.empty:
            return 0
            
        latest = df.iloc[-1]
        strength = 0
        
        # RSI signals
        if latest['rsi'] < 30:
            strength += 2  # Oversold
        elif latest['rsi'] > 70:
            strength -= 2  # Overbought
        
        # MACD signals
        if latest['macd'] > latest['macd_signal']:
            strength += 1
        elif latest['macd'] < latest['macd_signal']:
            strength -= 1
        
        # EMA cross
        if latest['ema_cross'] == 1:
            strength += 1
        else:
            strength -= 1
        
        # Bollinger Bands
        if latest['close'] < latest['bb_lower']:
            strength += 1  # Below lower band
        elif latest['close'] > latest['bb_upper']:
            strength -= 1  # Above upper band
        
        # Volume confirmation
        if latest['volume_ratio'] > 1.5:
            strength *= 1.2  # Boost signal if high volume
        
        return strength
    
    def get_trend_direction(self, df):
        """Determine trend direction from higher timeframe"""
        if df is None or df.empty:
            return 'neutral'
        
        latest = df.iloc[-1]
        
        if latest['ema_short'] > latest['ema_long'] and latest['close'] > latest['ema_long']:
            return 'uptrend'
        elif latest['ema_short'] < latest['ema_long'] and latest['close'] < latest['ema_long']:
            return 'downtrend'
        else:
            return 'sideways'
