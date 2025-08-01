#!/usr/bin/env python3
"""
Test a single request to see how many times middleware is called
"""

import asyncio
import aiohttp
import time
import uuid

async def test_single_request():
    """Test single request to debug middleware calls"""
    base_url = "http://localhost:8000"
    
    print("=== SINGLE REQUEST TEST ===\n")
    
    async with aiohttp.ClientSession() as session:
        # Clear rate limits first
        print("1. Clearing rate limits...")
        await session.post(f"{base_url}/admin/clear-rate-limits")
        await asyncio.sleep(1)
        
        # Check initial state
        print("\n2. Initial rate limit state:")
        async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   Keys: {data['total_keys']}")
                print(f"   Status: {data['rate_limit_status']}")
        
        # Make a single request with unique ID
        unique_id = str(uuid.uuid4())
        print(f"\n3. Making ONE request with ID: {unique_id}")
        
        headers = {
            "X-Request-ID": unique_id,
            "User-Agent": "TestClient/1.0"
        }
        
        async with session.post(
            f"{base_url}/analyze/docker", 
            json={
                "location": "alpine:3.18",
                "type": "docker", 
                "analyzer": "syft",
                "options": {"request_id": unique_id}
            },
            headers=headers
        ) as resp:
            print(f"   Response status: {resp.status}")
            if resp.status == 429:
                data = await resp.json()
                print(f"   Rate limit data: {data}")
        
        # Check rate limit state after ONE request
        print("\n4. Rate limit state after ONE request:")
        async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   Keys: {data['total_keys']}")
                for key, info in data['rate_limit_status'].items():
                    print(f"   {key}: count={info['count']}")
                    if 'all_timestamps' in info:
                        print(f"     Timestamps: {info['all_timestamps']}")
        
        print("\n=== ANALYSIS ===")
        print("If count > 1 after a single request, middleware is being called multiple times")

if __name__ == "__main__":
    asyncio.run(test_single_request())