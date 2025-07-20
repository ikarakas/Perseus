# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
CI/CD Integration API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime, timezone
import uuid
import asyncio
from pathlib import Path

from ..orchestrator.workflow import WorkflowEngine
from ..common.storage import ResultStorage
import logging

# Use standard logging for now
logger = logging.getLogger(__name__)
storage = ResultStorage()

router = APIRouter(prefix="/api/v1/cicd", tags=["CI/CD Integration"])

# In-memory storage for builds (replace with database in production)
builds_storage: Dict[str, Dict] = {}

class ProjectInfo(BaseModel):
    """Project information from CI/CD"""
    name: str
    path: str = "."
    type: str = "unknown"
    branch: str = "unknown"
    commit: str = "unknown"
    version: Optional[str] = None

class CIContext(BaseModel):
    """CI/CD platform context"""
    platform: str
    build_id: Optional[str] = None
    job_name: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + 'Z')
    workspace: str = "."

class BuildRegistration(BaseModel):
    """Build registration request"""
    build_id: str
    project: ProjectInfo
    ci_context: CIContext

class ScanRequest(BaseModel):
    """Scan request for a build"""
    scan_type: Literal["full", "quick", "policy-only"] = "full"
    wait: bool = True  # Synchronous mode
    timeout: int = 300
    policies: List[str] = []
    output_formats: List[str] = ["spdx", "cyclonedx"]

class BuildStatus(BaseModel):
    """Build scan status"""
    build_id: str
    status: Literal["registered", "scanning", "analyzing", "completed", "failed"]
    progress: int = 0
    analysis_id: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class BuildResults(BaseModel):
    """Build scan results"""
    build_id: str
    status: str
    component_count: int = 0
    vulnerabilities: Dict[str, int] = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    licenses: List[str] = []
    sbom_formats: List[str] = []
    scan_duration_seconds: Optional[float] = None
    ci_context: Optional[Dict] = None

@router.post("/builds", response_model=Dict[str, str])
async def register_build(build_reg: BuildRegistration):
    """Register a new CI/CD build for scanning"""
    try:
        # Store build information
        build_data = {
            "id": build_reg.build_id,
            "project": build_reg.project.dict(),
            "ci_context": build_reg.ci_context.dict(),
            "status": "registered",
            "created_at": datetime.now(timezone.utc).isoformat() + 'Z',
            "analysis_id": None,
            "results": None
        }
        
        builds_storage[build_reg.build_id] = build_data
        
        logger.info(f"Registered CI/CD build: {build_reg.build_id} from {build_reg.ci_context.platform}")
        
        return {"build_id": build_reg.build_id, "status": "registered"}
    
    except Exception as e:
        logger.error(f"Failed to register build: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/builds/{build_id}/scan")
async def start_scan(
    build_id: str,
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """Start SBOM scan for a registered build"""
    if build_id not in builds_storage:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    build = builds_storage[build_id]
    
    try:
        # Create analysis based on project type
        project = build["project"]
        project_path = project["path"]
        
        # Initialize workflow engine
        from ..monitoring.metrics import MetricsCollector
        metrics = MetricsCollector()
        workflow = WorkflowEngine(metrics_collector=metrics)
        
        # Create analysis request
        from ..api.models import AnalysisRequest
        
        if project["type"] in ["java", "python", "javascript", "go", "c++"]:
            # Source code analysis
            analysis_request = AnalysisRequest(
                type="source",
                language=project["type"],
                location=project_path,
                options={
                    "deep_scan": scan_request.scan_type == "full",
                    "ci_build_id": build_id
                }
            )
        else:
            # Try binary analysis as fallback
            analysis_request = AnalysisRequest(
                type="binary",
                location=project_path,
                options={
                    "ci_build_id": build_id
                }
            )
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        build["analysis_id"] = analysis_id
        
        # Start analysis
        if scan_request.wait:
            # Synchronous mode - wait for completion
            build["status"] = "scanning"
            build["started_at"] = datetime.now(timezone.utc).isoformat() + 'Z'
            
            # Start the analysis based on type
            if analysis_request.type == "source":
                background_tasks.add_task(
                    workflow.analyze_source,
                    analysis_id,
                    analysis_request
                )
            else:
                background_tasks.add_task(
                    workflow.analyze_binary,
                    analysis_id,
                    analysis_request
                )
            
            # Wait for completion
            timeout_count = 0
            while timeout_count < scan_request.timeout:
                status = workflow.get_analysis_status(analysis_id)
                
                if status and status.get("status") == "completed":
                    build["status"] = "completed"
                    build["completed_at"] = datetime.now(timezone.utc).isoformat() + 'Z'
                    
                    # Get results
                    results = workflow.get_analysis_results(analysis_id)
                    
                    if results:
                        # Process results for CI/CD format
                        build["results"] = _process_results_for_cicd(results.__dict__)
                    
                    return {
                        "build_id": build_id,
                        "analysis_id": analysis_id,
                        "status": "completed"
                    }
                
                elif status and status.get("status") == "failed":
                    build["status"] = "failed"
                    build["error"] = status.get("error", "Analysis failed")
                    raise HTTPException(status_code=500, detail=build["error"])
                
                await asyncio.sleep(2)
                timeout_count += 2
            
            # Timeout reached
            build["status"] = "failed"
            build["error"] = "Scan timeout exceeded"
            raise HTTPException(status_code=408, detail="Scan timeout exceeded")
        
        else:
            # Asynchronous mode - return immediately
            background_tasks.add_task(_async_scan, build_id, analysis_id, analysis_request, workflow)
            return {
                "build_id": build_id,
                "analysis_id": analysis_id,
                "status": "scanning",
                "message": "Scan started in background"
            }
    
    except Exception as e:
        logger.error(f"Failed to start scan for build {build_id}: {str(e)}")
        build["status"] = "failed"
        build["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/builds/{build_id}/status", response_model=BuildStatus)
async def get_build_status(build_id: str):
    """Get current status of a build scan"""
    if build_id not in builds_storage:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    build = builds_storage[build_id]
    
    return BuildStatus(
        build_id=build_id,
        status=build["status"],
        analysis_id=build.get("analysis_id"),
        error=build.get("error"),
        started_at=build.get("started_at"),
        completed_at=build.get("completed_at")
    )

@router.get("/builds/{build_id}/results", response_model=BuildResults)
async def get_build_results(build_id: str):
    """Get results of a completed build scan"""
    if build_id not in builds_storage:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    build = builds_storage[build_id]
    
    if build["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Build scan not completed. Current status: {build['status']}"
        )
    
    results = build.get("results", {})
    
    # Calculate scan duration
    scan_duration = None
    if build.get("started_at") and build.get("completed_at"):
        start = datetime.fromisoformat(build["started_at"].replace('Z', '+00:00'))
        end = datetime.fromisoformat(build["completed_at"].replace('Z', '+00:00'))
        scan_duration = (end - start).total_seconds()
    
    return BuildResults(
        build_id=build_id,
        status=build["status"],
        component_count=results.get("component_count", 0),
        vulnerabilities=results.get("vulnerabilities", {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }),
        licenses=results.get("licenses", []),
        sbom_formats=results.get("sbom_formats", []),
        scan_duration_seconds=scan_duration,
        ci_context=build.get("ci_context")
    )

@router.get("/builds/{build_id}/artifacts")
async def get_build_artifacts(build_id: str):
    """Get generated artifacts (SBOMs, reports) for a build"""
    if build_id not in builds_storage:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    build = builds_storage[build_id]
    
    if build["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Build scan not completed. Current status: {build['status']}"
        )
    
    artifacts = []
    analysis_id = build.get("analysis_id")
    
    if analysis_id:
        # Check for generated SBOMs
        sbom_path = Path(storage.base_path) / "sboms"
        if sbom_path.exists():
            for sbom_file in sbom_path.glob(f"*{analysis_id}*"):
                artifacts.append({
                    "type": "sbom",
                    "format": "spdx" if "spdx" in sbom_file.name else "cyclonedx",
                    "filename": sbom_file.name,
                    "size_bytes": sbom_file.stat().st_size,
                    "download_url": f"/api/v1/cicd/builds/{build_id}/artifacts/{sbom_file.name}"
                })
    
    return {"build_id": build_id, "artifacts": artifacts}

def _process_results_for_cicd(analysis_results: Dict) -> Dict:
    """Process analysis results into CI/CD friendly format"""
    processed = {
        "component_count": len(analysis_results.get("components", [])),
        "vulnerabilities": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "licenses": [],
        "sbom_formats": ["spdx", "cyclonedx"]
    }
    
    # Count vulnerabilities by severity
    vulnerabilities = analysis_results.get("vulnerabilities", [])
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "unknown").lower()
        if severity in processed["vulnerabilities"]:
            processed["vulnerabilities"][severity] += 1
    
    # Extract unique licenses
    licenses = set()
    for component in analysis_results.get("components", []):
        for license in component.get("licenses", []):
            licenses.add(license)
    processed["licenses"] = sorted(list(licenses))
    
    return processed

async def _async_scan(build_id: str, analysis_id: str, analysis_request: "AnalysisRequest", workflow: WorkflowEngine):
    """Background task for asynchronous scanning"""
    build = builds_storage[build_id]
    
    try:
        build["status"] = "scanning"
        build["started_at"] = datetime.now(timezone.utc).isoformat() + 'Z'
        
        # Start the analysis
        if analysis_request.type == "source":
            await workflow.analyze_source(analysis_id, analysis_request)
        else:
            await workflow.analyze_binary(analysis_id, analysis_request)
        
        # Poll for completion
        while True:
            status = workflow.get_analysis_status(analysis_id)
            
            if status and status.get("status") == "completed":
                build["status"] = "completed"
                build["completed_at"] = datetime.now(timezone.utc).isoformat() + 'Z'
                
                # Get and process results
                results = workflow.get_analysis_results(analysis_id)
                if results:
                    build["results"] = _process_results_for_cicd(results.__dict__)
                break
            
            elif status and status.get("status") == "failed":
                build["status"] = "failed"
                build["error"] = status.get("error", "Analysis failed")
                break
            
            await asyncio.sleep(5)
    
    except Exception as e:
        logger.error(f"Async scan failed for build {build_id}: {str(e)}")
        build["status"] = "failed"
        build["error"] = str(e)