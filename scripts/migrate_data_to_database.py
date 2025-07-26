#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Migrate existing file-based data to PostgreSQL database
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import (
    init_database, get_db, test_connection, create_tables,
    Analysis, Component, SBOM, Vulnerability, License, Agent, TelemetryData,
    AnalysisStatus, ComponentType, VulnerabilitySeverity
)
from src.database.repositories import (
    AnalysisRepository, ComponentRepository, SBOMRepository, 
    VulnerabilityRepository
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Migrate file-based data to database"""
    
    def __init__(self, data_dir: str = "data", telemetry_dir: str = "telemetry_data"):
        self.data_dir = Path(data_dir)
        self.telemetry_dir = Path(telemetry_dir)
        self.results_dir = self.data_dir / "results"
        self.sboms_dir = self.data_dir / "sboms"
        
    def migrate_all(self):
        """Migrate all data to database"""
        logger.info("Starting data migration to database...")
        
        # Initialize database
        init_database()
        if not test_connection():
            logger.error("Database connection failed!")
            return False
        
        create_tables()
        logger.info("Database tables ready")
        
        # Migrate data
        with get_db() as db:
            try:
                # Migrate analysis results and components
                self.migrate_analysis_results(db)
                
                # Migrate SBOMs
                self.migrate_sboms(db)
                
                # Migrate telemetry data
                self.migrate_telemetry_data(db)
                
                db.commit()
                logger.info("Data migration completed successfully!")
                return True
                
            except Exception as e:
                logger.error(f"Migration failed: {e}")
                db.rollback()
                return False
    
    def migrate_analysis_results(self, db):
        """Migrate analysis results from JSON files"""
        logger.info("Migrating analysis results...")
        
        analysis_repo = AnalysisRepository(db)
        component_repo = ComponentRepository(db)
        
        if not self.results_dir.exists():
            logger.warning(f"Results directory {self.results_dir} not found")
            return
        
        migrated_count = 0
        
        for result_file in self.results_dir.glob("*.json"):
            try:
                logger.info(f"Processing {result_file.name}")
                
                with open(result_file, 'r') as f:
                    data = json.load(f)
                
                # Check if analysis already exists
                existing = analysis_repo.get_by_analysis_id(data['analysis_id'])
                if existing:
                    logger.info(f"Analysis {data['analysis_id']} already exists, skipping")
                    continue
                
                # Create analysis record
                analysis_data = {
                    'analysis_id': data['analysis_id'],
                    'status': AnalysisStatus(data.get('status', 'completed')),
                    'analysis_type': data.get('metadata', {}).get('analyzer', 'unknown'),
                    'location': data.get('metadata', {}).get('location', ''),
                    'component_count': len(data.get('components', [])),
                    'metadata': data.get('metadata', {}),
                    'errors': data.get('errors', [])
                }
                
                # Set timestamps
                if 'metadata' in data and 'vulnerability_scan_date' in data['metadata']:
                    try:
                        analysis_data['completed_at'] = datetime.fromisoformat(
                            data['metadata']['vulnerability_scan_date'].replace('Z', '+00:00')
                        )
                    except:
                        pass
                
                analysis = analysis_repo.create(**analysis_data)
                logger.info(f"Created analysis: {analysis.analysis_id}")
                
                # Migrate components
                components_data = []
                vulnerability_counts = {'total': 0, 'critical': 0, 'high': 0}
                
                for comp_data in data.get('components', []):
                    component = {
                        'name': comp_data['name'],
                        'version': comp_data['version'],
                        'type': self._map_component_type(comp_data.get('type', 'library')),
                        'purl': comp_data.get('purl', ''),
                        'vulnerability_count': comp_data.get('vulnerability_count', 0),
                        'critical_vulnerabilities': comp_data.get('critical_vulnerabilities', 0),
                        'high_vulnerabilities': comp_data.get('high_vulnerabilities', 0),
                        'metadata': comp_data.get('metadata', {}),
                        'syft_metadata': comp_data.get('metadata', {}).get('syft_metadata', {}),
                        'analysis_id': analysis.id
                    }
                    
                    components_data.append(component)
                    
                    # Aggregate vulnerability counts
                    vulnerability_counts['total'] += component['vulnerability_count']
                    vulnerability_counts['critical'] += component['critical_vulnerabilities']
                    vulnerability_counts['high'] += component['high_vulnerabilities']
                
                # Bulk create components
                if components_data:
                    component_repo.bulk_create(components_data)
                    logger.info(f"Created {len(components_data)} components")
                
                # Update analysis with vulnerability counts
                analysis_repo.update(analysis.id, 
                    vulnerability_count=vulnerability_counts['total'],
                    critical_vulnerability_count=vulnerability_counts['critical'],
                    high_vulnerability_count=vulnerability_counts['high']
                )
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {result_file.name}: {e}")
                continue
        
        logger.info(f"Migrated {migrated_count} analysis results")
    
    def migrate_sboms(self, db):
        """Migrate SBOM files"""
        logger.info("Migrating SBOMs...")
        
        sbom_repo = SBOMRepository(db)
        analysis_repo = AnalysisRepository(db)
        
        if not self.sboms_dir.exists():
            logger.warning(f"SBOMs directory {self.sboms_dir} not found")
            return
        
        migrated_count = 0
        
        for sbom_file in self.sboms_dir.glob("*.json"):
            try:
                logger.info(f"Processing SBOM {sbom_file.name}")
                
                with open(sbom_file, 'r') as f:
                    sbom_content = json.load(f)
                
                # Extract SBOM metadata
                sbom_data = {
                    'sbom_id': sbom_file.stem,
                    'content': sbom_content
                }
                
                # Determine format
                if 'spdxVersion' in sbom_content:
                    sbom_data['format'] = 'spdx'
                    sbom_data['spec_version'] = sbom_content.get('spdxVersion')
                    sbom_data['name'] = sbom_content.get('name')
                    sbom_data['namespace'] = sbom_content.get('documentNamespace')
                    sbom_data['created_by'] = ', '.join(sbom_content.get('creationInfo', {}).get('creators', []))
                elif 'bomFormat' in sbom_content:
                    sbom_data['format'] = 'cyclonedx'
                    sbom_data['spec_version'] = sbom_content.get('specVersion')
                    sbom_data['name'] = sbom_content.get('metadata', {}).get('component', {}).get('name')
                else:
                    sbom_data['format'] = 'unknown'
                
                # Try to link to analysis (if filename matches pattern)
                analysis_id = None
                if sbom_file.name.startswith('SBOM-'):
                    # Try to find matching analysis by timestamp or other pattern
                    pass  # Could implement more sophisticated matching
                
                # For now, create SBOM without analysis link
                existing = sbom_repo.get_by_sbom_id(sbom_data['sbom_id'])
                if existing:
                    logger.info(f"SBOM {sbom_data['sbom_id']} already exists, skipping")
                    continue
                
                sbom = sbom_repo.create(**sbom_data)
                logger.info(f"Created SBOM: {sbom.sbom_id}")
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Error processing SBOM {sbom_file.name}: {e}")
                continue
        
        logger.info(f"Migrated {migrated_count} SBOMs")
    
    def migrate_telemetry_data(self, db):
        """Migrate telemetry data"""
        logger.info("Migrating telemetry data...")
        
        if not self.telemetry_dir.exists():
            logger.warning(f"Telemetry directory {self.telemetry_dir} not found")
            return
        
        # Migrate agents
        agents_dir = self.telemetry_dir / "agents"
        if agents_dir.exists():
            self._migrate_agents(db, agents_dir)
        
        # Migrate BOM data
        bom_dir = self.telemetry_dir / "bom"
        if bom_dir.exists():
            self._migrate_bom_data(db, bom_dir)
    
    def _migrate_agents(self, db, agents_dir):
        """Migrate agent registration data"""
        migrated_count = 0
        
        for agent_file in agents_dir.glob("*.json"):
            try:
                with open(agent_file, 'r') as f:
                    agent_data = json.load(f)
                
                # Check if agent already exists
                existing = db.query(Agent).filter(
                    Agent.agent_id == agent_data['agent_id']
                ).first()
                
                if existing:
                    continue
                
                agent = Agent(
                    agent_id=agent_data['agent_id'],
                    hostname=agent_data.get('metadata', {}).get('hostname', 'unknown'),
                    platform=agent_data.get('metadata', {}).get('platform', 'unknown'),
                    architecture=agent_data.get('metadata', {}).get('architecture', 'unknown'),
                    is_active=agent_data.get('status') == 'active',
                    registration_date=datetime.fromisoformat(
                        agent_data.get('registered_at', datetime.utcnow().isoformat())
                    ),
                    metadata=agent_data.get('metadata', {})
                )
                
                if 'last_seen' in agent_data:
                    agent.last_heartbeat = datetime.fromisoformat(agent_data['last_seen'])
                
                db.add(agent)
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Error migrating agent {agent_file.name}: {e}")
                continue
        
        logger.info(f"Migrated {migrated_count} agents")
    
    def _migrate_bom_data(self, db, bom_dir):
        """Migrate BOM telemetry data"""
        migrated_count = 0
        
        for bom_file in bom_dir.glob("*.json"):
            try:
                with open(bom_file, 'r') as f:
                    bom_data = json.load(f)
                
                # Find corresponding agent
                agent = db.query(Agent).filter(
                    Agent.agent_id == bom_data.get('agent_id', '')
                ).first()
                
                if not agent:
                    logger.warning(f"Agent not found for BOM data: {bom_data.get('agent_id')}")
                    continue
                
                telemetry = TelemetryData(
                    message_type='bom_data',
                    timestamp=datetime.fromisoformat(
                        bom_data.get('timestamp', datetime.utcnow().isoformat())
                    ),
                    data=bom_data,
                    agent_id=agent.id
                )
                
                db.add(telemetry)
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Error migrating BOM data {bom_file.name}: {e}")
                continue
        
        logger.info(f"Migrated {migrated_count} BOM telemetry records")
    
    def _map_component_type(self, type_str: str) -> ComponentType:
        """Map string component type to enum"""
        type_mapping = {
            'java-archive': ComponentType.LIBRARY,
            'library': ComponentType.LIBRARY,
            'application': ComponentType.APPLICATION,
            'container': ComponentType.CONTAINER,
            'operating-system': ComponentType.OPERATING_SYSTEM,
            'device': ComponentType.DEVICE,
            'firmware': ComponentType.FIRMWARE,
            'file': ComponentType.FILE,
            'framework': ComponentType.FRAMEWORK
        }
        
        return type_mapping.get(type_str.lower(), ComponentType.LIBRARY)


def main():
    """Main migration function"""
    migrator = DataMigrator()
    
    logger.info("Perseus Data Migration Tool")
    logger.info("=" * 40)
    
    success = migrator.migrate_all()
    
    if success:
        logger.info("Migration completed successfully!")
        return 0
    else:
        logger.error("Migration failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())