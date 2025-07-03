#!/usr/bin/env python3
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
        log_level="info"
    )