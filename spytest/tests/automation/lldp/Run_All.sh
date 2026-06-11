#!/bin/bash

# ==========================================================
# LLDP Feature Test Runner
# Runs all LLDP tests and generates a feature-specific
# dashboard + JSON summary under this folder's reports/ dir.
#
# Outputs (all under tests/automation/lldp/scripts/reports/):
#   reports/results/<batch>/     -> per-batch spytest logs (single dir, wiped each run)
#   reports/lldp_dashboard.html  -> graphical dashboard
#   reports/LLDP_summary.json    -> JSON built from results_*_functions.csv
# ==========================================================

FEATURE_NAME="LLDP"
FEATURE_DISPLAY="LLDP (Link Layer Discovery Protocol)"
DATE_DIR=$(date +%Y%m%d)
TIME_STAMP=$(date +%H%M%S)

# Resolve paths.
#   SCRIPT_DIR   = .../spytest/tests/automation/scripts/lldp
#   SPYTEST_ROOT = .../spytest   (3 levels up; this is where ./bin/spytest lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPYTEST_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
cd "$SPYTEST_ROOT" || { echo "ERROR: cannot cd to spytest root: $SPYTEST_ROOT"; exit 1; }

# Reports live alongside this script (absolute paths so spytest cwd doesn't matter).
# Logs are kept in a single fixed directory (no per-run dated/timestamped folders).
# Any previous reports are removed at the start of each execution to save space.
REPORTS_DIR="${SCRIPT_DIR}/reports"
RESULTS_DIR="${REPORTS_DIR}/results"

rm -rf "${REPORTS_DIR}"
mkdir -p "${RESULTS_DIR}"

DASHBOARD_FILE="${REPORTS_DIR}/lldp_dashboard.html"
JSON_FILE="${REPORTS_DIR}/LLDP_summary.json"

echo "=============================================="
echo " ${FEATURE_DISPLAY} Test Execution"
echo " Date: ${DATE_DIR}"
echo " Time: ${TIME_STAMP}"
echo " Reports: ${REPORTS_DIR}"
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

    local batch_log="${RESULTS_DIR}/${batch_name}"
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
    automation/lldp/scripts/test_lldp_01_global_interface_cli.py \
    automation/lldp/scripts/test_lldp_02_neighbor_discovery.py \
    automation/lldp/scripts/test_lldp_03_transmit_receive_modes.py \
    automation/lldp/scripts/test_lldp_04_per_interface_enable_disable.py \
    automation/lldp/scripts/test_lldp_05_timers_multiplier.py \
    automation/lldp/scripts/test_lldp_06_system_name_description_mgmt_tlv.py \
    automation/lldp/scripts/test_lldp_07_vlan_specific_tlvs.py \
    automation/lldp/scripts/test_lldp_08_rapid_enable_disable.py \
    automation/lldp/scripts/test_lldp_09_clear_statistics.py \
    automation/lldp/scripts/test_lldp_10_save_reboot_persistence.py \
    automation/lldp/scripts/test_lldp_11_neighbor_detail_tlvs.py \
    automation/lldp/scripts/test_lldp_12_port_description_tlv.py \
    automation/lldp/scripts/test_lldp_13_system_capabilities_tlv.py \
    automation/lldp/scripts/test_lldp_14_management_address_selection.py \
    automation/lldp/scripts/test_lldp_15_ttl_hold_behavior.py \
    automation/lldp/scripts/test_lldp_16_lag_member_interfaces.py \
    automation/lldp/scripts/test_lldp_17_mtu_change_continuity.py \
    automation/lldp/scripts/test_lldp_18_per_port_tlv_enable_disable.py \
    automation/lldp/scripts/test_lldp_19_lldp_statistics_counters.py \
    automation/lldp/scripts/test_lldp_20_snmp_lldp_mib_parity.py \
    automation/lldp/scripts/test_lldp_21_ipv6_management_address_tlv.py \
    automation/lldp/scripts/test_lldp_22_lldp_over_different_media.py \
    automation/lldp/scripts/test_lldp_23_admin_down_up_flush.py \
    automation/lldp/scripts/test_lldp_24_local_chassis_port_id.py \
    automation/lldp/scripts/test_lldp_25_reject_invalid_timers.py \
    automation/lldp/scripts/test_lldp_26_receive_only_no_discovery.py \
    automation/lldp/scripts/test_lldp_27_unknown_private_tlvs.py \
    automation/lldp/scripts/test_lldp_28_malformed_lldp_frames.py \
    automation/lldp/scripts/test_lldp_29_vlan_tagged_lldp_frames.py \
    automation/lldp/scripts/test_lldp_30_disable_globally_active_neighbors.py \
    automation/lldp/scripts/test_lldp_31_reject_invalid_mgmt_address.py \
    automation/lldp/scripts/test_lldp_32_per_port_disable_peer_tx.py \
    automation/lldp/scripts/test_lldp_33_duplicate_chassis_port_id.py \
    automation/lldp/scripts/test_lldp_34_lldp_not_on_svis.py \
    automation/lldp/scripts/test_lldp_35_bulk_enable_interface_range.py \
    automation/lldp/scripts/test_lldp_36_bulk_tlv_toggle_range.py

# ==========================================================
# LLDP CLI Validation Tests (4 tests)
# ==========================================================
echo "Batch 2/3: LLDP CLI Validation"
run_lldp_test "LLDP_CLI_VALIDATION" "./testbeds/testbed_vs_2d_reg.yaml" \
    automation/lldp/scripts/test_lldp_cli_validation.py

# ==========================================================
# LLDP CLI Fix Tests (1 test)
# ==========================================================
echo "Batch 3/3: LLDP CLI Fix"
# Requires two connected DUTs (ensure_min_topology "D1D2:1") for LLDP neighbor
# discovery, so it runs on the 2-node testbed (a 1-node testbed -> TopoFail).
run_lldp_test "SM_ISCLI_P2_161_162_LLDP_CLI_FIX" "./testbeds/testbed_vs_2d_reg.yaml" \
    automation/lldp/scripts/test_sm_iscli_p2_161_162_lldp_cli_fix.py

# ==========================================================
# Generate Feature JSON  -> reports/LLDP_summary.json
# Built from the results_*_functions.csv files produced during the run.
# Reuses consolidate_feature_logs.py's proven parsing + JSON logic so the
# output schema matches LLDP_summary.json exactly.
# ==========================================================
echo "=============================================="
echo " Generating ${FEATURE_NAME} JSON"
echo "=============================================="

python3 - "${RESULTS_DIR}" "${JSON_FILE}" "${FEATURE_NAME}" <<'PYEOF'
import sys
import glob
import os

run_dir, json_file, feature = sys.argv[1], sys.argv[2], sys.argv[3]

# Reuse the existing consolidation logic (parse_functions_csv + generate_feature_json).
# Bypass __init__ via __new__: those two methods don't use feature_mapping.yaml, which
# isn't present at the spytest root in this checkout (it lives under test_run/support_files).
sys.path.insert(0, os.path.join("dashboard", "scripts"))
from consolidate_feature_logs import FeatureConsolidator

consolidator = FeatureConsolidator.__new__(FeatureConsolidator)

all_test_cases = []
pattern = os.path.join(run_dir, "**", "results_*_functions.csv")
csv_files = sorted(glob.glob(pattern, recursive=True))

if not csv_files:
    print("  ⚠️  No results_*_functions.csv found under {}".format(run_dir))
    sys.exit(1)

for csv_file in csv_files:
    # batch name = the top-level batch directory under run_dir
    rel = os.path.relpath(csv_file, run_dir)
    batch_name = rel.split(os.sep)[0]
    all_test_cases.extend(consolidator.parse_functions_csv(csv_file, batch_name))

if not all_test_cases:
    print("  ⚠️  No test cases parsed from {} CSV file(s)".format(len(csv_files)))
    sys.exit(1)

consolidator.generate_feature_json(feature, all_test_cases, json_file)
print("  Parsed {} CSV file(s), {} test cases".format(len(csv_files), len(all_test_cases)))
PYEOF

if [ $? -eq 0 ] && [ -f "${JSON_FILE}" ]; then
    echo "✓ JSON: ${JSON_FILE}"
else
    echo "✗ JSON generation failed"
fi

# ==========================================================
# Generate Feature Dashboard  -> reports/lldp_dashboard.html
# Built FROM the JSON (not the raw CSV paths) so every test is grouped under a
# single "${FEATURE_NAME}" module. The default CSV dashboard would label the
# per-path directory (e.g. automation/scripts/SM_ISCLI/ -> "SM_ISCLI"); since every script
# here belongs to the LLDP module, we force the module label to ${FEATURE_NAME}.
# ==========================================================
echo ""
echo "=============================================="
echo " Generating ${FEATURE_NAME} Dashboard"
echo "=============================================="

if [ -f "${JSON_FILE}" ]; then
    python3 dashboard/scripts/generate_dashboard_from_json.py \
        --json "${JSON_FILE}" \
        --out "${DASHBOARD_FILE}" \
        --module-name "${FEATURE_NAME}" \
        --name "${FEATURE_DISPLAY} - ${DATE_DIR}"

    if [ $? -eq 0 ] && [ -f "${DASHBOARD_FILE}" ]; then
        echo "✓ Dashboard: ${DASHBOARD_FILE}"
    else
        echo "✗ Dashboard generation failed"
    fi
else
    echo "✗ Skipping dashboard: ${JSON_FILE} not found"
fi

echo ""
echo "=============================================="
echo " ${FEATURE_NAME} Execution Complete"
echo "=============================================="
echo "Logs:      ${RESULTS_DIR}"
echo "Dashboard: ${DASHBOARD_FILE}"
echo "JSON:      ${JSON_FILE}"
echo "=============================================="
