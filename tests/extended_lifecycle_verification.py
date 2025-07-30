#!/usr/bin/env python3
"""
Extended Perseus Verification with Meticulous Count Tracking
Tracks components, vulnerabilities, and orphan objects throughout entire lifecycle
"""

import asyncio
import aiohttp
import json
import uuid
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

@dataclass
class CountSnapshot:
    timestamp: str
    event: str
    analyses_total: int
    analyses_completed: int
    components_total: int
    components_unique: int
    vulnerabilities_total: int
    vulnerabilities_active: int
    sboms_total: int
    orphan_vulnerabilities: int
    components_with_vulns: int

@dataclass 
class LifecycleEvent:
    timestamp: str
    user_id: str
    event_type: str  # analysis_start, analysis_complete, sbom_generate, etc.
    analysis_id: Optional[str]
    details: Dict

class ExtendedLifecycleVerification:
    def __init__(self, base_url: str = "http://localhost:8000", max_users: int = 15):
        self.base_url = base_url
        self.max_users = max_users
        self.test_start_time = datetime.now(timezone.utc)
        
        # Lifecycle tracking
        self.count_snapshots: List[CountSnapshot] = []
        self.lifecycle_events: List[LifecycleEvent] = []
        self.lock = threading.Lock()
        
        # Data consistency tracking
        self.analysis_tracking: Dict[str, Dict] = {}  # analysis_id -> {user, type, components, vulns}
        self.component_evolution: Dict[str, List[int]] = {}  # timestamp -> count
        self.vulnerability_evolution: Dict[str, List[int]] = {}  # timestamp -> count
        self.orphan_detection_log: List[Dict] = []
        
        # Test scenarios
        self.test_projects = [
            {"location": "data/vulnerable-java-app", "type": "source", "language": "java"},
            {"location": "nginx:latest", "type": "docker", "image": "nginx:latest"}, 
            {"location": "data/go-binary", "type": "binary"},
            {"location": "/etc", "type": "os"},
            {"location": "data/python-project", "type": "source", "language": "python"},
            {"location": "redis:7-alpine", "type": "docker", "image": "redis:7-alpine"},
            {"location": "ubuntu:22.04", "type": "docker", "image": "ubuntu:22.04"},
        ]
        
        # User profiles with specific behaviors
        self.user_profiles = {
            "repeat_analyzer": {"repeats": True, "sbom_frequency": 0.8},
            "explorer": {"repeats": False, "sbom_frequency": 0.6, "search_frequency": 0.7},
            "production_user": {"repeats": True, "sbom_frequency": 1.0, "vulnerability_focus": True},
            "developer": {"repeats": False, "sbom_frequency": 0.4},
            "security_auditor": {"repeats": True, "vulnerability_focus": True, "sbom_frequency": 0.9}
        }

    async def capture_count_snapshot(self, session: aiohttp.ClientSession, event: str):
        """Capture detailed count snapshot at a specific point in time"""
        try:
            # Get all counts in parallel
            tasks = [
                session.get(f"{self.base_url}/api/v1/analyses"),
                session.get(f"{self.base_url}/api/v1/components/unique"),
                session.get(f"{self.base_url}/api/v1/vulnerabilities?limit=1"),
                session.get(f"{self.base_url}/api/v1/sboms"),
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Parse responses safely
            analyses_total = analyses_completed = 0
            components_total = components_unique = 0
            vulnerabilities_total = vulnerabilities_active = 0
            sboms_total = 0
            orphan_vulnerabilities = 0
            components_with_vulns = 0
            
            # Analyses
            if not isinstance(responses[0], Exception) and responses[0].status == 200:
                data = await responses[0].json()
                analyses_total = data.get("total", 0)
                analyses_completed = len([a for a in data.get("analyses", []) if a.get("status") == "completed"])
            
            # Components
            if not isinstance(responses[1], Exception) and responses[1].status == 200:
                data = await responses[1].json()
                components_unique = data.get("total", 0)
                
                # Get detailed component stats
                async with session.get(f"{self.base_url}/api/v1/components?limit=1") as comp_resp:
                    if comp_resp.status == 200:
                        comp_data = await comp_resp.json()
                        components_total = comp_data.get("total", 0)
            
            # Vulnerabilities
            if not isinstance(responses[2], Exception) and responses[2].status == 200:
                vuln_data = await responses[2].json()
                vulnerabilities_total = vuln_data.get("total", 0)
                vulnerabilities_active = vulnerabilities_total  # Assume all are active for now
                
                # Check for orphan vulnerabilities using the correct API format
                async with session.get(f"{self.base_url}/api/v1/vulnerabilities") as all_vulns:
                    if all_vulns.status == 200:
                        all_vuln_data = await all_vulns.json()
                        # Count orphan vulns using the is_orphan field from API
                        for vuln in all_vuln_data.get("vulnerabilities", []):
                            if vuln.get("is_orphan", False):
                                orphan_vulnerabilities += 1
            
            # SBOMs
            if not isinstance(responses[3], Exception) and responses[3].status == 200:
                sbom_data = await responses[3].json()
                sboms_total = sbom_data.get("total", 0)
            
            # Create snapshot
            snapshot = CountSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event=event,
                analyses_total=analyses_total,
                analyses_completed=analyses_completed,
                components_total=components_total,
                components_unique=components_unique,
                vulnerabilities_total=vulnerabilities_total,
                vulnerabilities_active=vulnerabilities_active,
                sboms_total=sboms_total,
                orphan_vulnerabilities=orphan_vulnerabilities,
                components_with_vulns=components_with_vulns
            )
            
            with self.lock:
                self.count_snapshots.append(snapshot)
                
                # Track evolution
                timestamp_key = snapshot.timestamp
                self.component_evolution[timestamp_key] = components_unique
                self.vulnerability_evolution[timestamp_key] = vulnerabilities_total
                
                print(f"📊 Count Snapshot - {event}")
                print(f"   Analyses: {analyses_total} total, {analyses_completed} completed")
                print(f"   Components: {components_total} total, {components_unique} unique")
                print(f"   Vulnerabilities: {vulnerabilities_total} total, {orphan_vulnerabilities} orphan")
                print(f"   SBOMs: {sboms_total}")
                
        except Exception as e:
            print(f"⚠️  Count snapshot failed for {event}: {e}")

    async def log_lifecycle_event(self, user_id: str, event_type: str, analysis_id: str = None, **details):
        """Log a lifecycle event with timestamp"""
        event = LifecycleEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            event_type=event_type,
            analysis_id=analysis_id,
            details=details
        )
        
        with self.lock:
            self.lifecycle_events.append(event)

    async def simulate_user_lifecycle(self, session: aiohttp.ClientSession, user_id: str, profile: Dict):
        """Simulate a complete user lifecycle with detailed tracking"""
        await self.log_lifecycle_event(user_id, "user_start")
        
        completed_analyses = []
        analysis_attempts = 0
        max_analyses = random.randint(2, 4) if profile.get("repeats") else random.randint(1, 2)
        
        for attempt in range(max_analyses):
            analysis_attempts += 1
            
            # Choose project (repeat analyzer might repeat previous ones)
            if profile.get("repeats") and completed_analyses and random.random() < 0.4:
                # Repeat previous analysis to test count consistency
                previous_analysis = random.choice(completed_analyses)
                project = previous_analysis["project"]
                await self.log_lifecycle_event(user_id, "analysis_repeat_start", details={"project": project})
            else:
                project = random.choice(self.test_projects)
                await self.log_lifecycle_event(user_id, "analysis_new_start", details={"project": project})
            
            # Submit analysis
            analysis_id = await self.submit_analysis(session, user_id, project)
            if not analysis_id:
                continue
                
            # Track analysis in our system
            with self.lock:
                self.analysis_tracking[analysis_id] = {
                    "user": user_id,
                    "project": project,
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "components": 0,
                    "vulnerabilities": 0
                }
            
            # Wait for completion with periodic count tracking
            completed = await self.wait_for_analysis_with_tracking(session, analysis_id, user_id)
            if completed:
                completed_analyses.append({"analysis_id": analysis_id, "project": project})
                
                # Update our tracking
                await self.update_analysis_tracking(session, analysis_id)
                
                # Generate SBOM if user profile suggests it
                if random.random() < profile.get("sbom_frequency", 0.5):
                    await self.generate_sbom_with_tracking(session, user_id, analysis_id)
                
                # Perform vulnerability scan if security focused
                if profile.get("vulnerability_focus") and random.random() < 0.8:
                    await self.perform_vulnerability_scan(session, user_id, analysis_id)
                
                # Random wait between activities
                await asyncio.sleep(random.uniform(1, 3))
            
            # Take snapshot after each major activity
            await self.capture_count_snapshot(session, f"user_{user_id}_analysis_{attempt+1}_complete")
        
        await self.log_lifecycle_event(user_id, "user_complete", details={"analyses_completed": len(completed_analyses)})

    async def submit_analysis(self, session: aiohttp.ClientSession, user_id: str, project: Dict) -> Optional[str]:
        """Submit analysis and return analysis_id"""
        try:
            endpoint = f"/analyze/{project['type']}"
            
            async with session.post(f"{self.base_url}{endpoint}", json=project) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    analysis_id = result["analysis_id"]
                    await self.log_lifecycle_event(user_id, "analysis_submitted", analysis_id, project=project)
                    return analysis_id
                else:
                    await self.log_lifecycle_event(user_id, "analysis_submit_failed", details={"status": resp.status, "project": project})
                    return None
        except Exception as e:
            await self.log_lifecycle_event(user_id, "analysis_submit_error", details={"error": str(e)})
            return None

    async def wait_for_analysis_with_tracking(self, session: aiohttp.ClientSession, analysis_id: str, user_id: str) -> bool:
        """Wait for analysis completion while taking periodic snapshots"""
        max_wait = 60  # 60 seconds max
        check_interval = 5  # Every 5 seconds
        
        for check in range(max_wait // check_interval):
            await asyncio.sleep(check_interval)
            
            try:
                async with session.get(f"{self.base_url}/analyze/{analysis_id}/status") as resp:
                    if resp.status == 200:
                        status_data = await resp.json()
                        status = status_data.get("status")
                        
                        if status == "completed":
                            await self.log_lifecycle_event(user_id, "analysis_completed", analysis_id)
                            await self.capture_count_snapshot(session, f"analysis_{analysis_id}_completed")
                            return True
                        elif status == "failed":
                            await self.log_lifecycle_event(user_id, "analysis_failed", analysis_id)
                            return False
                        
                        # Still running, take a tracking snapshot
                        if check % 2 == 0:  # Every 10 seconds
                            await self.capture_count_snapshot(session, f"analysis_{analysis_id}_progress_check_{check}")
                            
            except Exception as e:
                await self.log_lifecycle_event(user_id, "analysis_status_error", analysis_id, error=str(e))
        
        await self.log_lifecycle_event(user_id, "analysis_timeout", analysis_id)
        return False

    async def update_analysis_tracking(self, session: aiohttp.ClientSession, analysis_id: str):
        """Update our tracking with actual analysis results"""
        try:
            async with session.get(f"{self.base_url}/analyze/{analysis_id}/results") as resp:
                if resp.status == 200:
                    results = await resp.json()
                    components = results.get("components", [])
                    vulnerabilities = results.get("vulnerabilities", [])
                    
                    with self.lock:
                        if analysis_id in self.analysis_tracking:
                            self.analysis_tracking[analysis_id].update({
                                "components": len(components),
                                "vulnerabilities": len(vulnerabilities),
                                "completion_time": datetime.now(timezone.utc).isoformat()
                            })
        except Exception as e:
            print(f"⚠️  Failed to update tracking for {analysis_id}: {e}")

    async def generate_sbom_with_tracking(self, session: aiohttp.ClientSession, user_id: str, analysis_id: str):
        """Generate SBOM with detailed tracking"""
        try:
            sbom_format = random.choice(["spdx", "cyclonedx"])
            request_data = {
                "analysis_ids": [analysis_id],
                "format": sbom_format,
                "include_vulnerabilities": True
            }
            
            await self.log_lifecycle_event(user_id, "sbom_generation_start", analysis_id, format=sbom_format)
            
            async with session.post(f"{self.base_url}/sbom/generate", json=request_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    sbom_id = result["sbom_id"]
                    await self.log_lifecycle_event(user_id, "sbom_generated", analysis_id, sbom_id=sbom_id, format=sbom_format)
                    
                    # Wait a moment then take a snapshot
                    await asyncio.sleep(2)
                    await self.capture_count_snapshot(session, f"sbom_{sbom_id}_generated")
                else:
                    await self.log_lifecycle_event(user_id, "sbom_generation_failed", analysis_id, status=resp.status)
                    
        except Exception as e:
            await self.log_lifecycle_event(user_id, "sbom_generation_error", analysis_id, error=str(e))

    async def perform_vulnerability_scan(self, session: aiohttp.ClientSession, user_id: str, analysis_id: str):
        """Perform detailed vulnerability scanning"""
        try:
            await self.log_lifecycle_event(user_id, "vulnerability_scan_start", analysis_id)
            
            # Get vulnerabilities for this analysis
            async with session.get(f"{self.base_url}/analyze/{analysis_id}/vulnerabilities") as resp:
                if resp.status == 200:
                    vulns = await resp.json()
                    vuln_count = len(vulns.get("vulnerabilities", []))
                    await self.log_lifecycle_event(user_id, "vulnerability_scan_complete", analysis_id, count=vuln_count)
                else:
                    await self.log_lifecycle_event(user_id, "vulnerability_scan_failed", analysis_id, status=resp.status)
                    
        except Exception as e:
            await self.log_lifecycle_event(user_id, "vulnerability_scan_error", analysis_id, error=str(e))

    async def detect_orphan_objects(self, session: aiohttp.ClientSession):
        """Detect and log orphan objects throughout the test"""
        try:
            # Get all vulnerabilities and check for orphans
            async with session.get(f"{self.base_url}/api/v1/vulnerabilities") as resp:
                if resp.status == 200:
                    vuln_data = await resp.json()
                    orphan_count = 0
                    
                    for vuln in vuln_data.get("vulnerabilities", []):
                        if vuln.get("is_orphan", False):
                            orphan_count += 1
                    
                    if orphan_count > 0:
                        orphan_log = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "orphan_vulnerabilities": orphan_count,
                            "total_vulnerabilities": len(vuln_data.get("vulnerabilities", []))
                        }
                        
                        with self.lock:
                            self.orphan_detection_log.append(orphan_log)
                        
                        print(f"🚨 Detected {orphan_count} orphan vulnerabilities")
                        
        except Exception as e:
            print(f"⚠️  Orphan detection failed: {e}")

    async def run_extended_test(self):
        """Run the extended lifecycle verification test"""
        print("🚀 Starting Extended Perseus Lifecycle Verification")
        print("=" * 60)
        
        # Initial clean state snapshot
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(total=60, connect=15)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Baseline snapshot
            await self.capture_count_snapshot(session, "test_start_baseline")
            
            # Create user tasks
            user_tasks = []
            for i in range(self.max_users):
                profile_name = random.choice(list(self.user_profiles.keys()))
                profile = self.user_profiles[profile_name]
                user_id = f"{profile_name}_{i+1}"
                
                task = asyncio.create_task(self.simulate_user_lifecycle(session, user_id, profile))
                user_tasks.append(task)
            
            # Start background orphan detection
            orphan_task = asyncio.create_task(self.periodic_orphan_detection(session))
            
            # Wait for all users to complete
            await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Final comprehensive snapshot
            await self.capture_count_snapshot(session, "test_complete_final")
            
            # Cancel background task
            orphan_task.cancel()
            
            # Generate comprehensive report
            await self.generate_lifecycle_report()

    async def periodic_orphan_detection(self, session: aiohttp.ClientSession):
        """Periodically check for orphan objects"""
        try:
            while True:
                await asyncio.sleep(10)  # Every 10 seconds
                await self.detect_orphan_objects(session)
        except asyncio.CancelledError:
            pass

    async def generate_lifecycle_report(self):
        """Generate comprehensive lifecycle tracking report"""
        test_end_time = datetime.now(timezone.utc)
        duration = (test_end_time - self.test_start_time).total_seconds()
        
        report = {
            "test_metadata": {
                "start_time": self.test_start_time.isoformat(),
                "end_time": test_end_time.isoformat(),
                "duration_seconds": duration,
                "total_users": self.max_users,
                "base_url": self.base_url
            },
            "count_evolution": {
                "snapshots": [asdict(s) for s in self.count_snapshots],
                "component_evolution": self.component_evolution,
                "vulnerability_evolution": self.vulnerability_evolution
            },
            "lifecycle_events": [asdict(e) for e in self.lifecycle_events],
            "analysis_tracking": self.analysis_tracking,
            "orphan_detection": self.orphan_detection_log,
            "consistency_analysis": self.analyze_count_consistency(),
            "lifecycle_summary": self.generate_lifecycle_summary()
        }
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"tests/extended_lifecycle_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Extended Lifecycle Report saved: {report_file}")
        self.print_summary_report(report)
        
        return report

    def analyze_count_consistency(self) -> Dict:
        """Analyze count consistency throughout the test"""
        consistency_issues = []
        component_changes = []
        vulnerability_changes = []
        
        for i in range(1, len(self.count_snapshots)):
            prev = self.count_snapshots[i-1]
            curr = self.count_snapshots[i]
            
            # Check for unexpected decreases
            if curr.components_unique < prev.components_unique:
                consistency_issues.append({
                    "timestamp": curr.timestamp,
                    "event": curr.event,
                    "issue": "component_count_decreased",
                    "previous": prev.components_unique,
                    "current": curr.components_unique
                })
            
            if curr.vulnerabilities_total < prev.vulnerabilities_total:
                consistency_issues.append({
                    "timestamp": curr.timestamp,
                    "event": curr.event,
                    "issue": "vulnerability_count_decreased",
                    "previous": prev.vulnerabilities_total,
                    "current": curr.vulnerabilities_total
                })
            
            # Track changes
            component_changes.append({
                "timestamp": curr.timestamp,
                "change": curr.components_unique - prev.components_unique
            })
            
            vulnerability_changes.append({
                "timestamp": curr.timestamp,
                "change": curr.vulnerabilities_total - prev.vulnerabilities_total
            })
        
        return {
            "consistency_issues": consistency_issues,
            "component_changes": component_changes,
            "vulnerability_changes": vulnerability_changes,
            "total_issues": len(consistency_issues)
        }

    def generate_lifecycle_summary(self) -> Dict:
        """Generate summary of lifecycle events"""
        event_counts = {}
        user_activity = {}
        
        for event in self.lifecycle_events:
            # Count event types
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Track user activity
            user_id = event.user_id
            if user_id not in user_activity:
                user_activity[user_id] = {"events": 0, "analyses": 0, "sboms": 0}
            
            user_activity[user_id]["events"] += 1
            
            if "analysis_completed" in event_type:
                user_activity[user_id]["analyses"] += 1
            if "sbom_generated" in event_type:
                user_activity[user_id]["sboms"] += 1
        
        return {
            "event_counts": event_counts,
            "user_activity": user_activity,
            "total_events": len(self.lifecycle_events)
        }

    def print_summary_report(self, report: Dict):
        """Print a concise summary report"""
        print("\n" + "="*60)
        print("📊 EXTENDED LIFECYCLE VERIFICATION RESULTS")
        print("="*60)
        
        metadata = report["test_metadata"]
        print(f"Duration: {metadata['duration_seconds']:.1f} seconds")
        print(f"Users: {metadata['total_users']}")
        
        if self.count_snapshots:
            final_snapshot = self.count_snapshots[-1]
            print(f"\n📈 Final Counts:")
            print(f"  Analyses: {final_snapshot.analyses_total} total, {final_snapshot.analyses_completed} completed")
            print(f"  Components: {final_snapshot.components_total} total, {final_snapshot.components_unique} unique")
            print(f"  Vulnerabilities: {final_snapshot.vulnerabilities_total} total, {final_snapshot.orphan_vulnerabilities} orphan")
            print(f"  SBOMs: {final_snapshot.sboms_total}")
        
        consistency = report["consistency_analysis"]
        print(f"\n🔍 Consistency Analysis:")
        print(f"  Issues detected: {consistency['total_issues']}")
        
        if consistency["total_issues"] == 0:
            print("  ✅ No count consistency issues detected!")
        else:
            print("  ⚠️  Count consistency issues found:")
            for issue in consistency["consistency_issues"][:3]:  # Show first 3
                print(f"    - {issue['issue']} at {issue['event']}")
        
        orphan_count = len(report["orphan_detection"])
        print(f"\n🚨 Orphan Detection:")
        print(f"  Orphan checks performed: {orphan_count}")
        if orphan_count > 0:
            latest_orphan = report["orphan_detection"][-1]
            print(f"  Latest: {latest_orphan['orphan_vulnerabilities']} orphan vulnerabilities")
        
        lifecycle = report["lifecycle_summary"]
        print(f"\n🔄 Lifecycle Summary:")
        print(f"  Total events: {lifecycle['total_events']}")
        print(f"  Event types: {len(lifecycle['event_counts'])}")
        
        completed_analyses = lifecycle["event_counts"].get("analysis_completed", 0)
        generated_sboms = lifecycle["event_counts"].get("sbom_generated", 0)
        print(f"  Completed analyses: {completed_analyses}")
        print(f"  Generated SBOMs: {generated_sboms}")
        
        print("\n" + "="*60)

async def main():
    verification = ExtendedLifecycleVerification(max_users=15)
    await verification.run_extended_test()

if __name__ == "__main__":
    asyncio.run(main())