#!/usr/bin/env python3
"""
Comprehensive 1-Hour Perseus Stress Test
20 concurrent users, extensive error capture, meticulous count tracking
"""

import asyncio
import aiohttp
import json
import uuid
import random
import time
import traceback
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import threading
from pathlib import Path
import sys
import os

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/stress_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ErrorCapture:
    timestamp: str
    user_id: str
    operation: str
    error_type: str
    error_message: str
    http_status: Optional[int]
    analysis_id: Optional[str]
    stack_trace: Optional[str]

@dataclass
class CountSnapshot:
    timestamp: str
    event: str
    analyses_total: int
    analyses_completed: int
    analyses_failed: int
    components_total: int
    components_unique: int
    vulnerabilities_total: int
    vulnerabilities_active: int
    sboms_total: int
    orphan_vulnerabilities: int
    components_with_vulns: int
    api_response_time: float

@dataclass 
class UserMetrics:
    user_id: str
    user_type: str
    start_time: str
    end_time: Optional[str]
    total_operations: int
    successful_operations: int
    failed_operations: int
    analyses_submitted: int
    analyses_completed: int
    sboms_generated: int
    vulnerability_scans: int
    component_searches: int
    total_errors: int
    avg_response_time: float

@dataclass
class SystemHealth:
    timestamp: str
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    api_availability: bool
    database_connectivity: bool
    concurrent_connections: int

class OneHourStressTest:
    def __init__(self, base_url: str = "http://localhost:8000", max_users: int = 20, duration_hours: float = 1.0):
        self.base_url = base_url
        self.max_users = max_users
        self.duration_seconds = duration_hours * 3600  # 1 hour = 3600 seconds
        self.test_start_time = datetime.now(timezone.utc)
        
        # Comprehensive tracking
        self.count_snapshots: List[CountSnapshot] = []
        self.error_log: List[ErrorCapture] = []
        self.user_metrics: Dict[str, UserMetrics] = {}
        self.system_health_log: List[SystemHealth] = []
        self.lock = threading.Lock()
        
        # Test statistics
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.total_response_time = 0.0
        
        # Extensive test projects with vulnerabilities
        self.test_projects = [
            # Existing vulnerable projects
            {"location": "data/vulnerable-java-app", "type": "source", "language": "java", "expected_vulns": "high"},
            {"location": "data/vulnerable-java-web", "type": "source", "language": "java", "expected_vulns": "critical"},
            
            # New vulnerable projects
            {"location": "data/vulnerable-python-app", "type": "source", "language": "python", "expected_vulns": "high"},
            {"location": "data/vulnerable-node-app", "type": "source", "language": "javascript", "expected_vulns": "critical"},
            {"location": "data/vulnerable-go-app", "type": "source", "language": "go", "expected_vulns": "medium"},
            {"location": "data/vulnerable-rust-app", "type": "source", "language": "rust", "expected_vulns": "medium"},
            {"location": "data/legacy-php-app", "type": "source", "language": "php", "expected_vulns": "critical"},
            
            # Container images with known vulnerabilities
            {"location": "nginx:1.15", "type": "docker", "image": "nginx:1.15", "expected_vulns": "medium"},
            {"location": "node:10.15-alpine", "type": "docker", "image": "node:10.15-alpine", "expected_vulns": "high"},
            {"location": "python:3.6", "type": "docker", "image": "python:3.6", "expected_vulns": "high"},
            {"location": "ubuntu:18.04", "type": "docker", "image": "ubuntu:18.04", "expected_vulns": "medium"},
            {"location": "redis:5.0", "type": "docker", "image": "redis:5.0", "expected_vulns": "medium"},
            {"location": "mysql:5.7", "type": "docker", "image": "mysql:5.7", "expected_vulns": "high"},
            
            # OS and binary analysis
            {"location": "/usr/bin", "type": "os", "expected_vulns": "low"},
            {"location": "/etc", "type": "os", "expected_vulns": "low"},
            {"location": "data/sample-macos-app/sample-macos-static-app", "type": "binary", "expected_vulns": "low"},
        ]
        
        # Diverse user behavior profiles for realistic testing
        self.user_profiles = {
            "heavy_analyzer": {"analyses_per_hour": 12, "sbom_frequency": 0.9, "repeat_rate": 0.6, "vulnerability_focus": True},
            "security_auditor": {"analyses_per_hour": 8, "sbom_frequency": 1.0, "repeat_rate": 0.8, "vulnerability_focus": True, "search_frequency": 0.9},
            "developer": {"analyses_per_hour": 6, "sbom_frequency": 0.4, "repeat_rate": 0.3, "vulnerability_focus": False},
            "devops_engineer": {"analyses_per_hour": 10, "sbom_frequency": 0.8, "repeat_rate": 0.5, "vulnerability_focus": False},
            "compliance_officer": {"analyses_per_hour": 4, "sbom_frequency": 0.9, "repeat_rate": 0.7, "vulnerability_focus": True, "search_frequency": 0.8},
            "casual_user": {"analyses_per_hour": 3, "sbom_frequency": 0.2, "repeat_rate": 0.2, "vulnerability_focus": False},
            "power_user": {"analyses_per_hour": 15, "sbom_frequency": 0.7, "repeat_rate": 0.4, "vulnerability_focus": False, "search_frequency": 0.6},
        }

    async def capture_error(self, user_id: str, operation: str, error: Exception, 
                          http_status: Optional[int] = None, analysis_id: Optional[str] = None):
        """Capture comprehensive error information"""
        error_capture = ErrorCapture(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            http_status=http_status,
            analysis_id=analysis_id,
            stack_trace=traceback.format_exc()
        )
        
        with self.lock:
            self.error_log.append(error_capture)
            self.failed_operations += 1
        
        logger.error(f"Error captured for {user_id} in {operation}: {error}")

    async def capture_detailed_count_snapshot(self, session: aiohttp.ClientSession, event: str):
        """Capture extremely detailed count snapshot with performance metrics"""
        start_time = time.time()
        
        try:
            # Parallel API calls for speed
            tasks = [
                self.timed_api_call(session, f"{self.base_url}/api/v1/analyses"),
                self.timed_api_call(session, f"{self.base_url}/api/v1/components/unique"),
                self.timed_api_call(session, f"{self.base_url}/api/v1/vulnerabilities?limit=1"),
                self.timed_api_call(session, f"{self.base_url}/api/v1/sboms"),
                self.timed_api_call(session, f"{self.base_url}/api/v1/components?limit=1"),
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            api_response_time = time.time() - start_time
            
            # Initialize counters
            analyses_total = analyses_completed = analyses_failed = 0
            components_total = components_unique = 0
            vulnerabilities_total = vulnerabilities_active = 0
            sboms_total = 0
            orphan_vulnerabilities = 0
            components_with_vulns = 0
            
            # Parse analyses data
            if not isinstance(responses[0], Exception) and responses[0][1] == 200:
                data = responses[0][0]
                analyses_total = data.get("total", 0)
                analyses = data.get("analyses", [])
                analyses_completed = len([a for a in analyses if a.get("status") == "completed"])
                analyses_failed = len([a for a in analyses if a.get("status") == "failed"])
            
            # Parse components data
            if not isinstance(responses[1], Exception) and responses[1][1] == 200:
                components_unique = responses[1][0].get("total", 0)
            
            if not isinstance(responses[4], Exception) and responses[4][1] == 200:
                components_total = responses[4][0].get("total", 0)
            
            # Parse vulnerabilities data
            if not isinstance(responses[2], Exception) and responses[2][1] == 200:
                vuln_data = responses[2][0]
                vulnerabilities_total = vuln_data.get("total", 0)
                vulnerabilities_active = vulnerabilities_total
                
                # Get detailed vulnerability info for orphan detection
                async with session.get(f"{self.base_url}/api/v1/vulnerabilities") as all_vulns:
                    if all_vulns.status == 200:
                        all_vuln_data = await all_vulns.json()
                        for vuln in all_vuln_data.get("vulnerabilities", []):
                            if vuln.get("is_orphan", False):
                                orphan_vulnerabilities += 1
                            if vuln.get("component_count", 0) > 0:
                                components_with_vulns += 1
            
            # Parse SBOMs data
            if not isinstance(responses[3], Exception) and responses[3][1] == 200:
                sboms_total = responses[3][0].get("total", 0)
            
            # Create comprehensive snapshot
            snapshot = CountSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event=event,
                analyses_total=analyses_total,
                analyses_completed=analyses_completed,
                analyses_failed=analyses_failed,
                components_total=components_total,
                components_unique=components_unique,
                vulnerabilities_total=vulnerabilities_total,
                vulnerabilities_active=vulnerabilities_active,
                sboms_total=sboms_total,
                orphan_vulnerabilities=orphan_vulnerabilities,
                components_with_vulns=components_with_vulns,
                api_response_time=api_response_time
            )
            
            with self.lock:
                self.count_snapshots.append(snapshot)
                self.total_response_time += api_response_time
            
            logger.info(f"📊 Snapshot [{event}] - A:{analyses_total}({analyses_completed}✓/{analyses_failed}✗) "
                       f"C:{components_unique} V:{vulnerabilities_total}({orphan_vulnerabilities}⚠️) "
                       f"S:{sboms_total} ({api_response_time:.2f}s)")
                
        except Exception as e:
            await self.capture_error("system", "count_snapshot", e)

    async def timed_api_call(self, session: aiohttp.ClientSession, url: str) -> Tuple[Dict, int]:
        """Make API call with timing and error handling"""
        try:
            async with session.get(url) as resp:
                data = await resp.json() if resp.status == 200 else {}
                return data, resp.status
        except Exception as e:
            logger.warning(f"API call failed: {url} - {e}")
            return {}, 500

    async def monitor_system_health(self, session: aiohttp.ClientSession):
        """Continuously monitor system health during test"""
        while True:
            try:
                start_time = time.time()
                
                # Test API availability
                async with session.get(f"{self.base_url}/health") as resp:
                    api_available = resp.status == 200
                    response_time = time.time() - start_time
                
                # Test database connectivity
                async with session.get(f"{self.base_url}/api/v1/analyses?limit=1") as resp:
                    db_available = resp.status == 200
                
                health = SystemHealth(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    cpu_usage=None,  # Could be implemented with psutil
                    memory_usage=None,  # Could be implemented with psutil
                    api_availability=api_available,
                    database_connectivity=db_available,
                    concurrent_connections=len(self.user_metrics)
                )
                
                with self.lock:
                    self.system_health_log.append(health)
                
                if not api_available or not db_available:
                    logger.error(f"🚨 System health issue: API={api_available}, DB={db_available}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.capture_error("system", "health_monitor", e)
                await asyncio.sleep(60)  # Wait longer on error

    async def simulate_intensive_user(self, session: aiohttp.ClientSession, user_id: str, profile: Dict):
        """Simulate an intensive user for 1 hour with comprehensive tracking"""
        start_time = datetime.now(timezone.utc)
        
        # Initialize user metrics
        user_metrics = UserMetrics(
            user_id=user_id,
            user_type=profile.get("type", "unknown"),
            start_time=start_time.isoformat(),
            end_time=None,
            total_operations=0,
            successful_operations=0,
            failed_operations=0,
            analyses_submitted=0,
            analyses_completed=0,
            sboms_generated=0,
            vulnerability_scans=0,
            component_searches=0,
            total_errors=0,
            avg_response_time=0.0
        )
        
        with self.lock:
            self.user_metrics[user_id] = user_metrics
        
        logger.info(f"🚀 User {user_id} started - {profile['type']} profile")
        
        completed_analyses = []
        response_times = []
        
        # Calculate operations based on profile
        analyses_per_hour = profile.get("analyses_per_hour", 5)
        operation_interval = 3600 / (analyses_per_hour * 2)  # Double for other operations
        
        end_time = start_time.timestamp() + self.duration_seconds
        
        while time.time() < end_time:
            try:
                operation_start = time.time()
                
                # Decide on operation type
                operation_type = self.choose_operation(profile)
                
                if operation_type == "analysis":
                    analysis_id = await self.perform_analysis(session, user_id, profile)
                    if analysis_id:
                        completed_analyses.append(analysis_id)
                        user_metrics.analyses_submitted += 1
                        
                        # Wait for completion and update metrics
                        if await self.wait_for_analysis_completion(session, user_id, analysis_id):
                            user_metrics.analyses_completed += 1
                            
                elif operation_type == "sbom_generation":
                    if completed_analyses:
                        analysis_id = random.choice(completed_analyses)
                        if await self.generate_sbom(session, user_id, analysis_id):
                            user_metrics.sboms_generated += 1
                
                elif operation_type == "vulnerability_scan":
                    if completed_analyses:
                        analysis_id = random.choice(completed_analyses)
                        if await self.perform_vulnerability_scan(session, user_id, analysis_id):
                            user_metrics.vulnerability_scans += 1
                
                elif operation_type == "component_search":
                    if await self.perform_component_search(session, user_id):
                        user_metrics.component_searches += 1
                
                # Track operation timing
                operation_time = time.time() - operation_start
                response_times.append(operation_time)
                user_metrics.total_operations += 1
                user_metrics.successful_operations += 1
                
                with self.lock:
                    self.successful_operations += 1
                    self.total_operations += 1
                
                # Random wait between operations
                await asyncio.sleep(random.uniform(operation_interval * 0.5, operation_interval * 1.5))
                
            except Exception as e:
                await self.capture_error(user_id, "user_operation", e)
                user_metrics.failed_operations += 1
                user_metrics.total_errors += 1
                
                # Brief pause on error
                await asyncio.sleep(5)
        
        # Finalize user metrics
        user_metrics.end_time = datetime.now(timezone.utc).isoformat()
        user_metrics.avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        with self.lock:
            self.user_metrics[user_id] = user_metrics
        
        logger.info(f"✅ User {user_id} completed - {user_metrics.total_operations} ops, "
                   f"{user_metrics.successful_operations} success, {user_metrics.total_errors} errors")

    def choose_operation(self, profile: Dict) -> str:
        """Choose operation type based on user profile"""
        rand = random.random()
        
        if rand < 0.4:  # 40% analysis
            return "analysis"
        elif rand < 0.4 + profile.get("sbom_frequency", 0.5) * 0.3:  # 30% SBOM (weighted by profile)
            return "sbom_generation"
        elif rand < 0.8 and profile.get("vulnerability_focus", False):  # 20% vulnerability scan
            return "vulnerability_scan"
        else:  # 20% component search
            return "component_search"

    async def perform_analysis(self, session: aiohttp.ClientSession, user_id: str, profile: Dict) -> Optional[str]:
        """Perform analysis with comprehensive error handling"""
        try:
            # Choose project (favor vulnerable ones for interesting results)
            if profile.get("vulnerability_focus", False):
                # Security-focused users prefer vulnerable projects
                vulnerable_projects = [p for p in self.test_projects if p.get("expected_vulns") in ["high", "critical"]]
                project = random.choice(vulnerable_projects) if vulnerable_projects else random.choice(self.test_projects)
            else:
                project = random.choice(self.test_projects)
            
            endpoint = f"/analyze/{project['type']}"
            
            async with session.post(f"{self.base_url}{endpoint}", json=project) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    analysis_id = result["analysis_id"]
                    logger.debug(f"Analysis submitted: {user_id} -> {analysis_id} ({project['type']})")
                    return analysis_id
                else:
                    await self.capture_error(user_id, "analysis_submission", 
                                           Exception(f"HTTP {resp.status}"), resp.status)
                    return None
                    
        except Exception as e:
            await self.capture_error(user_id, "analysis_submission", e)
            return None

    async def wait_for_analysis_completion(self, session: aiohttp.ClientSession, 
                                         user_id: str, analysis_id: str) -> bool:
        """Wait for analysis completion with timeout"""
        max_wait = 120  # 2 minutes max
        check_interval = 10  # Every 10 seconds
        
        for _ in range(max_wait // check_interval):
            try:
                await asyncio.sleep(check_interval)
                
                async with session.get(f"{self.base_url}/analyze/{analysis_id}/status") as resp:
                    if resp.status == 200:
                        status_data = await resp.json()
                        status = status_data.get("status")
                        
                        if status == "completed":
                            return True
                        elif status == "failed":
                            await self.capture_error(user_id, "analysis_completion", 
                                                   Exception(f"Analysis failed: {analysis_id}"), 
                                                   analysis_id=analysis_id)
                            return False
                            
            except Exception as e:
                await self.capture_error(user_id, "analysis_status_check", e, analysis_id=analysis_id)
        
        # Timeout
        await self.capture_error(user_id, "analysis_timeout", 
                               Exception(f"Analysis timeout: {analysis_id}"), 
                               analysis_id=analysis_id)
        return False

    async def generate_sbom(self, session: aiohttp.ClientSession, user_id: str, analysis_id: str) -> bool:
        """Generate SBOM with error handling"""
        try:
            sbom_format = random.choice(["spdx", "cyclonedx"])
            request_data = {
                "analysis_ids": [analysis_id],
                "format": sbom_format,
                "include_vulnerabilities": True
            }
            
            async with session.post(f"{self.base_url}/sbom/generate", json=request_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    sbom_id = result["sbom_id"]
                    logger.debug(f"SBOM generated: {user_id} -> {sbom_id} ({sbom_format})")
                    return True
                else:
                    await self.capture_error(user_id, "sbom_generation", 
                                           Exception(f"HTTP {resp.status}"), resp.status, analysis_id)
                    return False
                    
        except Exception as e:
            await self.capture_error(user_id, "sbom_generation", e, analysis_id=analysis_id)
            return False

    async def perform_vulnerability_scan(self, session: aiohttp.ClientSession, 
                                       user_id: str, analysis_id: str) -> bool:
        """Perform vulnerability scan"""
        try:
            async with session.get(f"{self.base_url}/vulnerabilities/scan/{analysis_id}") as resp:
                if resp.status == 200:
                    vulns = await resp.json()
                    vuln_count = len(vulns.get("vulnerabilities", []))
                    logger.debug(f"Vulnerability scan: {user_id} -> {vuln_count} vulns for {analysis_id}")
                    return True
                else:
                    await self.capture_error(user_id, "vulnerability_scan", 
                                           Exception(f"HTTP {resp.status}"), resp.status, analysis_id)
                    return False
                    
        except Exception as e:
            await self.capture_error(user_id, "vulnerability_scan", e, analysis_id=analysis_id)
            return False

    async def perform_component_search(self, session: aiohttp.ClientSession, user_id: str) -> bool:
        """Perform component search"""
        try:
            search_terms = ["log4j", "spring", "jackson", "apache", "mysql", "nginx", "node", "python"]
            search_term = random.choice(search_terms)
            
            async with session.get(f"{self.base_url}/api/v1/components/search?query={search_term}&limit=10") as resp:
                if resp.status == 200:
                    results = await resp.json()
                    count = results.get("total", 0)
                    logger.debug(f"Component search: {user_id} -> '{search_term}' found {count}")
                    return True
                else:
                    await self.capture_error(user_id, "component_search", 
                                           Exception(f"HTTP {resp.status}"), resp.status)
                    return False
                    
        except Exception as e:
            await self.capture_error(user_id, "component_search", e)
            return False

    async def run_one_hour_stress_test(self):
        """Execute comprehensive 1-hour stress test"""
        logger.info("🚀 Starting 1-Hour Perseus Stress Test")
        logger.info("=" * 80)
        logger.info(f"Duration: {self.duration_seconds}s ({self.duration_seconds/3600:.1f}h)")
        logger.info(f"Concurrent Users: {self.max_users}")
        logger.info(f"Test Projects: {len(self.test_projects)}")
        logger.info("=" * 80)
        
        # Enhanced connection settings for stress test
        connector = aiohttp.TCPConnector(
            limit=50,  # Increase connection pool
            limit_per_host=25,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=120, connect=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Initial baseline snapshot
            await self.capture_detailed_count_snapshot(session, "test_start_baseline")
            
            # Start system health monitoring
            health_monitor = asyncio.create_task(self.monitor_system_health(session))
            
            # Create diverse user tasks
            user_tasks = []
            for i in range(self.max_users):
                profile_name = random.choice(list(self.user_profiles.keys()))
                profile = self.user_profiles[profile_name].copy()
                profile["type"] = profile_name
                user_id = f"{profile_name}_{i+1:02d}"
                
                task = asyncio.create_task(self.simulate_intensive_user(session, user_id, profile))
                user_tasks.append(task)
                
                # Stagger user starts
                await asyncio.sleep(random.uniform(1, 5))
            
            # Start periodic count snapshots
            snapshot_task = asyncio.create_task(self.periodic_snapshots(session))
            
            logger.info(f"🏃 All {self.max_users} users started - running for {self.duration_seconds/3600:.1f} hours")
            
            # Wait for all users to complete
            await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Cancel monitoring tasks
            health_monitor.cancel()
            snapshot_task.cancel()
            
            # Final comprehensive snapshot
            await self.capture_detailed_count_snapshot(session, "test_complete_final")
            
            # Generate comprehensive report
            await self.generate_comprehensive_report()

    async def periodic_snapshots(self, session: aiohttp.ClientSession):
        """Take periodic snapshots during the test"""
        try:
            snapshot_interval = 300  # Every 5 minutes
            while True:
                await asyncio.sleep(snapshot_interval)
                await self.capture_detailed_count_snapshot(session, "periodic_snapshot")
        except asyncio.CancelledError:
            pass

    async def generate_comprehensive_report(self):
        """Generate extremely detailed test report"""
        test_end_time = datetime.now(timezone.utc)
        duration = (test_end_time - self.test_start_time).total_seconds()
        
        # Calculate comprehensive metrics
        total_users = len(self.user_metrics)
        total_user_operations = sum(m.total_operations for m in self.user_metrics.values())
        total_user_errors = sum(m.total_errors for m in self.user_metrics.values())
        
        avg_operations_per_user = total_user_operations / total_users if total_users > 0 else 0
        overall_success_rate = ((total_user_operations - total_user_errors) / total_user_operations * 100) if total_user_operations > 0 else 0
        
        operations_per_hour = (total_user_operations / duration) * 3600 if duration > 0 else 0
        avg_response_time = self.total_response_time / len(self.count_snapshots) if self.count_snapshots else 0
        
        # Error analysis
        error_by_type = {}
        error_by_user = {}
        for error in self.error_log:
            error_by_type[error.error_type] = error_by_type.get(error.error_type, 0) + 1
            error_by_user[error.user_id] = error_by_user.get(error.user_id, 0) + 1
        
        # Count consistency analysis
        consistency_issues = self.analyze_count_consistency()
        
        # Performance analysis
        performance_metrics = self.analyze_performance()
        
        report = {
            "test_metadata": {
                "test_type": "one_hour_stress_test",
                "version": "2.0",
                "start_time": self.test_start_time.isoformat(),
                "end_time": test_end_time.isoformat(),
                "duration_seconds": duration,
                "duration_hours": duration / 3600,
                "concurrent_users": self.max_users,
                "base_url": self.base_url,
                "test_projects_count": len(self.test_projects)
            },
            
            "executive_summary": {
                "total_operations": total_user_operations,
                "successful_operations": total_user_operations - total_user_errors,
                "failed_operations": total_user_errors,
                "success_rate_percent": overall_success_rate,
                "operations_per_hour": operations_per_hour,
                "avg_operations_per_user": avg_operations_per_user,
                "avg_response_time_seconds": avg_response_time,
                "total_errors": len(self.error_log),
                "unique_error_types": len(error_by_type),
                "system_stability": "excellent" if overall_success_rate > 95 else "good" if overall_success_rate > 85 else "poor"
            },
            
            "count_evolution": {
                "snapshots": [asdict(s) for s in self.count_snapshots],
                "consistency_analysis": consistency_issues,
                "final_counts": asdict(self.count_snapshots[-1]) if self.count_snapshots else {}
            },
            
            "error_analysis": {
                "total_errors": len(self.error_log),
                "errors_by_type": error_by_type,
                "errors_by_user": error_by_user,
                "error_rate_percent": (len(self.error_log) / total_user_operations * 100) if total_user_operations > 0 else 0,
                "detailed_errors": [asdict(e) for e in self.error_log[-50:]]  # Last 50 errors
            },
            
            "user_performance": {
                "user_metrics": {uid: asdict(metrics) for uid, metrics in self.user_metrics.items()},
                "user_summary": self.generate_user_summary(),
                "profile_performance": self.analyze_profile_performance()
            },
            
            "system_health": {
                "health_log": [asdict(h) for h in self.system_health_log],
                "availability_percentage": self.calculate_availability(),
                "performance_metrics": performance_metrics
            },
            
            "vulnerability_analysis": self.analyze_vulnerability_patterns(),
            "sbom_analysis": self.analyze_sbom_patterns(),
            "component_analysis": self.analyze_component_patterns(),
            
            "test_projects": self.test_projects,
            "recommendations": self.generate_recommendations(overall_success_rate, error_by_type)
        }
        
        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"tests/one_hour_stress_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Comprehensive 1-Hour Stress Test Report: {report_file}")
        self.print_executive_summary(report)
        
        return report

    def analyze_count_consistency(self) -> Dict[str, Any]:
        """Analyze count consistency throughout the test"""
        issues = []
        
        for i in range(1, len(self.count_snapshots)):
            prev = self.count_snapshots[i-1]
            curr = self.count_snapshots[i]
            
            # Check for unexpected decreases
            if curr.components_unique < prev.components_unique:
                issues.append({
                    "timestamp": curr.timestamp,
                    "event": curr.event,
                    "issue": "component_count_decreased",
                    "previous": prev.components_unique,
                    "current": curr.components_unique,
                    "severity": "high"
                })
            
            if curr.vulnerabilities_total < prev.vulnerabilities_total:
                issues.append({
                    "timestamp": curr.timestamp,
                    "event": curr.event,
                    "issue": "vulnerability_count_decreased",
                    "previous": prev.vulnerabilities_total,
                    "current": curr.vulnerabilities_total,
                    "severity": "high"
                })
            
            # Check for orphan vulnerabilities
            if curr.orphan_vulnerabilities > 0:
                issues.append({
                    "timestamp": curr.timestamp,
                    "event": curr.event,
                    "issue": "orphan_vulnerabilities_detected",
                    "count": curr.orphan_vulnerabilities,
                    "severity": "medium"
                })
        
        return {
            "total_issues": len(issues),
            "high_severity_issues": len([i for i in issues if i.get("severity") == "high"]),
            "medium_severity_issues": len([i for i in issues if i.get("severity") == "medium"]),
            "issues": issues,
            "consistency_score": max(0, 100 - len(issues) * 5)  # Deduct 5 points per issue
        }

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze system performance metrics"""
        if not self.count_snapshots:
            return {}
        
        response_times = [s.api_response_time for s in self.count_snapshots]
        
        return {
            "avg_api_response_time": sum(response_times) / len(response_times),
            "min_api_response_time": min(response_times),
            "max_api_response_time": max(response_times),
            "api_response_time_p95": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            "total_snapshots": len(self.count_snapshots),
            "snapshot_frequency": len(self.count_snapshots) / (self.duration_seconds / 60) if self.duration_seconds > 0 else 0
        }

    def generate_user_summary(self) -> Dict[str, Any]:
        """Generate user performance summary"""
        if not self.user_metrics:
            return {}
        
        all_operations = [m.total_operations for m in self.user_metrics.values()]
        all_success_rates = [(m.successful_operations / m.total_operations * 100) if m.total_operations > 0 else 0 
                           for m in self.user_metrics.values()]
        
        return {
            "total_users": len(self.user_metrics),
            "avg_operations_per_user": sum(all_operations) / len(all_operations),
            "min_operations": min(all_operations),
            "max_operations": max(all_operations),
            "avg_user_success_rate": sum(all_success_rates) / len(all_success_rates),
            "users_with_zero_errors": len([m for m in self.user_metrics.values() if m.total_errors == 0]),
            "users_with_high_errors": len([m for m in self.user_metrics.values() if m.total_errors > 5])
        }

    def analyze_profile_performance(self) -> Dict[str, Any]:
        """Analyze performance by user profile"""
        profile_stats = {}
        
        for user_id, metrics in self.user_metrics.items():
            profile_type = metrics.user_type
            if profile_type not in profile_stats:
                profile_stats[profile_type] = {
                    "users": 0,
                    "total_operations": 0,
                    "total_errors": 0,
                    "total_analyses": 0,
                    "total_sboms": 0
                }
            
            stats = profile_stats[profile_type]
            stats["users"] += 1
            stats["total_operations"] += metrics.total_operations
            stats["total_errors"] += metrics.total_errors
            stats["total_analyses"] += metrics.analyses_completed
            stats["total_sboms"] += metrics.sboms_generated
        
        # Calculate averages
        for profile_type, stats in profile_stats.items():
            user_count = stats["users"]
            stats["avg_operations_per_user"] = stats["total_operations"] / user_count
            stats["avg_errors_per_user"] = stats["total_errors"] / user_count
            stats["success_rate"] = ((stats["total_operations"] - stats["total_errors"]) / stats["total_operations"] * 100) if stats["total_operations"] > 0 else 0
        
        return profile_stats

    def analyze_vulnerability_patterns(self) -> Dict[str, Any]:
        """Analyze vulnerability detection patterns"""
        if not self.count_snapshots:
            return {}
        
        vuln_counts = [s.vulnerabilities_total for s in self.count_snapshots]
        orphan_counts = [s.orphan_vulnerabilities for s in self.count_snapshots]
        
        return {
            "initial_vulnerabilities": vuln_counts[0] if vuln_counts else 0,
            "final_vulnerabilities": vuln_counts[-1] if vuln_counts else 0,
            "peak_vulnerabilities": max(vuln_counts) if vuln_counts else 0,
            "vulnerability_growth": vuln_counts[-1] - vuln_counts[0] if len(vuln_counts) >= 2 else 0,
            "max_orphan_vulnerabilities": max(orphan_counts) if orphan_counts else 0,
            "orphan_vulnerability_periods": len([c for c in orphan_counts if c > 0])
        }

    def analyze_sbom_patterns(self) -> Dict[str, Any]:
        """Analyze SBOM generation patterns"""
        if not self.count_snapshots:
            return {}
        
        sbom_counts = [s.sboms_total for s in self.count_snapshots]
        sbom_generations = sum(m.sboms_generated for m in self.user_metrics.values())
        
        return {
            "initial_sboms": sbom_counts[0] if sbom_counts else 0,
            "final_sboms": sbom_counts[-1] if sbom_counts else 0,
            "sbom_growth": sbom_counts[-1] - sbom_counts[0] if len(sbom_counts) >= 2 else 0,
            "user_sbom_requests": sbom_generations,
            "sbom_success_rate": (sbom_counts[-1] / sbom_generations * 100) if sbom_generations > 0 else 0
        }

    def analyze_component_patterns(self) -> Dict[str, Any]:
        """Analyze component discovery patterns"""
        if not self.count_snapshots:
            return {}
        
        unique_counts = [s.components_unique for s in self.count_snapshots]
        total_counts = [s.components_total for s in self.count_snapshots]
        
        return {
            "initial_unique_components": unique_counts[0] if unique_counts else 0,
            "final_unique_components": unique_counts[-1] if unique_counts else 0,
            "component_discovery_growth": unique_counts[-1] - unique_counts[0] if len(unique_counts) >= 2 else 0,
            "peak_total_components": max(total_counts) if total_counts else 0,
            "component_deduplication_ratio": (unique_counts[-1] / total_counts[-1] * 100) if total_counts and total_counts[-1] > 0 else 0
        }

    def calculate_availability(self) -> float:
        """Calculate system availability percentage"""
        if not self.system_health_log:
            return 100.0
        
        available_checks = len([h for h in self.system_health_log if h.api_availability and h.database_connectivity])
        total_checks = len(self.system_health_log)
        
        return (available_checks / total_checks * 100) if total_checks > 0 else 100.0

    def generate_recommendations(self, success_rate: float, error_types: Dict[str, int]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if success_rate < 95:
            recommendations.append(f"🔴 System success rate ({success_rate:.1f}%) is below recommended 95%. Investigate error patterns.")
        
        if "ConnectionError" in error_types or "TimeoutError" in error_types:
            recommendations.append("🔴 Network connectivity issues detected. Consider increasing connection pool size or timeout values.")
        
        if len(error_types) > 5:
            recommendations.append("🟡 Multiple error types detected. Review error handling and implement more robust retry mechanisms.")
        
        if success_rate > 98:
            recommendations.append("✅ Excellent system stability. Consider increasing load for more comprehensive testing.")
        
        return recommendations

    def print_executive_summary(self, report: Dict[str, Any]):
        """Print concise executive summary"""
        logger.info("\n" + "="*80)
        logger.info("📊 ONE-HOUR STRESS TEST - EXECUTIVE SUMMARY")
        logger.info("="*80)
        
        summary = report["executive_summary"]
        metadata = report["test_metadata"]
        
        logger.info(f"⏱️  Duration: {metadata['duration_hours']:.2f} hours ({metadata['duration_seconds']:.0f}s)")
        logger.info(f"👥 Concurrent Users: {metadata['concurrent_users']}")
        logger.info(f"🎯 Test Projects: {metadata['test_projects_count']}")
        
        logger.info(f"\n📈 Performance Metrics:")
        logger.info(f"   Total Operations: {summary['total_operations']:,}")
        logger.info(f"   Success Rate: {summary['success_rate_percent']:.2f}%")
        logger.info(f"   Operations/Hour: {summary['operations_per_hour']:.1f}")
        logger.info(f"   Avg Response Time: {summary['avg_response_time_seconds']:.3f}s")
        
        logger.info(f"\n🎯 System Stability: {summary['system_stability'].upper()}")
        
        if report["count_evolution"]["consistency_analysis"]["total_issues"] == 0:
            logger.info("✅ Perfect count consistency - no issues detected!")
        else:
            issues = report["count_evolution"]["consistency_analysis"]["total_issues"]
            logger.info(f"⚠️  {issues} count consistency issues detected")
        
        final_counts = report["count_evolution"]["final_counts"]
        if final_counts:
            logger.info(f"\n📊 Final System State:")
            logger.info(f"   Analyses: {final_counts['analyses_total']} ({final_counts['analyses_completed']} completed)")
            logger.info(f"   Components: {final_counts['components_unique']} unique")
            logger.info(f"   Vulnerabilities: {final_counts['vulnerabilities_total']}")
            logger.info(f"   SBOMs: {final_counts['sboms_total']}")
        
        if report["recommendations"]:
            logger.info(f"\n💡 Recommendations:")
            for rec in report["recommendations"]:
                logger.info(f"   {rec}")
        
        logger.info("="*80)

async def main():
    # Parse command line arguments for flexibility
    import argparse
    parser = argparse.ArgumentParser(description='Perseus 1-Hour Stress Test')
    parser.add_argument('--users', type=int, default=20, help='Number of concurrent users')
    parser.add_argument('--duration', type=float, default=1.0, help='Test duration in hours')
    parser.add_argument('--url', default='http://localhost:8000', help='Perseus base URL')
    
    args = parser.parse_args()
    
    test = OneHourStressTest(
        base_url=args.url,
        max_users=args.users,
        duration_hours=args.duration
    )
    
    await test.run_one_hour_stress_test()

if __name__ == "__main__":
    asyncio.run(main())