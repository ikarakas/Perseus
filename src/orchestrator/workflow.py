"""
Workflow engine for orchestrating SBOM analysis pipeline
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
# Workflow orchestration (analyzers now use Syft instead of Docker containers)

from ..analyzers.factory import AnalyzerFactory
from ..sbom.generator import SBOMGenerator
from ..common.storage import ResultStorage
from ..api.models import AnalysisRequest, SBOMRequest, AnalysisResult
from ..monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """Orchestrates the SBOM generation workflow"""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        # Syft-based analysis - no Docker client needed for analyzers
        self.analyzer_factory = AnalyzerFactory()
        self.sbom_generator = SBOMGenerator()
        self.storage = ResultStorage()
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.metrics_collector = metrics_collector
        
    async def analyze_source(self, analysis_id: str, request: AnalysisRequest) -> None:
        """Analyze source code"""
        try:
            self.active_analyses[analysis_id] = {
                "status": "running",
                "start_time": datetime.utcnow(),
                "type": "source",
                "request": request.dict()
            }
            
            logger.info(f"Starting source analysis {analysis_id}")
            
            # Record analysis start in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_start(analysis_id, "source", request.language)
            
            # Get appropriate analyzer
            analyzer = self.analyzer_factory.get_source_analyzer(request.language)
            
            # Run analysis
            results = await analyzer.analyze(request.location, request.options)
            
            # Set the analysis ID in the results
            results.analysis_id = analysis_id
            
            # Store results
            self.storage.store_analysis_result(analysis_id, results)
            
            self.active_analyses[analysis_id].update({
                "status": "completed",
                "end_time": datetime.utcnow(),
                "components_found": len(results.components)
            })
            
            # Record analysis completion in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_completion(
                    analysis_id, "source", request.language, 
                    success=True, components_found=len(results.components)
                )
            
            logger.info(f"Completed source analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Source analysis {analysis_id} failed: {e}")
            self.active_analyses[analysis_id].update({
                "status": "failed",
                "error": str(e),
                "end_time": datetime.utcnow()
            })
            
            # Record analysis failure in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_completion(
                    analysis_id, "source", request.language, 
                    success=False, components_found=0
                )
    
    async def analyze_binary(self, analysis_id: str, request: AnalysisRequest) -> None:
        """Analyze binary files"""
        try:
            self.active_analyses[analysis_id] = {
                "status": "running",
                "start_time": datetime.utcnow(),
                "type": "binary",
                "request": request.dict()
            }
            
            logger.info(f"Starting binary analysis {analysis_id}")
            
            # Record analysis start in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_start(analysis_id, "binary")
            
            # Get binary analyzer
            analyzer = self.analyzer_factory.get_binary_analyzer()
            
            # Run analysis
            results = await analyzer.analyze(request.location, request.options)
            
            # Set the analysis ID in the results
            results.analysis_id = analysis_id
            
            # Store results
            self.storage.store_analysis_result(analysis_id, results)
            
            self.active_analyses[analysis_id].update({
                "status": "completed",
                "end_time": datetime.utcnow(),
                "components_found": len(results.components)
            })
            
            # Record analysis completion in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_completion(
                    analysis_id, "binary", None, 
                    success=True, components_found=len(results.components)
                )
            
            logger.info(f"Completed binary analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Binary analysis {analysis_id} failed: {e}")
            self.active_analyses[analysis_id].update({
                "status": "failed",
                "error": str(e),
                "end_time": datetime.utcnow()
            })
            
            # Record analysis failure in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_completion(
                    analysis_id, "binary", None, 
                    success=False, components_found=0
                )
    
    def get_analysis_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis status"""
        return self.active_analyses.get(analysis_id)
    
    def get_analysis_results(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Get analysis results"""
        return self.storage.get_analysis_result(analysis_id)
    
    async def generate_sbom(self, sbom_id: str, request: SBOMRequest) -> None:
        """Generate SBOM from analysis results"""
        try:
            logger.info(f"Starting SBOM generation {sbom_id}")
            start_time = datetime.utcnow()
            
            # Collect analysis results
            analysis_results = []
            for analysis_id in request.analysis_ids:
                result = self.storage.get_analysis_result(analysis_id)
                if result:
                    analysis_results.append(result)
            
            if not analysis_results:
                raise ValueError("No valid analysis results found")
            
            # Generate SBOM
            sbom_data = await self.sbom_generator.generate(
                analysis_results,
                request.format,
                request.include_licenses,
                request.include_vulnerabilities
            )
            
            # Store SBOM
            self.storage.store_sbom(sbom_id, sbom_data)
            
            # Record SBOM generation in metrics
            if self.metrics_collector:
                duration = (datetime.utcnow() - start_time).total_seconds()
                total_components = sum(len(result.components) for result in analysis_results)
                self.metrics_collector.record_sbom_generation(
                    request.format, duration, total_components, success=True
                )
            
            logger.info(f"Completed SBOM generation {sbom_id}")
            
        except Exception as e:
            logger.error(f"SBOM generation {sbom_id} failed: {e}")
            
            # Record SBOM generation failure in metrics
            if self.metrics_collector:
                self.metrics_collector.record_sbom_generation(
                    request.format, 0, 0, success=False
                )
            
            raise
    
    async def analyze_docker(self, analysis_id: str, request: AnalysisRequest) -> None:
        """Analyze Docker images"""
        try:
            self.active_analyses[analysis_id] = {
                "status": "running",
                "start_time": datetime.utcnow(),
                "type": "docker",
                "request": request.dict()
            }
            
            logger.info(f"Starting Docker image analysis {analysis_id} for {request.location}")
            
            # Record analysis start in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_start(analysis_id, "docker")
            
            # Get Docker analyzer
            analyzer = self.analyzer_factory.get_docker_analyzer()
            
            # Run analysis
            results = await analyzer.analyze(request.location, request.options)
            
            # Set the analysis ID in the results
            results.analysis_id = analysis_id
            
            # Store results
            self.storage.store_analysis_result(analysis_id, results)
            
            self.active_analyses[analysis_id].update({
                "status": "completed",
                "end_time": datetime.utcnow(),
                "components_found": len(results.components)
            })
            
            # Record analysis completion in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_completion(
                    analysis_id, "docker", None, 
                    success=True, components_found=len(results.components)
                )
            
            logger.info(f"Completed Docker image analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Docker image analysis {analysis_id} failed: {e}")
            self.active_analyses[analysis_id].update({
                "status": "failed",
                "error": str(e),
                "end_time": datetime.utcnow()
            })
            
            # Record analysis failure in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_completion(
                    analysis_id, "docker", None, 
                    success=False, components_found=0
                )
    
    def get_sbom(self, sbom_id: str) -> Optional[Dict[str, Any]]:
        """Get generated SBOM"""
        return self.storage.get_sbom(sbom_id)
    
    def validate_sbom(self, sbom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SBOM format"""
        return self.sbom_generator.validate(sbom_data)