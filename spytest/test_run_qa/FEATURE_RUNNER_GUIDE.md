# Feature-Based Test Runner - Complete Guide

**Date:** 2026-06-08
**System:** Simplified, Powerful Feature-Wise Test Execution

---

## Overview

This is a **new simplified batch system** that organizes test execution by feature. Each feature has its own script that runs all related tests and generates feature-specific outputs. A parent orchestrator consolidates everything into master reports.

### Key Benefits

✅ **Simplified**: One script per feature (lldp.sh, bgp.sh, vlan.sh)
✅ **Powerful**: Automatic dashboard and JSON generation per feature
✅ **Modular**: Easy to add/modify features independently
✅ **Consolidated**: Master dashboard + JSON from all features
✅ **Clean**: No modifications to existing run_testsuite_qa.sh

---

## Directory Structure

```
test_run/
├── run_testsuite.sh          # Parent orchestrator (NEW)
├── features/                  # Feature scripts (NEW)
│   ├── lldp.sh               # LLDP test runner
│   ├── bgp.sh                # BGP test runner
│   ├── vlan.sh               # VLAN test runner
│   ├── ospf.sh               # OSPF test runner
│   └── ...                   # More features
├── run_testsuite_qa.sh        # Original batch (untouched)
├── support_files/
│   └── feature_mapping.yaml
└── README.md
```

---

## How It Works

### Architecture

```
run_testsuite.sh (Parent)
    ├── Invokes → lldp.sh
    │   ├── Runs all LLDP tests
    │   ├── Generates logs/<DATE>/LLDP/dashboard_LLDP_<DATE>.html
    │   └── Generates logs/<DATE>/LLDP/LLDP.json
    │
    ├── Invokes → bgp.sh
    │   ├── Runs all BGP tests
    │   ├── Generates logs/<DATE>/BGP/dashboard_BGP_<DATE>.html
    │   └── Generates logs/<DATE>/BGP/BGP.json
    │
    ├── Invokes → vlan.sh
    │   ├── Runs all VLAN tests
    │   ├── Generates logs/<DATE>/VLAN/dashboard_VLAN_<DATE>.html
    │   └── Generates logs/<DATE>/VLAN/VLAN.json
    │
    └── Consolidates All
        ├── Master Dashboard: logs/<DATE>/dashboard/master_dashboard_<DATE>.html
        └── Master JSON: logs/<DATE>/master_results.json
```

### Execution Flow

1. **User runs** `./test_run/run_testsuite.sh --features LLDP,BGP`

2. **run_testsuite.sh**:
   - Validates features
   - Executes lldp.sh
   - Executes bgp.sh
   - Consolidates results

3. **Individual feature scripts** (e.g., lldp.sh):
   - Run all LLDP test batches
   - Generate feature-specific dashboard
   - Generate feature-specific JSON

4. **Consolidation**:
   - Master dashboard with all features
   - Master JSON with all feature results

---

## Usage

### Quick Start

```bash
cd /home/sonic-claude/athira/sonic-mgmt/spytest

# Run all features
./test_run/run_testsuite.sh

# Run specific features
./test_run/run_testsuite.sh --features LLDP

# Run multiple features
./test_run/run_testsuite.sh --features LLDP,BGP,VLAN

# List available features
./test_run/run_testsuite.sh --list

# Show help
./test_run/run_testsuite.sh --help
```

### Running Individual Features

You can also run feature scripts directly:

```bash
# Run LLDP tests only
./test_run/features/lldp.sh

# Run BGP tests only
./test_run/features/bgp.sh

# Run VLAN tests only
./test_run/features/vlan.sh
```

---

## Output Structure

### Per-Feature Outputs

When you run a feature (e.g., LLDP), you get:

```
logs/20260608/LLDP/
├── LLDP_COMPREHENSIVE__132629/
│   ├── results_*_functions.csv
│   ├── results_*_stats.csv
│   └── ...
├── SM_ISCLI_52_LLDP_CLI_VALIDATION__132629/
│   ├── results_*_functions.csv
│   └── ...
├── SM_ISCLI_P2_161_162_LLDP_CLI_FIX__132629/
│   └── ...
├── dashboard_LLDP_20260608_132629.html  ← Feature dashboard
└── LLDP.json                             ← Feature JSON
```

### Master Outputs

When run_testsuite.sh completes, you get:

```
logs/20260608/
├── LLDP/                  # LLDP feature directory
│   ├── dashboard_LLDP_*.html
│   └── LLDP.json
├── BGP/                   # BGP feature directory
│   ├── dashboard_BGP_*.html
│   └── BGP.json
├── VLAN/                  # VLAN feature directory
│   ├── dashboard_VLAN_*.html
│   └── VLAN.json
└── dashboard/
    └── master_dashboard_20260608_132629.html  ← Consolidated dashboard
└── master_results.json                         ← Consolidated JSON
```

---

## Feature Scripts

### Structure of a Feature Script

Each feature script follows this pattern:

```bash
#!/bin/bash

# 1. Feature metadata
FEATURE_NAME="LLDP"
FEATURE_DISPLAY="LLDP (Link Layer Discovery Protocol)"

# 2. Navigate to spytest root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPYTEST_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$SPYTEST_ROOT"

# 3. Create feature log directory
FEATURE_LOG="./logs/${DATE_DIR}/${FEATURE_NAME}"

# 4. Run test batches
run_test_batch "BATCH_NAME" "testbed.yaml" test1.py test2.py ...

# 5. Generate feature dashboard
python3 dashboard/scripts/generate_graphical_dashboard.py ...

# 6. Generate feature JSON
python3 dashboard/scripts/consolidate_feature_logs.py ...
```

### Available Feature Scripts

| Script | Feature | Test Count | Testbeds |
|--------|---------|------------|----------|
| `lldp.sh` | LLDP (Link Layer Discovery Protocol) | 40+ tests | testbed_vs_2d.yaml, testbed_vs_1node.yaml |
| `bgp.sh` | BGP (Border Gateway Protocol) | 50+ tests | testbed_vs_3rr.yaml, testbed_vs_2node.yaml, testbed_2vs.yaml |
| `vlan.sh` | VLAN (Virtual LAN) | 12+ tests | testbed_2node.yaml, testbed_vs_2d.yaml |
| `ospf.sh` | OSPF (Open Shortest Path First) | 40+ tests | testbed_4node.yaml |
| `ntp.sh` | NTP (Network Time Protocol) | 5+ tests | testbed_vs_1node.yaml |
| `acl.sh` | ACL (Access Control List) | 15+ tests | testbed_acl.yaml, ztp_standalone.yaml |
| `static_route.sh` | Static Route (IPv4/IPv6) | 30+ tests | testbed_vs_1node.yaml, testbed_oc_static_3vs.yaml |
| `portchannel.sh` | PortChannel (LAG) | 5+ tests | testbed_2node.yaml, testbed_vs_1node.yaml |
| `qos.sh` | QoS (Quality of Service) | 10+ tests | testbed_vs_2d.yaml, testbed_vs_1node.yaml |
| `arp.sh` | ARP (Address Resolution Protocol) | 30+ tests | testbed_2vs.yaml, ztp_standalone.yaml |

---

## Adding New Features

### Step 1: Create Feature Script

Create `test_run/features/your_feature.sh`:

```bash
#!/bin/bash

FEATURE_NAME="YOUR_FEATURE"
FEATURE_DISPLAY="Your Feature (Full Name)"
DATE_DIR=$(date +%Y%m%d)
TIME_STAMP=$(date +%H%M%S)

# Navigate to spytest root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPYTEST_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$SPYTEST_ROOT"

FEATURE_LOG="./logs/${DATE_DIR}/${FEATURE_NAME}"
mkdir -p "${FEATURE_LOG}"

# Define test runner function
run_test() {
    local batch_name=$1
    local testbed=$2
    shift 2
    local tests=("$@")

    local batch_log="${FEATURE_LOG}/${batch_name}__${TIME_STAMP}"
    mkdir -p "${batch_log}"

    ./bin/spytest --tryssh 1 \
        --testbed "${testbed}" \
        "${tests[@]}" \
        --logs-path "${batch_log}" \
        --log-level debug \
        --skip-init-config \
        --ifname-type native

    echo "Completed: ${batch_name}"
}

# Run your tests
run_test "BATCH_1" "./testbeds/testbed.yaml" \
    path/to/test1.py \
    path/to/test2.py

# Generate dashboard
DASHBOARD_FILE="${FEATURE_LOG}/dashboard_${FEATURE_NAME}_${DATE_DIR}_${TIME_STAMP}.html"
python3 dashboard/scripts/generate_graphical_dashboard.py \
    --log-root "${FEATURE_LOG}" \
    --out "${DASHBOARD_FILE}" \
    --name "${FEATURE_DISPLAY} - ${DATE_DIR}"

# Generate JSON
JSON_FILE="${FEATURE_LOG}/${FEATURE_NAME}.json"
python3 dashboard/scripts/consolidate_feature_logs.py \
    --log-root "${FEATURE_LOG}" \
    --consolidate \
    --json-output "${JSON_FILE}"

echo "Feature ${FEATURE_NAME} Complete"
echo "Dashboard: ${DASHBOARD_FILE}"
echo "JSON: ${JSON_FILE}"
```

### Step 2: Register in run_testsuite.sh

Edit `test_run/run_testsuite.sh` and add to the `FEATURES` array:

```bash
declare -A FEATURES=(
    ["LLDP"]="LLDP (Link Layer Discovery Protocol)"
    ["BGP"]="BGP (Border Gateway Protocol)"
    ["VLAN"]="VLAN (Virtual LAN)"
    ["YOUR_FEATURE"]="Your Feature (Full Name)"  # ← Add this
)
```

### Step 3: Make Executable

```bash
chmod +x test_run/features/your_feature.sh
```

### Step 4: Test

```bash
./test_run/run_testsuite.sh --features YOUR_FEATURE
```

---

## Dashboards

### Feature Dashboard

Each feature gets its own dashboard showing:
- All batches for that feature consolidated
- Test results from all batches
- Pass/Fail statistics
- Runtime information

**Example:** `logs/20260608/LLDP/dashboard_LLDP_20260608.html`

### Master Dashboard

Consolidates all feature dashboards:
- Shows all features in tabs
- Aggregated statistics across all features
- Overall pass/fail rates
- Total runtime

**Example:** `logs/20260608/dashboard/master_dashboard_20260608.html`

---

## JSON Outputs

### Feature JSON

Each feature generates a structured JSON:

```json
{
  "feature": "LLDP",
  "display_name": "LLDP (Link Layer Discovery Protocol)",
  "batches": 3,
  "tests": {
    "total": 40,
    "passed": 35,
    "failed": 4,
    "skipped": 1
  },
  "test_cases": [
    {
      "id": "test_lldp_01",
      "result": "Pass",
      "duration": "0:01:30"
    }
  ]
}
```

### Master JSON

Consolidates all feature JSONs:

```json
{
  "execution": {
    "date": "20260608",
    "duration_seconds": 3600
  },
  "features": {
    "LLDP": { ... },
    "BGP": { ... },
    "VLAN": { ... }
  }
}
```

---

## Comparison: Old vs New System

### Old System (run_testsuite_qa.sh)

```bash
./batch_full_run_qa.sh --features A,B,C,D...
```

- Runs batches by letter codes (A, B, C...)
- Single monolithic script
- All features in one execution
- Complex batch mapping
- Dashboard consolidation happens externally

### New System (run_testsuite.sh)

```bash
./test_run/run_testsuite.sh --features LLDP,BGP,VLAN
```

- ✅ Runs by feature name (intuitive)
- ✅ Modular: one script per feature
- ✅ Can run features individually
- ✅ Clear feature organization
- ✅ Built-in dashboard + JSON generation

---

## Troubleshooting

### Feature Script Not Found

```
✗ SKIP: LLDP (script not found: lldp.sh)
```

**Solution:**
```bash
ls test_run/features/lldp.sh  # Verify file exists
chmod +x test_run/features/lldp.sh  # Make executable
```

### Dashboard Generation Failed

```
✗ Dashboard generation failed
```

**Solution:**
```bash
# Check if logs exist
ls -la logs/20260608/LLDP/

# Check if CSV files have data
wc -l logs/20260608/LLDP/*/results_*_functions.csv
```

### JSON Generation Failed

```
✗ JSON generation failed
```

**Solution:**
```bash
# Run consolidation manually
python3 dashboard/scripts/consolidate_feature_logs.py \
    --log-root logs/20260608/LLDP \
    --consolidate \
    --json-output logs/20260608/LLDP/LLDP.json
```

---

## Advanced Usage

### Run Features in Parallel

```bash
# Run multiple features simultaneously in separate terminals

# Terminal 1
./test_run/features/lldp.sh &

# Terminal 2
./test_run/features/bgp.sh &

# Terminal 3
./test_run/features/vlan.sh &

# Wait for all to complete
wait

# Then consolidate
./test_run/run_testsuite.sh --consolidate-only  # (feature to be added)
```

### Custom Testbed

Edit the feature script to use your testbed:

```bash
# In lldp.sh, change:
run_lldp_test "BATCH_NAME" "./testbeds/your_custom_testbed.yaml" \
    test1.py test2.py
```

### Dry Run

Test feature script without running tests:

```bash
# Edit feature script, add after line 1:
DRY_RUN=true

# Then in run_test function, add:
if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY RUN] Would execute: $tests"
    return 0
fi
```

---

## Best Practices

### 1. Feature Organization

- **Group related tests**: All LLDP tests in lldp.sh
- **Use clear names**: dashboard_LLDP_*.html, not dashboard_1.html
- **Consistent structure**: All feature scripts follow same pattern

### 2. Testbed Selection

- Use appropriate testbeds for each feature
- Document testbed requirements in feature script header
- Validate testbed exists before running tests

### 3. Error Handling

- Check return codes after each batch
- Log failures clearly
- Continue execution even if one batch fails

### 4. Resource Management

- Clean up old logs periodically
- Monitor disk space in logs/ directory
- Archive completed test runs

---

## FAQ

**Q: Can I run individual batches without the feature script?**
A: Yes! You can still use `./bin/spytest` directly or the original `run_testsuite_qa.sh`.

**Q: What happens to old logs?**
A: Logs are organized by date (logs/YYYYMMDD/). Archive or delete old dates as needed.

**Q: Can I add custom test parameters?**
A: Yes! Edit the feature script and modify the `./bin/spytest` command with your parameters.

**Q: Does this replace run_testsuite_qa.sh?**
A: No! This is an additional, simplified system. The original script remains unchanged.

**Q: How do I consolidate existing logs?**
A: Use the dashboard generator directly:
```bash
python3 dashboard/scripts/generate_graphical_dashboard.py \
    --log-root logs/YYYYMMDD \
    --out dashboard.html
```

---

## Summary

✅ **Simplified**: One script per feature (10 features available)
✅ **Powerful**: Automatic dashboard + JSON per feature
✅ **Modular**: Easy to add/modify features independently
✅ **Consolidated**: Master dashboard + JSON from all features
✅ **Clean**: Original scripts untouched

**Available Features:**
- LLDP, BGP, VLAN, OSPF, NTP, ACL
- STATIC_ROUTE, PORTCHANNEL, QOS, ARP

**Start using:**
```bash
./test_run/run_testsuite.sh --features LLDP,BGP,VLAN
./test_run/run_testsuite.sh --features ACL,QOS,ARP
./test_run/run_testsuite.sh  # Run all 10 features
```

🎉 **Enjoy the new simplified test execution system!**
