import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging_config import setup_logging, logger
from api.router import router as api_router, video_queue, audio_queue
from socket_manager.manager import manager
from services.rt_detr_service import RTDETR_VisionService
from services.lstm_service import LSTM_AudioService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Enterprise App Factory Lifespan hook to manage background resources
    like AI inference engines and connection pool closures.
    """
    logger.info("Starting up FastAPI application...")
    
    # Initialize background inference loops connected to WebSocket Queues
    rt_detr = RTDETR_VisionService()
    lstm = LSTM_AudioService()
    
    task_vision = asyncio.create_task(rt_detr.start_background_loop(manager, "alerts", video_queue))
    task_audio = asyncio.create_task(lstm.start_background_loop(manager, "alerts", audio_queue))
    
    yield  # Allows the server to accept connections
    
    # Cleanup background resources on shutdown
    logger.info("Shutting down FastAPI application...")
    task_vision.cancel()
    task_audio.cancel()
    try:
        await task_vision
        await task_audio
    except asyncio.CancelledError:
        pass

def create_app() -> FastAPI:
    """
    Application Factory for creating the FastAPI instance.
    """
    # Initialize logging first
    setup_logging()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Register Routers
    app.include_router(api_router)
    
    return app

# The uvicorn entrypoint app instance
app = create_app()
