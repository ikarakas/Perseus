#!/usr/bin/env python3
"""Run the telemetry server standalone."""
import asyncio
import argparse
import yaml
import logging
import sys
from pathlib import Path

from src.telemetry.server import TelemetryServer
from src.telemetry.storage import TelemetryStorage
from src.telemetry.api import init_telemetry_api


def load_config(config_file: str) -> dict:
    """Load server configuration."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def setup_logging(config: dict) -> None:
    """Setup logging configuration."""
    log_config = config.get('logging', {})
    
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_config.get('file', 'telemetry-server.log'))
        ]
    )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Telemetry Server for SBOM Collection')
    parser.add_argument(
        '-c', '--config',
        default='telemetry-server-config.yaml',
        help='Configuration file path'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Initialize storage
    storage_config = config.get('storage', {})
    storage = TelemetryStorage(storage_config.get('path', './telemetry_data'))
    
    # Initialize server
    server_config = config.get('server', {})
    server = TelemetryServer(
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 9876),
        storage=storage
    )
    
    # Initialize telemetry API with server reference
    init_telemetry_api(storage, server)
    logger.info("Telemetry API initialized with server reference")
    
    try:
        logger.info("Starting telemetry server...")
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())