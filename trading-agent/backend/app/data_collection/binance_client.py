"""
Binance Client Module
Real-time crypto data from Binance (Free WebSocket + REST API)
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import hmac
import hashlib
import urllib.parse

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class BinanceKline:
    """Binance kline/candlestick data"""
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int


@dataclass
class BinanceTicker:
    """Binance 24h ticker data"""
    symbol: str
    price_change: float
    price_change_percent: float
    weighted_avg_price: float
    last_price: float
    last_qty: float
    open_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    open_time: int
    close_time: int
    first_id: int
    last_id: int
    count: int


@dataclass
class BinanceOrderBook:
    """Binance order book"""
    symbol: str
    last_update_id: int
    bids: List[List[float]]  # [[price, qty], ...]
    asks: List[List[float]]


class BinanceClient:
    """
    Binance API Client
    Uses free REST API and WebSocket streams
    """
    
    # Binance API endpoints
    BASE_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"
    WS_STREAM_URL = "wss://stream.binance.com:9443/ws"
    WS_TESTNET_URL = "wss://testnet.binance.vision/ws"
    
    # Timeframe mappings
    TIMEFRAMES = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M"
    }
    
    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        testnet: bool = None
    ):
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        self.testnet = testnet if testnet is not None else settings.BINANCE_TESTNET
        
        self.base_url = self.TESTNET_URL if self.testnet else self.BASE_URL
        self.ws_url = self.WS_TESTNET_URL if self.testnet else self.WS_STREAM_URL
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_session: Optional[aiohttp.ClientSession] = None
        self.ws_connections: Dict[str, Any] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        
        self.rate_limit_remaining = 1200
        self.rate_limit_reset = 0
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self):
        """Initialize HTTP session"""
        headers = {}
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        self.ws_session = aiohttp.ClientSession()
    
    async def close(self):
        """Close all connections"""
        # Close WebSocket connections
        for ws in self.ws_connections.values():
            if not ws.closed:
                await ws.close()
        
        if self.session:
            await self.session.close()
        if self.ws_session:
            await self.ws_session.close()
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC signature for authenticated requests"""
        if not self.api_secret:
            raise ValueError("API secret required for signed requests")
        
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        signed: bool = False
    ) -> Any:
        """Make HTTP request to Binance API"""
        if not self.session:
            raise RuntimeError("Client not started")
        
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        # Add timestamp for signed requests
        if signed:
            params['timestamp'] = int(datetime.now().timestamp() * 1000)
        
        # Build query string
        query_string = urllib.parse.urlencode(params)
        
        # Add signature for signed requests
        if signed:
            params['signature'] = self._generate_signature(query_string)
            query_string = urllib.parse.urlencode(params)
        
        try:
            async with self.session.request(
                method,
                url,
                params=params if not signed else None,
                data=query_string if signed else None
            ) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(
                    response.headers.get('X-MBX-USED-WEIGHT-1M', 0)
                )
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    logger.error(f"Binance API error: {error_data}")
                    raise Exception(f"Binance API error: {error_data}")
                    
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
    
    # ==================== Market Data Endpoints ====================
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        return await self._make_request("GET", "/api/v3/exchangeInfo")
    
    async def get_symbol_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol"""
        return await self._make_request(
            "GET",
            "/api/v3/ticker/price",
            {"symbol": symbol.upper()}
        )
    
    async def get_all_prices(self) -> List[Dict[str, Any]]:
        """Get all symbol prices"""
        return await self._make_request("GET", "/api/v3/ticker/price")
    
    async def get_24h_ticker(self, symbol: str) -> BinanceTicker:
        """Get 24h ticker data"""
        data = await self._make_request(
            "GET",
            "/api/v3/ticker/24hr",
            {"symbol": symbol.upper()}
        )
        
        return BinanceTicker(
            symbol=data["symbol"],
            price_change=float(data["priceChange"]),
            price_change_percent=float(data["priceChangePercent"]),
            weighted_avg_price=float(data["weightedAvgPrice"]),
            last_price=float(data["lastPrice"]),
            last_qty=float(data["lastQty"]),
            open_price=float(data["openPrice"]),
            high_price=float(data["highPrice"]),
            low_price=float(data["lowPrice"]),
            volume=float(data["volume"]),
            quote_volume=float(data["quoteVolume"]),
            open_time=data["openTime"],
            close_time=data["closeTime"],
            first_id=data["firstId"],
            last_id=data["lastId"],
            count=data["count"]
        )
    
    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 500,
        start_time: int = None,
        end_time: int = None
    ) -> List[BinanceKline]:
        """Get kline/candlestick data"""
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        data = await self._make_request("GET", "/api/v3/klines", params)
        
        klines = []
        for k in data:
            klines.append(BinanceKline(
                open_time=k[0],
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                volume=float(k[5]),
                close_time=k[6],
                quote_volume=float(k[7]),
                trades=k[8]
            ))
        
        return klines
    
    async def get_order_book(
        self,
        symbol: str,
        limit: int = 100
    ) -> BinanceOrderBook:
        """Get order book"""
        data = await self._make_request(
            "GET",
            "/api/v3/depth",
            {"symbol": symbol.upper(), "limit": limit}
        )
        
        return BinanceOrderBook(
            symbol=symbol.upper(),
            last_update_id=data["lastUpdateId"],
            bids=[[float(b[0]), float(b[1])] for b in data["bids"]],
            asks=[[float(a[0]), float(a[1])] for a in data["asks"]]
        )
    
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Get recent trades"""
        return await self._make_request(
            "GET",
            "/api/v3/trades",
            {"symbol": symbol.upper(), "limit": limit}
        )
    
    async def get_ticker_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive ticker statistics"""
        ticker = await self.get_24h_ticker(symbol)
        
        return {
            "symbol": ticker.symbol,
            "price": ticker.last_price,
            "change_24h": ticker.price_change,
            "change_percent_24h": ticker.price_change_percent,
            "high_24h": ticker.high_price,
            "low_24h": ticker.low_price,
            "volume_24h": ticker.volume,
            "quote_volume_24h": ticker.quote_volume,
            "trades_24h": ticker.count,
            "open": ticker.open_price,
            "weighted_avg_price": ticker.weighted_avg_price,
            "timestamp": datetime.now().isoformat()
        }
    
    # ==================== WebSocket Streams ====================
    
    async def start_kline_stream(
        self,
        symbol: str,
        interval: str,
        callback: Callable
    ):
        """Start WebSocket kline stream"""
        stream_name = f"{symbol.lower()}@kline_{interval}"
        await self._start_stream(stream_name, callback)
    
    async def start_ticker_stream(
        self,
        symbol: str,
        callback: Callable
    ):
        """Start WebSocket ticker stream"""
        stream_name = f"{symbol.lower()}@ticker"
        await self._start_stream(stream_name, callback)
    
    async def start_trade_stream(
        self,
        symbol: str,
        callback: Callable
    ):
        """Start WebSocket trade stream"""
        stream_name = f"{symbol.lower()}@trade"
        await self._start_stream(stream_name, callback)
    
    async def start_order_book_stream(
        self,
        symbol: str,
        levels: int = 20,
        callback: Callable
    ):
        """Start WebSocket order book stream"""
        stream_name = f"{symbol.lower()}@depth{levels}"
        await self._start_stream(stream_name, callback)
    
    async def _start_stream(self, stream_name: str, callback: Callable):
        """Start a WebSocket stream"""
        ws_url = f"{self.ws_url}/{stream_name}"
        
        try:
            async with self.ws_session.ws_connect(ws_url) as ws:
                self.ws_connections[stream_name] = ws
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        await callback(data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
                        
        except Exception as e:
            logger.error(f"Stream error: {e}")
    
    async def stop_stream(self, stream_name: str):
        """Stop a WebSocket stream"""
        ws = self.ws_connections.get(stream_name)
        if ws and not ws.closed:
            await ws.close()
            del self.ws_connections[stream_name]
    
    # ==================== Utility Methods ====================
    
    async def get_all_usdt_pairs(self) -> List[str]:
        """Get all USDT trading pairs"""
        info = await self.get_exchange_info()
        symbols = []
        
        for s in info.get("symbols", []):
            if s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
                symbols.append(s["symbol"])
        
        return sorted(symbols)
    
    async def get_top_volume_pairs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top volume trading pairs"""
        tickers = await self._make_request("GET", "/api/v3/ticker/24hr")
        
        # Sort by volume
        sorted_tickers = sorted(
            tickers,
            key=lambda x: float(x.get("quoteVolume", 0)),
            reverse=True
        )
        
        return [
            {
                "symbol": t["symbol"],
                "volume": float(t["volume"]),
                "quote_volume": float(t["quoteVolume"]),
                "price": float(t["lastPrice"]),
                "change_percent": float(t["priceChangePercent"])
            }
            for t in sorted_tickers[:limit]
        ]
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return {
            "used_weight": self.rate_limit_remaining,
            "limit": 1200,
            "remaining": 1200 - self.rate_limit_remaining
        }


# Singleton instance
_binance_client: Optional[BinanceClient] = None


def get_binance_client(
    api_key: str = None,
    api_secret: str = None,
    testnet: bool = None
) -> BinanceClient:
    """Get or create Binance client singleton"""
    global _binance_client
    if _binance_client is None:
        _binance_client = BinanceClient(api_key, api_secret, testnet)
    return _binance_client
