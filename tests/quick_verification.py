#!/usr/bin/env python3
"""
Quick verification to confirm fixes
"""

import asyncio
import aiohttp
import json

async def verify_data_integrity():
    print("🔍 Quick Data Integrity Verification")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Check vulnerabilities
        print("\n📊 Vulnerability Analysis:")
        async with session.get("http://localhost:8000/api/v1/vulnerabilities") as resp:
            if resp.status == 200:
                data = await resp.json()
                total_vulns = data.get("total", 0)
                
                orphan_count = 0
                with_components = 0
                
                for vuln in data.get("vulnerabilities", []):
                    if vuln.get("is_orphan", False):
                        orphan_count += 1
                    else:
                        with_components += 1
                
                print(f"  Total vulnerabilities: {total_vulns}")
                print(f"  With components: {with_components}")
                print(f"  Orphan vulnerabilities: {orphan_count}")
                
                if orphan_count == 0:
                    print("  ✅ NO ORPHAN VULNERABILITIES - Data integrity good!")
                else:
                    print(f"  ⚠️  {orphan_count} orphan vulnerabilities found")
        
        # Check SBOMs
        print("\n📋 SBOM Analysis:")
        async with session.get("http://localhost:8000/api/v1/sboms") as resp:
            if resp.status == 200:
                data = await resp.json()
                sbom_count = data.get("total", 0)
                print(f"  Total SBOMs: {sbom_count}")
                
                if sbom_count >= 20:
                    print("  ✅ SBOM generation working well!")
                else:
                    print(f"  ⚠️  Only {sbom_count} SBOMs found")
        
        # Check components
        print("\n🧩 Component Analysis:")
        async with session.get("http://localhost:8000/api/v1/components/unique") as resp:
            if resp.status == 200:
                data = await resp.json()
                unique_components = data.get("total", 0)
                print(f"  Unique components: {unique_components}")
                
                if unique_components > 300:
                    print("  ✅ Component discovery working well!")
        
        # Check analyses
        print("\n📈 Analysis Summary:")
        async with session.get("http://localhost:8000/api/v1/analyses") as resp:
            if resp.status == 200:
                data = await resp.json()
                total_analyses = data.get("total", 0)
                completed = len([a for a in data.get("analyses", []) if a.get("status") == "completed"])
                
                print(f"  Total analyses: {total_analyses}")
                print(f"  Completed: {completed}")
                
                if completed == total_analyses and completed > 0:
                    print("  ✅ All analyses completed successfully!")
    
    print("\n" + "=" * 50)
    print("🎯 VERIFICATION COMPLETE")

async def main():
    await verify_data_integrity()

if __name__ == "__main__":
    asyncio.run(main())