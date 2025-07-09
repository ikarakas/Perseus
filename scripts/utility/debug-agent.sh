#!/bin/bash
# Debug the agent issues

echo "🔍 Creating debug version of agent..."

# Copy the final package and extract it
cp telemetry-agent-final.tar.gz debug-agent.tar.gz
tar -xzf debug-agent.tar.gz
mv telemetry-agent-final debug-agent

# Create a test script to debug the OS analyzer
cat > debug-agent/test-analyzer.py << 'EOF'
#!/usr/bin/env python3
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
EOF

chmod +x debug-agent/test-analyzer.py

echo "✅ Debug version created!"
echo ""
echo "🚀 Deploy and test:"
echo "1. scp debug-agent.tar.gz parallels@10.211.55.3:/tmp/"
echo "2. ssh parallels@10.211.55.3"
echo "3. cd /tmp && tar -xzf debug-agent.tar.gz"
echo "4. cd debug-agent && source venv/bin/activate"
echo "5. python test-analyzer.py"
echo ""
echo "This will show exactly what's failing in the OS analysis."