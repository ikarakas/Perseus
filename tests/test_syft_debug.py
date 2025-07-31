#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('/Users/ikarakas/Development/Python/SBOM/src')

from analyzers.syft_analyzer import SyftAnalyzer

async def test_syft():
    print("Testing SyftAnalyzer...")
    
    try:
        analyzer = SyftAnalyzer()
        print(f"Syft path found: {analyzer.syft_path}")
        
        # Test analysis of the macOS binary
        result = await analyzer.analyze('data/sample-macos-app/sample-macos-static-app')
        print(f"Analysis status: {result.status}")
        print(f"Components found: {len(result.components)}")
        
        if result.status == "failed":
            print(f"Error: {result.metadata.get('error', 'Unknown error')}")
        else:
            print("✅ Syft analysis successful!")
            for i, comp in enumerate(result.components[:3]):  # Show first 3 components
                print(f"  Component {i+1}: {comp.name} v{comp.version}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_syft())