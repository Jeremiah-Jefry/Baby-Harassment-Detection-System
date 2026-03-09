import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import json

from socket_manager.manager import manager
from core.logging_config import logger

router = APIRouter()

# Global async queues for media chunks
video_queue = asyncio.Queue(maxsize=100)
audio_queue = asyncio.Queue(maxsize=100)

@router.get("/health")
async def health_check():
    """Enterprise REST health endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.websocket("/ws/media")
async def websocket_media(websocket: WebSocket):
    """
    WebSocket route for receiving live video/audio streams from the client.
    Clients push frames to be processed non-blockingly via asyncio queues.
    """
    room = "media"
    await manager.connect(websocket, room)
    try:
        while True:
            # We expect JSON blobs containing base64 data:
            # { "type": "video_frame", "data": "data:image/jpeg;base64,..." }
            # { "type": "audio_chunk", "data": "base64..." }
            message = await websocket.receive_text()
            
            # Fast ping-pong check
            if message == "ping":
                await websocket.send_text("pong")
                continue
                
            try:
                payload = json.loads(message)
                mtype = payload.get("type")
                mdata = payload.get("data")
                
                if mtype == "video_frame" and mdata:
                    if not video_queue.full():
                        await video_queue.put(mdata)
                elif mtype == "audio_chunk" and mdata:
                    if not audio_queue.full():
                        await audio_queue.put(mdata)
            except json.JSONDecodeError:
                pass # ignore malformed frames
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.error(f"Media WS Error: {e}")
        manager.disconnect(websocket, room)

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket route dedicated strictly to pushing AI real-time alerts.
    The AI background tasks push alerts to the 'alerts' room via the manager.
    """
    room = "alerts"
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.error(f"Alerts WS Error: {e}")
        manager.disconnect(websocket, room)
