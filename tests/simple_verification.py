#!/usr/bin/env python3
# Simple verification test to check the fixes
import asyncio
import aiohttp
import json
import uuid
from datetime import datetime

async def test_sbom_generation():
    """Test SBOM generation specifically"""
    print("Testing SBOM generation...")
    
    # First, submit an analysis
    async with aiohttp.ClientSession() as session:
        # Submit source analysis
        analysis_request = {
            "location": "data/vulnerable-java-app",
            "type": "source",
            "language": "java"
        }
        
        async with session.post("http://localhost:8000/analyze/source", json=analysis_request) as resp:
            if resp.status == 200:
                analysis_result = await resp.json()
                analysis_id = analysis_result["analysis_id"]
                print(f"✓ Analysis submitted: {analysis_id}")
                
                # Wait for analysis to complete
                print("Waiting for analysis to complete...")
                await asyncio.sleep(30)  # Wait 30 seconds
                
                # Check status
                async with session.get(f"http://localhost:8000/analyze/{analysis_id}/status") as status_resp:
                    if status_resp.status == 200:
                        status_data = await status_resp.json()
                        print(f"Analysis status: {status_data.get('status')}")
                        
                        if status_data.get('status') == 'completed':
                            # Now try SBOM generation with correct format
                            sbom_request = {
                                "analysis_ids": [analysis_id],  # Fixed: use analysis_ids (plural)
                                "format": "spdx",
                                "include_vulnerabilities": True
                            }
                            
                            async with session.post("http://localhost:8000/sbom/generate", json=sbom_request) as sbom_resp:
                                if sbom_resp.status == 200:
                                    sbom_result = await sbom_resp.json()
                                    sbom_id = sbom_result["sbom_id"]
                                    print(f"✓ SBOM generation started: {sbom_id}")
                                    
                                    # Wait for SBOM to generate
                                    await asyncio.sleep(10)
                                    
                                    # Check if SBOM was created in database
                                    async with session.get("http://localhost:8000/api/v1/sboms") as sboms_resp:
                                        if sboms_resp.status == 200:
                                            sboms_data = await sboms_resp.json()
                                            sbom_count = sboms_data.get("total", 0)
                                            print(f"✓ Total SBOMs in database: {sbom_count}")
                                            
                                            if sbom_count > 0:
                                                print("✅ SBOM GENERATION FIXED!")
                                                return True
                                            else:
                                                print("❌ SBOM not found in database")
                                                return False
                                else:
                                    print(f"❌ SBOM generation failed: {sbom_resp.status}")
                                    return False
                        else:
                            print(f"❌ Analysis not completed: {status_data.get('status')}")
                            return False
                    else:
                        print(f"❌ Status check failed: {status_resp.status}")
                        return False
            else:
                print(f"❌ Analysis submission failed: {resp.status}")
                return False

async def test_component_counting():
    """Test component counting"""
    print("\nTesting component counting...")
    
    async with aiohttp.ClientSession() as session:
        # Get current count
        async with session.get("http://localhost:8000/api/v1/components/unique") as resp:
            if resp.status == 200:
                data = await resp.json()
                component_count = data.get("total", 0)
                print(f"✓ Current unique components: {component_count}")
                return component_count > 0
            else:
                print(f"❌ Component count failed: {resp.status}")
                return False

async def test_vulnerability_tracking():
    """Test vulnerability tracking"""
    print("\nTesting vulnerability tracking...")
    
    async with aiohttp.ClientSession() as session:
        # Get current count
        async with session.get("http://localhost:8000/api/v1/vulnerabilities?limit=1") as resp:
            if resp.status == 200:
                data = await resp.json()
                vuln_count = data.get("total", 0)
                print(f"✓ Current vulnerabilities: {vuln_count}")
                return vuln_count > 0
            else:
                print(f"❌ Vulnerability count failed: {resp.status}")
                return False

async def main():
    print("Perseus Simple Verification Test")
    print("="*50)
    
    results = {
        "sbom_generation": await test_sbom_generation(),
        "component_counting": await test_component_counting(),
        "vulnerability_tracking": await test_vulnerability_tracking()
    }
    
    print("\n" + "="*50)
    print("RESULTS:")
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test}: {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED - Issues are fixed!")
    else:
        print("⚠️  Some issues remain - need more fixes")

if __name__ == "__main__":
    asyncio.run(main())