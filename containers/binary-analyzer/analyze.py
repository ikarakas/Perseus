#!/usr/bin/env python3
"""
Binary Analyzer Service
Standalone service for analyzing compiled binaries
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, '/analyzer/src')

from analyzers.binary_analyzer import BinaryAnalyzer
from api.models import AnalysisOptions, AnalysisRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinaryAnalyzerService:
    """Standalone binary analyzer service"""
    
    def __init__(self):
        self.analyzer = BinaryAnalyzer()
        self.data_dir = Path("/app/data")
        self.data_dir.mkdir(exist_ok=True)
    
    async def analyze_request(self, request_file: str):
        """Process analysis request from file"""
        try:
            # Read request
            with open(request_file, 'r') as f:
                request_data = json.load(f)
            
            request = AnalysisRequest(**request_data)
            
            # Perform analysis
            logger.info(f"Starting binary analysis for {request.location}")
            result = await self.analyzer.analyze(request.location, request.options)
            
            # Write result
            result_file = self.data_dir / f"{request_data['analysis_id']}_result.json"
            with open(result_file, 'w') as f:
                json.dump({
                    "analysis_id": request_data['analysis_id'],
                    "status": result.status,
                    "components": [comp.dict() for comp in result.components],
                    "errors": result.errors,
                    "metadata": result.metadata
                }, f, indent=2, default=str)
            
            logger.info(f"Completed binary analysis, found {len(result.components)} components")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Write error result
            error_result = {
                "analysis_id": request_data.get('analysis_id', 'unknown'),
                "status": "failed",
                "components": [],
                "errors": [str(e)],
                "metadata": {"analyzer_type": "binary"}
            }
            result_file = self.data_dir / f"{request_data.get('analysis_id', 'unknown')}_result.json"
            with open(result_file, 'w') as f:
                json.dump(error_result, f, indent=2)
    
    async def run(self):
        """Main service loop"""
        logger.info("Binary Analyzer Service starting...")
        
        # Watch for request files
        requests_dir = self.data_dir / "requests"
        requests_dir.mkdir(exist_ok=True)
        
        processed_dir = self.data_dir / "processed"
        processed_dir.mkdir(exist_ok=True)
        
        while True:
            try:
                # Look for new request files
                request_files = list(requests_dir.glob("binary_*.json"))
                
                for request_file in request_files:
                    try:
                        await self.analyze_request(request_file)
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
    service = BinaryAnalyzerService()
    asyncio.run(service.run())