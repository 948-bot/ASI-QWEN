# ============================================================
# XAUUSD/PAXG TRADING BOT - MAIN FILE (ASI LEVEL)
# Terintegrasi dengan Intermarket Analysis (DXY) & Smart Money Concepts
# ============================================================

import asyncio
import sys
import signal
import time
import os
from datetime import datetime

from config import Config
from data_fetcher import DataFetcher
from technical_analyzer import TechnicalAnalyzer
from signal_generator import SignalGenerator
from telegram_notifier import TelegramNotifier
from self_learning import SelfLearning

class TradingBot:
    def __init__(self):
        self.config = Config()
        # Inisialisasi DataFetcher (akan mengambil data Gold & DXY)
        self.fetcher = DataFetcher(symbol=self.config.PAXG_SYMBOL)
        self.analyzer = TechnicalAnalyzer(self.config)
        self.generator = SignalGenerator(self.config)
        self.notifier = TelegramNotifier(self.config.TELEGRAM_BOT_TOKEN, self.config.TELEGRAM_CHAT_ID)
        self.learner = SelfLearning(self.config)
        self.running = True
        self.cycle_count = 0
        
    async def start(self):
        print("=" * 60)
        print(" ASI TRADING BOT DIMULAI (LEVEL: MAXIMUM)")
        print("=" * 60)
        print(f"Symbol: {self.config.PAXG_SYMBOL}")
        print(f"Timeframes: {', '.join(self.config.TIMEFRAMES)}")
        print(f"Update Interval: {self.config.UPDATE_INTERVAL}s")
        print(f"Min Confidence ASI: {self.config.MIN_CONFIDENCE_ASI}%")
        print(f"Intermarket Analysis: AKTIF (DXY)")
        print(f"Smart Money Concepts: AKTIF (Sweep & FVG)")
        print("=" * 60)
        
        await self.notifier.send_notification(
            "🧠 *ASI BOT TRADING DIMULAI*\n\n"
            f"Symbol: {self.config.PAXG_SYMBOL}\n"
            f"Mode: Maximum Analysis (DXY + SMC)\n"
            f"Min Confidence: {self.config.MIN_CONFIDENCE_ASI}%\n"
            f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        while self.running:
            try:
                await self._run_cycle()
                self.cycle_count += 1
                if self.cycle_count % 10 == 0:
                    await self._periodic_tasks()
                await asyncio.sleep(self.config.UPDATE_INTERVAL)
            except KeyboardInterrupt:
                print("\n⚠️ Bot dihentikan oleh user")
                break
            except Exception as e:
                print(f"❌ Error dalam cycle: {str(e)}")
                await self._handle_error(e)
        
        await self.shutdown()
    
    async def _run_cycle(self):
        """Run one analysis cycle dengan ASI Intermarket Analysis"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Cycle #{self.cycle_count + 1}")
        
        # 1. Fetch data (Gold 5m, 15m + DXY 15m)
        data = await self.fetcher.fetch_multiple_timeframes()
        
        source_info = self.fetcher.get_data_source_info()
        if source_info:
            print(f" Data sources: {source_info}")
        
        # Validasi data Gold
        if not data or data.get('5m') is None or data.get('15m') is None:
            print("⚠️ Tidak ada data Gold, skip cycle ini")
            return
        
        # 2. Analisis Tren DXY (Indeks Dolar AS) untuk Korelasi Makro
        dxy_df = data.get('dxy')
        dxy_trend = self.analyzer.get_dxy_trend(dxy_df)
        print(f"🌍 Tren DXY (Indeks Dolar): {dxy_trend.upper()}")
        
        # 3. Analyze Gold data dengan SMC & DXY context
        analysis_results = {}
        for tf in ['5m', '15m']:
            if data.get(tf) is not None:
                # Masukkan dxy_df ke analyzer untuk konteks tambahan jika diperlukan
                analysis_results[tf] = self.analyzer.analyze(data[tf], dxy_df)
        
        # 4. Generate signals dengan logika ASI (Membutuhkan dxy_trend)
        signals = self.generator.generate_signals(analysis_results, dxy_trend)
        
        # 5. Proses Sinyal
        if signals:
            print(f"🚨 {len(signals)} SINYAL AKURASI TINGGI DITEMUKAN!")
            for signal in signals:
                await self._process_signal(signal)
        else:
            print("ℹ️ Tidak ada setup ASI yang valid. Sniper tetap menunggu...")
    
    async def _process_signal(self, signal):
        self.learner.record_signal(signal)
        await self.notifier.send_signal(signal)
        print(f" Signal {signal['type']} dikirim | Confidence: {signal['confidence']}% | DXY: {signal.get('dxy_trend', 'N/A')}")
    
    async def _periodic_tasks(self):
        print("\n🔧 Menjalankan tugas periodik...")
        insights = self.learner.get_learning_insights()
        print(insights)
    
    async def _handle_error(self, error):
        print(f"🔄 Mencoba recovery...")
        await asyncio.sleep(5)
    
    async def shutdown(self):
        print("\n" + "=" * 60)
        print("🛑 Bot sedang shutdown...")
        print("=" * 60)
        await self.notifier.send_notification(" *ASI BOT TRADING BERHENTI*")
        print("✅ Bot telah berhenti dengan aman")

def signal_handler(signum, frame):
    print("\n⚠️ Received shutdown signal")
    sys.exit(0)

async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    bot = TradingBot()
    try:
        await bot.start()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

# ============================================================
# ENTRY POINT (WAJIB ADA DI BARIS PALING BAWAH!)
# ============================================================
if __name__ == "__main__":
    print("✅ MAIN.PY (ASI VERSION) SEDANG DIJALANKAN...")
    print("🚀 MEMULAI EKSEKUSI BOT...")
    
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10)
        else:
            print("ℹ️ Bot berhenti secara normal.")
            break
