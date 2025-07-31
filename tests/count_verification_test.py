#!/usr/bin/env python3
"""
Count Verification Test - 5 Minute Controlled Test
Focus on meticulous count tracking with manageable load
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/count_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CountSnapshot:
    timestamp: str
    event: str
    analyses_total: int
    analyses_completed: int
    analyses_failed: int
    analyses_running: int
    components_total: int
    vulnerabilities_total: int
    sboms_total: int
    api_response_time: float

@dataclass
class AnalysisResult:
    analysis_id: str
    project: str
    status: str
    component_count: int
    vulnerability_count: int
    sbom_generated: bool
    duration: float

class CountVerificationTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.duration_seconds = 300  # 5 minutes
        self.max_concurrent = 3  # Very low load for stability
        self.snapshots: List[CountSnapshot] = []
        self.analysis_results: List[AnalysisResult] = []
        
        # Test projects that exist and have vulnerability data
        self.test_projects = [
            # Docker containers (smaller ones first)
            {"location": "alpine:3.18", "type": "docker", "name": "alpine_3_18"},
            {"location": "nginx:latest", "type": "docker", "name": "nginx_latest"},
            {"location": "node:16-alpine", "type": "docker", "name": "node_16_alpine"},
            
            # Source projects that exist
            {"location": "data/sample-java-project", "type": "source", "name": "java_sample"},
            {"location": "data/legacy-php-app", "type": "source", "name": "php_legacy"},
            
            # Binary analysis
            {"location": "data/sample-macos-app/sample-macos-static-app", "type": "binary", "name": "macos_binary"},
            {"location": "/bin/bash", "type": "binary", "name": "bash_binary"},
        ]

    async def make_api_request(self, session: aiohttp.ClientSession, url: str, method: str = "GET", data: Dict = None) -> tuple:
        """Make API request with timing"""
        start_time = time.time()
        try:
            if method == "POST":
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    return result, response.status, time.time() - start_time
            else:
                async with session.get(url) as response:
                    result = await response.json()
                    return result, response.status, time.time() - start_time
        except Exception as e:
            return {"error": str(e)}, 500, time.time() - start_time

    async def capture_count_snapshot(self, session: aiohttp.ClientSession, event: str):
        """Capture detailed count snapshot"""
        start_time = time.time()
        
        try:
            # Parallel API calls for efficiency
            tasks = [
                self.make_api_request(session, f"{self.base_url}/api/v1/analyses"),
                self.make_api_request(session, f"{self.base_url}/api/v1/components/unique"),
                self.make_api_request(session, f"{self.base_url}/api/v1/vulnerabilities?limit=1"),
                self.make_api_request(session, f"{self.base_url}/api/v1/sboms"),
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            api_response_time = time.time() - start_time
            
            # Parse responses
            analyses_total = analyses_completed = analyses_failed = analyses_running = 0
            components_total = vulnerabilities_total = sboms_total = 0
            
            # Analyses data
            if not isinstance(responses[0], Exception) and responses[0][1] == 200:
                data = responses[0][0]
                analyses_total = data.get("total", 0)
                analyses = data.get("analyses", [])
                analyses_completed = len([a for a in analyses if a.get("status") == "completed"])
                analyses_failed = len([a for a in analyses if a.get("status") == "failed"])
                analyses_running = len([a for a in analyses if a.get("status") == "running"])
            
            # Components data
            if not isinstance(responses[1], Exception) and responses[1][1] == 200:
                components_total = responses[1][0].get("total", 0)
            
            # Vulnerabilities data
            if not isinstance(responses[2], Exception) and responses[2][1] == 200:
                vulnerabilities_total = responses[2][0].get("total", 0)
            
            # SBOMs data
            if not isinstance(responses[3], Exception) and responses[3][1] == 200:
                sboms_total = responses[3][0].get("total", 0)
            
            # Create snapshot
            snapshot = CountSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event=event,
                analyses_total=analyses_total,
                analyses_completed=analyses_completed,
                analyses_failed=analyses_failed,
                analyses_running=analyses_running,
                components_total=components_total,
                vulnerabilities_total=vulnerabilities_total,
                sboms_total=sboms_total,
                api_response_time=api_response_time
            )
            
            self.snapshots.append(snapshot)
            
            logger.info(f"📊 {event} | A:{analyses_total}({analyses_completed}✓/{analyses_failed}✗/{analyses_running}⏳) C:{components_total} V:{vulnerabilities_total} S:{sboms_total} ({api_response_time:.2f}s)")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error capturing snapshot: {e}")
            return None

    async def submit_analysis(self, session: aiohttp.ClientSession, project: Dict) -> Optional[str]:
        """Submit analysis request"""
        try:
            data = {
                "location": project["location"],
                "type": project["type"],
                "analyzer": "syft",
                "options": {}
            }
            
            endpoint = f"analyze/{project['type']}"
            result, status, duration = await self.make_api_request(session, f"{self.base_url}/{endpoint}", "POST", data)
            
            if status == 200:
                analysis_id = result.get("analysis_id")
                logger.info(f"✅ Submitted {project['name']}: {analysis_id}")
                return analysis_id
            else:
                logger.error(f"❌ Failed to submit {project['name']}: HTTP {status}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error submitting {project['name']}: {e}")
            return None

    async def wait_for_analysis(self, session: aiohttp.ClientSession, analysis_id: str, project_name: str, timeout: int = 120) -> Optional[AnalysisResult]:
        """Wait for analysis completion and capture results"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result, status, _ = await self.make_api_request(session, f"{self.base_url}/api/v1/analyses/{analysis_id}")
                
                if status == 200:
                    analysis_status = result.get("status")
                    
                    if analysis_status == "completed":
                        duration = time.time() - start_time
                        component_count = result.get("component_count", 0)
                        vulnerability_count = result.get("vulnerability_count", 0)
                        
                        # Check for SBOM
                        sbom_result, sbom_status, _ = await self.make_api_request(session, f"{self.base_url}/api/v1/analyses/{analysis_id}/sbom")
                        sbom_generated = sbom_status == 200
                        
                        analysis_result = AnalysisResult(
                            analysis_id=analysis_id,
                            project=project_name,
                            status=analysis_status,
                            component_count=component_count,
                            vulnerability_count=vulnerability_count,
                            sbom_generated=sbom_generated,
                            duration=duration
                        )
                        
                        self.analysis_results.append(analysis_result)
                        logger.info(f"🎯 {project_name} completed: {component_count} components, {vulnerability_count} vulnerabilities ({duration:.1f}s)")
                        return analysis_result
                        
                    elif analysis_status == "failed":
                        logger.error(f"❌ {project_name} failed")
                        return AnalysisResult(analysis_id, project_name, "failed", 0, 0, False, time.time() - start_time)
                        
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error checking {project_name}: {e}")
                await asyncio.sleep(2)
        
        logger.warning(f"⏰ {project_name} timed out")
        return AnalysisResult(analysis_id, project_name, "timeout", 0, 0, False, timeout)

    async def run_verification_test(self):
        """Run the 5-minute count verification test"""
        logger.info("🚀 STARTING 5-MINUTE COUNT VERIFICATION TEST")
        logger.info("=" * 60)
        logger.info(f"🎯 Max concurrent: {self.max_concurrent}")
        logger.info(f"📋 Test projects: {len(self.test_projects)}")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Initial snapshot
            await self.capture_count_snapshot(session, "TEST_START")
            
            analysis_tasks = []
            submitted_analyses = []
            
            # Submit analyses in controlled batches
            for i, project in enumerate(self.test_projects):
                if i >= self.max_concurrent:
                    break
                    
                analysis_id = await self.submit_analysis(session, project)
                if analysis_id:
                    submitted_analyses.append((analysis_id, project["name"]))
                    
                await asyncio.sleep(1)  # Controlled rate
            
            # Monitor progress with periodic snapshots
            snapshot_interval = 30  # Every 30 seconds
            last_snapshot = time.time()
            
            # Create analysis tasks
            for analysis_id, project_name in submitted_analyses:
                task = asyncio.create_task(self.wait_for_analysis(session, analysis_id, project_name))
                analysis_tasks.append(task)
            
            # Monitor analyses completion
            while analysis_tasks and time.time() - start_time < self.duration_seconds:
                # Periodic snapshots
                if time.time() - last_snapshot >= snapshot_interval:
                    await self.capture_count_snapshot(session, "PROGRESS_CHECK")
                    last_snapshot = time.time()
                
                # Check for completed tasks
                done_tasks = []
                for i, task in enumerate(analysis_tasks):
                    if task.done():
                        done_tasks.append(i)
                
                # Remove completed tasks
                for i in reversed(done_tasks):
                    analysis_tasks.pop(i)
                
                if not analysis_tasks:
                    break
                    
                await asyncio.sleep(5)
            
            # Final snapshot
            final_snapshot = await self.capture_count_snapshot(session, "TEST_END")
            
            # Generate report
            await self.generate_verification_report(final_snapshot)

    async def generate_verification_report(self, final_snapshot: CountSnapshot):
        """Generate detailed verification report"""
        total_duration = time.time() - time.mktime(datetime.fromisoformat(self.snapshots[0].timestamp.replace('Z', '+00:00')).timetuple())
        
        # Calculate metrics
        successful_analyses = len([r for r in self.analysis_results if r.status == "completed"])
        failed_analyses = len([r for r in self.analysis_results if r.status in ["failed", "timeout"]])
        total_components = sum([r.component_count for r in self.analysis_results])
        total_vulnerabilities = sum([r.vulnerability_count for r in self.analysis_results])
        
        report = {
            "test_summary": {
                "test_type": "count_verification_test",
                "duration_seconds": total_duration,
                "max_concurrent_users": self.max_concurrent,
                "projects_tested": len(self.test_projects[:self.max_concurrent])
            },
            "analysis_results": {
                "successful": successful_analyses,
                "failed": failed_analyses,
                "total_submitted": len(self.analysis_results),
                "success_rate": (successful_analyses / len(self.analysis_results)) * 100 if self.analysis_results else 0
            },
            "count_summary": {
                "final_analyses_total": final_snapshot.analyses_total,
                "final_analyses_completed": final_snapshot.analyses_completed,
                "final_analyses_failed": final_snapshot.analyses_failed,
                "final_components_total": final_snapshot.components_total,
                "final_vulnerabilities_total": final_snapshot.vulnerabilities_total,
                "final_sboms_total": final_snapshot.sboms_total,
                "components_found_in_test": total_components,
                "vulnerabilities_found_in_test": total_vulnerabilities
            },
            "detailed_results": [asdict(r) for r in self.analysis_results],
            "count_snapshots": [asdict(s) for s in self.snapshots],
            "test_completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save report
        report_file = f"tests/count_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("🎯 COUNT VERIFICATION TEST COMPLETED")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {total_duration:.1f}s")
        total_analyses = successful_analyses + failed_analyses
        success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
        logger.info(f"📊 Analyses: {successful_analyses}✓/{failed_analyses}✗ ({success_rate:.1f}% success)")
        logger.info(f"🧩 Total Components: {final_snapshot.components_total} (Found in test: {total_components})")
        logger.info(f"🔍 Total Vulnerabilities: {final_snapshot.vulnerabilities_total} (Found in test: {total_vulnerabilities})")
        logger.info(f"📄 SBOMs Generated: {final_snapshot.sboms_total}")
        logger.info(f"📝 Report saved: {report_file}")
        
        # Detailed results
        logger.info("\n📋 DETAILED ANALYSIS RESULTS:")
        for result in self.analysis_results:
            status_emoji = "✅" if result.status == "completed" else "❌"
            logger.info(f"  {status_emoji} {result.project}: {result.component_count}C/{result.vulnerability_count}V ({result.duration:.1f}s)")
        
        return report

async def main():
    """Main function"""
    test = CountVerificationTest()
    await test.run_verification_test()

if __name__ == "__main__":
    asyncio.run(main())