# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Database connection and session management for Perseus
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from .config import db_config

logger = logging.getLogger(__name__)

# Create the declarative base
Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionLocal = None


def init_database(database_url: Optional[str] = None, **engine_kwargs):
    """
    Initialize the database engine and session factory
    
    Args:
        database_url: Optional database URL override
        **engine_kwargs: Additional engine configuration
    """
    global _engine, _SessionLocal
    
    url = database_url or db_config.database_url
    
    # Merge configuration
    config = db_config.get_engine_kwargs()
    config.update(engine_kwargs)
    
    # Create engine
    _engine = create_engine(url, **config)
    
    # Add event listeners for connection health
    @event.listens_for(_engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.debug("Database connection established")
    
    @event.listens_for(_engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        # Perform a simple query to verify connection
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            raise
    
    # Create session factory
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
        expire_on_commit=False
    )
    
    logger.info("Database initialized successfully")
    return _engine


def get_engine():
    """Get the database engine, initializing if necessary"""
    if _engine is None:
        init_database()
    return _engine


def get_session() -> Session:
    """
    Get a new database session
    
    Returns:
        Session: A new SQLAlchemy session
    """
    if _SessionLocal is None:
        init_database()
    return _SessionLocal()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Yields:
        Session: A database session that will be automatically closed
    """
    db = get_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database tables dropped")


def test_connection() -> bool:
    """
    Test the database connection
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


# For FastAPI dependency injection
def get_db_session():
    """
    Dependency for FastAPI routes to get database session
    
    Yields:
        Session: Database session
    """
    db = get_session()
    try:
        yield db
    finally:
        db.close()