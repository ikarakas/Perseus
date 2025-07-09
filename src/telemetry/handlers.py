"""Message handlers for telemetry server."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .protocol import TelemetryMessage, MessageType, ProtocolHandler
from .storage import TelemetryStorage


logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles different types of telemetry messages."""
    
    def __init__(self, storage: TelemetryStorage):
        self.storage = storage
        self.handlers = {
            MessageType.BOM_DATA: self.handle_bom_data,
            MessageType.HEARTBEAT: self.handle_heartbeat,
            MessageType.ERROR: self.handle_error,
            MessageType.AUTH: self.handle_auth,
        }
    
    async def handle_message(self, message: TelemetryMessage) -> Optional[TelemetryMessage]:
        """Route message to appropriate handler."""
        handler = self.handlers.get(message.message_type)
        
        if not handler:
            logger.warning(f"No handler for message type: {message.message_type}")
            return message.create_ack(
                success=False,
                message=f"Unknown message type: {message.message_type.value}"
            )
        
        try:
            return await handler(message)
        except Exception as e:
            logger.error(f"Error handling {message.message_type.value}: {e}")
            return message.create_ack(
                success=False,
                message=f"Error processing message: {str(e)}"
            )
    
    async def handle_bom_data(self, message: TelemetryMessage) -> Optional[TelemetryMessage]:
        """Handle BOM data submission."""
        logger.info(f"Received BOM data from agent {message.agent_id}")
        
        try:
            # Extract BOM data
            bom_data = message.data
            
            # Validate required fields
            required_fields = ["components", "metadata", "scan_id"]
            for field in required_fields:
                if field not in bom_data:
                    return message.create_ack(
                        success=False,
                        message=f"Missing required field: {field}"
                    )
            
            # Store BOM data
            record_id = await self.storage.store_bom_data(
                agent_id=message.agent_id,
                scan_id=bom_data["scan_id"],
                components=bom_data["components"],
                metadata=bom_data["metadata"],
                timestamp=message.timestamp
            )
            
            logger.info(f"Stored BOM data with ID: {record_id}")
            
            return message.create_ack(
                success=True,
                message=f"BOM data stored successfully with ID: {record_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to store BOM data: {e}")
            return message.create_ack(
                success=False,
                message=f"Failed to store BOM data: {str(e)}"
            )
    
    async def handle_heartbeat(self, message: TelemetryMessage) -> Optional[TelemetryMessage]:
        """Handle heartbeat message."""
        logger.debug(f"Heartbeat from agent {message.agent_id}")
        
        # Update agent status
        await self.storage.update_agent_status(
            agent_id=message.agent_id,
            status=message.data.get("status", {}),
            last_seen=message.timestamp
        )
        
        # Check if any commands are pending for this agent
        pending_commands = await self.storage.get_pending_commands(message.agent_id)
        
        if pending_commands:
            # Send the first pending command
            command = pending_commands[0]
            return ProtocolHandler.create_message(
                MessageType.COMMAND,
                message.agent_id,
                command
            )
        
        return message.create_ack(success=True, message="Heartbeat received")
    
    async def handle_error(self, message: TelemetryMessage) -> Optional[TelemetryMessage]:
        """Handle error message from agent."""
        logger.error(f"Error from agent {message.agent_id}: {message.data}")
        
        # Log error to storage
        await self.storage.log_agent_error(
            agent_id=message.agent_id,
            error_data=message.data,
            timestamp=message.timestamp
        )
        
        return message.create_ack(success=True, message="Error logged")
    
    async def handle_auth(self, message: TelemetryMessage) -> Optional[TelemetryMessage]:
        """Handle authentication message."""
        logger.info(f"Authentication request from agent {message.agent_id}")
        
        # TODO: Implement proper authentication
        # For now, accept all agents
        auth_data = message.data
        
        # Register agent
        await self.storage.register_agent(
            agent_id=message.agent_id,
            metadata=auth_data.get("metadata", {}),
            timestamp=message.timestamp
        )
        
        return message.create_ack(
            success=True,
            message="Authentication successful"
        )