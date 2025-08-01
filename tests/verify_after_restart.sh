#!/bin/bash
# Script to verify rate limiting after server restart

echo "=== RATE LIMIT VERIFICATION AFTER RESTART ==="
echo ""

# Step 1: Check if new endpoints exist
echo "1. Checking if server has new endpoints..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/rate-limit-status)
if [ "$STATUS_CODE" = "200" ]; then
    echo "   ✅ New endpoints are available - server restarted successfully"
else
    echo "   ❌ New endpoints not found (HTTP $STATUS_CODE) - server needs restart"
    echo "   Please restart the server and run this script again"
    exit 1
fi

# Step 2: Clear rate limits
echo ""
echo "2. Clearing rate limits..."
curl -s -X POST http://localhost:8000/admin/clear-rate-limits | python -m json.tool

# Step 3: Check initial state
echo ""
echo "3. Initial rate limit state:"
curl -s http://localhost:8000/admin/rate-limit-status | python -m json.tool

# Step 4: Run the comprehensive test
echo ""
echo "4. Running comprehensive rate limit test..."
python tests/final_rate_limit_test.py

# Step 5: Run stress test with proper rate
echo ""
echo "5. Running stress test with 8 requests (under limit)..."
python tests/stress_test.py 8

echo ""
echo "=== VERIFICATION COMPLETE ==="