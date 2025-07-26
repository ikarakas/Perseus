# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Database configuration for Perseus platform
"""

import os
from typing import Optional
from urllib.parse import quote_plus

class DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(self):
        # Database connection parameters
        self.db_host = os.getenv("PERSEUS_DB_HOST", "localhost")
        self.db_port = int(os.getenv("PERSEUS_DB_PORT", "5432"))
        self.db_name = os.getenv("PERSEUS_DB_NAME", "perseus")
        self.db_user = os.getenv("PERSEUS_DB_USER", "perseus")
        self.db_password = os.getenv("PERSEUS_DB_PASSWORD", "perseus_secret")
        
        # Connection pool settings
        self.pool_size = int(os.getenv("PERSEUS_DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("PERSEUS_DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("PERSEUS_DB_POOL_TIMEOUT", "30"))
        
        # Other settings
        self.echo_sql = os.getenv("PERSEUS_DB_ECHO_SQL", "false").lower() == "true"
        self.use_ssl = os.getenv("PERSEUS_DB_USE_SSL", "false").lower() == "true"
        
    @property
    def database_url(self) -> str:
        """Get the database connection URL"""
        # URL encode the password to handle special characters
        password = quote_plus(self.db_password)
        return f"postgresql://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def async_database_url(self) -> str:
        """Get the async database connection URL"""
        # URL encode the password to handle special characters
        password = quote_plus(self.db_password)
        return f"postgresql+asyncpg://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def get_engine_kwargs(self) -> dict:
        """Get SQLAlchemy engine configuration"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "echo": self.echo_sql,
            "pool_pre_ping": True,  # Verify connections before using
            "connect_args": self._get_connect_args()
        }
    
    def _get_connect_args(self) -> dict:
        """Get database-specific connection arguments"""
        args = {}
        if self.use_ssl:
            args["sslmode"] = "require"
        return args

# Global database configuration instance
db_config = DatabaseConfig()