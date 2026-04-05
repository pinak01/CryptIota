"""
QuantumGuard AI — Database Setup (SQLAlchemy + SQLite)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from config import DATABASE_URI

engine = create_engine(DATABASE_URI, echo=False, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))
Base = declarative_base()


def init_db():
    """Create all tables if they don't exist."""
    import models  # noqa: F401 — ensures models are registered with Base
    import iot_lab.models  # noqa: F401 — IoT Security Lab tables
    Base.metadata.create_all(bind=engine)
    print("[DB] All tables created / verified.")


def get_db():
    """Return a new database session. Caller must close it."""
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise
