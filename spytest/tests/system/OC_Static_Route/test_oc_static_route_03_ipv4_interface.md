# Test Case Documentation: OC-SR-12 - IPv4 Static Route Interface-Based Routes

**Test Case ID:** OC-SR-12
**Test Script:** `test_oc_static_route_03_ipv4_interface.py`
**Category:** Basic Functionality (IPv4) - Interface-Based Routes
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

This test case validates IPv4 static routes with interface-based next-hops (no next-hop IP address specified). Interface-based routes use ARP resolution on the egress interface to determine the MAC address of the next-hop router.

**Key Features Tested:**
- IPv4 static route configuration with interface-only next-hop
- Interface-based route verification in routing tables
- ARP resolution on egress interface
- Route removal and cleanup
- OC-build Klish CLI compatibility

**Test Type:** Functional
**CLI Mode:** Klish (sonic-cli)
**Build Type:** OC-build (OpenConfig)

---

## Test Objective

**Primary Objective:**
Verify that IPv4 static routes with interface-based next-hops can be successfully configured, verified, and removed using sonic-cli (Klish) commands in OC-build.

**Specific Goals:**
1. Configure static routes using `ip route <prefix> interface <interface>` syntax
2. Verify routes display as "directly connected, <interface>" in routing table
3. Configure multiple interface-based routes on both DUTs
4. Verify ARP resolution occurs on specified interfaces
5. Remove interface-based routes cleanly
6. Verify routes are removed from routing tables

**Success Criteria:**
- ✅ Interface-based routes configured without errors
- ✅ Routes show "directly connected, Ethernet<X>" in routing table
- ✅ Multiple interface routes coexist without conflicts
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
│  Ethernet4   │◄──────────────────►│  Ethernet8   │
│  10.2.1.1/24 │    Link-2          │  10.2.1.2/24 │
│              │                    │              │
│              │                    │  Ethernet12  │
│              │                    │  10.3.1.2/24 │
└──────────────┘                    └──────────────┘

Interface-Based Routes:
  DUT1: 192.168.70.0/24 → interface Ethernet0 (ARP on Ethernet0)
        192.168.71.0/24 → interface Ethernet4 (ARP on Ethernet4)

  DUT2: 192.168.70.0/24 → interface Ethernet8 (ARP on Ethernet8)
        192.168.71.0/24 → interface Ethernet0 (ARP on Ethernet0)
        192.168.72.0/24 → interface Ethernet12 (ARP on Ethernet12)
```

### Hardware Requirements

| Component | Requirement |
|-----------|-------------|
| **DUTs** | 2 SONiC devices |
| **Build Type** | OC-build (OpenConfig integration) |
| **Platform** | SONiC-VS (Virtual Switch) or Hardware |
| **Ports per DUT** | Minimum 2 Ethernet ports (DUT1), 3 ports (DUT2) |
| **Connections** | 2 links between DUT1-DUT2 |

### IP Addressing Scheme

#### DUT1 Configuration
| Interface | IP Address | Subnet | Connected To |
|-----------|------------|--------|--------------|
| Ethernet0 | 10.1.1.1 | /24 | DUT2 Ethernet0 |
| Ethernet4 | 10.2.1.1 | /24 | DUT2 Ethernet8 |

#### DUT2 Configuration
| Interface | IP Address | Subnet | Connected To |
|-----------|------------|--------|--------------|
| Ethernet0 | 10.1.1.2 | /24 | DUT1 Ethernet0 |
| Ethernet8 | 10.2.1.2 | /24 | DUT1 Ethernet4 |
| Ethernet12 | 10.3.1.2 | /24 | (Not connected in this test) |

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

# Add interface-based routes (no next-hop IP)
ip route 192.168.70.0/24 interface Ethernet0
ip route 192.168.71.0/24 interface Ethernet4

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

# Configure Ethernet8
interface Ethernet 8
  ip address 10.2.1.2/24
  no shutdown
  exit

# Configure Ethernet12
interface Ethernet 12
  ip address 10.3.1.2/24
  no shutdown
  exit

# Add interface-based routes (no next-hop IP)
ip route 192.168.70.0/24 interface Ethernet8
ip route 192.168.71.0/24 interface Ethernet0
ip route 192.168.72.0/24 interface Ethernet12

exit
```

### Verification Commands

```bash
# Show all static routes
show ip route static

# Show specific interface-based route
show ip route 192.168.70.0/24

# Expected output for interface-based route:
# S    192.168.70.0/24         directly connected, Ethernet0      0/0         -

# Show running configuration
show running-configuration | grep "interface"
```

---

## Test Steps

### Step 1: Pre-Configuration Cleanup
**Action:** Clear any existing IP addresses and static routes on both DUTs
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
**Test Case ID:** TC-OC-SR-12-001

### Step 3: Configure IP Addresses on DUT2
**Action:** Configure Ethernet0, Ethernet8, and Ethernet12
**Commands:**
```bash
interface Ethernet 0
  ip address 10.1.1.2/24
  no shutdown
interface Ethernet 8
  ip address 10.2.1.2/24
  no shutdown
interface Ethernet 12
  ip address 10.3.1.2/24
  no shutdown
```
**Verification:** All interfaces up, IP addresses assigned
**Test Case ID:** TC-OC-SR-12-001

### Step 4: Add Interface-Based Routes on DUT1
**Action:** Configure 2 interface-based routes
**Commands:**
```bash
ip route 192.168.70.0/24 interface Ethernet0
ip route 192.168.71.0/24 interface Ethernet4
```
**Expected:** Routes accepted without errors
**Test Case ID:** TC-OC-SR-12-002

### Step 5: Add Interface-Based Routes on DUT2
**Action:** Configure 3 interface-based routes
**Commands:**
```bash
ip route 192.168.70.0/24 interface Ethernet8
ip route 192.168.71.0/24 interface Ethernet0
ip route 192.168.72.0/24 interface Ethernet12
```
**Expected:** All routes accepted without errors
**Test Case ID:** TC-OC-SR-12-002

### Step 6: Verify Interface-Based Routes in Routing Tables
**Action:** Verify routes show "directly connected, Ethernet<X>"
**Commands:**
```bash
# DUT1
show ip route 192.168.70.0/24
# Expected: S    192.168.70.0/24         directly connected, Ethernet0

show ip route 192.168.71.0/24
# Expected: S    192.168.71.0/24         directly connected, Ethernet4

# DUT2
show ip route 192.168.70.0/24
# Expected: S    192.168.70.0/24         directly connected, Ethernet8

show ip route 192.168.71.0/24
# Expected: S    192.168.71.0/24         directly connected, Ethernet0

show ip route 192.168.72.0/24
# Expected: S    192.168.72.0/24         directly connected, Ethernet12

# Show all static routes
show ip route static
```
**Verification:**
- Routes show "directly connected" marker
- Interface name appears in route entry
- Static route marker 'S' present
**Test Case ID:** TC-OC-SR-12-003

### Step 7: Remove Interface-Based Routes
**Action:** Delete all configured interface-based routes
**Commands:**
```bash
# DUT1
no ip route 192.168.70.0/24 interface Ethernet0
no ip route 192.168.71.0/24 interface Ethernet4

# DUT2
no ip route 192.168.70.0/24 interface Ethernet8
no ip route 192.168.71.0/24 interface Ethernet0
no ip route 192.168.72.0/24 interface Ethernet12
```
**Verification:** Deletion commands complete without errors
**Test Case ID:** TC-OC-SR-12-004

### Step 8: Verify Route Removal
**Action:** Confirm routes removed from routing tables
**Commands:**
```bash
show ip route 192.168.70.0/24
show ip route 192.168.71.0/24
show ip route 192.168.72.0/24
show ip route static
```
**Verification:** Routes no longer appear in routing tables
**Test Case ID:** TC-OC-SR-12-004

### Step 9: Cleanup
**Action:** Remove IP addresses and shutdown interfaces
**Command:** Automated by script's `static_route_cleanup()` function
**Expected Result:** Clean final state

---

## Verification Points

### Interface-Based Route Verification

| DUT | Route Prefix | Interface | Command | Expected Output |
|-----|--------------|-----------|---------|-----------------|
| DUT1 | 192.168.70.0/24 | Ethernet0 | `show ip route 192.168.70.0/24` | `S    192.168.70.0/24         directly connected, Ethernet0      0/0         -` |
| DUT1 | 192.168.71.0/24 | Ethernet4 | `show ip route 192.168.71.0/24` | `S    192.168.71.0/24         directly connected, Ethernet4      0/0         -` |
| DUT2 | 192.168.70.0/24 | Ethernet8 | `show ip route 192.168.70.0/24` | `S    192.168.70.0/24         directly connected, Ethernet8      0/0         -` |
| DUT2 | 192.168.71.0/24 | Ethernet0 | `show ip route 192.168.71.0/24` | `S    192.168.71.0/24         directly connected, Ethernet0      0/0         -` |
| DUT2 | 192.168.72.0/24 | Ethernet12 | `show ip route 192.168.72.0/24` | `S    192.168.72.0/24         directly connected, Ethernet12     0/0         -` |

### Running Configuration Verification

**Command:**
```bash
show running-configuration | grep "route"
```

**Expected Output (DUT1):**
```
ip route 192.168.70.0/24 interface Ethernet0
ip route 192.168.71.0/24 interface Ethernet4
```

**Expected Output (DUT2):**
```
ip route 192.168.70.0/24 interface Ethernet8
ip route 192.168.71.0/24 interface Ethernet0
ip route 192.168.72.0/24 interface Ethernet12
```

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
 S    192.168.70.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet4      0/0         -
```

### Sample Output: DUT2 - show ip route static

```
Codes: K - kernel route, C - connected, S - static, B - BGP, O - OSPF
       > - selected route, * - FIB route, q - queued, r - rejected
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
```

### Key Observations

1. **Gateway Column:** Shows "directly connected, <interface>" instead of IP address
2. **Static Route Type:** All routes show 'S' code indicating static routes
3. **Distance/Metric:** Interface routes show 0/0 like normal static routes
4. **ARP Behavior:** Next-hop MAC address resolved via ARP on egress interface
5. **No IP Required:** No next-hop IP address needed in configuration

---

## Cleanup Procedure

The test script includes comprehensive cleanup that executes even if the test fails:

### Automatic Cleanup Steps

1. **Remove Interface-Based Routes**
   - Delete all interface-based routes on both DUTs
   - Commands: `no ip route <prefix> interface <interface>`

2. **Remove IP Addresses**
   - Clear IP addresses from configured interfaces
   - Commands: `interface <X>; no ip address`

3. **Shutdown Interfaces**
   - Shutdown interfaces to clean state
   - Commands: `interface <X>; shutdown`

### Manual Cleanup (if needed)

If automatic cleanup fails, manually execute:

```bash
# On DUT1
sonic-cli
configure terminal

no ip route 192.168.70.0/24 interface Ethernet0
no ip route 192.168.71.0/24 interface Ethernet4

interface Ethernet 0
  no ip address
  shutdown
  exit

interface Ethernet 4
  no ip address
  shutdown
  exit

exit

# On DUT2
sonic-cli
configure terminal

no ip route 192.168.70.0/24 interface Ethernet8
no ip route 192.168.71.0/24 interface Ethernet0
no ip route 192.168.72.0/24 interface Ethernet12

interface Ethernet 0
  no ip address
  shutdown
  exit

interface Ethernet 8
  no ip address
  shutdown
  exit

interface Ethernet 12
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
  tests/system/Static_Route/test_oc_static_route_03_ipv4_interface.py \
  --logs-path ./logs/oc_sr12_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

#### Option 2: With Test Markers

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_2vs.yaml \
  -m "interface_route and community_pass" \
  --logs-path ./logs/oc_sr12 \
  --log-level debug
```

### Expected Execution Time

| Phase | Duration |
|-------|----------|
| **Pre-configuration** | 5-10 seconds |
| **Interface Configuration** | 5-10 seconds |
| **Interface Route Config** | 5-10 seconds |
| **Route Verification** | 5-10 seconds |
| **Route Removal** | 5-10 seconds |
| **Cleanup** | 5-10 seconds |
| **Total** | ~40-60 seconds |

---

## Known Issues

### Issue 1: Interface-Based Routes and ARP

**Severity:** Informational
**Component:** Static Route / ARP

**Description:**
Interface-based routes rely on ARP to resolve the next-hop MAC address on the egress interface. If no device responds to ARP on that subnet, packets will be dropped.

**Impact:**
- Requires connected devices on the interface subnet
- ARP cache must be populated for forwarding to work
- May see packet loss until ARP resolution completes

**Workaround:**
Ensure destination networks have active devices that respond to ARP.

### Issue 2: Point-to-Point Links

**Severity:** Low
**Component:** Static Route

**Description:**
Interface-based routes are most suitable for broadcast networks (Ethernet). On point-to-point links, using next-hop IP is more efficient.

**Best Practice:**
- Broadcast networks: Use interface-based routes
- Point-to-point links: Use next-hop IP-based routes

---

## Use Cases for Interface-Based Routes

### 1. Broadcast Multi-Access Networks
```bash
# Ethernet segment with multiple routers
ip route 172.16.0.0/16 interface Ethernet0
```

### 2. Dynamic Next-Hop Selection
When next-hop router IP may change but interface remains constant:
```bash
ip route 10.0.0.0/8 interface Ethernet4
```

### 3. Unnumbered Interfaces
When egress interface has no IP address:
```bash
ip route 192.168.0.0/16 interface Ethernet8
```

### 4. Traffic Engineering
Force traffic out specific interface regardless of next-hop:
```bash
ip route 203.0.113.0/24 interface Ethernet0
```

---

## Troubleshooting

### Problem: Route showing but traffic not forwarding

**Check ARP:**
```bash
show arp
# Verify next-hop MAC address is learned
```

**Check Interface Status:**
```bash
show interface Ethernet0
# Verify interface is up/up
```

**Solution:**
1. Ensure destination device responds to ARP
2. Verify interface is operationally up
3. Check IP addressing on connected devices

### Problem: Cannot remove interface-based route

**Error:**
```
% Error: Route not found
```

**Solution:**
```bash
# Check exact interface name in running config
show running-configuration | grep "route"

# Use exact interface name from config
no ip route 192.168.70.0/24 interface Ethernet0
# NOT: no ip route 192.168.70.0/24 interface Ethernet 0 (with space)
```

---

## Comparison: Interface Routes vs Next-Hop IP Routes

| Feature | Interface Route | Next-Hop IP Route |
|---------|----------------|-------------------|
| **Syntax** | `interface Ethernet0` | `10.1.1.2` |
| **ARP Required** | Yes, on egress interface | Yes, for next-hop IP |
| **Configuration** | Interface name only | IP address required |
| **Best Use** | Broadcast networks | Point-to-point, any network |
| **Scalability** | Limited | Better |
| **Gateway Display** | "directly connected, Ethernet0" | Next-hop IP address |

---

## References

### Related Test Cases

- **test_oc_static_route_01_ipv4_basic_nexthop.py** - Basic next-hop route testing
- **test_oc_static_route_02_ipv4_blackhole.py** - Blackhole route testing
- **test_oc_static_route_04_ipv4_tags.py** - Tagged route testing

### Manual Test Logs

- **Manual test log section:** Testcase 12: IPv4 INTERFACE-BASED ROUTES
- **DUT1 verification:** Routes showing "directly connected, Ethernet0/4"
- **DUT2 verification:** Routes showing "directly connected, Ethernet8/0/12"

### Documentation

- **STATIC_ROUTE_testplan.md** - Complete static route test plan
- **STATIC_ROUTE_TEST_BREAKDOWN.md** - All 90 test cases breakdown

---

## Test Metadata

**PyTest Markers:**
- `@pytest.mark.static_route` - Static route test category
- `@pytest.mark.interface_route` - Interface-based route tests
- `@pytest.mark.community` - Community test suite
- `@pytest.mark.community_pass` - Community passing tests

**Test IDs:**
- TC-OC-SR-12-001: Interface configuration
- TC-OC-SR-12-002: Interface route addition
- TC-OC-SR-12-003: Interface route verification
- TC-OC-SR-12-004: Route removal

**Script Location:**
```
/home/adminuser/draksha/sonic-mgmt/spytest/tests/system/Static_Route/
  └── test_oc_static_route_03_ipv4_interface.py
```

**Configuration Format:**
- **CLI Type:** Klish (sonic-cli)
- **Interface Names:** Native (Ethernet 0, Ethernet 4, etc.)
- **Route Format:** `ip route <prefix> interface <interface>`

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-12 | Network Automation Team | Initial test case documentation for OC-SR-12 interface-based routes |

---

**Document End**
