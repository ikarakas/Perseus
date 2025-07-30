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
from ..common.version import version_config

logger = logging.getLogger(__name__)

class SBOMGenerator:
    """Generator for creating SBOMs in multiple formats"""
    
    def __init__(self):
        self.tool_name = "Perseus"
        self.tool_version = version_config.get_version_string()
        self.author = "Ilker Karakas"
    
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
                      include_vulnerabilities: bool = True,
                      analysis_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate SBOM in specified format with source/target metadata"""
        try:
            if format == SBOMFormat.SPDX:
                return self._generate_spdx(analysis_results, include_licenses, include_vulnerabilities, analysis_metadata)
            elif format == SBOMFormat.CYCLONEDX:
                return self._generate_cyclonedx(analysis_results, include_licenses, include_vulnerabilities, analysis_metadata)
            elif format == SBOMFormat.SWID:
                return self._generate_swid(analysis_results, include_licenses, analysis_metadata)
            else:
                raise ValueError(f"Unsupported SBOM format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to generate SBOM: {e}")
            raise
    
    def _generate_spdx(self, analysis_results: List[AnalysisResult], 
                      include_licenses: bool, include_vulnerabilities: bool,
                      analysis_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
                external_refs = []
                if component.purl:
                    external_refs.append({
                        "referenceCategory": "PACKAGE_MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": component.purl
                    })
                
                # Add vulnerability information if requested and available
                if include_vulnerabilities and hasattr(component, 'vulnerability_count') and component.vulnerability_count > 0:
                    # Add vulnerability count as annotation
                    package["annotations"] = [{
                        "annotationType": "REVIEW",
                        "annotator": f"Tool: {self.tool_name}",
                        "annotationDate": datetime.utcnow().isoformat() + "Z",
                        "annotationComment": f"Vulnerabilities found: {component.vulnerability_count} total"
                    }]
                    
                    # Add severity breakdown if available
                    vuln_details = []
                    if hasattr(component, 'critical_vulnerabilities') and component.critical_vulnerabilities:
                        vuln_details.append(f"{component.critical_vulnerabilities} critical")
                    if hasattr(component, 'high_vulnerabilities') and component.high_vulnerabilities:
                        vuln_details.append(f"{component.high_vulnerabilities} high")
                    if hasattr(component, 'medium_vulnerabilities') and component.medium_vulnerabilities:
                        vuln_details.append(f"{component.medium_vulnerabilities} medium")
                    if hasattr(component, 'low_vulnerabilities') and component.low_vulnerabilities:
                        vuln_details.append(f"{component.low_vulnerabilities} low")
                    
                    if vuln_details:
                        package["annotations"][0]["annotationComment"] += f" ({', '.join(vuln_details)})"
                    
                    # Add vulnerability external reference for security scanning
                    external_refs.append({
                        "referenceCategory": "SECURITY",
                        "referenceType": "advisory",
                        "referenceLocator": f"vulnerability-scan:{component.vulnerability_count}-found"
                    })
                
                if external_refs:
                    package["externalRefs"] = external_refs
                
                # Add analyzer info
                package["supplier"] = f"Tool: {analyzer_info}"
                
                if component.hashes:
                    package["checksums"] = [
                        {"algorithm": hash_type.upper(), "checksumValue": hash_value}
                        for hash_type, hash_value in component.hashes.items()
                    ]
                
                packages.append(package)
        
        spdx_doc = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": document_name,
            "documentNamespace": document_namespace,
            "creationInfo": {
                "created": datetime.utcnow().isoformat() + "Z",
                "creators": [
                    f"Tool: {self.tool_name}-{self.tool_version}",
                    f"Person: {self.author}"
                ]
            },
            "packages": packages
        }
        
        # Add analysis source/target information
        if analysis_metadata:
            spdx_doc["documentDescribes"] = []
            spdx_doc["externalDocumentRefs"] = []
            
            # Add source/target information as document comment
            source_info = []
            if analysis_metadata.get("location"):
                source_info.append(f"Analysis Target: {analysis_metadata['location']}")
            if analysis_metadata.get("analysis_type"):
                source_info.append(f"Analysis Type: {analysis_metadata['analysis_type']}")
            if analysis_metadata.get("analysis_id"):
                source_info.append(f"Analysis ID: {analysis_metadata['analysis_id']}")
            if analysis_metadata.get("source_metadata"):
                for key, value in analysis_metadata["source_metadata"].items():
                    if key != "workflow_version":  # Exclude workflow version
                        source_info.append(f"{key}: {value}")
            
            if source_info:
                spdx_doc["comment"] = "\n".join(source_info)
        
        return spdx_doc
    
    def _generate_cyclonedx(self, analysis_results: List[AnalysisResult], 
                           include_licenses: bool, include_vulnerabilities: bool,
                           analysis_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        
        cyclonedx_doc = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tools": [{
                    "vendor": "NATO AWACS",
                    "name": self.tool_name,
                    "version": self.tool_version,
                    "author": self.author
                }]
            },
            "components": components
        }
        
        # Add analysis source/target information to metadata
        if analysis_metadata:
            # Add component representing the analyzed target
            target_component = {
                "type": "application",
                "bom-ref": f"target:{analysis_metadata.get('analysis_id', 'unknown')}",
                "name": analysis_metadata.get("location", "Unknown Target"),
                "version": "unknown"
            }
            
            # Add properties with analysis details
            properties = []
            if analysis_metadata.get("analysis_type"):
                properties.append({
                    "name": "sbom:analysis_type",
                    "value": analysis_metadata["analysis_type"]
                })
            if analysis_metadata.get("analysis_id"):
                properties.append({
                    "name": "sbom:analysis_id", 
                    "value": analysis_metadata["analysis_id"]
                })
            if analysis_metadata.get("location"):
                properties.append({
                    "name": "sbom:target_location",
                    "value": analysis_metadata["location"]
                })
            
            # Add source metadata as properties
            if analysis_metadata.get("source_metadata"):
                for key, value in analysis_metadata["source_metadata"].items():
                    if key != "workflow_version":  # Exclude workflow version
                        properties.append({
                            "name": f"sbom:source_{key}",
                            "value": str(value)
                        })
            
            if properties:
                target_component["properties"] = properties
            
            cyclonedx_doc["metadata"]["component"] = target_component
        
        return cyclonedx_doc
    
    def _generate_swid(self, analysis_results: List[AnalysisResult], 
                      include_licenses: bool,
                      analysis_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate SWID tag format SBOM"""
        # Generate unique name based on analysis target
        sbom_name = f"SBOM-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        if analysis_metadata and analysis_metadata.get("location"):
            # Extract filename or last part of path for better naming
            target_name = analysis_metadata["location"].split('/')[-1]
            sbom_name = f"SBOM-{target_name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        swid_tag = {
            "SoftwareIdentity": {
                "@name": sbom_name,
                "@tagId": str(uuid.uuid4()),
                "@version": "1.6.0",
                "@xmlns": "http://standards.iso.org/iso/19770/-2/2015/schema.xsd",
                "@versionScheme": "multipartnumeric",
                "@corpus": "false",
                "@patch": "false",
                "@supplemental": "false",
                "Entity": {
                    "@name": f"{self.tool_name} ({self.author})",
                    "@role": "tagCreator softwareCreator",
                    "@thumbprint": f"generated-at-{datetime.utcnow().isoformat()}Z"
                },
                "Payload": {
                    "Resource": []
                }
            }
        }
        
        # Add comprehensive analysis metadata as additional Entity elements
        if analysis_metadata:
            entities = [swid_tag["SoftwareIdentity"]["Entity"]]
            
            if analysis_metadata.get("location"):
                entities.append({
                    "@name": f"Analysis Target: {analysis_metadata['location']}",
                    "@role": "aggregator"
                })
            
            if analysis_metadata.get("analysis_type"):
                entities.append({
                    "@name": f"Analysis Type: {analysis_metadata['analysis_type']}",
                    "@role": "distributor"
                })
            
            if analysis_metadata.get("analysis_id"):
                entities.append({
                    "@name": f"Analysis ID: {analysis_metadata['analysis_id']}",
                    "@role": "licensor"
                })
            
            # Add metadata as Meta elements for better structure
            meta_elements = []
            
            # Add all source metadata
            if analysis_metadata.get("source_metadata"):
                for key, value in analysis_metadata["source_metadata"].items():
                    if key != "workflow_version":  # Exclude workflow version
                        meta_elements.append({
                            "@key": f"sbom:{key}",
                            "@value": str(value)
                        })
            
            if meta_elements:
                swid_tag["SoftwareIdentity"]["Meta"] = meta_elements
            
            swid_tag["SoftwareIdentity"]["Entity"] = entities
        
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