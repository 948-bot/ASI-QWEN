# ============================================================
# XAUUSD/PAXG TRADING BOT - MAIN FILE
# File ini adalah entry point untuk menjalankan bot trading
# ============================================================

import asyncio
import sys
import signal
import time
import os
from datetime import datetime

# Import modul-modul bot
from config import Config
from data_fetcher import DataFetcher
from technical_analyzer import TechnicalAnalyzer
from signal_generator import SignalGenerator
from telegram_notifier import TelegramNotifier
from self_learning import SelfLearning


class TradingBot:
    """Class utama untuk menjalankan bot trading"""
    
    def __init__(self):
        self.config = Config()
        self.fetcher = DataFetcher(self.config.PAXG_SYMBOL)
        self.analyzer = TechnicalAnalyzer(self.config)
        self.generator = SignalGenerator(self.config)
        self.notifier = TelegramNotifier(
            self.config.TELEGRAM_BOT_TOKEN,
            self.config.TELEGRAM_CHAT_ID
        )
        self.learner = SelfLearning(self.config)
        self.running = True
        self.cycle_count = 0
        
    async def start(self):
        """Start the trading bot - method utama"""
        print("=" * 60)
        print("🚀 XAUUSD/PAXG SIGNAL BOT DIMULAI")
        print("=" * 60)
        print(f"Symbol: {self.config.PAXG_SYMBOL}")
        print(f"Timeframes: {', '.join(self.config.TIMEFRAMES)}")
        print(f"Update Interval: {self.config.UPDATE_INTERVAL}s")
        print(f"MTF Confluence: {self.config.USE_MTF_CONFLUENCE}")
        print(f"News Filter: {self.config.USE_NEWS_FILTER}")
        print("=" * 60)
        
        # Send startup notification
        await self.notifier.send_notification(
            "🚀 *BOT TRADING DIMULAI*\n\n"
            f"Symbol: {self.config.PAXG_SYMBOL}\n"
            f"Timeframes: {', '.join(self.config.TIMEFRAMES)}\n"
            f"MTF Confluence: {self.config.USE_MTF_CONFLUENCE}\n"
            f"News Filter: {self.config.USE_NEWS_FILTER}\n"
            f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Main loop - bot akan jalan terus sampai timeout GitHub
        while self.running:
            try:
                await self._run_cycle()
                self.cycle_count += 1
                
                # Periodic tasks every 10 cycles
                if self.cycle_count % 10 == 0:
                    await self._periodic_tasks()
                
                # Wait for next cycle
                await asyncio.sleep(self.config.UPDATE_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n⚠️ Bot dihentikan oleh user")
                break
            except Exception as e:
                error_msg = f"Error dalam cycle: {str(e)}"
                print(f"❌ {error_msg}")
                try:
                    await self.notifier.send_error(error_msg)
                except:
                    pass
                await self._handle_error(e)
        
        await self.shutdown()
    
    async def _run_cycle(self):
        """Run one analysis cycle"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Cycle #{self.cycle_count + 1}")
        
        # Fetch data dari Binance/Yahoo
        data = await self.fetcher.fetch_multiple_timeframes()
        
        # Tampilkan info data source
        source_info = self.fetcher.get_data_source_info()
        if source_info:
            print(f"📊 Data sources: {source_info}")
        
        if not data or all(df is None for df in data.values()):
            print("️ Tidak ada data, skip cycle ini")
            return
        
        # Analyze data untuk setiap timeframe
        analysis_results = {}
        for timeframe, df in data.items():
            if df is not None:
                analysis_results[timeframe] = self.analyzer.analyze(df)
        
        # Generate signals
        signals = self.generator.generate_signals(analysis_results)
        
        # Process signals
        if signals:
            print(f"✅ {len(signals)} sinyal ditemukan")
            for signal in signals:
                await self._process_signal(signal)
        else:
            print("ℹ️ Tidak ada sinyal valid")
    
    async def _process_signal(self, signal):
        """Process and send a signal"""
        # Record signal for learning
        self.learner.record_signal(signal)
        
        # Send to Telegram
        await self.notifier.send_signal(signal)
        
        mtf_info = signal.get('mtf_trend', 'N/A')
        print(f"📤 Signal {signal['type']} dikirim | Confidence: {signal['confidence']}% | MTF: {mtf_info}")
    
    async def _periodic_tasks(self):
        """Run periodic maintenance tasks"""
        print("\n Menjalankan tugas periodik...")
        
        # Analyze performance
        insights = self.learner.get_learning_insights()
        print(insights)
        
        # Optimize parameters if enough data
        optimized = self.learner.optimize_parameters()
        if optimized:
            print(f"✅ Parameter dioptimasi: {optimized}")
        
        # Health check
        if not self.learner.check_and_restart():
            print("⚠️ Sistem perlu restart")
            await self.notifier.send_notification("⚠️ Sistem melakukan self-restart")
    
    async def _handle_error(self, error):
        """Handle errors and attempt recovery"""
        print(f"🔄 Mencoba recovery...")
        await asyncio.sleep(5)
    
    async def shutdown(self):
        """Graceful shutdown"""
        print("\n" + "=" * 60)
        print("🛑 Bot sedang shutdown...")
        print("=" * 60)
        
        # Send shutdown notification
        try:
            await self.notifier.send_notification(
                "🛑 *BOT TRADING BERHENTI*\n\n"
                f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Total Cycles: {self.cycle_count}"
            )
        except:
            pass
        
        print("✅ Bot telah berhenti dengan aman")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n⚠️ Received shutdown signal")
    sys.exit(0)


async def main():
    """Main entry point - fungsi async utama"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start bot
    bot = TradingBot()
    
    try:
        await bot.start()
    except Exception as e:
        print(f" Fatal error: {e}")
        sys.exit(1)


# ============================================================
# ENTRY POINT - INI YANG MENJALANKAN BOT
# ============================================================
if __name__ == "__main__":
    print("✅ MAIN.PY SEDANG DIJALANKAN OLEH GITHUB ACTIONS...")
    print("🚀 MEMULAI EKSEKUSI BOT...")
    
    # Auto-restart wrapper
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10)
        else:
            print("️ Bot berhenti secara normal.")
            break
