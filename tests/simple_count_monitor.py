#!/usr/bin/env python3
"""
Simple Count Monitor - Track existing data consistency over 5 minutes
Focus on verifying data integrity without adding load
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/count_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CountSnapshot:
    timestamp: str
    analyses_total: int
    analyses_completed: int
    analyses_failed: int
    analyses_running: int
    components_total: int
    vulnerabilities_total: int
    sboms_total: int
    api_response_time: float

@dataclass
class DetailedAnalysis:
    analysis_id: str
    status: str
    component_count: int
    vulnerability_count: int
    created_at: str
    updated_at: str

class SimpleCountMonitor:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.duration_seconds = 300  # 5 minutes
        self.snapshots: List[CountSnapshot] = []
        self.detailed_analyses: Dict[str, DetailedAnalysis] = {}

    async def make_api_request(self, session: aiohttp.ClientSession, url: str) -> tuple:
        """Make API request with timing"""
        start_time = time.time()
        try:
            async with session.get(url) as response:
                result = await response.json()
                return result, response.status, time.time() - start_time
        except Exception as e:
            return {"error": str(e)}, 500, time.time() - start_time

    async def capture_detailed_snapshot(self, session: aiohttp.ClientSession, event: str):
        """Capture comprehensive data snapshot"""
        start_time = time.time()
        
        try:
            # Parallel API calls
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
            analyses_details = []
            
            # Analyses data
            if not isinstance(responses[0], Exception) and responses[0][1] == 200:
                data = responses[0][0]
                analyses_total = data.get("total", 0)
                analyses_details = data.get("analyses", [])
                analyses_completed = len([a for a in analyses_details if a.get("status") == "completed"])
                analyses_failed = len([a for a in analyses_details if a.get("status") == "failed"])
                analyses_running = len([a for a in analyses_details if a.get("status") == "running"])
            
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
            
            # Update detailed analysis tracking
            for analysis in analyses_details:
                analysis_id = analysis.get("analysis_id")
                if analysis_id:
                    detailed = DetailedAnalysis(
                        analysis_id=analysis_id,
                        status=analysis.get("status", "unknown"),
                        component_count=analysis.get("component_count", 0),
                        vulnerability_count=analysis.get("vulnerability_count", 0),
                        created_at=analysis.get("created_at", ""),
                        updated_at=analysis.get("updated_at", "")
                    )
                    self.detailed_analyses[analysis_id] = detailed
            
            logger.info(f"📊 {event} | A:{analyses_total}({analyses_completed}✓/{analyses_failed}✗/{analyses_running}⏳) C:{components_total} V:{vulnerabilities_total} S:{sboms_total} ({api_response_time:.2f}s)")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error capturing snapshot: {e}")
            return None

    async def run_monitoring_test(self):
        """Run the 5-minute count monitoring test"""
        logger.info("🚀 STARTING 5-MINUTE COUNT MONITORING TEST")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {self.duration_seconds}s")
        logger.info(f"📊 Monitoring existing data for consistency")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Initial detailed snapshot
            await self.capture_detailed_snapshot(session, "MONITOR_START")
            
            # Monitor every 30 seconds
            snapshot_interval = 30
            last_snapshot = time.time()
            
            while time.time() - start_time < self.duration_seconds:
                current_time = time.time()
                
                if current_time - last_snapshot >= snapshot_interval:
                    await self.capture_detailed_snapshot(session, "PERIODIC_CHECK")
                    last_snapshot = current_time
                
                await asyncio.sleep(5)  # Check every 5 seconds
            
            # Final snapshot
            final_snapshot = await self.capture_detailed_snapshot(session, "MONITOR_END")
            
            # Generate report
            await self.generate_monitoring_report(final_snapshot)

    async def generate_monitoring_report(self, final_snapshot: CountSnapshot):
        """Generate detailed monitoring report"""
        if not self.snapshots:
            logger.error("No snapshots captured")
            return
            
        first_snapshot = self.snapshots[0]
        total_duration = time.time() - time.mktime(datetime.fromisoformat(first_snapshot.timestamp.replace('Z', '+00:00')).timetuple())
        
        # Calculate changes
        analyses_change = final_snapshot.analyses_total - first_snapshot.analyses_total
        components_change = final_snapshot.components_total - first_snapshot.components_total  
        vulnerabilities_change = final_snapshot.vulnerabilities_total - first_snapshot.vulnerabilities_total
        sboms_change = final_snapshot.sboms_total - first_snapshot.sboms_total
        
        # Find top analyses by components/vulnerabilities
        top_components = sorted(self.detailed_analyses.values(), key=lambda x: x.component_count, reverse=True)[:5]
        top_vulnerabilities = sorted(self.detailed_analyses.values(), key=lambda x: x.vulnerability_count, reverse=True)[:5]
        
        report = {
            "test_summary": {
                "test_type": "count_monitoring_test",
                "duration_seconds": total_duration,
                "snapshots_captured": len(self.snapshots),
                "analyses_tracked": len(self.detailed_analyses)
            },
            "count_changes": {
                "analyses_change": analyses_change,
                "components_change": components_change,
                "vulnerabilities_change": vulnerabilities_change,
                "sboms_change": sboms_change
            },
            "final_counts": {
                "analyses_total": final_snapshot.analyses_total,
                "analyses_completed": final_snapshot.analyses_completed,
                "analyses_failed": final_snapshot.analyses_failed,
                "analyses_running": final_snapshot.analyses_running,
                "components_total": final_snapshot.components_total,
                "vulnerabilities_total": final_snapshot.vulnerabilities_total,
                "sboms_total": final_snapshot.sboms_total
            },
            "top_analyses": {
                "by_components": [asdict(a) for a in top_components],
                "by_vulnerabilities": [asdict(a) for a in top_vulnerabilities]
            },
            "all_snapshots": [asdict(s) for s in self.snapshots],
            "detailed_analyses": [asdict(a) for a in self.detailed_analyses.values()],
            "test_completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save report
        report_file = f"tests/count_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print detailed summary
        logger.info("\n" + "=" * 60)
        logger.info("🎯 COUNT MONITORING TEST COMPLETED")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {total_duration:.1f}s")
        logger.info(f"📸 Snapshots: {len(self.snapshots)}")
        logger.info(f"📊 Analyses Tracked: {len(self.detailed_analyses)}")
        
        logger.info("\n📈 COUNT CHANGES:")
        logger.info(f"  📋 Analyses: {first_snapshot.analyses_total} → {final_snapshot.analyses_total} ({analyses_change:+d})")
        logger.info(f"  🧩 Components: {first_snapshot.components_total} → {final_snapshot.components_total} ({components_change:+d})")
        logger.info(f"  🔍 Vulnerabilities: {first_snapshot.vulnerabilities_total} → {final_snapshot.vulnerabilities_total} ({vulnerabilities_change:+d})")
        logger.info(f"  📄 SBOMs: {first_snapshot.sboms_total} → {final_snapshot.sboms_total} ({sboms_change:+d})")
        
        logger.info(f"\n📊 FINAL STATUS:")
        logger.info(f"  ✅ Completed: {final_snapshot.analyses_completed}")
        logger.info(f"  ❌ Failed: {final_snapshot.analyses_failed}")
        logger.info(f"  ⏳ Running: {final_snapshot.analyses_running}")
        
        logger.info(f"\n🏆 TOP ANALYSES BY COMPONENTS:")
        for i, analysis in enumerate(top_components[:3], 1):
            logger.info(f"  {i}. {analysis.analysis_id}: {analysis.component_count} components, {analysis.vulnerability_count} vulnerabilities")
        
        logger.info(f"\n🚨 TOP ANALYSES BY VULNERABILITIES:")
        for i, analysis in enumerate(top_vulnerabilities[:3], 1):
            logger.info(f"  {i}. {analysis.analysis_id}: {analysis.vulnerability_count} vulnerabilities, {analysis.component_count} components")
        
        logger.info(f"\n📝 Report saved: {report_file}")
        
        return report

async def main():
    """Main function"""
    monitor = SimpleCountMonitor()
    await monitor.run_monitoring_test()

if __name__ == "__main__":
    asyncio.run(main())