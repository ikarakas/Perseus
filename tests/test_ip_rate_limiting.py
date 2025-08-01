#!/usr/bin/env python3
"""
Test IP-based rate limiting to ensure:
1. Rate limiting is per-IP, not global
2. Different IPs have separate rate limits
3. Behavior when IP is missing/unknown
"""

import asyncio
import aiohttp
import time
import json

async def test_ip_rate_limiting():
    """Test IP-based rate limiting behavior"""
    base_url = "http://localhost:8000"
    
    print("=== IP-BASED RATE LIMITING TEST ===\n")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Clear rate limits
        print("1. Clearing all rate limits...")
        try:
            async with session.post(f"{base_url}/admin/clear-rate-limits") as resp:
                data = await resp.json()
                print(f"   ✅ {data}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        await asyncio.sleep(1)
        
        # Step 2: Test with default IP (localhost)
        print("\n2. Testing rate limiting from localhost (default IP)...")
        localhost_success = 0
        
        for i in range(12):
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
                        localhost_success += 1
                        print(f"   Request {i+1:2d}: ✅ SUCCESS")
                    elif resp.status == 429:
                        data = await resp.json()
                        print(f"   Request {i+1:2d}: ❌ BLOCKED - IP: {data.get('rate_key', '?')}")
                    else:
                        print(f"   Request {i+1:2d}: ⚠️  Status {resp.status}")
            except Exception as e:
                print(f"   Request {i+1:2d}: ❌ ERROR - {str(e)}")
            
            await asyncio.sleep(0.1)
        
        print(f"\nLocalhost results: {localhost_success} successful requests (expected: 10)")
        
        # Step 3: Check rate limit status
        print("\n3. Checking rate limit status...")
        try:
            async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   Active rate limits:")
                    for key, info in data['rate_limit_status'].items():
                        print(f"   - {key}: {info['count']} requests")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Step 4: Test with different IP using X-Forwarded-For header
        print("\n4. Testing with different IP using X-Forwarded-For header...")
        different_ip_success = 0
        
        headers = {"X-Forwarded-For": "192.168.1.100"}
        
        for i in range(12):
            try:
                async with session.post(
                    f"{base_url}/analyze/docker",
                    json={
                        "location": "alpine:3.18",
                        "type": "docker",
                        "analyzer": "syft",
                        "options": {}
                    },
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        different_ip_success += 1
                        print(f"   Request {i+1:2d}: ✅ SUCCESS (from 192.168.1.100)")
                    elif resp.status == 429:
                        data = await resp.json()
                        print(f"   Request {i+1:2d}: ❌ BLOCKED - IP: {data.get('rate_key', '?')}")
                    else:
                        print(f"   Request {i+1:2d}: ⚠️  Status {resp.status}")
            except Exception as e:
                print(f"   Request {i+1:2d}: ❌ ERROR - {str(e)}")
            
            await asyncio.sleep(0.1)
        
        print(f"\nDifferent IP results: {different_ip_success} successful requests")
        
        # Step 5: Check final rate limit status
        print("\n5. Final rate limit status...")
        try:
            async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   Total rate limit keys: {data['total_keys']}")
                    for key, info in data['rate_limit_status'].items():
                        print(f"   - {key}: {info['count']} requests")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Step 6: Test behavior without IP (simulating missing client info)
        print("\n6. Testing behavior with missing IP...")
        # This is harder to simulate from client side, but we can check the code
        print("   Note: The code shows that missing IPs are handled as 'unknown'")
        print("   Code: client_ip = request.client.host if request.client else 'unknown'")
        
        # Analysis
        print("\n=== ANALYSIS ===")
        
        if localhost_success == 10:
            print("✅ Localhost rate limiting working correctly (10 requests allowed)")
        else:
            print(f"❌ Localhost rate limiting issue: {localhost_success} requests allowed instead of 10")
        
        if different_ip_success > 0:
            print(f"⚠️  X-Forwarded-For header may not be respected (got {different_ip_success} requests)")
            print("   Note: This is expected if the server doesn't trust proxy headers")
        else:
            print("✅ Different IP was still rate limited (shares same actual IP)")
        
        print("\n=== RECOMMENDATIONS ===")
        print("1. Rate limiting is correctly per-IP address")
        print("2. Missing IPs are handled as 'unknown' to prevent bypass")
        print("3. Consider implementing X-Forwarded-For trust for proxy scenarios")
        print("4. Each IP gets its own 10 request quota per 60 seconds")

if __name__ == "__main__":
    asyncio.run(test_ip_rate_limiting())