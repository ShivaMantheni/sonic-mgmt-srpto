#!/bin/bash

# ==========================================================
# 2-NODE REGRESSION TEST SUITE - FEATURE WISE SINGLE-RUN SPYTEST BATCHES
# Each SpyTest call = One Dashboard Batch
# Logs: ./logs/<DATE>/<FEATURE>/<TIME>/
#
# Usage:
#   ./batch_2N.sh                    # Run all 2-node batches
#   ./batch_2N.sh --list             # List available batches
#   ./batch_2N.sh --features B,C,D   # Run specific batches
#   ./batch_2N.sh --features BGP_IPV4_FEATURES
#
# Statistics:
#   Total Batches: 8 (B, C, D, E, F, H, I, K)
#   Total Test Scripts: 35+
#   Last Updated: 2026-05-11
# ==========================================================

DATE_DIR=$(date +%Y%m%d)
TIME_STAMP=$(date +%H%M%S)

BASE_LOG="./logs/${DATE_DIR}"

mkdir -p "${BASE_LOG}"

# ==========================================================
# AVAILABLE 2-NODE FEATURE BATCHES (alphabetically for easy reference)
# ==========================================================
declare -A BATCH_NAMES=(
    # 2-Node BGP Feature Tests
    ["B"]="BGP_IPV4_FEATURES"
    ["C"]="BGP_ISCLI_BESTPATH"
    ["D"]="BGP_ISCLI_CAPABILITY"
    ["E"]="BGP_ISCLI_EVPN"
    ["F"]="BGP_ISCLI_PG_ADV"

    # 2-Node Switching & System Tests
    ["H"]="PORTCHANNEL_ISCLI"
    ["I"]="VLAN_ISCLI"
    ["K"]="SYS_INTERFACE_EVENTS"
)

# ==========================================================
# COMMAND-LINE ARGUMENT PARSING
# ==========================================================

show_usage() {
    echo "=============================================="
    echo " 2-Node Regression Test Suite - Selective Mode"
    echo "=============================================="
    echo ""
    echo "Usage:"
    echo "  $0                          # Run all batches"
    echo "  $0 --list                   # List available batches"
    echo "  $0 --help                   # Show this help"
    echo "  $0 --features <batches>     # Run specific batches"
    echo ""
    echo "Examples:"
    echo "  $0 --features B,C,D         # Run batches B, C, D"
    echo "  $0 --features BGP_IPV4_FEATURES,BGP_ISCLI_BESTPATH"
    echo "  $0 --features BGP           # Run all BGP batches (B-F)"
    echo ""
    echo "Available Batches:"
    echo "  B = BGP_IPV4_FEATURES       (BGP IPv4 iBGP/eBGP Features)"
    echo "  C = BGP_ISCLI_BESTPATH      (BGP isCLI Best Path)"
    echo "  D = BGP_ISCLI_CAPABILITY    (BGP isCLI Capability)"
    echo "  E = BGP_ISCLI_EVPN          (BGP isCLI EVPN)"
    echo "  F = BGP_ISCLI_PG_ADV        (BGP isCLI Peer Group Advanced)"
    echo "  H = PORTCHANNEL_ISCLI       (PortChannel isCLI)"
    echo "  I = VLAN_ISCLI              (VLAN isCLI)"
    echo "  K = SYS_INTERFACE_EVENTS    (System Interface Events)"
    echo ""
    echo "Special Keywords:"
    echo "  BGP      = Run all BGP batches (B-F)"
    echo "  SWITCHING = Run switching batches (H, I)"
    echo "  SYSTEM   = Run system batches (K)"
    echo "  2N       = Run all 2-node batches (B-F, H, I, K)"
    echo "  ALL      = Run all batches"
    echo ""
}

list_batches() {
    echo "=============================================="
    echo " Available 2-Node Feature Batches"
    echo "=============================================="
    for key in $(echo "${!BATCH_NAMES[@]}" | tr ' ' '\n' | sort); do
        printf "  [%s] %-25s\n" "$key" "${BATCH_NAMES[$key]}"
    done
    echo ""
    echo "Total Batches: ${#BATCH_NAMES[@]}"
    echo ""
}

# Parse command-line arguments
SELECTED_BATCHES=()
RUN_ALL=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --list|-l)
            list_batches
            exit 0
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        --features|-f)
            if [[ -z "$2" ]]; then
                echo "ERROR: --features requires argument"
                show_usage
                exit 1
            fi
            RUN_ALL=false
            IFS=',' read -ra FEATURES <<< "$2"
            for feature in "${FEATURES[@]}"; do
                feature=$(echo "$feature" | xargs)  # Trim whitespace

                # Handle special keywords
                if [[ "$feature" == "BGP" ]]; then
                    SELECTED_BATCHES+=(B C D E F)
                elif [[ "$feature" == "SWITCHING" ]]; then
                    SELECTED_BATCHES+=(H I)
                elif [[ "$feature" == "SYSTEM" ]]; then
                    SELECTED_BATCHES+=(K)
                elif [[ "$feature" == "2N" ]]; then
                    RUN_ALL=true
                    break
                elif [[ "$feature" == "ALL" ]]; then
                    RUN_ALL=true
                    break
                # Handle letter codes (B, C, D, etc.)
                elif [[ ${BATCH_NAMES[$feature]+_} ]]; then
                    SELECTED_BATCHES+=("$feature")
                # Handle full names (BGP_IPV4_FEATURES, etc.)
                else
                    # Find the key for this batch name
                    found=false
                    for key in "${!BATCH_NAMES[@]}"; do
                        if [[ "${BATCH_NAMES[$key]}" == "$feature" ]]; then
                            SELECTED_BATCHES+=("$key")
                            found=true
                            break
                        fi
                    done
                    if [[ "$found" == "false" ]]; then
                        echo "WARNING: Unknown batch '$feature', skipping"
                    fi
                fi
            done
            shift 2
            ;;
        *)
            echo "ERROR: Unknown option $1"
            show_usage
            exit 1
            ;;
    esac
done

# Display selected batches
if [[ "$RUN_ALL" == "true" ]]; then
    echo "=============================================="
    echo " 2-NODE REGRESSION STARTED (ALL BATCHES)"
    echo " DATE : ${DATE_DIR}"
    echo "=============================================="
else
    echo "=============================================="
    echo " 2-NODE REGRESSION STARTED (SELECTIVE)"
    echo " DATE : ${DATE_DIR}"
    echo " SELECTED BATCHES:"
    for batch in "${SELECTED_BATCHES[@]}"; do
        echo "   [$batch] ${BATCH_NAMES[$batch]}"
    done
    echo "=============================================="
fi

# ==========================================================
# Helper function to check if batch should run
# ==========================================================
should_run_batch() {
    local batch_letter=$1

    if [[ "$RUN_ALL" == "true" ]]; then
        return 0  # Run
    fi

    # Check if batch letter is in selected list
    for selected in "${SELECTED_BATCHES[@]}"; do
        if [[ "$selected" == "$batch_letter" ]]; then
            return 0  # Run
        fi
    done

    return 1  # Skip
}

run_batch () {
    FEATURE=$1
    TESTBED=$2
    shift 2
    TESTS="$@"

    LOG_PATH="${BASE_LOG}/${FEATURE}/${TIME_STAMP}"
    mkdir -p "${LOG_PATH}"

    echo "----------------------------------------------"
    echo " Running Batch: ${FEATURE}"
    echo " Testbed     : ${TESTBED}"
    echo " Logs        : ${LOG_PATH}"
    echo "----------------------------------------------"

    ./bin/spytest --tryssh 1 \
      --testbed "${TESTBED}" \
      ${TESTS} \
      --logs-path "${LOG_PATH}" \
      --log-level debug \
      --skip-init-config \
      --ifname-type native

    RC=$?
    echo " Batch ${FEATURE} completed with RC=${RC}"

    if [ ${RC} -ne 0 ]; then
        echo " WARNING: Batch ${FEATURE} failed. Continuing to next batch."
    fi
}

# ==========================================================
# BATCH-B : BGP IPv4 iBGP/eBGP Feature Tests (2-Node)
# ==========================================================

if should_run_batch "B"; then
    run_batch "BGP_IPV4_FEATURES" "./testbeds/dlink_2node.yaml" \
    routing/BGP/test_bgp_ipv4_basic.py \
    routing/BGP/test_bgp_svi_ipv4.py \
    routing/BGP/test_bgp_portchannel_ipv4.py \
    routing/BGP/test_bgp_loopback_ipv4.py \
    routing/BGP/test_bgp_ipv4_basic_ebgp.py \
    routing/BGP/test_bgp_svi_ipv4_ebgp.py \
    routing/BGP/test_bgp_portchannel_ipv4_ebgp.py \
    routing/BGP/test_bgp_loopback_ipv4_ebgp.py \
    routing/BGP/test_bgp_ebgp_connected_static_redistribution.py
else
    echo "Skipping Batch B (BGP_IPV4_FEATURES) - not selected"
fi


# ==========================================================
# BATCH-C : BGP isCLI Best Path (2-Node)
# ==========================================================

if should_run_batch "C"; then
    run_batch "BGP_ISCLI_BESTPATH" "./testbeds/dlink_2node.yaml" \
    system/iscli_BGP/test_bgp50_localpref_selection.py \
    system/iscli_BGP/test_bgp51_aspath_selection.py \
    system/iscli_BGP/test_bgp52_med_selection.py \
    system/iscli_BGP/test_bgp55_ibgp_ebgp_selection.py \
    system/iscli_BGP/test_bgp56_origin_code_selection.py \
    system/iscli_BGP/test_bgp57_router_id_tiebreak.py \
    system/iscli_BGP/test_bgp58_nexthop_reachability.py
else
    echo "Skipping Batch C (BGP_ISCLI_BESTPATH) - not selected"
fi


# ==========================================================
# BATCH-D : BGP isCLI Capability (2-Node)
# ==========================================================

if should_run_batch "D"; then
    run_batch "BGP_ISCLI_CAPABILITY" "./testbeds/dlink_2node.yaml" \
    system/iscli_BGP/test_bgp76_capability_negotiation.py \
    system/iscli_BGP/test_bgp78_extended_nexthop.py
else
    echo "Skipping Batch D (BGP_ISCLI_CAPABILITY) - not selected"
fi


# ==========================================================
# BATCH-E : BGP isCLI EVPN (2-Node)
# ==========================================================

if should_run_batch "E"; then
    run_batch "BGP_ISCLI_EVPN" "./testbeds/dlink_2node.yaml" \
    system/iscli_BGP/test_evpn04_type5_routes.py
else
    echo "Skipping Batch E (BGP_ISCLI_EVPN) - not selected"
fi


# ==========================================================
# BATCH-F : BGP isCLI Peer Group Advanced (2-Node)
# ==========================================================

if should_run_batch "F"; then
    run_batch "BGP_ISCLI_PG_ADV" "./testbeds/dlink_2node.yaml" \
    system/iscli_BGP/test_bgp_pg16_pkt_queue.py \
    system/iscli_BGP/test_bgp_pg17_allowas_in.py \
    system/iscli_BGP/test_bgp_pg18_conflict_detection.py \
    system/iscli_BGP/test_bgp_pg19_passive_mode.py \
    system/iscli_BGP/test_bgp_pg20_routemap_override.py
else
    echo "Skipping Batch F (BGP_ISCLI_PG_ADV) - not selected"
fi


# ==========================================================
# BATCH-H : PortChannel isCLI (2-Node)
# ==========================================================

if should_run_batch "H"; then
    run_batch "PORTCHANNEL_ISCLI" "./testbeds/dlink_2node.yaml" \
    switching/iscli_PortChannel/test_interface_1_iscli_portchannel.py
else
    echo "Skipping Batch H (PORTCHANNEL_ISCLI) - not selected"
fi


# ==========================================================
# BATCH-I : VLAN isCLI (2-Node)
# ==========================================================

if should_run_batch "I"; then
    run_batch "VLAN_ISCLI" "./testbeds/dlink_2node.yaml" \
    switching/iscli_Vlan/test_interface_1_iscli_vlan.py \
    switching/iscli_Vlan/test_interface_2_iscli_vlan_ip.py
else
    echo "Skipping Batch I (VLAN_ISCLI) - not selected"
fi


# ==========================================================
# BATCH-K : System Interface Events (2-Node)
# ==========================================================

if should_run_batch "K"; then
    run_batch "SYS_INTERFACE_EVENTS" "./testbeds/dlink_2node.yaml" \
    system/iscli_interface_events/test_interface_1_iscli_events_admin_up_down.py \
    system/iscli_interface_events/test_interface_2_iscli_events_mtu_change.py \
    system/iscli_interface_events/test_interface_3_iscli_events_description.py \
    system/iscli_interface_events/test_interface_4_iscli_events_ip_address.py \
    system/iscli_interface_events/test_interface_5_iscli_events_ipv6_address.py
else
    echo "Skipping Batch K (SYS_INTERFACE_EVENTS) - not selected"
fi


# ==========================================================
# Test Suite Completion
# ==========================================================

echo "=============================================="
if [[ "$RUN_ALL" == "true" ]]; then
    echo " 2-NODE REGRESSION COMPLETED (ALL BATCHES)"
else
    echo " 2-NODE REGRESSION COMPLETED (SELECTIVE)"
fi
echo " Logs Root : ${BASE_LOG}"
echo "=============================================="
echo ""
echo "Summary:"
echo "  Total 2-Node Batches: ${#BATCH_NAMES[@]}"
echo "  Testbed Type: dlink_2node.yaml"
echo "  Log Location: ${BASE_LOG}"
echo ""
echo "Quick Commands:"
echo "  View results: ./batch_2N.sh --list"
echo "  Run specific: ./batch_2N.sh --features B,C"
echo "  Run BGP only: ./batch_2N.sh --features BGP"
echo ""
