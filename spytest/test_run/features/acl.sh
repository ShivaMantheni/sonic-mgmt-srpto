#!/bin/bash

# ==========================================================
# ACL Feature Test Runner
# Runs all ACL tests and generates feature-specific dashboard
# ==========================================================

FEATURE_NAME="ACL"
FEATURE_DISPLAY="ACL (Access Control List)"
DATE_DIR=$(date +%Y%m%d)
TIME_STAMP=$(date +%H%M%S)

# Navigate to spytest root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPYTEST_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$SPYTEST_ROOT"

# Feature-specific log directory
FEATURE_LOG="./logs/${DATE_DIR}/${FEATURE_NAME}"
mkdir -p "${FEATURE_LOG}"

echo "=============================================="
echo " ${FEATURE_DISPLAY} Test Execution"
echo " Date: ${DATE_DIR}"
echo " Time: ${TIME_STAMP}"
echo "=============================================="
echo ""

# ==========================================================
# ACL Test Runner Function
# ==========================================================

run_acl_test() {
    local batch_name=$1
    local testbed=$2
    shift 2
    local tests=("$@")

    local batch_log="${FEATURE_LOG}/${batch_name}__${TIME_STAMP}"
    mkdir -p "${batch_log}"

    echo "Running: ${batch_name}"
    echo "  Testbed: ${testbed}"
    echo "  Tests: ${#tests[@]}"
    echo "  Logs: ${batch_log}"

    ./bin/spytest --tryssh 1 \
        --testbed "${testbed}" \
        "${tests[@]}" \
        --logs-path "${batch_log}" \
        --log-level debug \
        --skip-init-config \
        --ifname-type native \
        --get-tech-support none \
        --syslog-check none

    echo "  Completed: ${batch_name} (RC=$?)"
    echo ""
}

# ==========================================================
# IPv4 ACL CLI Validation
# ==========================================================
echo "Batch 1/4: IPv4 ACL CLI Validation"
run_acl_test "IPV4_ACL_CLI" "./testbeds/QA/ztp_standalone_reg_qa.yaml" \
    qos/acl/test_ipv4_acl_cli_validation.py

# ==========================================================
# L3 ACL Comprehensive Tests
# ==========================================================
echo "Batch 2/4: L3 ACL Comprehensive"
run_acl_test "L3_ACL_COMPREHENSIVE" "./testbeds/QA/testbed_acl_reg_qa.yaml" \
    routing/l3_acl/test_l3_acl.py \
    routing/l3_acl/test_l3_acl_negative.py \
    routing/l3_acl/test_l3_acl_robustness.py

# ==========================================================
# L2 ACL Comprehensive Tests
# ==========================================================
echo "Batch 3/4: L2 ACL Comprehensive"
run_acl_test "L2_ACL_COMPREHENSIVE" "./testbeds/QA/testbed_acl_reg_qa.yaml" \
    switching/l2_acl/test_l2_acl.py \
    switching/l2_acl/test_l2_acl_negative.py \
    switching/l2_acl/test_l2_acl_robustness.py

# ==========================================================
# MAC ACL Comprehensive Tests
# ==========================================================
echo "Batch 4/4: MAC ACL Comprehensive"
run_acl_test "MAC_ACL_COMPREHENSIVE" "./testbeds/QA/ztp_standalone_reg_qa.yaml" \
    qos/acl/test_mac_acl_comprehensive.py

# ==========================================================
# Generate Feature Dashboard
# ==========================================================
echo "=============================================="
echo " Generating ${FEATURE_NAME} Dashboard"
echo "=============================================="

DASHBOARD_FILE="${FEATURE_LOG}/dashboard_${FEATURE_NAME}_${DATE_DIR}_${TIME_STAMP}.html"

python3 dashboard/scripts/generate_graphical_dashboard.py \
    --log-root "${FEATURE_LOG}" \
    --out "${DASHBOARD_FILE}" \
    --name "${FEATURE_DISPLAY} - ${DATE_DIR}"

if [ $? -eq 0 ]; then
    echo "✓ Dashboard: ${DASHBOARD_FILE}"
else
    echo "✗ Dashboard generation failed"
fi

# ==========================================================
# Generate Feature JSON
# ==========================================================
echo ""
echo "=============================================="
echo " Generating ${FEATURE_NAME} JSON"
echo "=============================================="

JSON_FILE="${FEATURE_LOG}/${FEATURE_NAME}.json"

python3 dashboard/scripts/consolidate_feature_logs.py \
    --log-root "${FEATURE_LOG}" \
    --consolidate \
    --json-output "${JSON_FILE}"

if [ $? -eq 0 ] && [ -f "${JSON_FILE}" ]; then
    echo "✓ JSON: ${JSON_FILE}"
else
    echo "✗ JSON generation failed"
fi

echo ""
echo "=============================================="
echo " ${FEATURE_NAME} Execution Complete"
echo "=============================================="
echo "Logs: ${FEATURE_LOG}"
echo "Dashboard: ${DASHBOARD_FILE}"
echo "JSON: ${JSON_FILE}"
echo "=============================================="
