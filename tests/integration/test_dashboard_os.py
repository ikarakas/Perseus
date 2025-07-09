#!/usr/bin/env python3
"""
Test script for dashboard OS BOM integration
"""

import asyncio
import aiohttp
import time

async def test_dashboard_integration():
    """Test OS BOM through dashboard API endpoints"""
    api_url = "http://localhost:8080"
    
    print("Testing Dashboard OS BOM Integration")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check if OS analysis endpoint exists
        print("\n1. Testing OS analysis endpoint...")
        request_data = {
            "type": "os",
            "location": "localhost"
        }
        
        try:
            async with session.post(f"{api_url}/analyze/os", json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    analysis_id = result.get('analysis_id')
                    print(f"✅ OS analysis started successfully!")
                    print(f"   Analysis ID: {analysis_id}")
                    
                    # Test 2: Wait and check status
                    print("\n2. Waiting for analysis to complete...")
                    for i in range(10):
                        await asyncio.sleep(2)
                        async with session.get(f"{api_url}/analyze/{analysis_id}/status") as status_response:
                            if status_response.status == 200:
                                status_data = await status_response.json()
                                print(f"   Status check {i+1}: {status_data.get('status', 'unknown')}")
                                
                                if status_data.get('status') == 'completed':
                                    break
                    
                    # Test 3: Get detailed results
                    print("\n3. Getting detailed results...")
                    async with session.get(f"{api_url}/analyze/{analysis_id}/results") as results_response:
                        if results_response.status == 200:
                            results = await results_response.json()
                            print(f"✅ Results retrieved successfully!")
                            print(f"   Components found: {len(results.get('components', []))}")
                            
                            # Show distribution info if available
                            metadata = results.get('metadata', {})
                            if 'distribution' in metadata:
                                dist = metadata['distribution']
                                print(f"   Distribution: {dist.get('NAME', 'Unknown')} {dist.get('VERSION', '')}")
                                print(f"   Package Manager: {metadata.get('package_manager', 'None')}")
                                
                                # Show component breakdown
                                components = results.get('components', [])
                                component_types = {}
                                for comp in components:
                                    comp_type = comp.get('type', 'unknown')
                                    component_types[comp_type] = component_types.get(comp_type, 0) + 1
                                
                                print(f"   Component Breakdown:")
                                for comp_type, count in component_types.items():
                                    print(f"     - {comp_type}: {count}")
                        else:
                            print(f"❌ Failed to get results: {results_response.status}")
                    
                    # Test 4: Check metrics
                    print("\n4. Checking metrics...")
                    async with session.get(f"{api_url}/api/metrics") as metrics_response:
                        if metrics_response.status == 200:
                            metrics = await metrics_response.json()
                            print(f"✅ Metrics retrieved successfully!")
                            
                            analysis_metrics = metrics.get('analysis', {})
                            print(f"   Total analyses: {analysis_metrics.get('total_analyses', 0)}")
                            
                            by_type = analysis_metrics.get('analyses_by_type', {})
                            for analysis_type, count in by_type.items():
                                if 'os' in analysis_type:
                                    print(f"   OS analyses: {count}")
                        else:
                            print(f"❌ Failed to get metrics: {metrics_response.status}")
                    
                    # Test 5: Test dashboard HTML
                    print("\n5. Testing dashboard HTML...")
                    async with session.get(f"{api_url}/dashboard") as dashboard_response:
                        if dashboard_response.status == 200:
                            html_content = await dashboard_response.text()
                            if 'Operating System' in html_content and 'analyze/os' in html_content:
                                print(f"✅ Dashboard contains OS analysis options!")
                            else:
                                print(f"❌ Dashboard missing OS analysis options")
                        else:
                            print(f"❌ Failed to get dashboard: {dashboard_response.status}")
                            
                else:
                    error_data = await response.text()
                    print(f"❌ OS analysis failed with status {response.status}:")
                    print(f"   {error_data}")
                    
        except aiohttp.ClientConnectorError:
            print("❌ Could not connect to API. Make sure the server is running on http://localhost:8080")
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    print("Dashboard OS BOM Integration Test")
    print("=================================\n")
    print("Prerequisites:")
    print("- SBOM API server running on http://localhost:8080")
    print("- Linux system for OS analysis to work properly")
    print()
    
    asyncio.run(test_dashboard_integration())