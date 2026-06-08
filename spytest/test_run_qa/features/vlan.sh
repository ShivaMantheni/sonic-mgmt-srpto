#!/bin/bash

# ==========================================================
# VLAN Feature Test Runner
# Runs all VLAN tests and generates feature-specific dashboard
# ==========================================================

FEATURE_NAME="VLAN"
FEATURE_DISPLAY="VLAN (Virtual LAN)"
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
# VLAN Test Runner Function
# ==========================================================

run_vlan_test() {
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
# VLAN ISCLI Tests (2-node Testbed)
# ==========================================================
echo "Batch 1/2: VLAN ISCLI Tests"
run_vlan_test "VLAN_ISCLI" "./testbeds/testbed_2node.yaml" \
    switching/iscli_Vlan/test_interface_1_iscli_vlan.py \
    switching/iscli_Vlan/test_interface_2_iscli_vlan_ip.py \
    switching/iscli_Vlan/test_interface_1_iscli_vlan_reboot.py \
    switching/iscli_Vlan/test_interface_2_iscli_vlan_ip_reboot.py

# ==========================================================
# VLAN Comprehensive Tests (2-node Testbed)
# ==========================================================
echo "Batch 2/2: VLAN Comprehensive Tests"
run_vlan_test "VLAN_COMPREHENSIVE" "./testbeds/testbed_vs_2d.yaml" \
    switching/vlan/test_vlan_create_delete.py \
    switching/vlan/test_vlan_access_port_change.py \
    switching/vlan/test_vlan_access_port.py \
    switching/vlan/test_vlan_isolation.py \
    switching/vlan/test_vlan_trunk_port.py \
    switching/vlan/test_vlan_trunk_segregation.py \
    switching/vlan/test_vlan_mixed_port.py \
    switching/vlan/test_vlan_native.py

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
