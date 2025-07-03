"""
Storage management for analysis results and SBOMs
"""

import os
import json
import pickle
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..api.models import AnalysisResult

logger = logging.getLogger(__name__)

class ResultStorage:
    """Manages storage and retrieval of analysis results and SBOMs"""
    
    def __init__(self, base_path: str = "/app/data"):
        self.base_path = Path(base_path)
        self.results_path = self.base_path / "results"
        self.sboms_path = self.base_path / "sboms"
        
        # Create directories if they don't exist
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.sboms_path.mkdir(parents=True, exist_ok=True)
    
    def store_analysis_result(self, analysis_id: str, result: AnalysisResult) -> None:
        """Store analysis result"""
        try:
            result_file = self.results_path / f"{analysis_id}.json"
            
            # Convert to dict for JSON serialization
            result_dict = {
                "analysis_id": analysis_id,
                "status": result.status,
                "components": [comp.dict() for comp in result.components],
                "errors": result.errors,
                "metadata": result.metadata
            }
            
            with open(result_file, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)
                
            logger.info(f"Stored analysis result {analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to store analysis result {analysis_id}: {e}")
            raise
    
    def get_analysis_result(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Retrieve analysis result"""
        try:
            result_file = self.results_path / f"{analysis_id}.json"
            
            if not result_file.exists():
                return None
            
            with open(result_file, 'r') as f:
                result_dict = json.load(f)
            
            # Convert back to AnalysisResult
            from ..api.models import Component
            components = [Component(**comp) for comp in result_dict["components"]]
            
            return AnalysisResult(
                analysis_id=result_dict["analysis_id"],
                status=result_dict["status"],
                components=components,
                errors=result_dict["errors"],
                metadata=result_dict["metadata"]
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve analysis result {analysis_id}: {e}")
            return None
    
    def store_sbom(self, sbom_id: str, sbom_data: Dict[str, Any]) -> None:
        """Store generated SBOM"""
        try:
            sbom_file = self.sboms_path / f"{sbom_id}.json"
            
            with open(sbom_file, 'w') as f:
                json.dump(sbom_data, f, indent=2, default=str)
                
            logger.info(f"Stored SBOM {sbom_id}")
            
        except Exception as e:
            logger.error(f"Failed to store SBOM {sbom_id}: {e}")
            raise
    
    def get_sbom(self, sbom_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve generated SBOM"""
        try:
            sbom_file = self.sboms_path / f"{sbom_id}.json"
            
            if not sbom_file.exists():
                return None
            
            with open(sbom_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to retrieve SBOM {sbom_id}: {e}")
            return None
    
    def list_analysis_results(self) -> list[str]:
        """List all analysis result IDs"""
        try:
            return [f.stem for f in self.results_path.glob("*.json")]
        except Exception as e:
            logger.error(f"Failed to list analysis results: {e}")
            return []
    
    def list_sboms(self) -> list[str]:
        """List all SBOM IDs"""
        try:
            return [f.stem for f in self.sboms_path.glob("*.json")]
        except Exception as e:
            logger.error(f"Failed to list SBOMs: {e}")
            return []
    
    def cleanup_old_results(self, max_age_days: int = 7) -> None:
        """Clean up old analysis results and SBOMs"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            # Clean analysis results
            for result_file in self.results_path.glob("*.json"):
                if current_time - result_file.stat().st_mtime > max_age_seconds:
                    result_file.unlink()
                    logger.info(f"Cleaned up old analysis result: {result_file.name}")
            
            # Clean SBOMs
            for sbom_file in self.sboms_path.glob("*.json"):
                if current_time - sbom_file.stat().st_mtime > max_age_seconds:
                    sbom_file.unlink()
                    logger.info(f"Cleaned up old SBOM: {sbom_file.name}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old results: {e}")