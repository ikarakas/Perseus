# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
API Reference and Useful Links static page
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from ..common.version import version_config

def setup_api_reference_routes(app: FastAPI):
    """Setup API reference routes"""
    
    @app.get("/api-reference", response_class=HTMLResponse)
    async def api_reference_page():
        """API Reference and Useful Links page"""
        
        # Get version info for consistent styling
        classification_color = version_config.get_classification_color()
        classification_display = version_config.should_display_classification()
        classification_level = version_config.get_classification_level()
        version_string = version_config.get_version_string()
        build_info = version_config.get_build_info()
        
        classification_banner = ''
        if classification_display:
            classification_banner = f'<!-- Classification Banner --><div class="classification-banner">{classification_level}</div>'
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>API Reference - SBOM Platform</title>
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
                .card {{ 
                    background: rgba(255, 255, 255, 0.95); 
                    backdrop-filter: blur(5px);
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    border: 1px solid rgba(255,255,255,0.2);
                    margin-bottom: 20px;
                }}
                .card h3 {{ margin-top: 0; color: #2c3e50; }}
                .btn {{ 
                    background: #3498db; 
                    color: white; 
                    padding: 10px 20px; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer; 
                    text-decoration: none;
                    display: inline-block;
                }}
                .btn:hover {{ background: #2980b9; }}
                .btn-back {{
                    background: linear-gradient(45deg, #4fd1c7, #3aa99f); 
                    color: white; 
                    padding: 12px 25px; 
                    text-decoration: none; 
                    border-radius: 25px; 
                    font-weight: bold; 
                    box-shadow: 0 4px 15px rgba(79, 209, 199, 0.3);
                    transition: transform 0.2s, box-shadow 0.2s;
                    display: inline-block;
                    margin-bottom: 20px;
                }}
                .btn-back:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(79, 209, 199, 0.4);
                }}
                .code {{ 
                    background: #f8f9fa; 
                    padding: 10px; 
                    border-radius: 4px; 
                    font-family: monospace; 
                    margin: 10px 0;
                    border-left: 4px solid #3498db;
                }}
            </style>
        </head>
        <body>
            {classification_banner}
            
            <div class="header">
                <div class="container">
                    <h1>🔗 API Reference & Useful Links</h1>
                    <p>Complete API documentation and platform resources</p>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 10px;">
                        Perseus SBOM Platform | Version: {version_string}
                    </div>
                    <div style="font-size: 11px; opacity: 0.6; margin-top: 5px;">
                        Build: {build_info['timestamp'][:10]} | Environment: {build_info['environment']}
                    </div>
                </div>
            </div>
            
            <div class="container">
                <!-- Back Button -->
                <a href="/dashboard" class="btn-back">
                    ← Back to Dashboard
                </a>
                
                <!-- API Reference -->
                <div class="card">
                    <h3>🔗 Quick API Reference</h3>
                    <div class="code">
                        <strong>Analyze source code (Java/Python/JS/Go/C++):</strong><br>
                        curl -X POST http://localhost:8000/api/v1/analyze \\<br>
                        &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                        &nbsp;&nbsp;-d '{{"type":"source","language":"java","location":"/app/data/my-project"}}'
                    </div>
                    <div class="code">
                        <strong>Analyze Docker image:</strong><br>
                        curl -X POST http://localhost:8000/api/v1/analyze \\<br>
                        &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                        &nbsp;&nbsp;-d '{{"type":"docker","location":"ubuntu:latest"}}'
                    </div>
                    <div class="code">
                        <strong>Analyze binary/executable:</strong><br>
                        curl -X POST http://localhost:8000/api/v1/analyze \\<br>
                        &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                        &nbsp;&nbsp;-d '{{"type":"binary","location":"/app/data/my-binary"}}'
                    </div>
                    <div class="code">
                        <strong>Get analysis results:</strong><br>
                        curl http://localhost:8000/api/v1/analyses/{{analysis_id}}/results
                    </div>
                    <div class="code">
                        <strong>Run vulnerability scan on analysis:</strong><br>
                        curl -X POST http://localhost:8000/api/v1/analyses/{{analysis_id}}/vulnerabilities/scan
                    </div>
                    <div class="code">
                        <strong>Search components by name:</strong><br>
                        curl "http://localhost:8000/api/v1/components/search?name=spring&limit=100"
                    </div>
                    <div class="code">
                        <strong>Get components by analysis ID:</strong><br>
                        curl "http://localhost:8000/api/v1/components/by-analysis/{{analysis_id}}?limit=1000"
                    </div>
                    <div class="code">
                        <strong>CI/CD Integration - Register build:</strong><br>
                        curl -X POST http://localhost:8000/api/v1/cicd/builds \\<br>
                        &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                        &nbsp;&nbsp;-d '{{"build_id":"build-123","project":{{"name":"my-project","path":"./data/my-project","type":"java"}},"ci_context":{{"platform":"jenkins"}}}}'
                    </div>
                    <div class="code">
                        <strong>CI/CD Integration - Start scan:</strong><br>
                        curl -X POST http://localhost:8000/api/v1/cicd/builds/{{build_id}}/scan \\<br>
                        &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                        &nbsp;&nbsp;-d '{{"scan_type":"full","wait":true}}'
                    </div>
                    <div class="code">
                        <strong>Check rate limit status:</strong><br>
                        curl http://localhost:8000/admin/rate-limits/status
                    </div>
                    <div class="code">
                        <strong>Update vulnerability database:</strong><br>
                        curl -X POST http://localhost:8000/vulnerabilities/database/update
                    </div>
                </div>
                
                <!-- Useful Links -->
                <div class="card">
                    <h3>🔗 Useful Links</h3>
                    <h4 style="margin-top: 15px; color: #555;">Dashboards & UI</h4>
                    <ul style="font-size: 16px; line-height: 1.8;">
                        <li><a href="/dashboard" target="_blank" style="color: #3498db;">📊 Main Dashboard</a></li>
                        <li><a href="/dashboard/enhanced" target="_blank" style="color: #4fd1c7; font-weight: bold;">🚀 Enhanced Portal - Database Analytics</a></li>
                        <li><a href="/components/search" target="_blank" style="color: #3498db;">🔍 Component Search</a></li>
                        <li><a href="/vulnerability-details" target="_blank" style="color: #3498db;">🛡️ Vulnerability Details Viewer</a></li>
                    </ul>
                    
                    <h4 style="margin-top: 15px; color: #555;">System Status & Monitoring</h4>
                    <ul style="font-size: 16px; line-height: 1.8;">
                        <li><a href="/api/metrics" target="_blank" style="color: #3498db;">📈 Platform Metrics</a></li>
                        <li><a href="/health" target="_blank" style="color: #3498db;">❤️ Health Check</a></li>
                        <li><a href="/vulnerabilities/database/status" target="_blank" style="color: #3498db;">🔄 Vulnerability Database Status</a></li>
                    </ul>
                    
                    <h4 style="margin-top: 15px; color: #555;">Documentation</h4>
                    <ul style="font-size: 16px; line-height: 1.8;">
                        <li><a href="/docs" target="_blank" style="color: #3498db;">📖 Interactive API Documentation</a></li>
                        <li><a href="/docs/readme" target="_blank" style="color: #3498db;">📋 User Manual (README)</a></li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(html_response)