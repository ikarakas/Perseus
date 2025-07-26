# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Database models for Perseus platform
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import uuid

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Float, 
    Text, JSON, ForeignKey, Table, Enum as SQLEnum,
    UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from .connection import Base


# Enums
class AnalysisStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ComponentType(enum.Enum):
    LIBRARY = "library"
    APPLICATION = "application"
    CONTAINER = "container"
    OPERATING_SYSTEM = "operating-system"
    DEVICE = "device"
    FIRMWARE = "firmware"
    FILE = "file"
    FRAMEWORK = "framework"


class VulnerabilitySeverity(enum.Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ScannerType(enum.Enum):
    GRYPE = "grype"
    OSV = "osv"
    OFFLINE = "offline"


# Association tables
component_vulnerabilities = Table(
    'component_vulnerabilities',
    Base.metadata,
    Column('component_id', UUID(as_uuid=True), ForeignKey('components.id', ondelete='CASCADE')),
    Column('vulnerability_id', UUID(as_uuid=True), ForeignKey('vulnerabilities.id', ondelete='CASCADE')),
    UniqueConstraint('component_id', 'vulnerability_id', name='uq_component_vulnerability')
)

component_licenses = Table(
    'component_licenses',
    Base.metadata,
    Column('component_id', UUID(as_uuid=True), ForeignKey('components.id', ondelete='CASCADE')),
    Column('license_id', UUID(as_uuid=True), ForeignKey('licenses.id', ondelete='CASCADE')),
    UniqueConstraint('component_id', 'license_id', name='uq_component_license')
)


class TimestampMixin:
    """Mixin for adding timestamp fields"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Analysis(Base, TimestampMixin):
    """Analysis entity representing a scan/analysis job"""
    __tablename__ = 'analyses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Analysis details
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    analysis_type = Column(String(50), nullable=False)  # source, binary, docker, os
    language = Column(String(50))  # For source analysis
    location = Column(String(1024), nullable=False)  # Path, URL, or image name
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Results
    component_count = Column(Integer, default=0)
    vulnerability_count = Column(Integer, default=0)
    critical_vulnerability_count = Column(Integer, default=0)
    high_vulnerability_count = Column(Integer, default=0)
    
    # Metadata
    analysis_metadata = Column(JSONB, default={})
    errors = Column(JSONB, default=[])
    
    # Relationships
    components = relationship("Component", back_populates="analysis", cascade="all, delete-orphan")
    sboms = relationship("SBOM", back_populates="analysis", cascade="all, delete-orphan")
    vulnerability_scans = relationship("VulnerabilityScan", back_populates="analysis", cascade="all, delete-orphan")
    build = relationship("Build", back_populates="analysis", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_status', 'status'),
        Index('idx_analysis_created_at', 'created_at'),
    )


class Component(Base, TimestampMixin):
    """Component entity representing a software component/dependency"""
    __tablename__ = 'components'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Component identification
    name = Column(String(512), nullable=False, index=True)
    version = Column(String(255), nullable=False)
    purl = Column(String(1024), index=True)  # Package URL
    cpe = Column(String(512))  # Common Platform Enumeration
    
    # Component details
    type = Column(SQLEnum(ComponentType), default=ComponentType.LIBRARY)
    description = Column(Text)
    author = Column(String(255))
    publisher = Column(String(255))
    
    # Source information
    source_location = Column(String(1024))
    download_location = Column(String(1024))
    home_page = Column(String(1024))
    
    # Hashes
    sha256 = Column(String(64))
    sha1 = Column(String(40))
    md5 = Column(String(32))
    
    # Vulnerability summary
    vulnerability_count = Column(Integer, default=0)
    critical_vulnerabilities = Column(Integer, default=0)
    high_vulnerabilities = Column(Integer, default=0)
    
    # Metadata
    component_metadata = Column(JSONB, default={})
    syft_metadata = Column(JSONB, default={})
    
    # Foreign keys
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="components")
    vulnerabilities = relationship("Vulnerability", secondary=component_vulnerabilities, back_populates="components")
    licenses = relationship("License", secondary=component_licenses, back_populates="components")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('analysis_id', 'name', 'version', 'type', name='uq_component_identity'),
        Index('idx_component_name_version', 'name', 'version'),
        Index('idx_component_purl', 'purl'),
    )
    
    @validates('sha256', 'sha1', 'md5')
    def validate_hash(self, key, value):
        """Validate hash formats"""
        if value:
            value = value.lower()
            if key == 'sha256' and len(value) != 64:
                raise ValueError(f"Invalid SHA256 hash length: {len(value)}")
            elif key == 'sha1' and len(value) != 40:
                raise ValueError(f"Invalid SHA1 hash length: {len(value)}")
            elif key == 'md5' and len(value) != 32:
                raise ValueError(f"Invalid MD5 hash length: {len(value)}")
        return value


class Vulnerability(Base, TimestampMixin):
    """Vulnerability entity"""
    __tablename__ = 'vulnerabilities'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Vulnerability identification
    vulnerability_id = Column(String(255), unique=True, nullable=False, index=True)  # CVE-YYYY-NNNNN, GHSA-xxxx
    source = Column(String(50), nullable=False)  # NVD, GitHub, OSV, etc.
    
    # Details
    title = Column(String(512))
    description = Column(Text)
    severity = Column(SQLEnum(VulnerabilitySeverity), default=VulnerabilitySeverity.UNKNOWN)
    
    # Scoring
    cvss_score = Column(Float, CheckConstraint('cvss_score >= 0 AND cvss_score <= 10'))
    cvss_vector = Column(String(255))
    epss_score = Column(Float, CheckConstraint('epss_score >= 0 AND epss_score <= 1'))
    
    # Dates
    published_date = Column(DateTime)
    modified_date = Column(DateTime)
    
    # References
    references = Column(JSONB, default=[])
    cwe_ids = Column(JSONB, default=[])
    
    # Affected versions and fixes
    affected_versions = Column(JSONB, default=[])
    fixed_versions = Column(JSONB, default=[])
    
    # Metadata
    vulnerability_metadata = Column(JSONB, default={})
    
    # Relationships
    components = relationship("Component", secondary=component_vulnerabilities, back_populates="vulnerabilities")
    
    # Indexes
    __table_args__ = (
        Index('idx_vulnerability_severity', 'severity'),
        Index('idx_vulnerability_cvss', 'cvss_score'),
    )


class License(Base, TimestampMixin):
    """License entity"""
    __tablename__ = 'licenses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # License identification
    spdx_id = Column(String(255), unique=True, index=True)
    name = Column(String(512), nullable=False)
    
    # License details
    is_osi_approved = Column(Boolean, default=False)
    is_fsf_libre = Column(Boolean, default=False)
    is_deprecated = Column(Boolean, default=False)
    
    # URLs
    reference_url = Column(String(1024))
    details_url = Column(String(1024))
    
    # Text
    license_text = Column(Text)
    
    # Metadata
    license_metadata = Column(JSONB, default={})
    
    # Relationships
    components = relationship("Component", secondary=component_licenses, back_populates="licenses")


class SBOM(Base, TimestampMixin):
    """SBOM entity for storing generated SBOMs"""
    __tablename__ = 'sboms'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sbom_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # SBOM details
    format = Column(String(50), nullable=False)  # spdx, cyclonedx, swid
    spec_version = Column(String(50))
    
    # Content
    content = Column(JSONB, nullable=False)
    
    # Metadata
    name = Column(String(512))
    namespace = Column(String(512))
    created_by = Column(String(255))
    component_count = Column(Integer, default=0)
    file_path = Column(String(1024))
    
    # Foreign keys
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="sboms")
    
    # Indexes
    __table_args__ = (
        Index('idx_sbom_format', 'format'),
    )


class VulnerabilityScan(Base, TimestampMixin):
    """Vulnerability scan results"""
    __tablename__ = 'vulnerability_scans'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Scan details
    scanner = Column(SQLEnum(ScannerType), nullable=False)
    scanner_version = Column(String(50))
    database_version = Column(String(50))
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Results summary
    total_vulnerabilities = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    
    # Raw results
    raw_results = Column(JSONB, default={})
    
    # Foreign keys
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="vulnerability_scans")


class Agent(Base, TimestampMixin):
    """Remote agent entity"""
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Agent details
    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    platform = Column(String(50))
    architecture = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime)
    registration_date = Column(DateTime, default=datetime.utcnow)
    
    # Capabilities
    capabilities = Column(JSONB, default=[])
    
    # Metadata
    agent_metadata = Column(JSONB, default={})
    
    # Relationships
    telemetry_data = relationship("TelemetryData", back_populates="agent", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_active', 'is_active'),
        Index('idx_agent_heartbeat', 'last_heartbeat'),
    )


class TelemetryData(Base, TimestampMixin):
    """Telemetry data from agents"""
    __tablename__ = 'telemetry_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Telemetry details
    message_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Data
    data = Column(JSONB, nullable=False)
    
    # Foreign keys
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="telemetry_data")
    
    # Indexes
    __table_args__ = (
        Index('idx_telemetry_type_timestamp', 'message_type', 'timestamp'),
    )


class Build(Base, TimestampMixin):
    """CI/CD build entity"""
    __tablename__ = 'builds'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    build_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Project information
    project_name = Column(String(255), nullable=False)
    project_path = Column(String(1024))
    project_type = Column(String(50))
    branch = Column(String(255))
    commit_sha = Column(String(40))
    version = Column(String(50))
    
    # CI/CD context
    ci_platform = Column(String(50))  # jenkins, gitlab, github-actions
    ci_job_name = Column(String(255))
    ci_job_url = Column(String(1024))
    
    # Status
    status = Column(String(50), default="registered")
    
    # Metadata
    build_metadata = Column(JSONB, default={})
    
    # Foreign keys
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id', ondelete='SET NULL'))
    
    # Relationships
    analysis = relationship("Analysis", back_populates="build")
    
    # Indexes
    __table_args__ = (
        Index('idx_build_project', 'project_name'),
        Index('idx_build_status', 'status'),
    )