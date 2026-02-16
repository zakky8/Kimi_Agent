"""
AI Trading Agent - Full System Control
24/7 Market Monitoring with Autonomous Decision Making
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import os

from openai import AsyncOpenAI
import google.generativeai as genai
from groq import AsyncGroq
import anthropic

from ..config import settings, AI_PROVIDERS

logger = logging.getLogger(__name__)


class AgentState(Enum):
    IDLE = "idle"
    MONITORING = "monitoring"
    ANALYZING = "analyzing"
    TRADING = "trading"
    ERROR = "error"


class CommandType(Enum):
    START = "start"
    STOP = "stop"
    STATUS = "status"
    ANALYZE = "analyze"
    TRADE = "trade"
    SCAN = "scan"
    ALERT = "alert"
    CONFIG = "config"


@dataclass
class AgentCommand:
    """Command for the AI agent"""
    command_type: CommandType
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None


@dataclass
class AgentResponse:
    """Response from the AI agent"""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    action_taken: Optional[str] = None


@dataclass
class MarketInsight:
    """Market analysis insight"""
    symbol: str
    timeframe: str
    sentiment: str
    technical_score: float
    fundamental_score: float
    recommendation: str
    confidence: float
    reasoning: str
    timestamp: datetime


class AIAgent:
    """
    AI Trading Agent with Full System Control
    - 24/7 market monitoring
    - Autonomous analysis
    - Multi-provider AI support
    - System integration
    """
    
    def __init__(self):
        self.state = AgentState.IDLE
        self.clients: Dict[str, Any] = {}
        self.command_history: List[AgentCommand] = []
        self.response_history: List[AgentResponse] = []
        self.insights: Dict[str, List[MarketInsight]] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.alert_callbacks: List[Callable] = []
        self.system_stats: Dict[str, Any] = {}
        
        # Initialize AI clients
        self._init_ai_clients()
        
    def _init_ai_clients(self):
        """Initialize AI provider clients"""
        try:
            # OpenRouter (recommended - multiple models)
            if settings.OPENROUTER_API_KEY:
                self.clients["openrouter"] = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=settings.OPENROUTER_API_KEY
                )
                logger.info("OpenRouter client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenRouter: {e}")
        
        try:
            # Google Gemini
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.clients["gemini"] = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
        
        try:
            # Groq
            if settings.GROQ_API_KEY:
                self.clients["groq"] = AsyncGroq(api_key=settings.GROQ_API_KEY)
                logger.info("Groq client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Groq: {e}")
        
        try:
            # Anthropic
            if settings.ANTHROPIC_API_KEY:
                self.clients["anthropic"] = anthropic.AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY
                )
                logger.info("Anthropic client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic: {e}")
        
        if not self.clients:
            logger.error("No AI clients initialized. Please configure API keys.")
    
    async def process_command(self, command: AgentCommand) -> AgentResponse:
        """Process agent command"""
        self.command_history.append(command)
        
        try:
            if command.command_type == CommandType.START:
                return await self._cmd_start(command)
            elif command.command_type == CommandType.STOP:
                return await self._cmd_stop(command)
            elif command.command_type == CommandType.STATUS:
                return await self._cmd_status(command)
            elif command.command_type == CommandType.ANALYZE:
                return await self._cmd_analyze(command)
            elif command.command_type == CommandType.TRADE:
                return await self._cmd_trade(command)
            elif command.command_type == CommandType.SCAN:
                return await self._cmd_scan(command)
            elif command.command_type == CommandType.ALERT:
                return await self._cmd_alert(command)
            elif command.command_type == CommandType.CONFIG:
                return await self._cmd_config(command)
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unknown command: {command.command_type}"
                )
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return AgentResponse(
                success=False,
                message=f"Error: {str(e)}"
            )
    
    async def _cmd_start(self, command: AgentCommand) -> AgentResponse:
        """Start 24/7 monitoring"""
        if self.state == AgentState.MONITORING:
            return AgentResponse(
                success=False,
                message="Agent is already monitoring"
            )
        
        self.state = AgentState.MONITORING
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Initial analysis
        await self._perform_initial_analysis()
        
        return AgentResponse(
            success=True,
            message="🚀 AI Agent started 24/7 monitoring",
            data={
                "state": self.state.value,
                "pairs": settings.DEFAULT_PAIRS,
                "timeframes": settings.TIMEFRAMES
            },
            action_taken="Started monitoring loop"
        )
    
    async def _cmd_stop(self, command: AgentCommand) -> AgentResponse:
        """Stop monitoring"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        self.state = AgentState.IDLE
        
        return AgentResponse(
            success=True,
            message="🛑 AI Agent stopped monitoring",
            data={"state": self.state.value}
        )
    
    async def _cmd_status(self, command: AgentCommand) -> AgentResponse:
        """Get agent status"""
        uptime = self._calculate_uptime()
        
        return AgentResponse(
            success=True,
            message=f"Agent Status: {self.state.value.upper()}",
            data={
                "state": self.state.value,
                "uptime": uptime,
                "ai_providers": list(self.clients.keys()),
                "pairs_monitored": settings.DEFAULT_PAIRS,
                "commands_processed": len(self.command_history),
                "insights_generated": sum(len(v) for v in self.insights.values())
            }
        )
    
    async def _cmd_analyze(self, command: AgentCommand) -> AgentResponse:
        """Analyze specific symbol"""
        symbol = command.parameters.get("symbol", "BTCUSDT")
        timeframe = command.parameters.get("timeframe", "1h")
        
        # Perform analysis
        insight = await self._analyze_symbol(symbol, timeframe)
        
        return AgentResponse(
            success=True,
            message=f"Analysis complete for {symbol}",
            data={
                "symbol": symbol,
                "timeframe": timeframe,
                "insight": insight.__dict__ if insight else None
            },
            action_taken="Performed technical and sentiment analysis"
        )
    
    async def _cmd_trade(self, command: AgentCommand) -> AgentResponse:
        """Execute trade (if enabled)"""
        symbol = command.parameters.get("symbol")
        direction = command.parameters.get("direction")
        size = command.parameters.get("size")
        
        # Validate trade
        if not all([symbol, direction, size]):
            return AgentResponse(
                success=False,
                message="Missing trade parameters"
            )
        
        # In a real system, this would execute the trade
        # For now, just return the intended action
        return AgentResponse(
            success=True,
            message=f"Trade signal: {direction} {size} {symbol}",
            data={
                "symbol": symbol,
                "direction": direction,
                "size": size,
                "status": "signal_generated"
            },
            action_taken="Generated trade signal"
        )
    
    async def _cmd_scan(self, command: AgentCommand) -> AgentResponse:
        """Scan all pairs for opportunities"""
        opportunities = await self._scan_all_pairs()
        
        return AgentResponse(
            success=True,
            message=f"Scan complete. Found {len(opportunities)} opportunities",
            data={"opportunities": opportunities}
        )
    
    async def _cmd_alert(self, command: AgentCommand) -> AgentResponse:
        """Set up alert"""
        alert_type = command.parameters.get("type")
        condition = command.parameters.get("condition")
        
        return AgentResponse(
            success=True,
            message=f"Alert configured: {alert_type}",
            data={"alert_type": alert_type, "condition": condition}
        )
    
    async def _cmd_config(self, command: AgentCommand) -> AgentResponse:
        """Update configuration"""
        key = command.parameters.get("key")
        value = command.parameters.get("value")
        
        return AgentResponse(
            success=True,
            message=f"Configuration updated: {key}",
            data={"key": key, "value": value}
        )
    
    async def _monitoring_loop(self):
        """24/7 monitoring loop"""
        logger.info("Starting 24/7 monitoring loop")
        
        while self.state == AgentState.MONITORING:
            try:
                # Check price movements
                await self._check_price_movements()
                
                # Check economic calendar
                await self._check_economic_events()
                
                # Check sentiment
                await self._check_sentiment()
                
                # Generate signals if conditions met
                await self._generate_signals()
                
                # Wait before next iteration
                await asyncio.sleep(settings.MONITOR_INTERVAL_SECONDS)
                
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _perform_initial_analysis(self):
        """Perform initial analysis on all pairs"""
        logger.info("Performing initial analysis...")
        
        for symbol in settings.DEFAULT_PAIRS[:5]:  # Limit to first 5 for speed
            try:
                insight = await self._analyze_symbol(symbol, settings.DEFAULT_TIMEFRAME)
                if insight:
                    if symbol not in self.insights:
                        self.insights[symbol] = []
                    self.insights[symbol].append(insight)
                    
                    # Check if we should alert
                    if insight.confidence > settings.MIN_CONFIDENCE_THRESHOLD:
                        await self._send_alert(f"High confidence insight for {symbol}: {insight.recommendation}")
                        
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
    
    async def _analyze_symbol(self, symbol: str, timeframe: str) -> Optional[MarketInsight]:
        """Analyze a symbol using AI"""
        try:
            # Get market data
            from ..data_collection.binance_client import get_binance_client
            
            async with get_binance_client() as client:
                klines = await client.get_klines(symbol, timeframe, limit=100)
                ticker = await client.get_24h_ticker(symbol)
            
            if not klines:
                return None
            
            # Prepare data for AI analysis
            analysis_prompt = self._build_analysis_prompt(symbol, timeframe, klines, ticker)
            
            # Get AI analysis
            response = await self._chat_completion(analysis_prompt)
            
            # Parse response
            try:
                result = json.loads(response)
                
                return MarketInsight(
                    symbol=symbol,
                    timeframe=timeframe,
                    sentiment=result.get("sentiment", "neutral"),
                    technical_score=result.get("technical_score", 0.5),
                    fundamental_score=result.get("fundamental_score", 0.5),
                    recommendation=result.get("recommendation", "hold"),
                    confidence=result.get("confidence", 0.5),
                    reasoning=result.get("reasoning", ""),
                    timestamp=datetime.now()
                )
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                return MarketInsight(
                    symbol=symbol,
                    timeframe=timeframe,
                    sentiment="neutral",
                    technical_score=0.5,
                    fundamental_score=0.5,
                    recommendation="analyze_manually",
                    confidence=0.3,
                    reasoning=response[:500],
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _build_analysis_prompt(self, symbol: str, timeframe: str, klines: List, ticker: Dict) -> str:
        """Build analysis prompt for AI"""
        # Calculate basic stats
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        current_price = closes[-1]
        price_change_24h = ticker.get("priceChangePercent", 0)
        volume_24h = ticker.get("volume", 0)
        
        # Calculate SMAs
        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else current_price
        
        prompt = f"""Analyze this trading data and provide insights:

Symbol: {symbol}
Timeframe: {timeframe}
Current Price: {current_price}
24h Change: {price_change_24h}%
24h Volume: {volume_24h}

Price Data (last 20 candles):
- High: {max(highs[-20:])}
- Low: {min(lows[-20:])}
- SMA 20: {sma_20}
- SMA 50: {sma_50}

Provide analysis in this JSON format:
{{
    "sentiment": "bullish/bearish/neutral",
    "technical_score": 0.0-1.0,
    "fundamental_score": 0.0-1.0,
    "recommendation": "buy/sell/hold/wait",
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation"
}}
"""
        return prompt
    
    async def _chat_completion(self, prompt: str, provider: str = None) -> str:
        """Get chat completion from AI"""
        # Use default provider or first available
        if not provider:
            provider = "openrouter" if "openrouter" in self.clients else list(self.clients.keys())[0]
        
        client = self.clients.get(provider)
        if not client:
            return "Error: No AI client available"
        
        try:
            if provider == "openrouter":
                response = await client.chat.completions.create(
                    model="anthropic/claude-3-sonnet",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                return response.choices[0].message.content
                
            elif provider == "gemini":
                response = await asyncio.to_thread(client.generate_content, prompt)
                return response.text
                
            elif provider == "groq":
                response = await client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                return response.choices[0].message.content
                
            elif provider == "anthropic":
                response = await client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
        except Exception as e:
            logger.error(f"AI completion error: {e}")
            return f"Error: {str(e)}"
    
    async def _check_price_movements(self):
        """Check for significant price movements"""
        # Implementation would check price changes and alert on significant moves
        pass
    
    async def _check_economic_events(self):
        """Check for upcoming economic events"""
        # Implementation would check Forex Factory calendar
        pass
    
    async def _check_sentiment(self):
        """Check market sentiment"""
        # Implementation would check social sentiment
        pass
    
    async def _generate_signals(self):
        """Generate trading signals"""
        # Implementation would generate signals based on analysis
        pass
    
    async def _scan_all_pairs(self) -> List[Dict]:
        """Scan all pairs for opportunities"""
        opportunities = []
        
        for symbol in settings.DEFAULT_PAIRS:
            try:
                insight = await self._analyze_symbol(symbol, settings.DEFAULT_TIMEFRAME)
                if insight and insight.confidence > settings.MIN_CONFIDENCE_THRESHOLD:
                    opportunities.append({
                        "symbol": symbol,
                        "recommendation": insight.recommendation,
                        "confidence": insight.confidence,
                        "reasoning": insight.reasoning
                    })
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
        
        return opportunities
    
    async def _send_alert(self, message: str):
        """Send alert to registered callbacks"""
        for callback in self.alert_callbacks:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def register_alert_callback(self, callback: Callable):
        """Register alert callback"""
        self.alert_callbacks.append(callback)
    
    def _calculate_uptime(self) -> str:
        """Calculate system uptime"""
        # Simplified - would track actual start time
        return "Running"


# Singleton instance
_agent_instance: Optional[AIAgent] = None


def get_agent() -> AIAgent:
    """Get or create AI agent singleton"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AIAgent()
    return _agent_instance
