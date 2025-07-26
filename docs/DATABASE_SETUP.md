# Perseus Database Setup Guide

This guide covers setting up and using the PostgreSQL database integration for Perseus SBOM Platform.

## 📋 Overview

Perseus now supports persistent data storage using PostgreSQL with SQLAlchemy ORM. This enables:

- **Historical tracking** of analyses and vulnerabilities
- **Advanced queries** and analytics
- **Data relationships** between components, vulnerabilities, and analyses
- **Performance improvements** for large datasets
- **Data integrity** with referential constraints

## 🗃️ Database Schema

### Core Tables

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `analyses` | SBOM analysis jobs | → `components`, `sboms`, `vulnerability_scans` |
| `components` | Software dependencies | ← `analyses`, ↔ `vulnerabilities` |
| `vulnerabilities` | CVE/security issues | ↔ `components` |
| `sboms` | Generated SBOM documents | ← `analyses` |
| `vulnerability_scans` | Scan results | ← `analyses` |
| `agents` | Remote telemetry agents | → `telemetry_data` |
| `builds` | CI/CD build integration | ← `analyses` |

### Key Features

- **UUID primary keys** for all entities
- **JSONB fields** for flexible metadata storage
- **Timestamps** for audit trails
- **Enum types** for status and severity levels
- **Full-text search** capabilities
- **Referential integrity** with cascade deletes

## 🚀 Quick Start

### 1. Using Docker Compose (Recommended)

The simplest way to get started:

```bash
# Start Perseus with PostgreSQL
docker-compose -f docker-compose-simple.yml up -d

# Database will be automatically initialized
# Access dashboard at http://localhost:8080/dashboard
```

### 2. Manual Setup

#### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Install PostgreSQL (macOS)
brew install postgresql
```

#### Database Setup

```bash
# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database and user
sudo -u postgres psql
```

```sql
-- In PostgreSQL shell
CREATE DATABASE perseus;
CREATE USER perseus WITH PASSWORD 'perseus_secret';
GRANT ALL PRIVILEGES ON DATABASE perseus TO perseus;
\q
```

#### Initialize Database

```bash
# Initialize tables and run migrations
python scripts/init_database.py

# Migrate existing file data (optional)
python scripts/migrate_data_to_database.py
```

## ⚙️ Configuration

### Environment Variables

Configure database connection via environment variables:

```bash
# Required
export PERSEUS_DB_HOST="localhost"
export PERSEUS_DB_PORT="5432"
export PERSEUS_DB_NAME="perseus"
export PERSEUS_DB_USER="perseus"
export PERSEUS_DB_PASSWORD="perseus_secret"

# Optional
export PERSEUS_DB_POOL_SIZE="10"
export PERSEUS_DB_MAX_OVERFLOW="20"
export PERSEUS_DB_ECHO_SQL="false"
export PERSEUS_DB_USE_SSL="false"
```

### Docker Environment

For Docker deployments, set in `docker-compose.yml`:

```yaml
environment:
  - PERSEUS_DB_HOST=postgres
  - PERSEUS_DB_PORT=5432
  - PERSEUS_DB_NAME=perseus
  - PERSEUS_DB_USER=perseus
  - PERSEUS_DB_PASSWORD=perseus_secret
```

## 🔧 Database Operations

### Manual Database Management

```bash
# Test database connection
python -c "from src.database import test_connection; print('OK' if test_connection() else 'FAILED')"

# Create/recreate all tables
python -c "from src.database import create_tables; create_tables()"

# Drop all tables (DANGEROUS!)
python -c "from src.database import drop_tables; drop_tables()"
```

### Alembic Migrations

```bash
# Create a new migration
alembic -c migrations/alembic.ini revision --autogenerate -m "Add new feature"

# Apply migrations
alembic -c migrations/alembic.ini upgrade head

# Downgrade to previous version
alembic -c migrations/alembic.ini downgrade -1

# Show migration history
alembic -c migrations/alembic.ini history
```

### Data Migration

Migrate existing file-based data to database:

```bash
# Migrate all existing data
python scripts/migrate_data_to_database.py

# The script migrates:
# - Analysis results from data/results/*.json
# - SBOMs from data/sboms/*.json  
# - Agent data from telemetry_data/agents/*.json
# - BOM data from telemetry_data/bom/*.json
```

## 🔌 API Endpoints

### New Database-Backed Endpoints

#### Analysis Management
```bash
# List all analyses with filtering
GET /api/v1/analyses?status=completed&limit=50

# Get detailed analysis with components
GET /api/v1/analyses/{analysis_id}

# Get dashboard statistics
GET /api/v1/statistics/dashboard
```

#### Component Operations
```bash
# Search components
GET /api/v1/components/search?q=jackson

# Get vulnerable components
GET /api/v1/components/vulnerable?min_severity=critical

# Get unique components across analyses
GET /api/v1/components/unique
```

#### SBOM Management
```bash
# List SBOMs by format
GET /api/v1/sboms?format=spdx

# Get SBOM with full content
GET /api/v1/sboms/{sbom_id}

# Get SBOM statistics
GET /api/v1/sboms/statistics
```

#### Vulnerability Database
```bash
# List vulnerabilities with filtering
GET /api/v1/vulnerabilities?severity=critical&search=log4j

# Get vulnerability details
GET /api/v1/vulnerabilities/{vulnerability_id}

# Get critical vulnerabilities
GET /api/v1/vulnerabilities/critical

# List vulnerability scans
GET /api/v1/vulnerability-scans?analysis_id={id}
```

### Example Usage

```bash
# Get recent completed analyses
curl "http://localhost:8080/api/v1/analyses?status=completed&limit=10"

# Search for components containing "jackson"
curl "http://localhost:8080/api/v1/components/search?q=jackson"

# Get dashboard statistics
curl "http://localhost:8080/api/v1/statistics/dashboard"

# Get all critical vulnerabilities
curl "http://localhost:8080/api/v1/vulnerabilities/critical"
```

## 📊 Data Model Examples

### Analysis Record
```json
{
  "analysis_id": "03f9c943-40e2-4c8d-9505-c078bebe8f83",
  "status": "completed",
  "analysis_type": "source",
  "language": "java",
  "location": "/app/data/my-project",
  "component_count": 15,
  "vulnerability_count": 42,
  "critical_vulnerability_count": 3,
  "created_at": "2025-07-24T10:30:00Z",
  "completed_at": "2025-07-24T10:35:00Z",
  "duration_seconds": 300.5,
  "components": [...]
}
```

### Component Record
```json
{
  "name": "jackson-databind",
  "version": "2.9.8",
  "type": "library",
  "purl": "pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.9.8",
  "vulnerability_count": 15,
  "critical_vulnerabilities": 3,
  "high_vulnerabilities": 5,
  "metadata": {
    "syft_metadata": {...},
    "locations": [...]
  }
}
```

### Vulnerability Record
```json
{
  "vulnerability_id": "CVE-2021-44228",
  "source": "NVD",
  "title": "Apache Log4j2 JNDI features do not protect against attacker controlled LDAP",
  "severity": "critical",
  "cvss_score": 10.0,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
  "published_date": "2021-12-10T10:15:09Z",
  "references": ["https://nvd.nist.gov/vuln/detail/CVE-2021-44228"],
  "fixed_versions": ["2.15.0", "2.12.2"]
}
```

## 🧪 Testing

### Run Database Tests

```bash
# Run all database tests
python -m pytest tests/test_database.py -v

# Run specific test class
python -m pytest tests/test_database.py::TestAnalysisRepository -v

# Run with coverage
python -m pytest tests/test_database.py --cov=src.database
```

### Test Database Setup

Tests use in-memory SQLite for fast execution:

```python
@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    # ... rest of setup
```

## 🔍 Troubleshooting

### Common Issues

#### Connection Failed
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U perseus -d perseus
```

#### Permission Denied
```sql
-- Grant proper permissions
GRANT ALL PRIVILEGES ON DATABASE perseus TO perseus;
GRANT ALL ON SCHEMA public TO perseus;
```

#### Migration Errors
```bash
# Reset migrations (DANGEROUS - loses data)
alembic -c migrations/alembic.ini stamp head

# Or start fresh
alembic -c migrations/alembic.ini downgrade base
alembic -c migrations/alembic.ini upgrade head
```

#### Port Already in Use
```bash
# Find process using port 5432
sudo lsof -i :5432

# Change port in configuration
export PERSEUS_DB_PORT="5433"
```

### Performance Tuning

#### Database Configuration

Add to PostgreSQL `postgresql.conf`:

```ini
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Connection settings
max_connections = 200

# Logging
log_statement = 'all'  # For debugging only
```

#### Connection Pool Tuning

```bash
# Increase pool size for high load
export PERSEUS_DB_POOL_SIZE="20"
export PERSEUS_DB_MAX_OVERFLOW="40"
```

#### Query Optimization

```sql
-- Create additional indexes for performance
CREATE INDEX idx_components_name_version ON components(name, version);
CREATE INDEX idx_vulnerabilities_severity_cvss ON vulnerabilities(severity, cvss_score);
CREATE INDEX idx_analyses_type_status ON analyses(analysis_type, status);
```

## 🔐 Security

### Production Security

```bash
# Use strong passwords
export PERSEUS_DB_PASSWORD="$(openssl rand -base64 32)"

# Enable SSL connections
export PERSEUS_DB_USE_SSL="true"

# Restrict database access
# In PostgreSQL pg_hba.conf:
# host perseus perseus 10.0.0.0/8 md5
```

### Backup and Recovery

```bash
# Backup database
pg_dump -U perseus -h localhost perseus > perseus_backup.sql

# Restore database
psql -U perseus -h localhost perseus < perseus_backup.sql

# Automated backups
0 2 * * * pg_dump -U perseus perseus | gzip > /backups/perseus_$(date +\%Y\%m\%d).sql.gz
```

## 📈 Monitoring

### Database Metrics

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('perseus'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'perseus';
```

### Performance Monitoring

```sql
-- Slow queries
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Index usage
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## 🚀 Next Steps

With the database integration complete, you can now:

1. **Historical Analysis**: Compare vulnerability trends over time
2. **Advanced Queries**: Find components used across multiple projects
3. **Performance Monitoring**: Track analysis success rates and durations
4. **Data Visualization**: Build dashboards with rich analytics
5. **Integration**: Connect with external security tools via API

For advanced usage, see:
- [API Documentation](API.md)
- [Advanced Analytics](ANALYTICS.md) 
- [Enterprise Deployment](DEPLOYMENT.md)