#!/usr/bin/env python3
"""Test script to reproduce and fix the Syft Docker analyzer issue"""

import asyncio
import logging
import sys
sys.path.insert(0, '/Users/ikarakas/Development/Python/SBOM')

from src.analyzers.syft_docker_analyzer import SyftDockerAnalyzer
from src.api.models import AnalysisOptions

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_syft_docker():
    """Test Syft Docker analyzer with non-existent image"""
    analyzer = SyftDockerAnalyzer()
    
    # Check the syft path
    print(f"Syft path detected: {analyzer.syft_path}")
    
    # Test with non-existent image
    print("\nTesting with non-existent image: alpine:nonexistent")
    result = await analyzer.analyze("alpine:nonexistent")
    
    print(f"\nResult status: {result.status}")
    print(f"Result errors: {result.errors}")
    print(f"Result metadata: {result.metadata}")

if __name__ == "__main__":
    asyncio.run(test_syft_docker())