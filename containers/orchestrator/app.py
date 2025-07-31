#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
SBOM Orchestrator API Service
Main entry point for the SBOM generation platform
"""

import uvicorn
from src.api.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        # Connection handling optimizations
        limit_concurrency=20,  # Limit concurrent connections (reduced)
        limit_max_requests=1000,  # Restart worker after N requests
        timeout_keep_alive=5,  # Keep-alive timeout (reduced)
        timeout_graceful_shutdown=10,  # Graceful shutdown timeout (reduced)
        # Performance tuning
        loop="asyncio",  # Use asyncio event loop
        http="h11",  # Use h11 HTTP implementation
        workers=1,  # Single worker for consistency
        access_log=True  # Enable access logging
    )