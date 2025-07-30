#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Automated Verification System for Perseus Prototype
Simulates concurrent users and verifies data consistency
"""

import asyncio
import aiohttp
import random
import time
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    """Represents a simulated user session"""
    user_id: str
    session_id: str
    created_at: datetime
    analyses: List[str] = field(default_factory=list)
    sboms: List[str] = field(default_factory=list)
    components_seen: int = 0
    vulnerabilities_seen: int = 0
    
@dataclass
class ConsistencyCheck:
    """Result of a consistency check"""
    timestamp: datetime
    check_type: str
    expected: Any
    actual: Any
    passed: bool
    details: Optional[str] = None

class PerseusVerificationSystem:
    """Automated verification system for Perseus"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.sessions: Dict[str, UserSession] = {}
        self.consistency_checks: List[ConsistencyCheck] = []
        self.lock = threading.Lock()
        self.global_state = {
            "total_analyses": 0,
            "total_components": 0,
            "total_vulnerabilities": 0,
            "analyses_by_type": {},
            "component_names": set(),
            "vulnerability_ids": set()
        }
        
    async def create_user_session(self, user_id: str) -> UserSession:
        """Create a new user session"""
        session = UserSession(
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        with self.lock:
            self.sessions[user_id] = session
        logger.info(f"Created session for user {user_id}")
        return session
    
    async def simulate_user_activity(self, user_id: str, analysis_types: List[str]):
        """Simulate a user performing various analyses"""
        session = await self.create_user_session(user_id)
        
        async with aiohttp.ClientSession() as client_session:
            for analysis_type in analysis_types:
                try:
                    if analysis_type == "source":
                        await self._simulate_source_analysis(client_session, session)
                    elif analysis_type == "docker":
                        await self._simulate_docker_analysis(client_session, session)
                    elif analysis_type == "os":
                        await self._simulate_os_analysis(client_session, session)
                    elif analysis_type == "binary":
                        await self._simulate_binary_analysis(client_session, session)
                    
                    # Random delay between operations
                    await asyncio.sleep(random.uniform(1, 3))
                    
                    # Check results and verify consistency
                    await self._check_analysis_results(client_session, session)
                    
                except Exception as e:
                    logger.error(f"User {user_id} encountered error: {e}")
    
    async def _simulate_source_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Simulate source code analysis"""
        # Use sample projects in the data directory
        sample_projects = [
            "data/sample-java-project",
            "data/vulnerable-java-app",
            "data/vulnerable-java-web",
            "examples/java-nato-library"
        ]
        
        project_path = random.choice(sample_projects)
        
        request_data = {
            "location": project_path,
            "type": "source",
            "language": "java"
        }
        
        async with session.post(f"{self.base_url}/analyze/source", json=request_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                analysis_id = result.get("analysis_id")
                user_session.analyses.append(analysis_id)
                logger.info(f"User {user_session.user_id} started source analysis {analysis_id}")
                
                with self.lock:
                    self.global_state["total_analyses"] += 1
                    self.global_state["analyses_by_type"]["source"] = \
                        self.global_state["analyses_by_type"].get("source", 0) + 1
    
    async def _simulate_docker_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Simulate Docker image analysis"""
        docker_images = [
            "alpine:latest",
            "ubuntu:22.04",
            "nginx:latest",
            "python:3.9-slim"
        ]
        
        image = random.choice(docker_images)
        
        request_data = {
            "location": image,
            "type": "docker"
        }
        
        async with session.post(f"{self.base_url}/analyze/docker", json=request_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                analysis_id = result.get("analysis_id")
                user_session.analyses.append(analysis_id)
                logger.info(f"User {user_session.user_id} started docker analysis {analysis_id}")
                
                with self.lock:
                    self.global_state["total_analyses"] += 1
                    self.global_state["analyses_by_type"]["docker"] = \
                        self.global_state["analyses_by_type"].get("docker", 0) + 1
    
    async def _simulate_os_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Simulate OS analysis"""
        request_data = {
            "location": "/",
            "type": "os"
        }
        
        async with session.post(f"{self.base_url}/analyze/os", json=request_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                analysis_id = result.get("analysis_id")
                user_session.analyses.append(analysis_id)
                logger.info(f"User {user_session.user_id} started OS analysis {analysis_id}")
                
                with self.lock:
                    self.global_state["total_analyses"] += 1
                    self.global_state["analyses_by_type"]["os"] = \
                        self.global_state["analyses_by_type"].get("os", 0) + 1
    
    async def _simulate_binary_analysis(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Simulate binary analysis"""
        # Look for sample binaries
        binary_path = "data/sample-macos-app/sample-macos-static-app"
        
        if not Path(binary_path).exists():
            logger.warning(f"Binary {binary_path} not found, skipping")
            return
        
        request_data = {
            "location": binary_path,
            "type": "binary"
        }
        
        async with session.post(f"{self.base_url}/analyze/binary", json=request_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                analysis_id = result.get("analysis_id")
                user_session.analyses.append(analysis_id)
                logger.info(f"User {user_session.user_id} started binary analysis {analysis_id}")
                
                with self.lock:
                    self.global_state["total_analyses"] += 1
                    self.global_state["analyses_by_type"]["binary"] = \
                        self.global_state["analyses_by_type"].get("binary", 0) + 1
    
    async def _check_analysis_results(self, session: aiohttp.ClientSession, user_session: UserSession):
        """Check analysis results and track components/vulnerabilities"""
        for analysis_id in user_session.analyses:
            # Wait for analysis to complete
            await self._wait_for_analysis_completion(session, analysis_id)
            
            # Get results
            async with session.get(f"{self.base_url}/analyze/{analysis_id}/results") as resp:
                if resp.status == 200:
                    results = await resp.json()
                    
                    # Track components
                    components = results.get("components", [])
                    user_session.components_seen += len(components)
                    
                    with self.lock:
                        for comp in components:
                            self.global_state["component_names"].add(f"{comp.get('name')}:{comp.get('version')}")
                    
                    # Check for vulnerabilities
                    async with session.get(f"{self.base_url}/api/v1/vulnerabilities/detailed/{analysis_id}") as vuln_resp:
                        if vuln_resp.status == 200:
                            vuln_data = await vuln_resp.json()
                            vulnerabilities = vuln_data.get("vulnerabilities", [])
                            user_session.vulnerabilities_seen += len(vulnerabilities)
                            
                            with self.lock:
                                for vuln in vulnerabilities:
                                    self.global_state["vulnerability_ids"].add(vuln.get("id"))
    
    async def _wait_for_analysis_completion(self, session: aiohttp.ClientSession, analysis_id: str, timeout: int = 60):
        """Wait for an analysis to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with session.get(f"{self.base_url}/analyze/{analysis_id}/status") as resp:
                if resp.status == 200:
                    status_data = await resp.json()
                    status = status_data.get("status")
                    
                    if status in ["completed", "failed"]:
                        return status
            
            await asyncio.sleep(2)
        
        logger.warning(f"Analysis {analysis_id} timed out")
        return "timeout"
    
    async def verify_global_consistency(self):
        """Verify global data consistency across all users"""
        async with aiohttp.ClientSession() as session:
            # Check total analyses count
            async with session.get(f"{self.base_url}/api/v1/analyses") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    db_total = data.get("total", 0)
                    
                    check = ConsistencyCheck(
                        timestamp=datetime.utcnow(),
                        check_type="total_analyses_count",
                        expected=self.global_state["total_analyses"],
                        actual=db_total,
                        passed=db_total >= self.global_state["total_analyses"],
                        details=f"Database has {db_total} analyses, tracked {self.global_state['total_analyses']}"
                    )
                    self.consistency_checks.append(check)
            
            # Check component counts
            unique_components_tracked = len(self.global_state["component_names"])
            
            async with session.get(f"{self.base_url}/api/v1/components/unique") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    db_unique = data.get("total", 0)
                    
                    check = ConsistencyCheck(
                        timestamp=datetime.utcnow(),
                        check_type="unique_components_count",
                        expected=unique_components_tracked,
                        actual=db_unique,
                        passed=db_unique >= unique_components_tracked * 0.9,  # Allow 10% variance
                        details=f"Database has {db_unique} unique components, tracked {unique_components_tracked}"
                    )
                    self.consistency_checks.append(check)
            
            # Check vulnerability consistency
            vulnerabilities_tracked = len(self.global_state["vulnerability_ids"])
            
            async with session.get(f"{self.base_url}/api/v1/vulnerabilities") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    db_vulns = data.get("total", 0)
                    
                    check = ConsistencyCheck(
                        timestamp=datetime.utcnow(),
                        check_type="total_vulnerabilities_count",
                        expected=vulnerabilities_tracked,
                        actual=db_vulns,
                        passed=db_vulns >= vulnerabilities_tracked * 0.9,  # Allow 10% variance
                        details=f"Database has {db_vulns} vulnerabilities, tracked {vulnerabilities_tracked}"
                    )
                    self.consistency_checks.append(check)
            
            # Verify count validation endpoint
            async with session.get(f"{self.base_url}/api/v1/counts/validate/all") as resp:
                if resp.status == 200:
                    validation_data = await resp.json()
                    total_discrepancies = validation_data.get("total_discrepancies", 0)
                    
                    check = ConsistencyCheck(
                        timestamp=datetime.utcnow(),
                        check_type="count_validation",
                        expected=0,
                        actual=total_discrepancies,
                        passed=total_discrepancies == 0,
                        details=f"Count validation found {total_discrepancies} discrepancies"
                    )
                    self.consistency_checks.append(check)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive verification report"""
        total_checks = len(self.consistency_checks)
        passed_checks = sum(1 for check in self.consistency_checks if check.passed)
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_users": len(self.sessions),
                "total_analyses": self.global_state["total_analyses"],
                "analyses_by_type": self.global_state["analyses_by_type"],
                "unique_components": len(self.global_state["component_names"]),
                "unique_vulnerabilities": len(self.global_state["vulnerability_ids"]),
                "consistency_checks": {
                    "total": total_checks,
                    "passed": passed_checks,
                    "failed": total_checks - passed_checks,
                    "pass_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0
                }
            },
            "user_sessions": [
                {
                    "user_id": session.user_id,
                    "session_id": session.session_id,
                    "duration": (datetime.utcnow() - session.created_at).total_seconds(),
                    "analyses_performed": len(session.analyses),
                    "components_seen": session.components_seen,
                    "vulnerabilities_seen": session.vulnerabilities_seen
                }
                for session in self.sessions.values()
            ],
            "consistency_checks": [
                {
                    "timestamp": check.timestamp.isoformat(),
                    "type": check.check_type,
                    "expected": check.expected,
                    "actual": check.actual,
                    "passed": check.passed,
                    "details": check.details
                }
                for check in self.consistency_checks
            ],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        # Check for consistency failures
        failed_checks = [check for check in self.consistency_checks if not check.passed]
        if failed_checks:
            recommendations.append("Data consistency issues detected - review count synchronization logic")
            
            for check in failed_checks:
                if check.check_type == "count_validation":
                    recommendations.append("Run count fix endpoint to resolve discrepancies: POST /api/v1/counts/fix/all")
                elif check.check_type == "total_analyses_count":
                    recommendations.append("Analysis count mismatch - check for missing or duplicate records")
        
        # Check for performance issues
        slow_analyses = []
        for session in self.sessions.values():
            if session.analyses and len(session.analyses) > 0:
                avg_time = (datetime.utcnow() - session.created_at).total_seconds() / len(session.analyses)
                if avg_time > 30:  # More than 30 seconds per analysis
                    slow_analyses.append(session.user_id)
        
        if slow_analyses:
            recommendations.append(f"Performance issues detected for users: {', '.join(slow_analyses)}")
        
        return recommendations if recommendations else ["All consistency checks passed - system is functioning correctly"]


async def run_verification(num_users: int = 7, duration_minutes: int = 5):
    """Run the automated verification"""
    verifier = PerseusVerificationSystem()
    
    # Define user scenarios
    user_scenarios = [
        # User 1: Java developer focusing on source analysis
        {"user_id": "java_dev_1", "analyses": ["source", "source", "source"]},
        
        # User 2: DevOps engineer working with Docker
        {"user_id": "devops_1", "analyses": ["docker", "docker", "os"]},
        
        # User 3: Security analyst doing mixed analyses
        {"user_id": "security_1", "analyses": ["source", "docker", "binary", "os"]},
        
        # User 4: QA engineer testing various scenarios
        {"user_id": "qa_1", "analyses": ["source", "docker", "source", "docker"]},
        
        # User 5: System admin focusing on OS analysis
        {"user_id": "sysadmin_1", "analyses": ["os", "os", "binary"]},
        
        # User 6: Developer doing rapid iterations
        {"user_id": "dev_2", "analyses": ["source", "source", "source", "source", "source"]},
        
        # User 7: Mixed usage pattern
        {"user_id": "mixed_user_1", "analyses": ["docker", "source", "os", "docker", "binary"]}
    ]
    
    # Start concurrent user simulations
    tasks = []
    for scenario in user_scenarios[:num_users]:
        task = asyncio.create_task(
            verifier.simulate_user_activity(
                scenario["user_id"],
                scenario["analyses"]
            )
        )
        tasks.append(task)
        
        # Stagger user starts
        await asyncio.sleep(random.uniform(0.5, 2))
    
    # Let simulations run
    logger.info(f"Running verification for {duration_minutes} minutes with {num_users} users...")
    await asyncio.sleep(duration_minutes * 60)
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Perform consistency checks
    logger.info("Performing global consistency verification...")
    await verifier.verify_global_consistency()
    
    # Generate and save report
    report = verifier.generate_report()
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = f"tests/verification_report_{timestamp}.json"
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report saved to {report_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("PERSEUS AUTOMATED VERIFICATION SUMMARY")
    print("="*80)
    print(f"Total Users: {report['summary']['total_users']}")
    print(f"Total Analyses: {report['summary']['total_analyses']}")
    print(f"Analyses by Type: {report['summary']['analyses_by_type']}")
    print(f"Unique Components: {report['summary']['unique_components']}")
    print(f"Unique Vulnerabilities: {report['summary']['unique_vulnerabilities']}")
    print(f"\nConsistency Checks:")
    print(f"  - Total: {report['summary']['consistency_checks']['total']}")
    print(f"  - Passed: {report['summary']['consistency_checks']['passed']}")
    print(f"  - Failed: {report['summary']['consistency_checks']['failed']}")
    print(f"  - Pass Rate: {report['summary']['consistency_checks']['pass_rate']:.2f}%")
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    print("="*80)
    
    return report


if __name__ == "__main__":
    # Run the verification
    asyncio.run(run_verification(num_users=7, duration_minutes=2))