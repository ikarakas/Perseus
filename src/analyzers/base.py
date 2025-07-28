# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Base analyzer class for all source and binary analyzers
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..api.models import AnalysisOptions, AnalysisResult, Component

logger = logging.getLogger(__name__)

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
    
    def _parse_location(self, location: str) -> str:
        """Parse and normalize location string to get file path"""
        # Remove file:// prefix if present
        if location.startswith('file://'):
            path = location[7:]
        elif location.startswith('git://'):
            # For git URLs, we'd need to clone first
            raise NotImplementedError("Git repository cloning not implemented")
        else:
            path = location
        
        # Normalize the path to handle trailing slashes and resolve . and .. components
        normalized_path = os.path.normpath(path)
        
        # If the original path ended with a slash and was a directory, preserve that intent
        # but os.path.normpath removes trailing slashes, so we need to check if it exists as a directory
        if path.endswith('/') and path != '/':
            # The user intended a directory path, verify it exists as a directory
            if os.path.exists(normalized_path) and os.path.isdir(normalized_path):
                logger.debug(f"Normalized directory path: {path} -> {normalized_path}")
                return normalized_path
            elif os.path.exists(normalized_path.rstrip('/')) and os.path.isdir(normalized_path.rstrip('/')):
                # Sometimes normpath might add/remove slashes, check without trailing slash
                return normalized_path.rstrip('/')
        
        # For paths without trailing slashes or when path doesn't exist yet, return normalized path
        logger.debug(f"Normalized path: {path} -> {normalized_path}")
        return normalized_path