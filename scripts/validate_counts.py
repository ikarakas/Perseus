#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Count validation and reconciliation script for maintaining data consistency
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_db_session
from database.repositories import CountValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_separator():
    """Print a separator line"""
    print("=" * 80)


def print_section(title: str):
    """Print a section header"""
    print_separator()
    print(f" {title}")
    print_separator()


def validate_and_report(validator: CountValidator, analysis_id: str = None):
    """Validate counts and print a detailed report"""
    if analysis_id:
        print_section(f"VALIDATING ANALYSIS: {analysis_id}")
        result = validator.validate_analysis_counts(analysis_id)
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return
        
        if result["has_discrepancies"]:
            print("⚠️  DISCREPANCIES FOUND:")
            for discrepancy in result["discrepancies"]:
                print(f"   • {discrepancy}")
            
            print("\n📊 ACTUAL COUNTS:")
            for key, value in result["actual_counts"].items():
                print(f"   • {key}: {value}")
            
            print("\n💾 STORED COUNTS:")
            for key, value in result["stored_counts"].items():
                print(f"   • {key}: {value}")
        else:
            print("✅ No discrepancies found")
    else:
        print_section("VALIDATING ALL ANALYSES")
        result = validator.validate_all_analysis_counts()
        
        print(f"📊 Total analyses checked: {result['total_analyses']}")
        print(f"⚠️  Analyses with discrepancies: {result['analyses_with_discrepancies']}")
        print(f"🔧 Total discrepancies found: {result['total_discrepancies']}")
        
        if result['analyses_with_discrepancies'] > 0:
            print("\n📋 DETAILED RESULTS:")
            for analysis_result in result['results']:
                if analysis_result['has_discrepancies']:
                    print(f"   • {analysis_result['analysis_id']}: {len(analysis_result['discrepancies'])} discrepancies")


def fix_counts(validator: CountValidator, analysis_id: str = None):
    """Fix count discrepancies"""
    if analysis_id:
        print_section(f"FIXING ANALYSIS: {analysis_id}")
        result = validator.fix_analysis_counts(analysis_id)
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return
        
        if "fixed" in result.get("message", ""):
            print("✅ Counts fixed successfully")
            print("📊 Fixed counts:")
            for key, value in result["fixed_counts"].items():
                print(f"   • {key}: {value}")
        else:
            print(f"ℹ️  {result['message']}")
    else:
        print_section("FIXING ALL ANALYSES")
        result = validator.fix_all_analysis_counts()
        
        print(f"✅ {result['message']}")
        print(f"📊 Total analyses: {result['total_analyses']}")
        print(f"🔧 Analyses fixed: {result['analyses_fixed']}")
        print(f"⚠️  Total discrepancies found: {result['total_discrepancies_found']}")


def cleanup_orphans(validator: CountValidator):
    """Clean up orphan vulnerabilities"""
    print_section("CLEANING UP ORPHAN VULNERABILITIES")
    result = validator.cleanup_orphan_vulnerabilities()
    
    print(f"✅ {result['message']}")
    print(f"🗑️  Orphan vulnerabilities removed: {result['orphan_vulnerabilities_removed']}")


def validate_component_counts(validator: CountValidator):
    """Validate component vulnerability counts"""
    print_section("VALIDATING COMPONENT VULNERABILITY COUNTS")
    result = validator.validate_component_vulnerability_relationships()
    
    print(f"📊 Total components checked: {result['total_components_checked']}")
    print(f"⚠️  Inconsistent components: {result['inconsistent_components']}")
    
    if result['inconsistent_components'] > 0:
        print("\n📋 INCONSISTENCIES:")
        for inconsistency in result['inconsistencies'][:10]:  # Show first 10
            print(f"   • {inconsistency['component_name']} (Analysis: {inconsistency['analysis_id']})")
            print(f"     Stored: {inconsistency['stored_count']}, Actual: {inconsistency['actual_count']}")
        
        if len(result['inconsistencies']) > 10:
            print(f"   ... and {len(result['inconsistencies']) - 10} more")


def fix_component_counts(validator: CountValidator):
    """Fix component vulnerability counts"""
    print_section("FIXING COMPONENT VULNERABILITY COUNTS")
    result = validator.fix_component_vulnerability_counts()
    
    print(f"✅ {result['message']}")
    print(f"🔧 Components fixed: {result['components_fixed']}")
    print(f"⚠️  Total inconsistencies found: {result['total_inconsistencies_found']}")


def show_statistics(validator: CountValidator):
    """Show comprehensive statistics"""
    print_section("COMPREHENSIVE COUNT STATISTICS")
    stats = validator.get_count_statistics()
    
    print("📊 ANALYSIS STATISTICS:")
    print(f"   • Total analyses: {stats['analyses']['total']}")
    print(f"   • Completed analyses: {stats['analyses']['completed']}")
    
    print("\n📦 COMPONENT STATISTICS:")
    print(f"   • Total components: {stats['components']['total']}")
    print(f"   • Components with vulnerabilities: {stats['components']['with_vulnerabilities']}")
    
    print("\n🚨 VULNERABILITY STATISTICS:")
    print(f"   • Total vulnerabilities: {stats['vulnerabilities']['total']}")
    print(f"   • Active vulnerabilities: {stats['vulnerabilities']['active']}")
    print(f"   • Orphan vulnerabilities: {stats['vulnerabilities']['orphan']}")
    
    print("\n🔍 DATA QUALITY:")
    print(f"   • Orphan vulnerability rate: {stats['data_quality']['orphan_vulnerability_rate']:.2f}%")


def main():
    """Main function"""
    print("🔧 SBOM Platform Count Validation and Reconciliation Tool")
    print(f"📅 Started at: {datetime.utcnow()}")
    
    try:
        # Get database session
        db_session = next(get_db_session())
        validator = CountValidator(db_session)
        
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description="Count validation and reconciliation tool")
        parser.add_argument("--action", choices=["validate", "fix", "cleanup", "stats", "validate-components", "fix-components"], 
                          default="validate", help="Action to perform")
        parser.add_argument("--analysis-id", help="Specific analysis ID to validate/fix")
        parser.add_argument("--all", action="store_true", help="Perform action on all analyses")
        
        args = parser.parse_args()
        
        if args.action == "validate":
            if args.analysis_id:
                validate_and_report(validator, args.analysis_id)
            elif args.all:
                validate_and_report(validator)
            else:
                print("❌ Please specify --analysis-id or --all")
        
        elif args.action == "fix":
            if args.analysis_id:
                fix_counts(validator, args.analysis_id)
            elif args.all:
                fix_counts(validator)
            else:
                print("❌ Please specify --analysis-id or --all")
        
        elif args.action == "cleanup":
            cleanup_orphans(validator)
        
        elif args.action == "stats":
            show_statistics(validator)
        
        elif args.action == "validate-components":
            validate_component_counts(validator)
        
        elif args.action == "fix-components":
            fix_component_counts(validator)
        
        print_separator()
        print("✅ Operation completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to perform count validation: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if 'db_session' in locals():
            db_session.close()


if __name__ == "__main__":
    main() 