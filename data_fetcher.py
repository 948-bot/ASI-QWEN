import requests
import pandas as pd
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import os

class DataFetcher:
    def __init__(self, symbol):
        self.symbol = symbol
        self.base_url = "https://api.binance.com/api/v3"
        self.futures_url = "https://fapi.binance.com/fapi/v1"
        self.yahoo_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.cache = {}
        self.last_fetch = {}
        self.last_success_source = {}
        self.request_count = 0
        self.max_requests_per_minute = 50
        
        # User-Agent rotation untuk hindari blokir
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'TradingBot/1.0 (Automated Trading System)',
        ]
        
        # Map symbol untuk berbagai source
        self.symbol_mapping = {
            'XAUUSDT': {'binance_spot': 'PAXGUSDT', 'binance_futures': 'XAUUSDT', 'yahoo': 'GC=F'},
            'PAXGUSDT': {'binance_spot': 'PAXGUSDT', 'binance_futures': None, 'yahoo': 'PAXG-USD'},
            'XAUUSD': {'binance_spot': 'PAXGUSDT', 'binance_futures': 'XAUUSDT', 'yahoo': 'GC=F'},
        }
        
    def _get_mapped_symbol(self, source):
        """Dapatkan symbol yang sesuai untuk setiap source"""
        mapping = self.symbol_mapping.get(self.symbol, {})
        return mapping.get(source, self.symbol)
    
    def _get_random_user_agent(self):
        """Random User-Agent untuk hindari blokir"""
        return random.choice(self.user_agents)
    
    async def fetch_klines(self, interval='5m', limit=100):
        """Fetch candlestick data dengan multi-source fallback"""
        cache_key = f"{self.symbol}_{interval}"
        
        # Check cache (avoid rate limiting)
        if cache_key in self.last_fetch:
            if time.time() - self.last_fetch[cache_key] < 10:
                return self.cache.get(cache_key)
        
        # Rate limiting
        self.request_count += 1
        if self.request_count > self.max_requests_per_minute:
            print(f"⚠️ Rate limit reached, waiting...")
            await asyncio.sleep(60)
            self.request_count = 0
        
        # Coba Binance Spot dulu
        df = await self._fetch_from_binance_spot(interval, limit)
        if df is not None and not df.empty:
            self.last_success_source[cache_key] = 'binance_spot'
            self.cache[cache_key] = df
            self.last_fetch[cache_key] = time.time()
            return df
        
        # Fallback ke Binance Futures
        df = await self._fetch_from_binance_futures(interval, limit)
        if df is not None and not df.empty:
            self.last_success_source[cache_key] = 'binance_futures'
            self.cache[cache_key] = df
            self.last_fetch[cache_key] = time.time()
            return df
        
        # Fallback ke Yahoo Finance
        df = await self._fetch_from_yahoo(interval, limit)
        if df is not None and not df.empty:
            self.last_success_source[cache_key] = 'yahoo'
            self.cache[cache_key] = df
            self.last_fetch[cache_key] = time.time()
            return df
        
        print(f"❌ Semua source gagal, menggunakan cache terakhir")
        return self.cache.get(cache_key)
    
    async def _fetch_from_binance_spot(self, interval, limit):
        """Fetch dari Binance Spot API"""
        mapped_symbol = self._get_mapped_symbol('binance_spot')
        if not mapped_symbol:
            return None
        
        try:
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'application/json',
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{self.base_url}/klines"
                params = {
                    'symbol': mapped_symbol,
                    'interval': interval,
                    'limit': limit
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = self._parse_klines(data, mapped_symbol)
                        print(f"✅ Data fetched from Binance Spot ({mapped_symbol})")
                        return df
                    else:
                        print(f"⚠️ Binance Spot failed: {response.status} for {mapped_symbol}")
                        return None
                        
        except asyncio.TimeoutError:
            print(f"⚠️ Binance Spot timeout")
            return None
        except Exception as e:
            print(f"⚠️ Binance Spot error: {e}")
            return None
    
    async def _fetch_from_binance_futures(self, interval, limit):
        """Fetch dari Binance Futures API"""
        mapped_symbol = self._get_mapped_symbol('binance_futures')
        if not mapped_symbol:
            return None
        
        try:
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'application/json',
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{self.futures_url}/klines"
                params = {
                    'symbol': mapped_symbol,
                    'interval': interval,
                    'limit': limit
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = self._parse_klines(data, mapped_symbol)
                        print(f"✅ Data fetched from Binance Futures ({mapped_symbol})")
                        return df
                    else:
                        print(f"⚠️ Binance Futures failed: {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            print(f"⚠️ Binance Futures timeout")
            return None
        except Exception as e:
            print(f"⚠️ Binance Futures error: {e}")
            return None
    
    async def _fetch_from_yahoo(self, interval, limit):
        """Fetch dari Yahoo Finance API"""
        mapped_symbol = self._get_mapped_symbol('yahoo')
        if not mapped_symbol:
            return None
        
        try:
            # Map interval ke Yahoo format
            yahoo_interval = self._map_interval_to_yahoo(interval)
            yahoo_range = self._calculate_yahoo_range(interval, limit)
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{self.yahoo_url}/{mapped_symbol}"
                params = {
                    'interval': yahoo_interval,
                    'range': yahoo_range,
                    'includePrePost': 'false'
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = self._parse_yahoo_data(data, mapped_symbol)
                        if df is not None and not df.empty:
                            print(f"✅ Data fetched from Yahoo Finance ({mapped_symbol})")
                            return df
                    else:
                        print(f"️ Yahoo Finance failed: {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            print(f"⚠️ Yahoo Finance timeout")
            return None
        except Exception as e:
            print(f"⚠️ Yahoo Finance error: {e}")
            return None
    
    def _map_interval_to_yahoo(self, interval):
        """Map interval ke format Yahoo Finance"""
        mapping = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '1h',
            '1d': '1d',
        }
        return mapping.get(interval, '5m')
    
    def _calculate_yahoo_range(self, interval, limit):
        """Hitung range waktu untuk Yahoo Finance"""
        # Yahoo Finance menggunakan range (1d, 5d, 1mo, dll)
        if interval in ['1m', '5m']:
            return '2d'
        elif interval in ['15m', '30m']:
            return '5d'
        elif interval in ['1h', '4h']:
            return '1mo'
        else:
            return '3mo'
    
    def _parse_yahoo_data(self, data, symbol):
        """Parse data dari Yahoo Finance"""
        try:
            chart = data.get('chart', {})
            result = chart.get('result', [])
            
            if not result:
                return None
            
            result = result[0]
            timestamps = result.get('timestamp', [])
            indicators = result.get('indicators', {})
            quote = indicators.get('quote', [{}])[0]
            
            if not timestamps:
                return None
            
            df = pd.DataFrame({
                'open_time': pd.to_datetime(timestamps, unit='s'),
                'open': quote.get('open', []),
                'high': quote.get('high', []),
                'low': quote.get('low', []),
                'close': quote.get('close', []),
                'volume': quote.get('volume', [])
            })
            
            # Drop NaN values
            df = df.dropna()
            
            if df.empty:
                return None
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            return df.tail(100)  # Ambil 100 candle terakhir
            
        except Exception as e:
            print(f"Error parsing Yahoo data: {e}")
            return None
    
    def _parse_klines(self, data, symbol):
        """Parse Binance kline data to DataFrame"""
        if not data:
            return None
        
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
        """Fetch current price dengan fallback"""
        # Coba Binance Spot
        price = await self._get_price_from_binance_spot()
        if price:
            return price
        
        # Fallback ke Binance Futures
        price = await self._get_price_from_binance_futures()
        if price:
            return price
        
        # Fallback ke Yahoo
        price = await self._get_price_from_yahoo()
        if price:
            return price
        
        return None
    
    async def _get_price_from_binance_spot(self):
        """Get price dari Binance Spot"""
        mapped_symbol = self._get_mapped_symbol('binance_spot')
        if not mapped_symbol:
            return None
        
        try:
            headers = {'User-Agent': self._get_random_user_agent()}
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{self.base_url}/ticker/price"
                params = {'symbol': mapped_symbol}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
        except:
            pass
        return None
    
    async def _get_price_from_binance_futures(self):
        """Get price dari Binance Futures"""
        mapped_symbol = self._get_mapped_symbol('binance_futures')
        if not mapped_symbol:
            return None
        
        try:
            headers = {'User-Agent': self._get_random_user_agent()}
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{self.futures_url}/ticker/price"
                params = {'symbol': mapped_symbol}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
        except:
            pass
        return None
    
    async def _get_price_from_yahoo(self):
        """Get price dari Yahoo Finance"""
        mapped_symbol = self._get_mapped_symbol('yahoo')
        if not mapped_symbol:
            return None
        
        try:
            headers = {'User-Agent': self._get_random_user_agent()}
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{self.yahoo_url}/{mapped_symbol}"
                params = {'interval': '1m', 'range': '1d'}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        chart = data.get('chart', {})
                        result = chart.get('result', [])
                        if result:
                            meta = result[0].get('meta', {})
                            return float(meta.get('regularMarketPrice', 0))
        except:
            pass
        return None
    
    async def fetch_multiple_timeframes(self):
        """Fetch data untuk semua timeframe"""
        tasks = []
        for tf in ['5m', '15m']:
            tasks.append(self.fetch_klines(interval=tf, limit=100))
        
        results = await asyncio.gather(*tasks)
        return {
            '5m': results[0],
            '15m': results[1]
        }
    
    def get_data_source_info(self):
        """Dapatkan info source data yang digunakan"""
        info = {}
        for key, source in self.last_success_source.items():
            info[key] = source
        return info
