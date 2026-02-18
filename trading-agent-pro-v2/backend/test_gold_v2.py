
import asyncio
import yfinance as yf

async def test_ticker(symbol: str):
    print(f"\nTesting Ticker: {symbol}")
    try:
        def _fetch():
            return yf.Ticker(symbol).history(period="1d", interval="1h")
        
        hist = await asyncio.to_thread(_fetch)
        
        if hist.empty:
            print(f"❌ {symbol}: Empty DataFrame")
        else:
            print(f"✅ {symbol}: Data Found! Last: {hist['Close'].iloc[-1]}")
            
    except Exception as e:
        print(f"⚠️ {symbol} Exception: {e}")

async def main():
    # GLD is reliable but price is different. 
    # GC=F hangs.
    # Try XAUUSD=X
    tickers = ["GLD", "XAUUSD=X"] 
    for t in tickers:
        await test_ticker(t)

if __name__ == "__main__":
    asyncio.run(main())
