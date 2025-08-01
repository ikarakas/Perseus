#!/usr/bin/env python3
"""
Comprehensive test to diagnose rate limiting issue
"""

import asyncio
import aiohttp
import time
import json

async def test_comprehensive_rate_limit():
    """Comprehensive rate limit test"""
    base_url = "http://localhost:8000"
    
    print("=== COMPREHENSIVE RATE LIMIT TEST ===\n")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Clear rate limits
        print("1. Clearing rate limits...")
        try:
            async with session.post(f"{base_url}/admin/clear-rate-limits") as resp:
                if resp.status == 200:
                    print("   ✅ Rate limits cleared")
                else:
                    print(f"   ❌ Failed to clear: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        await asyncio.sleep(1)
        
        # Step 2: Check initial state
        print("\n2. Checking initial rate limit state...")
        try:
            async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   Total keys: {data['total_keys']}")
                    if data['rate_limit_status']:
                        print(f"   Active limits: {json.dumps(data['rate_limit_status'], indent=4)}")
                    else:
                        print("   ✅ No active rate limits")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Step 3: Make exactly 10 requests
        print("\n3. Making exactly 10 requests to /analyze/docker...")
        results = []
        
        for i in range(10):
            start = time.time()
            try:
                async with session.post(
                    f"{base_url}/analyze/docker",
                    json={
                        "location": "alpine:3.18",
                        "type": "docker",
                        "analyzer": "syft",
                        "options": {"test_num": i+1}
                    }
                ) as resp:
                    elapsed = time.time() - start
                    status = resp.status
                    
                    if status == 200:
                        print(f"   Request {i+1:2d}: ✅ SUCCESS ({elapsed:.3f}s)")
                        results.append(("success", i+1))
                    elif status == 429:
                        data = await resp.json()
                        count = data.get('current_count', '?')
                        key = data.get('rate_key', '?')
                        print(f"   Request {i+1:2d}: ❌ BLOCKED - count: {count}, key: {key}")
                        results.append(("blocked", i+1))
                    else:
                        print(f"   Request {i+1:2d}: ⚠️  Status {status}")
                        results.append(("other", i+1))
                    
                    # Small delay between requests
                    await asyncio.sleep(0.2)
                    
            except Exception as e:
                print(f"   Request {i+1:2d}: ❌ ERROR - {str(e)}")
                results.append(("error", i+1))
        
        # Count results
        successful = sum(1 for r in results if r[0] == "success")
        blocked = sum(1 for r in results if r[0] == "blocked")
        
        print(f"\nResults: {successful} successful, {blocked} blocked out of 10")
        
        # Step 4: Check rate limit state after requests
        print("\n4. Checking rate limit state after requests...")
        try:
            async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   Current state: {json.dumps(data, indent=4)}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Step 5: Try one more request
        print("\n5. Trying one more request (should be blocked)...")
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
                    print("   ⚠️  Request succeeded (should have been blocked!)")
                elif resp.status == 429:
                    data = await resp.json()
                    print(f"   ✅ Request blocked as expected - count: {data.get('current_count', '?')}")
                else:
                    print(f"   ⚠️  Unexpected status: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Analysis
        print("\n=== ANALYSIS ===")
        if successful == 10 and blocked == 0:
            print("✅ Rate limiting is working correctly!")
        else:
            print(f"❌ Rate limiting issue: Only {successful} requests succeeded instead of 10")
            print("\nPossible causes:")
            print("- Middleware being called multiple times per request")
            print("- OPTIONS/preflight requests being counted")
            print("- Previous requests still in the rate limit window")
            print("- Rate limit key not properly isolated")

if __name__ == "__main__":
    asyncio.run(test_comprehensive_rate_limit())