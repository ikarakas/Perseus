#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Export complete Perseus database to JSON for MongoDB import
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
    VulnerabilityScan, Agent, TelemetryData, Build,
    component_vulnerabilities, component_licenses
)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def serialize_model(instance) -> Dict[str, Any]:
    """Convert SQLAlchemy model instance to dictionary"""
    data = {}
    
    # Get all columns
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        
        # Handle enums
        if hasattr(value, 'value'):
            value = value.value
            
        data[column.name] = value
    
    return data


def export_analyses(session: Session) -> List[Dict[str, Any]]:
    """Export all analyses"""
    print("Exporting analyses...")
    analyses = session.query(Analysis).all()
    return [serialize_model(analysis) for analysis in analyses]


def export_components(session: Session) -> List[Dict[str, Any]]:
    """Export all components with their relationships"""
    print("Exporting components...")
    components = session.query(Component).all()
    component_list = []
    
    for component in components:
        data = serialize_model(component)
        
        # Add vulnerability IDs
        data['vulnerability_ids'] = [str(v.id) for v in component.vulnerabilities]
        
        # Add license IDs
        data['license_ids'] = [str(l.id) for l in component.licenses]
        
        component_list.append(data)
    
    return component_list


def export_vulnerabilities(session: Session) -> List[Dict[str, Any]]:
    """Export all vulnerabilities"""
    print("Exporting vulnerabilities...")
    vulnerabilities = session.query(Vulnerability).all()
    return [serialize_model(vuln) for vuln in vulnerabilities]


def export_licenses(session: Session) -> List[Dict[str, Any]]:
    """Export all licenses"""
    print("Exporting licenses...")
    licenses = session.query(License).all()
    return [serialize_model(license) for license in licenses]


def export_sboms(session: Session) -> List[Dict[str, Any]]:
    """Export all SBOMs"""
    print("Exporting SBOMs...")
    sboms = session.query(SBOM).all()
    return [serialize_model(sbom) for sbom in sboms]


def export_vulnerability_scans(session: Session) -> List[Dict[str, Any]]:
    """Export all vulnerability scans"""
    print("Exporting vulnerability scans...")
    scans = session.query(VulnerabilityScan).all()
    return [serialize_model(scan) for scan in scans]


def export_agents(session: Session) -> List[Dict[str, Any]]:
    """Export all agents"""
    print("Exporting agents...")
    agents = session.query(Agent).all()
    return [serialize_model(agent) for agent in agents]


def export_telemetry_data(session: Session) -> List[Dict[str, Any]]:
    """Export all telemetry data"""
    print("Exporting telemetry data...")
    telemetry = session.query(TelemetryData).all()
    return [serialize_model(t) for t in telemetry]


def export_builds(session: Session) -> List[Dict[str, Any]]:
    """Export all builds"""
    print("Exporting builds...")
    builds = session.query(Build).all()
    return [serialize_model(build) for build in builds]


def export_relationships(session: Session) -> Dict[str, List[Dict[str, str]]]:
    """Export many-to-many relationships"""
    print("Exporting relationships...")
    
    # Component-Vulnerability relationships
    comp_vuln_query = session.execute(
        f"SELECT component_id, vulnerability_id FROM {component_vulnerabilities.name}"
    )
    comp_vuln_rels = [
        {"component_id": str(row[0]), "vulnerability_id": str(row[1])}
        for row in comp_vuln_query
    ]
    
    # Component-License relationships
    comp_lic_query = session.execute(
        f"SELECT component_id, license_id FROM {component_licenses.name}"
    )
    comp_lic_rels = [
        {"component_id": str(row[0]), "license_id": str(row[1])}
        for row in comp_lic_query
    ]
    
    return {
        "component_vulnerabilities": comp_vuln_rels,
        "component_licenses": comp_lic_rels
    }


def export_database(output_file: str, pretty: bool = False):
    """Export entire database to JSON"""
    print(f"Starting database export to {output_file}...")
    
    engine = get_engine()
    with Session(engine) as session:
        export_data = {
            "export_metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "version": "1.0",
                "source": "perseus_sbom"
            },
            "data": {
                "analyses": export_analyses(session),
                "components": export_components(session),
                "vulnerabilities": export_vulnerabilities(session),
                "licenses": export_licenses(session),
                "sboms": export_sboms(session),
                "vulnerability_scans": export_vulnerability_scans(session),
                "agents": export_agents(session),
                "telemetry_data": export_telemetry_data(session),
                "builds": export_builds(session),
            },
            "relationships": export_relationships(session)
        }
        
        # Add statistics
        export_data["statistics"] = {
            "total_analyses": len(export_data["data"]["analyses"]),
            "total_components": len(export_data["data"]["components"]),
            "total_vulnerabilities": len(export_data["data"]["vulnerabilities"]),
            "total_licenses": len(export_data["data"]["licenses"]),
            "total_sboms": len(export_data["data"]["sboms"]),
            "total_scans": len(export_data["data"]["vulnerability_scans"]),
            "total_agents": len(export_data["data"]["agents"]),
            "total_telemetry_records": len(export_data["data"]["telemetry_data"]),
            "total_builds": len(export_data["data"]["builds"])
        }
    
    # Write to file
    with open(output_file, 'w') as f:
        if pretty:
            json.dump(export_data, f, cls=DateTimeEncoder, indent=2)
        else:
            json.dump(export_data, f, cls=DateTimeEncoder)
    
    print(f"Export completed successfully!")
    print(f"Statistics:")
    for key, value in export_data["statistics"].items():
        print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(description="Export Perseus database to JSON")
    parser.add_argument(
        "-o", "--output",
        default="perseus_database_export.json",
        help="Output JSON file (default: perseus_database_export.json)"
    )
    parser.add_argument(
        "-p", "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    args = parser.parse_args()
    
    try:
        export_database(args.output, args.pretty)
    except Exception as e:
        print(f"Error during export: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()