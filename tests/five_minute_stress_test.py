#!/usr/bin/env python3
"""
Perseus 5-Minute High-Intensity Stress Test
25 concurrent users, java/c++ source, docker, and binary analysis
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
        logging.FileHandler('tests/five_minute_stress.log'),
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
    sboms_total: int
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

class FiveMinuteStressTest:
    def __init__(self, base_url: str = "http://localhost:8000", max_users: int = 25):
        self.base_url = base_url
        self.max_users = max_users
        self.duration_seconds = 300  # 5 minutes
        self.test_start_time = datetime.now(timezone.utc)
        
        # Tracking
        self.count_snapshots: List[CountSnapshot] = []
        self.error_log: List[ErrorCapture] = []
        self.user_metrics: Dict[str, UserMetrics] = {}
        self.lock = threading.Lock()
        
        # Test statistics
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.total_response_time = 0.0
        
        # Focused test projects - Java/C++ source, docker, binary
        self.test_projects = [
            # Java source projects
            {"location": "data/vulnerable-java-app", "type": "source", "language": "java", "category": "java_source"},
            {"location": "data/vulnerable-java-web", "type": "source", "language": "java", "category": "java_source"},
            {"location": "data/test-java-app", "type": "source", "language": "java", "category": "java_source"},
            {"location": "data/sample-java-project", "type": "source", "language": "java", "category": "java_source"},
            
            # C++ source projects  
            {"location": "data/sample-macos-app", "type": "source", "language": "c++", "category": "cpp_source"},
            
            # Docker containers (high vulnerability potential)
            {"location": "nginx:1.15", "type": "docker", "image": "nginx:1.15", "category": "docker"},
            {"location": "node:10.15-alpine", "type": "docker", "image": "node:10.15-alpine", "category": "docker"},
            {"location": "python:3.6", "type": "docker", "image": "python:3.6", "category": "docker"},
            {"location": "ubuntu:18.04", "type": "docker", "image": "ubuntu:18.04", "category": "docker"},
            {"location": "redis:5.0", "type": "docker", "image": "redis:5.0", "category": "docker"},
            {"location": "mysql:5.7", "type": "docker", "image": "mysql:5.7", "category": "docker"},
            {"location": "alpine:3.8", "type": "docker", "image": "alpine:3.8", "category": "docker"},
            {"location": "centos:7", "type": "docker", "image": "centos:7", "category": "docker"},
            
            # Binary analysis
            {"location": "data/sample-macos-app/sample-macos-static-app", "type": "binary", "category": "binary"},
            {"location": "/usr/bin/curl", "type": "binary", "category": "binary"},
            {"location": "/bin/bash", "type": "binary", "category": "binary"},
        ]
        
        # Aggressive user profiles for maximum stress
        self.user_profiles = {
            "heavy_java_analyzer": {"analyses_per_minute": 6, "sbom_frequency": 0.8, "focus": "java_source"},
            "docker_specialist": {"analyses_per_minute": 8, "sbom_frequency": 0.9, "focus": "docker"},  
            "security_scanner": {"analyses_per_minute": 5, "sbom_frequency": 1.0, "vulnerability_focus": True},
            "binary_analyzer": {"analyses_per_minute": 4, "sbom_frequency": 0.7, "focus": "binary"},
            "cpp_developer": {"analyses_per_minute": 5, "sbom_frequency": 0.6, "focus": "cpp_source"},
            "high_frequency_user": {"analyses_per_minute": 10, "sbom_frequency": 0.5, "rapid_fire": True}
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
            analysis_id=analysis_id
        )
        
        with self.lock:
            self.error_log.append(error_capture)
            self.failed_operations += 1
        
        logger.error(f"⚠️  {user_id} | {operation} | {error}")

    async def capture_count_snapshot(self, session: aiohttp.ClientSession, event: str):
        """Capture detailed count snapshot with performance metrics"""
        start_time = time.time()
        
        try:
            # Fast parallel API calls
            tasks = [
                self.timed_api_call(session, f"{self.base_url}/api/v1/analyses"),
                self.timed_api_call(session, f"{self.base_url}/api/v1/components/unique"),
                self.timed_api_call(session, f"{self.base_url}/api/v1/vulnerabilities?limit=1"),
                self.timed_api_call(session, f"{self.base_url}/api/v1/sboms"),
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            api_response_time = time.time() - start_time
            
            # Parse responses
            analyses_total = analyses_completed = analyses_failed = 0
            components_total = components_unique = 0
            vulnerabilities_total = 0
            sboms_total = 0
            
            if not isinstance(responses[0], Exception) and responses[0][1] == 200:
                data = responses[0][0]
                analyses_total = data.get("total", 0)
                analyses = data.get("analyses", [])
                analyses_completed = len([a for a in analyses if a.get("status") == "completed"])
                analyses_failed = len([a for a in analyses if a.get("status") == "failed"])
            
            if not isinstance(responses[1], Exception) and responses[1][1] == 200:
                components_unique = responses[1][0].get("total", 0)
            
            if not isinstance(responses[2], Exception) and responses[2][1] == 200:
                vulnerabilities_total = responses[2][0].get("total", 0)
            
            if not isinstance(responses[3], Exception) and responses[3][1] == 200:
                sboms_total = responses[3][0].get("total", 0)
            
            # Create snapshot
            snapshot = CountSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event=event,
                analyses_total=analyses_total,
                analyses_completed=analyses_completed,
                analyses_failed=analyses_failed,
                components_total=components_total,
                components_unique=components_unique,
                vulnerabilities_total=vulnerabilities_total,
                sboms_total=sboms_total,
                api_response_time=api_response_time
            )
            
            with self.lock:
                self.count_snapshots.append(snapshot)
                self.total_response_time += api_response_time
            
            logger.info(f"📊 {event} | A:{analyses_total}({analyses_completed}✓/{analyses_failed}✗) "
                       f"C:{components_unique} V:{vulnerabilities_total} S:{sboms_total} ({api_response_time:.2f}s)")
                
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

    async def simulate_high_intensity_user(self, session: aiohttp.ClientSession, user_id: str, profile: Dict):
        """Simulate high-intensity user for 5 minutes"""
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
        
        logger.info(f"🚀 {user_id} started | {profile['type']} | {profile.get('analyses_per_minute', 5)}/min")
        
        completed_analyses = []
        response_times = []
        
        # Calculate operation interval for high intensity
        analyses_per_minute = profile.get("analyses_per_minute", 5)
        base_interval = 60 / analyses_per_minute  # Base time between analyses
        operation_interval = base_interval / 3  # More operations per analysis
        
        end_time = start_time.timestamp() + self.duration_seconds
        
        while time.time() < end_time:
            try:
                operation_start = time.time()
                
                # Choose operation based on profile
                operation_type = self.choose_operation(profile, completed_analyses)
                
                if operation_type == "analysis":
                    analysis_id = await self.perform_focused_analysis(session, user_id, profile)
                    if analysis_id:
                        completed_analyses.append(analysis_id)
                        user_metrics.analyses_submitted += 1
                        
                        # Quick completion check for high intensity
                        if await self.quick_completion_check(session, user_id, analysis_id):
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
                
                # Track timing
                operation_time = time.time() - operation_start
                response_times.append(operation_time)
                user_metrics.total_operations += 1
                user_metrics.successful_operations += 1
                
                with self.lock:
                    self.successful_operations += 1
                    self.total_operations += 1
                
                # Aggressive timing for stress test
                if profile.get("rapid_fire"):
                    await asyncio.sleep(random.uniform(1, 3))  # Very fast
                else:
                    await asyncio.sleep(random.uniform(operation_interval * 0.3, operation_interval * 0.8))
                
            except Exception as e:
                await self.capture_error(user_id, "user_operation", e)
                user_metrics.failed_operations += 1
                user_metrics.total_errors += 1
                await asyncio.sleep(2)  # Brief pause on error
        
        # Finalize metrics
        user_metrics.end_time = datetime.now(timezone.utc).isoformat()
        user_metrics.avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        with self.lock:
            self.user_metrics[user_id] = user_metrics
        
        logger.info(f"✅ {user_id} completed | {user_metrics.total_operations} ops | "
                   f"{user_metrics.analyses_completed} analyses | {user_metrics.total_errors} errors")

    def choose_operation(self, profile: Dict, completed_analyses: List) -> str:
        """Choose operation type based on profile and available analyses"""
        rand = random.random()
        
        # Heavy analysis focus for stress test
        if rand < 0.5:  # 50% analysis
            return "analysis"
        elif rand < 0.5 + profile.get("sbom_frequency", 0.5) * 0.3 and completed_analyses:  # 30% SBOM
            return "sbom_generation"
        elif rand < 0.8 and completed_analyses and profile.get("vulnerability_focus", False):  # 20% vuln scan
            return "vulnerability_scan"
        else:  # 20% component search
            return "component_search"

    async def perform_focused_analysis(self, session: aiohttp.ClientSession, user_id: str, profile: Dict) -> Optional[str]:
        """Perform analysis focused on user's specialty"""
        try:
            # Choose project based on profile focus
            focus = profile.get("focus", "any")
            if focus != "any":
                focused_projects = [p for p in self.test_projects if p.get("category") == focus]
                project = random.choice(focused_projects) if focused_projects else random.choice(self.test_projects)
            else:
                project = random.choice(self.test_projects)
            
            endpoint = f"/analyze/{project['type']}"
            
            async with session.post(f"{self.base_url}{endpoint}", json=project) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    analysis_id = result["analysis_id"]
                    logger.debug(f"📝 {user_id} | Analysis: {analysis_id} | {project['category']}")
                    return analysis_id
                else:
                    await self.capture_error(user_id, "analysis_submission", 
                                           Exception(f"HTTP {resp.status}"), resp.status)
                    return None
                    
        except Exception as e:
            await self.capture_error(user_id, "analysis_submission", e)
            return None

    async def quick_completion_check(self, session: aiohttp.ClientSession, 
                                   user_id: str, analysis_id: str) -> bool:
        """Quick check for analysis completion - don't wait long in stress test"""
        max_checks = 3  # Only check 3 times
        check_interval = 15  # 15 seconds between checks
        
        for check in range(max_checks):
            await asyncio.sleep(check_interval)
            
            try:
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
        
        # Don't wait longer in stress test - assume still running
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
                    logger.debug(f"📋 {user_id} | SBOM: {sbom_id} | {sbom_format}")
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
        """Perform vulnerability scan using correct endpoint"""
        try:
            async with session.get(f"{self.base_url}/vulnerabilities/scan/{analysis_id}") as resp:
                if resp.status == 200:
                    vulns = await resp.json()
                    vuln_count = len(vulns.get("vulnerable_components", []))
                    logger.debug(f"🔍 {user_id} | Vuln scan: {vuln_count} vulns | {analysis_id}")
                    return True
                else:
                    await self.capture_error(user_id, "vulnerability_scan", 
                                           Exception(f"HTTP {resp.status}"), resp.status, analysis_id)
                    return False
                    
        except Exception as e:
            await self.capture_error(user_id, "vulnerability_scan", e, analysis_id=analysis_id)
            return False

    async def perform_component_search(self, session: aiohttp.ClientSession, user_id: str) -> bool:
        """Perform component search using correct endpoint"""
        try:
            search_terms = ["java", "spring", "log4j", "maven", "apache", "mysql", "nginx", "alpine", "curl"]
            search_term = random.choice(search_terms)
            
            async with session.get(f"{self.base_url}/api/v1/components/search?query={search_term}&limit=10") as resp:
                if resp.status == 200:
                    results = await resp.json()
                    count = len(results.get("components", []))
                    logger.debug(f"🔎 {user_id} | Search: '{search_term}' | {count} results")
                    return True
                else:
                    await self.capture_error(user_id, "component_search", 
                                           Exception(f"HTTP {resp.status}"), resp.status)
                    return False
                    
        except Exception as e:
            await self.capture_error(user_id, "component_search", e)
            return False

    async def run_five_minute_stress_test(self):
        """Execute high-intensity 5-minute stress test"""
        logger.info("⚡ STARTING 5-MINUTE HIGH-INTENSITY STRESS TEST")
        logger.info("=" * 80)
        logger.info(f"🎯 Target: {self.max_users} concurrent users for {self.duration_seconds} seconds")
        logger.info(f"📋 Test Projects: {len(self.test_projects)} (Java/C++ source, Docker, Binary)")
        logger.info(f"⚡ Mode: HIGH INTENSITY - Maximum stress")
        logger.info("=" * 80)
        
        # High-performance connection settings
        connector = aiohttp.TCPConnector(
            limit=100,  # High connection pool for stress
            limit_per_host=50,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=120,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=60, connect=15)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Initial baseline
            await self.capture_count_snapshot(session, "STRESS_TEST_START")
            
            # Create high-intensity user tasks
            user_tasks = []
            profile_names = list(self.user_profiles.keys())
            
            for i in range(self.max_users):
                profile_name = profile_names[i % len(profile_names)]  # Distribute profiles evenly
                profile = self.user_profiles[profile_name].copy()
                profile["type"] = profile_name
                user_id = f"{profile_name}_{i+1:02d}"
                
                task = asyncio.create_task(self.simulate_high_intensity_user(session, user_id, profile))
                user_tasks.append(task)
                
                # Very minimal stagger for maximum concurrency
                await asyncio.sleep(0.1)
            
            # Start periodic snapshots
            snapshot_task = asyncio.create_task(self.periodic_snapshots(session))
            
            logger.info(f"⚡ ALL {self.max_users} USERS LAUNCHED - MAXIMUM STRESS ENGAGED!")
            
            # Wait for completion
            await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Cancel monitoring
            snapshot_task.cancel()
            
            # Final snapshot
            await self.capture_count_snapshot(session, "STRESS_TEST_COMPLETE")
            
            # Generate results
            await self.generate_stress_results()

    async def periodic_snapshots(self, session: aiohttp.ClientSession):
        """Take snapshots every 30 seconds during stress test"""
        try:
            snapshot_interval = 30  # Every 30 seconds
            while True:
                await asyncio.sleep(snapshot_interval)
                await self.capture_count_snapshot(session, "PERIODIC_SNAPSHOT")
        except asyncio.CancelledError:
            pass

    async def generate_stress_results(self):
        """Generate comprehensive stress test results"""
        test_end_time = datetime.now(timezone.utc)
        duration = (test_end_time - self.test_start_time).total_seconds()
        
        # Calculate metrics
        total_users = len(self.user_metrics)
        total_user_operations = sum(m.total_operations for m in self.user_metrics.values())
        total_user_errors = sum(m.total_errors for m in self.user_metrics.values())
        
        operations_per_minute = (total_user_operations / duration) * 60 if duration > 0 else 0
        overall_success_rate = ((total_user_operations - total_user_errors) / total_user_operations * 100) if total_user_operations > 0 else 0
        
        # Error analysis
        error_by_type = {}
        for error in self.error_log:
            error_by_type[error.error_type] = error_by_type.get(error.error_type, 0) + 1
        
        # Count analysis
        final_snapshot = self.count_snapshots[-1] if self.count_snapshots else None
        
        report = {
            "test_metadata": {
                "test_type": "five_minute_high_intensity_stress_test",
                "start_time": self.test_start_time.isoformat(),
                "end_time": test_end_time.isoformat(),
                "duration_seconds": duration,
                "concurrent_users": self.max_users,
                "base_url": self.base_url,
                "test_projects": len(self.test_projects)
            },
            
            "performance_summary": {
                "total_operations": total_user_operations,
                "successful_operations": total_user_operations - total_user_errors,
                "failed_operations": total_user_errors,
                "success_rate_percent": overall_success_rate,
                "operations_per_minute": operations_per_minute,
                "operations_per_second": operations_per_minute / 60,
                "total_system_errors": len(self.error_log),
                "error_rate_percent": (len(self.error_log) / total_user_operations * 100) if total_user_operations > 0 else 0
            },
            
            "final_system_state": asdict(final_snapshot) if final_snapshot else {},
            
            "count_evolution": [asdict(s) for s in self.count_snapshots],
            
            "error_analysis": {
                "total_errors": len(self.error_log),
                "errors_by_type": error_by_type,
                "detailed_errors": [asdict(e) for e in self.error_log]
            },
            
            "user_performance": {
                "user_metrics": {uid: asdict(metrics) for uid, metrics in self.user_metrics.items()},
                "user_summary": self.generate_user_summary(),
                "profile_performance": self.analyze_profile_performance()
            },
            
            "category_analysis": self.analyze_by_category(),
            "stress_test_verdict": self.generate_verdict(overall_success_rate, final_snapshot)
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"tests/five_minute_stress_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 5-Minute Stress Test Report: {report_file}")
        self.print_stress_results(report)
        
        return report

    def generate_user_summary(self) -> Dict[str, Any]:
        """Generate user performance summary"""
        if not self.user_metrics:
            return {}
        
        all_operations = [m.total_operations for m in self.user_metrics.values()]
        all_analyses = [m.analyses_completed for m in self.user_metrics.values()]
        all_sboms = [m.sboms_generated for m in self.user_metrics.values()]
        
        return {
            "total_users": len(self.user_metrics),
            "avg_operations_per_user": sum(all_operations) / len(all_operations),
            "total_analyses_completed": sum(all_analyses),
            "total_sboms_generated": sum(all_sboms),
            "users_with_zero_errors": len([m for m in self.user_metrics.values() if m.total_errors == 0])
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
                    "total_analyses": 0,
                    "total_sboms": 0,
                    "total_errors": 0
                }
            
            stats = profile_stats[profile_type]
            stats["users"] += 1
            stats["total_operations"] += metrics.total_operations
            stats["total_analyses"] += metrics.analyses_completed
            stats["total_sboms"] += metrics.sboms_generated
            stats["total_errors"] += metrics.total_errors
        
        return profile_stats

    def analyze_by_category(self) -> Dict[str, Any]:
        """Analyze performance by project category"""
        return {
            "project_categories": [
                {"name": "Java Source", "count": len([p for p in self.test_projects if p.get("category") == "java_source"])},
                {"name": "C++ Source", "count": len([p for p in self.test_projects if p.get("category") == "cpp_source"])},
                {"name": "Docker Images", "count": len([p for p in self.test_projects if p.get("category") == "docker"])},
                {"name": "Binary Analysis", "count": len([p for p in self.test_projects if p.get("category") == "binary"])}
            ]
        }

    def generate_verdict(self, success_rate: float, final_snapshot: Optional[CountSnapshot]) -> Dict[str, Any]:
        """Generate stress test verdict"""
        if success_rate >= 95 and final_snapshot and final_snapshot.analyses_completed > 20:
            verdict = "EXCELLENT"
            confidence = "VERY_HIGH"
        elif success_rate >= 85 and final_snapshot and final_snapshot.analyses_completed > 10:
            verdict = "GOOD"  
            confidence = "HIGH"
        elif success_rate >= 70:
            verdict = "ACCEPTABLE"
            confidence = "MEDIUM"
        else:
            verdict = "NEEDS_IMPROVEMENT"
            confidence = "LOW"
        
        return {
            "overall_verdict": verdict,
            "confidence_level": confidence,
            "success_rate": success_rate,
            "production_ready": verdict in ["EXCELLENT", "GOOD"],
            "recommendation": self.get_recommendation(verdict)
        }

    def get_recommendation(self, verdict: str) -> str:
        """Get recommendation based on verdict"""
        recommendations = {
            "EXCELLENT": "System is production-ready with exceptional performance under extreme stress",
            "GOOD": "System is production-ready with good performance under high load",
            "ACCEPTABLE": "System can handle moderate load but may need optimization for high-stress scenarios",
            "NEEDS_IMPROVEMENT": "System requires optimization before handling high-stress production workloads"
        }
        return recommendations.get(verdict, "Review system performance and optimize as needed")

    def print_stress_results(self, report: Dict[str, Any]):
        """Print comprehensive stress test results"""
        logger.info("\n" + "="*80)
        logger.info("⚡ 5-MINUTE HIGH-INTENSITY STRESS TEST RESULTS")
        logger.info("="*80)
        
        perf = report["performance_summary"]
        final = report["final_system_state"]
        verdict = report["stress_test_verdict"]
        
        logger.info(f"⏱️  Duration: {report['test_metadata']['duration_seconds']:.1f} seconds")
        logger.info(f"👥 Concurrent Users: {report['test_metadata']['concurrent_users']}")
        
        logger.info(f"\n🚀 Performance Metrics:")
        logger.info(f"   Total Operations: {perf['total_operations']:,}")
        logger.info(f"   Success Rate: {perf['success_rate_percent']:.2f}%")
        logger.info(f"   Operations/Minute: {perf['operations_per_minute']:.1f}")
        logger.info(f"   Operations/Second: {perf['operations_per_second']:.1f}")
        logger.info(f"   System Error Rate: {perf['error_rate_percent']:.2f}%")
        
        if final:
            logger.info(f"\n📊 Final System State:")
            logger.info(f"   Analyses: {final['analyses_total']} ({final['analyses_completed']} completed)")
            logger.info(f"   Components: {final['components_unique']:,} unique")
            logger.info(f"   Vulnerabilities: {final['vulnerabilities_total']:,}")
            logger.info(f"   SBOMs: {final['sboms_total']}")
        
        logger.info(f"\n🎯 VERDICT: {verdict['overall_verdict']}")
        logger.info(f"   Confidence: {verdict['confidence_level']}")
        logger.info(f"   Production Ready: {'✅ YES' if verdict['production_ready'] else '❌ NO'}")
        logger.info(f"   Recommendation: {verdict['recommendation']}")
        
        logger.info("="*80)

async def main():
    test = FiveMinuteStressTest(max_users=25)
    await test.run_five_minute_stress_test()

if __name__ == "__main__":
    asyncio.run(main())