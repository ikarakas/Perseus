#!/usr/bin/env python3
"""
Isolated test to verify rate limiting logic with clean state
"""

import asyncio
import aiohttp
import time
import json

async def test_clean_rate_limit():
    """Test rate limiting with fresh start"""
    base_url = "http://localhost:8000"
    
    print("=== ISOLATED RATE LIMIT TEST ===")
    print("Testing with a unique endpoint to avoid previous request history\n")
    
    # Use a timestamp to make requests unique
    test_id = int(time.time())
    
    async with aiohttp.ClientSession() as session:
        # First, make a request to a different endpoint to check clean state
        print("1. Making request to health endpoint first (different rate limit):")
        async with session.get(f"{base_url}/health") as resp:
            print(f"   Health check: {resp.status}")
        
        print("\n2. Testing exactly 10 requests to analyze endpoint:")
        
        successful = 0
        for i in range(12):  # Try 12 to see when it starts blocking
            start = time.time()
            try:
                # Add a unique parameter to avoid caching
                async with session.post(
                    f"{base_url}/analyze/docker",
                    json={
                        "location": "alpine:3.18",
                        "type": "docker",
                        "analyzer": "syft",
                        "options": {"test_id": f"{test_id}_{i}"}
                    }
                ) as resp:
                    status = resp.status
                    data = await resp.json()
                    
                    if status == 200:
                        successful += 1
                        print(f"   Request {i+1:2d}: ✅ SUCCESS")
                    else:
                        print(f"   Request {i+1:2d}: ❌ BLOCKED - {data.get('detail', 'Unknown')}")
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"   Request {i+1:2d}: ❌ ERROR - {str(e)}")
        
        print(f"\nExpected: 10 successful requests")
        print(f"Actual: {successful} successful requests")
        
        # Test the sliding window behavior
        print("\n3. Testing sliding window (waiting for old requests to expire):")
        print("   Waiting 30 seconds...")
        await asyncio.sleep(30)
        
        print("   Making 5 more requests (should have 5 slots available from expired requests):")
        newly_successful = 0
        for i in range(6):  # Try 6 to see if we get 5
            try:
                async with session.post(
                    f"{base_url}/analyze/docker",
                    json={
                        "location": "alpine:3.18",
                        "type": "docker",
                        "analyzer": "syft",
                        "options": {"test_id": f"{test_id}_phase2_{i}"}
                    }
                ) as resp:
                    if resp.status == 200:
                        newly_successful += 1
                        print(f"   Request {i+1}: ✅ SUCCESS")
                    else:
                        data = await resp.json()
                        print(f"   Request {i+1}: ❌ BLOCKED - {data.get('detail', 'Unknown')}")
                    
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"   Request {i+1}: ❌ ERROR - {str(e)}")
        
        print(f"\nExpected ~5 successful (half the window expired)")
        print(f"Actual: {newly_successful} successful")
        
        print("\n=== ANALYSIS ===")
        if successful == 10:
            print("✅ Rate limiting is working correctly for initial burst")
        else:
            print(f"❌ Rate limiting issue: Only {successful} requests succeeded instead of 10")
        
        print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_clean_rate_limit())