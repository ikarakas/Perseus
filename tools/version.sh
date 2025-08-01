#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
#
# Simple Version Management Script for SBOM Application
# Uses 3-part semantic versioning: major.minor.build

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_ROOT/config/version.json"

# Function to display version in simple format
display_version() {
    local version=$(jq -r '.version.string' "$VERSION_FILE")
    local env=$(jq -r '.build_info.environment' "$VERSION_FILE")
    local timestamp=$(jq -r '.build_info.timestamp' "$VERSION_FILE")
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN} ███████╗██████╗  ██████╗ ███╗   ███╗    ${YELLOW}██╗   ██╗${NC}"
    echo -e "${GREEN} ██╔════╝██╔══██╗██╔═══██╗████╗ ████║    ${YELLOW}██║   ██║${NC}"
    echo -e "${GREEN} ███████╗██████╔╝██║   ██║██╔████╔██║    ${YELLOW}██║   ██║${NC}"
    echo -e "${GREEN} ╚════██║██╔══██╗██║   ██║██║╚██╔╝██║    ${YELLOW}╚██╗ ██╔╝${NC}"
    echo -e "${GREEN} ███████║██████╔╝╚██████╔╝██║ ╚═╝ ██║     ${YELLOW}╚████╔╝${NC}"
    echo -e "${GREEN} ╚══════╝╚═════╝  ╚═════╝ ╚═╝     ╚═╝      ${YELLOW}╚═══╝${NC}"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e " ${BLUE}Version:${NC}         ${GREEN}${version}${NC}"
    echo -e " ${BLUE}Environment:${NC}     ${YELLOW}${env}${NC}"
    echo -e " ${BLUE}Build Time:${NC}      ${timestamp}"
    echo ""
    
    # Check where version is used
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e " ${YELLOW}Version Locations:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check all version locations
    echo -e " ${BLUE}Primary Configuration:${NC}"
    echo -e " ${GREEN}✓${NC} config/version.json - ${GREEN}$version${NC}"
    echo ""
    
    echo -e " ${BLUE}Application Files:${NC}"
    
    # Check each file for version
    check_file_version() {
        local file="$1"
        local pattern="$2"
        local FULL_PATH="$PROJECT_ROOT/$file"
        
        if [ -f "$FULL_PATH" ]; then
            # Find 3-part version (X.Y.Z)
            FOUND_VERSION=$(grep -o "$pattern" "$FULL_PATH" 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
            
            # Special handling for README.md which has v prefix
            if [ "$file" = "README.md" ] && [ -z "$FOUND_VERSION" ]; then
                FOUND_VERSION=$(grep -o "$pattern" "$FULL_PATH" 2>/dev/null | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' | sed 's/^v//' | head -1)
            fi
            
            if [ -n "$FOUND_VERSION" ]; then
                if [ "$FOUND_VERSION" = "$version" ]; then
                    echo -e " ${GREEN}✓${NC} $file - ${GREEN}$FOUND_VERSION${NC}"
                else
                    echo -e " ${RED}✗${NC} $file - ${RED}$FOUND_VERSION${NC} (should be $version)"
                fi
            else
                echo -e " ${YELLOW}?${NC} $file - version not found"
            fi
        else
            echo -e " ${YELLOW}!${NC} $file - file not found"
        fi
    }
    
    # Check each file with descriptions
    echo -e " ${YELLOW}Checking application versions...${NC}"
    check_file_version "src/api/main.py" 'version="[^"]*"'
    check_file_version "src/orchestrator/workflow.py" "'workflow_version': '[^']*'"
    check_file_version "src/sbom/generator.py" '"@version": "[^"]*"'
    check_file_version "telemetry-agent/collector.py" '"agent_version": "[^"]*"'
    check_file_version "telemetry-agent/transport.py" '"agent_version": "[^"]*"'
    check_file_version "k8s/api.yaml" 'VERSION: "[^"]*"'
    check_file_version "README.md" 'Perseus-v[0-9]\+\.[0-9]\+\.[0-9]\+'
    
    # Check grype_scanner.py separately with more specific pattern
    echo ""
    echo -e " ${YELLOW}Checking tool metadata versions...${NC}"
    FILE="$PROJECT_ROOT/src/vulnerability/grype_scanner.py"
    if [ -f "$FILE" ]; then
        # Look for Perseus tool version in metadata
        FOUND_VERSIONS=$(grep -o '"name": ".*sbom-platform", "version": "[0-9]\+\.[0-9]\+\.[0-9]\+"' "$FILE" 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | sort -u)
        if [ -n "$FOUND_VERSIONS" ]; then
            ALL_MATCH=true
            for FOUND_VERSION in $FOUND_VERSIONS; do
                if [ "$FOUND_VERSION" != "$version" ]; then
                    ALL_MATCH=false
                    break
                fi
            done
            if [ "$ALL_MATCH" = true ]; then
                echo -e " ${GREEN}✓${NC} src/vulnerability/grype_scanner.py - ${GREEN}$version${NC} (tool metadata)"
            else
                echo -e " ${RED}✗${NC} src/vulnerability/grype_scanner.py - ${RED}mixed versions found${NC} (should be $version)"
            fi
        else
            echo -e " ${YELLOW}?${NC} src/vulnerability/grype_scanner.py - tool version not found"
        fi
    else
        echo -e " ${YELLOW}!${NC} src/vulnerability/grype_scanner.py - file not found"
    fi
    
    echo ""
    echo -e " ${BLUE}Dynamic Readers:${NC}"
    echo -e " ${GREEN}✓${NC} Web Dashboard (reads from config/version.json)"
    echo -e " ${GREEN}✓${NC} API Reference (reads from config/version.json)"
    echo -e " ${GREEN}✓${NC} SBOM Generator (reads from config/version.json)"
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to update version in all files
update_all_files() {
    local NEW_VERSION="$1"
    
    echo ""
    echo -e "${BLUE}Updating version in all locations...${NC}"
    
    # Update src/api/main.py - FastAPI version parameter
    FILE="$PROJECT_ROOT/src/api/main.py"
    if [ -f "$FILE" ]; then
        # Handle multi-line FastAPI initialization
        # First try single line, then multi-line pattern
        if grep -q 'version="[0-9]\+\.[0-9]\+\.[0-9]\+"' "$FILE"; then
            sed -i.bak -E "s/(version=)\"[0-9]+\.[0-9]+\.[0-9]+\"/\1\"${NEW_VERSION}\"/g" "$FILE" && rm "${FILE}.bak" && echo -e " ${GREEN}✓${NC} Updated src/api/main.py (FastAPI version)" || echo -e " ${RED}✗${NC} Failed to update src/api/main.py"
        else
            echo -e " ${YELLOW}!${NC} src/api/main.py - version pattern not found, skipping"
        fi
    fi
    
    # Update src/orchestrator/workflow.py
    FILE="$PROJECT_ROOT/src/orchestrator/workflow.py"
    if [ -f "$FILE" ]; then
        sed -i.bak -E "s/'workflow_version': '[0-9]+\.[0-9]+\.[0-9]+'/'workflow_version': '${NEW_VERSION}'/g; s/Perseus Platform v[0-9]+\.[0-9]+\.[0-9]+/Perseus Platform v${NEW_VERSION}/g" "$FILE" && rm "${FILE}.bak" && echo -e " ${GREEN}✓${NC} Updated src/orchestrator/workflow.py" || echo -e " ${RED}✗${NC} Failed to update src/orchestrator/workflow.py"
    fi
    
    # Update src/sbom/generator.py - SWID tag version attribute
    FILE="$PROJECT_ROOT/src/sbom/generator.py"
    if [ -f "$FILE" ]; then
        sed -i.bak -E "s/\"@version\": \"[0-9]+\.[0-9]+\.[0-9]+\"/\"@version\": \"${NEW_VERSION}\"/g" "$FILE" && rm "${FILE}.bak" && echo -e " ${GREEN}✓${NC} Updated src/sbom/generator.py (SWID tag version)" || echo -e " ${RED}✗${NC} Failed to update src/sbom/generator.py"
    fi
    
    # Update telemetry-agent/collector.py
    FILE="$PROJECT_ROOT/telemetry-agent/collector.py"
    if [ -f "$FILE" ]; then
        sed -i.bak -E "s/\"agent_version\": \"[0-9]+\.[0-9]+\.[0-9]+\"/\"agent_version\": \"${NEW_VERSION}\"/g" "$FILE" && rm "${FILE}.bak" && echo -e " ${GREEN}✓${NC} Updated telemetry-agent/collector.py" || echo -e " ${RED}✗${NC} Failed to update telemetry-agent/collector.py"
    fi
    
    # Update telemetry-agent/transport.py
    FILE="$PROJECT_ROOT/telemetry-agent/transport.py"
    if [ -f "$FILE" ]; then
        sed -i.bak -E "s/\"agent_version\": \"[0-9]+\.[0-9]+\.[0-9]+\"/\"agent_version\": \"${NEW_VERSION}\"/g" "$FILE" && rm "${FILE}.bak" && echo -e " ${GREEN}✓${NC} Updated telemetry-agent/transport.py" || echo -e " ${RED}✗${NC} Failed to update telemetry-agent/transport.py"
    fi
    
    # Update k8s/api.yaml
    FILE="$PROJECT_ROOT/k8s/api.yaml"
    if [ -f "$FILE" ]; then
        sed -i.bak -E "s/VERSION: \"[0-9]+\.[0-9]+\.[0-9]+\"/VERSION: \"${NEW_VERSION}\"/g" "$FILE" && rm "${FILE}.bak" && echo -e " ${GREEN}✓${NC} Updated k8s/api.yaml" || echo -e " ${RED}✗${NC} Failed to update k8s/api.yaml"
    fi
    
    # Update README.md
    FILE="$PROJECT_ROOT/README.md"
    if [ -f "$FILE" ]; then
        sed -i.bak -E "s/Perseus-v[0-9]+\.[0-9]+\.[0-9]+/Perseus-v${NEW_VERSION}/g" "$FILE" && rm "${FILE}.bak" && echo -e " ${GREEN}✓${NC} Updated README.md" || echo -e " ${RED}✗${NC} Failed to update README.md"
    fi
    
    # Update src/vulnerability/grype_scanner.py - Only Perseus platform version in tools metadata
    FILE="$PROJECT_ROOT/src/vulnerability/grype_scanner.py"
    if [ -f "$FILE" ]; then
        # Update only the specific tool version references, not all version strings
        sed -i.bak -E "s/(\"tools\": \[\{\"name\": \"sbom-platform\", \"version\": \")[0-9]+\.[0-9]+\.[0-9]+(\")/\1${NEW_VERSION}\2/g; s/(\"tools\": \[\{\"name\": \"perseus-sbom-platform\", \"version\": \")[0-9]+\.[0-9]+\.[0-9]+(\")/\1${NEW_VERSION}\2/g" "$FILE" && rm "${FILE}.bak" && echo -e " ${GREEN}✓${NC} Updated src/vulnerability/grype_scanner.py (tool versions)" || echo -e " ${RED}✗${NC} Failed to update src/vulnerability/grype_scanner.py"
    fi
}

# Function to rebuild containers
rebuild_containers() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Rebuilding Containers${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed. Please install Docker to rebuild containers.${NC}"
        return 1
    fi
    
    # Check if docker-compose.yml exists
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        echo -e "${BLUE}Using docker-compose for rebuild...${NC}"
        
        # Stop existing containers
        echo -e "${YELLOW}Stopping existing containers...${NC}"
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" down || true
        
        # Build new containers
        echo -e "${YELLOW}Building new containers...${NC}"
        if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" build --no-cache; then
            echo -e "${GREEN}✓ Containers rebuilt successfully${NC}"
            
            # Start containers if in development environment
            if [ "$ENVIRONMENT" = "development" ] || [ -z "$ENVIRONMENT" ]; then
                echo -e "${YELLOW}Starting containers in development mode...${NC}"
                if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up -d; then
                    echo -e "${GREEN}✓ Containers started successfully${NC}"
                else
                    echo -e "${RED}✗ Failed to start containers${NC}"
                fi
            fi
        else
            echo -e "${RED}✗ Failed to rebuild containers${NC}"
            return 1
        fi
    elif [ -f "$PROJECT_ROOT/Dockerfile" ]; then
        echo -e "${BLUE}Using Docker for rebuild...${NC}"
        
        # Build the main image
        echo -e "${YELLOW}Building Docker image...${NC}"
        NEW_VERSION=$(jq -r '.version.string' "$VERSION_FILE")
        if docker build -t "perseus-sbom:${NEW_VERSION}" -t "perseus-sbom:latest" "$PROJECT_ROOT"; then
            echo -e "${GREEN}✓ Docker image built successfully${NC}"
            echo -e "${GREEN}Tagged as: perseus-sbom:${NEW_VERSION} and perseus-sbom:latest${NC}"
        else
            echo -e "${RED}✗ Failed to build Docker image${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ No docker-compose.yml or Dockerfile found in project root${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Usage function
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  show          Display current version (default)"
    echo "  build         Increment build version (X.Y.Z → X.Y.Z+1)"
    echo "  minor         Increment minor version (X.Y.Z → X.Y+1.0)"
    echo "  major         Increment major version (X.Y.Z → X+1.0.0)"
    echo "  set VERSION   Set specific version (e.g., 2.0.0)"
    echo ""
    echo "Options:"
    echo "  -e ENV        Set environment (development/production/staging)"
    echo "  -r, --rebuild Trigger container rebuild after version change"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Show current version"
    echo "  $0 build              # Increment build: 1.6.1 → 1.6.2"
    echo "  $0 minor -e staging   # Increment minor and set staging env"
    echo "  $0 set 2.0.0         # Set specific version"
    echo "  $0 minor --rebuild    # Increment minor and rebuild containers"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed. Please install jq to use this script.${NC}"
    echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi

# Parse command
COMMAND="${1:-show}"

# Handle help as a command
if [ "$COMMAND" = "--help" ] || [ "$COMMAND" = "-h" ] || [ "$COMMAND" = "help" ]; then
    usage
    exit 0
fi

shift || true

# Parse options
ENVIRONMENT=""
REBUILD_CONTAINERS=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--rebuild)
            REBUILD_CONTAINERS=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            if [ "$COMMAND" = "set" ]; then
                NEW_VERSION="$1"
                shift
            else
                echo -e "${RED}Unknown option: $1${NC}"
                usage
                exit 1
            fi
            ;;
    esac
done

# Execute command
case $COMMAND in
    show)
        display_version
        ;;
        
    build|minor|major)
        # Read current version
        CURRENT_VERSION=$(jq -r '.version.string' "$VERSION_FILE")
        echo -e "${BLUE}Current version: $CURRENT_VERSION${NC}"
        
        # Update version.json
        TMP_FILE=$(mktemp)
        
        if [ "$COMMAND" = "major" ]; then
            jq '.version.major += 1 | .version.minor = 0 | .version.build = 0' "$VERSION_FILE" > "$TMP_FILE"
        elif [ "$COMMAND" = "minor" ]; then
            jq '.version.minor += 1 | .version.build = 0' "$VERSION_FILE" > "$TMP_FILE"
        elif [ "$COMMAND" = "build" ]; then
            jq '.version.build += 1' "$VERSION_FILE" > "$TMP_FILE"
        fi
        
        # Update version string and timestamp
        jq '.version.string = "\(.version.major).\(.version.minor).\(.version.build)" | .build_info.timestamp = (now | todate)' "$TMP_FILE" > "${TMP_FILE}.2"
        mv "${TMP_FILE}.2" "$TMP_FILE"
        
        # Update environment if specified
        if [ -n "$ENVIRONMENT" ]; then
            jq --arg env "$ENVIRONMENT" '.build_info.environment = $env' "$TMP_FILE" > "${TMP_FILE}.2"
            mv "${TMP_FILE}.2" "$TMP_FILE"
        fi
        
        # Save and get new version
        mv "$TMP_FILE" "$VERSION_FILE"
        NEW_VERSION=$(jq -r '.version.string' "$VERSION_FILE")
        
        echo -e "${GREEN}✓ Updated config/version.json${NC}"
        echo -e "${GREEN}Version updated to: $NEW_VERSION${NC}"
        
        # Update all version locations
        update_all_files "$NEW_VERSION"
        
        echo ""
        echo -e "${GREEN}Version update complete!${NC}"
        echo -e "${YELLOW}The web dashboard will automatically show the new version.${NC}"
        
        # Rebuild containers if requested
        if [ "$REBUILD_CONTAINERS" = true ]; then
            rebuild_containers
        else
            echo -e "${YELLOW}Remember to rebuild and redeploy if needed.${NC}"
        fi
        ;;
        
    set)
        if [ -z "$NEW_VERSION" ]; then
            echo -e "${RED}Error: Version required for 'set' command${NC}"
            usage
            exit 1
        fi
        
        # Validate version format
        if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo -e "${RED}Error: Version must be in format X.Y.Z${NC}"
            exit 1
        fi
        
        # Parse version parts
        IFS='.' read -r major minor build <<< "$NEW_VERSION"
        
        CURRENT_VERSION=$(jq -r '.version.string' "$VERSION_FILE")
        echo -e "${BLUE}Current version: $CURRENT_VERSION${NC}"
        
        # Update version.json
        TMP_FILE=$(mktemp)
        jq --arg major "$major" \
           --arg minor "$minor" \
           --arg build "$build" \
           --arg version "$NEW_VERSION" \
           '.version.major = ($major | tonumber) |
            .version.minor = ($minor | tonumber) |
            .version.build = ($build | tonumber) |
            .version.string = $version |
            .build_info.timestamp = (now | todate)' "$VERSION_FILE" > "$TMP_FILE"
        
        # Update environment if specified
        if [ -n "$ENVIRONMENT" ]; then
            jq --arg env "$ENVIRONMENT" '.build_info.environment = $env' "$TMP_FILE" > "${TMP_FILE}.2"
            mv "${TMP_FILE}.2" "$TMP_FILE"
        fi
        
        mv "$TMP_FILE" "$VERSION_FILE"
        
        echo -e "${GREEN}✓ Updated config/version.json${NC}"
        echo -e "${GREEN}Version set to: $NEW_VERSION${NC}"
        
        # Update all version locations
        update_all_files "$NEW_VERSION"
        
        echo ""
        echo -e "${GREEN}Version update complete!${NC}"
        
        # Rebuild containers if requested
        if [ "$REBUILD_CONTAINERS" = true ]; then
            rebuild_containers
        fi
        ;;
        
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        usage
        exit 1
        ;;
esac