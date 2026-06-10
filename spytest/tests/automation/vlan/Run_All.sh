#!/bin/bash

# ==========================================================
# VLAN Feature Test Runner
# Runs all VLAN tests and generates a feature-specific
# dashboard + JSON summary under this folder's reports/ dir.
#
# Outputs (all under tests/automation/vlan/reports/):
#   reports/results/<batch>/     -> per-batch spytest logs (single dir, wiped each run)
#   reports/vlan_dashboard.html  -> graphical dashboard
#   reports/VLAN_summary.json    -> JSON built from results_*_functions.csv
# ==========================================================

FEATURE_NAME="VLAN"
FEATURE_DISPLAY="VLAN (Virtual LAN)"
DATE_DIR=$(date +%Y%m%d)
TIME_STAMP=$(date +%H%M%S)

# Resolve paths.
#   SCRIPT_DIR   = .../spytest/tests/automation/vlan
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

DASHBOARD_FILE="${REPORTS_DIR}/vlan_dashboard.html"
JSON_FILE="${REPORTS_DIR}/VLAN_summary.json"

echo "=============================================="
echo " ${FEATURE_DISPLAY} Test Execution"
echo " Date: ${DATE_DIR}"
echo " Time: ${TIME_STAMP}"
echo " Reports: ${REPORTS_DIR}"
echo "=============================================="
echo ""

# ==========================================================
# VLAN Test Batches
# ==========================================================

run_vlan_test() {
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
# Batch 1/5 : VLAN 2-DUT Tests (testbed_vs_2d_reg.yaml) - 12 tests
# Note: reboot tests are isolated into their own batch (Batch 2) so a
# reboot timeout cannot abort the rest of these tests.
# ==========================================================
echo "Batch 1/5: VLAN 2-DUT Tests"
run_vlan_test "VLAN_2D" "./testbeds/testbed_vs_2d_reg.yaml" \
    automation/vlan/scripts/test_interface_1_iscli_vlan.py \
    automation/vlan/scripts/test_interface_2_iscli_vlan_ip.py \
    automation/vlan/scripts/test_remove_vlan_interface.py \
    automation/vlan/scripts/test_vlan_negative_member.py \
    automation/vlan/scripts/test_vlan_create_delete.py \
    automation/vlan/scripts/test_vlan_access_port_change.py \
    automation/vlan/scripts/test_vlan_access_port.py \
    automation/vlan/scripts/test_vlan_isolation.py \
    automation/vlan/scripts/test_vlan_trunk_port.py \
    automation/vlan/scripts/test_vlan_trunk_segregation.py \
    automation/vlan/scripts/test_vlan_mixed_port.py \
    automation/vlan/scripts/test_vlan_native.py

# ==========================================================
# Batch 2/5 : VLAN Reboot Tests (testbed_vs_2d_reg.yaml) - 2 tests
# Isolated batch: these tests reboot the DUT and can time out; running them
# separately keeps a reboot failure from aborting the other 2-DUT tests.
# ==========================================================
echo "Batch 2/5: VLAN Reboot Tests"
run_vlan_test "VLAN_REBOOT" "./testbeds/testbed_vs_2d_reg.yaml" \
    automation/vlan/scripts/test_interface_1_iscli_vlan_reboot.py \
    automation/vlan/scripts/test_interface_2_iscli_vlan_ip_reboot.py

# ==========================================================
# Batch 3/5 : VLAN Standalone Tests (ztp_standalone_reg.yaml) - 5 tests
# ==========================================================
echo "Batch 3/5: VLAN Standalone Tests"
run_vlan_test "VLAN_STANDALONE" "./testbeds/ztp_standalone_reg.yaml" \
    automation/vlan/scripts/test_vlan_basic_config.py \
    automation/vlan/scripts/test_vlan_interface_lifecycle.py \
    automation/vlan/scripts/test_vlan_persistence.py \
    automation/vlan/scripts/test_vlan_boundary_deletion.py \
    automation/vlan/scripts/test_vlan_trunk_config_removal.py

# ==========================================================
# Batch 4/5 : VLAN 2-VS Tests (testbed_2vs_reg.yaml) - 3 tests
# ==========================================================
echo "Batch 4/5: VLAN 2-VS Tests"
run_vlan_test "VLAN_2VS" "./testbeds/testbed_2vs_reg.yaml" \
    automation/vlan/scripts/test_vlan_iscli_p2_42_svi_removal.py \
    automation/vlan/scripts/test_vlan_iscli_p2_39_switchport_trunk_vlan.py \
    automation/vlan/scripts/test_vlan_svi_l3_traffic_2dut.py

# ==========================================================
# Batch 5/5 : VLAN 3-DUT Delete Tests (testbed_vs_3d_reg.yaml) - 2 tests
# ==========================================================
echo "Batch 5/5: VLAN 3-DUT Delete Tests"
run_vlan_test "VLAN_3D_DELETE" "./testbeds/testbed_vs_3d_reg.yaml" \
    automation/vlan/scripts/test_vlan_delete_with_members.py \
    automation/vlan/scripts/test_vlan_delete_verification.py

# ==========================================================
# Generate Feature JSON  -> reports/VLAN_summary.json
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
# Generate Feature Dashboard  -> reports/vlan_dashboard.html
# Built FROM the JSON (not the raw CSV paths) so every test is grouped under a
# single "${FEATURE_NAME}" module. The default CSV dashboard would label the
# per-path directory; since every script here belongs to the VLAN module, we
# force the module label to ${FEATURE_NAME}.
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
