# Test Case Documentation: OC-SR-10 - IPv4 Static Route Basic Next-Hop (3 DUTs)

**Test Case ID:** OC-SR-10
**Test Script:** `test_oc_static_route_01_ipv4_basic_nexthop.py`
**Category:** Basic Functionality (IPv4)
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

This test case validates basic IPv4 static route functionality with next-hop IP addresses across a 3-DUT topology in OpenConfig (OC) build. The test configures static routes on all three DUTs, verifies route installation in the routing tables, and validates route removal.

**Key Features Tested:**
- IPv4 static route configuration with next-hop IP
- Multi-DUT route propagation
- Route verification in routing tables
- Route deletion and cleanup
- OC-build Klish CLI compatibility

**Test Type:** Functional
**CLI Mode:** Klish (sonic-cli)
**Build Type:** OC-build (OpenConfig)

---

## Test Objective

**Primary Objective:**
Verify that IPv4 static routes with next-hop IP addresses can be successfully configured, installed, verified, and removed across a 3-DUT linear topology using sonic-cli (Klish) commands in OC-build.

**Specific Goals:**
1. Configure IP addresses on multiple interfaces across 3 DUTs
2. Add static routes with next-hop IP addresses
3. Verify routes appear in routing tables with correct next-hop
4. Remove static routes cleanly
5. Verify routes are removed from routing tables
6. Ensure configuration persists in running-config

**Success Criteria:**
- ✅ All interface IP addresses configured successfully
- ✅ All static routes added without errors
- ✅ Routes visible in `show ip route` with 'S' (static) marker
- ✅ Routes show correct next-hop IP addresses
- ✅ Routes can be removed cleanly
- ✅ Routes disappear from routing table after removal

---

## Topology Requirements

### Network Topology

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   DUT1       │         │   DUT2       │         │   DUT3       │
│              │         │              │         │              │
│  Ethernet0   │◄───────►│  Ethernet0   │         │              │
│  10.1.1.1/24 │ Link-1  │  10.1.1.2/24 │         │              │
│              │         │              │         │              │
│  Ethernet4   │◄───────►│  Ethernet4   │         │              │
│  10.2.1.1/24 │ Link-2  │  10.1.2.2/24 │         │              │
│              │         │              │         │              │
│              │         │  Ethernet8   │◄───────►│  Ethernet8   │
│              │         │  10.2.1.1/24 │ Link-3  │  10.3.1.2/24 │
│              │         │              │         │              │
│              │         │  Ethernet12  │◄───────►│  Ethernet12  │
│              │         │  10.2.2.1/24 │ Link-4  │  10.3.2.2/24 │
└──────────────┘         └──────────────┘         └──────────────┘

Static Routes:
  DUT1: 30.30.30.0/24 → 10.1.1.2 (via DUT2)
        40.40.40.0/24 → 10.2.1.1 (via DUT2)

  DUT2: 30.30.30.0/24 → 10.2.1.2 (via DUT3)
        40.40.40.0/24 → 10.1.1.1 (via DUT1)

  DUT3: 40.40.40.0/24 → 10.2.1.1 (via DUT2)
```

### Hardware Requirements

| Component | Requirement |
|-----------|-------------|
| **DUTs** | 3 SONiC devices |
| **Build Type** | OC-build (OpenConfig integration) |
| **Platform** | SONiC-VS (Virtual Switch) or Hardware |
| **Ports per DUT** | Minimum 4 Ethernet ports |
| **Connections** | 2 links between DUT1-DUT2, 2 links between DUT2-DUT3 |

### IP Addressing Scheme

#### DUT1 Configuration
| Interface | IP Address | Subnet | Connected To |
|-----------|------------|--------|--------------|
| Ethernet0 | 10.1.1.1 | /24 | DUT2 Ethernet0 |
| Ethernet4 | 10.2.1.1 | /24 | DUT2 Ethernet4 |

#### DUT2 Configuration
| Interface | IP Address | Subnet | Connected To |
|-----------|------------|--------|--------------|
| Ethernet0 | 10.1.1.2 | /24 | DUT1 Ethernet0 |
| Ethernet4 | 10.1.2.2 | /24 | DUT1 Ethernet4 |
| Ethernet8 | 10.2.1.1 | /24 | DUT3 Ethernet8 |
| Ethernet12 | 10.2.2.1 | /24 | DUT3 Ethernet12 |

#### DUT3 Configuration
| Interface | IP Address | Subnet | Connected To |
|-----------|------------|--------|--------------|
| Ethernet8 | 10.3.1.2 | /24 | DUT2 Ethernet8 |
| Ethernet12 | 10.3.2.2 | /24 | DUT2 Ethernet12 |

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

# Configure Ethernet4
interface Ethernet 4
  ip address 10.2.1.1/24
  no shutdown
  exit

# Add static routes
ip route 30.30.30.0/24 10.1.1.2
ip route 40.40.40.0/24 10.2.1.1

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

# Configure Ethernet4
interface Ethernet 4
  ip address 10.1.2.2/24
  no shutdown
  exit

# Configure Ethernet8
interface Ethernet 8
  ip address 10.2.1.1/24
  no shutdown
  exit

# Configure Ethernet12
interface Ethernet 12
  ip address 10.2.2.1/24
  no shutdown
  exit

# Add static routes
ip route 30.30.30.0/24 10.2.1.2
ip route 40.40.40.0/24 10.1.1.1

exit
```

### DUT3 Configuration Commands

```bash
sonic-cli
configure terminal

# Configure Ethernet8
interface Ethernet 8
  ip address 10.3.1.2/24
  no shutdown
  exit

# Configure Ethernet12
interface Ethernet 12
  ip address 10.3.2.2/24
  no shutdown
  exit

# Add static route
ip route 40.40.40.0/24 10.2.1.1

exit
```

---

## Test Steps

### Step 1: Pre-Configuration Cleanup
**Action:** Clear any existing IP addresses and static routes on all DUTs
**Command:** Automated by script's `static_route_pre_config()` function
**Expected Result:** Clean state with no conflicting configurations

### Step 2: Configure IP Addresses on DUT1
**Action:** Configure Ethernet0 and Ethernet4 with IP addresses
**Commands:**
```bash
interface Ethernet 0
  ip address 10.1.1.1/24
  no shutdown
interface Ethernet 4
  ip address 10.2.1.1/24
  no shutdown
```
**Verification:** Interfaces up, IP addresses assigned
**Test Case ID:** TC-OC-SR-10-001

### Step 3: Configure IP Addresses on DUT2
**Action:** Configure all 4 interfaces with IP addresses
**Commands:**
```bash
interface Ethernet 0
  ip address 10.1.1.2/24
  no shutdown
interface Ethernet 4
  ip address 10.1.2.2/24
  no shutdown
interface Ethernet 8
  ip address 10.2.1.1/24
  no shutdown
interface Ethernet 12
  ip address 10.2.2.1/24
  no shutdown
```
**Verification:** All interfaces up, IP addresses assigned
**Test Case ID:** TC-OC-SR-10-001

### Step 4: Configure IP Addresses on DUT3
**Action:** Configure Ethernet8 and Ethernet12 with IP addresses
**Commands:**
```bash
interface Ethernet 8
  ip address 10.3.1.2/24
  no shutdown
interface Ethernet 12
  ip address 10.3.2.2/24
  no shutdown
```
**Verification:** Interfaces up, IP addresses assigned
**Test Case ID:** TC-OC-SR-10-001

### Step 5: Add Static Routes on DUT1
**Action:** Configure 2 static routes with next-hop IPs
**Commands:**
```bash
ip route 30.30.30.0/24 10.1.1.2
ip route 40.40.40.0/24 10.2.1.1
```
**Verification:** Routes accepted without errors
**Test Case ID:** TC-OC-SR-10-002

### Step 6: Add Static Routes on DUT2
**Action:** Configure 2 static routes with next-hop IPs
**Commands:**
```bash
ip route 30.30.30.0/24 10.2.1.2
ip route 40.40.40.0/24 10.1.1.1
```
**Verification:** Routes accepted without errors
**Test Case ID:** TC-OC-SR-10-002

### Step 7: Add Static Route on DUT3
**Action:** Configure 1 static route with next-hop IP
**Commands:**
```bash
ip route 40.40.40.0/24 10.2.1.1
```
**Verification:** Route accepted without errors
**Test Case ID:** TC-OC-SR-10-002

### Step 8: Verify Routes in Routing Tables
**Action:** Verify all routes installed correctly
**Commands:**
```bash
# On DUT1
show ip route 30.30.30.0/24
show ip route 40.40.40.0/24

# On DUT2
show ip route 30.30.30.0/24
show ip route 40.40.40.0/24

# On DUT3
show ip route 40.40.40.0/24

# Also verify with
show ip route static
```
**Verification:**
- Routes show 'S' (static) marker
- Correct next-hop IP addresses displayed
- Routes present in routing table
**Test Case ID:** TC-OC-SR-10-003

### Step 9: Remove Static Routes
**Action:** Delete all configured static routes
**Commands:**
```bash
# DUT1
no ip route 30.30.30.0/24 10.1.1.2
no ip route 40.40.40.0/24 10.2.1.1

# DUT2
no ip route 30.30.30.0/24 10.2.1.2
no ip route 40.40.40.0/24 10.1.1.1

# DUT3
no ip route 40.40.40.0/24 10.2.1.1
```
**Verification:** Deletion commands complete without errors
**Test Case ID:** TC-OC-SR-10-004

### Step 10: Verify Route Removal
**Action:** Confirm routes removed from routing tables
**Commands:**
```bash
show ip route <prefix>
show ip route static
```
**Verification:** Routes no longer appear in routing tables
**Test Case ID:** TC-OC-SR-10-004

### Step 11: Cleanup
**Action:** Remove IP addresses and shutdown interfaces
**Command:** Automated by script's `static_route_cleanup()` function
**Expected Result:** Clean final state

---

## Verification Points

### Interface Configuration Verification

| DUT | Interface | Command | Expected Output |
|-----|-----------|---------|-----------------|
| DUT1 | Ethernet0 | `show ip interface brief` | 10.1.1.1/24, up |
| DUT1 | Ethernet4 | `show ip interface brief` | 10.2.1.1/24, up |
| DUT2 | Ethernet0 | `show ip interface brief` | 10.1.1.2/24, up |
| DUT2 | Ethernet4 | `show ip interface brief` | 10.1.2.2/24, up |
| DUT2 | Ethernet8 | `show ip interface brief` | 10.2.1.1/24, up |
| DUT2 | Ethernet12 | `show ip interface brief` | 10.2.2.1/24, up |
| DUT3 | Ethernet8 | `show ip interface brief` | 10.3.1.2/24, up |
| DUT3 | Ethernet12 | `show ip interface brief` | 10.3.2.2/24, up |

### Static Route Verification

| DUT | Route Prefix | Next-Hop | Verification Command | Expected Output |
|-----|--------------|----------|---------------------|-----------------|
| DUT1 | 30.30.30.0/24 | 10.1.1.2 | `show ip route 30.30.30.0/24` | `S    30.30.30.0/24           10.1.1.2` |
| DUT1 | 40.40.40.0/24 | 10.2.1.1 | `show ip route 40.40.40.0/24` | `S    40.40.40.0/24           10.2.1.1` |
| DUT2 | 30.30.30.0/24 | 10.2.1.2 | `show ip route 30.30.30.0/24` | `S    30.30.30.0/24           10.2.1.2` |
| DUT2 | 40.40.40.0/24 | 10.1.1.1 | `show ip route 40.40.40.0/24` | `S    40.40.40.0/24           10.1.1.1` |
| DUT3 | 40.40.40.0/24 | 10.2.1.1 | `show ip route 40.40.40.0/24` | `S    40.40.40.0/24           10.2.1.1` |

### Running Configuration Verification

**Command:**
```bash
show running-configuration | grep "ip route"
```

**Expected Output (DUT1):**
```
ip route 30.30.30.0/24 10.1.1.2
ip route 40.40.40.0/24 10.2.1.1
```

**Expected Output (DUT2):**
```
ip route 30.30.30.0/24 10.2.1.2
ip route 40.40.40.0/24 10.1.1.1
```

**Expected Output (DUT3):**
```
ip route 40.40.40.0/24 10.2.1.1
```

**Note:** Due to known bug SOCCI-6XX, the grep filter may show entire configuration instead of filtered output. This is a CLI display issue and does not affect route functionality.

---

## Expected Results

### Test Case Success Criteria

| Test Step | Expected Result | Pass Criteria |
|-----------|----------------|---------------|
| **Step 2-4: Interface Config** | All interfaces configured with correct IPs | No errors, interfaces up |
| **Step 5-7: Route Addition** | All routes configured successfully | No CLI errors, routes accepted |
| **Step 8: Route Verification** | Routes visible in routing tables | 'S' marker, correct next-hop |
| **Step 9: Route Deletion** | Routes removed without errors | Deletion commands succeed |
| **Step 10: Removal Verification** | Routes absent from routing tables | No 'S' marker for deleted routes |
| **Step 11: Cleanup** | Configuration cleaned up | All test configs removed |

### Sample Output: Route Verification

**DUT1 - show ip route 30.30.30.0/24:**
```
Codes: K - kernel route, C - connected, S - static, B - BGP, O - OSPF
       > - selected route, * - FIB route, q - queued, r - rejected
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -
```

**DUT2 - show ip route static:**
```
Codes: K - kernel route, C - connected, S - static, B - BGP, O - OSPF
       > - selected route, * - FIB route, q - queued, r - rejected
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
```

---

## Cleanup Procedure

The test script includes comprehensive cleanup that executes even if the test fails:

### Automatic Cleanup Steps

1. **Remove Static Routes**
   - Delete all configured static routes on all DUTs
   - Commands: `no ip route <prefix> <nexthop>`

2. **Remove IP Addresses**
   - Clear IP addresses from all configured interfaces
   - Commands: `interface <X>; no ip address`

3. **Shutdown Interfaces**
   - Shutdown interfaces to clean state
   - Commands: `interface <X>; shutdown`

### Manual Cleanup (if needed)

If automatic cleanup fails, manually execute:

```bash
# On each DUT
sonic-cli
configure terminal

# Remove routes
no ip route 30.30.30.0/24 10.1.1.2
no ip route 40.40.40.0/24 10.2.1.1
# (adjust per DUT)

# Remove IPs
interface Ethernet 0
  no ip address
  shutdown
  exit
# (repeat for all interfaces)

exit
```

---

## Execution Instructions

### Prerequisites

1. **Testbed File:** 3-DUT testbed YAML configured
   Location: `./testbeds/testbed_3vs.yaml`

2. **Network Access:** SSH access to all 3 DUTs

3. **Build Verification:**
   ```bash
   # On each DUT
   show version
   # Verify: SONiC.oc-integration.0-<version>
   ```

### Running the Test

#### Option 1: Direct Execution

```bash
cd /home/claudeuser/draksha/sonic-mgmt/spytest

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_3vs.yaml \
  tests/system/OC_Static_Route/test_oc_static_route_01_ipv4_basic_nexthop.py \
  --logs-path ./logs/oc_sr10_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

#### Option 2: With Test Markers

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_3vs.yaml \
  -m "static_route and community_pass" \
  --logs-path ./logs/oc_sr10 \
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
| `--ifname-type native` | Use native interface names (Ethernet0, etc.) |
| `-m <marker>` | Run tests with specific pytest markers |

### Expected Execution Time

| Phase | Duration |
|-------|----------|
| **Pre-configuration** | 5-10 seconds |
| **Interface Configuration** | 10-15 seconds |
| **Route Configuration** | 10-15 seconds |
| **Route Verification** | 5-10 seconds |
| **Route Removal** | 5-10 seconds |
| **Cleanup** | 5-10 seconds |
| **Total** | ~60-90 seconds |

### Log Files

After execution, check these logs in `--logs-path` directory:

| File | Content |
|------|---------|
| `dlog-D1-<device>.log` | DUT1 command/output logs |
| `dlog-D2-<device>.log` | DUT2 command/output logs |
| `dlog-D3-<device>.log` | DUT3 command/output logs |
| `module_test_oc_static_route_01_ipv4_basic_nexthop.log` | Module execution logs |
| `results.html` | HTML test report |
| `summary.txt` | Quick test summary |

### Interpreting Results

**Test PASSED:**
```
TEST RESULT: OC-SR-10 PASSED
  ✓ All interface IP addresses configured
  ✓ All static routes added successfully
  ✓ All routes verified in routing tables
  ✓ All routes removed successfully
  ✓ Route removal verified
```

**Test FAILED:**
```
TEST RESULT: OC-SR-10 FAILED
  ✗ Test failed - check logs for details
```

Check `dlog-*` files for specific failure details.

---

## Known Issues

### Issue 1: grep Filter Not Working on show running-configuration

**Bug ID:** SOCCI-6XX (to be filed)
**Severity:** Medium
**Component:** OC-CLI

**Description:**
The `show running-configuration | grep "ip route"` command shows the entire running configuration instead of filtering to only matching lines.

**Impact:**
- Cannot filter large configurations using grep
- Must manually review full output
- This is a display issue only - route functionality works correctly

**Workaround:**
Use `show ip route` or `show running-configuration` without grep and manually search for routes.

**Status:** Bug needs to be reported

### Issue 2: Loopback Interface Not Supported in Klish CLI

**Bug ID:** SOCCI-600
**Severity:** High
**Component:** OC-CLI

**Description:**
Cannot create Loopback interfaces using `interface Loopback X` command in sonic-cli.

**Impact:**
Cannot use loopback interfaces as route next-hops via CLI. This test uses physical interface IPs as next-hops to avoid this limitation.

**Workaround:**
Use physical interface IP addresses as next-hops instead of loopback IPs.

**Status:** Already reported

### Issue 3: Route Tags Not Displayed in Routing Table

**Bug ID:** To be filed
**Severity:** Medium
**Component:** Static Route / OC-CLI

**Description:**
Route tags can be configured but are not visible in `show ip route` output.

**Impact:**
Cannot verify route tags in routing table (though tags are visible in `show running-configuration`).

**Workaround:**
This test does not use route tags.

**Status:** Not tested in this scenario

---

## References

### Related Test Cases

- **test_static_route_01_ipv4_basic.py** - 2-DUT basic static route test
- **test_static_route_02_ipv4_blackhole.py** - Blackhole route testing
- **test_static_route_05_ipv6_basic.py** - IPv6 static route testing

### Manual Test Logs

- **OC-CLI-StaticRoute-Test1.txt** - Original manual validation logs
- **static_binny.txt** - Manual test command reference
- **static_hritik.txt** - Quick test commands

### Documentation

- **STATIC_ROUTE_testplan.md** - Complete static route test plan
- **STATIC_ROUTE_TEST_BREAKDOWN.md** - All 90 test cases breakdown
- **Requirements.txt** - 3-node topology requirements

### SPyTest Framework

- **Doc/intro.md** - SPyTest framework introduction
- **CLAUDE.md** - Project overview and conventions
- **spytest/framework.py** - Test orchestration

---

## Test Metadata

**PyTest Markers:**
- `@pytest.mark.static_route` - Static route test category
- `@pytest.mark.community` - Community test suite
- `@pytest.mark.community_pass` - Community passing tests

**Test IDs:**
- TC-OC-SR-10-001: Interface configuration
- TC-OC-SR-10-002: Route addition
- TC-OC-SR-10-003: Route verification
- TC-OC-SR-10-004: Route removal

**Script Location:**
```
/home/claudeuser/draksha/sonic-mgmt/spytest/tests/system/OC_Static_Route/
  └── test_oc_static_route_01_ipv4_basic_nexthop.py
```

**Configuration Format:**
- **CLI Type:** Klish (sonic-cli)
- **Interface Names:** Native (Ethernet 0, Ethernet 4, etc.)
- **Route Format:** `ip route <prefix> <nexthop>`

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-12 | Network Automation Team | Initial test case documentation |

---

**Document End**
