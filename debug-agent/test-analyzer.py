#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""Test the OS analyzer directly to see what's failing."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.analyzers.os_analyzer import OSAnalyzer
from src.api.models import AnalysisOptions

async def test_analyzer():
    print("🔍 Testing OS analyzer directly...")
    
    analyzer = OSAnalyzer()
    options = AnalysisOptions(deep_scan=False)
    
    try:
        result = await analyzer.analyze("localhost", options)
        
        print(f"✅ Analysis Status: {result.status}")
        print(f"📦 Components found: {len(result.components)}")
        
        if result.errors:
            print(f"❌ Errors: {result.errors}")
        
        if result.components:
            print("\n📋 First 5 components:")
            for i, comp in enumerate(result.components[:5]):
                print(f"  {i+1}. {comp.get('name', 'Unknown')} ({comp.get('type', 'unknown')})")
        
        print(f"\n🖥️  Distribution: {result.metadata.get('distribution', {})}")
        print(f"📦 Package Manager: {result.metadata.get('package_manager', 'Unknown')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_analyzer())
