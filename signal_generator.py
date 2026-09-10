from datetime import datetime

class SignalGenerator:
    def __init__(self, config):
        self.config = config
        self.last_signal_time = {}
        self.signals_this_hour = 0
        self.last_hour = datetime.now().hour
        
    def generate_signals(self, analysis_data, dxy_trend='neutral'):
        if datetime.now().hour != self.last_hour:
            self.signals_this_hour = 0
            self.last_hour = datetime.now().hour
            
        if self.signals_this_hour >= self.config.MAX_SIGNALS_PER_HOUR:
            return []
            
        signals = []
        mtf_trend = 'neutral'
        
        if self.config.USE_MTF_CONFLUENCE and '15m' in analysis_data and analysis_data['15m'] is not None:
            df_15m = analysis_data['15m']
            latest_15m = df_15m.iloc[-1]
            if latest_15m['ema_short'] > latest_15m['ema_long']:
                mtf_trend = 'bullish'
            elif latest_15m['ema_short'] < latest_15m['ema_long']:
                mtf_trend = 'bearish'

        # Fokus evaluasi terstruktur untuk menghindari konflik arah sinyal
        target_timeframes = ['15m', '5m']
        
        for timeframe in target_timeframes:
            if timeframe not in analysis_data or analysis_data[timeframe] is None:
                continue
                
            df = analysis_data[timeframe]
            signal = self._analyze_timeframe(df, timeframe, mtf_trend, dxy_trend)
            if signal:
                # Cegah sinyal yang berlawanan arah dalam cycle yang sama
                if signals and signals[0]['type'] != signal['type']:
                    continue
                signals.append(signal)
                
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Batasi maksimal hanya 1 sinyal terkuat per cycle agar tidak konflik & akurat
        return signals[:1]

    def _analyze_timeframe(self, df, timeframe, mtf_trend, dxy_trend):
        latest = df.iloc[-1]
        
        if not self._can_send_signal(timeframe):
            return None
            
        # === ASI SCORING SYSTEM ===
        score = 50 # Base score
        signal_type = None
        
        # 1. SMC Liquidity Sweeps (Sangat Akurat untuk Reversal)
        if latest.get('bullish_sweep', False):
            score += 25
            signal_type = 'BUY'
        elif latest.get('bearish_sweep', False):
            score += 25
            signal_type = 'SELL'
            
        # 2. Fair Value Gaps (FVG)
        if latest.get('fvg_bullish', False) and signal_type == 'BUY':
            score += 15
        elif latest.get('fvg_bearish', False) and signal_type == 'SELL':
            score += 15
            
        # 3. Intermarket Correlation (DXY)
        # Emas berbanding terbalik dengan Dolar
        if dxy_trend == 'bearish' and signal_type == 'BUY':
            score += 20 # Dolar lemah, Emas kuat
        elif dxy_trend == 'bullish' and signal_type == 'SELL':
            score += 20 # Dolar kuat, Emas lemah
        elif dxy_trend == 'bullish' and signal_type == 'BUY':
            score -= 30 # Kontradiksi makro, batalkan BUY
        elif dxy_trend == 'bearish' and signal_type == 'SELL':
            score -= 30 # Kontradiksi makro, batalkan SELL
            
        # 4. MTF Confluence
        if self.config.USE_MTF_CONFLUENCE:
            if mtf_trend == 'bullish' and signal_type == 'BUY':
                score += 15
            elif mtf_trend == 'bearish' and signal_type == 'SELL':
                score += 15
            elif mtf_trend != signal_type.lower() and signal_type is not None:
                score -= 20
                
        # 5. Standard Indicators (RSI & MACD)
        if signal_type == 'BUY' and latest['rsi'] < 40 and latest['macd'] > latest['macd_signal']:
            score += 10
        elif signal_type == 'SELL' and latest['rsi'] > 60 and latest['macd'] < latest['macd_signal']:
            score += 10

        # === FINAL DECISION ===
        if signal_type and score >= self.config.MIN_CONFIDENCE_ASI:
            atr = latest['atr']
            sl_distance = atr * self.config.ATR_MULTIPLIER_SL
            tp_distance = atr * self.config.ATR_MULTIPLIER_TP
            
            if signal_type == 'BUY':
                stop_loss = latest['close'] - sl_distance
                take_profit = latest['close'] + tp_distance
            else:
                stop_loss = latest['close'] + sl_distance
                take_profit = latest['close'] - tp_distance
                
            self.last_signal_time[timeframe] = datetime.now()
            self.signals_this_hour += 1
            
            return {
                'timeframe': timeframe, 'type': signal_type, 'confidence': score,
                'price': latest['close'], 'timestamp': datetime.now(),
                'stop_loss': stop_loss, 'take_profit': take_profit,
                'risk_reward': abs(tp_distance/sl_distance) if sl_distance > 0 else 0,
                'atr': atr, 'mtf_trend': mtf_trend, 'dxy_trend': dxy_trend
            }
        return None

    def _can_send_signal(self, timeframe):
        if timeframe not in self.last_signal_time: return True
        time_diff = datetime.now() - self.last_signal_time[timeframe]
        return time_diff.total_seconds() >= self.config.MIN_SIGNAL_INTERVAL
