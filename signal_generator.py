from datetime import datetime, timedelta
import time

class SignalGenerator:
    def __init__(self, config):
        self.config = config
        self.signal_history = []
        self.last_signal_time = {}
        self.performance_tracker = {}
        
    def generate_signals(self, analysis_data):
        signals = []
        
        for timeframe, df in analysis_data.items():
            if df is None or df.empty:
                continue
                
            signal = self._analyze_timeframe(df, timeframe)
            if signal:
                signals.append(signal)
        
        return self._filter_and_rank_signals(signals)
    
    def _analyze_timeframe(self, df, timeframe):
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal_type = None
        confidence = 0
        
        if not self._can_send_signal(timeframe):
            return None
        
        if self._is_buy_signal(latest, prev, df):
            signal_type = 'BUY'
            confidence = self._calculate_confidence(df, 'BUY')
        
        elif self._is_sell_signal(latest, prev, df):
            signal_type = 'SELL'
            confidence = self._calculate_confidence(df, 'SELL')
        
        if signal_type and confidence >= 60:
            signal = {
                'timeframe': timeframe,
                'type': signal_type,
                'confidence': confidence,
                'price': latest['close'],
                'timestamp': datetime.now(),
                'indicators': self._get_indicator_values(latest),
                'stop_loss': self._calculate_stop_loss(latest['close'], signal_type),
                'take_profit': self._calculate_take_profit(latest['close'], signal_type),
                'risk_reward': self._calculate_risk_reward(latest['close'], signal_type)
            }
            
            self.last_signal_time[timeframe] = datetime.now()
            return signal
        
        return None
    
    def _is_buy_signal(self, latest, prev, df):
        conditions = [
            latest['rsi'] < 35,
            latest['macd'] > latest['macd_signal'],
            latest['ema_cross'] == 1,
            latest['close'] < latest['bb_lower'],
            latest['volume_ratio'] > 1.2
        ]
        return sum(conditions) >= 3
    
    def _is_sell_signal(self, latest, prev, df):
        conditions = [
            latest['rsi'] > 65,
            latest['macd'] < latest['macd_signal'],
            latest['ema_cross'] == 0,
            latest['close'] > latest['bb_upper'],
            latest['volume_ratio'] > 1.2
        ]
        return sum(conditions) >= 3
    
    def _calculate_confidence(self, df, signal_type):
        latest = df.iloc[-1]
        confidence = 50
        
        if signal_type == 'BUY':
            if latest['rsi'] < 30:
                confidence += 15
            if latest['macd'] > latest['macd_signal']:
                confidence += 10
            if latest['volume_ratio'] > 1.5:
                confidence += 10
        else:
            if latest['rsi'] > 70:
                confidence += 15
            if latest['macd'] < latest['macd_signal']:
                confidence += 10
            if latest['volume_ratio'] > 1.5:
                confidence += 10
        
        return min(confidence, 95)
    
    def _calculate_stop_loss(self, price, signal_type):
        if signal_type == 'BUY':
            return price * (1 - self.config.STOP_LOSS_PERCENT / 100)
        else:
            return price * (1 + self.config.STOP_LOSS_PERCENT / 100)
    
    def _calculate_take_profit(self, price, signal_type):
        if signal_type == 'BUY':
            return price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
        else:
            return price * (1 - self.config.TAKE_PROFIT_PERCENT / 100)
    
    def _calculate_risk_reward(self, price, signal_type):
        sl = self._calculate_stop_loss(price, signal_type)
        tp = self._calculate_take_profit(price, signal_type)
        risk = abs(price - sl)
        reward = abs(tp - price)
        return reward / risk if risk > 0 else 0
    
    def _get_indicator_values(self, latest):
        return {
            'RSI': round(latest['rsi'], 2),
            'MACD': round(latest['macd'], 4),
            'EMA_Short': round(latest['ema_short'], 2),
            'EMA_Long': round(latest['ema_long'], 2),
            'BB_Upper': round(latest['bb_upper'], 2),
            'BB_Lower': round(latest['bb_lower'], 2)
        }
    
    def _can_send_signal(self, timeframe):
        if timeframe not in self.last_signal_time:
            return True
        
        time_diff = datetime.now() - self.last_signal_time[timeframe]
        return time_diff.total_seconds() >= self.config.MIN_SIGNAL_INTERVAL
    
    def _filter_and_rank_signals(self, signals):
        if not signals:
            return []
        
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        return signals[:3]
