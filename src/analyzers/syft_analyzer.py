# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Syft-based analyzer for comprehensive SBOM generation
"""

import os
import json
import subprocess
import asyncio
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
        """Find syft binary in PATH or common locations"""
        # Check if SYFT_PATH environment variable is set (useful for containers)
        env_syft_path = os.environ.get('SYFT_PATH')
        if env_syft_path and os.path.isfile(env_syft_path) and os.access(env_syft_path, os.X_OK):
            logger.info(f"Using SYFT_PATH from environment: {env_syft_path}")
            return env_syft_path
        
        # Check if we're running in a container
        is_container = os.path.exists('/.dockerenv') or os.environ.get('CONTAINER_ENV') == 'true'
        
        # First try 'which' command - using sync subprocess for init only
        try:
            result = subprocess.run(['which', 'syft'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                syft_path = result.stdout.strip()
                # Verify the binary actually exists and is executable
                if os.path.isfile(syft_path) and os.access(syft_path, os.X_OK):
                    logger.info(f"Found syft via which: {syft_path}")
                    return syft_path
        except Exception:
            pass
        
        # Try common locations based on environment
        if is_container:
            # Container paths (Linux)
            common_paths = [
                '/usr/local/bin/syft',
                '/usr/bin/syft',
                '/opt/syft/syft',
                os.path.expanduser('~/.local/bin/syft'),
            ]
        else:
            # Development paths (macOS/Linux)
            common_paths = [
                '/opt/homebrew/bin/syft',  # macOS ARM64
                '/usr/local/bin/syft',      # macOS Intel or Linux
                '/usr/bin/syft',            # Linux system
                '/home/linuxbrew/.linuxbrew/bin/syft',  # Linux homebrew
                os.path.expanduser('~/.local/bin/syft'),
                os.path.expanduser('~/go/bin/syft'),
            ]
        
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                logger.info(f"Found syft at: {path} (container={is_container})")
                return path
        
        # Try to find in PATH environment variable
        path_env = os.environ.get('PATH', '').split(os.pathsep)
        for directory in path_env:
            syft_path = os.path.join(directory, 'syft')
            if os.path.isfile(syft_path) and os.access(syft_path, os.X_OK):
                logger.info(f"Found syft in PATH at: {syft_path}")
                return syft_path
        
        logger.error(f"Syft not found. Searched paths: {common_paths}")
        logger.error(f"PATH environment: {os.environ.get('PATH', 'Not set')}")
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
        temp_output = None
        
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
            
            # Execute Syft asynchronously
            # Use SYFT_WORK_DIR env var or current directory
            work_dir = os.environ.get('SYFT_WORK_DIR', os.getcwd())
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=300  # 5 minute timeout
                )
                stdout_text = stdout.decode('utf-8') if stdout else ''
                stderr_text = stderr.decode('utf-8') if stderr else ''
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise subprocess.TimeoutExpired(cmd, 300)
            
            if process.returncode != 0:
                error_msg = stderr_text.strip() if stderr_text else "Unknown error"
                if not error_msg or error_msg == "":
                    error_msg = stdout_text.strip() if stdout_text else "No error output available"
                if not error_msg or error_msg == "":
                    error_msg = f"Command failed with return code {process.returncode}"
                logger.error(f"Syft command failed: {error_msg}")
                raise RuntimeError(f"Syft analysis failed: {error_msg}")
            
            # Parse Syft JSON output
            components = await self._parse_syft_output(temp_output)
            
            return components
            
        except subprocess.TimeoutExpired:
            logger.error("Syft analysis timed out")
            raise RuntimeError("Analysis timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Syft execution failed: {str(e)}")
            raise
        finally:
            # Always clean up temporary file
            if temp_output and os.path.exists(temp_output):
                try:
                    os.unlink(temp_output)
                    logger.debug(f"Cleaned up temporary file: {temp_output}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file {temp_output}: {cleanup_error}")
    
    async def _parse_syft_output(self, output_file: str) -> List[Component]:
        """Parse Syft JSON output into Component objects"""
        components = []
        
        try:
            # Check if the output file is empty (can happen with non-existent images)
            if os.path.getsize(output_file) == 0:
                logger.warning(f"Syft output file is empty: {output_file}")
                return components  # Return empty list
                
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
                
                # Try multiple locations where Syft stores Maven group/artifact info
                group_id = (metadata.get('groupId', '') or 
                           metadata.get('group', '') or
                           metadata.get('pomProperties', {}).get('groupId', '') or
                           metadata.get('pomProject', {}).get('groupId', ''))
                
                artifact_id = (metadata.get('artifactId', '') or
                              metadata.get('artifact', '') or
                              metadata.get('pomProperties', {}).get('artifactId', '') or
                              metadata.get('pomProject', {}).get('artifactId', '') or
                              name)
                
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
            process = await asyncio.create_subprocess_exec(
                self.syft_path, 'version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                stdout_text = stdout.decode('utf-8')
                # Parse version from output
                lines = stdout_text.strip().split('\n')
                for line in lines:
                    if 'version:' in line.lower() or 'syft' in line.lower():
                        return line.strip()
                return stdout_text.strip().split('\n')[0]
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