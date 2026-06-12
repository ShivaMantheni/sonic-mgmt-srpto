# BGP Clear Commands - Comprehensive Test Plan

**Document Version:** 1.0
**Last Updated:** 2026-05-28
**Feature:** BGP Clear Commands
**Module:** Routing / BGP
**Author:** Test Automation Framework
**Testbed:** testbed_vs_3rr_reg.yaml
**Topology:** 3-Router Route Reflector (3RR)

---

## 1. Executive Summary

This test plan provides comprehensive coverage for BGP clear commands in SONiC network operating systems. The plan includes positive and negative test cases for all BGP clear command variants across IPv4/IPv6 unicast address families.

**Total Test Cases:** 52
**Breakdown:**
- Positive Cases: 28
- Negative Cases: 24

**Priority Distribution:**
- P0 (Critical): 12
- P1 (High): 22
- P2 (Medium): 18

**CLI Types Tested:**
- Klish CLI (primary)
- Click/Vtysh CLI (compatibility)

---

## 2. Feature Overview

### 2.1 BGP Clear Commands Purpose

BGP clear commands are used to reset BGP sessions and trigger route updates without tearing down the entire BGP configuration. Key use cases:

- **Hard Reset:** Completely reset BGP session (TCP teardown and re-establishment)
- **Soft Reconfiguration:** Refresh routing information without session reset
  - **Soft In:** Request neighbor to resend routes
  - **Soft Out:** Resend routes to neighbor
  - **Soft (both):** Bi-directional soft reset

### 2.2 Command Variants Covered

#### Global Clear Commands
- `clear bgp all` - Clear all BGP sessions (all address families)

#### IPv4 Unicast Clear Commands
- `clear bgp ipv4 unicast *` - Clear all IPv4 unicast neighbors
- `clear bgp ipv4 unicast <ip-address>` - Clear specific neighbor
- `clear bgp ipv4 unicast external` - Clear all eBGP neighbors
- `clear bgp ipv4 unicast interface <interface>` - Clear neighbors on interface
- `clear bgp ipv4 unicast peer-group <name>` - Clear all peers in peer-group
- `clear bgp ipv4 unicast vrf <vrf-name> *` - Clear neighbors in VRF

#### IPv6 Unicast Clear Commands
- `clear bgp ipv6 unicast *` - Clear all IPv6 unicast neighbors
- `clear bgp ipv6 unicast <ipv6-address>` - Clear specific neighbor
- `clear bgp ipv6 unicast external` - Clear all eBGP neighbors
- `clear bgp ipv6 unicast interface <interface>` - Clear neighbors on interface
- `clear bgp ipv6 unicast peer-group <name>` - Clear all peers in peer-group
- `clear bgp ipv6 unicast vrf <vrf-name> *` - Clear neighbors in VRF

#### Soft Reconfiguration Variants
All above commands support soft reconfiguration options:
- `soft` - Soft reset both directions
- `soft in` - Soft inbound reset
- `soft out` - Soft outbound reset

---

## 3. Test Topology

### 3.1 Physical Topology (3RR - Route Reflector)

```
    +--------+                +--------+                +--------+
    |  DUT1  |----------------| DUT2   |----------------|  DUT3  |
    | (RR)   |  Ethernet32    | (RR    |  Ethernet32    | (Client)|
    | AS     |                | Server)|                | AS      |
    | 65001  |                | AS     |                | 65001   |
    |        |                | 65001  |                |         |
    +--------+                +--------+                +--------+
        |                                                     |
        |                   Ethernet36                        |
        +-----------------------------------------------------+
```

### 3.2 IP Addressing Scheme

**IPv4 Addressing:**
- DUT1-DUT2 link: 10.1.1.1/30 - 10.1.1.2/30
- DUT2-DUT3 link: 10.1.2.1/30 - 10.1.2.2/30
- DUT1-DUT3 link: 10.1.3.1/30 - 10.1.3.2/30

**IPv6 Addressing:**
- DUT1-DUT2 link: 2001:db8:1::1/64 - 2001:db8:1::2/64
- DUT2-DUT3 link: 2001:db8:2::1/64 - 2001:db8:2::2/64
- DUT1-DUT3 link: 2001:db8:3::1/64 - 2001:db8:3::2/64

**Loopback Addresses:**
- DUT1: 1.1.1.1/32 (IPv4), 2001:db8::1/128 (IPv6)
- DUT2: 2.2.2.2/32 (IPv4), 2001:db8::2/128 (IPv6)
- DUT3: 3.3.3.3/32 (IPv4), 2001:db8::3/128 (IPv6)

### 3.3 BGP Configuration

**AS Numbers:**
- All devices: AS 65001 (iBGP)
- External test: Use AS 65002 for eBGP scenarios

**Route Reflector:**
- DUT2 acts as Route Reflector server
- DUT1 and DUT3 are Route Reflector clients

---

## 4. Positive Test Cases

### 4.1 Global Clear Commands

---

#### TC-BGP-CLI-CLEAR-001

**Title:** Clear all BGP sessions using 'clear bgp all'
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Testbed topology: 3RR configured with iBGP sessions
2. All BGP neighbors in Established state (IPv4 and IPv6)
3. Routes exchanged between all peers
4. No pending configuration changes

**Test Steps:**
1. Verify all BGP sessions are Established
   ```
   show bgp ipv4 unicast summary
   show bgp ipv6 unicast summary
   ```
2. Record current BGP session uptime for all neighbors
3. Execute clear command:
   ```
   clear bgp all
   ```
4. Wait 30 seconds for BGP re-convergence
5. Verify all BGP sessions re-established
6. Verify session uptimes are reset (less than 1 minute)
7. Verify route counts match pre-clear values

**Test Data:**
```yaml
neighbors_ipv4:
  - 10.1.1.2  # DUT2
  - 10.1.3.2  # DUT3
neighbors_ipv6:
  - 2001:db8:1::2  # DUT2
  - 2001:db8:3::2  # DUT3
expected_convergence_time: 30
```

**Expected Result:**
- Command executes without errors
- All BGP sessions transition from Established → Idle → Connect → Established
- Session uptimes reset to 0 and begin incrementing
- All routes re-learned after convergence
- No route loss or inconsistencies

**Postcondition/Cleanup:**
- Wait for full BGP convergence before next test
- All sessions remain in Established state

**Verification Commands:**
```
show bgp ipv4 unicast summary
show bgp ipv6 unicast summary
show ip bgp
show bgp ipv6 unicast
```

---

### 4.2 IPv4 Unicast Clear Commands

---

#### TC-BGP-CLI-CLEAR-002

**Title:** Clear all IPv4 unicast neighbors using asterisk wildcard
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 BGP neighbors in Established state
2. IPv4 routes present in BGP table
3. IPv6 sessions also established (to verify they remain unaffected)

**Test Steps:**
1. Verify IPv4 BGP sessions established
2. Record IPv6 session uptime (should remain unchanged)
3. Execute command:
   ```
   clear bgp ipv4 unicast *
   ```
4. Wait 20 seconds for convergence
5. Verify IPv4 sessions re-established
6. Verify IPv6 sessions remain in Established state with original uptime
7. Verify IPv4 route counts restored

**Test Data:**
```yaml
ipv4_neighbors: [10.1.1.2, 10.1.3.2]
ipv6_neighbors: [2001:db8:1::2, 2001:db8:3::2]
convergence_timeout: 20
```

**Expected Result:**
- Only IPv4 unicast sessions reset
- IPv6 sessions unaffected (uptime unchanged)
- IPv4 routes re-learned after convergence
- No cross-address-family impact

**Postcondition/Cleanup:**
- All sessions in Established state

---

#### TC-BGP-CLI-CLEAR-003

**Title:** Clear specific IPv4 neighbor by IP address
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Multiple IPv4 BGP neighbors established
2. Known target neighbor IP address

**Test Steps:**
1. Verify all neighbors in Established state
2. Record uptime for neighbor 10.1.1.2 and 10.1.3.2
3. Execute command to clear only one neighbor:
   ```
   clear bgp ipv4 unicast 10.1.1.2
   ```
4. Wait 15 seconds
5. Verify 10.1.1.2 session reset (uptime < 1 min)
6. Verify 10.1.3.2 session unchanged (original uptime)
7. Verify routes from 10.1.1.2 re-learned

**Test Data:**
```yaml
target_neighbor: 10.1.1.2
unaffected_neighbor: 10.1.3.2
wait_time: 15
```

**Expected Result:**
- Only specified neighbor session reset
- Other neighbors remain in Established state
- Selective session reset successful

**Postcondition/Cleanup:**
- All neighbors in Established state

---

#### TC-BGP-CLI-CLEAR-004

**Title:** Clear external (eBGP) IPv4 neighbors only
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Mixed iBGP and eBGP IPv4 neighbors configured
2. At least one eBGP neighbor (different AS)
3. All sessions in Established state

**Test Steps:**
1. Configure one neighbor as eBGP (AS 65002)
2. Verify iBGP (AS 65001) and eBGP (AS 65002) sessions established
3. Record uptimes for both session types
4. Execute command:
   ```
   clear bgp ipv4 unicast external
   ```
5. Wait 15 seconds
6. Verify only eBGP sessions reset
7. Verify iBGP sessions remain with original uptime

**Test Data:**
```yaml
ibgp_neighbors:
  - ip: 10.1.3.2
    asn: 65001
ebgp_neighbors:
  - ip: 10.1.1.2
    asn: 65002
wait_time: 15
```

**Expected Result:**
- Only eBGP sessions reset (AS != local AS)
- iBGP sessions unaffected
- Selective clear by neighbor type successful

**Postcondition/Cleanup:**
- Restore iBGP configuration
- All sessions in Established state

---

#### TC-BGP-CLI-CLEAR-005

**Title:** Clear IPv4 neighbors on specific interface
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP neighbors configured on multiple interfaces
2. Known interface with BGP neighbor

**Test Steps:**
1. Verify neighbors on Ethernet32 and Ethernet36
2. Record uptimes for all neighbors
3. Execute command:
   ```
   clear bgp ipv4 unicast interface Ethernet32
   ```
4. Wait 15 seconds
5. Verify only Ethernet32 neighbor reset
6. Verify Ethernet36 neighbor uptime unchanged

**Test Data:**
```yaml
target_interface: Ethernet32
target_neighbor: 10.1.1.2
unaffected_interface: Ethernet36
unaffected_neighbor: 10.1.3.2
wait_time: 15
```

**Expected Result:**
- Only neighbors on specified interface reset
- Other interface neighbors unaffected
- Interface-specific clear successful

**Postcondition/Cleanup:**
- All neighbors in Established state

---

#### TC-BGP-CLI-CLEAR-006

**Title:** Clear IPv4 neighbors in peer-group
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Peer-group "SPINE_PEERS" configured with 2+ members
2. At least one neighbor not in peer-group
3. All sessions established

**Test Steps:**
1. Create peer-group "SPINE_PEERS"
2. Add neighbor 10.1.1.2 to peer-group
3. Keep neighbor 10.1.3.2 outside peer-group
4. Verify all sessions established
5. Execute command:
   ```
   clear bgp ipv4 unicast peer-group SPINE_PEERS
   ```
6. Wait 15 seconds
7. Verify only peer-group members reset
8. Verify non-member neighbor uptime unchanged

**Test Data:**
```yaml
peer_group: SPINE_PEERS
pg_members: [10.1.1.2]
non_members: [10.1.3.2]
wait_time: 15
```

**Expected Result:**
- Only peer-group members reset
- Non-member neighbors unaffected
- Peer-group selective clear successful

**Postcondition/Cleanup:**
- Remove peer-group configuration
- All neighbors in Established state

---

#### TC-BGP-CLI-CLEAR-007

**Title:** Clear IPv4 neighbors in specific VRF
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. VRF "Vrf-RED" configured with BGP neighbors
2. Default VRF also has BGP neighbors
3. All sessions established

**Test Steps:**
1. Configure VRF Vrf-RED
2. Add neighbor 10.100.1.2 in Vrf-RED
3. Keep neighbor 10.1.1.2 in default VRF
4. Verify both sessions established
5. Execute command:
   ```
   clear bgp ipv4 unicast vrf Vrf-RED *
   ```
6. Wait 15 seconds
7. Verify only Vrf-RED neighbors reset
8. Verify default VRF neighbors unaffected

**Test Data:**
```yaml
target_vrf: Vrf-RED
vrf_neighbor: 10.100.1.2
default_neighbor: 10.1.1.2
wait_time: 15
```

**Expected Result:**
- Only VRF-specific neighbors reset
- Default VRF neighbors unaffected
- VRF isolation maintained

**Postcondition/Cleanup:**
- Remove VRF configuration
- All default VRF neighbors in Established state

---

### 4.3 IPv4 Soft Reconfiguration Commands

---

#### TC-BGP-CLI-CLEAR-008

**Title:** Soft reset IPv4 neighbor (bidirectional)
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 BGP neighbor 10.1.1.2 in Established state
2. Routes exchanged in both directions
3. Route-map applied for inbound/outbound filtering

**Test Steps:**
1. Record BGP session uptime (should remain unchanged)
2. Record route count before soft reset
3. Execute command:
   ```
   clear bgp ipv4 unicast 10.1.1.2 soft
   ```
4. Wait 10 seconds
5. Verify session remains in Established state
6. Verify session uptime unchanged (no TCP teardown)
7. Verify routes refreshed (route count matches)

**Test Data:**
```yaml
neighbor: 10.1.1.2
expected_state: Established
uptime_tolerance: 5  # seconds tolerance
route_count_tolerance: 0  # exact match expected
```

**Expected Result:**
- BGP session remains Established (no state change)
- Session uptime unchanged
- Routes refreshed without session reset
- TCP connection maintained

**Postcondition/Cleanup:**
- Neighbor remains in Established state

---

#### TC-BGP-CLI-CLEAR-009

**Title:** Soft inbound reset for IPv4 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 neighbor established
2. Inbound route-map configured
3. Soft-reconfiguration inbound enabled

**Test Steps:**
1. Enable soft-reconfiguration inbound:
   ```
   router bgp 65001
   neighbor 10.1.1.2 soft-reconfiguration inbound
   ```
2. Record session uptime
3. Execute command:
   ```
   clear bgp ipv4 unicast 10.1.1.2 soft in
   ```
4. Wait 10 seconds
5. Verify session uptime unchanged
6. Verify inbound routes refreshed
7. Verify outbound routes not re-sent (check neighbor logs)

**Test Data:**
```yaml
neighbor: 10.1.1.2
direction: inbound
soft_reconfig_required: true
```

**Expected Result:**
- Session remains Established
- Only inbound routes refreshed
- Neighbor does not receive route updates from us
- Uptime unchanged

**Postcondition/Cleanup:**
- soft-reconfiguration configuration remains

---

#### TC-BGP-CLI-CLEAR-010

**Title:** Soft outbound reset for IPv4 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 neighbor established
2. Outbound route-map configured

**Test Steps:**
1. Configure outbound route-map
2. Record session uptime
3. Execute command:
   ```
   clear bgp ipv4 unicast 10.1.1.2 soft out
   ```
4. Wait 10 seconds
5. Verify session uptime unchanged
6. Verify outbound routes re-sent to neighbor
7. Verify we do not re-request routes from neighbor

**Test Data:**
```yaml
neighbor: 10.1.1.2
direction: outbound
route_map: SET_METRIC_OUT
```

**Expected Result:**
- Session remains Established
- Only outbound routes re-sent
- We do not request inbound refresh
- Uptime unchanged

**Postcondition/Cleanup:**
- Route-map configuration remains

---

#### TC-BGP-CLI-CLEAR-011

**Title:** Soft reset all IPv4 external neighbors
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Mixed iBGP and eBGP neighbors
2. All sessions established

**Test Steps:**
1. Configure eBGP neighbor (AS 65002)
2. Record uptimes for iBGP and eBGP sessions
3. Execute command:
   ```
   clear bgp ipv4 unicast external soft
   ```
4. Wait 10 seconds
5. Verify only eBGP sessions perform soft reset
6. Verify iBGP session uptimes unchanged
7. Verify eBGP session uptimes unchanged (soft reset)

**Test Data:**
```yaml
ebgp_neighbors:
  - ip: 10.1.1.2
    asn: 65002
ibgp_neighbors:
  - ip: 10.1.3.2
    asn: 65001
```

**Expected Result:**
- Only eBGP neighbors perform soft reset
- All session uptimes unchanged
- iBGP sessions not affected

**Postcondition/Cleanup:**
- Restore iBGP configuration

---

#### TC-BGP-CLI-CLEAR-012

**Title:** Soft reset all IPv4 neighbors using wildcard
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Multiple IPv4 BGP neighbors established
2. Routes exchanged

**Test Steps:**
1. Record uptimes for all neighbors
2. Record route counts
3. Execute command:
   ```
   clear bgp ipv4 unicast * soft
   ```
4. Wait 10 seconds
5. Verify all session uptimes unchanged
6. Verify all routes refreshed
7. Verify no sessions transitioned to non-Established state

**Test Data:**
```yaml
neighbors: [10.1.1.2, 10.1.3.2]
expected_state: Established
```

**Expected Result:**
- All neighbors perform soft reset
- All uptimes unchanged
- All routes refreshed

**Postcondition/Cleanup:**
- All neighbors in Established state

---

### 4.4 IPv6 Unicast Clear Commands

---

#### TC-BGP-CLI-CLEAR-013

**Title:** Clear all IPv6 unicast neighbors
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 BGP neighbors established
2. IPv4 sessions also established (to verify isolation)

**Test Steps:**
1. Verify IPv6 sessions established
2. Record IPv4 and IPv6 session uptimes
3. Execute command:
   ```
   clear bgp ipv6 unicast *
   ```
4. Wait 20 seconds
5. Verify IPv6 sessions reset
6. Verify IPv4 sessions unaffected (original uptime)

**Test Data:**
```yaml
ipv6_neighbors: [2001:db8:1::2, 2001:db8:3::2]
ipv4_neighbors: [10.1.1.2, 10.1.3.2]
wait_time: 20
```

**Expected Result:**
- Only IPv6 sessions reset
- IPv4 sessions unaffected
- Address family isolation maintained

**Postcondition/Cleanup:**
- All sessions in Established state

---

#### TC-BGP-CLI-CLEAR-014

**Title:** Clear specific IPv6 neighbor by address
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Multiple IPv6 neighbors established

**Test Steps:**
1. Record uptimes for all IPv6 neighbors
2. Execute command:
   ```
   clear bgp ipv6 unicast 2001:db8:1::2
   ```
3. Wait 15 seconds
4. Verify only 2001:db8:1::2 reset
5. Verify other IPv6 neighbors unchanged

**Test Data:**
```yaml
target_neighbor: 2001:db8:1::2
unaffected_neighbors: [2001:db8:3::2]
wait_time: 15
```

**Expected Result:**
- Only specified neighbor reset
- Other neighbors unaffected

**Postcondition/Cleanup:**
- All neighbors in Established state

---

#### TC-BGP-CLI-CLEAR-015

**Title:** Clear IPv6 external neighbors
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Mixed iBGP and eBGP IPv6 neighbors
2. All sessions established

**Test Steps:**
1. Configure eBGP neighbor (AS 65002)
2. Record uptimes
3. Execute command:
   ```
   clear bgp ipv6 unicast external
   ```
4. Wait 15 seconds
5. Verify only eBGP sessions reset
6. Verify iBGP sessions unchanged

**Test Data:**
```yaml
ibgp_neighbors:
  - ip: 2001:db8:3::2
    asn: 65001
ebgp_neighbors:
  - ip: 2001:db8:1::2
    asn: 65002
```

**Expected Result:**
- Only eBGP neighbors reset
- iBGP neighbors unaffected

**Postcondition/Cleanup:**
- Restore iBGP configuration

---

#### TC-BGP-CLI-CLEAR-016

**Title:** Clear IPv6 neighbors on interface
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 neighbors on multiple interfaces
2. All sessions established

**Test Steps:**
1. Verify neighbors on Ethernet32 and Ethernet36
2. Execute command:
   ```
   clear bgp ipv6 unicast interface Ethernet32
   ```
3. Wait 15 seconds
4. Verify only Ethernet32 neighbor reset
5. Verify Ethernet36 neighbor unchanged

**Test Data:**
```yaml
target_interface: Ethernet32
target_neighbor: 2001:db8:1::2
unaffected_interface: Ethernet36
unaffected_neighbor: 2001:db8:3::2
```

**Expected Result:**
- Only interface-specific neighbor reset
- Other neighbors unaffected

**Postcondition/Cleanup:**
- All neighbors in Established state

---

#### TC-BGP-CLI-CLEAR-017

**Title:** Clear IPv6 neighbors in peer-group
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 peer-group configured
2. Members and non-members established

**Test Steps:**
1. Create peer-group "IPV6_PEERS"
2. Add 2001:db8:1::2 to peer-group
3. Keep 2001:db8:3::2 outside peer-group
4. Execute command:
   ```
   clear bgp ipv6 unicast peer-group IPV6_PEERS
   ```
5. Wait 15 seconds
6. Verify only peer-group members reset
7. Verify non-members unchanged

**Test Data:**
```yaml
peer_group: IPV6_PEERS
pg_members: [2001:db8:1::2]
non_members: [2001:db8:3::2]
```

**Expected Result:**
- Only peer-group members reset
- Non-members unaffected

**Postcondition/Cleanup:**
- Remove peer-group configuration

---

#### TC-BGP-CLI-CLEAR-018

**Title:** Clear IPv6 neighbors in VRF
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. VRF with IPv6 BGP configured
2. Default VRF also has IPv6 neighbors

**Test Steps:**
1. Configure VRF Vrf-BLUE
2. Add IPv6 neighbor 2001:db8:100::2 in Vrf-BLUE
3. Keep 2001:db8:1::2 in default VRF
4. Execute command:
   ```
   clear bgp ipv6 unicast vrf Vrf-BLUE *
   ```
5. Wait 15 seconds
6. Verify only VRF neighbors reset
7. Verify default VRF neighbors unchanged

**Test Data:**
```yaml
target_vrf: Vrf-BLUE
vrf_neighbor: 2001:db8:100::2
default_neighbor: 2001:db8:1::2
```

**Expected Result:**
- Only VRF neighbors reset
- Default VRF unaffected

**Postcondition/Cleanup:**
- Remove VRF configuration

---

### 4.5 IPv6 Soft Reconfiguration Commands

---

#### TC-BGP-CLI-CLEAR-019

**Title:** Soft reset IPv6 neighbor (bidirectional)
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 neighbor established

**Test Steps:**
1. Record session uptime
2. Execute command:
   ```
   clear bgp ipv6 unicast 2001:db8:1::2 soft
   ```
3. Wait 10 seconds
4. Verify uptime unchanged
5. Verify routes refreshed

**Test Data:**
```yaml
neighbor: 2001:db8:1::2
expected_state: Established
```

**Expected Result:**
- Session remains Established
- Uptime unchanged
- Routes refreshed

**Postcondition/Cleanup:**
- Neighbor in Established state

---

#### TC-BGP-CLI-CLEAR-020

**Title:** Soft inbound reset for IPv6 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 neighbor with soft-reconfiguration inbound

**Test Steps:**
1. Enable soft-reconfiguration inbound
2. Execute command:
   ```
   clear bgp ipv6 unicast 2001:db8:1::2 soft in
   ```
3. Wait 10 seconds
4. Verify uptime unchanged
5. Verify only inbound routes refreshed

**Test Data:**
```yaml
neighbor: 2001:db8:1::2
direction: inbound
```

**Expected Result:**
- Session unchanged
- Only inbound refresh

**Postcondition/Cleanup:**
- Configuration remains

---

#### TC-BGP-CLI-CLEAR-021

**Title:** Soft outbound reset for IPv6 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 neighbor established

**Test Steps:**
1. Configure outbound route-map
2. Execute command:
   ```
   clear bgp ipv6 unicast 2001:db8:1::2 soft out
   ```
3. Wait 10 seconds
4. Verify uptime unchanged
5. Verify only outbound routes re-sent

**Test Data:**
```yaml
neighbor: 2001:db8:1::2
direction: outbound
```

**Expected Result:**
- Session unchanged
- Only outbound refresh

**Postcondition/Cleanup:**
- Configuration remains

---

#### TC-BGP-CLI-CLEAR-022

**Title:** Soft reset all IPv6 external neighbors
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Mixed iBGP and eBGP IPv6 neighbors

**Test Steps:**
1. Configure eBGP neighbor
2. Execute command:
   ```
   clear bgp ipv6 unicast external soft
   ```
3. Wait 10 seconds
4. Verify only eBGP soft reset
5. Verify all uptimes unchanged

**Test Data:**
```yaml
ebgp_neighbors:
  - ip: 2001:db8:1::2
    asn: 65002
ibgp_neighbors:
  - ip: 2001:db8:3::2
    asn: 65001
```

**Expected Result:**
- Only eBGP soft reset
- All uptimes unchanged

**Postcondition/Cleanup:**
- Restore iBGP configuration

---

#### TC-BGP-CLI-CLEAR-023

**Title:** Soft reset all IPv6 neighbors
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Multiple IPv6 neighbors established

**Test Steps:**
1. Record all uptimes
2. Execute command:
   ```
   clear bgp ipv6 unicast * soft
   ```
3. Wait 10 seconds
4. Verify all uptimes unchanged
5. Verify all routes refreshed

**Test Data:**
```yaml
neighbors: [2001:db8:1::2, 2001:db8:3::2]
```

**Expected Result:**
- All neighbors soft reset
- All uptimes unchanged

**Postcondition/Cleanup:**
- All neighbors in Established state

---

### 4.6 Click/Vtysh CLI Compatibility

---

#### TC-BGP-CLI-CLEAR-024

**Title:** Clear IPv4 BGP using vtysh/click CLI
**Priority:** P2
**Type:** Positive
**CLI Type:** Click/Vtysh

**Preconditions:**
1. Click/Vtysh CLI accessible
2. IPv4 BGP neighbors established

**Test Steps:**
1. Switch to vtysh mode
2. Execute command:
   ```
   clear ip bgp ipv4 *
   ```
3. Wait 20 seconds
4. Verify sessions re-established

**Test Data:**
```yaml
cli_type: vtysh
neighbors: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- Command accepted in vtysh
- Sessions reset successfully
- Backward compatibility maintained

**Postcondition/Cleanup:**
- All neighbors in Established state

---

#### TC-BGP-CLI-CLEAR-025

**Title:** Clear IPv6 BGP using vtysh/click CLI
**Priority:** P2
**Type:** Positive
**CLI Type:** Click/Vtysh

**Preconditions:**
1. Click/Vtysh CLI accessible
2. IPv6 BGP neighbors established

**Test Steps:**
1. Switch to vtysh mode
2. Execute command:
   ```
   clear ip bgp ipv6 *
   ```
3. Wait 20 seconds
4. Verify sessions re-established

**Test Data:**
```yaml
cli_type: vtysh
neighbors: [2001:db8:1::2, 2001:db8:3::2]
```

**Expected Result:**
- Command accepted in vtysh
- Sessions reset successfully

**Postcondition/Cleanup:**
- All neighbors in Established state

---

#### TC-BGP-CLI-CLEAR-026

**Title:** Clear BGP VRF using vtysh CLI
**Priority:** P2
**Type:** Positive
**CLI Type:** Click/Vtysh

**Preconditions:**
1. VRF configured with BGP
2. Vtysh CLI accessible

**Test Steps:**
1. Switch to vtysh mode
2. Execute command:
   ```
   clear bgp vrf Vrf-RED ipv4 *
   ```
3. Wait 20 seconds
4. Verify VRF neighbors reset
5. Verify default VRF unaffected

**Test Data:**
```yaml
cli_type: vtysh
vrf: Vrf-RED
vrf_neighbor: 10.100.1.2
default_neighbor: 10.1.1.2
```

**Expected Result:**
- VRF command syntax accepted
- Only VRF neighbors reset

**Postcondition/Cleanup:**
- Remove VRF configuration

---

### 4.7 Multi-Address-Family Tests

---

#### TC-BGP-CLI-CLEAR-027

**Title:** Verify IPv4 clear does not affect IPv6 sessions
**Priority:** P0
**Type:** Positive (Isolation Test)
**CLI Type:** Klish

**Preconditions:**
1. Both IPv4 and IPv6 sessions established to same neighbor
2. All sessions stable

**Test Steps:**
1. Record IPv4 and IPv6 uptimes for neighbor on DUT2
2. Execute IPv4 clear:
   ```
   clear bgp ipv4 unicast 10.1.1.2
   ```
3. Wait 20 seconds
4. Verify IPv4 session uptime reset
5. Verify IPv6 session uptime unchanged (same neighbor)
6. Verify IPv6 routes unaffected

**Test Data:**
```yaml
neighbor_ipv4: 10.1.1.2
neighbor_ipv6: 2001:db8:1::2
same_device: DUT2
```

**Expected Result:**
- IPv4 session reset
- IPv6 session to same device unaffected
- Address family isolation confirmed

**Postcondition/Cleanup:**
- All sessions in Established state

---

#### TC-BGP-CLI-CLEAR-028

**Title:** Verify IPv6 clear does not affect IPv4 sessions
**Priority:** P0
**Type:** Positive (Isolation Test)
**CLI Type:** Klish

**Preconditions:**
1. Both IPv4 and IPv6 sessions established
2. All sessions stable

**Test Steps:**
1. Record IPv4 and IPv6 uptimes
2. Execute IPv6 clear:
   ```
   clear bgp ipv6 unicast 2001:db8:1::2
   ```
3. Wait 20 seconds
4. Verify IPv6 session reset
5. Verify IPv4 session unchanged

**Test Data:**
```yaml
neighbor_ipv4: 10.1.1.2
neighbor_ipv6: 2001:db8:1::2
same_device: DUT2
```

**Expected Result:**
- IPv6 session reset
- IPv4 session unaffected
- Address family isolation confirmed

**Postcondition/Cleanup:**
- All sessions in Established state

---

## 5. Negative Test Cases

### 5.1 Invalid Syntax and Parameters

---

#### TC-BGP-CLI-CLEAR-029

**Title:** Clear BGP with invalid neighbor IP address
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP configured and operational
2. No neighbor with IP 192.168.99.99

**Test Steps:**
1. Execute command with non-existent neighbor:
   ```
   clear bgp ipv4 unicast 192.168.99.99
   ```
2. Verify error message returned
3. Verify existing sessions unaffected
4. Check system logs for errors

**Test Data:**
```yaml
invalid_neighbor: 192.168.99.99
valid_neighbors: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- Command rejected with error message
- Error indicates neighbor not found or invalid
- No impact on existing BGP sessions
- Existing neighbors remain in Established state

**Postcondition/Cleanup:**
- No configuration changes
- All valid neighbors remain operational

**Expected Error Message:**
```
% Error: Neighbor 192.168.99.99 not found
```

---

#### TC-BGP-CLI-CLEAR-030

**Title:** Clear BGP with malformed IPv4 address
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Execute command with malformed IP:
   ```
   clear bgp ipv4 unicast 10.1.1.999
   ```
2. Verify syntax error
3. Verify no sessions affected

**Test Data:**
```yaml
malformed_ip: 10.1.1.999
```

**Expected Result:**
- Command rejected with syntax error
- Parser detects invalid IP format
- No sessions affected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Error: Invalid IP address format
```

---

#### TC-BGP-CLI-CLEAR-031

**Title:** Clear BGP with malformed IPv6 address
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. IPv6 BGP operational

**Test Steps:**
1. Execute command with malformed IPv6:
   ```
   clear bgp ipv6 unicast 2001:db8::gggg
   ```
2. Verify syntax error
3. Verify no sessions affected

**Test Data:**
```yaml
malformed_ipv6: 2001:db8::gggg
```

**Expected Result:**
- Syntax error returned
- No sessions affected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Error: Invalid IPv6 address format
```

---

#### TC-BGP-CLI-CLEAR-032

**Title:** Clear BGP with non-existent VRF
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP in default VRF operational
2. VRF "Vrf-NONEXIST" does not exist

**Test Steps:**
1. Execute command:
   ```
   clear bgp ipv4 unicast vrf Vrf-NONEXIST *
   ```
2. Verify error message
3. Verify default VRF neighbors unaffected

**Test Data:**
```yaml
nonexistent_vrf: Vrf-NONEXIST
default_neighbors: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- Error: VRF not found
- Default VRF sessions unaffected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Error: VRF Vrf-NONEXIST does not exist
```

---

#### TC-BGP-CLI-CLEAR-033

**Title:** Clear BGP with non-existent peer-group
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational
2. Peer-group "FAKE_GROUP" does not exist

**Test Steps:**
1. Execute command:
   ```
   clear bgp ipv4 unicast peer-group FAKE_GROUP
   ```
2. Verify error message
3. Verify all neighbors unaffected

**Test Data:**
```yaml
nonexistent_pg: FAKE_GROUP
valid_neighbors: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- Error: Peer-group not found
- All sessions unaffected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Error: Peer-group FAKE_GROUP does not exist
```

---

#### TC-BGP-CLI-CLEAR-034

**Title:** Clear BGP with non-existent interface
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational
2. Interface Ethernet999 does not exist

**Test Steps:**
1. Execute command:
   ```
   clear bgp ipv4 unicast interface Ethernet999
   ```
2. Verify error message
3. Verify all neighbors unaffected

**Test Data:**
```yaml
nonexistent_interface: Ethernet999
valid_neighbors: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- Error: Interface not found
- All sessions unaffected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Error: Interface Ethernet999 does not exist
```

---

#### TC-BGP-CLI-CLEAR-035

**Title:** Clear BGP with incomplete command syntax
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Execute incomplete command:
   ```
   clear bgp ipv4
   ```
2. Verify syntax error
3. Verify all neighbors unaffected

**Test Data:**
```yaml
incomplete_command: "clear bgp ipv4"
```

**Expected Result:**
- Syntax error: incomplete command
- All sessions unaffected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Incomplete command
```

---

#### TC-BGP-CLI-CLEAR-036

**Title:** Clear BGP with invalid soft direction
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. IPv4 neighbor established

**Test Steps:**
1. Execute command with invalid direction:
   ```
   clear bgp ipv4 unicast 10.1.1.2 soft invalid
   ```
2. Verify syntax error
3. Verify neighbor unaffected

**Test Data:**
```yaml
neighbor: 10.1.1.2
invalid_direction: invalid
valid_directions: [in, out]
```

**Expected Result:**
- Syntax error: invalid direction
- Neighbor session unaffected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Invalid input detected at '^' marker
```

---

### 5.2 Permission and Access Errors

---

#### TC-BGP-CLI-CLEAR-037

**Title:** Clear BGP without proper user privileges
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational
2. Non-privileged user account available

**Test Steps:**
1. Login as non-admin user (if RBAC enabled)
2. Attempt to execute:
   ```
   clear bgp ipv4 unicast *
   ```
3. Verify permission denied error
4. Login as admin and verify sessions unaffected

**Test Data:**
```yaml
non_privileged_user: operator
command: clear bgp ipv4 unicast *
required_privilege: admin
```

**Expected Result:**
- Permission denied error
- Command not executed
- Sessions unaffected

**Postcondition/Cleanup:**
- Logout and login as admin

**Expected Error Message:**
```
% Permission denied
```

---

#### TC-BGP-CLI-CLEAR-038

**Title:** Clear BGP when BGP is not configured
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP routing not configured on device
2. No BGP process running

**Test Steps:**
1. Ensure BGP not configured:
   ```
   show running-config | include router bgp
   ```
2. Attempt to clear:
   ```
   clear bgp ipv4 unicast *
   ```
3. Verify appropriate error message

**Test Data:**
```yaml
bgp_configured: false
```

**Expected Result:**
- Error: BGP not configured or not running
- Command handled gracefully

**Postcondition/Cleanup:**
- No changes (BGP remains unconfigured)

**Expected Error Message:**
```
% BGP is not configured
```

---

### 5.3 State and Timing Errors

---

#### TC-BGP-CLI-CLEAR-039

**Title:** Clear BGP neighbor in non-Established state
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP neighbor configured but in Idle/Active state
2. Neighbor not reachable or misconfigured

**Test Steps:**
1. Configure neighbor with unreachable IP
2. Verify neighbor in Idle/Active state
3. Execute clear command:
   ```
   clear bgp ipv4 unicast 10.99.99.99
   ```
4. Verify command accepted (soft failure)
5. Verify neighbor remains in non-Established state

**Test Data:**
```yaml
unreachable_neighbor: 10.99.99.99
expected_state: Idle
```

**Expected Result:**
- Command accepted (no error)
- Neighbor state unchanged (still Idle/Active)
- No impact on other neighbors
- System handles gracefully

**Postcondition/Cleanup:**
- Remove unreachable neighbor configuration

---

#### TC-BGP-CLI-CLEAR-040

**Title:** Rapid successive clear commands
**Priority:** P2
**Type:** Negative (Stress Test)
**CLI Type:** Klish

**Preconditions:**
1. BGP neighbors established
2. All sessions stable

**Test Steps:**
1. Execute clear command multiple times rapidly:
   ```
   clear bgp ipv4 unicast *
   clear bgp ipv4 unicast *
   clear bgp ipv4 unicast *
   ```
   (within 1 second interval)
2. Monitor BGP session state transitions
3. Verify system stability
4. Verify sessions eventually re-establish

**Test Data:**
```yaml
clear_count: 3
interval_ms: 500
neighbors: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- System handles multiple clears gracefully
- No crash or unexpected behavior
- Sessions eventually stabilize
- All neighbors re-establish after final clear

**Postcondition/Cleanup:**
- Wait for full BGP convergence
- Verify all sessions Established

---

#### TC-BGP-CLI-CLEAR-041

**Title:** Clear BGP during initial convergence
**Priority:** P2
**Type:** Negative (Timing Test)
**CLI Type:** Klish

**Preconditions:**
1. BGP recently configured
2. Neighbors in Connect/OpenSent state

**Test Steps:**
1. Restart BGP process to trigger re-convergence
2. Wait 5 seconds (partial convergence)
3. Execute clear during convergence:
   ```
   clear bgp ipv4 unicast *
   ```
4. Monitor session state
5. Verify eventual convergence

**Test Data:**
```yaml
convergence_wait: 5
neighbors: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- Command accepted during convergence
- System handles timing gracefully
- Sessions eventually establish
- No unexpected state transitions

**Postcondition/Cleanup:**
- Wait for full convergence

---

### 5.4 Soft Reconfiguration Errors

---

#### TC-BGP-CLI-CLEAR-042

**Title:** Soft inbound clear without soft-reconfiguration enabled
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. IPv4 neighbor established
2. Soft-reconfiguration inbound NOT enabled

**Test Steps:**
1. Verify soft-reconfiguration not configured:
   ```
   show running-config | include soft-reconfiguration
   ```
2. Execute soft inbound clear:
   ```
   clear bgp ipv4 unicast 10.1.1.2 soft in
   ```
3. Monitor behavior
4. Verify result (may trigger route refresh or warning)

**Test Data:**
```yaml
neighbor: 10.1.1.2
soft_reconfig_enabled: false
```

**Expected Result:**
- Option 1: Warning message about soft-reconfig not enabled
- Option 2: Route refresh capability used as fallback
- Option 3: Hard reset triggered if no route refresh
- System handles gracefully without crash

**Postcondition/Cleanup:**
- Session remains operational

**Expected Behavior:**
```
% Warning: soft-reconfiguration not enabled, using route refresh
```

---

#### TC-BGP-CLI-CLEAR-043

**Title:** Soft clear on neighbor without route refresh capability
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Neighbor does not support route refresh capability
2. Soft-reconfiguration not enabled

**Test Steps:**
1. Verify neighbor lacks route refresh in capabilities
2. Execute soft clear:
   ```
   clear bgp ipv4 unicast 10.1.1.2 soft
   ```
3. Monitor result

**Test Data:**
```yaml
neighbor: 10.1.1.2
route_refresh_capability: false
soft_reconfig_enabled: false
```

**Expected Result:**
- Warning or error message
- Possible hard reset fallback
- System handles limitation gracefully

**Postcondition/Cleanup:**
- Session remains operational

**Expected Error Message:**
```
% Warning: Neighbor does not support route refresh, performing hard reset
```

---

### 5.5 Address Family Mismatch

---

#### TC-BGP-CLI-CLEAR-044

**Title:** Clear IPv4 command on IPv6-only neighbor
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Neighbor configured for IPv6 only
2. No IPv4 address family configured for neighbor

**Test Steps:**
1. Configure neighbor with IPv6 address family only
2. Attempt IPv4 clear:
   ```
   clear bgp ipv4 unicast 2001:db8:1::2
   ```
3. Verify error (invalid IP format for IPv4)

**Test Data:**
```yaml
ipv6_only_neighbor: 2001:db8:1::2
address_family: ipv6_unicast_only
```

**Expected Result:**
- Syntax error: IPv6 address in IPv4 command
- Neighbor unaffected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Error: Invalid IPv4 address format
```

---

#### TC-BGP-CLI-CLEAR-045

**Title:** Clear IPv6 command on IPv4-only neighbor
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Neighbor configured for IPv4 only

**Test Steps:**
1. Attempt IPv6 clear with IPv4 address:
   ```
   clear bgp ipv6 unicast 10.1.1.2
   ```
2. Verify error

**Test Data:**
```yaml
ipv4_only_neighbor: 10.1.1.2
```

**Expected Result:**
- Syntax error: IPv4 address in IPv6 command
- Neighbor unaffected

**Postcondition/Cleanup:**
- No changes

**Expected Error Message:**
```
% Error: Invalid IPv6 address format
```

---

### 5.6 Mixed Scenario Errors

---

#### TC-BGP-CLI-CLEAR-046

**Title:** Clear command with special characters in peer-group name
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Attempt clear with special chars:
   ```
   clear bgp ipv4 unicast peer-group PEER@GROUP#1
   ```
2. Verify error handling

**Test Data:**
```yaml
invalid_pg_name: PEER@GROUP#1
```

**Expected Result:**
- Syntax error or peer-group not found
- No sessions affected

**Postcondition/Cleanup:**
- No changes

---

#### TC-BGP-CLI-CLEAR-047

**Title:** Clear command with excessively long VRF name
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Attempt clear with 100-character VRF name:
   ```
   clear bgp ipv4 unicast vrf VERYLONG...NAME *
   ```
2. Verify error handling

**Test Data:**
```yaml
vrf_name_length: 100
max_allowed_length: 32
```

**Expected Result:**
- Error: VRF name too long or invalid
- No sessions affected

**Postcondition/Cleanup:**
- No changes

---

#### TC-BGP-CLI-CLEAR-048

**Title:** Clear external when no external neighbors exist
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Only iBGP neighbors configured (same AS)
2. No eBGP neighbors present

**Test Steps:**
1. Verify all neighbors are iBGP
2. Execute:
   ```
   clear bgp ipv4 unicast external
   ```
3. Verify command completes without error
4. Verify no sessions affected (no external neighbors)

**Test Data:**
```yaml
neighbor_as: 65001
local_as: 65001
external_count: 0
```

**Expected Result:**
- Command completes without error
- No sessions affected (no external neighbors to clear)
- Informational message: no external neighbors found

**Postcondition/Cleanup:**
- No changes

**Expected Message:**
```
% No external neighbors found
```

---

#### TC-BGP-CLI-CLEAR-049

**Title:** Clear interface when interface has no BGP neighbors
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Interface Ethernet40 exists but has no BGP neighbors
2. Other interfaces have BGP neighbors

**Test Steps:**
1. Verify Ethernet40 has no BGP neighbors
2. Execute:
   ```
   clear bgp ipv4 unicast interface Ethernet40
   ```
3. Verify command completes
4. Verify other interface neighbors unaffected

**Test Data:**
```yaml
target_interface: Ethernet40
neighbor_count: 0
other_interfaces:
  - Ethernet32
  - Ethernet36
```

**Expected Result:**
- Command completes without error
- No neighbors affected (none on interface)
- Informational message

**Postcondition/Cleanup:**
- No changes

**Expected Message:**
```
% No neighbors found on interface Ethernet40
```

---

#### TC-BGP-CLI-CLEAR-050

**Title:** Clear VRF when VRF has no BGP neighbors
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. VRF Vrf-EMPTY exists but no BGP configured
2. Default VRF has BGP neighbors

**Test Steps:**
1. Create VRF without BGP
2. Execute:
   ```
   clear bgp ipv4 unicast vrf Vrf-EMPTY *
   ```
3. Verify command completes
4. Verify default VRF unaffected

**Test Data:**
```yaml
target_vrf: Vrf-EMPTY
vrf_neighbor_count: 0
default_vrf_neighbors: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- Command completes without error
- No neighbors to clear in VRF
- Default VRF unaffected

**Postcondition/Cleanup:**
- Remove empty VRF

**Expected Message:**
```
% No BGP neighbors configured in VRF Vrf-EMPTY
```

---

#### TC-BGP-CLI-CLEAR-051

**Title:** Clear peer-group with no members
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Peer-group "EMPTY_GROUP" exists but has no members
2. Other neighbors configured outside peer-group

**Test Steps:**
1. Create empty peer-group
2. Execute:
   ```
   clear bgp ipv4 unicast peer-group EMPTY_GROUP
   ```
3. Verify command completes
4. Verify non-member neighbors unaffected

**Test Data:**
```yaml
peer_group: EMPTY_GROUP
member_count: 0
non_members: [10.1.1.2, 10.1.3.2]
```

**Expected Result:**
- Command completes without error
- No neighbors affected (peer-group empty)
- Non-members unaffected

**Postcondition/Cleanup:**
- Remove empty peer-group

**Expected Message:**
```
% Peer-group EMPTY_GROUP has no members
```

---

#### TC-BGP-CLI-CLEAR-052

**Title:** Clear command during device reboot
**Priority:** P2
**Type:** Negative (Edge Case)
**CLI Type:** Klish

**Preconditions:**
1. BGP operational
2. Device reboot initiated

**Test Steps:**
1. Initiate reboot in background
2. Attempt clear command during reboot:
   ```
   clear bgp ipv4 unicast *
   ```
3. Verify system response

**Test Data:**
```yaml
reboot_initiated: true
command_timing: during_reboot
```

**Expected Result:**
- Command may fail with connection error
- OR: Command queued but not executed
- OR: Error message: system restarting
- No unexpected crashes or corruption

**Postcondition/Cleanup:**
- Wait for reboot completion
- Verify BGP resumes normally

**Expected Behavior:**
- Graceful failure or queuing
- No system corruption

---

## 6. Test Execution Guidelines

### 6.1 Pre-Test Setup

**Configuration Script:**
```bash
# Configure baseline BGP on all 3 routers
# DUT1 configuration
router bgp 65001
  router-id 1.1.1.1
  neighbor 10.1.1.2 remote-as 65001
  neighbor 10.1.3.2 remote-as 65001
  neighbor 2001:db8:1::2 remote-as 65001
  neighbor 2001:db8:3::2 remote-as 65001
  address-family ipv4 unicast
    neighbor 10.1.1.2 activate
    neighbor 10.1.3.2 activate
  address-family ipv6 unicast
    neighbor 2001:db8:1::2 activate
    neighbor 2001:db8:3::2 activate

# DUT2 configuration (Route Reflector)
router bgp 65001
  router-id 2.2.2.2
  neighbor 10.1.1.1 remote-as 65001
  neighbor 10.1.2.2 remote-as 65001
  neighbor 2001:db8:1::1 remote-as 65001
  neighbor 2001:db8:2::2 remote-as 65001
  address-family ipv4 unicast
    neighbor 10.1.1.1 activate
    neighbor 10.1.1.1 route-reflector-client
    neighbor 10.1.2.2 activate
    neighbor 10.1.2.2 route-reflector-client
  address-family ipv6 unicast
    neighbor 2001:db8:1::1 activate
    neighbor 2001:db8:1::1 route-reflector-client
    neighbor 2001:db8:2::2 activate
    neighbor 2001:db8:2::2 route-reflector-client

# DUT3 configuration
router bgp 65001
  router-id 3.3.3.3
  neighbor 10.1.2.1 remote-as 65001
  neighbor 10.1.3.1 remote-as 65001
  neighbor 2001:db8:2::1 remote-as 65001
  neighbor 2001:db8:3::1 remote-as 65001
  address-family ipv4 unicast
    neighbor 10.1.2.1 activate
    neighbor 10.1.3.1 activate
  address-family ipv6 unicast
    neighbor 2001:db8:2::1 activate
    neighbor 2001:db8:3::1 activate
```

### 6.2 Verification Commands

**Essential verification commands after each clear:**

```bash
# BGP summary
show bgp ipv4 unicast summary
show bgp ipv6 unicast summary

# Neighbor details
show bgp ipv4 unicast neighbors
show bgp ipv6 unicast neighbors

# Route counts
show ip bgp summary
show bgp ipv6 unicast summary

# Session state
show bgp ipv4 unicast neighbors <ip> | include BGP state
show bgp ipv6 unicast neighbors <ipv6> | include BGP state

# Uptime verification
show bgp ipv4 unicast neighbors <ip> | include "BGP version\\|up for"
```

### 6.3 Wait Times and Convergence

**Recommended wait times:**
- After hard reset: 30 seconds minimum
- After soft reset: 10 seconds minimum
- After clear all: 45 seconds minimum
- Before verification: 5 seconds minimum

### 6.4 Test Cleanup

**After each test:**
1. Verify all sessions return to Established state
2. Clear any test-specific configuration (VRFs, peer-groups)
3. Verify route counts match baseline
4. Check for error messages in syslog
5. Wait 10 seconds before next test

### 6.5 Logging and Debugging

**Enable debug logging before tests:**
```bash
# On each DUT
debug bgp updates
debug bgp neighbor-events
terminal monitor
```

**Collect logs after failed tests:**
```bash
show logging | include BGP
show bgp ipv4 unicast summary
show running-config | section router bgp
```

---

## 7. Success Criteria

### 7.1 Positive Test Success Criteria

**For each positive test case, all of the following must be true:**

1. **Command Execution:**
   - Command accepted without syntax errors
   - Command completes within expected time

2. **Session Behavior:**
   - Target sessions reset as expected
   - Non-target sessions unaffected
   - All sessions return to Established state

3. **Route Behavior:**
   - Routes re-learned after reset
   - Route counts match pre-clear values (±tolerance)
   - No route loss or corruption

4. **Timing:**
   - Convergence within expected time window
   - Uptime reset for hard clear
   - Uptime unchanged for soft clear

5. **Isolation:**
   - Address family isolation maintained
   - VRF isolation maintained
   - Neighbor-specific operations isolated

### 7.2 Negative Test Success Criteria

**For each negative test case, all of the following must be true:**

1. **Error Handling:**
   - Appropriate error message returned
   - Error message accurately describes problem
   - No generic or misleading errors

2. **System Stability:**
   - No system crash or hang
   - CLI remains responsive
   - BGP process continues running

3. **State Protection:**
   - No unintended neighbor resets
   - No configuration corruption
   - All valid sessions remain operational

4. **Logging:**
   - Error logged appropriately in syslog
   - No spurious error messages for valid neighbors

---

## 8. Test Automation Notes

### 8.1 Python Test Implementation

**Recommended test structure:**

```python
import pytest
from spytest import st, SpyTestDict
import apis.routing.bgp as bgpapi
import apis.routing.ip as ipapi

# Global variables
vars = SpyTestDict()
data = SpyTestDict()

# Test configuration
CONFIG = SpyTestDict({
    "as_number": "65001",
    "ipv4_neighbors": ["10.1.1.2", "10.1.3.2"],
    "ipv6_neighbors": ["2001:db8:1::2", "2001:db8:3::2"],
    "convergence_timeout": 30,
    "soft_reset_timeout": 10,
})

@pytest.fixture(scope="module", autouse=True)
def bgp_clear_module_hooks(request):
    global vars
    vars = st.ensure_min_topology("D1D2:1", "D1D3:1", "D2D3:1")
    data.cli_type = "klish"

    # Setup BGP
    bgp_baseline_config()

    yield

    # Cleanup
    bgp_baseline_cleanup()

def verify_neighbor_state(dut, neighbor, expected_state="Established"):
    """Verify BGP neighbor state"""
    result = bgpapi.verify_bgp_neighbor(
        dut, neighborip=neighbor, state=expected_state
    )
    return result

def verify_uptime_reset(dut, neighbor, max_uptime=60):
    """Verify neighbor uptime was reset (< max_uptime seconds)"""
    output = bgpapi.show_bgp_ipv4_neighbor(dut, neighbor)
    uptime = parse_uptime(output)
    return uptime < max_uptime

def verify_uptime_unchanged(dut, neighbor, previous_uptime, tolerance=5):
    """Verify neighbor uptime did NOT reset"""
    output = bgpapi.show_bgp_ipv4_neighbor(dut, neighbor)
    current_uptime = parse_uptime(output)
    return abs(current_uptime - previous_uptime) <= tolerance

def test_clear_bgp_all():
    """TC-BGP-CLI-CLEAR-001: Clear all BGP sessions"""
    # Record uptimes
    uptimes_before = {}
    for nbr in CONFIG.ipv4_neighbors:
        uptimes_before[nbr] = get_uptime(vars.D1, nbr)

    # Execute clear
    bgpapi.clear_bgp_vtysh(vars.D1, address_family='all')

    # Wait for convergence
    st.wait(CONFIG.convergence_timeout)

    # Verify all sessions re-established
    for nbr in CONFIG.ipv4_neighbors:
        if not verify_neighbor_state(vars.D1, nbr):
            st.report_fail("bgp_neighbor_not_established", nbr)
        if not verify_uptime_reset(vars.D1, nbr):
            st.report_fail("bgp_uptime_not_reset", nbr)

    st.report_pass("test_case_passed")
```

### 8.2 API Functions Used

**Key BGP API functions for clear operations:**

```python
# From apis/routing/bgp.py

# Clear all BGP (both IPv4 and IPv6)
bgpapi.clear_bgp_vtysh(dut, address_family='all')

# Clear IPv4 neighbors
bgpapi.clear_ip_bgp_vtysh(dut, value="*")
bgpapi.clear_ip_bgp_vtysh(dut, value="10.1.1.2")
bgpapi.clear_ip_bgp_vtysh(dut, value="*", soft=True, dir="in")

# Clear IPv6 neighbors
bgpapi.clear_ipv6_bgp_vtysh(dut, value="*")
bgpapi.clear_ipv6_bgp_vtysh(dut, value="2001:db8:1::2")
bgpapi.clear_ipv6_bgp_vtysh(dut, value="*", soft=True, dir="out")

# Clear VRF neighbors
bgpapi.clear_ip_bgp_vrf_vtysh(dut, vrf="Vrf-RED", family='ipv4', value="*")
bgpapi.clear_ip_bgp_vrf_vtysh(dut, vrf="Vrf-BLUE", family='ipv6', value="*")

# Verification functions
bgpapi.verify_bgp_neighbor(dut, neighborip=neighbor, state="Established")
bgpapi.show_bgp_ipv4_neighbor_vtysh(dut, neighbor_ip=neighbor)
bgpapi.show_bgp_ipv6_neighbor_vtysh(dut, neighbor_ip=neighbor)
```

### 8.3 Common Test Patterns

**Pattern 1: Record and Compare Uptimes**
```python
def record_uptimes(dut, neighbors):
    uptimes = {}
    for nbr in neighbors:
        output = bgpapi.show_bgp_ipv4_neighbor(dut, nbr)
        uptimes[nbr] = parse_uptime(output)
    return uptimes

def verify_uptimes_reset(dut, neighbors, max_uptime=60):
    for nbr in neighbors:
        if not verify_uptime_reset(dut, nbr, max_uptime):
            return False
    return True
```

**Pattern 2: Verify Isolation**
```python
def verify_neighbor_isolation(dut, reset_neighbors, unchanged_neighbors):
    # Verify reset neighbors have new uptime
    for nbr in reset_neighbors:
        if not verify_uptime_reset(dut, nbr):
            st.log(f"ERROR: {nbr} uptime not reset")
            return False

    # Verify unchanged neighbors have old uptime
    for nbr in unchanged_neighbors:
        old_uptime = get_previous_uptime(nbr)
        if not verify_uptime_unchanged(dut, nbr, old_uptime):
            st.log(f"ERROR: {nbr} uptime changed unexpectedly")
            return False

    return True
```

**Pattern 3: Negative Test Wrapper**
```python
def execute_invalid_command(dut, command, expected_error_pattern):
    """Execute command expected to fail and verify error"""
    try:
        output = st.config(dut, command, type='klish', conf=False, skip_error_check=False)
        if expected_error_pattern not in output:
            st.log(f"ERROR: Expected error pattern not found: {expected_error_pattern}")
            return False
    except Exception as e:
        if expected_error_pattern in str(e):
            return True
        st.log(f"ERROR: Unexpected exception: {e}")
        return False
    return True
```

---

## 9. Appendix

### 9.1 Reference Documents

- RFC 4271: A Border Gateway Protocol 4 (BGP-4)
- RFC 2918: Route Refresh Capability for BGP-4
- SONiC BGP Configuration Guide
- FRRouting BGP Documentation

### 9.2 Glossary

| Term | Definition |
|------|------------|
| **Hard Reset** | Complete BGP session reset with TCP teardown |
| **Soft Reset** | Route refresh without session teardown |
| **Route Refresh** | BGP capability to re-request routes |
| **Soft Reconfiguration** | Storing unfiltered routes for policy changes |
| **iBGP** | Internal BGP (same AS) |
| **eBGP** | External BGP (different AS) |
| **RR** | Route Reflector |
| **AS** | Autonomous System |
| **AFI** | Address Family Identifier |
| **SAFI** | Subsequent Address Family Identifier |

### 9.3 CLI Command Reference

**Klish CLI Commands:**
```
clear bgp all
clear bgp ipv4 unicast *
clear bgp ipv4 unicast <ip-address>
clear bgp ipv4 unicast external
clear bgp ipv4 unicast interface <interface>
clear bgp ipv4 unicast peer-group <name>
clear bgp ipv4 unicast vrf <vrf-name> *
clear bgp ipv4 unicast * soft [in|out]
clear bgp ipv6 unicast *
clear bgp ipv6 unicast <ipv6-address>
clear bgp ipv6 unicast external
clear bgp ipv6 unicast interface <interface>
clear bgp ipv6 unicast peer-group <name>
clear bgp ipv6 unicast vrf <vrf-name> *
clear bgp ipv6 unicast * soft [in|out]
```

**Vtysh/Click CLI Commands:**
```
clear ip bgp ipv4 *
clear ip bgp ipv6 *
clear bgp vrf <vrf-name> ipv4 *
clear bgp vrf <vrf-name> ipv6 *
```

### 9.4 Test Case Priority Definitions

| Priority | Definition | Execution Frequency |
|----------|------------|---------------------|
| **P0** | Critical functionality, must pass | Every build |
| **P1** | High priority, important features | Daily regression |
| **P2** | Medium priority, edge cases | Weekly regression |
| **P3** | Low priority, nice-to-have | Monthly regression |

---

**Document End**

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-28 | Test Automation | Initial comprehensive test plan |

---

**Approval:**

- Test Lead: _______________
- Development Lead: _______________
- QA Manager: _______________

---
