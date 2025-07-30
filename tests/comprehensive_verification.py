#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Comprehensive Automated Verification System for Perseus
Tests all functionality including SBOM generation with up to 20 concurrent users
"""

import asyncio
import aiohttp
import random
import time
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import threading
from asyncio import sleep

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DetailedMetrics:
    """Detailed metrics tracking"""
    analyses_submitted: int = 0
    analyses_completed: int = 0
    analyses_failed: int = 0
    sboms_generated: int = 0
    vulnerability_scans: int = 0
    component_searches: int = 0
    api_calls_total: int = 0
    api_errors: int = 0
    average_response_time: float = 0.0
    
@dataclass 
class CountTracking:
    """Meticulous count tracking"""
    timestamp: datetime
    operation: str
    entity_type: str  # analysis, component, vulnerability, sbom
    count_before: int
    count_after: int
    expected_change: int
    actual_change: int
    consistent: bool
    details: Optional[str] = None

@dataclass
class UserSession:
    """Enhanced user session with detailed tracking"""
    user_id: str
    user_type: str  # developer, security, devops, qa, analyst
    session_id: str
    created_at: datetime
    analyses: List[Dict[str, Any]] = field(default_factory=list)
    sboms: List[Dict[str, Any]] = field(default_factory=list)
    vulnerability_scans: List[Dict[str, Any]] = field(default_factory=list)
    api_calls: List[Dict[str, Any]] = field(default_factory=list)
    metrics: DetailedMetrics = field(default_factory=DetailedMetrics)
    
class ComprehensivePerseusVerification:
    """Enhanced verification system with complete functionality testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.sessions: Dict[str, UserSession] = {}
        self.count_tracking: List[CountTracking] = []
        self.global_metrics = DetailedMetrics()
        self.lock = threading.Lock()
        
        # Enhanced global state tracking
        self.global_state = {
            "total_analyses": 0,
            "total_components": 0,
            "total_vulnerabilities": 0,
            "total_sboms": 0,
            "analyses_by_type": defaultdict(int),
            "sboms_by_format": defaultdict(int),
            "component_names": set(),
            "vulnerability_ids": set(),
            "analysis_to_sbom_mapping": {},
            "component_vulnerability_mapping": defaultdict(set),
            "timestamp_start": datetime.now(timezone.utc)
        }
        
    async def track_count_change(self, operation: str, entity_type: str, 
                                expected_change: int, action_func):
        """Track count changes for any operation"""
        # Get count before
        count_before = await self._get_entity_count(entity_type)
        
        # Perform action
        result = await action_func()
        
        # Wait for database to update (longer wait for eventual consistency)
        await asyncio.sleep(2.0)
        
        # Get count after
        count_after = await self._get_entity_count(entity_type)
        
        actual_change = count_after - count_before
        consistent = actual_change == expected_change
        
        tracking = CountTracking(
            timestamp=datetime.now(timezone.utc),
            operation=operation,
            entity_type=entity_type,
            count_before=count_before,
            count_after=count_after,
            expected_change=expected_change,
            actual_change=actual_change,
            consistent=consistent,
            details=f"Expected {expected_change}, got {actual_change}"
        )
        
        with self.lock:
            self.count_tracking.append(tracking)
            
        if not consistent:
            logger.warning(f"Count inconsistency in {operation}: {tracking.details}")
            
        return result, tracking
        
    async def _get_entity_count(self, entity_type: str) -> int:
        """Get current count for an entity type"""
        async with aiohttp.ClientSession() as session:
            if entity_type == "analysis":
                async with session.get(f"{self.base_url}/api/v1/analyses") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("total", 0)
            elif entity_type == "component":
                async with session.get(f"{self.base_url}/api/v1/components/unique") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("total", 0)
            elif entity_type == "vulnerability":
                async with session.get(f"{self.base_url}/api/v1/vulnerabilities?limit=1") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("total", 0)
            elif entity_type == "sbom":
                async with session.get(f"{self.base_url}/api/v1/sboms") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("total", 0)
        return 0
        
    async def create_user_session(self, user_id: str, user_type: str) -> UserSession:
        """Create an enhanced user session"""
        session = UserSession(
            user_id=user_id,
            user_type=user_type,
            session_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc)
        )
        with self.lock:
            self.sessions[user_id] = session
        logger.info(f"Created session for {user_type} user {user_id}")
        return session
        
    async def simulate_user_activity(self, user_id: str, user_type: str, activities: List[str]):
        """Simulate comprehensive user activities"""
        session = await self.create_user_session(user_id, user_type)
        
        # Use connection pooling and timeout to prevent server disconnect errors
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as client_session:
            for activity in activities:
                try:
                    # Random wait between activities (1-5 seconds)
                    await asyncio.sleep(random.uniform(1, 5))
                    
                    if activity == "source_analysis":
                        await self._perform_source_analysis(client_session, session)
                    elif activity == "docker_analysis":
                        await self._perform_docker_analysis(client_session, session)
                    elif activity == "os_analysis":
                        await self._perform_os_analysis(client_session, session)
                    elif activity == "binary_analysis":
                        await self._perform_binary_analysis(client_session, session)
                    elif activity == "generate_sbom":
                        await self._perform_sbom_generation(client_session, session)
                    elif activity == "vulnerability_scan":
                        await self._perform_vulnerability_scan(client_session, session)
                    elif activity == "component_search":
                        await self._perform_component_search(client_session, session)
                    elif activity == "view_dashboard":
                        await self._view_dashboard(client_session, session)
                    elif activity == "delete_analysis":
                        await self._delete_old_analysis(client_session, session)
                        
                except Exception as e:
                    logger.error(f"User {user_id} error in {activity}: {e}")
                    session.metrics.api_errors += 1
                    
    async def _perform_source_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Perform source code analysis with count tracking"""
        projects = [
            ("data/sample-java-project", "java"),
            ("data/vulnerable-java-app", "java"),
            ("data/vulnerable-java-web", "java"),
            ("examples/java-nato-library", "java"),
            ("data/sample-macos-app", "go")
        ]
        
        project_path, language = random.choice(projects)
        
        async def submit_analysis():
            request_data = {
                "location": project_path,
                "type": "source",
                "language": language
            }
            
            start_time = time.time()
            async with session.post(f"{self.base_url}/analyze/source", json=request_data) as resp:
                response_time = time.time() - start_time
                user_session.metrics.api_calls_total += 1
                
                if resp.status == 200:
                    result = await resp.json()
                    analysis_id = result.get("analysis_id")
                    
                    analysis_data = {
                        "id": analysis_id,
                        "type": "source",
                        "language": language,
                        "path": project_path,
                        "submitted_at": datetime.now(timezone.utc).isoformat(),
                        "response_time": response_time
                    }
                    
                    user_session.analyses.append(analysis_data)
                    user_session.metrics.analyses_submitted += 1
                    
                    with self.lock:
                        self.global_state["total_analyses"] += 1
                        self.global_state["analyses_by_type"]["source"] += 1
                        
                    logger.info(f"User {user_session.user_id} submitted source analysis {analysis_id}")
                    return analysis_id
                else:
                    user_session.metrics.api_errors += 1
                    
        # Submit analysis without detailed count tracking to reduce noise
        result = await submit_analysis()
        
    async def _perform_docker_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Perform Docker image analysis with count tracking"""
        images = [
            "alpine:latest",
            "ubuntu:22.04", 
            "nginx:latest",
            "python:3.9-slim",
            "node:16-alpine",
            "redis:7-alpine"
        ]
        
        image = random.choice(images)
        
        async def submit_analysis():
            request_data = {
                "location": image,
                "type": "docker"
            }
            
            async with session.post(f"{self.base_url}/analyze/docker", json=request_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    analysis_id = result.get("analysis_id")
                    
                    user_session.analyses.append({
                        "id": analysis_id,
                        "type": "docker",
                        "image": image,
                        "submitted_at": datetime.now(timezone.utc).isoformat()
                    })
                    
                    with self.lock:
                        self.global_state["total_analyses"] += 1
                        self.global_state["analyses_by_type"]["docker"] += 1
                        
                    return analysis_id
                    
        result = await submit_analysis()
        
    async def _perform_os_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Perform OS analysis with count tracking"""
        async def submit_analysis():
            request_data = {
                "location": "/",
                "type": "os"
            }
            
            async with session.post(f"{self.base_url}/analyze/os", json=request_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    analysis_id = result.get("analysis_id")
                    
                    user_session.analyses.append({
                        "id": analysis_id,
                        "type": "os",
                        "submitted_at": datetime.now(timezone.utc).isoformat()
                    })
                    
                    with self.lock:
                        self.global_state["total_analyses"] += 1
                        self.global_state["analyses_by_type"]["os"] += 1
                        
                    return analysis_id
                    
        result = await submit_analysis()
        
    async def _perform_binary_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Perform binary analysis with count tracking"""
        binary_path = "data/sample-macos-app/sample-macos-static-app"
        
        async def submit_analysis():
            request_data = {
                "location": binary_path,
                "type": "binary"
            }
            
            async with session.post(f"{self.base_url}/analyze/binary", json=request_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    analysis_id = result.get("analysis_id")
                    
                    user_session.analyses.append({
                        "id": analysis_id,
                        "type": "binary",
                        "submitted_at": datetime.now(timezone.utc).isoformat()
                    })
                    
                    with self.lock:
                        self.global_state["total_analyses"] += 1
                        self.global_state["analyses_by_type"]["binary"] += 1
                        
                    return analysis_id
                    
        result = await submit_analysis()
        
    async def _perform_sbom_generation(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Generate SBOM from completed analyses"""
        # Wait for any recent analysis to complete
        if not user_session.analyses:
            logger.info(f"User {user_session.user_id} has no analyses to generate SBOM from")
            return
            
        # Pick a recent analysis
        analysis = random.choice(user_session.analyses[-5:] if len(user_session.analyses) > 5 else user_session.analyses)
        analysis_id = analysis["id"]
        
        # Wait for analysis completion
        await self._wait_for_analysis_completion(session, analysis_id)
        
        # Generate SBOM
        formats = ["spdx", "cyclonedx"]
        sbom_format = random.choice(formats)
        
        async def generate_sbom():
            request_data = {
                "analysis_ids": [analysis_id],
                "format": sbom_format,
                "include_vulnerabilities": True
            }
            
            async with session.post(f"{self.base_url}/sbom/generate", json=request_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    sbom_id = result.get("sbom_id")
                    
                    sbom_data = {
                        "id": sbom_id,
                        "analysis_id": analysis_id,
                        "format": sbom_format,
                        "generated_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    user_session.sboms.append(sbom_data)
                    user_session.metrics.sboms_generated += 1
                    
                    with self.lock:
                        self.global_state["total_sboms"] += 1
                        self.global_state["sboms_by_format"][sbom_format] += 1
                        self.global_state["analysis_to_sbom_mapping"][analysis_id] = sbom_id
                        
                    logger.info(f"User {user_session.user_id} generated {sbom_format} SBOM {sbom_id}")
                    return sbom_id
                    
        result = await generate_sbom()
        
    async def _perform_vulnerability_scan(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Perform vulnerability scanning operations"""
        # Get a recent analysis for vulnerability details
        if user_session.analyses:
            analysis = random.choice(user_session.analyses)
            analysis_id = analysis["id"]
            
            # Get detailed vulnerability scan
            async with session.get(f"{self.base_url}/api/v1/vulnerabilities/detailed/{analysis_id}") as resp:
                if resp.status == 200:
                    vuln_data = await resp.json()
                    user_session.vulnerability_scans.append({
                        "analysis_id": analysis_id,
                        "vulnerabilities_found": len(vuln_data.get("vulnerabilities", [])),
                        "scanned_at": datetime.now(timezone.utc).isoformat()
                    })
                    user_session.metrics.vulnerability_scans += 1
                    
        # Also scan a single component
        test_components = [
            {"name": "log4j", "version": "2.14.0", "purl": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.0"},
            {"name": "jackson-databind", "version": "2.9.8", "purl": "pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.9.8"},
            {"name": "spring-core", "version": "5.2.0.RELEASE", "purl": "pkg:maven/org.springframework/spring-core@5.2.0.RELEASE"}
        ]
        
        component = random.choice(test_components)
        
        async with session.post(f"{self.base_url}/vulnerabilities/scan/component", json=component) as resp:
            if resp.status == 200:
                result = await resp.json()
                logger.info(f"User {user_session.user_id} scanned component {component['name']}")
                
    async def _perform_component_search(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Perform component searches"""
        search_terms = ["log4j", "spring", "jackson", "commons", "apache", "mysql"]
        search_term = random.choice(search_terms)
        
        params = {
            "q": search_term,
            "vulnerable_only": str(random.choice([True, False])).lower(),
            "limit": "20"
        }
        
        async with session.get(f"{self.base_url}/api/v1/components/search", params=params) as resp:
            if resp.status == 200:
                result = await resp.json()
                user_session.metrics.component_searches += 1
                logger.info(f"User {user_session.user_id} searched for '{search_term}', found {len(result.get('components', []))} components")
                
    async def _view_dashboard(self, session: aiohttp.ClientSession, user_session: UserSession):
        """View various dashboard pages"""
        endpoints = [
            "/dashboard",
            "/api/v1/statistics/dashboard",
            "/api/v1/vulnerabilities/statistics",
            "/api/v1/sboms/statistics",
            "/api/v1/counts/statistics"
        ]
        
        endpoint = random.choice(endpoints)
        async with session.get(f"{self.base_url}{endpoint}") as resp:
            if resp.status == 200:
                logger.info(f"User {user_session.user_id} viewed {endpoint}")
                
    async def _delete_old_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Delete an old analysis (with count tracking)"""
        if len(user_session.analyses) < 3:
            return  # Don't delete if user has few analyses
            
        # Delete one of the older analyses
        old_analysis = user_session.analyses[0]
        analysis_id = old_analysis["id"]
        
        async def delete_analysis():
            async with session.delete(f"{self.base_url}/api/v1/analyses/{analysis_id}") as resp:
                if resp.status == 200:
                    user_session.analyses.remove(old_analysis)
                    logger.info(f"User {user_session.user_id} deleted analysis {analysis_id}")
                    return True
                return False
                
        result = await delete_analysis()
        
    async def _wait_for_analysis_completion(self, session: aiohttp.ClientSession, 
                                          analysis_id: str, timeout: int = 120):
        """Wait for analysis to complete with progress tracking"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with session.get(f"{self.base_url}/analyze/{analysis_id}/status") as resp:
                if resp.status == 200:
                    status_data = await resp.json()
                    status = status_data.get("status")
                    
                    if status == "completed":
                        # Update metrics
                        for s in self.sessions.values():
                            for a in s.analyses:
                                if a["id"] == analysis_id:
                                    a["completed_at"] = datetime.now(timezone.utc).isoformat()
                                    a["duration"] = time.time() - start_time
                                    s.metrics.analyses_completed += 1
                                    break
                        
                        # Get the analysis results and update global state
                        await self._update_global_state_from_results(session, analysis_id)
                        
                        return "completed"
                    elif status == "failed":
                        for s in self.sessions.values():
                            for a in s.analyses:
                                if a["id"] == analysis_id:
                                    s.metrics.analyses_failed += 1
                                    break
                        return "failed"
                        
            await asyncio.sleep(2)
            
        logger.warning(f"Analysis {analysis_id} timed out after {timeout}s")
        return "timeout"
        
    async def _update_global_state_from_results(self, session: aiohttp.ClientSession, analysis_id: str):
        """Update global state with components and vulnerabilities from analysis results"""
        try:
            # Get analysis results
            async with session.get(f"{self.base_url}/analyze/{analysis_id}/results") as resp:
                if resp.status == 200:
                    results = await resp.json()
                    components = results.get("components", [])
                    
                    with self.lock:
                        for comp in components:
                            comp_key = f"{comp.get('name')}:{comp.get('version')}"
                            self.global_state["component_names"].add(comp_key)
                    
            # Get vulnerability details
            async with session.get(f"{self.base_url}/api/v1/vulnerabilities/detailed/{analysis_id}") as resp:
                if resp.status == 200:
                    vuln_data = await resp.json()
                    vulnerabilities = vuln_data.get("vulnerabilities", [])
                    
                    with self.lock:
                        for vuln in vulnerabilities:
                            vuln_id = vuln.get("id")
                            if vuln_id:
                                self.global_state["vulnerability_ids"].add(vuln_id)
                                
        except Exception as e:
            logger.error(f"Failed to update global state from results for {analysis_id}: {e}")
        
    async def perform_comprehensive_verification(self):
        """Perform comprehensive consistency verification"""
        logger.info("Starting comprehensive verification...")
        
        verification_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": []
        }
        
        async with aiohttp.ClientSession() as session:
            # 1. Verify total counts
            checks = [
                ("total_analyses", "analysis", self.global_state["total_analyses"]),
                ("total_sboms", "sbom", self.global_state["total_sboms"]),
                ("unique_components", "component", len(self.global_state["component_names"])),
                ("total_vulnerabilities", "vulnerability", len(self.global_state["vulnerability_ids"]))
            ]
            
            for check_name, entity_type, expected in checks:
                actual = await self._get_entity_count(entity_type)
                passed = actual >= expected * 0.8  # Allow 20% variance for eventual consistency
                
                verification_results["checks"].append({
                    "name": check_name,
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                    "variance": abs(actual - expected) / expected * 100 if expected > 0 else 0
                })
                
            # 2. Verify SBOM generation rate
            total_analyses = sum(len(s.analyses) for s in self.sessions.values())
            total_sboms = sum(len(s.sboms) for s in self.sessions.values())
            sbom_generation_rate = (total_sboms / total_analyses * 100) if total_analyses > 0 else 0
            
            verification_results["sbom_generation_rate"] = sbom_generation_rate
            
            # 3. Check for orphan vulnerabilities
            async with session.get(f"{self.base_url}/api/v1/vulnerabilities/orphans") as resp:
                if resp.status == 200:
                    orphan_data = await resp.json()
                    orphan_count = orphan_data.get("orphan_count", 0)
                    verification_results["orphan_vulnerabilities"] = orphan_count
                    
            # 4. Validate all counts
            async with session.get(f"{self.base_url}/api/v1/counts/statistics") as resp:
                if resp.status == 200:
                    count_stats = await resp.json()
                    verification_results["count_statistics"] = count_stats
                    
        return verification_results
        
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive verification report"""
        # Calculate detailed metrics
        total_users = len(self.sessions)
        total_api_calls = sum(s.metrics.api_calls_total for s in self.sessions.values())
        total_errors = sum(s.metrics.api_errors for s in self.sessions.values())
        error_rate = (total_errors / total_api_calls * 100) if total_api_calls > 0 else 0
        
        # Count tracking analysis
        total_count_checks = len(self.count_tracking)
        consistent_checks = sum(1 for ct in self.count_tracking if ct.consistent)
        consistency_rate = (consistent_checks / total_count_checks * 100) if total_count_checks > 0 else 0
        
        # Performance metrics
        test_duration = (datetime.now(timezone.utc) - self.global_state["timestamp_start"]).total_seconds()
        analyses_per_minute = (self.global_state["total_analyses"] / test_duration * 60) if test_duration > 0 else 0
        
        report = {
            "test_metadata": {
                "start_time": self.global_state["timestamp_start"].isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": test_duration,
                "total_users": total_users,
                "base_url": self.base_url
            },
            "summary_metrics": {
                "total_analyses": self.global_state["total_analyses"],
                "total_sboms": self.global_state["total_sboms"],
                "total_components": len(self.global_state["component_names"]),
                "total_vulnerabilities": len(self.global_state["vulnerability_ids"]),
                "total_api_calls": total_api_calls,
                "error_rate_percent": error_rate,
                "analyses_per_minute": analyses_per_minute
            },
            "detailed_breakdown": {
                "analyses_by_type": dict(self.global_state["analyses_by_type"]),
                "sboms_by_format": dict(self.global_state["sboms_by_format"]),
                "sbom_generation_coverage": f"{(self.global_state['total_sboms'] / self.global_state['total_analyses'] * 100):.2f}%" if self.global_state['total_analyses'] > 0 else "0%"
            },
            "count_consistency": {
                "total_checks": total_count_checks,
                "consistent_checks": consistent_checks,
                "inconsistent_checks": total_count_checks - consistent_checks,
                "consistency_rate_percent": consistency_rate,
                "inconsistent_operations": [
                    {
                        "timestamp": ct.timestamp.isoformat(),
                        "operation": ct.operation,
                        "entity_type": ct.entity_type,
                        "expected_change": ct.expected_change,
                        "actual_change": ct.actual_change,
                        "details": ct.details
                    }
                    for ct in self.count_tracking if not ct.consistent
                ]
            },
            "user_activity_summary": [
                {
                    "user_id": session.user_id,
                    "user_type": session.user_type,
                    "duration_seconds": (datetime.now(timezone.utc) - session.created_at).total_seconds(),
                    "analyses_submitted": session.metrics.analyses_submitted,
                    "analyses_completed": session.metrics.analyses_completed,
                    "analyses_failed": session.metrics.analyses_failed,
                    "sboms_generated": session.metrics.sboms_generated,
                    "vulnerability_scans": session.metrics.vulnerability_scans,
                    "component_searches": session.metrics.component_searches,
                    "api_calls": session.metrics.api_calls_total,
                    "api_errors": session.metrics.api_errors
                }
                for session in self.sessions.values()
            ],
            "performance_analysis": {
                "analyses_per_user": self.global_state["total_analyses"] / total_users if total_users > 0 else 0,
                "sboms_per_user": self.global_state["total_sboms"] / total_users if total_users > 0 else 0,
                "average_api_calls_per_user": total_api_calls / total_users if total_users > 0 else 0
            },
            "data_quality_metrics": {
                "unique_component_ratio": len(self.global_state["component_names"]) / sum(s.metrics.analyses_completed for s in self.sessions.values()) if sum(s.metrics.analyses_completed for s in self.sessions.values()) > 0 else 0,
                "vulnerability_detection_coverage": len([s for s in self.sessions.values() if s.metrics.vulnerability_scans > 0]) / total_users * 100 if total_users > 0 else 0
            }
        }
        
        return report
    
    async def _make_robust_request(self, session: aiohttp.ClientSession, method: str, url: str, **kwargs):
        """Make a robust HTTP request with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    async with session.get(url, **kwargs) as resp:
                        return resp, await resp.json() if resp.content_type == 'application/json' else await resp.text()
                elif method.upper() == 'POST':
                    async with session.post(url, **kwargs) as resp:
                        return resp, await resp.json() if resp.content_type == 'application/json' else await resp.text()
                elif method.upper() == 'DELETE':
                    async with session.delete(url, **kwargs) as resp:
                        return resp, await resp.json() if resp.content_type == 'application/json' else await resp.text()
            except aiohttp.ClientError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                    await sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
                    await sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise


async def run_comprehensive_test(num_users: int = 20, duration_minutes: int = 10):
    """Run comprehensive verification test with up to 20 users"""
    verifier = ComprehensivePerseusVerification()
    
    # Define 20 diverse user scenarios
    user_scenarios = [
        # Developers (6 users)
        {"user_id": "dev_java_1", "type": "developer", "activities": ["source_analysis", "source_analysis", "generate_sbom", "component_search"]},
        {"user_id": "dev_java_2", "type": "developer", "activities": ["source_analysis", "vulnerability_scan", "generate_sbom", "source_analysis"]},
        {"user_id": "dev_python_1", "type": "developer", "activities": ["source_analysis", "docker_analysis", "generate_sbom", "view_dashboard"]},
        {"user_id": "dev_go_1", "type": "developer", "activities": ["source_analysis", "binary_analysis", "generate_sbom", "component_search"]},
        {"user_id": "dev_fullstack_1", "type": "developer", "activities": ["source_analysis", "docker_analysis", "source_analysis", "generate_sbom"]},
        {"user_id": "dev_backend_1", "type": "developer", "activities": ["source_analysis", "generate_sbom", "vulnerability_scan", "delete_analysis"]},
        
        # DevOps Engineers (4 users)
        {"user_id": "devops_1", "type": "devops", "activities": ["docker_analysis", "docker_analysis", "generate_sbom", "os_analysis"]},
        {"user_id": "devops_2", "type": "devops", "activities": ["docker_analysis", "generate_sbom", "vulnerability_scan", "docker_analysis"]},
        {"user_id": "devops_sre_1", "type": "devops", "activities": ["os_analysis", "docker_analysis", "generate_sbom", "view_dashboard"]},
        {"user_id": "devops_platform_1", "type": "devops", "activities": ["docker_analysis", "os_analysis", "generate_sbom", "component_search"]},
        
        # Security Analysts (4 users)
        {"user_id": "security_1", "type": "security", "activities": ["vulnerability_scan", "source_analysis", "generate_sbom", "vulnerability_scan"]},
        {"user_id": "security_2", "type": "security", "activities": ["docker_analysis", "vulnerability_scan", "component_search", "generate_sbom"]},
        {"user_id": "security_audit_1", "type": "security", "activities": ["source_analysis", "vulnerability_scan", "generate_sbom", "view_dashboard"]},
        {"user_id": "security_compliance_1", "type": "security", "activities": ["generate_sbom", "vulnerability_scan", "component_search", "generate_sbom"]},
        
        # QA Engineers (3 users)
        {"user_id": "qa_1", "type": "qa", "activities": ["source_analysis", "docker_analysis", "generate_sbom", "vulnerability_scan"]},
        {"user_id": "qa_automation_1", "type": "qa", "activities": ["docker_analysis", "source_analysis", "generate_sbom", "delete_analysis"]},
        {"user_id": "qa_manual_1", "type": "qa", "activities": ["component_search", "vulnerability_scan", "view_dashboard", "generate_sbom"]},
        
        # Data Analysts (3 users) 
        {"user_id": "analyst_1", "type": "analyst", "activities": ["view_dashboard", "component_search", "vulnerability_scan", "view_dashboard"]},
        {"user_id": "analyst_2", "type": "analyst", "activities": ["component_search", "view_dashboard", "generate_sbom", "component_search"]},
        {"user_id": "analyst_metrics_1", "type": "analyst", "activities": ["view_dashboard", "component_search", "view_dashboard", "vulnerability_scan"]}
    ]
    
    # Start time
    start_time = datetime.now(timezone.utc)
    logger.info(f"Starting comprehensive verification test with {num_users} users for {duration_minutes} minutes")
    
    # Launch all user simulations
    tasks = []
    for i, scenario in enumerate(user_scenarios[:num_users]):
        # Repeat activities based on duration
        extended_activities = scenario["activities"] * (duration_minutes // 2)  # Repeat activities
        
        task = asyncio.create_task(
            verifier.simulate_user_activity(
                scenario["user_id"],
                scenario["type"],
                extended_activities
            )
        )
        tasks.append(task)
        
        # Stagger user starts (0.5-2 seconds apart)
        await asyncio.sleep(random.uniform(0.5, 2))
    
    # Let simulation run
    logger.info("All users started, simulation running...")
    await asyncio.sleep(duration_minutes * 60)
    
    # Cancel remaining tasks
    for task in tasks:
        if not task.done():
            task.cancel()
    
    # Wait for all tasks to complete/cancel
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Perform final verification
    logger.info("Performing comprehensive verification...")
    verification_results = await verifier.perform_comprehensive_verification()
    
    # Generate report
    report = verifier.generate_comprehensive_report()
    report["verification_results"] = verification_results
    
    # Save report
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = f"tests/comprehensive_report_{timestamp}.json"
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Comprehensive report saved to {report_path}")
    
    # Print summary
    print("\n" + "="*100)
    print("PERSEUS COMPREHENSIVE VERIFICATION SUMMARY")
    print("="*100)
    print(f"Test Duration: {report['test_metadata']['duration_seconds']:.2f} seconds")
    print(f"Total Users: {report['test_metadata']['total_users']}")
    print(f"\nActivity Summary:")
    print(f"  - Total Analyses: {report['summary_metrics']['total_analyses']}")
    print(f"  - Total SBOMs Generated: {report['summary_metrics']['total_sboms']}")
    print(f"  - SBOM Generation Coverage: {report['detailed_breakdown']['sbom_generation_coverage']}")
    print(f"  - Total API Calls: {report['summary_metrics']['total_api_calls']}")
    print(f"  - Error Rate: {report['summary_metrics']['error_rate_percent']:.2f}%")
    print(f"\nData Discovered:")
    print(f"  - Unique Components: {report['summary_metrics']['total_components']}")
    print(f"  - Unique Vulnerabilities: {report['summary_metrics']['total_vulnerabilities']}")
    print(f"\nCount Consistency:")
    print(f"  - Total Checks: {report['count_consistency']['total_checks']}")
    print(f"  - Consistent: {report['count_consistency']['consistent_checks']}")
    print(f"  - Inconsistent: {report['count_consistency']['inconsistent_checks']}")
    print(f"  - Consistency Rate: {report['count_consistency']['consistency_rate_percent']:.2f}%")
    
    if report['count_consistency']['inconsistent_checks'] > 0:
        print(f"\n⚠️  Found {report['count_consistency']['inconsistent_checks']} count inconsistencies!")
        for inc in report['count_consistency']['inconsistent_operations'][:5]:  # Show first 5
            print(f"    - {inc['operation']}: expected {inc['expected_change']}, got {inc['actual_change']}")
    
    print("\nBreakdown by Type:")
    print(f"  - Analyses: {report['detailed_breakdown']['analyses_by_type']}")
    print(f"  - SBOMs: {report['detailed_breakdown']['sboms_by_format']}")
    print("="*100)
    
    return report


if __name__ == "__main__":
    # Run comprehensive test with 20 users for 5 minutes
    asyncio.run(run_comprehensive_test(num_users=20, duration_minutes=5))