#!/bin/bash
# Test script to verify tool paths work correctly

echo "=== Tool Path Detection Test ==="
echo

# Check environment
if [ -f "/.dockerenv" ] || [ "$CONTAINER_ENV" = "true" ]; then
    echo "Running in container: YES"
else
    echo "Running in container: NO"
fi

echo "SYFT_PATH env: ${SYFT_PATH:-Not set}"
echo "GRYPE_PATH env: ${GRYPE_PATH:-Not set}"
echo

# Test Syft
echo "=== Testing Syft ==="
which_syft=$(which syft 2>/dev/null)
if [ -n "$which_syft" ]; then
    echo "✓ Found syft via which: $which_syft"
    $which_syft version 2>&1 | head -1
else
    echo "✗ Syft not found via which"
fi

# Check common locations
for path in /usr/local/bin/syft /opt/homebrew/bin/syft /usr/bin/syft; do
    if [ -x "$path" ]; then
        echo "✓ Found syft at: $path"
        $path version 2>&1 | head -1
        break
    fi
done
echo

# Test Grype
echo "=== Testing Grype ==="
which_grype=$(which grype 2>/dev/null)
if [ -n "$which_grype" ]; then
    echo "✓ Found grype via which: $which_grype"
    $which_grype version 2>&1 | head -1
else
    echo "✗ Grype not found via which"
fi

# Check common locations
for path in /usr/local/bin/grype /opt/homebrew/bin/grype /usr/bin/grype; do
    if [ -x "$path" ]; then
        echo "✓ Found grype at: $path"
        $path version 2>&1 | head -1
        break
    fi
done
echo

echo "=== Test Complete ==="