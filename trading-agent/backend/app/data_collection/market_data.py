"""
Market Data Collector
Uses free financial data APIs
"""
import asyncio
import aiohttp
import yfinance as yf
import ccxt.async_support as ccxt
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    """Structured price data"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str


@dataclass
class OrderBook:
    """Order book data"""
    symbol: str
    bids: List[Tuple[float, float]]  # (price, size)
    asks: List[Tuple[float, float]]
    timestamp: datetime


class MarketDataCollector:
    """
    Collects market data from free sources:
    - Yahoo Finance (free, no API key)
    - CCXT (100+ exchanges, free)
    - Alpha Vantage (25 calls/day free)
    - CryptoCompare (100k calls/month free)
    - Finnhub (60 calls/min free)
    """
    
    # Symbol mappings
    YF_SYMBOLS = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "JPY=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "CAD=X",
        "BTCUSD": "BTC-USD",
        "ETHUSD": "ETH-USD",
        "SOLUSD": "SOL-USD",
        "BNBUSD": "BNB-USD",
        "XAUUSD": "GC=F",
        "XAGUSD": "SI=F",
        "USOIL": "CL=F",
        "SPX": "^GSPC",
        "NASDAQ": "^IXIC",
        "DOW": "^DJI",
        "VIX": "^VIX"
    }
    
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1wk": "1wk",
        "1mo": "1mo"
    }
    
    def __init__(
        self,
        alpha_vantage_key: Optional[str] = None,
        cryptocompare_key: Optional[str] = None,
        finnhub_key: Optional[str] = None
    ):
        self.alpha_vantage_key = alpha_vantage_key
        self.cryptocompare_key = cryptocompare_key
        self.finnhub_key = finnhub_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.exchange: Optional[ccxt.Exchange] = None
        self.cache: Dict[str, Any] = {}
        self.cache_duration = 60  # 1 minute for price data
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        # Initialize CCXT with a reliable exchange
        try:
            self.exchange = ccxt.kraken({
                'enableRateLimit': True,
            })
            await self.exchange.load_markets()
        except Exception as e:
            logger.warning(f"Could not initialize CCXT: {e}")
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.exchange:
            await self.exchange.close()
    
    async def get_yahoo_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: str = "5d"
    ) -> pd.DataFrame:
        """
        Get data from Yahoo Finance (free, no API key)
        """
        yf_symbol = self.YF_SYMBOLS.get(symbol, symbol)
        
        cache_key = f"yf_{symbol}_{timeframe}_{period}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < self.cache_duration:
                return cached["data"]
        
        try:
            ticker = yf.Ticker(yf_symbol)
            
            # Map timeframe to yfinance interval
            interval_map = {
                "1m": "1m", "5m": "5m", "15m": "15m",
                "30m": "30m", "1h": "1h", "4h": "1h",
                "1d": "1d", "1wk": "1wk", "1mo": "1mo"
            }
            interval = interval_map.get(timeframe, "1h")
            
            df = ticker.history(period=period, interval=interval)
            
            if not df.empty:
                self.cache[cache_key] = {
                    "data": df,
                    "timestamp": datetime.now()
                }
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_ccxt_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get data from CCXT-supported exchanges (free)
        """
        if not self.exchange:
            return pd.DataFrame()
        
        cache_key = f"ccxt_{symbol}_{timeframe}_{limit}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < self.cache_duration:
                return cached["data"]
        
        try:
            # Map symbol to CCXT format
            ccxt_symbol = self._to_ccxt_symbol(symbol)
            
            # Fetch OHLCV
            ohlcv = await self.exchange.fetch_ohlcv(
                ccxt_symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            if ohlcv:
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                self.cache[cache_key] = {
                    "data": df,
                    "timestamp": datetime.now()
                }
                
                return df
            
        except Exception as e:
            logger.error(f"Error fetching CCXT data for {symbol}: {e}")
        
        return pd.DataFrame()
    
    async def get_cryptocompare_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time price from CryptoCompare (free tier)
        """
        if not self.session:
            return None
        
        cache_key = f"cc_price_{symbol}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < 30:  # 30 second cache
                return cached["data"]
        
        try:
            # Parse symbol (e.g., BTCUSD -> BTC, USD)
            if len(symbol) >= 6:
                fsym = symbol[:3]
                tsym = symbol[3:]
            else:
                fsym = symbol
                tsym = "USD"
            
            url = f"https://min-api.cryptocompare.com/data/pricemultifull"
            params = {
                "fsyms": fsym,
                "tsyms": tsym
            }
            
            if self.cryptocompare_key:
                params["api_key"] = self.cryptocompare_key
            
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get("Response") == "Success":
                        price_data = data["RAW"][fsym][tsym]
                        
                        result = {
                            "symbol": symbol,
                            "price": price_data["PRICE"],
                            "change_24h": price_data.get("CHANGE24HOUR", 0),
                            "change_pct_24h": price_data.get("CHANGEPCT24HOUR", 0),
                            "high_24h": price_data.get("HIGH24HOUR", 0),
                            "low_24h": price_data.get("LOW24HOUR", 0),
                            "volume_24h": price_data.get("VOLUME24HOUR", 0),
                            "market_cap": price_data.get("MKTCAP", 0),
                            "last_update": datetime.fromtimestamp(price_data["LASTUPDATE"]),
                            "source": "cryptocompare"
                        }
                        
                        self.cache[cache_key] = {
                            "data": result,
                            "timestamp": datetime.now()
                        }
                        
                        return result
                        
        except Exception as e:
            logger.error(f"Error fetching CryptoCompare price: {e}")
        
        return None
    
    async def get_finnhub_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get quote from Finnhub (free: 60 calls/min)
        """
        if not self.finnhub_key or not self.session:
            return None
        
        cache_key = f"fh_quote_{symbol}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < 30:
                return cached["data"]
        
        try:
            url = f"https://finnhub.io/api/v1/quote"
            params = {
                "symbol": symbol,
                "token": self.finnhub_key
            }
            
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    result = {
                        "symbol": symbol,
                        "price": data.get("c"),
                        "change": data.get("c", 0) - data.get("pc", 0),
                        "change_percent": ((data.get("c", 0) - data.get("pc", 0)) / data.get("pc", 1)) * 100,
                        "high": data.get("h"),
                        "low": data.get("l"),
                        "open": data.get("o"),
                        "previous_close": data.get("pc"),
                        "timestamp": datetime.now(),
                        "source": "finnhub"
                    }
                    
                    self.cache[cache_key] = {
                        "data": result,
                        "timestamp": datetime.now()
                    }
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Error fetching Finnhub quote: {e}")
        
        return None
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[OrderBook]:
        """Get order book from CCXT exchange"""
        if not self.exchange:
            return None
        
        try:
            ccxt_symbol = self._to_ccxt_symbol(symbol)
            orderbook = await self.exchange.fetch_order_book(ccxt_symbol, limit)
            
            return OrderBook(
                symbol=symbol,
                bids=orderbook["bids"][:limit],
                asks=orderbook["asks"][:limit],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return None
    
    async def get_ticker_24h(self, symbol: str) -> Dict[str, Any]:
        """Get 24h ticker statistics"""
        stats = {
            "symbol": symbol,
            "price": None,
            "change_24h": None,
            "change_percent_24h": None,
            "high_24h": None,
            "low_24h": None,
            "volume_24h": None,
            "timestamp": datetime.now()
        }
        
        # Try CryptoCompare for crypto
        if symbol in ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD"]:
            cc_data = await self.get_cryptocompare_price(symbol)
            if cc_data:
                stats.update(cc_data)
                return stats
        
        # Try Yahoo Finance
        try:
            yf_data = await self.get_yahoo_data(symbol, timeframe="1h", period="2d")
            if not yf_data.empty:
                stats["price"] = yf_data["close"].iloc[-1]
                stats["high_24h"] = yf_data["high"].max()
                stats["low_24h"] = yf_data["low"].min()
                stats["volume_24h"] = yf_data["volume"].sum()
                
                if len(yf_data) > 1:
                    prev_close = yf_data["close"].iloc[-2]
                    current = yf_data["close"].iloc[-1]
                    stats["change_24h"] = current - prev_close
                    stats["change_percent_24h"] = ((current - prev_close) / prev_close) * 100
                
                return stats
        except Exception as e:
            logger.error(f"Error getting 24h ticker from Yahoo: {e}")
        
        return stats
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Get prices for multiple symbols"""
        results = {}
        
        tasks = [self.get_ticker_24h(symbol) for symbol in symbols]
        price_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(symbols, price_results):
            if isinstance(result, dict):
                results[symbol] = result
            else:
                results[symbol] = {"error": str(result)}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "prices": results
        }
    
    def _to_ccxt_symbol(self, symbol: str) -> str:
        """Convert symbol to CCXT format"""
        # Map common symbols
        symbol_map = {
            "BTCUSD": "BTC/USD",
            "ETHUSD": "ETH/USD",
            "SOLUSD": "SOL/USD",
            "BNBUSD": "BNB/USD",
            "XRPUSD": "XRP/USD",
            "ADAUSD": "ADA/USD",
            "EURUSD": "EUR/USD",
            "GBPUSD": "GBP/USD",
            "USDJPY": "USD/JPY"
        }
        
        return symbol_map.get(symbol, symbol.replace("USD", "/USD"))
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 500
    ) -> pd.DataFrame:
        """Get historical OHLCV data"""
        # Try CCXT first
        df = await self.get_ccxt_data(symbol, timeframe, limit)
        
        if df.empty:
            # Fallback to Yahoo Finance
            period_map = {
                "1m": "5d", "5m": "5d", "15m": "5d",
                "1h": "1mo", "4h": "3mo",
                "1d": "1y", "1wk": "5y"
            }
            period = period_map.get(timeframe, "1mo")
            df = await self.get_yahoo_data(symbol, timeframe, period)
        
        return df


# Singleton instance
_market_collector: Optional[MarketDataCollector] = None


def get_market_collector(
    alpha_vantage_key: Optional[str] = None,
    cryptocompare_key: Optional[str] = None,
    finnhub_key: Optional[str] = None
) -> MarketDataCollector:
    """Get or create market data collector singleton"""
    global _market_collector
    if _market_collector is None:
        _market_collector = MarketDataCollector(
            alpha_vantage_key,
            cryptocompare_key,
            finnhub_key
        )
    return _market_collector
