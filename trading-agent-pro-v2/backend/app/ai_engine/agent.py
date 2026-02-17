"""
Multi-Agent Swarm Architecture for Autonomous Trading
Fixed V2 Implementation with Full Monitoring Loop
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from .signal_generator import SignalGenerator, TradingSignal, OrderBlockType
from ..core.trade_history_manager import trade_history_manager
from ..services.market_data import get_institutional_context
# Assuming these exist or will be created
# from ..mt5_client import MT5Client 
# Need to check where MT5Client is actually located in the folder structure

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "idle"
    MONITORING = "monitoring"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    ERROR = "error"
    STOPPED = "stopped"
    CIRCUIT_BREAKER = "circuit_breaker"
    EVOLVING = "evolving"

@dataclass
class AgentMemory:
    """Persistent memory for each agent instance"""
    recent_signals: List[TradingSignal] = field(default_factory=list)
    trade_history: List[Dict] = field(default_factory=list)
    last_prices: Dict[str, float] = field(default_factory=dict)
    daily_pnl: float = 0.0
    daily_trades: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)
    errors_count: int = 0
    consecutive_errors: int = 0
    
    def add_signal(self, signal: TradingSignal):
        self.recent_signals.append(signal)
        if len(self.recent_signals) > 100:
            self.recent_signals.pop(0)
    
    def add_trade(self, trade: Dict):
        self.trade_history.append(trade)
        self.daily_trades += 1
        self.daily_pnl += trade.get('profit', 0)
        
        # Persist to history manager
        trade_history_manager.save_trade(trade)
        
        if len(self.trade_history) > 1000:
            self.trade_history.pop(0)
    
    def reset_daily_stats(self):
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset = datetime.utcnow()
    
    def record_error(self):
        self.errors_count += 1
        self.consecutive_errors += 1
    
    def clear_errors(self):
        self.consecutive_errors = 0

class AIAgent:
    """
    Individual AI Agent for specific trading symbol
    Part of the Swarm Architecture
    """
    
    def __init__(self, 
                 symbol: str,
                 agent_id: str,
                 mt5_client,
                 config: Dict,
                 signal_callback: Optional[Callable] = None):
        """
        Initialize agent for specific symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSD')
            agent_id: Unique identifier for this agent
            mt5_client: MT5 connection client
            config: Agent configuration
            signal_callback: Optional callback for signal notifications
        """
        self.symbol = symbol
        self.agent_id = agent_id
        self.mt5 = mt5_client
        self.config = config
        self.signal_callback = signal_callback
        
        # Core components
        self.signal_generator = SignalGenerator(config.get('signal_config', {}))
        # News analyzer is optional and may need to be imported correctly
        self.news_analyzer = None 
        
        # State management
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory()
        self.is_running = False
        self._monitoring_task = None
        self._lock = asyncio.Lock()
        
        # Configuration
        self.monitor_interval = config.get('monitor_interval', 60)  # seconds
        self.autonomous_mode = config.get('autonomous_mode', False)
        self.min_confidence = config.get('min_confidence', 0.85)
        self.max_daily_loss = config.get('max_daily_loss', -0.02)  # -2%
        self.max_consecutive_errors = config.get('max_consecutive_errors', 5)
        
        # Evolution Knowledge Base
        self.knowledge = {
            'failed_patterns': [],  # Summaries of technical conditions during losses
            'last_evolution': None
        }
        
        logger.info(f"Agent {agent_id} initialized for {symbol}")
    
    async def start(self):
        """Start the agent monitoring loop"""
        if self.is_running:
            logger.warning(f"Agent {self.agent_id} already running")
            return
        
        self.is_running = True
        self.status = AgentStatus.MONITORING
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Agent {self.agent_id} started monitoring {self.symbol}")
    
    async def stop(self):
        """Stop the agent gracefully"""
        self.is_running = False
        self.status = AgentStatus.STOPPED
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def _monitoring_loop(self):
        """
        Main 24/7 monitoring loop with error handling and reconnection logic
        FIXED: Replaced placeholder 'pass' with full implementation
        """
        retry_delay = 5
        
        while self.is_running:
            try:
                # Check circuit breaker
                if await self._check_circuit_breaker():
                    logger.warning(f"Circuit breaker active for {self.agent_id}")
                    await asyncio.sleep(60)
                    continue
                
                # Reset daily stats if needed
                if datetime.utcnow() - self.memory.last_reset > timedelta(days=1):
                    self.memory.reset_daily_stats()
                
                # Core monitoring cycle
                self.status = AgentStatus.MONITORING
                
                # 1. Check price movements
                price_data = await self._check_price_movements()
                
                # 2. Generate signals if price action detected
                if price_data is not None:
                    self.status = AgentStatus.ANALYZING
                    signal = await self._generate_signals(price_data)
                    
                    # 3. Execute if signal valid and autonomous mode enabled
                    if signal and self.autonomous_mode:
                        await self._execute_signal(signal)
                
                # Reset error counter on successful iteration
                self.memory.clear_errors()
                retry_delay = 5
                
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop {self.agent_id}: {e}")
                self.memory.record_error()
                
                if self.memory.consecutive_errors >= self.max_consecutive_errors:
                    logger.critical(f"Agent {self.agent_id} exceeded max errors, stopping")
                    self.status = AgentStatus.ERROR
                    break
                
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)  # Max 5 min backoff
    
    async def _check_circuit_breaker(self) -> bool:
        """Check if daily drawdown exceeds limit"""
        if hasattr(self.mt5, 'get_account_info'):
            account_info = await self.mt5.get_account_info()
            if account_info:
                daily_profit = account_info.get('profit', 0)
                balance = account_info.get('balance', 1)
                drawdown = daily_profit / balance if balance > 0 else 0
                
                if drawdown <= self.max_daily_loss:
                    self.status = AgentStatus.CIRCUIT_BREAKER
                    return True
        return False
    
    async def _check_price_movements(self) -> Optional[pd.DataFrame]:
        """
        Check for significant price movements and return OHLCV data
        FIXED: Replaced placeholder 'pass' with full implementation
        """
        try:
            # Fetch recent price data from MT5
            if not hasattr(self.mt5, 'get_rates'):
                return None
                
            rates = await self.mt5.get_rates(self.symbol, timeframe='M15', count=100)
            
            if rates is None or len(rates) < 50:
                logger.debug(f"Insufficient data for {self.symbol}")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            
            current_price = df['close'].iloc[-1]
            last_price = self.memory.last_prices.get(self.symbol)
            
            # Store current price
            self.memory.last_prices[self.symbol] = current_price
            
            # Check for significant movement (>0.1% change)
            if last_price and abs(current_price - last_price) / last_price > 0.001:
                logger.info(f"Price movement detected for {self.symbol}: {last_price} -> {current_price}")
                return df
            
            # Also return data if we haven't checked in a while (for signal generation)
            if not hasattr(self, '_last_check_time') or \
               time.time() - self._last_check_time > 300:  # 5 minutes
                self._last_check_time = time.time()
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking price movements for {self.symbol}: {e}")
            return None
    
    async def _generate_signals(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """
        Generate trading signals using Institutional-Grade Multi-Source Analysis
        """
        try:
            # 1. Multi-Intermarket Context (DXY, Sentiment)
            inst_context = await get_institutional_context()
            
            # 2. Institutional Volume Profile Analysis
            vol_zones = self.signal_generator.identify_institutional_volume_zones(df)
            
            # 3. Core Technical analysis
            signal = self.signal_generator.generate_signal(
                symbol=self.symbol,
                df=df,
                timeframe='M15'
            )
            
            if signal is None:
                return None
            
            # 4. Institutional Confluence Check
            # If Gold (XAUUSD), it should have Inverse Correlation with DXY
            if "XAU" in self.symbol and inst_context.get('dxy'):
                dxy_direction = inst_context['dxy'].get('macd')
                if dxy_direction == "Bullish" and signal.direction == "buy":
                    logger.warning(f"Blocking Gold Buy due to Institutional DXY Headwind (DXY is Bullish)")
                    return None
            
            # 5. Evolution Filtering
            if await self._is_repeating_mistake(signal, df):
                logger.warning(f"Agent {self.agent_id} blocked potential repeating mistake on {self.symbol}")
                return None
            
            # 6. Inject institutional data into signal metadata
            signal.metadata['institutional_context'] = inst_context
            signal.metadata['volume_surges'] = len(vol_zones)
            
            # Store in memory
            self.memory.add_signal(signal)
            
            # Log signal
            logger.info(f"Signal generated for {self.symbol}: "
                       f"{signal.direction.upper()} @ {signal.entry_price} "
                       f"(Confidence: {signal.confidence})")
            
            # Notify if callback provided
            if self.signal_callback:
                await self.signal_callback(self.agent_id, signal)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signals for {self.symbol}: {e}")
            return None

    async def _is_repeating_mistake(self, signal: TradingSignal, df: pd.DataFrame) -> bool:
        """Heuristic check against known failure patterns"""
        if not self.knowledge['failed_patterns']:
            return False
            
        # Example logic: If we lost multiple times in a specific market structure
        # or near a specific OB type, block it.
        # This is a simplified implementation of "learning"
        current_structure = self.signal_generator.smc.determine_market_structure(df)
        
        for pattern in self.knowledge['failed_patterns']:
            if pattern.get('structure') == current_structure.value and \
               pattern.get('direction') == signal.direction:
                return True
        return False

    async def evolve(self):
        """Analyze past mistakes and update knowledge base"""
        if self.status == AgentStatus.EVOLVING:
            return
            
        prev_status = self.status
        self.status = AgentStatus.EVOLVING
        logger.info(f"Agent {self.agent_id} entering evolution phase...")
        
        try:
            mistakes = trade_history_manager.get_recent_mistakes(self.agent_id)
            if not mistakes:
                logger.info(f"Agent {self.agent_id} has no mistakes to learn from.")
                return

            new_patterns = []
            for m in mistakes[-5:]: # Analyze last 5 losses
                # In a real app, this would use LLM to summarize the context
                # Here we use technical metadata if available
                metadata = m.get('metadata', {})
                if metadata:
                    new_patterns.append({
                        'structure': metadata.get('market_structure'),
                        'direction': m.get('direction'),
                        'timestamp': datetime.utcnow().isoformat()
                    })
            
            self.knowledge['failed_patterns'] = new_patterns
            self.knowledge['last_evolution'] = datetime.utcnow().isoformat()
            logger.info(f"Agent {self.agent_id} evolution complete. Knowledge base updated.")
            
        except Exception as e:
            logger.error(f"Error during agent evolution: {e}")
        finally:
            self.status = prev_status
    
    async def _execute_signal(self, signal: TradingSignal):
        """Execute trade via ExecutionManager"""
        from .execution_manager import ExecutionManager
        execution_manager = ExecutionManager(self.mt5)
        await execution_manager.execute_signal(signal, self.agent_id)
        self.memory.add_trade({
            'signal': signal,
            'timestamp': datetime.utcnow(),
            'profit': 0  # Updated later
        })
    
    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            'agent_id': self.agent_id,
            'symbol': self.symbol,
            'status': self.status.value,
            'is_running': self.is_running,
            'daily_pnl': self.memory.daily_pnl,
            'daily_trades': self.memory.daily_trades,
            'recent_signals': len(self.memory.recent_signals),
            'autonomous_mode': self.autonomous_mode
        }


class AgentSwarm:
    """
    Factory and Manager for Multiple AI Agents
    Implements the Swarm Architecture
    """
    
    def __init__(self, mt5_client, config: Dict = None):
        self.mt5 = mt5_client
        self.config = config or {}
        self.agents: Dict[str, AIAgent] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=10)
        
    def create_agent(self, 
                     symbol: str, 
                     agent_id: Optional[str] = None,
                     agent_config: Optional[Dict] = None) -> AIAgent:
        """
        Factory method to create new agent instance
        
        Args:
            symbol: Trading symbol
            agent_id: Optional custom ID (default: auto-generated)
            agent_config: Optional agent-specific config
            
        Returns:
            AIAgent instance
        """
        with self._lock:
            if agent_id is None:
                agent_id = f"{symbol}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            if agent_id in self.agents:
                raise ValueError(f"Agent {agent_id} already exists")
            
            config = {**self.config, **(agent_config or {})}
            
            agent = AIAgent(
                symbol=symbol,
                agent_id=agent_id,
                mt5_client=self.mt5,
                config=config,
                signal_callback=self._on_signal
            )
            
            self.agents[agent_id] = agent
            logger.info(f"Created agent {agent_id} for {symbol}")
            return agent
    
    def remove_agent(self, agent_id: str):
        """Remove and stop an agent"""
        with self._lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                asyncio.create_task(agent.stop())
                del self.agents[agent_id]
                logger.info(f"Removed agent {agent_id}")
    
    async def start_all(self):
        """Start all agents in the swarm"""
        await asyncio.gather(*[agent.start() for agent in self.agents.values()])
    
    async def stop_all(self):
        """Stop all agents"""
        await asyncio.gather(*[agent.stop() for agent in self.agents.values()])
    
    def get_agent(self, agent_id: str) -> Optional[AIAgent]:
        """Get specific agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict]:
        """List all agents and their status"""
        return [agent.get_status() for agent in self.agents.values()]
    
    def get_swarm_stats(self) -> Dict:
        """Get aggregate statistics for entire swarm"""
        total_pnl = sum(a.memory.daily_pnl for a in self.agents.values())
        total_trades = sum(a.memory.daily_trades for a in self.agents.values())
        active_agents = sum(1 for a in self.agents.values() if a.is_running)
        
        return {
            'total_agents': len(self.agents),
            'active_agents': active_agents,
            'total_daily_pnl': total_pnl,
            'total_daily_trades': total_trades,
            'agents': self.list_agents()
        }
    
    async def _on_signal(self, agent_id: str, signal: TradingSignal):
        """Callback for when any agent generates a signal"""
        logger.info(f"Swarm received signal from {agent_id}: {signal.direction} {signal.symbol}")


# Singleton instance for application-wide access
_swarm_instance: Optional[AgentSwarm] = None

def get_swarm(mt5_client = None, config: Dict = None) -> AgentSwarm:
    """Get or create singleton swarm instance"""
    global _swarm_instance
    if _swarm_instance is None:
        # Avoid circular imports by importing settings only if needed
        from ..config import settings
        from ..mt5_client import MT5Client
        
        cfg = config or (settings.model_dump() if hasattr(settings, 'model_dump') else settings.dict() if hasattr(settings, 'dict') else dict(settings))
        mt5 = mt5_client or MT5Client(cfg)
        _swarm_instance = AgentSwarm(mt5, cfg)
        
    return _swarm_instance

def get_agent() -> AgentSwarm:
    """Compatibility alias for get_swarm to match main.py"""
    return get_swarm()
