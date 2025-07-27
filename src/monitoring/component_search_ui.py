# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Component search UI with database integration
"""

from fastapi import Request, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db_session
from ..database.repositories import ComponentRepository, VulnerabilityRepository


def setup_component_search_routes(app):
    """Setup component search UI routes"""
    
    @app.get("/components/search", response_class=HTMLResponse)
    async def component_search_ui():
        """Component search interface"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perseus Component Search</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
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
        .search-container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        .search-box {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .search-input {
            width: 100%;
            padding: 1rem;
            font-size: 1.2rem;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            box-sizing: border-box;
        }
        .search-filters {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        .filter-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .filter-item input, .filter-item select {
            padding: 0.5rem;
            border-radius: 5px;
            border: none;
            background: rgba(255, 255, 255, 0.9);
        }
        .results-container {
            display: grid;
            gap: 1rem;
        }
        .component-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-left: 4px solid #4fd1c7;
        }
        .component-card.vulnerable {
            border-left-color: #ff4444;
        }
        .component-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }
        .component-name {
            font-size: 1.3rem;
            font-weight: bold;
            color: #4fd1c7;
        }
        .component-version {
            background: rgba(255, 255, 255, 0.2);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        .component-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .detail-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .vulnerability-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
            margin: 0.2rem;
        }
        .critical { background: #dc143c; }
        .high { background: #ff8c00; }
        .medium { background: #ffd700; color: #333; }
        .low { background: #32cd32; color: #333; }
        .loading {
            text-align: center;
            padding: 2rem;
            font-size: 1.2rem;
        }
        .no-results {
            text-align: center;
            padding: 3rem;
            color: #b0c4de;
            font-size: 1.2rem;
        }
        .back-link {
            color: #4fd1c7;
            text-decoration: none;
            font-size: 1.1rem;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Component Search</h1>
        <p><a href="/dashboard/enhanced" class="back-link">← Back to Dashboard</a></p>
    </div>
    
    <div class="search-container">
        <div class="search-box">
            <input type="text" id="searchInput" class="search-input" 
                   placeholder="Search components by name, version, or description..." 
                   onkeyup="handleSearch(event)">
            
            <div class="search-filters">
                <div class="filter-item">
                    <label>Analysis ID (first 8 chars):</label>
                    <input type="text" id="analysisIdFilter" placeholder="e.g. a517933d" 
                           style="width: 120px;" onkeyup="handleAnalysisIdSearch(event)">
                </div>
                <div class="filter-item">
                    <label>Show only vulnerable:</label>
                    <input type="checkbox" id="vulnerableOnly" onchange="performSearch()">
                </div>
                <div class="filter-item">
                    <label>Min Severity:</label>
                    <select id="minSeverity" onchange="performSearch()">
                        <option value="">All</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </select>
                </div>
                <div class="filter-item">
                    <label title="Component type detected by analysis (library=dependency, application=main program, etc.)">Component Type:</label>
                    <select id="componentType" onchange="performSearch()">
                        <option value="">All Types</option>
                        <option value="library">Library (dependencies)</option>
                        <option value="application">Application (main programs)</option>
                        <option value="container">Container</option>
                        <option value="framework">Framework</option>
                    </select>
                </div>
            </div>
        </div>
        
        <div id="loading" class="loading" style="display: none;">
            <h2>🔄 Searching...</h2>
        </div>
        
        <div id="results" class="results-container">
            <div class="no-results">
                <h2>🔍 Search Components</h2>
                <p>Enter a search term above to find components across all analyses</p>
            </div>
        </div>
    </div>

    <script>
        let searchTimeout = null;
        
        function handleSearch(event) {
            if (event.key === 'Enter') {
                performSearch();
            } else {
                // Debounce search
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(performSearch, 500);
            }
        }
        
        function handleAnalysisIdSearch(event) {
            if (event.key === 'Enter') {
                performSearch();
            } else {
                // Debounce search for analysis ID
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(performSearch, 300);
            }
        }
        
        async function performSearch() {
            const query = document.getElementById('searchInput').value.trim();
            const vulnerableOnly = document.getElementById('vulnerableOnly').checked;
            const minSeverity = document.getElementById('minSeverity').value;
            const componentType = document.getElementById('componentType').value;
            const analysisIdFilter = document.getElementById('analysisIdFilter').value.trim();
            
            if (!query && !vulnerableOnly && !analysisIdFilter) {
                document.getElementById('results').innerHTML = `
                    <div class="no-results">
                        <h2>🔍 Search Components</h2>
                        <p>Enter a search term, analysis ID, or check "Show only vulnerable" to find components</p>
                        <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">
                            💡 Tip: Use the first 8 characters of an Analysis ID to filter components from specific analyses
                        </p>
                    </div>
                `;
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            
            try {
                let url;
                const params = new URLSearchParams();
                
                if (vulnerableOnly) {
                    url = '/api/v1/components/vulnerable';
                    if (minSeverity) params.append('min_severity', minSeverity);
                    if (analysisIdFilter) params.append('analysis_id', analysisIdFilter);
                } else {
                    url = '/api/v1/components/search';
                    if (query) params.append('q', query);
                    if (analysisIdFilter) params.append('analysis_id', analysisIdFilter);
                }
                
                params.append('limit', '50');
                
                const response = await fetch(`${url}?${params}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                displayResults(data);
                
            } catch (error) {
                console.error('Search error:', error);
                document.getElementById('results').innerHTML = `
                    <div class="no-results">
                        <h2>❌ Search Error</h2>
                        <p>${error.message}</p>
                    </div>
                `;
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function displayResults(data) {
            const results = data.components || data.vulnerable_components || [];
            const resultsContainer = document.getElementById('results');
            
            if (results.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="no-results">
                        <h2>📭 No Results Found</h2>
                        <p>No components match your search criteria</p>
                    </div>
                `;
                return;
            }
            
            resultsContainer.innerHTML = results.map(component => `
                <div class="component-card ${component.vulnerability_count > 0 ? 'vulnerable' : ''}">
                    <div class="component-header">
                        <div>
                            <div class="component-name">${component.name}</div>
                            <div style="margin-top: 0.5rem;">
                                <span class="component-version">v${component.version}</span>
                                <span class="component-version">${component.type || 'unknown'}</span>
                            </div>
                        </div>
                        <div>
                            ${component.vulnerability_count > 0 ? `
                                ${component.critical_vulnerabilities > 0 ? 
                                    `<span class="vulnerability-badge critical">${component.critical_vulnerabilities} Critical</span>` : ''}
                                ${component.high_vulnerabilities > 0 ? 
                                    `<span class="vulnerability-badge high">${component.high_vulnerabilities} High</span>` : ''}
                                <span class="vulnerability-badge" style="background: #666;">
                                    ${component.vulnerability_count} Total
                                </span>
                            ` : '<span class="vulnerability-badge" style="background: #32cd32; color: #333;">✓ Clean</span>'}
                        </div>
                    </div>
                    
                    ${component.description ? `<p style="color: #b0c4de; margin: 1rem 0;">${component.description}</p>` : ''}
                    
                    <div class="component-details">
                        ${component.purl ? `
                            <div class="detail-item">
                                <span>Package URL:</span>
                                <span style="font-family: monospace; font-size: 0.9em;">${component.purl}</span>
                            </div>
                        ` : ''}
                        <div class="detail-item">
                            <span>Analysis ID:</span>
                            <span style="font-family: monospace; font-size: 0.9em;">${component.analysis_id || 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span>Vulnerabilities:</span>
                            <span>${component.vulnerability_count || 0}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    </script>
</body>
</html>
        '''
    
    return app