"""REST API for telemetry data access."""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from .storage import TelemetryStorage
from .server import TelemetryServer


router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class TelemetryAPI:
    """API endpoints for telemetry data."""
    
    def __init__(self, storage: TelemetryStorage, server: Optional[TelemetryServer] = None):
        self.storage = storage
        self.server = server


# Global instance (will be initialized by main app)
telemetry_api: Optional[TelemetryAPI] = None


@router.get("/agents")
async def get_agents() -> Dict[str, Any]:
    """Get all registered agents."""
    # Create storage instance directly if API not initialized
    if not telemetry_api:
        from .storage import TelemetryStorage
        storage = TelemetryStorage()
        agents = await storage.get_all_agents()
    else:
        agents = await telemetry_api.storage.get_all_agents()
    
    # Time-based connection status
    from datetime import datetime, timezone
    HEARTBEAT_GRACE = 120  # seconds (2x default heartbeat interval)
    now = datetime.now(timezone.utc)
    for agent_id, agent in agents.items():
        last_seen_str = agent.get("last_seen") or agent.get("last_heartbeat")
        connected = False
        if last_seen_str:
            try:
                last_seen = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
                diff = (now - last_seen).total_seconds()
                if diff < HEARTBEAT_GRACE:
                    connected = True
            except Exception:
                pass
        agent["connected"] = connected
    
    # Optionally, add hard connection info if server is available
    if telemetry_api and telemetry_api.server:
        connected_agents = telemetry_api.server.get_connected_agents()
        for agent_id in agents:
            if agent_id in connected_agents:
                agents[agent_id]["connection_info"] = connected_agents[agent_id]
    
    return {
        "agents": agents,
        "total": len(agents)
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get specific agent information."""
    # Create storage instance directly if API not initialized
    if not telemetry_api:
        from .storage import TelemetryStorage
        storage = TelemetryStorage()
        agent_info = await storage.get_agent_info(agent_id)
    else:
        agent_info = await telemetry_api.storage.get_agent_info(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Add connection status
    if telemetry_api.server:
        connected_agents = telemetry_api.server.get_connected_agents()
        agent_info["connected"] = agent_id in connected_agents
        if agent_id in connected_agents:
            agent_info["connection_info"] = connected_agents[agent_id]
    
    return agent_info


@router.get("/agents/{agent_id}/bom/latest")
async def get_latest_bom(agent_id: str) -> Dict[str, Any]:
    """Get latest BOM data for an agent."""
    # Create storage instance directly if API not initialized
    if not telemetry_api:
        from .storage import TelemetryStorage
        storage = TelemetryStorage()
        bom_data = await storage.get_latest_bom(agent_id)
    else:
        bom_data = await telemetry_api.storage.get_latest_bom(agent_id)
    if not bom_data:
        raise HTTPException(status_code=404, detail=f"No BOM data found for agent {agent_id}")
    
    return bom_data


@router.get("/agents/{agent_id}/bom/history")
async def get_bom_history(
    agent_id: str,
    limit: int = Query(10, ge=1, le=100)
) -> Dict[str, Any]:
    """Get BOM history for an agent."""
    if not telemetry_api:
        raise HTTPException(status_code=503, detail="Telemetry service not initialized")
    
    history = await telemetry_api.storage.get_bom_history(agent_id, limit)
    
    return {
        "agent_id": agent_id,
        "history": history,
        "count": len(history)
    }


@router.post("/agents/{agent_id}/command")
async def send_command(agent_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
    """Queue a command for an agent."""
    if not telemetry_api:
        raise HTTPException(status_code=503, detail="Telemetry service not initialized")
    
    # Validate agent exists
    agent_info = await telemetry_api.storage.get_agent_info(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Add command to queue
    await telemetry_api.storage.add_command(agent_id, command)
    
    return {
        "status": "queued",
        "agent_id": agent_id,
        "command": command,
        "queued_at": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/status")
async def get_telemetry_status() -> Dict[str, Any]:
    """Get telemetry service status."""
    if not telemetry_api:
        raise HTTPException(status_code=503, detail="Telemetry service not initialized")
    
    agents = await telemetry_api.storage.get_all_agents()
    
    status = {
        "service": "active" if telemetry_api.server else "storage-only",
        "agents": {
            "total": len(agents),
            "active": sum(1 for a in agents.values() if a.get("status") == "active")
        }
    }
    
    if telemetry_api.server:
        connected = telemetry_api.server.get_connected_agents()
        status["server"] = {
            "connected_agents": len(connected),
            "host": telemetry_api.server.host,
            "port": telemetry_api.server.port
        }
    
    return status


@router.post("/purge")
async def purge_agents() -> Dict[str, Any]:
    """Purge all agent data and connections."""
    if not telemetry_api:
        raise HTTPException(status_code=503, detail="Telemetry service not initialized")
    
    try:
        # Get current counts before purging
        agents = await telemetry_api.storage.get_all_agents()
        connected_count = 0
        
        if telemetry_api.server:
            connected_agents = telemetry_api.server.get_connected_agents()
            connected_count = len(connected_agents)
            
            # Disconnect all connected agents
            await telemetry_api.server.disconnect_all_agents()
        
        # Purge all agent data from storage
        await telemetry_api.storage.purge_all_agents()
        
        return {
            "status": "success",
            "message": "All agent data and connections purged",
            "purged": {
                "total_agents": len(agents),
                "connected_agents": connected_count
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to purge agents: {str(e)}")


def init_telemetry_api(storage: TelemetryStorage, server: Optional[TelemetryServer] = None) -> None:
    """Initialize the telemetry API."""
    global telemetry_api
    telemetry_api = TelemetryAPI(storage, server)