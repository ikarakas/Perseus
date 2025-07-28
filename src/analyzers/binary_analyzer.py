# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Binary analyzer for C/C++ and Java binaries
"""

import os
import re
import subprocess
import json
import logging
import zipfile
import struct
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from .base import BaseAnalyzer
from ..api.models import AnalysisOptions, AnalysisResult, Component

logger = logging.getLogger(__name__)

class BinaryAnalyzer(BaseAnalyzer):
    """Analyzer for compiled binaries (C/C++, Java)"""
    
    def __init__(self):
        self.elf_magic = b'\x7fELF'
        self.jar_magic = b'PK\x03\x04'
        
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """Analyze binary files"""
        try:
            components = []
            errors = []
            
            # Parse location
            binary_path = self._parse_location(location)
            
            # Validate path exists
            if not os.path.exists(binary_path):
                error_msg = f"Path does not exist: {binary_path}"
                if location != binary_path:
                    error_msg += f" (normalized from: {location})"
                raise FileNotFoundError(error_msg)
            
            # Determine binary type
            if os.path.isfile(binary_path):
                binary_files = [binary_path]
            elif os.path.isdir(binary_path):
                binary_files = self._find_binary_files(binary_path)
                if not binary_files:
                    logger.warning(f"No binary files found in directory: {binary_path}")
            else:
                raise ValueError(f"Path is neither a file nor a directory: {binary_path}")
            
            for binary_file in binary_files:
                try:
                    binary_type = self._detect_binary_type(binary_file)
                    
                    if binary_type == 'elf':
                        elf_components = self._analyze_elf_binary(binary_file)
                        components.extend(elf_components)
                    elif binary_type == 'jar':
                        jar_components = self._analyze_jar_binary(binary_file)
                        components.extend(jar_components)
                    elif binary_type == 'war':
                        war_components = self._analyze_war_binary(binary_file)
                        components.extend(war_components)
                    elif binary_type == 'ear':
                        ear_components = self._analyze_ear_binary(binary_file)
                        components.extend(ear_components)
                    else:
                        logger.warning(f"Unknown binary type for {binary_file}")
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze binary {binary_file}: {e}")
                    errors.append(f"Failed to analyze {binary_file}: {str(e)}")
            
            # Remove duplicates
            unique_components = self._deduplicate_components(components)
            
            return AnalysisResult(
                analysis_id="",  # Will be set by workflow
                status="completed",
                components=unique_components,
                errors=errors,
                metadata={
                    "binary_files_analyzed": len(binary_files),
                    "analyzer_type": "binary"
                }
            )
            
        except Exception as e:
            logger.error(f"Binary analysis failed: {e}")
            return AnalysisResult(
                analysis_id="",
                status="failed",
                components=[],
                errors=[str(e)],
                metadata={"analyzer_type": "binary"}
            )
    
    # Note: _parse_location is now inherited from BaseAnalyzer with improved path normalization
    
    def _find_binary_files(self, directory: str) -> List[str]:
        """Find binary files in directory"""
        binary_files = []
        binary_extensions = {'.so', '.a', '.jar', '.war', '.ear'}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check by extension
                if any(file.endswith(ext) for ext in binary_extensions):
                    binary_files.append(file_path)
                # Check for ELF binaries without extension
                elif os.access(file_path, os.X_OK) and self._is_elf_file(file_path):
                    binary_files.append(file_path)
        
        return binary_files
    
    def _detect_binary_type(self, binary_file: str) -> str:
        """Detect the type of binary file"""
        try:
            with open(binary_file, 'rb') as f:
                magic = f.read(4)
                
                if magic == self.elf_magic:
                    return 'elf'
                elif magic == self.jar_magic:
                    # Check if it's a JAR, WAR, or EAR
                    if binary_file.endswith('.war'):
                        return 'war'
                    elif binary_file.endswith('.ear'):
                        return 'ear'
                    else:
                        return 'jar'
                        
        except Exception as e:
            logger.warning(f"Failed to detect binary type for {binary_file}: {e}")
        
        return 'unknown'
    
    def _is_elf_file(self, file_path: str) -> bool:
        """Check if file is an ELF binary"""
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                return magic == self.elf_magic
        except:
            return False
    
    def _analyze_elf_binary(self, elf_file: str) -> List[Component]:
        """Analyze ELF binary for shared library dependencies"""
        components = []
        
        try:
            # Use ldd to find shared library dependencies
            result = subprocess.run(
                ['ldd', elf_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                dependencies = self._parse_ldd_output(result.stdout)
                for dep in dependencies:
                    component = self._create_component(
                        name=dep['name'],
                        version=dep.get('version'),
                        source_location=dep.get('path', elf_file)
                    )
                    components.append(component)
            
            # Use readelf to get additional information
            readelf_components = self._analyze_with_readelf(elf_file)
            components.extend(readelf_components)
            
            # Use objdump for symbol analysis
            objdump_components = self._analyze_with_objdump(elf_file)
            components.extend(objdump_components)
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Analysis of {elf_file} timed out")
        except Exception as e:
            logger.warning(f"Failed to analyze ELF binary {elf_file}: {e}")
        
        return components
    
    def _analyze_jar_binary(self, jar_file: str) -> List[Component]:
        """Analyze JAR file for dependencies"""
        components = []
        
        try:
            with zipfile.ZipFile(jar_file, 'r') as jar:
                # Read MANIFEST.MF
                manifest_components = self._analyze_jar_manifest(jar, jar_file)
                components.extend(manifest_components)
                
                # Look for Maven metadata
                maven_components = self._analyze_jar_maven_metadata(jar, jar_file)
                components.extend(maven_components)
                
                # Analyze embedded JARs
                embedded_components = self._analyze_embedded_jars(jar, jar_file)
                components.extend(embedded_components)
                
        except Exception as e:
            logger.warning(f"Failed to analyze JAR file {jar_file}: {e}")
        
        return components
    
    def _analyze_war_binary(self, war_file: str) -> List[Component]:
        """Analyze WAR file for dependencies"""
        components = []
        
        try:
            with zipfile.ZipFile(war_file, 'r') as war:
                # Analyze WEB-INF/lib JARs
                lib_jars = [name for name in war.namelist() if name.startswith('WEB-INF/lib/') and name.endswith('.jar')]
                
                for jar_path in lib_jars:
                    jar_name = os.path.basename(jar_path)
                    name, version = self._parse_jar_filename(jar_name)
                    
                    component = self._create_component(
                        name=name,
                        version=version,
                        source_location=f"{war_file}:{jar_path}"
                    )
                    components.append(component)
                
                # Analyze manifest
                manifest_components = self._analyze_jar_manifest(war, war_file)
                components.extend(manifest_components)
                
        except Exception as e:
            logger.warning(f"Failed to analyze WAR file {war_file}: {e}")
        
        return components
    
    def _analyze_ear_binary(self, ear_file: str) -> List[Component]:
        """Analyze EAR file for dependencies"""
        components = []
        
        try:
            with zipfile.ZipFile(ear_file, 'r') as ear:
                # Find all JARs and WARs in the EAR
                archives = [name for name in ear.namelist() 
                           if name.endswith(('.jar', '.war'))]
                
                for archive_path in archives:
                    archive_name = os.path.basename(archive_path)
                    name, version = self._parse_jar_filename(archive_name)
                    
                    component = self._create_component(
                        name=name,
                        version=version,
                        source_location=f"{ear_file}:{archive_path}"
                    )
                    components.append(component)
                
        except Exception as e:
            logger.warning(f"Failed to analyze EAR file {ear_file}: {e}")
        
        return components
    
    def _parse_ldd_output(self, ldd_output: str) -> List[Dict[str, str]]:
        """Parse ldd output to extract library dependencies"""
        dependencies = []
        
        for line in ldd_output.split('\n'):
            line = line.strip()
            if not line or '=>' not in line:
                continue
            
            # Parse lines like: libssl.so.1.1 => /usr/lib/x86_64-linux-gnu/libssl.so.1.1 (0x...)
            parts = line.split('=>')
            if len(parts) >= 2:
                lib_name = parts[0].strip()
                lib_path = parts[1].split('(')[0].strip()
                
                # Extract version from library name
                version = self._extract_version_from_lib_name(lib_name)
                
                # Clean library name
                clean_name = self._clean_library_name(lib_name)
                
                dependencies.append({
                    'name': clean_name,
                    'version': version,
                    'path': lib_path
                })
        
        return dependencies
    
    def _analyze_with_readelf(self, elf_file: str) -> List[Component]:
        """Use readelf to analyze ELF binary"""
        components = []
        
        try:
            # Get dynamic section information
            result = subprocess.run(
                ['readelf', '-d', elf_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse NEEDED entries
                needed_libs = re.findall(r'NEEDED.*\[([^\]]+)\]', result.stdout)
                for lib in needed_libs:
                    clean_name = self._clean_library_name(lib)
                    version = self._extract_version_from_lib_name(lib)
                    
                    component = self._create_component(
                        name=clean_name,
                        version=version,
                        source_location=elf_file
                    )
                    components.append(component)
                    
        except subprocess.TimeoutExpired:
            logger.warning(f"readelf analysis of {elf_file} timed out")
        except Exception as e:
            logger.warning(f"readelf analysis failed for {elf_file}: {e}")
        
        return components
    
    def _analyze_with_objdump(self, elf_file: str) -> List[Component]:
        """Use objdump for symbol analysis"""
        components = []
        
        try:
            # Get dynamic symbol table
            result = subprocess.run(
                ['objdump', '-T', elf_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Look for library-specific symbols that might indicate dependencies
                library_symbols = self._extract_library_symbols(result.stdout)
                for lib_name in library_symbols:
                    component = self._create_component(
                        name=lib_name,
                        source_location=f"{elf_file}:symbols"
                    )
                    components.append(component)
                    
        except subprocess.TimeoutExpired:
            logger.warning(f"objdump analysis of {elf_file} timed out")
        except Exception as e:
            logger.warning(f"objdump analysis failed for {elf_file}: {e}")
        
        return components
    
    def _analyze_jar_manifest(self, jar: zipfile.ZipFile, jar_file: str) -> List[Component]:
        """Analyze JAR manifest for dependency information"""
        components = []
        
        try:
            manifest_data = jar.read('META-INF/MANIFEST.MF').decode('utf-8')
            
            # Look for Class-Path entries
            class_path_pattern = r'Class-Path:\s*([^\n\r]+(?:\n\s+[^\n\r]+)*)'
            match = re.search(class_path_pattern, manifest_data, re.MULTILINE)
            
            if match:
                class_path = match.group(1)
                # Remove line continuations
                class_path = re.sub(r'\n\s+', ' ', class_path)
                
                # Extract JAR names from classpath
                jar_names = re.findall(r'([^/\s]+\.jar)', class_path)
                for jar_name in jar_names:
                    name, version = self._parse_jar_filename(jar_name)
                    component = self._create_component(
                        name=name,
                        version=version,
                        source_location=f"{jar_file}:MANIFEST.MF"
                    )
                    components.append(component)
            
            # Look for other manifest attributes that might indicate dependencies
            bundle_pattern = r'Bundle-ClassPath:\s*([^\n\r]+)'
            bundle_match = re.search(bundle_pattern, manifest_data)
            if bundle_match:
                bundle_path = bundle_match.group(1)
                jar_names = re.findall(r'([^/,\s]+\.jar)', bundle_path)
                for jar_name in jar_names:
                    name, version = self._parse_jar_filename(jar_name)
                    component = self._create_component(
                        name=name,
                        version=version,
                        source_location=f"{jar_file}:MANIFEST.MF"
                    )
                    components.append(component)
                    
        except KeyError:
            # No manifest file
            pass
        except Exception as e:
            logger.warning(f"Failed to analyze manifest in {jar_file}: {e}")
        
        return components
    
    def _analyze_jar_maven_metadata(self, jar: zipfile.ZipFile, jar_file: str) -> List[Component]:
        """Analyze Maven metadata in JAR"""
        components = []
        
        try:
            # Look for Maven pom.xml files
            pom_files = [name for name in jar.namelist() 
                        if name.startswith('META-INF/maven/') and name.endswith('pom.xml')]
            
            for pom_file in pom_files:
                pom_content = jar.read(pom_file).decode('utf-8')
                # Extract basic artifact info from path
                path_parts = pom_file.split('/')
                if len(path_parts) >= 4:
                    group_id = path_parts[2]
                    artifact_id = path_parts[3]
                    
                    # Try to extract version from pom content
                    version_match = re.search(r'<version>([^<]+)</version>', pom_content)
                    version = version_match.group(1) if version_match else None
                    
                    name = f"{group_id}:{artifact_id}"
                    purl = f"pkg:maven/{group_id}/{artifact_id}"
                    if version:
                        purl += f"@{version}"
                    
                    component = self._create_component(
                        name=name,
                        version=version,
                        purl=purl,
                        source_location=f"{jar_file}:{pom_file}"
                    )
                    components.append(component)
                    
        except Exception as e:
            logger.warning(f"Failed to analyze Maven metadata in {jar_file}: {e}")
        
        return components
    
    def _analyze_embedded_jars(self, jar: zipfile.ZipFile, jar_file: str) -> List[Component]:
        """Analyze embedded JAR files"""
        components = []
        
        try:
            # Find embedded JARs
            embedded_jars = [name for name in jar.namelist() if name.endswith('.jar')]
            
            for embedded_jar in embedded_jars:
                jar_name = os.path.basename(embedded_jar)
                name, version = self._parse_jar_filename(jar_name)
                
                component = self._create_component(
                    name=name,
                    version=version,
                    source_location=f"{jar_file}:{embedded_jar}"
                )
                components.append(component)
                
        except Exception as e:
            logger.warning(f"Failed to analyze embedded JARs in {jar_file}: {e}")
        
        return components
    
    def _extract_version_from_lib_name(self, lib_name: str) -> Optional[str]:
        """Extract version from library name"""
        # Common patterns: libname.so.1.2.3, libname-1.2.3.so
        version_patterns = [
            r'\.so\.(\d+(?:\.\d+)*)',  # libname.so.1.2.3
            r'-(\d+(?:\.\d+)+)\.so',   # libname-1.2.3.so
            r'\.(\d+)$'                # libname.1
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, lib_name)
            if match:
                return match.group(1)
        
        return None
    
    def _clean_library_name(self, lib_name: str) -> str:
        """Clean library name by removing version and extension"""
        # Remove common prefixes and suffixes
        clean_name = lib_name
        
        # Remove lib prefix
        if clean_name.startswith('lib'):
            clean_name = clean_name[3:]
        
        # Remove version and extension
        clean_name = re.sub(r'\.so(\.\d+)*$', '', clean_name)
        clean_name = re.sub(r'-\d+(\.\d+)*\.so$', '', clean_name)
        clean_name = re.sub(r'\.\d+$', '', clean_name)
        
        return clean_name
    
    def _extract_library_symbols(self, objdump_output: str) -> Set[str]:
        """Extract library names from symbol analysis"""
        libraries = set()
        
        # Look for common library symbol patterns
        symbol_patterns = {
            'openssl': ['SSL_', 'EVP_', 'BIO_'],
            'zlib': ['deflate', 'inflate', 'gzip'],
            'curl': ['curl_', 'CURL'],
            'sqlite': ['sqlite3_'],
            'pcre': ['pcre_'],
            'boost': ['boost::']
        }
        
        for lib_name, patterns in symbol_patterns.items():
            for pattern in patterns:
                if pattern in objdump_output:
                    libraries.add(lib_name)
                    break
        
        return libraries
    
    def _parse_jar_filename(self, jar_name: str) -> tuple[str, Optional[str]]:
        """Parse JAR filename to extract name and version"""
        # Remove .jar extension
        base_name = jar_name[:-4] if jar_name.endswith('.jar') else jar_name
        
        # Common patterns: name-version.jar, name_version.jar
        version_patterns = [
            r'^(.+)-(\d+(?:\.\d+)*).*$',  # name-1.2.3
            r'^(.+)_(\d+(?:\.\d+)*).*$',  # name_1.2.3
            r'^(.+)-v(\d+(?:\.\d+)*).*$', # name-v1.2.3
        ]
        
        for pattern in version_patterns:
            match = re.match(pattern, base_name)
            if match:
                return match.group(1), match.group(2)
        
        # No version found
        return base_name, None
    
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