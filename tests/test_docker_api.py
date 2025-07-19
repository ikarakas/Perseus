# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Tests for Docker API endpoints
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from src.api.main import app
from src.api.models import AnalysisRequest, AnalysisOptions
from src.orchestrator.workflow import WorkflowEngine


class TestDockerAPI:
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_workflow_engine(self):
        """Mock workflow engine"""
        with patch('api.main.workflow_engine') as mock:
            yield mock
    
    def test_analyze_docker_endpoint_success(self, client, mock_workflow_engine):
        """Test successful Docker analysis submission"""
        request_data = {
            "type": "docker",
            "location": "nginx:latest",
            "options": {
                "deep_scan": True
            }
        }
        
        response = client.post("/analyze/docker", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "started"
        assert data["message"] == "Docker image analysis initiated"
        
        # Verify workflow engine was called
        mock_workflow_engine.analyze_docker.assert_called_once()
    
    def test_analyze_docker_wrong_type(self, client):
        """Test Docker endpoint with wrong analysis type"""
        request_data = {
            "type": "source",  # Wrong type
            "location": "nginx:latest"
        }
        
        response = client.post("/analyze/docker", json=request_data)
        
        assert response.status_code == 400
        assert "Analysis type must be 'docker'" in response.json()["detail"]
    
    def test_analyze_docker_with_registry_auth(self, client, mock_workflow_engine):
        """Test Docker analysis with registry authentication"""
        request_data = {
            "type": "docker",
            "location": "registry.example.com/private:latest",
            "options": {
                "deep_scan": True,
                "docker_auth": {
                    "username": "testuser",
                    "password": "testpass",
                    "registry": "registry.example.com"
                }
            }
        }
        
        response = client.post("/analyze/docker", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
    
    def test_analyze_docker_missing_location(self, client):
        """Test Docker analysis without image location"""
        request_data = {
            "type": "docker"
            # Missing location
        }
        
        response = client.post("/analyze/docker", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_docker_invalid_json(self, client):
        """Test Docker analysis with invalid JSON"""
        response = client.post(
            "/analyze/docker", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_analyze_docker_workflow_exception(self, client, mock_workflow_engine):
        """Test Docker analysis when workflow raises exception"""
        mock_workflow_engine.analyze_docker.side_effect = Exception("Workflow error")
        
        request_data = {
            "type": "docker",
            "location": "nginx:latest"
        }
        
        response = client.post("/analyze/docker", json=request_data)
        
        assert response.status_code == 500
        assert "Workflow error" in response.json()["detail"]
    
    def test_analyze_docker_complex_image_references(self, client, mock_workflow_engine):
        """Test Docker analysis with various image reference formats"""
        test_images = [
            "nginx:latest",
            "ubuntu:20.04",
            "registry.example.com/namespace/image:tag",
            "gcr.io/project/service:v1.0",
            "docker:alpine:3.14",
            "image@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        ]
        
        for image in test_images:
            request_data = {
                "type": "docker",
                "location": image
            }
            
            response = client.post("/analyze/docker", json=request_data)
            
            assert response.status_code == 200, f"Failed for image: {image}"
            data = response.json()
            assert data["status"] == "started"
    
    def test_docker_analysis_request_model_validation(self):
        """Test AnalysisRequest model validation for Docker type"""
        # Valid Docker request
        valid_request = AnalysisRequest(
            type="docker",
            location="nginx:latest",
            options=AnalysisOptions(deep_scan=True)
        )
        assert valid_request.type == "docker"
        assert valid_request.location == "nginx:latest"
        assert valid_request.options.deep_scan is True
        
        # Docker request with auth
        auth_request = AnalysisRequest(
            type="docker",
            location="private.registry.io/app:v1",
            options=AnalysisOptions(
                docker_auth={
                    "username": "user",
                    "password": "pass"
                }
            )
        )
        assert auth_request.options.docker_auth["username"] == "user"
    
    def test_docker_integration_with_existing_endpoints(self, client):
        """Test that Docker endpoint doesn't interfere with existing endpoints"""
        # Test source analysis still works
        source_request = {
            "type": "source",
            "language": "java",
            "location": "/app/data/test"
        }
        
        response = client.post("/analyze/source", json=source_request)
        # Should not be 404 (endpoint exists)
        assert response.status_code in [200, 500]  # 500 if workflow fails, but endpoint exists
        
        # Test binary analysis still works
        binary_request = {
            "type": "binary",
            "location": "/app/data/test.jar"
        }
        
        response = client.post("/analyze/binary", json=binary_request)
        # Should not be 404 (endpoint exists)
        assert response.status_code in [200, 500]  # 500 if workflow fails, but endpoint exists


if __name__ == "__main__":
    pytest.main([__file__])