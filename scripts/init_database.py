#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Initialize the Perseus database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from alembic import command
from alembic.config import Config

from src.database import init_database, create_tables, test_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database and run migrations"""
    logger.info("Initializing Perseus database...")
    
    # Initialize database connection
    engine = init_database()
    
    # Test connection
    if not test_connection():
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    logger.info("Database connection successful")
    
    # Create tables
    logger.info("Creating database tables...")
    create_tables()
    
    # Set up Alembic config
    alembic_cfg = Config("migrations/alembic.ini")
    
    # Create initial migration if needed
    try:
        logger.info("Stamping database with initial migration...")
        command.stamp(alembic_cfg, "head")
    except Exception as e:
        logger.warning(f"Could not stamp database: {e}")
    
    logger.info("Database initialization complete!")


if __name__ == "__main__":
    main()