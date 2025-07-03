#!/usr/bin/env python3
"""
SBOM Generator Service
Standalone service for generating SBOMs from analysis results
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, '/generator/src')

from sbom.generator import SBOMGenerator
from api.models import SBOMRequest, AnalysisResult, Component

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SBOMGeneratorService:
    """Standalone SBOM generator service"""
    
    def __init__(self):
        self.generator = SBOMGenerator()
        self.data_dir = Path("/app/data")
        self.data_dir.mkdir(exist_ok=True)
    
    async def process_request(self, request_file: str):
        """Process SBOM generation request from file"""
        try:
            # Read request
            with open(request_file, 'r') as f:
                request_data = json.load(f)
            
            request = SBOMRequest(**request_data['request'])
            sbom_id = request_data['sbom_id']
            
            # Load analysis results
            analysis_results = []
            for analysis_id in request.analysis_ids:
                result_file = self.data_dir / f"{analysis_id}_result.json"
                if result_file.exists():
                    with open(result_file, 'r') as f:
                        result_data = json.load(f)
                    
                    # Convert to AnalysisResult
                    components = [Component(**comp) for comp in result_data["components"]]
                    analysis_result = AnalysisResult(
                        analysis_id=result_data["analysis_id"],
                        status=result_data["status"],
                        components=components,
                        errors=result_data["errors"],
                        metadata=result_data["metadata"]
                    )
                    analysis_results.append(analysis_result)
                else:
                    logger.warning(f"Analysis result not found: {analysis_id}")
            
            if not analysis_results:
                raise ValueError("No valid analysis results found")
            
            # Generate SBOM
            logger.info(f"Starting SBOM generation {sbom_id} with format {request.format}")
            sbom_data = await self.generator.generate(
                analysis_results,
                request.format,
                request.include_licenses,
                request.include_vulnerabilities
            )
            
            # Write SBOM
            sbom_file = self.data_dir / f"{sbom_id}_sbom.json"
            with open(sbom_file, 'w') as f:
                json.dump(sbom_data, f, indent=2, default=str)
            
            logger.info(f"Completed SBOM generation {sbom_id}")
            
        except Exception as e:
            logger.error(f"SBOM generation failed: {e}")
            # Write error result
            error_result = {
                "sbom_id": request_data.get('sbom_id', 'unknown'),
                "status": "failed",
                "error": str(e)
            }
            error_file = self.data_dir / f"{request_data.get('sbom_id', 'unknown')}_error.json"
            with open(error_file, 'w') as f:
                json.dump(error_result, f, indent=2)
    
    async def run(self):
        """Main service loop"""
        logger.info("SBOM Generator Service starting...")
        
        # Watch for request files
        requests_dir = self.data_dir / "requests"
        requests_dir.mkdir(exist_ok=True)
        
        processed_dir = self.data_dir / "processed"
        processed_dir.mkdir(exist_ok=True)
        
        while True:
            try:
                # Look for new request files
                request_files = list(requests_dir.glob("sbom_*.json"))
                
                for request_file in request_files:
                    try:
                        await self.process_request(request_file)
                        # Move to processed
                        request_file.rename(processed_dir / request_file.name)
                    except Exception as e:
                        logger.error(f"Failed to process {request_file}: {e}")
                        # Move to processed anyway to avoid infinite loop
                        request_file.rename(processed_dir / f"error_{request_file.name}")
                
                # Sleep before checking again
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Service stopped")
                break
            except Exception as e:
                logger.error(f"Service error: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    service = SBOMGeneratorService()
    asyncio.run(service.run())