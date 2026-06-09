#!/bin/bash

# ==========================================================
# LLDP Feature Test Runner
# Runs all LLDP tests and generates feature-specific dashboard
# ==========================================================

FEATURE_NAME="LLDP"
FEATURE_DISPLAY="LLDP (Link Layer Discovery Protocol)"
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
# LLDP Test Batches
# ==========================================================

run_lldp_test() {
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
# LLDP Comprehensive Tests (36 tests)
# ==========================================================
echo "Batch 1/3: LLDP Comprehensive Tests"
run_lldp_test "LLDP_COMPREHENSIVE" "./testbeds/testbed_vs_2d_reg.yaml" \
    system/ISCLI_LLDP/test_lldp_01_global_interface_cli.py \
    system/ISCLI_LLDP/test_lldp_02_neighbor_discovery.py \
    system/ISCLI_LLDP/test_lldp_03_transmit_receive_modes.py \
    system/ISCLI_LLDP/test_lldp_04_per_interface_enable_disable.py \
    system/ISCLI_LLDP/test_lldp_05_timers_multiplier.py \
    system/ISCLI_LLDP/test_lldp_06_system_name_description_mgmt_tlv.py \
    system/ISCLI_LLDP/test_lldp_07_vlan_specific_tlvs.py \
    system/ISCLI_LLDP/test_lldp_08_rapid_enable_disable.py \
    system/ISCLI_LLDP/test_lldp_09_clear_statistics.py \
    system/ISCLI_LLDP/test_lldp_10_save_reboot_persistence.py \
    system/ISCLI_LLDP/test_lldp_11_neighbor_detail_tlvs.py \
    system/ISCLI_LLDP/test_lldp_12_port_description_tlv.py \
    system/ISCLI_LLDP/test_lldp_13_system_capabilities_tlv.py \
    system/ISCLI_LLDP/test_lldp_14_management_address_selection.py \
    system/ISCLI_LLDP/test_lldp_15_ttl_hold_behavior.py \
    system/ISCLI_LLDP/test_lldp_16_lag_member_interfaces.py \
    system/ISCLI_LLDP/test_lldp_17_mtu_change_continuity.py \
    system/ISCLI_LLDP/test_lldp_18_per_port_tlv_enable_disable.py \
    system/ISCLI_LLDP/test_lldp_19_lldp_statistics_counters.py \
    system/ISCLI_LLDP/test_lldp_20_snmp_lldp_mib_parity.py \
    system/ISCLI_LLDP/test_lldp_21_ipv6_management_address_tlv.py \
    system/ISCLI_LLDP/test_lldp_22_lldp_over_different_media.py \
    system/ISCLI_LLDP/test_lldp_23_admin_down_up_flush.py \
    system/ISCLI_LLDP/test_lldp_24_local_chassis_port_id.py \
    system/ISCLI_LLDP/test_lldp_25_reject_invalid_timers.py \
    system/ISCLI_LLDP/test_lldp_26_receive_only_no_discovery.py \
    system/ISCLI_LLDP/test_lldp_27_unknown_private_tlvs.py \
    system/ISCLI_LLDP/test_lldp_28_malformed_lldp_frames.py \
    system/ISCLI_LLDP/test_lldp_29_vlan_tagged_lldp_frames.py \
    system/ISCLI_LLDP/test_lldp_30_disable_globally_active_neighbors.py \
    system/ISCLI_LLDP/test_lldp_31_reject_invalid_mgmt_address.py \
    system/ISCLI_LLDP/test_lldp_32_per_port_disable_peer_tx.py \
    system/ISCLI_LLDP/test_lldp_33_duplicate_chassis_port_id.py \
    system/ISCLI_LLDP/test_lldp_34_lldp_not_on_svis.py \
    system/ISCLI_LLDP/test_lldp_35_bulk_enable_interface_range.py \
    system/ISCLI_LLDP/test_lldp_36_bulk_tlv_toggle_range.py

# ==========================================================
# LLDP CLI Validation Tests (4 tests)
# ==========================================================
echo "Batch 2/3: LLDP CLI Validation"
run_lldp_test "SM_ISCLI_52_LLDP_CLI_VALIDATION" "./testbeds/testbed_vs_2d_reg.yaml" \
    system/lldp/test_sm_iscli_52_lldp_cli_output.py

# ==========================================================
# LLDP CLI Fix Tests (1 test)
# ==========================================================
echo "Batch 3/3: LLDP CLI Fix"
run_lldp_test "SM_ISCLI_P2_161_162_LLDP_CLI_FIX" "./testbeds/testbed_vs_1node_reg.yaml" \
    system/lldp/test_sm_iscli_p2_161_162_lldp_cli_fix.py

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
