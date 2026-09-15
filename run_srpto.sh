#!/usr/bin/env bash
# =============================================================================
# run_srpto.sh — SRPTO Parallel Test Runner for sonic-mgmt (SpyTest edition)
# =============================================================================
#
# Drop-in parallel replacement for running spytest scripts sequentially.
# Runs multiple test scripts in parallel on a single topology, allocating
# idle DUTs dynamically — same logic as the Eka Execute Tab.
#
# YOUR SPYTEST COMMAND:
#   ./spytest/bin/spytest --tryssh 1 \
#       --testbed ./testbeds/testbed_vs_1node_reg.yaml \
#       automation/bfd/scripts/test_bfd_prof004_detmult_klish_reject.py \
#       --logs-path ./logs/bfd_prof004_$(date +%F_%H%M%S) \
#       --log-level debug --skip-init-config --ifname-type native
#
# SRPTO EQUIVALENT (runs multiple scripts in PARALLEL):
#   ./run_srpto.sh \
#       --testbed ./testbeds/testbed_vs_1node_reg.yaml \
#       --logs-dir ./logs \
#       --log-level debug \
#       --tryssh 1 \
#       --skip-init-config \
#       --ifname-type native \
#       automation/bfd/scripts/test_bfd_prof004_detmult_klish_reject.py \
#       automation/bgp/scripts/test_bgp_base.py \
#       automation/acl/scripts/test_acl_v4.py
#
# =============================================================================
#
# Usage:
#   ./run_srpto.sh [OPTIONS] script1.py script2.py ...
#
# Options (common):
#   --testbed PATH        Testbed YAML (required for real runs)
#   --logs-dir DIR        Base log directory (default: ./logs)
#   --resource-map PATH   SRPTO resource map YAML (auto-detect if omitted)
#   --dry-run             Resolve allocations only — no test execution
#   --generate-map OUT    Auto-generate a resource map YAML then exit
#
# SpyTest passthrough options (forwarded to every ./bin/spytest invocation):
#   --tryssh N            spytest --tryssh (default: 1)
#   --log-level LEVEL     debug / info / warning (default: debug)
#   --skip-init-config    Pass --skip-init-config to spytest
#   --ifname-type TYPE    Pass --ifname-type to spytest (e.g. native, alias)
#   --get-tech-support VAL Pass --get-tech-support to spytest (default: none)
#   --syslog-check VAL    Pass --syslog-check to spytest (default: none)
#   --extra-args "..."    Any other spytest args (quoted string)
#
# Advanced:
#   --mode {spytest,pytest}  Invocation mode (default: spytest)
#   --max-workers N          Max parallel scripts (default: 16)
#   --acquire-timeout SEC    DUT wait timeout seconds (0=forever)
#   --spytest-bin PATH       Explicit spytest binary (default: auto-detect)
#
# Examples:
#   # Run 3 BFD tests in parallel
#   ./run_srpto.sh \
#       --testbed ./testbeds/testbed_vs_1node_reg.yaml \
#       --log-level debug --skip-init-config --ifname-type native \
#       automation/bfd/scripts/test_bfd_prof004_detmult_klish_reject.py \
#       automation/bfd/scripts/test_bfd_prof005_echo.py \
#       automation/bfd/scripts/test_bfd_prof006_ipv6.py
#
#   # Mix BFD + BGP + ACL in parallel on a 4-DUT testbed
#   ./run_srpto.sh \
#       --testbed ./testbeds/testbed_4dut.yaml \
#       --resource-map srpto_resources.yaml \
#       --log-level debug --skip-init-config --ifname-type native \
#       automation/bfd/scripts/test_bfd_prof004_detmult_klish_reject.py \
#       automation/bgp/scripts/test_bgp_base.py \
#       automation/acl/scripts/test_acl_v4.py
#
#   # Dry-run — see what DUTs would be assigned without running anything
#   ./run_srpto.sh \
#       --testbed ./testbeds/testbed_vs_1node_reg.yaml \
#       --dry-run \
#       automation/bfd/scripts/test_bfd_prof004_detmult_klish_reject.py
#
#   # Auto-generate resource map from a set of scripts
#   ./run_srpto.sh \
#       --testbed ./testbeds/testbed_vs_1node_reg.yaml \
#       --generate-map srpto_resources.yaml \
#       automation/bfd/scripts/*.py
# =============================================================================

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

# ── Defaults ──────────────────────────────────────────────────────────────────
TESTBED=""
RESOURCE_MAP=""
LOGS_DIR="./logs"
DRY_RUN=""
GENERATE_MAP=""
MODE="spytest"
MAX_WORKERS="16"
ACQUIRE_TIMEOUT="0"
SPYTEST_BIN=""

# SpyTest passthrough flags
TRYSSH="1"
LOG_LEVEL="debug"
SKIP_INIT_CONFIG=""
IFNAME_TYPE=""
GET_TECH_SUPPORT="none"
SYSLOG_CHECK="none"
EXTRA_ARGS=()
SCRIPTS=()

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        # SRPTO options
        --testbed)          TESTBED="$2";           shift 2 ;;
        --resource-map)     RESOURCE_MAP="$2";       shift 2 ;;
        --logs-dir)         LOGS_DIR="$2";           shift 2 ;;
        --dry-run)          DRY_RUN="--dry-run";     shift ;;
        --generate-map)     GENERATE_MAP="$2";       shift 2 ;;
        --mode)             MODE="$2";               shift 2 ;;
        --max-workers)      MAX_WORKERS="$2";        shift 2 ;;
        --acquire-timeout)  ACQUIRE_TIMEOUT="$2";    shift 2 ;;
        --spytest-bin)      SPYTEST_BIN="$2";        shift 2 ;;
        # SpyTest passthrough
        --tryssh)           TRYSSH="$2";             shift 2 ;;
        --log-level)        LOG_LEVEL="$2";          shift 2 ;;
        --skip-init-config) SKIP_INIT_CONFIG="yes";  shift ;;
        --ifname-type)      IFNAME_TYPE="$2";        shift 2 ;;
        --get-tech-support) GET_TECH_SUPPORT="$2";   shift 2 ;;
        --syslog-check)     SYSLOG_CHECK="$2";       shift 2 ;;
        --extra-args)       EXTRA_ARGS+=("$2");      shift 2 ;;
        --*)                echo "[SRPTO] Unknown option: $1"; exit 1 ;;
        *)                  SCRIPTS+=("$1");         shift ;;
    esac
done

# ── Validation ────────────────────────────────────────────────────────────────
if [[ ${#SCRIPTS[@]} -eq 0 && -z "${GENERATE_MAP}" ]]; then
    echo "Usage: $0 [options] script1.py script2.py ..."
    echo "       $0 --generate-map out.yaml script1.py script2.py ..."
    exit 1
fi

# ── Build SpyTest extra-args string ──────────────────────────────────────────
# These are passed via --extra-args to SRPTO, which appends them to each
# individual ./bin/spytest invocation — mirroring your single-script command:
#   ./bin/spytest --tryssh 1 --testbed TB SCRIPT --logs-path LOGS --log-level debug ...
SPYTEST_PASSTHROUGH=(
    "--tryssh" "${TRYSSH}"
    "--log-level" "${LOG_LEVEL}"
    "--get-tech-support" "${GET_TECH_SUPPORT}"
    "--syslog-check" "${SYSLOG_CHECK}"
)
[[ -n "${SKIP_INIT_CONFIG}" ]] && SPYTEST_PASSTHROUGH+=("--skip-init-config")
[[ -n "${IFNAME_TYPE}" ]]      && SPYTEST_PASSTHROUGH+=("--ifname-type" "${IFNAME_TYPE}")
SPYTEST_PASSTHROUGH+=("${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}")

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================"
echo "  SRPTO — SONiC Resource-Aware Parallel Test Orchestrator"
echo "================================================================"
echo "  Testbed    : ${TESTBED:-auto-detect}"
echo "  Resources  : ${RESOURCE_MAP:-auto-detect}"
echo "  Mode       : ${MODE}"
echo "  Scripts    : ${#SCRIPTS[@]} file(s)"
echo "  Logs dir   : ${LOGS_DIR}"
echo "  SpyTest    : tryssh=${TRYSSH} log-level=${LOG_LEVEL}"
[[ -n "${SKIP_INIT_CONFIG}" ]] && echo "               skip-init-config=yes"
[[ -n "${IFNAME_TYPE}" ]]      && echo "               ifname-type=${IFNAME_TYPE}"
[[ -n "${DRY_RUN}" ]]          && echo "  *** DRY-RUN MODE — no tests will execute ***"
echo "================================================================"
echo ""

mkdir -p "${LOGS_DIR}"

# ── Generate resource map and exit ───────────────────────────────────────────
if [[ -n "${GENERATE_MAP}" ]]; then
    echo "[SRPTO] Generating resource map → ${GENERATE_MAP}"
    cd "${SCRIPT_DIR}"
    ${PYTHON} -m srpto.cli.srpto_run \
        --testbed "${TESTBED:-/dev/null}" \
        --scripts "${SCRIPTS[@]}" \
        --generate-resource-map "${GENERATE_MAP}"
    echo ""
    echo "[SRPTO] Edit ${GENERATE_MAP} and re-run without --generate-map"
    exit 0
fi

# ── Build SRPTO command ───────────────────────────────────────────────────────
CMD=(
    ${PYTHON} -m srpto.cli.srpto_run
    --mode "${MODE}"
    --logs-dir "${LOGS_DIR}"
    --json-results "${LOGS_DIR}/srpto_results.json"
    --max-workers "${MAX_WORKERS}"
    --acquire-timeout "${ACQUIRE_TIMEOUT}"
    --log-level INFO
    --scripts "${SCRIPTS[@]}"
)

[[ -n "${TESTBED}" ]]         && CMD+=(--testbed "${TESTBED}")
[[ -n "${RESOURCE_MAP}" ]]    && CMD+=(--resource-map "${RESOURCE_MAP}")
[[ -n "${SPYTEST_BIN}" ]]     && CMD+=(--spytest-bin "${SPYTEST_BIN}")
[[ -n "${DRY_RUN}" ]]         && CMD+=("${DRY_RUN}")

# Pass SpyTest flags through to every script invocation
if [[ ${#SPYTEST_PASSTHROUGH[@]} -gt 0 ]]; then
    CMD+=(--extra-args "${SPYTEST_PASSTHROUGH[@]}")
fi

# ── Run ───────────────────────────────────────────────────────────────────────
echo "[SRPTO] Command: ${CMD[*]}"
echo ""

cd "${SCRIPT_DIR}"
exec "${CMD[@]}"
