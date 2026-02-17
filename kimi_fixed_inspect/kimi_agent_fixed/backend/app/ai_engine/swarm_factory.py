"""
Swarm Factory - Multi-Agent Orchestration
Manages independent agents for different symbols
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .agent import AIAgent
from ..mt5.mt5_client import MT5Client

logger = logging.getLogger(__name__)


class SwarmFactory:
    """
    Factory for creating and managing multiple independent AI agents
    Each agent trades a different symbol autonomously
    """
    
    def __init__(self, mt5_client: MT5Client, config: Dict = None):
        self.mt5_client = mt5_client
        self.config = config or {}
        
        # Active agents registry
        self.agents: Dict[str, AIAgent] = {}
        
        # Swarm configuration
        self.max_agents = self.config.get('max_agents', 10)
        
        logger.info(f"SwarmFactory initialized (max agents: {self.max_agents})")
    
    async def create_agent(self, symbol: str, agent_config: Dict = None) -> Optional[AIAgent]:
        """
        Create and start a new trading agent for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            agent_config: Agent-specific configuration
        
        Returns:
            AIAgent instance or None if creation failed
        """
        try:
            # Check if agent already exists
            if symbol in self.agents:
                logger.warning(f"Agent for {symbol} already exists")
                return self.agents[symbol]
            
            # Check max agents limit
            if len(self.agents) >= self.max_agents:
                logger.error(f"Cannot create agent: max agents limit ({self.max_agents}) reached")
                return None
            
            # Create agent
            logger.info(f"Creating new agent for {symbol}")
            
            agent = AIAgent(
                symbol=symbol,
                mt5_client=self.mt5_client,
                config=agent_config or self.config.get('default_agent_config', {})
            )
            
            # Start agent
            await agent.start()
            
            # Register agent
            self.agents[symbol] = agent
            
            logger.info(f"✅ Agent created and started for {symbol}")
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent for {symbol}: {e}", exc_info=True)
            return None
    
    async def stop_agent(self, symbol: str) -> bool:
        """
        Stop and remove an agent
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if symbol not in self.agents:
                logger.warning(f"No agent found for {symbol}")
                return False
            
            logger.info(f"Stopping agent for {symbol}")
            
            agent = self.agents[symbol]
            await agent.stop()
            
            # Remove from registry
            del self.agents[symbol]
            
            logger.info(f"✅ Agent stopped for {symbol}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping agent for {symbol}: {e}", exc_info=True)
            return False
    
    async def stop_all_agents(self):
        """Stop all running agents"""
        logger.info("Stopping all agents...")
        
        # Stop all agents concurrently
        stop_tasks = [
            self.stop_agent(symbol) 
            for symbol in list(self.agents.keys())
        ]
        
        await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        logger.info("All agents stopped")
    
    def get_agent(self, symbol: str) -> Optional[AIAgent]:
        """Get agent for a specific symbol"""
        return self.agents.get(symbol)
    
    def get_all_agents(self) -> List[AIAgent]:
        """Get list of all active agents"""
        return list(self.agents.values())
    
    def get_agent_status(self, symbol: str) -> Optional[Dict]:
        """Get status of a specific agent"""
        agent = self.agents.get(symbol)
        if agent:
            return agent.get_status()
        return None
    
    def get_swarm_status(self) -> Dict:
        """
        Get overall swarm status
        
        Returns:
            Dict with swarm metrics and agent statuses
        """
        agent_statuses = {
            symbol: agent.get_status() 
            for symbol, agent in self.agents.items()
        }
        
        # Aggregate metrics
        total_positions = sum(
            status['open_positions'] 
            for status in agent_statuses.values()
        )
        
        total_daily_trades = sum(
            status['daily_trades'] 
            for status in agent_statuses.values()
        )
        
        total_pnl = sum(
            status['total_pnl'] 
            for status in agent_statuses.values()
        )
        
        any_circuit_breaker = any(
            status['circuit_breaker_active'] 
            for status in agent_statuses.values()
        )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_agents': len(self.agents),
            'active_agents': sum(1 for a in agent_statuses.values() if a['is_active']),
            'total_open_positions': total_positions,
            'total_daily_trades': total_daily_trades,
            'total_pnl': total_pnl,
            'circuit_breaker_active': any_circuit_breaker,
            'agents': agent_statuses
        }
    
    async def create_default_swarm(self, symbols: List[str]) -> List[AIAgent]:
        """
        Create a swarm of agents for multiple symbols
        
        Args:
            symbols: List of trading symbols
        
        Returns:
            List of created agents
        """
        logger.info(f"Creating default swarm for {len(symbols)} symbols")
        
        # Create all agents concurrently
        create_tasks = [
            self.create_agent(symbol) 
            for symbol in symbols
        ]
        
        agents = await asyncio.gather(*create_tasks, return_exceptions=True)
        
        # Filter out failed creations
        successful_agents = [
            agent for agent in agents 
            if isinstance(agent, AIAgent)
        ]
        
        logger.info(
            f"✅ Created {len(successful_agents)}/{len(symbols)} agents successfully"
        )
        
        return successful_agents
    
    async def restart_agent(self, symbol: str) -> bool:
        """
        Restart an agent (stop and start)
        
        Returns:
            True if restarted successfully
        """
        try:
            logger.info(f"Restarting agent for {symbol}")
            
            # Get current config
            agent = self.agents.get(symbol)
            if not agent:
                logger.warning(f"No agent found for {symbol}")
                return False
            
            agent_config = agent.config
            
            # Stop existing agent
            await self.stop_agent(symbol)
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # Create new agent
            new_agent = await self.create_agent(symbol, agent_config)
            
            return new_agent is not None
            
        except Exception as e:
            logger.error(f"Error restarting agent for {symbol}: {e}", exc_info=True)
            return False
    
    async def emergency_stop_all(self):
        """
        Emergency stop - close all positions and stop all agents
        """
        logger.critical("🚨 EMERGENCY STOP ACTIVATED")
        
        try:
            # 1. Close all open positions
            for symbol, agent in self.agents.items():
                logger.info(f"Closing positions for {symbol}")
                
                # Get open positions
                positions = await self.mt5_client.get_open_positions(symbol)
                
                # Close all positions
                for position in positions:
                    await self.mt5_client.close_position(position['ticket'])
            
            # 2. Stop all agents
            await self.stop_all_agents()
            
            logger.critical("🚨 Emergency stop completed")
            
        except Exception as e:
            logger.critical(f"Error during emergency stop: {e}", exc_info=True)
