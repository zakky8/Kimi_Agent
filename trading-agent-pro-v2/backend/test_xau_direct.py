
import asyncio
import yfinance as yf
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_xau_direct():
    print("\n--- Direct XAU/USD Verification (Bypassing App Config) ---\n")
    
    # 1. Fetch Gold Data
    print("[1/2] Fetching XAUUSD data via yfinance (Ticker: GC=F)...")
    try:
        # Using GC=F (Gold Futures) as per config
        ticker = yf.Ticker("GC=F")
        hist = ticker.history(period="5d", interval="1h")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            print(f"✅ Gold Data Fetched:")
            print(f"   - Current Price: {current_price:.2f}")
            print(f"   - Last 5 hours trend: {hist['Close'].tail(5).tolist()}")
        else:
            print("❌ Failed to fetch Gold data (Empty).")
            return
            
    except Exception as e:
        print(f"❌ Error fetching Gold data: {e}")
        return

    # 2. Fetch DXY Data for Institutional Context
    print("\n[2/2] Fetching DXY data for Correlation Check...")
    try:
        dxy_ticker = yf.Ticker("DX-Y.NYB")
        dxy_hist = dxy_ticker.history(period="5d", interval="1h")
        
        if not dxy_hist.empty:
            dxy_price = dxy_hist['Close'].iloc[-1]
            
            # Simple MACD Calculation
            ema12 = dxy_hist['Close'].ewm(span=12, adjust=False).mean()
            ema26 = dxy_hist['Close'].ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            
            dxy_trend = "Bullish" if macd.iloc[-1] > signal.iloc[-1] else "Bearish"
            
            print(f"✅ DXY Data Fetched:")
            print(f"   - Price: {dxy_price:.2f}")
            print(f"   - Trend (MACD): {dxy_trend}")
            
            if dxy_trend == "Bullish":
                print("   -> ⚠️  INSTITUTIONAL LOGIC: DXY is Bullish => Gold BUY Blocked.")
            else:
                print("   -> ✅  INSTITUTIONAL LOGIC: DXY is Bearish => Gold BUY Allowed.")
        else:
            print("⚠️ Failed to fetch DXY data.")
            
    except Exception as e:
        print(f"❌ Error fetching DXY: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_xau_direct())
