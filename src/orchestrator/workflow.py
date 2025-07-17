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
from ..vulnerability.scanner import VulnerabilityScanner

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
        self.vulnerability_scanner = VulnerabilityScanner()
        
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
            analyze_imports = request.options.analyze_imports if request.options else False
            logger.info(f"Analyze imports option: {analyze_imports}, Options: {request.options}")
            analyzer = self.analyzer_factory.get_source_analyzer(request.language, analyze_imports)
            
            # Run analysis
            results = await analyzer.analyze(request.location, request.options)
            
            # Set the analysis ID in the results
            results.analysis_id = analysis_id
            
            # Run vulnerability scanning if enabled
            if request.options and request.options.include_vulnerabilities:
                await self._add_vulnerability_data(results)
            
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
    
    async def analyze_os(self, analysis_id: str, request: AnalysisRequest) -> None:
        """Analyze operating system"""
        try:
            self.active_analyses[analysis_id] = {
                "status": "running",
                "start_time": datetime.utcnow(),
                "type": "os",
                "request": request.dict()
            }
            
            logger.info(f"Starting OS analysis {analysis_id}")
            
            # Record analysis start in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_start(analysis_id, "os")
            
            # Get OS analyzer
            analyzer = self.analyzer_factory.get_os_analyzer()
            
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
                    analysis_id, "os", None, 
                    success=True, components_found=len(results.components)
                )
            
            logger.info(f"Completed OS analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"OS analysis {analysis_id} failed: {e}")
            self.active_analyses[analysis_id].update({
                "status": "failed",
                "error": str(e),
                "end_time": datetime.utcnow()
            })
            
            # Record analysis failure in metrics
            if self.metrics_collector:
                self.metrics_collector.record_analysis_completion(
                    analysis_id, "os", None, 
                    success=False, components_found=0
                )
    
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
    
    async def _add_vulnerability_data(self, analysis_result: AnalysisResult) -> None:
        """Add vulnerability data to analysis results"""
        try:
            logger.info(f"Starting vulnerability scan for {len(analysis_result.components)} components")
            
            # Scan for vulnerabilities
            vuln_data = await self.vulnerability_scanner.scan_analysis_result(analysis_result)
            
            # Add vulnerability summary to analysis result
            analysis_result.vulnerability_summary = vuln_data['summary']
            
            # Update component vulnerability counts
            for component in analysis_result.components:
                comp_vuln = next(
                    (cv for cv in vuln_data['scan_results'] if cv.component_name == component.name),
                    None
                )
                if comp_vuln:
                    component.vulnerability_count = len(comp_vuln.vulnerabilities)
                    component.critical_vulnerabilities = sum(
                        1 for v in comp_vuln.vulnerabilities if v.severity == "critical"
                    )
                else:
                    component.vulnerability_count = 0
                    component.critical_vulnerabilities = 0
            
            # Update analysis metadata
            analysis_result.metadata.update({
                'vulnerability_scan_performed': True,
                'vulnerability_scan_date': datetime.utcnow().isoformat(),
                'total_vulnerabilities': vuln_data['summary']['total_vulnerabilities'],
                'vulnerable_components': vuln_data['summary']['vulnerable_components']
            })
            
            logger.info(f"Vulnerability scan completed: {vuln_data['summary']['total_vulnerabilities']} vulnerabilities found")
            
        except Exception as e:
            logger.error(f"Vulnerability scanning failed: {e}")
            analysis_result.vulnerability_summary = {
                'error': str(e),
                'scan_failed': True
            }
            analysis_result.metadata.update({
                'vulnerability_scan_performed': False,
                'vulnerability_scan_error': str(e)
            })
    
    def validate_sbom(self, sbom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SBOM format"""
        return self.sbom_generator.validate(sbom_data)