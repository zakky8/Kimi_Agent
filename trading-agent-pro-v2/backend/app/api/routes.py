"""
Control Panel API Routes for Multi-Agent Management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio

from ..ai_engine.agent import get_swarm, AIAgent, AgentStatus
from ..mt5_client import MT5Client
from ..config import settings # Assuming settings from config.py

router = APIRouter(tags=["control_panel"])

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
    swarm = get_swarm_instance()
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
    swarm = get_swarm_instance()
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
    swarm = get_swarm_instance()
    return swarm.list_agents()

@router.get("/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get detailed status of specific agent"""
    swarm = get_swarm_instance()
    agent = swarm.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get_status()

@router.patch("/agents/{agent_id}/config")
async def update_agent_config(agent_id: str, config: AgentConfigUpdate):
    """Update agent configuration dynamically"""
    swarm = get_swarm_instance()
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
    swarm = get_swarm_instance()
    return swarm.get_swarm_stats()

@router.post("/swarm/stop-all")
async def stop_all_agents():
    """Emergency stop all agents"""
    swarm = get_swarm_instance()
    await swarm.stop_all()
    return {"success": True, "message": "All agents stopped"}

@router.post("/swarm/emergency-shutdown")
async def emergency_shutdown():
    """Emergency shutdown: Close all positions and stop all agents"""
    swarm = get_swarm_instance()
    mt5 = swarm.mt5
    
    positions = await mt5.get_positions()
    closed = 0
    for pos in positions:
        result = await mt5.close_position(pos['ticket'])
        if result['success']: closed += 1
    
    await swarm.stop_all()
    
    return {
        "success": True,
        "message": "Emergency shutdown completed",
        "positions_closed": closed
    }

# Health Check
@router.get("/health")
async def system_health():
    swarm = get_swarm_instance()
    return {
        "status": "operational",
        "mt5_connected": swarm.mt5.connected if swarm and swarm.mt5 else False,
        "active_agents": len(swarm.agents) if swarm else 0
    }
