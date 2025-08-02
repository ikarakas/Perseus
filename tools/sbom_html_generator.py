#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
SBOM HTML Generator - Creates beautiful HTML reports from SBOM JSON data
"""

import json
import sys
from datetime import datetime
from collections import defaultdict
import os

def detect_sbom_format(data):
    """Detect the SBOM format from the JSON structure"""
    if 'spdxVersion' in data or 'SPDXID' in data:
        return "SPDX"
    elif 'bomFormat' in data or 'specVersion' in data:
        return "CycloneDX"
    elif 'SoftwareIdentity' in data:
        return "SWID"
    else:
        return "Unknown"

def generate_html_report(json_file_path, output_file=None):
    """Generate a beautiful HTML report from SBOM JSON data"""
    
    try:
        with open(json_file_path, 'r') as f:
            sbom_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{json_file_path}'.")
        return
    
    # Detect SBOM format and extract data accordingly
    sbom_format = detect_sbom_format(sbom_data)
    
    if sbom_format == "SPDX":
        # Extract SPDX data
        doc_info = sbom_data.get('creationInfo', {})
        created_date = doc_info.get('created', 'Unknown')
        creators = doc_info.get('creators', [])
        doc_name = sbom_data.get('name', 'Unknown')
        doc_namespace = sbom_data.get('documentNamespace', '')
        spec_version = sbom_data.get('spdxVersion', 'Unknown')
        packages = sbom_data.get('packages', [])
        
    elif sbom_format == "CycloneDX":
        # Extract CycloneDX data
        metadata = sbom_data.get('metadata', {})
        created_date = metadata.get('timestamp', 'Unknown')
        creators = []
        if 'tools' in metadata:
            for tool in metadata.get('tools', []):
                creators.append(f"Tool: {tool.get('name', 'Unknown')} {tool.get('version', '')}")
        doc_name = metadata.get('component', {}).get('name', 'Unknown')
        doc_namespace = sbom_data.get('serialNumber', '')
        spec_version = f"CycloneDX {sbom_data.get('specVersion', 'Unknown')}"
        # Convert components to package-like format
        packages = []
        for comp in sbom_data.get('components', []):
            pkg = {
                'name': comp.get('name', 'Unknown'),
                'SPDXID': comp.get('bom-ref', ''),
                'downloadLocation': comp.get('purl', ''),
                'filesAnalyzed': False,
                'licenseConcluded': comp.get('licenses', [{}])[0].get('license', {}).get('id', 'Unknown') if comp.get('licenses') else 'Unknown',
                'copyrightText': comp.get('copyright', ''),
                'versionInfo': comp.get('version', ''),
                'externalRefs': [{'referenceLocator': comp.get('purl', ''), 'referenceType': 'purl'}] if comp.get('purl') else []
            }
            packages.append(pkg)
            
    elif sbom_format == "SWID":
        # Extract SWID data
        swid = sbom_data.get('SoftwareIdentity', {})
        created_date = 'Unknown'  # SWID doesn't have creation date in standard location
        creators = []
        if 'Entity' in swid:
            entities = swid.get('Entity', [])
            if not isinstance(entities, list):
                entities = [entities]
            for entity in entities:
                if isinstance(entity, dict) and 'tagCreator' in entity.get('@role', ''):
                    creators.append(entity.get('@name', 'Unknown'))
                    # Try to extract date from thumbprint
                    thumbprint = entity.get('@thumbprint', '')
                    if 'generated-at-' in thumbprint:
                        created_date = thumbprint.split('generated-at-')[1].replace('Z', '')
                        if created_date.endswith('Z'):
                            created_date = created_date[:-1]
        doc_name = swid.get('@name', 'Unknown')
        doc_namespace = swid.get('@tagId', '')
        spec_version = f"SWID {swid.get('@version', 'Unknown')}"
        # Convert SWID Payload to package-like format
        packages = []
        if 'Payload' in swid:
            payload = swid.get('Payload', {})
            # Check for Resource elements (components/packages)
            resources = payload.get('Resource', [])
            if not isinstance(resources, list):
                resources = [resources]
            for resource in resources:
                if isinstance(resource, dict):
                    pkg = {
                        'name': resource.get('@name', 'Unknown'),
                        'SPDXID': f"Resource-{resource.get('@name', '').replace('/', '-')}",
                        'downloadLocation': resource.get('@location', ''),
                        'filesAnalyzed': False,
                        'licenseConcluded': 'Unknown',
                        'copyrightText': '',
                        'versionInfo': resource.get('@version', ''),
                        'externalRefs': []
                    }
                    packages.append(pkg)
            
            # Also check for Directory/File structure
            directories = payload.get('Directory', [])
            if not isinstance(directories, list):
                directories = [directories]
            for directory in directories:
                if isinstance(directory, dict) and 'File' in directory:
                    files = directory.get('File', [])
                    if not isinstance(files, list):
                        files = [files]
                    for file_item in files:
                        if isinstance(file_item, dict):
                            pkg = {
                                'name': file_item.get('@name', 'Unknown'),
                                'SPDXID': f"File-{file_item.get('@name', '').replace('/', '-')}",
                                'downloadLocation': directory.get('@name', '') + '/' + file_item.get('@name', ''),
                                'filesAnalyzed': False,
                                'licenseConcluded': 'Unknown',
                                'copyrightText': '',
                                'versionInfo': file_item.get('@version', ''),
                                'externalRefs': []
                            }
                            packages.append(pkg)
    else:
        # Unknown format - try to extract what we can
        doc_name = sbom_data.get('name', 'Unknown')
        created_date = 'Unknown'
        creators = []
        doc_namespace = ''
        spec_version = 'Unknown'
        packages = []
    
    # Parse creation date
    try:
        dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
        formatted_date = dt.strftime('%B %d, %Y at %I:%M:%S %p UTC')
    except:
        formatted_date = created_date
    
    # Group packages by type
    package_types = defaultdict(list)
    for pkg in packages:
        pkg_type = "Unknown"
        if 'externalRefs' in pkg:
            for ref in pkg['externalRefs']:
                if ref.get('referenceType') == 'purl':
                    purl = ref.get('referenceLocator', '')
                    if purl.startswith('pkg:deb/'):
                        pkg_type = "Debian Package"
                    elif purl.startswith('pkg:maven/'):
                        pkg_type = "Java/Maven Package"
                    elif purl.startswith('pkg:npm/'):
                        pkg_type = "Node.js Package"
                    elif purl.startswith('pkg:pypi/'):
                        pkg_type = "Python Package"
                    else:
                        pkg_type = "Other"
                    break
        package_types[pkg_type].append(pkg)
    
    # License analysis
    license_counts = defaultdict(int)
    for pkg in packages:
        license_info = pkg.get('licenseConcluded', 'Unknown')
        if license_info != 'Unknown':
            license_counts[license_info] += 1
        else:
            license_counts['Unknown'] += 1
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SBOM Report - {doc_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.1em;
            margin-bottom: 20px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .info-card {{
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .info-card h3 {{
            color: #34495e;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .info-card p {{
            color: #2c3e50;
            font-weight: 500;
        }}
        
        .stats-section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .packages-section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        .package-type {{
            margin-bottom: 40px;
        }}
        
        .package-type h3 {{
            color: #2c3e50;
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}
        
        .package-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 15px;
        }}
        
        .package-card {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s ease;
        }}
        
        .package-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .package-name {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 1.1em;
            margin-bottom: 5px;
        }}
        
        .package-version {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        
        .package-license {{
            color: #27ae60;
            font-size: 0.85em;
            background: #e8f5e8;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 8px;
        }}
        
        .package-purl {{
            color: #3498db;
            font-size: 0.8em;
            word-break: break-all;
        }}
        
        .license-section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        .license-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .license-item:last-child {{
            border-bottom: none;
        }}
        
        .license-name {{
            flex: 1;
            font-weight: 500;
        }}
        
        .license-count {{
            background: #3498db;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .search-box {{
            width: 100%;
            padding: 12px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            font-size: 1em;
            margin-bottom: 20px;
            transition: border-color 0.3s ease;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: #3498db;
        }}
        
        .hidden {{
            display: none;
        }}
        
        .footer {{
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            padding: 20px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .package-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📦 Software Bill of Materials</h1>
            <p class="subtitle">Comprehensive Software Composition Analysis</p>
            <div class="info-grid">
                <div class="info-card">
                    <h3>Document Name</h3>
                    <p>{doc_name}</p>
                </div>
                <div class="info-card">
                    <h3>Generated</h3>
                    <p>{formatted_date}</p>
                </div>
                <div class="info-card">
                    <h3>SBOM Format</h3>
                    <p>{spec_version}</p>
                </div>
                <div class="info-card">
                    <h3>Generated By</h3>
                    <p>{', '.join(creators) if creators else 'Unknown'}</p>
                </div>
            </div>
        </div>
        
        <div class="stats-section">
            <h2 style="color: #2c3e50; margin-bottom: 20px;">📊 Summary Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{len(packages)}</div>
                    <div class="stat-label">Total Packages</div>
                </div>
"""
    
    # Add package type statistics
    for pkg_type, pkgs in package_types.items():
        html_content += f"""
                <div class="stat-card">
                    <div class="stat-number">{len(pkgs)}</div>
                    <div class="stat-label">{pkg_type}</div>
                </div>
"""
    
    html_content += """
            </div>
        </div>
        
        <div class="packages-section">
            <h2 style="color: #2c3e50; margin-bottom: 20px;">📋 Package Details</h2>
            <input type="text" class="search-box" id="packageSearch" placeholder="Search packages by name, version, or license...">
"""
    
    # Add packages by type
    for pkg_type, pkgs in package_types.items():
        # Sort packages by name
        pkgs.sort(key=lambda x: x.get('name', '').lower())
        
        html_content += f"""
            <div class="package-type">
                <h3>{pkg_type} ({len(pkgs)} packages)</h3>
                <div class="package-grid">
"""
        
        for pkg in pkgs:
            name = pkg.get('name', 'Unknown')
            version = pkg.get('versionInfo', pkg.get('version', 'Unknown'))
            license_info = pkg.get('licenseConcluded', 'Unknown')
            
            # Truncate long license strings
            if len(license_info) > 60:
                license_info = license_info[:57] + "..."
            
            # Get PURL
            purl = ""
            if 'externalRefs' in pkg:
                for ref in pkg['externalRefs']:
                    if ref.get('referenceType') == 'purl':
                        purl = ref.get('referenceLocator', '')
                        break
            
            html_content += f"""
                    <div class="package-card" data-search="{name.lower()} {version.lower()} {license_info.lower()}">
                        <div class="package-name">{name}</div>
                        <div class="package-version">Version: {version}</div>
                        <div class="package-license">{license_info}</div>
                        <div class="package-purl">{purl}</div>
                    </div>
"""
        
        html_content += """
                </div>
            </div>
"""
    
    # Add license analysis
    html_content += """
        </div>
        
        <div class="license-section">
            <h2 style="color: #2c3e50; margin-bottom: 20px;">📜 License Analysis</h2>
"""
    
    # Show top licenses
    sorted_licenses = sorted(license_counts.items(), key=lambda x: x[1], reverse=True)
    for license_name, count in sorted_licenses[:15]:
        percentage = (count / len(packages)) * 100
        html_content += f"""
            <div class="license-item">
                <div class="license-name">{license_name}</div>
                <div class="license-count">{count} packages ({percentage:.1f}%)</div>
            </div>
"""
    
    html_content += """
        </div>
    </div>
    
    <div class="footer">
        <p>Generated by SBOM HTML Generator | Data License: CC0-1.0</p>
    </div>
    
    <script>
        // Search functionality
        document.getElementById('packageSearch').addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const packageCards = document.querySelectorAll('.package-card');
            
            packageCards.forEach(card => {
                const searchData = card.getAttribute('data-search');
                if (searchData.includes(searchTerm)) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            });
        });
        
        // Add some interactive effects
        document.querySelectorAll('.package-card').forEach(card => {
            card.addEventListener('click', function() {
                this.style.transform = 'scale(1.02)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 200);
            });
        });
    </script>
</body>
</html>
"""
    
    # Write to file
    if output_file is None:
        base_name = os.path.splitext(json_file_path)[0]
        output_file = f"{base_name}_report.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML report generated successfully: {output_file}")
    print(f"📊 Total packages: {len(packages)}")
    print(f"📁 Package types: {len(package_types)}")
    print(f"📜 Unique licenses: {len(license_counts)}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate beautiful HTML reports from SBOM JSON data")
    parser.add_argument("json_file", help="Path to the SBOM JSON file")
    parser.add_argument("-o", "--output", dest="output_file", help="Output HTML file path (default: <input>_report.html)")
    
    args = parser.parse_args()
    
    generate_html_report(args.json_file, args.output_file)

if __name__ == "__main__":
    main() 