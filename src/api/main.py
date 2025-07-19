# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
FastAPI application for SBOM generation platform
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import logging
import time
from datetime import datetime
import os

from .models import AnalysisRequest, AnalysisResponse, SBOMRequest
from ..orchestrator.workflow import WorkflowEngine
from ..monitoring.metrics import MetricsCollector
from ..monitoring.dashboard import MonitoringDashboard
from ..telemetry.api import router as telemetry_router, init_telemetry_api
from ..telemetry.storage import TelemetryStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Perseus SBOM Platform",
    description="Enterprise SBOM & Vulnerability Management Platform",
    version="1.3.1"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize telemetry storage first
telemetry_storage = TelemetryStorage()

# Initialize telemetry server
from ..telemetry.server import TelemetryServer
telemetry_server = TelemetryServer(storage=telemetry_storage)

# Initialize workflow engine and monitoring
metrics_collector = MetricsCollector()
workflow_engine = WorkflowEngine(metrics_collector)
dashboard = MonitoringDashboard(metrics_collector, telemetry_storage)

# Initialize telemetry API with server
init_telemetry_api(telemetry_storage, telemetry_server)

# Include telemetry router
app.include_router(telemetry_router)

# Startup event to start telemetry server
@app.on_event("startup")
async def startup_event():
    """Start the telemetry server when the API starts."""
    import asyncio
    asyncio.create_task(telemetry_server.start())

# Add API metrics tracking middleware
@app.middleware("http")
async def track_api_requests(request: Request, call_next):
    """Track API requests for metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Record metrics
    metrics_collector.record_api_request(
        endpoint=request.url.path,
        method=request.method,
        response_time=response_time,
        status_code=response.status_code
    )
    
    return response

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup dashboard routes
dashboard.setup_routes(app)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SBOM Platform", "timestamp": datetime.utcnow()}

@app.post("/analyze/source", response_model=AnalysisResponse)
async def analyze_source(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Submit source code for analysis"""
    try:
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting source analysis {analysis_id} for {request.language}")
        
        # Start analysis in background
        background_tasks.add_task(
            workflow_engine.analyze_source,
            analysis_id,
            request
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Source code analysis initiated"
        )
    except Exception as e:
        logger.error(f"Error starting source analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/binary", response_model=AnalysisResponse)
async def analyze_binary(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Submit binary for analysis"""
    try:
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting binary analysis {analysis_id}")
        
        # Start analysis in background
        background_tasks.add_task(
            workflow_engine.analyze_binary,
            analysis_id,
            request
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Binary analysis initiated"
        )
    except Exception as e:
        logger.error(f"Error starting binary analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get analysis status"""
    try:
        status = workflow_engine.get_analysis_status(analysis_id)
        if not status:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return status
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get analysis results"""
    try:
        results = workflow_engine.get_analysis_results(analysis_id)
        if not results:
            raise HTTPException(status_code=404, detail="Analysis results not found")
        return results
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sbom/generate")
async def generate_sbom(request: SBOMRequest, background_tasks: BackgroundTasks):
    """Generate SBOM from analysis results"""
    try:
        sbom_id = str(uuid.uuid4())
        logger.info(f"Starting SBOM generation {sbom_id}")
        
        # Start SBOM generation in background
        background_tasks.add_task(
            workflow_engine.generate_sbom,
            sbom_id,
            request
        )
        
        return {"sbom_id": sbom_id, "status": "started", "message": "SBOM generation initiated"}
    except Exception as e:
        logger.error(f"Error starting SBOM generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/docker", response_model=AnalysisResponse)
async def analyze_docker(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Submit Docker image for analysis"""
    try:
        # Validate that the analysis type is Docker
        if request.type != "docker":
            raise HTTPException(status_code=400, detail="Analysis type must be 'docker'")
        
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting Docker image analysis {analysis_id} for {request.location}")
        
        # Start analysis in background
        background_tasks.add_task(
            workflow_engine.analyze_docker,
            analysis_id,
            request
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Docker image analysis initiated"
        )
    except Exception as e:
        logger.error(f"Error starting Docker analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/os", response_model=AnalysisResponse)
async def analyze_os(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Submit OS for analysis"""
    try:
        # Validate that the analysis type is OS
        if request.type != "os":
            raise HTTPException(status_code=400, detail="Analysis type must be 'os'")
        
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting OS analysis {analysis_id} for {request.location}")
        
        # Start analysis in background
        background_tasks.add_task(
            workflow_engine.analyze_os,
            analysis_id,
            request
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="OS analysis initiated"
        )
    except Exception as e:
        logger.error(f"Error starting OS analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sbom/{sbom_id}")
async def get_sbom(sbom_id: str):
    """Retrieve generated SBOM"""
    try:
        sbom = workflow_engine.get_sbom(sbom_id)
        if not sbom:
            raise HTTPException(status_code=404, detail="SBOM not found")
        return sbom
    except Exception as e:
        logger.error(f"Error getting SBOM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sbom/validate")
async def validate_sbom(sbom_data: Dict[str, Any]):
    """Validate SBOM format"""
    try:
        validation_result = workflow_engine.validate_sbom(sbom_data)
        return validation_result
    except Exception as e:
        logger.error(f"Error validating SBOM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vulnerabilities/scan/{analysis_id}")
async def get_vulnerability_scan(analysis_id: str):
    """Get vulnerability scan results for an analysis"""
    try:
        results = workflow_engine.get_analysis_results(analysis_id)
        if not results:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Extract vulnerability summary from metadata
        vulnerability_summary = results.vulnerability_summary or {}
        
        # Get detailed vulnerability data for components
        vulnerability_details = []
        for component in results.components:
            if component.vulnerability_count and component.vulnerability_count > 0:
                vulnerability_details.append({
                    "component_name": component.name,
                    "component_version": component.version,
                    "purl": component.purl,
                    "vulnerability_count": component.vulnerability_count,
                    "critical_vulnerabilities": component.critical_vulnerabilities or 0
                })
        
        return {
            "analysis_id": analysis_id,
            "summary": vulnerability_summary,
            "vulnerable_components": vulnerability_details,
            "scan_metadata": {
                "scan_performed": results.metadata.get("vulnerability_scan_performed", False),
                "scan_date": results.metadata.get("vulnerability_scan_date"),
                "total_components": len(results.components)
            }
        }
    except Exception as e:
        logger.error(f"Error getting vulnerability scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vulnerabilities/scan/component")
async def scan_single_component(component_data: Dict[str, Any]):
    """Scan a single component for vulnerabilities"""
    try:
        from ..api.models import Component
        from ..vulnerability.scanner import VulnerabilityScanner
        
        # Create component object
        component = Component(
            name=component_data.get("name"),
            version=component_data.get("version"),
            purl=component_data.get("purl"),
            type=component_data.get("type", "library")
        )
        
        # Scan for vulnerabilities
        scanner = VulnerabilityScanner()
        vulnerability_result = await scanner.scan_single_component(component)
        
        return {
            "component": {
                "name": component.name,
                "version": component.version,
                "purl": component.purl
            },
            "vulnerabilities": [
                {
                    "id": vuln.id,
                    "title": vuln.title,
                    "description": vuln.description,
                    "severity": vuln.severity,
                    "cvss_score": vuln.cvss.base_score if vuln.cvss else None,
                    "published": vuln.published.isoformat() if vuln.published else None,
                    "references": vuln.references,
                    "cwe_ids": vuln.cwe_ids,
                    "affected_versions": vuln.affected_versions,
                    "fixed_versions": vuln.fixed_versions
                }
                for vuln in vulnerability_result.vulnerabilities
            ],
            "scan_metadata": {
                "scan_date": datetime.utcnow().isoformat(),
                "scanner": "OSV",
                "vulnerability_count": len(vulnerability_result.vulnerabilities)
            }
        }
    except Exception as e:
        logger.error(f"Error scanning component: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vulnerabilities/summary")
async def get_vulnerability_summary():
    """Get overall vulnerability summary across all analyses"""
    try:
        # This is a placeholder - in a real implementation, you'd aggregate across all analyses
        return {
            "total_analyses_with_vulnerabilities": 0,
            "total_vulnerabilities_found": 0,
            "severity_breakdown": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "most_vulnerable_components": [],
            "scan_statistics": {
                "total_scans_performed": 0,
                "successful_scans": 0,
                "failed_scans": 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting vulnerability summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vulnerabilities/database/update")
async def update_vulnerability_database():
    """Update the local vulnerability database"""
    try:
        from ..vulnerability.grype_scanner import GrypeScanner
        
        scanner = GrypeScanner()
        result = scanner._update_database()
        
        return {
            "status": "success",
            "message": "Vulnerability database update initiated",
            "details": result
        }
    except Exception as e:
        logger.error(f"Error updating vulnerability database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vulnerabilities/database/status")
async def get_vulnerability_database_status():
    """Get vulnerability database status"""
    try:
        from ..vulnerability.grype_scanner import GrypeScanner
        
        scanner = GrypeScanner()
        status = scanner.get_status()
        
        return status
    except Exception as e:
        logger.error(f"Error getting vulnerability database status: {e}")
        raise HTTPException(status_code=500, detail=str(e))