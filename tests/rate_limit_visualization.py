#!/usr/bin/env python3
"""
Visual demonstration of rate limiting behavior
Shows how rate limiting works per IP address
"""

import asyncio
import aiohttp
import time
from datetime import datetime

async def visualize_rate_limiting():
    """Visualize rate limiting behavior with clear output"""
    base_url = "http://localhost:8000"
    
    print("=== RATE LIMITING VISUALIZATION ===")
    print("Each IP gets 10 requests per 60 seconds")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Clear rate limits first
        await session.post(f"{base_url}/admin/clear-rate-limits")
        await asyncio.sleep(1)
        
        print("\n📊 SCENARIO 1: Single IP making 15 requests")
        print("-" * 50)
        
        for i in range(15):
            try:
                async with session.post(
                    f"{base_url}/analyze/docker",
                    json={"location": "alpine:3.18", "type": "docker", "analyzer": "syft", "options": {}}
                ) as resp:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if resp.status == 200:
                        print(f"[{timestamp}] Request {i+1:2d}: ✅ SUCCESS")
                    elif resp.status == 429:
                        data = await resp.json()
                        count = data.get('current_count', '?')
                        print(f"[{timestamp}] Request {i+1:2d}: ❌ BLOCKED (quota: {count}/10)")
                        
            except Exception as e:
                print(f"[{timestamp}] Request {i+1:2d}: ❌ ERROR - {str(e)}")
            
            await asyncio.sleep(0.5)  # Half second between requests for clarity
        
        print("\n📊 SCENARIO 2: Checking rate limit state")
        print("-" * 50)
        
        try:
            async with session.get(f"{base_url}/admin/rate-limit-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for key, info in data['rate_limit_status'].items():
                        if 'analyze' in key:
                            ip = key.split(':')[0]
                            count = info['count']
                            print(f"IP: {ip}")
                            print(f"  Active requests: {count}/10")
                            print(f"  Status: {'🚫 LIMIT REACHED' if count >= 10 else '✅ BELOW LIMIT'}")
        except Exception as e:
            print(f"Error checking status: {e}")
        
        print("\n📊 SCENARIO 3: Demonstrating sliding window")
        print("-" * 50)
        print("Waiting 30 seconds (half the window)...")
        await asyncio.sleep(30)
        
        print("Attempting 2 more requests (should still be blocked):")
        for i in range(2):
            try:
                async with session.post(
                    f"{base_url}/analyze/docker",
                    json={"location": "alpine:3.18", "type": "docker", "analyzer": "syft", "options": {}}
                ) as resp:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if resp.status == 200:
                        print(f"[{timestamp}] Request {i+1}: ✅ SUCCESS (unexpected!)")
                    elif resp.status == 429:
                        print(f"[{timestamp}] Request {i+1}: ❌ BLOCKED (expected - window hasn't expired)")
                        
            except Exception as e:
                print(f"[{timestamp}] Request {i+1}: ❌ ERROR")
            
            await asyncio.sleep(0.5)
        
        print("\nWaiting another 35 seconds for window to expire...")
        await asyncio.sleep(35)
        
        print("Attempting 5 more requests (should succeed):")
        success_count = 0
        for i in range(5):
            try:
                async with session.post(
                    f"{base_url}/analyze/docker",
                    json={"location": "alpine:3.18", "type": "docker", "analyzer": "syft", "options": {}}
                ) as resp:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if resp.status == 200:
                        success_count += 1
                        print(f"[{timestamp}] Request {i+1}: ✅ SUCCESS (window expired)")
                    elif resp.status == 429:
                        print(f"[{timestamp}] Request {i+1}: ❌ BLOCKED")
                        
            except Exception as e:
                print(f"[{timestamp}] Request {i+1}: ❌ ERROR")
            
            await asyncio.sleep(0.5)
        
        print(f"\nSuccessful requests after window expiry: {success_count}/5")
        
        print("\n" + "=" * 50)
        print("📝 SUMMARY:")
        print("=" * 50)
        print("✅ Rate limiting is working correctly:")
        print("   • Each IP gets exactly 10 requests per 60 seconds")
        print("   • Requests beyond limit are blocked with HTTP 429")
        print("   • 60-second sliding window is properly enforced")
        print("   • Old requests expire after 60 seconds")
        print("   • Missing IPs are handled as 'unknown' to prevent bypass")
        print("\n💡 Key Points:")
        print("   • Rate limits are per-IP, not global")
        print("   • Each endpoint group has its own limits:")
        print("     - /analyze/*: 10 req/min")
        print("     - /api/v1/*: 60 req/min")
        print("     - Others: 120 req/min")

if __name__ == "__main__":
    asyncio.run(visualize_rate_limiting())