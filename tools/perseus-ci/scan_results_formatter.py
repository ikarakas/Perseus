#!/usr/bin/env python3
"""
Scan Results Formatter - Visualize SBOM scan results
A comprehensive tool to format and display vulnerability scan results in various formats.
"""

import json
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter
import os

class ScanResultsFormatter:
    """Format and visualize scan results from JSON data."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.analysis_id = data.get('analysis_id', 'Unknown')
        self.status = data.get('status', 'Unknown')
        self.components = data.get('components', [])
        self.metadata = data.get('metadata', {})
        self.vulnerability_summary = data.get('vulnerability_summary', {})
        self.vulnerable_components = data.get('vulnerable_components', [])
        self.detailed_vulnerabilities = data.get('detailed_vulnerabilities', [])
    
    def print_header(self):
        """Print formatted header information."""
        print("=" * 80)
        print("🔍 SECURITY SCAN RESULTS")
        print("=" * 80)
        print(f"Analysis ID: {self.analysis_id}")
        print(f"Status: {self.status.upper()}")
        print(f"Analyzer: {self.metadata.get('analyzer', 'Unknown')}")
        print(f"Location: {self.metadata.get('location', 'Unknown')}")
        print(f"Analysis Type: {self.metadata.get('analysis_type', 'Unknown')}")
        print(f"Deep Scan: {'✓' if self.metadata.get('deep_scan') else '✗'}")
        print(f"Vulnerability Scan: {'✓' if self.metadata.get('vulnerability_scan_performed') else '✗'}")
        
        scan_date = self.metadata.get('vulnerability_scan_date')
        if scan_date:
            try:
                formatted_date = datetime.fromisoformat(scan_date.replace('Z', '+00:00'))
                print(f"Scan Date: {formatted_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            except:
                print(f"Scan Date: {scan_date}")
        print()
    
    def print_summary(self):
        """Print vulnerability summary."""
        print("📊 VULNERABILITY SUMMARY")
        print("-" * 40)
        
        total_components = self.metadata.get('components_found', len(self.components))
        vulnerable_components = self.metadata.get('vulnerable_components', len(self.vulnerable_components))
        total_vulns = self.vulnerability_summary.get('total', 0)
        
        print(f"Total Components: {total_components}")
        print(f"Vulnerable Components: {vulnerable_components}")
        print(f"Clean Components: {total_components - vulnerable_components}")
        print(f"Total Vulnerabilities: {total_vulns}")
        print()
        
        if self.vulnerability_summary:
            print("Vulnerability Breakdown:")
            critical = self.vulnerability_summary.get('critical', 0)
            high = self.vulnerability_summary.get('high', 0)
            medium = self.vulnerability_summary.get('medium', 0)
            low = self.vulnerability_summary.get('low', 0)
            
            print(f"  🔴 Critical: {critical:>3}")
            print(f"  🟠 High:     {high:>3}")
            print(f"  🟡 Medium:   {medium:>3}")
            print(f"  🟢 Low:      {low:>3}")
            print()
    
    def print_risk_assessment(self):
        """Print risk assessment based on vulnerabilities."""
        print("⚠️  RISK ASSESSMENT")
        print("-" * 40)
        
        critical = self.vulnerability_summary.get('critical', 0)
        high = self.vulnerability_summary.get('high', 0)
        medium = self.vulnerability_summary.get('medium', 0)
        
        if critical > 0:
            risk_level = "🚨 CRITICAL"
            color = "\033[91m"  # Red
        elif high > 0:
            risk_level = "🔥 HIGH"
            color = "\033[93m"  # Yellow
        elif medium > 0:
            risk_level = "⚠️  MEDIUM"
            color = "\033[33m"  # Orange
        else:
            risk_level = "✅ LOW"
            color = "\033[92m"  # Green
        
        reset = "\033[0m"
        print(f"Overall Risk Level: {color}{risk_level}{reset}")
        
        if critical > 0:
            print(f"⚡ Immediate action required! {critical} critical vulnerabilities found.")
        elif high > 0:
            print(f"🔥 High priority remediation needed for {high} high-severity issues.")
        elif medium > 0:
            print(f"⚠️  Medium risk - plan remediation for {medium} issues.")
        else:
            print("🎉 Good security posture - no high-risk vulnerabilities detected.")
        print()
    
    def print_components_table(self, show_clean: bool = False):
        """Print components in a formatted table."""
        print("📦 COMPONENT ANALYSIS")
        print("-" * 100)
        
        # Header
        header = f"{'Component Name':<30} {'Version':<15} {'Type':<15} {'Vulns':<6} {'Critical':<8}"
        print(header)
        print("-" * 100)
        
        # Sort components by vulnerability count (descending)
        sorted_components = sorted(
            self.components, 
            key=lambda x: (x.get('critical_vulnerabilities', 0), x.get('vulnerability_count', 0)),
            reverse=True
        )
        
        for component in sorted_components:
            name = component.get('name', 'Unknown')[:29]
            version = component.get('version', 'Unknown')[:14]
            comp_type = component.get('type', 'Unknown')[:14]
            vuln_count = component.get('vulnerability_count', 0)
            critical_count = component.get('critical_vulnerabilities', 0)
            
            # Skip clean components if not requested
            if not show_clean and vuln_count == 0:
                continue
            
            # Color coding based on vulnerability severity
            if critical_count > 0:
                color = "\033[91m"  # Red
                status = "🔴"
            elif vuln_count > 0:
                color = "\033[93m"  # Yellow  
                status = "🟡"
            else:
                color = "\033[92m"  # Green
                status = "✅"
            
            reset = "\033[0m"
            
            row = f"{color}{name:<30} {version:<15} {comp_type:<15} {vuln_count:<6} {critical_count:<8}{reset}"
            print(f"{status} {row}")
        
        print("-" * 100)
        print()
    
    def print_top_vulnerable_components(self, limit: int = 5):
        """Print the most vulnerable components."""
        print(f"🎯 TOP {limit} MOST VULNERABLE COMPONENTS")
        print("-" * 60)
        
        # Sort by critical vulnerabilities first, then by total vulnerabilities
        sorted_vulns = sorted(
            self.vulnerable_components,
            key=lambda x: (x.get('critical_vulnerabilities', 0), x.get('vulnerability_count', 0)),
            reverse=True
        )
        
        for i, component in enumerate(sorted_vulns[:limit], 1):
            name = component.get('component_name', 'Unknown')
            version = component.get('component_version', 'Unknown')
            total_vulns = component.get('vulnerability_count', 0)
            critical_vulns = component.get('critical_vulnerabilities', 0)
            
            print(f"{i}. {name} v{version}")
            print(f"   Total Vulnerabilities: {total_vulns}")
            if critical_vulns > 0:
                print(f"   🔴 Critical: {critical_vulns}")
            print(f"   PURL: {component.get('purl', 'N/A')}")
            print()
    
    def print_component_types_breakdown(self):
        """Print breakdown of component types."""
        print("📋 COMPONENT TYPES BREAKDOWN")
        print("-" * 40)
        
        type_counts = Counter(comp.get('type', 'Unknown') for comp in self.components)
        type_vulns = {}
        
        for comp in self.components:
            comp_type = comp.get('type', 'Unknown')
            vulns = comp.get('vulnerability_count', 0)
            if comp_type not in type_vulns:
                type_vulns[comp_type] = 0
            type_vulns[comp_type] += vulns
        
        for comp_type, count in type_counts.most_common():
            vulns = type_vulns.get(comp_type, 0)
            avg_vulns = vulns / count if count > 0 else 0
            print(f"{comp_type:<20}: {count:>3} components, {vulns:>3} total vulns (avg: {avg_vulns:.1f})")
        print()
    
    def print_detailed_vulnerabilities(self, limit: int = 10):
        """Print detailed CVE information when available."""
        if not self.detailed_vulnerabilities:
            return
        
        print("🚨 DETAILED VULNERABILITY INFORMATION")
        print("=" * 80)
        print(f"Showing {min(len(self.detailed_vulnerabilities), limit)} of {len(self.detailed_vulnerabilities)} detailed vulnerabilities")
        print()
        
        # Sort by severity (Critical first) and CVSS score
        severity_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1, 'Unknown': 0}
        sorted_vulns = sorted(
            self.detailed_vulnerabilities,
            key=lambda x: (severity_order.get(x.get('severity', 'Unknown'), 0), x.get('cvss_score', 0)),
            reverse=True
        )
        
        for i, vuln in enumerate(sorted_vulns[:limit], 1):
            component = vuln.get('component', 'Unknown')
            version = vuln.get('version', 'Unknown')
            cve_id = vuln.get('cve_id', 'N/A')
            severity = vuln.get('severity', 'Unknown')
            cvss_score = vuln.get('cvss_score', 0)
            description = vuln.get('description', 'No description available')
            fixed_version = vuln.get('fixed_version', 'N/A')
            
            # Color coding based on severity
            if severity == 'Critical':
                color = "\033[91m"  # Red
                emoji = "🔴"
            elif severity == 'High':
                color = "\033[93m"  # Yellow
                emoji = "🟠"
            elif severity == 'Medium':
                color = "\033[33m"  # Orange
                emoji = "🟡"
            else:
                color = "\033[92m"  # Green
                emoji = "🟢"
            
            reset = "\033[0m"
            
            print(f"{emoji} {color}CVE #{i}: {cve_id}{reset}")
            print(f"   📦 Component: {component} v{version}")
            print(f"   📊 Severity: {color}{severity}{reset} (CVSS: {cvss_score})")
            if fixed_version != 'N/A':
                print(f"   🔧 Fixed in: {fixed_version}")
            print(f"   📝 Description: {description[:100]}{'...' if len(description) > 100 else ''}")
            
            # Show related CVEs if available
            related_cves = vuln.get('related_cves', [])
            if related_cves:
                related_str = ', '.join(related_cves[:3])
                if len(related_cves) > 3:
                    related_str += f" (and {len(related_cves) - 3} more)"
                print(f"   🔗 Related: {related_str}")
            
            print("-" * 80)
        
        if len(self.detailed_vulnerabilities) > limit:
            print(f"... and {len(self.detailed_vulnerabilities) - limit} more vulnerabilities")
        print()
    
    def export_csv(self, filename: str = "scan_results.csv"):
        """Export results to CSV format."""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'component_name', 'version', 'type', 'purl', 'source_location',
                'vulnerability_count', 'critical_vulnerabilities', 'cves'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for component in self.components:
                # Extract CVE information from detailed vulnerabilities if available
                cves = []
                component_name = component.get('name', '')
                component_version = component.get('version', '')
                
                # Look for detailed vulnerabilities for this component
                for vuln in self.detailed_vulnerabilities:
                    if (vuln.get('component', '') == component_name and 
                        vuln.get('version', '') == component_version):
                        cve_id = vuln.get('cve_id', '')
                        if cve_id and cve_id != 'N/A':
                            cves.append(f"{cve_id} ({vuln.get('severity', 'Unknown')})")
                
                # Fallback to component-level vulnerability data if no detailed info
                if not cves:
                    vulnerabilities = component.get('vulnerabilities', [])
                    for vuln in vulnerabilities:
                        cve_id = vuln.get('cve_id') or vuln.get('id', '')
                        if cve_id.startswith('CVE-'):
                            cves.append(cve_id)
                
                writer.writerow({
                    'component_name': component_name,
                    'version': component_version,
                    'type': component.get('type', ''),
                    'purl': component.get('purl', ''),
                    'source_location': component.get('source_location', ''),
                    'vulnerability_count': component.get('vulnerability_count', 0),
                    'critical_vulnerabilities': component.get('critical_vulnerabilities', 0),
                    'cves': '; '.join(cves) if cves else 'N/A'
                })
        
        print(f"✅ Results exported to {filename}")
    
    def export_html(self, filename: str = "scan_results.html"):
        """Export results to HTML format."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Scan Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .summary {{ background-color: #e8f4fd; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .critical {{ color: #d32f2f; font-weight: bold; }}
                .high {{ color: #f57c00; font-weight: bold; }}
                .medium {{ color: #fbc02d; font-weight: bold; }}
                .low {{ color: #388e3c; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .vuln-count {{ text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 Security Scan Results</h1>
                <p><strong>Analysis ID:</strong> {self.analysis_id}</p>
                <p><strong>Status:</strong> {self.status}</p>
                <p><strong>Analyzer:</strong> {self.metadata.get('analyzer', 'Unknown')}</p>
                <p><strong>Location:</strong> {self.metadata.get('location', 'Unknown')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Vulnerability Summary</h2>
                <p><strong>Total Components:</strong> {self.metadata.get('components_found', len(self.components))}</p>
                <p><strong>Vulnerable Components:</strong> {self.metadata.get('vulnerable_components', len(self.vulnerable_components))}</p>
                <p><strong>Total Vulnerabilities:</strong> {self.vulnerability_summary.get('total', 0)}</p>
                <ul>
                    <li class="critical">Critical: {self.vulnerability_summary.get('critical', 0)}</li>
                    <li class="high">High: {self.vulnerability_summary.get('high', 0)}</li>
                    <li class="medium">Medium: {self.vulnerability_summary.get('medium', 0)}</li>
                    <li class="low">Low: {self.vulnerability_summary.get('low', 0)}</li>
                </ul>
            </div>
            
            <h2>📦 Components</h2>
            <table>
                <tr>
                    <th>Component Name</th>
                    <th>Version</th>
                    <th>Type</th>
                    <th>Total Vulns</th>
                    <th>Critical Vulns</th>
                    <th>CVEs</th>
                    <th>PURL</th>
                </tr>
        """
        
        for component in sorted(self.components, key=lambda x: x.get('vulnerability_count', 0), reverse=True):
            vuln_count = component.get('vulnerability_count', 0)
            critical_count = component.get('critical_vulnerabilities', 0)
            
            # Extract CVE information from detailed vulnerabilities if available
            cves = []
            component_name = component.get('name', '')
            component_version = component.get('version', '')
            
            for vuln in self.detailed_vulnerabilities:
                if (vuln.get('component', '') == component_name and 
                    vuln.get('version', '') == component_version):
                    cve_id = vuln.get('cve_id', '')
                    severity = vuln.get('severity', 'Unknown')
                    if cve_id and cve_id != 'N/A':
                        severity_class = severity.lower()
                        cves.append(f'<span class="{severity_class}">{cve_id}</span>')
            
            cves_html = '<br>'.join(cves[:5])  # Show max 5 CVEs
            if len(cves) > 5:
                cves_html += f'<br><small>... and {len(cves) - 5} more</small>'
            if not cves_html:
                cves_html = 'N/A'
            
            row_class = ""
            if critical_count > 0:
                row_class = 'class="critical"'
            elif vuln_count > 0:
                row_class = 'class="high"'
            
            html_content += f"""
                <tr {row_class}>
                    <td>{component.get('name', 'Unknown')}</td>
                    <td>{component.get('version', 'Unknown')}</td>
                    <td>{component.get('type', 'Unknown')}</td>
                    <td class="vuln-count">{vuln_count}</td>
                    <td class="vuln-count">{critical_count}</td>
                    <td><small>{cves_html}</small></td>
                    <td><small>{component.get('purl', 'N/A')}</small></td>
                </tr>
            """
        
        # Add detailed vulnerabilities section if available
        if self.detailed_vulnerabilities:
            html_content += """
            </table>
            
            <h2>🚨 Detailed Vulnerability Information</h2>
            <table>
                <tr>
                    <th>CVE ID</th>
                    <th>Component</th>
                    <th>Version</th>
                    <th>Severity</th>
                    <th>CVSS Score</th>
                    <th>Fixed Version</th>
                    <th>Description</th>
                </tr>
            """
            
            # Sort by severity and CVSS score
            severity_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1, 'Unknown': 0}
            sorted_vulns = sorted(
                self.detailed_vulnerabilities,
                key=lambda x: (severity_order.get(x.get('severity', 'Unknown'), 0), x.get('cvss_score', 0)),
                reverse=True
            )
            
            for vuln in sorted_vulns[:20]:  # Show max 20 detailed vulnerabilities
                severity = vuln.get('severity', 'Unknown')
                severity_class = severity.lower()
                description = vuln.get('description', 'No description available')
                # Truncate long descriptions
                if len(description) > 100:
                    description = description[:97] + '...'
                
                html_content += f"""
                    <tr class="{severity_class}">
                        <td><strong>{vuln.get('cve_id', 'N/A')}</strong></td>
                        <td>{vuln.get('component', 'Unknown')}</td>
                        <td>{vuln.get('version', 'Unknown')}</td>
                        <td class="{severity_class}"><strong>{severity}</strong></td>
                        <td class="vuln-count">{vuln.get('cvss_score', 0)}</td>
                        <td>{vuln.get('fixed_version', 'N/A')}</td>
                        <td><small>{description}</small></td>
                    </tr>
                """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML report exported to {filename}")
    
    def display_full_report(self, show_clean: bool = False, show_cves: bool = None, cve_limit: int = 10):
        """Display the complete formatted report."""
        self.print_header()
        self.print_summary()
        self.print_risk_assessment()
        self.print_components_table(show_clean=show_clean)
        self.print_top_vulnerable_components()
        self.print_component_types_breakdown()
        
        # Show detailed CVEs if explicitly requested or if detailed vulnerabilities are available
        if show_cves or (show_cves is None and self.detailed_vulnerabilities):
            self.print_detailed_vulnerabilities(limit=cve_limit)


def load_scan_results(filename: str) -> Dict[str, Any]:
    """Load scan results from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{filename}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading '{filename}': {e}")
        sys.exit(1)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Format and visualize security scan results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_results_formatter.py                    # Use default scan-results.json
  python scan_results_formatter.py -f results.json   # Use specific file
  python scan_results_formatter.py --clean           # Show clean components too
  python scan_results_formatter.py --csv             # Export to CSV
  python scan_results_formatter.py --html            # Export to HTML
  python scan_results_formatter.py --summary-only    # Show only summary
  python scan_results_formatter.py --show-cves       # Force show detailed CVE information
  python scan_results_formatter.py --cve-limit 20    # Show up to 20 detailed CVEs
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        default='scan-results.json',
        help='Path to scan results JSON file (default: scan-results.json)'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Show components with no vulnerabilities'
    )
    
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Show only summary information'
    )
    
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Export results to CSV format'
    )
    
    parser.add_argument(
        '--html',
        action='store_true',
        help='Export results to HTML format'
    )
    
    parser.add_argument(
        '--csv-filename',
        default='scan_results.csv',
        help='CSV output filename (default: scan_results.csv)'
    )
    
    parser.add_argument(
        '--html-filename',
        default='scan_results.html',
        help='HTML output filename (default: scan_results.html)'
    )
    
    parser.add_argument(
        '--show-cves',
        action='store_true',
        help='Show detailed CVE information (enabled by default if detailed_vulnerabilities are available)'
    )
    
    parser.add_argument(
        '--cve-limit',
        type=int,
        default=10,
        help='Maximum number of detailed CVEs to display (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Load scan results
    data = load_scan_results(args.file)
    formatter = ScanResultsFormatter(data)
    
    # Display report based on options
    if args.summary_only:
        formatter.print_header()
        formatter.print_summary()
        formatter.print_risk_assessment()
    else:
        formatter.display_full_report(
            show_clean=args.clean,
            show_cves=args.show_cves,
            cve_limit=args.cve_limit
        )
    
    # Export options
    if args.csv:
        formatter.export_csv(args.csv_filename)
    
    if args.html:
        formatter.export_html(args.html_filename)


if __name__ == '__main__':
    main()
