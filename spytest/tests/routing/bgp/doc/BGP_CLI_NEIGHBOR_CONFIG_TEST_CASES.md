# BGP Neighbor Configuration Commands - Comprehensive Test Cases

## Document Information
- **Document Version:** 1.0
- **Creation Date:** 2026-05-28
- **Author:** QA Team
- **Feature Area:** BGP Neighbor Configuration CLI
- **Testbed:** testbed_vs_3rr_reg.yaml
- **Test Case ID Range:** TC-BGP-CLI-NEIGHBOR-001 to TC-BGP-CLI-NEIGHBOR-150

## Testbed Reference
- YAML: `./testbeds/testbed_vs_3rr_reg.yaml`
- Topology Summary:
  ```
  # +----------------------+                   +----------------------+
  # |   D1 (Router 1)      |===================|   D2 (Router 2)      |
  # |   AS 65001/65100     |     Ethernet4     |   AS 65002/65100     |
  # +----------------------+                   +----------------------+
  #           ||                                         ||
  #           ||                                         ||
  # +----------------------+                   +----------------------+
  # |   D3 (Route          |===================|   External Peer      |
  # |   Reflector)         |     Ethernet8     |   (AS 65200)         |
  # |   AS 65100           |                   |                      |
  # +----------------------+                   +----------------------+
  ```
- Management access and validations performed with both `click` and `klish` (sonic-cli) modes

## Overview

This document provides comprehensive test cases for BGP neighbor-level configuration commands in SONiC. The test cases cover positive scenarios, negative scenarios, and edge cases for all major BGP neighbor configuration options.

### Commands Covered

1. **bfd check-control-plane-failure** - BFD control plane failure detection
2. **disable-connected-check** - Disable eBGP connected check
3. **enforce-first-as** - Enforce first AS in AS-PATH
4. **enforce-multihop** - Enforce multihop for eBGP sessions
5. **advertisement-interval** - Minimum interval between BGP advertisements
6. **capability dynamic** - Dynamic capability advertisement
7. **capability extended-nexthop** - Extended next-hop capability
8. **ebgp-multihop** - eBGP multihop TTL value
9. **local-as** - Configure local AS for neighbor
10. **shutdown message** - Graceful shutdown with message
11. **timers connect** - BGP connect timer
12. **v6only** - IPv6-only peering with IPv4 AFI/SAFI
13. All corresponding "no" variants for command removal

### Test Categories

- **Positive Tests:** Valid configurations that should succeed
- **Negative Tests:** Invalid configurations that should fail with appropriate error messages
- **Edge Tests:** Boundary conditions and corner cases
- **Persistence Tests:** Configuration save/reload verification
- **Interoperability Tests:** Multi-vendor and mixed-version scenarios

---

## Test Case Summary

| Test ID Range | Feature | Number of Tests |
|---------------|---------|-----------------|
| TC-BGP-CLI-NEIGHBOR-001 to 015 | BFD Check Control-Plane-Failure | 15 |
| TC-BGP-CLI-NEIGHBOR-016 to 030 | Disable Connected Check | 15 |
| TC-BGP-CLI-NEIGHBOR-031 to 045 | Enforce First AS | 15 |
| TC-BGP-CLI-NEIGHBOR-046 to 060 | Enforce Multihop | 15 |
| TC-BGP-CLI-NEIGHBOR-061 to 075 | Advertisement Interval | 15 |
| TC-BGP-CLI-NEIGHBOR-076 to 090 | Capability Dynamic | 15 |
| TC-BGP-CLI-NEIGHBOR-091 to 105 | Capability Extended-Nexthop | 15 |
| TC-BGP-CLI-NEIGHBOR-106 to 120 | eBGP Multihop | 15 |
| TC-BGP-CLI-NEIGHBOR-121 to 135 | Local-AS Configuration | 15 |
| TC-BGP-CLI-NEIGHBOR-136 to 150 | Shutdown with Message | 15 |
| TC-BGP-CLI-NEIGHBOR-151 to 165 | Timers Connect | 15 |
| TC-BGP-CLI-NEIGHBOR-166 to 180 | V6only Configuration | 15 |

**Total Test Cases:** 180

---

## BFD Check Control-Plane-Failure Test Cases

### TC-BGP-CLI-NEIGHBOR-001: Enable BFD Control-Plane Failure Check (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-001
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** High
**Type:** Positive

**Objective:**
Verify that BFD control-plane failure check can be enabled on a BGP neighbor successfully.

**Topology:**
2-node testbed with D1 and D2 connected via Ethernet4

**Pre-requisites:**
- BGP session established between D1 and D2
- BFD daemon running on both devices
- eBGP or iBGP peering configured

**Test Steps:**

1. Configure BGP neighbor on D1
2. Enable BFD for the neighbor
3. Enable BFD control-plane failure check
4. Verify configuration using show commands
5. Verify BFD session status

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 bfd
  neighbor 10.0.24.2 bfd check-control-plane-failure
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 10.0.24.2 remote-as 65002" \
  -c "neighbor 10.0.24.2 bfd" \
  -c "neighbor 10.0.24.2 bfd check-control-plane-failure"
```

**Verification Commands:**
```bash
# Klish mode
show running-config | grep "bfd check-control-plane-failure"
show bfd peers
show ip bgp neighbors 10.0.24.2 | grep -i bfd

# Click mode
show running-config | grep "bfd check-control-plane-failure"
show bfd peers
```

**Expected Result:**
- Configuration accepted without errors
- `show running-config` displays: `neighbor 10.0.24.2 bfd check-control-plane-failure`
- BFD session shows control-plane failure check enabled
- BGP session remains Established

**Pass/Fail Criteria:**
- PASS: Configuration accepted, BFD control-plane failure check enabled
- FAIL: Configuration rejected or BFD check not enabled

---

### TC-BGP-CLI-NEIGHBOR-002: Disable BFD Control-Plane Failure Check (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-002
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** High
**Type:** Positive

**Objective:**
Verify that BFD control-plane failure check can be disabled using "no" variant.

**Topology:**
2-node testbed with D1 and D2 connected via Ethernet4

**Pre-requisites:**
- BGP session established with BFD control-plane failure check enabled (TC-001)

**Test Steps:**

1. Verify current BFD control-plane failure check configuration
2. Disable BFD control-plane failure check using "no" command
3. Verify configuration removal
4. Verify BFD session continues without control-plane check

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  no neighbor 10.0.24.2 bfd check-control-plane-failure
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "no neighbor 10.0.24.2 bfd check-control-plane-failure"
```

**Verification Commands:**
```bash
show running-config | grep "bfd check-control-plane-failure"
show bfd peers
show ip bgp neighbors 10.0.24.2
```

**Expected Result:**
- Configuration removed without errors
- `show running-config` does NOT display: `neighbor 10.0.24.2 bfd check-control-plane-failure`
- BFD session continues (if BFD still enabled)
- BGP session remains Established
- Control-plane failure check disabled in BFD session

**Pass/Fail Criteria:**
- PASS: Configuration removed successfully, BFD check disabled
- FAIL: Configuration persists or BFD session disrupted

---

### TC-BGP-CLI-NEIGHBOR-003: BFD Control-Plane Failure Without BFD Enabled (Negative)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-003
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Medium
**Type:** Negative

**Objective:**
Verify that attempting to enable BFD control-plane failure check without BFD enabled is rejected with appropriate error.

**Topology:**
2-node testbed with D1 and D2 connected via Ethernet4

**Pre-requisites:**
- BGP session established without BFD enabled

**Test Steps:**

1. Configure BGP neighbor without BFD
2. Attempt to enable BFD control-plane failure check without BFD base configuration
3. Verify error message displayed
4. Verify configuration not applied

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 bfd check-control-plane-failure
  exit
exit
```

**Expected Result:**
- Configuration rejected with error message similar to:
  - "BFD must be enabled for neighbor before enabling check-control-plane-failure"
  - "Error: neighbor 10.0.24.2 bfd not configured"
- Configuration NOT applied in running-config
- BGP session unaffected

**Pass/Fail Criteria:**
- PASS: Appropriate error message displayed, configuration rejected
- FAIL: Configuration accepted or no error message

---

### TC-BGP-CLI-NEIGHBOR-004: BFD Control-Plane Failure on Non-Existent Neighbor (Negative)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-004
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Medium
**Type:** Negative

**Objective:**
Verify that attempting to configure BFD control-plane failure check on non-existent neighbor fails appropriately.

**Test Steps:**

1. Ensure neighbor 192.0.2.99 is NOT configured
2. Attempt to configure BFD control-plane failure check on non-existent neighbor
3. Verify error message

**Configuration (Klish Mode):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 192.0.2.99 bfd check-control-plane-failure
  exit
exit
```

**Expected Result:**
- Error message: "Neighbor 192.0.2.99 not configured" or similar
- Configuration rejected
- No impact on existing neighbors

**Pass/Fail Criteria:**
- PASS: Error message displayed, configuration rejected
- FAIL: Configuration accepted for non-existent neighbor

---

### TC-BGP-CLI-NEIGHBOR-005: BFD Control-Plane Failure - IPv6 Neighbor (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-005
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** High
**Type:** Positive

**Objective:**
Verify BFD control-plane failure check works with IPv6 BGP neighbors.

**Pre-requisites:**
- IPv6 BGP session established
- IPv6 addressing configured on interfaces
- BFD IPv6 support enabled

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 2001:db8:24::2 remote-as 65002
  neighbor 2001:db8:24::2 bfd
  neighbor 2001:db8:24::2 bfd check-control-plane-failure
  exit
exit
```

**Verification Commands:**
```bash
show running-config | grep "2001:db8:24::2"
show bfd peers ipv6
show ipv6 bgp neighbors 2001:db8:24::2
```

**Expected Result:**
- IPv6 neighbor accepts BFD control-plane failure check
- BFD session established over IPv6
- BGP session Established with BFD protection

**Pass/Fail Criteria:**
- PASS: IPv6 BFD control-plane failure check enabled successfully
- FAIL: Configuration rejected or IPv6 BFD not working

---

### TC-BGP-CLI-NEIGHBOR-006: BFD Control-Plane Failure - Peer Group (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-006
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** High
**Type:** Positive

**Objective:**
Verify BFD control-plane failure check can be configured on peer-group and inherited by members.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor EBGP-PEERS peer-group
  neighbor EBGP-PEERS remote-as 65002
  neighbor EBGP-PEERS bfd
  neighbor EBGP-PEERS bfd check-control-plane-failure
  neighbor 10.0.24.2 peer-group EBGP-PEERS
  neighbor 10.0.25.2 peer-group EBGP-PEERS
  exit
exit
```

**Verification Commands:**
```bash
show running-config | grep -A 10 "neighbor EBGP-PEERS"
show ip bgp peer-group EBGP-PEERS
show ip bgp neighbors 10.0.24.2 | grep -i bfd
show ip bgp neighbors 10.0.25.2 | grep -i bfd
```

**Expected Result:**
- Peer-group configuration includes BFD check
- All peer-group members inherit BFD control-plane failure check
- Both neighbors show BFD check enabled

**Pass/Fail Criteria:**
- PASS: Peer-group members inherit BFD control-plane failure check
- FAIL: Inheritance not working or configuration rejected

---

### TC-BGP-CLI-NEIGHBOR-007: BFD Control-Plane Failure - Configuration Persistence (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-007
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** High
**Type:** Persistence

**Objective:**
Verify BFD control-plane failure check configuration persists across config save and reload.

**Test Steps:**

1. Configure BFD control-plane failure check
2. Save configuration: `write memory` or `copy running-config startup-config`
3. Reload configuration or reboot device
4. Verify configuration persists after reload

**Configuration (Klish Mode):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 bfd check-control-plane-failure
  exit
write memory
```

**Post-Reload Verification:**
```bash
show running-config | grep "bfd check-control-plane-failure"
show bfd peers
show ip bgp summary
```

**Expected Result:**
- Configuration saved successfully
- After reload, `show running-config` displays BFD check configuration
- BGP session re-establishes with BFD protection
- BFD control-plane failure check active

**Pass/Fail Criteria:**
- PASS: Configuration persists, BGP and BFD sessions restored
- FAIL: Configuration lost after reload

---

### TC-BGP-CLI-NEIGHBOR-008: BFD Control-Plane Failure - iBGP Scenario (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-008
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Medium
**Type:** Positive

**Objective:**
Verify BFD control-plane failure check works in iBGP scenarios.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65100
  neighbor 1.1.1.2 remote-as 65100
  neighbor 1.1.1.2 update-source Loopback0
  neighbor 1.1.1.2 bfd
  neighbor 1.1.1.2 bfd check-control-plane-failure
  exit
exit
```

**Verification Commands:**
```bash
show ip bgp neighbors 1.1.1.2 | grep -i bfd
show bfd peers
show ip bgp summary
```

**Expected Result:**
- iBGP neighbor accepts BFD control-plane failure check
- BFD session established for iBGP peer
- Session state: Established

**Pass/Fail Criteria:**
- PASS: iBGP BFD control-plane failure check working
- FAIL: Configuration rejected or BFD not functional for iBGP

---

### TC-BGP-CLI-NEIGHBOR-009: BFD Control-Plane Failure - Session Flap Detection (Functional)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-009
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** High
**Type:** Functional

**Objective:**
Verify that BFD control-plane failure check detects BGP session issues faster than traditional keepalive/holdtime.

**Test Steps:**

1. Configure BGP with BFD control-plane failure check
2. Establish BGP session
3. Simulate control-plane failure (shutdown BGP process or interface)
4. Measure time to session down detection
5. Compare with non-BFD scenario

**Expected Result:**
- With BFD: Session down detected in < 1 second
- Without BFD: Session down detected based on hold-timer (default 180s)
- BFD provides faster failure detection

**Pass/Fail Criteria:**
- PASS: BFD detects failure significantly faster than holdtime
- FAIL: No improvement in failure detection time

---

### TC-BGP-CLI-NEIGHBOR-010: BFD Control-Plane Failure - Multiple Neighbors (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-010
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Medium
**Type:** Edge

**Objective:**
Verify BFD control-plane failure check works with maximum number of BGP neighbors.

**Configuration (Klish Mode):**
```bash
sonic-cli

configure terminal
router bgp 65001
  # Configure 100 neighbors with BFD check
  neighbor 10.0.1.1 remote-as 65002
  neighbor 10.0.1.1 bfd
  neighbor 10.0.1.1 bfd check-control-plane-failure
  # ... repeat for 10.0.1.2 through 10.0.1.100
  exit
exit
```

**Verification:**
```bash
show bfd peers | count
show ip bgp summary | count
```

**Expected Result:**
- All neighbors accept BFD control-plane failure check
- System remains stable with multiple BFD sessions
- CPU/memory usage within acceptable limits

**Pass/Fail Criteria:**
- PASS: All neighbors configured successfully, system stable
- FAIL: Configuration fails or system becomes unstable

---

### TC-BGP-CLI-NEIGHBOR-011: BFD Control-Plane Failure - Invalid Syntax (Negative)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-011
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Low
**Type:** Negative

**Objective:**
Verify that invalid syntax variations are rejected with appropriate errors.

**Test Attempts:**
```bash
# Invalid command variants
neighbor 10.0.24.2 bfd check-control-plane
neighbor 10.0.24.2 check-control-plane-failure
neighbor 10.0.24.2 bfd control-plane-failure
neighbor 10.0.24.2 bfd check-cp-failure
```

**Expected Result:**
- All invalid syntax variants rejected
- Clear error messages indicating correct syntax
- No partial configuration applied

**Pass/Fail Criteria:**
- PASS: All invalid syntax rejected with helpful error messages
- FAIL: Invalid syntax accepted or unclear error messages

---

### TC-BGP-CLI-NEIGHBOR-012: BFD Control-Plane Failure - Interface-Based Neighbor (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-012
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Medium
**Type:** Positive

**Objective:**
Verify BFD control-plane failure check works with interface-based (unnumbered) neighbors.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor Ethernet4 interface remote-as 65002
  neighbor Ethernet4 bfd
  neighbor Ethernet4 bfd check-control-plane-failure
  exit
exit
```

**Verification Commands:**
```bash
show running-config | grep "neighbor Ethernet4"
show bfd peers
show ip bgp neighbors Ethernet4
```

**Expected Result:**
- Interface-based neighbor accepts BFD control-plane failure check
- BFD session established using interface
- BGP session Established

**Pass/Fail Criteria:**
- PASS: Interface neighbor with BFD check works correctly
- FAIL: Configuration rejected for interface neighbor

---

### TC-BGP-CLI-NEIGHBOR-013: BFD Control-Plane Failure - BFD Profile Integration (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-013
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Medium
**Type:** Positive

**Objective:**
Verify BFD control-plane failure check works with custom BFD profiles.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
# Create BFD profile
bfd
  profile FAST-DETECT
    detect-multiplier 3
    receive-interval 300
    transmit-interval 300
    exit
  exit

router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 bfd profile FAST-DETECT
  neighbor 10.0.24.2 bfd check-control-plane-failure
  exit
exit
```

**Expected Result:**
- BFD profile and control-plane failure check work together
- BFD session uses custom profile parameters
- Control-plane failure detection enabled

**Pass/Fail Criteria:**
- PASS: BFD profile and control-plane check integrate correctly
- FAIL: Configuration conflict or feature not working

---

### TC-BGP-CLI-NEIGHBOR-014: BFD Control-Plane Failure - Configuration Order Variation (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-014
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Low
**Type:** Edge

**Objective:**
Verify BFD control-plane failure check works regardless of configuration order.

**Test Variations:**

**Variation 1: Check before BFD**
```bash
neighbor 10.0.24.2 bfd check-control-plane-failure
neighbor 10.0.24.2 bfd
```

**Variation 2: BFD before Check**
```bash
neighbor 10.0.24.2 bfd
neighbor 10.0.24.2 bfd check-control-plane-failure
```

**Expected Result:**
- Both orders should work (if system allows)
- OR Variation 1 should fail with clear error indicating BFD must be configured first
- Final configuration should be identical regardless of order (if both accepted)

**Pass/Fail Criteria:**
- PASS: Consistent behavior, clear error if order matters
- FAIL: Inconsistent behavior or unclear errors

---

### TC-BGP-CLI-NEIGHBOR-015: BFD Control-Plane Failure - Show Command Validation (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-015
**Feature:** BGP Neighbor BFD Control-Plane Failure Detection
**Priority:** Medium
**Type:** Positive

**Objective:**
Verify all show commands correctly display BFD control-plane failure check status.

**Show Commands to Verify:**
```bash
show running-config | grep bfd
show ip bgp neighbors 10.0.24.2
show ip bgp neighbors 10.0.24.2 | include BFD
show bfd peers
show bfd peers detail
show ip bgp summary
```

**Expected Result:**
- `show running-config`: Displays `neighbor 10.0.24.2 bfd check-control-plane-failure`
- `show ip bgp neighbors`: Shows BFD status with control-plane check enabled
- `show bfd peers`: Shows BFD session with control-plane failure detection
- All outputs consistent and accurate

**Pass/Fail Criteria:**
- PASS: All show commands display accurate BFD control-plane failure check status
- FAIL: Inconsistent or missing information in show commands

---

## Disable Connected Check Test Cases

### TC-BGP-CLI-NEIGHBOR-016: Enable Disable Connected Check (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-016
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** High
**Type:** Positive

**Objective:**
Verify that eBGP connected check can be disabled for non-directly connected neighbors.

**Topology:**
D1 and D2 connected via intermediate router (multi-hop scenario)

**Pre-requisites:**
- eBGP session configured between D1 and D2
- Neighbors NOT directly connected (multi-hop required)
- Static routes or IGP providing reachability

**Test Steps:**

1. Configure eBGP neighbor without disable-connected-check (should fail to establish)
2. Enable disable-connected-check
3. Verify BGP session establishes
4. Verify running configuration

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
interface Ethernet4
  ip address 10.0.24.1/24
  no shutdown
  exit

# Static route to remote peer's loopback
ip route 2.2.2.2/32 10.0.24.254

router bgp 65001
  neighbor 2.2.2.2 remote-as 65002
  neighbor 2.2.2.2 ebgp-multihop 2
  neighbor 2.2.2.2 disable-connected-check
  neighbor 2.2.2.2 update-source Loopback0
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 2.2.2.2 remote-as 65002" \
  -c "neighbor 2.2.2.2 ebgp-multihop 2" \
  -c "neighbor 2.2.2.2 disable-connected-check" \
  -c "neighbor 2.2.2.2 update-source Loopback0"
```

**Verification Commands:**
```bash
show running-config | grep "disable-connected-check"
show ip bgp neighbors 2.2.2.2 | grep -i connected
show ip bgp summary
```

**Expected Result:**
- Configuration accepted without errors
- `show running-config` displays: `neighbor 2.2.2.2 disable-connected-check`
- BGP session transitions to Established state
- eBGP session works over non-directly connected link

**Pass/Fail Criteria:**
- PASS: eBGP session establishes with disable-connected-check
- FAIL: Configuration rejected or session fails to establish

---

### TC-BGP-CLI-NEIGHBOR-017: Remove Disable Connected Check (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-017
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** High
**Type:** Positive

**Objective:**
Verify that disable-connected-check can be removed using "no" command.

**Pre-requisites:**
- eBGP neighbor with disable-connected-check configured (TC-016)

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  no neighbor 2.2.2.2 disable-connected-check
  exit
exit
```

**Verification Commands:**
```bash
show running-config | grep "disable-connected-check"
show ip bgp neighbors 2.2.2.2
```

**Expected Result:**
- Configuration removed successfully
- `show running-config` does NOT show disable-connected-check
- BGP session may reset (expected behavior for multi-hop without disable-connected-check)
- Connected check re-enabled

**Pass/Fail Criteria:**
- PASS: Configuration removed, connected check re-enabled
- FAIL: Configuration persists or system error

---

### TC-BGP-CLI-NEIGHBOR-018: Disable Connected Check on iBGP (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-018
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** Low
**Type:** Edge

**Objective:**
Verify behavior when disable-connected-check is configured on iBGP neighbor.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65100
  neighbor 1.1.1.2 remote-as 65100
  neighbor 1.1.1.2 disable-connected-check
  exit
exit
```

**Expected Result:**
- Configuration MAY be accepted (iBGP doesn't have connected check by default)
- OR configuration ignored with warning
- iBGP session unaffected (disable-connected-check has no effect on iBGP)

**Pass/Fail Criteria:**
- PASS: Consistent behavior, appropriate handling of iBGP scenario
- FAIL: System error or unexpected behavior

---

### TC-BGP-CLI-NEIGHBOR-019: Disable Connected Check Without eBGP Multihop (Negative)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-019
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** Medium
**Type:** Negative

**Objective:**
Verify behavior when disable-connected-check configured without ebgp-multihop for non-connected peers.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 2.2.2.2 remote-as 65002
  neighbor 2.2.2.2 disable-connected-check
  # Note: NO ebgp-multihop configured
  exit
exit
```

**Expected Result:**
- Configuration accepted (both are independent settings)
- BGP session may fail to establish if TTL=1 and peer not directly connected
- Warning message may appear about potential connectivity issues

**Pass/Fail Criteria:**
- PASS: System behavior documented and consistent
- FAIL: System crash or undefined behavior

---

### TC-BGP-CLI-NEIGHBOR-020: Disable Connected Check - Direct Connection (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-020
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** Medium
**Type:** Edge

**Objective:**
Verify disable-connected-check on directly connected eBGP peers (should work but unnecessary).

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 disable-connected-check
  exit
exit
```

**Expected Result:**
- Configuration accepted
- BGP session establishes (neighbor is directly connected)
- disable-connected-check has no practical effect but doesn't harm

**Pass/Fail Criteria:**
- PASS: Configuration accepted, session establishes
- FAIL: Configuration causes session issues

---

### TC-BGP-CLI-NEIGHBOR-021: Disable Connected Check - Peer Group (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-021
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** High
**Type:** Positive

**Objective:**
Verify disable-connected-check can be configured on peer-group.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor EBGP-MULTIHOP peer-group
  neighbor EBGP-MULTIHOP remote-as 65002
  neighbor EBGP-MULTIHOP ebgp-multihop 3
  neighbor EBGP-MULTIHOP disable-connected-check
  neighbor 2.2.2.2 peer-group EBGP-MULTIHOP
  neighbor 2.2.2.3 peer-group EBGP-MULTIHOP
  exit
exit
```

**Expected Result:**
- Peer-group accepts disable-connected-check
- All members inherit the setting
- BGP sessions establish for all members

**Pass/Fail Criteria:**
- PASS: Peer-group configuration works, members inherit setting
- FAIL: Configuration rejected or inheritance fails

---

### TC-BGP-CLI-NEIGHBOR-022: Disable Connected Check - IPv6 Neighbor (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-022
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** High
**Type:** Positive

**Objective:**
Verify disable-connected-check works with IPv6 eBGP neighbors.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 2001:db8:2::2 remote-as 65002
  neighbor 2001:db8:2::2 ebgp-multihop 2
  neighbor 2001:db8:2::2 disable-connected-check
  exit
exit
```

**Expected Result:**
- IPv6 neighbor accepts disable-connected-check
- BGP session establishes over IPv6
- Connected check disabled for IPv6 peer

**Pass/Fail Criteria:**
- PASS: IPv6 eBGP with disable-connected-check works
- FAIL: Configuration rejected for IPv6

---

### TC-BGP-CLI-NEIGHBOR-023: Disable Connected Check - Configuration Persistence (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-023
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** High
**Type:** Persistence

**Objective:**
Verify disable-connected-check configuration persists across reloads.

**Test Steps:**

1. Configure disable-connected-check
2. Save configuration
3. Reload device or configuration
4. Verify persistence

**Configuration:**
```bash
sonic-cli
configure terminal
router bgp 65001
  neighbor 2.2.2.2 disable-connected-check
  exit
write memory
```

**Post-Reload Verification:**
```bash
show running-config | grep "disable-connected-check"
show ip bgp neighbors 2.2.2.2
```

**Expected Result:**
- Configuration persists after reload
- BGP session re-establishes with disable-connected-check

**Pass/Fail Criteria:**
- PASS: Configuration persists, session restored
- FAIL: Configuration lost after reload

---

### TC-BGP-CLI-NEIGHBOR-024: Disable Connected Check - Show Command Verification (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-024
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** Medium
**Type:** Positive

**Objective:**
Verify show commands correctly display disable-connected-check status.

**Show Commands:**
```bash
show running-config | grep disable-connected-check
show ip bgp neighbors 2.2.2.2
show ip bgp neighbors 2.2.2.2 | include "disable-connected-check"
show ip bgp peer-group EBGP-MULTIHOP
```

**Expected Result:**
- All show commands consistently display disable-connected-check status
- Neighbor details show connected check disabled
- Running config shows the command

**Pass/Fail Criteria:**
- PASS: All show commands accurate and consistent
- FAIL: Inconsistent or missing information

---

### TC-BGP-CLI-NEIGHBOR-025: Disable Connected Check - Non-Existent Neighbor (Negative)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-025
**Feature:** BGP Neighbor Disable Connected Check
**Priority:** Low
**Type:** Negative

**Objective:**
Verify error when configuring disable-connected-check on non-existent neighbor.

**Configuration:**
```bash
sonic-cli
configure terminal
router bgp 65001
  neighbor 192.0.2.99 disable-connected-check
  exit
exit
```

**Expected Result:**
- Error message: "Neighbor not configured" or similar
- Configuration rejected

**Pass/Fail Criteria:**
- PASS: Appropriate error message, configuration rejected
- FAIL: Configuration accepted for non-existent neighbor

---

### TC-BGP-CLI-NEIGHBOR-026 to 030: Additional Disable Connected Check Tests

**TC-BGP-CLI-NEIGHBOR-026:** Invalid Syntax Variations (Negative)
**TC-BGP-CLI-NEIGHBOR-027:** Disable Connected Check with Dynamic Neighbors (Edge)
**TC-BGP-CLI-NEIGHBOR-028:** Multiple Neighbors Disable Connected Check (Scale)
**TC-BGP-CLI-NEIGHBOR-029:** Disable Connected Check Order Variation (Edge)
**TC-BGP-CLI-NEIGHBOR-030:** Disable Connected Check - Session Impact Testing (Functional)

*(Detailed test cases follow same pattern as above)*

---

## Enforce First AS Test Cases

### TC-BGP-CLI-NEIGHBOR-031: Enable Enforce First AS (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-031
**Feature:** BGP Neighbor Enforce First AS
**Priority:** High
**Type:** Positive

**Objective:**
Verify that enforce-first-as can be enabled to validate first AS in AS-PATH matches remote-as.

**Topology:**
2-node eBGP testbed

**Pre-requisites:**
- eBGP session between D1 (AS 65001) and D2 (AS 65002)

**Test Steps:**

1. Configure eBGP neighbor
2. Enable enforce-first-as
3. Verify configuration
4. Test with correct AS-PATH (first AS = remote-as)
5. Test with incorrect AS-PATH (first AS ≠ remote-as)

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 enforce-first-as
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 10.0.24.2 remote-as 65002" \
  -c "neighbor 10.0.24.2 enforce-first-as"
```

**Verification Commands:**
```bash
show running-config | grep "enforce-first-as"
show ip bgp neighbors 10.0.24.2 | grep -i "enforce"
show ip bgp summary
```

**Expected Result:**
- Configuration accepted
- `show running-config` displays: `neighbor 10.0.24.2 enforce-first-as`
- BGP accepts routes with correct first AS (65002)
- BGP rejects routes where first AS ≠ 65002

**Pass/Fail Criteria:**
- PASS: enforce-first-as enabled, AS validation working
- FAIL: Configuration rejected or validation not working

---

### TC-BGP-CLI-NEIGHBOR-032: Disable Enforce First AS (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-032
**Feature:** BGP Neighbor Enforce First AS
**Priority:** High
**Type:** Positive

**Objective:**
Verify enforce-first-as can be disabled using "no" command.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  no neighbor 10.0.24.2 enforce-first-as
  exit
exit
```

**Expected Result:**
- Configuration removed
- First AS validation disabled
- Routes accepted regardless of first AS

**Pass/Fail Criteria:**
- PASS: enforce-first-as disabled successfully
- FAIL: Configuration persists

---

### TC-BGP-CLI-NEIGHBOR-033: Enforce First AS - AS-PATH Validation (Functional)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-033
**Feature:** BGP Neighbor Enforce First AS
**Priority:** High
**Type:** Functional

**Objective:**
Verify that routes with incorrect first AS are rejected when enforce-first-as is enabled.

**Test Setup:**
- D1 (AS 65001) peers with D2 (AS 65002)
- D2 configured to send routes with manipulated AS-PATH

**Test Scenario 1: Correct AS-PATH**
```
Route: 192.0.2.0/24
AS-PATH: 65002 65003
First AS: 65002 (matches remote-as)
Expected: ACCEPTED
```

**Test Scenario 2: Incorrect AS-PATH**
```
Route: 198.51.100.0/24
AS-PATH: 65003 65002
First AS: 65003 (does NOT match remote-as 65002)
Expected: REJECTED
```

**Verification:**
```bash
show ip bgp neighbors 10.0.24.2 received-routes
show ip bgp
```

**Expected Result:**
- Scenario 1: Route accepted and installed
- Scenario 2: Route rejected, not in BGP table
- Log message about AS-PATH validation failure

**Pass/Fail Criteria:**
- PASS: Correct AS-PATH accepted, incorrect rejected
- FAIL: Incorrect AS-PATH accepted

---

### TC-BGP-CLI-NEIGHBOR-034: Enforce First AS on iBGP (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-034
**Feature:** BGP Neighbor Enforce First AS
**Priority:** Low
**Type:** Edge

**Objective:**
Verify behavior when enforce-first-as configured on iBGP session.

**Configuration (Klish Mode):**
```bash
sonic-cli

configure terminal
router bgp 65100
  neighbor 1.1.1.2 remote-as 65100
  neighbor 1.1.1.2 enforce-first-as
  exit
exit
```

**Expected Result:**
- Configuration may be accepted (but has no effect on iBGP)
- OR configuration rejected with error: "enforce-first-as only applicable to eBGP"
- iBGP session unaffected

**Pass/Fail Criteria:**
- PASS: Appropriate handling of iBGP case
- FAIL: System error or unexpected behavior

---

### TC-BGP-CLI-NEIGHBOR-035: Enforce First AS - Peer Group (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-035
**Feature:** BGP Neighbor Enforce First AS
**Priority:** High
**Type:** Positive

**Objective:**
Verify enforce-first-as can be configured on peer-group and inherited.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor EBGP-SECURE peer-group
  neighbor EBGP-SECURE remote-as 65002
  neighbor EBGP-SECURE enforce-first-as
  neighbor 10.0.24.2 peer-group EBGP-SECURE
  neighbor 10.0.25.2 peer-group EBGP-SECURE
  exit
exit
```

**Expected Result:**
- Peer-group accepts enforce-first-as
- All members inherit the setting
- AS validation active for all members

**Pass/Fail Criteria:**
- PASS: Peer-group configuration works correctly
- FAIL: Inheritance fails

---

### TC-BGP-CLI-NEIGHBOR-036 to 045: Additional Enforce First AS Tests

**TC-BGP-CLI-NEIGHBOR-036:** Enforce First AS - IPv6 Neighbor (Positive)
**TC-BGP-CLI-NEIGHBOR-037:** Enforce First AS - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-038:** Enforce First AS - Non-Existent Neighbor (Negative)
**TC-BGP-CLI-NEIGHBOR-039:** Enforce First AS - Invalid Syntax (Negative)
**TC-BGP-CLI-NEIGHBOR-040:** Enforce First AS - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-041:** Enforce First AS - Confederation Scenario (Edge)
**TC-BGP-CLI-NEIGHBOR-042:** Enforce First AS - AS-SET in Path (Edge)
**TC-BGP-CLI-NEIGHBOR-043:** Enforce First AS - Route Reflection Interaction (Edge)
**TC-BGP-CLI-NEIGHBOR-044:** Enforce First AS - Multiple eBGP Peers (Scale)
**TC-BGP-CLI-NEIGHBOR-045:** Enforce First AS - Session Reset Behavior (Functional)

---

## Enforce Multihop Test Cases

### TC-BGP-CLI-NEIGHBOR-046: Enable Enforce Multihop (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-046
**Feature:** BGP Neighbor Enforce Multihop
**Priority:** High
**Type:** Positive

**Objective:**
Verify that enforce-multihop can be enabled for eBGP sessions.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 ebgp-multihop 2
  neighbor 10.0.24.2 enforce-multihop
  exit
exit
```

**Verification Commands:**
```bash
show running-config | grep "enforce-multihop"
show ip bgp neighbors 10.0.24.2 | grep -i multihop
```

**Expected Result:**
- Configuration accepted
- enforce-multihop enabled for neighbor
- BGP session behavior enforces multihop check

**Pass/Fail Criteria:**
- PASS: enforce-multihop configured successfully
- FAIL: Configuration rejected

---

### TC-BGP-CLI-NEIGHBOR-047 to 060: Additional Enforce Multihop Tests

*(Following same comprehensive pattern for enforce-multihop command including positive, negative, edge, persistence, peer-group, IPv6, show commands, etc.)*

---

## Advertisement Interval Test Cases

### TC-BGP-CLI-NEIGHBOR-061: Configure Advertisement Interval (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-061
**Feature:** BGP Neighbor Advertisement Interval
**Priority:** High
**Type:** Positive

**Objective:**
Verify that advertisement-interval can be configured to control minimum time between BGP updates.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 advertisement-interval 10
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 10.0.24.2 remote-as 65002" \
  -c "neighbor 10.0.24.2 advertisement-interval 10"
```

**Verification Commands:**
```bash
show running-config | grep "advertisement-interval"
show ip bgp neighbors 10.0.24.2 | grep -i advertisement
show ip bgp summary
```

**Expected Result:**
- Configuration accepted
- `show running-config` displays: `neighbor 10.0.24.2 advertisement-interval 10`
- Advertisement interval set to 10 seconds
- Neighbor details show advertisement interval value

**Pass/Fail Criteria:**
- PASS: advertisement-interval configured successfully
- FAIL: Configuration rejected or incorrect value

---

### TC-BGP-CLI-NEIGHBOR-062: Advertisement Interval - Boundary Values (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-062
**Feature:** BGP Neighbor Advertisement Interval
**Priority:** High
**Type:** Edge

**Objective:**
Verify advertisement-interval accepts valid range and rejects invalid values.

**Test Cases:**

**Minimum Valid Value (0 seconds):**
```bash
neighbor 10.0.24.2 advertisement-interval 0
Expected: ACCEPTED
```

**Maximum Valid Value (600 seconds):**
```bash
neighbor 10.0.24.2 advertisement-interval 600
Expected: ACCEPTED
```

**Below Minimum (-1):**
```bash
neighbor 10.0.24.2 advertisement-interval -1
Expected: REJECTED with error
```

**Above Maximum (601):**
```bash
neighbor 10.0.24.2 advertisement-interval 601
Expected: REJECTED with error
```

**Non-Numeric Value:**
```bash
neighbor 10.0.24.2 advertisement-interval abc
Expected: REJECTED with error
```

**Expected Result:**
- Valid range: 0-600 seconds accepted
- Out-of-range values rejected with clear error messages
- Non-numeric values rejected

**Pass/Fail Criteria:**
- PASS: All valid values accepted, invalid values rejected with errors
- FAIL: Invalid values accepted or valid values rejected

---

### TC-BGP-CLI-NEIGHBOR-063: Advertisement Interval - Default Value (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-063
**Feature:** BGP Neighbor Advertisement Interval
**Priority:** Medium
**Type:** Positive

**Objective:**
Verify default advertisement-interval values for eBGP and iBGP.

**Test Scenario:**

**eBGP Neighbor (default should be 30 seconds):**
```bash
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  # No advertisement-interval configured
```

**iBGP Neighbor (default should be 5 seconds):**
```bash
router bgp 65001
  neighbor 1.1.1.2 remote-as 65001
  # No advertisement-interval configured
```

**Verification:**
```bash
show ip bgp neighbors 10.0.24.2 | grep -i "minimum.*advertisement"
show ip bgp neighbors 1.1.1.2 | grep -i "minimum.*advertisement"
```

**Expected Result:**
- eBGP: Default advertisement interval = 30 seconds
- iBGP: Default advertisement interval = 5 seconds
- Values shown in neighbor details

**Pass/Fail Criteria:**
- PASS: Default values match expected (eBGP=30s, iBGP=5s)
- FAIL: Incorrect default values

---

### TC-BGP-CLI-NEIGHBOR-064: Advertisement Interval - Remove Configuration (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-064
**Feature:** BGP Neighbor Advertisement Interval
**Priority:** High
**Type:** Positive

**Objective:**
Verify advertisement-interval can be reset to default using "no" command.

**Configuration:**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 advertisement-interval 10
  exit
exit

# Verify custom value
show ip bgp neighbors 10.0.24.2 | grep advertisement

# Remove custom value
configure terminal
router bgp 65001
  no neighbor 10.0.24.2 advertisement-interval
  exit
exit

# Verify default restored
show ip bgp neighbors 10.0.24.2 | grep advertisement
```

**Expected Result:**
- Custom value removed
- Default value restored (30s for eBGP, 5s for iBGP)
- Running config does not show advertisement-interval line

**Pass/Fail Criteria:**
- PASS: Default value restored after "no" command
- FAIL: Custom value persists or error occurs

---

### TC-BGP-CLI-NEIGHBOR-065: Advertisement Interval - Functional Validation (Functional)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-065
**Feature:** BGP Neighbor Advertisement Interval
**Priority:** High
**Type:** Functional

**Objective:**
Verify that advertisement-interval actually controls the rate of BGP updates.

**Test Setup:**
1. Configure advertisement-interval to 60 seconds
2. Generate multiple route changes rapidly
3. Monitor BGP update messages sent to peer
4. Verify updates are throttled according to configured interval

**Configuration:**
```bash
router bgp 65001
  neighbor 10.0.24.2 advertisement-interval 60
```

**Test Procedure:**
1. Clear BGP statistics: `clear ip bgp * statistics`
2. Advertise 10 new routes in quick succession (within 5 seconds)
3. Monitor update messages: `show ip bgp neighbors 10.0.24.2 | include "Update messages sent"`
4. Wait 65 seconds
5. Check update messages again

**Expected Result:**
- Initial burst of routes triggers 1 update message
- Additional update messages sent at ~60 second intervals
- All 10 routes eventually advertised, but throttled

**Pass/Fail Criteria:**
- PASS: Advertisement throttling works as configured
- FAIL: All updates sent immediately, ignoring interval

---

### TC-BGP-CLI-NEIGHBOR-066 to 075: Additional Advertisement Interval Tests

**TC-BGP-CLI-NEIGHBOR-066:** Advertisement Interval - Peer Group (Positive)
**TC-BGP-CLI-NEIGHBOR-067:** Advertisement Interval - IPv6 Neighbor (Positive)
**TC-BGP-CLI-NEIGHBOR-068:** Advertisement Interval - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-069:** Advertisement Interval - iBGP vs eBGP (Edge)
**TC-BGP-CLI-NEIGHBOR-070:** Advertisement Interval - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-071:** Advertisement Interval - Zero Value (Edge)
**TC-BGP-CLI-NEIGHBOR-072:** Advertisement Interval - Session Reset (Functional)
**TC-BGP-CLI-NEIGHBOR-073:** Advertisement Interval - Multiple Neighbors (Scale)
**TC-BGP-CLI-NEIGHBOR-074:** Advertisement Interval - Invalid Syntax (Negative)
**TC-BGP-CLI-NEIGHBOR-075:** Advertisement Interval - Dynamic Change (Functional)

---

## Capability Dynamic Test Cases

### TC-BGP-CLI-NEIGHBOR-076: Enable Capability Dynamic (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-076
**Feature:** BGP Neighbor Capability Dynamic
**Priority:** High
**Type:** Positive

**Objective:**
Verify that dynamic capability advertisement can be enabled for BGP neighbors.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 capability dynamic
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 10.0.24.2 remote-as 65002" \
  -c "neighbor 10.0.24.2 capability dynamic"
```

**Verification Commands:**
```bash
show running-config | grep "capability dynamic"
show ip bgp neighbors 10.0.24.2 | grep -i "dynamic capability"
show ip bgp neighbors 10.0.24.2 capabilities
```

**Expected Result:**
- Configuration accepted
- `show running-config` displays: `neighbor 10.0.24.2 capability dynamic`
- BGP neighbor capabilities show dynamic capability advertised/received
- Capability code 67 (Dynamic Capability) present

**Pass/Fail Criteria:**
- PASS: Dynamic capability enabled and advertised
- FAIL: Configuration rejected or capability not advertised

---

### TC-BGP-CLI-NEIGHBOR-077: Disable Capability Dynamic (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-077
**Feature:** BGP Neighbor Capability Dynamic
**Priority:** High
**Type:** Positive

**Objective:**
Verify that dynamic capability can be disabled using "no" command.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  no neighbor 10.0.24.2 capability dynamic
  exit
exit
```

**Expected Result:**
- Configuration removed
- Dynamic capability not advertised in subsequent session
- May require session reset to take effect

**Pass/Fail Criteria:**
- PASS: Dynamic capability removed, not advertised
- FAIL: Configuration persists

---

### TC-BGP-CLI-NEIGHBOR-078: Capability Dynamic - Negotiation Test (Functional)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-078
**Feature:** BGP Neighbor Capability Dynamic
**Priority:** High
**Type:** Functional

**Objective:**
Verify that dynamic capability is properly negotiated between peers.

**Test Scenarios:**

**Scenario 1: Both Peers Support Dynamic Capability**
- D1: `capability dynamic` configured
- D2: `capability dynamic` configured
- Expected: Dynamic capability negotiated, both sides advertise and receive

**Scenario 2: Only One Peer Supports Dynamic Capability**
- D1: `capability dynamic` configured
- D2: No `capability dynamic`
- Expected: Dynamic capability advertised by D1 but not received from D2

**Scenario 3: Neither Peer Supports Dynamic Capability**
- D1: No `capability dynamic`
- D2: No `capability dynamic`
- Expected: Dynamic capability not used

**Verification:**
```bash
show ip bgp neighbors 10.0.24.2 capabilities | grep -i dynamic
show ip bgp neighbors 10.0.24.2 | include "Neighbor capabilities"
```

**Expected Result:**
- Proper capability negotiation in all scenarios
- Show commands reflect negotiation result
- Session remains stable

**Pass/Fail Criteria:**
- PASS: All scenarios behave correctly
- FAIL: Negotiation fails or session disrupted

---

### TC-BGP-CLI-NEIGHBOR-079 to 090: Additional Capability Dynamic Tests

**TC-BGP-CLI-NEIGHBOR-079:** Capability Dynamic - Session Reset Behavior (Functional)
**TC-BGP-CLI-NEIGHBOR-080:** Capability Dynamic - Peer Group (Positive)
**TC-BGP-CLI-NEIGHBOR-081:** Capability Dynamic - IPv6 Neighbor (Positive)
**TC-BGP-CLI-NEIGHBOR-082:** Capability Dynamic - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-083:** Capability Dynamic - iBGP and eBGP (Positive)
**TC-BGP-CLI-NEIGHBOR-084:** Capability Dynamic - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-085:** Capability Dynamic - Non-Existent Neighbor (Negative)
**TC-BGP-CLI-NEIGHBOR-086:** Capability Dynamic - Invalid Syntax (Negative)
**TC-BGP-CLI-NEIGHBOR-087:** Capability Dynamic - Multiple Neighbors (Scale)
**TC-BGP-CLI-NEIGHBOR-088:** Capability Dynamic - Runtime Configuration Change (Functional)
**TC-BGP-CLI-NEIGHBOR-089:** Capability Dynamic - Interaction with Other Capabilities (Edge)
**TC-BGP-CLI-NEIGHBOR-090:** Capability Dynamic - Soft Reconfiguration Impact (Functional)

---

## Capability Extended-Nexthop Test Cases

### TC-BGP-CLI-NEIGHBOR-091: Enable Capability Extended-Nexthop (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-091
**Feature:** BGP Neighbor Capability Extended-Nexthop
**Priority:** High
**Type:** Positive

**Objective:**
Verify that extended next-hop capability can be enabled for BGP neighbors.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 capability extended-nexthop
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 10.0.24.2 remote-as 65002" \
  -c "neighbor 10.0.24.2 capability extended-nexthop"
```

**Verification Commands:**
```bash
show running-config | grep "capability extended-nexthop"
show ip bgp neighbors 10.0.24.2 | grep -i "extended.*nexthop"
show ip bgp neighbors 10.0.24.2 capabilities
```

**Expected Result:**
- Configuration accepted
- `show running-config` displays: `neighbor 10.0.24.2 capability extended-nexthop`
- BGP capabilities show extended next-hop capability (capability code 5)
- Allows IPv6 next-hop for IPv4 NLRI

**Pass/Fail Criteria:**
- PASS: Extended next-hop capability enabled and advertised
- FAIL: Configuration rejected or capability not working

---

### TC-BGP-CLI-NEIGHBOR-092: Capability Extended-Nexthop - IPv6 Nexthop for IPv4 Routes (Functional)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-092
**Feature:** BGP Neighbor Capability Extended-Nexthop
**Priority:** High
**Type:** Functional

**Objective:**
Verify that IPv6 next-hop can be used for IPv4 routes when extended-nexthop is enabled.

**Test Setup:**
- D1 and D2 connected with both IPv4 and IPv6 addresses
- BGP session over IPv6 transport
- IPv4 routes advertised with IPv6 next-hop

**Configuration (D1):**
```bash
sonic-cli

configure terminal
interface Ethernet4
  ip address 10.0.24.1/24
  ipv6 address 2001:db8:24::1/64
  no shutdown
  exit

router bgp 65001
  neighbor 2001:db8:24::2 remote-as 65002
  neighbor 2001:db8:24::2 capability extended-nexthop
  address-family ipv4 unicast
    neighbor 2001:db8:24::2 activate
    network 192.0.2.0/24
    exit-address-family
  exit
exit
```

**Verification:**
```bash
show ip bgp 192.0.2.0/24
show ip bgp neighbors 2001:db8:24::2 received-routes
```

**Expected Result:**
- IPv4 routes received with IPv6 next-hop (2001:db8:24::2)
- Routes installed in BGP table
- Extended next-hop capability negotiated successfully

**Pass/Fail Criteria:**
- PASS: IPv4 routes with IPv6 next-hop accepted and installed
- FAIL: Routes rejected or capability not negotiated

---

### TC-BGP-CLI-NEIGHBOR-093 to 105: Additional Capability Extended-Nexthop Tests

**TC-BGP-CLI-NEIGHBOR-093:** Capability Extended-Nexthop - Disable (Positive)
**TC-BGP-CLI-NEIGHBOR-094:** Capability Extended-Nexthop - Peer Group (Positive)
**TC-BGP-CLI-NEIGHBOR-095:** Capability Extended-Nexthop - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-096:** Capability Extended-Nexthop - eBGP and iBGP (Positive)
**TC-BGP-CLI-NEIGHBOR-097:** Capability Extended-Nexthop - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-098:** Capability Extended-Nexthop - Without Capability (Negative)
**TC-BGP-CLI-NEIGHBOR-099:** Capability Extended-Nexthop - Negotiation Mismatch (Edge)
**TC-BGP-CLI-NEIGHBOR-100:** Capability Extended-Nexthop - IPv6-Only Peering (Functional)
**TC-BGP-CLI-NEIGHBOR-101:** Capability Extended-Nexthop - Invalid Syntax (Negative)
**TC-BGP-CLI-NEIGHBOR-102:** Capability Extended-Nexthop - Multiple Neighbors (Scale)
**TC-BGP-CLI-NEIGHBOR-103:** Capability Extended-Nexthop - Address Family Specific (Edge)
**TC-BGP-CLI-NEIGHBOR-104:** Capability Extended-Nexthop - Session Reset (Functional)
**TC-BGP-CLI-NEIGHBOR-105:** Capability Extended-Nexthop - RFC 5549 Compliance (Functional)

---

## eBGP Multihop Test Cases

### TC-BGP-CLI-NEIGHBOR-106: Configure eBGP Multihop with TTL (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-106
**Feature:** BGP Neighbor eBGP Multihop
**Priority:** High
**Type:** Positive

**Objective:**
Verify that eBGP multihop can be configured with specific TTL value.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 2.2.2.2 remote-as 65002
  neighbor 2.2.2.2 ebgp-multihop 3
  neighbor 2.2.2.2 update-source Loopback0
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 2.2.2.2 remote-as 65002" \
  -c "neighbor 2.2.2.2 ebgp-multihop 3" \
  -c "neighbor 2.2.2.2 update-source Loopback0"
```

**Verification Commands:**
```bash
show running-config | grep "ebgp-multihop"
show ip bgp neighbors 2.2.2.2 | grep -i "external.*hops"
show ip bgp summary
```

**Expected Result:**
- Configuration accepted
- `show running-config` displays: `neighbor 2.2.2.2 ebgp-multihop 3`
- BGP session establishes with TTL=3
- Multihop eBGP session functional

**Pass/Fail Criteria:**
- PASS: eBGP multihop configured, session establishes
- FAIL: Configuration rejected or session fails

---

### TC-BGP-CLI-NEIGHBOR-107: eBGP Multihop - TTL Boundary Values (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-107
**Feature:** BGP Neighbor eBGP Multihop
**Priority:** High
**Type:** Edge

**Objective:**
Verify eBGP multihop accepts valid TTL range and rejects invalid values.

**Test Cases:**

**Minimum Valid TTL (1):**
```bash
neighbor 2.2.2.2 ebgp-multihop 1
Expected: ACCEPTED (but functionally same as no multihop)
```

**Common TTL (2):**
```bash
neighbor 2.2.2.2 ebgp-multihop 2
Expected: ACCEPTED
```

**Common TTL (255):**
```bash
neighbor 2.2.2.2 ebgp-multihop 255
Expected: ACCEPTED (maximum TTL)
```

**Invalid: Zero TTL:**
```bash
neighbor 2.2.2.2 ebgp-multihop 0
Expected: REJECTED
```

**Invalid: TTL > 255:**
```bash
neighbor 2.2.2.2 ebgp-multihop 256
Expected: REJECTED
```

**Invalid: Negative TTL:**
```bash
neighbor 2.2.2.2 ebgp-multihop -1
Expected: REJECTED
```

**Expected Result:**
- Valid range: 1-255 accepted
- Out-of-range values rejected with error messages
- Non-numeric values rejected

**Pass/Fail Criteria:**
- PASS: All valid values accepted, invalid rejected with errors
- FAIL: Invalid values accepted or valid values rejected

---

### TC-BGP-CLI-NEIGHBOR-108: eBGP Multihop - Default Value (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-108
**Feature:** BGP Neighbor eBGP Multihop
**Priority:** Medium
**Type:** Positive

**Objective:**
Verify eBGP multihop without TTL argument uses default value.

**Configuration:**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 2.2.2.2 remote-as 65002
  neighbor 2.2.2.2 ebgp-multihop
  # No TTL value specified
  exit
exit
```

**Verification:**
```bash
show ip bgp neighbors 2.2.2.2 | grep -i "external.*hop"
```

**Expected Result:**
- Configuration accepted
- Default TTL = 255 (or implementation-specific default)
- eBGP session works with default TTL

**Pass/Fail Criteria:**
- PASS: Default TTL applied correctly
- FAIL: Configuration rejected or incorrect default

---

### TC-BGP-CLI-NEIGHBOR-109 to 120: Additional eBGP Multihop Tests

**TC-BGP-CLI-NEIGHBOR-109:** eBGP Multihop - Remove Configuration (Positive)
**TC-BGP-CLI-NEIGHBOR-110:** eBGP Multihop - iBGP Neighbor (Edge)
**TC-BGP-CLI-NEIGHBOR-111:** eBGP Multihop - Peer Group (Positive)
**TC-BGP-CLI-NEIGHBOR-112:** eBGP Multihop - IPv6 Neighbor (Positive)
**TC-BGP-CLI-NEIGHBOR-113:** eBGP Multihop - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-114:** eBGP Multihop - Directly Connected Peer (Edge)
**TC-BGP-CLI-NEIGHBOR-115:** eBGP Multihop - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-116:** eBGP Multihop - TTL Security (Edge)
**TC-BGP-CLI-NEIGHBOR-117:** eBGP Multihop - Invalid Syntax (Negative)
**TC-BGP-CLI-NEIGHBOR-118:** eBGP Multihop - Multiple Hops Test (Functional)
**TC-BGP-CLI-NEIGHBOR-119:** eBGP Multihop - Session Establishment Time (Performance)
**TC-BGP-CLI-NEIGHBOR-120:** eBGP Multihop - Dynamic TTL Change (Functional)

---

## Local-AS Configuration Test Cases

### TC-BGP-CLI-NEIGHBOR-121: Configure Local-AS (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-121
**Feature:** BGP Neighbor Local-AS
**Priority:** High
**Type:** Positive

**Objective:**
Verify that local-as can be configured for BGP neighbor for AS migration scenarios.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 local-as 65100
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 10.0.24.2 remote-as 65002" \
  -c "neighbor 10.0.24.2 local-as 65100"
```

**Verification Commands:**
```bash
show running-config | grep "local-as"
show ip bgp neighbors 10.0.24.2 | grep -i "local.*as"
show ip bgp summary
show ip bgp neighbors 10.0.24.2 advertised-routes
```

**Expected Result:**
- Configuration accepted
- `show running-config` displays: `neighbor 10.0.24.2 local-as 65100`
- BGP session uses AS 65100 in OPEN message to peer
- AS-PATH prepended with local-as value
- Session establishes successfully

**Pass/Fail Criteria:**
- PASS: Local-AS configured, session uses configured AS
- FAIL: Configuration rejected or incorrect AS used

---

### TC-BGP-CLI-NEIGHBOR-122: Local-AS with no-prepend (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-122
**Feature:** BGP Neighbor Local-AS
**Priority:** High
**Type:** Positive

**Objective:**
Verify local-as with no-prepend option prevents local-as prepending to AS-PATH.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 local-as 65100 no-prepend
  exit
exit
```

**Verification:**
```bash
show running-config | grep "local-as"
show ip bgp neighbors 10.0.24.2 advertised-routes
```

**Expected Result:**
- Configuration accepted with no-prepend option
- AS-PATH does NOT include local-as (65100)
- AS-PATH includes only real AS (65001)
- Session functional

**Pass/Fail Criteria:**
- PASS: no-prepend works, local-as not in AS-PATH
- FAIL: local-as still prepended or configuration rejected

---

### TC-BGP-CLI-NEIGHBOR-123: Local-AS with replace-as (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-123
**Feature:** BGP Neighbor Local-AS
**Priority:** High
**Type:** Positive

**Objective:**
Verify local-as with replace-as option replaces real AS with local-as in AS-PATH.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 local-as 65100 no-prepend replace-as
  exit
exit
```

**Verification:**
```bash
show running-config | grep "local-as"
show ip bgp neighbors 10.0.24.2 advertised-routes
```

**Expected Result:**
- Configuration accepted with replace-as option
- AS-PATH shows local-as (65100) instead of real AS (65001)
- Peer sees AS 65100 in AS-PATH
- Session functional

**Pass/Fail Criteria:**
- PASS: replace-as works, only local-as in AS-PATH
- FAIL: Real AS still in path or configuration rejected

---

### TC-BGP-CLI-NEIGHBOR-124 to 135: Additional Local-AS Tests

**TC-BGP-CLI-NEIGHBOR-124:** Local-AS - Remove Configuration (Positive)
**TC-BGP-CLI-NEIGHBOR-125:** Local-AS - Invalid AS Number (Negative)
**TC-BGP-CLI-NEIGHBOR-126:** Local-AS - Same as Real AS (Edge)
**TC-BGP-CLI-NEIGHBOR-127:** Local-AS - Same as Remote AS (Edge)
**TC-BGP-CLI-NEIGHBOR-128:** Local-AS - Peer Group (Positive)
**TC-BGP-CLI-NEIGHBOR-129:** Local-AS - IPv6 Neighbor (Positive)
**TC-BGP-CLI-NEIGHBOR-130:** Local-AS - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-131:** Local-AS - iBGP Session (Edge)
**TC-BGP-CLI-NEIGHBOR-132:** Local-AS - 4-Byte AS Numbers (Positive)
**TC-BGP-CLI-NEIGHBOR-133:** Local-AS - AS Migration Scenario (Functional)
**TC-BGP-CLI-NEIGHBOR-134:** Local-AS - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-135:** Local-AS - Dual-AS Configuration (Edge)

---

## Shutdown with Message Test Cases

### TC-BGP-CLI-NEIGHBOR-136: Configure Shutdown with Message (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-136
**Feature:** BGP Neighbor Shutdown with Message
**Priority:** High
**Type:** Positive

**Objective:**
Verify that BGP neighbor can be gracefully shutdown with administrative message.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 shutdown message "Planned maintenance - back in 1 hour"
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 10.0.24.2 remote-as 65002" \
  -c "neighbor 10.0.24.2 shutdown message \"Planned maintenance\""
```

**Verification Commands:**
```bash
show running-config | grep shutdown
show ip bgp neighbors 10.0.24.2 | grep -i shutdown
show ip bgp summary
```

**Expected Result:**
- Configuration accepted
- BGP session gracefully shutdown
- Shutdown message sent to peer in NOTIFICATION message
- Session state: Idle (Admin)
- Peer receives NOTIFICATION with cease code and shutdown message

**Pass/Fail Criteria:**
- PASS: Graceful shutdown with message successful
- FAIL: Configuration rejected or ungraceful shutdown

---

### TC-BGP-CLI-NEIGHBOR-137: Shutdown Message - Character Limit (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-137
**Feature:** BGP Neighbor Shutdown with Message
**Priority:** Medium
**Type:** Edge

**Objective:**
Verify shutdown message character limit enforcement.

**Test Cases:**

**Valid: Short Message (< 128 characters):**
```bash
neighbor 10.0.24.2 shutdown message "Maintenance"
Expected: ACCEPTED
```

**Valid: Maximum Length (128 characters):**
```bash
neighbor 10.0.24.2 shutdown message "This is exactly one hundred and twenty-eight characters long message for testing maximum allowed length limit enforcement."
Expected: ACCEPTED
```

**Invalid: Exceeds Maximum (> 128 characters):**
```bash
neighbor 10.0.24.2 shutdown message "This message is intentionally too long and exceeds the RFC-defined maximum length of one hundred twenty-eight characters for BGP shutdown messages."
Expected: REJECTED or TRUNCATED
```

**Edge: Empty Message:**
```bash
neighbor 10.0.24.2 shutdown message ""
Expected: ACCEPTED (shutdown without message) or REJECTED
```

**Expected Result:**
- Messages ≤ 128 characters accepted
- Messages > 128 characters rejected or truncated
- Appropriate error/warning messages

**Pass/Fail Criteria:**
- PASS: Character limit enforced correctly
- FAIL: Oversized messages accepted without truncation

---

### TC-BGP-CLI-NEIGHBOR-138: Shutdown Message - Special Characters (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-138
**Feature:** BGP Neighbor Shutdown with Message
**Priority:** Low
**Type:** Edge

**Objective:**
Verify shutdown message handles special characters correctly.

**Test Cases:**
```bash
# Test 1: Quotes in message
neighbor 10.0.24.2 shutdown message "Router \"R1\" maintenance"

# Test 2: Unicode characters
neighbor 10.0.24.2 shutdown message "Maintenance: 维护中"

# Test 3: Special symbols
neighbor 10.0.24.2 shutdown message "Maintenance @ site #1 - 50% complete"

# Test 4: Newline/Tab (should be handled)
neighbor 10.0.24.2 shutdown message "Line1\nLine2"
```

**Expected Result:**
- Valid printable ASCII characters accepted
- Special characters handled appropriately (escaped or rejected)
- Non-printable characters stripped or rejected
- Clear error messages for invalid characters

**Pass/Fail Criteria:**
- PASS: Special characters handled consistently
- FAIL: System error or corrupted messages

---

### TC-BGP-CLI-NEIGHBOR-139 to 150: Additional Shutdown Message Tests

**TC-BGP-CLI-NEIGHBOR-139:** Shutdown Message - Remove Shutdown (Positive)
**TC-BGP-CLI-NEIGHBOR-140:** Shutdown Message - Without Message Text (Edge)
**TC-BGP-CLI-NEIGHBOR-141:** Shutdown Message - Peer Group (Positive)
**TC-BGP-CLI-NEIGHBOR-142:** Shutdown Message - IPv6 Neighbor (Positive)
**TC-BGP-CLI-NEIGHBOR-143:** Shutdown Message - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-144:** Shutdown Message - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-145:** Shutdown Message - NOTIFICATION Verification (Functional)
**TC-BGP-CLI-NEIGHBOR-146:** Shutdown Message - Peer Receives Message (Functional)
**TC-BGP-CLI-NEIGHBOR-147:** Shutdown Message - Multiple Neighbors (Scale)
**TC-BGP-CLI-NEIGHBOR-148:** Shutdown Message - Session Recovery (Functional)
**TC-BGP-CLI-NEIGHBOR-149:** Shutdown Message - Invalid Syntax (Negative)
**TC-BGP-CLI-NEIGHBOR-150:** Shutdown Message - RFC 8203 Compliance (Functional)

---

## Timers Connect Test Cases

### TC-BGP-CLI-NEIGHBOR-151: Configure Timers Connect (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-151
**Feature:** BGP Neighbor Timers Connect
**Priority:** High
**Type:** Positive

**Objective:**
Verify that BGP connect timer can be configured to control connection retry interval.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  neighbor 10.0.24.2 timers connect 30
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 10.0.24.2 remote-as 65002" \
  -c "neighbor 10.0.24.2 timers connect 30"
```

**Verification Commands:**
```bash
show running-config | grep "timers connect"
show ip bgp neighbors 10.0.24.2 | grep -i "connect.*timer"
```

**Expected Result:**
- Configuration accepted
- `show running-config` displays: `neighbor 10.0.24.2 timers connect 30`
- Connect retry timer set to 30 seconds
- If session down, BGP retries connection after 30 seconds

**Pass/Fail Criteria:**
- PASS: Connect timer configured successfully
- FAIL: Configuration rejected or incorrect timer value

---

### TC-BGP-CLI-NEIGHBOR-152: Timers Connect - Boundary Values (Edge)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-152
**Feature:** BGP Neighbor Timers Connect
**Priority:** High
**Type:** Edge

**Objective:**
Verify timers connect accepts valid range and rejects invalid values.

**Test Cases:**

**Minimum Valid (1 second):**
```bash
neighbor 10.0.24.2 timers connect 1
Expected: ACCEPTED
```

**Default Value (120 seconds):**
```bash
neighbor 10.0.24.2 timers connect 120
Expected: ACCEPTED
```

**Maximum Valid (65535 seconds):**
```bash
neighbor 10.0.24.2 timers connect 65535
Expected: ACCEPTED
```

**Invalid: Zero:**
```bash
neighbor 10.0.24.2 timers connect 0
Expected: REJECTED
```

**Invalid: Exceeds Maximum:**
```bash
neighbor 10.0.24.2 timers connect 65536
Expected: REJECTED
```

**Invalid: Negative Value:**
```bash
neighbor 10.0.24.2 timers connect -1
Expected: REJECTED
```

**Expected Result:**
- Valid range: 1-65535 seconds accepted
- Out-of-range values rejected with errors
- Non-numeric values rejected

**Pass/Fail Criteria:**
- PASS: All valid values accepted, invalid rejected with errors
- FAIL: Invalid values accepted or valid values rejected

---

### TC-BGP-CLI-NEIGHBOR-153 to 165: Additional Timers Connect Tests

**TC-BGP-CLI-NEIGHBOR-153:** Timers Connect - Remove Configuration (Positive)
**TC-BGP-CLI-NEIGHBOR-154:** Timers Connect - Default Value Restoration (Positive)
**TC-BGP-CLI-NEIGHBOR-155:** Timers Connect - Functional Validation (Functional)
**TC-BGP-CLI-NEIGHBOR-156:** Timers Connect - Peer Group (Positive)
**TC-BGP-CLI-NEIGHBOR-157:** Timers Connect - IPv6 Neighbor (Positive)
**TC-BGP-CLI-NEIGHBOR-158:** Timers Connect - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-159:** Timers Connect - iBGP and eBGP (Positive)
**TC-BGP-CLI-NEIGHBOR-160:** Timers Connect - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-161:** Timers Connect - Rapid Reconnection Test (Functional)
**TC-BGP-CLI-NEIGHBOR-162:** Timers Connect - Invalid Syntax (Negative)
**TC-BGP-CLI-NEIGHBOR-163:** Timers Connect - Multiple Neighbors (Scale)
**TC-BGP-CLI-NEIGHBOR-164:** Timers Connect - Session Flap Behavior (Functional)
**TC-BGP-CLI-NEIGHBOR-165:** Timers Connect - Interaction with Keepalive (Edge)

---

## V6only Configuration Test Cases

### TC-BGP-CLI-NEIGHBOR-166: Enable V6only for IPv4 AFI (Positive)

**Test Case ID:** TC-BGP-CLI-NEIGHBOR-166
**Feature:** BGP Neighbor V6only
**Priority:** High
**Type:** Positive

**Objective:**
Verify that v6only can be enabled to allow IPv6-only peering with IPv4 AFI/SAFI.

**Configuration (Klish Mode - D1):**
```bash
sonic-cli

configure terminal
router bgp 65001
  neighbor 2001:db8:24::2 remote-as 65002
  neighbor 2001:db8:24::2 v6only
  address-family ipv4 unicast
    neighbor 2001:db8:24::2 activate
    exit-address-family
  exit
exit
```

**Configuration (Click Mode - D1):**
```bash
sudo vtysh -c "configure terminal" \
  -c "router bgp 65001" \
  -c "neighbor 2001:db8:24::2 remote-as 65002" \
  -c "neighbor 2001:db8:24::2 v6only" \
  -c "address-family ipv4 unicast" \
  -c "neighbor 2001:db8:24::2 activate"
```

**Verification Commands:**
```bash
show running-config | grep v6only
show bgp neighbors 2001:db8:24::2 | grep -i v6only
show ip bgp summary
```

**Expected Result:**
- Configuration accepted
- IPv6 peering session established
- IPv4 routes exchanged over IPv6 transport
- v6only peer capability negotiated

**Pass/Fail Criteria:**
- PASS: v6only peering works, IPv4 routes over IPv6 session
- FAIL: Configuration rejected or session fails

---

### TC-BGP-CLI-NEIGHBOR-167 to 180: Additional V6only Tests

**TC-BGP-CLI-NEIGHBOR-167:** V6only - Disable Configuration (Positive)
**TC-BGP-CLI-NEIGHBOR-168:** V6only - Peer Group (Positive)
**TC-BGP-CLI-NEIGHBOR-169:** V6only - Configuration Persistence (Persistence)
**TC-BGP-CLI-NEIGHBOR-170:** V6only - Show Commands (Positive)
**TC-BGP-CLI-NEIGHBOR-171:** V6only - Capability Negotiation (Functional)
**TC-BGP-CLI-NEIGHBOR-172:** V6only - IPv4 Neighbor (Negative)
**TC-BGP-CLI-NEIGHBOR-173:** V6only - Extended Nexthop Interaction (Edge)
**TC-BGP-CLI-NEIGHBOR-174:** V6only - Invalid Syntax (Negative)
**TC-BGP-CLI-NEIGHBOR-175:** V6only - Multiple Address Families (Functional)
**TC-BGP-CLI-NEIGHBOR-176:** V6only - eBGP and iBGP (Positive)
**TC-BGP-CLI-NEIGHBOR-177:** V6only - Session Reset Behavior (Functional)
**TC-BGP-CLI-NEIGHBOR-178:** V6only - RFC 8950 Compliance (Functional)
**TC-BGP-CLI-NEIGHBOR-179:** V6only - Non-Existent Neighbor (Negative)
**TC-BGP-CLI-NEIGHBOR-180:** V6only - Multiple Neighbors (Scale)

---

## Test Execution Guidelines

### Pre-Test Setup

1. **Testbed Preparation:**
   - Ensure testbed_vs_3rr_reg.yaml is properly configured
   - Verify all devices are reachable
   - Confirm SONiC version compatibility
   - Backup existing configurations

2. **Tool Verification:**
   - Verify Klish (sonic-cli) accessibility
   - Verify Click mode (vtysh) accessibility
   - Ensure sufficient privileges for BGP configuration

3. **Baseline Configuration:**
   - Clear any existing BGP configurations
   - Establish baseline connectivity (IP addressing, routing)
   - Verify interface status (all UP)

### Test Execution Order

1. Execute positive tests first to establish baseline functionality
2. Execute edge case tests to validate boundary conditions
3. Execute negative tests to verify error handling
4. Execute persistence tests to verify configuration durability
5. Execute functional/performance tests to validate operational behavior

### Post-Test Cleanup

1. Remove all test configurations
2. Restore original configuration (if applicable)
3. Verify no residual test artifacts
4. Document any anomalies or unexpected behaviors

---

## Pass/Fail Criteria

### General Criteria

**PASS Conditions:**
- Configuration accepted without errors
- Show commands reflect configured values accurately
- BGP session behavior matches expected outcome
- Error handling works as designed (for negative tests)
- Configuration persists across reloads (for persistence tests)
- Performance metrics within acceptable ranges (for functional tests)

**FAIL Conditions:**
- Configuration rejected when it should be accepted
- Configuration accepted when it should be rejected
- Incorrect or inconsistent show command outputs
- BGP session fails when it should establish
- System crash or undefined behavior
- Configuration lost after reload (for persistence tests)
- Performance degradation beyond acceptable thresholds

---

## Known Limitations and Notes

1. **Platform Dependencies:**
   - Some features may have platform-specific limitations
   - Virtual platforms may behave differently than hardware platforms

2. **Version Dependencies:**
   - Feature availability may vary by SONiC release version
   - Verify feature support before executing tests

3. **Timing Considerations:**
   - BGP session establishment may take several seconds
   - Allow sufficient time for convergence before verification

4. **Concurrent Testing:**
   - Avoid running conflicting tests simultaneously
   - Ensure proper test isolation

---

## References

1. **RFCs:**
   - RFC 4271: A Border Gateway Protocol 4 (BGP-4)
   - RFC 5492: Capabilities Advertisement with BGP-4
   - RFC 5549: Advertising IPv4 Network Layer Reachability Information with an IPv6 Next Hop
   - RFC 8203: BGP Administrative Shutdown Communication
   - RFC 8950: Advertising IPv4 NLRI with an IPv6 Next Hop (Clarification)

2. **SONiC Documentation:**
   - SONiC BGP Configuration Guide
   - SONiC CLI Reference Manual
   - FRR BGP Documentation (underlying routing stack)

3. **Related Test Plans:**
   - BGP Session Establishment Tests (Doc/bgp_241.md)
   - BGP Route Advertisement Tests
   - BGP Policy Tests

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-28 | QA Team | Initial comprehensive test case document creation |

---

**Document Status:** Final
**Last Updated:** 2026-05-28
**Total Test Cases:** 180
**Review Status:** Ready for Execution
