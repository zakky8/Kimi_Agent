
import asyncio
import yfinance as yf
import pandas as pd

async def test_ticker(symbol: str):
    print(f"\nTesting Ticker: {symbol}")
    try:
        def _fetch():
            return yf.Ticker(symbol).history(period="5d", interval="1h")
        
        hist = await asyncio.to_thread(_fetch)
        
        if hist.empty:
            print(f"❌ {symbol}: Empty DataFrame")
        else:
            print(f"✅ {symbol}: Data Found! Last: {hist['Close'].iloc[-1]}")
            
    except Exception as e:
        print(f"⚠️ {symbol} Exception: {e}")

async def main():
    tickers = ["GC=F", "XAU-USD", "GOLD", "GLD"]
    for t in tickers:
        await test_ticker(t)

if __name__ == "__main__":
    asyncio.run(main())
