from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./guardianize.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_alert_to_db(alert):
    import models
    db = SessionLocal()
    try:
        db_alert = models.AlertLog(
            alert_type=alert.target,
            message=alert.message,
            severity=alert.type,
            confidence=alert.confidence,
            model_source=alert.model_source
        )
        db.add(db_alert)
        db.commit()
    except Exception as e:
        print(f"DB Save Error: {e}")
    finally:
        db.close()
