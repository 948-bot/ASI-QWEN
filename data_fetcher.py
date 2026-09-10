import pandas as pd
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta

class DataFetcher:
    def __init__(self, symbol=None, api_key_twelve=None):
        # Kita pakai PAXG-USD dari Coinbase
        self.symbol = "PAXG-USD"
        self.coinbase_candles_url = "https://api.exchange.coinbase.com/products/PAXG-USD/candles"
        self.coinbase_spot_url = "https://api.coinbase.com/v2/prices/PAXG-USD/spot"
        
        self.cache = {}
        self.last_fetch = {}
        self.last_success_source = {}
        
    async def fetch_klines(self, interval='5m', limit=100):
        """
        Fetch data candlestick dari Coinbase Public API
        100% GRATIS, TANPA API KEY, TANPA AUTH
        """
        cache_key = f"PAXGUSD_{interval}"
        
        # Check cache (hindari request terlalu sering, max 1x per 30 detik)
        if cache_key in self.last_fetch:
            time_since = time.time() - self.last_fetch[cache_key]
            if time_since < 30:
                return self.cache.get(cache_key)
        
        # Map interval ke granularity Coinbase (dalam detik)
        # 60=1m, 300=5m, 900=15m, 3600=1h, 21600=6h, 86400=1d
        granularity = 300 if interval in ['5m', '5min'] else 900
        
        df = await self._fetch_from_coinbase_candles(granularity, limit)
        
        if df is not None and not df.empty:
            self.last_success_source[cache_key] = 'coinbase_candles'
            self.cache[cache_key] = df
            self.last_fetch[cache_key] = time.time()
            print(f"✅ Data Candlestick berhasil diambil dari Coinbase (PAXG-USD) - GRATIS")
            return df
        
        print(f"⚠️ Gagal ambil data candle, menggunakan cache terakhir")
        return self.cache.get(cache_key)
    
    async def _fetch_from_coinbase_candles(self, granularity, limit):
        """Fetch historical candles dari Coinbase Exchange API (Public)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                params = {
                    'granularity': granularity,
                    'limit': limit
                }
                
                async with session.get(self.coinbase_candles_url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = self._parse_coinbase_candles(data, granularity)
                        return df
                    else:
                        print(f"⚠️ Coinbase Candles HTTP {response.status}")
                        
        except asyncio.TimeoutError:
            print(f"⚠️ Coinbase Candles timeout")
        except Exception as e:
            print(f"⚠️ Coinbase Candles error: {e}")
        
        return None
    
    def _parse_coinbase_candles(self, data, granularity):
        """
        Parse data dari Coinbase.
        Format Coinbase: [time, low, high, open, close, volume]
        """
        if not data:
            return None
        
        # Coinbase mengembalikan data dari TERBARU ke TERLAMA, kita harus reverse
        data.reverse()
        
        df = pd.DataFrame(data, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
        
        # Convert time (Unix timestamp) to datetime
        df['open_time'] = pd.to_datetime(df['time'], unit='s')
        df['close_time'] = df['open_time'] + pd.Timedelta(seconds=granularity)
        
        # Convert columns to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop any NaN rows
        df = df.dropna()
        
        # Urutkan berdasarkan waktu
        df = df.sort_values('open_time').reset_index(drop=True)
        
        return df
    
    async def fetch_current_price(self):
        """Ambil harga current dari Coinbase Spot API (URL yang Anda berikan)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'application/json',
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(self.coinbase_spot_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data['data']['amount'])
                        print(f"💰 Current PAXG-USD Price: ${price:.2f} (Source: Coinbase Spot)")
                        return price
        except Exception as e:
            print(f"⚠️ Error getting current price from Coinbase: {e}")
        
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
