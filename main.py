import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from core.config import settings
from core.logging_config import setup_logging, logger
from api.router import router as api_router, video_queue, audio_queue
from socket_manager.manager import manager
from services.rt_detr_service import RTDETR_VisionService
from services.lstm_service import LSTM_AudioService

import models
from database import engine, get_db
from schemas import LoginRequest
from sqlalchemy.orm import Session
from fastapi import Depends

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Enterprise App Factory Lifespan hook to manage background resources
    like AI inference engines and connection pool closures.
    """
    logger.info("Starting up FastAPI application...")
    
    # Initialize SQLite database file instantly
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database schemas hydrated.")
    
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
    
    # Static Assets & Templates
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    
    # Ensure directories exist to prevent startup crash
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)
    
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    templates = Jinja2Templates(directory=templates_dir)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        return templates.TemplateResponse("login.html", {"request": request})

    @app.post("/login")
    async def login_submit(request: LoginRequest, db: Session = Depends(get_db)):
        # Provide Mock authentication / seeding for MVP logic
        db_user = db.query(models.User).filter(models.User.username == request.email).first()
        if not db_user:
            db_user = models.User(username=request.email, hashed_password="mock_hashed_password")
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
        return {"status": "success", "message": "Authenticated. Connecting WebSocket feed."}

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return templates.TemplateResponse("dashboard.html", {"request": request})

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request):
        return templates.TemplateResponse("settings.html", {"request": request})

    return app

# The uvicorn entrypoint app instance
app = create_app()
