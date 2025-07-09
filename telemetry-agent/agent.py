"""Telemetry agent for remote BOM collection."""
import asyncio
import logging
import signal
import sys
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import yaml

from collector import BOMCollector
from transport import TelemetryTransport


logger = logging.getLogger(__name__)


class TelemetryAgent:
    """Main telemetry agent class."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        
        # Initialize components
        self.collector = BOMCollector(
            agent_id=config.get("agent", {}).get("id")
        )
        
        self.transport = TelemetryTransport(
            server_host=config["server"]["host"],
            server_port=config["server"]["port"],
            agent_id=self.collector.agent_id,
            ssl_context=None  # TODO: Add SSL support
        )
        
        # Collection settings
        self.collection_interval = config.get("collection", {}).get("interval", 3600)
        self.deep_scan = config.get("collection", {}).get("deep_scan", False)
        self.heartbeat_interval = config.get("agent", {}).get("heartbeat_interval", 60)
        
        # State
        self.last_collection: Optional[datetime] = None
        self.uptime_start = datetime.now(timezone.utc)
    
    async def start(self) -> None:
        """Start the telemetry agent."""
        logger.info(f"Starting telemetry agent (ID: {self.collector.agent_id})")
        
        # Connect to server
        if not await self.transport.connect():
            logger.error("Failed to connect to telemetry server")
            return
        
        self.running = True
        
        # Immediately collect and send SBOM on initial connection
        logger.info("Initial connection established, triggering immediate SBOM collection...")
        asyncio.create_task(self._collect_and_send())
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._collection_loop()),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._reconnection_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Agent tasks cancelled")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the telemetry agent."""
        logger.info("Stopping telemetry agent...")
        self.running = False
        await self.transport.disconnect()
        logger.info("Telemetry agent stopped")
    
    async def _collection_loop(self) -> None:
        """Periodically collect and send BOM data."""
        # Initial delay to allow system to stabilize
        await asyncio.sleep(10)
        
        while self.running:
            try:
                if self.transport.connected:
                    await self._collect_and_send()
                else:
                    logger.warning("Not connected, skipping collection")
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(60)  # Error backoff
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to the server."""
        while self.running:
            try:
                if self.transport.connected:
                    status = self._get_agent_status()
                    await self.transport.send_heartbeat(status)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(30)
    
    async def _reconnection_loop(self) -> None:
        """Monitor connection and reconnect if needed."""
        while self.running:
            try:
                if not self.transport.connected:
                    logger.info("Connection lost, attempting to reconnect...")
                    connected = await self.transport.connect()
                    
                    # If reconnection successful, immediately collect and send SBOM
                    if connected:
                        logger.info("Reconnected successfully, triggering immediate SBOM collection...")
                        asyncio.create_task(self._collect_and_send())
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in reconnection loop: {e}")
                await asyncio.sleep(60)
    
    async def _collect_and_send(self) -> None:
        """Collect BOM data and send to server."""
        logger.info("Starting BOM collection...")
        
        try:
            # Collect BOM data
            bom_data = await self.collector.collect_bom(deep_scan=self.deep_scan)
            
            # Send to server
            if await self.transport.send_bom_data(bom_data):
                self.last_collection = datetime.now(timezone.utc)
                logger.info(f"BOM data sent successfully ({len(bom_data['components'])} components)")
            else:
                logger.error("Failed to send BOM data")
                
        except Exception as e:
            logger.error(f"Failed to collect/send BOM: {e}")
            
            # Report error to server
            await self.transport.send_error(
                error_code="COLLECTION_ERROR",
                error_message=str(e),
                details={"phase": "collection"}
            )
    
    def _get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        uptime = (datetime.now(timezone.utc) - self.uptime_start).total_seconds()
        
        return {
            "uptime": int(uptime),
            "last_collection": self.last_collection.isoformat() if self.last_collection else None,
            "system_info": self.collector.get_system_info(),
            "config": {
                "collection_interval": self.collection_interval,
                "deep_scan": self.deep_scan
            }
        }


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('telemetry-agent.log')
        ]
    )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Telemetry Agent for SBOM Collection')
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Configuration file path'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create and start agent
    agent = TelemetryAgent(config)
    
    # Setup signal handlers  
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        agent.running = False
        # Force exit if graceful shutdown fails
        import sys
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Agent error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())