"""
Syft-based analyzer for Docker image SBOM generation
"""

import os
import re
import json
import subprocess
import logging
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

from .syft_analyzer import SyftAnalyzer
from ..api.models import AnalysisOptions, AnalysisResult, Component

logger = logging.getLogger(__name__)

class SyftDockerAnalyzer(SyftAnalyzer):
    """Analyzer using Syft for Docker image SBOM generation"""
    
    # Docker image reference patterns
    DOCKER_IMAGE_PATTERNS = [
        # docker:image:tag
        re.compile(r'^docker:([^:]+):([^:]+)$'),
        # docker:image (latest implied)
        re.compile(r'^docker:([^:]+)$'),
        # registry.example.com/namespace/image:tag
        re.compile(r'^([a-zA-Z0-9\.\-]+(?:\:[0-9]+)?)/([a-zA-Z0-9\.\-_/]+):([a-zA-Z0-9\.\-_]+)$'),
        # registry.example.com/namespace/image (latest implied)
        re.compile(r'^([a-zA-Z0-9\.\-]+(?:\:[0-9]+)?)/([a-zA-Z0-9\.\-_/]+)$'),
        # image:tag (dockerhub implied)
        re.compile(r'^([a-zA-Z0-9\.\-_]+):([a-zA-Z0-9\.\-_]+)$'),
        # image@sha256:digest
        re.compile(r'^([a-zA-Z0-9\.\-_/]+)@sha256:([a-f0-9]{64})$'),
    ]
    
    def _is_docker_image(self, location: str) -> bool:
        """Check if location is a Docker image reference"""
        for pattern in self.DOCKER_IMAGE_PATTERNS:
            if pattern.match(location):
                return True
        return location.startswith('docker:') or '@sha256:' in location
    
    def _normalize_docker_image(self, location: str) -> str:
        """Normalize Docker image reference for Syft"""
        # Remove docker: prefix if present
        if location.startswith('docker:'):
            location = location[7:]
        
        # Handle special cases
        if ':' not in location and '@' not in location:
            # No tag specified, Syft will use latest
            return location
            
        return location
    
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """Analyze Docker image using Syft"""
        try:
            if not self._is_docker_image(location):
                raise ValueError(f"Invalid Docker image reference: {location}")
            
            logger.info(f"Starting Docker image analysis: {location}")
            
            # Normalize image reference
            image_ref = self._normalize_docker_image(location)
            
            # Set up Docker authentication if provided
            if options and options.docker_auth:
                await self._setup_docker_auth(options.docker_auth)
            
            # Run Syft analysis on Docker image
            components = await self._run_docker_analysis(image_ref, options)
            
            return AnalysisResult(
                analysis_id="",  # Will be set by the workflow engine
                status="completed",
                components=components,
                metadata={
                    "analyzer": "syft-docker",
                    "image": image_ref,
                    "type": "docker",
                    "components_found": len(components),
                    "syft_version": await self._get_syft_version()
                }
            )
            
        except Exception as e:
            logger.error(f"Docker image analysis failed: {str(e)}")
            return AnalysisResult(
                analysis_id="",  # Will be set by the workflow engine
                status="failed",
                components=[],
                errors=[str(e)],
                metadata={
                    "analyzer": "syft-docker",
                    "error": str(e),
                    "image": location
                }
            )
    
    async def _setup_docker_auth(self, auth_config: Dict[str, str]) -> None:
        """Set up Docker authentication"""
        try:
            # Support for different auth methods
            if 'username' in auth_config and 'password' in auth_config:
                # Basic auth
                registry = auth_config.get('registry', 'docker.io')
                username = auth_config['username']
                password = auth_config['password']
                
                # Use docker login (Syft respects Docker's auth config)
                cmd = ['docker', 'login', registry, '-u', username, '--password-stdin']
                result = subprocess.run(
                    cmd,
                    input=password,
                    text=True,
                    capture_output=True
                )
                
                if result.returncode != 0:
                    logger.warning(f"Docker login failed: {result.stderr}")
                else:
                    logger.info(f"Successfully authenticated to {registry}")
                    
            elif 'config_path' in auth_config:
                # Use existing Docker config
                os.environ['DOCKER_CONFIG'] = auth_config['config_path']
                
        except Exception as e:
            logger.warning(f"Failed to set up Docker auth: {e}")
    
    async def _run_docker_analysis(self, image_ref: str, options: Optional[AnalysisOptions] = None) -> List[Component]:
        """Run Syft analysis on Docker image"""
        components = []
        
        try:
            # Create temporary file for Syft output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                temp_output = temp_file.name
            
            # Build Syft command for Docker image
            cmd = [
                self.syft_path,
                'scan',
                image_ref,  # Direct image reference
                '--output', f'syft-json={temp_output}',
                '--quiet'
            ]
            
            # Add scope for container images
            if options and options.deep_scan:
                # Analyze all layers
                cmd.extend(['--scope', 'all-layers'])
            else:
                # Default to squashed image
                cmd.extend(['--scope', 'squashed'])
            
            # Set timeout based on options
            timeout = 600  # 10 minutes default for Docker images
            if options and options.timeout_minutes:
                timeout = options.timeout_minutes * 60
            
            logger.info(f"Running Syft Docker command: {' '.join(cmd)}")
            
            # Execute Syft
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()  # Include any Docker auth env vars
            )
            
            if result.returncode != 0:
                logger.error(f"Syft Docker command failed: {result.stderr}")
                # Check for common Docker errors
                if 'no such image' in result.stderr.lower():
                    raise RuntimeError(f"Docker image not found: {image_ref}")
                elif 'unauthorized' in result.stderr.lower():
                    raise RuntimeError(f"Docker authentication failed for: {image_ref}")
                elif 'timeout' in result.stderr.lower():
                    raise RuntimeError(f"Docker pull timeout for: {image_ref}")
                else:
                    raise RuntimeError(f"Syft analysis failed: {result.stderr}")
            
            # Parse Syft JSON output
            components = await self._parse_syft_output(temp_output)
            
            # Clean up temporary file
            os.unlink(temp_output)
            
            return components
            
        except subprocess.TimeoutExpired:
            logger.error(f"Docker image analysis timed out after {timeout} seconds")
            raise RuntimeError(f"Analysis timed out for image: {image_ref}")
        except Exception as e:
            logger.error(f"Docker Syft execution failed: {str(e)}")
            raise
    
    async def _parse_syft_output(self, output_file: str) -> List[Component]:
        """Parse Syft JSON output with Docker-specific handling"""
        components = await super()._parse_syft_output(output_file)
        
        # Add Docker-specific metadata to components
        for component in components:
            if component.metadata:
                component.metadata['source'] = 'docker'
        
        return components