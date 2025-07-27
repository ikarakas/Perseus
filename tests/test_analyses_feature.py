#!/usr/bin/env python3
"""
Test script for enhanced dashboard analyses functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_all_analyses_endpoint():
    """Test the new all analyses endpoint"""
    print("Testing /api/v1/dashboard/analyses/all endpoint...")
    
    # Test without filters
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/analyses/all")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} total analyses")
        print(f"✓ Returned {len(data['analyses'])} analyses (limit: {data.get('limit', 'N/A')})")
        if data['analyses']:
            print("\nSample analysis:")
            a = data['analyses'][0]
            print(f"  - ID: {a['analysis_id']}")
            print(f"  - Type: {a['analysis_type']}")
            print(f"  - Status: {a['status']}")
            print(f"  - Components: {a['component_count']}")
            print(f"  - Vulnerabilities: {a['vulnerability_count']}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
    
    # Test with pagination
    print("\nTesting pagination...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/analyses/all?offset=5&limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Pagination works - offset: {data['offset']}, limit: {data['limit']}")
    else:
        print(f"✗ Pagination error: {response.status_code}")
    
    # Test with search
    print("\nTesting search functionality...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/analyses/all?search=syft")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Search works - found {data['total']} analyses matching 'syft'")
    else:
        print(f"✗ Search error: {response.status_code}")
    
    # Test with status filter
    print("\nTesting status filter...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/analyses/all?status=completed")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status filter works - found {data['total']} completed analyses")
    else:
        print(f"✗ Status filter error: {response.status_code}")
    
    # Test with analysis type filter
    print("\nTesting analysis type filter...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/analyses/all?analysis_type=syft")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Type filter works - found {data['total']} syft analyses")
    else:
        print(f"✗ Type filter error: {response.status_code}")

def test_dashboard_page():
    """Test the dashboard page loads with analyses section"""
    print("\nTesting dashboard page...")
    response = requests.get(f"{BASE_URL}/dashboard")
    if response.status_code == 200:
        content = response.text
        if "All Analyses" in content:
            print("✓ Dashboard page includes All Analyses section")
        else:
            print("✗ All Analyses section not found in dashboard")
    else:
        print(f"✗ Dashboard page error: {response.status_code}")

if __name__ == "__main__":
    print("Enhanced Dashboard Analyses Feature Test")
    print("=" * 40)
    test_all_analyses_endpoint()
    test_dashboard_page()
    print("\nTest complete!")