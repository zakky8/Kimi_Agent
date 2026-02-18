
import asyncio
import ccxt.async_support as ccxt
import pandas as pd

async def test_ccxt_gold():
    symbol = "PAXG/USDT"
    print(f"\nTesting CCXT Symbol: {symbol}")
    exchange = ccxt.binance()
    try:
        ticker = await exchange.fetch_ticker(symbol)
        await exchange.close()
        
        if ticker:
            print(f"✅ {symbol}: Price {ticker['last']}")
        else:
            print(f"❌ {symbol}: No Data")
            
    except Exception as e:
        await exchange.close()
        print(f"⚠️ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_ccxt_gold())
