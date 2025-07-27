#!/usr/bin/env python3
"""
Test script for SBOM source information enhancement
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_sbom_source_info():
    """Test that SBOMs include source/target information"""
    print("Testing SBOM source information...")
    
    # Test enhanced dashboard SBOM endpoint
    print("\n1. Testing enhanced dashboard SBOMs endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/sboms/all?limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} SBOMs")
        
        if data['sboms']:
            sbom = data['sboms'][0]
            print("\nSample SBOM with source info:")
            print(f"  - SBOM ID: {sbom['sbom_id']}")
            print(f"  - Format: {sbom['format']}")
            print(f"  - Name: {sbom['name']}")
            
            source_info = sbom.get('source_info', {})
            if source_info:
                print("  - Source Information:")
                print(f"    • Analysis Type: {source_info.get('analysis_type', 'N/A')}")
                print(f"    • Target Location: {source_info.get('target_location', 'N/A')}")
                print(f"    • Analysis ID: {source_info.get('analysis_id', 'N/A')}")
                details = source_info.get('details', {})
                if details:
                    print("    • Additional Details:")
                    for key, value in details.items():
                        print(f"      - {key}: {value}")
                print("✓ Source information is present!")
            else:
                print("✗ No source information found")
        else:
            print("No SBOMs available for testing")
    else:
        print(f"✗ Error fetching SBOMs: {response.status_code}")
    
    # Test downloading a specific SBOM to check content
    print("\n2. Testing SBOM content includes source metadata...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/sboms/all?limit=1")
    if response.status_code == 200:
        data = response.json()
        if data['sboms']:
            sbom_id = data['sboms'][0]['sbom_id']
            
            # Download the SBOM
            sbom_response = requests.get(f"{BASE_URL}/sbom/{sbom_id}")
            if sbom_response.status_code == 200:
                sbom_content = sbom_response.json()
                print(f"✓ Downloaded SBOM {sbom_id}")
                
                # Check for source information in different formats
                if sbom_content.get("spdxVersion"):
                    print("  - SPDX format detected")
                    if "comment" in sbom_content:
                        print("  - Comment field found (should contain source info):")
                        print(f"    {sbom_content['comment']}")
                    else:
                        print("  - No comment field with source info")
                
                elif sbom_content.get("bomFormat") == "CycloneDX":
                    print("  - CycloneDX format detected")
                    metadata = sbom_content.get("metadata", {})
                    component = metadata.get("component", {})
                    if component:
                        print("  - Target component found:")
                        print(f"    • Name: {component.get('name', 'N/A')}")
                        print(f"    • Type: {component.get('type', 'N/A')}")
                        
                        properties = component.get("properties", [])
                        if properties:
                            print("  - Properties with source info:")
                            for prop in properties:
                                if prop.get("name", "").startswith("sbom:"):
                                    print(f"    • {prop['name']}: {prop['value']}")
                        else:
                            print("  - No properties with source info")
                    else:
                        print("  - No target component with source info")
                
                elif sbom_content.get("SoftwareIdentity"):
                    print("  - SWID format detected")
                    entities = sbom_content["SoftwareIdentity"].get("Entity", [])
                    if isinstance(entities, dict):
                        entities = [entities]
                    
                    source_entities = [e for e in entities if 
                                     e.get("@name", "").startswith(("Analysis Target:", "Analysis Type:"))]
                    if source_entities:
                        print("  - Source information entities found:")
                        for entity in source_entities:
                            print(f"    • {entity.get('@name', 'N/A')} ({entity.get('@role', 'N/A')})")
                    else:
                        print("  - No source information entities")
                
                else:
                    print("  - Unknown SBOM format")
            else:
                print(f"✗ Failed to download SBOM: {sbom_response.status_code}")

def test_dashboard_display():
    """Test that dashboard displays source information"""
    print("\n3. Testing dashboard display...")
    response = requests.get(f"{BASE_URL}/dashboard")
    if response.status_code == 200:
        content = response.text
        if "Target:" in content and "source_info" in content:
            print("✓ Dashboard includes source information display")
        else:
            print("✗ Dashboard may not be showing source information properly")
    else:
        print(f"✗ Dashboard not accessible: {response.status_code}")

if __name__ == "__main__":
    print("SBOM Source Information Enhancement Test")
    print("=" * 45)
    test_sbom_source_info()
    test_dashboard_display()
    print("\nTest complete!")