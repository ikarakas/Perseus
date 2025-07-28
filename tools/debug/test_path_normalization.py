#!/usr/bin/env python3
"""
Test script to verify path normalization works correctly
"""

import os
import sys
import tempfile
import shutil

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analyzers.base import BaseAnalyzer

class TestAnalyzer(BaseAnalyzer):
    """Test analyzer to verify path normalization"""
    
    async def analyze(self, location, options=None):
        pass  # Not needed for testing

def test_path_normalization():
    """Test that path normalization handles trailing slashes correctly"""
    analyzer = TestAnalyzer()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = os.path.join(temp_dir, "sample-test-app")
        os.makedirs(test_dir)
        
        # Create a test file in the directory
        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        print(f"Created test directory: {test_dir}")
        
        # Test cases
        test_cases = [
            (test_dir, "Directory without trailing slash"),
            (test_dir + "/", "Directory with trailing slash"),
            (test_dir + "//", "Directory with double trailing slash"),
            (test_dir + "/./", "Directory with ./ at end"),
            (test_dir + "/../" + os.path.basename(test_dir) + "/", "Directory with ../ navigation"),
        ]
        
        print("\n=== Path Normalization Test Results ===")
        all_passed = True
        
        for test_path, description in test_cases:
            try:
                normalized = analyzer._parse_location(test_path)
                exists = os.path.exists(normalized)
                is_dir = os.path.isdir(normalized)
                
                # All should normalize to the same directory
                expected = test_dir
                passed = normalized == expected and exists and is_dir
                
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"{status} {description}")
                print(f"    Input:      {test_path}")
                print(f"    Normalized: {normalized}")
                print(f"    Expected:   {expected}")
                print(f"    Exists:     {exists}, Is Dir: {is_dir}")
                print()
                
                if not passed:
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ ERROR {description}")
                print(f"    Input: {test_path}")
                print(f"    Error: {e}")
                print()
                all_passed = False
        
        # Test file:// prefix handling
        print("=== File:// Protocol Test ===")
        file_url = f"file://{test_dir}"
        normalized_file = analyzer._parse_location(file_url)
        file_passed = normalized_file == test_dir and os.path.exists(normalized_file)
        
        status = "✅ PASS" if file_passed else "❌ FAIL"
        print(f"{status} File:// protocol handling")
        print(f"    Input:      {file_url}")
        print(f"    Normalized: {normalized_file}")
        print(f"    Expected:   {test_dir}")
        print()
        
        if not file_passed:
            all_passed = False
        
        # Test non-existent path handling
        print("=== Non-existent Path Test ===")
        nonexistent = os.path.join(temp_dir, "does-not-exist")
        normalized_nonexistent = analyzer._parse_location(nonexistent)
        
        print(f"✅ INFO Non-existent path handling")
        print(f"    Input:      {nonexistent}")
        print(f"    Normalized: {normalized_nonexistent}")
        print(f"    Expected:   {nonexistent}")
        print()
        
        return all_passed

if __name__ == "__main__":
    print("Testing path normalization for trailing slash handling...")
    
    success = test_path_normalization()
    
    if success:
        print("🎉 All tests passed! Path normalization works correctly.")
        print("\nBoth '/app/data/sample-macos-app/' and '/app/data/sample-macos-app' should now work!")
    else:
        print("💥 Some tests failed. Check the implementation.")
        sys.exit(1)