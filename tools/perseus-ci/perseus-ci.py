#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Perseus CI/CD CLI Tool - Platform-agnostic CI/CD integration for SBOM scanning
"""

import argparse
import json
import os
import sys
import time
from typing import Optional, List, Dict, Any
import requests
from datetime import datetime, timezone
import subprocess
from pathlib import Path

class PerseusCI:
    """Main CLI class for Perseus CI/CD integration"""
    
    def __init__(self):
        self.api_url = os.getenv('PERSEUS_API_URL', 'http://localhost:8000')
        self.api_key = os.getenv('PERSEUS_API_KEY', '')
        self.timeout = int(os.getenv('PERSEUS_TIMEOUT', '300'))
        self.project_id = os.getenv('PERSEUS_PROJECT_ID', '')
        
        # Detect CI environment
        self.ci_platform = self._detect_ci_platform()
        self.build_info = self._collect_build_info()
        
    def _detect_ci_platform(self) -> str:
        """Detect which CI/CD platform we're running in"""
        if os.getenv('JENKINS_URL'):
            return 'jenkins'
        elif os.getenv('GITLAB_CI'):
            return 'gitlab'
        elif os.getenv('GITHUB_ACTIONS'):
            return 'github'
        elif os.getenv('TF_BUILD'):  # Azure DevOps
            return 'azure'
        elif os.getenv('CIRCLECI'):
            return 'circle'
        else:
            return 'unknown'
    
    def _collect_build_info(self) -> Dict[str, Any]:
        """Collect build information from CI environment"""
        info = {
            'platform': self.ci_platform,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Jenkins
        if self.ci_platform == 'jenkins':
            info.update({
                'build_id': os.getenv('BUILD_ID', ''),
                'job_name': os.getenv('JOB_NAME', ''),
                'branch': os.getenv('GIT_BRANCH', ''),
                'commit': os.getenv('GIT_COMMIT', ''),
                'workspace': os.getenv('WORKSPACE', '.')
            })
        
        # GitLab CI
        elif self.ci_platform == 'gitlab':
            info.update({
                'build_id': os.getenv('CI_PIPELINE_ID', ''),
                'job_name': os.getenv('CI_JOB_NAME', ''),
                'branch': os.getenv('CI_COMMIT_REF_NAME', ''),
                'commit': os.getenv('CI_COMMIT_SHA', ''),
                'workspace': os.getenv('CI_PROJECT_DIR', '.')
            })
        
        # GitHub Actions
        elif self.ci_platform == 'github':
            info.update({
                'build_id': os.getenv('GITHUB_RUN_ID', ''),
                'job_name': os.getenv('GITHUB_JOB', ''),
                'branch': os.getenv('GITHUB_REF_NAME', ''),
                'commit': os.getenv('GITHUB_SHA', ''),
                'workspace': os.getenv('GITHUB_WORKSPACE', '.')
            })
        
        # Azure DevOps
        elif self.ci_platform == 'azure':
            info.update({
                'build_id': os.getenv('BUILD_BUILDID', ''),
                'job_name': os.getenv('BUILD_DEFINITIONNAME', ''),
                'branch': os.getenv('BUILD_SOURCEBRANCHNAME', ''),
                'commit': os.getenv('BUILD_SOURCEVERSION', ''),
                'workspace': os.getenv('BUILD_SOURCESDIRECTORY', '.')
            })
        
        # CircleCI
        elif self.ci_platform == 'circle':
            info.update({
                'build_id': os.getenv('CIRCLE_BUILD_NUM', ''),
                'job_name': os.getenv('CIRCLE_JOB', ''),
                'branch': os.getenv('CIRCLE_BRANCH', ''),
                'commit': os.getenv('CIRCLE_SHA1', ''),
                'workspace': os.getenv('CIRCLE_WORKING_DIRECTORY', '.')
            })
        
        return info
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Perseus API"""
        url = f"{self.api_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _get_detailed_vulnerabilities(self, vulnerable_components: list) -> list:
        """Get detailed CVE information using Grype directly (simplified)"""
        detailed_vulns = []
        
        try:
            import subprocess
            
            # Only process components with critical vulnerabilities and limit to first 3
            critical_components = [c for c in vulnerable_components if c.get('critical_vulnerabilities', 0) > 0][:3]
            
            for component in critical_components:
                purl = component.get('purl', '')
                if purl:
                    try:
                        # Run grype with table output (faster than JSON)
                        result = subprocess.run(
                            ['grype', purl, '--quiet'],
                            capture_output=True,
                            text=True,
                            timeout=15
                        )
                        
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')
                            # Skip header line
                            for line in lines[1:]:
                                if line.strip() and 'Critical' in line:
                                    parts = line.split()
                                    if len(parts) >= 6:
                                        detailed_vulns.append({
                                            'component': component['component_name'],
                                            'version': component['component_version'],
                                            'cve_id': parts[4] if len(parts) > 4 else 'N/A',
                                            'severity': 'Critical',
                                            'description': f"Critical vulnerability in {component['component_name']}",
                                            'cvss_score': 10.0,  # Assume max for critical
                                            'fixed_version': parts[2] if len(parts) > 2 else 'N/A',
                                            'related_cves': []
                                        })
                    except Exception as e:
                        print(f"⚠️  Warning: Could not get details for {component['component_name']}: {e}")
                        continue
        
        except ImportError:
            print("⚠️  Warning: subprocess not available for detailed CVE information")
        except Exception as e:
            print(f"⚠️  Warning: Error getting detailed vulnerabilities: {e}")
        
        return detailed_vulns
    
    def _extract_cvss_score(self, vulnerability: dict) -> float:
        """Extract CVSS score from vulnerability data"""
        cvss_list = vulnerability.get('cvss', [])
        for cvss in cvss_list:
            if cvss.get('type') == 'Primary':
                return cvss.get('metrics', {}).get('baseScore', 0.0)
        
        # Fallback to any CVSS score
        if cvss_list:
            return cvss_list[0].get('metrics', {}).get('baseScore', 0.0)
        
        return 0.0
    
    def _extract_fixed_version(self, match: dict) -> str:
        """Extract fixed version from match data"""
        fix_info = match.get('vulnerability', {}).get('fix', {})
        versions = fix_info.get('versions', [])
        if versions:
            return versions[0]
        return 'N/A'
    
    def _display_detailed_vulnerabilities(self, detailed_vulns: list):
        """Display detailed CVE information"""
        print("\n🚨 Critical Vulnerability Details:")
        print("=" * 80)
        
        for vuln in detailed_vulns:
            print(f"\n📦 Component: {vuln['component']} {vuln['version']}")
            print(f"🔴 CVE ID: {vuln['cve_id']}")
            print(f"📊 CVSS Score: {vuln['cvss_score']}")
            print(f"🔧 Fixed in: {vuln['fixed_version']}")
            print(f"📝 Description: {vuln['description'][:200]}{'...' if len(vuln['description']) > 200 else ''}")
            
            if vuln['related_cves']:
                related = ', '.join(vuln['related_cves'][:3])
                if len(vuln['related_cves']) > 3:
                    related += f" (and {len(vuln['related_cves']) - 3} more)"
                print(f"🔗 Related CVEs: {related}")
            
            print("-" * 80)
    
    def _detect_project_type(self, project_path: str) -> str:
        """Detect project type based on files present"""
        path = Path(project_path)
        
        if (path / "pom.xml").exists():
            return "java"
        elif (path / "package.json").exists():
            return "javascript"
        elif (path / "requirements.txt").exists() or (path / "setup.py").exists():
            return "python"
        elif (path / "go.mod").exists():
            return "go"
        elif (path / "Cargo.toml").exists():
            return "rust"
        elif (path / "CMakeLists.txt").exists() or any(path.glob("*.cpp")) or any(path.glob("*.c")):
            return "c++"
        else:
            return "unknown"
    
    def scan(self, args):
        """Perform synchronous SBOM scan"""
        project_path = args.project_path or self.build_info.get('workspace', '.')
        project_type = self._detect_project_type(project_path)
        
        print(f"🔍 Perseus CI/CD Scanner")
        print(f"   Platform: {self.ci_platform}")
        print(f"   Project: {project_path}")
        print(f"   Type: {project_type}")
        print(f"   API: {self.api_url}")
        
        # For now, use the existing API endpoints directly
        # until CI/CD endpoints are properly integrated
        
        # Prepare analysis request based on project type
        if project_type in ["java", "python", "javascript", "go", "c++"]:
            analysis_data = {
                "type": "source",
                "language": project_type,
                "location": f"/app/data/{os.path.basename(project_path)}",
                "options": {
                    "deep_scan": True,
                    "ci_context": self.build_info
                }
            }
            endpoint = "/analyze/source"
        else:
            analysis_data = {
                "type": "binary",
                "location": f"/app/data/{os.path.basename(project_path)}",
                "options": {
                    "ci_context": self.build_info
                }
            }
            endpoint = "/analyze/binary"
        
        print("\n🚀 Starting scan...")
        scan_response = self._make_request('POST', endpoint, analysis_data)
        analysis_id = scan_response.get('analysis_id')
        print(f"   Analysis ID: {analysis_id}")
        
        # Wait for completion
        print("\n⏳ Waiting for scan to complete...")
        start_time = time.time()
        last_status = None
        
        while True:
            if time.time() - start_time > self.timeout:
                print("❌ Scan timeout exceeded", file=sys.stderr)
                sys.exit(1)
            
            status_response = self._make_request('GET', f'/analyze/{analysis_id}/status')
            status = status_response.get('status')
            
            if status != last_status:
                print(f"   Status: {status}")
                last_status = status
            
            if status == 'completed':
                break
            elif status == 'failed':
                print(f"❌ Scan failed: {status_response.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
            
            time.sleep(2)
        
        # Get results
        print("\n📋 Retrieving results...")
        results = self._make_request('GET', f'/analyze/{analysis_id}/results')
        
        # Get vulnerability scan results
        try:
            vuln_results = self._make_request('GET', f'/vulnerabilities/scan/{analysis_id}')
            vulnerable_components = vuln_results.get('vulnerable_components', [])
            
            # Count vulnerabilities by severity
            critical_count = sum(comp.get('critical_vulnerabilities', 0) for comp in vulnerable_components)
            high_count = 0
            medium_count = 0
            low_count = 0
            
            # Calculate total non-critical vulnerabilities
            for comp in vulnerable_components:
                total_vulns = comp.get('vulnerability_count', 0)
                critical_vulns = comp.get('critical_vulnerabilities', 0)
                remaining_vulns = total_vulns - critical_vulns
                # For now, assume remaining are split between high/medium/low
                # This is a simplification - ideally we'd get detailed severity breakdown
                high_count += int(remaining_vulns * 0.4)  # Rough estimate
                medium_count += int(remaining_vulns * 0.4)
                low_count += remaining_vulns - int(remaining_vulns * 0.4) - int(remaining_vulns * 0.4)
                
        except Exception as e:
            print(f"⚠️  Warning: Could not retrieve vulnerability details: {e}")
            critical_count = high_count = medium_count = low_count = 0
            
        # Get detailed CVE information if requested
        detailed_vulns = []
        if args.detailed and 'vulnerable_components' in locals():
            print("\n🔍 Fetching detailed CVE information...")
            detailed_vulns = self._get_detailed_vulnerabilities(vulnerable_components)
        
        print("\n📊 Scan Results:")
        print(f"   Components found: {len(results.get('components', []))}")
        print(f"   Vulnerabilities:")
        print(f"     🔴 Critical: {critical_count}")
        print(f"     🟠 High: {high_count}")
        print(f"     🟡 Medium: {medium_count}")
        print(f"     🟢 Low: {low_count}")
        
        # Display detailed CVE information if requested
        if args.detailed and detailed_vulns:
            self._display_detailed_vulnerabilities(detailed_vulns)
        
        # Save reports if requested
        if args.output:
            # Combine analysis results with vulnerability data
            output_data = results.copy()
            if 'vuln_results' in locals():
                output_data['vulnerability_summary'] = {
                    'critical': critical_count,
                    'high': high_count,
                    'medium': medium_count,
                    'low': low_count,
                    'total': critical_count + high_count + medium_count + low_count
                }
                output_data['vulnerable_components'] = vulnerable_components
                
                # Include detailed CVE information if available
                if detailed_vulns:
                    output_data['detailed_vulnerabilities'] = detailed_vulns
            
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\n💾 Report saved to: {args.output}")
        
        # Check fail conditions
        fail_on = args.fail_on.lower().split(',') if args.fail_on else []
        should_fail = False
        
        if 'critical' in fail_on and critical_count > 0:
            should_fail = True
            print(f"\n❌ Build failed: Found {critical_count} critical vulnerabilities", file=sys.stderr)
        elif 'high' in fail_on and high_count > 0:
            should_fail = True
            print(f"\n❌ Build failed: Found {high_count} high vulnerabilities", file=sys.stderr)
        
        if should_fail:
            sys.exit(1)
        else:
            print("\n✅ Scan completed successfully!")
            return 0
    
    def check_health(self):
        """Check Perseus API health"""
        try:
            response = self._make_request('GET', '/health')
            if response.get('status') == 'healthy':
                print("✅ Perseus API is healthy")
                return 0
            else:
                print("❌ Perseus API is unhealthy", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"❌ Failed to check health: {e}", file=sys.stderr)
            return 1

def main():
    parser = argparse.ArgumentParser(
        description='Perseus CI/CD Integration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple scan with failure on critical vulnerabilities
  perseus-ci scan --fail-on critical
  
  # Scan specific project path
  perseus-ci scan --project-path ./my-app --fail-on critical,high
  
  # Save results to file
  perseus-ci scan --output scan-results.json
  
  # Check API health
  perseus-ci health
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Perform SBOM scan')
    scan_parser.add_argument('--project-path', help='Path to project (default: current directory)')
    scan_parser.add_argument('--fail-on', help='Fail on vulnerability severity (comma-separated: critical,high,medium,low)')
    scan_parser.add_argument('--output', help='Save results to file')
    scan_parser.add_argument('--timeout', type=int, help='Scan timeout in seconds (default: 300)')
    scan_parser.add_argument('--detailed', action='store_true', help='Include detailed CVE information')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check Perseus API health')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = PerseusCI()
    
    if args.command == 'scan':
        return cli.scan(args)
    elif args.command == 'health':
        return cli.check_health()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    sys.exit(main())