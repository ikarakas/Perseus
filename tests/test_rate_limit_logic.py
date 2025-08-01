#!/usr/bin/env python3
"""
Test to verify rate limiting logic
"""

import asyncio
import aiohttp
import time
import json

async def test_rate_limit():
    """Test the rate limiting behavior"""
    base_url = "http://localhost:8000"
    
    print("=== RATE LIMIT LOGIC TEST ===\n")
    
    # Test scenario: Send requests and observe rate limiting behavior
    async with aiohttp.ClientSession() as session:
        
        # First, let's see current rate limit state
        print("1. Testing rapid burst of requests:")
        
        results = []
        for i in range(15):
            start = time.time()
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
                    status = resp.status
                    data = await resp.json()
                    elapsed = time.time() - start
                    
                    if status == 200:
                        print(f"   Request {i+1}: ✅ SUCCESS (took {elapsed:.3f}s)")
                    else:
                        print(f"   Request {i+1}: ❌ RATE LIMITED - {data.get('detail', 'Unknown error')}")
                    
                    results.append((i+1, status, elapsed))
                    
            except Exception as e:
                print(f"   Request {i+1}: ❌ ERROR - {str(e)}")
                results.append((i+1, 0, 0))
        
        # Count successful vs rate limited
        successful = sum(1 for _, status, _ in results if status == 200)
        rate_limited = sum(1 for _, status, _ in results if status == 429)
        
        print(f"\nResults: {successful} successful, {rate_limited} rate limited out of 15 requests")
        
        # Wait for rate limit window to reset
        print("\n2. Waiting 65 seconds for rate limit window to reset...")
        await asyncio.sleep(65)
        
        # Try again after window reset
        print("\n3. Testing after rate limit window reset:")
        
        for i in range(5):
            start = time.time()
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
                    status = resp.status
                    data = await resp.json()
                    elapsed = time.time() - start
                    
                    if status == 200:
                        print(f"   Request {i+1}: ✅ SUCCESS (took {elapsed:.3f}s)")
                    else:
                        print(f"   Request {i+1}: ❌ RATE LIMITED - {data.get('detail', 'Unknown error')}")
                        
            except Exception as e:
                print(f"   Request {i+1}: ❌ ERROR - {str(e)}")
        
        # Test spreading requests over time
        print("\n4. Testing requests spread over time (1 request every 7 seconds):")
        
        for i in range(10):
            start = time.time()
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
                    status = resp.status
                    data = await resp.json()
                    elapsed = time.time() - start
                    
                    if status == 200:
                        print(f"   Request {i+1}: ✅ SUCCESS (took {elapsed:.3f}s)")
                    else:
                        print(f"   Request {i+1}: ❌ RATE LIMITED - {data.get('detail', 'Unknown error')}")
                        
            except Exception as e:
                print(f"   Request {i+1}: ❌ ERROR - {str(e)}")
            
            if i < 9:  # Don't wait after last request
                print("   Waiting 7 seconds...")
                await asyncio.sleep(7)
        
        print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_rate_limit())