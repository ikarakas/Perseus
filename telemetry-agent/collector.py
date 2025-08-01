# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""OS BOM collector for telemetry agent."""
import platform
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

# Import the existing OS analyzer to reuse its logic
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyzers.os_analyzer import OSAnalyzer
from src.api.models import AnalysisResult, AnalysisOptions


logger = logging.getLogger(__name__)


class BOMCollector:
    """Collects OS BOM data for telemetry."""
    
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or self._generate_agent_id()
        self.os_analyzer = OSAnalyzer()
    
    def _generate_agent_id(self) -> str:
        """Generate a unique agent ID based on system info."""
        hostname = platform.node()
        mac = uuid.getnode()
        return f"{hostname}-{mac:x}"
    
    async def collect_bom(self, deep_scan: bool = False) -> Dict[str, Any]:
        """Collect OS BOM data."""
        logger.info(f"Starting BOM collection (deep_scan={deep_scan})")
        
        try:
            # Use the existing OS analyzer with proper options object
            options = AnalysisOptions(deep_scan=deep_scan)
            result = await self.os_analyzer.analyze(
                location="localhost",
                options=options
            )
            
            if result.status == "error":
                raise Exception(f"Analysis failed: {result.errors}")
            elif result.status == "completed_with_errors" and result.errors:
                logger.warning(f"Analysis completed with warnings: {result.errors}")
            
            # Format for telemetry
            bom_data = {
                "scan_id": str(uuid.uuid4()),
                "components": [self._format_component(c) for c in result.components],
                "metadata": {
                    **result.metadata,
                    "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent_id": self.agent_id,
                    "agent_version": "1.9.2",
                    "deep_scan": deep_scan
                }
            }
            
            logger.info(f"Collected {len(result.components)} components")
            return bom_data
            
        except Exception as e:
            logger.error(f"Failed to collect BOM: {e}")
            raise
    
    def _format_component(self, component) -> Dict[str, Any]:
        """Format component for telemetry transmission."""
        # Handle both dict and Pydantic Component objects
        if hasattr(component, 'model_dump'):
            # Pydantic model
            comp_dict = component.model_dump()
        elif hasattr(component, 'dict'):
            # Older Pydantic versions
            comp_dict = component.dict()
        else:
            # Regular dictionary
            comp_dict = component
            
        return {
            "name": comp_dict.get("name"),
            "version": comp_dict.get("version"),
            "type": comp_dict.get("type"),
            "purl": comp_dict.get("purl"),
            "metadata": comp_dict.get("metadata", {})
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        return {
            "hostname": platform.node(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }