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
#   Total Batches: 47 (B, C, D, E, F, H, I, K, P, Q, R, Y, Z, AA-AN, AQ, AU, AW-AZ, BC, BU-BX, CG, CM-CT)
#   Total Test Scripts: 148 (comprehensive 2-node regression coverage)
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

    # 2-Node SM_ISCLI Tests (P-R, Y-Z, AA-AN, AQ, AU, AW-AZ)
    ["P"]="SM_ISCLI_4_EBGP_MULTIHOP"
    ["Q"]="SM_ISCLI_5_BGP_L2VPN_EVPN"
    ["R"]="SM_ISCLI_6_BGP_TIMERS"
    ["Y"]="SM_ISCLI_8_MGMT_STATIC_IP"
    ["Z"]="SM_ISCLI_9_L2VPN_EVPN_ORDER"
    ["AA"]="SM_ISCLI_11_BGP_GRACEFUL_RESTART"
    ["AB"]="SM_ISCLI_12_MGMT_PORT_VISIBLE"
    ["AC"]="SM_ISCLI_10_UPDATE_SOURCE"
    ["AD"]="SM_ISCLI_13_IBGP_MULTIPATH"
    ["AE"]="SM_ISCLI_15_BGP_NETWORK_CONFLICT"
    ["AF"]="SM_ISCLI_41_BGP_REMOTE_AS_INTERNAL_EXTERNAL"
    ["AG"]="SM_ISCLI_82_BGP_VRF_VALIDATION"
    ["AH"]="SM_ISCLI_74_HOSTNAME_VALIDATION"
    ["AI"]="SM_ISCLI_29_IP_ROUTE_SVI"
    ["AJ"]="SM_ISCLI_46_PORT_BREAKOUT"
    ["AK"]="SM_ISCLI_60_REMOVE_VLAN_INTERFACE"
    ["AL"]="SM_ISCLI_12_SHOW_IP_INTERFACE"
    ["AM"]="SM_ISCLI_33_SHOW_RUN_INTERFACE"
    ["AN"]="SM_ISCLI_54_SHOW_RUNNING_CONFIG"
    ["AO"]="SM_ISCLI_73_VRF_INTERFACE_VALIDATION"
    ["AQ"]="SM_ISCLI_20_OSPF_LOOPBACK_NO_IP"
    ["AU"]="SM_ISCLI_82_BGP_VRF_UNCONFIG"
    ["AW"]="SM_ISCLI_69_VLAN_NEGATIVE_MEMBER"
    ["AX"]="SM_ISCLI_76_SHOW_IP_ROUTE_FILTERING"
    ["AY"]="SM_ISCLI_21_OSPF_NETWORK_REMOVAL"
    ["AZ"]="SM_ISCLI_27_BGP_PEERGROUP_ACTIVATE"
    ["BA"]="SM_ISCLI_52_LLDP_CLI_VALIDATION"
    ["BC"]="SM_ISCLI_70_BGP_IPV6_CLI_VALIDATION"
    ["BU"]="SM_ISCLI_P2_42_VLAN_SVI_REMOVAL"
    ["BV"]="SM_ISCLI_P2_39_SWITCHPORT_TRUNK_VLAN"
    ["BW"]="SM_ISCLI_13_VRF_BINDING"
    ["BX"]="SM_ISCLI_P2_32_BGP_VRF_INSTANCE"

    # 2-Node QoS and L2/L3 Tests (CG, CM-CT)
    ["CG"]="QOS_PFC_PRIORITY_PG_MAP"
    ["CM"]="VLAN_SVI_L3_TRAFFIC"
    ["CN"]="VLAN_COMPREHENSIVE"
    ["CO"]="ARP_COMPREHENSIVE"
    ["CR"]="ARP_EXTENDED_TESTS"
    ["CS"]="ND_NEIGHBOR_DISCOVERY"
    ["CT"]="LLDP_COMPREHENSIVE"
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
# BATCH-BA : SM_ISCLI_52 - LLDP CLI Validation (2-Node)
# ==========================================================

if should_run_batch "BA"; then
    run_batch "SM_ISCLI_52_LLDP_CLI_VALIDATION" "./testbeds/testbed_vs_2d.yaml" \
    system/lldp/test_sm_iscli_52_lldp_cli_output.py
else
    echo "Skipping Batch BA (SM_ISCLI_52_LLDP_CLI_VALIDATION) - not selected"
fi


if should_run_batch "AA"; then
    run_batch "SM_ISCLI_11_BGP_GRACEFUL_RESTART" "./testbeds/testbed_vs_2d.yaml" \
    system/SM_ISCLI/test_sm_iscli_11_bgp_graceful_restart.py
else
    echo "Skipping Batch AA (SM_ISCLI_11_BGP_GRACEFUL_RESTART) - not selected"
fi

if should_run_batch "AB"; then
    run_batch "SM_ISCLI_12_MGMT_PORT_VISIBLE" "./testbeds/testbed_vs_2d.yaml" \
    system/SM_ISCLI/test_sm_iscli_12_management_port_visible.py
else
    echo "Skipping Batch AB (SM_ISCLI_12_MGMT_PORT_VISIBLE) - not selected"
fi

if should_run_batch "AC"; then
    run_batch "SM_ISCLI_10_UPDATE_SOURCE" "./testbeds/testbed_vs_2d.yaml" \
    routing/bgp/test_sm_iscli_10_update_source_format.py
else
    echo "Skipping Batch AC (SM_ISCLI_10_UPDATE_SOURCE) - not selected"
fi

if should_run_batch "AD"; then
    run_batch "SM_ISCLI_13_IBGP_MULTIPATH" "./testbeds/testbed_vs_2d.yaml" \
    routing/bgp/test_sm_iscli_13_ibgp_multipath.py
else
    echo "Skipping Batch AD (SM_ISCLI_13_IBGP_MULTIPATH) - not selected"
fi

if should_run_batch "AE"; then
    run_batch "SM_ISCLI_15_BGP_NETWORK_CONFLICT" "./testbeds/testbed_vs_2d.yaml" \
    routing/bgp/test_sm_iscli_15_bgp_network_ip_conflict.py
else
    echo "Skipping Batch AE (SM_ISCLI_15_BGP_NETWORK_CONFLICT) - not selected"
fi

if should_run_batch "AF"; then
    run_batch "SM_ISCLI_41_BGP_REMOTE_AS_INTERNAL_EXTERNAL" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_bgp_remote_as_internal_external.py
else
    echo "Skipping Batch AF (SM_ISCLI_41_BGP_REMOTE_AS_INTERNAL_EXTERNAL) - not selected"
fi

if should_run_batch "AG"; then
    run_batch "SM_ISCLI_82_BGP_VRF_VALIDATION" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_bgp_vrf_validation.py
else
    echo "Skipping Batch AG (SM_ISCLI_82_BGP_VRF_VALIDATION) - not selected"
fi

if should_run_batch "AH"; then
    run_batch "SM_ISCLI_74_HOSTNAME_VALIDATION" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_hostname_validation.py
else
    echo "Skipping Batch AH (SM_ISCLI_74_HOSTNAME_VALIDATION) - not selected"
fi

if should_run_batch "AI"; then
    run_batch "SM_ISCLI_29_IP_ROUTE_SVI" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_ip_route_svi.py
else
    echo "Skipping Batch AI (SM_ISCLI_29_IP_ROUTE_SVI) - not selected"
fi

if should_run_batch "AJ"; then
    run_batch "SM_ISCLI_46_PORT_BREAKOUT" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_port_breakout.py
else
    echo "Skipping Batch AJ (SM_ISCLI_46_PORT_BREAKOUT) - not selected"
fi

if should_run_batch "AK"; then
    run_batch "SM_ISCLI_60_REMOVE_VLAN_INTERFACE" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_remove_vlan_interface.py
else
    echo "Skipping Batch AK (SM_ISCLI_60_REMOVE_VLAN_INTERFACE) - not selected"
fi

if should_run_batch "AL"; then
    run_batch "SM_ISCLI_12_SHOW_IP_INTERFACE" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_show_ip_interface.py
else
    echo "Skipping Batch AL (SM_ISCLI_12_SHOW_IP_INTERFACE) - not selected"
fi

if should_run_batch "AM"; then
    run_batch "SM_ISCLI_33_SHOW_RUN_INTERFACE" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_show_run_interface.py
else
    echo "Skipping Batch AM (SM_ISCLI_33_SHOW_RUN_INTERFACE) - not selected"
fi

if should_run_batch "AN"; then
    run_batch "SM_ISCLI_54_SHOW_RUNNING_CONFIG" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_show_running_config.py
else
    echo "Skipping Batch AN (SM_ISCLI_54_SHOW_RUNNING_CONFIG) - not selected"
fi

if should_run_batch "AO"; then
    run_batch "SM_ISCLI_73_VRF_INTERFACE_VALIDATION" "./testbeds/testbed_vs_2d.yaml" \
    Bug-fix/test_vrf_interface_validation.py
else
    echo "Skipping Batch AO (SM_ISCLI_73_VRF_INTERFACE_VALIDATION) - not selected"
fi

if should_run_batch "AQ"; then
    run_batch "SM_ISCLI_20_OSPF_LOOPBACK_NO_IP" "./testbeds/testbed_vs_2d.yaml" \
    routing/ospf/test_sm_iscli_20_ospf_loopback_no_ip.py
else
    echo "Skipping Batch AQ (SM_ISCLI_20_OSPF_LOOPBACK_NO_IP) - not selected"
fi

if should_run_batch "AU"; then
    run_batch "SM_ISCLI_82_BGP_VRF_UNCONFIG" "./testbeds/testbed_2vs.yaml" \
    system/SM_ISCLI/test_sm_iscli_82_bgp_vrf_unconfigurations.py
else
    echo "Skipping Batch AU (SM_ISCLI_82_BGP_VRF_UNCONFIG) - not selected"
fi

if should_run_batch "AW"; then
    run_batch "SM_ISCLI_69_VLAN_NEGATIVE_MEMBER" "./testbeds/testbed_vs_2d.yaml" \
    switching/vlan/test_vlan_negative_member.py
else
    echo "Skipping Batch AW (SM_ISCLI_69_VLAN_NEGATIVE_MEMBER) - not selected"
fi

if should_run_batch "AX"; then
    run_batch "SM_ISCLI_76_SHOW_IP_ROUTE_FILTERING" "./testbeds/testbed_vs_2d.yaml" \
    routing/ipv4/test_show_ip_route_filtering.py
else
    echo "Skipping Batch AX (SM_ISCLI_76_SHOW_IP_ROUTE_FILTERING) - not selected"
fi

if should_run_batch "AY"; then
    run_batch "SM_ISCLI_21_OSPF_NETWORK_REMOVAL" "./testbeds/testbed_vs_2d.yaml" \
    routing/ospf/test_ospf_network_removal.py
else
    echo "Skipping Batch AY (SM_ISCLI_21_OSPF_NETWORK_REMOVAL) - not selected"
fi

if should_run_batch "AZ"; then
    run_batch "SM_ISCLI_27_BGP_PEERGROUP_ACTIVATE" "./testbeds/testbed_vs_2d.yaml" \
    routing/bgp/test_bgp_peergroup_activate.py
else
    echo "Skipping Batch AZ (SM_ISCLI_27_BGP_PEERGROUP_ACTIVATE) - not selected"
fi

if should_run_batch "BC"; then
    run_batch "SM_ISCLI_70_BGP_IPV6_CLI_VALIDATION" "./testbeds/testbed_vs_2d.yaml" \
    routing/bgp/test_bgp_ipv6_cli_validation.py
else
    echo "Skipping Batch BC (SM_ISCLI_70_BGP_IPV6_CLI_VALIDATION) - not selected"
fi

if should_run_batch "BU"; then
    run_batch "SM_ISCLI_P2_42_VLAN_SVI_REMOVAL" "./testbeds/testbed_2vs.yaml" \
    system/iscli_BGP/test_vlan_iscli_p2_42_svi_removal.py
else
    echo "Skipping Batch BU (SM_ISCLI_P2_42_VLAN_SVI_REMOVAL) - not selected"
fi

if should_run_batch "BV"; then
    run_batch "SM_ISCLI_P2_39_SWITCHPORT_TRUNK_VLAN" "./testbeds/testbed_2vs.yaml" \
    system/iscli_BGP/test_vlan_iscli_p2_39_switchport_trunk_vlan.py
else
    echo "Skipping Batch BV (SM_ISCLI_P2_39_SWITCHPORT_TRUNK_VLAN) - not selected"
fi

if should_run_batch "BW"; then
    run_batch "SM_ISCLI_13_VRF_BINDING" "./testbeds/testbed_2vs.yaml" \
    system/iscli_BGP/test_sm_iscli_13_vrf_binding.py
else
    echo "Skipping Batch BW (SM_ISCLI_13_VRF_BINDING) - not selected"
fi

if should_run_batch "BX"; then
    run_batch "SM_ISCLI_P2_32_BGP_VRF_INSTANCE" "./testbeds/testbed_2vs.yaml" \
    system/iscli_BGP/test_bgp_p2_32_vrf_instance.py
else
    echo "Skipping Batch BX (SM_ISCLI_P2_32_BGP_VRF_INSTANCE) - not selected"
fi

if should_run_batch "CG"; then
    run_batch "QOS_PFC_PRIORITY_PG_MAP" "./testbeds/testbed_vs_2d.yaml" \
    qos/test_qos_pfc_priority_pg_map.py
else
    echo "Skipping Batch CG (QOS_PFC_PRIORITY_PG_MAP) - not selected"
fi

if should_run_batch "CM"; then
    run_batch "VLAN_SVI_L3_TRAFFIC" "./testbeds/testbed_2vs.yaml" \
    switching/vlan/test_vlan_svi_l3_traffic_2dut.py
else
    echo "Skipping Batch CM (VLAN_SVI_L3_TRAFFIC) - not selected"
fi

if should_run_batch "CN"; then
    run_batch "VLAN_COMPREHENSIVE" "./testbeds/testbed_vs_2d.yaml" \
    switching/vlan/test_vlan_create_delete.py \
    switching/vlan/test_vlan_access_port_change.py \
    switching/vlan/test_vlan_access_port.py \
    switching/vlan/test_vlan_isolation.py \
    switching/vlan/test_vlan_trunk_port.py \
    switching/vlan/test_vlan_trunk_segregation.py \
    switching/vlan/test_vlan_mixed_port.py \
    switching/vlan/test_vlan_native.py

    # Run standalone testbed tests separately
    run_batch "VLAN_COMPREHENSIVE_STANDALONE" "./testbeds/ztp_standalone.yaml" \
    switching/vlan/test_vlan_persistence.py \
    switching/vlan/test_vlan_boundary_deletion.py \
    switching/vlan/test_vlan_trunk_config_removal.py
else
    echo "Skipping Batch CN (VLAN_COMPREHENSIVE) - not selected"
fi

if should_run_batch "CO"; then
    run_batch "ARP_COMPREHENSIVE" "./testbeds/testbed_2vs.yaml" \
    system/iscli_ARP/test_arp_01_dynamic_learning.py \
    system/iscli_ARP/test_arp_02_static_wrong_mac.py \
    system/iscli_ARP/test_arp_scapy_01_request_reply.py \
    system/iscli_ARP/test_arp_scapy_02_gratuitous.py \
    system/iscli_ARP/test_arp_scapy_03_spoofing.py \
    system/iscli_ARP/test_arp_scapy_04_opcode_validation.py \
    system/iscli_ARP/test_arp_scapy_05_cache_timeout.py \
    system/iscli_ARP/test_arp_scapy_06_probe_conflict.py \
    system/iscli_ARP/test_arp_scapy_07_announcement.py
else
    echo "Skipping Batch CO (ARP_COMPREHENSIVE) - not selected"
fi

if should_run_batch "CR"; then
    run_batch "ARP_EXTENDED_TESTS" "./testbeds/testbed_2vs.yaml" \
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
else
    echo "Skipping Batch CR (ARP_EXTENDED_TESTS) - not selected"
fi

if should_run_batch "CS"; then
    run_batch "ND_NEIGHBOR_DISCOVERY" "./testbeds/testbed_2vs.yaml" \
    system/ISCLI_ND/test_nd_basic_operations.py \
    system/ISCLI_ND/test_nd_interface_behavior.py \
    system/ISCLI_ND/test_nd_multi_vlan.py \
    system/ISCLI_ND/test_nd_aging_and_state.py
else
    echo "Skipping Batch CS (ND_NEIGHBOR_DISCOVERY) - not selected"
fi

if should_run_batch "CT"; then
    run_batch "LLDP_COMPREHENSIVE" "./testbeds/testbed_2vs.yaml" \
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
else
    echo "Skipping Batch CT (LLDP_COMPREHENSIVE) - not selected"
fi

if should_run_batch "P"; then
    run_batch "SM_ISCLI_4_EBGP_MULTIHOP" "./testbeds/testbed_vs_2d.yaml" \
    system/SM_ISCLI/test_sm_iscli_4_ebgp_multihop.py
else
    echo "Skipping Batch P (SM_ISCLI_4_EBGP_MULTIHOP) - not selected"
fi

if should_run_batch "Q"; then
    run_batch "SM_ISCLI_5_BGP_L2VPN_EVPN" "./testbeds/testbed_vs_2d.yaml" \
    system/SM_ISCLI/test_sm_iscli_5_bgp_l2vpn_evpn_output.py
else
    echo "Skipping Batch Q (SM_ISCLI_5_BGP_L2VPN_EVPN) - not selected"
fi

if should_run_batch "R"; then
    run_batch "SM_ISCLI_6_BGP_TIMERS" "./testbeds/testbed_vs_2d.yaml" \
    system/SM_ISCLI/test_sm_iscli_6_bgp_timers.py
else
    echo "Skipping Batch R (SM_ISCLI_6_BGP_TIMERS) - not selected"
fi

if should_run_batch "Y"; then
    run_batch "SM_ISCLI_8_MGMT_STATIC_IP" "./testbeds/testbed_vs_2d.yaml" \
    system/SM_ISCLI/test_sm_iscli_8_management_static_ip.py
else
    echo "Skipping Batch Y (SM_ISCLI_8_MGMT_STATIC_IP) - not selected"
fi

if should_run_batch "Z"; then
    run_batch "SM_ISCLI_9_L2VPN_EVPN_ORDER" "./testbeds/testbed_vs_2d.yaml" \
    system/SM_ISCLI/test_sm_iscli_9_l2vpn_evpn_order.py
else
    echo "Skipping Batch Z (SM_ISCLI_9_L2VPN_EVPN_ORDER) - not selected"
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
echo "  Total 2-Node Batches: ${#BATCH_NAMES[@]} (47 total)"
echo "  Total Test Scripts: 148"
echo "  Testbed Types: testbed_vs_2d.yaml, testbed_2vs.yaml, testbed_2node.yaml, testbed_vs_2node.yaml"
echo "  Log Location: ${BASE_LOG}"
echo ""
echo "Quick Commands:"
echo "  View results: ./batch_2N.sh --list"
echo "  Run specific: ./batch_2N.sh --features B,C"
echo "  Run BGP only: ./batch_2N.sh --features BGP"
echo ""
