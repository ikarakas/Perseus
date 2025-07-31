#!/bin/bash

# Stress test script for SBOM Platform
# Tests concurrent requests across different analysis types

BASE_URL="http://localhost:8000"
NUM_CONCURRENT=${1:-15}
LOG_FILE="stress_test_results_$(date +%Y%m%d_%H%M%S).json"

echo "🚀 Starting stress test with $NUM_CONCURRENT concurrent requests..."
echo "📝 Results will be logged to: $LOG_FILE"

# Create results file
echo "[]" > "$LOG_FILE"

# Define test cases
declare -a TEST_CASES=(
    "analyze/binary|{\"location\":\"/app/data/sample-macos-app/sample-macos-static-app\",\"type\":\"binary\",\"analyzer\":\"syft\",\"options\":{}}|binary_analysis"
    "analyze/docker|{\"location\":\"alpine:3.18\",\"type\":\"docker\",\"analyzer\":\"syft\",\"options\":{}}|docker_alpine"
    "analyze/source|{\"location\":\"/app/data/sample-java-project\",\"type\":\"source\",\"analyzer\":\"syft\",\"options\":{}}|source_java"
    "analyze/docker|{\"location\":\"mysql:8.0\",\"type\":\"docker\",\"analyzer\":\"syft\",\"options\":{}}|docker_mysql"
)

# Function to make a single request
make_request() {
    local test_num=$1
    local endpoint=$2
    local data=$3
    local test_name=$4
    
    echo "📤 Starting request $test_num: $test_name"
    
    local start_time=$(date +%s.%N)
    local response=$(curl -s -w "\n%{http_code}\n%{time_total}" \
        -X POST "$BASE_URL/$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data" 2>/dev/null)
    local end_time=$(date +%s.%N)
    
    # Parse response
    local body=$(echo "$response" | head -n -2)
    local http_code=$(echo "$response" | tail -n 2 | head -n 1)
    local curl_time=$(echo "$response" | tail -n 1)
    local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    # Extract analysis_id if successful
    local analysis_id=""
    if [[ $http_code == "200" ]]; then
        analysis_id=$(echo "$body" | grep -o '"analysis_id":"[^"]*"' | cut -d'"' -f4)
        echo "✅ Request $test_num completed successfully: $analysis_id"
    else
        echo "❌ Request $test_num failed with HTTP $http_code"
    fi
    
    # Log result
    echo "$test_num|$test_name|$http_code|$duration|$analysis_id|$body" >> "temp_results.txt"
}

# Create temp file for results
> temp_results.txt

# Launch concurrent requests
echo "📤 Launching $NUM_CONCURRENT concurrent requests..."
START_TIME=$(date +%s.%N)

# Launch background processes
for i in $(seq 1 $NUM_CONCURRENT); do
    test_case_index=$(( (i - 1) % ${#TEST_CASES[@]} ))
    test_case="${TEST_CASES[$test_case_index]}"
    
    IFS='|' read -r endpoint data test_name <<< "$test_case"
    
    make_request "$i" "$endpoint" "$data" "${test_name}_$i" &
done

# Wait for all requests to complete
wait
REQUEST_TIME=$(echo "$(date +%s.%N) - $START_TIME" | bc -l)

echo "⏱️  All requests completed in ${REQUEST_TIME}s"

# Process results
echo "📊 Processing results..."
successful=0
failed=0
analysis_ids=()

while IFS='|' read -r test_num test_name http_code duration analysis_id body; do
    if [[ $http_code == "200" ]]; then
        ((successful++))
        if [[ -n "$analysis_id" ]]; then
            analysis_ids+=("$analysis_id")
        fi
    else
        ((failed++))
    fi
done < temp_results.txt

echo "📊 Request Results:"
echo "   ✅ Successful: $successful/$NUM_CONCURRENT"
echo "   ❌ Failed: $failed/$NUM_CONCURRENT"
echo "   ⏱️  Request Time: ${REQUEST_TIME}s"

# Wait for analyses to complete
echo "⏳ Waiting for analyses to complete..."
sleep 10

# Check final results
echo "🔍 Checking analysis completion..."
analyses_response=$(curl -s "$BASE_URL/api/v1/analyses" 2>/dev/null)

if [[ -n "$analyses_response" ]]; then
    # Count completed and failed analyses for our test
    completed=0
    analysis_failed=0
    total_components=0
    total_vulnerabilities=0
    
    # Simple parsing for our analysis IDs
    for analysis_id in "${analysis_ids[@]}"; do
        if echo "$analyses_response" | grep -q "\"analysis_id\":\"$analysis_id\""; then
            if echo "$analyses_response" | grep -A 5 "\"analysis_id\":\"$analysis_id\"" | grep -q "\"status\":\"completed\""; then
                ((completed++))
                # Extract component and vulnerability counts (simplified)
                component_count=$(echo "$analyses_response" | grep -A 10 "\"analysis_id\":\"$analysis_id\"" | grep -o '"component_count":[0-9]*' | cut -d':' -f2 || echo "0")
                vulnerability_count=$(echo "$analyses_response" | grep -A 10 "\"analysis_id\":\"$analysis_id\"" | grep -o '"vulnerability_count":[0-9]*' | cut -d':' -f2 || echo "0")
                total_components=$((total_components + component_count))
                total_vulnerabilities=$((total_vulnerabilities + vulnerability_count))
            elif echo "$analyses_response" | grep -A 5 "\"analysis_id\":\"$analysis_id\"" | grep -q "\"status\":\"failed\""; then
                ((analysis_failed++))
            fi
        fi
    done
    
    total_analyses=${#analysis_ids[@]}
    
    echo "🎯 Final Results:"
    echo "   📊 Analyses Completed: $completed/$total_analyses"
    echo "   ❌ Analyses Failed: $analysis_failed/$total_analyses"
    echo "   🧩 Total Components Found: $total_components"
    echo "   🔍 Total Vulnerabilities Found: $total_vulnerabilities"
    
    # Calculate success rates
    if [[ $NUM_CONCURRENT -gt 0 ]]; then
        request_success_rate=$(echo "scale=1; $successful * 100 / $NUM_CONCURRENT" | bc -l)
    else
        request_success_rate=0
    fi
    
    if [[ $total_analyses -gt 0 ]]; then
        completion_rate=$(echo "scale=1; $completed * 100 / $total_analyses" | bc -l)
    else
        completion_rate=0
    fi
    
    avg_request_time=$(echo "scale=3; $REQUEST_TIME / $NUM_CONCURRENT" | bc -l)
    
    echo "📈 Performance Metrics:"
    echo "   🎯 Request Success Rate: ${request_success_rate}%"
    echo "   ✅ Analysis Completion Rate: ${completion_rate}%"
    echo "   ⚡ Avg Request Time: ${avg_request_time}s"
    
    # Success criteria
    success_threshold=95
    if (( $(echo "$request_success_rate >= $success_threshold" | bc -l) )) && (( $(echo "$completion_rate >= $success_threshold" | bc -l) )); then
        echo "✅ STRESS TEST PASSED!"
        exit_code=0
    else
        echo "❌ STRESS TEST FAILED!"
        exit_code=1
    fi
else
    echo "❌ Failed to get analysis results"
    exit_code=1
fi

# Cleanup
rm -f temp_results.txt

echo "📝 Detailed results saved to: $LOG_FILE"
exit $exit_code