# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
FastAPI application for SBOM generation platform
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from sqlalchemy.orm import Session
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
from ..monitoring.database_dashboard import DatabaseDashboard
from ..monitoring.component_search_ui import setup_component_search_routes
from ..telemetry.api import router as telemetry_router, init_telemetry_api
from ..telemetry.storage import TelemetryStorage
from .cicd import router as cicd_router
from ..database import init_database, get_db_session, test_connection
from ..database.repositories import (
    AnalysisRepository, ComponentRepository, SBOMRepository, 
    VulnerabilityRepository, VulnerabilityScanRepository
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Perseus SBOM Platform",
    description="Enterprise SBOM & Vulnerability Management Platform",
    version="1.4.0"
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
database_dashboard = DatabaseDashboard()

# Initialize telemetry API with server
init_telemetry_api(telemetry_storage, telemetry_server)

# Include telemetry router
app.include_router(telemetry_router)

# Include CI/CD integration router
app.include_router(cicd_router)

# Startup event to start telemetry server and initialize database
@app.on_event("startup")
async def startup_event():
    """Start the telemetry server and initialize database when the API starts."""
    # Initialize database
    logger.info("Initializing database connection...")
    try:
        init_database()
        if not test_connection():
            logger.error("Database connection failed!")
            raise Exception("Database connection failed")
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Continue without database for backwards compatibility
        logger.warning("Continuing without database - using file-based storage")
    
    # Start telemetry server
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
database_dashboard.setup_routes(app)
setup_component_search_routes(app)

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


# New Database-backed Endpoints

@app.get("/api/v1/analyses")
async def list_analyses(
    status: Optional[str] = None,
    analysis_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db_session)
):
    """List analyses with optional filtering"""
    try:
        analysis_repo = AnalysisRepository(db)
        
        if status:
            from ..database.models import AnalysisStatus
            status_enum = AnalysisStatus(status)
            analyses = analysis_repo.get_by_status(status_enum, limit=limit)
        elif analysis_type:
            analyses = analysis_repo.get_analyses_by_type(analysis_type, limit=limit)
        else:
            analyses = analysis_repo.get_all(limit=limit, offset=offset)
        
        return {
            "analyses": [
                {
                    "analysis_id": a.analysis_id,
                    "status": a.status.value,
                    "analysis_type": a.analysis_type,
                    "location": a.location,
                    "component_count": a.component_count,
                    "vulnerability_count": a.vulnerability_count,
                    "created_at": a.created_at,
                    "completed_at": a.completed_at,
                    "duration_seconds": a.duration_seconds
                }
                for a in analyses
            ],
            "total": len(analyses)
        }
    except Exception as e:
        logger.error(f"Error listing analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analyses/{analysis_id}")
async def get_analysis_detail(analysis_id: str, db: Session = Depends(get_db_session)):
    """Get detailed analysis information from database"""
    try:
        analysis_repo = AnalysisRepository(db)
        analysis = analysis_repo.get_with_components(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "analysis_id": analysis.analysis_id,
            "status": analysis.status.value,
            "analysis_type": analysis.analysis_type,
            "language": analysis.language,
            "location": analysis.location,
            "component_count": analysis.component_count,
            "vulnerability_count": analysis.vulnerability_count,
            "critical_vulnerability_count": analysis.critical_vulnerability_count,
            "high_vulnerability_count": analysis.high_vulnerability_count,
            "created_at": analysis.created_at,
            "started_at": analysis.started_at,
            "completed_at": analysis.completed_at,
            "duration_seconds": analysis.duration_seconds,
            "metadata": analysis.analysis_metadata,
            "errors": analysis.errors,
            "components": [
                {
                    "name": c.name,
                    "version": c.version,
                    "type": c.type.value if c.type else None,
                    "purl": c.purl,
                    "vulnerability_count": c.vulnerability_count,
                    "critical_vulnerabilities": c.critical_vulnerabilities,
                    "high_vulnerabilities": c.high_vulnerabilities
                }
                for c in analysis.components
            ]
        }
    except Exception as e:
        logger.error(f"Error getting analysis detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/components/search")
async def search_components(
    q: str,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """Search components by name or description"""
    try:
        component_repo = ComponentRepository(db)
        components = component_repo.search_components(q, limit=limit)
        
        return {
            "components": [
                {
                    "name": c.name,
                    "version": c.version,
                    "type": c.type.value if c.type else None,
                    "purl": c.purl,
                    "vulnerability_count": c.vulnerability_count,
                    "critical_vulnerabilities": c.critical_vulnerabilities,
                    "description": c.description,
                    "analysis_id": str(c.analysis_id)
                }
                for c in components
            ],
            "total": len(components)
        }
    except Exception as e:
        logger.error(f"Error searching components: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/components/vulnerable")
async def get_vulnerable_components(
    min_severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """Get components with vulnerabilities"""
    try:
        component_repo = ComponentRepository(db)
        components = component_repo.get_vulnerable_components(min_severity)[:limit]
        
        return {
            "vulnerable_components": [
                {
                    "name": c.name,
                    "version": c.version,
                    "type": c.type.value if c.type else None,
                    "purl": c.purl,
                    "vulnerability_count": c.vulnerability_count,
                    "critical_vulnerabilities": c.critical_vulnerabilities,
                    "high_vulnerabilities": c.high_vulnerabilities,
                    "analysis_id": str(c.analysis_id)
                }
                for c in components
            ],
            "total": len(components)
        }
    except Exception as e:
        logger.error(f"Error getting vulnerable components: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/statistics/dashboard")
async def get_dashboard_statistics(db: Session = Depends(get_db_session)):
    """Get comprehensive statistics for dashboard"""
    try:
        analysis_repo = AnalysisRepository(db)
        component_repo = ComponentRepository(db)
        
        analysis_stats = analysis_repo.get_statistics(days=30)
        vulnerability_summary = analysis_repo.get_vulnerability_summary()
        component_stats = component_repo.get_component_statistics()
        top_vulnerable = component_repo.get_top_vulnerable_components(limit=10)
        
        return {
            "analysis_statistics": analysis_stats,
            "vulnerability_summary": vulnerability_summary,
            "component_statistics": component_stats,
            "top_vulnerable_components": top_vulnerable,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/components/unique")
async def get_unique_components(db: Session = Depends(get_db_session)):
    """Get unique components across all analyses"""
    try:
        component_repo = ComponentRepository(db)
        unique_components = component_repo.get_unique_components()
        
        return {
            "unique_components": unique_components,
            "total": len(unique_components)
        }
    except Exception as e:
        logger.error(f"Error getting unique components: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# SBOM Database Endpoints

@app.get("/api/v1/sboms")
async def list_sboms(
    format: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """List SBOMs with optional format filtering"""
    try:
        sbom_repo = SBOMRepository(db)
        
        if format:
            sboms = sbom_repo.get_by_format(format, limit=limit)
        else:
            sboms = sbom_repo.get_recent_sboms(limit=limit)
        
        return {
            "sboms": [
                {
                    "sbom_id": s.sbom_id,
                    "format": s.format,
                    "spec_version": s.spec_version,
                    "name": s.name,
                    "namespace": s.namespace,
                    "created_by": s.created_by,
                    "created_at": s.created_at,
                    "analysis_id": str(s.analysis_id)
                }
                for s in sboms
            ],
            "total": len(sboms)
        }
    except Exception as e:
        logger.error(f"Error listing SBOMs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sboms/{sbom_id}")
async def get_sbom_detail(sbom_id: str, db: Session = Depends(get_db_session)):
    """Get detailed SBOM information including content"""
    try:
        sbom_repo = SBOMRepository(db)
        sbom = sbom_repo.get_with_analysis(sbom_id)
        
        if not sbom:
            raise HTTPException(status_code=404, detail="SBOM not found")
        
        return {
            "sbom_id": sbom.sbom_id,
            "format": sbom.format,
            "spec_version": sbom.spec_version,
            "name": sbom.name,
            "namespace": sbom.namespace,
            "created_by": sbom.created_by,
            "content": sbom.content,
            "created_at": sbom.created_at,
            "analysis": {
                "analysis_id": sbom.analysis.analysis_id,
                "analysis_type": sbom.analysis.analysis_type,
                "location": sbom.analysis.location,
                "component_count": sbom.analysis.component_count
            } if sbom.analysis else None
        }
    except Exception as e:
        logger.error(f"Error getting SBOM detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sboms/statistics")
async def get_sbom_statistics(db: Session = Depends(get_db_session)):
    """Get SBOM generation statistics"""
    try:
        sbom_repo = SBOMRepository(db)
        stats = sbom_repo.get_sbom_statistics()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting SBOM statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Vulnerability Database Endpoints

@app.get("/api/v1/vulnerabilities")
async def list_vulnerabilities(
    severity: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """List vulnerabilities with optional filtering"""
    try:
        vuln_repo = VulnerabilityRepository(db)
        
        if search:
            vulnerabilities = vuln_repo.search_vulnerabilities(search, limit=limit)
        elif severity:
            from ..database.models import VulnerabilitySeverity
            severity_enum = VulnerabilitySeverity(severity.lower())
            vulnerabilities = vuln_repo.get_by_severity(severity_enum, limit=limit)
        else:
            vulnerabilities = vuln_repo.get_all(limit=limit)
        
        return {
            "vulnerabilities": [
                {
                    "vulnerability_id": v.vulnerability_id,
                    "title": v.title,
                    "severity": v.severity.value if v.severity else None,
                    "cvss_score": v.cvss_score,
                    "published_date": v.published_date,
                    "description": v.description[:200] + "..." if v.description and len(v.description) > 200 else v.description
                }
                for v in vulnerabilities
            ],
            "total": len(vulnerabilities)
        }
    except Exception as e:
        logger.error(f"Error listing vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vulnerabilities/{vulnerability_id}")
async def get_vulnerability_detail(vulnerability_id: str, db: Session = Depends(get_db_session)):
    """Get detailed vulnerability information"""
    try:
        vuln_repo = VulnerabilityRepository(db)
        vulnerability = vuln_repo.get_by_vulnerability_id(vulnerability_id)
        
        if not vulnerability:
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        
        return {
            "vulnerability_id": vulnerability.vulnerability_id,
            "source": vulnerability.source,
            "title": vulnerability.title,
            "description": vulnerability.description,
            "severity": vulnerability.severity.value if vulnerability.severity else None,
            "cvss_score": vulnerability.cvss_score,
            "cvss_vector": vulnerability.cvss_vector,
            "epss_score": vulnerability.epss_score,
            "published_date": vulnerability.published_date,
            "modified_date": vulnerability.modified_date,
            "references": vulnerability.references,
            "cwe_ids": vulnerability.cwe_ids,
            "affected_versions": vulnerability.affected_versions,
            "fixed_versions": vulnerability.fixed_versions,
            "created_at": vulnerability.created_at,
            "updated_at": vulnerability.updated_at
        }
    except Exception as e:
        logger.error(f"Error getting vulnerability detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vulnerabilities/statistics")
async def get_vulnerability_statistics(db: Session = Depends(get_db_session)):
    """Get vulnerability statistics"""
    try:
        vuln_repo = VulnerabilityRepository(db)
        stats = vuln_repo.get_vulnerability_statistics()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting vulnerability statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vulnerabilities/critical")
async def get_critical_vulnerabilities(limit: int = 20, db: Session = Depends(get_db_session)):
    """Get critical vulnerabilities"""
    try:
        vuln_repo = VulnerabilityRepository(db)
        vulnerabilities = vuln_repo.get_critical_vulnerabilities(limit=limit)
        
        return {
            "critical_vulnerabilities": [
                {
                    "vulnerability_id": v.vulnerability_id,
                    "title": v.title,
                    "cvss_score": v.cvss_score,
                    "published_date": v.published_date,
                    "description": v.description[:200] + "..." if v.description and len(v.description) > 200 else v.description
                }
                for v in vulnerabilities
            ],
            "total": len(vulnerabilities)
        }
    except Exception as e:
        logger.error(f"Error getting critical vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vulnerability-scans")
async def list_vulnerability_scans(
    analysis_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """List vulnerability scans"""
    try:
        scan_repo = VulnerabilityScanRepository(db)
        
        if analysis_id:
            # Convert string to UUID
            from uuid import UUID
            analysis_uuid = UUID(analysis_id)
            scans = scan_repo.get_by_analysis_id(analysis_uuid)
        else:
            scans = scan_repo.get_recent_scans(limit=limit)
        
        return {
            "vulnerability_scans": [
                {
                    "scan_id": s.scan_id,
                    "scanner": s.scanner.value if s.scanner else None,
                    "scanner_version": s.scanner_version,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "duration_seconds": s.duration_seconds,
                    "total_vulnerabilities": s.total_vulnerabilities,
                    "critical_count": s.critical_count,
                    "high_count": s.high_count,
                    "medium_count": s.medium_count,
                    "low_count": s.low_count,
                    "analysis_id": str(s.analysis_id)
                }
                for s in scans
            ],
            "total": len(scans)
        }
    except Exception as e:
        logger.error(f"Error listing vulnerability scans: {e}")
        raise HTTPException(status_code=500, detail=str(e))