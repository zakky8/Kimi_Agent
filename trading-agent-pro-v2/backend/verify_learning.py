
import asyncio
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai_engine.agent import AIAgent, AgentStatus
from app.core.trade_history_manager import trade_history_manager
from datetime import datetime

class MockMT5:
    def __init__(self):
        self.connected = True
    async def get_rates(self, symbol, timeframe, count):
        return []
    async def get_account_info(self):
        return {"balance": 10000, "profit": 0}

async def test_learning_loop():
    print("🚀 Testing Agent Learning Loop...")
    
    mock_mt5 = MockMT5()
    agent = AIAgent(
        symbol="XAUUSD",
        agent_id="test_agent_v1",
        mt5_client=mock_mt5,
        config={"signal_config": {}}
    )
    
    # 1. Simulate a mistake (a losing trade)
    print("📝 Recording a simulated mistake (Loss)...")
    mistake_trade = {
        "agent_id": "test_agent_v1",
        "symbol": "XAUUSD",
        "direction": "buy",
        "profit": -50.0,
        "metadata": {
            "market_structure": "downtrend"
        }
    }
    trade_history_manager.save_trade(mistake_trade)
    
    # 2. Trigger Evolution
    print("🧠 Triggering Evolution...")
    await agent.evolve()
    
    print(f"📊 Agent Knowledge: {agent.knowledge['failed_patterns']}")
    
    # 3. Verify Learning (Should block a similar setup)
    print("🛡️ Verifying Learning Mechanism...")
    # Mock a signal that matches the mistake pattern
    from app.ai_engine.signal_generator import TradingSignal
    
    bad_signal = TradingSignal(
        symbol="XAUUSD",
        direction="buy",
        entry_price=2000.0,
        stop_loss=1980.0,
        take_profit=2040.0,
        confidence=0.9,
        strategy="SMC",
        smc_zones=[],
        risk_reward=2.0,
        timeframe="M15",
        timestamp=datetime.utcnow(),
        metadata={}
    )
    
    # Mock a dataframe that shows 'downtrend' (needs high, low, close, open)
    import pandas as pd
    df = pd.DataFrame([{
        "close": 100, 
        "open": 105, 
        "high": 110, 
        "low": 95, 
        "volume": 1000
    }] * 100)
    
    is_mistake = await agent._is_repeating_mistake(bad_signal, df)
    
    if is_mistake:
        print("✅ SUCCESS: Agent correctly identified and blocked a repeating mistake pattern!")
    else:
        print("❌ FAILURE: Agent failed to block the repeating mistake.")

if __name__ == "__main__":
    asyncio.run(test_learning_loop())
