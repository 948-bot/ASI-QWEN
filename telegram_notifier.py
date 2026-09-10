import requests
from datetime import datetime
import asyncio
import aiohttp

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.message_queue = []
        
    async def send_signal(self, signal):
        message = self._format_signal_message(signal)
        await self._send_message(message)
    
    def _format_signal_message(self, signal):
        emoji = "" if signal['type'] == 'BUY' else "🔴"
        
        message = f"""
{emoji} *SIGNAL TRADING XAUUSD/PAXG* {emoji}

📊 *Timeframe:* {signal['timeframe']}
🎯 *Tipe:* {signal['type']}
💪 *Confidence:* {signal['confidence']}%

💰 *Price:* ${signal['price']:.2f}
 *Stop Loss:* ${signal['stop_loss']:.2f}
✅ *Take Profit:* ${signal['take_profit']:.2f}
📈 *Risk/Reward:* 1:{signal['risk_reward']:.2f}

📉 *Indicators:*
• RSI: {signal['indicators']['RSI']}
• MACD: {signal['indicators']['MACD']}
• EMA Short: {signal['indicators']['EMA_Short']}
• EMA Long: {signal['indicators']['EMA_Long']}

⏰ *Waktu:* {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

️ *Disclaimer:* Ini adalah sinyal analisis otomatis. Selalu lakukan analisis mandiri.
        """
        
        return message.strip()
    
    async def _send_message(self, message):
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
        message = f"️ *ERROR*\n\n{error_msg}"
        await self._send_message(message)
