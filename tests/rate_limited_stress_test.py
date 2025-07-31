#!/usr/bin/env python3
"""
Rate-Limited Stress Test for SBOM Platform
Tests concurrent requests while respecting rate limits
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any
import sys

class RateLimitedStressTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        # Rate limit: 10 requests per 60 seconds, so we'll pace at 1 request per 6 seconds
        self.request_delay = 6.5  # Add buffer
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, data: Dict[str, Any], test_name: str) -> Dict[str, Any]:
        """Make a single analysis request"""
        start_time = time.time()
        try:
            async with session.post(f"{self.base_url}/{endpoint}", json=data) as response:
                response_data = await response.json()
                duration = time.time() - start_time
                
                result = {
                    "test_name": test_name,
                    "status_code": response.status,
                    "duration": duration,
                    "success": response.status == 200,
                    "analysis_id": response_data.get("analysis_id"),
                    "error": None
                }
                
                if not result["success"]:
                    result["error"] = response_data
                    
                return result
                
        except Exception as e:
            duration = time.time() - start_time
            return {
                "test_name": test_name,
                "status_code": 0,
                "duration": duration,
                "success": False,
                "analysis_id": None,
                "error": str(e)
            }
    
    async def check_analysis_completion(self, session: aiohttp.ClientSession, analysis_id: str) -> Dict[str, Any]:
        """Check completion status of a single analysis"""
        try:
            async with session.get(f"{self.base_url}/api/v1/analyses/{analysis_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "analysis_id": analysis_id,
                        "status": data.get("status"),
                        "component_count": data.get("component_count", 0),
                        "vulnerability_count": data.get("vulnerability_count", 0)
                    }
        except Exception as e:
            print(f"Error checking analysis {analysis_id}: {e}")
        
        return None
    
    async def run_rate_limited_test(self, total_requests: int = 8):
        """Run rate-limited stress test"""
        print(f"🚀 Starting rate-limited stress test with {total_requests} requests...")
        print(f"⏱️  Request delay: {self.request_delay}s between requests")
        
        # Define test cases
        test_cases = [
            {
                "endpoint": "analyze/docker",
                "data": {
                    "location": "alpine:3.18",
                    "type": "docker",
                    "analyzer": "syft",
                    "options": {}
                },
                "name": "docker_alpine"
            },
            {
                "endpoint": "analyze/docker",
                "data": {
                    "location": "nginx:latest",
                    "type": "docker",
                    "analyzer": "syft",
                    "options": {}
                },
                "name": "docker_nginx"
            },
            {
                "endpoint": "analyze/docker",
                "data": {
                    "location": "node:16-alpine",
                    "type": "docker",
                    "analyzer": "syft",
                    "options": {}
                },
                "name": "docker_node"
            },
            {
                "endpoint": "analyze/docker",
                "data": {
                    "location": "redis:7-alpine",
                    "type": "docker",
                    "analyzer": "syft",
                    "options": {}
                },
                "name": "docker_redis"
            }
        ]
        
        start_time = time.time()
        analysis_ids = []
        
        async with aiohttp.ClientSession() as session:
            # Submit requests with rate limiting
            print("📤 Submitting requests with rate limiting...")
            for i in range(total_requests):
                test_case = test_cases[i % len(test_cases)]
                
                result = await self.make_request(
                    session, 
                    test_case["endpoint"], 
                    test_case["data"], 
                    f"{test_case['name']}_{i+1}"
                )
                
                if result["success"]:
                    print(f"✅ {i+1}/{total_requests} - {result['test_name']}: {result['analysis_id']}")
                    analysis_ids.append(result['analysis_id'])
                else:
                    print(f"❌ {i+1}/{total_requests} - {result['test_name']}: {result['error']}")
                
                self.results.append(result)
                
                # Rate limit delay (except for last request)
                if i < total_requests - 1:
                    await asyncio.sleep(self.request_delay)
            
            request_duration = time.time() - start_time
            
            # Calculate results
            successful_requests = len([r for r in self.results if r["success"]])
            failed_requests = len([r for r in self.results if not r["success"]])
            
            print(f"\n📊 Request Results:")
            print(f"   ✅ Successful: {successful_requests}/{total_requests}")
            print(f"   ❌ Failed: {failed_requests}/{total_requests}")
            print(f"   ⏱️  Total Request Time: {request_duration:.2f}s")
            
            # Wait for analyses to complete
            print("\n⏳ Waiting for analyses to complete...")
            await asyncio.sleep(30)  # Give analyses time to complete
            
            # Check completion status
            completed = 0
            failed = 0
            total_components = 0
            total_vulnerabilities = 0
            
            for analysis_id in analysis_ids:
                status = await self.check_analysis_completion(session, analysis_id)
                if status:
                    if status["status"] == "completed":
                        completed += 1
                        total_components += status["component_count"]
                        total_vulnerabilities += status["vulnerability_count"]
                    elif status["status"] == "failed":
                        failed += 1
            
            total_duration = time.time() - start_time
            
            print(f"\n🎯 Final Results:")
            print(f"   📊 Analyses Completed: {completed}/{len(analysis_ids)}")
            print(f"   ❌ Analyses Failed: {failed}/{len(analysis_ids)}")
            print(f"   🧩 Total Components Found: {total_components}")
            print(f"   🔍 Total Vulnerabilities Found: {total_vulnerabilities}")
            print(f"   ⏱️  Total Duration: {total_duration:.2f}s")
            
            # Success criteria
            success_rate = (successful_requests / total_requests) * 100
            completion_rate = (completed / len(analysis_ids)) * 100 if analysis_ids else 0
            
            print(f"\n📈 Performance Metrics:")
            print(f"   🎯 Request Success Rate: {success_rate:.1f}%")
            print(f"   ✅ Analysis Completion Rate: {completion_rate:.1f}%")
            print(f"   ⚡ Avg Time per Request: {request_duration/total_requests:.3f}s")
            
            if success_rate >= 95 and completion_rate >= 95:
                print("\n✅ RATE-LIMITED STRESS TEST PASSED!")
                return True
            else:
                print("\n❌ RATE-LIMITED STRESS TEST FAILED!")
                return False

async def main():
    """Main function"""
    total_requests = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    
    stress_test = RateLimitedStressTest()
    success = await stress_test.run_rate_limited_test(total_requests)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())