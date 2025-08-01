#!/usr/bin/env python3
"""
Debug rate limiting to understand the issue
"""

import asyncio
import aiohttp
import time
import json

async def debug_rate_limit():
    """Debug the rate limiting behavior"""
    base_url = "http://localhost:8000"
    
    print("=== RATE LIMIT DEBUG ===\n")
    
    async with aiohttp.ClientSession() as session:
        # First check what's in the rate limit state
        print("1. Testing with debug headers to trace requests:\n")
        
        for i in range(6):
            start = time.time()
            headers = {
                "X-Debug-Request-Id": f"test-{i+1}",
                "X-Real-IP": "127.0.0.1"  # Ensure consistent IP
            }
            
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
                    status = resp.status
                    data = await resp.json()
                    
                    if status == 200:
                        print(f"Request {i+1}: ✅ SUCCESS")
                    else:
                        print(f"Request {i+1}: ❌ BLOCKED - {data}")
                    
                    # Check response headers for any rate limit info
                    if 'X-RateLimit-Limit' in resp.headers:
                        print(f"  Rate Limit Headers: {dict(resp.headers)}")
                    
            except Exception as e:
                print(f"Request {i+1}: ❌ ERROR - {str(e)}")
            
            # Small delay to ensure clean request separation
            await asyncio.sleep(0.5)
        
        print("\n2. Checking if middleware is being called multiple times:")
        print("   Making a single request and checking server logs...\n")
        
        # Make request with unique identifier
        unique_id = f"single-test-{int(time.time())}"
        async with session.post(
            f"{base_url}/analyze/docker",
            json={
                "location": "alpine:3.18",
                "type": "docker",
                "analyzer": "syft",
                "options": {"debug_id": unique_id}
            }
        ) as resp:
            print(f"Single request status: {resp.status}")
            if resp.status != 200:
                data = await resp.json()
                print(f"Response: {data}")

if __name__ == "__main__":
    asyncio.run(debug_rate_limit())