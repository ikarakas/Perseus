#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Comprehensive concurrent verification test runner for Perseus
"""

import asyncio
import subprocess
import time
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.automated_verification import run_verification


def check_perseus_running():
    """Check if Perseus API is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/")
        return response.status_code == 200
    except:
        return False


def cleanup_old_analyses():
    """Clean up old analyses to start fresh"""
    try:
        import requests
        # Get all analyses
        response = requests.get("http://localhost:8000/api/v1/analyses")
        if response.status_code == 200:
            data = response.json()
            analyses = data.get("analyses", [])
            
            print(f"Found {len(analyses)} existing analyses")
            
            # Delete old analyses
            for analysis in analyses:
                analysis_id = analysis.get("analysis_id")
                del_response = requests.delete(f"http://localhost:8000/api/v1/analyses/{analysis_id}")
                if del_response.status_code == 200:
                    print(f"  - Deleted analysis {analysis_id}")
            
            # Clean up orphan vulnerabilities
            cleanup_response = requests.post("http://localhost:8000/api/v1/counts/cleanup/orphans")
            if cleanup_response.status_code == 200:
                cleanup_data = cleanup_response.json()
                print(f"Cleaned up {cleanup_data.get('deleted_count', 0)} orphan vulnerabilities")
                
    except Exception as e:
        print(f"Warning: Could not clean up old data: {e}")


def run_count_validation():
    """Run count validation and fix any discrepancies"""
    try:
        import requests
        
        # Validate counts
        val_response = requests.get("http://localhost:8000/api/v1/counts/validate/all")
        if val_response.status_code == 200:
            val_data = val_response.json()
            discrepancies = val_data.get("total_discrepancies", 0)
            
            if discrepancies > 0:
                print(f"Found {discrepancies} count discrepancies, fixing...")
                fix_response = requests.post("http://localhost:8000/api/v1/counts/fix/all")
                if fix_response.status_code == 200:
                    fix_data = fix_response.json()
                    print(f"Fixed {fix_data.get('analyses_fixed', 0)} analyses")
                    
    except Exception as e:
        print(f"Warning: Could not run count validation: {e}")


async def main():
    """Main test runner"""
    print("Perseus Concurrent Verification Test")
    print("="*80)
    print()
    
    # Check if Perseus is running
    if not check_perseus_running():
        print("ERROR: Perseus API is not running on http://localhost:8000")
        print("Please start Perseus first with: docker-compose up -d")
        return 1
    
    print("✓ Perseus API is running")
    print()
    
    # Optional: Clean up old data
    response = input("Clean up old analyses before starting? (y/N): ")
    if response.lower() == 'y':
        print("Cleaning up old analyses...")
        cleanup_old_analyses()
        print()
    
    # Configure test parameters
    num_users = 7
    duration_minutes = 3
    
    print(f"Test Configuration:")
    print(f"  - Number of concurrent users: {num_users}")
    print(f"  - Test duration: {duration_minutes} minutes")
    print()
    
    # Run the verification
    print("Starting concurrent user simulation...")
    print("-"*80)
    
    try:
        report = await run_verification(num_users=num_users, duration_minutes=duration_minutes)
        
        # Run final count validation
        print("\nRunning final count validation...")
        run_count_validation()
        
        # Analyze results
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        
        consistency_checks = report['summary']['consistency_checks']
        pass_rate = consistency_checks['pass_rate']
        
        if pass_rate >= 95:
            print("✓ PASSED: All consistency checks passed with high confidence")
            result_code = 0
        elif pass_rate >= 80:
            print("⚠ WARNING: Some consistency issues detected")
            result_code = 1
        else:
            print("✗ FAILED: Significant consistency issues detected")
            result_code = 2
        
        print()
        print("Detailed Results:")
        print(f"  - Pass Rate: {pass_rate:.2f}%")
        print(f"  - Total Checks: {consistency_checks['total']}")
        print(f"  - Passed: {consistency_checks['passed']}")
        print(f"  - Failed: {consistency_checks['failed']}")
        
        # Show failed checks
        if consistency_checks['failed'] > 0:
            print("\nFailed Checks:")
            for check in report['consistency_checks']:
                if not check['passed']:
                    print(f"  - {check['type']}: {check['details']}")
        
        print("\nPerformance Metrics:")
        total_analyses = report['summary']['total_analyses']
        total_time = duration_minutes * 60
        analyses_per_minute = (total_analyses / total_time) * 60 if total_time > 0 else 0
        print(f"  - Total Analyses: {total_analyses}")
        print(f"  - Analyses per minute: {analyses_per_minute:.2f}")
        print(f"  - Unique Components Found: {report['summary']['unique_components']}")
        print(f"  - Unique Vulnerabilities Found: {report['summary']['unique_vulnerabilities']}")
        
        return result_code
        
    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)