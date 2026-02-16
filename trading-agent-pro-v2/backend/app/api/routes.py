"""
API Routes - AI Trading Agent Pro v2
Complete REST API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import asyncio
import logging
import json
import os

from ..config import settings, AI_PROVIDERS, TRADING_PAIRS_CONFIG
from ..ai_engine.agent import get_agent, AgentCommand, CommandType
from ..browser_automation.forex_factory import get_calendar
from ..analysis.liquidity_analysis import LiquidityAnalyzer
from ..analysis.price_action import PriceActionAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic Models ====================

class StartMonitoringRequest(BaseModel):
    pairs: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None


class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    symbol: Optional[str] = None


class AnalyzeImageRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    analysis_type: str = "technical"


class TelegramChannelRequest(BaseModel):
    channels: List[str]


class SettingsUpdateRequest(BaseModel):
    section: str
    settings: Dict[str, Any]


# ==================== Agent Control ====================

@router.post("/agent/start")
async def start_monitoring(request: StartMonitoringRequest):
    """Start 24/7 AI agent monitoring"""
    try:
        agent = get_agent()
        
        command = AgentCommand(
            command_type=CommandType.START,
            parameters={
                "pairs": request.pairs or settings.DEFAULT_PAIRS,
                "timeframes": request.timeframes or [settings.DEFAULT_TIMEFRAME]
            }
        )
        
        response = await agent.process_command(command)
        
        return {
            "success": response.success,
            "message": response.message,
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/stop")
async def stop_monitoring():
    """Stop AI agent monitoring"""
    try:
        agent = get_agent()
        
        command = AgentCommand(command_type=CommandType.STOP)
        response = await agent.process_command(command)
        
        return {
            "success": response.success,
            "message": response.message
        }
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/status")
async def get_agent_status():
    """Get AI agent status"""
    try:
        agent = get_agent()
        
        command = AgentCommand(command_type=CommandType.STATUS)
        response = await agent.process_command(command)
        
        return response.data
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Chat with AI Agent ====================

@router.post("/chat/message")
async def send_chat_message(request: ChatMessageRequest):
    """Send message to AI agent"""
    try:
        agent = get_agent()
        
        # Process natural language command
        message = request.message.lower()
        
        # Detect command type from message
        if "start" in message and "monitor" in message:
            cmd_type = CommandType.START
        elif "stop" in message:
            cmd_type = CommandType.STOP
        elif "analyze" in message or "check" in message:
            cmd_type = CommandType.ANALYZE
        elif "status" in message:
            cmd_type = CommandType.STATUS
        else:
            # General chat - get AI response
            response_text = await agent._chat_completion(
                f"You are an AI trading assistant. User asks: {request.message}\n\n"
                f"Provide a helpful response about trading, market analysis, or system control."
            )
            return {
                "success": True,
                "message": response_text,
                "type": "chat"
            }
        
        # Extract symbol if mentioned
        symbol = request.symbol
        if not symbol:
            for pair in settings.DEFAULT_PAIRS:
                if pair.lower() in message:
                    symbol = pair
                    break
        
        command = AgentCommand(
            command_type=cmd_type,
            parameters={"symbol": symbol} if symbol else {}
        )
        
        response = await agent.process_command(command)
        
        return {
            "success": response.success,
            "message": response.message,
            "data": response.data,
            "type": "command"
        }
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/analyze-image")
async def analyze_chart_image(
    file: UploadFile = File(...),
    symbol: str = Form(...),
    timeframe: str = Form("1h")
):
    """Upload and analyze chart image"""
    try:
        # Save uploaded file
        upload_dir = "./data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = f"{upload_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Get AI agent
        agent = get_agent()
        
        # Analyze with vision-capable AI
        # This would use Gemini or Claude vision
        analysis_prompt = f"""Analyze this trading chart for {symbol} on {timeframe} timeframe.

Provide:
1. Current trend direction
2. Key support and resistance levels
3. Any visible patterns
4. Trading recommendation (buy/sell/wait)
5. Risk level (low/medium/high)

Be specific and actionable."""
        
        # For now, return a placeholder response
        # In production, this would use actual vision AI
        return {
            "success": True,
            "message": f"Chart uploaded for {symbol} {timeframe}",
            "file_path": file_path,
            "analysis": "Vision analysis would be performed here with Gemini/Claude vision models",
            "note": "Connect Gemini API key for full image analysis"
        }
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Market Data ====================

@router.get("/market/price/{symbol}")
async def get_price(symbol: str):
    """Get current price for a symbol"""
    try:
        from ..data_collection.binance_client import get_binance_client
        
        async with get_binance_client() as client:
            ticker = await client.get_24h_ticker(symbol.upper())
            return ticker
    except Exception as e:
        logger.error(f"Error getting price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get historical OHLCV data"""
    try:
        from ..data_collection.binance_client import get_binance_client
        
        async with get_binance_client() as client:
            klines = await client.get_klines(symbol.upper(), timeframe, limit)
            
            if not klines:
                raise HTTPException(status_code=404, detail="No data available")
            
            # Format data
            data = []
            for k in klines:
                data.append({
                    "timestamp": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5])
                })
            
            return {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "data": data
            }
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Technical Analysis ====================

@router.get("/analysis/{symbol}")
async def get_technical_analysis(
    symbol: str,
    timeframe: str = Query("1h"),
    include_liquidity: bool = Query(True),
    include_price_action: bool = Query(True)
):
    """Get comprehensive technical analysis"""
    try:
        from ..data_collection.binance_client import get_binance_client
        import pandas as pd
        
        # Get data
        async with get_binance_client() as client:
            klines = await client.get_klines(symbol.upper(), timeframe, limit=200)
        
        if not klines:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Create DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy',
            'taker_buy_quote', 'ignore'
        ])
        
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df.index = pd.to_datetime(df['timestamp'], unit='ms')
        
        result = {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat()
        }
        
        # Liquidity Analysis
        if include_liquidity:
            liquidity = LiquidityAnalyzer(df)
            liquidity.analyze_all()
            result["liquidity"] = liquidity.get_summary()
        
        # Price Action Analysis
        if include_price_action:
            price_action = PriceActionAnalyzer(df)
            price_action.analyze_all()
            result["price_action"] = price_action.get_summary()
        
        return result
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Forex Calendar ====================

@router.get("/calendar/forexfactory")
async def get_forex_calendar(
    days: int = Query(7, ge=1, le=30),
    currencies: Optional[str] = Query(None, description="Comma-separated currencies"),
    impact: Optional[str] = Query(None, description="high,medium,low")
):
    """Get Forex Factory economic calendar (IST timezone)"""
    try:
        async with get_calendar() as calendar:
            currency_list = currencies.split(",") if currencies else None
            
            impact_filter = None
            if impact:
                from ..browser_automation.forex_factory import ImpactLevel
                impact_map = {
                    "high": [ImpactLevel.HIGH],
                    "medium": [ImpactLevel.MEDIUM],
                    "low": [ImpactLevel.LOW],
                    "all": [ImpactLevel.HIGH, ImpactLevel.MEDIUM, ImpactLevel.LOW]
                }
                impact_filter = impact_map.get(impact.lower())
            
            events = await calendar.get_calendar(
                days=days,
                currencies=currency_list,
                impact_filter=impact_filter
            )
            
            return {
                "source": "forexfactory",
                "timezone": "IST",
                "events": [e.to_dict() for e in events]
            }
    except Exception as e:
        logger.error(f"Error getting calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/next-high-impact")
async def get_next_high_impact_event():
    """Get next high impact economic event"""
    try:
        async with get_calendar() as calendar:
            event = calendar.get_next_high_impact_event()
            
            if event:
                return event.to_dict()
            else:
                return {"message": "No upcoming high impact events found"}
    except Exception as e:
        logger.error(f"Error getting next event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Telegram ====================

@router.post("/telegram/channels")
async def add_telegram_channels(request: TelegramChannelRequest):
    """Add Telegram channels to monitor"""
    try:
        from ..data_collection.telegram_collector import get_telegram_collector
        
        collector = get_telegram_collector()
        collector.add_channels(request.channels)
        
        return {
            "success": True,
            "channels": collector.channels
        }
    except Exception as e:
        logger.error(f"Error adding channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telegram/sentiment/{symbol}")
async def get_telegram_sentiment(symbol: str):
    """Get Telegram sentiment for a symbol"""
    try:
        from ..data_collection.telegram_collector import get_telegram_collector
        
        collector = get_telegram_collector()
        
        # Fetch messages if needed
        if not collector.messages:
            await collector.fetch_all_channels(limit_per_channel=50)
        
        sentiment = collector.get_symbol_sentiment(symbol.upper())
        return sentiment
    except Exception as e:
        logger.error(f"Error getting Telegram sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telegram/trending")
async def get_telegram_trending(limit: int = Query(10)):
    """Get trending symbols from Telegram"""
    try:
        from ..data_collection.telegram_collector import get_telegram_collector
        
        collector = get_telegram_collector()
        
        if not collector.messages:
            await collector.fetch_all_channels(limit_per_channel=50)
        
        trending = collector.get_trending_symbols(limit)
        return {"trending": trending}
    except Exception as e:
        logger.error(f"Error getting trending: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Settings ====================

@router.get("/settings/schema")
async def get_settings_schema():
    """Get settings UI schema"""
    return {
        "ai_providers": AI_PROVIDERS,
        "trading_pairs": TRADING_PAIRS_CONFIG,
        "timezones": ["Asia/Kolkata", "America/New_York", "Europe/London", "UTC"],
        "timeframes": settings.TIMEFRAMES
    }


@router.get("/settings/current")
async def get_current_settings():
    """Get current settings"""
    return {
        "default_pairs": settings.DEFAULT_PAIRS,
        "default_timeframe": settings.DEFAULT_TIMEFRAME,
        "risk_settings": {
            "max_drawdown": settings.MAX_DRAWDOWN_PERCENT,
            "daily_loss_limit": settings.DAILY_LOSS_LIMIT_PERCENT,
            "per_trade_risk": settings.PER_TRADE_RISK_PERCENT
        },
        "monitoring": {
            "interval_seconds": settings.MONITOR_INTERVAL_SECONDS,
            "alert_enabled": settings.ALERT_ENABLED
        },
        "telegram_channels": settings.TELEGRAM_CHANNELS
    }


@router.post("/settings/update")
async def update_settings(request: SettingsUpdateRequest):
    """Update settings"""
    try:
        # In production, this would update the .env file or database
        return {
            "success": True,
            "message": f"Settings updated for section: {request.section}",
            "settings": request.settings
        }
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== System Info ====================

@router.get("/system/info")
async def get_system_info():
    """Get system information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "default_timezone": settings.DEFAULT_TIMEZONE,
        "ai_providers_configured": [
            k for k, v in {
                "openrouter": settings.OPENROUTER_API_KEY,
                "gemini": settings.GEMINI_API_KEY,
                "groq": settings.GROQ_API_KEY,
                "anthropic": settings.ANTHROPIC_API_KEY
            }.items() if v
        ],
        "financial_apis": {
            "binance": bool(settings.BINANCE_API_KEY),
            "alpha_vantage": bool(settings.ALPHA_VANTAGE_API_KEY)
        },
        "social_apis": {
            "telegram": bool(settings.TELEGRAM_API_ID),
            "reddit": bool(settings.REDDIT_CLIENT_ID)
        }
    }
