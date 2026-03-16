from __future__ import annotations

import asyncio
import base64
import logging
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import torch
from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_pipeline import GuardianizeModel
from database import SessionLocal, engine, get_db
from models import AlertLog, Base, User


LOGGER = logging.getLogger("guardianize")
BASE_DIR = Path(__file__).resolve().parent
SEQUENCE_LENGTH = 16
FRAME_SIZE = (224, 224)
ANOMALY_KEYWORDS = {
    "rough",
    "abusive",
    "harsh",
    "beaten",
    "edge",
    "sharp",
    "electrical",
    "hazard",
}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    Base.metadata.create_all(bind=engine)
    app.state.guardian_model = GuardianizeModel()
    app.state.monitor_clients = set()
    yield


app = FastAPI(title="Guardianize", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("settings.html", {"request": request})


@app.post("/api/login")
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> JSONResponse:
    user = db.scalar(select(User).where(User.username == payload.email))
    if user is None:
        user = User(username=payload.email, hashed_password=payload.password)
        db.add(user)
        db.commit()
        db.refresh(user)

    return JSONResponse({"ok": True, "user": {"id": user.id, "username": user.username}})


@app.post("/login")
async def login_legacy(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.scalar(select(User).where(User.username == payload.email))
    if user is None:
        user = User(username=payload.email, hashed_password=payload.password)
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"status": "success", "message": "Authenticated. Connecting WebSocket feed."}


@app.get("/api/alerts/history")
async def alert_history(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(AlertLog).order_by(AlertLog.timestamp.desc()).limit(100)).all()
    return [serialize_alert(row) for row in rows]


@app.websocket("/ws/monitor")
async def monitor_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    app.state.monitor_clients.add(websocket)
    frame_buffer: deque[np.ndarray] = deque(maxlen=SEQUENCE_LENGTH)
    inference_lock = asyncio.Lock()

    try:
        await websocket.send_json({"event": "status", "message": "connected"})
        while True:
            payload = await websocket.receive_json()
            frame_data = payload.get("frame") or payload.get("data")
            if payload.get("type") not in {None, "frame"} or not frame_data:
                continue

            frame = decode_base64_frame(frame_data)
            frame_buffer.append(frame)

            if len(frame_buffer) == SEQUENCE_LENGTH and not inference_lock.locked():
                window = list(frame_buffer)
                asyncio.create_task(run_inference_window(window, inference_lock))
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        LOGGER.exception("WebSocket monitor failure: %s", exc)
    finally:
        app.state.monitor_clients.discard(websocket)


async def run_inference_window(frames: list[np.ndarray], inference_lock: asyncio.Lock) -> None:
    async with inference_lock:
        video_tensor = frames_to_tensor(frames)
        prediction = await asyncio.to_thread(app.state.guardian_model.inference, video_tensor)
        if not is_anomaly_prediction(prediction):
            return

        alert = await asyncio.to_thread(save_alert_record, prediction)
        await broadcast_json(alert)


def decode_base64_frame(data_url: str) -> np.ndarray:
    encoded = data_url.split(",", 1)[1] if "," in data_url else data_url
    image_bytes = base64.b64decode(encoded)
    with Image.open(BytesIO(image_bytes)) as image:
        frame = image.convert("RGB").resize(FRAME_SIZE)
        return np.asarray(frame, dtype=np.uint8)


def frames_to_tensor(frames: list[np.ndarray]) -> torch.Tensor:
    np_frames = np.stack(frames).astype(np.float32) / 255.0
    tensor = torch.from_numpy(np_frames).permute(3, 0, 1, 2).unsqueeze(0)
    return tensor.contiguous()


def build_alert_message(prediction: str) -> str:
    normalized = prediction.strip().lower()
    if "rough" in normalized or "harsh" in normalized or "abusive" in normalized or "beaten" in normalized:
        return f"Potential mistreatment detected: {prediction}."
    if "edge" in normalized or "sharp" in normalized or "electrical" in normalized or "hazard" in normalized:
        return f"Potential environmental hazard detected: {prediction}."
    return f"Anomalous event detected: {prediction}."


def is_anomaly_prediction(prediction: str) -> bool:
    normalized = prediction.strip().lower()
    return any(keyword in normalized for keyword in ANOMALY_KEYWORDS)


def save_alert_record(prediction: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        alert = AlertLog(alert_type=prediction, message=build_alert_message(prediction))
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return serialize_alert(alert)
    finally:
        db.close()


def serialize_alert(alert: AlertLog) -> dict[str, Any]:
    normalized = alert.alert_type.strip().lower()
    severity = "critical" if any(tag in normalized for tag in ("beaten", "sharp", "edge", "electrical", "hazard")) else "warning"
    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "message": alert.message,
        "severity": severity,
        "type": severity,
        "target": "baby",
        "model_source": "3D CNN",
        "timestamp": alert.timestamp.isoformat(timespec="seconds") if isinstance(alert.timestamp, datetime) else str(alert.timestamp),
    }


async def broadcast_json(payload: dict[str, Any]) -> None:
    stale_clients: list[WebSocket] = []
    for client in list(app.state.monitor_clients):
        try:
            await client.send_json(payload)
        except Exception:
            stale_clients.append(client)

    for client in stale_clients:
        app.state.monitor_clients.discard(client)
