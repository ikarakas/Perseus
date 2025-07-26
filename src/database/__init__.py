# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Database package for Perseus platform
"""

from .config import db_config
from .connection import (
    init_database,
    get_engine,
    get_session,
    get_db,
    get_db_session,
    create_tables,
    drop_tables,
    test_connection,
    Base
)
from .models import (
    Analysis,
    Component,
    Vulnerability,
    License,
    SBOM,
    VulnerabilityScan,
    Agent,
    TelemetryData,
    Build,
    AnalysisStatus,
    ComponentType,
    VulnerabilitySeverity,
    ScannerType
)

__all__ = [
    # Config
    'db_config',
    
    # Connection
    'init_database',
    'get_engine',
    'get_session',
    'get_db',
    'get_db_session',
    'create_tables',
    'drop_tables',
    'test_connection',
    'Base',
    
    # Models
    'Analysis',
    'Component',
    'Vulnerability',
    'License',
    'SBOM',
    'VulnerabilityScan',
    'Agent',
    'TelemetryData',
    'Build',
    
    # Enums
    'AnalysisStatus',
    'ComponentType',
    'VulnerabilitySeverity',
    'ScannerType'
]