# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Factory for creating appropriate analyzers based on language and type
"""

from typing import Optional
from .syft_analyzer import SyftSourceAnalyzer, SyftBinaryAnalyzer
from .syft_docker_analyzer import SyftDockerAnalyzer
from .cpp_analyzer import CppSourceAnalyzer
from .java_analyzer import JavaSourceAnalyzer
from .binary_analyzer import BinaryAnalyzer
from .os_analyzer import OSAnalyzer
from ..api.models import Language
import logging

logger = logging.getLogger(__name__)

class AnalyzerFactory:
    """Factory for creating analyzers"""
    
    def __init__(self, use_syft: bool = True):
        """Initialize factory
        
        Args:
            use_syft: Whether to use Syft analyzers (default) or legacy analyzers
        """
        self.use_syft = use_syft
    
    def get_source_analyzer(self, language: Optional[Language], analyze_imports: bool = False):
        """Get source code analyzer for specified language"""
        logger.info(f"Getting source analyzer - Language: {language}")
        
        # Always use JavaSourceAnalyzer for Java to support POM/Gradle analysis
        if language == Language.JAVA:
            logger.info(f"Using Java analyzer for POM/Gradle analysis")
            return JavaSourceAnalyzer()
        elif self.use_syft:
            logger.info(f"Using Syft analyzer for source code analysis")
            return SyftSourceAnalyzer()
        else:
            # Legacy analyzers
            if language == Language.CPP or language == Language.C:
                return CppSourceAnalyzer()
            else:
                raise ValueError(f"Unsupported source language: {language}")
    
    def get_binary_analyzer(self):
        """Get binary analyzer"""
        if self.use_syft:
            logger.info(f"Using Syft analyzer for binary analysis")
            return SyftBinaryAnalyzer()
        else:
            # Legacy analyzer
            return BinaryAnalyzer()
    
    def get_docker_analyzer(self):
        """Get Docker image analyzer"""
        logger.info(f"Using Syft analyzer for Docker image analysis")
        return SyftDockerAnalyzer()
    
    def get_os_analyzer(self):
        """Get OS-level analyzer"""
        logger.info(f"Using OS analyzer for operating system analysis")
        return OSAnalyzer()