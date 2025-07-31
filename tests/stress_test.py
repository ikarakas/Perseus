#!/usr/bin/env python3
"""
Stress test script for SBOM Platform
Tests concurrent requests across different analysis types
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any
import sys

class StressTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
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
    
    async def check_analysis_completion(self, session: aiohttp.ClientSession, analysis_ids: List[str]) -> Dict[str, Any]:
        """Check completion status of all analyses"""
        completed = 0
        failed = 0
        total_components = 0
        total_vulnerabilities = 0
        
        try:
            async with session.get(f"{self.base_url}/api/v1/analyses") as response:
                if response.status == 200:
                    data = await response.json()
                    analyses = data.get("analyses", [])
                    
                    for analysis in analyses:
                        if analysis["analysis_id"] in analysis_ids:
                            if analysis["status"] == "completed":
                                completed += 1
                                total_components += analysis.get("component_count", 0)
                                total_vulnerabilities += analysis.get("vulnerability_count", 0)
                            elif analysis["status"] == "failed":
                                failed += 1
                                
        except Exception as e:
            print(f"Error checking analysis completion: {e}")
        
        return {
            "completed": completed,
            "failed": failed,
            "total": len(analysis_ids),
            "total_components": total_components,
            "total_vulnerabilities": total_vulnerabilities
        }
    
    async def run_concurrent_test(self, num_concurrent: int = 10):
        """Run concurrent stress test"""
        print(f"🚀 Starting stress test with {num_concurrent} concurrent requests...")
        
        # Define test cases
        test_cases = [
            {
                "endpoint": "analyze/binary",
                "data": {
                    "location": "/app/data/sample-macos-app/sample-macos-static-app",
                    "type": "binary",
                    "analyzer": "syft",
                    "options": {}
                },
                "name": "binary_analysis"
            },
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
                "endpoint": "analyze/source",
                "data": {
                    "location": "/app/data/sample-java-project",
                    "type": "source",
                    "analyzer": "syft",
                    "options": {}
                },
                "name": "source_java"
            },
            {
                "endpoint": "analyze/docker",
                "data": {
                    "location": "mysql:8.0",
                    "type": "docker",
                    "analyzer": "syft",
                    "options": {}
                },
                "name": "docker_mysql"
            }
        ]
        
        start_time = time.time()
        analysis_ids = []
        
        async with aiohttp.ClientSession() as session:
            # Create tasks for concurrent requests
            tasks = []
            for i in range(num_concurrent):
                test_case = test_cases[i % len(test_cases)]
                task = self.make_request(
                    session, 
                    test_case["endpoint"], 
                    test_case["data"], 
                    f"{test_case['name']}_{i+1}"
                )
                tasks.append(task)
            
            # Execute all requests concurrently
            print("📤 Sending concurrent requests...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_requests = 0
            failed_requests = 0
            
            for result in results:
                if isinstance(result, Exception):
                    failed_requests += 1
                    print(f"❌ Exception: {result}")
                elif result["success"]:
                    successful_requests += 1
                    if result["analysis_id"]:
                        analysis_ids.append(result["analysis_id"])
                else:
                    failed_requests += 1
                    print(f"❌ Failed request: {result['test_name']} - {result['error']}")
            
            request_duration = time.time() - start_time
            
            print(f"📊 Request Results:")
            print(f"   ✅ Successful: {successful_requests}/{num_concurrent}")
            print(f"   ❌ Failed: {failed_requests}/{num_concurrent}")
            print(f"   ⏱️  Request Time: {request_duration:.2f}s")
            
            # Wait for analyses to complete
            print("⏳ Waiting for analyses to complete...")
            max_wait_time = 120  # 2 minutes
            wait_start = time.time()
            
            while time.time() - wait_start < max_wait_time:
                completion_status = await self.check_analysis_completion(session, analysis_ids)
                
                if completion_status["completed"] + completion_status["failed"] >= len(analysis_ids):
                    break
                    
                await asyncio.sleep(2)
            
            # Final status check
            final_status = await self.check_analysis_completion(session, analysis_ids)
            total_duration = time.time() - start_time
            
            print(f"\n🎯 Final Results:")
            print(f"   📊 Analyses Completed: {final_status['completed']}/{final_status['total']}")
            print(f"   ❌ Analyses Failed: {final_status['failed']}/{final_status['total']}")
            print(f"   🧩 Total Components Found: {final_status['total_components']}")
            print(f"   🔍 Total Vulnerabilities Found: {final_status['total_vulnerabilities']}")
            print(f"   ⏱️  Total Duration: {total_duration:.2f}s")
            
            # Success criteria
            success_rate = (successful_requests / num_concurrent) * 100
            completion_rate = (final_status['completed'] / final_status['total']) * 100 if final_status['total'] > 0 else 0
            
            print(f"\n📈 Performance Metrics:")
            print(f"   🎯 Request Success Rate: {success_rate:.1f}%")
            print(f"   ✅ Analysis Completion Rate: {completion_rate:.1f}%")
            print(f"   ⚡ Avg Request Time: {request_duration/num_concurrent:.3f}s")
            
            if success_rate >= 95 and completion_rate >= 95:
                print("✅ STRESS TEST PASSED!")
                return True
            else:
                print("❌ STRESS TEST FAILED!")
                return False

async def main():
    """Main function"""
    num_concurrent = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    
    stress_test = StressTest()
    success = await stress_test.run_concurrent_test(num_concurrent)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())