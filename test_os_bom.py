#!/usr/bin/env python3
"""
Test script for OS-level Bill of Materials functionality
"""

import asyncio
import json
import pprint
from src.analyzers.os_analyzer import OSAnalyzer
from src.api.models import AnalysisOptions

async def test_os_analyzer():
    """Test the OS analyzer locally"""
    print("Testing OS-level Bill of Materials Analyzer\n")
    print("=" * 60)
    
    # Create analyzer
    analyzer = OSAnalyzer()
    
    # Show detected distribution and package manager
    print(f"Detected Distribution: {analyzer.distribution.get('NAME', 'Unknown')}")
    print(f"Distribution Version: {analyzer.distribution.get('VERSION', 'Unknown')}")
    print(f"Package Manager: {analyzer.package_manager or 'None detected'}")
    print()
    
    # Run analysis with default options
    print("Running OS analysis with default options...")
    result = await analyzer.analyze("localhost")
    
    print(f"\nAnalysis ID: {result.analysis_id}")
    print(f"Status: {result.status}")
    print(f"Components found: {len(result.components)}")
    
    if result.errors:
        print(f"\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
    
    print(f"\nMetadata:")
    pprint.pprint(result.metadata, indent=2)
    
    print(f"\nComponents Summary:")
    component_types = {}
    for component in result.components:
        comp_type = component.type or "unknown"
        component_types[comp_type] = component_types.get(comp_type, 0) + 1
    
    for comp_type, count in component_types.items():
        print(f"  - {comp_type}: {count}")
    
    # Show some example components
    print(f"\nExample Components:")
    for component in result.components[:10]:
        print(f"  - {component.name} (v{component.version}) - Type: {component.type}")
    
    # Run deep scan analysis
    print("\n" + "=" * 60)
    print("Running OS analysis with deep scan enabled...")
    options = AnalysisOptions(deep_scan=True)
    deep_result = await analyzer.analyze("localhost", options)
    
    print(f"\nDeep scan components found: {len(deep_result.components)}")
    
    # Save results to file
    output_file = "os_bom_test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "analysis_id": deep_result.analysis_id,
            "status": deep_result.status,
            "metadata": deep_result.metadata,
            "components": [comp.dict() for comp in deep_result.components],
            "errors": deep_result.errors
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    return deep_result

async def test_api_integration():
    """Test the OS analyzer through the API"""
    import aiohttp
    
    print("\n" + "=" * 60)
    print("Testing OS BOM through API...")
    
    # Assuming the API is running on localhost:8000
    api_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Submit OS analysis request
        request_data = {
            "type": "os",
            "location": "localhost",
            "options": {
                "deep_scan": True
            }
        }
        
        try:
            async with session.post(f"{api_url}/analyze/os", json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"\nAnalysis submitted successfully!")
                    print(f"Analysis ID: {result['analysis_id']}")
                    print(f"Status: {result['status']}")
                    print(f"Message: {result['message']}")
                    
                    # Wait a bit for analysis to complete
                    await asyncio.sleep(5)
                    
                    # Check analysis status
                    async with session.get(f"{api_url}/analyze/{result['analysis_id']}/status") as status_response:
                        if status_response.status == 200:
                            status = await status_response.json()
                            print(f"\nAnalysis Status:")
                            pprint.pprint(status, indent=2)
                    
                    # Get results
                    async with session.get(f"{api_url}/analyze/{result['analysis_id']}/results") as results_response:
                        if results_response.status == 200:
                            results = await results_response.json()
                            print(f"\nAnalysis Results:")
                            print(f"Components found: {len(results.get('components', []))}")
                            
                else:
                    print(f"\nError: API returned status {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    
        except aiohttp.ClientConnectorError:
            print("\nError: Could not connect to API. Make sure the API server is running on http://localhost:8000")
        except Exception as e:
            print(f"\nError testing API: {e}")

if __name__ == "__main__":
    print("OS-Level Bill of Materials Test Script")
    print("=====================================\n")
    
    # Run local analyzer test
    asyncio.run(test_os_analyzer())
    
    # Optionally test API integration
    print("\n\nTo test API integration, make sure the SBOM API is running, then uncomment the line below:")
    # asyncio.run(test_api_integration())