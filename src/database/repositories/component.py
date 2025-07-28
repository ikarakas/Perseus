# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Repository for Component entity operations
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import func, and_, or_, distinct
from sqlalchemy.orm import Session, joinedload

from .base import BaseRepository
from ..models import Component, ComponentType, Vulnerability, License


class ComponentRepository(BaseRepository[Component]):
    """Repository for Component operations"""
    
    def __init__(self, session: Session):
        super().__init__(Component, session)
    
    def get_by_purl(self, purl: str) -> List[Component]:
        """Get components by Package URL"""
        return self.session.query(Component).filter(
            Component.purl == purl
        ).all()
    
    def get_by_name_version(self, name: str, version: str = None) -> List[Component]:
        """Get components by name and optionally version"""
        query = self.session.query(Component).filter(
            Component.name == name
        )
        
        if version:
            query = query.filter(Component.version == version)
            
        return query.all()
    
    def get_with_vulnerabilities(self, component_id: UUID) -> Optional[Component]:
        """Get component with vulnerabilities eagerly loaded"""
        return self.session.query(Component).options(
            joinedload(Component.vulnerabilities)
        ).filter(
            Component.id == component_id
        ).first()
    
    def get_by_analysis_and_name(self, analysis_id: UUID, component_name: str) -> Optional[Component]:
        """Get component by analysis ID and component name"""
        return self.session.query(Component).filter(
            and_(
                Component.analysis_id == analysis_id,
                Component.name == component_name
            )
        ).first()
    
    def search_components(self, search_term: str, limit: int = 50) -> List[Component]:
        """Search components by name or description"""
        search_pattern = f"%{search_term}%"
        return self.session.query(Component).filter(
            or_(
                Component.name.ilike(search_pattern),
                Component.description.ilike(search_pattern),
                Component.purl.ilike(search_pattern)
            )
        ).limit(limit).all()
    
    def search_by_analysis_id(self, analysis_id_pattern: str, text_search: str = "", limit: int = 50) -> List[Component]:
        """Search components by analysis ID pattern with optional text search"""
        from ..models import Analysis
        
        # Join Component with Analysis using the defined relationship
        query = self.session.query(Component).join(Component.analysis)
        
        # Filter by analysis ID pattern (supports partial matching)
        analysis_pattern = f"%{analysis_id_pattern}%"
        query = query.filter(Analysis.analysis_id.ilike(analysis_pattern))
        
        # Add text search if provided
        if text_search:
            text_pattern = f"%{text_search}%"
            query = query.filter(
                or_(
                    Component.name.ilike(text_pattern),
                    Component.description.ilike(text_pattern),
                    Component.purl.ilike(text_pattern)
                )
            )
        
        return query.limit(limit).all()
    
    def get_vulnerable_components(self, min_severity: str = None, analysis_id: str = None) -> List[Component]:
        """Get components with vulnerabilities"""
        query = self.session.query(Component).filter(
            Component.vulnerability_count > 0
        )
        
        # Filter by analysis ID if provided
        if analysis_id:
            from ..models import Analysis
            query = query.join(Component.analysis).filter(
                Analysis.analysis_id.ilike(f"%{analysis_id}%")
            )
        
        if min_severity == "critical":
            query = query.filter(Component.critical_vulnerabilities > 0)
        elif min_severity == "high":
            query = query.filter(
                or_(
                    Component.critical_vulnerabilities > 0,
                    Component.high_vulnerabilities > 0
                )
            )
            
        return query.all()
    
    def get_unique_components(self) -> List[Dict[str, Any]]:
        """Get unique components across all analyses"""
        results = self.session.query(
            Component.name,
            Component.version,
            Component.type,
            func.count(distinct(Component.analysis_id)).label('usage_count'),
            func.max(Component.vulnerability_count).label('max_vulnerabilities')
        ).group_by(
            Component.name,
            Component.version,
            Component.type
        ).all()
        
        return [
            {
                'name': r.name,
                'version': r.version,
                'type': r.type.value if r.type else None,
                'usage_count': r.usage_count,
                'max_vulnerabilities': r.max_vulnerabilities
            }
            for r in results
        ]
    
    def get_components_by_license(self, license_spdx_id: str) -> List[Component]:
        """Get components using a specific license"""
        return self.session.query(Component).join(
            Component.licenses
        ).filter(
            License.spdx_id == license_spdx_id
        ).all()
    
    def get_component_statistics(self) -> Dict[str, Any]:
        """Get component statistics"""
        total_components = self.session.query(func.count(Component.id)).scalar()
        
        unique_components = self.session.query(
            func.count(distinct(func.concat(Component.name, ':', Component.version)))
        ).scalar()
        
        vulnerable_components = self.session.query(
            func.count(Component.id)
        ).filter(
            Component.vulnerability_count > 0
        ).scalar()
        
        type_distribution = dict(
            self.session.query(
                Component.type, func.count(Component.id)
            ).group_by(Component.type).all()
        )
        
        return {
            'total_components': total_components,
            'unique_components': unique_components,
            'vulnerable_components': vulnerable_components,
            'vulnerability_rate': (
                (vulnerable_components / total_components * 100)
                if total_components > 0 else 0
            ),
            'type_distribution': {
                k.value if k else 'unknown': v 
                for k, v in type_distribution.items()
            }
        }
    
    def bulk_create_or_update(self, components_data: List[Dict[str, Any]], 
                             analysis_id: UUID) -> List[Component]:
        """Bulk create or update components for an analysis"""
        created_components = []
        
        for comp_data in components_data:
            # Check if component already exists for this analysis
            existing = self.session.query(Component).filter(
                and_(
                    Component.analysis_id == analysis_id,
                    Component.name == comp_data['name'],
                    Component.version == comp_data['version'],
                    Component.type == comp_data.get('type', ComponentType.LIBRARY)
                )
            ).first()
            
            if existing:
                # Update existing component
                for key, value in comp_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                created_components.append(existing)
            else:
                # Create new component
                comp_data['analysis_id'] = analysis_id
                component = Component(**comp_data)
                self.session.add(component)
                created_components.append(component)
        
        self.session.flush()
        return created_components
    
    def get_top_vulnerable_components(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top vulnerable components across all analyses"""
        results = self.session.query(
            Component.name,
            Component.version,
            func.max(Component.vulnerability_count).label('vulnerabilities'),
            func.max(Component.critical_vulnerabilities).label('critical'),
            func.max(Component.high_vulnerabilities).label('high'),
            func.count(distinct(Component.analysis_id)).label('affected_analyses')
        ).filter(
            Component.vulnerability_count > 0
        ).group_by(
            Component.name,
            Component.version
        ).order_by(
            func.max(Component.critical_vulnerabilities).desc(),
            func.max(Component.vulnerability_count).desc()
        ).limit(limit).all()
        
        return [
            {
                'name': r.name,
                'version': r.version,
                'vulnerabilities': r.vulnerabilities,
                'critical': r.critical,
                'high': r.high,
                'affected_analyses': r.affected_analyses
            }
            for r in results
        ]