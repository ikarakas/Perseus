# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""Telemetry protocol definitions and handlers."""
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict


class MessageType(Enum):
    """Types of messages in the telemetry protocol."""
    BOM_DATA = "bom_data"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    COMMAND = "command"
    ACK = "acknowledgment"
    AUTH = "authentication"


@dataclass
class TelemetryMessage:
    """Base telemetry message structure."""
    version: str
    message_type: MessageType
    agent_id: str
    timestamp: str
    data: Dict[str, Any]
    checksum: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        msg_dict = {
            "version": self.version,
            "message_type": self.message_type.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "data": self.data
        }
        
        # Calculate checksum if not provided
        if not self.checksum:
            content = json.dumps(msg_dict, sort_keys=True)
            self.checksum = hashlib.sha256(content.encode()).hexdigest()
        
        msg_dict["checksum"] = self.checksum
        return json.dumps(msg_dict)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TelemetryMessage':
        """Create message from JSON string."""
        data = json.loads(json_str)
        
        # Verify checksum
        checksum = data.pop("checksum", None)
        content = json.dumps(data, sort_keys=True)
        calculated_checksum = hashlib.sha256(content.encode()).hexdigest()
        
        if checksum and checksum != calculated_checksum:
            raise ValueError("Message checksum verification failed")
        
        return cls(
            version=data["version"],
            message_type=MessageType(data["message_type"]),
            agent_id=data["agent_id"],
            timestamp=data["timestamp"],
            data=data["data"],
            checksum=checksum
        )
    
    def create_ack(self, success: bool = True, message: str = "") -> 'TelemetryMessage':
        """Create acknowledgment message for this message."""
        return TelemetryMessage(
            version=self.version,
            message_type=MessageType.ACK,
            agent_id=self.agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "success": success,
                "message": message,
                "original_message_type": self.message_type.value
            }
        )


class ProtocolHandler:
    """Handles protocol-level operations."""
    
    PROTOCOL_VERSION = "1.0"
    MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def create_message(
        message_type: MessageType,
        agent_id: str,
        data: Dict[str, Any]
    ) -> TelemetryMessage:
        """Create a new telemetry message."""
        return TelemetryMessage(
            version=ProtocolHandler.PROTOCOL_VERSION,
            message_type=message_type,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data
        )
    
    @staticmethod
    def encode_message(message: TelemetryMessage) -> bytes:
        """Encode message for transmission."""
        json_str = message.to_json()
        
        # Check message size
        if len(json_str) > ProtocolHandler.MAX_MESSAGE_SIZE:
            raise ValueError(f"Message exceeds maximum size of {ProtocolHandler.MAX_MESSAGE_SIZE} bytes")
        
        # Add length prefix for framing
        length_prefix = len(json_str).to_bytes(4, byteorder='big')
        return length_prefix + json_str.encode('utf-8')
    
    @staticmethod
    def decode_message(data: bytes) -> tuple[Optional[TelemetryMessage], bytes]:
        """Decode message from received data.
        
        Returns:
            Tuple of (decoded message or None, remaining data)
        """
        if len(data) < 4:
            return None, data
        
        # Extract length prefix
        message_length = int.from_bytes(data[:4], byteorder='big')
        
        if message_length > ProtocolHandler.MAX_MESSAGE_SIZE:
            raise ValueError(f"Message size {message_length} exceeds maximum")
        
        if len(data) < 4 + message_length:
            return None, data
        
        # Extract message
        message_data = data[4:4 + message_length]
        remaining_data = data[4 + message_length:]
        
        try:
            message = TelemetryMessage.from_json(message_data.decode('utf-8'))
            return message, remaining_data
        except Exception as e:
            raise ValueError(f"Failed to decode message: {e}")
    
    @staticmethod
    def create_error_message(
        agent_id: str,
        error_code: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> TelemetryMessage:
        """Create an error message."""
        return ProtocolHandler.create_message(
            MessageType.ERROR,
            agent_id,
            {
                "error_code": error_code,
                "error_message": error_message,
                "details": details or {}
            }
        )
    
    @staticmethod
    def create_heartbeat(agent_id: str, status: Dict[str, Any]) -> TelemetryMessage:
        """Create a heartbeat message."""
        return ProtocolHandler.create_message(
            MessageType.HEARTBEAT,
            agent_id,
            {
                "status": status,
                "uptime": status.get("uptime", 0),
                "last_collection": status.get("last_collection", None)
            }
        )