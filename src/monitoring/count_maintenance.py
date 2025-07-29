# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Background count maintenance and validation for data consistency
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from ..database import get_db_session
from ..database.repositories import CountValidator

logger = logging.getLogger(__name__)


class CountMaintenanceService:
    """Background service for count validation and maintenance"""
    
    def __init__(self, validation_interval_hours: int = 24, cleanup_interval_hours: int = 168):
        """
        Initialize the count maintenance service
        
        Args:
            validation_interval_hours: How often to validate counts (default: 24 hours)
            cleanup_interval_hours: How often to cleanup orphans (default: 168 hours = 1 week)
        """
        self.validation_interval = validation_interval_hours * 3600  # Convert to seconds
        self.cleanup_interval = cleanup_interval_hours * 3600
        self.running = False
        self.thread = None
        self.last_validation = None
        self.last_cleanup = None
        self.validation_results = []
        self.cleanup_results = []
    
    def start(self):
        """Start the background maintenance service"""
        if self.running:
            logger.warning("Count maintenance service is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.thread.start()
        logger.info("Count maintenance service started")
    
    def stop(self):
        """Stop the background maintenance service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Count maintenance service stopped")
    
    def _maintenance_loop(self):
        """Main maintenance loop"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time for validation
                if (self.last_validation is None or 
                    current_time - self.last_validation >= self.validation_interval):
                    self._perform_validation()
                    self.last_validation = current_time
                
                # Check if it's time for cleanup
                if (self.last_cleanup is None or 
                    current_time - self.last_cleanup >= self.cleanup_interval):
                    self._perform_cleanup()
                    self.last_cleanup = current_time
                
                # Sleep for a short interval
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in count maintenance loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _perform_validation(self):
        """Perform count validation"""
        try:
            logger.info("Starting scheduled count validation")
            db_session = next(get_db_session())
            validator = CountValidator(db_session)
            
            # Validate all analyses
            validation_result = validator.validate_all_analysis_counts()
            
            # Store result
            self.validation_results.append({
                'timestamp': datetime.utcnow(),
                'result': validation_result
            })
            
            # Keep only last 10 results
            if len(self.validation_results) > 10:
                self.validation_results = self.validation_results[-10:]
            
            # Log results
            if validation_result['analyses_with_discrepancies'] > 0:
                logger.warning(
                    f"Count validation found {validation_result['analyses_with_discrepancies']} "
                    f"analyses with {validation_result['total_discrepancies']} discrepancies"
                )
                
                # Auto-fix if discrepancies are minor (less than 5% of analyses)
                total_analyses = validation_result['total_analyses']
                if (validation_result['analyses_with_discrepancies'] / total_analyses < 0.05 
                    and total_analyses > 0):
                    logger.info("Auto-fixing minor count discrepancies")
                    fix_result = validator.fix_all_analysis_counts()
                    logger.info(f"Auto-fixed {fix_result['analyses_fixed']} analyses")
            else:
                logger.info("Count validation completed - no discrepancies found")
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"Failed to perform count validation: {e}")
    
    def _perform_cleanup(self):
        """Perform orphan cleanup"""
        try:
            logger.info("Starting scheduled orphan cleanup")
            db_session = next(get_db_session())
            validator = CountValidator(db_session)
            
            # Clean up orphan vulnerabilities
            cleanup_result = validator.cleanup_orphan_vulnerabilities()
            
            # Store result
            self.cleanup_results.append({
                'timestamp': datetime.utcnow(),
                'result': cleanup_result
            })
            
            # Keep only last 10 results
            if len(self.cleanup_results) > 10:
                self.cleanup_results = self.cleanup_results[-10:]
            
            # Log results
            if cleanup_result['orphan_vulnerabilities_removed'] > 0:
                logger.info(f"Cleanup removed {cleanup_result['orphan_vulnerabilities_removed']} orphan vulnerabilities")
            else:
                logger.info("Cleanup completed - no orphan vulnerabilities found")
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"Failed to perform orphan cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the maintenance service"""
        return {
            'running': self.running,
            'validation_interval_hours': self.validation_interval / 3600,
            'cleanup_interval_hours': self.cleanup_interval / 3600,
            'last_validation': self.last_validation.isoformat() if self.last_validation else None,
            'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None,
            'validation_results_count': len(self.validation_results),
            'cleanup_results_count': len(self.cleanup_results),
            'recent_validation_results': [
                {
                    'timestamp': result['timestamp'].isoformat(),
                    'analyses_with_discrepancies': result['result']['analyses_with_discrepancies'],
                    'total_discrepancies': result['result']['total_discrepancies']
                }
                for result in self.validation_results[-5:]  # Last 5 results
            ],
            'recent_cleanup_results': [
                {
                    'timestamp': result['timestamp'].isoformat(),
                    'orphan_vulnerabilities_removed': result['result']['orphan_vulnerabilities_removed']
                }
                for result in self.cleanup_results[-5:]  # Last 5 results
            ]
        }
    
    def trigger_validation(self) -> Dict[str, Any]:
        """Manually trigger count validation"""
        try:
            logger.info("Manual count validation triggered")
            db_session = next(get_db_session())
            validator = CountValidator(db_session)
            
            validation_result = validator.validate_all_analysis_counts()
            fix_result = None
            
            if validation_result['analyses_with_discrepancies'] > 0:
                fix_result = validator.fix_all_analysis_counts()
            
            db_session.close()
            
            return {
                'validation': validation_result,
                'fix': fix_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger manual validation: {e}")
            raise
    
    def trigger_cleanup(self) -> Dict[str, Any]:
        """Manually trigger orphan cleanup"""
        try:
            logger.info("Manual orphan cleanup triggered")
            db_session = next(get_db_session())
            validator = CountValidator(db_session)
            
            cleanup_result = validator.cleanup_orphan_vulnerabilities()
            
            db_session.close()
            
            return {
                'cleanup': cleanup_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger manual cleanup: {e}")
            raise


# Global instance
count_maintenance_service = CountMaintenanceService()


def start_count_maintenance():
    """Start the count maintenance service"""
    count_maintenance_service.start()


def stop_count_maintenance():
    """Stop the count maintenance service"""
    count_maintenance_service.stop()


def get_count_maintenance_status() -> Dict[str, Any]:
    """Get the status of the count maintenance service"""
    return count_maintenance_service.get_status()


def trigger_count_validation() -> Dict[str, Any]:
    """Manually trigger count validation"""
    return count_maintenance_service.trigger_validation()


def trigger_count_cleanup() -> Dict[str, Any]:
    """Manually trigger orphan cleanup"""
    return count_maintenance_service.trigger_cleanup() 