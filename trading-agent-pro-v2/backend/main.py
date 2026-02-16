"""
AI Trading Agent Pro v2 - Main Entry Point
High-End Automated Trading System with Full System Control
"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.api.routes import router
from app.websocket.server import get_websocket_server
from app.ai_engine.agent import get_agent

# Configure logging
Path("./logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)


# Global instances
ws_server = None
ai_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ws_server, ai_agent
    
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize AI Agent
    ai_agent = get_agent()
    logger.info("✅ AI Agent initialized")
    
    # Start WebSocket server
    ws_server = get_websocket_server()
    await ws_server.start()
    logger.info("✅ WebSocket server started")
    
    # Create data directories
    Path("./data").mkdir(exist_ok=True)
    Path("./data/uploads").mkdir(exist_ok=True)
    Path("./data/cache").mkdir(exist_ok=True)
    
    logger.info("✅ Application ready")
    logger.info(f"📊 Monitoring {len(settings.DEFAULT_PAIRS)} trading pairs")
    logger.info(f"🤖 AI Providers: {list(ai_agent.clients.keys())}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    
    if ws_server:
        await ws_server.stop()
    
    # Stop AI agent if monitoring
    if ai_agent and ai_agent.state.value == "monitoring":
        await ai_agent.process_command(type(ai_agent).CommandType.STOP)
    
    logger.info("👋 Goodbye!")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="High-End AI Trading Agent with Full System Control",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory="./data/uploads"), name="uploads")

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1",
        "websocket": f"ws://{settings.HOST}:{settings.WEBSOCKET_PORT}"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_state": ai_agent.state.value if ai_agent else "unknown"
    }


def main():
    """Main entry point"""
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    from datetime import datetime
    main()
