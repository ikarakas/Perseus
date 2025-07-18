#!/usr/bin/env python3
"""
Test OS scanning using a Linux Docker container
"""

import asyncio
import subprocess
import json
import sys
import os

from src.analyzers.os_analyzer import OSAnalyzer
from src.api.models import AnalysisOptions

async def test_os_scan_in_docker():
    """Test OS scanning by running the analyzer inside a Linux container"""
    
    print("🐧 Testing OS Scan Feature using Docker Linux Container")
    print("=" * 60)
    
    # Method 1: Create a test script to run inside a container
    test_script = '''
import sys
sys.path.insert(0, "/app/src")

import asyncio
from analyzers.os_analyzer import OSAnalyzer
from api.models import AnalysisOptions

async def main():
    analyzer = OSAnalyzer()
    result = await analyzer.analyze("localhost", AnalysisOptions(deep_scan=True))
    
    print(f"Analysis ID: {result.analysis_id}")
    print(f"Status: {result.status}")
    print(f"Components found: {len(result.components)}")
    
    if result.metadata.get("distribution"):
        dist = result.metadata["distribution"]
        print(f"Distribution: {dist.get('NAME', 'Unknown')} {dist.get('VERSION', '')}")
        print(f"Package Manager: {result.metadata.get('package_manager', 'None')}")
    
    # Show component breakdown
    component_types = {}
    for comp in result.components:
        comp_type = comp.type or "unknown"
        component_types[comp_type] = component_types.get(comp_type, 0) + 1
    
    print("\\nComponent Breakdown:")
    for comp_type, count in component_types.items():
        print(f"  - {comp_type}: {count}")
    
    # Show some examples
    print("\\nExample Components:")
    for comp in result.components[:10]:
        print(f"  • {comp.name} (v{comp.version}) - {comp.type}")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Write the test script
    with open("docker_os_test.py", "w") as f:
        f.write(test_script)
    
    print("1. Running OS scan inside Ubuntu container...")
    
    # Run the test inside an Ubuntu container
    docker_cmd = [
        "docker", "run", "--rm", 
        "-v", f"{os.getcwd()}:/app",
        "-w", "/app",
        "ubuntu:22.04",
        "bash", "-c", 
        "apt-get update > /dev/null 2>&1 && "
        "apt-get install -y python3 python3-pip > /dev/null 2>&1 && "
        "pip3 install psutil > /dev/null 2>&1 && "
        "python3 docker_os_test.py"
    ]
    
    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✅ Ubuntu container analysis:")
            print(result.stdout)
        else:
            print("❌ Ubuntu analysis failed:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("⏱️ Ubuntu analysis timed out")
    except Exception as e:
        print(f"❌ Error running Ubuntu analysis: {e}")
    
    print("\n" + "=" * 60)
    print("2. Running OS scan inside Alpine container...")
    
    # Test with Alpine Linux
    alpine_cmd = [
        "docker", "run", "--rm", 
        "-v", f"{os.getcwd()}:/app",
        "-w", "/app",
        "alpine:latest",
        "sh", "-c", 
        "apk add --no-cache python3 py3-pip > /dev/null 2>&1 && "
        "pip3 install psutil --break-system-packages > /dev/null 2>&1 && "
        "python3 docker_os_test.py"
    ]
    
    try:
        result = subprocess.run(alpine_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✅ Alpine container analysis:")
            print(result.stdout)
        else:
            print("❌ Alpine analysis failed:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("⏱️ Alpine analysis timed out")
    except Exception as e:
        print(f"❌ Error running Alpine analysis: {e}")
    
    # Clean up
    if os.path.exists("docker_os_test.py"):
        os.remove("docker_os_test.py")

async def test_via_api():
    """Test OS scanning via the API (will show error on macOS)"""
    import aiohttp
    
    print("\n" + "=" * 60)
    print("3. Testing via API (expecting macOS error)...")
    
    try:
        async with aiohttp.ClientSession() as session:
            request_data = {
                "type": "os",
                "location": "localhost"
            }
            
            async with session.post("http://localhost:8080/analyze/os", json=request_data) as response:
                result = await response.json()
                analysis_id = result.get('analysis_id')
                print(f"Analysis started: {analysis_id}")
                
                # Wait a moment
                await asyncio.sleep(3)
                
                # Get results
                async with session.get(f"http://localhost:8080/analyze/{analysis_id}/results") as results_response:
                    if results_response.status == 200:
                        results = await results_response.json()
                        print(f"Status: {results.get('status')}")
                        print(f"Errors: {results.get('errors', [])}")
                        print(f"OS Type: {results.get('metadata', {}).get('os_type')}")
    except Exception as e:
        print(f"API test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_os_scan_in_docker())
    asyncio.run(test_via_api())