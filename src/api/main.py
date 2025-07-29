# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
FastAPI application for SBOM generation platform
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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
from ..monitoring.api_reference import setup_api_reference_routes
from ..monitoring.vulnerability_details_ui import get_vulnerability_details_ui
from ..telemetry.api import router as telemetry_router, init_telemetry_api
from ..telemetry.storage import TelemetryStorage
from .cicd import router as cicd_router
from ..database import init_database, get_db_session, test_connection
from ..database.repositories import (
    AnalysisRepository, ComponentRepository, SBOMRepository,
    VulnerabilityRepository, VulnerabilityScanRepository, CountValidator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Perseus SBOM Platform",
    description="Enterprise SBOM & Vulnerability Management Platform",
    version="1.5.0"
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
setup_api_reference_routes(app)

# Add vulnerability details route
@app.get("/vulnerability-details", response_class=HTMLResponse)
async def vulnerability_details_page():
    """Vulnerability details UI with enhanced CVE information"""
    return get_vulnerability_details_ui()

@app.get("/api/v1/vulnerabilities/detailed/{analysis_id}")
async def get_detailed_vulnerability_scan(analysis_id: str, db: Session = Depends(get_db_session)):
    """Get detailed vulnerability scan results with enhanced CVE information"""
    print(f"DEBUG: Starting detailed vulnerability scan for analysis {analysis_id}")
    try:
        from ..database.repositories.vulnerability import VulnerabilityRepository
        
        vuln_repo = VulnerabilityRepository(db)
        print(f"DEBUG: Created VulnerabilityRepository for analysis {analysis_id}")
        detailed_vulnerabilities = vuln_repo.get_vulnerabilities_by_analysis(analysis_id)
        print(f"DEBUG: Found {len(detailed_vulnerabilities)} vulnerabilities via relationships for analysis {analysis_id}")
        
        # If no vulnerabilities found via relationships, try legacy approach
        if not detailed_vulnerabilities:
            logger.info(f"No vulnerabilities found via relationships for {analysis_id}, trying legacy approach")
            try:
                # Get vulnerability data using the existing workflow engine
                results = workflow_engine.get_analysis_results(analysis_id)
                if not results:
                    return {
                        "analysis_id": analysis_id,
                        "vulnerabilities": [],
                        "total_count": 0,
                        "message": "Analysis not found"
                    }
                
                # Extract legacy vulnerability data from results
                legacy_results = {
                    "vulnerable_components": []
                }
                
                for component in results.components:
                    if component.vulnerabilities and len(component.vulnerabilities) > 0:
                        component_data = {
                            "component_name": component.name,
                            "component_version": component.version,
                            "purl": component.purl,
                            "vulnerabilities": component.vulnerabilities
                        }
                        legacy_results["vulnerable_components"].append(component_data)
                
                # Convert legacy format to enhanced format
                enhanced_vulnerabilities = []
                for component in legacy_results.get("vulnerable_components", []):
                    for vuln in component.get("vulnerabilities", []):
                        enhanced_vuln = {
                            "id": vuln.get("id", "Unknown"),
                            "title": vuln.get("title", ""),
                            "description": vuln.get("description", ""),
                            "severity": vuln.get("severity", "unknown"),
                            "published": vuln.get("published"),
                            "updated": vuln.get("updated"),
                            "references": vuln.get("references", []),
                            "fixed_versions": vuln.get("fixed_versions", []),
                            "affected_versions": vuln.get("affected_versions", []),
                            "cvss": {
                                "base_score": vuln.get("cvss_score"),
                                "severity": vuln.get("severity", "unknown"),
                                "vector_string": vuln.get("cvss_vector")
                            } if vuln.get("cvss_score") else None,
                            "cwe_ids": vuln.get("cwe_ids", []),
                            "aliases": [],
                            "exploit_info": None,
                            "patches": [],
                            "advisories": [],
                            "affected_platforms": [],
                            "affected_products": [],
                            "mitigation": None,
                            "technical_details": None,
                            # Add component context for UI display
                            "component_name": component.get("component_name"),
                            "component_version": component.get("component_version"),
                            "analysis_id": analysis_id
                        }
                        enhanced_vulnerabilities.append(enhanced_vuln)
                
                return {
                    "analysis_id": analysis_id,
                    "vulnerabilities": enhanced_vulnerabilities,
                    "total_vulnerabilities": len(enhanced_vulnerabilities),
                    "data_source": "legacy_scan_results"
                }
            except Exception as legacy_error:
                logger.error(f"Legacy approach also failed: {legacy_error}")
                return {
                    "analysis_id": analysis_id,
                    "vulnerabilities": [],
                    "total_vulnerabilities": 0,
                    "error": "No vulnerability data available via any method"
                }
        
        detailed_vulnerabilities = detailed_vulnerabilities
        
        # Transform to the enhanced format
        enhanced_vulnerabilities = []
        for vuln in detailed_vulnerabilities:
            enhanced_vuln = {
                "id": vuln.vulnerability_id,
                "title": vuln.title or "",
                "description": vuln.description or "",
                "severity": vuln.severity.value if vuln.severity else "unknown",
                "published": vuln.published_date.isoformat() if vuln.published_date else None,
                "updated": vuln.modified_date.isoformat() if vuln.modified_date else None,
                "references": vuln.references if vuln.references else [],
                "fixed_versions": vuln.fixed_versions if vuln.fixed_versions else [],
                "affected_versions": vuln.affected_versions if vuln.affected_versions else [],
                "cvss": {
                    "base_score": vuln.cvss_score,
                    "vector_string": vuln.cvss_vector,
                    "version": "3.1",  # Default version
                    "severity": vuln.severity.value if vuln.severity else "unknown"
                } if vuln.cvss_score else None,
                "cwe_ids": vuln.cwe_ids if vuln.cwe_ids else [],
                "aliases": [],
                "exploit_info": None,
                "patches": [{"version": v, "release_date": None, "url": None} for v in (vuln.fixed_versions or [])],
                "advisories": [],
                "affected_platforms": [],
                "affected_products": [],
                "mitigation": None,
                "technical_details": None
            }
            
            # Add component context for UI display
            logger.info(f"Getting component context for detailed vuln: {vuln.vulnerability_id}")
            component_context = vuln_repo.get_vulnerability_component_context(vuln.vulnerability_id, analysis_id)
            logger.info(f"Component context result for {vuln.vulnerability_id}: {len(component_context) if component_context else 0} items")
            if component_context:
                # Take the first component as primary context
                primary_context = component_context[0]
                enhanced_vuln["component_name"] = primary_context.get("component_name")
                enhanced_vuln["component_version"] = primary_context.get("component_version")
                enhanced_vuln["analysis_id"] = primary_context.get("analysis_id")
                
                # If there are multiple components, add a count
                if len(component_context) > 1:
                    enhanced_vuln["additional_components"] = len(component_context) - 1
            
            enhanced_vulnerabilities.append(enhanced_vuln)
        
        return {
            "analysis_id": analysis_id,
            "vulnerabilities": enhanced_vulnerabilities,
            "total_count": len(enhanced_vulnerabilities),
            "severity_counts": {
                "critical": len([v for v in enhanced_vulnerabilities if v["severity"] == "critical"]),
                "high": len([v for v in enhanced_vulnerabilities if v["severity"] == "high"]),
                "medium": len([v for v in enhanced_vulnerabilities if v["severity"] == "medium"]),
                "low": len([v for v in enhanced_vulnerabilities if v["severity"] == "low"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed vulnerability scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SBOM Platform", "timestamp": datetime.utcnow()}

@app.post("/analyze/source", response_model=AnalysisResponse)
async def analyze_source(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Submit source code for analysis"""
    try:
        # Validate path exists before creating analysis record
        import os
        source_path = request.location
        
        # Handle file:// prefixes if present
        if source_path.startswith('file://'):
            source_path = source_path[7:]
        
        # Normalize path
        source_path = os.path.normpath(source_path)
        
        # Check if path exists
        if not os.path.exists(source_path):
            logger.warning(f"Source path does not exist: {source_path}")
            raise HTTPException(
                status_code=400, 
                detail=f"Source path does not exist: {source_path}"
            )
        
        # Check if it's a file or directory (both are valid for source analysis)
        if not (os.path.isfile(source_path) or os.path.isdir(source_path)):
            logger.warning(f"Source path is not a valid file or directory: {source_path}")
            raise HTTPException(
                status_code=400,
                detail=f"Source path is not a valid file or directory: {source_path}"
            )
        
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting source analysis {analysis_id} for {request.language} at {source_path}")
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting source analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/binary", response_model=AnalysisResponse)
async def analyze_binary(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Submit binary for analysis"""
    try:
        # Validate binary path exists before creating analysis record
        import os
        binary_path = request.location
        
        # Handle file:// prefixes if present
        if binary_path.startswith('file://'):
            binary_path = binary_path[7:]
        
        # Normalize path
        binary_path = os.path.normpath(binary_path)
        
        # Check if path exists
        if not os.path.exists(binary_path):
            logger.warning(f"Binary path does not exist: {binary_path}")
            raise HTTPException(
                status_code=400, 
                detail=f"Binary path does not exist: {binary_path}"
            )
        
        # For binary analysis, it should be a file, not a directory
        if not os.path.isfile(binary_path):
            logger.warning(f"Binary path is not a valid file: {binary_path}")
            raise HTTPException(
                status_code=400,
                detail=f"Binary path must be a file, not a directory: {binary_path}"
            )
        
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting binary analysis {analysis_id} for {binary_path}")
        
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
    except HTTPException:
        raise
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
async def get_analysis_results(analysis_id: str, db: Session = Depends(get_db_session)):
    """Get analysis results with accurate component count from database"""
    try:
        results = workflow_engine.get_analysis_results(analysis_id)
        if not results:
            raise HTTPException(status_code=404, detail="Analysis results not found")
        
        # Get actual component count from database instead of cached results
        from src.database.repositories.component import ComponentRepository
        component_repo = ComponentRepository(db)
        
        # Search for components by analysis ID to get actual count
        actual_components = component_repo.search_by_analysis_id(analysis_id, limit=1000)
        
        # Convert results to dict for modification
        results_dict = results.dict() if hasattr(results, 'dict') else results
        if isinstance(results_dict, dict) and 'components' in results_dict:
            # Replace the components list with the actual database components
            # Convert Component objects to dictionaries
            components_data = []
            for comp in actual_components:
                comp_dict = {
                    'id': str(comp.id),
                    'name': comp.name,
                    'version': comp.version,
                    'type': comp.type.value if comp.type else None,
                    'purl': comp.purl,
                    'vulnerability_count': comp.vulnerability_count,
                    'critical_vulnerabilities': comp.critical_vulnerabilities,
                    'high_vulnerabilities': comp.high_vulnerabilities
                }
                components_data.append(comp_dict)
            
            results_dict['components'] = components_data
        
        return results_dict
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
        
        # Get total count for pagination
        total_count = analysis_repo.session.query(analysis_repo.model).count()
        
        if status:
            from ..database.models import AnalysisStatus
            status_enum = AnalysisStatus(status)
            analyses = analysis_repo.get_by_status(status_enum, limit=limit)
        elif analysis_type:
            analyses = analysis_repo.get_analyses_by_type(analysis_type, limit=limit)
        else:
            analyses = analysis_repo.get_recent_analyses(limit=limit, offset=offset)
        
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
                    "duration_seconds": a.duration_seconds,
                    "source_info": {
                        "analysis_type": a.analysis_type,
                        "target_location": a.location,
                        "analysis_id": a.analysis_id
                    }
                }
                for a in analyses
            ],
            "total": total_count
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


@app.delete("/api/v1/analyses/{analysis_id}")
async def delete_analysis(analysis_id: str, db: Session = Depends(get_db_session)):
    """Delete a specific analysis and all its related data"""
    try:
        analysis_repo = AnalysisRepository(db)
        analysis = analysis_repo.get_by_analysis_id(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Delete the analysis (this will cascade to related tables due to FK constraints)
        delete_result = analysis_repo.delete(analysis.id)
        
        if not delete_result:
            raise HTTPException(status_code=500, detail="Failed to delete analysis from database")
        
        # Clean up orphaned vulnerabilities after analysis deletion
        try:
            from sqlalchemy import text
            orphaned_cleanup_query = """
            DELETE FROM vulnerabilities 
            WHERE id IN (
                SELECT v.id
                FROM vulnerabilities v
                LEFT JOIN component_vulnerabilities cv ON v.id = cv.vulnerability_id
                WHERE cv.vulnerability_id IS NULL
            )
            """
            result = db.execute(text(orphaned_cleanup_query))
            orphaned_count = result.rowcount
            if orphaned_count > 0:
                logger.info(f"Cleaned up {orphaned_count} orphaned vulnerabilities")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up orphaned vulnerabilities: {cleanup_error}")
        
        # Commit the transaction immediately after deletion and cleanup
        try:
            db.commit()
            logger.info(f"Successfully committed deletion of analysis {analysis_id}")
        except Exception as commit_error:
            db.rollback()
            logger.error(f"Failed to commit deletion of analysis {analysis_id}: {commit_error}")
            raise HTTPException(status_code=500, detail=f"Failed to commit deletion: {str(commit_error)}")
        
        # Also clean up the analysis result files from filesystem
        try:
            import os
            import glob
            
            # Clean up analysis result files
            analysis_files = glob.glob(f"data/analysis_results/*{analysis_id}*")
            for file_path in analysis_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Removed analysis file: {file_path}")
            
            # Clean up related SBOM files 
            sbom_files = glob.glob(f"data/sboms/*{analysis_id}*")
            for file_path in sbom_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Removed SBOM file: {file_path}")
                    
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up files for analysis {analysis_id}: {cleanup_error}")
        
        logger.info(f"Successfully deleted analysis {analysis_id}")
        
        return {
            "message": f"Analysis {analysis_id} deleted successfully",
            "analysis_id": analysis_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")


@app.get("/api/v1/components/search")
async def search_components(
    q: str = "",
    analysis_id: Optional[str] = None,
    vulnerable_only: bool = False,
    min_severity: Optional[str] = None,
    component_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """Search components with multiple filters"""
    try:
        logger.info(f"Component search params: q={q}, analysis_id={analysis_id}, vulnerable_only={vulnerable_only}, min_severity={min_severity}, component_type={component_type}")
        
        component_repo = ComponentRepository(db)
        
        # Start with base search
        if analysis_id:
            # Search by analysis ID (supports partial matching)
            components = component_repo.search_by_analysis_id(analysis_id, q, limit=limit)
        else:
            # Regular text search
            components = component_repo.search_components(q, limit=limit)
        
        logger.info(f"Found {len(components)} components before filtering")
        
        # Apply filters
        filtered_components = []
        for component in components:
            # Filter by vulnerable_only
            if vulnerable_only and component.vulnerability_count == 0:
                continue
                
            # Filter by min_severity
            if min_severity:
                has_severity = False
                if min_severity == "critical" and component.critical_vulnerabilities > 0:
                    has_severity = True
                elif min_severity == "high" and (component.critical_vulnerabilities > 0 or component.high_vulnerabilities > 0):
                    has_severity = True
                elif min_severity == "medium":
                    # Calculate medium vulnerabilities as total - critical - high
                    medium_vulns = component.vulnerability_count - component.critical_vulnerabilities - component.high_vulnerabilities
                    if component.critical_vulnerabilities > 0 or component.high_vulnerabilities > 0 or medium_vulns > 0:
                        has_severity = True
                elif min_severity == "low" and component.vulnerability_count > 0:
                    has_severity = True
                    
                if not has_severity:
                    continue
            
            # Filter by component_type
            if component_type:
                # Handle enum comparison
                comp_type_value = None
                if hasattr(component, 'type') and component.type:
                    comp_type_value = component.type.value if hasattr(component.type, 'value') else str(component.type)
                
                if comp_type_value != component_type:
                    continue
                
            filtered_components.append(component)
        
        logger.info(f"After filtering: {len(filtered_components)} components remain")
        
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
                    "analysis_id": c.analysis.analysis_id if c.analysis else str(c.analysis_id)
                }
                for c in filtered_components
            ],
            "total": len(filtered_components)
        }
    except Exception as e:
        logger.error(f"Error searching components: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/components/vulnerable")
async def get_vulnerable_components(
    min_severity: Optional[str] = None,
    analysis_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """Get components with vulnerabilities"""
    try:
        component_repo = ComponentRepository(db)
        components = component_repo.get_vulnerable_components(min_severity, analysis_id)[:limit]
        
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
                    "analysis_id": c.analysis.analysis_id if c.analysis else str(c.analysis_id)
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
            # Load analysis relationships for format-filtered results
            from sqlalchemy.orm import joinedload
            sbom_ids = [s.sbom_id for s in sboms]
            sboms = sbom_repo.session.query(SBOM).options(
                joinedload(SBOM.analysis)
            ).filter(SBOM.sbom_id.in_(sbom_ids)).all() if sbom_ids else []
        else:
            sboms = sbom_repo.get_recent_sboms_with_analysis(limit=limit)
        
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
                    "analysis_id": s.analysis.analysis_id if s.analysis else None
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

@app.get("/api/v1/test-search")
async def test_search():
    """Test endpoint to isolate search issue"""
    return {"message": "Search test working"}

@app.get("/api/v1/vulnerabilities")
async def list_vulnerabilities(
    severity: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db_session)
):
    """List vulnerabilities with optional filtering"""
    logger.info(f"Entering list_vulnerabilities function with search={search}")
    
    try:
        logger.info(f"About to create vulnerability repository")
        vuln_repo = VulnerabilityRepository(db)
        logger.info(f"Created vulnerability repository successfully")
        
        # Get the vulnerabilities based on filters - use simple methods only
        if search:
            logger.info(f"Searching vulnerabilities with term: {search}")
            vulnerabilities = vuln_repo.search_vulnerabilities(search, limit=limit, offset=offset)
            total_count = vuln_repo.count_search_vulnerabilities(search)
        elif severity:
            from ..database.models import VulnerabilitySeverity
            severity_enum = VulnerabilitySeverity(severity.lower())
            vulnerabilities = vuln_repo.get_by_severity(severity_enum, limit=limit, offset=offset)
            total_count = vuln_repo.count_by_severity(severity_enum)
        else:
            # Use simple query without joins
            vulnerabilities = vuln_repo.get_all(limit=limit, offset=offset)
            total_count = vuln_repo.count()
        
        # Format vulnerabilities 
        formatted_vulns = []
        for v in vulnerabilities:
            vuln_data = {
                "vulnerability_id": v.vulnerability_id,
                "title": v.title,
                "severity": v.severity.value if v.severity else None,
                "cvss_score": v.cvss_score,
                "published_date": v.published_date,
                "description": v.description[:200] + "..." if v.description and len(v.description) > 200 else v.description
            }
            
            # Add component and analysis context
            logger.info(f"Getting component context for vulnerability: {v.vulnerability_id}")
            component_context = vuln_repo.get_vulnerability_component_context(v.vulnerability_id)
            logger.info(f"Component context result: {len(component_context) if component_context else 0} items")
            
            # Check if vulnerability is orphan
            is_orphan = vuln_repo.is_vulnerability_orphan(v.vulnerability_id)
            vuln_data["is_orphan"] = is_orphan
            vuln_data["component_count"] = len(component_context) if component_context else 0
            
            if component_context and not is_orphan:
                # Take the first component as primary context
                primary_context = component_context[0]
                vuln_data["component_name"] = primary_context.get("component_name")
                vuln_data["component_version"] = primary_context.get("component_version")
                vuln_data["analysis_id"] = primary_context.get("analysis_id")
                
                # If there are multiple components, add a count
                if len(component_context) > 1:
                    vuln_data["additional_components"] = len(component_context) - 1
            else:
                # Mark orphan vulnerabilities
                vuln_data["component_name"] = None
                vuln_data["component_version"] = None
                vuln_data["analysis_id"] = None
                        
            formatted_vulns.append(vuln_data)
        
        return {
            "vulnerabilities": formatted_vulns,
            "total": total_count,
            "returned": len(vulnerabilities),
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(vulnerabilities) < total_count
        }
    except Exception as e:
        logger.error(f"Error listing vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vulnerabilities/orphans")
async def get_orphan_vulnerabilities(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db_session)
):
    """Get vulnerabilities that have no linked components (orphan vulnerabilities)"""
    try:
        vuln_repo = VulnerabilityRepository(db)
        
        orphan_vulnerabilities = vuln_repo.get_orphan_vulnerabilities(limit=limit, offset=offset)
        total_count = vuln_repo.count_orphan_vulnerabilities()
        
        formatted_vulns = []
        for v in orphan_vulnerabilities:
            vuln_data = {
                "vulnerability_id": v.vulnerability_id,
                "title": v.title,
                "severity": v.severity.value if v.severity else None,
                "cvss_score": v.cvss_score,
                "published_date": v.published_date,
                "description": v.description[:200] + "..." if v.description and len(v.description) > 200 else v.description,
                "is_orphan": True,
                "component_count": 0
            }
            formatted_vulns.append(vuln_data)
        
        return {
            "vulnerabilities": formatted_vulns,
            "total_count": total_count,
            "orphan_count": total_count,
            "page_info": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Error getting orphan vulnerabilities: {e}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.delete("/api/v1/vulnerabilities/orphans")
async def delete_orphan_vulnerabilities(db: Session = Depends(get_db_session)):
    """Delete all orphan vulnerabilities"""
    try:
        vuln_repo = VulnerabilityRepository(db)
        
        orphan_count_before = vuln_repo.count_orphan_vulnerabilities()
        deleted_count = vuln_repo.delete_orphan_vulnerabilities()
        
        return {
            "message": f"Successfully deleted {deleted_count} orphan vulnerabilities",
            "deleted_count": deleted_count,
            "orphan_count_before": orphan_count_before,
            "orphan_count_after": vuln_repo.count_orphan_vulnerabilities()
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Error deleting orphan vulnerabilities: {e}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


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


# Count validation endpoints
@app.get("/api/v1/counts/validate/{analysis_id}")
async def validate_analysis_counts(
    analysis_id: str,
    db: Session = Depends(get_db_session)
):
    """Validate count consistency for a specific analysis"""
    try:
        validator = CountValidator(db)
        result = validator.validate_analysis_counts(analysis_id)
        return result
    except Exception as e:
        logger.error(f"Failed to validate analysis counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/counts/fix/{analysis_id}")
async def fix_analysis_counts(
    analysis_id: str,
    db: Session = Depends(get_db_session)
):
    """Fix count discrepancies for a specific analysis"""
    try:
        validator = CountValidator(db)
        result = validator.fix_analysis_counts(analysis_id)
        return result
    except Exception as e:
        logger.error(f"Failed to fix analysis counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/counts/validate/all")
async def validate_all_analysis_counts(
    db: Session = Depends(get_db_session)
):
    """Validate count consistency for all analyses"""
    try:
        validator = CountValidator(db)
        result = validator.validate_all_analysis_counts()
        return result
    except Exception as e:
        logger.error(f"Failed to validate all analysis counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/counts/fix/all")
async def fix_all_analysis_counts(
    db: Session = Depends(get_db_session)
):
    """Fix count discrepancies for all analyses"""
    try:
        validator = CountValidator(db)
        result = validator.fix_all_analysis_counts()
        return result
    except Exception as e:
        logger.error(f"Failed to fix all analysis counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/counts/cleanup/orphans")
async def cleanup_orphan_vulnerabilities(
    db: Session = Depends(get_db_session)
):
    """Clean up orphan vulnerabilities not linked to any components"""
    try:
        validator = CountValidator(db)
        result = validator.cleanup_orphan_vulnerabilities()
        return result
    except Exception as e:
        logger.error(f"Failed to cleanup orphan vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/counts/statistics")
async def get_count_statistics(
    db: Session = Depends(get_db_session)
):
    """Get comprehensive count statistics and data quality metrics"""
    try:
        validator = CountValidator(db)
        result = validator.get_count_statistics()
        return result
    except Exception as e:
        logger.error(f"Failed to get count statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/counts/validate/components")
async def validate_component_vulnerability_counts(
    db: Session = Depends(get_db_session)
):
    """Validate that component vulnerability counts match actual relationships"""
    try:
        validator = CountValidator(db)
        result = validator.validate_component_vulnerability_relationships()
        return result
    except Exception as e:
        logger.error(f"Failed to validate component vulnerability counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/counts/fix/components")
async def fix_component_vulnerability_counts(
    db: Session = Depends(get_db_session)
):
    """Fix component vulnerability count discrepancies"""
    try:
        validator = CountValidator(db)
        result = validator.fix_component_vulnerability_counts()
        return result
    except Exception as e:
        logger.error(f"Failed to fix component vulnerability counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Count maintenance endpoints
@app.get("/api/v1/counts/maintenance/status")
async def get_count_maintenance_status():
    """Get the status of the count maintenance service"""
    try:
        from ..monitoring.count_maintenance import get_count_maintenance_status
        return get_count_maintenance_status()
    except Exception as e:
        logger.error(f"Failed to get count maintenance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/counts/maintenance/start")
async def start_count_maintenance():
    """Start the count maintenance service"""
    try:
        from ..monitoring.count_maintenance import start_count_maintenance
        start_count_maintenance()
        return {"message": "Count maintenance service started"}
    except Exception as e:
        logger.error(f"Failed to start count maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/counts/maintenance/stop")
async def stop_count_maintenance():
    """Stop the count maintenance service"""
    try:
        from ..monitoring.count_maintenance import stop_count_maintenance
        stop_count_maintenance()
        return {"message": "Count maintenance service stopped"}
    except Exception as e:
        logger.error(f"Failed to stop count maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/counts/maintenance/trigger-validation")
async def trigger_count_validation():
    """Manually trigger count validation"""
    try:
        from ..monitoring.count_maintenance import trigger_count_validation
        result = trigger_count_validation()
        return result
    except Exception as e:
        logger.error(f"Failed to trigger count validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/counts/maintenance/trigger-cleanup")
async def trigger_count_cleanup():
    """Manually trigger orphan cleanup"""
    try:
        from ..monitoring.count_maintenance import trigger_count_cleanup
        result = trigger_count_cleanup()
        return result
    except Exception as e:
        logger.error(f"Failed to trigger count cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))