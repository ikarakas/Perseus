"""
OS-level Bill of Materials analyzer for Linux systems
"""

import platform
import subprocess
import json
import os
import re
import time
import glob
import shutil
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from ..api.models import AnalysisOptions, AnalysisResult, Component
from .base import BaseAnalyzer
import logging

logger = logging.getLogger(__name__)

class OSAnalyzer(BaseAnalyzer):
    """Analyzer for generating OS-level Bill of Materials"""
    
    def __init__(self):
        """Initialize OS analyzer with distribution detection"""
        self.distribution = self._get_linux_distribution()
        self.package_manager, self.pm_info = self._detect_package_manager()
        logger.info(f"Detected distribution: {self.distribution.get('NAME', 'Unknown')}")
        logger.info(f"Detected package manager: {self.package_manager}")
    
    def _get_linux_distribution(self) -> Dict[str, str]:
        """Get Linux distribution information"""
        dist_info = {}
        
        # Try /etc/os-release (systemd standard)
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        dist_info[key] = value.strip('"')
        
        # Fallback to older methods
        elif os.path.exists('/etc/lsb-release'):
            with open('/etc/lsb-release') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        dist_info[key.replace('DISTRIB_', '')] = value.strip('"')
        
        # Check for specific distribution files
        elif os.path.exists('/etc/redhat-release'):
            with open('/etc/redhat-release') as f:
                dist_info['NAME'] = f.read().strip()
        elif os.path.exists('/etc/debian_version'):
            with open('/etc/debian_version') as f:
                dist_info['NAME'] = 'Debian'
                dist_info['VERSION'] = f.read().strip()
        
        return dist_info
    
    def _detect_package_manager(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Detect which package manager is available"""
        package_managers = {
            'dpkg': {
                'cmd': ['dpkg', '-l'],
                'type': 'deb',
                'parse_installed': self._parse_dpkg_output
            },
            'rpm': {
                'cmd': ['rpm', '-qa', '--queryformat', '%{NAME}|%{VERSION}-%{RELEASE}|%{LICENSE}\n'],
                'type': 'rpm',
                'parse_installed': self._parse_rpm_output
            },
            'pacman': {
                'cmd': ['pacman', '-Q'],
                'type': 'arch',
                'parse_installed': self._parse_pacman_output
            },
            'apk': {
                'cmd': ['apk', 'info', '-v'],
                'type': 'alpine',
                'parse_installed': self._parse_apk_output
            },
            'emerge': {
                'cmd': ['qlist', '-ICv'],
                'type': 'gentoo',
                'parse_installed': self._parse_gentoo_output
            }
        }
        
        for pm, info in package_managers.items():
            if shutil.which(pm) or (pm == 'emerge' and shutil.which('qlist')):
                return pm, info
        return None, None
    
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """
        Analyze the operating system and generate OS BOM
        
        Args:
            location: For OS analysis, this should be 'localhost' or a hostname for future remote support
            options: Analysis options
            
        Returns:
            AnalysisResult containing OS components
        """
        analysis_id = f"os-{platform.node()}-{int(time.time())}"
        components = []
        errors = []
        metadata = {
            "os_type": platform.system(),
            "hostname": platform.node(),
            "architecture": platform.machine(),
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "distribution": self.distribution,
            "package_manager": self.package_manager
        }
        
        if platform.system() != "Linux":
            errors.append(f"OS analysis currently only supports Linux. Detected: {platform.system()}")
            return AnalysisResult(
                analysis_id=analysis_id,
                status="error",
                components=components,
                errors=errors,
                metadata=metadata
            )
        
        try:
            # Collect kernel information
            kernel_components = await self._analyze_kernel()
            components.extend(kernel_components)
            
            # Collect kernel modules
            module_components = await self._analyze_kernel_modules()
            components.extend(module_components)
            
            # Collect system libraries
            library_components = await self._analyze_system_libraries()
            components.extend(library_components)
            
            # Collect installed packages
            if options and options.deep_scan:
                package_components = await self._analyze_installed_packages()
                components.extend(package_components)
            
            # Collect security features
            security_info = await self._analyze_security_features()
            metadata["security_features"] = security_info
            
            # Collect hardware/firmware info
            hardware_info = await self._analyze_hardware()
            metadata["hardware_info"] = hardware_info
            
            status = "completed" if not errors else "completed_with_errors"
            
        except Exception as e:
            logger.error(f"OS analysis failed: {str(e)}")
            errors.append(str(e))
            status = "error"
        
        return AnalysisResult(
            analysis_id=analysis_id,
            status=status,
            components=components,
            errors=errors,
            metadata=metadata
        )
    
    async def _analyze_kernel(self) -> List[Component]:
        """Analyze Linux kernel information"""
        components = []
        
        try:
            # Get kernel version
            kernel_version = platform.release()
            
            # Try to get more detailed kernel info
            kernel_info = {}
            if os.path.exists("/proc/version"):
                with open("/proc/version", "r") as f:
                    kernel_info["full_version"] = f.read().strip()
            
            # Get kernel build info if available
            if os.path.exists("/proc/version_signature"):
                with open("/proc/version_signature", "r") as f:
                    kernel_info["signature"] = f.read().strip()
            
            # Get kernel config if available
            config_path = self._find_kernel_config(kernel_version)
            if config_path:
                kernel_info["config_path"] = config_path
            
            # Create kernel component
            kernel_component = self._create_component(
                name="linux-kernel",
                version=kernel_version,
                purl=f"pkg:generic/linux-kernel@{kernel_version}"
            )
            kernel_component.type = "kernel"
            kernel_component.metadata = kernel_info
            components.append(kernel_component)
            
        except Exception as e:
            logger.error(f"Failed to analyze kernel: {str(e)}")
        
        return components
    
    async def _analyze_kernel_modules(self) -> List[Component]:
        """Analyze loaded kernel modules"""
        components = []
        
        try:
            # Get loaded modules using lsmod
            result = subprocess.run(["lsmod"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 1:
                        module_name = parts[0]
                        module_size = parts[1] if len(parts) > 1 else "unknown"
                        
                        # Try to get module info
                        module_info = {}
                        modinfo_result = subprocess.run(
                            ["modinfo", module_name], 
                            capture_output=True, 
                            text=True
                        )
                        
                        if modinfo_result.returncode == 0:
                            for info_line in modinfo_result.stdout.split('\n'):
                                if ':' in info_line:
                                    key, value = info_line.split(':', 1)
                                    module_info[key.strip()] = value.strip()
                        
                        module_component = self._create_component(
                            name=f"kernel-module:{module_name}",
                            version=module_info.get("version", "unknown"),
                            license=module_info.get("license")
                        )
                        module_component.type = "kernel-module"
                        module_component.metadata = {
                            "size": module_size,
                            "filename": module_info.get("filename"),
                            "description": module_info.get("description"),
                            "author": module_info.get("author")
                        }
                        components.append(module_component)
                        
        except Exception as e:
            logger.error(f"Failed to analyze kernel modules: {str(e)}")
        
        return components
    
    async def _analyze_system_libraries(self) -> List[Component]:
        """Analyze critical system libraries"""
        components = []
        
        try:
            # Check libc version
            result = subprocess.run(["ldd", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                first_line = result.stdout.split('\n')[0]
                # Extract version from string like "ldd (GNU libc) 2.31"
                version_match = re.search(r'(\d+\.\d+)', first_line)
                if version_match:
                    glibc_version = version_match.group(1)
                    
                    glibc_component = self._create_component(
                        name="glibc",
                        version=glibc_version,
                        purl=f"pkg:generic/glibc@{glibc_version}"
                    )
                    glibc_component.type = "library"
                    components.append(glibc_component)
            
            # Find critical libraries across different distributions
            libraries = self._find_system_libraries()
            
            for lib_name, lib_path in libraries.items():
                # Try to get version from the library
                lib_real = os.path.realpath(lib_path)
                version_match = re.search(r'\.so\.(\d+(?:\.\d+)*)', lib_real)
                version = version_match.group(1) if version_match else "unknown"
                
                # Clean up library name
                clean_name = lib_name.replace('.so', '')
                
                lib_component = self._create_component(
                    name=clean_name,
                    version=version,
                    source_location=lib_path
                )
                lib_component.type = "library"
                components.append(lib_component)
                    
        except Exception as e:
            logger.error(f"Failed to analyze system libraries: {str(e)}")
        
        return components
    
    async def _analyze_installed_packages(self) -> List[Component]:
        """Analyze installed system packages"""
        components = []
        
        if not self.package_manager or not self.pm_info:
            logger.warning("No supported package manager detected")
            return components
        
        try:
            result = subprocess.run(
                self.pm_info['cmd'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Use the appropriate parser for the package manager
                parser = self.pm_info['parse_installed']
                components = parser(result.stdout)
            else:
                logger.error(f"Package manager command failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Failed to analyze installed packages: {str(e)}")
        
        return components
    
    async def _analyze_security_features(self) -> Dict[str, Any]:
        """Analyze security features and settings"""
        security_info = {}
        
        try:
            # Check SELinux status
            if os.path.exists("/usr/sbin/getenforce"):
                result = subprocess.run(["/usr/sbin/getenforce"], capture_output=True, text=True)
                if result.returncode == 0:
                    security_info["selinux"] = result.stdout.strip()
            
            # Check AppArmor status
            if os.path.exists("/sys/kernel/security/apparmor/profiles"):
                try:
                    with open("/sys/kernel/security/apparmor/profiles", "r") as f:
                        profiles = f.read().strip().split('\n')
                        security_info["apparmor_profiles"] = len(profiles)
                except PermissionError:
                    logger.warning("AppArmor profiles not accessible (requires sudo)")
                    security_info["apparmor_profiles"] = "access_denied"
            
            # Check kernel security parameters
            security_params = {
                "kernel.randomize_va_space": "/proc/sys/kernel/randomize_va_space",
                "kernel.dmesg_restrict": "/proc/sys/kernel/dmesg_restrict",
                "kernel.kptr_restrict": "/proc/sys/kernel/kptr_restrict",
                "kernel.yama.ptrace_scope": "/proc/sys/kernel/yama/ptrace_scope"
            }
            
            for param, path in security_params.items():
                if os.path.exists(path):
                    try:
                        with open(path, "r") as f:
                            security_info[param] = f.read().strip()
                    except PermissionError:
                        logger.warning(f"Security parameter {param} not accessible")
                        security_info[param] = "access_denied"
                        
        except Exception as e:
            logger.error(f"Failed to analyze security features: {str(e)}")
        
        return security_info
    
    async def _analyze_hardware(self) -> Dict[str, Any]:
        """Analyze hardware and firmware information"""
        hardware_info = {}
        
        try:
            # CPU info
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r") as f:
                    cpu_data = f.read()
                    model_match = re.search(r'model name\s*:\s*(.+)', cpu_data)
                    if model_match:
                        hardware_info["cpu_model"] = model_match.group(1)
                    
                    cores = len(re.findall(r'processor\s*:', cpu_data))
                    hardware_info["cpu_cores"] = cores
            
            # Memory info
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    mem_data = f.read()
                    total_match = re.search(r'MemTotal:\s*(\d+)', mem_data)
                    if total_match:
                        hardware_info["memory_total_kb"] = int(total_match.group(1))
            
            # DMI/BIOS info
            if os.path.exists("/sys/class/dmi/id/bios_version"):
                with open("/sys/class/dmi/id/bios_version", "r") as f:
                    hardware_info["bios_version"] = f.read().strip()
            
            if os.path.exists("/sys/class/dmi/id/bios_vendor"):
                with open("/sys/class/dmi/id/bios_vendor", "r") as f:
                    hardware_info["bios_vendor"] = f.read().strip()
                    
        except Exception as e:
            logger.error(f"Failed to analyze hardware: {str(e)}")
        
        return hardware_info
    
    def _find_kernel_config(self, kernel_version: str) -> Optional[str]:
        """Find kernel config across different locations"""
        # Common config locations
        config_locations = [
            f'/boot/config-{kernel_version}',
            '/proc/config.gz',
            '/proc/config',
            f'/usr/src/linux-{kernel_version}/.config',
            '/usr/src/linux/.config'
        ]
        
        for location in config_locations:
            if os.path.exists(location):
                return location
        
        # Try to find any config in /boot
        configs = glob.glob('/boot/config-*')
        if configs:
            # Return the newest one
            return max(configs, key=os.path.getmtime)
        
        return None
    
    def _find_system_libraries(self) -> Dict[str, str]:
        """Find system libraries across different Linux distributions"""
        # Common library locations across distributions
        lib_search_paths = [
            '/lib',
            '/lib64',
            '/usr/lib',
            '/usr/lib64',
            '/lib/x86_64-linux-gnu',
            '/usr/lib/x86_64-linux-gnu',
            '/lib/aarch64-linux-gnu',
            '/usr/lib/aarch64-linux-gnu',
            '/lib/i386-linux-gnu',
            '/usr/lib/i386-linux-gnu'
        ]
        
        libraries = {}
        lib_names = ['libssl.so', 'libcrypto.so', 'libz.so', 'libsystemd.so', 'libc.so']
        
        for lib_name in lib_names:
            for search_path in lib_search_paths:
                if os.path.exists(search_path):
                    # Use glob to find versioned libraries
                    matches = glob.glob(os.path.join(search_path, f"{lib_name}*"))
                    if matches:
                        # Get the actual library (not just symlink)
                        for match in matches:
                            if os.path.isfile(match) and not os.path.islink(match):
                                libraries[lib_name] = match
                                break
                        if lib_name in libraries:
                            break
        
        return libraries
    
    def _parse_dpkg_output(self, output: str) -> List[Component]:
        """Parse dpkg output"""
        components = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.startswith('ii'):
                parts = line.split()
                if len(parts) >= 3:
                    package_name = parts[1]
                    version = parts[2]
                    
                    package_component = self._create_component(
                        name=package_name,
                        version=version,
                        purl=f"pkg:deb/debian/{package_name}@{version}"
                    )
                    package_component.type = "package"
                    components.append(package_component)
        
        return components
    
    def _parse_rpm_output(self, output: str) -> List[Component]:
        """Parse rpm output"""
        components = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip():
                parts = line.split('|')
                if len(parts) >= 2:
                    package_name = parts[0]
                    version = parts[1]
                    license = parts[2] if len(parts) > 2 else None
                    
                    package_component = self._create_component(
                        name=package_name,
                        version=version,
                        license=license,
                        purl=f"pkg:rpm/redhat/{package_name}@{version}"
                    )
                    package_component.type = "package"
                    components.append(package_component)
        
        return components
    
    def _parse_pacman_output(self, output: str) -> List[Component]:
        """Parse pacman output"""
        components = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    package_name = parts[0]
                    version = parts[1]
                    
                    package_component = self._create_component(
                        name=package_name,
                        version=version,
                        purl=f"pkg:arch/{package_name}@{version}"
                    )
                    package_component.type = "package"
                    components.append(package_component)
        
        return components
    
    def _parse_apk_output(self, output: str) -> List[Component]:
        """Parse apk output"""
        components = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip() and '-' in line:
                # APK format: package-version-rX
                match = re.match(r'^(.+?)-(\d+\..+)$', line.strip())
                if match:
                    package_name = match.group(1)
                    version = match.group(2)
                    
                    package_component = self._create_component(
                        name=package_name,
                        version=version,
                        purl=f"pkg:alpine/{package_name}@{version}"
                    )
                    package_component.type = "package"
                    components.append(package_component)
        
        return components
    
    def _parse_gentoo_output(self, output: str) -> List[Component]:
        """Parse Gentoo qlist output"""
        components = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip():
                # Gentoo format: category/package-version
                match = re.match(r'^(.+?)/(.+?)-(\d+\..+)$', line.strip())
                if match:
                    category = match.group(1)
                    package_name = match.group(2)
                    version = match.group(3)
                    
                    package_component = self._create_component(
                        name=f"{category}/{package_name}",
                        version=version,
                        purl=f"pkg:gentoo/{category}/{package_name}@{version}"
                    )
                    package_component.type = "package"
                    components.append(package_component)
        
        return components