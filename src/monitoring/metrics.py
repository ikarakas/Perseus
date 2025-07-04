"""
Metrics collection and monitoring for SBOM platform
"""

import time
import logging
import json
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and manages platform metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics_lock = Lock()
        
        # Analysis metrics
        self.analysis_counts = defaultdict(int)
        self.analysis_durations = defaultdict(list)
        self.analysis_success_rates = defaultdict(lambda: {"success": 0, "failed": 0})
        self.component_detection_stats = defaultdict(list)
        
        # SBOM generation metrics
        self.sbom_generation_counts = defaultdict(int)
        self.sbom_generation_durations = defaultdict(list)
        self.sbom_format_usage = defaultdict(int)
        
        # API metrics
        self.api_request_counts = defaultdict(int)
        self.api_response_times = defaultdict(list)
        self.api_error_rates = defaultdict(lambda: {"success": 0, "error": 0})
        
        # System metrics
        self.system_metrics_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        
        # Time-series data
        self.metrics_history = deque(maxlen=retention_hours * 60)  # Minute-by-minute for retention period
        
        self._start_time = time.time()
    
    def record_analysis_start(self, analysis_id: str, analysis_type: str, language: str = None):
        """Record start of analysis"""
        with self.metrics_lock:
            key = f"{analysis_type}_{language}" if language else analysis_type
            self.analysis_counts[key] += 1
            
            # Store start time for duration calculation
            if not hasattr(self, '_analysis_start_times'):
                self._analysis_start_times = {}
            self._analysis_start_times[analysis_id] = time.time()
    
    def record_analysis_completion(self, analysis_id: str, analysis_type: str, 
                                 language: str = None, success: bool = True, 
                                 components_found: int = 0):
        """Record completion of analysis"""
        with self.metrics_lock:
            key = f"{analysis_type}_{language}" if language else analysis_type
            
            # Record success/failure
            if success:
                self.analysis_success_rates[key]["success"] += 1
            else:
                self.analysis_success_rates[key]["failed"] += 1
            
            # Record duration
            if hasattr(self, '_analysis_start_times') and analysis_id in self._analysis_start_times:
                duration = time.time() - self._analysis_start_times[analysis_id]
                self.analysis_durations[key].append(duration)
                del self._analysis_start_times[analysis_id]
            
            # Record component detection
            if success:
                self.component_detection_stats[key].append(components_found)
    
    def record_sbom_generation(self, sbom_format: str, duration: float, 
                             component_count: int, success: bool = True):
        """Record SBOM generation metrics"""
        with self.metrics_lock:
            if success:
                self.sbom_generation_counts[sbom_format] += 1
                self.sbom_generation_durations[sbom_format].append(duration)
                self.sbom_format_usage[sbom_format] += 1
    
    def record_api_request(self, endpoint: str, method: str, response_time: float, 
                          status_code: int):
        """Record API request metrics"""
        with self.metrics_lock:
            key = f"{method}_{endpoint}"
            self.api_request_counts[key] += 1
            self.api_response_times[key].append(response_time)
            
            if 200 <= status_code < 400:
                self.api_error_rates[key]["success"] += 1
            else:
                self.api_error_rates[key]["error"] += 1
    
    def collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            # Get CPU usage (1 second interval for accuracy)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Get disk usage for current working directory
            disk = psutil.disk_usage('.')
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_used_gb": round(memory_used_gb, 2),
                "memory_total_gb": round(memory_total_gb, 2),
                "disk_percent": round(disk.percent, 1),
                "disk_used_gb": round(disk_used_gb, 2),
                "disk_total_gb": round(disk_total_gb, 2)
            }
            
            with self.metrics_lock:
                self.system_metrics_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return placeholder values if psutil fails
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "memory_used_gb": 0.0,
                "memory_total_gb": 0.0,
                "disk_percent": 0.0,
                "disk_used_gb": 0.0,
                "disk_total_gb": 0.0
            }
    
    def get_analysis_metrics(self) -> Dict[str, Any]:
        """Get analysis performance metrics"""
        with self.metrics_lock:
            metrics = {
                "total_analyses": sum(self.analysis_counts.values()),
                "analyses_by_type": dict(self.analysis_counts),
                "success_rates": {
                    key: {
                        "success_rate": stats["success"] / (stats["success"] + stats["failed"]) * 100
                        if (stats["success"] + stats["failed"]) > 0 else 0,
                        "total_attempts": stats["success"] + stats["failed"]
                    }
                    for key, stats in self.analysis_success_rates.items()
                },
                "average_durations": {
                    key: sum(durations) / len(durations) if durations else 0
                    for key, durations in self.analysis_durations.items()
                },
                "average_components_detected": {
                    key: sum(counts) / len(counts) if counts else 0
                    for key, counts in self.component_detection_stats.items()
                }
            }
        
        return metrics
    
    def get_sbom_metrics(self) -> Dict[str, Any]:
        """Get SBOM generation metrics"""
        with self.metrics_lock:
            metrics = {
                "total_sboms_generated": sum(self.sbom_generation_counts.values()),
                "sboms_by_format": dict(self.sbom_format_usage),
                "average_generation_time": {
                    format_type: sum(durations) / len(durations) if durations else 0
                    for format_type, durations in self.sbom_generation_durations.items()
                }
            }
        
        return metrics
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics"""
        with self.metrics_lock:
            metrics = {
                "total_requests": sum(self.api_request_counts.values()),
                "requests_by_endpoint": dict(self.api_request_counts),
                "average_response_times": {
                    endpoint: sum(times) / len(times) if times else 0
                    for endpoint, times in self.api_response_times.items()
                },
                "error_rates": {
                    endpoint: {
                        "error_rate": stats["error"] / (stats["success"] + stats["error"]) * 100
                        if (stats["success"] + stats["error"]) > 0 else 0,
                        "total_requests": stats["success"] + stats["error"]
                    }
                    for endpoint, stats in self.api_error_rates.items()
                }
            }
        
        return metrics
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current and historical system metrics"""
        current_metrics = self.collect_system_metrics()
        
        with self.metrics_lock:
            recent_metrics = list(self.system_metrics_history)[-60:]  # Last hour
        
        if recent_metrics:
            avg_cpu = sum(m["cpu_percent"] for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m["memory_percent"] for m in recent_metrics) / len(recent_metrics)
            avg_disk = sum(m["disk_percent"] for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = avg_memory = avg_disk = 0
        
        return {
            "current": current_metrics,
            "averages_last_hour": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory,
                "disk_percent": avg_disk
            },
            "uptime_hours": (time.time() - self._start_time) / 3600
        }
    
    def get_summary_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary for dashboard"""
        return {
            "analysis": self.get_analysis_metrics(),
            "sbom": self.get_sbom_metrics(),
            "api": self.get_api_metrics(),
            "system": self.get_system_metrics(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        metrics = self.get_summary_dashboard()
        
        if format.lower() == "json":
            return json.dumps(metrics, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")


class AlertManager:
    """Manages alerts based on metrics thresholds"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "error_rate_percent": 5,
            "response_time_seconds": 30
        }
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        current_time = datetime.utcnow()
        
        # Check system metrics
        system_metrics = self.metrics_collector.get_system_metrics()
        if system_metrics["current"]:
            current = system_metrics["current"]
            
            # CPU alert
            if current["cpu_percent"] > self.alert_thresholds["cpu_percent"]:
                alerts.append(self._create_alert(
                    "high_cpu_usage",
                    f"CPU usage is {current['cpu_percent']:.1f}%",
                    "warning"
                ))
            
            # Memory alert
            if current["memory_percent"] > self.alert_thresholds["memory_percent"]:
                alerts.append(self._create_alert(
                    "high_memory_usage",
                    f"Memory usage is {current['memory_percent']:.1f}%",
                    "warning"
                ))
            
            # Disk alert
            if current["disk_percent"] > self.alert_thresholds["disk_percent"]:
                alerts.append(self._create_alert(
                    "high_disk_usage",
                    f"Disk usage is {current['disk_percent']:.1f}%",
                    "critical"
                ))
        
        # Check API error rates
        api_metrics = self.metrics_collector.get_api_metrics()
        for endpoint, stats in api_metrics["error_rates"].items():
            if stats["error_rate"] > self.alert_thresholds["error_rate_percent"]:
                alerts.append(self._create_alert(
                    "high_error_rate",
                    f"High error rate for {endpoint}: {stats['error_rate']:.1f}%",
                    "warning"
                ))
        
        # Check response times
        for endpoint, avg_time in api_metrics["average_response_times"].items():
            if avg_time > self.alert_thresholds["response_time_seconds"]:
                alerts.append(self._create_alert(
                    "slow_response_time",
                    f"Slow response time for {endpoint}: {avg_time:.1f}s",
                    "warning"
                ))
        
        # Update active alerts and history
        for alert in alerts:
            alert_key = f"{alert['type']}_{alert['source']}"
            if alert_key not in self.active_alerts:
                self.active_alerts[alert_key] = alert
                self.alert_history.append(alert)
                logger.warning(f"Alert triggered: {alert['message']}")
        
        return alerts
    
    def _create_alert(self, alert_type: str, message: str, severity: str, 
                     source: str = "system") -> Dict[str, Any]:
        """Create alert dictionary"""
        return {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "id": f"{alert_type}_{int(time.time())}"
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts"""
        return list(self.active_alerts.values())
    
    def clear_alert(self, alert_id: str):
        """Clear an active alert"""
        for key, alert in list(self.active_alerts.items()):
            if alert["id"] == alert_id:
                del self.active_alerts[key]
                logger.info(f"Alert cleared: {alert_id}")
                break


class PerformanceProfiler:
    """Profiles performance of various operations"""
    
    def __init__(self):
        self.operation_times = defaultdict(list)
        self.operation_counts = defaultdict(int)
    
    def profile_operation(self, operation_name: str):
        """Context manager for profiling operations"""
        return OperationProfiler(self, operation_name)
    
    def record_operation(self, operation_name: str, duration: float):
        """Record operation duration"""
        self.operation_times[operation_name].append(duration)
        self.operation_counts[operation_name] += 1
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get performance profile summary"""
        summary = {}
        
        for operation, times in self.operation_times.items():
            if times:
                summary[operation] = {
                    "count": self.operation_counts[operation],
                    "avg_duration": sum(times) / len(times),
                    "min_duration": min(times),
                    "max_duration": max(times),
                    "total_duration": sum(times)
                }
        
        return summary


class OperationProfiler:
    """Context manager for profiling individual operations"""
    
    def __init__(self, profiler: PerformanceProfiler, operation_name: str):
        self.profiler = profiler
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.profiler.record_operation(self.operation_name, duration)