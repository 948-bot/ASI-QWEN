import json
import os
from datetime import datetime
import numpy as np

class SelfLearning:
    def __init__(self, config):
        self.config = config
        self.history_file = 'signal_history.json'
        self.performance_file = 'performance.json'
        self.signal_history = self._load_history()
        self.performance_data = self._load_performance()
        
    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _load_performance(self):
        if os.path.exists(self.performance_file):
            with open(self.performance_file, 'r') as f:
                return json.load(f)
        return {'total_signals': 0, 'successful': 0, 'failed': 0}
    
    def record_signal(self, signal):
        """Catat sinyal ASI (Format Baru)"""
        signal_record = {
            'timestamp': signal['timestamp'].isoformat(),
            'timeframe': signal['timeframe'],
            'type': signal['type'],
            'price': signal['price'],
            'confidence': signal['confidence'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'atr': signal.get('atr', 0),
            'dxy_trend': signal.get('dxy_trend', 'N/A'),
            'mtf_trend': signal.get('mtf_trend', 'N/A'),
            'outcome': 'pending'
        }
        
        self.signal_history.append(signal_record)
        self._save_history()
        
        if len(self.signal_history) > self.config.HISTORY_SIZE:
            self.signal_history = self.signal_history[-self.config.HISTORY_SIZE:]
            self._save_history()
    
    def _save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.signal_history, f, indent=2)
    
    def update_outcome(self, signal_index, outcome, final_price):
        if signal_index < len(self.signal_history):
            self.signal_history[signal_index]['outcome'] = outcome
            self.signal_history[signal_index]['final_price'] = final_price
            self._save_history()
            
            self.performance_data['total_signals'] += 1
            if outcome == 'success':
                self.performance_data['successful'] += 1
            else:
                self.performance_data['failed'] += 1
            self._save_performance()
    
    def _save_performance(self):
        with open(self.performance_file, 'w') as f:
            json.dump(self.performance_data, f, indent=2)
    
    def analyze_performance(self):
        if not self.signal_history: return None
        successful = [s for s in self.signal_history if s['outcome'] == 'success']
        failed = [s for s in self.signal_history if s['outcome'] == 'failed']
        
        return {
            'total': len(self.signal_history),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(self.signal_history) * 100 if self.signal_history else 0,
        }
    
    def get_learning_insights(self):
        analysis = self.analyze_performance()
        if not analysis: return "Belum cukup data untuk analisis"
        return f"📊 Total: {analysis['total']} | Win: {analysis['successful']} | Rate: {analysis['success_rate']:.1f}%"
    
    def check_and_restart(self):
        try:
            self._load_history()
            return True
        except:
            self.signal_history = []
            self._save_history()
            return False
