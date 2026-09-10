import pandas as pd
import asyncio
import websockets
import aiohttp
import json
import time
from datetime import datetime

class DataFetcher:
    def __init__(self, symbol=None, api_key_twelve=None):
        self.symbol = "frxXAUUSD" 
        self.deriv_ws_url = "wss://ws.derivws.com/websockets/v3?app_id=1089"
        self.yahoo_base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        
        self.cache = {}
        self.last_fetch = {}
        self.last_success_source = {}
        
    async def fetch_klines(self, interval='5m', limit=100):
        cache_key = f"DERIV_{self.symbol}_{interval}"
        
        if cache_key in self.last_fetch and (time.time() - self.last_fetch[cache_key] < 15):
            return self.cache.get(cache_key)
        
        granularity = 300 if interval in ['5m', '5min'] else 900
        df = await self._fetch_from_deriv_ws(granularity, limit)
        
        if df is not None and not df.empty:
            self.last_success_source[cache_key] = 'deriv_ws'
            self.cache[cache_key] = df
            self.last_fetch[cache_key] = time.time()
            return df
        return self.cache.get(cache_key)
    
    async def fetch_dxy_data(self):
        cache_key = "DXY_15m"
        if cache_key in self.last_fetch and (time.time() - self.last_fetch[cache_key] < 45):
            return self.cache.get(cache_key)

        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{self.yahoo_base_url}/DX-Y.NYB"
                params = {'interval': '15m', 'range': '2d'}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = self._parse_yahoo_dxy(data)
                        if df is not None and not df.empty:
                            self.cache[cache_key] = df
                            self.last_fetch[cache_key] = time.time()
                            print(f"✅ Data DXY (Indeks Dolar) berhasil diambil untuk korelasi makro")
                            return df
        except Exception as e:
            print(f"⚠️ Gagal mengambil data DXY: {e}")
        return None

    def _parse_yahoo_dxy(self, data):
        try:
            result = data.get('chart', {}).get('result', [])
            if not result: return None
            res = result[0]
            timestamps = res.get('timestamp', [])
            quote = res.get('indicators', {}).get('quote', [{}])[0]
            
            df = pd.DataFrame({
                'open_time': pd.to_datetime(timestamps, unit='s'),
                'open': quote.get('open', []),
                'high': quote.get('high', []),
                'low': quote.get('low', []),
                'close': quote.get('close', [])
            })
            df = df.dropna()
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df.tail(50)
        except:
            return None
    
    async def _fetch_from_deriv_ws(self, granularity, limit):
        try:
            payload = {
                "ticks_history": self.symbol, "adjust_start_time": 1,
                "count": limit, "end": "latest", "start": 1,
                "style": "candles", "granularity": granularity
            }
            async with websockets.connect(self.deriv_ws_url, ping_interval=None) as ws:
                await ws.send(json.dumps(payload))
                response_str = await asyncio.wait_for(ws.recv(), timeout=15.0)
                response = json.loads(response_str)
                
                if "error" in response: return None
                if "candles" in response:
                    return self._parse_deriv_candles(response["candles"], granularity)
        except Exception as e:
            print(f"⚠️ Deriv fetch error: {e}")
        return None
    
    def _parse_deriv_candles(self, candles_data, granularity):
        if not candles_data: return None
        
        df = pd.DataFrame(candles_data)
        df = df.rename(columns={'epoch': 'open_time', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'})
        df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
        df['close_time'] = df['open_time'] + pd.Timedelta(seconds=granularity)
        
        if 'volume' not in df.columns: 
            df['volume'] = 0
            
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df = df.dropna().sort_values('open_time').reset_index(drop=True)
        return df
    
    async def fetch_multiple_timeframes(self):
        tasks = [
            self.fetch_klines(interval='5m', limit=100),
            self.fetch_klines(interval='15m', limit=100),
            self.fetch_dxy_data()
        ]
        results = await asyncio.gather(*tasks)
        return {'5m': results[0], '15m': results[1], 'dxy': results[2]}
    
    def get_data_source_info(self):
        return self.last_success_source
