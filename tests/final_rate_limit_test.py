#!/usr/bin/env python3
"""
Final comprehensive rate limit test after fixes
"""

import asyncio
import aiohttp
import time
import json

async def final_rate_limit_test():
    """Final test of rate limiting after all fixes"""
    base_url = "http://localhost:8000"
    
    print("=== FINAL RATE LIMIT TEST ===")
    print("Note: Server must be restarted for changes to take effect\n")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Check current state
        print("1. Checking current rate limit state...")
        try:
            async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   Total keys: {data['total_keys']}")
                    if data['rate_limit_status']:
                        for key, info in data['rate_limit_status'].items():
                            print(f"   {key}: active={info['count']}, total={info.get('total_stored', '?')}")
                else:
                    print(f"   Status endpoint returned: {resp.status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Step 2: Clear rate limits
        print("\n2. Clearing rate limits...")
        try:
            async with session.post(f"{base_url}/admin/clear-rate-limits") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ {data}")
                else:
                    print(f"   ❌ Failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        await asyncio.sleep(1)
        
        # Step 3: Verify cleared
        print("\n3. Verifying rate limits are cleared...")
        try:
            async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data['total_keys'] == 0:
                        print("   ✅ Rate limits successfully cleared")
                    else:
                        print(f"   ⚠️  Still have {data['total_keys']} keys")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Step 4: Test with exactly 10 requests
        print("\n4. Making exactly 10 requests (should all succeed)...")
        results = []
        
        for i in range(12):  # Try 12 to verify blocking starts at 11
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
                        print(f"   Request {i+1:2d}: ✅ SUCCESS")
                        results.append("success")
                    elif resp.status == 429:
                        data = await resp.json()
                        print(f"   Request {i+1:2d}: ❌ BLOCKED (count: {data.get('current_count', '?')})")
                        results.append("blocked")
                    else:
                        print(f"   Request {i+1:2d}: ⚠️  Status {resp.status}")
                        results.append("other")
                    
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"   Request {i+1:2d}: ❌ ERROR - {str(e)}")
                results.append("error")
        
        # Count results
        success_count = results.count("success")
        blocked_count = results.count("blocked")
        
        print(f"\nResults: {success_count} successful, {blocked_count} blocked")
        
        # Step 5: Final state check
        print("\n5. Final rate limit state...")
        try:
            async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for key, info in data['rate_limit_status'].items():
                        print(f"   {key}: {info['count']} active requests")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Analysis
        print("\n=== ANALYSIS ===")
        if success_count == 10 and blocked_count == 2:
            print("✅ RATE LIMITING IS WORKING CORRECTLY!")
            print("   - First 10 requests succeeded")
            print("   - Requests 11 and 12 were blocked")
        else:
            print(f"❌ RATE LIMITING ISSUE PERSISTS")
            print(f"   - Expected: 10 successful, 2 blocked")
            print(f"   - Actual: {success_count} successful, {blocked_count} blocked")
            
            if success_count < 10:
                print("\nPossible issues:")
                print("1. Server not restarted after code changes")
                print("2. Multiple middleware calls per request")
                print("3. Background processes making requests")
                print("4. Rate limit key calculation issue")

if __name__ == "__main__":
    asyncio.run(final_rate_limit_test())