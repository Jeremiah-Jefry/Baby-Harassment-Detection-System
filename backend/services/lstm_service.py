import asyncio
import random
from services.ai_base import AIServiceInterface
from models.domain import AlertEvent
from core.logging_config import logger

class LSTM_AudioService(AIServiceInterface):
    """
    Stub for the LSTM Audio classification model.
    Processes live audio chunks buffering from the user's microphone.
    """
    
    async def process_async(self, data: any) -> AlertEvent | None:
        # Simulate processing an audio snippet (200ms - 500ms delay)
        delay = random.uniform(0.2, 0.5)
        await asyncio.sleep(delay)
        
        # Simulate a ~1% chance per chunk of detecting distress logic
        if random.random() < 0.01:
            return AlertEvent(
                type="danger",
                message="Distress Audio Detected by LSTM from live mic (Confidence: 0.91)",
                target="babysitter",
                confidence=0.91,
                model_source="LSTM_Audio_Engine"
            )
        return None

    async def start_background_loop(self, manager, room: str, inbound_queue: asyncio.Queue):
        logger.info("Starting LSTM Audio Service background task mapping to queue...")
        try:
            while True:
                # Blocks until an audio chunk arrives from the WebSocket
                audio_chunk = await inbound_queue.get()
                
                # Perform inference
                result = await self.process_async(audio_chunk)
                if result:
                    logger.warning(f"LSTM triggered alert: {result.message}")
                    await manager.broadcast(result.model_dump_json(), room)
                
                # Mark task as done
                inbound_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info("LSTM Audio Service background task cancelled.")
        except Exception as e:
            logger.error(f"LSTM Service Error: {e}")
