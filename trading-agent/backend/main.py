"""
Main Application Entry Point
AI Trading Agent Pro - Free Data Sources Edition
"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from app.api.routes import router
from app.websocket.server import get_websocket_server

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


# WebSocket server instance
ws_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize AI client
    try:
        from app.ai_providers import get_ai_client
        ai_client = get_ai_client()
        logger.info(f"AI client initialized with provider: {settings.DEFAULT_AI_PROVIDER}")
    except Exception as e:
        logger.warning(f"AI client initialization failed: {e}")
    
    # Initialize chat engine
    try:
        from app.ai_providers import get_chat_engine
        chat_engine = await get_chat_engine()
        logger.info("Chat engine initialized")
    except Exception as e:
        logger.warning(f"Chat engine initialization failed: {e}")
    
    # Start WebSocket server
    global ws_server
    ws_server = get_websocket_server()
    await ws_server.start()
    
    # Initialize MT5 if enabled
    if settings.MT5_ENABLED:
        try:
            from app.data_collection import get_mt5_client
            mt5 = get_mt5_client()
            if mt5.initialize():
                logger.info("MT5 initialized successfully")
                mt5.shutdown()
            else:
                logger.warning("MT5 initialization failed")
        except Exception as e:
            logger.warning(f"MT5 initialization error: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if ws_server:
        await ws_server.stop()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Institutional-grade AI trading agent using free data sources with multi-provider AI support",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

# Static files for uploads
import os
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1",
        "features": [
            "multi-provider-ai",
            "binance-integration",
            "telegram-data",
            "mt5-desktop",
            "rss-feeds",
            "chat-system",
            "image-analysis",
            "browser-research"
        ]
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
    main()
