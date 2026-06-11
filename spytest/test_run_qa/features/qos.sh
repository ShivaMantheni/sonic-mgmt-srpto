#!/bin/bash

# ==========================================================
# QoS Feature Test Runner
# Runs all QoS tests and generates feature-specific dashboard
# ==========================================================

FEATURE_NAME="QOS"
FEATURE_DISPLAY="QoS (Quality of Service)"
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
# QoS Test Runner Function
# ==========================================================

run_qos_test() {
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
# QoS PFC Priority PG Map
# ==========================================================
echo "Batch 1/5: QoS PFC Priority PG Map"
run_qos_test "QOS_PFC_PRIORITY_PG_MAP" "./testbeds/testbed_vs_2d.yaml" \
    qos/test_qos_pfc_priority_pg_map.py

# ==========================================================
# QoS PFC PG Map Negative Tests
# ==========================================================
echo "Batch 2/5: QoS PFC PG Map Negative"
run_qos_test "QOS_PFC_PG_MAP_NEGATIVE" "./testbeds/testbed_vs_1node.yaml" \
    qos/test_qos_pfc_pg_map_negative.py

# ==========================================================
# QoS PFC PG Map Configuration
# ==========================================================
echo "Batch 3/5: QoS PFC PG Map Configuration"
run_qos_test "QOS_PFC_PG_MAP_CONFIG" "./testbeds/testbed_vs_1node.yaml" \
    qos/test_qos_pfc_pg_map_config.py

# ==========================================================
# QoS PFC PG Map Persistence
# ==========================================================
echo "Batch 4/5: QoS PFC PG Map Persistence"
run_qos_test "QOS_PFC_PG_MAP_PERSISTENCE" "./testbeds/testbed_vs_1node.yaml" \
    qos/test_qos_pfc_pg_map_persistence.py

# ==========================================================
# QoS Delete Active PFC Map
# ==========================================================
echo "Batch 5/5: QoS Delete Active PFC"
run_qos_test "QOS_DELETE_ACTIVE_PFC" "./testbeds/testbed_vs_1node.yaml" \
    qos/test_qos_delete_active_pfc_map.py

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
