
import asyncio
import yfinance as yf
import pandas as pd

async def test_yfinance_data(symbol: str):
    ticker_map = {
        "XAUUSD": "GC=F", "GOLD": "GC=F",
        "BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD",
        "DXY": "DX-Y.NYB",
    }
    yf_symbol = ticker_map.get(symbol, symbol)
    print(f"Testing Symbol: {symbol} -> Mapped: {yf_symbol}")
    
    try:
        def _fetch():
            # Test with 1mo period and 1h interval as per routes.py
            return yf.Ticker(yf_symbol).history(period="1mo", interval="1h")
        
        print("Fetching data...")
        hist = await asyncio.to_thread(_fetch)
        
        if hist.empty:
            print("❌ Result: Empty DataFrame")
            return
            
        print("✅ Result: Data Found")
        print(f"Rows: {len(hist)}")
        print(f"Last Close: {hist['Close'].iloc[-1]}")
        print(f"Last Timestamp: {hist.index[-1]}")
        
    except Exception as e:
        print(f"⚠️ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_yfinance_data("XAUUSD"))
    asyncio.run(test_yfinance_data("BTCUSDT"))
