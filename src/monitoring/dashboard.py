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

class MonitoringDashboard:
    """Web dashboard for platform monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_manager = AlertManager(metrics_collector)
        # self.templates = Jinja2Templates(directory="templates")
    
    def setup_routes(self, app: FastAPI):
        """Setup dashboard routes"""
        
        @app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            metrics = self.metrics_collector.get_summary_dashboard()
            alerts = self.alert_manager.get_active_alerts()
            
            # Return enhanced HTML dashboard
            return HTMLResponse(f"""
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
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="container">
                        <h1>🛡️ SBOM Platform Dashboard</h1>
                        <p>NATO-Grade Software Bill of Materials Generation & Analysis</p>
                        <div style="font-size: 12px; opacity: 0.8; margin-top: 10px;">
                            ⭐ Airborne Warning & Control System (AWACS) - Software Asset Monitoring
                        </div>
                    </div>
                </div>
                
                <div class="container">
                    <div class="grid">
                        <!-- Analysis Form -->
                        <div class="card">
                            <h3>📁 Submit Analysis</h3>
                            <p><strong>Note:</strong> Files must be copied to the <code>./data/</code> directory first.</p>
                            
                            <div class="form-group">
                                <label for="analysisType">Analysis Type:</label>
                                <select id="analysisType" onchange="toggleAnalysisOptions()">
                                    <option value="source">Source Code</option>
                                    <option value="binary">Binary Files</option>
                                    <option value="docker">Docker Image</option>
                                </select>
                            </div>
                            
                            <div class="form-group" id="languageGroup">
                                <label for="language">Language:</label>
                                <select id="language">
                                    <option value="java">Java</option>
                                    <option value="c++">C++</option>
                                </select>
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
                    
                    <!-- API Reference -->
                    <div class="card">
                        <h3>🔗 Quick API Reference</h3>
                        <div class="code">
                            <strong>Copy files to data directory:</strong><br>
                            cp -r /path/to/project ./data/my-project
                        </div>
                        <div class="code">
                            <strong>Analyze source code via curl:</strong><br>
                            curl -X POST http://localhost:8080/analyze/source \\<br>
                            &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                            &nbsp;&nbsp;-d '{{"type":"source","language":"java","location":"/app/data/my-project"}}'
                        </div>
                        <div class="code">
                            <strong>Analyze Docker image via curl:</strong><br>
                            curl -X POST http://localhost:8080/analyze/docker \\<br>
                            &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                            &nbsp;&nbsp;-d '{{"type":"docker","location":"ubuntu:latest"}}'
                        </div>
                        <p><strong>Useful Links:</strong></p>
                        <ul>
                            <li><a href="/api/metrics" target="_blank">📈 Platform Metrics</a></li>
                            <li><a href="/health" target="_blank">❤️ Health Check</a></li>
                            <li><a href="/docs/readme" target="_blank">📖 Full User Manual</a></li>
                        </ul>
                    </div>
                </div>
                
                <script>
                    function toggleAnalysisOptions() {{
                        const type = document.getElementById('analysisType').value;
                        const languageGroup = document.getElementById('languageGroup');
                        const locationGroup = document.getElementById('locationGroup');
                        const dockerGroup = document.getElementById('dockerGroup');
                        
                        if (type === 'source') {{
                            languageGroup.style.display = 'block';
                            locationGroup.style.display = 'block';
                            dockerGroup.style.display = 'none';
                        }} else if (type === 'binary') {{
                            languageGroup.style.display = 'none';
                            locationGroup.style.display = 'block';
                            dockerGroup.style.display = 'none';
                        }} else if (type === 'docker') {{
                            languageGroup.style.display = 'none';
                            locationGroup.style.display = 'none';
                            dockerGroup.style.display = 'block';
                        }}
                    }}
                    
                    async function submitAnalysis() {{
                        const type = document.getElementById('analysisType').value;
                        const language = document.getElementById('language').value;
                        const location = document.getElementById('location').value;
                        const dockerImage = document.getElementById('dockerImage').value;
                        
                        const payload = {{
                            type: type
                        }};
                        
                        if (type === 'source') {{
                            payload.language = language;
                            payload.location = location;
                        }} else if (type === 'binary') {{
                            payload.location = location;
                        }} else if (type === 'docker') {{
                            payload.location = dockerImage;
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
                            resultsDiv.innerHTML = `
                                <h4>📊 Analysis Results</h4>
                                <p><strong>Status:</strong> ${{status.status}}</p>
                                <p><strong>Components Found:</strong> ${{results.components ? results.components.length : 0}}</p>
                                <p><strong>Analysis ID:</strong> ${{analysisId}}</p>
                                <p><em>Use this Analysis ID to generate an SBOM below.</em></p>
                            `;
                        }} catch (error) {{
                            console.error('Error checking status:', error);
                        }}
                    }}
                    
                    async function generateSBOM() {{
                        const analysisIds = document.getElementById('analysisIds').value.split(',').map(s => s.trim());
                        const format = document.getElementById('sbomFormat').value;
                        
                        try {{
                            const response = await fetch('/sbom/generate', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{
                                    analysis_ids: analysisIds,
                                    format: format,
                                    include_licenses: true,
                                    include_vulnerabilities: false
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
                    
                    // Load metrics on page load
                    async function loadMetrics() {{
                        try {{
                            const response = await fetch('/api/metrics');
                            const metrics = await response.json();
                            
                            document.getElementById('analysisCount').textContent = metrics.analysis.total_analyses || 0;
                            document.getElementById('sbomCount').textContent = metrics.sbom.total_sboms_generated || 0;
                            document.getElementById('uptime').textContent = (metrics.system.uptime_hours || 0).toFixed(1) + 'h';
                        }} catch (error) {{
                            console.error('Error loading metrics:', error);
                        }}
                    }}
                    
                    // Load metrics on page load and refresh every 30 seconds
                    loadMetrics();
                    setInterval(loadMetrics, 30000);
                </script>
            </body>
            </html>
            """)
        
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
            document.getElementById('last-updated').textContent = 'Last updated: ' + new Date().toLocaleString();
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