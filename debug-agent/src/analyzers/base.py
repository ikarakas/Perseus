# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Base analyzer class for all source and binary analyzers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..api.models import AnalysisOptions, AnalysisResult, Component

class BaseAnalyzer(ABC):
    """Base class for all analyzers"""
    
    @abstractmethod
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """Analyze the given location and return results"""
        pass
    
    def _create_component(self, name: str, version: str = None, license: str = None, 
                         purl: str = None, source_location: str = None) -> Component:
        """Helper method to create a component"""
        return Component(
            name=name,
            version=version,
            license=license,
            purl=purl,
            source_location=source_location
        )
    
    def _parse_version(self, version_string: str) -> str:
        """Parse and normalize version string"""
        if not version_string:
            return "unknown"
        
        # Clean up common version formats
        version = version_string.strip()
        if version.startswith('v'):
            version = version[1:]
        
        return version