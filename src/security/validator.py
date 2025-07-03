"""
Security validation and input sanitization
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Validates and sanitizes inputs for security"""
    
    def __init__(self):
        self.max_path_length = 4096
        self.max_file_size = 1024 * 1024 * 1024  # 1GB
        self.allowed_schemes = {'file', 'http', 'https', 'git'}
        self.dangerous_patterns = [
            r'\.\.',           # Path traversal
            r'[\x00-\x1f]',    # Control characters
            r'[<>&\'"\\]',     # Potential injection characters
            r'javascript:',    # JavaScript protocol
            r'data:',          # Data protocol
        ]
    
    def validate_location(self, location: str) -> Dict[str, Any]:
        """Validate and sanitize location input"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "sanitized_location": location
        }
        
        try:
            # Check length
            if len(location) > self.max_path_length:
                validation_result["valid"] = False
                validation_result["errors"].append("Location path too long")
                return validation_result
            
            # Parse URL if it looks like one
            if '://' in location:
                parsed = urlparse(location)
                
                # Check scheme
                if parsed.scheme not in self.allowed_schemes:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Unsupported scheme: {parsed.scheme}")
                    return validation_result
                
                # Check for dangerous patterns in URL
                if self._contains_dangerous_patterns(location):
                    validation_result["valid"] = False
                    validation_result["errors"].append("Location contains potentially dangerous patterns")
                    return validation_result
                
                # Sanitize file:// URLs
                if parsed.scheme == 'file':
                    file_path = parsed.path
                    validation_result.update(self._validate_file_path(file_path))
                    if validation_result["valid"]:
                        validation_result["sanitized_location"] = f"file://{validation_result['sanitized_path']}"
            else:
                # Treat as file path
                validation_result.update(self._validate_file_path(location))
                validation_result["sanitized_location"] = validation_result.get("sanitized_path", location)
            
        except Exception as e:
            logger.error(f"Location validation error: {e}")
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """Validate file path for security"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        try:
            # Normalize path
            normalized = os.path.normpath(file_path)
            result["sanitized_path"] = normalized
            
            # Check for path traversal
            if '..' in normalized:
                result["valid"] = False
                result["errors"].append("Path traversal detected")
                return result
            
            # Check for dangerous patterns
            if self._contains_dangerous_patterns(normalized):
                result["valid"] = False
                result["errors"].append("File path contains dangerous patterns")
                return result
            
            # Check if path exists and is accessible
            if os.path.exists(normalized):
                if os.path.isfile(normalized):
                    # Check file size
                    file_size = os.path.getsize(normalized)
                    if file_size > self.max_file_size:
                        result["warnings"].append(f"Large file detected: {file_size} bytes")
                
                # Check permissions
                if not os.access(normalized, os.R_OK):
                    result["valid"] = False
                    result["errors"].append("File/directory not readable")
            else:
                result["warnings"].append("Path does not exist")
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Path validation error: {str(e)}")
        
        return result
    
    def _contains_dangerous_patterns(self, text: str) -> bool:
        """Check if text contains dangerous patterns"""
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def validate_analysis_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate analysis options"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        try:
            # Check timeout
            if "timeout_minutes" in options:
                timeout = options["timeout_minutes"]
                if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 180:
                    result["valid"] = False
                    result["errors"].append("Invalid timeout value (must be 1-180 minutes)")
            
            # Check boolean options
            bool_options = ["deep_scan", "include_dev_dependencies"]
            for option in bool_options:
                if option in options and not isinstance(options[option], bool):
                    result["warnings"].append(f"Option {option} should be boolean")
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Options validation error: {str(e)}")
        
        return result
    
    def sanitize_component_name(self, name: str) -> str:
        """Sanitize component name"""
        if not name:
            return "unknown"
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>&\'"\\]', '', name)
        
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized.strip()
    
    def validate_sbom_data(self, sbom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SBOM data for security issues"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        try:
            # Check for suspicious URLs or paths in SBOM
            self._scan_dict_for_security_issues(sbom_data, result)
            
            # Check SBOM size
            sbom_str = str(sbom_data)
            if len(sbom_str) > 100 * 1024 * 1024:  # 100MB
                result["warnings"].append("Very large SBOM detected")
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"SBOM validation error: {str(e)}")
        
        return result
    
    def _scan_dict_for_security_issues(self, data: Any, result: Dict[str, Any], path: str = ""):
        """Recursively scan dictionary for security issues"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                self._scan_dict_for_security_issues(value, result, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                self._scan_dict_for_security_issues(item, result, current_path)
        elif isinstance(data, str):
            # Check for suspicious patterns in string values
            if self._contains_dangerous_patterns(data):
                result["warnings"].append(f"Potentially dangerous content at {path}: {data[:50]}...")
            
            # Check for URLs
            if '://' in data:
                parsed = urlparse(data)
                if parsed.scheme not in self.allowed_schemes:
                    result["warnings"].append(f"Suspicious URL scheme at {path}: {parsed.scheme}")


class InputSanitizer:
    """Sanitizes various types of input"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[/\\:*?"<>|]', '', filename)
        sanitized = re.sub(r'\.\.', '', sanitized)
        
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_version(version: str) -> str:
        """Sanitize version string"""
        if not version:
            return "unknown"
        
        # Allow only alphanumeric, dots, hyphens, and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9.\-_]', '', version)
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_license(license_str: str) -> str:
        """Sanitize license string"""
        if not license_str:
            return "NOASSERTION"
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>&\'"\\]', '', license_str)
        
        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized.strip()


class SecurityAuditor:
    """Audits security events and maintains logs"""
    
    def __init__(self):
        self.audit_log_file = "/app/data/security_audit.log"
        self._setup_audit_logging()
    
    def _setup_audit_logging(self):
        """Setup security audit logging"""
        self.audit_logger = logging.getLogger("security_audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # Create file handler
        os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)
        file_handler = logging.FileHandler(self.audit_log_file)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.audit_logger.addHandler(file_handler)
    
    def log_analysis_request(self, request_data: Dict[str, Any], client_info: str = "unknown"):
        """Log analysis request for audit"""
        self.audit_logger.info(
            f"Analysis request - Client: {client_info}, "
            f"Type: {request_data.get('type')}, "
            f"Language: {request_data.get('language')}, "
            f"Location: {request_data.get('location', 'unknown')[:100]}"
        )
    
    def log_security_violation(self, violation_type: str, details: str, client_info: str = "unknown"):
        """Log security violation"""
        self.audit_logger.warning(
            f"Security violation - Type: {violation_type}, "
            f"Client: {client_info}, "
            f"Details: {details}"
        )
    
    def log_file_access(self, file_path: str, operation: str, client_info: str = "unknown"):
        """Log file access operations"""
        self.audit_logger.info(
            f"File access - Operation: {operation}, "
            f"Path: {file_path}, "
            f"Client: {client_info}"
        )
    
    def log_sbom_generation(self, sbom_id: str, format_type: str, component_count: int):
        """Log SBOM generation"""
        self.audit_logger.info(
            f"SBOM generated - ID: {sbom_id}, "
            f"Format: {format_type}, "
            f"Components: {component_count}"
        )