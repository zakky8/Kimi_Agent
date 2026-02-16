"""
API Routes
FastAPI endpoints for the trading agent
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import asyncio
import logging
import json
import os

from ..config import settings, TRADING_PAIRS_CONFIG, DATA_SOURCES, AI_PROVIDERS, SETTINGS_SCHEMA
from ..data_collection import (
    get_reddit_collector,
    get_telegram_collector,
    get_web_scraper,
    get_news_collector,
    get_market_collector,
    get_binance_client,
    get_mt5_client,
    get_rss_collector
)
from ..ai_providers import get_ai_client, get_chat_engine, ChatMessage
from ..browser_automation import get_research_engine
from ..signals import get_signal_generator, get_sentiment_analyzer

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic Models ====================

class SignalResponse(BaseModel):
    symbol: str
    direction: str
    strength: str
    confidence: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_reward: Optional[float]
    strategy: str
    reasons: List[str]
    timestamp: str


class SentimentResponse(BaseModel):
    symbol: str
    overall_score: float
    label: str
    source_breakdown: List[Dict[str, Any]]
    timestamp: str


class MarketDataResponse(BaseModel):
    symbol: str
    price: Optional[float]
    change_24h: Optional[float]
    change_percent_24h: Optional[float]
    high_24h: Optional[float]
    low_24h: Optional[float]
    volume_24h: Optional[float]
    timestamp: str


class AnalysisResponse(BaseModel):
    symbol: str
    indicators: Dict[str, Any]
    patterns: Dict[str, Any]
    regime: Dict[str, Any]
    support_resistance: Dict[str, List[float]]
    timestamp: str


class ChatMessageRequest(BaseModel):
    session_id: Optional[str] = None
    content: str
    image_url: Optional[str] = None


class ChatMessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class SettingsUpdateRequest(BaseModel):
    section: str
    settings: Dict[str, Any]


class ResearchRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = None
    max_results: int = 10


# ==================== Health & Status ====================

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/config")
async def get_config():
    """Get trading agent configuration"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "default_pairs": settings.DEFAULT_PAIRS,
        "timeframes": settings.TIMEFRAMES,
        "risk_settings": {
            "max_drawdown": settings.MAX_DRAWDOWN_PERCENT,
            "daily_loss_limit": settings.DAILY_LOSS_LIMIT_PERCENT,
            "per_trade_risk": settings.PER_TRADE_RISK_PERCENT
        },
        "data_sources": {
            k: {
                "enabled": v["enabled"],
                "configured": _check_source_configured(k)
            }
            for k, v in DATA_SOURCES.items()
        },
        "ai_providers": AI_PROVIDERS,
        "default_ai_provider": settings.DEFAULT_AI_PROVIDER,
        "default_ai_model": settings.DEFAULT_AI_MODEL
    }


def _check_source_configured(source: str) -> bool:
    """Check if a data source is configured"""
    config_checks = {
        "binance": bool(settings.BINANCE_API_KEY),
        "alpha_vantage": bool(settings.ALPHA_VANTAGE_API_KEY),
        "cryptocompare": bool(settings.CRYPTOCOMPARE_API_KEY),
        "finnhub": bool(settings.FINNHUB_API_KEY),
        "reddit": bool(settings.REDDIT_CLIENT_ID),
        "telegram": bool(settings.TELEGRAM_API_ID),
        "newsapi": bool(settings.NEWSAPI_KEY),
        "mt5": settings.MT5_ENABLED,
        "yahoo_finance": True,  # Always available
        "rss": True,  # Always available
        "web_scraping": True  # Always available
    }
    return config_checks.get(source, False)


# ==================== Settings Management ====================

@router.get("/settings/schema")
async def get_settings_schema():
    """Get settings schema for frontend"""
    return SETTINGS_SCHEMA


@router.get("/settings/current")
async def get_current_settings():
    """Get current settings values"""
    return {
        "ai_providers": {
            "OPENROUTER_API_KEY": "***" if settings.OPENROUTER_API_KEY else None,
            "GEMINI_API_KEY": "***" if settings.GEMINI_API_KEY else None,
            "GROQ_API_KEY": "***" if settings.GROQ_API_KEY else None,
            "BASETEN_API_KEY": "***" if settings.BASETEN_API_KEY else None,
            "DEFAULT_AI_PROVIDER": settings.DEFAULT_AI_PROVIDER,
            "DEFAULT_AI_MODEL": settings.DEFAULT_AI_MODEL
        },
        "financial_apis": {
            "BINANCE_API_KEY": "***" if settings.BINANCE_API_KEY else None,
            "BINANCE_TESTNET": settings.BINANCE_TESTNET,
            "ALPHA_VANTAGE_API_KEY": "***" if settings.ALPHA_VANTAGE_API_KEY else None,
            "CRYPTOCOMPARE_API_KEY": "***" if settings.CRYPTOCOMPARE_API_KEY else None,
            "FINNHUB_API_KEY": "***" if settings.FINNHUB_API_KEY else None
        },
        "social_media": {
            "REDDIT_CLIENT_ID": "***" if settings.REDDIT_CLIENT_ID else None,
            "TELEGRAM_API_ID": settings.TELEGRAM_API_ID,
            "TELEGRAM_BOT_TOKEN": "***" if settings.TELEGRAM_BOT_TOKEN else None
        },
        "news_rss": {
            "NEWSAPI_KEY": "***" if settings.NEWSAPI_KEY else None,
            "GNEWS_API_KEY": "***" if settings.GNEWS_API_KEY else None,
            "RSS_FEEDS": settings.RSS_FEEDS
        },
        "mt5": {
            "MT5_ENABLED": settings.MT5_ENABLED,
            "MT5_ACCOUNT": settings.MT5_ACCOUNT,
            "MT5_SERVER": settings.MT5_SERVER
        },
        "risk_management": {
            "PER_TRADE_RISK_PERCENT": settings.PER_TRADE_RISK_PERCENT,
            "MAX_DRAWDOWN_PERCENT": settings.MAX_DRAWDOWN_PERCENT,
            "DAILY_LOSS_LIMIT_PERCENT": settings.DAILY_LOSS_LIMIT_PERCENT,
            "DEFAULT_RISK_REWARD": settings.DEFAULT_RISK_REWARD
        },
        "signal_settings": {
            "MIN_CONFIDENCE_THRESHOLD": settings.MIN_CONFIDENCE_THRESHOLD,
            "CONFLUENCE_FACTORS_REQUIRED": settings.CONFLUENCE_FACTORS_REQUIRED,
            "DEFAULT_TIMEFRAME": settings.DEFAULT_TIMEFRAME,
            "CHART_UPDATE_INTERVAL": settings.CHART_UPDATE_INTERVAL
        }
    }


@router.post("/settings/update")
async def update_settings(request: SettingsUpdateRequest):
    """Update settings (saves to .env file)"""
    try:
        # Update settings in memory
        for key, value in request.settings.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        # Save to .env file
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_lines = []
        
        # Read existing .env
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add new values
        updated_keys = set()
        for i, line in enumerate(env_lines):
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0].strip()
                if key in request.settings:
                    env_lines[i] = f"{key}={request.settings[key]}\n"
                    updated_keys.add(key)
        
        # Add new keys
        for key, value in request.settings.items():
            if key not in updated_keys:
                env_lines.append(f"{key}={value}\n")
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        return {"status": "success", "message": "Settings updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/test-connection/{provider}")
async def test_provider_connection(provider: str):
    """Test connection to a data provider"""
    try:
        if provider == "binance":
            async with get_binance_client() as client:
                info = await client.get_exchange_info()
                return {"status": "success", "message": "Binance connection successful", "data": {"server_time": info.get('serverTime')}}
        
        elif provider == "alpha_vantage":
            from alpha_vantage.foreignexchange import ForeignExchange
            fx = ForeignExchange(key=settings.ALPHA_VANTAGE_API_KEY)
            data, _ = fx.get_currency_exchange_rate(from_currency="EUR", to_currency="USD")
            return {"status": "success", "message": "Alpha Vantage connection successful"}
        
        elif provider == "openrouter":
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
                )
                if response.status_code == 200:
                    return {"status": "success", "message": "OpenRouter connection successful"}
                else:
                    return {"status": "error", "message": f"OpenRouter error: {response.status_code}"}
        
        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            models = genai.list_models()
            return {"status": "success", "message": "Gemini connection successful", "data": {"models": len(list(models))}}
        
        elif provider == "groq":
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            models = client.models.list()
            return {"status": "success", "message": "Groq connection successful"}
        
        elif provider == "reddit":
            async with get_reddit_collector() as reddit:
                # Try to get a subreddit
                sub = await reddit.reddit.subreddit("wallstreetbets")
                await sub.load()
                return {"status": "success", "message": "Reddit connection successful"}
        
        elif provider == "telegram":
            async with get_telegram_collector() as tg:
                if tg.client and await tg.client.is_user_authorized():
                    me = await tg.client.get_me()
                    return {"status": "success", "message": "Telegram connection successful", "data": {"user": me.username}}
                else:
                    return {"status": "error", "message": "Telegram not authorized"}
        
        elif provider == "mt5":
            mt5 = get_mt5_client()
            if mt5.initialize():
                info = mt5.get_terminal_info()
                mt5.shutdown()
                return {"status": "success", "message": "MT5 connection successful", "data": info}
            else:
                return {"status": "error", "message": "MT5 initialization failed"}
        
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}
            
    except Exception as e:
        logger.error(f"Connection test error for {provider}: {e}")
        return {"status": "error", "message": str(e)}


# ==================== AI Chat ====================

@router.post("/chat/session/create")
async def create_chat_session(title: Optional[str] = None):
    """Create a new chat session"""
    try:
        chat_engine = await get_chat_engine()
        session = chat_engine.create_session(title=title)
        return {
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions")
async def list_chat_sessions():
    """List all chat sessions"""
    try:
        chat_engine = await get_chat_engine()
        sessions = chat_engine.list_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session details"""
    try:
        chat_engine = await get_chat_engine()
        session = chat_engine.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/session/{session_id}/messages")
async def get_chat_messages(session_id: str, limit: int = 100):
    """Get messages for a chat session"""
    try:
        chat_engine = await get_chat_engine()
        messages = chat_engine.get_session_messages(session_id, limit)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/message")
async def send_chat_message(request: ChatMessageRequest):
    """Send a message to the AI"""
    try:
        chat_engine = await get_chat_engine()
        
        # Create session if not provided
        if not request.session_id:
            session = chat_engine.create_session()
            request.session_id = session.session_id
        
        result = await chat_engine.send_message(
            session_id=request.session_id,
            content=request.content,
            image_url=request.image_url
        )
        
        return result
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    try:
        chat_engine = await get_chat_engine()
        success = chat_engine.delete_session(session_id)
        if success:
            return {"status": "success", "message": "Session deleted"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Image Analysis ====================

@router.post("/analysis/image")
async def analyze_image(
    file: UploadFile = File(...),
    symbol: str = Form(...),
    timeframe: str = Form(...),
    question: Optional[str] = Form(None)
):
    """Analyze chart image using AI"""
    try:
        # Read image data
        image_data = await file.read()
        
        # Get AI client
        ai_client = get_ai_client()
        
        # Analyze chart
        result = await ai_client.analyze_chart(
            image_data=image_data,
            symbol=symbol,
            timeframe=timeframe
        )
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/image")
async def chat_with_image(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    symbol: str = Form(...),
    timeframe: str = Form(...),
    question: Optional[str] = Form(None)
):
    """Send image to chat for analysis"""
    try:
        # Read image data
        image_data = await file.read()
        
        # Get chat engine
        chat_engine = await get_chat_engine()
        
        # Analyze chart in chat context
        result = await chat_engine.analyze_chart_image(
            session_id=session_id,
            image_data=image_data,
            symbol=symbol,
            timeframe=timeframe,
            question=question
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing chat image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Browser Research ====================

@router.post("/research")
async def start_research(request: ResearchRequest):
    """Start a research task"""
    try:
        async with get_research_engine() as engine:
            task_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            task = await engine.create_research_task(
                task_id=task_id,
                query=request.query,
                sources=request.sources,
                max_results=request.max_results
            )
            
            return {
                "task_id": task_id,
                "status": task.status,
                "query": request.query
            }
    except Exception as e:
        logger.error(f"Error starting research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/{task_id}/status")
async def get_research_status(task_id: str):
    """Get research task status"""
    try:
        async with get_research_engine() as engine:
            status = engine.get_task_status(task_id)
            if not status:
                raise HTTPException(status_code=404, detail="Task not found")
            return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting research status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/symbol/{symbol}")
async def research_symbol(symbol: str):
    """Research a trading symbol"""
    try:
        async with get_research_engine() as engine:
            result = await engine.research_symbol(symbol)
            return result
    except Exception as e:
        logger.error(f"Error researching symbol: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Market Data ====================

@router.get("/market/price/{symbol}", response_model=MarketDataResponse)
async def get_price(symbol: str):
    """Get current price for a symbol"""
    try:
        # Try Binance first for crypto
        if symbol.upper().endswith('USDT') or symbol.upper().endswith('BTC'):
            try:
                async with get_binance_client() as client:
                    ticker = await client.get_24h_ticker(symbol)
                    return MarketDataResponse(
                        symbol=symbol.upper(),
                        price=ticker.last_price,
                        change_24h=ticker.price_change,
                        change_percent_24h=ticker.price_change_percent,
                        high_24h=ticker.high_price,
                        low_24h=ticker.low_price,
                        volume_24h=ticker.volume,
                        timestamp=datetime.now().isoformat()
                    )
            except Exception:
                pass
        
        # Fallback to market data collector
        from ..data_collection.market_data import MarketDataCollector
        
        async with MarketDataCollector() as collector:
            data = await collector.get_ticker_24h(symbol.upper())
            
            return MarketDataResponse(
                symbol=symbol.upper(),
                price=data.get("price"),
                change_24h=data.get("change_24h"),
                change_percent_24h=data.get("change_percent_24h"),
                high_24h=data.get("high_24h"),
                low_24h=data.get("low_24h"),
                volume_24h=data.get("volume_24h"),
                timestamp=datetime.now().isoformat()
            )
    except Exception as e:
        logger.error(f"Error getting price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/prices")
async def get_multiple_prices(symbols: str = Query(..., description="Comma-separated symbols")):
    """Get prices for multiple symbols"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        # Try Binance for crypto symbols
        crypto_symbols = [s for s in symbol_list if s.endswith('USDT') or s.endswith('BTC')]
        other_symbols = [s for s in symbol_list if s not in crypto_symbols]
        
        results = {}
        
        if crypto_symbols:
            try:
                async with get_binance_client() as client:
                    for symbol in crypto_symbols:
                        try:
                            ticker = await client.get_24h_ticker(symbol)
                            results[symbol] = {
                                "symbol": symbol,
                                "price": ticker.last_price,
                                "change_24h": ticker.price_change,
                                "change_percent_24h": ticker.price_change_percent,
                                "high_24h": ticker.high_price,
                                "low_24h": ticker.low_price,
                                "volume_24h": ticker.volume,
                                "timestamp": datetime.now().isoformat()
                            }
                        except Exception:
                            continue
            except Exception:
                pass
        
        # Get remaining symbols from market collector
        if other_symbols:
            from ..data_collection.market_data import MarketDataCollector
            async with MarketDataCollector() as collector:
                data = await collector.get_multiple_prices(other_symbols)
                results.update(data.get("prices", {}))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "prices": results
        }
    except Exception as e:
        logger.error(f"Error getting prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(100, description="Number of candles", ge=1, le=1000)
):
    """Get historical OHLCV data"""
    try:
        # Try Binance for crypto
        if symbol.upper().endswith('USDT') or symbol.upper().endswith('BTC'):
            try:
                async with get_binance_client() as client:
                    klines = await client.get_klines(symbol.upper(), timeframe, limit)
                    
                    data = [
                        {
                            "timestamp": k.open_time,
                            "open": k.open,
                            "high": k.high,
                            "low": k.low,
                            "close": k.close,
                            "volume": k.volume
                        }
                        for k in klines
                    ]
                    
                    return {
                        "symbol": symbol.upper(),
                        "timeframe": timeframe,
                        "source": "binance",
                        "data": data
                    }
            except Exception:
                pass
        
        # Fallback to market data collector
        from ..data_collection.market_data import MarketDataCollector
        
        async with MarketDataCollector() as collector:
            df = await collector.get_historical_data(
                symbol.upper(),
                timeframe=timeframe,
                limit=limit
            )
            
            if df.empty:
                raise HTTPException(status_code=404, detail="No data available")
            
            records = df.reset_index().to_dict('records')
            
            for record in records:
                if 'timestamp' in record and hasattr(record['timestamp'], 'isoformat'):
                    record['timestamp'] = record['timestamp'].isoformat()
            
            return {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "source": "yahoo",
                "data": records
            }
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/binance/top-volume")
async def get_binance_top_volume(limit: int = 20):
    """Get top volume pairs from Binance"""
    try:
        async with get_binance_client() as client:
            pairs = await client.get_top_volume_pairs(limit)
            return {"pairs": pairs}
    except Exception as e:
        logger.error(f"Error getting top volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MT5 Integration ====================

@router.get("/mt5/status")
async def get_mt5_status():
    """Get MT5 connection status"""
    try:
        mt5 = get_mt5_client()
        
        if not settings.MT5_ENABLED:
            return {"enabled": False, "message": "MT5 integration disabled"}
        
        # Try to initialize
        initialized = mt5.initialize()
        
        if initialized:
            summary = mt5.get_summary()
            mt5.shutdown()
            return summary
        else:
            return {"enabled": True, "initialized": False, "message": "MT5 not connected"}
            
    except Exception as e:
        logger.error(f"Error getting MT5 status: {e}")
        return {"enabled": False, "error": str(e)}


@router.get("/mt5/account")
async def get_mt5_account():
    """Get MT5 account info"""
    try:
        mt5 = get_mt5_client()
        
        if not mt5.initialize():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        account_info = mt5.get_account_info()
        mt5.shutdown()
        
        if account_info:
            return account_info.__dict__
        else:
            raise HTTPException(status_code=404, detail="Account info not available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MT5 account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mt5/positions")
async def get_mt5_positions():
    """Get MT5 open positions"""
    try:
        mt5 = get_mt5_client()
        
        if not mt5.initialize():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        positions = mt5.get_positions()
        mt5.shutdown()
        
        return {"positions": [p.__dict__ for p in positions]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MT5 positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Sentiment ====================

@router.get("/sentiment/{symbol}", response_model=SentimentResponse)
async def get_sentiment(symbol: str):
    """Get sentiment analysis for a symbol"""
    try:
        reddit = None
        telegram = None
        
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            reddit = get_reddit_collector()
        
        if settings.TELEGRAM_API_ID:
            telegram = get_telegram_collector()
        
        from ..signals import SentimentAnalyzer
        analyzer = SentimentAnalyzer(reddit, telegram)
        
        # Collect sentiment from available sources
        all_scores = []
        
        if reddit:
            try:
                async with reddit:
                    reddit_sentiment = await reddit.get_symbol_sentiment(symbol)
                    all_scores.append(reddit_sentiment.get("sentiment_score", 0))
            except Exception as e:
                logger.error(f"Reddit sentiment error: {e}")
        
        if telegram:
            try:
                async with telegram:
                    telegram_sentiment = await telegram.get_symbol_sentiment(symbol)
                    all_scores.append(telegram_sentiment.get("sentiment_score", 0))
            except Exception as e:
                logger.error(f"Telegram sentiment error: {e}")
        
        # Calculate average
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        if avg_score > 0.3:
            label = "bullish"
        elif avg_score < -0.3:
            label = "bearish"
        else:
            label = "neutral"
        
        return SentimentResponse(
            symbol=symbol.upper(),
            overall_score=round(avg_score, 3),
            label=label,
            source_breakdown=[
                {"source": "reddit", "score": reddit_sentiment.get("sentiment_score", 0)} if reddit else None,
                {"source": "telegram", "score": telegram_sentiment.get("sentiment_score", 0)} if telegram else None
            ],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Technical Analysis ====================

@router.get("/analysis/{symbol}", response_model=AnalysisResponse)
async def get_technical_analysis(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe")
):
    """Get technical analysis for a symbol"""
    try:
        from ..data_collection.market_data import MarketDataCollector
        from ..analysis.technical_indicators import TechnicalIndicators
        from ..analysis.pattern_recognition import PatternRecognition
        from ..analysis.market_regime import MarketRegimeDetector
        
        async with MarketDataCollector() as collector:
            df = await collector.get_historical_data(
                symbol.upper(),
                timeframe=timeframe,
                limit=200
            )
            
            if df.empty:
                raise HTTPException(status_code=404, detail="No data available")
            
            # Technical Indicators
            indicators = TechnicalIndicators(df)
            indicators.add_all_indicators()
            indicators.generate_signals()
            
            # Pattern Recognition
            patterns = PatternRecognition(df)
            patterns.detect_all_patterns()
            
            # Market Regime
            regime_detector = MarketRegimeDetector(df)
            regime = regime_detector.detect_regime()
            
            # Support/Resistance
            sr_levels = indicators.get_support_resistance()
            
            return AnalysisResponse(
                symbol=symbol.upper(),
                indicators=indicators.get_summary(),
                patterns=patterns.get_pattern_summary(),
                regime={
                    "current": regime.regime.value,
                    "confidence": regime.confidence,
                    "duration": regime.duration
                },
                support_resistance=sr_levels,
                timestamp=datetime.now().isoformat()
            )
    except Exception as e:
        logger.error(f"Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Trading Signals ====================

@router.get("/signals/generate/{symbol}", response_model=SignalResponse)
async def generate_signal(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe")
):
    """Generate trading signal for a symbol"""
    try:
        from ..data_collection.market_data import MarketDataCollector
        from ..signals import SignalGenerator
        
        async with MarketDataCollector() as collector:
            df = await collector.get_historical_data(
                symbol.upper(),
                timeframe=timeframe,
                limit=200
            )
            
            if df.empty:
                raise HTTPException(status_code=404, detail="No data available")
            
            generator = SignalGenerator()
            signal = await generator.generate_signal(
                symbol.upper(),
                df,
                sentiment_data=None
            )
            
            if not signal:
                return JSONResponse(
                    status_code=204,
                    content={"message": "No signal generated - insufficient confidence"}
                )
            
            return SignalResponse(
                symbol=signal.symbol,
                direction=signal.direction.value,
                strength=signal.strength.value,
                confidence=signal.confidence,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                risk_reward=signal.risk_reward,
                strategy=signal.strategy,
                reasons=signal.reasons,
                timestamp=signal.timestamp.isoformat()
            )
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/active")
async def get_active_signals():
    """Get all active trading signals"""
    try:
        from ..signals import SignalGenerator
        
        generator = SignalGenerator()
        summary = generator.get_signal_summary()
        
        return summary
    except Exception as e:
        logger.error(f"Error getting active signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Social Media ====================

@router.get("/social/reddit/{symbol}")
async def get_reddit_data(symbol: str, limit: int = Query(50, ge=1, le=100)):
    """Get Reddit data for a symbol"""
    try:
        if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
            raise HTTPException(status_code=503, detail="Reddit API not configured")
        
        async with get_reddit_collector() as reddit:
            sentiment = await reddit.get_symbol_sentiment(symbol.upper())
            return sentiment
    except Exception as e:
        logger.error(f"Error getting Reddit data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social/telegram/{symbol}")
async def get_telegram_data(symbol: str, limit: int = Query(50, ge=1, le=100)):
    """Get Telegram data for a symbol"""
    try:
        if not settings.TELEGRAM_API_ID:
            raise HTTPException(status_code=503, detail="Telegram API not configured")
        
        async with get_telegram_collector() as telegram:
            sentiment = await telegram.get_symbol_sentiment(symbol.upper())
            return sentiment
    except Exception as e:
        logger.error(f"Error getting Telegram data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== News & RSS ====================

@router.get("/news/market")
async def get_market_news():
    """Get latest market news"""
    try:
        async with get_rss_collector() as rss:
            articles = await rss.get_latest_news(limit=20)
            return {
                "articles": [
                    {
                        "title": a.title,
                        "link": a.link,
                        "description": a.description,
                        "published": a.published.isoformat(),
                        "source": a.source,
                        "category": a.category
                    }
                    for a in articles
                ],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/rss/summary")
async def get_rss_summary():
    """Get RSS feeds summary"""
    try:
        async with get_rss_collector() as rss:
            summary = await rss.get_feeds_summary()
            return summary
    except Exception as e:
        logger.error(f"Error getting RSS summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/search")
async def search_news(query: str, limit: int = 20):
    """Search news by keyword"""
    try:
        async with get_rss_collector() as rss:
            articles = await rss.search_news(query, limit)
            return {
                "articles": [
                    {
                        "title": a.title,
                        "link": a.link,
                        "description": a.description,
                        "published": a.published.isoformat(),
                        "source": a.source
                    }
                    for a in articles
                ]
            }
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Pairs & Markets ====================

@router.get("/pairs")
async def get_trading_pairs():
    """Get available trading pairs"""
    return {
        "pairs": [
            {"symbol": symbol, **config}
            for symbol, config in TRADING_PAIRS_CONFIG.items()
        ]
    }


@router.get("/pairs/{symbol}")
async def get_pair_info(symbol: str):
    """Get info for a specific pair"""
    symbol_upper = symbol.upper()
    
    if symbol_upper not in TRADING_PAIRS_CONFIG:
        raise HTTPException(status_code=404, detail="Pair not found")
    
    return {"symbol": symbol_upper, **TRADING_PAIRS_CONFIG[symbol_upper]}
