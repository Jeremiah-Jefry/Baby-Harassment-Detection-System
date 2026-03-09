import asyncio
import random
from services.ai_base import AIServiceInterface
from core.logging_config import logger
from models.domain import AlertEvent

class RTDETR_VisionService(AIServiceInterface):
    """
    Stub for the Hugging Face RT-DETR vision model.
    Processes live frames captured by the user's camera.
    """
    
    async def process_async(self, data: any) -> AlertEvent | None:
        # Simulate loading the base64 frame into a tensor pipeline (150ms-250ms delay)
        # i.e., `image = Image.open(BytesIO(base64.b64decode(data)))`
        delay = random.uniform(0.15, 0.25)
        await asyncio.sleep(delay)
        
        # Simulate ~2% chance per frame of detecting a bounding box hazard
        if random.random() < 0.02:
            return AlertEvent(
                type="danger",
                message="Hazard Detected by RT-DETR from live camera (Confidence: 0.94)",
                target="baby",
                confidence=0.94,
                model_source="RT-DETR_HuggingFace"
            )
        return None

    async def start_background_loop(self, manager, room: str, inbound_queue: asyncio.Queue):
        logger.info("Starting RT-DETR Vision Service background task mapping to queue...")
        try:
            while True:
                # Blocks until a real base64 frame arrives from the browser
                frame_data = await inbound_queue.get()
                
                # Perform inference
                result = await self.process_async(frame_data)
                if result:
                    logger.warning(f"RT-DETR triggered alert: {result.message}")
                    await manager.broadcast(result.model_dump_json(), room)
                
                # Mark task as done
                inbound_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info("RT-DETR Vision Service background task cancelled.")
        except Exception as e:
            logger.error(f"RT-DETR Service Error: {e}")
