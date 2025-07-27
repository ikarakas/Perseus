#!/usr/bin/env python3
"""
Test script for enhanced dashboard SBOM functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_all_sboms_endpoint():
    """Test the new all SBOMs endpoint"""
    print("Testing /api/v1/dashboard/sboms/all endpoint...")
    
    # Test without filters
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/sboms/all")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} total SBOMs")
        print(f"✓ Returned {len(data['sboms'])} SBOMs (limit: {data.get('limit', 'N/A')})")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
    
    # Test with pagination
    print("\nTesting pagination...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/sboms/all?offset=10&limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Pagination works - offset: {data['offset']}, limit: {data['limit']}")
    else:
        print(f"✗ Pagination error: {response.status_code}")
    
    # Test with search
    print("\nTesting search functionality...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/sboms/all?search=test")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Search works - found {data['total']} SBOMs matching 'test'")
    else:
        print(f"✗ Search error: {response.status_code}")
    
    # Test with format filter
    print("\nTesting format filter...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/sboms/all?format=cyclonedx")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Format filter works - found {data['total']} CycloneDX SBOMs")
    else:
        print(f"✗ Format filter error: {response.status_code}")

def test_enhanced_dashboard_page():
    """Test the enhanced dashboard page loads"""
    print("\nTesting enhanced dashboard page...")
    response = requests.get(f"{BASE_URL}/dashboard/enhanced")
    if response.status_code == 200:
        print("✓ Enhanced dashboard page loads successfully")
    else:
        print(f"✗ Dashboard page error: {response.status_code}")

if __name__ == "__main__":
    print("Enhanced Dashboard SBOM Feature Test")
    print("=" * 40)
    test_all_sboms_endpoint()
    test_enhanced_dashboard_page()
    print("\nTest complete!")