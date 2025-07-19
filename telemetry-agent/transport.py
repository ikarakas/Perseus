# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""Transport layer for telemetry agent."""
import asyncio
import logging
import socket
import ssl
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.telemetry.protocol import TelemetryMessage, MessageType, ProtocolHandler


logger = logging.getLogger(__name__)


class TelemetryTransport:
    """Handles communication with telemetry server."""
    
    def __init__(
        self,
        server_host: str,
        server_port: int,
        agent_id: str,
        ssl_context: Optional[ssl.SSLContext] = None
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.agent_id = agent_id
        self.ssl_context = ssl_context
        
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.buffer = b""
        
        # Connection retry settings
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.max_retry_delay = 300  # 5 minutes
    
    async def connect(self) -> bool:
        """Connect to telemetry server."""
        retry_count = 0
        delay = self.retry_delay
        
        while retry_count < self.max_retries:
            try:
                logger.info(f"Connecting to {self.server_host}:{self.server_port}...")
                
                self.reader, self.writer = await asyncio.open_connection(
                    self.server_host,
                    self.server_port,
                    ssl=self.ssl_context
                )
                
                self.connected = True
                logger.info("Connected to telemetry server")
                
                # Send authentication message
                await self._authenticate()
                
                return True
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Connection failed (attempt {retry_count}/{self.max_retries}): {e}")
                
                if retry_count < self.max_retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self.max_retry_delay)  # Exponential backoff
        
        return False
    
    
    async def disconnect(self) -> None:
        """Disconnect from telemetry server."""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
        
        self.connected = False
        self.reader = None
        self.writer = None
        logger.info("Disconnected from telemetry server")
    
    async def send_message(self, message: TelemetryMessage) -> bool:
        """Send a message to the server."""
        if not self.connected:
            logger.error("Not connected to server")
            return False
        
        try:
            data = ProtocolHandler.encode_message(message)
            self.writer.write(data)
            await self.writer.drain()
            logger.debug(f"Sent {message.message_type.value} message")
            
            # Check if connection is still alive by testing the socket
            if self.writer.is_closing():
                logger.error("Connection closed by server")
                self.connected = False
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.connected = False
            return False
    
    async def receive_message(self, timeout: float = 30.0) -> Optional[TelemetryMessage]:
        """Receive a message from the server."""
        if not self.connected:
            return None
        
        try:
            # Read with timeout
            data = await asyncio.wait_for(
                self.reader.read(8192),
                timeout=timeout
            )
            
            if not data:
                logger.warning("Server closed connection")
                self.connected = False
                return None
            
            # Add to buffer and try to decode
            self.buffer += data
            message, self.buffer = ProtocolHandler.decode_message(self.buffer)
            
            if message:
                logger.debug(f"Received {message.message_type.value} message")
            
            return message
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            self.connected = False
            return None
    
    async def send_bom_data(self, bom_data: Dict[str, Any]) -> bool:
        """Send BOM data to the server."""
        message = ProtocolHandler.create_message(
            MessageType.BOM_DATA,
            self.agent_id,
            bom_data
        )
        
        if await self.send_message(message):
            logger.info("BOM data sent successfully")
            return True
        
        return False
    
    async def send_heartbeat(self, status: Dict[str, Any]) -> bool:
        """Send heartbeat to the server."""
        message = ProtocolHandler.create_heartbeat(self.agent_id, status)
        
        # Send heartbeat
        if not await self.send_message(message):
            return False
        
        # Check if connection is still alive by trying to read (with very short timeout)
        try:
            if self.reader and self.connected:
                # Try to read with minimal timeout to detect closed connection
                data = await asyncio.wait_for(self.reader.read(1), timeout=0.1)
                if data == b'':
                    # Empty data means connection closed
                    logger.error("Server closed connection (detected during heartbeat)")
                    self.connected = False
                    return False
        except asyncio.TimeoutError:
            # No data available - connection is still alive
            pass
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            self.connected = False
            return False
        
        return True
    
    async def send_error(self, error_code: str, error_message: str, details: Dict[str, Any] = None) -> bool:
        """Send error message to the server."""
        message = ProtocolHandler.create_error_message(
            self.agent_id,
            error_code,
            error_message,
            details
        )
        
        return await self.send_message(message)
    
    async def _authenticate(self) -> bool:
        """Authenticate with the server."""
        auth_message = ProtocolHandler.create_message(
            MessageType.AUTH,
            self.agent_id,
            {
                "metadata": {
                    "agent_version": "1.3.1",
                    "hostname": socket.gethostname(),
                    "platform": sys.platform
                }
            }
        )
        
        if await self.send_message(auth_message):
            response = await self.receive_message(timeout=10.0)
            
            if response and response.message_type == MessageType.ACK:
                if response.data.get("success"):
                    logger.info("Authentication successful")
                    # Brief delay to ensure connection is stable
                    await asyncio.sleep(0.1)
                    return True
                else:
                    logger.error(f"Authentication failed: {response.data.get('message')}")
        
        return False