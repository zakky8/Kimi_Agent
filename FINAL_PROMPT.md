# Master AI Upgrade Prompt

This prompt is designed to be given to an advanced AI (like Claude 3.5 Sonnet, GPT-4, or Antigravity) to fix the current codebase and implement the Multi-Agent Autonomous Trading system.

---

### **Master Prompt for AI Trading Agent Upgrade**

**Objective**: Fix the existing codebase and implement a multi-agent system capable of autonomous, hands-off trade execution.

**Context**: I have two versions of a trading agent (`v1` and `v2 Pro`). 
- `v1` is functional but lacks an execution loop. 
- `v2` has the structure for "24/7 monitoring" but is missing core files (like `signal_generator.py`) and uses placeholder `pass` statements in the monitoring cycle.

**Tasks**:

1.  **Fix V2 Structural Errors**:
    *   Reconstruct the missing `backend/app/ai_engine/signal_generator.py` for v2 by porting the logic from v1 and adapting it for Smart Money Concepts (SMC).
    *   Replace all `pass` placeholders in `backend/app/ai_engine/agent.py` (specifically in `_monitoring_loop`, `_check_price_movements`, and `_generate_signals`) with functional code.

2.  **Implement Multiple Independent Agents**:
    *   Refactor the `AIAgent` class to support a **"Swarm" architecture**. 
    *   Create a factory that can spin up dedicated agent instances for different symbols (e.g., one agent for BTCUSD, one for EURUSD).
    *   Each agent must manage its own state, memory, and monitoring cycle independently.

3.  **Bridge the "Auto-Pilot" (Execution Layer)**:
    *   Create a new `ExecutionManager` that connects the `SignalGenerator` to the `MT5Client.place_order` method.
    *   Implement **Autonomous Mode**: When a signal is generated with `confidence > 0.85` and matches risk management rules, the agent should automatically execute the trade via MT5 without asking for permission.
    *   Implement a safety "Circuit Breaker" to stop all trading if daily drawdown exceeds 2%.

4.  **Automation & Reliability**:
    *   Implement a background task using `apscheduler` or a persistent `asyncio` loop to ensure the "24/7 monitoring" handles connection drops and restarts.
    *   Add an auto-installer for Playwright (`playwright install chromium`) to ensure the Research Engine works out-of-the-box.

**Deliverables**: 
- Fully functional `agent.py` and `signal_generator.py`.
- An updated `MT5Client` that handles real trade execution with Stop Loss and Take Profit.
- A central "Control Panel" logic in `routes.py` to manage multiple active agents.

---
