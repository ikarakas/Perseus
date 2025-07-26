# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Unit tests for database operations
"""

import pytest
import tempfile
import os
from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, init_database
from src.database.models import (
    Analysis, Component, Vulnerability, SBOM, Agent, TelemetryData,
    AnalysisStatus, ComponentType, VulnerabilitySeverity
)
from src.database.repositories import (
    AnalysisRepository, ComponentRepository, SBOMRepository,
    VulnerabilityRepository
)


@pytest.fixture
def db_session():
    """Create a test database session"""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_analysis(db_session):
    """Create a sample analysis for testing"""
    analysis = Analysis(
        analysis_id=str(uuid4()),
        status=AnalysisStatus.COMPLETED,
        analysis_type="source",
        language="java",
        location="/test/project",
        component_count=2,
        vulnerability_count=5,
        metadata={"test": "data"}
    )
    
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    
    return analysis


@pytest.fixture
def sample_component(db_session, sample_analysis):
    """Create a sample component for testing"""
    component = Component(
        name="test-library",
        version="1.0.0",
        type=ComponentType.LIBRARY,
        purl="pkg:maven/test/test-library@1.0.0",
        vulnerability_count=3,
        critical_vulnerabilities=1,
        high_vulnerabilities=2,
        analysis_id=sample_analysis.id
    )
    
    db_session.add(component)
    db_session.commit()
    db_session.refresh(component)
    
    return component


class TestAnalysisRepository:
    """Test AnalysisRepository operations"""
    
    def test_create_analysis(self, db_session):
        """Test creating an analysis"""
        repo = AnalysisRepository(db_session)
        
        analysis_data = {
            'analysis_id': str(uuid4()),
            'status': AnalysisStatus.PENDING,
            'analysis_type': 'docker',
            'location': 'nginx:latest',
            'metadata': {'image': 'nginx:latest'}
        }
        
        analysis = repo.create(**analysis_data)
        
        assert analysis.analysis_id == analysis_data['analysis_id']
        assert analysis.status == AnalysisStatus.PENDING
        assert analysis.analysis_type == 'docker'
        assert analysis.metadata['image'] == 'nginx:latest'
    
    def test_get_by_analysis_id(self, db_session, sample_analysis):
        """Test retrieving analysis by analysis_id"""
        repo = AnalysisRepository(db_session)
        
        found = repo.get_by_analysis_id(sample_analysis.analysis_id)
        
        assert found is not None
        assert found.id == sample_analysis.id
        assert found.analysis_type == "source"
    
    def test_get_by_status(self, db_session, sample_analysis):
        """Test filtering analyses by status"""
        repo = AnalysisRepository(db_session)
        
        completed = repo.get_by_status(AnalysisStatus.COMPLETED)
        
        assert len(completed) >= 1
        assert all(a.status == AnalysisStatus.COMPLETED for a in completed)
    
    def test_update_status(self, db_session, sample_analysis):
        """Test updating analysis status"""
        repo = AnalysisRepository(db_session)
        
        updated = repo.update_status(
            sample_analysis.analysis_id,
            AnalysisStatus.FAILED,
            errors=["Test error"]
        )
        
        assert updated is not None
        assert updated.status == AnalysisStatus.FAILED
        assert "Test error" in updated.errors
        assert updated.completed_at is not None
    
    def test_get_statistics(self, db_session, sample_analysis):
        """Test getting analysis statistics"""
        repo = AnalysisRepository(db_session)
        
        stats = repo.get_statistics(days=30)
        
        assert 'total_analyses' in stats
        assert 'status_breakdown' in stats
        assert 'type_breakdown' in stats
        assert 'success_rate' in stats
        assert stats['total_analyses'] >= 1


class TestComponentRepository:
    """Test ComponentRepository operations"""
    
    def test_create_component(self, db_session, sample_analysis):
        """Test creating a component"""
        repo = ComponentRepository(db_session)
        
        component_data = {
            'name': 'jackson-core',
            'version': '2.9.8',
            'type': ComponentType.LIBRARY,
            'purl': 'pkg:maven/jackson-core@2.9.8',
            'vulnerability_count': 10,
            'analysis_id': sample_analysis.id
        }
        
        component = repo.create(**component_data)
        
        assert component.name == 'jackson-core'
        assert component.version == '2.9.8'
        assert component.vulnerability_count == 10
        assert component.analysis_id == sample_analysis.id
    
    def test_search_components(self, db_session, sample_component):
        """Test searching components"""
        repo = ComponentRepository(db_session)
        
        results = repo.search_components("test")
        
        assert len(results) >= 1
        assert any(c.name == "test-library" for c in results)
    
    def test_get_vulnerable_components(self, db_session, sample_component):
        """Test getting vulnerable components"""
        repo = ComponentRepository(db_session)
        
        vulnerable = repo.get_vulnerable_components()
        
        assert len(vulnerable) >= 1
        assert all(c.vulnerability_count > 0 for c in vulnerable)
    
    def test_get_component_statistics(self, db_session, sample_component):
        """Test getting component statistics"""
        repo = ComponentRepository(db_session)
        
        stats = repo.get_component_statistics()
        
        assert 'total_components' in stats
        assert 'unique_components' in stats
        assert 'vulnerable_components' in stats
        assert 'vulnerability_rate' in stats
        assert stats['total_components'] >= 1
    
    def test_bulk_create_or_update(self, db_session, sample_analysis):
        """Test bulk creating/updating components"""
        repo = ComponentRepository(db_session)
        
        components_data = [
            {
                'name': 'lib1',
                'version': '1.0.0',
                'type': ComponentType.LIBRARY,
                'vulnerability_count': 2
            },
            {
                'name': 'lib2',
                'version': '2.0.0',
                'type': ComponentType.LIBRARY,
                'vulnerability_count': 0
            }
        ]
        
        components = repo.bulk_create_or_update(components_data, sample_analysis.id)
        
        assert len(components) == 2
        assert all(c.analysis_id == sample_analysis.id for c in components)


class TestSBOMRepository:
    """Test SBOMRepository operations"""
    
    def test_create_sbom(self, db_session, sample_analysis):
        """Test creating an SBOM"""
        repo = SBOMRepository(db_session)
        
        sbom_data = {
            'sbom_id': str(uuid4()),
            'format': 'spdx',
            'spec_version': 'SPDX-2.3',
            'name': 'Test SBOM',
            'content': {'spdxVersion': 'SPDX-2.3', 'packages': []},
            'analysis_id': sample_analysis.id
        }
        
        sbom = repo.create(**sbom_data)
        
        assert sbom.sbom_id == sbom_data['sbom_id']
        assert sbom.format == 'spdx'
        assert sbom.content['spdxVersion'] == 'SPDX-2.3'
    
    def test_get_by_format(self, db_session, sample_analysis):
        """Test filtering SBOMs by format"""
        repo = SBOMRepository(db_session)
        
        # Create test SBOMs
        repo.create(
            sbom_id=str(uuid4()),
            format='spdx',
            content={'spdxVersion': 'SPDX-2.3'},
            analysis_id=sample_analysis.id
        )
        
        spdx_sboms = repo.get_by_format('spdx')
        
        assert len(spdx_sboms) >= 1
        assert all(s.format == 'spdx' for s in spdx_sboms)


class TestVulnerabilityRepository:
    """Test VulnerabilityRepository operations"""
    
    def test_create_vulnerability(self, db_session):
        """Test creating a vulnerability"""
        repo = VulnerabilityRepository(db_session)
        
        vuln_data = {
            'vulnerability_id': 'CVE-2021-44228',
            'source': 'NVD',
            'title': 'Log4j RCE Vulnerability',
            'description': 'Remote code execution in Log4j',
            'severity': VulnerabilitySeverity.CRITICAL,
            'cvss_score': 10.0
        }
        
        vulnerability = repo.create(**vuln_data)
        
        assert vulnerability.vulnerability_id == 'CVE-2021-44228'
        assert vulnerability.severity == VulnerabilitySeverity.CRITICAL
        assert vulnerability.cvss_score == 10.0
    
    def test_get_by_severity(self, db_session):
        """Test filtering vulnerabilities by severity"""
        repo = VulnerabilityRepository(db_session)
        
        # Create test vulnerability
        repo.create(
            vulnerability_id='CVE-2021-TEST',
            source='Test',
            title='Test Vulnerability',
            severity=VulnerabilitySeverity.HIGH,
            cvss_score=8.5
        )
        
        high_vulns = repo.get_by_severity(VulnerabilitySeverity.HIGH)
        
        assert len(high_vulns) >= 1
        assert all(v.severity == VulnerabilitySeverity.HIGH for v in high_vulns)
    
    def test_search_vulnerabilities(self, db_session):
        """Test searching vulnerabilities"""
        repo = VulnerabilityRepository(db_session)
        
        # Create test vulnerability
        repo.create(
            vulnerability_id='CVE-2021-SEARCH',
            source='Test',
            title='Searchable Vulnerability',
            description='This is a test vulnerability for searching'
        )
        
        results = repo.search_vulnerabilities('Searchable')
        
        assert len(results) >= 1
        assert any('Searchable' in v.title for v in results)


class TestDatabaseIntegration:
    """Test database integration scenarios"""
    
    def test_analysis_with_components_and_sbom(self, db_session):
        """Test creating analysis with components and SBOM"""
        # Create analysis
        analysis = Analysis(
            analysis_id=str(uuid4()),
            status=AnalysisStatus.COMPLETED,
            analysis_type="integration_test",
            location="/test/integration"
        )
        db_session.add(analysis)
        db_session.commit()
        
        # Add components
        for i in range(3):
            component = Component(
                name=f"component-{i}",
                version="1.0.0",
                type=ComponentType.LIBRARY,
                analysis_id=analysis.id
            )
            db_session.add(component)
        
        # Add SBOM
        sbom = SBOM(
            sbom_id=str(uuid4()),
            format='spdx',
            content={'packages': []},
            analysis_id=analysis.id
        )
        db_session.add(sbom)
        
        db_session.commit()
        
        # Verify relationships
        db_session.refresh(analysis)
        assert len(analysis.components) == 3
        assert len(analysis.sboms) == 1
        assert analysis.sboms[0].format == 'spdx'


if __name__ == "__main__":
    pytest.main([__file__])