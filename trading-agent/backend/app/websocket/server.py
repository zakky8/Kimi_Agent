"""
WebSocket Server
Handles real-time data streaming
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

from ..config import settings
from ..data_collection.market_data import MarketDataCollector

logger = logging.getLogger(__name__)


class WebSocketServer:
    """
    WebSocket server for real-time trading data
    Streams prices, signals, and sentiment updates
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.subscriptions: Dict[str, Set[WebSocketServerProtocol]] = {
            "prices": set(),
            "signals": set(),
            "sentiment": set(),
            "news": set(),
            "all": set()
        }
        self.running = False
        self.tasks = []
        
    async def register(self, websocket: WebSocketServerProtocol):
        """Register new client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
    async def unregister(self, websocket: WebSocketServerProtocol):
        """Unregister client"""
        self.clients.discard(websocket)
        for sub in self.subscriptions.values():
            sub.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle client connection"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def process_message(self, websocket: WebSocketServerProtocol, message: str):
        """Process incoming client message"""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                channel = data.get("channel", "all")
                if channel in self.subscriptions:
                    self.subscriptions[channel].add(websocket)
                    await websocket.send(json.dumps({
                        "type": "subscription",
                        "channel": channel,
                        "status": "subscribed"
                    }))
                    
            elif action == "unsubscribe":
                channel = data.get("channel", "all")
                if channel in self.subscriptions:
                    self.subscriptions[channel].discard(websocket)
                    await websocket.send(json.dumps({
                        "type": "subscription",
                        "channel": channel,
                        "status": "unsubscribed"
                    }))
                    
            elif action == "get_price":
                symbol = data.get("symbol")
                if symbol:
                    price_data = await self.fetch_price(symbol)
                    await websocket.send(json.dumps({
                        "type": "price",
                        "data": price_data
                    }))
                    
            elif action == "ping":
                await websocket.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
    
    async def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch current price for a symbol"""
        try:
            async with MarketDataCollector() as collector:
                data = await collector.get_ticker_24h(symbol.upper())
                return {
                    "symbol": symbol.upper(),
                    **data
                }
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return {"error": str(e)}
    
    async def broadcast_prices(self):
        """Broadcast price updates to subscribed clients"""
        while self.running:
            try:
                if self.subscriptions["prices"] or self.subscriptions["all"]:
                    # Fetch prices for default pairs
                    async with MarketDataCollector() as collector:
                        prices = await collector.get_multiple_prices(
                            settings.DEFAULT_PAIRS[:10]  # Limit to first 10
                        )
                    
                    message = json.dumps({
                        "type": "prices",
                        "data": prices,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Broadcast to subscribers
                    targets = self.subscriptions["prices"] | self.subscriptions["all"]
                    if targets:
                        await asyncio.gather(
                            *[client.send(message) for client in targets if client.open],
                            return_exceptions=True
                        )
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting prices: {e}")
                await asyncio.sleep(5)
    
    async def broadcast_signals(self):
        """Broadcast signal updates"""
        while self.running:
            try:
                if self.subscriptions["signals"] or self.subscriptions["all"]:
                    from ..signals import SignalGenerator
                    
                    generator = SignalGenerator()
                    summary = generator.get_signal_summary()
                    
                    message = json.dumps({
                        "type": "signals",
                        "data": summary,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    targets = self.subscriptions["signals"] | self.subscriptions["all"]
                    if targets:
                        await asyncio.gather(
                            *[client.send(message) for client in targets if client.open],
                            return_exceptions=True
                        )
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting signals: {e}")
                await asyncio.sleep(30)
    
    async def broadcast_sentiment(self):
        """Broadcast sentiment updates"""
        while self.running:
            try:
                if self.subscriptions["sentiment"] or self.subscriptions["all"]:
                    from ..data_collection import WebScraper
                    
                    async with WebScraper() as scraper:
                        fear_greed = await scraper.get_fear_greed_index()
                    
                    message = json.dumps({
                        "type": "sentiment",
                        "data": {
                            "fear_greed": fear_greed,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                    
                    targets = self.subscriptions["sentiment"] | self.subscriptions["all"]
                    if targets:
                        await asyncio.gather(
                            *[client.send(message) for client in targets if client.open],
                            return_exceptions=True
                        )
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error broadcasting sentiment: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start WebSocket server"""
        self.running = True
        
        # Start broadcast tasks
        self.tasks = [
            asyncio.create_task(self.broadcast_prices()),
            asyncio.create_task(self.broadcast_signals()),
            asyncio.create_task(self.broadcast_sentiment())
        ]
        
        # Start server
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        
        return server
    
    async def stop(self):
        """Stop WebSocket server"""
        self.running = False
        
        # Cancel broadcast tasks
        for task in self.tasks:
            task.cancel()
        
        # Close all client connections
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )
        
        logger.info("WebSocket server stopped")


# Global server instance
_ws_server: Optional[WebSocketServer] = None


def get_websocket_server() -> WebSocketServer:
    """Get or create WebSocket server singleton"""
    global _ws_server
    if _ws_server is None:
        _ws_server = WebSocketServer(
            host=settings.HOST,
            port=settings.WEBSOCKET_PORT
        )
    return _ws_server
