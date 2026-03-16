from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from model.model_3dcnn import Simple3DCNN

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional dependency during early setup
    YOLO = None


LOGGER = logging.getLogger("guardianize.ai")


class GuardianizeModel:
    HAZARD_KEYWORDS = {"knife", "fire", "smoke", "scissors", "glass", "weapon"}

    def __init__(self, weights_path: str | Path | None = None, device: str | None = None) -> None:
        self.weights_path = self._resolve_weights_path(weights_path)
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.labels = ["Safe", "Rough Handling", "Hazard"]
        self.temporal_model: nn.Module | None = None
        self.checkpoint: dict[str, Any] | None = None
        self.yolo_model = None
        self.model_ready = False
        self._load_models()

    @staticmethod
    def _resolve_weights_path(explicit_path: str | Path | None) -> Path:
        if explicit_path is not None:
            return Path(explicit_path)

        base_dir = Path(__file__).resolve().parent
        candidates = [
            base_dir / "model" / "checkpoints" / "best_model.pt",
            base_dir / "model" / "checkpoints" / "final_model.pt",
            base_dir / "Model" / "best.pt",
            base_dir / "model" / "best.pt",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _build_temporal_model(self, num_classes: int) -> nn.Module:
        return Simple3DCNN(num_classes=num_classes)

    def _load_models(self) -> None:
        try:
            self.checkpoint = torch.load(str(self.weights_path), map_location=self.device)
            LOGGER.info("Loaded checkpoint from %s", self.weights_path)
        except FileNotFoundError:
            LOGGER.warning("Checkpoint not found at %s. Guardianize will run in heuristic fallback mode.", self.weights_path)
            return
        except Exception as exc:
            LOGGER.exception("Unable to load checkpoint: %s", exc)
            return

        label_mapping = self.checkpoint.get("idx2label") if isinstance(self.checkpoint, dict) else None
        if isinstance(label_mapping, dict) and label_mapping:
            ordered_indices = sorted(label_mapping.keys(), key=int)
            self.labels = [str(label_mapping[index]) for index in ordered_indices]

        state_dict = self._extract_state_dict(self.checkpoint)
        if state_dict:
            try:
                self.temporal_model = self._build_temporal_model(num_classes=len(self.labels)).to(self.device)
                self.temporal_model.load_state_dict(state_dict, strict=False)
                self.temporal_model.eval()
                self.model_ready = True
            except Exception as exc:
                LOGGER.warning("3D CNN weights could not be applied cleanly: %s", exc)

        if YOLO is not None:
            try:
                self.yolo_model = YOLO(str(self.weights_path))
            except Exception as exc:
                LOGGER.warning("YOLOv8 weights could not be initialized from %s: %s", self.weights_path, exc)

    @staticmethod
    def _extract_state_dict(checkpoint: Any) -> dict[str, torch.Tensor] | None:
        if isinstance(checkpoint, dict):
            for key in ("state_dict", "model_state_dict", "model"):
                value = checkpoint.get(key)
                if isinstance(value, dict):
                    return value
            if all(isinstance(value, torch.Tensor) for value in checkpoint.values()):
                return checkpoint
        return None

    def inference(self, video_tensor: torch.Tensor) -> str:
        """
        Run Guardianize inference.

        Args:
            video_tensor: Tensor with shape (batch, channels, frames, height, width)
        """
        if video_tensor.ndim != 5:
            raise ValueError("Expected input tensor in (B, C, T, H, W) format.")

        prepared = video_tensor.to(self.device, dtype=torch.float32)
        yolo_prediction = self._predict_hazard_with_yolo(prepared)
        if yolo_prediction != "Safe":
            return yolo_prediction

        if self.model_ready and self.temporal_model is not None:
            with torch.inference_mode():
                logits = self.temporal_model(prepared)
                predicted_index = int(torch.argmax(logits, dim=1).item())
            if 0 <= predicted_index < len(self.labels):
                return self.labels[predicted_index]
            return "Safe"

        return self._heuristic_prediction(prepared)

    def _predict_hazard_with_yolo(self, video_tensor: torch.Tensor) -> str:
        if self.yolo_model is None:
            return "Safe"

        middle_frame = video_tensor[0, :, video_tensor.shape[2] // 2].detach().cpu()
        image = middle_frame.permute(1, 2, 0).clamp(0, 1).numpy()
        image_uint8 = (image * 255.0).astype(np.uint8)

        try:
            results = self.yolo_model.predict(source=image_uint8, verbose=False)
        except Exception as exc:
            LOGGER.warning("YOLO inference failed: %s", exc)
            return "Safe"

        for result in results:
            names = getattr(result, "names", {})
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for class_index in boxes.cls.tolist():
                label = str(names.get(int(class_index), "")).lower()
                if label in self.HAZARD_KEYWORDS:
                    return "Hazard"
        return "Safe"

    def _heuristic_prediction(self, video_tensor: torch.Tensor) -> str:
        motion_score = float(torch.mean(torch.abs(video_tensor[:, :, 1:] - video_tensor[:, :, :-1])).item())
        brightness = float(video_tensor.mean().item())

        if motion_score > 0.24:
            return "Rough Handling"
        if brightness < 0.14:
            return "Hazard"
        return "Safe"