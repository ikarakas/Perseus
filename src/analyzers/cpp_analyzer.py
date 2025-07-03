"""
C/C++ source code analyzer
"""

import os
import re
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from .base import BaseAnalyzer
from ..api.models import AnalysisOptions, AnalysisResult, Component

logger = logging.getLogger(__name__)

class CppSourceAnalyzer(BaseAnalyzer):
    """Analyzer for C/C++ source code"""
    
    def __init__(self):
        self.system_includes = {
            'stdio.h', 'stdlib.h', 'string.h', 'math.h', 'time.h',
            'iostream', 'vector', 'string', 'map', 'set', 'algorithm'
        }
    
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """Analyze C/C++ source code"""
        try:
            components = []
            errors = []
            
            # Parse location
            source_path = self._parse_location(location)
            
            # Find build files
            build_files = self._find_build_files(source_path)
            
            # Analyze CMake files
            cmake_components = self._analyze_cmake_files(build_files.get('cmake', []))
            components.extend(cmake_components)
            
            # Analyze source files for includes
            source_files = self._find_source_files(source_path)
            include_components = self._analyze_includes(source_files)
            components.extend(include_components)
            
            # Analyze package managers
            pkg_components = self._analyze_package_managers(source_path)
            components.extend(pkg_components)
            
            # Remove duplicates
            unique_components = self._deduplicate_components(components)
            
            return AnalysisResult(
                analysis_id="",  # Will be set by workflow
                status="completed",
                components=unique_components,
                errors=errors,
                metadata={
                    "source_files_analyzed": len(source_files),
                    "build_files_found": len(build_files),
                    "analyzer_type": "cpp_source"
                }
            )
            
        except Exception as e:
            logger.error(f"C++ analysis failed: {e}")
            return AnalysisResult(
                analysis_id="",
                status="failed",
                components=[],
                errors=[str(e)],
                metadata={"analyzer_type": "cpp_source"}
            )
    
    def _parse_location(self, location: str) -> str:
        """Parse location string to get file path"""
        if location.startswith('file://'):
            return location[7:]
        elif location.startswith('git://'):
            # For git URLs, we'd need to clone first
            raise NotImplementedError("Git repository cloning not implemented")
        else:
            return location
    
    def _find_build_files(self, source_path: str) -> Dict[str, List[str]]:
        """Find build configuration files"""
        build_files = {'cmake': [], 'make': [], 'autoconf': []}
        
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                if file.lower() in ['cmakelists.txt']:
                    build_files['cmake'].append(file_path)
                elif file.lower() in ['makefile', 'makefile.am', 'makefile.in']:
                    build_files['make'].append(file_path)
                elif file.lower() in ['configure.ac', 'configure.in']:
                    build_files['autoconf'].append(file_path)
        
        return build_files
    
    def _find_source_files(self, source_path: str) -> List[str]:
        """Find C/C++ source files"""
        source_files = []
        extensions = {'.c', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.hxx', '.hh'}
        
        for root, dirs, files in os.walk(source_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    source_files.append(os.path.join(root, file))
        
        return source_files
    
    def _analyze_cmake_files(self, cmake_files: List[str]) -> List[Component]:
        """Analyze CMake files for dependencies"""
        components = []
        
        for cmake_file in cmake_files:
            try:
                with open(cmake_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Find find_package calls
                find_package_pattern = r'find_package\s*\(\s*([^\s\)]+)(?:\s+([^\)]+))?\)'
                matches = re.findall(find_package_pattern, content, re.IGNORECASE)
                
                for match in matches:
                    package_name = match[0]
                    version_info = match[1] if len(match) > 1 else ""
                    
                    # Extract version if present
                    version = self._extract_version_from_cmake(version_info)
                    
                    component = self._create_component(
                        name=package_name,
                        version=version,
                        source_location=cmake_file
                    )
                    components.append(component)
                
                # Find target_link_libraries for external libraries
                link_pattern = r'target_link_libraries\s*\([^)]+\)'
                link_matches = re.findall(link_pattern, content, re.IGNORECASE)
                
                for match in link_matches:
                    libs = self._extract_libraries_from_link_command(match)
                    for lib in libs:
                        if not lib.startswith(('${', '$<')):  # Skip CMake variables
                            component = self._create_component(
                                name=lib,
                                source_location=cmake_file
                            )
                            components.append(component)
                            
            except Exception as e:
                logger.warning(f"Failed to parse CMake file {cmake_file}: {e}")
        
        return components
    
    def _analyze_includes(self, source_files: List[str]) -> List[Component]:
        """Analyze include statements in source files"""
        components = []
        external_includes = set()
        
        for source_file in source_files:
            try:
                with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Find #include statements
                include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
                matches = re.findall(include_pattern, content)
                
                for include in matches:
                    # Skip system headers and common standard library headers
                    if include not in self.system_includes and not include.startswith('sys/'):
                        # Check if it's likely a third-party library
                        if '/' in include or not include.endswith('.h'):
                            external_includes.add(include)
                            
            except Exception as e:
                logger.warning(f"Failed to parse source file {source_file}: {e}")
        
        # Create components for external includes
        for include in external_includes:
            # Try to infer library name from include path
            lib_name = self._infer_library_from_include(include)
            if lib_name:
                component = self._create_component(
                    name=lib_name,
                    source_location="inferred_from_includes"
                )
                components.append(component)
        
        return components
    
    def _analyze_package_managers(self, source_path: str) -> List[Component]:
        """Analyze package manager files (Conan, vcpkg)"""
        components = []
        
        # Analyze Conan files
        conan_file = os.path.join(source_path, 'conanfile.txt')
        if os.path.exists(conan_file):
            components.extend(self._parse_conan_file(conan_file))
        
        conan_py = os.path.join(source_path, 'conanfile.py')
        if os.path.exists(conan_py):
            components.extend(self._parse_conan_py_file(conan_py))
        
        # Analyze vcpkg files
        vcpkg_file = os.path.join(source_path, 'vcpkg.json')
        if os.path.exists(vcpkg_file):
            components.extend(self._parse_vcpkg_file(vcpkg_file))
        
        return components
    
    def _parse_conan_file(self, conan_file: str) -> List[Component]:
        """Parse conanfile.txt for dependencies"""
        components = []
        
        try:
            with open(conan_file, 'r') as f:
                content = f.read()
            
            # Find [requires] section
            in_requires = False
            for line in content.split('\n'):
                line = line.strip()
                if line == '[requires]':
                    in_requires = True
                    continue
                elif line.startswith('[') and line != '[requires]':
                    in_requires = False
                    continue
                
                if in_requires and line and not line.startswith('#'):
                    # Parse package/version format
                    if '/' in line:
                        name, version = line.split('/', 1)
                        # Remove @channel if present
                        if '@' in version:
                            version = version.split('@')[0]
                    else:
                        name = line
                        version = None
                    
                    component = self._create_component(
                        name=name,
                        version=version,
                        source_location=conan_file
                    )
                    components.append(component)
                    
        except Exception as e:
            logger.warning(f"Failed to parse Conan file {conan_file}: {e}")
        
        return components
    
    def _parse_conan_py_file(self, conan_py: str) -> List[Component]:
        """Parse conanfile.py for dependencies"""
        components = []
        
        try:
            with open(conan_py, 'r') as f:
                content = f.read()
            
            # Look for requires = statements
            requires_pattern = r'requires\s*=\s*[\'"](.*?)[\'"]'
            matches = re.findall(requires_pattern, content)
            
            for require in matches:
                if '/' in require:
                    name, version = require.split('/', 1)
                    if '@' in version:
                        version = version.split('@')[0]
                else:
                    name = require
                    version = None
                
                component = self._create_component(
                    name=name,
                    version=version,
                    source_location=conan_py
                )
                components.append(component)
                
        except Exception as e:
            logger.warning(f"Failed to parse Conan Python file {conan_py}: {e}")
        
        return components
    
    def _parse_vcpkg_file(self, vcpkg_file: str) -> List[Component]:
        """Parse vcpkg.json for dependencies"""
        components = []
        
        try:
            with open(vcpkg_file, 'r') as f:
                data = json.load(f)
            
            dependencies = data.get('dependencies', [])
            for dep in dependencies:
                if isinstance(dep, str):
                    name = dep
                    version = None
                elif isinstance(dep, dict):
                    name = dep.get('name', '')
                    version = dep.get('version-string') or dep.get('version')
                else:
                    continue
                
                component = self._create_component(
                    name=name,
                    version=version,
                    source_location=vcpkg_file
                )
                components.append(component)
                
        except Exception as e:
            logger.warning(f"Failed to parse vcpkg file {vcpkg_file}: {e}")
        
        return components
    
    def _extract_version_from_cmake(self, version_info: str) -> Optional[str]:
        """Extract version from CMake find_package version info"""
        if not version_info:
            return None
        
        # Look for version numbers
        version_pattern = r'(\d+(?:\.\d+)*)'
        match = re.search(version_pattern, version_info)
        return match.group(1) if match else None
    
    def _extract_libraries_from_link_command(self, link_command: str) -> List[str]:
        """Extract library names from target_link_libraries command"""
        libraries = []
        
        # Remove the command name and parentheses
        content = re.sub(r'target_link_libraries\s*\(\s*[^\s]+\s*', '', link_command, flags=re.IGNORECASE)
        content = content.rstrip(')')
        
        # Split by whitespace and filter
        tokens = content.split()
        for token in tokens:
            token = token.strip()
            if token and not token.startswith(('${', '$<', 'PUBLIC', 'PRIVATE', 'INTERFACE')):
                libraries.append(token)
        
        return libraries
    
    def _infer_library_from_include(self, include_path: str) -> Optional[str]:
        """Infer library name from include path"""
        # Common library patterns
        library_patterns = {
            'boost/': 'boost',
            'opencv2/': 'opencv',
            'eigen3/': 'eigen',
            'fmt/': 'fmt',
            'spdlog/': 'spdlog',
            'curl/': 'curl',
            'json/': 'nlohmann-json',
            'rapidjson/': 'rapidjson'
        }
        
        for pattern, lib_name in library_patterns.items():
            if include_path.startswith(pattern):
                return lib_name
        
        # Try to extract first directory as library name
        if '/' in include_path:
            return include_path.split('/')[0]
        
        return None
    
    def _deduplicate_components(self, components: List[Component]) -> List[Component]:
        """Remove duplicate components based on name"""
        seen = set()
        unique_components = []
        
        for component in components:
            key = component.name.lower()
            if key not in seen:
                seen.add(key)
                unique_components.append(component)
        
        return unique_components