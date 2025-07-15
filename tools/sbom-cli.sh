#!/bin/bash

# SBOM Platform CLI Helper Script
# Usage: ./sbom-cli.sh [command] [options]

SBOM_API="http://localhost:8000"
DATA_DIR="./data"

show_help() {
    echo "🔍 SBOM Platform CLI Helper"
    echo "   Powered by Syft v1.28.0 for industry-standard analysis"
    echo ""
    echo "USAGE:"
    echo "  ./sbom-cli.sh [command] [options]"
    echo ""
    echo "COMMANDS:"
    echo "  analyze-source <path> <language> [--analyze-imports]"
    echo "                                     - Analyze source code (auto-copies from any path)"
    echo "                                       --analyze-imports: Analyze import statements (Java only)"
    echo "  analyze-binary <path>              - Analyze binary files (auto-copies from any path)"
    echo "  analyze-docker <image>             - Analyze Docker image"
    echo "  analyze-os                         - Analyze local OS (Linux only)"
    echo "  status <analysis-id>               - Check analysis status"
    echo "  results <analysis-id>              - Get analysis results"
    echo "  generate-sbom <analysis-ids> <format> - Generate SBOM"
    echo "  get-sbom <sbom-id>                 - Download SBOM"
    echo "  health                             - Check platform health"
    echo ""
    echo "EXAMPLES:"
    echo "  # Analyze project from anywhere (auto-copies to ./data/)"
    echo "  ./sbom-cli.sh analyze-source /path/to/my-java-app java"
    echo "  ./sbom-cli.sh analyze-source ~/Projects/my-cpp-project c++"
    echo ""
    echo "  # Analyze binary from anywhere (auto-copies to ./data/)"
    echo "  ./sbom-cli.sh analyze-binary /path/to/application.jar"
    echo "  ./sbom-cli.sh analyze-binary ~/Downloads/executable"
    echo ""
    echo "  # Analyze Docker images"
    echo "  ./sbom-cli.sh analyze-docker nginx:latest"
    echo "  ./sbom-cli.sh analyze-docker ubuntu:20.04"
    echo "  ./sbom-cli.sh analyze-docker registry.example.com/myapp:v1.0"
    echo ""
    echo "  # Analyze project already in ./data/"
    echo "  ./sbom-cli.sh analyze-source my-local-project java"
    echo ""
    echo "  # Analyze local OS"
    echo "  ./sbom-cli.sh analyze-os"
    echo ""
    echo "  # Generate SPDX SBOM"
    echo "  ./sbom-cli.sh generate-sbom \"analysis-id-1,analysis-id-2\" spdx"
    echo ""
    echo "SUPPORTED FORMATS: spdx, cyclonedx, swid"
    echo "SUPPORTED LANGUAGES: java, c++"
    echo ""
    echo "NOTE: Files are automatically copied to ./data/ if they're not already there."
}

check_dependencies() {
    if ! command -v curl &> /dev/null; then
        echo "❌ Error: curl is required but not installed."
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Error: python3 is required but not installed."
        exit 1
    fi
}

check_platform() {
    if ! curl -s "$SBOM_API/health" > /dev/null; then
        echo "❌ Error: SBOM Platform is not running or not accessible at $SBOM_API"
        echo "   Start the platform with: docker-compose -f docker-compose-simple.yml up -d"
        exit 1
    fi
}

prepare_source_path() {
    local input_path="$1"
    
    # If path starts with /, ~, or ./, it's an absolute/relative path - copy it
    if [[ "$input_path" == /* ]] || [[ "$input_path" == ~* ]] || [[ "$input_path" == ./* ]] || [[ "$input_path" == ../* ]]; then
        # Expand tilde if present
        input_path="${input_path/#\~/$HOME}"
        
        if [[ ! -e "$input_path" ]]; then
            echo "❌ Error: Path '$input_path' does not exist" >&2
            exit 1
        fi
        
        # Get basename for destination
        local dest_name=$(basename "$input_path")
        local dest_path="$DATA_DIR/$dest_name"
        
        echo "📁 Copying '$input_path' to '$dest_path'..." >&2
        
        # Remove existing destination if it exists
        if [[ -e "$dest_path" ]]; then
            echo "   Removing existing '$dest_path'" >&2
            rm -rf "$dest_path"
        fi
        
        # Copy the source
        if [[ -d "$input_path" ]]; then
            cp -r "$input_path" "$dest_path"
        else
            cp "$input_path" "$dest_path"
        fi
        
        if [[ $? -ne 0 ]]; then
            echo "❌ Error: Failed to copy '$input_path' to '$dest_path'" >&2
            exit 1
        fi
        
        echo "✅ Copied successfully" >&2
        echo "$dest_name"
    else
        # Path doesn't look absolute - assume it's already in data dir
        if [[ ! -e "$DATA_DIR/$input_path" ]]; then
            echo "❌ Error: Path '$DATA_DIR/$input_path' does not exist" >&2
            echo "   Either provide an absolute path or ensure the file/folder exists in $DATA_DIR/" >&2
            exit 1
        fi
        echo "$input_path"
    fi
}

analyze_source() {
    local project_path="$1"
    local language="$2"
    local analyze_imports="$3"
    
    if [[ -z "$project_path" || -z "$language" ]]; then
        echo "❌ Usage: analyze-source <path> <language> [--analyze-imports]"
        echo "   Examples:"
        echo "     analyze-source /path/to/my-java-project java"
        echo "     analyze-source ~/Projects/my-cpp-project c++"
        echo "     analyze-source my-local-project java  # if already in ./data/"
        echo "     analyze-source /path/to/java-project java --analyze-imports"
        exit 1
    fi
    
    # Prepare the path (copy if needed)
    local prepared_path=$(prepare_source_path "$project_path")
    local full_path="/app/data/$prepared_path"
    
    echo ""
    echo "🔍 Analyzing source code..."
    echo "   Container path: $full_path"
    echo "   Language: $language"
    
    # Build options JSON
    local options="{\"deep_scan\":true"
    if [[ "$analyze_imports" == "--analyze-imports" ]]; then
        echo "   Import analysis: enabled"
        options="${options},\"analyze_imports\":true"
    fi
    options="${options}}"
    
    local response=$(curl -s -X POST "$SBOM_API/analyze/source" \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"source\",\"language\":\"$language\",\"location\":\"$full_path\",\"options\":$options}")
    
    local analysis_id=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('analysis_id', 'ERROR'))")
    
    if [[ "$analysis_id" == "ERROR" ]]; then
        echo "❌ Analysis failed:"
        echo "$response" | python3 -m json.tool
        exit 1
    fi
    
    echo "✅ Analysis started successfully!"
    echo "   Analysis ID: $analysis_id"
    echo ""
    echo "Check status with: ./sbom-cli.sh status $analysis_id"
    echo "Get results with: ./sbom-cli.sh results $analysis_id"
}

analyze_binary() {
    local binary_path="$1"
    
    if [[ -z "$binary_path" ]]; then
        echo "❌ Usage: analyze-binary <path>"
        echo "   Examples:"
        echo "     analyze-binary /path/to/application.jar"
        echo "     analyze-binary ~/Downloads/executable"
        echo "     analyze-binary my-local-file.jar  # if already in ./data/"
        exit 1
    fi
    
    # Prepare the path (copy if needed)
    local prepared_path=$(prepare_source_path "$binary_path")
    local full_path="/app/data/$prepared_path"
    
    echo ""
    echo "🔍 Analyzing binary..."
    echo "   Container path: $full_path"
    
    local response=$(curl -s -X POST "$SBOM_API/analyze/binary" \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"binary\",\"location\":\"$full_path\"}")
    
    local analysis_id=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('analysis_id', 'ERROR'))")
    
    if [[ "$analysis_id" == "ERROR" ]]; then
        echo "❌ Analysis failed:"
        echo "$response" | python3 -m json.tool
        exit 1
    fi
    
    echo "✅ Analysis started successfully!"
    echo "   Analysis ID: $analysis_id"
    echo ""
    echo "Check status with: ./sbom-cli.sh status $analysis_id"
}

analyze_docker() {
    local image="$1"
    
    if [[ -z "$image" ]]; then
        echo "❌ Usage: analyze-docker <image>"
        echo "   Examples:"
        echo "     analyze-docker nginx:latest"
        echo "     analyze-docker ubuntu:20.04"
        echo "     analyze-docker registry.example.com/myapp:v1.0"
        echo "     analyze-docker python:3.9-slim"
        exit 1
    fi
    
    echo ""
    echo "🐋 Analyzing Docker image..."
    echo "   Image: $image"
    
    local response=$(curl -s -X POST "$SBOM_API/analyze/docker" \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"docker\",\"location\":\"$image\"}")
    
    local analysis_id=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('analysis_id', 'ERROR'))")
    
    if [[ "$analysis_id" == "ERROR" ]]; then
        echo "❌ Analysis failed:"
        echo "$response" | python3 -m json.tool
        exit 1
    fi
    
    echo "✅ Analysis started successfully!"
    echo "   Analysis ID: $analysis_id"
    echo ""
    echo "Check status with: ./sbom-cli.sh status $analysis_id"
    echo "Get results with: ./sbom-cli.sh results $analysis_id"
}

check_status() {
    local analysis_id="$1"
    
    if [[ -z "$analysis_id" ]]; then
        echo "❌ Usage: status <analysis-id>"
        exit 1
    fi
    
    echo "📊 Checking analysis status..."
    
    local status_response=$(curl -s "$SBOM_API/analyze/$analysis_id/status")
    local status=$(echo "$status_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'ERROR'))")
    
    if [[ "$status" == "ERROR" ]]; then
        echo "❌ Failed to get status:"
        echo "$status_response"
        exit 1
    fi
    
    echo "   Status: $status"
    
    if [[ "$status" == "completed" ]]; then
        local components=$(echo "$status_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('components_found', 0))")
        echo "   Components found: $components"
        echo ""
        echo "Get detailed results with: ./sbom-cli.sh results $analysis_id"
    fi
}

get_results() {
    local analysis_id="$1"
    
    if [[ -z "$analysis_id" ]]; then
        echo "❌ Usage: results <analysis-id>"
        exit 1
    fi
    
    echo "📋 Getting analysis results..."
    
    local results=$(curl -s "$SBOM_API/analyze/$analysis_id/results")
    echo "$results" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'error' in data:
    print('❌ Error:', data['error'])
    sys.exit(1)

print(f'✅ Analysis: {data[\"status\"]}')
print(f'📦 Components found: {len(data[\"components\"])}')

if data['components']:
    print('\nComponents:')
    for i, comp in enumerate(data['components'], 1):
        version = comp.get('version') or 'unknown'
        location = comp.get('source_location', 'unknown')
        print(f'  {i:2}. {comp[\"name\"]} v{version}')
        if location != 'unknown':
            print(f'      Source: {location}')

print(f'\nMetadata: {data[\"metadata\"]}')
print(f'\nTo generate an SBOM, use: ./sbom-cli.sh generate-sbom {data[\"analysis_id\"]} spdx')
"
}

generate_sbom() {
    local analysis_ids="$1"
    local format="$2"
    
    if [[ -z "$analysis_ids" || -z "$format" ]]; then
        echo "❌ Usage: generate-sbom <analysis-ids> <format>"
        echo "   Example: generate-sbom \"id1,id2\" spdx"
        echo "   Formats: spdx, cyclonedx, swid"
        exit 1
    fi
    
    echo "📄 Generating SBOM..."
    echo "   Analysis IDs: $analysis_ids"
    echo "   Format: $format"
    
    # Convert comma-separated string to JSON array
    local ids_json=$(echo "$analysis_ids" | python3 -c "
import sys
ids = sys.stdin.read().strip().split(',')
ids = [id.strip() for id in ids]
print(str(ids).replace(\"'\", '\"'))
")
    
    local response=$(curl -s -X POST "$SBOM_API/sbom/generate" \
        -H "Content-Type: application/json" \
        -d "{\"analysis_ids\":$ids_json,\"format\":\"$format\",\"include_licenses\":true}")
    
    local sbom_id=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('sbom_id', 'ERROR'))")
    
    if [[ "$sbom_id" == "ERROR" ]]; then
        echo "❌ SBOM generation failed:"
        echo "$response" | python3 -m json.tool
        exit 1
    fi
    
    echo "✅ SBOM generation started!"
    echo "   SBOM ID: $sbom_id"
    echo ""
    echo "Download with: ./sbom-cli.sh get-sbom $sbom_id"
}

get_sbom() {
    local sbom_id="$1"
    
    if [[ -z "$sbom_id" ]]; then
        echo "❌ Usage: get-sbom <sbom-id>"
        exit 1
    fi
    
    echo "📥 Downloading SBOM..."
    
    local filename="sbom-$sbom_id.json"
    
    if curl -s "$SBOM_API/sbom/$sbom_id" > "$filename"; then
        # Check if file contains valid JSON
        if python3 -m json.tool "$filename" > /dev/null 2>&1; then
            local components=$(python3 -c "
import json
with open('$filename') as f:
    data = json.load(f)
    if 'packages' in data:
        print(len(data['packages']))
    elif 'components' in data:
        print(len(data['components']))
    else:
        print('unknown')
")
            echo "✅ SBOM downloaded successfully!"
            echo "   File: $filename"
            echo "   Components: $components"
        else
            echo "❌ Invalid SBOM received"
            cat "$filename"
            rm "$filename"
            exit 1
        fi
    else
        echo "❌ Failed to download SBOM"
        exit 1
    fi
}

analyze_os() {
    echo ""
    echo "🖥️  Analyzing local operating system..."
    echo "   Note: Currently supports Linux only"
    
    local response=$(curl -s -X POST "$SBOM_API/analyze/os" \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"os\",\"location\":\"localhost\"}")
    
    local analysis_id=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('analysis_id', 'ERROR'))")
    
    if [[ "$analysis_id" == "ERROR" ]]; then
        echo "❌ Analysis failed:"
        echo "$response" | python3 -m json.tool
        exit 1
    fi
    
    echo "✅ OS analysis started successfully!"
    echo "   Analysis ID: $analysis_id"
    echo ""
    echo "Check status with: ./sbom-cli.sh status $analysis_id"
    echo "Get results with: ./sbom-cli.sh results $analysis_id"
}

check_health() {
    echo "❤️ Checking platform health..."
    
    local health=$(curl -s "$SBOM_API/health")
    echo "$health" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ Status: {data[\"status\"]}')
    if 'uptime_hours' in data:
        print(f'⏱️  Uptime: {data[\"uptime_hours\"]:.1f} hours')
    if 'timestamp' in data:
        print(f'🕒 Timestamp: {data[\"timestamp\"]}')
except:
    print('❌ Platform not responding correctly')
    sys.exit(1)
"
    
    echo ""
    echo "🌐 Dashboard: $SBOM_API/dashboard"
    echo "📊 Metrics: $SBOM_API/api/metrics"
}

# Main script logic
check_dependencies
check_platform

case "$1" in
    "analyze-source")
        analyze_source "$2" "$3" "$4"
        ;;
    "analyze-binary")
        analyze_binary "$2"
        ;;
    "analyze-docker")
        analyze_docker "$2"
        ;;
    "analyze-os")
        analyze_os
        ;;
    "status")
        check_status "$2"
        ;;
    "results")
        get_results "$2"
        ;;
    "generate-sbom")
        generate_sbom "$2" "$3"
        ;;
    "get-sbom")
        get_sbom "$2"
        ;;
    "health")
        check_health
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac