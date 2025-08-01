#!/usr/bin/env python3
"""
Test the fixed rate limiting
"""

import asyncio
import aiohttp
import time
import json

async def test_fixed_rate_limit():
    """Test rate limiting after fix"""
    base_url = "http://localhost:8000"
    
    print("=== TESTING FIXED RATE LIMIT ===\n")
    
    # Wait a bit to ensure clean state
    print("Waiting 65 seconds to ensure clean rate limit window...")
    await asyncio.sleep(65)
    
    async with aiohttp.ClientSession() as session:
        print("\n1. Testing exactly 10 requests (should all succeed):")
        
        successful = 0
        blocked = 0
        
        for i in range(12):  # Try 12 to see when blocking starts
            try:
                async with session.post(
                    f"{base_url}/analyze/docker",
                    json={
                        "location": "alpine:3.18",
                        "type": "docker",
                        "analyzer": "syft",
                        "options": {}
                    }
                ) as resp:
                    if resp.status == 200:
                        successful += 1
                        print(f"   Request {i+1:2d}: ✅ SUCCESS")
                    elif resp.status == 429:
                        blocked += 1
                        data = await resp.json()
                        current_count = data.get('current_count', '?')
                        print(f"   Request {i+1:2d}: ❌ BLOCKED (count: {current_count})")
                    else:
                        print(f"   Request {i+1:2d}: ⚠️  Status {resp.status}")
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"   Request {i+1:2d}: ❌ ERROR - {str(e)}")
        
        print(f"\nResult: {successful} successful, {blocked} blocked")
        print(f"Expected: 10 successful, 2 blocked")
        
        if successful == 10 and blocked == 2:
            print("✅ RATE LIMITING FIXED!")
        else:
            print("❌ RATE LIMITING STILL HAS ISSUES")
            
            # Try to get debug info
            try:
                async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"\nDebug info: {json.dumps(data, indent=2)}")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(test_fixed_rate_limit())