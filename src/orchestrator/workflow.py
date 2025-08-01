# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Workflow engine for orchestrating SBOM analysis pipeline
"""

import asyncio
import logging
import json
import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
# Workflow orchestration (analyzers now use Syft instead of Docker containers)

from sqlalchemy.orm import Session

from ..analyzers.factory import AnalyzerFactory
from ..sbom.generator import SBOMGenerator
from ..common.storage import ResultStorage
from ..api.models import AnalysisRequest, SBOMRequest, AnalysisResult
from ..monitoring.metrics import MetricsCollector
from ..vulnerability.scanner import VulnerabilityScanner
from ..database import test_connection
from ..database.connection import get_db_for_task
from ..database.repositories import (
    AnalysisRepository, ComponentRepository, SBOMRepository,
    VulnerabilityRepository, VulnerabilityScanRepository
)
from ..database.models import AnalysisStatus, ComponentType

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """Orchestrates the SBOM generation workflow"""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        # Syft-based analysis - no Docker client needed for analyzers
        self.analyzer_factory = AnalyzerFactory()
        self.sbom_generator = SBOMGenerator()
        self.storage = ResultStorage()  # Keep for backward compatibility
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.metrics_collector = metrics_collector
        self.vulnerability_scanner = VulnerabilityScanner()
        
        # Database integration
        self.use_database = test_connection()
        if self.use_database:
            logger.info("Database connection available - using database storage")
        else:
            logger.warning("Database connection not available - using file-based storage")
    
    def _create_analysis_record(self, analysis_id: str, analysis_type: str, request: AnalysisRequest, db: Session) -> Any:
        """Create analysis record in database"""
        try:
            analysis_repo = AnalysisRepository(db)
            
            analysis_data = {
                'analysis_id': analysis_id,
                'status': AnalysisStatus.IN_PROGRESS,
                'analysis_type': analysis_type,
                'language': getattr(request, 'language', None),
                'location': request.location,
                'started_at': datetime.utcnow(),
                'analysis_metadata': {
                    'request_data': request.dict(),
                    'workflow_version': '1.8.0'
                }
            }
            
            return analysis_repo.create(**analysis_data)
        except Exception as e:
            logger.error(f"Failed to create analysis record: {e}")
            return None
    
    def _update_analysis_completion(self, analysis_id: str, analysis_result: AnalysisResult, db: Session):
        """Update analysis record with completion data using atomic count updates"""
        try:
            analysis_repo = AnalysisRepository(db)
            analysis = analysis_repo.get_by_analysis_id(analysis_id)
            
            if analysis:
                # Calculate counts from actual database state
                from sqlalchemy import func
                from ..database.models import Component
                
                # Get component count from database
                component_count = db.query(func.count(Component.id)).filter(
                    Component.analysis_id == analysis.id
                ).scalar()
                
                # Get vulnerability counts from components
                vuln_counts = db.query(
                    func.sum(Component.vulnerability_count).label('total'),
                    func.sum(Component.critical_vulnerabilities).label('critical'),
                    func.sum(Component.high_vulnerabilities).label('high')
                ).filter(
                    Component.analysis_id == analysis.id
                ).first()
                
                total_vulnerabilities = int(vuln_counts.total or 0)
                critical_vulnerabilities = int(vuln_counts.critical or 0)
                high_vulnerabilities = int(vuln_counts.high or 0)
                
                completion_data = {
                    'status': AnalysisStatus.COMPLETED,
                    'completed_at': datetime.utcnow(),
                    'component_count': component_count,
                    'vulnerability_count': total_vulnerabilities,
                    'critical_vulnerability_count': critical_vulnerabilities,
                    'high_vulnerability_count': high_vulnerabilities,
                    'duration_seconds': (datetime.utcnow() - analysis.started_at).total_seconds() if analysis.started_at else None
                }
                
                analysis_repo.update(analysis.id, **completion_data)
                
                # Log count validation
                logger.info(f"Analysis {analysis_id} completed with {component_count} components, {total_vulnerabilities} vulnerabilities")
                
                return analysis
        except Exception as e:
            logger.error(f"Failed to update analysis completion: {e}")
            db.rollback()
        return None
    
    def _store_components_in_db(self, analysis_id: str, components: List, db: Session):
        """Store components in database"""
        try:
            component_repo = ComponentRepository(db)
            analysis_repo = AnalysisRepository(db)
            analysis = analysis_repo.get_by_analysis_id(analysis_id)
            
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found in database")
                return
            
            # Prepare component data for bulk upsert and deduplicate with vulnerability merging
            components_data = []
            seen_components = {}  # Changed to dict to store component data for merging
            
            for component_data in components:
                component_dict = component_data.dict() if hasattr(component_data, 'dict') else component_data
                
                # Map component type
                component_type = ComponentType.LIBRARY  # Default
                if component_dict.get('type'):
                    try:
                        component_type = ComponentType(component_dict['type'])
                    except ValueError:
                        pass
                
                # Create a unique key for deduplication
                name = component_dict.get('name', '')
                version = component_dict.get('version', '')
                unique_key = (name, version, component_type)
                
                db_component_data = {
                    'name': name,
                    'version': version,
                    'type': component_type,
                    'purl': component_dict.get('purl'),
                    'description': component_dict.get('description'),
                    'vulnerability_count': component_dict.get('vulnerability_count', 0),
                    'critical_vulnerabilities': component_dict.get('critical_vulnerabilities', 0),
                    'high_vulnerabilities': component_dict.get('high_vulnerabilities', 0),
                    'component_metadata': component_dict.get('metadata', {}),
                    'syft_metadata': component_dict.get('syft_metadata', {})
                }
                
                # Merge vulnerability data if we've seen this component before
                if unique_key in seen_components:
                    existing = seen_components[unique_key]
                    # Take maximum vulnerability counts to avoid double-counting same vulnerabilities
                    existing['vulnerability_count'] = max(
                        existing['vulnerability_count'], 
                        db_component_data['vulnerability_count']
                    )
                    existing['critical_vulnerabilities'] = max(
                        existing['critical_vulnerabilities'], 
                        db_component_data['critical_vulnerabilities']
                    )
                    existing['high_vulnerabilities'] = max(
                        existing['high_vulnerabilities'], 
                        db_component_data['high_vulnerabilities']
                    )
                    # Update metadata if new component has more data
                    if db_component_data['component_metadata']:
                        existing['component_metadata'].update(db_component_data['component_metadata'])
                    if db_component_data['syft_metadata']:
                        existing['syft_metadata'].update(db_component_data['syft_metadata'])
                else:
                    seen_components[unique_key] = db_component_data
            
            # Convert merged components to list
            components_data = list(seen_components.values())
            
            logger.info(f"Storing {len(components_data)} unique components (merged from {len(components)} total components)")
            
            # Use bulk create or update to handle duplicates
            component_repo.bulk_create_or_update(components_data, analysis.id)
                
        except Exception as e:
            logger.error(f"Failed to store components in database: {e}")
        
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
            logger.info(f"Source analysis options: {request.options}")
            analyzer = self.analyzer_factory.get_source_analyzer(request.language)
            
            # Run analysis
            results = await analyzer.analyze(request.location, request.options)
            
            # Set the analysis ID in the results
            results.analysis_id = analysis_id
            
            # Store results in database if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        # Create analysis record
                        self._create_analysis_record(analysis_id, "source", request, db_session)
                        
                        # Run vulnerability scanning if enabled
                        if request.options and request.options.include_vulnerabilities:
                            await self._add_vulnerability_data(results, db_session)
                        
                        # Store components
                        if results.components:
                            self._store_components_in_db(analysis_id, results.components, db_session)
                        
                        # Link vulnerabilities to components if vulnerability scanning was performed
                        if hasattr(results, 'vulnerability_summary') and results.vulnerability_summary:
                            linked_count = self._link_vulnerabilities_to_components(analysis_id, db_session)
                            # Update metadata with correct vulnerability count
                            if linked_count is not None and hasattr(results, 'metadata'):
                                results.metadata.update({
                                    'total_vulnerabilities': linked_count,
                                    'raw_scan_vulnerabilities': results.metadata.get('total_vulnerabilities', 0)
                                })
                        
                        # Update analysis completion
                        self._update_analysis_completion(analysis_id, results, db_session)
                        
                        # Commit all changes
                        db_session.commit()
                        logger.info(f"Database transaction committed for analysis {analysis_id}")
                        
                    except Exception as db_e:
                        db_session.rollback()
                        logger.error(f"Database operation failed, rolled back: {db_e}")
                        # Continue even if database fails
            
            # Store results in file system (for backward compatibility)
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
            
            # Update database with failure if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        analysis_repo = AnalysisRepository(db_session)
                        analysis = analysis_repo.get_by_analysis_id(analysis_id)
                        if analysis:
                            analysis_repo.update(analysis.id, status=AnalysisStatus.FAILED, errors=[str(e)])
                            db_session.commit()
                    except Exception as db_e:
                        logger.error(f"Failed to update database with error: {db_e}")
            
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
            
            # Store results in database if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        # Create analysis record
                        self._create_analysis_record(analysis_id, "binary", request, db_session)
                        
                        # Run vulnerability scanning if enabled
                        if request.options and request.options.include_vulnerabilities:
                            await self._add_vulnerability_data(results, db_session)
                        
                        # Store components
                        if results.components:
                            self._store_components_in_db(analysis_id, results.components, db_session)
                        
                        # Link vulnerabilities to components if vulnerability scanning was performed
                        if hasattr(results, 'vulnerability_summary') and results.vulnerability_summary:
                            linked_count = self._link_vulnerabilities_to_components(analysis_id, db_session)
                            # Update metadata with correct vulnerability count
                            if linked_count is not None and hasattr(results, 'metadata'):
                                results.metadata.update({
                                    'total_vulnerabilities': linked_count,
                                    'raw_scan_vulnerabilities': results.metadata.get('total_vulnerabilities', 0)
                                })
                        
                        # Update analysis completion
                        self._update_analysis_completion(analysis_id, results, db_session)
                        
                        # Commit all changes
                        db_session.commit()
                        logger.info(f"Database transaction committed for analysis {analysis_id}")
                        
                    except Exception as db_e:
                        db_session.rollback()
                        logger.error(f"Database operation failed, rolled back: {db_e}")
                        # Continue even if database fails
            
            # Store results in file system (for backward compatibility)
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
            
            # Update database with failure if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        analysis_repo = AnalysisRepository(db_session)
                        analysis = analysis_repo.get_by_analysis_id(analysis_id)
                        if analysis:
                            analysis_repo.update(analysis.id, status=AnalysisStatus.FAILED, errors=[str(e)])
                            db_session.commit()
                    except Exception as db_e:
                        logger.error(f"Failed to update database with error: {db_e}")
            
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
            
            # Collect analysis results and metadata
            analysis_results = []
            analysis_metadata = None
            
            # Get analysis metadata from database if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    analysis_repo = AnalysisRepository(db_session)
                    
                    for analysis_id in request.analysis_ids:
                        result = self.storage.get_analysis_result(analysis_id)
                        if result:
                            analysis_results.append(result)
                            
                            # Get analysis metadata from database (use first analysis)
                            if analysis_metadata is None:
                                db_analysis = analysis_repo.get_by_analysis_id(analysis_id)
                                if db_analysis:
                                    analysis_metadata = {
                                        "analysis_id": db_analysis.analysis_id,
                                        "analysis_type": db_analysis.analysis_type,
                                        "location": db_analysis.location,
                                        "language": db_analysis.language,
                                        "source_metadata": {
                                            "started_at": db_analysis.started_at.isoformat() if db_analysis.started_at else None,
                                            "completed_at": db_analysis.completed_at.isoformat() if db_analysis.completed_at else None,
                                            "duration_seconds": db_analysis.duration_seconds,
                                            "component_count": db_analysis.component_count,
                                            "vulnerability_count": db_analysis.vulnerability_count
                                        }
                                    }
                                    # Add any additional metadata from the analysis_metadata field
                                    if db_analysis.analysis_metadata:
                                        analysis_metadata["source_metadata"].update(db_analysis.analysis_metadata)
            else:
                # No database, just collect from file storage
                for analysis_id in request.analysis_ids:
                    result = self.storage.get_analysis_result(analysis_id)
                    if result:
                        analysis_results.append(result)
            
            if not analysis_results:
                raise ValueError("No valid analysis results found")
            
            # Generate SBOM with analysis metadata
            sbom_data = await self.sbom_generator.generate(
                analysis_results,
                request.format,
                request.include_licenses,
                request.include_vulnerabilities,
                analysis_metadata
            )
            
            # Store SBOM in file system (for backward compatibility)
            self.storage.store_sbom(sbom_id, sbom_data)
            
            # Store SBOM in database if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        sbom_repo = SBOMRepository(db_session)
                        analysis_repo = AnalysisRepository(db_session)
                        
                        # Get the first analysis for SBOM association (could be enhanced to support multiple)
                        primary_analysis = analysis_repo.get_by_analysis_id(request.analysis_ids[0])
                        
                        if primary_analysis:
                            # Calculate component count
                            total_components = sum(len(result.components) for result in analysis_results)
                            
                            sbom_db_data = {
                                'sbom_id': sbom_id,
                                'format': request.format,
                                'spec_version': sbom_data.get('specVersion') or sbom_data.get('spec_version', '2.3'),
                                'content': sbom_data,
                                'name': sbom_data.get('name', f"SBOM-{sbom_id}"),
                                'namespace': sbom_data.get('documentNamespace') or sbom_data.get('metadata', {}).get('component', {}).get('bom-ref', ''),
                                'created_by': 'Perseus Platform v1.8.0',
                                'component_count': total_components,
                                'file_path': f"data/sboms/{sbom_id}.json",
                                'analysis_id': primary_analysis.id
                            }
                            
                            sbom_repo.create(**sbom_db_data)
                            db_session.commit()
                            logger.info(f"SBOM {sbom_id} stored in database")
                        else:
                            logger.warning(f"Analysis {request.analysis_ids[0]} not found in database - SBOM stored only in file system")
                            
                    except Exception as db_e:
                        db_session.rollback()
                        logger.error(f"Failed to store SBOM in database: {db_e}")
                        # Continue without database storage
            
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
            
            # Store results in database if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        # Create analysis record
                        self._create_analysis_record(analysis_id, "os", request, db_session)
                        
                        # Run vulnerability scanning if enabled
                        if request.options and request.options.include_vulnerabilities:
                            await self._add_vulnerability_data(results, db_session)
                        
                        # Store components
                        if results.components:
                            self._store_components_in_db(analysis_id, results.components, db_session)
                        
                        # Link vulnerabilities to components if vulnerability scanning was performed
                        if hasattr(results, 'vulnerability_summary') and results.vulnerability_summary:
                            linked_count = self._link_vulnerabilities_to_components(analysis_id, db_session)
                            # Update metadata with correct vulnerability count
                            if linked_count is not None and hasattr(results, 'metadata'):
                                results.metadata.update({
                                    'total_vulnerabilities': linked_count,
                                    'raw_scan_vulnerabilities': results.metadata.get('total_vulnerabilities', 0)
                                })
                        
                        # Update analysis completion
                        self._update_analysis_completion(analysis_id, results, db_session)
                        
                        # Commit all changes
                        db_session.commit()
                        logger.info(f"Database transaction committed for analysis {analysis_id}")
                        
                    except Exception as db_e:
                        db_session.rollback()
                        logger.error(f"Database operation failed, rolled back: {db_e}")
                        # Continue even if database fails
            
            # Store results in file system (for backward compatibility)
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
            
            # Update database with failure if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        analysis_repo = AnalysisRepository(db_session)
                        analysis = analysis_repo.get_by_analysis_id(analysis_id)
                        if analysis:
                            analysis_repo.update(analysis.id, status=AnalysisStatus.FAILED, errors=[str(e)])
                            db_session.commit()
                    except Exception as db_e:
                        logger.error(f"Failed to update database with error: {db_e}")
            
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
            
            # Store results in database if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        # Create analysis record
                        self._create_analysis_record(analysis_id, "docker", request, db_session)
                        
                        # Run vulnerability scanning if enabled
                        if request.options and request.options.include_vulnerabilities:
                            await self._add_vulnerability_data(results, db_session)
                        
                        # Store components
                        if results.components:
                            self._store_components_in_db(analysis_id, results.components, db_session)
                        
                        # Link vulnerabilities to components if vulnerability scanning was performed
                        if hasattr(results, 'vulnerability_summary') and results.vulnerability_summary:
                            linked_count = self._link_vulnerabilities_to_components(analysis_id, db_session)
                            # Update metadata with correct vulnerability count
                            if linked_count is not None and hasattr(results, 'metadata'):
                                results.metadata.update({
                                    'total_vulnerabilities': linked_count,
                                    'raw_scan_vulnerabilities': results.metadata.get('total_vulnerabilities', 0)
                                })
                        
                        # Update analysis completion
                        self._update_analysis_completion(analysis_id, results, db_session)
                        
                        # Commit all changes
                        db_session.commit()
                        logger.info(f"Database transaction committed for analysis {analysis_id}")
                        
                    except Exception as db_e:
                        db_session.rollback()
                        logger.error(f"Database operation failed, rolled back: {db_e}")
                        # Continue even if database fails
            
            # Store results in file system (for backward compatibility)
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
            
            # Update database with failure if available
            if self.use_database:
                with get_db_for_task() as db_session:
                    try:
                        analysis_repo = AnalysisRepository(db_session)
                        analysis = analysis_repo.get_by_analysis_id(analysis_id)
                        if analysis:
                            analysis_repo.update(analysis.id, status=AnalysisStatus.FAILED, errors=[str(e)])
                            db_session.commit()
                    except Exception as db_e:
                        logger.error(f"Failed to update database with error: {db_e}")
            
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
    
    async def _add_vulnerability_data(self, analysis_result: AnalysisResult, db_session: Optional[Session] = None) -> None:
        """Add vulnerability data to analysis results"""
        scan_start_time = datetime.utcnow()
        scan_id = str(uuid.uuid4())
        
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
                    component.high_vulnerabilities = sum(
                        1 for v in comp_vuln.vulnerabilities if v.severity == "high"
                    )
                else:
                    component.vulnerability_count = 0
                    component.critical_vulnerabilities = 0
                    component.high_vulnerabilities = 0
            
            # Update analysis metadata
            analysis_result.metadata.update({
                'vulnerability_scan_performed': True,
                'vulnerability_scan_date': datetime.utcnow().isoformat(),
                'total_vulnerabilities': vuln_data['summary']['total_vulnerabilities'],
                'vulnerable_components': vuln_data['summary']['vulnerable_components']
            })
            
            # Store vulnerability scan in database if available
            if self.use_database and db_session:
                try:
                    logger.info(f"Attempting to store vulnerability scan in database for {scan_id}")
                    self._store_vulnerability_scan_in_db(
                        scan_id, analysis_result.analysis_id, vuln_data, 
                        scan_start_time, datetime.utcnow(), db_session
                    )
                    logger.info(f"Successfully stored vulnerability scan in database for {scan_id}")
                except Exception as db_e:
                    logger.error(f"Failed to store vulnerability scan in database: {db_e}")
            
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
            
            # Store failed scan in database if available
            if self.use_database and db_session:
                try:
                    logger.info(f"Attempting to store failed vulnerability scan in database for {scan_id}")
                    self._store_vulnerability_scan_in_db(
                        scan_id, analysis_result.analysis_id, {'summary': {'total_vulnerabilities': 0}, 'scan_results': []},
                        scan_start_time, datetime.utcnow(), db_session, error=str(e)
                    )
                    logger.info(f"Successfully stored failed vulnerability scan in database for {scan_id}")
                except Exception as db_e:
                    logger.error(f"Failed to store failed vulnerability scan in database: {db_e}")
    
    def _serialize_vulnerability_data(self, vuln_data: Dict) -> Dict:
        """Convert vulnerability data with Pydantic models to JSON-serializable format"""
        import json
        import uuid
        from datetime import datetime
        from decimal import Decimal
        from enum import Enum
        from ..vulnerability.models import ComponentVulnerabilities
        
        def make_serializable(obj):
            """Recursively convert objects to JSON-serializable format"""
            if obj is None:
                return None
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, uuid.UUID):
                return str(obj)
            elif isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, ComponentVulnerabilities):
                return obj.dict()
            elif hasattr(obj, 'dict') and callable(obj.dict):  # Pydantic models
                return make_serializable(obj.dict())
            elif isinstance(obj, dict):
                return {key: make_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, (list, tuple, set)):
                return [make_serializable(item) for item in obj]
            else:
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError):
                    return str(obj)
        
        return make_serializable(vuln_data)
    
    def _store_vulnerability_scan_in_db(self, scan_id: str, analysis_id: str, vuln_data: Dict, 
                                      start_time: datetime, end_time: datetime, db_session: Session, 
                                      error: Optional[str] = None):
        """Store vulnerability scan results in database"""
        try:
            from ..database.models import ScannerType
            
            analysis_repo = AnalysisRepository(db_session)
            scan_repo = VulnerabilityScanRepository(db_session)
            vuln_repo = VulnerabilityRepository(db_session)
            
            analysis = analysis_repo.get_by_analysis_id(analysis_id)
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found for vulnerability scan storage")
                return
            
            # Convert vulnerability data to JSON string and back to ensure serializability
            import json
            from datetime import datetime
            import uuid
            from decimal import Decimal
            from enum import Enum
            
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif isinstance(obj, uuid.UUID):
                        return str(obj)
                    elif isinstance(obj, Decimal):
                        return float(obj)
                    elif isinstance(obj, Enum):
                        return obj.value
                    elif hasattr(obj, 'dict') and callable(obj.dict):
                        return obj.dict()
                    return super().default(obj)
            
            # Force JSON serialization to catch any non-serializable data
            try:
                json_str = json.dumps(vuln_data, cls=DateTimeEncoder)
                serializable_vuln_data = json.loads(json_str)
                logger.info(f"Successfully serialized vulnerability data for scan {scan_id}")
            except Exception as e:
                logger.error(f"Failed to serialize vulnerability data: {e}")
                # Fallback to minimal data
                serializable_vuln_data = {
                    'summary': summary,
                    'scan_results': [],
                    'error': f'Serialization failed: {str(e)}'
                }
            
            # Store vulnerability scan record
            summary = vuln_data.get('summary', {})
            scan_data = {
                'scan_id': scan_id,
                'scanner': ScannerType.OSV,  # Default scanner type
                'scanner_version': '1.0.0',
                'started_at': start_time,
                'completed_at': end_time,
                'duration_seconds': (end_time - start_time).total_seconds(),
                'total_vulnerabilities': summary.get('total_vulnerabilities', 0),
                'critical_count': summary.get('critical_vulnerabilities', 0),
                'high_count': summary.get('high_vulnerabilities', 0),
                'medium_count': summary.get('medium_vulnerabilities', 0),
                'low_count': summary.get('low_vulnerabilities', 0),
                'raw_results': serializable_vuln_data,
                'analysis_id': analysis.id
            }
            
            if error:
                scan_data['raw_results'] = {'error': error}
            
            scan_repo.create(**scan_data)
            
            # Store individual vulnerabilities if scan was successful
            if not error and 'scan_results' in vuln_data:
                for scan_result in vuln_data['scan_results']:
                    for vuln in scan_result.vulnerabilities:
                        # Check if vulnerability already exists
                        existing_vuln = vuln_repo.get_by_vulnerability_id(vuln.id)
                        
                        if not existing_vuln:
                            # Create new vulnerability record
                            from ..database.models import VulnerabilitySeverity
                            
                            severity = VulnerabilitySeverity.UNKNOWN
                            try:
                                if vuln.severity:
                                    severity = VulnerabilitySeverity(vuln.severity.lower())
                            except ValueError:
                                pass
                            
                            vuln_data_dict = {
                                'vulnerability_id': vuln.id,
                                'source': 'OSV',
                                'title': vuln.title,
                                'description': vuln.description,
                                'severity': severity,
                                'cvss_score': vuln.cvss.base_score if vuln.cvss else None,
                                'cvss_vector': vuln.cvss.vector_string if vuln.cvss else None,
                                'published_date': vuln.published,
                                'modified_date': vuln.updated,
                                'references': vuln.references or [],
                                'cwe_ids': vuln.cwe_ids or [],
                                'affected_versions': vuln.affected_versions or [],
                                'fixed_versions': vuln.fixed_versions or [],
                                'vulnerability_metadata': {
                                    'aliases': vuln.aliases or [],
                                    'database_specific': getattr(vuln, 'database_specific', {}),
                                    'ecosystem_specific': getattr(vuln, 'ecosystem_specific', {})
                                }
                            }
                            
                            vuln_repo.create(**vuln_data_dict)
            
            logger.info(f"Vulnerability scan {scan_id} stored in database")
            
        except Exception as e:
            logger.error(f"Failed to store vulnerability scan in database: {e}")
            raise
    
    def _link_vulnerabilities_to_components(self, analysis_id: str, db_session: Session) -> Optional[int]:
        """Link stored vulnerabilities to components after both are in database with improved error handling"""
        try:
            analysis_repo = AnalysisRepository(db_session)
            comp_repo = ComponentRepository(db_session)
            vuln_repo = VulnerabilityRepository(db_session)
            
            analysis = analysis_repo.get_by_analysis_id(analysis_id)
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found for vulnerability linking")
                return None
            
            # Get the last vulnerability scan for this analysis
            from ..database.repositories import VulnerabilityScanRepository
            scan_repo = VulnerabilityScanRepository(db_session)
            scans = scan_repo.get_by_analysis_id(analysis.id)
            
            if not scans:
                logger.warning(f"No vulnerability scans found for analysis {analysis_id}")
                return 0
            
            latest_scan = scans[0]  # get_by_analysis_id returns results ordered by started_at desc
            scan_results = latest_scan.raw_results.get('scan_results', [])
            
            logger.info(f"Linking vulnerabilities from {len(scan_results)} scan results to components")
            
            total_vulns_in_scan = 0
            total_linked = 0
            components_with_vulns = 0
            linking_errors = []
            
            # Process scan results without nested transaction
            for scan_result in scan_results:
                component_name = scan_result.get('component_name')
                vulnerabilities = scan_result.get('vulnerabilities', [])
                
                if vulnerabilities:
                    components_with_vulns += 1
                    total_vulns_in_scan += len(vulnerabilities)
                    logger.debug(f"Component {component_name} has {len(vulnerabilities)} vulnerabilities in scan")
                
                # Find the corresponding component in the database
                component = comp_repo.get_by_analysis_and_name(analysis.id, component_name)
                if not component:
                    if vulnerabilities:  # Only warn if component has vulnerabilities
                        error_msg = f"Component {component_name} with {len(vulnerabilities)} vulnerabilities not found in database"
                        logger.warning(error_msg)
                        linking_errors.append(error_msg)
                    continue
                
                # Update component vulnerability counts based on scan results
                component.vulnerability_count = len(vulnerabilities)
                component.critical_vulnerabilities = sum(
                    1 for v in vulnerabilities 
                    if isinstance(v, dict) and v.get('severity', '').lower() == 'critical'
                    or hasattr(v, 'severity') and v.severity and v.severity.lower() == 'critical'
                )
                component.high_vulnerabilities = sum(
                    1 for v in vulnerabilities 
                    if isinstance(v, dict) and v.get('severity', '').lower() == 'high'
                    or hasattr(v, 'severity') and v.severity and v.severity.lower() == 'high'
                )
                
                for vuln_data in vulnerabilities:
                    vuln_id = vuln_data.get('id') if isinstance(vuln_data, dict) else getattr(vuln_data, 'id', None)
                    if not vuln_id:
                        error_msg = f"Vulnerability data missing ID: {vuln_data}"
                        logger.warning(error_msg)
                        linking_errors.append(error_msg)
                        continue
                        
                    # Find the vulnerability in the database
                    vulnerability = vuln_repo.get_by_vulnerability_id(vuln_id)
                    if not vulnerability:
                        error_msg = f"Vulnerability {vuln_id} not found in database"
                        logger.warning(error_msg)
                        linking_errors.append(error_msg)
                        continue
                        
                    if vulnerability and component:
                        try:
                            # Add the vulnerability to the component's vulnerabilities relationship
                            if vulnerability not in component.vulnerabilities:
                                component.vulnerabilities.append(vulnerability)
                                total_linked += 1
                                logger.debug(f"Linked vulnerability {vuln_id} to component {component.name}")
                        except Exception as link_error:
                            error_msg = f"Failed to link vulnerability {vuln_id} to component {component.name}: {link_error}"
                            logger.error(error_msg)
                            linking_errors.append(error_msg)
            
            # Update analysis counts after linking
            self._update_analysis_counts_from_components(analysis_id, db_session)
            
            logger.info(f"Vulnerability linking summary: {total_vulns_in_scan} vulnerabilities in scan, {total_linked} successfully linked, {components_with_vulns} components had vulnerabilities")
            
            if linking_errors:
                logger.warning(f"Vulnerability linking completed with {len(linking_errors)} errors for analysis {analysis_id}")
            
            return total_linked
            
        except Exception as e:
            logger.error(f"Failed to link vulnerabilities to components: {e}")
            db_session.rollback()
            return None
    
    def _update_analysis_counts_from_components(self, analysis_id: str, db_session: Session):
        """Update analysis counts based on component aggregation"""
        try:
            analysis_repo = AnalysisRepository(db_session)
            analysis = analysis_repo.get_by_analysis_id(analysis_id)
            
            if not analysis:
                return
            
            # Calculate counts from components
            from sqlalchemy import func
            from ..database.models import Component
            
            vuln_counts = db_session.query(
                func.sum(Component.vulnerability_count).label('total'),
                func.sum(Component.critical_vulnerabilities).label('critical'),
                func.sum(Component.high_vulnerabilities).label('high')
            ).filter(
                Component.analysis_id == analysis.id
            ).first()
            
            # Update analysis with calculated counts
            update_data = {
                'vulnerability_count': int(vuln_counts.total or 0),
                'critical_vulnerability_count': int(vuln_counts.critical or 0),
                'high_vulnerability_count': int(vuln_counts.high or 0)
            }
            
            analysis_repo.update(analysis.id, **update_data)
            logger.debug(f"Updated analysis {analysis_id} counts: {update_data}")
            
        except Exception as e:
            logger.error(f"Failed to update analysis counts from components: {e}")
            raise
    
    def validate_sbom(self, sbom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SBOM format"""
        return self.sbom_generator.validate(sbom_data)