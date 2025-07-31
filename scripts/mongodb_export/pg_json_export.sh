#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
# Export Perseus database using PostgreSQL's native JSON capabilities

# Database connection parameters
DB_HOST=${PERSEUS_DB_HOST:-localhost}
DB_PORT=${PERSEUS_DB_PORT:-5432}
DB_NAME=${PERSEUS_DB_NAME:-perseus}
DB_USER=${PERSEUS_DB_USER:-perseus}
OUTPUT_DIR=${1:-./json_export}

echo "Exporting Perseus database to JSON using PostgreSQL..."
mkdir -p "$OUTPUT_DIR"

# Export analyses with related data as JSON
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_agg(row_to_json(t)) FROM (
    SELECT 
        a.*,
        (
            SELECT json_agg(row_to_json(c))
            FROM components c
            WHERE c.analysis_id = a.id
        ) as components,
        (
            SELECT json_agg(row_to_json(s))
            FROM sboms s
            WHERE s.analysis_id = a.id
        ) as sboms,
        (
            SELECT json_agg(row_to_json(vs))
            FROM vulnerability_scans vs
            WHERE vs.analysis_id = a.id
        ) as vulnerability_scans
    FROM analyses a
) t;
" > "$OUTPUT_DIR/analyses_full.json"

# Export components with their relationships
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_agg(row_to_json(t)) FROM (
    SELECT 
        c.*,
        array_agg(DISTINCT cv.vulnerability_id) FILTER (WHERE cv.vulnerability_id IS NOT NULL) as vulnerability_ids,
        array_agg(DISTINCT cl.license_id) FILTER (WHERE cl.license_id IS NOT NULL) as license_ids
    FROM components c
    LEFT JOIN component_vulnerabilities cv ON c.id = cv.component_id
    LEFT JOIN component_licenses cl ON c.id = cl.component_id
    GROUP BY c.id
) t;
" > "$OUTPUT_DIR/components_with_relations.json"

# Export vulnerabilities
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_agg(row_to_json(vulnerabilities)) FROM vulnerabilities;
" > "$OUTPUT_DIR/vulnerabilities.json"

# Export licenses
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_agg(row_to_json(licenses)) FROM licenses;
" > "$OUTPUT_DIR/licenses.json"

# Export agents with telemetry
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_agg(row_to_json(t)) FROM (
    SELECT 
        a.*,
        (
            SELECT json_agg(row_to_json(td))
            FROM telemetry_data td
            WHERE td.agent_id = a.id
            ORDER BY td.timestamp DESC
            LIMIT 100
        ) as recent_telemetry
    FROM agents a
) t;
" > "$OUTPUT_DIR/agents_with_telemetry.json"

# Export builds
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_agg(row_to_json(builds)) FROM builds;
" > "$OUTPUT_DIR/builds.json"

# Create a combined export with all tables
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_build_object(
    'export_date', now(),
    'database', '$DB_NAME',
    'tables', json_build_object(
        'analyses', (SELECT count(*) FROM analyses),
        'components', (SELECT count(*) FROM components),
        'vulnerabilities', (SELECT count(*) FROM vulnerabilities),
        'licenses', (SELECT count(*) FROM licenses),
        'sboms', (SELECT count(*) FROM sboms),
        'vulnerability_scans', (SELECT count(*) FROM vulnerability_scans),
        'agents', (SELECT count(*) FROM agents),
        'builds', (SELECT count(*) FROM builds)
    )
);
" > "$OUTPUT_DIR/export_metadata.json"

echo "Export completed! Files created in $OUTPUT_DIR:"
ls -la "$OUTPUT_DIR"/*.json

# Create MongoDB import instructions
cat > "$OUTPUT_DIR/mongodb_import_instructions.txt" << 'EOF'
MongoDB Import Instructions
===========================

1. To import the JSON files into MongoDB:

   # Import each collection
   mongoimport --db perseus_sbom --collection analyses --file analyses_full.json --jsonArray
   mongoimport --db perseus_sbom --collection components --file components_with_relations.json --jsonArray
   mongoimport --db perseus_sbom --collection vulnerabilities --file vulnerabilities.json --jsonArray
   mongoimport --db perseus_sbom --collection licenses --file licenses.json --jsonArray
   mongoimport --db perseus_sbom --collection agents --file agents_with_telemetry.json --jsonArray
   mongoimport --db perseus_sbom --collection builds --file builds.json --jsonArray

2. Create indexes in MongoDB:

   use perseus_sbom
   db.analyses.createIndex({ "analysis_id": 1 })
   db.components.createIndex({ "name": 1, "version": 1 })
   db.components.createIndex({ "purl": 1 })
   db.vulnerabilities.createIndex({ "vulnerability_id": 1 })
   db.vulnerabilities.createIndex({ "severity": 1 })
   db.licenses.createIndex({ "spdx_id": 1 })

3. Data transformation notes:
   - PostgreSQL UUIDs are exported as strings
   - Timestamps are in ISO 8601 format
   - JSONB fields are preserved as nested documents
   - Enum values are exported as strings
EOF

echo ""
echo "MongoDB import instructions saved to: $OUTPUT_DIR/mongodb_import_instructions.txt"