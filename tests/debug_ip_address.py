#!/usr/bin/env python3
"""
Debug what IP address is being used for rate limiting
"""

import asyncio
import aiohttp
import socket

async def debug_ip_address():
    """Debug IP address issues"""
    base_url = "http://localhost:8000"
    
    print("=== IP ADDRESS DEBUG ===\n")
    
    # Show local IP addresses
    print("1. Local machine info:")
    print(f"   Hostname: {socket.gethostname()}")
    print(f"   localhost resolves to: {socket.gethostbyname('localhost')}")
    
    async with aiohttp.ClientSession() as session:
        # Try different connection methods
        test_urls = [
            ("http://localhost:8000", "localhost"),
            ("http://127.0.0.1:8000", "127.0.0.1"),
            ("http://[::1]:8000", "IPv6 ::1"),
        ]
        
        for url, desc in test_urls:
            print(f"\n2. Testing with {desc} ({url}):")
            try:
                # Clear rate limits
                async with session.post(f"{url}/admin/clear-rate-limits") as resp:
                    if resp.status == 200:
                        print(f"   ✅ Cleared rate limits")
                
                # Check status
                async with session.get(f"{url}/admin/rate-limit-status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"   Rate limit keys: {list(data['rate_limit_status'].keys())}")
                
                # Make a request
                async with session.post(
                    f"{url}/analyze/docker",
                    json={
                        "location": "alpine:3.18",
                        "type": "docker",
                        "analyzer": "syft",
                        "options": {}
                    }
                ) as resp:
                    if resp.status == 200:
                        print(f"   ✅ Request succeeded")
                    elif resp.status == 429:
                        data = await resp.json()
                        key = data.get('rate_key', 'unknown')
                        count = data.get('current_count', '?')
                        print(f"   ❌ Rate limited - key: {key}, count: {count}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_ip_address())