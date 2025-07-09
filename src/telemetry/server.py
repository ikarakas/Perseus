"""Telemetry server for receiving BOM data from remote agents."""
import asyncio
import logging
import json
import ssl
from typing import Dict, Any, Optional, Set
from datetime import datetime

from .protocol import TelemetryMessage, MessageType, ProtocolHandler
from .handlers import MessageHandler
from .storage import TelemetryStorage


logger = logging.getLogger(__name__)


class TelemetryClient:
    """Represents a connected telemetry agent."""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_address: tuple):
        self.reader = reader
        self.writer = writer
        self.client_address = client_address
        self.agent_id: Optional[str] = None
        self.authenticated = False
        self.last_seen = datetime.utcnow()
        self.buffer = b""
    
    async def send_message(self, message: TelemetryMessage) -> None:
        """Send a message to the client."""
        try:
            data = ProtocolHandler.encode_message(message)
            self.writer.write(data)
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Error sending message to {self.agent_id}: {e}")
            raise
    
    async def close(self) -> None:
        """Close the client connection."""
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass


class TelemetryServer:
    """Async TCP server for telemetry data collection."""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 9876,
        storage: Optional[TelemetryStorage] = None,
        ssl_context: Optional[ssl.SSLContext] = None
    ):
        self.host = host
        self.port = port
        self.storage = storage or TelemetryStorage()
        self.ssl_context = ssl_context
        self.clients: Dict[str, TelemetryClient] = {}
        self.server: Optional[asyncio.Server] = None
        self.message_handler = MessageHandler(self.storage)
        self._running = False
    
    async def start(self) -> None:
        """Start the telemetry server."""
        logger.info(f"Starting telemetry server on {self.host}:{self.port}")
        
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
            ssl=self.ssl_context
        )
        
        self._running = True
        
        addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
        logger.info(f"Telemetry server listening on {addrs}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self) -> None:
        """Stop the telemetry server."""
        logger.info("Stopping telemetry server...")
        self._running = False
        
        # Close all client connections
        for client in list(self.clients.values()):
            await client.close()
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Telemetry server stopped")
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle a client connection."""
        client_address = writer.get_extra_info('peername')
        logger.info(f"New connection from {client_address}")
        
        client = TelemetryClient(reader, writer, client_address)
        
        try:
            await self._handle_client_messages(client)
        except asyncio.CancelledError:
            logger.info(f"Client {client.agent_id or client_address} connection cancelled")
        except Exception as e:
            logger.error(f"Error handling client {client.agent_id or client_address}: {e}")
        finally:
            # Remove client from active clients
            if client.agent_id and client.agent_id in self.clients:
                del self.clients[client.agent_id]
            
            await client.close()
            logger.info(f"Connection closed for {client.agent_id or client_address}")
    
    async def _handle_client_messages(self, client: TelemetryClient) -> None:
        """Handle messages from a client."""
        while self._running:
            try:
                # Read data with timeout
                data = await asyncio.wait_for(client.reader.read(8192), timeout=300.0)
                
                if not data:
                    logger.info(f"Client {client.agent_id or client.client_address} disconnected")
                    break
                
                # Add to buffer
                client.buffer += data
                
                # Process messages in buffer
                while True:
                    message, client.buffer = ProtocolHandler.decode_message(client.buffer)
                    if not message:
                        break
                    
                    await self._process_message(client, message)
                    
            except asyncio.TimeoutError:
                logger.warning(f"Client {client.agent_id or client.client_address} timed out")
                break
            except Exception as e:
                logger.error(f"Error reading from client {client.agent_id or client.client_address}: {e}")
                break
    
    async def _process_message(self, client: TelemetryClient, message: TelemetryMessage) -> None:
        """Process a received message."""
        try:
            logger.debug(f"Received {message.message_type.value} from {message.agent_id}")
            
            # Update client info
            client.last_seen = datetime.utcnow()
            
            # Handle authentication first
            if not client.authenticated and message.message_type != MessageType.AUTH:
                # For now, accept the first message as implicit auth
                # TODO: Implement proper authentication
                client.authenticated = True
                client.agent_id = message.agent_id
                self.clients[client.agent_id] = client
                logger.info(f"Agent {client.agent_id} authenticated")
            
            # Process message based on type
            response = await self.message_handler.handle_message(message)
            
            # Send response if any
            if response:
                await client.send_message(response)
            else:
                # Send generic acknowledgment
                ack = message.create_ack(success=True, message="Message processed successfully")
                await client.send_message(ack)
                
        except Exception as e:
            logger.error(f"Error processing message from {client.agent_id}: {e}")
            
            # Send error response
            error_msg = ProtocolHandler.create_error_message(
                agent_id=message.agent_id,
                error_code="PROCESSING_ERROR",
                error_message=str(e)
            )
            await client.send_message(error_msg)
    
    def get_connected_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about connected agents."""
        return {
            agent_id: {
                "address": client.client_address,
                "last_seen": client.last_seen.isoformat(),
                "authenticated": client.authenticated
            }
            for agent_id, client in self.clients.items()
        }


async def main():
    """Run the telemetry server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = TelemetryServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())