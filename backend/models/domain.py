from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class BaseEvent(BaseModel):
    model_config = {"protected_namespaces": ()}
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class AlertEvent(BaseEvent):
    """
    Domain entity representing an AI inference alert.
    """
    type: Literal["danger", "warning", "info", "critical", "urgent", "alert"]
    message: str
    target: Literal["baby", "babysitter"]
    confidence: float
    model_source: str

class VideoFrameEvent(BaseEvent):
    """
    Domain entity representing a frame telemetry event.
    """
    type: Literal["video_frame"] = "video_frame"
    content: str  # Simulated content for now, later base64.
