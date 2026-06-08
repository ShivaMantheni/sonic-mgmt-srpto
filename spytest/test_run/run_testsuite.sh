#!/bin/bash

# ==========================================================
# Feature-Based Test Runner (Parent Orchestrator)
# Simplified, powerful batch system for feature-wise execution
#
# Each feature script (lldp.sh, bgp.sh, etc.):
#   - Runs all tests for that feature
#   - Generates feature-specific dashboard
#   - Generates feature-specific JSON
#
# This parent script:
#   - Orchestrates feature execution
#   - Consolidates feature dashboards into master dashboard
#   - Consolidates feature JSONs into master JSON
# ==========================================================

DATE_DIR=$(date +%Y%m%d)
TIME_STAMP=$(date +%H%M%S)

# Navigate to spytest root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPYTEST_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$SPYTEST_ROOT"

# Master log directory
MASTER_LOG="./logs/${DATE_DIR}"
mkdir -p "${MASTER_LOG}"

# ==========================================================
# Available Features
# ==========================================================
declare -A FEATURES=(
    ["LLDP"]="LLDP (Link Layer Discovery Protocol)"
    ["BGP"]="BGP (Border Gateway Protocol)"
    ["VLAN"]="VLAN (Virtual LAN)"
    ["OSPF"]="OSPF (Open Shortest Path First)"
    ["NTP"]="NTP (Network Time Protocol)"
    ["ACL"]="ACL (Access Control List)"
    ["STATIC_ROUTE"]="Static Route (IPv4/IPv6)"
    ["PORTCHANNEL"]="PortChannel (LAG)"
    ["QOS"]="QoS (Quality of Service)"
    ["ARP"]="ARP (Address Resolution Protocol)"
)

# ==========================================================
# Helper Functions
# ==========================================================

show_usage() {
    cat << EOF
==============================================
 Feature-Based Test Runner
==============================================

Usage:
  $0                          # Run all features
  $0 --list                   # List available features
  $0 --features <features>    # Run specific features
  $0 --help                   # Show this help

Examples:
  $0 --features LLDP          # Run LLDP only
  $0 --features LLDP,BGP,VLAN # Run multiple features
  $0                          # Run all features

Available Features:
EOF

    for feature in $(echo "${!FEATURES[@]}" | tr ' ' '\n' | sort); do
        printf "  %-15s : %s\n" "$feature" "${FEATURES[$feature]}"
    done

    echo ""
    echo "Feature Scripts Location: $SCRIPT_DIR/features/"
    echo "Logs Location: ./logs/<DATE>/<FEATURE>/"
    echo ""
}

list_features() {
    echo "=============================================="
    echo " Available Features"
    echo "=============================================="
    echo ""

    for feature in $(echo "${!FEATURES[@]}" | tr ' ' '\n' | sort); do
        script_path="$SCRIPT_DIR/features/${feature,,}.sh"
        if [ -f "$script_path" ]; then
            printf "  ✓ %-15s : %s\n" "$feature" "${FEATURES[$feature]}"
        else
            printf "  ✗ %-15s : %s (script missing)\n" "$feature" "${FEATURES[$feature]}"
        fi
    done
    echo ""
}

# ==========================================================
# Parse Arguments
# ==========================================================

SELECTED_FEATURES=()
RUN_ALL=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --list|-l)
            list_features
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
            IFS=',' read -ra FEATURES_ARG <<< "$2"
            for feature in "${FEATURES_ARG[@]}"; do
                feature=$(echo "$feature" | xargs | tr '[:lower:]' '[:upper:]')
                if [[ -n "${FEATURES[$feature]}" ]]; then
                    SELECTED_FEATURES+=("$feature")
                else
                    echo "WARNING: Unknown feature '$feature', skipping"
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

# ==========================================================
# Determine which features to run
# ==========================================================

FEATURES_TO_RUN=()

if [[ "$RUN_ALL" == "true" ]]; then
    echo "=============================================="
    echo " Running All Features"
    echo " Date: ${DATE_DIR}"
    echo " Time: ${TIME_STAMP}"
    echo "=============================================="
    echo ""

    for feature in $(echo "${!FEATURES[@]}" | tr ' ' '\n' | sort); do
        FEATURES_TO_RUN+=("$feature")
    done
else
    echo "=============================================="
    echo " Running Selected Features"
    echo " Date: ${DATE_DIR}"
    echo " Time: ${TIME_STAMP}"
    echo "=============================================="
    echo ""
    echo "Selected Features:"
    for feature in "${SELECTED_FEATURES[@]}"; do
        echo "  - $feature: ${FEATURES[$feature]}"
        FEATURES_TO_RUN+=("$feature")
    done
    echo ""
fi

if [[ ${#FEATURES_TO_RUN[@]} -eq 0 ]]; then
    echo "ERROR: No features to run"
    exit 1
fi

# ==========================================================
# Execute Feature Scripts
# ==========================================================

EXECUTION_START=$(date +%s)
FEATURE_RESULTS=()

echo "=============================================="
echo " Executing Feature Tests"
echo "=============================================="
echo ""

for feature in "${FEATURES_TO_RUN[@]}"; do
    feature_script="$SCRIPT_DIR/features/${feature,,}.sh"

    if [ ! -f "$feature_script" ]; then
        echo "✗ SKIP: $feature (script not found: ${feature,,}.sh)"
        echo ""
        continue
    fi

    echo "=============================================="
    echo " Feature: ${feature} - ${FEATURES[$feature]}"
    echo "=============================================="

    # Make script executable
    chmod +x "$feature_script"

    # Execute feature script
    FEATURE_START=$(date +%s)
    bash "$feature_script"
    FEATURE_RC=$?
    FEATURE_END=$(date +%s)
    FEATURE_DURATION=$((FEATURE_END - FEATURE_START))

    # Store result
    FEATURE_RESULTS+=("${feature}:${FEATURE_RC}:${FEATURE_DURATION}")

    if [ $FEATURE_RC -eq 0 ]; then
        echo "✓ Feature ${feature} completed successfully (${FEATURE_DURATION}s)"
    else
        echo "✗ Feature ${feature} failed with RC=${FEATURE_RC} (${FEATURE_DURATION}s)"
    fi

    echo ""
done

EXECUTION_END=$(date +%s)
TOTAL_DURATION=$((EXECUTION_END - EXECUTION_START))

# ==========================================================
# Consolidate Feature Dashboards into Master Dashboard
# ==========================================================

echo "=============================================="
echo " Consolidating Feature Dashboards"
echo "=============================================="

MASTER_DASHBOARD="${MASTER_LOG}/dashboard/master_dashboard_${DATE_DIR}_${TIME_STAMP}.html"
mkdir -p "${MASTER_LOG}/dashboard"

# Collect all feature logs for master dashboard
python3 dashboard/scripts/generate_graphical_dashboard.py \
    --log-root "${MASTER_LOG}" \
    --out "${MASTER_DASHBOARD}" \
    --name "Master Dashboard - ${DATE_DIR}"

if [ $? -eq 0 ]; then
    echo "✓ Master Dashboard: ${MASTER_DASHBOARD}"
else
    echo "✗ Master Dashboard generation failed"
fi

echo ""

# ==========================================================
# Consolidate Feature JSONs into Master JSON
# ==========================================================

echo "=============================================="
echo " Consolidating Feature JSONs"
echo "=============================================="

MASTER_JSON="${MASTER_LOG}/master_results.json"

# Start master JSON
cat > "${MASTER_JSON}" << EOF
{
  "execution": {
    "date": "${DATE_DIR}",
    "timestamp": "${TIME_STAMP}",
    "start_time": ${EXECUTION_START},
    "end_time": ${EXECUTION_END},
    "duration_seconds": ${TOTAL_DURATION}
  },
  "features": {
EOF

# Add each feature's JSON
FIRST=true
for feature in "${FEATURES_TO_RUN[@]}"; do
    feature_json="${MASTER_LOG}/${feature}/${feature}.json"

    if [ -f "$feature_json" ]; then
        if [ "$FIRST" = false ]; then
            echo "," >> "${MASTER_JSON}"
        fi
        FIRST=false

        echo "    \"${feature}\": " >> "${MASTER_JSON}"
        cat "$feature_json" >> "${MASTER_JSON}"

        echo "  ✓ Consolidated: ${feature}.json"
    else
        echo "  ✗ Missing: ${feature}.json"
    fi
done

# Close master JSON
cat >> "${MASTER_JSON}" << EOF

  }
}
EOF

echo "✓ Master JSON: ${MASTER_JSON}"
echo ""

# ==========================================================
# Execution Summary
# ==========================================================

echo "=============================================="
echo " Execution Summary"
echo "=============================================="
echo ""
echo "Total Features: ${#FEATURES_TO_RUN[@]}"
echo "Total Duration: ${TOTAL_DURATION}s ($(($TOTAL_DURATION / 60))m $(($TOTAL_DURATION % 60))s)"
echo ""
echo "Feature Results:"

PASSED=0
FAILED=0

for result in "${FEATURE_RESULTS[@]}"; do
    IFS=':' read -r feature rc duration <<< "$result"

    if [ $rc -eq 0 ]; then
        echo "  ✓ ${feature}: PASS (${duration}s)"
        PASSED=$((PASSED + 1))
    else
        echo "  ✗ ${feature}: FAIL (RC=${rc}, ${duration}s)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "Summary: ${PASSED} passed, ${FAILED} failed"
echo ""

# ==========================================================
# Output Locations
# ==========================================================

echo "=============================================="
echo " Output Locations"
echo "=============================================="
echo ""
echo "Master Dashboard: ${MASTER_DASHBOARD}"
echo "Master JSON: ${MASTER_JSON}"
echo ""
echo "Feature Logs:"
for feature in "${FEATURES_TO_RUN[@]}"; do
    feature_log="${MASTER_LOG}/${feature}"
    if [ -d "$feature_log" ]; then
        echo "  - ${feature}: ${feature_log}/"
    fi
done
echo ""

# ==========================================================
# Quick Access URLs
# ==========================================================

echo "=============================================="
echo " Quick Access"
echo "=============================================="
echo ""
echo "Open Master Dashboard:"
echo "  file://$(pwd)/${MASTER_DASHBOARD}"
echo ""
echo "View Master JSON:"
echo "  cat ${MASTER_JSON} | python3 -m json.tool"
echo ""

# ==========================================================
# Exit with appropriate code
# ==========================================================

if [ $FAILED -eq 0 ]; then
    echo "=============================================="
    echo " ✓ All Features Passed"
    echo "=============================================="
    exit 0
else
    echo "=============================================="
    echo " ✗ Some Features Failed"
    echo "=============================================="
    exit 1
fi
