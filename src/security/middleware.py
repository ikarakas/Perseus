# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Security middleware for FastAPI application
"""

import time
import logging
from typing import Dict, Set
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .validator import SecurityValidator, SecurityAuditor

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and rate limiting"""
    
    def __init__(self, app, max_requests_per_minute: int = 60):
        super().__init__(app)
        self.validator = SecurityValidator()
        self.auditor = SecurityAuditor()
        self.max_requests_per_minute = max_requests_per_minute
        self.rate_limit_cache: Dict[str, Dict] = {}
        self.blocked_ips: Set[str] = set()
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware"""
        client_ip = self._get_client_ip(request)
        
        try:
            # Check if IP is blocked
            if client_ip in self.blocked_ips:
                self.auditor.log_security_violation(
                    "blocked_ip_access",
                    f"Blocked IP attempted access: {client_ip}",
                    client_ip
                )
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Rate limiting
            if not self._check_rate_limit(client_ip):
                self.auditor.log_security_violation(
                    "rate_limit_exceeded",
                    f"Rate limit exceeded for IP: {client_ip}",
                    client_ip
                )
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Validate request
            await self._validate_request(request, client_ip)
            
            # Process request
            response = await call_next(request)
            
            # Log successful request
            self.auditor.log_analysis_request(
                {"path": request.url.path, "method": request.method},
                client_ip
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            self.auditor.log_security_violation(
                "middleware_error",
                f"Middleware error: {str(e)}",
                client_ip
            )
            raise HTTPException(status_code=500, detail="Internal security error")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limits"""
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_rate_limit_cache(current_time)
        
        # Check current client
        if client_ip not in self.rate_limit_cache:
            self.rate_limit_cache[client_ip] = {
                "requests": [],
                "last_request": current_time
            }
        
        client_data = self.rate_limit_cache[client_ip]
        
        # Remove requests older than 1 minute
        client_data["requests"] = [
            req_time for req_time in client_data["requests"]
            if current_time - req_time < 60
        ]
        
        # Check if limit exceeded
        if len(client_data["requests"]) >= self.max_requests_per_minute:
            return False
        
        # Add current request
        client_data["requests"].append(current_time)
        client_data["last_request"] = current_time
        
        return True
    
    def _cleanup_rate_limit_cache(self, current_time: float):
        """Clean up old entries from rate limit cache"""
        expired_ips = []
        for ip, data in self.rate_limit_cache.items():
            if current_time - data["last_request"] > 300:  # 5 minutes
                expired_ips.append(ip)
        
        for ip in expired_ips:
            del self.rate_limit_cache[ip]
    
    async def _validate_request(self, request: Request, client_ip: str):
        """Validate incoming request"""
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > 100 * 1024 * 1024:  # 100MB
                    self.auditor.log_security_violation(
                        "large_request",
                        f"Request too large: {size} bytes",
                        client_ip
                    )
                    raise HTTPException(status_code=413, detail="Request too large")
            except ValueError:
                pass
        
        # Validate URL path
        path = str(request.url.path)
        if self.validator._contains_dangerous_patterns(path):
            self.auditor.log_security_violation(
                "dangerous_path",
                f"Dangerous path pattern: {path}",
                client_ip
            )
            raise HTTPException(status_code=400, detail="Invalid request path")
        
        # Check for analysis endpoints
        if request.method == "POST" and "/analyze/" in path:
            try:
                body = await request.body()
                if body:
                    import json
                    try:
                        request_data = json.loads(body)
                        await self._validate_analysis_request(request_data, client_ip)
                    except json.JSONDecodeError:
                        self.auditor.log_security_violation(
                            "invalid_json",
                            "Invalid JSON in request body",
                            client_ip
                        )
                        raise HTTPException(status_code=400, detail="Invalid JSON")
            except Exception as e:
                logger.error(f"Request validation error: {e}")
    
    async def _validate_analysis_request(self, request_data: Dict, client_ip: str):
        """Validate analysis request data"""
        # Validate location
        location = request_data.get("location")
        if location:
            validation_result = self.validator.validate_location(location)
            if not validation_result["valid"]:
                self.auditor.log_security_violation(
                    "invalid_location",
                    f"Invalid location: {'; '.join(validation_result['errors'])}",
                    client_ip
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid location: {'; '.join(validation_result['errors'])}"
                )
        
        # Validate options
        options = request_data.get("options", {})
        if options:
            validation_result = self.validator.validate_analysis_options(options)
            if not validation_result["valid"]:
                self.auditor.log_security_violation(
                    "invalid_options",
                    f"Invalid options: {'; '.join(validation_result['errors'])}",
                    client_ip
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid options: {'; '.join(validation_result['errors'])}"
                )
    
    def block_ip(self, ip: str):
        """Block an IP address"""
        self.blocked_ips.add(ip)
        self.auditor.log_security_violation(
            "ip_blocked",
            f"IP address blocked: {ip}",
            "system"
        )
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)
        self.auditor.log_security_violation(
            "ip_unblocked",
            f"IP address unblocked: {ip}",
            "system"
        )


class ContainerSecurityManager:
    """Manages container security settings"""
    
    def __init__(self):
        self.container_limits = {
            "memory": "2g",
            "cpu_shares": 1024,
            "network_mode": "bridge",
            "read_only": True,
            "no_new_privileges": True
        }
    
    def create_secure_container_config(self, image: str, command: list = None) -> Dict:
        """Create secure Docker container configuration"""
        config = {
            "image": image,
            "mem_limit": self.container_limits["memory"],
            "cpu_shares": self.container_limits["cpu_shares"],
            "network_mode": self.container_limits["network_mode"],
            "read_only": self.container_limits["read_only"],
            "security_opt": [
                "no-new-privileges:true",
                "apparmor:docker-default"
            ],
            "cap_drop": ["ALL"],
            "cap_add": ["CHOWN", "SETUID", "SETGID"],  # Minimal required capabilities
            "user": "1000:1000",  # Non-root user
            "tmpfs": {
                "/tmp": "noexec,nosuid,size=100m",
                "/var/tmp": "noexec,nosuid,size=50m"
            }
        }
        
        if command:
            config["command"] = command
        
        return config
    
    def validate_container_runtime(self) -> Dict[str, bool]:
        """Validate container runtime security"""
        checks = {
            "docker_daemon_running": False,
            "security_options_available": False,
            "user_namespaces_enabled": False
        }
        
        try:
            import docker
            client = docker.from_env()
            
            # Check if Docker daemon is running
            client.ping()
            checks["docker_daemon_running"] = True
            
            # Check security options
            info = client.info()
            security_options = info.get("SecurityOptions", [])
            if any("apparmor" in opt or "selinux" in opt for opt in security_options):
                checks["security_options_available"] = True
            
            # Check for user namespace support
            if "userns" in info.get("InitBinary", ""):
                checks["user_namespaces_enabled"] = True
                
        except Exception as e:
            logger.error(f"Container security validation error: {e}")
        
        return checks