import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings, using environment variables with fallbacks.
    Pydantic allows type validation on .env file loading.
    """
    PROJECT_NAME: str = "Guardianize Enterprise Vision"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] = ["*"]  # In production, restrict to FE domain
    
    # Environment (development/production)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # AI thresholds
    ALERT_CONFIDENCE_THRESHOLD: float = 0.85

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
