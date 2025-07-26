# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Repository for SBOM entity operations
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from .base import BaseRepository
from ..models import SBOM, Analysis


class SBOMRepository(BaseRepository[SBOM]):
    """Repository for SBOM operations"""
    
    def __init__(self, session: Session):
        super().__init__(SBOM, session)
    
    def get_by_sbom_id(self, sbom_id: str) -> Optional[SBOM]:
        """Get SBOM by sbom_id field"""
        return self.session.query(SBOM).filter(
            SBOM.sbom_id == sbom_id
        ).first()
    
    def get_by_analysis_id(self, analysis_id: UUID) -> List[SBOM]:
        """Get all SBOMs for a specific analysis"""
        return self.session.query(SBOM).filter(
            SBOM.analysis_id == analysis_id
        ).all()
    
    def get_by_format(self, format: str, limit: int = None) -> List[SBOM]:
        """Get SBOMs by format (spdx, cyclonedx, swid)"""
        query = self.session.query(SBOM).filter(
            SBOM.format == format
        ).order_by(SBOM.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_with_analysis(self, sbom_id: str) -> Optional[SBOM]:
        """Get SBOM with analysis information eagerly loaded"""
        return self.session.query(SBOM).options(
            joinedload(SBOM.analysis)
        ).filter(
            SBOM.sbom_id == sbom_id
        ).first()
    
    def get_recent_sboms(self, limit: int = 10) -> List[SBOM]:
        """Get recent SBOMs ordered by creation date"""
        return self.session.query(SBOM).order_by(
            SBOM.created_at.desc()
        ).limit(limit).all()
    
    def get_sbom_statistics(self) -> Dict[str, Any]:
        """Get SBOM generation statistics"""
        total_sboms = self.session.query(func.count(SBOM.id)).scalar()
        
        format_distribution = dict(
            self.session.query(
                SBOM.format, func.count(SBOM.id)
            ).group_by(SBOM.format).all()
        )
        
        # Get analyses with SBOMs vs without
        analyses_with_sboms = self.session.query(
            func.count(func.distinct(SBOM.analysis_id))
        ).scalar()
        
        total_analyses = self.session.query(func.count(Analysis.id)).scalar()
        
        return {
            'total_sboms': total_sboms,
            'format_distribution': format_distribution,
            'analyses_with_sboms': analyses_with_sboms,
            'total_analyses': total_analyses,
            'sbom_coverage': (
                (analyses_with_sboms / total_analyses * 100)
                if total_analyses > 0 else 0
            )
        }
    
    def search_sboms(self, search_term: str, limit: int = 50) -> List[SBOM]:
        """Search SBOMs by name or namespace"""
        search_pattern = f"%{search_term}%"
        return self.session.query(SBOM).filter(
            or_(
                SBOM.name.ilike(search_pattern),
                SBOM.namespace.ilike(search_pattern),
                SBOM.created_by.ilike(search_pattern)
            )
        ).limit(limit).all()