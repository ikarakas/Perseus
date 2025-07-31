#!/usr/bin/env python3
"""Test script to verify Syft and Grype path detection works correctly"""

import os
import sys
import subprocess

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzers.syft_analyzer import SyftAnalyzer
from src.vulnerability.grype_scanner import GrypeScanner

def test_tool_detection():
    """Test that tools are detected correctly in different environments"""
    
    # Check environment
    is_container = os.path.exists('/.dockerenv') or os.environ.get('CONTAINER_ENV') == 'true'
    print(f"Running in container: {is_container}")
    print(f"SYFT_PATH env: {os.environ.get('SYFT_PATH', 'Not set')}")
    print(f"GRYPE_PATH env: {os.environ.get('GRYPE_PATH', 'Not set')}")
    print()
    
    # Test Syft detection
    try:
        analyzer = SyftAnalyzer()
        print(f"✓ Syft found at: {analyzer.syft_path}")
        
        # Verify it actually works
        result = subprocess.run([analyzer.syft_path, 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Syft version: {result.stdout.strip()}")
        else:
            print(f"✗ Syft execution failed: {result.stderr}")
    except Exception as e:
        print(f"✗ Syft detection failed: {e}")
    
    print()
    
    # Test Grype detection
    try:
        # Use a temp directory for grype db in tests
        scanner = GrypeScanner(db_path="/tmp/grype-test-db")
        print(f"✓ Grype found at: {scanner.grype_binary}")
        
        # Verify it actually works
        result = subprocess.run([scanner.grype_binary, 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Grype version: {result.stdout.strip()}")
        else:
            print(f"✗ Grype execution failed: {result.stderr}")
    except Exception as e:
        print(f"✗ Grype detection failed: {e}")

if __name__ == "__main__":
    test_tool_detection()