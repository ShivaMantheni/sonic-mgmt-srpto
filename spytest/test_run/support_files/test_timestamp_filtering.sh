#!/bin/bash

# Test script to verify timestamp filtering in consolidation

echo "=============================================="
echo " Testing Timestamp Filtering"
echo "=============================================="
echo ""

# Create test log directory
TEST_LOG_ROOT="/tmp/test_consolidation_timestamp"
rm -rf "${TEST_LOG_ROOT}"
mkdir -p "${TEST_LOG_ROOT}"

# Create some old batch directories (4 hours ago)
echo "Creating old batch directories (simulating previous run)..."
OLD_BATCH1="${TEST_LOG_ROOT}/BGP_NEG_FLAP_RR"
OLD_BATCH2="${TEST_LOG_ROOT}/OSPF_ISCLI_MASTER"
mkdir -p "${OLD_BATCH1}/173100"
mkdir -p "${OLD_BATCH2}/173100"

# Set modification time to 4 hours ago
FOUR_HOURS_AGO=$(date -d '4 hours ago' +%s)
touch -d "@${FOUR_HOURS_AGO}" "${OLD_BATCH1}"
touch -d "@${FOUR_HOURS_AGO}" "${OLD_BATCH2}"

echo "  Created: ${OLD_BATCH1} (mtime: $(date -d @${FOUR_HOURS_AGO}))"
echo "  Created: ${OLD_BATCH2} (mtime: $(date -d @${FOUR_HOURS_AGO}))"
echo ""

# Create some new batch directories (current time)
echo "Creating new batch directories (simulating current run)..."
NEW_BATCH1="${TEST_LOG_ROOT}/LLDP_COMPREHENSIVE"
NEW_BATCH2="${TEST_LOG_ROOT}/SM_ISCLI_52_LLDP_CLI_VALIDATION"
mkdir -p "${NEW_BATCH1}/215100"
mkdir -p "${NEW_BATCH2}/214600"

echo "  Created: ${NEW_BATCH1} (mtime: $(date))"
echo "  Created: ${NEW_BATCH2} (mtime: $(date))"
echo ""

# Create dummy CSV files in new batches
cat > "${NEW_BATCH1}/215100/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_lldp_01.py,test_lldp_basic,Pass,0:00:30,2026-06-05 21:51:00,0,1,1,2,LLDP basic test,"D1, D2",,
EOF

cat > "${NEW_BATCH2}/214600/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_lldp_cli.py,test_lldp_help_command,Pass,0:00:18,2026-06-05 21:46:00,0,1,1,2,Test LLDP help command,"D1, D2",,
EOF

# Capture current timestamp (simulating execution start)
EXECUTION_START=$(date +%s)
echo "=============================================="
echo " Simulated Execution Start"
echo " Timestamp: ${EXECUTION_START}"
echo " Time: $(date -d @${EXECUTION_START})"
echo "=============================================="
echo ""

# Wait 1 second to ensure directory timestamps are captured correctly
sleep 1

# List all directories with their timestamps
echo "=============================================="
echo " All Batch Directories (before consolidation)"
echo "=============================================="
for dir in "${TEST_LOG_ROOT}"/*; do
    if [ -d "$dir" ]; then
        mtime=$(stat -c %Y "$dir")
        mtime_str=$(date -d @${mtime} "+%Y-%m-%d %H:%M:%S")
        name=$(basename "$dir")
        age=$((EXECUTION_START - mtime))

        if [ $age -gt 0 ]; then
            echo "  ⏰ ${name} (modified: ${mtime_str}, ${age}s before start)"
        else
            echo "  ✓ ${name} (modified: ${mtime_str})"
        fi
    fi
done
echo ""

# Test WITHOUT timestamp filtering
echo "=============================================="
echo " TEST 1: Without Timestamp Filtering"
echo "=============================================="
echo ""
python3 dashboard/scripts/consolidate_feature_logs.py \
    --log-root "${TEST_LOG_ROOT}" \
    --consolidate

echo ""
echo "Result: Feature directories created:"
ls -la "${TEST_LOG_ROOT}/" | grep -E "BGP|OSPF|LLDP" || echo "  (none)"
echo ""

# Clean up feature directories for next test
rm -rf "${TEST_LOG_ROOT}/BGP" "${TEST_LOG_ROOT}/OSPF" "${TEST_LOG_ROOT}/LLDP"

# Test WITH timestamp filtering
echo "=============================================="
echo " TEST 2: With Timestamp Filtering"
echo " (min-timestamp: ${EXECUTION_START})"
echo "=============================================="
echo ""
python3 dashboard/scripts/consolidate_feature_logs.py \
    --log-root "${TEST_LOG_ROOT}" \
    --consolidate \
    --min-timestamp "${EXECUTION_START}"

echo ""
echo "Result: Feature directories created:"
ls -la "${TEST_LOG_ROOT}/" | grep -E "BGP|OSPF|LLDP" || echo "  (none)"
echo ""

# Verify expected results
echo "=============================================="
echo " Verification"
echo "=============================================="

if [ -d "${TEST_LOG_ROOT}/LLDP" ]; then
    echo "✓ PASS: LLDP directory created (expected)"
else
    echo "✗ FAIL: LLDP directory NOT created (unexpected)"
fi

if [ ! -d "${TEST_LOG_ROOT}/BGP" ]; then
    echo "✓ PASS: BGP directory NOT created (expected - filtered out)"
else
    echo "✗ FAIL: BGP directory created (unexpected - should be filtered)"
fi

if [ ! -d "${TEST_LOG_ROOT}/OSPF" ]; then
    echo "✓ PASS: OSPF directory NOT created (expected - filtered out)"
else
    echo "✗ FAIL: OSPF directory created (unexpected - should be filtered)"
fi

echo ""
echo "=============================================="
echo " Test Complete"
echo "=============================================="
echo "Test log root: ${TEST_LOG_ROOT}"
echo "To inspect results: ls -la ${TEST_LOG_ROOT}/"
echo "To clean up: rm -rf ${TEST_LOG_ROOT}"
