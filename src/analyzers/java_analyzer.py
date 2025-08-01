# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Java source code analyzer
"""

import os
import re
import xml.etree.ElementTree as ET
import json
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from .base import BaseAnalyzer
from ..api.models import AnalysisOptions, AnalysisResult, Component

logger = logging.getLogger(__name__)

class JavaSourceAnalyzer(BaseAnalyzer):
    """Analyzer for Java source code - supports Maven POM and Gradle build files"""
    
    async def analyze(self, location: str, options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        """Analyze Java source code"""
        try:
            components = []
            errors = []
            
            # Parse location
            source_path = self._parse_location(location)
            
            # Find build files
            build_files = self._find_build_files(source_path)
            
            # Analyze Maven pom.xml files
            maven_components = []
            for pom_file in build_files.get('maven', []):
                maven_components.extend(self._analyze_maven_pom(pom_file))
            components.extend(maven_components)
            
            # Analyze Gradle build files
            gradle_components = []
            for gradle_file in build_files.get('gradle', []):
                gradle_components.extend(self._analyze_gradle_build(gradle_file))
            components.extend(gradle_components)
            
            # Note: Java import analysis removed for simplicity
            
            # Analyze JAR files if present
            jar_files = self._find_jar_files(source_path)
            jar_components = self._analyze_jar_files(jar_files)
            components.extend(jar_components)
            
            # Remove duplicates
            unique_components = self._deduplicate_components(components)
            
            return AnalysisResult(
                analysis_id="",  # Will be set by workflow
                status="completed",
                components=unique_components,
                errors=errors,
                metadata={
                    "build_files_found": sum(len(files) for files in build_files.values()),
                    "jar_files_found": len(jar_files),
                    "analyzer_type": "java_source"
                }
            )
            
        except Exception as e:
            logger.error(f"Java analysis failed: {e}")
            return AnalysisResult(
                analysis_id="",
                status="failed",
                components=[],
                errors=[str(e)],
                metadata={"analyzer_type": "java_source"}
            )
    
    # Note: _parse_location is now inherited from BaseAnalyzer with improved path normalization
    
    def _find_build_files(self, source_path: str) -> Dict[str, List[str]]:
        """Find Java build configuration files"""
        build_files = {'maven': [], 'gradle': []}
        
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                if file.lower() == 'pom.xml':
                    build_files['maven'].append(file_path)
                elif file.lower() in ['build.gradle', 'build.gradle.kts']:
                    build_files['gradle'].append(file_path)
        
        return build_files
    
    
    def _find_jar_files(self, source_path: str) -> List[str]:
        """Find JAR files"""
        jar_files = []
        
        for root, dirs, files in os.walk(source_path):
            for file in files:
                if file.endswith('.jar'):
                    jar_files.append(os.path.join(root, file))
        
        return jar_files
    
    def _analyze_maven_pom(self, pom_file: str) -> List[Component]:
        """Analyze Maven pom.xml for dependencies"""
        components = []
        
        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()
            
            # Handle namespace
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            if root.tag.startswith('{'):
                namespace_uri = root.tag[1:root.tag.index('}')]
                namespace = {'maven': namespace_uri}
            
            # Find dependencies
            dependencies = root.findall('.//maven:dependency', namespace)
            if not dependencies:  # Try without namespace
                dependencies = root.findall('.//dependency')
            
            for dep in dependencies:
                group_id = self._get_element_text(dep, 'groupId', namespace)
                artifact_id = self._get_element_text(dep, 'artifactId', namespace)
                version = self._get_element_text(dep, 'version', namespace)
                scope = self._get_element_text(dep, 'scope', namespace)
                
                if group_id and artifact_id:
                    # Skip test dependencies if not requested
                    if scope == 'test':
                        continue
                    
                    name = f"{group_id}:{artifact_id}"
                    purl = f"pkg:maven/{group_id}/{artifact_id}"
                    if version:
                        purl += f"@{version}"
                    
                    component = self._create_component(
                        name=name,
                        version=self._parse_version(version) if version else None,
                        purl=purl,
                        source_location=pom_file
                    )
                    components.append(component)
            
            # Find parent dependencies
            parent = root.find('maven:parent', namespace) or root.find('parent')
            if parent is not None:
                parent_group_id = self._get_element_text(parent, 'groupId', namespace)
                parent_artifact_id = self._get_element_text(parent, 'artifactId', namespace)
                parent_version = self._get_element_text(parent, 'version', namespace)
                
                if parent_group_id and parent_artifact_id:
                    name = f"{parent_group_id}:{parent_artifact_id}"
                    purl = f"pkg:maven/{parent_group_id}/{parent_artifact_id}"
                    if parent_version:
                        purl += f"@{parent_version}"
                    
                    component = self._create_component(
                        name=name,
                        version=self._parse_version(parent_version) if parent_version else None,
                        purl=purl,
                        source_location=pom_file
                    )
                    components.append(component)
                    
        except Exception as e:
            logger.warning(f"Failed to parse Maven POM {pom_file}: {e}")
        
        return components
    
    def _analyze_gradle_build(self, gradle_file: str) -> List[Component]:
        """Analyze Gradle build file for dependencies"""
        components = []
        
        try:
            with open(gradle_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find dependency declarations
            # Match various Gradle dependency formats
            patterns = [
                r'implementation\s+[\'"]([^:]+):([^:]+):([^\'"]+)[\'"]',
                r'compile\s+[\'"]([^:]+):([^:]+):([^\'"]+)[\'"]',
                r'api\s+[\'"]([^:]+):([^:]+):([^\'"]+)[\'"]',
                r'runtimeOnly\s+[\'"]([^:]+):([^:]+):([^\'"]+)[\'"]',
                r'testImplementation\s+[\'"]([^:]+):([^:]+):([^\'"]+)[\'"]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    group_id, artifact_id, version = match
                    
                    # Skip test dependencies for testImplementation
                    if 'test' in pattern.lower():
                        continue
                    
                    name = f"{group_id}:{artifact_id}"
                    purl = f"pkg:maven/{group_id}/{artifact_id}@{version}"
                    
                    component = self._create_component(
                        name=name,
                        version=self._parse_version(version),
                        purl=purl,
                        source_location=gradle_file
                    )
                    components.append(component)
            
            # Also look for dependency blocks
            dep_block_pattern = r'dependencies\s*\{([^}]+)\}'
            dep_blocks = re.findall(dep_block_pattern, content, re.DOTALL)
            
            for block in dep_blocks:
                # Extract individual dependency lines
                dep_lines = re.findall(r'(\w+)\s+[\'"]([^:]+):([^:]+):([^\'"]+)[\'"]', block)
                for dep_line in dep_lines:
                    config, group_id, artifact_id, version = dep_line
                    
                    if config.lower() in ['implementation', 'compile', 'api', 'runtimeonly']:
                        name = f"{group_id}:{artifact_id}"
                        purl = f"pkg:maven/{group_id}/{artifact_id}@{version}"
                        
                        component = self._create_component(
                            name=name,
                            version=self._parse_version(version),
                            purl=purl,
                            source_location=gradle_file
                        )
                        components.append(component)
                        
        except Exception as e:
            logger.warning(f"Failed to parse Gradle file {gradle_file}: {e}")
        
        return components
    
    
    def _analyze_jar_files(self, jar_files: List[str]) -> List[Component]:
        """Analyze JAR files for basic information"""
        components = []
        
        for jar_file in jar_files:
            try:
                # Extract basic info from JAR filename
                jar_name = os.path.basename(jar_file)
                
                # Try to parse version from filename
                name, version = self._parse_jar_filename(jar_name)
                
                component = self._create_component(
                    name=name,
                    version=version,
                    source_location=jar_file
                )
                components.append(component)
                
            except Exception as e:
                logger.warning(f"Failed to analyze JAR file {jar_file}: {e}")
        
        return components
    
    def _get_element_text(self, parent, tag_name: str, namespace: Dict[str, str]) -> Optional[str]:
        """Get text content of XML element with namespace support"""
        element = parent.find(f"maven:{tag_name}", namespace)
        if element is None:
            element = parent.find(tag_name)
        
        return element.text.strip() if element is not None and element.text else None
    
    
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