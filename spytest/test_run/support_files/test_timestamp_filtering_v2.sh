#!/bin/bash

# Better test to simulate the actual scenario

echo "=============================================="
echo " Testing Timestamp Filtering - Real Scenario"
echo "=============================================="
echo ""

# Create test log directory
TEST_LOG_ROOT="/tmp/test_consolidation_v2"
rm -rf "${TEST_LOG_ROOT}"
mkdir -p "${TEST_LOG_ROOT}"

# SCENARIO: Old batch directories from a previous execution
echo "Step 1: Creating old batch directories (from 4 hours ago)..."
OLD_BATCH1="${TEST_LOG_ROOT}/BGP_NEG_FLAP_RR"
OLD_BATCH2="${TEST_LOG_ROOT}/OSPF_ISCLI_MASTER"
mkdir -p "${OLD_BATCH1}/173100"
mkdir -p "${OLD_BATCH2}/173100"

# Create dummy CSV in old batches
cat > "${OLD_BATCH1}/173100/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_bgp.py,test_bgp_basic,Pass,0:01:00,2026-06-05 17:31:00,0,1,1,2,BGP basic test,"D1, D2",,
EOF

# Set modification time to 4 hours ago
FOUR_HOURS_AGO=$(date -d '4 hours ago' +%Y%m%d%H%M.%S)
touch -t "${FOUR_HOURS_AGO}" "${OLD_BATCH1}"
touch -t "${FOUR_HOURS_AGO}" "${OLD_BATCH2}"

echo "  Created: BGP_NEG_FLAP_RR (4 hours ago)"
echo "  Created: OSPF_ISCLI_MASTER (4 hours ago)"
echo ""

# SCENARIO: Capture execution start time (simulating when user starts LLDP-only execution)
EXECUTION_START=$(date +%s)
echo "Step 2: Simulating execution start (user runs: --features LLDP)"
echo "  Timestamp: ${EXECUTION_START}"
echo "  Time: $(date -d @${EXECUTION_START})"
echo ""

# Wait a moment to ensure new directories have later timestamps
sleep 2

# SCENARIO: New batch directories created during LLDP execution
echo "Step 3: Creating new LLDP batch directories (current execution)..."
NEW_BATCH1="${TEST_LOG_ROOT}/LLDP_COMPREHENSIVE"
NEW_BATCH2="${TEST_LOG_ROOT}/SM_ISCLI_52_LLDP_CLI_VALIDATION"
NEW_BATCH3="${TEST_LOG_ROOT}/SM_ISCLI_P2_161_162_LLDP_CLI_FIX"
mkdir -p "${NEW_BATCH1}/215100"
mkdir -p "${NEW_BATCH2}/214600"
mkdir -p "${NEW_BATCH3}/214900"

cat > "${NEW_BATCH1}/215100/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_lldp_01.py,test_lldp_basic,Pass,0:00:30,2026-06-05 21:51:00,0,1,1,2,LLDP basic test,"D1, D2",,
EOF

cat > "${NEW_BATCH2}/214600/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_lldp_cli.py,test_lldp_help_command,Pass,0:00:18,2026-06-05 21:46:00,0,1,1,2,Test LLDP help,"D1, D2",,
EOF

cat > "${NEW_BATCH3}/214900/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_lldp_fix.py,test_lldp_cli_fix,TopoFail,0:00:00,2026-06-05 21:49:00,0,1,1,2,LLDP CLI fix,"D1, D2",,
EOF

echo "  Created: LLDP_COMPREHENSIVE (now)"
echo "  Created: SM_ISCLI_52_LLDP_CLI_VALIDATION (now)"
echo "  Created: SM_ISCLI_P2_161_162_LLDP_CLI_FIX (now)"
echo ""

# Show directory listing with timestamps
echo "=============================================="
echo " Current State (before consolidation)"
echo "=============================================="
for dir in "${TEST_LOG_ROOT}"/*; do
    if [ -d "$dir" ]; then
        mtime=$(stat -c %Y "$dir")
        name=$(basename "$dir")
        age=$(($(date +%s) - mtime))
        mtime_str=$(date -d @${mtime} "+%Y-%m-%d %H:%M:%S")

        if [ $mtime -lt $EXECUTION_START ]; then
            echo "  🕰️  OLD: ${name} (modified: ${mtime_str})"
        else
            echo "  ✅ NEW: ${name} (modified: ${mtime_str})"
        fi
    fi
done
echo ""

# Test WITHOUT timestamp filtering (CURRENT PROBLEMATIC BEHAVIOR)
echo "=============================================="
echo " TEST 1: WITHOUT Timestamp Filtering"
echo " (Current behavior - consolidates everything)"
echo "=============================================="
echo ""

python3 dashboard/scripts/consolidate_feature_logs.py \
    --log-root "${TEST_LOG_ROOT}" \
    --consolidate 2>&1 | grep -E "(Found|Batches:|feature|Moved|Created|Summary)"

echo ""
echo "Result: Feature directories created:"
ls -d "${TEST_LOG_ROOT}"/*/ 2>/dev/null | grep -E "BGP|OSPF|LLDP" | xargs -I {} basename {}
echo ""

# Verify Issue #3 from user report
echo "Verification (Issue #3):"
if [ -d "${TEST_LOG_ROOT}/BGP" ]; then
    echo "  ❌ BGP directory created (PROBLEM: shouldn't exist for LLDP-only execution)"
else
    echo "  ✅ BGP directory NOT created"
fi

if [ -d "${TEST_LOG_ROOT}/OSPF" ]; then
    echo "  ❌ OSPF directory created (PROBLEM: shouldn't exist for LLDP-only execution)"
else
    echo "  ✅ OSPF directory NOT created"
fi

if [ -d "${TEST_LOG_ROOT}/LLDP" ]; then
    echo "  ✅ LLDP directory created (expected)"
else
    echo "  ❌ LLDP directory NOT created"
fi
echo ""

# Reset for next test
rm -rf "${TEST_LOG_ROOT}"
mkdir -p "${TEST_LOG_ROOT}"

# Recreate old directories
mkdir -p "${OLD_BATCH1}/173100"
mkdir -p "${OLD_BATCH2}/173100"
cat > "${OLD_BATCH1}/173100/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_bgp.py,test_bgp_basic,Pass,0:01:00,2026-06-05 17:31:00,0,1,1,2,BGP basic test,"D1, D2",,
EOF
touch -t "${FOUR_HOURS_AGO}" "${OLD_BATCH1}"
touch -t "${FOUR_HOURS_AGO}" "${OLD_BATCH2}"

# Recreate new directories
sleep 2
mkdir -p "${NEW_BATCH1}/215100"
mkdir -p "${NEW_BATCH2}/214600"
mkdir -p "${NEW_BATCH3}/214900"
cat > "${NEW_BATCH1}/215100/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_lldp_01.py,test_lldp_basic,Pass,0:00:30,2026-06-05 21:51:00,0,1,1,2,LLDP basic test,"D1, D2",,
EOF
cat > "${NEW_BATCH2}/214600/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_lldp_cli.py,test_lldp_help_command,Pass,0:00:18,2026-06-05 21:46:00,0,1,1,2,Test LLDP help,"D1, D2",,
EOF
cat > "${NEW_BATCH3}/214900/results_test_functions.csv" << 'EOF'
#,Module,TestFunction,Result,TimeTaken,ExecutedOn,Syslogs,FCLI,TSSH,DCNT,Description,Devices,KnownIssue,Doc
1,test_lldp_fix.py,test_lldp_cli_fix,TopoFail,0:00:00,2026-06-05 21:49:00,0,1,1,2,LLDP CLI fix,"D1, D2",,
EOF

# Test WITH timestamp filtering (NEW FIXED BEHAVIOR)
echo "=============================================="
echo " TEST 2: WITH Timestamp Filtering"
echo " (Fixed behavior - only current execution)"
echo " Min-timestamp: ${EXECUTION_START}"
echo "=============================================="
echo ""

python3 dashboard/scripts/consolidate_feature_logs.py \
    --log-root "${TEST_LOG_ROOT}" \
    --consolidate \
    --min-timestamp "${EXECUTION_START}" 2>&1 | grep -E "(Found|Skipped|Batches:|feature|Moved|Created|Summary|⊘|⏭)"

echo ""
echo "Result: Feature directories created:"
ls -d "${TEST_LOG_ROOT}"/*/ 2>/dev/null | grep -E "BGP|OSPF|LLDP" | xargs -I {} basename {}
echo ""

# Final verification
echo "=============================================="
echo " Final Verification (Issue #3 FIXED)"
echo "=============================================="

if [ ! -d "${TEST_LOG_ROOT}/BGP" ]; then
    echo "  ✅ PASS: BGP directory NOT created (correctly filtered out old batch)"
else
    echo "  ❌ FAIL: BGP directory created (timestamp filtering failed)"
fi

if [ ! -d "${TEST_LOG_ROOT}/OSPF" ]; then
    echo "  ✅ PASS: OSPF directory NOT created (correctly filtered out old batch)"
else
    echo "  ❌ FAIL: OSPF directory created (timestamp filtering failed)"
fi

if [ -d "${TEST_LOG_ROOT}/LLDP" ]; then
    echo "  ✅ PASS: LLDP directory created (current execution included)"
    echo ""
    echo "  LLDP contains:"
    ls -1 "${TEST_LOG_ROOT}/LLDP/" | grep -v "\.csv\|\.json" | sed 's/^/    - /'
else
    echo "  ❌ FAIL: LLDP directory NOT created"
fi

echo ""
echo "=============================================="
echo " Test Complete"
echo "=============================================="
echo "Test directory: ${TEST_LOG_ROOT}"
echo ""
echo "Summary:"
echo "  - Timestamp filtering prevents old batch directories from being consolidated"
echo "  - Only batches modified after execution start are processed"
echo "  - This solves Issue #3: BGP and OSPF folders no longer created for LLDP-only execution"
