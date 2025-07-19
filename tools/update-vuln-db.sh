#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
# Update Grype vulnerability database for offline operation

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 Updating Grype Vulnerability Database${NC}"
echo "This requires internet connection and will download ~1.2GB of data"

# Check if container is running
if ! docker ps | grep -q sbom-sbom-platform-1; then
    echo -e "${RED}❌ Error: SBOM platform container is not running${NC}"
    echo "Please start the container first: docker-compose up -d"
    exit 1
fi

# Get current database status
echo -e "\n${YELLOW}📊 Current Database Status:${NC}"
docker exec sbom-sbom-platform-1 sh -c \
    "GRYPE_DB_CACHE_DIR=/app/data/grype-db grype db status"

# Update database
echo -e "\n${YELLOW}⬇️  Downloading latest vulnerability database...${NC}"
docker exec sbom-sbom-platform-1 sh -c \
    "GRYPE_DB_CACHE_DIR=/app/data/grype-db grype db update"

# Verify update
echo -e "\n${GREEN}✅ Database Updated Successfully!${NC}"
echo -e "\n${YELLOW}📊 New Database Status:${NC}"
docker exec sbom-sbom-platform-1 sh -c \
    "GRYPE_DB_CACHE_DIR=/app/data/grype-db grype db status"

# Show database location for backup
DB_PATH="./data/grype-db"
DB_SIZE=$(du -sh $DB_PATH 2>/dev/null | cut -f1 || echo "N/A")
echo -e "\n${YELLOW}💾 Database Location:${NC} $DB_PATH"
echo -e "${YELLOW}📦 Database Size:${NC} $DB_SIZE"
echo -e "\n${GREEN}✅ The vulnerability database is now updated and ready for offline use!${NC}"
echo -e "${YELLOW}💡 Tip:${NC} You can backup the database by copying the $DB_PATH directory"