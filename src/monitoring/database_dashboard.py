# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Enhanced dashboard with database integration
"""

import json
import logging
import os
import glob
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db_session
from ..database.models import SBOM, Analysis
from ..database.repositories import (
    AnalysisRepository, ComponentRepository, SBOMRepository,
    VulnerabilityRepository, VulnerabilityScanRepository
)
from ..common.version import VersionConfig

logger = logging.getLogger(__name__)


class DatabaseDashboard:
    """Enhanced dashboard with database features"""
    
    def __init__(self):
        self.dashboard_html = self._generate_dashboard_html()
    
    def setup_routes(self, app):
        """Setup dashboard routes with database integration"""
        
        @app.get("/dashboard/enhanced", response_class=HTMLResponse)
        async def enhanced_dashboard():
            """Enhanced dashboard with database features"""
            return self.dashboard_html
        
        @app.get("/api/v1/dashboard/metrics")
        async def get_dashboard_metrics(db: Session = Depends(get_db_session)):
            """Get comprehensive dashboard metrics from database"""
            try:
                analysis_repo = AnalysisRepository(db)
                component_repo = ComponentRepository(db)
                sbom_repo = SBOMRepository(db)
                vuln_repo = VulnerabilityRepository(db)
                scan_repo = VulnerabilityScanRepository(db)
                
                # Get comprehensive statistics
                analysis_stats = analysis_repo.get_statistics(days=30)
                vulnerability_summary = analysis_repo.get_vulnerability_summary()
                component_stats = component_repo.get_component_statistics()
                sbom_stats = sbom_repo.get_sbom_statistics()
                vuln_stats = vuln_repo.get_vulnerability_statistics()
                scan_stats = scan_repo.get_scan_statistics()
                
                # Get top vulnerable components
                top_vulnerable = component_repo.get_top_vulnerable_components(limit=10)
                
                # Get recent analyses
                recent_analyses = analysis_repo.get_recent_analyses(limit=10)
                
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "analysis_statistics": analysis_stats,
                    "vulnerability_summary": vulnerability_summary,
                    "component_statistics": component_stats,
                    "sbom_statistics": sbom_stats,
                    "vulnerability_statistics": vuln_stats,
                    "scan_statistics": scan_stats,
                    "top_vulnerable_components": top_vulnerable,
                    "recent_analyses": [
                        {
                            "analysis_id": a.analysis_id,
                            "status": a.status.value,
                            "analysis_type": a.analysis_type,
                            "component_count": a.component_count,
                            "vulnerability_count": a.vulnerability_count,
                            "created_at": a.created_at.isoformat() if a.created_at else None
                        }
                        for a in recent_analyses
                    ]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/v1/dashboard/trends")
        async def get_vulnerability_trends(
            days: int = 30, 
            db: Session = Depends(get_db_session)
        ):
            """Get vulnerability trends over time"""
            try:
                analysis_repo = AnalysisRepository(db)
                
                # Get analyses from the last N days
                since = datetime.utcnow() - timedelta(days=days)
                analyses = db.query(analysis_repo.model).filter(
                    analysis_repo.model.created_at >= since
                ).order_by(analysis_repo.model.created_at).all()
                
                # Group by day
                daily_stats = {}
                for analysis in analyses:
                    day = analysis.created_at.date().isoformat()
                    if day not in daily_stats:
                        daily_stats[day] = {
                            'date': day,
                            'analyses': 0,
                            'total_vulnerabilities': 0,
                            'critical_vulnerabilities': 0,
                            'high_vulnerabilities': 0,
                            'medium_vulnerabilities': 0,
                            'low_vulnerabilities': 0,
                            'components': 0
                        }
                    
                    daily_stats[day]['analyses'] += 1
                    daily_stats[day]['total_vulnerabilities'] += analysis.vulnerability_count or 0
                    daily_stats[day]['critical_vulnerabilities'] += analysis.critical_vulnerability_count or 0
                    daily_stats[day]['high_vulnerabilities'] += analysis.high_vulnerability_count or 0
                    daily_stats[day]['components'] += analysis.component_count or 0
                    
                    # Calculate medium/low as the difference
                    total = analysis.vulnerability_count or 0
                    critical = analysis.critical_vulnerability_count or 0
                    high = analysis.high_vulnerability_count or 0
                    medium_low = total - critical - high
                    
                    # For now, split medium/low evenly (or we could add these fields to the database)
                    if medium_low > 0:
                        # Assume 60% are medium, 40% are low (typical distribution)
                        daily_stats[day]['medium_vulnerabilities'] += int(medium_low * 0.6)
                        daily_stats[day]['low_vulnerabilities'] += medium_low - int(medium_low * 0.6)
                
                return {
                    "trends": list(daily_stats.values()),
                    "period_days": days
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/v1/dashboard/sboms")
        async def get_recent_sboms(
            limit: int = 10,
            db: Session = Depends(get_db_session)
        ):
            """Get recent SBOMs for dashboard display"""
            try:
                from sqlalchemy.orm import joinedload
                sbom_repo = SBOMRepository(db)
                # Load with analysis relationship to get the correct analysis_id
                recent_sboms = db.query(SBOM).options(
                    joinedload(SBOM.analysis)
                ).order_by(SBOM.created_at.desc()).limit(limit).all()
                
                return {
                    "sboms": [
                        {
                            "sbom_id": sbom.sbom_id,
                            "name": sbom.name,
                            "format": sbom.format,
                            "namespace": sbom.namespace,
                            "analysis_id": sbom.analysis.analysis_id if sbom.analysis else None,
                            "component_count": sbom.component_count,
                            "created_at": sbom.created_at.isoformat() if sbom.created_at else None,
                            "file_path": sbom.file_path
                        }
                        for sbom in recent_sboms
                    ],
                    "total": len(recent_sboms)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/v1/dashboard/sboms/all")
        async def get_all_sboms(
            search: Optional[str] = None,
            format: Optional[str] = None,
            offset: int = 0,
            limit: int = 100,
            db: Session = Depends(get_db_session)
        ):
            """Get all SBOMs with search and pagination"""
            try:
                sbom_repo = SBOMRepository(db)
                query = db.query(SBOM)
                
                # Apply search filter
                if search:
                    search_pattern = f"%{search}%"
                    query = query.filter(
                        or_(
                            SBOM.name.ilike(search_pattern),
                            SBOM.namespace.ilike(search_pattern),
                            SBOM.sbom_id.ilike(search_pattern)
                        )
                    )
                
                # Apply format filter
                if format:
                    query = query.filter(SBOM.format == format)
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination and ordering with analysis relationship
                from sqlalchemy.orm import joinedload
                sboms = query.options(
                    joinedload(SBOM.analysis)
                ).order_by(SBOM.created_at.desc()).offset(offset).limit(limit).all()
                
                return {
                    "sboms": [
                        {
                            "sbom_id": sbom.sbom_id,
                            "name": sbom.name,
                            "format": sbom.format,
                            "namespace": sbom.namespace,
                            "analysis_id": sbom.analysis.analysis_id if sbom.analysis else None,
                            "component_count": sbom.component_count,
                            "created_at": sbom.created_at.isoformat() if sbom.created_at else None,
                            "file_path": sbom.file_path,
                            # Extract source information from SBOM content or analysis
                            "source_info": self._extract_source_info(sbom)
                        }
                        for sbom in sboms
                    ],
                    "total": total_count,
                    "offset": offset,
                    "limit": limit
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/v1/dashboard/analyses/all")
        async def get_all_analyses(
            search: Optional[str] = None,
            status: Optional[str] = None,
            analysis_type: Optional[str] = None,
            offset: int = 0,
            limit: int = 50,
            db: Session = Depends(get_db_session)
        ):
            """Get all analyses with search and pagination"""
            try:
                analysis_repo = AnalysisRepository(db)
                query = db.query(analysis_repo.model)
                
                # Apply search filter
                if search:
                    search_pattern = f"%{search}%"
                    query = query.filter(
                        or_(
                            analysis_repo.model.analysis_id.ilike(search_pattern),
                            analysis_repo.model.analysis_type.ilike(search_pattern),
                            analysis_repo.model.location.ilike(search_pattern)
                        )
                    )
                
                # Apply status filter
                if status:
                    query = query.filter(analysis_repo.model.status == status)
                
                # Apply analysis type filter
                if analysis_type:
                    query = query.filter(analysis_repo.model.analysis_type == analysis_type)
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination and ordering
                analyses = query.order_by(analysis_repo.model.created_at.desc()).offset(offset).limit(limit).all()
                
                return {
                    "analyses": [
                        {
                            "analysis_id": a.analysis_id,
                            "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                            "analysis_type": a.analysis_type,
                            "component_count": a.component_count,
                            "vulnerability_count": a.vulnerability_count,
                            "critical_vulnerability_count": a.critical_vulnerability_count,
                            "high_vulnerability_count": a.high_vulnerability_count,
                            "source_info": self._extract_analysis_source_info(a),
                            "created_at": a.created_at.isoformat() if a.created_at else None,
                            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                            "duration_seconds": a.duration_seconds
                        }
                        for a in analyses
                    ],
                    "total": total_count,
                    "offset": offset,
                    "limit": limit
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/api/v1/dashboard/sboms/purge")
        async def purge_all_sboms(
            confirm: bool = False,
            db: Session = Depends(get_db_session)
        ):
            """Purge all SBOMs from database and filesystem"""
            if not confirm:
                raise HTTPException(
                    status_code=400, 
                    detail="Purge operation must be confirmed with confirm=true parameter"
                )
            
            try:
                sbom_repo = SBOMRepository(db)
                
                # Get all SBOMs before deletion for cleanup
                all_sboms = db.query(SBOM).all()
                sbom_count = len(all_sboms)
                
                if sbom_count == 0:
                    return {
                        "message": "No SBOMs found to purge",
                        "purged_count": 0
                    }
                
                # Delete from database first
                db.query(SBOM).delete()
                db.commit()
                
                # Clean up files from filesystem (optional - for file-based storage)
                import os
                import glob
                file_cleanup_count = 0
                
                try:
                    # Clean up SBOM files in data/sboms directory
                    sbom_files = glob.glob("data/sboms/*.json")
                    for file_path in sbom_files:
                        try:
                            os.remove(file_path)
                            file_cleanup_count += 1
                        except Exception as file_e:
                            # Log but don't fail the operation
                            logger.warning(f"Failed to remove SBOM file {file_path}: {file_e}")
                except Exception as cleanup_e:
                    logger.warning(f"SBOM file cleanup failed: {cleanup_e}")
                
                return {
                    "message": f"Successfully purged {sbom_count} SBOMs from database",
                    "purged_count": sbom_count,
                    "files_cleaned": file_cleanup_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to purge SBOMs: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to purge SBOMs: {str(e)}")
        
        # Setup additional routes
        self.setup_analyses_purge_route(app)
    
    def setup_analyses_purge_route(self, app: FastAPI):
        """Setup analyses purge route"""
        
        @app.delete("/api/v1/dashboard/analyses/purge")
        async def purge_all_analyses(
            confirm: bool = False,
            db: Session = Depends(get_db_session)
        ):
            """Purge all analyses from database with confirmation requirement"""
            if not confirm:
                raise HTTPException(
                    status_code=400, 
                    detail="Confirmation required. Add '?confirm=true' to confirm this destructive operation."
                )
            
            logger.warning("PURGE ALL ANALYSES operation initiated")
            
            try:
                from ..database.models import Analysis, Component, VulnerabilityScan, SBOM
                from datetime import datetime
                
                # Count current analyses
                analysis_count = db.query(Analysis).count()
                
                if analysis_count == 0:
                    return {
                        "message": "No analyses found to purge",
                        "purged_count": 0
                    }
                
                # Delete related data first (cascading will handle this, but being explicit)
                # Delete associated SBOMs
                sbom_count = db.query(SBOM).count()
                db.query(SBOM).delete()
                
                # Delete components (should cascade from analyses deletion)
                component_count = db.query(Component).count()
                db.query(Component).delete()
                
                # Delete vulnerability scans (should cascade from analyses deletion)
                vuln_scan_count = db.query(VulnerabilityScan).count()
                db.query(VulnerabilityScan).delete()
                
                # Finally delete analyses
                db.query(Analysis).delete()
                db.commit()
                
                # Clean up files from filesystem (optional - for file-based storage)
                import os
                import glob
                file_cleanup_count = 0
                
                try:
                    # Clean up analysis result files
                    analysis_files = glob.glob("data/analysis_results/*.json")
                    for file_path in analysis_files:
                        try:
                            os.remove(file_path)
                            file_cleanup_count += 1
                        except Exception as file_e:
                            logger.warning(f"Failed to remove analysis file {file_path}: {file_e}")
                    
                    # Clean up SBOM files as well since they depend on analyses
                    sbom_files = glob.glob("data/sboms/*.json")
                    for file_path in sbom_files:
                        try:
                            os.remove(file_path)
                            file_cleanup_count += 1
                        except Exception as file_e:
                            logger.warning(f"Failed to remove SBOM file {file_path}: {file_e}")
                            
                except Exception as cleanup_e:
                    logger.warning(f"File cleanup failed: {cleanup_e}")
                
                return {
                    "message": f"Successfully purged {analysis_count} analyses and all related data from database",
                    "purged_analyses": analysis_count,
                    "purged_components": component_count,
                    "purged_sboms": sbom_count,
                    "purged_vuln_scans": vuln_scan_count,
                    "files_cleaned": file_cleanup_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to purge analyses: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to purge analyses: {str(e)}")
        
        @app.delete("/api/v1/dashboard/purge-everything")
        async def purge_entire_database(
            confirm: str = "",
            db: Session = Depends(get_db_session)
        ):
            """
            NUCLEAR OPTION: Purge EVERYTHING from the database.
            This will delete ALL analyses, components, SBOMs, vulnerabilities, scans, etc.
            Requires confirmation string: 'DESTROY-ALL-DATA'
            """
            CONFIRMATION_STRING = "DESTROY-ALL-DATA"
            
            if confirm != CONFIRMATION_STRING:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Confirmation required. Add '?confirm={CONFIRMATION_STRING}' to confirm this EXTREMELY destructive operation."
                )
            
            logger.critical("NUCLEAR PURGE INITIATED - DELETING ALL DATABASE CONTENT")
            
            try:
                from ..database.models import (
                    Analysis, Component, SBOM, Vulnerability, VulnerabilityScan,
                    License, Agent, TelemetryData, Build
                )
                
                # Get counts before deletion
                counts = {
                    "analyses": db.query(Analysis).count(),
                    "components": db.query(Component).count(),
                    "sboms": db.query(SBOM).count(),
                    "vulnerabilities": db.query(Vulnerability).count(),
                    "vulnerability_scans": db.query(VulnerabilityScan).count(),
                    "licenses": db.query(License).count(),
                    "agents": db.query(Agent).count(),
                    "telemetry_data": db.query(TelemetryData).count(),
                    "builds": db.query(Build).count()
                }
                
                # Delete everything in order (respecting foreign key constraints)
                # Delete telemetry data first
                db.query(TelemetryData).delete()
                
                # Delete builds
                db.query(Build).delete()
                
                # Delete vulnerability scans
                db.query(VulnerabilityScan).delete()
                
                # Delete SBOMs
                db.query(SBOM).delete()
                
                # Delete components (this will also clear component_vulnerabilities and component_licenses)
                db.query(Component).delete()
                
                # Delete analyses
                db.query(Analysis).delete()
                
                # Delete vulnerabilities
                db.query(Vulnerability).delete()
                
                # Delete licenses
                db.query(License).delete()
                
                # Delete agents
                db.query(Agent).delete()
                
                # Commit all deletions
                db.commit()
                
                # Clean up filesystem (optional)
                file_cleanup_count = 0
                try:
                    # Clean up all data files
                    file_patterns = [
                        "data/analysis_results/*.json",
                        "data/sboms/*.json",
                        "data/vulnerabilities/*.json",
                        "data/metrics/*.json"
                    ]
                    
                    for pattern in file_patterns:
                        files = glob.glob(pattern)
                        for file_path in files:
                            try:
                                os.remove(file_path)
                                file_cleanup_count += 1
                            except Exception as file_e:
                                logger.warning(f"Failed to remove file {file_path}: {file_e}")
                                
                except Exception as cleanup_e:
                    logger.warning(f"File cleanup failed: {cleanup_e}")
                
                logger.critical(f"NUCLEAR PURGE COMPLETED - Deleted: {counts}")
                
                # Add warning about persistent volumes
                volume_warning = {
                    "warning": "Data may persist in Docker volumes",
                    "solution": "To completely remove all data including Docker volumes, run: docker compose down -v && docker compose up -d",
                    "volumes_affected": ["postgres_data", "telemetry_data", "logs"]
                }
                
                return {
                    "message": "NUCLEAR PURGE COMPLETED - ALL DATA DESTROYED",
                    "purged": counts,
                    "files_cleaned": file_cleanup_count,
                    "timestamp": datetime.utcnow(),
                    "volume_notice": volume_warning
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to purge everything: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to purge everything: {str(e)}")
    
    def _extract_analysis_source_info(self, analysis) -> Dict[str, Any]:
        """Extract source information from analysis object"""
        return {
            "analysis_type": analysis.analysis_type,
            "target_location": analysis.location,
            "analysis_id": analysis.analysis_id,
            "details": {
                "language": analysis.language,
                "duration": f"{analysis.duration_seconds:.1f}s" if analysis.duration_seconds else "N/A",
                "component_count": analysis.component_count,
                "vulnerability_count": analysis.vulnerability_count
            }
        }

    def _extract_source_info(self, sbom) -> Dict[str, Any]:
        """Extract source/target information from SBOM"""
        source_info = {
            "analysis_type": None,
            "target_location": None,
            "analysis_id": None,
            "details": {}
        }
        
        try:
            # Get analysis information
            if sbom.analysis:
                source_info["analysis_type"] = sbom.analysis.analysis_type
                source_info["target_location"] = sbom.analysis.location
                source_info["analysis_id"] = sbom.analysis.analysis_id
                if sbom.analysis.language:
                    source_info["details"]["language"] = sbom.analysis.language
                if sbom.analysis.duration_seconds:
                    source_info["details"]["duration"] = f"{sbom.analysis.duration_seconds:.1f}s"
            
            # Extract from SBOM content
            if sbom.content:
                content = sbom.content
                
                # For SPDX format
                if content.get("spdxVersion") and content.get("comment"):
                    comment_lines = content["comment"].split("\n")
                    for line in comment_lines:
                        if line.startswith("Analysis Target:"):
                            source_info["target_location"] = line.replace("Analysis Target:", "").strip()
                        elif line.startswith("Analysis Type:"):
                            source_info["analysis_type"] = line.replace("Analysis Type:", "").strip()
                        elif line.startswith("Analysis ID:"):
                            source_info["analysis_id"] = line.replace("Analysis ID:", "").strip()
                
                # For CycloneDX format
                elif content.get("bomFormat") == "CycloneDX":
                    metadata = content.get("metadata", {})
                    component = metadata.get("component", {})
                    
                    if component.get("name"):
                        source_info["target_location"] = component["name"]
                    
                    properties = component.get("properties", [])
                    for prop in properties:
                        if prop.get("name") == "sbom:analysis_type":
                            source_info["analysis_type"] = prop.get("value")
                        elif prop.get("name") == "sbom:target_location":
                            source_info["target_location"] = prop.get("value")
                        elif prop.get("name") == "sbom:analysis_id":
                            source_info["analysis_id"] = prop.get("value")
                        elif prop.get("name", "").startswith("sbom:source_"):
                            key = prop["name"].replace("sbom:source_", "")
                            source_info["details"][key] = prop.get("value")
                
                # For SWID format
                elif content.get("SoftwareIdentity"):
                    entities = content["SoftwareIdentity"].get("Entity", [])
                    if isinstance(entities, dict):
                        entities = [entities]
                    
                    for entity in entities:
                        name = entity.get("@name", "")
                        if name.startswith("Analysis Target:"):
                            source_info["target_location"] = name.replace("Analysis Target:", "").strip()
                        elif name.startswith("Analysis Type:"):
                            source_info["analysis_type"] = name.replace("Analysis Type:", "").strip()
        
        except Exception as e:
            # If extraction fails, return basic info
            pass
        
        return source_info
    
    def _generate_dashboard_html(self) -> str:
        """Generate enhanced dashboard HTML with database features"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perseus Enhanced Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .classification-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #00FF00;
            color: #000;
            font-weight: bold;
            text-align: center;
            padding: 3px 0;
            font-size: 12px;
            z-index: 1001;
            border-bottom: 1px solid #000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            padding-top: 25px;
            background: #f5f5f5;
            background-image: url('/static/images/nato-awacs-real.jpg');
            background-repeat: no-repeat;
            background-position: center center;
            background-attachment: fixed;
            background-size: 900px 600px;
            background-opacity: 0.08;
            color: #333;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 20px;
            margin: -20px -20px 20px -20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url('/static/images/nato-awacs-real.jpg');
            background-repeat: no-repeat;
            background-position: right center;
            background-size: 300px 200px;
            opacity: 0.12;
            z-index: 0;
        }
        .header > * {
            position: relative;
            z-index: 1;
        }
        .header h1 {
            margin: 0;
            font-size: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            position: relative;
            z-index: 2;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(5px);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .metric-card h3 {
            margin-top: 0;
            color: #2c3e50;
            font-size: 1.3rem;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
            margin: 0.5rem 0;
        }
        .metric-label {
            font-size: 14px;
            color: #7f8c8d;
        }
        .chart-container {
            grid-column: span 2;
            height: 400px;
        }
        .vulnerability-severity {
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
        }
        .severity-item {
            flex: 1;
            text-align: center;
            padding: 0.5rem;
            border-radius: 8px;
        }
        .critical { background: rgba(220, 20, 60, 0.3); }
        .high { background: rgba(255, 140, 0, 0.3); }
        .medium { background: rgba(255, 215, 0, 0.3); }
        .low { background: rgba(50, 205, 50, 0.3); }
        .component-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .component-item {
            background: #f8f9fa;
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 4px;
            border-left: 4px solid #3498db;
            border: 1px solid #ddd;
        }
        .component-name {
            font-weight: bold;
            font-size: 1.1rem;
            color: #2c3e50;
        }
        .component-details {
            font-size: 0.9rem;
            color: #7f8c8d;
            margin-top: 0.5rem;
        }
        .refresh-btn {
            position: fixed;
            top: 40px;
            right: 20px;
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: normal;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .refresh-btn:hover {
            background: #2980b9;
        }
        .loading {
            text-align: center;
            padding: 2rem;
            font-size: 1.2rem;
            color: #2c3e50;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <!-- Classification Banner -->
    <div class="classification-banner">NOT CLASSIFIED</div>
    
    <div class="header">
        <h1>🛡️ Perseus Enhanced Dashboard</h1>
        <p>Enterprise SBOM & Vulnerability Management Platform - Database-Powered Analytics</p>
        <div style="margin-top: 15px;">
            <a href="/dashboard" 
               style="display: inline-block; 
                      background: linear-gradient(45deg, #3498db, #2980b9); 
                      color: white; 
                      padding: 12px 25px; 
                      text-decoration: none; 
                      border-radius: 4px; 
                      font-weight: bold; 
                      margin-right: 10px;
                      box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                ← 📊 Classic Dashboard
            </a>
            <a href="/components/search" style="color: white; margin-right: 2rem; text-decoration: none;">🔍 Component Search</a>
            <a href="/docs" style="color: white; text-decoration: none;">📚 API Documentation</a>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
    
    <div id="loading" class="loading">
        <h2>🔄 Loading Enhanced Dashboard...</h2>
        <p>Fetching data from database...</p>
    </div>
    
    <div class="container">
        <div id="error" class="error" style="display: none;"></div>
        
        <div id="dashboard" class="dashboard-grid" style="display: none;">
        <!-- Analysis Statistics -->
        <div class="metric-card">
            <h3>📊 Analysis Statistics (30 Days)</h3>
            <div class="metric-value" id="total-analyses">-</div>
            <div class="metric-label">Total Analyses</div>
            <div style="margin-top: 1rem;">
                <div>Success Rate: <span id="success-rate">-</span>%</div>
                <div>Avg Duration: <span id="avg-duration">-</span>s</div>
            </div>
        </div>
        
        <!-- Vulnerability Summary -->
        <div class="metric-card">
            <h3>🚨 Platform-wide Vulnerability Summary</h3>
            <div style="font-size: 12px; color: #666; margin-bottom: 10px;">Total across all analyses</div>
            <div class="vulnerability-severity">
                <div class="severity-item critical">
                    <div class="metric-value" id="critical-vulns">-</div>
                    <div class="metric-label">Critical</div>
                </div>
                <div class="severity-item high">
                    <div class="metric-value" id="high-vulns">-</div>
                    <div class="metric-label">High</div>
                </div>
                <div class="severity-item medium">
                    <div class="metric-value" id="medium-vulns">-</div>
                    <div class="metric-label">Medium</div>
                </div>
                <div class="severity-item low">
                    <div class="metric-value" id="low-vulns">-</div>
                    <div class="metric-label">Low</div>
                </div>
            </div>
            <div>Total Unique Vulnerabilities: <span id="total-vulns">-</span></div>
        </div>
        
        <!-- Component Statistics -->
        <div class="metric-card">
            <h3>📦 Component Statistics</h3>
            <div class="metric-value" id="total-components">-</div>
            <div class="metric-label">Total Components</div>
            <div style="margin-top: 1rem;">
                <div>Unique: <span id="unique-components">-</span></div>
                <div>Vulnerable: <span id="vulnerable-components">-</span></div>
                <div>Vulnerability Rate: <span id="vulnerability-rate">-</span>%</div>
            </div>
        </div>
        
        <!-- SBOM Statistics -->
        <div class="metric-card">
            <h3>📋 SBOM Statistics</h3>
            <div class="metric-value" id="total-sboms">-</div>
            <div class="metric-label">Generated SBOMs</div>
            <div style="margin-top: 1rem;">
                <div>Coverage: <span id="sbom-coverage">-</span>%</div>
                <div id="sbom-formats">-</div>
            </div>
        </div>
        
        <!-- Vulnerability Trends Chart -->
        <div class="metric-card chart-container">
            <h3>📊 Vulnerability Trends (30 Days)</h3>
            <canvas id="trendsChart"></canvas>
        </div>
        
        <!-- Vulnerability Severity Distribution -->
        <div class="metric-card chart-container">
            <h3>🎯 Vulnerability Severity Distribution</h3>
            <canvas id="severityChart"></canvas>
        </div>
        
        <!-- Top Vulnerable Components -->
        <div class="metric-card">
            <h3>🎯 Top Vulnerable Components</h3>
            <div id="vulnerable-components-list" class="component-list">
                Loading...
            </div>
        </div>
        
        <!-- Recent Analyses -->
        <div class="metric-card">
            <h3>⏱️ Recent Analyses</h3>
            <div id="recent-analyses-list" class="component-list">
                Loading...
            </div>
        </div>
        
        <!-- All Analyses with Management -->
        <div class="metric-card" style="grid-column: span 2;">
            <h3>🔍 All Analyses Management</h3>
            <div style="margin-bottom: 1rem;">
                <input type="text" id="analysis-search" placeholder="Search analyses..." 
                       style="padding: 8px; border-radius: 4px; border: 1px solid #ddd; background: white; color: #333; width: 300px; margin-right: 1rem;">
                <select id="analysis-type-filter" style="padding: 8px; border-radius: 4px; border: 1px solid #ddd; background: white; color: #333;">
                    <option value="">All Types</option>
                    <option value="source">Source</option>
                    <option value="binary">Binary</option>
                    <option value="docker">Docker</option>
                    <option value="os">OS</option>
                </select>
                <select id="analysis-status-filter" style="padding: 8px; border-radius: 4px; border: 1px solid #ddd; background: white; color: #333; margin-left: 1rem;">
                    <option value="">All Statuses</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                    <option value="in_progress">In Progress</option>
                </select>
                <button onclick="searchAnalyses()" style="margin-left: 1rem; background: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    🔍 Search
                </button>
                <button onclick="showPurgeAnalysesConfirm()" style="margin-left: 1rem; background: #e74c3c; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    🗑️ Purge All Analyses
                </button>
            </div>
            <div style="margin-bottom: 1rem; color: #7f8c8d;">
                Total Analyses: <span id="total-analysis-count">-</span>
            </div>
            <div id="all-analyses-list" class="component-list" style="max-height: 400px; overflow-y: auto;">
                Loading analyses...
            </div>
            <div style="margin-top: 1rem; text-align: center;">
                <button id="load-more-analyses" onclick="loadMoreAnalyses()" style="background: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; display: none;">
                    Load More
                </button>
            </div>
        </div>
        
        <!-- Generated SBOMs -->
        <div class="metric-card" style="grid-column: span 2;">
            <h3>📋 All Generated SBOMs</h3>
            <div style="margin-bottom: 1rem;">
                <input type="text" id="sbom-search" placeholder="Search SBOMs..." 
                       style="padding: 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.1); color: white; width: 300px; margin-right: 1rem;">
                <select id="sbom-format-filter" style="padding: 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.1); color: white;">
                    <option value="">All Formats</option>
                    <option value="spdx">SPDX</option>
                    <option value="cyclonedx">CycloneDX</option>
                    <option value="swid">SWID</option>
                </select>
                <button onclick="searchSBOMs()" style="margin-left: 1rem; background: #4fd1c7; color: #1e3c72; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    🔍 Search
                </button>
                <button onclick="downloadAllSBOMs()" style="margin-left: 1rem; background: #4fd1c7; color: #1e3c72; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    📥 Download All
                </button>
                <button onclick="showPurgeConfirmation()" style="margin-left: 1rem; background: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    🗑️ Purge All SBOMs
                </button>
            </div>
            <div id="sbom-stats" style="margin-bottom: 1rem; color: #b0c4de;">
                Total SBOMs: <span id="total-sbom-count">-</span>
            </div>
            <div id="generated-sboms-list" class="component-list" style="max-height: 500px;">
                Loading...
            </div>
            <div id="sbom-pagination" style="margin-top: 1rem; text-align: center;">
                <button id="prev-page" onclick="loadPreviousPage()" style="background: #4fd1c7; color: #1e3c72; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-right: 1rem;">
                    ← Previous
                </button>
                <span id="page-info">Page 1</span>
                <button id="next-page" onclick="loadNextPage()" style="background: #4fd1c7; color: #1e3c72; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-left: 1rem;">
                    Next →
                </button>
            </div>
        </div>
        
        <!-- DANGER ZONE - System Administration -->
        <div class="metric-card" style="grid-column: span 2; background: linear-gradient(135deg, #2c0000 0%, #4a0000 100%); border: 2px solid #ff0000;">
            <h3 style="color: #ff6666;">☢️ DANGER ZONE - System Administration</h3>
            <div style="background: rgba(255, 0, 0, 0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <p style="color: #ffcccc; margin: 0 0 1rem 0;">
                    <strong>⚠️ EXTREME CAUTION:</strong> The following operations are IRREVERSIBLE and will permanently delete ALL data from the database.
                </p>
                <div style="text-align: center;">
                    <button onclick="showNuclearPurgeConfirm()" 
                            style="background: #ff0000; 
                                   color: white; 
                                   border: 2px solid #cc0000; 
                                   padding: 12px 24px; 
                                   border-radius: 4px; 
                                   cursor: pointer; 
                                   font-weight: bold; 
                                   font-size: 16px;
                                   box-shadow: 0 4px 6px rgba(255,0,0,0.3);
                                   transition: all 0.3s;"
                            onmouseover="this.style.background='#cc0000'; this.style.boxShadow='0 6px 8px rgba(255,0,0,0.5)';"
                            onmouseout="this.style.background='#ff0000'; this.style.boxShadow='0 4px 6px rgba(255,0,0,0.3)';">
                        ☢️ NUCLEAR PURGE - DELETE EVERYTHING
                    </button>
                </div>
                <p style="color: #ff9999; margin: 1rem 0 0 0; font-size: 14px; text-align: center;">
                    This will delete ALL analyses, components, SBOMs, vulnerabilities, scans, licenses, agents, telemetry data, and builds.
                </p>
            </div>
        </div>
    </div>

    <script>
        let trendsChart = null;
        let severityChart = null;
        
        // Helper function to format dates with timezone
        function formatDateWithTimezone(dateString) {
            const date = new Date(dateString);
            const options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZoneName: 'short'
            };
            return date.toLocaleString(undefined, options);
        }
        
        function formatDateOnly(dateString) {
            const date = new Date(dateString);
            const options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                timeZoneName: 'short'
            };
            return date.toLocaleDateString(undefined, options);
        }
        let currentPage = 0;
        let pageSize = 50;
        let totalSBOMs = 0;
        let currentSearch = '';
        let currentFormat = '';
        
        async function fetchDashboardData() {
            try {
                const response = await fetch('/api/v1/dashboard/metrics');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
                throw error;
            }
        }
        
        async function fetchTrendsData() {
            try {
                const response = await fetch('/api/v1/dashboard/trends?days=30');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching trends data:', error);
                return { trends: [] };
            }
        }
        
        async function fetchAllSbomsData(offset = 0, limit = 50) {
            try {
                let url = `/api/v1/dashboard/sboms/all?offset=${offset}&limit=${limit}`;
                if (currentSearch) {
                    url += `&search=${encodeURIComponent(currentSearch)}`;
                }
                if (currentFormat) {
                    url += `&format=${currentFormat}`;
                }
                
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching SBOMs data:', error);
                return { sboms: [], total: 0 };
            }
        }
        
        function updateDashboard(data) {
            // Analysis Statistics
            const analysisStats = data.analysis_statistics;
            document.getElementById('total-analyses').textContent = analysisStats.total_analyses;
            document.getElementById('success-rate').textContent = analysisStats.success_rate.toFixed(1);
            document.getElementById('avg-duration').textContent = analysisStats.average_duration_seconds.toFixed(1);
            
            // Vulnerability Summary
            const vulnSummary = data.vulnerability_summary;
            document.getElementById('critical-vulns').textContent = vulnSummary.total_critical || 0;
            document.getElementById('high-vulns').textContent = vulnSummary.total_high || 0;
            document.getElementById('medium-vulns').textContent = vulnSummary.total_medium || 0;
            document.getElementById('low-vulns').textContent = vulnSummary.total_low || 0;
            document.getElementById('total-vulns').textContent = vulnSummary.total_vulnerabilities;
            
            // Component Statistics
            const compStats = data.component_statistics;
            document.getElementById('total-components').textContent = compStats.total_components;
            document.getElementById('unique-components').textContent = compStats.unique_components;
            document.getElementById('vulnerable-components').textContent = compStats.vulnerable_components;
            document.getElementById('vulnerability-rate').textContent = compStats.vulnerability_rate.toFixed(1);
            
            // SBOM Statistics
            const sbomStats = data.sbom_statistics;
            document.getElementById('total-sboms').textContent = sbomStats.total_sboms;
            document.getElementById('sbom-coverage').textContent = sbomStats.sbom_coverage.toFixed(1);
            
            // Format distribution
            const formatDist = Object.entries(sbomStats.format_distribution)
                .map(([format, count]) => `${format.toUpperCase()}: ${count}`)
                .join(', ');
            document.getElementById('sbom-formats').textContent = formatDist || 'No SBOMs';
            
            // Top Vulnerable Components
            const vulnList = document.getElementById('vulnerable-components-list');
            vulnList.innerHTML = data.top_vulnerable_components.map(comp => `
                <div class="component-item">
                    <div class="component-name">${comp.name} v${comp.version}</div>
                    <div class="component-details">
                        🚨 ${comp.critical} Critical, ${comp.high} High | 
                        📊 ${comp.vulnerabilities} Total | 
                        🔍 ${comp.affected_analyses} Analyses
                    </div>
                </div>
            `).join('') || '<div>No vulnerable components found</div>';
            
            // Recent Analyses
            const analysesList = document.getElementById('recent-analyses-list');
            analysesList.innerHTML = data.recent_analyses.map(analysis => `
                <div class="component-item">
                    <div class="component-name">${analysis.analysis_type.toUpperCase()} - ${analysis.status}</div>
                    <div class="component-details">
                        📦 ${analysis.component_count} Components | 
                        🚨 ${analysis.vulnerability_count} Vulnerabilities | 
                        ⏰ ${formatDateWithTimezone(analysis.created_at)}
                    </div>
                </div>
            `).join('') || '<div>No recent analyses found</div>';
        }
        
        function updateSbomsList(sbomsData) {
            const sbomsList = document.getElementById('generated-sboms-list');
            totalSBOMs = sbomsData.total;
            
            // Update total count
            document.getElementById('total-sbom-count').textContent = totalSBOMs;
            
            // Update pagination info
            const totalPages = Math.ceil(totalSBOMs / pageSize);
            document.getElementById('page-info').textContent = `Page ${currentPage + 1} of ${totalPages}`;
            
            // Enable/disable pagination buttons
            document.getElementById('prev-page').disabled = currentPage === 0;
            document.getElementById('next-page').disabled = (currentPage + 1) * pageSize >= totalSBOMs;
            
            sbomsList.innerHTML = sbomsData.sboms.map(sbom => {
                const sourceInfo = sbom.source_info || {};
                const targetLocation = sourceInfo.target_location || 'Unknown';
                const analysisType = sourceInfo.analysis_type || 'Unknown';
                const details = sourceInfo.details || {};
                
                return `
                    <div class="component-item">
                        <div class="component-name">
                            ${sbom.format.toUpperCase()}: ${sbom.name}
                            <button onclick="downloadSBOM('${sbom.sbom_id}')" 
                                    style="float: right; background: #4fd1c7; color: #1e3c72; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">
                                📥 Download
                            </button>
                        </div>
                        <div class="component-details">
                            🆔 ${sbom.sbom_id} | 
                            📦 ${sbom.component_count} Components | 
                            🔗 Analysis: ${sbom.analysis_id.substring(0, 8)}... | 
                            ⏰ ${formatDateWithTimezone(sbom.created_at)}
                            <br>🎯 <strong>Target:</strong> ${targetLocation} | 
                            🔍 <strong>Type:</strong> ${analysisType.toUpperCase()}
                            ${details.language ? ` | 💻 <strong>Language:</strong> ${details.language}` : ''}
                            ${details.duration ? ` | ⏱️ <strong>Duration:</strong> ${details.duration}` : ''}
                            ${sbom.file_path ? `<br>📁 ${sbom.file_path}` : ''}
                        </div>
                    </div>
                `;
            }).join('') || '<div>No SBOMs found</div>';
        }
        
        async function loadSBOMs() {
            const sbomsData = await fetchAllSbomsData(currentPage * pageSize, pageSize);
            updateSbomsList(sbomsData);
        }
        
        function loadPreviousPage() {
            if (currentPage > 0) {
                currentPage--;
                loadSBOMs();
            }
        }
        
        function loadNextPage() {
            if ((currentPage + 1) * pageSize < totalSBOMs) {
                currentPage++;
                loadSBOMs();
            }
        }
        
        function searchSBOMs() {
            currentSearch = document.getElementById('sbom-search').value;
            currentFormat = document.getElementById('sbom-format-filter').value;
            currentPage = 0;
            loadSBOMs();
        }
        
        async function downloadAllSBOMs() {
            try {
                showError('Preparing to download all SBOMs...');
                
                // Fetch all SBOMs (up to 1000)
                let url = '/api/v1/dashboard/sboms/all?limit=1000';
                if (currentSearch) {
                    url += `&search=${encodeURIComponent(currentSearch)}`;
                }
                if (currentFormat) {
                    url += `&format=${currentFormat}`;
                }
                
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const data = await response.json();
                
                // Create a summary file with all SBOM IDs and metadata
                const summary = {
                    generated_at: new Date().toISOString(),
                    total_sboms: data.total,
                    sboms: data.sboms.map(sbom => ({
                        sbom_id: sbom.sbom_id,
                        name: sbom.name,
                        format: sbom.format,
                        component_count: sbom.component_count,
                        created_at: sbom.created_at,
                        download_url: `/sbom/${sbom.sbom_id}`
                    }))
                };
                
                // Download the summary
                const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' });
                const url_download = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url_download;
                a.download = `sbom-summary-${new Date().toLocaleDateString('sv-SE')}.json`;
                a.click();
                URL.revokeObjectURL(url_download);
                
                document.getElementById('error').style.display = 'none';
                alert(`Downloaded summary of ${data.total} SBOMs. Use the download URLs in the summary file to fetch individual SBOMs.`);
            } catch (error) {
                showError(`Failed to download SBOMs: ${error.message}`);
            }
        }
        
        async function downloadSBOM(sbomId) {
            try {
                const response = await fetch(`/sbom/${sbomId}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const sbom = await response.json();
                
                // Create download link
                const blob = new Blob([JSON.stringify(sbom, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `sbom-${sbomId}.json`;
                a.click();
                URL.revokeObjectURL(url);
            } catch (error) {
                showError(`Failed to download SBOM: ${error.message}`);
            }
        }
        
        function updateTrendsChart(trendsData) {
            updateVulnerabilityTrends(trendsData);
            updateSeverityDistribution(trendsData);
        }
        
        function updateVulnerabilityTrends(trendsData) {
            const ctx = document.getElementById('trendsChart').getContext('2d');
            
            if (trendsChart) {
                trendsChart.destroy();
            }
            
            const trends = trendsData.trends || [];
            
            trendsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: trends.map(t => formatDateOnly(t.date)),
                    datasets: [
                        {
                            label: 'Critical',
                            data: trends.map(t => t.critical_vulnerabilities),
                            backgroundColor: '#dc3545',
                            borderColor: '#dc3545',
                            borderWidth: 1
                        },
                        {
                            label: 'High',
                            data: trends.map(t => t.high_vulnerabilities),
                            backgroundColor: '#fd7e14',
                            borderColor: '#fd7e14',
                            borderWidth: 1
                        },
                        {
                            label: 'Medium',
                            data: trends.map(t => t.medium_vulnerabilities || 0),
                            backgroundColor: '#ffc107',
                            borderColor: '#ffc107',
                            borderWidth: 1
                        },
                        {
                            label: 'Low',
                            data: trends.map(t => t.low_vulnerabilities || 0),
                            backgroundColor: '#28a745',
                            borderColor: '#28a745',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: {
                            left: 10,
                            right: 10,
                            top: 10,
                            bottom: 25
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Daily Vulnerability Discovery',
                            font: { size: 14, weight: 'bold' },
                            color: '#2c3e50',
                            padding: {
                                top: 10,
                                bottom: 10
                            }
                        },
                        legend: {
                            position: 'top',
                            labels: { 
                                usePointStyle: true,
                                color: '#2c3e50',
                                padding: 15
                            }
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            ticks: { 
                                color: '#2c3e50',
                                maxRotation: 45,
                                padding: 8
                            },
                            grid: { 
                                color: 'rgba(44, 62, 80, 0.1)',
                                drawTicks: true,
                                tickLength: 8
                            },
                            offset: true
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: { 
                                color: '#2c3e50',
                                padding: 15
                            },
                            grid: { 
                                color: 'rgba(44, 62, 80, 0.1)',
                                drawTicks: true,
                                tickLength: 8
                            },
                            title: {
                                display: true,
                                text: 'Number of Vulnerabilities',
                                color: '#2c3e50',
                                padding: {
                                    top: 15,
                                    bottom: 15
                                }
                            },
                            grace: '8%',
                            offset: true
                        }
                    },
                    interaction: {
                        mode: 'index',
                        intersect: false
                    }
                }
            });
        }
        
        function updateSeverityDistribution(trendsData) {
            const ctx = document.getElementById('severityChart').getContext('2d');
            
            if (severityChart) {
                severityChart.destroy();
            }
            
            const trends = trendsData.trends || [];
            
            // Calculate total vulnerabilities by severity across all days
            const totals = trends.reduce((acc, trend) => {
                acc.critical += trend.critical_vulnerabilities || 0;
                acc.high += trend.high_vulnerabilities || 0;
                acc.medium += trend.medium_vulnerabilities || 0;
                acc.low += trend.low_vulnerabilities || 0;
                return acc;
            }, { critical: 0, high: 0, medium: 0, low: 0 });
            
            const data = [totals.critical, totals.high, totals.medium, totals.low];
            const labels = ['Critical', 'High', 'Medium', 'Low'];
            const colors = ['#dc3545', '#fd7e14', '#ffc107', '#28a745'];
            
            severityChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors,
                        borderColor: colors.map(color => color + '80'),
                        borderWidth: 2,
                        hoverBorderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Total Vulnerabilities by Severity (30 Days)',
                            font: { size: 14, weight: 'bold' },
                            color: '#2c3e50'
                        },
                        legend: {
                            position: 'bottom',
                            labels: { 
                                usePointStyle: true,
                                color: '#2c3e50',
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    return data.labels.map((label, i) => {
                                        const value = data.datasets[0].data[i];
                                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                        return {
                                            text: `${label}: ${value} (${percentage}%)`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            hidden: false,
                                            index: i
                                        };
                                    });
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return `${label}: ${value} vulnerabilities (${percentage}%)`;
                                }
                            }
                        }
                    },
                    animation: {
                        animateScale: true,
                        animateRotate: true
                    }
                }
            });
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = `❌ Error: ${message}`;
            errorDiv.style.display = 'block';
        }
        
        function showPurgeConfirmation() {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            `;
            
            const dialog = document.createElement('div');
            dialog.style.cssText = `
                background: white;
                border-radius: 12px;
                padding: 30px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                color: #333;
            `;
            
            dialog.innerHTML = `
                <h2 style="color: #dc3545; margin-top: 0; display: flex; align-items: center;">
                    ⚠️ Confirm SBOM Purge
                </h2>
                <p style="margin: 20px 0; line-height: 1.6;">
                    <strong>This action will permanently delete ALL generated SBOMs!</strong>
                </p>
                <p style="margin: 20px 0; line-height: 1.6;">
                    This includes:
                    <ul style="margin: 10px 0;">
                        <li>All SBOM records from the database</li>
                        <li>All SBOM files from the filesystem</li>
                        <li>This action <strong>CANNOT</strong> be undone</li>
                    </ul>
                </p>
                <div style="margin-top: 30px; display: flex; gap: 15px; justify-content: flex-end;">
                    <button id="cancel-purge" style="
                        background: #6c757d; 
                        color: white; 
                        border: none; 
                        padding: 10px 20px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-size: 14px;
                    ">
                        Cancel
                    </button>
                    <button id="confirm-purge" style="
                        background: #dc3545; 
                        color: white; 
                        border: none; 
                        padding: 10px 20px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-size: 14px;
                        font-weight: bold;
                    ">
                        🗑️ Yes, Delete All SBOMs
                    </button>
                </div>
            `;
            
            modal.appendChild(dialog);
            document.body.appendChild(modal);
            
            // Add event listeners
            document.getElementById('cancel-purge').onclick = () => {
                document.body.removeChild(modal);
            };
            
            document.getElementById('confirm-purge').onclick = async () => {
                document.body.removeChild(modal);
                await purgeAllSBOMs();
            };
            
            // Close on background click
            modal.onclick = (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                }
            };
        }
        
        async function purgeAllSBOMs() {
            try {
                // Show loading state
                showError('Purging all SBOMs... Please wait.');
                
                const response = await fetch('/api/v1/dashboard/sboms/purge?confirm=true', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status}`);
                }
                
                const result = await response.json();
                
                // Hide error div and show success
                document.getElementById('error').style.display = 'none';
                
                // Show success message
                const successModal = document.createElement('div');
                successModal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 10000;
                `;
                
                const successDialog = document.createElement('div');
                successDialog.style.cssText = `
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    max-width: 400px;
                    width: 90%;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                    color: #333;
                    text-align: center;
                `;
                
                successDialog.innerHTML = `
                    <h2 style="color: #28a745; margin-top: 0;">
                        ✅ Purge Completed
                    </h2>
                    <p style="margin: 20px 0;">
                        Successfully deleted <strong>${result.purged_count}</strong> SBOMs from database
                    </p>
                    ${result.files_cleaned ? `<p>Cleaned <strong>${result.files_cleaned}</strong> SBOM files</p>` : ''}
                    <button onclick="location.reload()" style="
                        background: #28a745; 
                        color: white; 
                        border: none; 
                        padding: 10px 20px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: bold;
                    ">
                        Refresh Dashboard
                    </button>
                `;
                
                successModal.appendChild(successDialog);
                document.body.appendChild(successModal);
                
                // Auto-refresh the dashboard after 3 seconds
                setTimeout(() => {
                    location.reload();
                }, 3000);
                
            } catch (error) {
                showError(`Failed to purge SBOMs: ${error.message}`);
            }
        }
        
        // Analyses Management Functions
        let currentAnalysesOffset = 0;
        let totalAnalyses = 0;
        
        async function loadAnalyses(search = '', type = '', status = '', offset = 0, limit = 50) {
            try {
                let url = `/api/v1/dashboard/analyses/all?offset=${offset}&limit=${limit}`;
                if (search) url += `&search=${encodeURIComponent(search)}`;
                if (type) url += `&analysis_type=${encodeURIComponent(type)}`;
                if (status) url += `&status=${encodeURIComponent(status)}`;
                
                const response = await fetch(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                return await response.json();
            } catch (error) {
                showError(`Failed to load analyses: ${error.message}`);
                return { analyses: [], total: 0 };
            }
        }
        
        async function searchAnalyses() {
            const search = document.getElementById('analysis-search').value;
            const type = document.getElementById('analysis-type-filter').value;
            const status = document.getElementById('analysis-status-filter').value;
            
            currentAnalysesOffset = 0;
            const data = await loadAnalyses(search, type, status, 0, 50);
            updateAnalysesList(data, false);
        }
        
        async function loadMoreAnalyses() {
            const search = document.getElementById('analysis-search').value;
            const type = document.getElementById('analysis-type-filter').value;
            const status = document.getElementById('analysis-status-filter').value;
            
            currentAnalysesOffset += 50;
            const data = await loadAnalyses(search, type, status, currentAnalysesOffset, 50);
            updateAnalysesList(data, true);
        }
        
        function updateAnalysesList(analysesData, append = false) {
            const analysesList = document.getElementById('all-analyses-list');
            totalAnalyses = analysesData.total;
            
            // Update total count
            document.getElementById('total-analysis-count').textContent = totalAnalyses;
            
            const analysesHtml = analysesData.analyses.map(analysis => {
                const sourceInfo = analysis.source_info || {};
                const statusColor = analysis.status === 'completed' ? '#28a745' : 
                                  analysis.status === 'failed' ? '#dc3545' : '#ffc107';
                
                return `
                    <div class="component-item" style="border-left-color: ${statusColor};">
                        <div class="component-name">
                            ${analysis.analysis_type.toUpperCase()} Analysis - ${analysis.status.toUpperCase()}
                        </div>
                        <div class="component-details">
                            📍 <strong>Target:</strong> ${sourceInfo.target_location || 'Unknown'} | 
                            🆔 <strong>ID:</strong> ${analysis.analysis_id}<br>
                            📦 <strong>Components:</strong> ${analysis.component_count || 0} | 
                            🚨 <strong>Vulnerabilities:</strong> ${analysis.vulnerability_count || 0} | 
                            ⏰ <strong>Created:</strong> ${formatDateWithTimezone(analysis.created_at)}
                            ${analysis.duration_seconds ? ` | ⏱️ <strong>Duration:</strong> ${analysis.duration_seconds.toFixed(1)}s` : ''}
                        </div>
                    </div>
                `;
            }).join('');
            
            if (append) {
                analysesList.innerHTML += analysesHtml;
            } else {
                analysesList.innerHTML = analysesHtml || '<div>No analyses found</div>';
            }
            
            // Show/hide load more button
            const loadMoreBtn = document.getElementById('load-more-analyses');
            if (currentAnalysesOffset + 50 < totalAnalyses) {
                loadMoreBtn.style.display = 'inline-block';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        }
        
        function showPurgeAnalysesConfirm() {
            const confirmModal = document.createElement('div');
            confirmModal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            `;
            
            const confirmDialog = document.createElement('div');
            confirmDialog.style.cssText = `
                background: white;
                padding: 30px;
                border-radius: 12px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                color: #333;
                text-align: center;
            `;
            
            confirmDialog.innerHTML = `
                <h2 style="color: #e74c3c; margin-top: 0;">
                    ⚠️ DANGEROUS OPERATION
                </h2>
                <p style="margin: 20px 0; font-size: 16px;">
                    You are about to <strong>permanently delete ALL analyses</strong> and related data:
                </p>
                <ul style="text-align: left; margin: 20px 0; color: #666;">
                    <li>🔍 All analysis records</li>
                    <li>📦 All component data</li>
                    <li>📋 All generated SBOMs</li>
                    <li>🚨 All vulnerability scans</li>
                    <li>📁 All related files</li>
                </ul>
                <p style="margin: 20px 0; font-weight: bold; color: #e74c3c;">
                    This action cannot be undone!
                </p>
                <p style="margin: 20px 0;">
                    Total analyses to be deleted: <strong id="confirm-analysis-count">${totalAnalyses}</strong>
                </p>
                <div style="margin-top: 30px;">
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" style="
                        background: #6c757d; 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        margin-right: 15px;
                        font-weight: bold;
                    ">
                        ❌ Cancel
                    </button>
                    <button onclick="showFinalAnalysesConfirm()" style="
                        background: #e74c3c; 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: bold;
                    ">
                        🗑️ Continue to Final Confirmation
                    </button>
                </div>
            `;
            
            confirmModal.appendChild(confirmDialog);
            document.body.appendChild(confirmModal);
        }
        
        function showFinalAnalysesConfirm() {
            // Remove first confirmation
            document.querySelector('div[style*="position: fixed"]').remove();
            
            const finalModal = document.createElement('div');
            finalModal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(220, 20, 60, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10001;
            `;
            
            const finalDialog = document.createElement('div');
            finalDialog.style.cssText = `
                background: white;
                padding: 40px;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
                color: #333;
                text-align: center;
                border: 3px solid #e74c3c;
            `;
            
            finalDialog.innerHTML = `
                <h2 style="color: #e74c3c; margin-top: 0; font-size: 24px;">
                    🚨 FINAL CONFIRMATION REQUIRED
                </h2>
                <p style="margin: 25px 0; font-size: 18px; font-weight: bold;">
                    Last chance to abort this operation!
                </p>
                <p style="margin: 20px 0; font-size: 16px;">
                    Type <strong style="color: #e74c3c;">"DELETE ALL ANALYSES"</strong> to confirm:
                </p>
                <input type="text" id="final-confirm-input" placeholder="Type here..." style="
                    width: 100%;
                    padding: 15px;
                    font-size: 16px;
                    border: 2px solid #e74c3c;
                    border-radius: 6px;
                    margin: 20px 0;
                    text-align: center;
                ">
                <div style="margin-top: 30px;">
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" style="
                        background: #28a745; 
                        color: white; 
                        border: none; 
                        padding: 15px 30px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        margin-right: 20px;
                        font-weight: bold;
                        font-size: 16px;
                    ">
                        🛡️ ABORT - Keep All Data
                    </button>
                    <button onclick="confirmPurgeAnalyses()" style="
                        background: #e74c3c; 
                        color: white; 
                        border: none; 
                        padding: 15px 30px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 16px;
                    ">
                        💀 DELETE EVERYTHING
                    </button>
                </div>
            `;
            
            finalModal.appendChild(finalDialog);
            document.body.appendChild(finalModal);
            
            // Focus on input
            document.getElementById('final-confirm-input').focus();
        }
        
        async function confirmPurgeAnalyses() {
            const input = document.getElementById('final-confirm-input');
            if (input.value !== 'DELETE ALL ANALYSES') {
                alert('❌ Confirmation text does not match. Type exactly: "DELETE ALL ANALYSES"');
                input.focus();
                return;
            }
            
            // Remove confirmation modal
            document.querySelector('div[style*="position: fixed"]').remove();
            
            await purgeAllAnalyses();
        }
        
        async function purgeAllAnalyses() {
            try {
                // Show loading state
                showError('🔄 Purging all analyses... This may take a few minutes. Please wait.');
                
                const response = await fetch('/api/v1/dashboard/analyses/purge?confirm=true', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status}`);
                }
                
                const result = await response.json();
                
                // Hide error div and show success
                document.getElementById('error').style.display = 'none';
                
                // Show success message
                const successModal = document.createElement('div');
                successModal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.8);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 10000;
                `;
                
                const successDialog = document.createElement('div');
                successDialog.style.cssText = `
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    max-width: 600px;
                    width: 90%;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                    color: #333;
                    text-align: center;
                `;
                
                successDialog.innerHTML = `
                    <h2 style="color: #28a745; margin-top: 0;">
                        ✅ Purge Completed Successfully
                    </h2>
                    <p style="margin: 20px 0; font-size: 16px;">
                        Successfully deleted <strong>${result.purged_analyses}</strong> analyses and all related data:
                    </p>
                    <ul style="text-align: left; margin: 20px 0; color: #666;">
                        <li>📦 <strong>${result.purged_components}</strong> components deleted</li>
                        <li>📋 <strong>${result.purged_sboms}</strong> SBOMs deleted</li>
                        <li>🚨 <strong>${result.purged_vuln_scans}</strong> vulnerability scans deleted</li>
                        ${result.files_cleaned ? `<li>📁 <strong>${result.files_cleaned}</strong> files cleaned</li>` : ''}
                    </ul>
                    <button onclick="location.reload()" style="
                        background: #28a745; 
                        color: white; 
                        border: none; 
                        padding: 15px 30px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 16px;
                    ">
                        🔄 Refresh Dashboard
                    </button>
                `;
                
                successModal.appendChild(successDialog);
                document.body.appendChild(successModal);
                
                // Auto-refresh the dashboard after 5 seconds
                setTimeout(() => {
                    location.reload();
                }, 5000);
                
            } catch (error) {
                showError(`Failed to purge analyses: ${error.message}`);
            }
        }
        
        function showNuclearPurgeConfirm() {
            const confirmModal = document.createElement('div');
            confirmModal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(139, 0, 0, 0.9);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 20000;
            `;
            
            const confirmDialog = document.createElement('div');
            confirmDialog.style.cssText = `
                background: #1a1a1a;
                padding: 40px;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(255, 0, 0, 0.5);
                color: white;
                text-align: center;
                border: 3px solid #ff0000;
            `;
            
            confirmDialog.innerHTML = `
                <h2 style="color: #ff0000; margin-top: 0; font-size: 28px;">
                    ☢️ NUCLEAR PURGE WARNING ☢️
                </h2>
                <p style="margin: 20px 0; font-size: 18px; color: #ffcccc;">
                    <strong>THIS WILL DESTROY EVERYTHING IN THE DATABASE!</strong>
                </p>
                <div style="background: rgba(255, 0, 0, 0.2); padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="color: #ff9999; margin: 10px 0;">You are about to delete:</p>
                    <ul style="text-align: left; color: #ffcccc; margin: 10px 0;">
                        <li>🔍 ALL Analyses</li>
                        <li>📦 ALL Components</li>
                        <li>📋 ALL SBOMs</li>
                        <li>🚨 ALL Vulnerabilities</li>
                        <li>🔬 ALL Vulnerability Scans</li>
                        <li>📜 ALL Licenses</li>
                        <li>🤖 ALL Agents</li>
                        <li>📊 ALL Telemetry Data</li>
                        <li>🏗️ ALL Builds</li>
                        <li>📁 ALL Related Files</li>
                    </ul>
                </div>
                <p style="margin: 20px 0; font-size: 20px; font-weight: bold; color: #ff6666;">
                    ⚠️ THIS CANNOT BE UNDONE! ⚠️
                </p>
                <div style="margin-top: 30px;">
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" style="
                        background: #28a745; 
                        color: white; 
                        border: none; 
                        padding: 15px 30px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        margin-right: 20px;
                        font-weight: bold;
                        font-size: 18px;
                    ">
                        🛡️ ABORT - I WANT TO KEEP MY DATA
                    </button>
                    <button onclick="showSecondNuclearConfirm()" style="
                        background: #ff0000; 
                        color: white; 
                        border: 2px solid #cc0000; 
                        padding: 15px 30px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 18px;
                    ">
                        ⚠️ I UNDERSTAND - CONTINUE
                    </button>
                </div>
            `;
            
            confirmModal.appendChild(confirmDialog);
            document.body.appendChild(confirmModal);
        }
        
        function showSecondNuclearConfirm() {
            // Remove first confirmation
            document.querySelector('div[style*="position: fixed"]').remove();
            
            const secondModal = document.createElement('div');
            secondModal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 0, 0, 0.95);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 20001;
            `;
            
            const secondDialog = document.createElement('div');
            secondDialog.style.cssText = `
                background: black;
                padding: 50px;
                border-radius: 12px;
                max-width: 700px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(255, 0, 0, 0.8);
                color: white;
                text-align: center;
                border: 5px solid #ff0000;
            `;
            
            secondDialog.innerHTML = `
                <h2 style="color: #ff0000; margin-top: 0; font-size: 32px;">
                    💀 FINAL WARNING - POINT OF NO RETURN 💀
                </h2>
                <p style="margin: 25px 0; font-size: 20px; color: #ff6666;">
                    <strong>Are you ABSOLUTELY CERTAIN?</strong>
                </p>
                <p style="margin: 20px 0; font-size: 18px; color: #ffcccc;">
                    This is your LAST CHANCE to abort!
                </p>
                <p style="margin: 30px 0; font-size: 18px; color: #ff9999;">
                    Type exactly: <strong style="color: #ff0000; font-size: 22px;">DESTROY-ALL-DATA</strong>
                </p>
                <input type="text" id="nuclear-confirm-input" placeholder="Type the confirmation text here..." style="
                    width: 100%;
                    padding: 20px;
                    font-size: 20px;
                    border: 3px solid #ff0000;
                    border-radius: 6px;
                    margin: 20px 0;
                    text-align: center;
                    background: #ffeeee;
                    color: #333;
                ">
                <div style="margin-top: 40px;">
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" style="
                        background: #28a745; 
                        color: white; 
                        border: none; 
                        padding: 20px 40px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        margin-right: 30px;
                        font-weight: bold;
                        font-size: 20px;
                    ">
                        ✅ STOP - KEEP ALL DATA
                    </button>
                    <button onclick="executeNuclearPurge()" style="
                        background: #000000; 
                        color: #ff0000; 
                        border: 3px solid #ff0000; 
                        padding: 20px 40px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 20px;
                    ">
                        ☢️ EXECUTE NUCLEAR PURGE
                    </button>
                </div>
            `;
            
            secondModal.appendChild(secondDialog);
            document.body.appendChild(secondModal);
            
            // Focus on input
            document.getElementById('nuclear-confirm-input').focus();
        }
        
        async function executeNuclearPurge() {
            const input = document.getElementById('nuclear-confirm-input');
            if (input.value !== 'DESTROY-ALL-DATA') {
                alert('❌ Confirmation text does not match. Type exactly: "DESTROY-ALL-DATA"');
                input.focus();
                return;
            }
            
            // Remove confirmation modal
            document.querySelector('div[style*="position: fixed"]').remove();
            
            // Execute the nuclear purge
            try {
                // Show critical loading state
                const loadingModal = document.createElement('div');
                loadingModal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.95);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 30000;
                `;
                
                const loadingContent = document.createElement('div');
                loadingContent.style.cssText = `
                    text-align: center;
                    color: white;
                `;
                
                loadingContent.innerHTML = `
                    <h2 style="color: #ff0000; font-size: 36px;">☢️ NUCLEAR PURGE IN PROGRESS ☢️</h2>
                    <p style="font-size: 24px; margin: 20px 0;">DESTROYING ALL DATA...</p>
                    <p style="font-size: 18px; color: #ff9999;">Please wait. This cannot be cancelled.</p>
                `;
                
                loadingModal.appendChild(loadingContent);
                document.body.appendChild(loadingModal);
                
                const response = await fetch('/api/v1/dashboard/purge-everything?confirm=DESTROY-ALL-DATA', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status}`);
                }
                
                const result = await response.json();
                
                // Remove loading modal
                document.body.removeChild(loadingModal);
                
                // Show completion message
                const completeModal = document.createElement('div');
                completeModal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.9);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 30000;
                `;
                
                const completeContent = document.createElement('div');
                completeContent.style.cssText = `
                    background: white;
                    padding: 50px;
                    border-radius: 12px;
                    max-width: 700px;
                    width: 90%;
                    text-align: center;
                    color: #333;
                `;
                
                completeContent.innerHTML = `
                    <h2 style="color: #dc3545; margin-top: 0; font-size: 32px;">
                        ☢️ NUCLEAR PURGE COMPLETED
                    </h2>
                    <p style="font-size: 20px; margin: 20px 0;">
                        <strong>ALL DATA HAS BEEN DESTROYED</strong>
                    </p>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Deletion Summary:</h3>
                        <ul style="text-align: left; list-style: none; padding: 0;">
                            <li>🔍 Analyses: <strong>${result.purged.analyses}</strong></li>
                            <li>📦 Components: <strong>${result.purged.components}</strong></li>
                            <li>📋 SBOMs: <strong>${result.purged.sboms}</strong></li>
                            <li>🚨 Vulnerabilities: <strong>${result.purged.vulnerabilities}</strong></li>
                            <li>🔬 Vulnerability Scans: <strong>${result.purged.vulnerability_scans}</strong></li>
                            <li>📜 Licenses: <strong>${result.purged.licenses}</strong></li>
                            <li>🤖 Agents: <strong>${result.purged.agents}</strong></li>
                            <li>📊 Telemetry Data: <strong>${result.purged.telemetry_data}</strong></li>
                            <li>🏗️ Builds: <strong>${result.purged.builds}</strong></li>
                            <li>📁 Files Cleaned: <strong>${result.files_cleaned}</strong></li>
                        </ul>
                    </div>
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="color: #856404; margin-top: 0;">⚠️ Important: Docker Volume Persistence</h4>
                        <p style="color: #856404; margin: 0; font-size: 14px;">
                            <strong>Database tables have been purged</strong>, but Docker volumes may still contain data. 
                            If you rebuild containers and see old data, run:
                        </p>
                        <div style="background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 4px; margin: 10px 0; font-family: monospace; font-size: 14px;">
                            docker compose down -v && docker compose up -d
                        </div>
                        <p style="color: #856404; margin: 0; font-size: 12px;">
                            This will remove ALL Docker volumes including: postgres_data, telemetry_data, logs
                        </p>
                    </div>
                    <p style="font-size: 16px; margin: 20px 0;">
                        The database has been completely wiped. The system will now restart with a clean state.
                    </p>
                    <button onclick="location.reload()" style="
                        background: #dc3545;
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 18px;
                        margin-top: 20px;
                    ">
                        🔄 Restart Dashboard
                    </button>
                `;
                
                completeModal.appendChild(completeContent);
                document.body.appendChild(completeModal);
                
                // Auto-refresh after 10 seconds
                setTimeout(() => {
                    location.reload();
                }, 10000);
                
            } catch (error) {
                alert(`❌ NUCLEAR PURGE FAILED: ${error.message}`);
                location.reload();
            }
        }
        
        async function refreshDashboard() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('dashboard').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            
            try {
                const [dashboardData, trendsData] = await Promise.all([
                    fetchDashboardData(),
                    fetchTrendsData()
                ]);
                
                updateDashboard(dashboardData);
                updateTrendsChart(trendsData);
                
                // Load SBOMs separately with pagination
                await loadSBOMs();
                
                // Load Analyses separately with pagination
                const analysesData = await loadAnalyses('', '', '', 0, 50);
                updateAnalysesList(analysesData, false);
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard').style.display = 'grid';
                
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                showError(error.message);
            }
        }
        
        // Initial load
        refreshDashboard();
        
        // Auto-refresh every 30 seconds
        setInterval(refreshDashboard, 30000);
    </script>
    
    </div> <!-- End container -->
</body>
</html>
        '''