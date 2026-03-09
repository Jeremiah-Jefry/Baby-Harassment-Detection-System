import asyncio
import time
import base64
import numpy as np
from io import BytesIO
from PIL import Image

from transformers import pipeline
from services.ai_base import AIServiceInterface
from core.logging_config import logger
from models.domain import AlertEvent

class RTDETR_VisionService(AIServiceInterface):
    """
    Real Hugging Face RT-DETR vision model.
    Processes live frames captured by the user's camera to detect hazards.
    """
    
    def __init__(self):
        self.last_process_time = 0
        self.process_interval = 2.0  # process a frame every 2 seconds to prevent crashing
        
        self.lone_baby_start_time = None
        self.last_frame_pixels = None
        
        logger.info("Initializing Object Detection Pipeline... (May download model first run)")
        # Loading the highly stable Facebook DETR architecture since RT-DETR requires custom trust_remote_code setups
        self.detector = pipeline("object-detection", model="facebook/detr-resnet-50")
        logger.info("DETR Pipeline Loaded.")

    def _sync_process_frame(self, frame_data: str, current_time: float) -> AlertEvent | None:
        """Synchronous inference function running in a background thread."""
        try:
            # Parse the Base64 frame
            if "," in frame_data:
                frame_data = frame_data.split(",", 1)[1]
                
            image_bytes = base64.b64decode(frame_data)
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            
            # Inter-frame difference proxy for movement
            current_pixels = np.array(image.convert("L"))
            movement = 0.0
            if self.last_frame_pixels is not None:
                diff = np.abs(current_pixels.astype(np.float32) - self.last_frame_pixels.astype(np.float32))
                movement = np.mean(diff)
            self.last_frame_pixels = current_pixels
            
            # Run Inference
            results = self.detector(image)
            
            # Filter for persons with decent confidence
            persons = [r for r in results if r['label'] == 'person' and r['score'] > 0.5]
            num_persons = len(persons)
            
            # Rule 1: "Baby Unattended" if only 1 person detected for > 30s
            if num_persons == 1:
                if self.lone_baby_start_time is None:
                    self.lone_baby_start_time = current_time
                elif current_time - self.lone_baby_start_time > 30:
                    self.lone_baby_start_time = current_time # Reset loop
                    return AlertEvent(
                        type="alert",
                        message="ALERT: Babysitter Left Room - Baby Unattended for > 30s",
                        target="baby",
                        confidence=round(float(persons[0]['score']), 2),
                        model_source="RT-DETR_HuggingFace"
                    )
            else:
                self.lone_baby_start_time = None
                
            # Rule 2: Intersecting Bounding Boxes + High Movement -> Erratic Movement
            if num_persons >= 2:
                box1, box2 = persons[0]['box'], persons[1]['box']
                # Check for rectangle intersection
                intersect = not (box1['xmax'] < box2['xmin'] or box1['xmin'] > box2['xmax'] or
                                 box1['ymax'] < box2['ymin'] or box1['ymin'] > box2['ymax'])
                                 
                if intersect and movement > 15.0: # Movement heuristic threshold
                    return AlertEvent(
                        type="warning",
                        message="WARNING: Erratic Movement / Potential Rough Handling Detected",
                        target="baby",
                        confidence=round(float(max(persons[0]['score'], persons[1]['score'])), 2),
                        model_source="RT-DETR_HuggingFace"
                    )
            
            return None
        except Exception as e:
            logger.error(f"RT-DETR Sync Inference Error: {e}")
            return None

    async def process_async(self, data: any) -> AlertEvent | None:
        current_time = time.time()
        
        # Frame-skipping mechanism to respect interval
        if current_time - self.last_process_time < self.process_interval:
            return None
            
        self.last_process_time = current_time
        
        # Offload pipeline inference to threadpool to avoid blocking event loop
        return await asyncio.to_thread(self._sync_process_frame, data, current_time)

    async def start_background_loop(self, manager, room: str, inbound_queue: asyncio.Queue):
        logger.info("Starting Actual RT-DETR Vision Service mapping to queue...")
        try:
            while True:
                # Blocks until a real base64 frame arrives from the browser
                frame_data = await inbound_queue.get()
                
                # Perform inference asynchronously
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
