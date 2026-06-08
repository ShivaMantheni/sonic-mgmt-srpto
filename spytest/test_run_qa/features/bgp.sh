#!/bin/bash

# ==========================================================
# BGP Feature Test Runner
# Runs all BGP tests and generates feature-specific dashboard
# ==========================================================

FEATURE_NAME="BGP"
FEATURE_DISPLAY="BGP (Border Gateway Protocol)"
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
# BGP Test Runner Function
# ==========================================================

run_bgp_test() {
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
# BGP Negative/Flap/RR Tests (3RR Testbed)
# ==========================================================
echo "Batch 1/6: BGP Negative/Flap/RR Tests"
run_bgp_test "BGP_NEG_FLAP_RR" "./testbeds/testbed_vs_3rr.yaml" \
    routing/bgp/test_ipv4_bgp_link_flap.py \
    routing/bgp/test_ipv4_bgp_daemon_restart.py \
    routing/bgp/test_ipv6_bgp_daemon_restart.py \
    routing/bgp/test_ipv4_bgp_route_reflector.py \
    routing/bgp/test_ipv4_bgp_negative_password.py \
    routing/bgp/test_ipv4_bgp_negative_nexthop.py \
    routing/bgp/test_ipv4_bgp_negative_asn.py \
    routing/bgp/test_ipv4_bgp_loopback_negative_updatesource.py \
    routing/bgp/test_ipv6_bgp_route_reflector.py \
    routing/bgp/test_ipv6_bgp_negative_password.py \
    routing/bgp/test_ipv6_bgp_negative_asn.py \
    routing/bgp/test_ipv6_bgp_loopback.py \
    routing/bgp/test_ipv6_bgp_loopback_negative_updatesource.py \
    routing/bgp/test_ipv6_bgp_link_flap.py \
    routing/bgp/test_ipv6_bgp_interface_routes.py \
    routing/bgp/test_ipv6_bgp_interface.py \
    routing/bgp/test_ipv6_bgp_interface_ebgp.py \
    routing/bgp/test_portchannel_ipv6_bgp.py

# ==========================================================
# BGP IPv4 Features (2-node Testbed)
# ==========================================================
echo "Batch 2/6: BGP IPv4 Basic Features"
run_bgp_test "BGP_IPV4_FEATURES" "./testbeds/testbed_vs_2node.yaml" \
    routing/BGP/test_bgp_ipv4_basic.py \
    routing/BGP/test_bgp_svi_ipv4.py \
    routing/BGP/test_bgp_portchannel_ipv4.py \
    routing/BGP/test_bgp_loopback_ipv4.py \
    routing/BGP/test_bgp_ipv4_basic_ebgp.py \
    routing/BGP/test_bgp_svi_ipv4_ebgp.py \
    routing/BGP/test_bgp_portchannel_ipv4_ebgp.py \
    routing/BGP/test_bgp_loopback_ipv4_ebgp.py \
    routing/BGP/test_bgp_ebgp_connected_static_redistribution.py

# ==========================================================
# BGP Advanced Features (3RR Testbed)
# ==========================================================
echo "Batch 3/6: BGP Advanced Features"
run_bgp_test "BGP_ADVANCED_FEATURES" "./testbeds/testbed_vs_3rr.yaml" \
    routing/BGP/test_bgp_advanced_features.py \
    routing/BGP/test_ipv4_bgp_route_reflector.py \
    routing/BGP/test_bgp_med_weight.py

# ==========================================================
# BGP ISCLI Best Path (2-node Testbed)
# ==========================================================
echo "Batch 4/6: BGP ISCLI Best Path"
run_bgp_test "BGP_ISCLI_BESTPATH" "./testbeds/testbed_2vs.yaml" \
    system/iscli_BGP/test_bgp50_localpref_selection.py \
    system/iscli_BGP/test_bgp51_aspath_selection.py \
    system/iscli_BGP/test_bgp52_med_selection.py \
    system/iscli_BGP/test_bgp55_ibgp_ebgp_selection.py \
    system/iscli_BGP/test_bgp56_origin_code_selection.py \
    system/iscli_BGP/test_bgp57_router_id_tiebreak.py \
    system/iscli_BGP/test_bgp58_nexthop_reachability.py

# ==========================================================
# BGP ISCLI Capability (2-node Testbed)
# ==========================================================
echo "Batch 5/6: BGP ISCLI Capability"
run_bgp_test "BGP_ISCLI_CAPABILITY" "./testbeds/testbed_2vs.yaml" \
    system/iscli_BGP/test_bgp76_capability_negotiation.py \
    system/iscli_BGP/test_bgp78_extended_nexthop.py

# ==========================================================
# BGP ISCLI Peer Group Advanced (2-node Testbed)
# ==========================================================
echo "Batch 6/6: BGP ISCLI Peer Group Advanced"
run_bgp_test "BGP_ISCLI_PG_ADV" "./testbeds/testbed_2vs.yaml" \
    system/iscli_BGP/test_bgp_pg16_pkt_queue.py \
    system/iscli_BGP/test_bgp_pg17_allowas_in.py \
    system/iscli_BGP/test_bgp_pg18_conflict_detection.py \
    system/iscli_BGP/test_bgp_pg19_passive_mode.py \
    system/iscli_BGP/test_bgp_pg20_routemap_override.py

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
