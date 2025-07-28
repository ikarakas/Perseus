#!/usr/bin/env python3
"""
Debug script to test OSV scanner functionality
"""

import sys
import asyncio
import logging
sys.path.insert(0, 'src')

from api.models import Component
from vulnerability.osv_scanner import OSVScanner

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_osv_scanner():
    """Test OSV scanner with known vulnerable components"""
    
    # Test components that should have vulnerabilities
    test_components = [
        Component(
            name="log4j-core",
            version="2.14.0",
            purl="pkg:maven/org.apache.logging.log4j/log4j-core@2.14.0"
        ),
        Component(
            name="jackson-databind", 
            version="2.9.8",
            purl="pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.9.8"
        ),
        Component(
            name="commons-collections",
            version="3.2.1", 
            purl="pkg:maven/commons-collections/commons-collections@3.2.1"
        )
    ]
    
    async with OSVScanner() as scanner:
        print("Testing OSV Scanner...")
        
        for component in test_components:
            print(f"\n=== Testing {component.name}@{component.version} ===")
            print(f"PURL: {component.purl}")
            
            try:
                vulnerabilities = await scanner.scan_component(component)
                print(f"Found {len(vulnerabilities)} vulnerabilities:")
                
                for vuln in vulnerabilities[:3]:  # Show first 3
                    print(f"  - {vuln.id}: {vuln.title}")
                    print(f"    Severity: {vuln.severity}")
                    print(f"    CVSS: {vuln.cvss.base_score if vuln.cvss else 'N/A'}")
                    
            except Exception as e:
                print(f"  ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_osv_scanner())