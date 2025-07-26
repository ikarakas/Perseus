# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Repository for Analysis entity operations
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload

from .base import BaseRepository
from ..models import Analysis, AnalysisStatus, Component


class AnalysisRepository(BaseRepository[Analysis]):
    """Repository for Analysis operations"""
    
    def __init__(self, session: Session):
        super().__init__(Analysis, session)
    
    def get_by_analysis_id(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by analysis_id field"""
        return self.session.query(Analysis).filter(
            Analysis.analysis_id == analysis_id
        ).first()
    
    def get_with_components(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis with components eagerly loaded"""
        return self.session.query(Analysis).options(
            joinedload(Analysis.components)
        ).filter(
            Analysis.analysis_id == analysis_id
        ).first()
    
    def get_recent_analyses(self, limit: int = 10) -> List[Analysis]:
        """Get recent analyses ordered by creation date"""
        return self.session.query(Analysis).order_by(
            Analysis.created_at.desc()
        ).limit(limit).all()
    
    def get_by_status(self, status: AnalysisStatus, limit: int = None) -> List[Analysis]:
        """Get analyses by status"""
        query = self.session.query(Analysis).filter(
            Analysis.status == status
        ).order_by(Analysis.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_failed_analyses(self, since: datetime = None) -> List[Analysis]:
        """Get failed analyses, optionally since a specific date"""
        query = self.session.query(Analysis).filter(
            Analysis.status == AnalysisStatus.FAILED
        )
        
        if since:
            query = query.filter(Analysis.created_at >= since)
            
        return query.order_by(Analysis.created_at.desc()).all()
    
    def get_analyses_by_type(self, analysis_type: str, limit: int = None) -> List[Analysis]:
        """Get analyses by type (source, binary, docker, os)"""
        query = self.session.query(Analysis).filter(
            Analysis.analysis_type == analysis_type
        ).order_by(Analysis.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_vulnerability_summary(self) -> Dict[str, Any]:
        """Get summary of vulnerabilities across all analyses"""
        result = self.session.query(
            func.count(Analysis.id).label('total_analyses'),
            func.sum(Analysis.vulnerability_count).label('total_vulnerabilities'),
            func.sum(Analysis.critical_vulnerability_count).label('total_critical'),
            func.sum(Analysis.high_vulnerability_count).label('total_high'),
            func.avg(Analysis.vulnerability_count).label('avg_vulnerabilities_per_analysis')
        ).filter(
            Analysis.status == AnalysisStatus.COMPLETED
        ).first()
        
        return {
            'total_analyses': result.total_analyses or 0,
            'total_vulnerabilities': int(result.total_vulnerabilities or 0),
            'total_critical': int(result.total_critical or 0),
            'total_high': int(result.total_high or 0),
            'avg_vulnerabilities_per_analysis': float(result.avg_vulnerabilities_per_analysis or 0)
        }
    
    def update_status(self, analysis_id: str, status: AnalysisStatus, 
                     errors: List[str] = None) -> Optional[Analysis]:
        """Update analysis status and optionally add errors"""
        analysis = self.get_by_analysis_id(analysis_id)
        if analysis:
            analysis.status = status
            
            if status == AnalysisStatus.IN_PROGRESS:
                analysis.started_at = datetime.utcnow()
            elif status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                analysis.completed_at = datetime.utcnow()
                if analysis.started_at:
                    analysis.duration_seconds = (
                        analysis.completed_at - analysis.started_at
                    ).total_seconds()
            
            if errors:
                if not analysis.errors:
                    analysis.errors = []
                analysis.errors.extend(errors)
            
            self.session.flush()
        
        return analysis
    
    def update_vulnerability_counts(self, analysis_id: str) -> Optional[Analysis]:
        """Update vulnerability counts based on associated components"""
        analysis = self.get_by_analysis_id(analysis_id)
        if analysis:
            # Calculate totals from components
            totals = self.session.query(
                func.sum(Component.vulnerability_count).label('total'),
                func.sum(Component.critical_vulnerabilities).label('critical'),
                func.sum(Component.high_vulnerabilities).label('high')
            ).filter(
                Component.analysis_id == analysis.id
            ).first()
            
            analysis.vulnerability_count = int(totals.total or 0)
            analysis.critical_vulnerability_count = int(totals.critical or 0)
            analysis.high_vulnerability_count = int(totals.high or 0)
            analysis.component_count = len(analysis.components)
            
            self.session.flush()
        
        return analysis
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get analysis statistics for the past N days"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Basic counts
        total_analyses = self.session.query(func.count(Analysis.id)).filter(
            Analysis.created_at >= since
        ).scalar()
        
        # Status breakdown
        status_counts = dict(
            self.session.query(
                Analysis.status, func.count(Analysis.id)
            ).filter(
                Analysis.created_at >= since
            ).group_by(Analysis.status).all()
        )
        
        # Type breakdown
        type_counts = dict(
            self.session.query(
                Analysis.analysis_type, func.count(Analysis.id)
            ).filter(
                Analysis.created_at >= since
            ).group_by(Analysis.analysis_type).all()
        )
        
        # Average duration for completed analyses
        avg_duration = self.session.query(
            func.avg(Analysis.duration_seconds)
        ).filter(
            and_(
                Analysis.created_at >= since,
                Analysis.status == AnalysisStatus.COMPLETED,
                Analysis.duration_seconds.isnot(None)
            )
        ).scalar()
        
        return {
            'period_days': days,
            'total_analyses': total_analyses,
            'status_breakdown': status_counts,
            'type_breakdown': type_counts,
            'average_duration_seconds': float(avg_duration or 0),
            'success_rate': (
                (status_counts.get(AnalysisStatus.COMPLETED, 0) / total_analyses * 100)
                if total_analyses > 0 else 0
            )
        }