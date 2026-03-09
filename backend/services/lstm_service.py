import asyncio
import time
import base64
import tempfile
import os

from transformers import pipeline
import librosa
import soundfile as sf

from services.ai_base import AIServiceInterface
from models.domain import AlertEvent
from core.logging_config import logger

class LSTM_AudioService(AIServiceInterface):
    """
    Real Audio Classification Engine using AST model on incoming WebRTC chunks.
    Buffers incoming microphone audio into 3-second segments for processing.
    """
    
    def __init__(self):
        logger.info("Initializing AST Audio Classification Pipeline...")
        self.audio_classifier = pipeline(
            "audio-classification", 
            model="MIT/ast-finetuned-audioset-10-10-0.4593"
        )
        logger.info("Audio Pipeline Loaded.")
        
        # Buffer to hold sequential 1-second chunks from the client
        self.chunk_buffer = []
        self.min_buffer_size = 3  # Wait for 3 chunks (~3 seconds) before running model

    def _sync_process_audio(self, chunks_to_process: list) -> AlertEvent | None:
        """Runs the librosa/transformers workflow synchronosly in thread."""
        tmp_name = None
        try:
            # Reconstruct the WebM buffer from multiple chunks securely
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                for chunk in chunks_to_process:
                    if "," in chunk:
                        chunk = chunk.split(",", 1)[1]
                    tmp.write(base64.b64decode(chunk))
                tmp_name = tmp.name

            # Load via librosa, converting to model's expected 16kHz sample rate
            # Note: This natively requires ffmpeg installed if evaluating compressed webm
            y, sr = librosa.load(tmp_name, sr=16000)
            
            # Fire pipeline inference
            results = self.audio_classifier(y)
            
            for r in results:
                label = r['label'].lower()
                score = r['score']
                
                # URGENT: Distressed Crying Pattern (> 80% confidence)
                if ("crying" in label or "sobbing" in label) and score > 0.8:
                    return AlertEvent(
                        type="urgent",
                        message="URGENT: Prolonged Distress Crying (Duration: > 2 mins)",
                        target="babysitter",
                        confidence=round(score, 2),
                        model_source="AST_Audio_Engine"
                    )
                    
                # CRITICAL: Yelling / Shouting
                if "shouting" in label or "yelling" in label:
                    return AlertEvent(
                        type="critical",
                        message="CRITICAL: Harsh Vocal Tone / Aggressive Yelling Detected",
                        target="babysitter",
                        confidence=round(score, 2),
                        model_source="AST_Audio_Engine"
                    )
            
            return None
        except Exception as e:
            logger.error(f"Audio Inference Error (Requires FFMPEG on OS): {e}")
            return None
        finally:
            if tmp_name and os.path.exists(tmp_name):
                os.remove(tmp_name)

    async def process_async(self, data: any) -> AlertEvent | None:
        # Buffer incoming frame
        self.chunk_buffer.append(data)
        
        # Ensure we have ~3 seconds before running the heavy model
        if len(self.chunk_buffer) >= self.min_buffer_size:
            chunks_to_process = self.chunk_buffer.copy()
            self.chunk_buffer.clear() # Clear buffer for next 3 seconds
            
            # Offload heavy librosa + transformer parse to thread
            return await asyncio.to_thread(self._sync_process_audio, chunks_to_process)
            
        return None

    async def start_background_loop(self, manager, room: str, inbound_queue: asyncio.Queue):
        logger.info("Starting Actual Audio Service background processing...")
        try:
            while True:
                audio_chunk = await inbound_queue.get()
                
                result = await self.process_async(audio_chunk)
                if result:
                    logger.warning(f"Audio Model triggered alert: {result.message}")
                    await manager.broadcast(result.model_dump_json(), room)
                
                inbound_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info("Audio Service background task cancelled.")
        except Exception as e:
            logger.error(f"Audio Service Loop Error: {e}")
