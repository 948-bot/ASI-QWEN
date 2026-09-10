import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class SelfLearning:
    def __init__(self, config):
        self.config = config
        self.history_file = 'signal_history.json'
        self.performance_file = 'performance.json'
        self.parameters_file = 'optimized_parameters.json'
        self.signal_history = self._load_history()
        self.performance_data = self._load_performance()
        
    def _load_history(self):
        """Load signal history from file"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _load_performance(self):
        """Load performance data"""
        if os.path.exists(self.performance_file):
            with open(self.performance_file, 'r') as f:
                return json.load(f)
        return {'total_signals': 0, 'successful': 0, 'failed': 0}
    
    def record_signal(self, signal):
        """Record a signal for future learning"""
        signal_record = {
            'timestamp': signal['timestamp'].isoformat(),
            'timeframe': signal['timeframe'],
            'type': signal['type'],
            'price': signal['price'],
            'confidence': signal['confidence'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'indicators': signal['indicators'],
            'outcome': 'pending'
        }
        
        self.signal_history.append(signal_record)
        self._save_history()
        
        # Keep only recent history
        if len(self.signal_history) > self.config.HISTORY_SIZE:
            self.signal_history = self.signal_history[-self.config.HISTORY_SIZE:]
            self._save_history()
    
    def _save_history(self):
        """Save signal history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.signal_history, f, indent=2)
    
    def update_outcome(self, signal_index, outcome, final_price):
        """Update signal outcome after it resolves"""
        if signal_index < len(self.signal_history):
            self.signal_history[signal_index]['outcome'] = outcome
            self.signal_history[signal_index]['final_price'] = final_price
            self._save_history()
            
            # Update performance
            self.performance_data['total_signals'] += 1
            if outcome == 'success':
                self.performance_data['successful'] += 1
            else:
                self.performance_data['failed'] += 1
            
            self._save_performance()
    
    def _save_performance(self):
        """Save performance data"""
        with open(self.performance_file, 'w') as f:
            json.dump(self.performance_data, f, indent=2)
    
    def analyze_performance(self):
        """Analyze historical performance"""
        if not self.signal_history:
            return None
        
        successful = [s for s in self.signal_history if s['outcome'] == 'success']
        failed = [s for s in self.signal_history if s['outcome'] == 'failed']
        
        analysis = {
            'total': len(self.signal_history),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(self.signal_history) * 100 if self.signal_history else 0,
            'avg_confidence_success': np.mean([s['confidence'] for s in successful]) if successful else 0,
            'avg_confidence_failed': np.mean([s['confidence'] for s in failed]) if failed else 0
        }
        
        return analysis
    
    def optimize_parameters(self):
        """Optimize parameters based on historical performance"""
        if len(self.signal_history) < 50:
            return None  # Not enough data
        
        successful = [s for s in self.signal_history if s['outcome'] == 'success']
        
        if not successful:
            return None
        
        # Analyze what made successful signals work
        avg_rsi_buy = np.mean([s['indicators']['RSI'] for s in successful if s['type'] == 'BUY'])
        avg_rsi_sell = np.mean([s['indicators']['RSI'] for s in successful if s['type'] == 'SELL'])
        
        optimized = {
            'rsi_oversold': max(25, avg_rsi_buy - 5) if avg_rsi_buy else 30,
            'rsi_overbought': min(75, avg_rsi_sell + 5) if avg_rsi_sell else 70,
            'min_confidence': 65,  # Increase minimum confidence
            'timestamp': datetime.now().isoformat()
        }
        
        # Save optimized parameters
        with open(self.parameters_file, 'w') as f:
            json.dump(optimized, f, indent=2)
        
        return optimized
    
    def get_learning_insights(self):
        """Get insights from learning"""
        analysis = self.analyze_performance()
        if not analysis:
            return "Belum cukup data untuk analisis"
        
        insights = f"""
📊 *ANALISIS PERFORMA*

Total Sinyal: {analysis['total']}
Berhasil: {analysis['successful']}
Gagal: {analysis['failed']}
Success Rate: {analysis['success_rate']:.2f}%

Avg Confidence (Success): {analysis['avg_confidence_success']:.2f}
Avg Confidence (Failed): {analysis['avg_confidence_failed']:.2f}
        """
        
        return insights.strip()
    
    def check_and_restart(self):
        """Check system health and restart if needed"""
        # Check if history file is corrupted
        try:
            self._load_history()
            return True
        except:
            # Reset history
            self.signal_history = []
            self._save_history()
            return False
