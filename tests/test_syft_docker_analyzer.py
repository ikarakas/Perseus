"""
Tests for Docker image analysis using Syft
"""

import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch, AsyncMock
import subprocess

from src.analyzers.syft_docker_analyzer import SyftDockerAnalyzer
from src.api.models import AnalysisOptions, AnalysisResult, Component


class TestSyftDockerAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        """Create a Docker analyzer instance for testing"""
        with patch.object(SyftDockerAnalyzer, '_find_syft', return_value='/usr/local/bin/syft'):
            return SyftDockerAnalyzer()
    
    @pytest.fixture
    def mock_syft_output(self):
        """Mock Syft JSON output for testing"""
        return {
            "artifacts": [
                {
                    "name": "nginx",
                    "version": "1.21.6",
                    "type": "deb",
                    "locations": [{"path": "/var/lib/dpkg/status"}],
                    "licenses": [{"value": "Apache-2.0"}],
                    "metadata": {
                        "architecture": "amd64",
                        "maintainer": "nginx packaging <nginx-packaging@f5.com>"
                    }
                },
                {
                    "name": "openssl",
                    "version": "1.1.1f",
                    "type": "deb",
                    "locations": [{"path": "/var/lib/dpkg/status"}],
                    "licenses": [{"value": "OpenSSL"}],
                    "metadata": {
                        "architecture": "amd64"
                    }
                }
            ]
        }
    
    def test_is_docker_image_valid_formats(self, analyzer):
        """Test Docker image format detection"""
        # Valid Docker image formats
        valid_images = [
            "nginx:latest",
            "docker:ubuntu:20.04",
            "registry.example.com/myapp:v1.0",
            "gcr.io/project/image:tag",
            "image@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        ]
        
        for image in valid_images:
            assert analyzer._is_docker_image(image), f"Should recognize {image} as Docker image"
    
    def test_is_docker_image_invalid_formats(self, analyzer):
        """Test rejection of non-Docker paths"""
        # Invalid Docker image formats
        invalid_images = [
            "/path/to/file",
            "file://local/path",
            "http://example.com",
            "just-a-string",
            ""
        ]
        
        for image in invalid_images:
            assert not analyzer._is_docker_image(image), f"Should NOT recognize {image} as Docker image"
    
    def test_normalize_docker_image(self, analyzer):
        """Test Docker image normalization"""
        test_cases = [
            ("docker:nginx:latest", "nginx:latest"),
            ("docker:ubuntu", "ubuntu"),
            ("nginx:1.21", "nginx:1.21"),
            ("registry.com/app:v1", "registry.com/app:v1")
        ]
        
        for input_image, expected in test_cases:
            result = analyzer._normalize_docker_image(input_image)
            assert result == expected, f"Expected {expected}, got {result}"
    
    @pytest.mark.asyncio
    async def test_analyze_success(self, analyzer, mock_syft_output):
        """Test successful Docker image analysis"""
        with patch.object(analyzer, '_run_docker_analysis') as mock_run:
            # Setup mock to return test components
            mock_components = [
                Component(
                    name="nginx",
                    version="1.21.6",
                    type="deb",
                    purl="pkg:deb/nginx@1.21.6",
                    licenses=["Apache-2.0"]
                )
            ]
            mock_run.return_value = mock_components
            
            result = await analyzer.analyze("nginx:latest")
            
            assert isinstance(result, AnalysisResult)
            assert result.status == "completed"
            assert len(result.components) == 1
            assert result.components[0].name == "nginx"
            assert result.metadata["analyzer"] == "syft-docker"
            assert result.metadata["type"] == "docker"
    
    @pytest.mark.asyncio
    async def test_analyze_invalid_image(self, analyzer):
        """Test analysis with invalid Docker image reference"""
        result = await analyzer.analyze("/invalid/path")
        
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert "Invalid Docker image reference" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_analyze_with_auth(self, analyzer):
        """Test analysis with Docker authentication"""
        options = AnalysisOptions(
            docker_auth={
                "username": "testuser",
                "password": "testpass",
                "registry": "registry.example.com"
            }
        )
        
        with patch.object(analyzer, '_setup_docker_auth') as mock_auth, \
             patch.object(analyzer, '_run_docker_analysis', return_value=[]):
            
            await analyzer.analyze("registry.example.com/private:latest", options)
            
            mock_auth.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_docker_auth_basic(self, analyzer):
        """Test Docker basic authentication setup"""
        auth_config = {
            "username": "testuser",
            "password": "testpass",
            "registry": "registry.example.com"
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            await analyzer._setup_docker_auth(auth_config)
            
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert 'docker' in call_args[0][0]
            assert 'login' in call_args[0][0]
            assert auth_config['registry'] in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_setup_docker_auth_config_path(self, analyzer):
        """Test Docker config path authentication"""
        auth_config = {
            "config_path": "/home/user/.docker"
        }
        
        with patch.dict(os.environ, {}, clear=True):
            await analyzer._setup_docker_auth(auth_config)
            assert os.environ.get('DOCKER_CONFIG') == "/home/user/.docker"
    
    @pytest.mark.asyncio
    async def test_run_docker_analysis(self, analyzer, mock_syft_output):
        """Test Docker analysis execution"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(mock_syft_output, temp_file)
            temp_output = temp_file.name
        
        try:
            with patch('subprocess.run') as mock_run, \
                 patch('tempfile.NamedTemporaryFile') as mock_temp:
                
                # Configure mocks
                mock_run.return_value.returncode = 0
                mock_run.return_value.stderr = ""
                
                mock_temp.return_value.__enter__.return_value.name = temp_output
                
                components = await analyzer._run_docker_analysis("nginx:latest")
                
                assert len(components) == 2
                assert components[0].name == "nginx"
                assert components[1].name == "openssl"
                
                # Verify Syft command was called correctly
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert 'syft' in call_args[0]
                assert 'packages' in call_args
                assert 'nginx:latest' in call_args
                
        finally:
            os.unlink(temp_output)
    
    @pytest.mark.asyncio
    async def test_run_docker_analysis_timeout(self, analyzer):
        """Test Docker analysis timeout handling"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(['syft'], 600)
            
            with pytest.raises(RuntimeError, match="Analysis timed out"):
                await analyzer._run_docker_analysis("nginx:latest")
    
    @pytest.mark.asyncio
    async def test_run_docker_analysis_image_not_found(self, analyzer):
        """Test handling of non-existent Docker images"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "no such image: nonexistent:latest"
            
            with pytest.raises(RuntimeError, match="Docker image not found"):
                await analyzer._run_docker_analysis("nonexistent:latest")
    
    @pytest.mark.asyncio
    async def test_run_docker_analysis_unauthorized(self, analyzer):
        """Test handling of unauthorized Docker registry access"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "unauthorized: access denied"
            
            with pytest.raises(RuntimeError, match="Docker authentication failed"):
                await analyzer._run_docker_analysis("private/image:latest")
    
    @pytest.mark.asyncio
    async def test_parse_syft_output_with_docker_metadata(self, analyzer, mock_syft_output):
        """Test parsing Syft output with Docker-specific metadata"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(mock_syft_output, temp_file)
            temp_output = temp_file.name
        
        try:
            components = await analyzer._parse_syft_output(temp_output)
            
            assert len(components) == 2
            
            # Check Docker-specific metadata
            for component in components:
                assert component.metadata['source'] == 'docker'
                assert 'syft_type' in component.metadata
                assert 'language' in component.metadata
                
        finally:
            os.unlink(temp_output)
    
    def test_generate_purl_docker_specific(self, analyzer):
        """Test PURL generation for Docker-specific packages"""
        # Test Debian package from Docker image
        artifact = {
            "name": "nginx",
            "version": "1.21.6",
            "type": "deb",
            "metadata": {}
        }
        
        purl = analyzer._generate_purl(artifact)
        assert purl == "pkg:deb/nginx@1.21.6"
        
        # Test Alpine package
        artifact = {
            "name": "musl",
            "version": "1.2.2",
            "type": "apk",
            "metadata": {}
        }
        
        purl = analyzer._generate_purl(artifact)
        assert purl == "pkg:apk/musl@1.2.2"


if __name__ == "__main__":
    pytest.main([__file__])