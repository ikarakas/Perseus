#!/usr/bin/env python3
"""
Complete database wipe script for Perseus
Removes ALL data from all tables
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from src.database.connection import get_db
from src.database.models import Analysis, Component, Vulnerability, SBOM
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_database_wipe():
    """Completely wipe all tables in proper order to handle foreign key constraints"""
    
    with get_db() as session:
        try:
            # Get initial counts
            logger.info("Getting initial counts...")
            initial_counts = {
                'analyses': session.query(func.count(Analysis.id)).scalar(),
                'components': session.query(func.count(Component.id)).scalar(),
                'vulnerabilities': session.query(func.count(Vulnerability.id)).scalar(),
                'sboms': session.query(func.count(SBOM.id)).scalar()
            }
            
            print("Initial database status:")
            for table, count in initial_counts.items():
                print(f"  {table}: {count}")
            
            if sum(initial_counts.values()) == 0:
                print("✅ Database is already empty")
                return True
            
            print("\n🗑️  Starting complete database wipe...")
            
            # Delete in proper order to respect foreign key constraints
            
            # 1. Delete SBOMs first (they reference analyses)
            logger.info("Deleting SBOMs...")
            sbom_deleted = session.query(SBOM).delete()
            session.commit()
            print(f"  ✓ Deleted {sbom_deleted} SBOMs")
            
            # 2. Delete junction tables (they should cascade automatically, but let's be explicit)
            logger.info("Deleting relationship mappings...")
            try:
                session.execute(text("DELETE FROM component_vulnerabilities"))
                session.commit()
                print("  ✓ Deleted component-vulnerability relationships")
            except Exception as e:
                logger.warning(f"Component-vulnerability deletion: {e}")
                session.rollback()
            
            # 3. Delete analyses
            logger.info("Deleting analyses...")
            analysis_deleted = session.query(Analysis).delete()
            session.commit()
            print(f"  ✓ Deleted {analysis_deleted} analyses")
            
            # 4. Delete components
            logger.info("Deleting components...")
            component_deleted = session.query(Component).delete()
            session.commit()
            print(f"  ✓ Deleted {component_deleted} components")
            
            # 5. Delete vulnerabilities
            logger.info("Deleting vulnerabilities...")
            vuln_deleted = session.query(Vulnerability).delete()
            session.commit()
            print(f"  ✓ Deleted {vuln_deleted} vulnerabilities")
            
            # Verify everything is clean
            logger.info("Verifying wipe completion...")
            final_counts = {
                'analyses': session.query(func.count(Analysis.id)).scalar(),
                'components': session.query(func.count(Component.id)).scalar(),
                'vulnerabilities': session.query(func.count(Vulnerability.id)).scalar(),
                'sboms': session.query(func.count(SBOM.id)).scalar()
            }
            
            print("\nFinal database status:")
            for table, count in final_counts.items():
                print(f"  {table}: {count}")
            
            if sum(final_counts.values()) == 0:
                print("✅ Database wipe completed successfully - all tables clean!")
                return True
            else:
                print("❌ Database wipe incomplete - some data remains")
                return False
                
        except Exception as e:
            logger.error(f"Error during database wipe: {e}")
            session.rollback()
            print(f"❌ Database wipe failed: {e}")
            return False

if __name__ == "__main__":
    success = complete_database_wipe()
    exit(0 if success else 1)