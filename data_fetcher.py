import requests
import pandas as pd
import time
import asyncio
import aiohttp
from datetime import datetime

class DataFetcher:
    def __init__(self, symbol):
        self.symbol = symbol
        self.base_url = "https://api.binance.com/api/v3"
        self.cache = {}
        self.last_fetch = {}
        
    async def fetch_klines(self, interval='5m', limit=100):
        """Fetch candlestick data from Binance"""
        cache_key = f"{self.symbol}_{interval}"
        
        # Check cache (avoid rate limiting)
        if cache_key in self.last_fetch:
            if time.time() - self.last_fetch[cache_key] < 5:
                return self.cache.get(cache_key)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/klines"
                params = {
                    'symbol': self.symbol,
                    'interval': interval,
                    'limit': limit
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = self._parse_klines(data)
                        self.cache[cache_key] = df
                        self.last_fetch[cache_key] = time.time()
                        return df
                    else:
                        print(f"Error fetching data: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Exception in fetch_klines: {e}")
            return self.cache.get(cache_key)
    
    def _parse_klines(self, data):
        """Parse Binance kline data to DataFrame"""
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        # Convert timestamps
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        return df
    
    async def fetch_current_price(self):
        """Fetch current price"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/ticker/price"
                params = {'symbol': self.symbol}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
                    return None
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None
    
    async def fetch_multiple_timeframes(self):
        """Fetch data for all configured timeframes"""
        tasks = []
        for tf in ['5m', '15m']:
            tasks.append(self.fetch_klines(interval=tf, limit=100))
        
        results = await asyncio.gather(*tasks)
        return {
            '5m': results[0],
            '15m': results[1]
        }
