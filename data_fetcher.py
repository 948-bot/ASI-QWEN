import pandas as pd
import asyncio
import websockets
import json
import time
from datetime import datetime

class DataFetcher:
    def __init__(self, symbol=None, api_key_twelve=None):
        # frxXAUUSD adalah simbol Gold Forex di Deriv (Sangat dekat dengan MT5)
        self.symbol = "frxXAUUSD" 
        self.deriv_ws_url = "wss://ws.derivws.com/websockets/v3?app_id=1089" # 1089 adalah App ID Publik Gratis
        
        self.cache = {}
        self.last_fetch = {}
        self.last_success_source = {}
        
    async def fetch_klines(self, interval='5m', limit=100):
        """
        Fetch data candlestick dari Deriv Public WebSocket API
        100% GRATIS, TANPA API KEY, MENGGUNAKAN App ID Publik (1089)
        """
        cache_key = f"DERIV_{self.symbol}_{interval}"
        
        # Check cache (hindari request terlalu sering, max 1x per 30 detik)
        if cache_key in self.last_fetch:
            time_since = time.time() - self.last_fetch[cache_key]
            if time_since < 30:
                return self.cache.get(cache_key)
        
        # Map interval ke detik (Granularity Deriv)
        # 60=1m, 300=5m, 900=15m, 3600=1h, 86400=1d
        granularity = 300 if interval in ['5m', '5min'] else 900
        
        df = await self._fetch_from_deriv_ws(granularity, limit)
        
        if df is not None and not df.empty:
            self.last_success_source[cache_key] = 'deriv_ws'
            self.cache[cache_key] = df
            self.last_fetch[cache_key] = time.time()
            print(f"✅ Data Candlestick berhasil diambil dari Deriv ({self.symbol}) - GRATIS & AKURAT")
            return df
        
        print(f"⚠️ Gagal ambil data dari Deriv, menggunakan cache terakhir")
        return self.cache.get(cache_key)
    
    async def _fetch_from_deriv_ws(self, granularity, limit):
        """Fetch historical candles dari Deriv WebSocket"""
        try:
            # Payload request sesuai dokumentasi API Deriv
            payload = {
                "ticks_history": self.symbol,
                "adjust_start_time": 1,
                "count": limit,
                "end": "latest",
                "start": 1,
                "style": "candles",
                "granularity": granularity
            }
            
            # Connect ke WebSocket Deriv (Timeout 15 detik)
            async with websockets.connect(self.deriv_ws_url, ping_interval=None) as ws:
                await ws.send(json.dumps(payload))
                
                # Tunggu response
                response_str = await asyncio.wait_for(ws.recv(), timeout=15.0)
                response = json.loads(response_str)
                
                # Cek jika ada error dari Deriv
                if "error" in response:
                    print(f"⚠️ Deriv API Error: {response['error']['message']}")
                    return None
                
                # Parse data candles
                if "candles" in response:
                    df = self._parse_deriv_candles(response["candles"], granularity)
                    return df
                else:
                    print("⚠️ Deriv response tidak mengandung data candles")
                    return None
                    
        except asyncio.TimeoutError:
            print(f"⚠️ Deriv WebSocket timeout")
        except websockets.exceptions.WebSocketException as e:
            print(f"⚠️ Deriv WebSocket connection error: {e}")
        except Exception as e:
            print(f"⚠️ Deriv fetch error: {e}")
        
        return None
    
    def _parse_deriv_candles(self, candles_data, granularity):
        """Parse data dari Deriv ke DataFrame Pandas"""
        if not candles_data:
            return None
        
        # Deriv mengembalikan data dari TERLAMA ke TERBARU (sudah urut, bagus!)
        df = pd.DataFrame(candles_data)
        
        # Rename kolom agar sesuai dengan format bot kita
        # Deriv: epoch, open, high, low, close
        df = df.rename(columns={'epoch': 'open_time'})
        
        # Convert epoch (unix timestamp) ke datetime
        df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
        df['close_time'] = df['open_time'] + pd.Timedelta(seconds=granularity)
        
        # Pastikan kolom volume ada (Deriv kadang tidak kirim volume untuk forex, kita isi 0)
        if 'volume' not in df.columns:
            df['volume'] = 0
            
        # Convert ke numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop NaN
        df = df.dropna()
        
        return df
    
    async def fetch_current_price(self):
        """Ambil harga current (tick terakhir) dari Deriv"""
        try:
            payload = {
                "ticks": self.symbol,
                "subscribe": 0
            }
            
            async with websockets.connect(self.deriv_ws_url, ping_interval=None) as ws:
                await ws.send(json.dumps(payload))
                response_str = await asyncio.wait_for(ws.recv(), timeout=10.0)
                response = json.loads(response_str)
                
                if "tick" in response and "quote" in response["tick"]:
                    price = float(response["tick"]["quote"])
                    print(f"💰 Current {self.symbol} Price: ${price:.2f} (Source: Deriv)")
                    return price
        except Exception as e:
            print(f"⚠️ Error getting current price from Deriv: {e}")
        
        return None
    
    async def fetch_multiple_timeframes(self):
        """Fetch data untuk 5m dan 15m secara bersamaan"""
        tasks = [
            self.fetch_klines(interval='5m', limit=100),
            self.fetch_klines(interval='15m', limit=100)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            '5m': results[0],
            '15m': results[1]
        }
    
    def get_data_source_info(self):
        """Info source data yang dipakai"""
        return self.last_success_source
