import requests
from datetime import datetime
import asyncio
import aiohttp

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        
    async def send_signal(self, signal):
        """Kirim sinyal ASI ke Telegram"""
        message = self._format_signal_message(signal)
        await self._send_message(message)
    
    def _format_signal_message(self, signal):
        """Format pesan Telegram level ASI"""
        emoji = "🟢" if signal['type'] == 'BUY' else "🔴"
        
        # Ambil data tren
        dxy_trend = signal.get('dxy_trend', 'N/A').upper()
        mtf_trend = signal.get('mtf_trend', 'N/A').upper()
        
        message = f"""
{emoji} *ASI SIGNAL: {signal['type']} XAUUSD* {emoji}

🧠 *ASI CONFIDENCE:* {signal['confidence']}%
📊 *Timeframe:* {signal['timeframe']}

💰 *Entry:* ${signal['price']:.2f}
 *Stop Loss:* ${signal['stop_loss']:.2f}
✅ *Take Profit:* ${signal['take_profit']:.2f}
⚖️ *Risk/Reward:* 1:{signal['risk_reward']:.2f}
📏 *ATR (Volatility):* {signal['atr']:.2f}

🌍 *Makro (DXY):* {dxy_trend}
🔄 *MTF Confluence:* {mtf_trend}

⏰ *Waktu:* {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

⚠️ *Disclaimer:* Sinyal AI tingkat lanjut. Gunakan manajemen risiko ketat.
        """
        return message.strip()
    
    async def _send_message(self, message):
        """Kirim pesan ke Telegram"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                data = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        print(f"✅ Signal sent to Telegram")
                    else:
                        print(f"❌ Failed to send signal: {response.status}")
        except Exception as e:
            print(f"❌ Exception sending message: {e}")
    
    async def send_notification(self, message):
        await self._send_message(message)
    
    async def send_error(self, error_msg):
        message = f"⚠️ *ERROR*\n\n{error_msg}"
        await self._send_message(message)
