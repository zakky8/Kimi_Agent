import yfinance as yf
import pandas as pd
import asyncio
import logging
import numpy as np

try:
    import ccxt.async_support as ccxt
except ImportError:
    ccxt = None

logger = logging.getLogger(__name__)

# --- Helper Functions for Manual Indicators ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

async def get_market_data(symbol: str):
    """
    Fetch current price and technical indicators (RSI, MACD) manually.
    """
    symbol = symbol.upper().replace("-", "")
    
    # 1. Try Crypto first (CCXT)
    if symbol == "BTC": symbol = "BTC/USDT"
    if symbol == "ETH": symbol = "ETH/USDT"
    if symbol.endswith("USDT") and "/" not in symbol:
        symbol = symbol.replace("USDT", "/USDT")

    try:
        if "/" in symbol and ccxt:
            return await get_crypto_data(symbol)
        else:
            return await get_yfinance_data(symbol)
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

async def get_crypto_data(symbol: str):
    exchange = ccxt.binance()
    try:
        ticker = await exchange.fetch_ticker(symbol)
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
        await exchange.close()
        
        if not ticker or not ohlcv:
            return None
            
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Manual Indicators
        df['rsi'] = calculate_rsi(df['close'])
        macd, signal = calculate_macd(df['close'])
        
        current_price = ticker['last']
        rsi_val = df['rsi'].iloc[-1]
        if pd.isna(rsi_val): rsi_val = 50.0
        
        macd_val = macd.iloc[-1]
        signal_val = signal.iloc[-1]
        
        return {
            "source": "Binance",
            "symbol": symbol,
            "price": current_price,
            "rsi": round(rsi_val, 2),
            "macd": "Bullish" if macd_val > signal_val else "Bearish",
            "ma_50": df['close'].rolling(50).mean().iloc[-1],
            "ma_200": df['close'].rolling(200).mean().iloc[-1]
        }
    except Exception as e:
        await exchange.close()
        logger.error(f"CCXT Error: {e}")
        return await get_yfinance_data(symbol.replace("/", ""))

async def get_yfinance_data(symbol: str):
    ticker_map = {
        "XAUUSD": "GC=F",
        "GOLD": "GC=F",
        "BTCUSDT": "BTC-USD",
        "ETHUSDT": "ETH-USD"
    }
    yf_symbol = ticker_map.get(symbol, symbol)
    
    try:
        def fetch_yf():
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="1mo", interval="1h")
            return hist

        hist = await asyncio.to_thread(fetch_yf)
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        # Manual Indicators
        hist['rsi'] = calculate_rsi(hist['Close'])
        macd, signal = calculate_macd(hist['Close'])
        
        rsi_val = hist['rsi'].iloc[-1]
        if pd.isna(rsi_val): rsi_val = 50.0
        
        macd_val = macd.iloc[-1]
        signal_val = signal.iloc[-1]
        
        return {
            "source": "Yahoo Finance (Delayed)",
            "symbol": symbol,
            "price": round(current_price, 2),
            "rsi": round(rsi_val, 2),
            "macd": "Bullish" if macd_val > signal_val else "Bearish"
        }
        
    except Exception as e:
        logger.error(f"YFinance Error for {yf_symbol}: {e}")
        return None
