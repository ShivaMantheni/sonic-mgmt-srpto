#!/bin/bash

# ==========================================================
# ARP Feature Test Runner
# Runs all ARP tests and generates feature-specific dashboard
# ==========================================================

FEATURE_NAME="ARP"
FEATURE_DISPLAY="ARP (Address Resolution Protocol)"
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
# ARP Test Runner Function
# ==========================================================

run_arp_test() {
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
# ARP Comprehensive Tests
# ==========================================================
echo "Batch 1/3: ARP Comprehensive Tests"
run_arp_test "ARP_COMPREHENSIVE" "./testbeds/testbed_2vs.yaml" \
    system/iscli_ARP/test_arp_01_dynamic_learning.py \
    system/iscli_ARP/test_arp_02_static_wrong_mac.py \
    system/iscli_ARP/test_arp_scapy_01_request_reply.py \
    system/iscli_ARP/test_arp_scapy_02_gratuitous.py \
    system/iscli_ARP/test_arp_scapy_03_spoofing.py \
    system/iscli_ARP/test_arp_scapy_04_opcode_validation.py \
    system/iscli_ARP/test_arp_scapy_05_cache_timeout.py \
    system/iscli_ARP/test_arp_scapy_06_probe_conflict.py \
    system/iscli_ARP/test_arp_scapy_07_announcement.py

# ==========================================================
# ARP Extended Tests
# ==========================================================
echo "Batch 2/3: ARP Extended Tests"
run_arp_test "ARP_EXTENDED" "./testbeds/testbed_2vs.yaml" \
    system/ISCLI_ARP/test_arp_01_basic_request_reply.py \
    system/ISCLI_ARP/test_arp_02_static_wrong_mac.py \
    system/ISCLI_ARP/test_arp_03_proxy_arp.py \
    system/ISCLI_ARP/test_arp_04_static_entry.py \
    system/ISCLI_ARP/test_arp_05_aging_timeout.py \
    system/ISCLI_ARP/test_arp_05_aging.py \
    system/ISCLI_ARP/test_arp_02_garp.py \
    system/ISCLI_ARP/test_arp_07_portchannel.py \
    system/ISCLI_ARP/test_arp_06_vlan.py \
    system/ISCLI_ARP/test_arp_08_spoofing.py \
    system/ISCLI_ARP/test_arp_09_flooding.py \
    system/ISCLI_ARP/test_arp_10_malformed_opcode.py \
    system/ISCLI_ARP/test_arp_11_malformed_hwtype.py \
    system/ISCLI_ARP/test_arp_12_truncated.py \
    system/ISCLI_ARP/test_arp_13_cache_limit.py \
    system/ISCLI_ARP/test_arp_14_loopback.py \
    system/ISCLI_ARP/test_arp_15_different_subnet.py \
    system/ISCLI_ARP/test_arp_16_unsolicited.py \
    system/ISCLI_ARP/test_arp_17_broadcast_src.py \
    system/ISCLI_ARP/test_arp_18_unicast_dst.py \
    system/ISCLI_ARP/test_arp_19_mismatch.py \
    system/ISCLI_ARP/test_arp_20_zero_ip.py

# ==========================================================
# ARP Table Verification
# ==========================================================
echo "Batch 3/3: ARP Table Verification"
run_arp_test "ARP_TABLE_VERIFICATION" "./testbeds/ztp_standalone.yaml" \
    routing/arp/test_arp_table_verification.py

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
