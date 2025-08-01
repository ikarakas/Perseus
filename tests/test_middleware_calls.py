#!/usr/bin/env python3
"""
Test to check if middleware is being called multiple times
"""

import asyncio
import aiohttp
import time
import json
import uuid

async def test_middleware_calls():
    """Test if middleware is called multiple times per request"""
    base_url = "http://localhost:8000"
    
    print("=== MIDDLEWARE CALL TEST ===\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Simple POST request
        print("1. Testing simple POST request:")
        
        request_id = str(uuid.uuid4())
        headers = {
            "X-Request-ID": request_id,
            "Content-Type": "application/json"
        }
        
        try:
            async with session.post(
                f"{base_url}/analyze/docker",
                json={
                    "location": "alpine:3.18",
                    "type": "docker",
                    "analyzer": "syft",
                    "options": {"request_id": request_id}
                },
                headers=headers,
                allow_redirects=False  # Prevent any redirects
            ) as resp:
                print(f"   Status: {resp.status}")
                print(f"   Headers: {dict(resp.headers)}")
                data = await resp.json()
                if resp.status == 429:
                    print(f"   Rate limit info: {data}")
                
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        print("\n2. Testing OPTIONS request (CORS preflight):")
        
        # Test if OPTIONS requests are counted
        try:
            async with session.options(
                f"{base_url}/analyze/docker",
                headers={"Origin": "http://localhost:3000"}
            ) as resp:
                print(f"   OPTIONS Status: {resp.status}")
        except Exception as e:
            print(f"   OPTIONS Error: {str(e)}")
        
        # Now try POST again
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
                print(f"   POST after OPTIONS Status: {resp.status}")
                if resp.status == 429:
                    data = await resp.json()
                    print(f"   Current count: {data.get('current_count', 'N/A')}")
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        print("\n3. Testing with explicit localhost IP:")
        
        # Test if 127.0.0.1 and localhost are treated differently
        localhost_url = "http://127.0.0.1:8000"
        try:
            async with session.post(
                f"{localhost_url}/analyze/docker",
                json={
                    "location": "alpine:3.18",
                    "type": "docker",
                    "analyzer": "syft",
                    "options": {}
                }
            ) as resp:
                print(f"   Status with 127.0.0.1: {resp.status}")
                if resp.status == 429:
                    data = await resp.json()
                    print(f"   Rate limit details: {data}")
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_middleware_calls())