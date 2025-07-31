# MongoDB Export Data

This directory contains Perseus SBOM database data exported in MongoDB-compatible JSON format.

## Export Details

- **Export Date**: 2025-07-31
- **Source Database**: PostgreSQL (Kubernetes deployment)
- **Export Tool**: `export_for_mongodb.py`

## Files

### Data Files

- **analyses.json** - Main collection containing analyses with embedded components
  - Each analysis document includes:
    - Analysis metadata (ID, status, type, timing)
    - Embedded components array with full component details
    - Embedded SBOM references
    - Embedded vulnerability scan summaries
    - Build information (if applicable)

- **vulnerabilities.json** - Reference collection for vulnerability details
  - Full vulnerability information including CVE IDs, scores, descriptions
  - Used for lookups when detailed vulnerability info is needed

- **licenses.json** - Reference collection for license information
  - SPDX license identifiers and full license details
  - Used for license compliance queries

- **agents.json** - Agent information with recent telemetry
  - Remote agent details and last 100 telemetry entries per agent
  - Used for monitoring distributed scans

### Import Script

- **import_to_mongodb.sh** - Automated import script for MongoDB

## Import Instructions

### Prerequisites

- MongoDB installed and running
- `mongoimport` command available in PATH

### Basic Import

```bash
# Import to default database name
./import_to_mongodb.sh

# Import to custom database
./import_to_mongodb.sh my_sbom_database
```

### Manual Import

If you prefer to import collections individually:

```bash
# Import each collection
mongoimport --db perseus_sbom --collection analyses --file analyses.json
mongoimport --db perseus_sbom --collection vulnerabilities --file vulnerabilities.json
mongoimport --db perseus_sbom --collection licenses --file licenses.json
mongoimport --db perseus_sbom --collection agents --file agents.json
```

### Create Indexes

After import, create indexes for optimal query performance:

```javascript
use perseus_sbom

// Analyses indexes
db.analyses.createIndex({ "analysis_id": 1 })
db.analyses.createIndex({ "created_at": -1 })
db.analyses.createIndex({ "status": 1 })
db.analyses.createIndex({ "components.name": 1 })
db.analyses.createIndex({ "components.purl": 1 })

// Vulnerability indexes
db.vulnerabilities.createIndex({ "vulnerability_id": 1 })
db.vulnerabilities.createIndex({ "severity": 1 })
db.vulnerabilities.createIndex({ "cvss_score": -1 })

// License indexes
db.licenses.createIndex({ "spdx_id": 1 })
db.licenses.createIndex({ "name": 1 })

// Agent indexes
db.agents.createIndex({ "agent_id": 1 })
db.agents.createIndex({ "hostname": 1 })
```

## Data Format

### Date Fields

Dates are exported in MongoDB Extended JSON format:
```json
{"$date": "2025-07-31T17:12:36.432775Z"}
```

### ID Fields

PostgreSQL UUIDs are converted to strings and stored as `_id`:
```json
{"_id": "d69dd0fa-5792-4949-98f8-b6ba822c6f62"}
```

### Embedded vs Reference Design

- **Analyses** collection uses embedded documents for components, reducing the need for joins
- **Vulnerabilities** and **Licenses** are stored as separate collections for:
  - Deduplication (same vulnerability/license can affect multiple components)
  - Detailed information that's not always needed
  - Efficient updates when vulnerability data changes

## Query Examples

### Find all analyses with critical vulnerabilities
```javascript
db.analyses.find({
  "critical_vulnerability_count": { $gt: 0 }
})
```

### Find components by name across all analyses
```javascript
db.analyses.find({
  "components.name": "openssl"
}, {
  "analysis_id": 1,
  "components.$": 1
})
```

### Get vulnerability details for a specific CVE
```javascript
db.vulnerabilities.findOne({
  "vulnerability_id": "CVE-2023-12345"
})
```

### Find all components with a specific license
```javascript
db.analyses.aggregate([
  { $unwind: "$components" },
  { $unwind: "$components.licenses" },
  { $match: { "components.licenses.spdx_id": "Apache-2.0" } },
  { $project: {
      "analysis_id": 1,
      "component_name": "$components.name",
      "component_version": "$components.version"
    }
  }
])
```

## Notes

- Line-delimited JSON format (one document per line) for efficient streaming import
- All collections can be imported independently
- The import script handles database creation if it doesn't exist
- Consider MongoDB's 16MB document size limit for very large analyses

## Regenerating Export

To regenerate this export with fresh data:

```bash
# From project root
cd /Users/ikarakas/Development/Python/SBOM

# Set K8s PostgreSQL credentials
export PERSEUS_DB_HOST=localhost
export PERSEUS_DB_PORT=5432
export PERSEUS_DB_NAME=sbom_platform
export PERSEUS_DB_USER=sbom_user
export PERSEUS_DB_PASSWORD=sbom_password

# Ensure K8s port-forward is running
kubectl port-forward -n perseus svc/postgres 5432:5432 &

# Run export (default: line-delimited JSON)
python scripts/mongodb_export/export_for_mongodb.py -o scripts/mongodb_export/

# Export as JSON arrays with pretty printing
python scripts/mongodb_export/export_for_mongodb.py -o scripts/mongodb_export/ -a
```

### Export Format Options

The `export_for_mongodb.py` script supports two output formats:

1. **Line-delimited JSON (default)** - One document per line, optimal for `mongoimport`
   ```bash
   python scripts/mongodb_export/export_for_mongodb.py -o output_dir/
   ```

2. **JSON Arrays** - Pretty-printed JSON arrays, easier to read but requires `--jsonArray` flag for import
   ```bash
   python scripts/mongodb_export/export_for_mongodb.py -o output_dir/ -a
   ```

## Export Scripts

This folder contains three export scripts:

1. **export_for_mongodb.py** - MongoDB-optimized export with embedded documents
2. **export_database_to_json.py** - General JSON export preserving all relationships
3. **pg_json_export.sh** - PostgreSQL native JSON export using SQL queries

Each script serves different use cases:
- Use `export_for_mongodb.py` for optimal MongoDB import
- Use `export_database_to_json.py` for complete database backup/migration
- Use `pg_json_export.sh` for quick exports using PostgreSQL's JSON capabilities