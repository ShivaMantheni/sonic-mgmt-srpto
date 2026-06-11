#!/bin/bash

# ==========================================================
# PortChannel / LACP Feature Test Runner
# Runs all PortChannel/LACP tests and generates a feature-specific
# dashboard + JSON summary under this folder's reports/ dir.
#
# Outputs (all under tests/automation/portchannel/reports/):
#   reports/results/<batch>/            -> per-batch spytest logs (single dir, wiped each run)
#   reports/portchannel_dashboard.html  -> graphical dashboard
#   reports/PORTCHANNEL_summary.json    -> JSON built from results_*_functions.csv
# ==========================================================

FEATURE_NAME="PORTCHANNEL"
FEATURE_DISPLAY="PortChannel / LACP"
DATE_DIR=$(date +%Y%m%d)
TIME_STAMP=$(date +%H%M%S)

# Resolve paths.
#   SCRIPT_DIR   = .../spytest/tests/automation/portchannel
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

DASHBOARD_FILE="${REPORTS_DIR}/portchannel_dashboard.html"
JSON_FILE="${REPORTS_DIR}/PORTCHANNEL_summary.json"

echo "=============================================="
echo " ${FEATURE_DISPLAY} Test Execution"
echo " Date: ${DATE_DIR}"
echo " Time: ${TIME_STAMP}"
echo " Reports: ${REPORTS_DIR}"
echo "=============================================="
echo ""

# ==========================================================
# PortChannel / LACP Test Batches
# ==========================================================

run_pc_test() {
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
# Batch 1/3 : iSCLI PortChannel Tests (testbed_vs_2d_reg.yaml) - 2 tests
# ==========================================================
echo "Batch 1/3: iSCLI PortChannel Tests"
run_pc_test "PORTCHANNEL_ISCLI" "./testbeds/testbed_vs_2d_reg.yaml" \
    automation/portchannel/scripts/test_interface_1_iscli_portchannel.py \
    automation/portchannel/scripts/test_interface_2_iscli_portchannel_Reboot.py

# ==========================================================
# Batch 2/3 : LACP Fast Rate (testbed_vs_1node_reg.yaml) - 1 test
# ==========================================================
echo "Batch 2/3: LACP Fast Rate"
run_pc_test "LACP_FAST_RATE" "./testbeds/testbed_vs_1node_reg.yaml" \
    automation/portchannel/scripts/test_sm_iscli_p2_78_lacp_fast_rate.py

# ==========================================================
# Batch 3/3 : LACP Comprehensive Tests (testbed_lacp_vs.yaml) - 14 tests
# ==========================================================
echo "Batch 3/3: LACP Comprehensive Tests"
run_pc_test "LACP_COMPREHENSIVE" "./testbeds/testbed_lacp_vs.yaml" \
    automation/portchannel/scripts/test_lacp_cli_001_active_portchannel.py \
    automation/portchannel/scripts/test_lacp_cli_002_passive_portchannel.py \
    automation/portchannel/scripts/test_lacp_cli_004_add_members.py \
    automation/portchannel/scripts/test_lacp_cli_005_remove_members.py \
    automation/portchannel/scripts/test_lacp_cli_006_mtu_configuration.py \
    automation/portchannel/scripts/test_lacp_cli_007_shutdown_enable.py \
    automation/portchannel/scripts/test_lacp_cli_008_running_config.py \
    automation/portchannel/scripts/test_lacp_pos_009_traffic_distribution.py \
    automation/portchannel/scripts/test_lacp_pos_010_bidirectional_traffic.py \
    automation/portchannel/scripts/test_lacp_pos_011_pdu_exchange.py \
    automation/portchannel/scripts/test_lacp_pos_012_all_members_synced.py \
    automation/portchannel/scripts/test_lacp_pos_013_vlan_on_portchannel.py \
    automation/portchannel/scripts/test_lacp_pos_014_ip_on_vlan_svi.py \
    automation/portchannel/scripts/test_lacp_pos_015_mtu_configuration.py

# ==========================================================
# Generate Feature JSON  -> reports/PORTCHANNEL_summary.json
# Built from the results_*_functions.csv files produced during the run.
# Reuses consolidate_feature_logs.py's proven parsing + JSON logic so the
# output schema matches the feature summary schema exactly.
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
# Generate Feature Dashboard  -> reports/portchannel_dashboard.html
# Built FROM the JSON (not the raw CSV paths) so every test is grouped under a
# single "${FEATURE_NAME}" module.
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
