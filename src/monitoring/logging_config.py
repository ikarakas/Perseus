# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Centralized logging configuration for SBOM platform
"""

import os
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any, Optional

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, service_name: str = "sbom-platform"):
        self.service_name = service_name
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'analysis_id'):
            log_entry["analysis_id"] = record.analysis_id
        if hasattr(record, 'sbom_id'):
            log_entry["sbom_id"] = record.sbom_id
        if hasattr(record, 'client_ip'):
            log_entry["client_ip"] = record.client_ip
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
        if hasattr(record, 'duration'):
            log_entry["duration"] = record.duration
        
        return json.dumps(log_entry, default=str)


class LoggingConfig:
    """Centralized logging configuration"""
    
    def __init__(self, service_name: str = "sbom-platform", log_level: str = "INFO"):
        self.service_name = service_name
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = "/app/data/logs"
        self._setup_directories()
    
    def _setup_directories(self):
        """Create log directories"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def setup_logging(self):
        """Configure logging for the entire application"""
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        # File handler for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, f"{self.service_name}.log"),
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=10
        )
        file_handler.setLevel(self.log_level)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, f"{self.service_name}-error.log"),
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Set formatters
        structured_formatter = StructuredFormatter(self.service_name)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(structured_formatter)
        error_handler.setFormatter(structured_formatter)
        
        # Add handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        
        # Setup specific loggers
        self._setup_specific_loggers()
        
        logging.info(f"Logging configured for {self.service_name}")
    
    def _setup_specific_loggers(self):
        """Setup loggers for specific components"""
        # Analysis logger
        analysis_logger = logging.getLogger("analysis")
        analysis_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, "analysis.log"),
            maxBytes=50 * 1024 * 1024,
            backupCount=5
        )
        analysis_handler.setFormatter(StructuredFormatter("analysis"))
        analysis_logger.addHandler(analysis_handler)
        
        # SBOM generation logger
        sbom_logger = logging.getLogger("sbom")
        sbom_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, "sbom.log"),
            maxBytes=50 * 1024 * 1024,
            backupCount=5
        )
        sbom_handler.setFormatter(StructuredFormatter("sbom"))
        sbom_logger.addHandler(sbom_handler)
        
        # Security logger
        security_logger = logging.getLogger("security")
        security_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, "security.log"),
            maxBytes=50 * 1024 * 1024,
            backupCount=10
        )
        security_handler.setFormatter(StructuredFormatter("security"))
        security_logger.addHandler(security_handler)
        
        # Performance logger
        perf_logger = logging.getLogger("performance")
        perf_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, "performance.log"),
            maxBytes=50 * 1024 * 1024,
            backupCount=5
        )
        perf_handler.setFormatter(StructuredFormatter("performance"))
        perf_logger.addHandler(perf_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger with proper configuration"""
        return logging.getLogger(name)


class AuditLogger:
    """Specialized logger for audit events"""
    
    def __init__(self, service_name: str = "sbom-platform"):
        self.logger = logging.getLogger("audit")
        self.service_name = service_name
        self._setup_audit_logging()
    
    def _setup_audit_logging(self):
        """Setup audit-specific logging"""
        audit_handler = logging.handlers.RotatingFileHandler(
            filename="/app/data/logs/audit.log",
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=20  # Keep more audit logs
        )
        
        audit_formatter = StructuredFormatter("audit")
        audit_handler.setFormatter(audit_formatter)
        
        self.logger.addHandler(audit_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_analysis_request(self, analysis_id: str, request_data: Dict[str, Any], 
                           client_ip: str = "unknown"):
        """Log analysis request"""
        self.logger.info(
            "Analysis request submitted",
            extra={
                "analysis_id": analysis_id,
                "client_ip": client_ip,
                "operation": "analysis_request",
                "request_type": request_data.get("type"),
                "language": request_data.get("language"),
                "location": request_data.get("location", "")[:100]  # Truncate long paths
            }
        )
    
    def log_analysis_completion(self, analysis_id: str, success: bool, 
                              components_found: int = 0, duration: float = 0):
        """Log analysis completion"""
        self.logger.info(
            f"Analysis {'completed' if success else 'failed'}",
            extra={
                "analysis_id": analysis_id,
                "operation": "analysis_completion",
                "success": success,
                "components_found": components_found,
                "duration": duration
            }
        )
    
    def log_sbom_generation(self, sbom_id: str, analysis_ids: list, 
                          format_type: str, success: bool = True):
        """Log SBOM generation"""
        self.logger.info(
            f"SBOM {'generated' if success else 'generation failed'}",
            extra={
                "sbom_id": sbom_id,
                "operation": "sbom_generation",
                "analysis_ids": analysis_ids,
                "format": format_type,
                "success": success
            }
        )
    
    def log_file_access(self, file_path: str, operation: str, 
                       client_ip: str = "unknown"):
        """Log file access operations"""
        self.logger.info(
            f"File access: {operation}",
            extra={
                "operation": "file_access",
                "file_path": file_path[:200],  # Truncate long paths
                "access_type": operation,
                "client_ip": client_ip
            }
        )
    
    def log_security_event(self, event_type: str, details: str, 
                         client_ip: str = "unknown", severity: str = "info"):
        """Log security events"""
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(
            f"Security event: {event_type}",
            extra={
                "operation": "security_event",
                "event_type": event_type,
                "details": details,
                "client_ip": client_ip,
                "severity": severity
            }
        )


class PerformanceLogger:
    """Logger for performance metrics and events"""
    
    def __init__(self):
        self.logger = logging.getLogger("performance")
    
    def log_operation_timing(self, operation: str, duration: float, 
                           details: Optional[Dict[str, Any]] = None):
        """Log operation timing"""
        extra = {
            "operation": operation,
            "duration": duration,
            "performance_event": True
        }
        
        if details:
            extra.update(details)
        
        self.logger.info(f"Operation completed: {operation}", extra=extra)
    
    def log_resource_usage(self, cpu_percent: float, memory_percent: float, 
                         disk_percent: float):
        """Log system resource usage"""
        self.logger.info(
            "System resource usage",
            extra={
                "operation": "resource_monitoring",
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "performance_event": True
            }
        )
    
    def log_api_performance(self, endpoint: str, method: str, 
                          response_time: float, status_code: int):
        """Log API performance"""
        self.logger.info(
            f"API request: {method} {endpoint}",
            extra={
                "operation": "api_request",
                "endpoint": endpoint,
                "method": method,
                "response_time": response_time,
                "status_code": status_code,
                "performance_event": True
            }
        )


def setup_application_logging(service_name: str = "sbom-platform", 
                            log_level: str = "INFO"):
    """Setup logging for the entire application"""
    config = LoggingConfig(service_name, log_level)
    config.setup_logging()
    
    return {
        "audit": AuditLogger(service_name),
        "performance": PerformanceLogger(),
        "config": config
    }