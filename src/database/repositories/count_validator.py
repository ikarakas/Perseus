# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Count validation and reconciliation utilities for maintaining data consistency
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from ..models import Analysis, Component, Vulnerability, AnalysisStatus, component_vulnerabilities
from .analysis import AnalysisRepository
from .component import ComponentRepository
from .vulnerability import VulnerabilityRepository

logger = logging.getLogger(__name__)


class CountValidator:
    """Validates and reconciles count inconsistencies in the database"""
    
    def __init__(self, session: Session):
        self.session = session
        self.analysis_repo = AnalysisRepository(session)
        self.component_repo = ComponentRepository(session)
        self.vulnerability_repo = VulnerabilityRepository(session)
    
    def validate_analysis_counts(self, analysis_id: str) -> Dict[str, Any]:
        """Validate that analysis counts match component aggregation"""
        analysis = self.analysis_repo.get_by_analysis_id(analysis_id)
        if not analysis:
            return {"error": f"Analysis {analysis_id} not found"}
        
        # Calculate actual counts from components
        actual_component_count = len(analysis.components)
        actual_vuln_count = sum(c.vulnerability_count or 0 for c in analysis.components)
        actual_critical_count = sum(c.critical_vulnerabilities or 0 for c in analysis.components)
        actual_high_count = sum(c.high_vulnerabilities or 0 for c in analysis.components)
        
        # Get stored counts
        stored_component_count = analysis.component_count or 0
        stored_vuln_count = analysis.vulnerability_count or 0
        stored_critical_count = analysis.critical_vulnerability_count or 0
        stored_high_count = analysis.high_vulnerability_count or 0
        
        # Check for discrepancies
        discrepancies = []
        if actual_component_count != stored_component_count:
            discrepancies.append(f"Component count: stored={stored_component_count}, actual={actual_component_count}")
        
        if actual_vuln_count != stored_vuln_count:
            discrepancies.append(f"Vulnerability count: stored={stored_vuln_count}, actual={actual_vuln_count}")
        
        if actual_critical_count != stored_critical_count:
            discrepancies.append(f"Critical count: stored={stored_critical_count}, actual={actual_critical_count}")
        
        if actual_high_count != stored_high_count:
            discrepancies.append(f"High count: stored={stored_high_count}, actual={actual_high_count}")
        
        return {
            "analysis_id": analysis_id,
            "has_discrepancies": len(discrepancies) > 0,
            "discrepancies": discrepancies,
            "actual_counts": {
                "component_count": actual_component_count,
                "vulnerability_count": actual_vuln_count,
                "critical_vulnerability_count": actual_critical_count,
                "high_vulnerability_count": actual_high_count
            },
            "stored_counts": {
                "component_count": stored_component_count,
                "vulnerability_count": stored_vuln_count,
                "critical_vulnerability_count": stored_critical_count,
                "high_vulnerability_count": stored_high_count
            }
        }
    
    def fix_analysis_counts(self, analysis_id: str) -> Dict[str, Any]:
        """Fix count discrepancies for a specific analysis"""
        validation = self.validate_analysis_counts(analysis_id)
        
        if validation.get("error"):
            return validation
        
        if not validation["has_discrepancies"]:
            return {"message": "No discrepancies found", "analysis_id": analysis_id}
        
        analysis = self.analysis_repo.get_by_analysis_id(analysis_id)
        actual_counts = validation["actual_counts"]
        
        # Update analysis with correct counts
        self.analysis_repo.update(analysis.id, **actual_counts)
        
        logger.info(f"Fixed count discrepancies for analysis {analysis_id}")
        
        return {
            "message": "Counts fixed successfully",
            "analysis_id": analysis_id,
            "fixed_counts": actual_counts
        }
    
    def validate_all_analysis_counts(self) -> Dict[str, Any]:
        """Validate counts for all analyses"""
        analyses = self.session.query(Analysis).filter(
            Analysis.status == AnalysisStatus.COMPLETED
        ).all()
        
        results = []
        total_discrepancies = 0
        
        for analysis in analyses:
            validation = self.validate_analysis_counts(analysis.analysis_id)
            if validation["has_discrepancies"]:
                total_discrepancies += len(validation["discrepancies"])
            results.append(validation)
        
        return {
            "total_analyses": len(analyses),
            "analyses_with_discrepancies": len([r for r in results if r["has_discrepancies"]]),
            "total_discrepancies": total_discrepancies,
            "results": results
        }
    
    def fix_all_analysis_counts(self) -> Dict[str, Any]:
        """Fix count discrepancies for all analyses"""
        validation = self.validate_all_analysis_counts()
        
        fixed_count = 0
        for result in validation["results"]:
            if result["has_discrepancies"]:
                fix_result = self.fix_analysis_counts(result["analysis_id"])
                if "message" in fix_result and "fixed" in fix_result["message"]:
                    fixed_count += 1
        
        return {
            "message": f"Fixed {fixed_count} analyses with count discrepancies",
            "total_analyses": validation["total_analyses"],
            "analyses_fixed": fixed_count,
            "total_discrepancies_found": validation["total_discrepancies"]
        }
    
    def cleanup_orphan_vulnerabilities(self) -> Dict[str, Any]:
        """Remove vulnerabilities not linked to any components"""
        # Find orphan vulnerabilities
        orphan_vulns = self.session.query(Vulnerability).outerjoin(
            component_vulnerabilities
        ).filter(component_vulnerabilities.c.vulnerability_id.is_(None)).all()
        
        orphan_count = len(orphan_vulns)
        
        if orphan_count > 0:
            for vuln in orphan_vulns:
                self.session.delete(vuln)
            
            self.session.commit()
            logger.info(f"Cleaned up {orphan_count} orphan vulnerabilities")
        
        return {
            "message": f"Cleaned up {orphan_count} orphan vulnerabilities",
            "orphan_vulnerabilities_removed": orphan_count
        }
    
    def validate_component_vulnerability_relationships(self) -> Dict[str, Any]:
        """Validate that component vulnerability counts match actual relationships"""
        components = self.session.query(Component).filter(
            Component.vulnerability_count > 0
        ).all()
        
        inconsistencies = []
        
        for component in components:
            actual_vuln_count = len(component.vulnerabilities)
            stored_vuln_count = component.vulnerability_count or 0
            
            if actual_vuln_count != stored_vuln_count:
                inconsistencies.append({
                    "component_id": str(component.id),
                    "component_name": component.name,
                    "analysis_id": str(component.analysis_id),
                    "stored_count": stored_vuln_count,
                    "actual_count": actual_vuln_count
                })
        
        return {
            "total_components_checked": len(components),
            "inconsistent_components": len(inconsistencies),
            "inconsistencies": inconsistencies
        }
    
    def fix_component_vulnerability_counts(self) -> Dict[str, Any]:
        """Fix component vulnerability count discrepancies"""
        validation = self.validate_component_vulnerability_relationships()
        
        fixed_count = 0
        for inconsistency in validation["inconsistencies"]:
            component = self.session.query(Component).filter(
                Component.id == inconsistency["component_id"]
            ).first()
            
            if component:
                component.vulnerability_count = inconsistency["actual_count"]
                fixed_count += 1
        
        if fixed_count > 0:
            self.session.commit()
            logger.info(f"Fixed {fixed_count} component vulnerability count discrepancies")
        
        return {
            "message": f"Fixed {fixed_count} component vulnerability count discrepancies",
            "components_fixed": fixed_count,
            "total_inconsistencies_found": len(validation["inconsistencies"])
        }
    
    def get_count_statistics(self) -> Dict[str, Any]:
        """Get comprehensive count statistics"""
        # Analysis counts
        total_analyses = self.session.query(func.count(Analysis.id)).scalar()
        completed_analyses = self.session.query(func.count(Analysis.id)).filter(
            Analysis.status == AnalysisStatus.COMPLETED
        ).scalar()
        
        # Component counts
        total_components = self.session.query(func.count(Component.id)).scalar()
        components_with_vulns = self.session.query(func.count(Component.id)).filter(
            Component.vulnerability_count > 0
        ).scalar()
        
        # Vulnerability counts
        total_vulnerabilities = self.session.query(func.count(Vulnerability.id)).scalar()
        active_vulnerabilities = self.session.query(Vulnerability).join(
            component_vulnerabilities
        ).distinct().count()
        
        # Orphan counts
        orphan_vulnerabilities = self.session.query(Vulnerability).outerjoin(
            component_vulnerabilities
        ).filter(component_vulnerabilities.c.vulnerability_id.is_(None)).count()
        
        return {
            "analyses": {
                "total": total_analyses,
                "completed": completed_analyses
            },
            "components": {
                "total": total_components,
                "with_vulnerabilities": components_with_vulns
            },
            "vulnerabilities": {
                "total": total_vulnerabilities,
                "active": active_vulnerabilities,
                "orphan": orphan_vulnerabilities
            },
            "data_quality": {
                "orphan_vulnerability_rate": (orphan_vulnerabilities / total_vulnerabilities * 100) if total_vulnerabilities > 0 else 0
            }
        } 