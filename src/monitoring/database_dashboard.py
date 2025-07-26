# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Enhanced dashboard with database integration
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..database.repositories import (
    AnalysisRepository, ComponentRepository, SBOMRepository,
    VulnerabilityRepository, VulnerabilityScanRepository
)
from ..common.version import VersionConfig


class DatabaseDashboard:
    """Enhanced dashboard with database features"""
    
    def __init__(self):
        self.dashboard_html = self._generate_dashboard_html()
    
    def setup_routes(self, app):
        """Setup dashboard routes with database integration"""
        
        @app.get("/dashboard/enhanced", response_class=HTMLResponse)
        async def enhanced_dashboard():
            """Enhanced dashboard with database features"""
            return self.dashboard_html
        
        @app.get("/api/v1/dashboard/metrics")
        async def get_dashboard_metrics(db: Session = Depends(get_db_session)):
            """Get comprehensive dashboard metrics from database"""
            try:
                analysis_repo = AnalysisRepository(db)
                component_repo = ComponentRepository(db)
                sbom_repo = SBOMRepository(db)
                vuln_repo = VulnerabilityRepository(db)
                scan_repo = VulnerabilityScanRepository(db)
                
                # Get comprehensive statistics
                analysis_stats = analysis_repo.get_statistics(days=30)
                vulnerability_summary = analysis_repo.get_vulnerability_summary()
                component_stats = component_repo.get_component_statistics()
                sbom_stats = sbom_repo.get_sbom_statistics()
                vuln_stats = vuln_repo.get_vulnerability_statistics()
                scan_stats = scan_repo.get_scan_statistics()
                
                # Get top vulnerable components
                top_vulnerable = component_repo.get_top_vulnerable_components(limit=10)
                
                # Get recent analyses
                recent_analyses = analysis_repo.get_recent_analyses(limit=10)
                
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "analysis_statistics": analysis_stats,
                    "vulnerability_summary": vulnerability_summary,
                    "component_statistics": component_stats,
                    "sbom_statistics": sbom_stats,
                    "vulnerability_statistics": vuln_stats,
                    "scan_statistics": scan_stats,
                    "top_vulnerable_components": top_vulnerable,
                    "recent_analyses": [
                        {
                            "analysis_id": a.analysis_id,
                            "status": a.status.value,
                            "analysis_type": a.analysis_type,
                            "component_count": a.component_count,
                            "vulnerability_count": a.vulnerability_count,
                            "created_at": a.created_at.isoformat() if a.created_at else None
                        }
                        for a in recent_analyses
                    ]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/v1/dashboard/trends")
        async def get_vulnerability_trends(
            days: int = 30, 
            db: Session = Depends(get_db_session)
        ):
            """Get vulnerability trends over time"""
            try:
                analysis_repo = AnalysisRepository(db)
                
                # Get analyses from the last N days
                since = datetime.utcnow() - timedelta(days=days)
                analyses = db.query(analysis_repo.model).filter(
                    analysis_repo.model.created_at >= since
                ).order_by(analysis_repo.model.created_at).all()
                
                # Group by day
                daily_stats = {}
                for analysis in analyses:
                    day = analysis.created_at.date().isoformat()
                    if day not in daily_stats:
                        daily_stats[day] = {
                            'date': day,
                            'analyses': 0,
                            'total_vulnerabilities': 0,
                            'critical_vulnerabilities': 0,
                            'high_vulnerabilities': 0,
                            'components': 0
                        }
                    
                    daily_stats[day]['analyses'] += 1
                    daily_stats[day]['total_vulnerabilities'] += analysis.vulnerability_count or 0
                    daily_stats[day]['critical_vulnerabilities'] += analysis.critical_vulnerability_count or 0
                    daily_stats[day]['high_vulnerabilities'] += analysis.high_vulnerability_count or 0
                    daily_stats[day]['components'] += analysis.component_count or 0
                
                return {
                    "trends": list(daily_stats.values()),
                    "period_days": days
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/v1/dashboard/sboms")
        async def get_recent_sboms(
            limit: int = 10,
            db: Session = Depends(get_db_session)
        ):
            """Get recent SBOMs for dashboard display"""
            try:
                sbom_repo = SBOMRepository(db)
                recent_sboms = sbom_repo.get_recent_sboms(limit=limit)
                
                return {
                    "sboms": [
                        {
                            "sbom_id": sbom.sbom_id,
                            "name": sbom.name,
                            "format": sbom.format,
                            "namespace": sbom.namespace,
                            "analysis_id": str(sbom.analysis_id),
                            "component_count": sbom.component_count,
                            "created_at": sbom.created_at.isoformat() if sbom.created_at else None,
                            "file_path": sbom.file_path
                        }
                        for sbom in recent_sboms
                    ],
                    "total": len(recent_sboms)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _generate_dashboard_html(self) -> str:
        """Generate enhanced dashboard HTML with database features"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perseus Enhanced Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .classification-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #00FF00;
            color: #000;
            font-weight: bold;
            text-align: center;
            padding: 3px 0;
            font-size: 12px;
            z-index: 1001;
            border-bottom: 1px solid #000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            padding-top: 25px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        .header {
            background: rgba(0,0,0,0.3);
            padding: 1rem 2rem;
            border-bottom: 2px solid #4a90e2;
        }
        .header h1 {
            margin: 0;
            font-size: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .metric-card h3 {
            margin: 0 0 1rem 0;
            color: #4fd1c7;
            font-size: 1.3rem;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        .metric-label {
            color: #b0c4de;
            font-size: 0.9rem;
        }
        .chart-container {
            grid-column: span 2;
            height: 400px;
        }
        .vulnerability-severity {
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
        }
        .severity-item {
            flex: 1;
            text-align: center;
            padding: 0.5rem;
            border-radius: 8px;
        }
        .critical { background: rgba(220, 20, 60, 0.3); }
        .high { background: rgba(255, 140, 0, 0.3); }
        .medium { background: rgba(255, 215, 0, 0.3); }
        .low { background: rgba(50, 205, 50, 0.3); }
        .component-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .component-item {
            background: rgba(255, 255, 255, 0.1);
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #ff4444;
        }
        .component-name {
            font-weight: bold;
            font-size: 1.1rem;
        }
        .component-details {
            font-size: 0.9rem;
            color: #b0c4de;
            margin-top: 0.5rem;
        }
        .refresh-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4fd1c7;
            color: #1e3c72;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(79, 209, 199, 0.3);
        }
        .refresh-btn:hover {
            background: #3aa99f;
            transform: translateY(-2px);
        }
        .loading {
            text-align: center;
            padding: 2rem;
            font-size: 1.2rem;
        }
        .error {
            background: rgba(220, 20, 60, 0.3);
            border: 1px solid #dc143c;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <!-- Classification Banner -->
    <div class="classification-banner">NOT CLASSIFIED</div>
    
    <div class="header">
        <h1>🛡️ Perseus Enhanced Dashboard</h1>
        <p>Enterprise SBOM & Vulnerability Management Platform - Database-Powered Analytics</p>
        <div style="margin-top: 1rem;">
            <a href="/dashboard" style="color: #4fd1c7; margin-right: 2rem; font-weight: bold;">← 📊 Classic Dashboard</a>
            <a href="/components/search" style="color: #4fd1c7; margin-right: 2rem;">🔍 Component Search</a>
            <a href="/docs" style="color: #4fd1c7;">📚 API Documentation</a>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
    
    <div id="loading" class="loading">
        <h2>🔄 Loading Enhanced Dashboard...</h2>
        <p>Fetching data from database...</p>
    </div>
    
    <div id="error" class="error" style="display: none;"></div>
    
    <div id="dashboard" class="dashboard-grid" style="display: none;">
        <!-- Analysis Statistics -->
        <div class="metric-card">
            <h3>📊 Analysis Statistics (30 Days)</h3>
            <div class="metric-value" id="total-analyses">-</div>
            <div class="metric-label">Total Analyses</div>
            <div style="margin-top: 1rem;">
                <div>Success Rate: <span id="success-rate">-</span>%</div>
                <div>Avg Duration: <span id="avg-duration">-</span>s</div>
            </div>
        </div>
        
        <!-- Vulnerability Summary -->
        <div class="metric-card">
            <h3>🚨 Vulnerability Summary</h3>
            <div class="vulnerability-severity">
                <div class="severity-item critical">
                    <div class="metric-value" id="critical-vulns">-</div>
                    <div class="metric-label">Critical</div>
                </div>
                <div class="severity-item high">
                    <div class="metric-value" id="high-vulns">-</div>
                    <div class="metric-label">High</div>
                </div>
            </div>
            <div>Total Vulnerabilities: <span id="total-vulns">-</span></div>
        </div>
        
        <!-- Component Statistics -->
        <div class="metric-card">
            <h3>📦 Component Statistics</h3>
            <div class="metric-value" id="total-components">-</div>
            <div class="metric-label">Total Components</div>
            <div style="margin-top: 1rem;">
                <div>Unique: <span id="unique-components">-</span></div>
                <div>Vulnerable: <span id="vulnerable-components">-</span></div>
                <div>Vulnerability Rate: <span id="vulnerability-rate">-</span>%</div>
            </div>
        </div>
        
        <!-- SBOM Statistics -->
        <div class="metric-card">
            <h3>📋 SBOM Statistics</h3>
            <div class="metric-value" id="total-sboms">-</div>
            <div class="metric-label">Generated SBOMs</div>
            <div style="margin-top: 1rem;">
                <div>Coverage: <span id="sbom-coverage">-</span>%</div>
                <div id="sbom-formats">-</div>
            </div>
        </div>
        
        <!-- Vulnerability Trends Chart -->
        <div class="metric-card chart-container">
            <h3>📈 Vulnerability Trends (30 Days)</h3>
            <canvas id="trendsChart"></canvas>
        </div>
        
        <!-- Top Vulnerable Components -->
        <div class="metric-card">
            <h3>🎯 Top Vulnerable Components</h3>
            <div id="vulnerable-components-list" class="component-list">
                Loading...
            </div>
        </div>
        
        <!-- Recent Analyses -->
        <div class="metric-card">
            <h3>⏱️ Recent Analyses</h3>
            <div id="recent-analyses-list" class="component-list">
                Loading...
            </div>
        </div>
        
        <!-- Generated SBOMs -->
        <div class="metric-card">
            <h3>📋 Generated SBOMs</h3>
            <div id="generated-sboms-list" class="component-list">
                Loading...
            </div>
        </div>
    </div>

    <script>
        let trendsChart = null;
        
        async function fetchDashboardData() {
            try {
                const response = await fetch('/api/v1/dashboard/metrics');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
                throw error;
            }
        }
        
        async function fetchTrendsData() {
            try {
                const response = await fetch('/api/v1/dashboard/trends?days=30');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching trends data:', error);
                return { trends: [] };
            }
        }
        
        async function fetchSbomsData() {
            try {
                const response = await fetch('/api/v1/dashboard/sboms?limit=10');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching SBOMs data:', error);
                return { sboms: [] };
            }
        }
        
        function updateDashboard(data) {
            // Analysis Statistics
            const analysisStats = data.analysis_statistics;
            document.getElementById('total-analyses').textContent = analysisStats.total_analyses;
            document.getElementById('success-rate').textContent = analysisStats.success_rate.toFixed(1);
            document.getElementById('avg-duration').textContent = analysisStats.average_duration_seconds.toFixed(1);
            
            // Vulnerability Summary
            const vulnSummary = data.vulnerability_summary;
            document.getElementById('critical-vulns').textContent = vulnSummary.total_critical;
            document.getElementById('high-vulns').textContent = vulnSummary.total_high;
            document.getElementById('total-vulns').textContent = vulnSummary.total_vulnerabilities;
            
            // Component Statistics
            const compStats = data.component_statistics;
            document.getElementById('total-components').textContent = compStats.total_components;
            document.getElementById('unique-components').textContent = compStats.unique_components;
            document.getElementById('vulnerable-components').textContent = compStats.vulnerable_components;
            document.getElementById('vulnerability-rate').textContent = compStats.vulnerability_rate.toFixed(1);
            
            // SBOM Statistics
            const sbomStats = data.sbom_statistics;
            document.getElementById('total-sboms').textContent = sbomStats.total_sboms;
            document.getElementById('sbom-coverage').textContent = sbomStats.sbom_coverage.toFixed(1);
            
            // Format distribution
            const formatDist = Object.entries(sbomStats.format_distribution)
                .map(([format, count]) => `${format.toUpperCase()}: ${count}`)
                .join(', ');
            document.getElementById('sbom-formats').textContent = formatDist || 'No SBOMs';
            
            // Top Vulnerable Components
            const vulnList = document.getElementById('vulnerable-components-list');
            vulnList.innerHTML = data.top_vulnerable_components.map(comp => `
                <div class="component-item">
                    <div class="component-name">${comp.name} v${comp.version}</div>
                    <div class="component-details">
                        🚨 ${comp.critical} Critical, ${comp.high} High | 
                        📊 ${comp.vulnerabilities} Total | 
                        🔍 ${comp.affected_analyses} Analyses
                    </div>
                </div>
            `).join('') || '<div>No vulnerable components found</div>';
            
            // Recent Analyses
            const analysesList = document.getElementById('recent-analyses-list');
            analysesList.innerHTML = data.recent_analyses.map(analysis => `
                <div class="component-item">
                    <div class="component-name">${analysis.analysis_type.toUpperCase()} - ${analysis.status}</div>
                    <div class="component-details">
                        📦 ${analysis.component_count} Components | 
                        🚨 ${analysis.vulnerability_count} Vulnerabilities | 
                        ⏰ ${new Date(analysis.created_at).toLocaleString()}
                    </div>
                </div>
            `).join('') || '<div>No recent analyses found</div>';
        }
        
        function updateSbomsList(sbomsData) {
            const sbomsList = document.getElementById('generated-sboms-list');
            sbomsList.innerHTML = sbomsData.sboms.map(sbom => `
                <div class="component-item">
                    <div class="component-name">
                        ${sbom.format.toUpperCase()}: ${sbom.name}
                        <button onclick="downloadSBOM('${sbom.sbom_id}')" 
                                style="float: right; background: #4fd1c7; color: #1e3c72; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">
                            📥 Download
                        </button>
                    </div>
                    <div class="component-details">
                        🆔 ${sbom.sbom_id} | 
                        📦 ${sbom.component_count} Components | 
                        🔗 Analysis: ${sbom.analysis_id.substring(0, 8)}... | 
                        ⏰ ${new Date(sbom.created_at).toLocaleString()}
                        ${sbom.file_path ? `<br>📁 ${sbom.file_path}` : ''}
                    </div>
                </div>
            `).join('') || '<div>No SBOMs generated yet</div>';
        }
        
        async function downloadSBOM(sbomId) {
            try {
                const response = await fetch(`/sbom/${sbomId}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const sbom = await response.json();
                
                // Create download link
                const blob = new Blob([JSON.stringify(sbom, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `sbom-${sbomId}.json`;
                a.click();
                URL.revokeObjectURL(url);
            } catch (error) {
                showError(`Failed to download SBOM: ${error.message}`);
            }
        }
        
        function updateTrendsChart(trendsData) {
            const ctx = document.getElementById('trendsChart').getContext('2d');
            
            if (trendsChart) {
                trendsChart.destroy();
            }
            
            const trends = trendsData.trends || [];
            
            trendsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: trends.map(t => new Date(t.date).toLocaleDateString()),
                    datasets: [
                        {
                            label: 'Critical Vulnerabilities',
                            data: trends.map(t => t.critical_vulnerabilities),
                            borderColor: '#dc143c',
                            backgroundColor: 'rgba(220, 20, 60, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'High Vulnerabilities',
                            data: trends.map(t => t.high_vulnerabilities),
                            borderColor: '#ff8c00',
                            backgroundColor: 'rgba(255, 140, 0, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Total Vulnerabilities',
                            data: trends.map(t => t.total_vulnerabilities),
                            borderColor: '#4fd1c7',
                            backgroundColor: 'rgba(79, 209, 199, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: 'white' }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        y: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    }
                }
            });
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = `❌ Error: ${message}`;
            errorDiv.style.display = 'block';
        }
        
        async function refreshDashboard() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('dashboard').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            
            try {
                const [dashboardData, trendsData, sbomsData] = await Promise.all([
                    fetchDashboardData(),
                    fetchTrendsData(),
                    fetchSbomsData()
                ]);
                
                updateDashboard(dashboardData);
                updateTrendsChart(trendsData);
                updateSbomsList(sbomsData);
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard').style.display = 'grid';
                
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                showError(error.message);
            }
        }
        
        // Initial load
        refreshDashboard();
        
        // Auto-refresh every 30 seconds
        setInterval(refreshDashboard, 30000);
    </script>
</body>
</html>
        '''