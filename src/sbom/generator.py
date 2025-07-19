# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
SBOM generator supporting multiple formats (SPDX, CycloneDX, SWID)
"""

import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
# SBOM generation using native format creation (powered by Syft analysis)
import yaml

from ..api.models import AnalysisResult, SBOMFormat

logger = logging.getLogger(__name__)

class SBOMGenerator:
    """Generator for creating SBOMs in multiple formats"""
    
    def __init__(self):
        self.tool_name = "SBOM Generation Platform"
        self.tool_version = "1.3.1"
    
    def _map_component_type(self, syft_type: str) -> str:
        """Map Syft component type to CycloneDX component type"""
        type_mapping = {
            'java-archive': 'library',
            'java': 'library',
            'npm': 'library',
            'python': 'library',
            'gem': 'library',
            'go-module': 'library',
            'deb': 'library',
            'rpm': 'library',
            'apk': 'library',
            'conan': 'library',
            'binary': 'library',
            'application': 'application',
            'framework': 'framework',
            'library': 'library',
            'container': 'container',
            'file': 'file'
        }
        return type_mapping.get(syft_type.lower(), 'library')
    
    async def generate(self, analysis_results: List[AnalysisResult], 
                      format: SBOMFormat, include_licenses: bool = True,
                      include_vulnerabilities: bool = True) -> Dict[str, Any]:
        """Generate SBOM in specified format"""
        try:
            if format == SBOMFormat.SPDX:
                return self._generate_spdx(analysis_results, include_licenses)
            elif format == SBOMFormat.CYCLONEDX:
                return self._generate_cyclonedx(analysis_results, include_licenses, include_vulnerabilities)
            elif format == SBOMFormat.SWID:
                return self._generate_swid(analysis_results, include_licenses)
            else:
                raise ValueError(f"Unsupported SBOM format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to generate SBOM: {e}")
            raise
    
    def _generate_spdx(self, analysis_results: List[AnalysisResult], 
                      include_licenses: bool) -> Dict[str, Any]:
        """Generate SPDX 2.3 format SBOM"""
        document_name = f"SBOM-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        document_namespace = f"https://sbom-platform.local/{document_name}"
        
        packages = []
        for result in analysis_results:
            analyzer_info = result.metadata.get('analyzer', 'unknown')
            
            for i, component in enumerate(result.components):
                package = {
                    "SPDXID": f"SPDXRef-Package-{len(packages)}",
                    "name": component.name,
                    "version": component.version or "NOASSERTION",
                    "downloadLocation": component.source_location or "NOASSERTION",
                    "filesAnalyzed": False,
                    "copyrightText": "NOASSERTION"
                }
                
                # Handle licenses from Syft (can be multiple)
                if include_licenses:
                    if hasattr(component, 'licenses') and component.licenses:
                        # Multiple licenses from Syft
                        if len(component.licenses) == 1:
                            package["licenseConcluded"] = component.licenses[0]
                        else:
                            package["licenseConcluded"] = f"({' AND '.join(component.licenses)})"
                    elif hasattr(component, 'license') and component.license:
                        # Single license (legacy)
                        package["licenseConcluded"] = component.license
                    else:
                        package["licenseConcluded"] = "NOASSERTION"
                else:
                    package["licenseConcluded"] = "NOASSERTION"
                
                # Add PURL as external reference if available
                if component.purl:
                    package["externalRefs"] = [{
                        "referenceCategory": "PACKAGE_MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": component.purl
                    }]
                
                # Add analyzer info
                package["supplier"] = f"Tool: {analyzer_info}"
                
                if component.hashes:
                    package["checksums"] = [
                        {"algorithm": hash_type.upper(), "checksumValue": hash_value}
                        for hash_type, hash_value in component.hashes.items()
                    ]
                
                packages.append(package)
        
        return {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": document_name,
            "documentNamespace": document_namespace,
            "creationInfo": {
                "created": datetime.utcnow().isoformat() + "Z",
                "creators": [f"Tool: {self.tool_name}-{self.tool_version}"]
            },
            "packages": packages
        }
    
    def _generate_cyclonedx(self, analysis_results: List[AnalysisResult], 
                           include_licenses: bool, include_vulnerabilities: bool) -> Dict[str, Any]:
        """Generate CycloneDX 1.5 format SBOM"""
        
        components = []
        for result in analysis_results:
            analyzer_info = result.metadata.get('analyzer', 'unknown')
            
            for component in result.components:
                # Map component type from Syft to CycloneDX
                comp_type = self._map_component_type(getattr(component, 'type', 'library'))
                
                comp_data = {
                    "type": comp_type,
                    "bom-ref": component.purl if component.purl else f"pkg:{component.name}@{component.version or 'unknown'}",
                    "name": component.name,
                    "version": component.version or "unknown"
                }
                
                if component.purl:
                    comp_data["purl"] = component.purl
                
                # Handle multiple licenses from Syft
                if include_licenses:
                    if hasattr(component, 'licenses') and component.licenses:
                        comp_data["licenses"] = [
                            {"license": {"name": license}} for license in component.licenses
                        ]
                    elif hasattr(component, 'license') and component.license:
                        comp_data["licenses"] = [{"license": {"name": component.license}}]
                
                if component.hashes:
                    comp_data["hashes"] = [
                        {"alg": hash_type.upper(), "content": hash_value}
                        for hash_type, hash_value in component.hashes.items()
                    ]
                
                # Add source location as external reference
                if component.source_location and component.source_location != 'unknown':
                    comp_data["externalReferences"] = [{
                        "type": "distribution",
                        "url": component.source_location
                    }]
                
                # Add Syft metadata if available
                if hasattr(component, 'metadata') and component.metadata:
                    syft_metadata = component.metadata.get('syft_metadata', {})
                    if syft_metadata:
                        comp_data["properties"] = [
                            {"name": f"syft:{key}", "value": str(value)}
                            for key, value in syft_metadata.items()
                            if value is not None
                        ]
                
                components.append(comp_data)
        
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tools": [{
                    "vendor": "SBOM Platform",
                    "name": self.tool_name,
                    "version": self.tool_version
                }]
            },
            "components": components
        }
    
    def _generate_swid(self, analysis_results: List[AnalysisResult], 
                      include_licenses: bool) -> Dict[str, Any]:
        """Generate SWID tag format SBOM"""
        swid_tag = {
            "SoftwareIdentity": {
                "@name": f"SBOM-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                "@tagId": str(uuid.uuid4()),
                "@version": "1.3.1",
                "@xmlns": "http://standards.iso.org/iso/19770/-2/2015/schema.xsd",
                "Entity": {
                    "@name": self.tool_name,
                    "@role": "tagCreator softwareCreator"
                },
                "Payload": {
                    "Resource": []
                }
            }
        }
        
        # Add components as resources
        resources = []
        for result in analysis_results:
            for component in result.components:
                resource = {
                    "@name": component.name,
                    "@version": component.version or "unknown"
                }
                
                if component.source_location:
                    resource["@location"] = component.source_location
                
                if include_licenses and component.license:
                    resource["@license"] = component.license
                
                if component.hashes:
                    resource["@hash"] = list(component.hashes.values())[0]  # Use first hash
                
                resources.append(resource)
        
        swid_tag["SoftwareIdentity"]["Payload"]["Resource"] = resources
        
        return swid_tag
    
    def _spdx_document_to_dict(self, document) -> Dict[str, Any]:
        """Convert SPDX document to dictionary format"""
        # This is a simplified conversion - in practice, you'd use the SPDX tools
        return {
            "spdxVersion": document.creation_info.spdx_version,
            "dataLicense": "CC0-1.0",
            "SPDXID": document.creation_info.spdx_id,
            "name": document.creation_info.name,
            "documentNamespace": document.creation_info.document_namespace,
            "creationInfo": {
                "created": document.creation_info.created.isoformat() + "Z",
                "creators": [f"Tool: {creator.name}" for creator in document.creation_info.creators]
            },
            "packages": [
                {
                    "SPDXID": package.spdx_id,
                    "name": package.name,
                    "version": package.version,
                    "downloadLocation": package.download_location,
                    "filesAnalyzed": package.files_analyzed,
                    "licenseConcluded": package.license_concluded,
                    "copyrightText": package.copyright_text,
                    "checksums": [
                        {
                            "algorithm": checksum.algorithm.name,
                            "checksumValue": checksum.value
                        } for checksum in getattr(package, 'checksums', [])
                    ]
                } for package in document.packages
            ]
        }
    
    def _determine_cyclonedx_type(self, component) -> str:
        """Determine CycloneDX component type based on component info"""
        if component.name.endswith('.jar') or ':' in component.name:
            return "library"
        elif 'lib' in component.name.lower():
            return "library"
        elif component.source_location and 'binary' in component.source_location:
            return "application"
        else:
            return "library"
    
    def validate(self, sbom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SBOM format and content"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "format": "unknown"
        }
        
        try:
            # Detect format
            if "spdxVersion" in sbom_data:
                validation_result["format"] = "spdx"
                validation_result.update(self._validate_spdx(sbom_data))
            elif "bomFormat" in sbom_data and sbom_data["bomFormat"] == "CycloneDX":
                validation_result["format"] = "cyclonedx"
                validation_result.update(self._validate_cyclonedx(sbom_data))
            elif "SoftwareIdentity" in sbom_data:
                validation_result["format"] = "swid"
                validation_result.update(self._validate_swid(sbom_data))
            else:
                validation_result["valid"] = False
                validation_result["errors"].append("Unknown SBOM format")
                
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_spdx(self, spdx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SPDX format"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["spdxVersion", "dataLicense", "SPDXID", "name", "documentNamespace"]
        for field in required_fields:
            if field not in spdx_data:
                errors.append(f"Missing required field: {field}")
        
        # Check SPDX version
        if "spdxVersion" in spdx_data and not spdx_data["spdxVersion"].startswith("SPDX-"):
            errors.append("Invalid SPDX version format")
        
        # Check packages
        if "packages" in spdx_data:
            for i, package in enumerate(spdx_data["packages"]):
                if "SPDXID" not in package:
                    errors.append(f"Package {i}: Missing SPDXID")
                if "name" not in package:
                    errors.append(f"Package {i}: Missing name")
        
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
    
    def _validate_cyclonedx(self, cyclonedx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CycloneDX format"""
        errors = []
        warnings = []
        
        # Check required fields
        if "bomFormat" not in cyclonedx_data:
            errors.append("Missing bomFormat field")
        elif cyclonedx_data["bomFormat"] != "CycloneDX":
            errors.append("Invalid bomFormat value")
        
        if "specVersion" not in cyclonedx_data:
            errors.append("Missing specVersion field")
        
        if "serialNumber" not in cyclonedx_data:
            errors.append("Missing serialNumber field")
        
        # Check components
        if "components" in cyclonedx_data:
            for i, component in enumerate(cyclonedx_data["components"]):
                if "type" not in component:
                    errors.append(f"Component {i}: Missing type")
                if "name" not in component:
                    errors.append(f"Component {i}: Missing name")
        
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
    
    def _validate_swid(self, swid_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SWID format"""
        errors = []
        warnings = []
        
        # Check SoftwareIdentity element
        if "SoftwareIdentity" not in swid_data:
            errors.append("Missing SoftwareIdentity element")
        else:
            sw_id = swid_data["SoftwareIdentity"]
            
            # Check required attributes
            required_attrs = ["@name", "@tagId"]
            for attr in required_attrs:
                if attr not in sw_id:
                    errors.append(f"Missing required attribute: {attr}")
            
            # Check Entity
            if "Entity" not in sw_id:
                warnings.append("Missing Entity element")
        
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}