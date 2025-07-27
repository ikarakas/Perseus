# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Web dashboard for monitoring SBOM platform metrics
"""

from fastapi import FastAPI, Request
# from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import json
import os
from typing import Dict, Any
import markdown

from .metrics import MetricsCollector, AlertManager
from ..telemetry.storage import TelemetryStorage
from ..common.version import version_config

class MonitoringDashboard:
    """Web dashboard for platform monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector, telemetry_storage: TelemetryStorage = None):
        self.metrics_collector = metrics_collector
        self.alert_manager = AlertManager(metrics_collector)
        self.telemetry_storage = telemetry_storage
        # self.templates = Jinja2Templates(directory="templates")
    
    def setup_routes(self, app: FastAPI):
        """Setup dashboard routes"""
        
        @app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            metrics = self.metrics_collector.get_summary_dashboard()
            alerts = self.alert_manager.get_active_alerts()
            
            # Return enhanced HTML dashboard
            classification_color = version_config.get_classification_color()
            classification_display = version_config.should_display_classification()
            classification_level = version_config.get_classification_level()
            version_string = version_config.get_version_string()
            build_info = version_config.get_build_info()
            
            classification_banner = ''
            if classification_display:
                classification_banner = f'<!-- Classification Banner --><div class="classification-banner">{classification_level}</div>'
            
            # Build the HTML response with proper string interpolation
            html_response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SBOM Platform Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 0; 
                        padding: 20px; 
                        background: #f5f5f5;
                        background-image: url('/static/images/nato-awacs-real.jpg');
                        background-repeat: no-repeat;
                        background-position: center center;
                        background-attachment: fixed;
                        background-size: 900px 600px;
                        background-opacity: 0.08;
                    }}
                    .header {{ 
                        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                        color: white; 
                        padding: 20px; 
                        margin: -20px -20px 20px -20px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        position: relative;
                        overflow: hidden;
                    }}
                    .header::before {{
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background-image: url('/static/images/nato-awacs-real.jpg');
                        background-repeat: no-repeat;
                        background-position: right center;
                        background-size: 300px 200px;
                        opacity: 0.12;
                        z-index: 0;
                    }}
                    .header > * {{
                        position: relative;
                        z-index: 1;
                    }}
                    .classification-banner {{
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        background: {classification_color};
                        color: #000;
                        font-weight: bold;
                        text-align: center;
                        padding: 3px 0;
                        font-size: 12px;
                        z-index: 1001;
                        border-bottom: 1px solid #000;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    body {{
                        padding-top: 25px;
                    }}
                    .container {{ max-width: 1200px; margin: 0 auto; position: relative; z-index: 2; }}
                    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                    .card {{ 
                        background: rgba(255, 255, 255, 0.95); 
                        backdrop-filter: blur(5px);
                        padding: 20px; 
                        border-radius: 8px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        border: 1px solid rgba(255,255,255,0.2);
                    }}
                    .card h3 {{ margin-top: 0; color: #2c3e50; }}
                    .form-group {{ margin: 15px 0; }}
                    .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                    .form-group input, .form-group select {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
                    .btn {{ background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
                    .btn:hover {{ background: #2980b9; }}
                    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
                    .metric {{ text-align: center; }}
                    .metric-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
                    .metric-label {{ font-size: 14px; color: #7f8c8d; }}
                    .status-good {{ color: #27ae60; }}
                    .code {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; margin: 10px 0; }}
                    .results {{ margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; display: none; }}
                    .os-info {{ background: #e8f4fd; padding: 10px; border-radius: 4px; margin: 10px 0; border-left: 4px solid #3498db; }}
                    .component-breakdown {{ margin-left: 20px; }}
                </style>
            </head>
            <body>
                {classification_banner}
                
                <div class="header">
                    <div class="container">
                        <h1>🛡️ SBOM Platform Dashboard</h1>
                        <p>Bill of Materials Generation & Analysis</p>
                        <div style="font-size: 12px; opacity: 0.8; margin-top: 10px;">
                            BOM Generation - by I. KARAKAS | Version: {version_string}
                        </div>
                        <div style="font-size: 11px; opacity: 0.6; margin-top: 5px;">
                            Build: {build_info['timestamp'][:10]} | Environment: {build_info['environment']}
                        </div>
                        
                        <!-- Enhanced Portal Shortcut -->
                        <div style="margin-top: 15px;">
                            <a href="/dashboard/enhanced" 
                               style="display: inline-block; 
                                      background: linear-gradient(45deg, #4fd1c7, #3aa99f); 
                                      color: white; 
                                      padding: 12px 25px; 
                                      text-decoration: none; 
                                      border-radius: 25px; 
                                      font-weight: bold; 
                                      box-shadow: 0 4px 15px rgba(79, 209, 199, 0.3);
                                      transition: transform 0.2s, box-shadow 0.2s;"
                               onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(79, 209, 199, 0.4)'"
                               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(79, 209, 199, 0.3)'">
                                🚀 Enhanced Portal - Database Analytics
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="container">
                    <div class="grid">
                        <!-- Analysis Form -->
                        <div class="card">
                            <h3>📁 Submit Analysis</h3>
                            <p><strong>Note:</strong> Files must be copied to the <code>./data/</code> directory first.</p>
                            <div class="os-info" style="display: none;" id="osInfo">
                                <strong>🖥️ OS Analysis:</strong> Generates Bill of Materials for the local Linux system including kernel, modules, packages, libraries, and security features. Currently supports Debian, Ubuntu, RHEL, CentOS, Fedora, Arch, Alpine, and Gentoo distributions.
                            </div>
                            
                            <div class="form-group">
                                <label for="analysisType">Analysis Type:</label>
                                <select id="analysisType" onchange="toggleAnalysisOptions()">
                                    <option value="source">Source Code</option>
                                    <option value="binary">Binary Files</option>
                                    <option value="docker">Docker Image</option>
                                    <option value="os">Operating System</option>
                                </select>
                            </div>
                            
                            <div class="form-group" id="languageGroup">
                                <label for="language">Language:</label>
                                <select id="language">
                                    <option value="java">Java</option>
                                    <option value="c++">C++</option>
                                </select>
                            </div>
                            
                            <div class="form-group" id="importAnalysisGroup" style="display: block;">
                                <label>
                                    <input type="checkbox" id="analyzeImports" style="width: auto; margin-right: 10px;">
                                    Analyze import statements (Java only)
                                </label>
                                <small style="display: block; color: #7f8c8d; margin-top: 5px;">
                                    Detects libraries from import statements when build files are missing
                                </small>
                            </div>
                            
                            <div class="form-group" id="locationGroup">
                                <label for="location">File/Folder Path:</label>
                                <input type="text" id="location" placeholder="/app/data/my-project" value="/app/data/">
                            </div>
                            
                            <div class="form-group" id="dockerGroup" style="display: none;">
                                <label for="dockerImage">Docker Image:</label>
                                <input type="text" id="dockerImage" placeholder="ubuntu:latest or registry.example.com/myapp:v1.0">
                                <small style="display: block; color: #7f8c8d; margin-top: 5px;">
                                    Examples: nginx:latest, python:3.9-slim, ghcr.io/owner/image:tag
                                </small>
                            </div>
                            
                            <div class="form-group" id="osGroup" style="display: none;">
                                <label for="osTarget">Target System:</label>
                                <input type="text" id="osTarget" value="localhost" readonly>
                                <small style="display: block; color: #7f8c8d; margin-top: 5px;">
                                    Currently only supports local Linux system analysis
                                </small>
                            </div>
                            
                            <button class="btn" onclick="submitAnalysis()">🚀 Start Analysis</button>
                            
                            <div id="analysisResults" class="results"></div>
                        </div>
                        
                        <!-- SBOM Generation -->
                        <div class="card">
                            <h3>📋 Generate SBOM</h3>
                            <div class="form-group">
                                <label for="analysisIds">Analysis IDs (comma-separated):</label>
                                <input type="text" id="analysisIds" placeholder="analysis-id-1,analysis-id-2">
                            </div>
                            
                            <div class="form-group">
                                <label for="sbomFormat">SBOM Format:</label>
                                <select id="sbomFormat">
                                    <option value="spdx">SPDX 2.3</option>
                                    <option value="cyclonedx">CycloneDX 1.5</option>
                                    <option value="swid">SWID</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="includeVulnerabilities" checked style="width: auto; margin-right: 10px;">
                                    Include vulnerability data
                                </label>
                                <small style="display: block; color: #7f8c8d; margin-top: 5px;">
                                    Include security vulnerability information in the SBOM
                                </small>
                            </div>
                            
                            <button class="btn" onclick="generateSBOM()">📄 Generate SBOM</button>
                            
                            <div id="sbomResults" class="results"></div>
                        </div>
                    </div>
                    
                    <!-- Platform Metrics -->
                    <div class="card">
                        <h3>📊 Platform Metrics</h3>
                        <div class="metrics" id="metricsContainer">
                            <div class="metric">
                                <div class="metric-value status-good">●</div>
                                <div class="metric-label">Status: Healthy</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value" id="analysisCount">0</div>
                                <div class="metric-label">Total Analyses</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value" id="sbomCount">0</div>
                                <div class="metric-label">SBOMs Generated</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value" id="uptime">0h</div>
                                <div class="metric-label">Uptime</div>
                            </div>
                        </div>
                    </div>
                    
                    
                    <!-- All Analyses -->
                    <div class="card" style="margin-top: 20px;">
                        <h3>🔍 All Analyses</h3>
                        <div style="margin-bottom: 15px;">
                            <input type="text" id="analysisSearch" placeholder="Search by ID, type, or source..." 
                                   style="padding: 8px; border-radius: 4px; border: 1px solid #ddd; width: 300px; margin-right: 10px;">
                            <select id="analysisStatusFilter" style="padding: 8px; border-radius: 4px; border: 1px solid #ddd; margin-right: 10px;">
                                <option value="">All Statuses</option>
                                <option value="pending">Pending</option>
                                <option value="running">Running</option>
                                <option value="completed">Completed</option>
                                <option value="failed">Failed</option>
                            </select>
                            <select id="analysisTypeFilter" style="padding: 8px; border-radius: 4px; border: 1px solid #ddd; margin-right: 10px;">
                                <option value="">All Types</option>
                                <option value="syft">Syft</option>
                                <option value="manual">Manual</option>
                                <option value="api">API</option>
                                <option value="os">OS</option>
                            </select>
                            <button class="btn" onclick="searchAllAnalyses()" style="padding: 8px 16px;">🔍 Search</button>
                        </div>
                        <div style="margin-bottom: 10px; color: #7f8c8d;">
                            Total Analyses: <span id="totalAnalysisCount" style="font-weight: bold;">-</span> | 
                            Showing last 10 by default (use search to see all)
                        </div>
                        <div id="analysesList" style="max-height: 500px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 4px;">
                            <p>Loading analyses...</p>
                        </div>
                        <div id="analysisPagination" style="margin-top: 15px; text-align: center;">
                            <button class="btn" id="prevAnalysisBtn" onclick="loadPrevAnalysisPage()" style="padding: 6px 12px;">← Previous</button>
                            <span id="analysisPageInfo" style="margin: 0 15px;">Page 1</span>
                            <button class="btn" id="nextAnalysisBtn" onclick="loadNextAnalysisPage()" style="padding: 6px 12px;">Next →</button>
                        </div>
                    </div>
                    
                    <!-- API Reference -->
                    <div class="card">
                        <h3>🔗 Quick API Reference</h3>
                        <div class="code">
                            <strong>Copy files to data directory:</strong><br>
                            cp -r /path/to/project ./data/my-project
                        </div>
                        <div class="code">
                            <strong>Analyze source code via curl:</strong><br>
                            curl -X POST http://localhost:8000/analyze/source \\<br>
                            &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                            &nbsp;&nbsp;-d '{{"type":"source","language":"java","location":"/app/data/my-project"}}'
                        </div>
                        <div class="code">
                            <strong>Analyze Docker image via curl:</strong><br>
                            curl -X POST http://localhost:8000/analyze/docker \\<br>
                            &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                            &nbsp;&nbsp;-d '{{"type":"docker","location":"ubuntu:latest"}}'
                        </div>
                        <div class="code">
                            <strong>CI/CD Integration (register build):</strong><br>
                            curl -X POST http://localhost:8000/api/v1/cicd/builds \\<br>
                            &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                            &nbsp;&nbsp;-d '{{"build_id":"build-123","project":{{"name":"my-project","path":"./data/my-project"}},"ci_context":{{"platform":"jenkins"}}}}'
                        </div>
                        <div class="code">
                            <strong>Analyze OS (Linux only) via curl:</strong><br>
                            curl -X POST http://localhost:8000/analyze/os \\<br>
                            &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                            &nbsp;&nbsp;-d '{{"type":"os","location":"localhost"}}'
                        </div>
                        <p><strong>Useful Links:</strong></p>
                        <ul>
                            <li><a href="/dashboard/enhanced" target="_blank" style="color: #4fd1c7; font-weight: bold;">🚀 Enhanced Portal - Database Analytics</a></li>
                            <li><a href="/components/search" target="_blank">🔍 Component Search</a></li>
                            <li><a href="/api/metrics" target="_blank">📈 Platform Metrics</a></li>
                            <li><a href="/health" target="_blank">❤️ Health Check</a></li>
                            <li><a href="/docs" target="_blank">📖 API Documentation</a></li>
                            <li><a href="/api/v1/cicd/builds" target="_blank">🚀 CI/CD API</a></li>
                        </ul>
                    </div>
                    
                    <!-- Telemetry Agents -->
                    <div class="card">
                        <h3>🖥️ Remote Agents</h3>
                        <div id="telemetrySection">
                            <div class="metrics" id="agentMetrics">
                                <div class="metric">
                                    <div class="metric-value" id="agentCount">0</div>
                                    <div class="metric-label">Connected Agents</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value" id="totalAgents">0</div>
                                    <div class="metric-label">Total Registered</div>
                                </div>
                            </div>
                            <div style="margin-top: 15px; margin-bottom: 15px;">
                                <button class="btn" onclick="purgeAgents()" style="background-color: #e74c3c; color: white;">
                                    🗑️ Purge All Agents
                                </button>
                            </div>
                            <div id="agentList" style="margin-top: 15px;">
                                <div style="color: #7f8c8d; font-style: italic;">Loading agent data...</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <script>
                    function toggleAnalysisOptions() {{
                        const type = document.getElementById('analysisType').value;
                        const languageGroup = document.getElementById('languageGroup');
                        const locationGroup = document.getElementById('locationGroup');
                        const dockerGroup = document.getElementById('dockerGroup');
                        const osGroup = document.getElementById('osGroup');
                        const osInfo = document.getElementById('osInfo');
                        const importAnalysisGroup = document.getElementById('importAnalysisGroup');
                        
                        if (type === 'source') {{
                            languageGroup.style.display = 'block';
                            importAnalysisGroup.style.display = 'block';
                            locationGroup.style.display = 'block';
                            dockerGroup.style.display = 'none';
                            osGroup.style.display = 'none';
                            osInfo.style.display = 'none';
                        }} else if (type === 'binary') {{
                            languageGroup.style.display = 'none';
                            importAnalysisGroup.style.display = 'none';
                            locationGroup.style.display = 'block';
                            dockerGroup.style.display = 'none';
                            osGroup.style.display = 'none';
                            osInfo.style.display = 'none';
                        }} else if (type === 'docker') {{
                            languageGroup.style.display = 'none';
                            importAnalysisGroup.style.display = 'none';
                            locationGroup.style.display = 'none';
                            dockerGroup.style.display = 'block';
                            osGroup.style.display = 'none';
                            osInfo.style.display = 'none';
                        }} else if (type === 'os') {{
                            languageGroup.style.display = 'none';
                            importAnalysisGroup.style.display = 'none';
                            locationGroup.style.display = 'none';
                            dockerGroup.style.display = 'none';
                            osGroup.style.display = 'block';
                            osInfo.style.display = 'block';
                        }}
                    }}
                    
                    async function submitAnalysis() {{
                        const type = document.getElementById('analysisType').value;
                        const language = document.getElementById('language').value;
                        const location = document.getElementById('location').value;
                        const dockerImage = document.getElementById('dockerImage').value;
                        const analyzeImports = document.getElementById('analyzeImports').checked;
                        
                        const payload = {{
                            type: type
                        }};
                        
                        if (type === 'source') {{
                            payload.language = language;
                            payload.location = location;
                            // Always include options with vulnerability scanning enabled
                            payload.options = {{
                                deep_scan: true,
                                analyze_imports: analyzeImports,
                                include_vulnerabilities: true
                            }};
                        }} else if (type === 'binary') {{
                            payload.location = location;
                            // Include vulnerability scanning for binary analysis
                            payload.options = {{
                                include_vulnerabilities: true
                            }};
                        }} else if (type === 'docker') {{
                            payload.location = dockerImage;
                            // Include vulnerability scanning for docker analysis
                            payload.options = {{
                                include_vulnerabilities: true
                            }};
                        }} else if (type === 'os') {{
                            payload.location = 'localhost';
                            // Include vulnerability scanning for OS analysis
                            payload.options = {{
                                include_vulnerabilities: true
                            }};
                        }}
                        
                        try {{
                            const response = await fetch(`/analyze/${{type}}`, {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify(payload)
                            }});
                            
                            const result = await response.json();
                            const resultsDiv = document.getElementById('analysisResults');
                            
                            if (response.ok) {{
                                resultsDiv.innerHTML = `
                                    <h4>✅ Analysis Started</h4>
                                    <p><strong>Analysis ID:</strong> ${{result.analysis_id}}</p>
                                    <p><strong>Status:</strong> ${{result.status}}</p>
                                    <p><em>🔒 Vulnerability scanning enabled by default</em></p>
                                    <button class="btn" onclick="checkStatus('${{result.analysis_id}}')">Check Status</button>
                                `;
                                resultsDiv.style.display = 'block';
                            }} else {{
                                resultsDiv.innerHTML = `<h4>❌ Error</h4><p>${{result.detail || 'Analysis failed'}}</p>`;
                                resultsDiv.style.display = 'block';
                            }}
                        }} catch (error) {{
                            document.getElementById('analysisResults').innerHTML = `<h4>❌ Network Error</h4><p>${{error.message}}</p>`;
                            document.getElementById('analysisResults').style.display = 'block';
                        }}
                    }}
                    
                    async function checkStatus(analysisId) {{
                        try {{
                            const response = await fetch(`/analyze/${{analysisId}}/status`);
                            const status = await response.json();
                            
                            const resultsResponse = await fetch(`/analyze/${{analysisId}}/results`);
                            const results = await resultsResponse.json();
                            
                            const resultsDiv = document.getElementById('analysisResults');
                            let resultsHtml = `
                                <h4>📊 Analysis Results</h4>
                                <p><strong>Status:</strong> ${{status.status}}</p>
                                <p><strong>Components Found:</strong> ${{results.components ? results.components.length : 0}}</p>
                                <p><strong>Analysis ID:</strong> ${{analysisId}}</p>
                            `;
                            
                            // Add vulnerability information if available
                            if (results.metadata && results.metadata.vulnerability_scan_performed) {{
                                const totalVulns = results.metadata.total_vulnerabilities || 0;
                                const vulnComponents = results.metadata.vulnerable_components || 0;
                                const scanDate = results.metadata.vulnerability_scan_date;
                                
                                resultsHtml += `
                                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; border-left: 4px solid #3498db;">
                                        <h5>🔒 Vulnerability Scan Results</h5>
                                        <p><strong>Total Vulnerabilities:</strong> ${{totalVulns}}</p>
                                        <p><strong>Vulnerable Components:</strong> ${{vulnComponents}}</p>
                                        <p><strong>Scan Date:</strong> ${{scanDate ? new Date(scanDate).toLocaleString(undefined, {{timeZoneName: 'short'}}) : 'Unknown'}}</p>
                                    </div>
                                `;
                            }} else if (results.metadata && results.metadata.vulnerability_scan_performed === false) {{
                                resultsHtml += `
                                    <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; border-left: 4px solid #ffc107;">
                                        <h5>⚠️ Vulnerability Scan</h5>
                                        <p>Vulnerability scan failed or was disabled for this analysis.</p>
                                    </div>
                                `;
                            }}
                            
                            
                            // Add OS-specific information if available
                            if (results.metadata && results.metadata.distribution) {{
                                resultsHtml += `
                                    <p><strong>Distribution:</strong> ${{results.metadata.distribution.NAME || 'Unknown'}} ${{results.metadata.distribution.VERSION || ''}}</p>
                                    <p><strong>Package Manager:</strong> ${{results.metadata.package_manager || 'None detected'}}</p>
                                `;
                                
                                // Show component breakdown
                                const componentTypes = {{}};
                                if (results.components) {{
                                    results.components.forEach(comp => {{
                                        const type = comp.type || 'unknown';
                                        componentTypes[type] = (componentTypes[type] || 0) + 1;
                                    }});
                                    
                                    resultsHtml += '<p><strong>Component Breakdown:</strong></p><ul>';
                                    Object.entries(componentTypes).forEach(([type, count]) => {{
                                        resultsHtml += `<li>${{type}}: ${{count}}</li>`;
                                    }});
                                    resultsHtml += '</ul>';
                                }}
                            }}
                            
                            resultsHtml += '<p><em>Use this Analysis ID to generate an SBOM below.</em></p>';
                            resultsDiv.innerHTML = resultsHtml;
                        }} catch (error) {{
                            console.error('Error checking status:', error);
                        }}
                    }}
                    
                    async function generateSBOM() {{
                        const analysisIds = document.getElementById('analysisIds').value.split(',').map(s => s.trim());
                        const format = document.getElementById('sbomFormat').value;
                        const includeVulnerabilities = document.getElementById('includeVulnerabilities').checked;
                        
                        try {{
                            const response = await fetch('/sbom/generate', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{
                                    analysis_ids: analysisIds,
                                    format: format,
                                    include_licenses: true,
                                    include_vulnerabilities: includeVulnerabilities
                                }})
                            }});
                            
                            const result = await response.json();
                            const resultsDiv = document.getElementById('sbomResults');
                            
                            if (response.ok) {{
                                resultsDiv.innerHTML = `
                                    <h4>✅ SBOM Generation Started</h4>
                                    <p><strong>SBOM ID:</strong> ${{result.sbom_id}}</p>
                                    <p><strong>Format:</strong> ${{format.toUpperCase()}}</p>
                                    <button class="btn" onclick="downloadSBOM('${{result.sbom_id}}')">Download SBOM</button>
                                `;
                                resultsDiv.style.display = 'block';
                            }} else {{
                                resultsDiv.innerHTML = `<h4>❌ Error</h4><p>${{result.detail || 'SBOM generation failed'}}</p>`;
                                resultsDiv.style.display = 'block';
                            }}
                        }} catch (error) {{
                            document.getElementById('sbomResults').innerHTML = `<h4>❌ Network Error</h4><p>${{error.message}}</p>`;
                            document.getElementById('sbomResults').style.display = 'block';
                        }}
                    }}
                    
                    async function downloadSBOM(sbomId) {{
                        try {{
                            const response = await fetch(`/sbom/${{sbomId}}`);
                            const sbom = await response.json();
                            
                            // Create download link
                            const blob = new Blob([JSON.stringify(sbom, null, 2)], {{ type: 'application/json' }});
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `sbom-${{sbomId}}.json`;
                            a.click();
                            URL.revokeObjectURL(url);
                            
                            // Show success message
                            document.getElementById('sbomResults').innerHTML += `
                                <p>✅ <strong>SBOM Downloaded!</strong> Components: ${{sbom.packages ? sbom.packages.length : sbom.components ? sbom.components.length : 'N/A'}}</p>
                            `;
                        }} catch (error) {{
                            console.error('Error downloading SBOM:', error);
                        }}
                    }}
                    
                    // Analysis pagination variables
                    let currentAnalysisPage = 0;
                    let analysisPageSize = 10;
                    let totalAnalyses = 0;
                    let currentAnalysisSearch = '';
                    let currentAnalysisStatus = '';
                    let currentAnalysisType = '';
                    
                    
                    // Load all analyses with pagination
                    async function loadAllAnalyses(page = 0, limit = 10) {{
                        try {{
                            const offset = page * limit;
                            let url = `/api/v1/dashboard/analyses/all?offset=${{offset}}&limit=${{limit}}`;
                            
                            if (currentAnalysisSearch) {{
                                url += `&search=${{encodeURIComponent(currentAnalysisSearch)}}`;
                            }}
                            if (currentAnalysisStatus) {{
                                url += `&status=${{currentAnalysisStatus}}`;
                            }}
                            if (currentAnalysisType) {{
                                url += `&analysis_type=${{currentAnalysisType}}`;
                            }}
                            
                            const response = await fetch(url);
                            const data = await response.json();
                            
                            totalAnalyses = data.total || 0;
                            document.getElementById('totalAnalysisCount').textContent = totalAnalyses;
                            
                            // Update pagination
                            const totalPages = Math.ceil(totalAnalyses / limit);
                            document.getElementById('analysisPageInfo').textContent = `Page ${{page + 1}} of ${{totalPages || 1}}`;
                            document.getElementById('prevAnalysisBtn').disabled = page === 0;
                            document.getElementById('nextAnalysisBtn').disabled = page >= totalPages - 1;
                            
                            // Display analyses
                            const analysesList = document.getElementById('analysesList');
                            if (data.analyses && data.analyses.length > 0) {{
                                analysesList.innerHTML = data.analyses.map(analysis => {{
                                    const statusColor = {{
                                        'completed': '#27ae60',
                                        'failed': '#e74c3c',
                                        'running': '#f39c12',
                                        'pending': '#95a5a6'
                                    }}[analysis.status] || '#95a5a6';
                                    
                                    const duration = analysis.duration_seconds ? 
                                        `${{analysis.duration_seconds.toFixed(1)}}s` : 
                                        'In progress';
                                    
                                    return `
                                        <div style="background: white; padding: 15px; margin: 8px 0; border-radius: 4px; border-left: 4px solid ${{statusColor}};">
                                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                                <div style="flex: 1;">
                                                    <strong style="font-size: 16px;">
                                                        ${{analysis.analysis_type.toUpperCase()}} Analysis
                                                    </strong>
                                                    <span style="background: ${{statusColor}}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px;">
                                                        ${{analysis.status}}
                                                    </span>
                                                </div>
                                                <button class="btn" onclick="viewAnalysisDetails('${{analysis.analysis_id}}')" 
                                                        style="padding: 6px 12px; font-size: 12px;">
                                                    📊 View Details
                                                </button>
                                            </div>
                                            <div style="font-size: 13px; color: #7f8c8d; margin-top: 8px;">
                                                <div>🆔 <strong>ID:</strong> ${{analysis.analysis_id}}</div>
                                                <div style="margin-top: 4px;">
                                                    📦 <strong>Components:</strong> ${{analysis.component_count || 0}} | 
                                                    🚨 <strong>Vulnerabilities:</strong> ${{analysis.vulnerability_count || 0}} 
                                                    (${{analysis.critical_vulnerability_count || 0}} critical, ${{analysis.high_vulnerability_count || 0}} high)
                                                </div>
                                                ${{analysis.source_info ? `<div style="margin-top: 4px;">📁 <strong>Source:</strong> ${{analysis.source_info.target_location}} (${{analysis.source_info.analysis_type}})</div>` : ''}}
                                                <div style="margin-top: 4px;">
                                                    ⏰ <strong>Started:</strong> ${{new Date(analysis.created_at).toLocaleString(undefined, {{timeZoneName: 'short'}})}} | 
                                                    ⏱️ <strong>Duration:</strong> ${{duration}}
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }}).join('');
                            }} else {{
                                analysesList.innerHTML = '<p>No analyses found</p>';
                            }}
                            
                            currentAnalysisPage = page;
                            analysisPageSize = limit;
                        }} catch (error) {{
                            console.error('Error loading analyses:', error);
                            document.getElementById('analysesList').innerHTML = '<p style="color: red;">Error loading analyses</p>';
                        }}
                    }}
                    
                    function searchAllAnalyses() {{
                        currentAnalysisSearch = document.getElementById('analysisSearch').value;
                        currentAnalysisStatus = document.getElementById('analysisStatusFilter').value;
                        currentAnalysisType = document.getElementById('analysisTypeFilter').value;
                        currentAnalysisPage = 0;
                        // When searching, show more results
                        loadAllAnalyses(0, currentAnalysisSearch || currentAnalysisStatus || currentAnalysisType ? 50 : 10);
                    }}
                    
                    function loadPrevAnalysisPage() {{
                        if (currentAnalysisPage > 0) {{
                            loadAllAnalyses(currentAnalysisPage - 1, analysisPageSize);
                        }}
                    }}
                    
                    function loadNextAnalysisPage() {{
                        const totalPages = Math.ceil(totalAnalyses / analysisPageSize);
                        if (currentAnalysisPage < totalPages - 1) {{
                            loadAllAnalyses(currentAnalysisPage + 1, analysisPageSize);
                        }}
                    }}
                    
                    async function viewAnalysisDetails(analysisId) {{
                        // Open enhanced dashboard with this analysis highlighted
                        window.open(`/dashboard/enhanced#analysis-${{analysisId}}`, '_blank');
                    }}
                    
                    // Load metrics on page load
                    async function loadMetrics() {{
                        try {{
                            const response = await fetch('/api/v1/dashboard/metrics');
                            const metrics = await response.json();
                            
                            document.getElementById('analysisCount').textContent = metrics.analysis_statistics.total_analyses || 0;
                            document.getElementById('sbomCount').textContent = metrics.sbom_statistics.total_sboms || 0;
                            document.getElementById('uptime').textContent = 'N/A';
                        }} catch (error) {{
                            console.error('Error loading metrics:', error);
                        }}
                    }}
                    
                    // Load telemetry data
                    async function loadTelemetryData() {{
                        try {{
                            const response = await fetch('/telemetry/agents');
                            const data = await response.json();
                            
                            // Update metrics
                            const connected = Object.values(data.agents).filter(agent => agent.connected).length;
                            document.getElementById('agentCount').textContent = connected;
                            document.getElementById('totalAgents').textContent = data.total || 0;
                            
                            // Update agent list
                            const agentList = document.getElementById('agentList');
                            if (data.total === 0) {{
                                agentList.innerHTML = '<div style="color: #7f8c8d; font-style: italic;">No agents registered</div>';
                            }} else {{
                                let html = '';
                                Object.entries(data.agents).forEach(([agentId, agent]) => {{
                                    const status = agent.connected ? '🟢' : '🔴';
                                    const lastSeen = new Date(agent.last_seen).toLocaleString(undefined, {{timeZoneName: 'short'}});
                                    const hostname = agent.metadata?.hostname || agentId;
                                    html += `
                                        <div style="padding: 8px; margin: 4px 0; background: #f8f9fa; border-radius: 4px; border-left: 3px solid ${{agent.connected ? '#27ae60' : '#e74c3c'}};">
                                            <strong>${{status}} ${{hostname}}</strong><br>
                                            <small>Last seen: ${{lastSeen}}</small>
                                            ${{agent.last_scan ? `<br><small>Last scan: ${{agent.last_scan.component_count}} components</small>` : ''}}
                                            <br><button class="btn" style="margin-top: 5px; padding: 4px 8px; font-size: 12px;" onclick="viewAgentBOM('${{agentId}}')">View BOM</button>
                                        </div>
                                    `;
                                }});
                                agentList.innerHTML = html;
                            }}
                        }} catch (error) {{
                            console.error('Error loading telemetry data:', error);
                            document.getElementById('agentList').innerHTML = '<div style="color: #e74c3c;">Error loading agent data</div>';
                        }}
                    }}
                    
                    // Purge all agents
                    async function purgeAgents() {{
                        if (!confirm('⚠️ Are you sure you want to purge all agent data?\\n\\nThis will:\\n- Disconnect all connected agents\\n- Delete all agent registration data\\n- Remove all BOM data\\n- Clear all error logs\\n\\nThis action cannot be undone.')) {{
                            return;
                        }}
                        
                        try {{
                            const response = await fetch('/telemetry/purge', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }}
                            }});
                            
                            const result = await response.json();
                            
                            if (response.ok) {{
                                alert(`✅ Purge completed successfully!\\n\\nPurged:\\n- ${{result.purged.total_agents}} registered agents\\n- ${{result.purged.connected_agents}} connected agents\\n\\nAll agent data has been cleared.`);
                                
                                // Immediately refresh the display
                                loadTelemetryData();
                                loadMetrics();
                            }} else {{
                                alert(`❌ Purge failed: ${{result.detail || 'Unknown error'}}`);
                            }}
                        }} catch (error) {{
                            alert(`❌ Error during purge: ${{error.message}}`);
                        }}
                    }}
                    
                    // Load metrics on page load and refresh every 30 seconds
                    loadMetrics();
                    loadTelemetryData();
                    loadAllAnalyses(0, 10);  // Load last 10 analyses by default
                    setInterval(loadMetrics, 30000);
                    setInterval(loadTelemetryData, 15000);
                    
                    // View Agent BOM Data
                    async function viewAgentBOM(agentId) {{
                        try {{
                            // Create modal container
                            const modal = document.createElement('div');
                            modal.style.cssText = `
                                position: fixed;
                                top: 0;
                                left: 0;
                                width: 100%;
                                height: 100%;
                                background: rgba(0,0,0,0.8);
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                z-index: 1000;
                            `;
                            
                            const modalContent = document.createElement('div');
                            modalContent.style.cssText = `
                                background: white;
                                padding: 20px;
                                border-radius: 8px;
                                max-width: 90%;
                                max-height: 90%;
                                overflow: auto;
                                position: relative;
                            `;
                            
                            modalContent.innerHTML = '<h3>Loading BOM data...</h3>';
                            modal.appendChild(modalContent);
                            document.body.appendChild(modal);
                            
                            // Close on background click
                            modal.onclick = (e) => {{
                                if (e.target === modal) {{
                                    document.body.removeChild(modal);
                                }}
                            }};
                            
                            // Fetch BOM data
                            const response = await fetch(`/telemetry/agents/${{agentId}}/bom/latest`);
                            const bomData = await response.json();
                            
                            if (response.ok) {{
                                let html = `
                                    <button style="position: absolute; top: 10px; right: 10px; padding: 5px 10px;" onclick="this.parentElement.parentElement.remove()">✕</button>
                                    <h3>📋 BOM Data for ${{agentId}}</h3>
                                    <p><strong>Scan ID:</strong> ${{bomData.scan_id}}</p>
                                    <p><strong>Timestamp:</strong> ${{new Date(bomData.timestamp).toLocaleString(undefined, {{timeZoneName: 'short'}})}}</p>
                                    <p><strong>Total Components:</strong> ${{bomData.components ? bomData.components.length : 0}}</p>
                                    
                                    <h4>System Information</h4>
                                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0;">
                                        <strong>OS:</strong> ${{bomData.metadata.os_type}}<br>
                                        <strong>Hostname:</strong> ${{bomData.metadata.hostname}}<br>
                                        <strong>Architecture:</strong> ${{bomData.metadata.architecture}}<br>
                                        <strong>Distribution:</strong> ${{bomData.metadata.distribution?.NAME || 'Unknown'}} ${{bomData.metadata.distribution?.VERSION || ''}}<br>
                                        <strong>Package Manager:</strong> ${{bomData.metadata.package_manager || 'Unknown'}}
                                    </div>
                                    
                                    <h4>Components by Type</h4>
                                `;
                                
                                // Group components by type
                                const componentsByType = {{}};
                                if (bomData.components) {{
                                    bomData.components.forEach(comp => {{
                                        const type = comp.type || 'unknown';
                                        if (!componentsByType[type]) componentsByType[type] = [];
                                        componentsByType[type].push(comp);
                                    }});
                                }}
                                
                                // Display components grouped by type
                                Object.entries(componentsByType).forEach(([type, components]) => {{
                                    html += `
                                        <details style="margin: 10px 0;">
                                            <summary style="cursor: pointer; font-weight: bold;">
                                                ${{type}} (${{components.length}} items)
                                            </summary>
                                            <div style="margin-left: 20px; margin-top: 10px;">
                                    `;
                                    
                                    components.slice(0, 20).forEach(comp => {{
                                        html += `
                                            <div style="padding: 5px; margin: 2px 0; background: #f8f9fa; border-radius: 2px;">
                                                <strong>${{comp.name}}</strong> ${{comp.version ? `v${{comp.version}}` : ''}}
                                                ${{comp.purl ? `<br><small style="color: #666;">purl: ${{comp.purl}}</small>` : ''}}
                                            </div>
                                        `;
                                    }});
                                    
                                    if (components.length > 20) {{
                                        html += `<p style="color: #666; font-style: italic;">... and ${{components.length - 20}} more</p>`;
                                    }}
                                    
                                    html += `
                                            </div>
                                        </details>
                                    `;
                                }});
                                
                                html += `
                                    <div style="margin-top: 20px;">
                                        <button class="btn" onclick="downloadAgentBOM('${{agentId}}')">Download Full BOM</button>
                                    </div>
                                `;
                                
                                modalContent.innerHTML = html;
                            }} else {{
                                modalContent.innerHTML = `
                                    <button style="position: absolute; top: 10px; right: 10px;" onclick="this.parentElement.parentElement.remove()">✕</button>
                                    <h3>❌ Error</h3>
                                    <p>${{bomData.detail || 'Failed to load BOM data'}}</p>
                                `;
                            }}
                            
                        }} catch (error) {{
                            console.error('Error viewing BOM:', error);
                            alert('Failed to load BOM data');
                        }}
                    }}
                    
                    // Download Agent BOM
                    async function downloadAgentBOM(agentId) {{
                        try {{
                            const response = await fetch(`/telemetry/agents/${{agentId}}/bom/latest`);
                            const bomData = await response.json();
                            
                            const blob = new Blob([JSON.stringify(bomData, null, 2)], {{ type: 'application/json' }});
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `bom-${{agentId}}-${{new Date().toISOString().split('T')[0]}}.json`;
                            a.click();
                            URL.revokeObjectURL(url);
                        }} catch (error) {{
                            console.error('Error downloading BOM:', error);
                            alert('Failed to download BOM data');
                        }}
                    }}
                </script>
            </body>
            </html>
            """
            
            return HTMLResponse(html_response)
        
        @app.get("/api/metrics")
        async def get_metrics():
            """API endpoint for metrics data"""
            return JSONResponse(self.metrics_collector.get_summary_dashboard())
        
        @app.get("/api/metrics/analysis")
        async def get_analysis_metrics():
            """API endpoint for analysis metrics"""
            return JSONResponse(self.metrics_collector.get_analysis_metrics())
        
        @app.get("/api/metrics/sbom")
        async def get_sbom_metrics():
            """API endpoint for SBOM metrics"""
            return JSONResponse(self.metrics_collector.get_sbom_metrics())
        
        @app.get("/api/metrics/system")
        async def get_system_metrics():
            """API endpoint for system metrics"""
            return JSONResponse(self.metrics_collector.get_system_metrics())
        
        @app.get("/api/alerts")
        async def get_alerts():
            """API endpoint for active alerts"""
            alerts = self.alert_manager.check_alerts()
            return JSONResponse({
                "active_alerts": self.alert_manager.get_active_alerts(),
                "new_alerts": alerts
            })
        
        @app.post("/api/alerts/{alert_id}/clear")
        async def clear_alert(alert_id: str):
            """Clear an active alert"""
            self.alert_manager.clear_alert(alert_id)
            return JSONResponse({"status": "cleared"})
        
        @app.get("/api/version")
        async def get_version():
            """Get version information"""
            return JSONResponse({
                "version": version_config.get_version_string(),
                "version_parts": version_config.get_version_parts(),
                "classification": {
                    "level": version_config.get_classification_level(),
                    "display": version_config.should_display_classification(),
                    "color": version_config.get_classification_color()
                },
                "build": version_config.get_build_info()
            })
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            system_metrics = self.metrics_collector.get_system_metrics()
            
            # Determine health status
            health_status = "healthy"
            if system_metrics["current"]:
                current = system_metrics["current"]
                if (current["cpu_percent"] > 90 or 
                    current["memory_percent"] > 95 or 
                    current["disk_percent"] > 95):
                    health_status = "degraded"
            
            return JSONResponse({
                "status": health_status,
                "timestamp": system_metrics["current"]["timestamp"] if system_metrics["current"] else None,
                "uptime_hours": system_metrics["uptime_hours"]
            })
        
        @app.get("/docs/readme", response_class=HTMLResponse)
        async def serve_readme():
            """Serve README.md as HTML"""
            readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "README.md")
            
            if not os.path.exists(readme_path):
                return HTMLResponse("<h1>User Manual Not Found</h1><p>Could not find README.md file.</p>", status_code=404)
            
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                # Convert markdown to HTML
                html_content = markdown.markdown(readme_content, extensions=['extra', 'tables', 'toc'])
                
                # Wrap in HTML template with styling
                full_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>SBOM Platform User Manual</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 900px;
                            margin: 0 auto;
                            padding: 20px;
                            background: #f5f5f5;
                        }}
                        h1, h2, h3, h4 {{
                            color: #2c3e50;
                            margin-top: 1.5em;
                        }}
                        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 0.3em; }}
                        h2 {{ border-bottom: 1px solid #ecf0f1; padding-bottom: 0.2em; }}
                        code {{
                            background: #f8f9fa;
                            padding: 2px 4px;
                            border-radius: 3px;
                            font-family: 'Consolas', 'Monaco', monospace;
                        }}
                        pre {{
                            background: #2c3e50;
                            color: #ecf0f1;
                            padding: 15px;
                            border-radius: 5px;
                            overflow-x: auto;
                        }}
                        pre code {{
                            background: none;
                            color: inherit;
                            padding: 0;
                        }}
                        table {{
                            border-collapse: collapse;
                            width: 100%;
                            margin: 1em 0;
                        }}
                        th, td {{
                            border: 1px solid #ddd;
                            padding: 8px;
                            text-align: left;
                        }}
                        th {{
                            background: #34495e;
                            color: white;
                        }}
                        tr:nth-child(even) {{
                            background: #f8f9fa;
                        }}
                        a {{
                            color: #3498db;
                            text-decoration: none;
                        }}
                        a:hover {{
                            text-decoration: underline;
                        }}
                        .back-link {{
                            display: inline-block;
                            margin-bottom: 20px;
                            padding: 10px 20px;
                            background: #3498db;
                            color: white;
                            border-radius: 4px;
                            text-decoration: none;
                        }}
                        .back-link:hover {{
                            background: #2980b9;
                            text-decoration: none;
                        }}
                    </style>
                </head>
                <body>
                    <a href="/dashboard" class="back-link">← Back to Dashboard</a>
                    {html_content}
                </body>
                </html>
                """
                
                return HTMLResponse(full_html)
                
            except Exception as e:
                return HTMLResponse(f"<h1>Error</h1><p>Could not load user manual: {str(e)}</p>", status_code=500)


# HTML template for dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SBOM Platform Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #2c3e50; }
        .metric-value { font-size: 24px; font-weight: bold; color: #3498db; }
        .metric-label { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
        .alerts { background: #e74c3c; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .alert-item { margin: 5px 0; padding: 5px; background: rgba(0,0,0,0.1); border-radius: 4px; }
        .status-good { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-critical { color: #e74c3c; }
        .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .timestamp { font-size: 12px; color: #7f8c8d; text-align: right; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>SBOM Platform Dashboard</h1>
        <button class="refresh-btn" onclick="refreshData()">Refresh</button>
    </div>
    
    <div id="alerts-container"></div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-title">Analysis Performance</div>
            <div class="metric-value" id="total-analyses">0</div>
            <div class="metric-label">Total Analyses</div>
            <div style="margin-top: 10px;">
                <div>Success Rate: <span id="success-rate" class="status-good">0%</span></div>
                <div>Avg Duration: <span id="avg-duration">0s</span></div>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">SBOM Generation</div>
            <div class="metric-value" id="total-sboms">0</div>
            <div class="metric-label">Total SBOMs Generated</div>
            <div style="margin-top: 10px;">
                <div>SPDX: <span id="spdx-count">0</span></div>
                <div>CycloneDX: <span id="cyclonedx-count">0</span></div>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">API Performance</div>
            <div class="metric-value" id="total-requests">0</div>
            <div class="metric-label">Total API Requests</div>
            <div style="margin-top: 10px;">
                <div>Avg Response: <span id="avg-response">0ms</span></div>
                <div>Error Rate: <span id="error-rate" class="status-good">0%</span></div>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">System Resources</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; text-align: center;">
                <div>
                    <div class="metric-value" id="cpu-usage">0%</div>
                    <div class="metric-label">CPU</div>
                </div>
                <div>
                    <div class="metric-value" id="memory-usage">0%</div>
                    <div class="metric-label">Memory</div>
                </div>
                <div>
                    <div class="metric-value" id="disk-usage">0%</div>
                    <div class="metric-label">Disk</div>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <div>Uptime: <span id="uptime">0h</span></div>
            </div>
        </div>
    </div>
    
    <div class="timestamp" id="last-updated"></div>
    
    <script>
        function refreshData() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error fetching metrics:', error));
            
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => updateAlerts(data.active_alerts))
                .catch(error => console.error('Error fetching alerts:', error));
        }
        
        function updateDashboard(metrics) {
            // Analysis metrics
            document.getElementById('total-analyses').textContent = metrics.analysis.total_analyses || 0;
            
            // Calculate overall success rate
            let totalSuccess = 0, totalAttempts = 0;
            for (const [key, stats] of Object.entries(metrics.analysis.success_rates)) {
                totalSuccess += stats.total_attempts * (stats.success_rate / 100);
                totalAttempts += stats.total_attempts;
            }
            const overallSuccessRate = totalAttempts > 0 ? (totalSuccess / totalAttempts * 100).toFixed(1) : 0;
            document.getElementById('success-rate').textContent = overallSuccessRate + '%';
            
            // Average duration
            const durations = Object.values(metrics.analysis.average_durations);
            const avgDuration = durations.length > 0 ? (durations.reduce((a, b) => a + b, 0) / durations.length).toFixed(1) : 0;
            document.getElementById('avg-duration').textContent = avgDuration + 's';
            
            // SBOM metrics
            document.getElementById('total-sboms').textContent = metrics.sbom.total_sboms_generated || 0;
            document.getElementById('spdx-count').textContent = metrics.sbom.sboms_by_format.spdx || 0;
            document.getElementById('cyclonedx-count').textContent = metrics.sbom.sboms_by_format.cyclonedx || 0;
            
            // API metrics
            document.getElementById('total-requests').textContent = metrics.api.total_requests || 0;
            
            const responseTimes = Object.values(metrics.api.average_response_times);
            const avgResponse = responseTimes.length > 0 ? (responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length * 1000).toFixed(0) : 0;
            document.getElementById('avg-response').textContent = avgResponse + 'ms';
            
            // Calculate overall error rate
            let totalErrors = 0, totalApiRequests = 0;
            for (const [key, stats] of Object.entries(metrics.api.error_rates)) {
                totalErrors += stats.total_requests * (stats.error_rate / 100);
                totalApiRequests += stats.total_requests;
            }
            const overallErrorRate = totalApiRequests > 0 ? (totalErrors / totalApiRequests * 100).toFixed(1) : 0;
            document.getElementById('error-rate').textContent = overallErrorRate + '%';
            
            // System metrics
            if (metrics.system.current) {
                document.getElementById('cpu-usage').textContent = metrics.system.current.cpu_percent.toFixed(1) + '%';
                document.getElementById('memory-usage').textContent = metrics.system.current.memory_percent.toFixed(1) + '%';
                document.getElementById('disk-usage').textContent = metrics.system.current.disk_percent.toFixed(1) + '%';
            }
            document.getElementById('uptime').textContent = metrics.system.uptime_hours.toFixed(1) + 'h';
            
            // Update timestamp
            document.getElementById('last-updated').textContent = 'Last updated: ' + new Date().toLocaleString(undefined, {{timeZoneName: 'short'}});
        }
        
        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            if (alerts && alerts.length > 0) {
                container.innerHTML = '<div class="alerts"><h3>Active Alerts</h3>' + 
                    alerts.map(alert => `<div class="alert-item">${alert.severity.toUpperCase()}: ${alert.message}</div>`).join('') + 
                    '</div>';
            } else {
                container.innerHTML = '';
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
"""

def create_dashboard_template_file():
    """Create dashboard template file"""
    import os
    os.makedirs("templates", exist_ok=True)
    with open("templates/dashboard.html", "w") as f:
        f.write(DASHBOARD_TEMPLATE)