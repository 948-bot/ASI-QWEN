from datetime import datetime, timedelta
import time

class SignalGenerator:
    def __init__(self, config):
        self.config = config
        self.signal_history = []
        self.last_signal_time = {}
        self.performance_tracker = {}
        self.signals_this_hour = 0
        self.last_hour = datetime.now().hour
        
    def generate_signals(self, analysis_data):
        """Generate trading signals from analysis data"""
        # Reset hourly counter if new hour
        if datetime.now().hour != self.last_hour:
            self.signals_this_hour = 0
            self.last_hour = datetime.now().hour
        
        # Check if we've reached max signals per hour
        if self.signals_this_hour >= self.config.MAX_SIGNALS_PER_HOUR:
            print(f"⚠️ Max signals per hour reached ({self.config.MAX_SIGNALS_PER_HOUR})")
            return []
        
        # Check news filter
        if self.config.USE_NEWS_FILTER and self._is_news_time():
            print("⚠️ News blackout period - skipping signal generation")
            return []
        
        signals = []
        
        # Get trend from higher timeframe (15m)
        mtf_trend = 'neutral'
        if self.config.USE_MTF_CONFLUENCE and '15m' in analysis_data:
            mtf_trend = self._get_mtf_trend(analysis_data['15m'])
        
        for timeframe, df in analysis_data.items():
            if df is None or df.empty:
                continue
                
            signal = self._analyze_timeframe(df, timeframe, mtf_trend)
            if signal:
                signals.append(signal)
        
        return self._filter_and_rank_signals(signals)
    
    def _get_mtf_trend(self, df_15m):
        """Get trend from 15m timeframe for confluence"""
        latest = df_15m.iloc[-1]
        
        if latest['ema_short'] > latest['ema_long']:
            return 'bullish'
        elif latest['ema_short'] < latest['ema_long']:
            return 'bearish'
        else:
            return 'neutral'
    
    def _analyze_timeframe(self, df, timeframe, mtf_trend='neutral'):
        """Analyze single timeframe for signals"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal_type = None
        confidence = 0
        
        # Check for anti-spam
        if not self._can_send_signal(timeframe):
            return None
        
        # Check MTF confluence
        if self.config.USE_MTF_CONFLUENCE and timeframe == '5m':
            if mtf_trend == 'bullish':
                # Only look for BUY signals in 5m when 15m is bullish
                if self._is_buy_signal(latest, prev, df):
                    signal_type = 'BUY'
                    confidence = self._calculate_confidence(df, 'BUY', mtf_trend)
            elif mtf_trend == 'bearish':
                # Only look for SELL signals in 5m when 15m is bearish
                if self._is_sell_signal(latest, prev, df):
                    signal_type = 'SELL'
                    confidence = self._calculate_confidence(df, 'SELL', mtf_trend)
        else:
            # Normal signal generation
            if self._is_buy_signal(latest, prev, df):
                signal_type = 'BUY'
                confidence = self._calculate_confidence(df, 'BUY', mtf_trend)
            elif self._is_sell_signal(latest, prev, df):
                signal_type = 'SELL'
                confidence = self._calculate_confidence(df, 'SELL', mtf_trend)
        
        if signal_type and confidence >= 60:
            # Calculate dynamic SL/TP using ATR
            atr = latest['atr']
            sl_distance = atr * self.config.ATR_MULTIPLIER_SL
            tp_distance = atr * self.config.ATR_MULTIPLIER_TP
            
            if signal_type == 'BUY':
                stop_loss = latest['close'] - sl_distance
                take_profit = latest['close'] + tp_distance
            else:
                stop_loss = latest['close'] + sl_distance
                take_profit = latest['close'] - tp_distance
            
            risk_reward = abs(take_profit - latest['close']) / abs(latest['close'] - stop_loss)
            
            signal = {
                'timeframe': timeframe,
                'type': signal_type,
                'confidence': confidence,
                'price': latest['close'],
                'timestamp': datetime.now(),
                'indicators': self._get_indicator_values(latest),
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward': risk_reward,
                'atr': atr,
                'mtf_trend': mtf_trend
            }
            
            self.last_signal_time[timeframe] = datetime.now()
            self.signals_this_hour += 1
            return signal
        
        return None
    
    def _is_buy_signal(self, latest, prev, df):
        """Check for buy conditions"""
        conditions = [
            latest['rsi'] < 35,  # Oversold
            latest['macd'] > latest['macd_signal'],  # MACD bullish
            latest['ema_cross'] == 1,  # EMA bullish cross
            latest['close'] < latest['bb_lower'],  # Below lower BB
            latest['volume_ratio'] > 1.2  # Volume confirmation
        ]
        
        # Need at least 3 conditions
        return sum(conditions) >= 3
    
    def _is_sell_signal(self, latest, prev, df):
        """Check for sell conditions"""
        conditions = [
            latest['rsi'] > 65,  # Overbought
            latest['macd'] < latest['macd_signal'],  # MACD bearish
            latest['ema_cross'] == 0,  # EMA bearish cross
            latest['close'] > latest['bb_upper'],  # Above upper BB
            latest['volume_ratio'] > 1.2  # Volume confirmation
        ]
        
        # Need at least 3 conditions
        return sum(conditions) >= 3
    
    def _calculate_confidence(self, df, signal_type, mtf_trend='neutral'):
        """Calculate signal confidence with MTF confluence bonus"""
        latest = df.iloc[-1]
        confidence = 50  # Base confidence
        
        # MTF Confluence bonus
        if self.config.USE_MTF_CONFLUENCE:
            if signal_type == 'BUY' and mtf_trend == 'bullish':
                confidence += 15  # Big bonus for trend alignment
            elif signal_type == 'SELL' and mtf_trend == 'bearish':
                confidence += 15
            elif mtf_trend != 'neutral':
                confidence -= 10  # Penalty for counter-trend
        
        # Adjust based on indicator alignment
        if signal_type == 'BUY':
            if latest['rsi'] < 30:
                confidence += 15
            if latest['macd'] > latest['macd_signal']:
                confidence += 10
            if latest['volume_ratio'] > 1.5:
                confidence += 10
            if latest['close'] < latest['bb_lower']:
                confidence += 5
        else:  # SELL
            if latest['rsi'] > 70:
                confidence += 15
            if latest['macd'] < latest['macd_signal']:
                confidence += 10
            if latest['volume_ratio'] > 1.5:
                confidence += 10
            if latest['close'] > latest['bb_upper']:
                confidence += 5
        
        return min(confidence, 95)
    
    def _get_indicator_values(self, latest):
        """Get current indicator values"""
        return {
            'RSI': round(latest['rsi'], 2),
            'MACD': round(latest['macd'], 4),
            'EMA_Short': round(latest['ema_short'], 2),
            'EMA_Long': round(latest['ema_long'], 2),
            'BB_Upper': round(latest['bb_upper'], 2),
            'BB_Lower': round(latest['bb_lower'], 2),
            'ATR': round(latest['atr'], 2)
        }
    
    def _can_send_signal(self, timeframe):
        """Check if we can send signal (anti-spam)"""
        if timeframe not in self.last_signal_time:
            return True
        
        time_diff = datetime.now() - self.last_signal_time[timeframe]
        return time_diff.total_seconds() >= self.config.MIN_SIGNAL_INTERVAL
    
    def _filter_and_rank_signals(self, signals):
        """Filter and rank signals by confidence"""
        if not signals:
            return []
        
        # Sort by confidence
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Return top signals
        return signals[:3]
    
    def _is_news_time(self):
        """Check if current time is during high-impact news"""
        current_hour = datetime.utcnow().hour
        return current_hour in self.config.NEWS_BLACKOUT_HOURS
