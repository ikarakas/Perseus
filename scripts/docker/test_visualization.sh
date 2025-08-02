#!/bin/bash
# Test script for SBOM visualization feature

echo "🧪 Testing SBOM Visualization Feature"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# API base URL
API_URL="http://localhost:8000"

echo -e "${YELLOW}1. Getting list of available SBOMs...${NC}"
SBOMS=$(curl -s "${API_URL}/api/v1/dashboard/sboms/all?limit=1")

# Extract first SBOM ID
SBOM_ID=$(echo "$SBOMS" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['sboms'][0]['sbom_id'] if data['sboms'] else '')")

if [ -z "$SBOM_ID" ]; then
    echo -e "${RED}❌ No SBOMs found! Please generate an SBOM first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found SBOM: ${SBOM_ID}${NC}"

echo -e "\n${YELLOW}2. Triggering visualization generation...${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/sboms/${SBOM_ID}/visualize")

echo "Response: $RESPONSE"

# Extract HTML URL from response
HTML_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('html_url', ''))")

if [ -z "$HTML_URL" ]; then
    echo -e "${RED}❌ Failed to get visualization URL${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Visualization URL: ${API_URL}${HTML_URL}${NC}"

echo -e "\n${YELLOW}3. Waiting for visualization to be generated...${NC}"
sleep 3

echo -e "\n${YELLOW}4. Checking if visualization is accessible...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}${HTML_URL}")

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Visualization is ready!${NC}"
    echo -e "${GREEN}📊 Open in browser: ${API_URL}${HTML_URL}${NC}"
else
    echo -e "${RED}❌ Visualization not accessible (HTTP ${HTTP_STATUS})${NC}"
    echo "Checking visualization directory..."
    docker exec sbom-api-1 ls -la /app/data/visualizations/
fi

echo -e "\n${GREEN}✨ Test complete!${NC}"