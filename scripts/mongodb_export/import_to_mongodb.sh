#!/bin/bash
# MongoDB import script for Perseus SBOM data

DB_NAME=${1:-perseus_sbom}

echo "Importing Perseus data into MongoDB database: $DB_NAME"

# Import collections
mongoimport --db $DB_NAME --collection analyses --file analyses.json
mongoimport --db $DB_NAME --collection vulnerabilities --file vulnerabilities.json
mongoimport --db $DB_NAME --collection licenses --file licenses.json
mongoimport --db $DB_NAME --collection agents --file agents.json

echo "Import complete!"

# Create indexes
mongo $DB_NAME --eval '
db.analyses.createIndex({ "analysis_id": 1 });
db.analyses.createIndex({ "created_at": -1 });
db.analyses.createIndex({ "components.name": 1 });
db.vulnerabilities.createIndex({ "vulnerability_id": 1 });
db.vulnerabilities.createIndex({ "severity": 1 });
db.licenses.createIndex({ "spdx_id": 1 });
db.agents.createIndex({ "agent_id": 1 });
'

echo "Indexes created!"
