import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import json

from socket_manager.manager import manager
from core.logging_config import logger
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import models

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
    }

@router.get("/api/alerts/history")
async def get_alerts_history(db: Session = Depends(get_db)):
    """Fetch the last 50 alerts from SQLite database on dashboard load."""
    alerts = db.query(models.AlertLog).order_by(models.AlertLog.timestamp.desc()).limit(50).all()
    # Correctly format it back into the schema structure expected by the JS frontend
    return [
        {
            "id": a.id,
            "type": a.severity,
            "message": a.message,
            "target": a.alert_type,
            "confidence": a.confidence,
            "model_source": a.model_source,
            "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for a in reversed(alerts)  # oldest to newest order
    ]

@router.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    Unified WebSocket route for full-duplex communication.
    Receives base64 video/audio streams and pushes AI alerts.
    """
    room = "alerts" # Subscribe to AI alert broadcasts
    await manager.connect(websocket, room)
    try:
        while True:
            # We expect JSON blobs: { "type": "video_frame", "data": "..." }
            message = await websocket.receive_text()
            
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
                pass # safely ignore
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.error(f"Monitor WS Error: {e}")
        manager.disconnect(websocket, room)
