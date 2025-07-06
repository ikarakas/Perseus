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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SBOM Generation Platform",
    description="Multi-language SBOM generation for C/C++ and Java applications",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow engine and monitoring
metrics_collector = MetricsCollector()
workflow_engine = WorkflowEngine(metrics_collector)
dashboard = MonitoringDashboard(metrics_collector)

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