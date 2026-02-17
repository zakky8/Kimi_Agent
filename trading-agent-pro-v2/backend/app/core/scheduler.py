"""
Background Task Scheduler for 24/7 Monitoring
Handles connection persistence and auto-restart
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from playwright.async_api import async_playwright
import subprocess
import sys

from ..ai_engine.agent import get_swarm, AgentStatus

logger = logging.getLogger(__name__)

class SystemScheduler:
    """Manages background tasks and system maintenance"""
    
    def __init__(self, mt5_client):
        self.mt5 = mt5_client
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    async def start(self):
        """Start the scheduler with all jobs"""
        if self.is_running:
            return
        
        # Install Playwright if needed
        await self._ensure_playwright()
        
        # Schedule jobs
        self.scheduler.add_job(
            self._heartbeat_check,
            IntervalTrigger(seconds=30),
            id='heartbeat',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self._reconnect_mt5,
            IntervalTrigger(minutes=5),
            id='mt5_reconnect',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("System scheduler started")
    
    async def stop(self):
        """Stop all scheduled jobs"""
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("System scheduler stopped")
    
    async def _ensure_playwright(self):
        """Auto-install Playwright browsers"""
        try:
            async with async_playwright() as p:
                # Basic check if it can launch
                pass
            logger.info("Playwright Chromium check passed")
        except Exception:
            logger.info("Installing Playwright Chromium...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    check=True,
                    capture_output=True
                )
                logger.info("Playwright Chromium installed successfully")
            except Exception as e:
                logger.error(f"Failed to install Playwright: {e}")
    
    async def _heartbeat_check(self):
        """Check all agents are alive"""
        swarm = get_swarm()
        if not swarm:
            return
        
        for agent_id, agent in swarm.agents.items():
            if agent.is_running and agent.status == AgentStatus.ERROR:
                logger.warning(f"Agent {agent_id} in error state, attempting restart...")
                await agent.stop()
                await asyncio.sleep(2)
                await agent.start()
    
    async def _reconnect_mt5(self):
        """Ensure MT5 connection is alive"""
        if not self.mt5.connected:
            logger.warning("MT5 disconnected, attempting reconnect...")
            await self.mt5.connect()

    async def _evolve_agents(self):
        """Trigger evolution cycle for all active agents"""
        swarm = get_swarm()
        if not swarm:
            return
            
        logger.info("Starting global agent evolution cycle...")
        for agent_id, agent in swarm.agents.items():
            if agent.is_running:
                await agent.evolve()


# Global instance
_scheduler_instance = None

def get_scheduler(mt5_client = None) -> SystemScheduler:
    """Get or create scheduler singleton"""
    global _scheduler_instance
    if _scheduler_instance is None and mt5_client is not None:
        _scheduler_instance = SystemScheduler(mt5_client)
    return _scheduler_instance
