from abc import ABC, abstractmethod
import asyncio

class AIServiceInterface(ABC):
    """
    Abstract Base Class for all AI inference services in the pipeline.
    Ensures that services operate asynchronously and provide a standard interface.
    """
    
    @abstractmethod
    async def process_async(self, data: any) -> any:
        """
        Takes raw data (frame or audio buffer), processes it asynchronously,
        and returns detection results or an AlertEntity if a threshold is met.
        """
        pass
        
    @abstractmethod
    async def start_background_loop(self, manager, room: str, inbound_queue: asyncio.Queue):
        """
        Starts the continuous monitoring loop for this specific model,
        pulling data from the provided inbound_queue rather than simulating generation.
        """
        pass
