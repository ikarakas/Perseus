"""
Syft-based analyzer for comprehensive SBOM generation
"""

import os
import json
import subprocess
import logging
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseAnalyzer
from ..api.models import AnalysisOptions, AnalysisResult, Component

logger = logging.getLogger(__name__)

class SyftAnalyzer(BaseAnalyzer):
    """Analyzer using Syft for comprehensive SBOM generation"""
    
    def __init__(self):
        self.syft_path = self._find_syft()
        if not self.syft_path:
            raise RuntimeError("Syft not found in PATH")
    
    def _find_syft(self) -> Optional[str]:
        """Find syft binary in PATH"""
        try:
            result = subprocess.run(['which', 'syft'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """Analyze using Syft"""
        try:
            logger.info(f"Starting Syft analysis of: {location}")
            
            # Check if location exists
            if not os.path.exists(location):
                raise FileNotFoundError(f"Location not found: {location}")
            
            # Run Syft analysis
            components = await self._run_syft_analysis(location, options)
            
            # Determine analysis type
            analysis_type = "directory" if os.path.isdir(location) else "file"
            
            return AnalysisResult(
                analysis_id="",  # Will be set by the workflow engine
                status="completed",
                components=components,
                metadata={
                    "analyzer": "syft",
                    "location": location,
                    "type": analysis_type,
                    "components_found": len(components),
                    "syft_version": await self._get_syft_version()
                }
            )
            
        except Exception as e:
            logger.error(f"Syft analysis failed: {str(e)}")
            return AnalysisResult(
                analysis_id="",  # Will be set by the workflow engine
                status="failed",
                components=[],
                metadata={
                    "analyzer": "syft",
                    "error": str(e),
                    "location": location
                }
            )
    
    async def _run_syft_analysis(self, location: str, options: Optional[AnalysisOptions] = None) -> List[Component]:
        """Run Syft analysis and parse results"""
        components = []
        
        try:
            # Create temporary file for Syft output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                temp_output = temp_file.name
            
            # Build Syft command
            cmd = [
                self.syft_path,
                'scan',
                location,
                '--output', f'syft-json={temp_output}',
                '--quiet'
            ]
            
            # Add scope if analyzing source code
            if options and hasattr(options, 'deep_scan') and options.deep_scan:
                cmd.extend(['--scope', 'all-layers'])
            else:
                cmd.extend(['--scope', 'squashed'])
            
            logger.info(f"Running Syft command: {' '.join(cmd)}")
            
            # Execute Syft
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.path.dirname(location) if os.path.isfile(location) else location
            )
            
            if result.returncode != 0:
                logger.error(f"Syft command failed: {result.stderr}")
                raise RuntimeError(f"Syft analysis failed: {result.stderr}")
            
            # Parse Syft JSON output
            components = await self._parse_syft_output(temp_output)
            
            # Clean up temporary file
            os.unlink(temp_output)
            
            return components
            
        except subprocess.TimeoutExpired:
            logger.error("Syft analysis timed out")
            raise RuntimeError("Analysis timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Syft execution failed: {str(e)}")
            raise
    
    async def _parse_syft_output(self, output_file: str) -> List[Component]:
        """Parse Syft JSON output into Component objects"""
        components = []
        
        try:
            with open(output_file, 'r') as f:
                syft_data = json.load(f)
            
            # Extract artifacts (packages) from Syft output
            artifacts = syft_data.get('artifacts', [])
            
            for artifact in artifacts:
                try:
                    component = await self._convert_syft_artifact_to_component(artifact)
                    if component:
                        components.append(component)
                except Exception as e:
                    logger.warning(f"Failed to convert artifact: {e}")
                    continue
            
            logger.info(f"Parsed {len(components)} components from Syft output")
            return components
            
        except Exception as e:
            logger.error(f"Failed to parse Syft output: {e}")
            raise
    
    async def _convert_syft_artifact_to_component(self, artifact: Dict[str, Any]) -> Optional[Component]:
        """Convert Syft artifact to Component object"""
        try:
            name = artifact.get('name', 'unknown')
            version = artifact.get('version', 'unknown')
            
            # Extract package type and language
            metadata = artifact.get('metadata', {})
            pkg_type = artifact.get('type', 'unknown')
            
            # Generate PURL if possible
            purl = self._generate_purl(artifact)
            
            # Extract licenses
            licenses = []
            if 'licenses' in artifact:
                licenses = [lic.get('value', '') for lic in artifact['licenses'] if lic.get('value')]
            
            # Extract locations
            locations = artifact.get('locations', [])
            source_location = locations[0].get('path') if locations else 'unknown'
            
            return Component(
                name=name,
                version=version,
                type=pkg_type,
                purl=purl,
                licenses=licenses,
                source_location=source_location,
                metadata={
                    'syft_type': pkg_type,
                    'syft_metadata': metadata,
                    'language': metadata.get('language', 'unknown'),
                    'locations': locations
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert artifact {artifact.get('name', 'unknown')}: {e}")
            return None
    
    def _generate_purl(self, artifact: Dict[str, Any]) -> str:
        """Generate Package URL (PURL) from Syft artifact"""
        try:
            pkg_type = artifact.get('type', 'generic')
            name = artifact.get('name', '')
            version = artifact.get('version', '')
            
            # Map Syft types to PURL types
            type_mapping = {
                'java-archive': 'maven',
                'java': 'maven',
                'npm': 'npm',
                'python': 'pypi',
                'gem': 'gem',
                'go-module': 'golang',
                'deb': 'deb',
                'rpm': 'rpm',
                'apk': 'apk',
                'conan': 'conan'
            }
            
            purl_type = type_mapping.get(pkg_type, 'generic')
            
            # Handle Maven packages
            if purl_type == 'maven':
                metadata = artifact.get('metadata', {})
                group_id = metadata.get('groupId', metadata.get('group', ''))
                artifact_id = metadata.get('artifactId', metadata.get('artifact', name))
                
                if group_id:
                    namespace = group_id
                    name = artifact_id
                else:
                    namespace = ''
                    name = name or artifact_id
                
                if namespace:
                    return f"pkg:{purl_type}/{namespace}/{name}@{version}"
            
            # Standard PURL format
            if name and version:
                return f"pkg:{purl_type}/{name}@{version}"
            elif name:
                return f"pkg:{purl_type}/{name}"
            else:
                return ""
                
        except Exception as e:
            logger.warning(f"Failed to generate PURL: {e}")
            return ""
    
    async def _get_syft_version(self) -> str:
        """Get Syft version"""
        try:
            result = subprocess.run([self.syft_path, 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse version from output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'version:' in line.lower() or 'syft' in line.lower():
                        return line.strip()
                return result.stdout.strip().split('\n')[0]
            return "unknown"
        except Exception:
            return "unknown"

class SyftSourceAnalyzer(SyftAnalyzer):
    """Syft analyzer specialized for source code"""
    
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """Analyze source code using Syft"""
        logger.info(f"Analyzing source code with Syft: {location}")
        
        # Set source-specific options
        if not options:
            options = AnalysisOptions()
        
        # Force deep scan for source code
        options.deep_scan = True
        
        result = await super().analyze(location, options)
        
        # Update metadata to indicate source analysis
        if result.metadata:
            result.metadata.update({
                'analysis_type': 'source',
                'deep_scan': True
            })
        
        return result

class SyftBinaryAnalyzer(SyftAnalyzer):
    """Syft analyzer specialized for binaries"""
    
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """Analyze binary files using Syft"""
        logger.info(f"Analyzing binary with Syft: {location}")
        
        result = await super().analyze(location, options)
        
        # Update metadata to indicate binary analysis
        if result.metadata:
            result.metadata.update({
                'analysis_type': 'binary'
            })
        
        return result