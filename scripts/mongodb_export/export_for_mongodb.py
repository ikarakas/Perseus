#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Export Perseus database optimized for MongoDB import with embedded documents
"""

import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from src.database.connection import get_db, get_engine
from src.database.models import (
    Analysis, Component, Vulnerability, License, SBOM, 
    VulnerabilityScan, Agent, TelemetryData, Build
)


class MongoDBEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB-compatible format"""
    def default(self, obj):
        if isinstance(obj, datetime):
            # MongoDB-friendly date format
            return {"$date": obj.isoformat() + "Z"}
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def transform_for_mongodb(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform data to be MongoDB-friendly"""
    # Convert UUID fields to _id for MongoDB
    if 'id' in data:
        data['_id'] = data.pop('id')
    
    # Handle PostgreSQL-specific fields
    for key, value in list(data.items()):
        # Convert None to null is handled by JSON encoder
        # Remove any SQLAlchemy internal fields
        if key.startswith('_'):
            del data[key]
    
    return data


def export_analyses_embedded(session: Session) -> List[Dict[str, Any]]:
    """Export analyses with embedded related data"""
    print("Exporting analyses with embedded documents...")
    analyses = session.query(Analysis).all()
    result = []
    
    for analysis in analyses:
        data = {
            "_id": str(analysis.id),
            "analysis_id": analysis.analysis_id,
            "status": analysis.status.value if analysis.status else None,
            "analysis_type": analysis.analysis_type,
            "language": analysis.language,
            "location": analysis.location,
            "started_at": analysis.started_at,
            "completed_at": analysis.completed_at,
            "duration_seconds": analysis.duration_seconds,
            "component_count": analysis.component_count,
            "vulnerability_count": analysis.vulnerability_count,
            "critical_vulnerability_count": analysis.critical_vulnerability_count,
            "high_vulnerability_count": analysis.high_vulnerability_count,
            "analysis_metadata": analysis.analysis_metadata or {},
            "errors": analysis.errors or [],
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
            
            # Embed related data
            "components": [
                {
                    "_id": str(comp.id),
                    "name": comp.name,
                    "version": comp.version,
                    "purl": comp.purl,
                    "type": comp.type.value if comp.type else None,
                    "vulnerability_count": comp.vulnerability_count,
                    "critical_vulnerabilities": comp.critical_vulnerabilities,
                    "high_vulnerabilities": comp.high_vulnerabilities,
                    
                    # Embed vulnerabilities summary
                    "vulnerabilities": [
                        {
                            "vulnerability_id": vuln.vulnerability_id,
                            "severity": vuln.severity.value if vuln.severity else None,
                            "cvss_score": vuln.cvss_score,
                            "title": vuln.title
                        }
                        for vuln in comp.vulnerabilities
                    ],
                    
                    # Embed licenses
                    "licenses": [
                        {
                            "spdx_id": lic.spdx_id,
                            "name": lic.name,
                            "is_osi_approved": lic.is_osi_approved
                        }
                        for lic in comp.licenses
                    ]
                }
                for comp in analysis.components
            ],
            
            # Embed SBOM if exists
            "sboms": [
                {
                    "_id": str(sbom.id),
                    "sbom_id": sbom.sbom_id,
                    "format": sbom.format,
                    "spec_version": sbom.spec_version,
                    "component_count": sbom.component_count,
                    "created_at": sbom.created_at
                }
                for sbom in analysis.sboms
            ],
            
            # Embed vulnerability scans
            "vulnerability_scans": [
                {
                    "_id": str(scan.id),
                    "scan_id": scan.scan_id,
                    "scanner": scan.scanner.value if scan.scanner else None,
                    "total_vulnerabilities": scan.total_vulnerabilities,
                    "critical_count": scan.critical_count,
                    "high_count": scan.high_count,
                    "completed_at": scan.completed_at
                }
                for scan in analysis.vulnerability_scans
            ]
        }
        
        # Add build info if exists
        if analysis.build:
            data["build"] = {
                "_id": str(analysis.build.id),
                "build_id": analysis.build.build_id,
                "project_name": analysis.build.project_name,
                "branch": analysis.build.branch,
                "version": analysis.build.version,
                "ci_platform": analysis.build.ci_platform
            }
        
        result.append(data)
    
    return result


def export_standalone_collections(session: Session) -> Dict[str, List[Dict[str, Any]]]:
    """Export collections that should remain standalone"""
    print("Exporting standalone collections...")
    
    # Full vulnerability details
    vulnerabilities = []
    for vuln in session.query(Vulnerability).all():
        vulnerabilities.append(transform_for_mongodb({
            "id": vuln.id,
            "vulnerability_id": vuln.vulnerability_id,
            "source": vuln.source,
            "title": vuln.title,
            "description": vuln.description,
            "severity": vuln.severity.value if vuln.severity else None,
            "cvss_score": vuln.cvss_score,
            "cvss_vector": vuln.cvss_vector,
            "epss_score": vuln.epss_score,
            "published_date": vuln.published_date,
            "modified_date": vuln.modified_date,
            "references": vuln.references or [],
            "cwe_ids": vuln.cwe_ids or [],
            "affected_versions": vuln.affected_versions or [],
            "fixed_versions": vuln.fixed_versions or [],
            "vulnerability_metadata": vuln.vulnerability_metadata or {},
            "created_at": vuln.created_at,
            "updated_at": vuln.updated_at
        }))
    
    # Full license details
    licenses = []
    for lic in session.query(License).all():
        licenses.append(transform_for_mongodb({
            "id": lic.id,
            "spdx_id": lic.spdx_id,
            "name": lic.name,
            "is_osi_approved": lic.is_osi_approved,
            "is_fsf_libre": lic.is_fsf_libre,
            "is_deprecated": lic.is_deprecated,
            "reference_url": lic.reference_url,
            "details_url": lic.details_url,
            "license_text": lic.license_text,
            "license_metadata": lic.license_metadata or {},
            "created_at": lic.created_at,
            "updated_at": lic.updated_at
        }))
    
    # Agents with telemetry
    agents = []
    for agent in session.query(Agent).all():
        agent_data = transform_for_mongodb({
            "id": agent.id,
            "agent_id": agent.agent_id,
            "hostname": agent.hostname,
            "ip_address": agent.ip_address,
            "platform": agent.platform,
            "architecture": agent.architecture,
            "is_active": agent.is_active,
            "last_heartbeat": agent.last_heartbeat,
            "registration_date": agent.registration_date,
            "capabilities": agent.capabilities or [],
            "agent_metadata": agent.agent_metadata or {},
            "created_at": agent.created_at,
            "updated_at": agent.updated_at
        })
        
        # Include recent telemetry data (last 100 entries)
        agent_data["recent_telemetry"] = [
            {
                "message_type": t.message_type,
                "timestamp": t.timestamp,
                "data": t.data
            }
            for t in agent.telemetry_data[-100:]
        ]
        
        agents.append(agent_data)
    
    return {
        "vulnerabilities": vulnerabilities,
        "licenses": licenses,
        "agents": agents
    }


def export_for_mongodb(output_dir: str, single_line: bool = True):
    """Export database in MongoDB-optimized format"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"Starting MongoDB-optimized export to {output_path}...")
    
    engine = get_engine()
    with Session(engine) as session:
        # Export main collection with embedded documents
        analyses = export_analyses_embedded(session)
        
        # Export standalone collections
        standalone = export_standalone_collections(session)
        
        # Write collections to separate files
        # Main analyses collection with embedded data
        with open(output_path / "analyses.json", 'w') as f:
            if single_line:
                # Write one document per line (MongoDB import format)
                for doc in analyses:
                    f.write(json.dumps(doc, cls=MongoDBEncoder) + '\n')
            else:
                # Write as JSON array with pretty printing
                json.dump(analyses, f, cls=MongoDBEncoder, indent=2)
        print(f"Exported {len(analyses)} analyses to analyses.json")
        
        # Standalone collections
        for collection_name, data in standalone.items():
            with open(output_path / f"{collection_name}.json", 'w') as f:
                if single_line:
                    # Write one document per line (MongoDB import format)
                    for doc in data:
                        f.write(json.dumps(doc, cls=MongoDBEncoder) + '\n')
                else:
                    # Write as JSON array with pretty printing
                    json.dump(data, f, cls=MongoDBEncoder, indent=2)
            print(f"Exported {len(data)} documents to {collection_name}.json")
        
        # Create import script
        import_mode = "" if single_line else " --jsonArray"
        format_desc = 'line-delimited JSON' if single_line else 'JSON arrays'
        import_script = f"""#!/bin/bash
# MongoDB import script for Perseus SBOM data

DB_NAME=${{1:-perseus_sbom}}

echo "Importing Perseus data into MongoDB database: $DB_NAME"
echo "Format: {format_desc}"

# Import collections
mongoimport --db $DB_NAME --collection analyses --file analyses.json{import_mode}
mongoimport --db $DB_NAME --collection vulnerabilities --file vulnerabilities.json{import_mode}
mongoimport --db $DB_NAME --collection licenses --file licenses.json{import_mode}
mongoimport --db $DB_NAME --collection agents --file agents.json{import_mode}

echo "Import complete!"

# Create indexes
mongo $DB_NAME --eval '
db.analyses.createIndex({{ "analysis_id": 1 }});
db.analyses.createIndex({{ "created_at": -1 }});
db.analyses.createIndex({{ "components.name": 1 }});
db.vulnerabilities.createIndex({{ "vulnerability_id": 1 }});
db.vulnerabilities.createIndex({{ "severity": 1 }});
db.licenses.createIndex({{ "spdx_id": 1 }});
db.agents.createIndex({{ "agent_id": 1 }});
'

echo "Indexes created!"
"""
        
        with open(output_path / "import_to_mongodb.sh", 'w') as f:
            f.write(import_script)
        
        # Make script executable
        import_script_path = output_path / "import_to_mongodb.sh"
        import_script_path.chmod(0o755)
        
        print(f"\nExport completed!")
        print(f"Files created in {output_path}:")
        print(f"  - analyses.json (main collection with embedded documents)")
        print(f"  - vulnerabilities.json (reference collection)")
        print(f"  - licenses.json (reference collection)")
        print(f"  - agents.json (with recent telemetry)")
        print(f"  - import_to_mongodb.sh (import script)")
        print(f"\nTo import into MongoDB, run:")
        print(f"  cd {output_path} && ./import_to_mongodb.sh [database_name]")


def main():
    parser = argparse.ArgumentParser(description="Export Perseus database for MongoDB")
    parser.add_argument(
        "-o", "--output-dir",
        default="mongodb_export",
        help="Output directory for JSON files (default: mongodb_export)"
    )
    parser.add_argument(
        "-a", "--array",
        action="store_true",
        help="Export as JSON arrays with pretty printing instead of line-delimited JSON"
    )
    
    args = parser.parse_args()
    
    try:
        # single_line is True by default, False when --array is used
        export_for_mongodb(args.output_dir, single_line=not args.array)
    except Exception as e:
        print(f"Error during export: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()