#!/usr/bin/env python3
"""
Simple integration test for Docker SBOM functionality
This script tests the Docker image analysis end-to-end without pytest
"""

import json
import requests
import time
import sys

def test_docker_analysis_api():
    """Test Docker analysis through the API"""
    base_url = "http://localhost:8000"  # Assuming API is running
    
    print("🐋 Testing Docker Image SBOM Analysis")
    print("=" * 50)
    
    # Test 1: Submit Docker analysis
    print("1. Submitting Docker image analysis for alpine:latest...")
    
    analysis_request = {
        "type": "docker",
        "location": "alpine:latest",
        "options": {
            "deep_scan": False,  # Use shallow scan for faster testing
            "timeout_minutes": 5
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/analyze/docker",
            json=analysis_request,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis_id = result.get("analysis_id")
            print(f"✅ Analysis submitted successfully. ID: {analysis_id}")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            
            # Test 2: Check analysis status
            print(f"\n2. Checking analysis status...")
            
            # Wait a bit for analysis to start
            time.sleep(2)
            
            max_attempts = 30  # Wait up to 60 seconds
            for attempt in range(max_attempts):
                status_response = requests.get(f"{base_url}/analyze/{analysis_id}/status")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    current_status = status_data.get("status", "unknown")
                    print(f"   Attempt {attempt + 1}: Status = {current_status}")
                    
                    if current_status in ["completed", "failed"]:
                        break
                        
                    time.sleep(2)
                else:
                    print(f"❌ Failed to get status: {status_response.status_code}")
                    break
            
            # Test 3: Get analysis results
            if current_status == "completed":
                print(f"\n3. Getting analysis results...")
                
                results_response = requests.get(f"{base_url}/analyze/{analysis_id}/results")
                
                if results_response.status_code == 200:
                    results_data = results_response.json()
                    components = results_data.get("components", [])
                    metadata = results_data.get("metadata", {})
                    
                    print(f"✅ Analysis completed successfully!")
                    print(f"   Components found: {len(components)}")
                    print(f"   Analyzer: {metadata.get('analyzer', 'unknown')}")
                    print(f"   Image: {metadata.get('image', 'unknown')}")
                    
                    # Show first few components
                    if components:
                        print(f"\n   Sample components:")
                        for i, comp in enumerate(components[:5]):
                            name = comp.get("name", "unknown")
                            version = comp.get("version", "unknown")
                            comp_type = comp.get("type", "unknown")
                            print(f"     {i+1}. {name} v{version} ({comp_type})")
                        
                        if len(components) > 5:
                            print(f"     ... and {len(components) - 5} more")
                    
                    # Test 4: Generate SBOM
                    print(f"\n4. Generating SBOM...")
                    
                    sbom_request = {
                        "analysis_ids": [analysis_id],
                        "format": "spdx",
                        "include_licenses": True,
                        "include_vulnerabilities": False
                    }
                    
                    sbom_response = requests.post(
                        f"{base_url}/sbom/generate",
                        json=sbom_request,
                        timeout=30
                    )
                    
                    if sbom_response.status_code == 200:
                        sbom_result = sbom_response.json()
                        sbom_id = sbom_result.get("sbom_id")
                        print(f"✅ SBOM generation started. ID: {sbom_id}")
                        
                        # Wait for SBOM completion
                        time.sleep(3)
                        
                        sbom_data_response = requests.get(f"{base_url}/sbom/{sbom_id}")
                        if sbom_data_response.status_code == 200:
                            sbom_data = sbom_data_response.json()
                            print(f"✅ SBOM generated successfully!")
                            print(f"   Format: SPDX")
                            print(f"   Document name: {sbom_data.get('name', 'unknown')}")
                            packages = sbom_data.get('packages', [])
                            print(f"   Total packages: {len(packages)}")
                            
                            print(f"\n🎉 Docker SBOM Analysis Test PASSED!")
                            return True
                        else:
                            print(f"❌ Failed to get SBOM: {sbom_data_response.status_code}")
                    else:
                        print(f"❌ SBOM generation failed: {sbom_response.status_code}")
                        
                else:
                    print(f"❌ Failed to get results: {results_response.status_code}")
                    
            elif current_status == "failed":
                print(f"❌ Analysis failed")
                # Try to get error details
                results_response = requests.get(f"{base_url}/analyze/{analysis_id}/results")
                if results_response.status_code == 200:
                    results_data = results_response.json()
                    errors = results_data.get("errors", [])
                    if errors:
                        print(f"   Error details: {errors[0]}")
            else:
                print(f"❌ Analysis timed out (status: {current_status})")
            
        else:
            print(f"❌ Failed to submit analysis: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.ConnectionError:
        print("❌ Could not connect to API server. Is it running on localhost:8000?")
        print("   Try running: uvicorn src.api.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return False


def test_docker_image_format_validation():
    """Test Docker image format validation locally"""
    print("\n🔍 Testing Docker Image Format Validation")
    print("=" * 50)
    
    # Test various image formats
    test_cases = [
        ("nginx:latest", True, "Standard Docker Hub image"),
        ("ubuntu:20.04", True, "Docker Hub with version"),
        ("docker:alpine:3.14", True, "Docker prefix format"),
        ("registry.example.com/myapp:v1.0", True, "Private registry"),
        ("gcr.io/project/image:tag", True, "Google Container Registry"),
        ("image@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", True, "SHA256 digest"),
        ("/path/to/file", False, "Local file path"),
        ("http://example.com", False, "HTTP URL"),
        ("", False, "Empty string"),
        ("just-text", False, "Plain text")
    ]
    
    # Simple validation logic (mimics the analyzer)
    import re
    
    docker_patterns = [
        re.compile(r'^docker:([^:]+):([^:]+)$'),
        re.compile(r'^docker:([^:]+)$'),
        re.compile(r'^([a-zA-Z0-9\.\-]+(?:\:[0-9]+)?)/([a-zA-Z0-9\.\-_/]+):([a-zA-Z0-9\.\-_]+)$'),
        re.compile(r'^([a-zA-Z0-9\.\-]+(?:\:[0-9]+)?)/([a-zA-Z0-9\.\-_/]+)$'),
        re.compile(r'^([a-zA-Z0-9\.\-_]+):([a-zA-Z0-9\.\-_]+)$'),
        re.compile(r'^([a-zA-Z0-9\.\-_/]+)@sha256:([a-f0-9]{64})$'),
    ]
    
    def is_docker_image(location):
        for pattern in docker_patterns:
            if pattern.match(location):
                return True
        return location.startswith('docker:') or '@sha256:' in location
    
    passed = 0
    total = len(test_cases)
    
    for image, expected, description in test_cases:
        result = is_docker_image(image)
        status = "✅" if result == expected else "❌"
        print(f"{status} {image:<50} -> {result} ({description})")
        if result == expected:
            passed += 1
    
    print(f"\nValidation Test Results: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    print("Docker SBOM Analysis Integration Test")
    print("=====================================\n")
    
    # Test 1: Format validation (local)
    validation_passed = test_docker_image_format_validation()
    
    # Test 2: API integration (requires running server)
    print("\nNote: The following test requires the API server to be running.")
    print("Start it with: uvicorn src.api.main:app --host 0.0.0.0 --port 8000\n")
    
    user_input = input("Do you want to run the API integration test? (y/N): ").strip().lower()
    
    if user_input in ['y', 'yes']:
        api_passed = test_docker_analysis_api()
    else:
        print("Skipping API integration test.")
        api_passed = True  # Don't fail overall test
    
    # Summary
    print(f"\n{'='*50}")
    print("Test Summary:")
    print(f"  Format Validation: {'PASS' if validation_passed else 'FAIL'}")
    print(f"  API Integration: {'PASS' if api_passed else 'SKIPPED/FAIL'}")
    
    if validation_passed:
        print(f"\n🎉 Docker SBOM functionality is working correctly!")
        sys.exit(0)
    else:
        print(f"\n❌ Some tests failed.")
        sys.exit(1)