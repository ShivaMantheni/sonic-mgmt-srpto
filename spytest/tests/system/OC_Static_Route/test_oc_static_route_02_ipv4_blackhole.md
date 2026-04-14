# Test Case Documentation: OC-SR-11 - IPv4 Static Route Blackhole Routes

**Test Case ID:** OC-SR-11
**Test Script:** `test_oc_static_route_02_ipv4_blackhole.py`
**Category:** Basic Functionality (IPv4) - Blackhole Routes
**Priority:** P0 (Critical)
**Status:** ✅ IMPLEMENTED
**Author:** Network Automation Team
**Copyright:** © 2026
**Last Updated:** April 12, 2026

---

## Table of Contents

1. [Test Overview](#test-overview)
2. [Test Objective](#test-objective)
3. [Topology Requirements](#topology-requirements)
4. [Configuration Details](#configuration-details)
5. [Test Steps](#test-steps)
6. [Verification Points](#verification-points)
7. [Expected Results](#expected-results)
8. [Cleanup Procedure](#cleanup-procedure)
9. [Execution Instructions](#execution-instructions)
10. [Known Issues](#known-issues)
11. [References](#references)

---

## Test Overview

This test case validates IPv4 blackhole static route functionality in OpenConfig (OC) build. Blackhole routes drop packets destined to specified prefixes without sending ICMP unreachable messages. This is useful for:
- Preventing routing loops
- Dropping unwanted traffic
- Network security (blocking malicious destinations)
- Traffic engineering

**Key Features Tested:**
- IPv4 blackhole route configuration
- Blackhole route verification in routing tables
- Mixed blackhole and normal static routes
- Blackhole route removal
- OC-build Klish CLI compatibility

**Test Type:** Functional
**CLI Mode:** Klish (sonic-cli)
**Build Type:** OC-build (OpenConfig)

---

## Test Objective

**Primary Objective:**
Verify that IPv4 blackhole static routes can be successfully configured, verified, and removed using sonic-cli (Klish) commands in OC-build, and that they correctly drop traffic to specified destinations.

**Specific Goals:**
1. Configure blackhole routes using `ip route <prefix> blackhole` syntax
2. Verify blackhole routes display as "Unreachable (blackhole)" in routing table
3. Configure normal static routes alongside blackhole routes
4. Verify both route types coexist correctly
5. Remove blackhole routes cleanly
6. Verify routes are removed from routing tables

**Success Criteria:**
- ✅ Blackhole routes configured without errors
- ✅ Blackhole routes show "Unreachable (blackhole)" in `show ip route`
- ✅ Normal routes configured alongside blackhole routes
- ✅ All routes visible in routing table with correct type
- ✅ Routes can be removed cleanly
- ✅ Routes disappear from routing table after removal

---

## Topology Requirements

### Network Topology

```
┌──────────────┐                    ┌──────────────┐
│   DUT1       │                    │   DUT2       │
│              │                    │              │
│  Ethernet0   │◄──────────────────►│  Ethernet0   │
│  10.1.1.1/24 │    Link-1          │  10.1.1.2/24 │
│              │                    │              │
└──────────────┘                    └──────────────┘

Blackhole Routes:
  DUT1: 172.16.10.0/24 → blackhole (drops all traffic)
  DUT2: 172.16.20.0/24 → blackhole (drops all traffic)

Normal Routes:
  DUT1: 172.16.20.0/24 → 10.1.1.2 (forwards to DUT2)
  DUT2: 172.16.10.0/24 → 10.1.1.1 (forwards to DUT1)
  DUT2: 172.16.30.0/24 → 10.2.1.2 (forwards to next-hop)
```

### Hardware Requirements

| Component | Requirement |
|-----------|-------------|
| **DUTs** | 2 SONiC devices |
| **Build Type** | OC-build (OpenConfig integration) |
| **Platform** | SONiC-VS (Virtual Switch) or Hardware |
| **Ports per DUT** | Minimum 1 Ethernet port |
| **Connections** | 1 link between DUT1-DUT2 |

### IP Addressing Scheme

#### DUT1 Configuration
| Interface | IP Address | Subnet | Connected To |
|-----------|------------|--------|--------------|
| Ethernet0 | 10.1.1.1 | /24 | DUT2 Ethernet0 |

#### DUT2 Configuration
| Interface | IP Address | Subnet | Connected To |
|-----------|------------|--------|--------------|
| Ethernet0 | 10.1.1.2 | /24 | DUT1 Ethernet0 |

---

## Configuration Details

### DUT1 Configuration Commands

```bash
sonic-cli
configure terminal

# Configure Ethernet0
interface Ethernet 0
  ip address 10.1.1.1/24
  no shutdown
  exit

# Add blackhole route - drops traffic to 172.16.10.0/24
ip route 172.16.10.0/24 blackhole

# Add normal static route - forwards to DUT2
ip route 172.16.20.0/24 10.1.1.2

exit
```

### DUT2 Configuration Commands

```bash
sonic-cli
configure terminal

# Configure Ethernet0
interface Ethernet 0
  ip address 10.1.1.2/24
  no shutdown
  exit

# Add normal route pointing to DUT1
ip route 172.16.10.0/24 10.1.1.1

# Add blackhole route - drops traffic to 172.16.20.0/24
ip route 172.16.20.0/24 blackhole

# Add another normal route
ip route 172.16.30.0/24 10.2.1.2

exit
```

### Verification Commands

```bash
# Show all static routes
show ip route static

# Show specific blackhole route
show ip route 172.16.10.0/24

# Show running configuration (blackhole routes)
show running-configuration | grep "blackhole"

# Expected output for blackhole route:
# S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
```

---

## Test Steps

### Step 1: Pre-Configuration Cleanup
**Action:** Clear any existing IP addresses and static routes on both DUTs
**Command:** Automated by script's `static_route_pre_config()` function
**Expected Result:** Clean state with no conflicting configurations

### Step 2: Configure IP Addresses
**Action:** Configure Ethernet0 on both DUTs with IP addresses
**Commands:**
```bash
# DUT1
interface Ethernet 0
  ip address 10.1.1.1/24
  no shutdown

# DUT2
interface Ethernet 0
  ip address 10.1.1.2/24
  no shutdown
```
**Verification:** Interfaces up, IP addresses assigned
**Test Case ID:** TC-OC-SR-11-001

### Step 3: Configure Blackhole Route on DUT1
**Action:** Add blackhole route for 172.16.10.0/24
**Command:**
```bash
ip route 172.16.10.0/24 blackhole
```
**Expected:** Route accepted without errors
**Test Case ID:** TC-OC-SR-11-002

### Step 4: Configure Normal Route on DUT1
**Action:** Add normal static route for 172.16.20.0/24
**Command:**
```bash
ip route 172.16.20.0/24 10.1.1.2
```
**Expected:** Route accepted without errors
**Test Case ID:** TC-OC-SR-11-002

### Step 5: Configure Routes on DUT2
**Action:** Add 1 normal route, 1 blackhole route, 1 additional normal route
**Commands:**
```bash
ip route 172.16.10.0/24 10.1.1.1
ip route 172.16.20.0/24 blackhole
ip route 172.16.30.0/24 10.2.1.2
```
**Expected:** All routes accepted without errors
**Test Case ID:** TC-OC-SR-11-002

### Step 6: Verify Blackhole Routes in Routing Tables
**Action:** Verify blackhole routes show "Unreachable (blackhole)"
**Commands:**
```bash
# DUT1
show ip route 172.16.10.0/24
# Expected: S    172.16.10.0/24          Unreachable (blackhole)

# DUT2
show ip route 172.16.20.0/24
# Expected: S    172.16.20.0/24          Unreachable (blackhole)

# Show all static routes
show ip route static
```
**Verification:**
- Blackhole routes show "Unreachable (blackhole)" marker
- Normal routes show next-hop IP addresses
- Both route types coexist in routing table
**Test Case ID:** TC-OC-SR-11-003

### Step 7: Verify Normal Routes
**Action:** Verify normal static routes are configured correctly
**Commands:**
```bash
# DUT1
show ip route 172.16.20.0/24
# Expected: S    172.16.20.0/24          10.1.1.2

# DUT2
show ip route 172.16.10.0/24
# Expected: S    172.16.10.0/24          10.1.1.1

show ip route 172.16.30.0/24
# Expected: S    172.16.30.0/24          10.2.1.2
```
**Verification:** All normal routes visible with correct next-hops
**Test Case ID:** TC-OC-SR-11-003

### Step 8: Remove All Routes
**Action:** Delete all configured static and blackhole routes
**Commands:**
```bash
# DUT1
no ip route 172.16.10.0/24 blackhole
no ip route 172.16.20.0/24 10.1.1.2

# DUT2
no ip route 172.16.10.0/24 10.1.1.1
no ip route 172.16.20.0/24 blackhole
no ip route 172.16.30.0/24 10.2.1.2
```
**Verification:** Deletion commands complete without errors
**Test Case ID:** TC-OC-SR-11-004

### Step 9: Verify Route Removal
**Action:** Confirm routes removed from routing tables
**Commands:**
```bash
show ip route 172.16.10.0/24
show ip route 172.16.20.0/24
show ip route 172.16.30.0/24
show ip route static
```
**Verification:** Routes no longer appear in routing tables
**Test Case ID:** TC-OC-SR-11-004

### Step 10: Cleanup
**Action:** Remove IP addresses and shutdown interfaces
**Command:** Automated by script's `static_route_cleanup()` function
**Expected Result:** Clean final state

---

## Verification Points

### Blackhole Route Verification

| DUT | Route Prefix | Command | Expected Output |
|-----|--------------|---------|-----------------|
| DUT1 | 172.16.10.0/24 | `show ip route 172.16.10.0/24` | `S    172.16.10.0/24          Unreachable (blackhole)            0/0         -` |
| DUT2 | 172.16.20.0/24 | `show ip route 172.16.20.0/24` | `S    172.16.20.0/24          Unreachable (blackhole)            0/0         -` |

### Normal Route Verification

| DUT | Route Prefix | Next-Hop | Command | Expected Output |
|-----|--------------|----------|---------|-----------------|
| DUT1 | 172.16.20.0/24 | 10.1.1.2 | `show ip route 172.16.20.0/24` | `S    172.16.20.0/24          10.1.1.2` |
| DUT2 | 172.16.10.0/24 | 10.1.1.1 | `show ip route 172.16.10.0/24` | `S    172.16.10.0/24          10.1.1.1` |
| DUT2 | 172.16.30.0/24 | 10.2.1.2 | `show ip route 172.16.30.0/24` | `S    172.16.30.0/24          10.2.1.2` |

### Running Configuration Verification

**Command:**
```bash
show running-configuration | grep "route"
```

**Expected Output (DUT1):**
```
ip route 172.16.10.0/24 blackhole
ip route 172.16.20.0/24 10.1.1.2
```

**Expected Output (DUT2):**
```
ip route 172.16.10.0/24 10.1.1.1
ip route 172.16.20.0/24 blackhole
ip route 172.16.30.0/24 10.2.1.2
```

**Note:** Due to known bug SOCCI-6XX, the grep filter may show entire configuration instead of filtered output.

---

## Expected Results

### Sample Output: DUT1 - show ip route static

```
Codes: K - kernel route, C - connected, S - static, B - BGP, O - OSPF
       > - selected route, * - FIB route, q - queued, r - rejected
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
```

### Sample Output: DUT2 - show ip route static

```
Codes: K - kernel route, C - connected, S - static, B - BGP, O - OSPF
       > - selected route, * - FIB route, q - queued, r - rejected
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    172.16.10.0/24          10.1.1.1                           0/0         -
 S    172.16.20.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.30.0/24          10.2.1.2                           0/0         -
```

### Key Observations

1. **Blackhole Marker:** Routes configured with `blackhole` show "Unreachable (blackhole)" in Gateway column
2. **Static Route Type:** All routes show 'S' code indicating static routes
3. **Distance/Metric:** Blackhole routes show 0/0 like normal static routes
4. **No FIB Selection:** Blackhole routes typically don't show '>' or '*' markers (not installed in FIB)
5. **Coexistence:** Blackhole and normal routes can coexist without conflicts

---

## Cleanup Procedure

The test script includes comprehensive cleanup that executes even if the test fails:

### Automatic Cleanup Steps

1. **Remove Blackhole Routes**
   - Delete all blackhole routes on both DUTs
   - Commands: `no ip route <prefix> blackhole`

2. **Remove Normal Static Routes**
   - Delete all normal static routes on both DUTs
   - Commands: `no ip route <prefix> <nexthop>`

3. **Remove IP Addresses**
   - Clear IP addresses from configured interfaces
   - Commands: `interface <X>; no ip address`

4. **Shutdown Interfaces**
   - Shutdown interfaces to clean state
   - Commands: `interface <X>; shutdown`

### Manual Cleanup (if needed)

If automatic cleanup fails, manually execute:

```bash
# On DUT1
sonic-cli
configure terminal

no ip route 172.16.10.0/24 blackhole
no ip route 172.16.20.0/24 10.1.1.2

interface Ethernet 0
  no ip address
  shutdown
  exit

exit

# On DUT2
sonic-cli
configure terminal

no ip route 172.16.10.0/24 10.1.1.1
no ip route 172.16.20.0/24 blackhole
no ip route 172.16.30.0/24 10.2.1.2

interface Ethernet 0
  no ip address
  shutdown
  exit

exit
```

---

## Execution Instructions

### Prerequisites

1. **Testbed File:** 2-DUT testbed YAML configured
   Location: `./testbeds/testbed_2vs.yaml`

2. **Network Access:** SSH access to both DUTs

3. **Build Verification:**
   ```bash
   # On each DUT
   show version
   # Verify: SONiC.oc-integration.0-<version>
   ```

### Running the Test

#### Option 1: Direct Execution

```bash
cd /home/adminuser/draksha/sonic-mgmt/spytest

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_2vs.yaml \
  tests/system/Static_Route/test_oc_static_route_02_ipv4_blackhole.py \
  --logs-path ./logs/oc_sr11_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

#### Option 2: With Test Markers

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_2vs.yaml \
  -m "blackhole and community_pass" \
  --logs-path ./logs/oc_sr11 \
  --log-level debug
```

#### Option 3: Run All Static Route Tests

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_2vs.yaml \
  -m "static_route" \
  --logs-path ./logs/static_routes \
  --log-level debug
```

### Command-Line Options Explained

| Option | Purpose |
|--------|---------|
| `--tryssh 1` | Enable SSH connection attempts |
| `--testbed <file>` | Specify testbed YAML file |
| `--logs-path <dir>` | Output directory for logs/results |
| `--log-level debug` | Enable detailed debug logging |
| `--skip-init-config` | Skip initial device configuration (faster) |
| `--ifname-type native` | Use native interface names (Ethernet 0, etc.) |
| `-m <marker>` | Run tests with specific pytest markers |

### Expected Execution Time

| Phase | Duration |
|-------|----------|
| **Pre-configuration** | 5-10 seconds |
| **Interface Configuration** | 5-10 seconds |
| **Blackhole Route Config** | 5-10 seconds |
| **Route Verification** | 5-10 seconds |
| **Route Removal** | 5-10 seconds |
| **Cleanup** | 5-10 seconds |
| **Total** | ~40-60 seconds |

### Log Files

After execution, check these logs in `--logs-path` directory:

| File | Content |
|------|---------|
| `dlog-D1-<device>.log` | DUT1 command/output logs |
| `dlog-D2-<device>.log` | DUT2 command/output logs |
| `module_test_oc_static_route_02_ipv4_blackhole.log` | Module execution logs |
| `results.html` | HTML test report |
| `summary.txt` | Quick test summary |

### Interpreting Results

**Test PASSED:**
```
TEST RESULT: OC-SR-11 PASSED
  ✓ Interface IP addresses configured
  ✓ Blackhole routes added successfully
  ✓ Blackhole routes verified with 'Unreachable (blackhole)'
  ✓ Normal routes added alongside blackhole routes
  ✓ All routes removed successfully
  ✓ Route removal verified
```

**Test FAILED:**
```
TEST RESULT: OC-SR-11 FAILED
  ✗ Test failed - check logs for details
```

Check `dlog-*` files for specific failure details.

---

## Known Issues

### Issue 1: Blackhole Routes May Not Show in FIB

**Severity:** Low
**Component:** Static Route / FRR

**Description:**
Blackhole routes may not display the '>' (selected) or '*' (FIB) markers in `show ip route` output, as they are not installed in the hardware forwarding table.

**Impact:**
This is expected behavior. Blackhole routes drop traffic in software before it reaches hardware.

**Workaround:**
None needed - this is correct behavior.

### Issue 2: grep Filter Not Working on show running-configuration

**Bug ID:** SOCCI-6XX (to be filed)
**Severity:** Medium
**Component:** OC-CLI

**Description:**
The `show running-configuration | grep "blackhole"` command shows the entire running configuration instead of filtering to only matching lines.

**Impact:**
Cannot filter configurations using grep. Must manually review full output.

**Workaround:**
Use `show ip route static` or `show running-configuration` without grep.

### Issue 3: Blackhole Traffic Behavior

**Severity:** Informational
**Component:** Static Route / FRR

**Description:**
Blackhole routes silently drop packets without sending ICMP unreachable messages back to the source.

**Impact:**
Applications may timeout waiting for responses instead of receiving immediate unreachable errors.

**Workaround:**
This is intended blackhole route behavior. Use reject routes if ICMP unreachable is needed (if supported).

---

## References

### Related Test Cases

- **test_oc_static_route_01_ipv4_basic_nexthop.py** - Basic next-hop route testing
- **test_static_route_02_ipv4_blackhole.py** - 2-DUT blackhole route test (ISCLI)
- **test_static_route_01_ipv4_basic.py** - 2-DUT basic static route test

### Manual Test Logs

- **Manual test log section:** Testcase 11: IPv4 BLACKHOLE ROUTES
- **DUT1 verification:** `show ip route static` showing "Unreachable (blackhole)"
- **DUT2 verification:** Multiple routes including blackhole

### Documentation

- **STATIC_ROUTE_testplan.md** - Complete static route test plan
- **STATIC_ROUTE_TEST_BREAKDOWN.md** - All 90 test cases breakdown
- **Requirements.txt** - Topology requirements

### SPyTest Framework

- **Doc/intro.md** - SPyTest framework introduction
- **CLAUDE.md** - Project overview and conventions

---

## Test Metadata

**PyTest Markers:**
- `@pytest.mark.static_route` - Static route test category
- `@pytest.mark.blackhole` - Blackhole route specific tests
- `@pytest.mark.community` - Community test suite
- `@pytest.mark.community_pass` - Community passing tests

**Test IDs:**
- TC-OC-SR-11-001: Interface configuration
- TC-OC-SR-11-002: Blackhole route addition
- TC-OC-SR-11-003: Blackhole route verification
- TC-OC-SR-11-004: Route removal

**Script Location:**
```
/home/adminuser/draksha/sonic-mgmt/spytest/tests/system/Static_Route/
  └── test_oc_static_route_02_ipv4_blackhole.py
```

**Configuration Format:**
- **CLI Type:** Klish (sonic-cli)
- **Interface Names:** Native (Ethernet 0, Ethernet 4, etc.)
- **Blackhole Route Format:** `ip route <prefix> blackhole`
- **Normal Route Format:** `ip route <prefix> <nexthop>`

---

## Use Cases for Blackhole Routes

### 1. Prevent Routing Loops
Configure blackhole route for aggregate prefix to prevent traffic loops when advertising summaries:
```bash
ip route 172.16.0.0/12 blackhole
```

### 2. Security - Block Malicious Traffic
Drop traffic to known malicious destinations:
```bash
ip route 192.0.2.0/24 blackhole  # Example malicious network
```

### 3. Traffic Engineering
Temporarily drop traffic during maintenance:
```bash
ip route 10.100.0.0/16 blackhole  # Drop traffic during migration
```

### 4. Discard Reserved/Unused Space
Drop traffic to unused address space:
```bash
ip route 172.31.0.0/16 blackhole  # Unused private space
```

---

## Troubleshooting

### Problem: Blackhole route not showing "Unreachable (blackhole)"

**Check:**
```bash
show ip route 172.16.10.0/24
show running-configuration | grep "172.16.10"
```

**Possible Causes:**
- Route configured with wrong syntax (missing "blackhole" keyword)
- Route overridden by more specific route
- Configuration not applied

**Solution:**
```bash
# Verify exact command
show running-configuration
# Look for: ip route 172.16.10.0/24 blackhole

# Re-configure if needed
configure terminal
ip route 172.16.10.0/24 blackhole
exit
```

### Problem: Cannot remove blackhole route

**Error:**
```
% Error: Route not found
```

**Solution:**
```bash
# Check exact prefix in running config
show running-configuration | grep "blackhole"

# Use exact prefix from running config
no ip route 172.16.10.0/24 blackhole
```

### Problem: Traffic still being forwarded instead of dropped

**Check:**
1. Verify blackhole route is in routing table:
   ```bash
   show ip route 172.16.10.0/24
   ```

2. Check for more specific routes:
   ```bash
   show ip route
   # Look for longer prefix matches
   ```

3. Verify source IP is not in blackhole range

**Note:** Blackhole routes match destination IPs, not source IPs.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-12 | Network Automation Team | Initial test case documentation for OC-SR-11 blackhole routes |

---

**Document End**
