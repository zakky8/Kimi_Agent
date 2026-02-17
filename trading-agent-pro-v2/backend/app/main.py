"""
Main Application Entry Point with Gold Standard Lifespan
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes
from .core.scheduler import get_scheduler
from .mt5_client import MT5Client
from .config import settings  # Path based on existing structure

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    mt5 = MT5Client(settings) # Using settings from config.py
    
    # Connect to MT5
    connected = await mt5.connect()
    if not connected:
        logging.error("Failed to connect to MT5 on startup")
    
    # Initialize swarm
    from .ai_engine.agent import get_swarm
    swarm = get_swarm(mt5, settings)
    
    # Start scheduler
    scheduler = get_scheduler(mt5)
    await scheduler.start()
    
    logging.info("Application startup complete (Gold Standard)")
    
    yield
    
    # Shutdown
    logging.info("Shutting down...")
    await scheduler.stop()
    await swarm.stop_all()
    await mt5.disconnect()

app = FastAPI(
    title="AI Trading Agent System",
    description="Multi-Agent Autonomous Trading Platform (Gold Standard)",
    version="2.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
# Include routes with version prefix
app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "AI Trading Agent System v2.1 (Gold Standard)",
        "status": "operational",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
