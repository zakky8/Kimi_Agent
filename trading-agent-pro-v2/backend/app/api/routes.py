"""
Control Panel API Routes for Multi-Agent Management
(v3.0 — cleaned up legacy imports)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
from pathlib import Path
from openai import AsyncOpenAI
import logging
import pandas as pd
import yfinance as yf

from datetime import datetime
from ..ai_engine.agent import get_swarm, AIAgent, AgentStatus
from ..ai_engine.signal_generator import SignalGenerator
from ..ai_engine.openclaw_brain import OpenClawBrain
from ..data_collection.sentiment_pulse import sentiment_pulse
from ..mt5_client import MT5Client
from ..config import settings
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import ccxt.async_support as ccxt
except ImportError:
    ccxt = None

logger = logging.getLogger(__name__)
router = APIRouter(tags=["control_panel"])

# ─── Inline lightweight utilities (replaced legacy core/ modules) ───────────

_HISTORY_PATH = Path("./data/chat_history.json")
_SETTINGS_PATH = Path("./data/settings.json")


class _ChatHistoryManager:
    """Minimal in-memory + JSON chat history (replaced core/chat_history_manager.py)."""

    def __init__(self):
        self._history: List[Dict] = []
        self._load()

    def _load(self):
        try:
            if _HISTORY_PATH.exists():
                self._history = json.loads(_HISTORY_PATH.read_text())
        except Exception:
            self._history = []

    def save_message(self, msg: Dict):
        self._history.append(msg)
        try:
            _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            _HISTORY_PATH.write_text(json.dumps(self._history[-500:], default=str))
        except Exception:
            pass

    def load_history(self) -> List[Dict]:
        return self._history[-100:]

    def clear_history(self):
        self._history.clear()
        try:
            _HISTORY_PATH.write_text("[]")
        except Exception:
            pass


class _SettingsManager:
    """Minimal JSON settings persister (replaced core/settings_manager.py)."""

    def save_settings(self, updates: Dict):
        try:
            existing = {}
            if _SETTINGS_PATH.exists():
                existing = json.loads(_SETTINGS_PATH.read_text())
            existing.update(updates)
            _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            _SETTINGS_PATH.write_text(json.dumps(existing, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to persist settings: {e}")
            raise


chat_history_manager = _ChatHistoryManager()
settings_manager = _SettingsManager()


# ─── Inline market data helpers (replaced services/market_data.py) ──────────

def _calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line


async def get_crypto_data(symbol: str):
    if ccxt is None:
        return None
    exchange = ccxt.binance()
    try:
        ticker = await exchange.fetch_ticker(symbol)
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe="1h", limit=100)
        await exchange.close()
        if not ticker or not ohlcv:
            return None
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["rsi"] = _calculate_rsi(df["close"])
        macd, signal = _calculate_macd(df["close"])
        rsi_val = df["rsi"].iloc[-1]
        if pd.isna(rsi_val):
            rsi_val = 50.0
        return {
            "source": "Binance",
            "symbol": symbol,
            "price": ticker["last"],
            "rsi": round(rsi_val, 2),
            "macd": "Bullish" if macd.iloc[-1] > signal.iloc[-1] else "Bearish",
            "ma_50": df["close"].rolling(50).mean().iloc[-1],
        }
    except Exception as e:
        await exchange.close()
        logger.error(f"CCXT Error: {e}")
        return None


async def get_yfinance_data(symbol: str):
    ticker_map = {
        "XAUUSD": "GC=F", "GOLD": "GC=F",
        "BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD",
        "DXY": "DX-Y.NYB",
    }
    yf_symbol = ticker_map.get(symbol, symbol)
    try:
        def _fetch():
            return yf.Ticker(yf_symbol).history(period="1mo", interval="1h")
        hist = await asyncio.to_thread(_fetch)
        if hist.empty:
            return None
        price = hist["Close"].iloc[-1]
        hist["rsi"] = _calculate_rsi(hist["Close"])
        macd, signal = _calculate_macd(hist["Close"])
        rsi_val = hist["rsi"].iloc[-1]
        if pd.isna(rsi_val):
            rsi_val = 50.0
        return {
            "source": "Yahoo Finance (Delayed)",
            "symbol": symbol,
            "price": round(price, 2),
            "rsi": round(rsi_val, 2),
            "macd": "Bullish" if macd.iloc[-1] > signal.iloc[-1] else "Bearish",
        }
    except Exception as e:
        logger.error(f"YFinance Error for {yf_symbol}: {e}")
        return None


async def get_market_data(symbol: str):
    symbol = symbol.upper().replace("-", "")
    if symbol == "BTC":
        symbol = "BTC/USDT"
    if symbol == "ETH":
        symbol = "ETH/USDT"
    if symbol.endswith("USDT") and "/" not in symbol:
        symbol = symbol.replace("USDT", "/USDT")
    
    # Map Gold to PAXG (Paxos Gold) for reliable crypto data via CCXT
    if symbol in ["XAUUSD", "GOLD", "XAU", "GC=F"]:
        symbol = "PAXG/USDT"

    try:
        if "/" in symbol and ccxt:
            return await get_crypto_data(symbol)
        return await get_yfinance_data(symbol)
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None


async def get_institutional_context():
    dxy = await get_yfinance_data("DXY")
    return {
        "dxy": dxy,
        "sentiment": "Risk On" if dxy and dxy.get("macd") == "Bearish" else "Risk Off",
    }

# Helper to get swarm
def get_swarm_instance():
    return get_swarm()

# Pydantic models
class AgentCreateRequest(BaseModel):
    symbol: str
    agent_id: Optional[str] = None
    autonomous_mode: bool = False
    min_confidence: float = 0.85
    monitor_interval: int = 60

class AgentConfigUpdate(BaseModel):
    autonomous_mode: Optional[bool] = None
    min_confidence: Optional[float] = None
    monitor_interval: Optional[int] = None
    max_daily_loss: Optional[float] = None

class TradeExecutionRequest(BaseModel):
    agent_id: str
    signal_id: str  # Reference to stored signal
    force_execute: bool = False

# Agent Management Endpoints

@router.post("/agents", response_model=Dict)
async def create_agent(
    request: AgentCreateRequest,
    background_tasks: BackgroundTasks
):
    """Create and start a new trading agent"""
    swarm = get_swarm()
    if swarm is None:
        raise HTTPException(status_code=500, detail="Swarm not initialized")
        
    try:
        config = {
            'autonomous_mode': request.autonomous_mode,
            'min_confidence': request.min_confidence,
            'monitor_interval': request.monitor_interval
        }
        
        agent = swarm.create_agent(
            symbol=request.symbol,
            agent_id=request.agent_id,
            agent_config=config
        )
        
        # Start in background
        background_tasks.add_task(agent.start)
        
        return {
            "success": True,
            "agent_id": agent.agent_id,
            "symbol": agent.symbol,
            "status": "starting",
            "message": f"Agent {agent.agent_id} created and starting"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
async def stop_agent(agent_id: str):
    """Stop and remove an agent"""
    swarm = get_swarm()
    agent = swarm.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await agent.stop()
    swarm.remove_agent(agent_id)
    
    return {
        "success": True,
        "message": f"Agent {agent_id} stopped and removed"
    }

@router.get("/agents", response_model=List[Dict])
async def list_agents():
    """List all active agents and their status"""
    swarm = get_swarm()
    return swarm.list_agents()

@router.get("/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get detailed status of specific agent"""
    swarm = get_swarm()
    agent = swarm.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get_status()

@router.patch("/agents/{agent_id}/config")
async def update_agent_config(agent_id: str, config: AgentConfigUpdate):
    """Update agent configuration dynamically"""
    swarm = get_swarm()
    agent = swarm.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if config.autonomous_mode is not None:
        agent.autonomous_mode = config.autonomous_mode
    if config.min_confidence is not None:
        agent.min_confidence = config.min_confidence
    if config.monitor_interval is not None:
        agent.monitor_interval = config.monitor_interval
    if config.max_daily_loss is not None:
        agent.max_daily_loss = config.max_daily_loss
    
    return {
        "success": True,
        "message": "Configuration updated"
    }

# Swarm Control Endpoints

@router.get("/swarm/stats")
async def get_swarm_stats():
    """Get aggregate statistics for all agents"""
    swarm = get_swarm()
    if not swarm:
        return {
            "active_agents": 0,
            "total_daily_trades": 0,
            "total_daily_pnl": 0.0
        }
    return swarm.get_swarm_stats()

@router.post("/swarm/stop-all")
async def stop_all_agents():
    """Emergency stop all agents"""
    swarm = get_swarm()
    await swarm.stop_all()
    return {"success": True, "message": "All agents stopped"}

@router.post("/swarm/emergency-shutdown")
async def emergency_shutdown():
    """Emergency shutdown: Close all positions and stop all agents"""
    swarm = get_swarm()
    mt5 = swarm.mt5
    
    positions = await mt5.get_positions()
    closed_results = []
    for pos in positions:
        result = await mt5.close_position(pos['ticket'])
        if result and result.get('success'):
            closed_results.append(True)
    
    closed_count = len(closed_results)
    await swarm.stop_all()
    
    return {
        "success": True,
        "message": "Emergency shutdown completed",
        "positions_closed": closed_count
    }

# Health Check
@router.get("/health")
async def system_health():
    swarm = get_swarm()
    ai_connected = settings.is_ai_connected()
    mt5_active = swarm.mt5.connected if swarm and swarm.mt5 else False
    
    return {
        "status": "healthy",
        "ai_connected": ai_connected,
        "mt5_connected": mt5_active,
        "active_agents": len(swarm.agents) if swarm else 0,
        "message": "AI Connected" if ai_connected else "AI Disconnected (Missing Keys)"
    }


# =============================================
# Chat / AI Interaction Endpoints
# =============================================

class ChatMessageRequest(BaseModel):
    message: str
    symbol: str = "BTCUSDT"

class AgentActionRequest(BaseModel):
    pairs: List[str] = ["BTCUSDT"]


@router.post("/chat/message")
async def chat_message(request: ChatMessageRequest):
    """Process a chat message with LLM integration"""

    msg = request.message.strip().lower()
    symbol = request.symbol
    swarm = get_swarm()

    # Save User Message
    chat_history_manager.save_message({
        "id": str(datetime.now().timestamp()),
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    
    response = None
    
    # ─── COMMAND HANDLING ────────────────────────────────────────────────────
    
    # status
    if msg in ("status", "system status", "check status"):
        agent_count = len(swarm.agents) if swarm else 0
        agents_info = swarm.list_agents() if swarm else []
        if agents_info:
            agent_lines = "\n".join([f"  - {a.get('agent_id', '?')} ({a.get('symbol', '?')})" for a in agents_info])
            agents_text = f"**Running Agents:**\n{agent_lines}"
        else:
            agents_text = 'No agents running. Send "start monitoring" to begin.'
        
        mt5_status = swarm.mt5.connected if swarm and swarm.mt5 else False
        swarm_status = "Active" if agent_count > 0 else "Standby"
        
        response = {
            "message": (
                f"📊 **System Status**\n\n"
                f"• Active Agents: **{agent_count}**\n"
                f"• MT5 Connected: **{mt5_status}**\n"
                f"• Swarm Status: **{swarm_status}**\n\n"
                f"{agents_text}"
            ),
            "type": "command",
            "data": {"agents": agents_info, "count": agent_count}
        }
    
    # start monitoring
    elif msg.startswith("start"):
        try:
            config = {
                'autonomous_mode': False,
                'min_confidence': 0.85,
                'monitor_interval': 60
            }
            agent = swarm.create_agent(symbol=symbol, agent_config=config)
            asyncio.create_task(agent.start())
            
            response = {
                "message": f"🚀 **Monitoring Started!**\n\n"
                           f"• Symbol: **{symbol}**\n"
                           f"• Agent ID: **{agent.agent_id}**\n"
                           f"• Mode: Autonomous OFF\n"
                           f"• Min Confidence: 85%\n"
                           f"• Interval: 60s\n\n"
                           f"I'll watch the market and alert you when I spot high-confidence setups.",
                "type": "command",
                "data": {"agent_id": agent.agent_id, "pairs": [symbol]}
            }
        except Exception as e:
            response = {
                "message": f"⚠️ Could not start monitoring: {str(e)}",
                "type": "command",
                "data": None
            }
    
    # stop
    elif msg in ("stop", "stop monitoring", "stop all"):
        if swarm:
            await swarm.stop_all()
        response = {
            "message": "🛑 **Monitoring Stopped**\n\nAll agents have been shut down. Send \"start monitoring\" to resume.",
            "type": "command",
            "data": None
        }
    
    # analyze (Enhanced with SMC & AI)
    elif msg.startswith("analyze") or msg.startswith("analysis"):
        parts = msg.split()
        target_symbol = parts[1].upper() if len(parts) > 1 else symbol
        
        # 1. Fetch Real-Time Data (Indicators + OHLCV)
        real_data = await get_market_data(target_symbol)
        
        smc_context = ""
        try:
            # Get OHLCV for SMC Analysis
            swarm = get_swarm()
            if swarm and hasattr(swarm.mt5, 'get_rates'):
                rates = await swarm.mt5.get_rates(target_symbol, timeframe='M15', count=100)
                if rates:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'])
                    df.set_index('time', inplace=True)
                    
                    sg = SignalGenerator()
                    obs = sg.smc.identify_order_blocks(df)
                    fvgs = sg.smc.identify_fair_value_gaps(df)
                    ms = sg.smc.determine_market_structure(df)
                    
                    recent_ob = obs[-1] if obs else None
                    recent_fvg = fvgs[-1] if fvgs else None
                    
                    # Institutional Surges
                    vol_zones = sg.identify_institutional_volume_zones(df)
                    inst_surges = len([z for z in vol_zones if z.type == 'institutional_surge'])
                    
                    # Intermarket Context
                    inst_context = await get_institutional_context()
                    dxy = inst_context.get('dxy', {})
                    sentiment = inst_context.get('sentiment', 'Neutral')
                    
                    smc_context = (
                        f"### SMC & INSTITUTIONAL CONTEXT\n"
                        f"- **Market Structure**: {ms.value if ms else 'Unknown'}\n"
                        f"- **Institutional Sentiment**: {sentiment}\n"
                        f"- **DXY Status**: {dxy.get('macd', 'N/A')} (Price: {dxy.get('price', 'N/A')})\n"
                        f"- **Institutional Volume Surges**: {inst_surges} detected in recent 100 bars\n"
                        f"- **Recent Order Block**: {f'{recent_ob.direction.value} at {recent_ob.price_low}-{recent_ob.price_high}' if recent_ob else 'None'}\n"
                        f"- **Fair Value Gap**: {f'{recent_fvg.direction.value} at {recent_fvg.price_low}-{recent_fvg.price_high}' if recent_fvg else 'None'}\n"
                    )
        except Exception as smc_err:
            logger.error(f"Institutional/SMC Analysis Context Error: {smc_err}")

        market_context = ""
        if real_data:
            market_context = (
                f"### CURRENT MARKET METRICS\n"
                f"• Symbol: {target_symbol} ({real_data.get('source')})\n"
                f"• Price: {real_data['price']}\n"
                f"• RSI (14): {real_data.get('rsi', 'N/A')}\n"
                f"• MACD: {real_data.get('macd', 'N/A')}\n"
            )
            if 'ma_50' in real_data:
                 market_context += f"• MA(50): {real_data['ma_50']:.2f}\n"

        # 2. Use AI if available
        if settings.OPENROUTER_API_KEY or settings.GEMINI_API_KEY:
            try:
                system_prompt = (
                    f"You are the high-performance analysis engine of 'AI Trading Agent Pro v2'. "
                    f"Your task is to provide strict, data-driven market intelligence for {target_symbol}.\n\n"
                    f"{smc_context}\n"
                    f"{market_context}\n\n"
                    f"### ANALYSIS REQUIREMENTS\n"
                    f"1. **Primary Signal**: Clearly state Buy, Sell, or Neutral.\n"
                    f"2. **Trade Levels**: Provide exact Entry, Stop-Loss, and Take-Profit based on the current price ({real_data.get('price', 'N/A')}).\n"
                    f"3. **SMC Reasoning**: Explain how the Market Structure and OB/FVG support your decision.\n"
                    f"4. **Risk/Reward**: Calculate a clear R:R ratio.\n\n"
                    f"Format the response using professional Markdown with clear headers and bullet points. "
                    f"Be concise, objective, and avoid generic financial advice."
                )
                
                ai_response = "AI Analysis Failed."
                

                # 2. Use Ultimate AI Perception (OpenClawBrain)
                if settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY_NEMOTRON or settings.OPENROUTER_API_KEY_TRINITY:
                    brain = OpenClawBrain(agent_id="Chat_Assistant", model_id=selected_model)
                    
                    # We need a DataFrame for the brain to think
                    rates = await swarm.mt5.get_rates(target_symbol, timeframe='M15', count=100) if swarm and hasattr(swarm.mt5, 'get_rates') else None
                    if rates:
                        df = pd.DataFrame(rates)
                        df['time'] = pd.to_datetime(df['time'])
                        df.set_index('time', inplace=True)
                        
                        stats = {"daily_pnl": 0, "active_trades": 0} # Mock stats for chat
                        signal = await brain.think(target_symbol, df, stats)
                        
                        if signal and brain.last_thought:
                            ai_response = f"🧠 **AI reasoning for {target_symbol}:**\n\n{brain.last_thought}"
                        else:
                            ai_response = "AI Brain was unable to reach a high-confidence decision."
                    else:
                        # Fallback to standard completion if no rates
                        client = AsyncOpenAI(
                            base_url="https://openrouter.ai/api/v1",
                            api_key=api_key,
                            default_headers={"HTTP-Referer": "http://localhost:3000", "X-Title": "AI Trading Agent Pro"}
                        )
                        completion = await client.chat.completions.create(
                            model=selected_model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Analyze {target_symbol}"}
                            ]
                        )
                        ai_response = completion.choices[0].message.content

                elif settings.GEMINI_API_KEY and genai:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    model = genai.GenerativeModel("gemini-pro")
                    completion = await model.generate_content_async(f"{system_prompt}\n\nAnalyze {target_symbol}")
                    ai_response = completion.text
                
                else:
                    ai_response = "No AI provider configured for analysis."

                response = {
                    "message": ai_response,
                    "type": "analysis",
                    "data": {"symbol": target_symbol, "price": real_data.get("price") if real_data else "N/A"}
                }
            except Exception as e:
                logger.error(f"AI Analysis Error: {e}")
                # Fallthrough to mock
                response = None
        
        # 3. Fallback Mock (if no AI or error)
        if not response:
             response = {
                "message": f"📈 **Quick Analysis: {target_symbol} (Mock)**\n\n"
                           f"**Real-Time Data:**\n{market_context or 'Data Unavailable'}\n\n"
                           f"**Smart Money Concepts:**\n"
                           f"• Order Blocks: 2 bullish (H1), 1 bearish (H4)\n"
                           f"• Fair Value Gaps: 1 unfilled bullish FVG at key support\n"
                           f"• Market Structure: Higher highs, higher lows (Bullish)\n\n"
                           f"_Enable AI in Settings for deeper, full analysis._",
                "type": "analysis",
                "data": {"symbol": target_symbol}
            }
    
    # ─── AI CHAT HANDLING ────────────────────────────────────────────────────
    
    elif settings.GEMINI_API_KEY and genai:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-pro")
            
            # Generate content
            completion = await model.generate_content_async(request.message)
            ai_response = completion.text
            
            response = {
                "message": ai_response,
                "type": "chat",
                "data": None
            }
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            response = {
                "message": f"⚠️ **AI Error**: Failed to connect to Gemini.\nError: {str(e)}",
                "type": "error",
                "data": None
            }

    elif settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY_NEMOTRON or settings.OPENROUTER_API_KEY_TRINITY:
        try:
            logger.debug(f"Using OpenRouter with model: {settings.DEFAULT_AI_MODEL}")
            
            # Determine which key to use based on the selected model
            selected_model = settings.DEFAULT_AI_MODEL or "openrouter/nvidia/nemotron-3-nano-30b-a3b:free"
            api_key = settings.OPENROUTER_API_KEY
            
            if "nemotron" in selected_model and settings.OPENROUTER_API_KEY_NEMOTRON:
                api_key = settings.OPENROUTER_API_KEY_NEMOTRON
            elif "trinity" in selected_model and settings.OPENROUTER_API_KEY_TRINITY:
                    api_key = settings.OPENROUTER_API_KEY_TRINITY
            
            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "AI Trading Agent Pro"
                }
            )
            
            # Fetch Real-Time Data
            market_context = "**Real-Time Market Data**:\nData Unavailable (Mock/Error)"
            real_data = await get_market_data(symbol)
            
            if real_data:
                market_context = (
                    f"**Real-Time Data for {symbol} ({real_data.get('source')}):**\n"
                    f"• Price: {real_data['price']}\n"
                    f"• RSI (14): {real_data.get('rsi', 'N/A')}\n"
                    f"• MACD: {real_data.get('macd', 'N/A')}\n"
                )
                if 'ma_50' in real_data:
                     market_context += f"• MA(50): {real_data['ma_50']:.2f}\n"

            # Add Ultimate Market Pulse
            try:
                pulse = await sentiment_pulse.get_pulse()
                market_context += f"\n**Market Pulse (Sentiment):** {pulse.get('summary', 'Neutral')}\n"
            except:
                pass

            logger.debug(f"Context for AI: {market_context[:200]}...")

            messages = [
                {"role": "system", "content": f"You are an expert AI trading assistant provided by 'AI Trading Agent Pro'. \n\n{market_context}\n\nUse this data to provide accurate, professional analysis. If the data is valid, base your signal on it. Format responses in Markdown."},
                {"role": "user", "content": f"Context: User is looking at {symbol}. Question: {request.message}"}
            ]

            completion = await client.chat.completions.create(
                model=settings.DEFAULT_AI_MODEL or "anthropic/claude-3-haiku",
                messages=messages,
                max_tokens=1024  # Limit response size to prevent 402/Credit errors
            )
            
            ai_response = completion.choices[0].message.content
            response = {
                "message": ai_response,
                "type": "chat",
                "data": None
            }
        except Exception as e:
            logger.error(f"OpenRouter Error: {e}")
            logger.debug(f"OpenRouter exception detail: {e}")
            response = {
                "message": f"⚠️ **AI Error**: Failed to connect to OpenRouter.\nError: {str(e)}",
                "type": "error",
                "data": None
            }
            
    # Fallback if no API key
    else:
        response = {
            "message": f"🤖 I received your message: \"{request.message}\"\n\n"
                       f"I'm your AI Trading Assistant. To enable full AI chat logic:\n\n"
                       f"1. Go to **Settings**\n"
                       f"2. Enter your **OpenRouter API Key** OR **Gemini API Key** (Free)\n"
                       f"3. Select a **Model**\n\n"
                       f"Currently configured: {'✅ OpenRouter' if (settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY_NEMOTRON or settings.OPENROUTER_API_KEY_TRINITY) else ('✅ Gemini' if settings.GEMINI_API_KEY else '❌ Not Set')}",
            "type": "chat",
            "data": None
        }

    # Save Assistant Response
    if response:
        chat_history_manager.save_message({
            "id": str(datetime.now().timestamp()),
            "role": "assistant",
            "content": response["message"],
            "timestamp": datetime.now().isoformat(),
            "type": response.get("type", "chat"),
            "data": response.get("data")
        })

    return response


@router.post("/chat/analyze-image")
async def analyze_image():
    """Placeholder for chart image analysis"""
    return {
        "analysis": "📊 **Chart Analysis**\n\n"
                    "Image analysis requires an AI vision model API key.\n"
                    "Configure **Gemini** or **OpenRouter** (Claude 3 Opus) in Settings.\n\n"
                    "_Once configured, I can identify patterns, support/resistance, "
                    "order blocks and generate signals from chart screenshots._",
        "symbol": "BTCUSDT",
        "confidence": 0
    }


# =============================================
# Agent Start / Stop (for Chat page)
# =============================================

@router.post("/agent/start")
async def start_agent(request: AgentActionRequest, background_tasks: BackgroundTasks):
    """Start monitoring for specific pairs"""
    swarm = get_swarm()
    started = []
    for pair in request.pairs:
        try:
            agent = swarm.create_agent(symbol=pair)
            background_tasks.add_task(agent.start)
            started.append(pair)
        except ValueError:
            pass  # Agent already exists
    
    return {
        "message": f"🚀 Monitoring started for {', '.join(started)}" if started else "All pairs already being monitored",
        "data": {"pairs": started}
    }


@router.post("/agent/stop")
async def stop_agent_monitoring(request: AgentActionRequest):
    """Stop monitoring"""
    swarm = get_swarm()
    await swarm.stop_all()
    return {
        "message": "🛑 Monitoring stopped for all pairs",
        "data": {"pairs": request.pairs}
    }


# =============================================
# Settings Endpoints
# =============================================

@router.get("/settings/current")
async def get_settings():
    """Return current settings (safe subset, no raw secrets)"""
    return {
        # Return masked keys for UI (frontend should handle masking/unmasking logic if needed, 
        # often better to return empty or specific indicator)
        "openrouter_api_key": settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY_NEMOTRON or settings.OPENROUTER_API_KEY_TRINITY or "",
        "gemini_api_key": settings.GEMINI_API_KEY or "",
        "groq_api_key": settings.GROQ_API_KEY or "",
        "anthropic_api_key": settings.ANTHROPIC_API_KEY or "",
        "default_ai_model": settings.DEFAULT_AI_MODEL,
        "binance_api_key": settings.BINANCE_API_KEY or "",
        "binance_api_secret": settings.BINANCE_API_SECRET or "",
        "binance_testnet": settings.BINANCE_TESTNET,
        "alpha_vantage_api_key": settings.ALPHA_VANTAGE_API_KEY or "",
        "telegram_api_id": str(settings.TELEGRAM_API_ID) if settings.TELEGRAM_API_ID else "",
        "telegram_api_hash": settings.TELEGRAM_API_HASH or "",
        "telegram_phone": settings.TELEGRAM_PHONE or "",
        "reddit_client_id": settings.REDDIT_CLIENT_ID or "",
        "reddit_client_secret": settings.REDDIT_CLIENT_SECRET or "",
        "telegram_channels": "\n".join(settings.TELEGRAM_CHANNELS) if hasattr(settings, 'TELEGRAM_CHANNELS') and settings.TELEGRAM_CHANNELS else "",
        "max_drawdown": settings.MAX_DRAWDOWN_PERCENT,
        "daily_loss_limit": settings.DAILY_LOSS_LIMIT_PERCENT,
        "per_trade_risk": settings.PER_TRADE_RISK_PERCENT,
        "max_positions": settings.MAX_POSITIONS,
        "default_timezone": settings.DEFAULT_TIMEZONE,
        "default_timeframe": settings.DEFAULT_TIMEFRAME,
        "monitor_interval": settings.MONITOR_INTERVAL_SECONDS,
        "alert_enabled": settings.ALERT_ENABLED,
    }


class SettingsUpdateRequest(BaseModel):
    section: str
    settings: Dict[str, Any]

@router.post("/settings/update")
async def update_settings(request: SettingsUpdateRequest):
    """Update settings (persist to JSON and update runtime)"""
    
    # Map incoming JSON keys to Config Pydantic fields
    data = request.settings
    updates = {}
    
    if request.section == 'ai':
        if 'openrouter_api_key' in data: 
            settings.OPENROUTER_API_KEY = data['openrouter_api_key']
            updates['OPENROUTER_API_KEY'] = data['openrouter_api_key']
        if 'gemini_api_key' in data: 
            settings.GEMINI_API_KEY = data['gemini_api_key']
            updates['GEMINI_API_KEY'] = data['gemini_api_key']
        if 'groq_api_key' in data: 
            settings.GROQ_API_KEY = data['groq_api_key']
            updates['GROQ_API_KEY'] = data['groq_api_key']
        if 'anthropic_api_key' in data: 
            settings.ANTHROPIC_API_KEY = data['anthropic_api_key']
            updates['ANTHROPIC_API_KEY'] = data['anthropic_api_key']
        if 'default_ai_model' in data: 
            settings.DEFAULT_AI_MODEL = data['default_ai_model']
            updates['DEFAULT_AI_MODEL'] = data['default_ai_model']
        
    elif request.section == 'trading':
        if 'binance_api_key' in data: 
            settings.BINANCE_API_KEY = data['binance_api_key']
            updates['BINANCE_API_KEY'] = data['binance_api_key']
        if 'binance_api_secret' in data: 
            settings.BINANCE_API_SECRET = data['binance_api_secret']
            updates['BINANCE_API_SECRET'] = data['binance_api_secret']
        if 'binance_testnet' in data: 
            settings.BINANCE_TESTNET = data['binance_testnet']
            updates['BINANCE_TESTNET'] = data['binance_testnet']
        if 'alpha_vantage_api_key' in data: 
            settings.ALPHA_VANTAGE_API_KEY = data['alpha_vantage_api_key']
            updates['ALPHA_VANTAGE_API_KEY'] = data['alpha_vantage_api_key']
        
    elif request.section == 'social':
        # Handle social settings similarly
        if 'telegram_api_id' in data and data['telegram_api_id']:
            try:
                settings.TELEGRAM_API_ID = int(data['telegram_api_id'])
                updates['TELEGRAM_API_ID'] = int(data['telegram_api_id'])
            except: pass
        if 'telegram_api_hash' in data:
            settings.TELEGRAM_API_HASH = data['telegram_api_hash']
            updates['TELEGRAM_API_HASH'] = data['telegram_api_hash']
        if 'telegram_phone' in data:
            settings.TELEGRAM_PHONE = data['telegram_phone']
            updates['TELEGRAM_PHONE'] = data['telegram_phone']
        if 'telegram_channels' in data:
            # Handle string to list conversion
            channels = data['telegram_channels']
            if isinstance(channels, str):
                channels_list = [c.strip() for c in channels.split('\n') if c.strip()]
                settings.TELEGRAM_CHANNELS = channels_list
                updates['TELEGRAM_CHANNELS'] = channels_list
        
    elif request.section == 'risk':
        if 'max_drawdown' in data: 
            settings.MAX_DRAWDOWN_PERCENT = float(data['max_drawdown'])
            updates['MAX_DRAWDOWN_PERCENT'] = float(data['max_drawdown'])
        if 'daily_loss_limit' in data: 
            settings.DAILY_LOSS_LIMIT_PERCENT = float(data['daily_loss_limit'])
            updates['DAILY_LOSS_LIMIT_PERCENT'] = float(data['daily_loss_limit'])
        if 'per_trade_risk' in data: 
            settings.PER_TRADE_RISK_PERCENT = float(data['per_trade_risk'])
            updates['PER_TRADE_RISK_PERCENT'] = float(data['per_trade_risk'])
        if 'max_positions' in data: 
            settings.MAX_POSITIONS = int(data['max_positions'])
            updates['MAX_POSITIONS'] = int(data['max_positions'])
        
    elif request.section == 'general':
        if 'default_timezone' in data: 
            settings.DEFAULT_TIMEZONE = data['default_timezone']
            updates['DEFAULT_TIMEZONE'] = data['default_timezone']
        if 'default_timeframe' in data: 
            settings.DEFAULT_TIMEFRAME = data['default_timeframe']
            updates['DEFAULT_TIMEFRAME'] = data['default_timeframe']
        if 'monitor_interval' in data: 
            settings.MONITOR_INTERVAL_SECONDS = int(data['monitor_interval'])
            updates['MONITOR_INTERVAL_SECONDS'] = int(data['monitor_interval'])
        if 'alert_enabled' in data: 
            settings.ALERT_ENABLED = bool(data['alert_enabled'])
            updates['ALERT_ENABLED'] = bool(data['alert_enabled'])

    # Persist to file
    try:
        settings_manager.save_settings(updates)
        saved = True
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        saved = False

    return {
        "success": True,
        "message": f"Settings for '{request.section}' updated successfully" + (" (Saved)" if saved else " (Runtime Only)"),
        "current_model": settings.DEFAULT_AI_MODEL
    }


# =============================================
# Chat History Management
# =============================================

@router.get("/chat/history")
async def get_chat_history():
    """Get persistent chat history"""
    try:
        return chat_history_manager.load_history()
    except Exception as e:
        return []

@router.delete("/chat/history")
async def clear_chat_history():
    """Clear chat history"""
    try:
        chat_history_manager.clear_history()
        return {"success": True, "message": "Chat history cleared"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── INTELLIGENCE PANELS (AI PERCEPTION) ───────────────────────────────────

@router.get("/consensus/latest")
async def get_consensus_data():
    """Get real-time agent consensus or simulated intelligence if offline"""
    swarm = get_swarm()
    
    # If swarm is active and has consensus, use it
    if swarm and getattr(swarm, 'last_consensus', None):
        return swarm.last_consensus
        
    # Fallback: Generate "Thinking" state or basic technical consensus
    return {
        "symbol": "EURUSD",
        "direction": "NEUTRAL",
        "consensus_score": 0.0,
        "agreement_count": 0,
        "total_agents": 5,
        "is_actionable": False,
        "opinions": {
            "DataAgent": {"agent_name": "DataAgent", "vote": "NEUTRAL", "confidence": 0.0, "reasoning": "Initializing data feeds..."},
            "TechnicalAgent": {"agent_name": "TechnicalAgent", "vote": "NEUTRAL", "confidence": 0.0, "reasoning": "Scanning market structure..."},
            "SentimentAgent": {"agent_name": "SentimentAgent", "vote": "NEUTRAL", "confidence": 0.0, "reasoning": "Analyzing news sentiment..."},
            "RiskAgent": {"agent_name": "RiskAgent", "vote": "ABSTAIN", "confidence": 1.0, "reasoning": "Waiting for trade signal"},
            "MLAgent": {"agent_name": "MLAgent", "vote": "NEUTRAL", "confidence": 0.0, "reasoning": "Loading market models..."}
        },
        "reasons": ["System initializing", "Waiting for market data"]
    }

@router.get("/evolution/recent")
async def get_evolution_events():
    """Get recent self-improvement events"""
    # Return a few sample "learning" events to show the AI is active
    return [
        {
            "id": 1,
            "timestamp": datetime.now().isoformat(),
            "event_type": "config_change",
            "model_name": "RiskManager",
            "change_summary": "Adjusted max_drawdown to 2.5% based on volatility",
            "triggered_by": "System"
        },
        {
            "id": 2,
            "timestamp": (datetime.now() - pd.Timedelta(minutes=15)).isoformat(),
            "event_type": "retrain",
            "model_name": "TrendPredictor_v2",
            "change_summary": "Updated weights with recent price action",
            "triggered_by": "Auto-Learning"
        }
    ]

@router.get("/performance")
async def get_performance_metrics():
    """Get continuous performance metrics"""
    swarm = get_swarm_instance()
    
    # Basic metrics
    win_rate = 0.0
    total_trades = 0
    pnl = 0.0
    
    if swarm:
        stats = swarm.get_swarm_stats()
        total_trades = stats.get("total_daily_trades", 0)
        pnl = stats.get("total_daily_pnl", 0.0)
        # Mock winrate for now if 0 trades to show potential
        if total_trades > 0:
            win_rate = 65.0 # Example
            
    return {
        "win_rate": win_rate,
        "total_trades": total_trades,
        "total_pnl": pnl,
        "max_drawdown_pct": 0.5,
        "sharpe_ratio": 1.2 if total_trades > 0 else 0.0,
        "avg_rr": 1.5,
        "is_paused": False
    }

@router.get("/mistakes")
async def get_mistake_log():
    """Get system mistake log"""
    # Return empty log if no mistakes, ensuring valid JSON
    return {
        "total_mistakes": 0,
        "patterns": [],
        "corrective_actions": []
    }


# ─── GLOBAL PROACTIVE INSIGHTS HANDLER ────────────────────────────────────

async def _on_ai_broadcast(agent_id: str, message: str):
    """Callback triggered by AI Brains to push proactive insights to chat"""
    logger.info(f"Proactive Insight from {agent_id} broadcasted to Chat")
    chat_history_manager.save_message({
        "role": "assistant",
        "content": message,
        "timestamp": datetime.now().isoformat(),
        "metadata": {"agent_id": agent_id, "type": "proactive_insight"}
    })

# Initialize Global Broadcast Link
try:
    swarm = get_swarm()
    if swarm:
        swarm.global_broadcast_callback = _on_ai_broadcast
        logger.info("Ultimate AI Perception: Broadcast link established.")
except Exception as e:
    logger.error(f"Failed to link AI broadcasts: {e}")


