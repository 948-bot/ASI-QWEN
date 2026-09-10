import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange

class TechnicalAnalyzer:
    def __init__(self, config):
        self.config = config
        
    def analyze(self, df, dxy_df=None):
        if df is None or df.empty: return None
        df = df.copy()
        
        # Standard Indicators
        df = self._calculate_rsi(df)
        df = self._calculate_macd(df)
        df = self._calculate_ema(df)
        df = self._calculate_atr(df)
        
        # ASI UPGRADE: Smart Money Concepts (SMC)
        df = self._calculate_smc(df)
        
        return df

    def _calculate_rsi(self, df):
        df['rsi'] = RSIIndicator(close=df['close'], window=self.config.RSI_PERIOD).rsi()
        return df

    def _calculate_macd(self, df):
        macd = MACD(close=df['close'], window_fast=self.config.MACD_FAST, window_slow=self.config.MACD_SLOW, window_sign=self.config.MACD_SIGNAL)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        return df

    def _calculate_ema(self, df):
        df['ema_short'] = EMAIndicator(close=df['close'], window=self.config.EMA_SHORT).ema_indicator()
        df['ema_long'] = EMAIndicator(close=df['close'], window=self.config.EMA_LONG).ema_indicator()
        df['ema_cross'] = (df['ema_short'] > df['ema_long']).astype(int)
        return df

    def _calculate_atr(self, df):
        df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=self.config.ATR_PERIOD).average_true_range()
        return df

    def _calculate_smc(self, df):
        """
        ASI UPGRADE: Menghitung Smart Money Concepts
        1. Liquidity Sweeps (Sweeping Swing High/Low)
        2. Fair Value Gaps (FVG) / Imbalance
        """
        lookback = self.config.SMC_LOOKBACK
        
        # Swing High & Low sederhana
        df['swing_high'] = df['high'] == df['high'].rolling(window=lookback, center=True).max()
        df['swing_low'] = df['low'] == df['low'].rolling(window=lookback, center=True).min()
        
        # Liquidity Sweep: Harga menembus swing low sebelumnya, tapi close di atasnya (Bullish Sweep)
        df['bullish_sweep'] = (df['low'] < df['low'].shift(1)) & (df['close'] > df['low'].shift(1))
        
        # Liquidity Sweep: Harga menembus swing high sebelumnya, tapi close di bawahnya (Bearish Sweep)
        df['bearish_sweep'] = (df['high'] > df['high'].shift(1)) & (df['close'] < df['high'].shift(1))
        
        # Fair Value Gap (FVG) Bullish: Low candle saat ini > High candle 2 periode lalu (Celah Imbalance naik)
        df['fvg_bullish'] = (df['low'] > df['high'].shift(2))
        
        # Fair Value Gap (FVG) Bearish: High candle saat ini < Low candle 2 periode lalu (Celah Imbalance turun)
        df['fvg_bearish'] = (df['high'] < df['low'].shift(2))
        
        return df

    def get_dxy_trend(self, dxy_df):
        """Menganalisis tren DXY untuk korelasi makro"""
        if dxy_df is None or dxy_df.empty:
            return 'neutral'
        
        latest = dxy_df.iloc[-1]
        prev = dxy_df.iloc[-5] if len(dxy_df) > 5 else dxy_df.iloc[0]
        
        if latest['close'] > prev['close'] * 1.001: # Naik > 0.1%
            return 'bullish'
        elif latest['close'] < prev['close'] * 0.999: # Turun > 0.1%
            return 'bearish'
        return 'neutral'
