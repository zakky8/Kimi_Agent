"""
Real-time Market Data API using yfinance
Provides live forex, crypto, and commodity prices + candlestick data
"""

from fastapi import APIRouter, Query
from typing import Optional
import yfinance as yf
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market_data"])

# Symbol mapping: display name -> yfinance symbol
SYMBOL_MAP = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    "USDCHF": "USDCHF=X",
    "XAUUSD": "GC=F",       # Gold futures
    "XAGUSD": "SI=F",       # Silver futures
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "USOIL": "CL=F",        # Crude oil futures
}

# Reverse lookup
REVERSE_MAP = {v: k for k, v in SYMBOL_MAP.items()}

# Price cache to avoid rate limiting
_price_cache = {}
_cache_time = None
CACHE_TTL = 15  # seconds


def _get_yf_symbol(symbol: str) -> str:
    """Convert display symbol to yfinance symbol"""
    clean = symbol.upper().replace("/", "")
    return SYMBOL_MAP.get(clean, clean)


def _get_display_symbol(yf_symbol: str) -> str:
    """Convert yfinance symbol back to display"""
    return REVERSE_MAP.get(yf_symbol, yf_symbol)


@router.get("/market/prices")
async def get_live_prices(
    symbols: str = Query(
        default="EURUSD,GBPUSD,USDJPY,XAUUSD,BTCUSD",
        description="Comma-separated list of symbols"
    )
):
    """Get live prices for multiple symbols"""
    global _cache_time
    
    requested = [s.strip().upper().replace("/", "") for s in symbols.split(",")]
    
    # Check cache
    now = datetime.now()
    if _cache_time and (now - _cache_time).seconds < CACHE_TTL and all(s in _price_cache for s in requested):
        return {
            "prices": [_price_cache[s] for s in requested if s in _price_cache],
            "cached": True,
            "timestamp": _cache_time.isoformat()
        }
    
    # Fetch live data
    yf_symbols = [_get_yf_symbol(s) for s in requested]
    
    try:
        result = []
        # Use yfinance to get current data
        tickers = yf.Tickers(" ".join(yf_symbols))
        
        for yf_sym, display_sym in zip(yf_symbols, requested):
            try:
                ticker = tickers.tickers.get(yf_sym)
                if ticker is None:
                    continue
                    
                info = ticker.fast_info
                price = info.last_price if hasattr(info, 'last_price') else 0
                prev_close = info.previous_close if hasattr(info, 'previous_close') else price
                
                change = price - prev_close if prev_close else 0
                change_pct = (change / prev_close * 100) if prev_close and prev_close != 0 else 0
                
                # Determine category
                if display_sym in ("BTCUSD", "ETHUSD"):
                    category = "Crypto"
                elif display_sym in ("XAUUSD", "XAGUSD", "USOIL"):
                    category = "Commodity"
                else:
                    category = "Forex"
                
                entry = {
                    "symbol": display_sym,
                    "price": round(price, 5 if category == "Forex" else 2),
                    "change": round(change, 5 if category == "Forex" else 2),
                    "changePercent": round(change_pct, 2),
                    "category": category,
                    "timestamp": now.isoformat()
                }
                result.append(entry)
                _price_cache[display_sym] = entry
                
            except Exception as e:
                logger.warning(f"Failed to fetch {display_sym}: {e}")
                # Use cached value if available
                if display_sym in _price_cache:
                    result.append(_price_cache[display_sym])
        
        _cache_time = now
        
        return {
            "prices": result,
            "cached": False,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Market data fetch error: {e}")
        # Return cached data if available
        if _price_cache:
            return {
                "prices": [_price_cache[s] for s in requested if s in _price_cache],
                "cached": True,
                "error": str(e),
                "timestamp": (_cache_time or now).isoformat()
            }
        return {"prices": [], "cached": False, "error": str(e), "timestamp": now.isoformat()}


@router.get("/market/candles")
async def get_candles(
    symbol: str = Query(default="EURUSD", description="Symbol (e.g., EURUSD, GBPUSD, XAUUSD)"),
    interval: str = Query(default="1h", description="Interval: 1m, 5m, 15m, 1h, 4h, 1d"),
    period: str = Query(default="5d", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y")
):
    """Get OHLCV candlestick data for charting"""
    yf_sym = _get_yf_symbol(symbol)
    
    # Map intervals to yfinance format
    interval_map = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1wk"
    }
    yf_interval = interval_map.get(interval, "1h")
    
    # Adjust period based on interval (yfinance limitations)
    if yf_interval in ("1m",):
        period = "1d"  # Max 7 days for 1m
    elif yf_interval in ("5m", "15m", "30m"):
        period = "5d" if period in ("1mo", "3mo", "6mo", "1y") else period
    
    try:
        ticker = yf.Ticker(yf_sym)
        df = ticker.history(period=period, interval=yf_interval)
        
        if df.empty:
            return {"candles": [], "symbol": symbol, "interval": interval, "error": "No data available"}
        
        candles = []
        for idx, row in df.iterrows():
            # Convert timestamp to Unix seconds for Lightweight Charts
            ts = int(idx.timestamp())
            candles.append({
                "time": ts,
                "open": round(float(row["Open"]), 5),
                "high": round(float(row["High"]), 5),
                "low": round(float(row["Low"]), 5),
                "close": round(float(row["Close"]), 5),
                "volume": int(row.get("Volume", 0))
            })
        
        return {
            "candles": candles,
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "count": len(candles),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Candle data fetch error for {symbol}: {e}")
        return {"candles": [], "symbol": symbol, "interval": interval, "error": str(e)}
