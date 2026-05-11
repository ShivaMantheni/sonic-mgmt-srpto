# SM_ISCLI_52: LLDP CLI Output Issue - Test Scenario Guide

**Date**: 2026-05-10
**Issue**: LLDP show commands returned no output in IS-CLI while Click CLI displayed data
**Test Case ID**: SM_ISCLI_52
**Status**: Automated for Regression Testing

---

## Executive Summary

The issue SM_ISCLI_52 identified that LLDP show commands (`show lldp`, `show lldp neighbors`, `show lldp table`, `show lldp statistics`) returned empty output in IS-CLI (Klish) mode, while the same commands worked correctly in Click CLI mode.

This test suite validates that the fix has been applied and LLDP commands now return proper output in IS-CLI mode.

---

## Problem Description

### Observed Behavior (BROKEN)
```bash
sonic# show lldp
neighbor Display LLDP neighbor information
statistics Display LLDP statistics information
table Display LLDP table information

sonic# show lldp neighbors
(no output)

sonic# show lldp table
(no output)

sonic# show lldp statistics
(no output)
```

### Expected Behavior (AFTER FIX)
```bash
sonic# show lldp neighbors
-------------------------------------------------------------------------------
LLDP neighbors:
-------------------------------------------------------------------------------
Interface: Ethernet440, via: LLDP, RID: 1, Time: 0 day, 00:01:33
Chassis:
ChassisID: mac 90:5a:08:af:dc:3c
SysName: sonic
... [full neighbor information]

sonic# show lldp table
Capability codes: (R) Router, (B) Bridge, (O) Other
LocalPort RemoteDevice RemotePortID Capability RemotePortDescr
----------- -------------- -------------- ------------ --------------------------------
Ethernet440 sonic Eth63 BR Ethernet496
Ethernet496 sonic Eth56 BR Ethernet440
... [table entries]

sonic# show lldp statistics
Transmitted: 150
Received: 148
Discarded: 0
... [statistics]
```

---

## Root Cause

The issue was in the IS-CLI implementation where the `show lldp` commands were not properly implemented to display data, likely due to:
1. Missing subcommand handler for display data
2. Incomplete LLDP data retrieval in Klish parser
3. Command format mismatch between Click and Klish implementations

---

## Topology Used for Testing

```
+---------------------------+                    +---------------------------+
|         DUT1 (D1)         |                    |         DUT2 (D2)         |
|  (Active LLDP Advertiser) |                    | (Passive LLDP Listener)   |
|                           |                    |                           |
| Ethernet0 - - - - - - - - - - - - - - - - - - - Ethernet0                  |
| Ethernet4 - - - - - - - - - - - - - - - - - - - Ethernet4                  |
|                           |                    |                           |
+---------------------------+                    +---------------------------+

Testbed: testbed_vs_2d.yaml (2-node virtual topology)
```

---

## Test Case Breakdown

### TC-SM_ISCLI_52-001: show lldp neighbors
**Objective**: Verify that `show lldp neighbors` returns actual neighbor data in IS-CLI
**Validation**:
- Command executes without error
- Output is not empty
- Contains expected keywords: Interface, ChassisID, PortID
- Data format matches Click CLI output

**Expected Keywords**:
```
- Interface
- Chassis
- ChassisID
- Port
- PortID
- Capability
- TTL
```

---

### TC-SM_ISCLI_52-002: show lldp table
**Objective**: Verify that `show lldp table` displays neighbor information in tabular format
**Validation**:
- Command executes without error
- Output is not empty
- Contains expected table headers: LocalPort, RemoteDevice, RemotePortID
- Data format matches Click CLI output

**Expected Headers**:
```
LocalPort | RemoteDevice | RemotePortID | Capability | RemotePortDescr
```

---

### TC-SM_ISCLI_52-003: show lldp statistics
**Objective**: Verify that `show lldp statistics | no-more` displays protocol statistics
**Note**: The `| no-more` pipe is required in IS-CLI to disable pagination
**Validation**:
- Command executes without error: `show lldp statistics | no-more`
- Output is not empty
- Contains statistics counters
- Meaningful data (minimum 50 characters of output)

**Expected Content**:
```
- Transmitted counters
- Received counters
- Discarded counters
- Interface-specific statistics (if applicable)
```

---

### TC-SM_ISCLI_52-004: show lldp (bare command)
**Objective**: Verify that bare `show lldp` command displays subcommand help
**Validation**:
- Command handles incomplete input gracefully
- Displays available subcommands or help text
- Does not crash or return error

**Expected Behavior**:
```
sonic# show lldp
neighbor     Display LLDP neighbor information
statistics   Display LLDP statistics information
table        Display LLDP table information
```

---

### TC-SM_ISCLI_52-005: Compare Klish vs Click CLI
**Objective**: Comprehensive comparison of LLDP command behavior between modes
**Validation**:
- All key LLDP commands work in Klish mode:
  - `show lldp neighbors`
  - `show lldp table`
  - `show lldp statistics | no-more` (with no-more pipe for pagination)
  - `show lldp local-device`
- Output format consistency between modes
- No empty outputs for data-returning commands
- Note: `| no-more` pipe is required for statistics command in IS-CLI

---

## Setup & Configuration Steps

### Step 1: Topology Setup
```bash
# Load 2-node virtual testbed
./bin/spytest --testbed ./testbeds/testbed_vs_2d.yaml [test file]
```

### Step 2: Enable LLDP (if not already enabled)
```bash
sonic# configure terminal
sonic(config)# lldp run
sonic(config)# exit
sonic#
```

### Step 3: Ensure Physical Connectivity
```bash
# Verify interfaces are up and connected
sonic# show interfaces Ethernet0 Ethernet4
```

### Step 4: Wait for LLDP Discovery
```bash
# LLDP takes time to discover neighbors (typically 30-60 seconds)
# Default LLDP send interval: 30 seconds
# Default LLDP TTL: 120 seconds
```

---

## Execution Instructions

### Run Complete Test Suite
```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2d.yaml \
  system/lldp/test_sm_iscli_52_lldp_cli_output.py \
  --logs-path ./logs/test_sm_iscli_52_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

### Run Specific Test Case
```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2d.yaml \
  system/lldp/test_sm_iscli_52_lldp_cli_output.py::TestSmIscli52LldpCliOutput::test_01_lldp_show_neighbors_not_empty \
  --logs-path ./logs/test_sm_iscli_52_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

### Run via Batch
```bash
# Add to batch_full_run.sh if running as part of regression suite
./batch_full_run.sh --features LLDP_ISCLI_52
```

---

## Expected Test Results

### Success Scenario (After Fix Applied)
```
test_01_lldp_show_neighbors_not_empty ........................ PASSED ✓
test_02_lldp_show_table_not_empty ............................ PASSED ✓
test_03_lldp_show_statistics_not_empty ....................... PASSED ✓
test_04_lldp_show_command_has_subcommands .................... PASSED ✓
test_05_lldp_commands_compare_click_vs_klish ................ PASSED ✓

Total: 5 test cases PASSED
```

### Failure Scenario (Bug Still Present)
```
test_01_lldp_show_neighbors_not_empty ........................ FAILED ✗
  Error: lldp_show_neighbors_empty
  Description: 'show lldp neighbors' returned empty output

test_02_lldp_show_table_not_empty ............................ FAILED ✗
  Error: lldp_show_table_empty
  Description: 'show lldp table' returned empty output

test_03_lldp_show_statistics_not_empty ....................... FAILED ✗
  Error: lldp_show_statistics_empty
  Description: 'show lldp statistics' returned empty output
```

---

## Cleanup

The test automatically cleans up after execution:
- LLDP configuration is preserved (as it's part of normal DUT state)
- No additional resources created that need cleanup
- Test is idempotent (can run multiple times without side effects)

---

## Key Validation Points

| Command | Click CLI | IS-CLI (Before Fix) | IS-CLI (After Fix) |
|---------|-----------|-------------------|-------------------|
| `show lldp neighbors` | ✓ Returns data | ✗ Empty output | ✓ Returns data |
| `show lldp table` | ✓ Returns data | ✗ Empty output | ✓ Returns data |
| `show lldp statistics` | ✓ Returns data | ✗ Empty output | ✓ Returns data |
| `show lldp` | ✓ Shows subcommands | ✗ Shows subcommands | ✓ Shows subcommands |

---

## References

- **Jira Issue**: SM_ISCLI_52
- **Feature**: LLDP (Link Layer Discovery Protocol)
- **CLI Mode**: IS-CLI (Klish)
- **Platforms**: SONiC Virtual (VS), SONiC Hardware (HW)
- **Related Files**:
  - Test: `tests/system/lldp/test_sm_iscli_52_lldp_cli_output.py`
  - Variables: `vars/system/lldp/vars_sm_iscli_52_lldp_cli_output.yaml`
  - API: `apis/system/lldp.py`

---

## Troubleshooting

### Issue: LLDP Neighbors Not Discovered
**Cause**: Interfaces not connected or LLDP not enabled
**Solution**:
1. Verify physical connectivity between test devices
2. Enable LLDP: `configure terminal` → `lldp run` → `exit`
3. Wait 30+ seconds for neighbor discovery
4. Check interface status: `show interfaces`

### Issue: Empty LLDP Output in IS-CLI
**Cause**: Bug still present or incorrect CLI type
**Solution**:
1. Verify using `--ifname-type native` flag
2. Check that test is using Klish CLI type
3. Ensure SONiC image supports IS-CLI LLDP commands
4. Review logs for specific error messages

### Issue: Test Timeout
**Cause**: LLDP neighbor discovery taking longer than expected
**Solution**:
1. Increase `lldp_wait_time` in YAML variables
2. Check for network stability issues
3. Verify LLDP send interval is set correctly
4. Check logs for connectivity issues

---

## Maintenance & Updates

**Last Updated**: 2026-05-10
**Test Status**: Ready for Production
**Maintenance**: Update topology references if testbed configuration changes
**Future Work**: Add HW testbed validation when HW topology available

