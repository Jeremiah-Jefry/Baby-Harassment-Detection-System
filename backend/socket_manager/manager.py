from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
from core.logging_config import logger

class ConnectionManager:
    """
    Robust WebSocket Connection Manager handling rooms and targeted broadcasts.
    """
    def __init__(self):
        # Maps room names (e.g. "video", "alerts") to a set of active connections
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "video": set(),
            "alerts": set()
        }

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = set()
        self.active_connections[room].add(websocket)
        logger.info(f"Client connected to room: {room}. Total: {len(self.active_connections[room])}")

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)
            logger.info(f"Client disconnected from room: {room}. Total: {len(self.active_connections[room])}")

    async def broadcast(self, message: str, room: str):
        if room not in self.active_connections:
            return
            
        disconnected = set()
        for connection in self.active_connections[room]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to client in {room}: {e}")
                disconnected.add(connection)
                
        # Clean up any dead connections we discovered during broadcast
        for conn in disconnected:
            self.disconnect(conn, room)

# Global unified connection manager
manager = ConnectionManager()
