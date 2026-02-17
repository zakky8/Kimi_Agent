"""
WebSocket Server for AI Trading Agent
Handled real-time updates and command processing
"""
import asyncio
import logging
import json
from typing import Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._running = False
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
            
        data = json.dumps(message)
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.add(connection)
                
        for conn in disconnected:
            self.disconnect(conn)

    async def start(self):
        self._running = True
        logger.info("WebSocket infrastructure initialized")

    async def stop(self):
        self._running = False
        for connection in list(self.active_connections):
            await connection.close()
        self.active_connections.clear()
        logger.info("WebSocket server stopped")

_ws_instance = WebSocketServer()

def get_websocket_server() -> WebSocketServer:
    """Get the global WebSocket server instance"""
    return _ws_instance
