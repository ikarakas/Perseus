"""
Tests for Docker workflow integration
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add the src directory to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from orchestrator.workflow import WorkflowEngine
from api.models import AnalysisRequest, AnalysisOptions, AnalysisResult, Component
from analyzers.factory import AnalyzerFactory


class TestDockerWorkflow:
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Mock metrics collector"""
        return Mock()
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage"""
        return Mock()
    
    @pytest.fixture
    def workflow_engine(self, mock_metrics_collector):
        """Create workflow engine with mocked dependencies"""
        with patch('orchestrator.workflow.AnalyzerFactory') as mock_factory, \
             patch('orchestrator.workflow.SBOMGenerator'), \
             patch('orchestrator.workflow.ResultStorage') as mock_storage:
            
            engine = WorkflowEngine(mock_metrics_collector)
            engine.storage = mock_storage.return_value
            return engine
    
    @pytest.fixture
    def docker_request(self):
        """Create a Docker analysis request"""
        return AnalysisRequest(
            type="docker",
            location="nginx:latest",
            options=AnalysisOptions(deep_scan=True)
        )
    
    @pytest.fixture
    def mock_analysis_result(self):
        """Mock analysis result with Docker components"""
        return AnalysisResult(
            analysis_id="test-analysis-id",
            status="completed",
            components=[
                Component(
                    name="nginx",
                    version="1.21.6",
                    type="deb",
                    purl="pkg:deb/nginx@1.21.6",
                    licenses=["Apache-2.0"]
                ),
                Component(
                    name="openssl",
                    version="1.1.1f",
                    type="deb",
                    purl="pkg:deb/openssl@1.1.1f",
                    licenses=["OpenSSL"]
                )
            ],
            metadata={
                "analyzer": "syft-docker",
                "type": "docker",
                "image": "nginx:latest",
                "components_found": 2
            }
        )
    
    @pytest.mark.asyncio
    async def test_analyze_docker_success(self, workflow_engine, docker_request, mock_analysis_result):
        """Test successful Docker analysis workflow"""
        # Mock the analyzer
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze.return_value = mock_analysis_result
        
        with patch.object(workflow_engine.analyzer_factory, 'get_docker_analyzer', return_value=mock_analyzer):
            
            await workflow_engine.analyze_docker("test-analysis-id", docker_request)
            
            # Verify analyzer was called
            mock_analyzer.analyze.assert_called_once_with(
                docker_request.location, 
                docker_request.options
            )
            
            # Verify workflow tracking
            assert "test-analysis-id" in workflow_engine.active_analyses
            analysis_info = workflow_engine.active_analyses["test-analysis-id"]
            assert analysis_info["status"] == "completed"
            assert analysis_info["type"] == "docker"
            assert analysis_info["components_found"] == 2
            
            # Verify storage
            workflow_engine.storage.store_analysis_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_docker_failure(self, workflow_engine, docker_request):
        """Test Docker analysis workflow failure handling"""
        # Mock analyzer that raises exception
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze.side_effect = Exception("Docker image not found")
        
        with patch.object(workflow_engine.analyzer_factory, 'get_docker_analyzer', return_value=mock_analyzer):
            
            await workflow_engine.analyze_docker("test-analysis-id", docker_request)
            
            # Verify failure tracking
            assert "test-analysis-id" in workflow_engine.active_analyses
            analysis_info = workflow_engine.active_analyses["test-analysis-id"]
            assert analysis_info["status"] == "failed"
            assert "Docker image not found" in analysis_info["error"]
            
            # Verify metrics recorded failure
            workflow_engine.metrics_collector.record_analysis_completion.assert_called_once_with(
                "test-analysis-id", "docker", None, success=False, components_found=0
            )
    
    @pytest.mark.asyncio
    async def test_analyze_docker_with_auth(self, workflow_engine):
        """Test Docker analysis with authentication"""
        docker_request = AnalysisRequest(
            type="docker",
            location="registry.example.com/private:latest",
            options=AnalysisOptions(
                docker_auth={
                    "username": "testuser",
                    "password": "testpass",
                    "registry": "registry.example.com"
                }
            )
        )
        
        mock_analyzer = AsyncMock()
        mock_result = AnalysisResult(
            analysis_id="test-analysis-id",
            status="completed",
            components=[],
            metadata={"analyzer": "syft-docker"}
        )
        mock_analyzer.analyze.return_value = mock_result
        
        with patch.object(workflow_engine.analyzer_factory, 'get_docker_analyzer', return_value=mock_analyzer):
            
            await workflow_engine.analyze_docker("test-analysis-id", docker_request)
            
            # Verify analyzer was called with auth options
            mock_analyzer.analyze.assert_called_once_with(
                docker_request.location,
                docker_request.options
            )
            
            # Verify auth was passed through
            args, kwargs = mock_analyzer.analyze.call_args
            options = args[1]
            assert options.docker_auth["username"] == "testuser"
    
    def test_get_analysis_status_docker(self, workflow_engine):
        """Test getting status of Docker analysis"""
        # Setup a completed Docker analysis
        workflow_engine.active_analyses["test-docker-id"] = {
            "status": "completed",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow(),
            "type": "docker",
            "components_found": 5,
            "request": {
                "type": "docker",
                "location": "nginx:latest"
            }
        }
        
        status = workflow_engine.get_analysis_status("test-docker-id")
        
        assert status is not None
        assert status["status"] == "completed"
        assert status["type"] == "docker"
        assert status["components_found"] == 5
    
    def test_get_analysis_results_docker(self, workflow_engine, mock_analysis_result):
        """Test getting results of Docker analysis"""
        # Mock storage to return Docker results
        workflow_engine.storage.get_analysis_result.return_value = mock_analysis_result
        
        results = workflow_engine.get_analysis_results("test-docker-id")
        
        assert results is not None
        assert results.status == "completed"
        assert len(results.components) == 2
        assert results.metadata["type"] == "docker"
        assert results.metadata["analyzer"] == "syft-docker"
    
    @pytest.mark.asyncio
    async def test_docker_analysis_metrics_recording(self, workflow_engine, docker_request, mock_analysis_result):
        """Test that Docker analysis metrics are properly recorded"""
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze.return_value = mock_analysis_result
        
        with patch.object(workflow_engine.analyzer_factory, 'get_docker_analyzer', return_value=mock_analyzer):
            
            await workflow_engine.analyze_docker("test-analysis-id", docker_request)
            
            # Verify metrics start was recorded
            workflow_engine.metrics_collector.record_analysis_start.assert_called_once_with(
                "test-analysis-id", "docker"
            )
            
            # Verify metrics completion was recorded
            workflow_engine.metrics_collector.record_analysis_completion.assert_called_once_with(
                "test-analysis-id", "docker", None, success=True, components_found=2
            )
    
    def test_analyzer_factory_docker_integration(self):
        """Test that AnalyzerFactory properly creates Docker analyzer"""
        factory = AnalyzerFactory()
        
        # Test that get_docker_analyzer method exists and returns correct type
        docker_analyzer = factory.get_docker_analyzer()
        
        # Should be able to import and create the analyzer
        from analyzers.syft_docker_analyzer import SyftDockerAnalyzer
        assert isinstance(docker_analyzer, SyftDockerAnalyzer)
    
    @pytest.mark.asyncio
    async def test_docker_analysis_timeout_handling(self, workflow_engine, docker_request):
        """Test Docker analysis timeout handling"""
        # Mock analyzer that takes too long
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze.side_effect = RuntimeError("Analysis timed out")
        
        with patch.object(workflow_engine.analyzer_factory, 'get_docker_analyzer', return_value=mock_analyzer):
            
            await workflow_engine.analyze_docker("test-analysis-id", docker_request)
            
            # Verify failure was recorded
            analysis_info = workflow_engine.active_analyses["test-analysis-id"]
            assert analysis_info["status"] == "failed"
            assert "timed out" in analysis_info["error"]
    
    @pytest.mark.asyncio
    async def test_docker_analysis_concurrent_requests(self, workflow_engine):
        """Test handling multiple concurrent Docker analysis requests"""
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze.return_value = AnalysisResult(
            analysis_id="",
            status="completed",
            components=[],
            metadata={"analyzer": "syft-docker"}
        )
        
        with patch.object(workflow_engine.analyzer_factory, 'get_docker_analyzer', return_value=mock_analyzer):
            
            # Submit multiple Docker analyses
            requests = [
                AnalysisRequest(type="docker", location="nginx:latest"),
                AnalysisRequest(type="docker", location="ubuntu:20.04"),
                AnalysisRequest(type="docker", location="alpine:3.14")
            ]
            
            # Run analyses concurrently
            import asyncio
            tasks = [
                workflow_engine.analyze_docker(f"test-{i}", req) 
                for i, req in enumerate(requests)
            ]
            await asyncio.gather(*tasks)
            
            # Verify all analyses were tracked
            assert len(workflow_engine.active_analyses) == 3
            for i in range(3):
                assert f"test-{i}" in workflow_engine.active_analyses
                assert workflow_engine.active_analyses[f"test-{i}"]["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__])