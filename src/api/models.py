# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class AnalysisType(str, Enum):
    SOURCE = "source"
    BINARY = "binary"
    DOCKER = "docker"
    OS = "os"

class Language(str, Enum):
    CPP = "c++"
    JAVA = "java"
    C = "c"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    TYPESCRIPT = "typescript"
    KOTLIN = "kotlin"
    SWIFT = "swift"

class SBOMFormat(str, Enum):
    SPDX = "spdx"
    CYCLONEDX = "cyclonedx"
    SWID = "swid"

class AnalysisOptions(BaseModel):
    deep_scan: bool = Field(default=True, description="Perform deep dependency analysis")
    include_dev_dependencies: bool = Field(default=False, description="Include development dependencies")
    timeout_minutes: int = Field(default=30, description="Analysis timeout in minutes")
    docker_auth: Optional[Dict[str, str]] = Field(default=None, description="Docker registry authentication")
    include_vulnerabilities: bool = Field(default=True, description="Include vulnerability scanning")

class AnalysisRequest(BaseModel):
    type: AnalysisType = Field(description="Type of analysis to perform")
    language: Optional[Language] = Field(default=None, description="Programming language (for source analysis)")
    location: str = Field(description="Source location (file://, git://, s3://, docker:, registry://)")
    options: Optional[AnalysisOptions] = Field(default_factory=AnalysisOptions)

class AnalysisResponse(BaseModel):
    analysis_id: str = Field(description="Unique analysis identifier")
    status: str = Field(description="Analysis status")
    message: str = Field(description="Status message")

class SBOMRequest(BaseModel):
    analysis_ids: List[str] = Field(description="List of analysis IDs to include in SBOM")
    format: SBOMFormat = Field(description="SBOM output format")
    include_licenses: bool = Field(default=True, description="Include license information")
    include_vulnerabilities: bool = Field(default=True, description="Include vulnerability data")

class Component(BaseModel):
    name: str = Field(description="Component name")
    version: Optional[str] = Field(default=None, description="Component version")
    type: Optional[str] = Field(default=None, description="Component type (library, application, etc.)")
    purl: Optional[str] = Field(default=None, description="Package URL identifier")
    license: Optional[str] = Field(default=None, description="Single license information (legacy)")
    licenses: Optional[List[str]] = Field(default=None, description="Multiple license information")
    hashes: Optional[Dict[str, str]] = Field(default=None, description="File hashes")
    source_location: Optional[str] = Field(default=None, description="Source location")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional component metadata")
    vulnerability_count: Optional[int] = Field(default=None, description="Number of vulnerabilities found")
    critical_vulnerabilities: Optional[int] = Field(default=None, description="Number of critical vulnerabilities")
    high_vulnerabilities: Optional[int] = Field(default=None, description="Number of high severity vulnerabilities")

class AnalysisResult(BaseModel):
    analysis_id: str = Field(description="Analysis identifier")
    status: str = Field(description="Analysis status")
    components: List[Component] = Field(description="Identified components")
    errors: List[str] = Field(default_factory=list, description="Analysis errors")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    vulnerability_summary: Optional[Dict[str, Any]] = Field(default=None, description="Vulnerability scan summary")