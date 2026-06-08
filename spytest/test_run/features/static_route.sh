#!/bin/bash

# ==========================================================
# Static Route Feature Test Runner
# Runs all Static Route tests and generates feature-specific dashboard
# ==========================================================

FEATURE_NAME="STATIC_ROUTE"
FEATURE_DISPLAY="Static Route (IPv4/IPv6)"
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
# Static Route Test Runner Function
# ==========================================================

run_static_test() {
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
# Static Route Basic Tests (IPv4/IPv6)
# ==========================================================
echo "Batch 1/3: Static Route Basic Tests"
run_static_test "STATIC_BASIC" "./testbeds/QA/testbed_vs_1node_reg_qa.yaml" \
    routing/static/test_sm_iscli_7.py \
    routing/static/test_static_route_basic.py \
    routing/static/test_static_route_basic_klish.py \
    routing/static/test_static_route_blackhole.py \
    routing/static/test_static_route_mgmt_vrf_klish.py \
    routing/static/test_static_route_vrf_klish.py

# ==========================================================
# Static IPv6 Tests
# ==========================================================
echo "Batch 2/3: Static IPv6 Tests"
run_static_test "STATIC_IPV6" "./testbeds/QA/testbed_vs_1node_reg_qa.yaml" \
    routing/static/test_static_ipv6_route_basic_1.py \
    routing/static/test_static_ipv6_negative.py \
    routing/static/test_static_ipv6_blackhole.py \
    routing/static/test_static_ipv6_ecmp.py \
    routing/static/test_static_ipv6_scale.py \
    routing/static/test_static_ipv6_vrf.py \
    routing/static/test_static_ipv6_mgmt_vrf.py

# ==========================================================
# Static Route OC Comprehensive Tests
# ==========================================================
echo "Batch 3/3: Static Route OC Comprehensive"
run_static_test "STATIC_OC_COMPREHENSIVE" "./testbeds/QA/testbed_oc_static_3vs_reg_qa.yaml" \
    system/Static_Route/test_oc_static_route_01_ipv4_basic_nexthop.py \
    system/Static_Route/test_oc_static_route_02_ipv4_blackhole.py \
    system/Static_Route/test_oc_static_route_03_ipv4_interface.py \
    system/Static_Route/test_oc_static_route_04_ipv4_tags.py \
    system/Static_Route/test_oc_static_route_05_ipv4_tag_distance.py \
    system/Static_Route/test_oc_static_route_06_ipv4_host_prefix.py \
    system/Static_Route/test_oc_static_route_07_ipv4_ecmp.py \
    system/Static_Route/test_oc_static_route_08_ipv6_basic.py \
    system/Static_Route/test_oc_static_route_09_ipv6_blackhole.py \
    system/Static_Route/test_oc_static_route_10_ipv6_interface.py \
    system/Static_Route/test_oc_static_route_11_ipv6_tag.py \
    system/Static_Route/test_oc_static_route_12_ipv6_distance.py \
    system/Static_Route/test_oc_static_route_13_ipv6_default.py \
    system/Static_Route/test_oc_static_route_14_ipv6_prefix_lengths.py \
    system/Static_Route/test_oc_static_route_15_ipv6_ecmp.py \
    system/Static_Route/test_oc_static_route_16_mixed_ipv4_ipv6.py \
    system/Static_Route/test_oc_static_route_17_route_deletion_modification.py \
    system/Static_Route/test_oc_static_route_18_interface_distance.py \
    system/Static_Route/test_oc_static_route_19_recursive_routes.py \
    system/Static_Route/test_oc_static_route_20_portchannel.py \
    system/Static_Route/test_oc_static_route_21_vlan_interface.py

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
