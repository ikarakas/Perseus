"""Storage backend for telemetry data."""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import aiofiles
import uuid


class TelemetryStorage:
    """Storage for telemetry data.
    
    This is a simple file-based storage for now.
    Can be replaced with database backend later.
    """
    
    def __init__(self, storage_path: str = "./telemetry_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.bom_path = self.storage_path / "bom"
        self.agents_path = self.storage_path / "agents"
        self.errors_path = self.storage_path / "errors"
        
        for path in [self.bom_path, self.agents_path, self.errors_path]:
            path.mkdir(exist_ok=True)
        
        # In-memory cache for agent data
        self.agents_cache: Dict[str, Dict[str, Any]] = {}
        self.commands_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Load existing agent data synchronously on init
        self._load_agents_sync()
    
    def _load_agents_sync(self) -> None:
        """Load agent data into cache synchronously."""
        for agent_file in self.agents_path.glob("*.json"):
            try:
                with open(agent_file, 'r') as f:
                    data = json.load(f)
                    agent_id = agent_file.stem
                    self.agents_cache[agent_id] = data
            except Exception:
                pass
    
    async def _load_agents(self) -> None:
        """Load agent data into cache asynchronously."""
        for agent_file in self.agents_path.glob("*.json"):
            try:
                async with aiofiles.open(agent_file, 'r') as f:
                    data = json.loads(await f.read())
                    agent_id = agent_file.stem
                    self.agents_cache[agent_id] = data
            except Exception:
                pass
    
    async def store_bom_data(
        self,
        agent_id: str,
        scan_id: str,
        components: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        timestamp: str
    ) -> str:
        """Store BOM data from an agent."""
        record_id = str(uuid.uuid4())
        
        bom_record = {
            "record_id": record_id,
            "agent_id": agent_id,
            "scan_id": scan_id,
            "components": components,
            "metadata": metadata,
            "timestamp": timestamp,
            "received_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Store to file
        filename = self.bom_path / f"{agent_id}_{record_id}.json"
        async with aiofiles.open(filename, 'w') as f:
            await f.write(json.dumps(bom_record, indent=2))
        
        # Update agent's last scan info
        if agent_id in self.agents_cache:
            self.agents_cache[agent_id]["last_scan"] = {
                "scan_id": scan_id,
                "record_id": record_id,
                "timestamp": timestamp,
                "component_count": len(components)
            }
            await self._save_agent(agent_id)
        
        return record_id
    
    async def register_agent(
        self,
        agent_id: str,
        metadata: Dict[str, Any],
        timestamp: str
    ) -> None:
        """Register a new agent."""
        self.agents_cache[agent_id] = {
            "agent_id": agent_id,
            "metadata": metadata,
            "registered_at": timestamp,
            "last_seen": timestamp,
            "status": "active"
        }
        await self._save_agent(agent_id)
    
    async def update_agent_status(
        self,
        agent_id: str,
        status: Dict[str, Any],
        last_seen: str
    ) -> None:
        """Update agent status."""
        if agent_id not in self.agents_cache:
            self.agents_cache[agent_id] = {
                "agent_id": agent_id,
                "registered_at": last_seen
            }
        
        self.agents_cache[agent_id].update({
            "status": status,
            "last_seen": last_seen,
            "last_heartbeat": datetime.utcnow().isoformat() + "Z"
        })
        
        await self._save_agent(agent_id)
    
    async def log_agent_error(
        self,
        agent_id: str,
        error_data: Dict[str, Any],
        timestamp: str
    ) -> None:
        """Log an error from an agent."""
        error_record = {
            "agent_id": agent_id,
            "error_data": error_data,
            "timestamp": timestamp,
            "logged_at": datetime.utcnow().isoformat() + "Z"
        }
        
        filename = self.errors_path / f"{agent_id}_{timestamp.replace(':', '-')}.json"
        async with aiofiles.open(filename, 'w') as f:
            await f.write(json.dumps(error_record, indent=2))
    
    async def get_pending_commands(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get pending commands for an agent."""
        return self.commands_cache.get(agent_id, [])
    
    async def add_command(self, agent_id: str, command: Dict[str, Any]) -> None:
        """Add a command for an agent."""
        if agent_id not in self.commands_cache:
            self.commands_cache[agent_id] = []
        self.commands_cache[agent_id].append(command)
    
    async def _save_agent(self, agent_id: str) -> None:
        """Save agent data to file."""
        if agent_id in self.agents_cache:
            filename = self.agents_path / f"{agent_id}.json"
            async with aiofiles.open(filename, 'w') as f:
                await f.write(json.dumps(self.agents_cache[agent_id], indent=2))
    
    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information."""
        return self.agents_cache.get(agent_id)
    
    async def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered agents."""
        return self.agents_cache.copy()
    
    async def get_latest_bom(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest BOM data for an agent."""
        bom_files = list(self.bom_path.glob(f"{agent_id}_*.json"))
        if not bom_files:
            return None
        
        # Get most recent file
        latest_file = max(bom_files, key=lambda f: f.stat().st_mtime)
        
        async with aiofiles.open(latest_file, 'r') as f:
            return json.loads(await f.read())
    
    async def get_bom_history(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get BOM history for an agent."""
        bom_files = list(self.bom_path.glob(f"{agent_id}_*.json"))
        bom_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        history = []
        for bom_file in bom_files[:limit]:
            async with aiofiles.open(bom_file, 'r') as f:
                data = json.loads(await f.read())
                # Include only summary info
                history.append({
                    "record_id": data["record_id"],
                    "scan_id": data["scan_id"],
                    "timestamp": data["timestamp"],
                    "component_count": len(data["components"])
                })
        
        return history