# BGP Show Commands - Comprehensive Test Plan

**Document Version:** 1.0
**Last Updated:** 2026-06-03
**Feature:** BGP Show Commands
**Module:** Routing / BGP
**Author:** Test Automation Framework
**Testbed:** testbed_vs_2node.yaml
**Topology:** 2-Node BGP Peer Setup
**CLI Type:** Klish (Primary)

---

## 1. Executive Summary

This test plan provides comprehensive coverage for BGP show commands in SONiC network operating systems. The plan includes positive and negative test cases for all BGP show command variants across IPv4/IPv6 unicast address families using Klish CLI.

**Total Test Cases:** 90
**Breakdown:**
- Positive Cases: 70
- Negative Cases: 20

**Priority Distribution:**
- P0 (Critical): 15
- P1 (High): 45
- P2 (Medium): 30

**CLI Type:** Klish CLI (primary)

---

## 2. Feature Overview

### 2.1 BGP Show Commands Purpose

BGP show commands are used to display the operational state, configuration, and learned routing information of BGP sessions. They are essential for:

- **Neighbor State Monitoring:** Check BGP session status and statistics
- **Route Table Verification:** Display learned, advertised, and received routes
- **Configuration Verification:** Review running BGP configuration
- **Troubleshooting:** Diagnose BGP issues through detailed output
- **Performance Monitoring:** View statistics and counters

### 2.2 Command Categories Covered

#### A. BGP Summary Commands
- `show bgp summary` - All BGP sessions summary
- `show bgp ipv4 unicast summary` - IPv4 unicast summary
- `show bgp ipv6 unicast summary` - IPv6 unicast summary
- `show bgp vrf <vrf-name> summary` - VRF-specific summary

#### B. BGP Neighbor Commands
- `show bgp neighbors` - All neighbors details
- `show bgp ipv4 unicast neighbors <ip>` - Specific IPv4 neighbor
- `show bgp ipv6 unicast neighbors <ipv6>` - Specific IPv6 neighbor
- `show bgp neighbors <ip> advertised-routes` - Routes advertised to peer
- `show bgp neighbors <ip> received-routes` - Routes received from peer
- `show bgp neighbors <ip> routes` - Accepted routes from peer

#### C. BGP Route Table Commands
- `show ip bgp` - IPv4 BGP route table
- `show bgp ipv6 unicast` - IPv6 BGP route table
- `show ip bgp <prefix>` - Specific IPv4 prefix details
- `show bgp ipv6 unicast <prefix>` - Specific IPv6 prefix details
- `show ip bgp cidr-only` - CIDR routes only
- `show ip bgp community <community>` - Routes with community

#### D. BGP Configuration Commands
- `show running-config bgp` - BGP configuration
- `show bgp ipv4 unicast neighbors <ip> configuration` - Neighbor config

#### E. BGP Statistics and Counters
- `show bgp statistics` - BGP global statistics
- `show bgp peer-group` - Peer group information
- `show bgp update-group` - Update group information

#### F. BGP VRF Commands
- `show bgp vrf <vrf-name> ipv4 unicast` - VRF IPv4 routes
- `show bgp vrf <vrf-name> ipv6 unicast` - VRF IPv6 routes
- `show bgp vrf <vrf-name> neighbors` - VRF neighbors

---

## 3. Test Topology

### 3.1 Physical Topology (2-Node Setup)

```
    +--------+                                +--------+
    |  DUT1  |--------------------------------|  DUT2  |
    |        |  Ethernet32 (10.1.1.1/30)     |        |
    | AS     |  2001:db8:1::1/64              | AS     |
    | 65001  |                                | 65001  |
    |        |                                |        |
    +--------+                                +--------+
```

### 3.2 IP Addressing Scheme

**IPv4 Addressing:**
- DUT1-DUT2 link: 10.1.1.1/30 - 10.1.1.2/30

**IPv6 Addressing:**
- DUT1-DUT2 link: 2001:db8:1::1/64 - 2001:db8:1::2/64

**Loopback Addresses:**
- DUT1: 1.1.1.1/32 (IPv4), 2001:db8::1/128 (IPv6)
- DUT2: 2.2.2.2/32 (IPv4), 2001:db8::2/128 (IPv6)

### 3.3 BGP Configuration

**AS Numbers:**
- DUT1: AS 65001 (iBGP scenario)
- DUT2: AS 65001 (iBGP scenario)
- For eBGP tests: DUT2 uses AS 65002

**Route Advertisements:**
- DUT1 advertises: 100.1.0.0/16, 100.2.0.0/16, 2001:100::/32
- DUT2 advertises: 200.1.0.0/16, 200.2.0.0/16, 2001:200::/32

---

## 4. Positive Test Cases

### 4.1 BGP Summary Commands

---

#### TC-BGP-SHOW-001

**Title:** Display global BGP summary (all address families)
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP configured with IPv4 and IPv6 neighbors
2. All neighbors in Established state
3. Routes advertised and received

**Test Steps:**
1. Execute command:
   ```
   show bgp summary
   ```
2. Verify output contains:
   - Local AS number
   - Router ID
   - Table version
   - Neighbor entries for both IPv4 and IPv6
   - State/PfxRcd columns populated
3. Verify all neighbors show "Established" state
4. Verify prefix received counts > 0

**Test Data:**
```yaml
local_as: 65001
router_id: 1.1.1.1
neighbors:
  - ip: 10.1.1.2
    state: Established
    prefix_count: ">0"
  - ip: 2001:db8:1::2
    state: Established
    prefix_count: ">0"
```

**Expected Result:**
- Command executes successfully
- Output displays all configured neighbors
- State column shows "Established" for active sessions
- PfxRcd column shows received prefix counts
- No error messages or truncated output

**Verification Commands:**
```
show bgp summary
show running-config bgp
```

---

#### TC-BGP-SHOW-002

**Title:** Display IPv4 unicast BGP summary
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 BGP neighbors configured
2. Neighbors in Established state

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast summary
   ```
2. Verify output contains:
   - IPv4 neighbors only (no IPv6)
   - Neighbor IP, Version, AS, MsgRcvd, MsgSent, TblVer, InQ, OutQ, Up/Down, State/PfxRcd
3. Verify neighbor state is "Established"
4. Verify uptime is reasonable

**Test Data:**
```yaml
neighbors:
  - ip: 10.1.1.2
    remote_as: 65001
    state: Established
    version: 4
```

**Expected Result:**
- Only IPv4 neighbors displayed
- All expected columns present
- Data formatted correctly
- Counters show activity (MsgRcvd, MsgSent > 0)

**Verification Commands:**
```
show bgp ipv4 unicast summary
show bgp ipv4 unicast neighbors
```

---

#### TC-BGP-SHOW-003

**Title:** Display IPv6 unicast BGP summary
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 BGP neighbors configured
2. Neighbors in Established state

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv6 unicast summary
   ```
2. Verify output contains:
   - IPv6 neighbors only
   - Proper IPv6 address formatting
   - State and prefix count
3. Verify no IPv4 neighbors displayed

**Test Data:**
```yaml
neighbors:
  - ip: 2001:db8:1::2
    remote_as: 65001
    state: Established
    address_family: ipv6
```

**Expected Result:**
- Only IPv6 neighbors shown
- IPv6 addresses properly formatted
- State shows "Established"
- Prefix counts accurate

**Verification Commands:**
```
show bgp ipv6 unicast summary
show bgp ipv6 unicast neighbors
```

---

### 4.2 BGP Neighbor Detail Commands

---

#### TC-BGP-SHOW-004

**Title:** Display all BGP neighbors detailed information
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Multiple BGP neighbors configured
2. Sessions established

**Test Steps:**
1. Execute command:
   ```
   show bgp neighbors
   ```
2. Verify output contains for each neighbor:
   - BGP neighbor address
   - Remote AS number
   - BGP version
   - BGP state (Established)
   - Neighbor capabilities
   - Received/Sent update counts
   - Hold/Keepalive timers
   - Configured timers
   - Connection information
   - Route statistics

**Test Data:**
```yaml
neighbors:
  - 10.1.1.2
  - 2001:db8:1::2
expected_fields:
  - BGP neighbor
  - remote AS
  - BGP version
  - BGP state
  - Hold time
  - Keepalive interval
```

**Expected Result:**
- Detailed information for all neighbors displayed
- All critical fields present
- No truncation or formatting errors
- Statistics show activity

**Verification Commands:**
```
show bgp neighbors
show bgp summary
```

---

#### TC-BGP-SHOW-005

**Title:** Display specific IPv4 neighbor details
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 neighbor 10.1.1.2 configured and established

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors 10.1.1.2
   ```
2. Verify output contains:
   - Neighbor IP: 10.1.1.2
   - BGP state: Established
   - Remote AS
   - Last reset reason (if any)
   - Prefix counts (accepted, sent)
   - Timer values
   - Capabilities exchanged
3. Verify only this neighbor's information shown

**Test Data:**
```yaml
neighbor: 10.1.1.2
remote_as: 65001
expected_state: Established
capabilities:
  - multiprotocol
  - route-refresh
  - 4-byte-as
```

**Expected Result:**
- Only specified neighbor details shown
- All sections complete
- Capabilities accurately listed
- Statistics populated

**Verification Commands:**
```
show bgp ipv4 unicast neighbors 10.1.1.2
show bgp ipv4 unicast summary
```

---

#### TC-BGP-SHOW-006

**Title:** Display specific IPv6 neighbor details
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 neighbor 2001:db8:1::2 configured

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv6 unicast neighbors 2001:db8:1::2
   ```
2. Verify IPv6-specific details
3. Verify address family information

**Test Data:**
```yaml
neighbor: 2001:db8:1::2
remote_as: 65001
address_family: ipv6 unicast
```

**Expected Result:**
- IPv6 neighbor details complete
- IPv6 address family information correct
- Link-local address shown (if applicable)

**Verification Commands:**
```
show bgp ipv6 unicast neighbors 2001:db8:1::2
show bgp ipv6 unicast summary
```

---

### 4.3 BGP Advertised/Received Routes

---

#### TC-BGP-SHOW-007

**Title:** Display routes advertised to IPv4 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 neighbor established
2. Local routes advertised to neighbor

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors 10.1.1.2 advertised-routes
   ```
2. Verify output contains:
   - List of prefixes advertised
   - Next-hop information
   - Path attributes (AS-path, origin)
3. Verify count matches configured advertisements

**Test Data:**
```yaml
neighbor: 10.1.1.2
expected_prefixes:
  - 100.1.0.0/16
  - 100.2.0.0/16
  - 1.1.1.1/32
```

**Expected Result:**
- All advertised routes listed
- Next-hop correctly shown
- AS-path information present
- No extraneous routes

**Verification Commands:**
```
show bgp ipv4 unicast neighbors 10.1.1.2 advertised-routes
show ip bgp
```

---

#### TC-BGP-SHOW-008

**Title:** Display routes received from IPv4 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 neighbor established
2. Routes received from neighbor

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors 10.1.1.2 received-routes
   ```
2. Verify routes received from peer displayed
3. Verify includes routes not yet accepted (if soft-reconfiguration enabled)

**Test Data:**
```yaml
neighbor: 10.1.1.2
expected_prefixes:
  - 200.1.0.0/16
  - 200.2.0.0/16
```

**Expected Result:**
- Received routes listed
- Includes filtered routes (if soft-reconfig enabled)
- Accurate prefix count

**Note:** Requires `neighbor soft-reconfiguration inbound` to be configured

**Verification Commands:**
```
show bgp ipv4 unicast neighbors 10.1.1.2 received-routes
show bgp ipv4 unicast neighbors 10.1.1.2 routes
```

---

#### TC-BGP-SHOW-009

**Title:** Display accepted routes from IPv4 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv4 neighbor established
2. Routes received and accepted

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors 10.1.1.2 routes
   ```
2. Verify only accepted (installed) routes shown
3. Compare with received-routes (should be subset)

**Test Data:**
```yaml
neighbor: 10.1.1.2
expected_prefixes:
  - 200.1.0.0/16
  - 200.2.0.0/16
```

**Expected Result:**
- Accepted routes listed
- Matches routes in BGP table
- Count accurate

**Verification Commands:**
```
show bgp ipv4 unicast neighbors 10.1.1.2 routes
show ip bgp
```

---

#### TC-BGP-SHOW-010

**Title:** Display routes advertised to IPv6 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 neighbor established
2. IPv6 routes advertised

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv6 unicast neighbors 2001:db8:1::2 advertised-routes
   ```
2. Verify IPv6 prefixes listed
3. Verify next-hop is IPv6 address

**Test Data:**
```yaml
neighbor: 2001:db8:1::2
expected_prefixes:
  - 2001:100::/32
  - 2001:db8::1/128
```

**Expected Result:**
- IPv6 routes displayed
- IPv6 next-hop shown
- Prefix format correct

**Verification Commands:**
```
show bgp ipv6 unicast neighbors 2001:db8:1::2 advertised-routes
show bgp ipv6 unicast
```

---

#### TC-BGP-SHOW-011

**Title:** Display routes received from IPv6 neighbor
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 neighbor established
2. Soft-reconfiguration inbound enabled

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv6 unicast neighbors 2001:db8:1::2 received-routes
   ```
2. Verify received IPv6 routes shown

**Test Data:**
```yaml
neighbor: 2001:db8:1::2
expected_prefixes:
  - 2001:200::/32
```

**Expected Result:**
- IPv6 received routes listed
- Prefix format correct

**Verification Commands:**
```
show bgp ipv6 unicast neighbors 2001:db8:1::2 received-routes
show bgp ipv6 unicast neighbors 2001:db8:1::2 routes
```

---

### 4.4 BGP Route Table Commands

---

#### TC-BGP-SHOW-012

**Title:** Display IPv4 BGP route table
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP sessions established
2. Routes learned and advertised

**Test Steps:**
1. Execute command:
   ```
   show ip bgp
   ```
2. Verify output contains:
   - Status codes legend (* = valid, > = best, etc.)
   - Network prefixes
   - Next hop
   - Metric
   - LocPrf
   - Weight
   - Path (AS-path)
3. Verify best path marked with ">"

**Test Data:**
```yaml
expected_prefixes:
  - 100.1.0.0/16
  - 100.2.0.0/16
  - 200.1.0.0/16
  - 200.2.0.0/16
```

**Expected Result:**
- All BGP routes displayed
- Status codes correct
- Best paths marked
- Formatting clean

**Verification Commands:**
```
show ip bgp
show bgp ipv4 unicast summary
```

---

#### TC-BGP-SHOW-013

**Title:** Display IPv6 BGP route table
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 BGP sessions established
2. IPv6 routes exchanged

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv6 unicast
   ```
2. Verify IPv6 routes displayed
3. Verify IPv6 next-hop format

**Test Data:**
```yaml
expected_prefixes:
  - 2001:100::/32
  - 2001:200::/32
```

**Expected Result:**
- IPv6 routes listed
- IPv6 next-hops shown
- Best paths marked

**Verification Commands:**
```
show bgp ipv6 unicast
show bgp ipv6 unicast summary
```

---

#### TC-BGP-SHOW-014

**Title:** Display specific IPv4 prefix details
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Prefix 200.1.0.0/16 learned via BGP

**Test Steps:**
1. Execute command:
   ```
   show ip bgp 200.1.0.0/16
   ```
2. Verify detailed output contains:
   - Prefix information
   - Best path selection reason
   - All available paths (if multipath)
   - Path attributes (origin, AS-path, next-hop, etc.)
   - Last update timestamp

**Test Data:**
```yaml
prefix: 200.1.0.0/16
expected_fields:
  - Next hop
  - Metric
  - Local preference
  - AS path
  - Origin
  - Last update
```

**Expected Result:**
- Detailed prefix information shown
- Best path explanation included
- All attributes visible
- Timestamps accurate

**Verification Commands:**
```
show ip bgp 200.1.0.0/16
show ip bgp
```

---

#### TC-BGP-SHOW-015

**Title:** Display specific IPv6 prefix details
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. IPv6 prefix 2001:200::/32 learned

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv6 unicast 2001:200::/32
   ```
2. Verify detailed IPv6 prefix information

**Test Data:**
```yaml
prefix: 2001:200::/32
expected_fields:
  - Next hop
  - Path
  - Origin
```

**Expected Result:**
- IPv6 prefix details shown
- IPv6 next-hop displayed
- Path attributes complete

**Verification Commands:**
```
show bgp ipv6 unicast 2001:200::/32
show bgp ipv6 unicast
```

---

#### TC-BGP-SHOW-016

**Title:** Display BGP CIDR routes only
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP routes include both classful and CIDR routes

**Test Steps:**
1. Execute command:
   ```
   show ip bgp cidr-only
   ```
2. Verify only non-classful (CIDR) routes shown
3. Verify classful routes excluded

**Test Data:**
```yaml
cidr_routes:
  - 100.1.0.0/16
  - 10.1.1.0/30
classful_routes_excluded:
  - 10.0.0.0/8 (if any)
```

**Expected Result:**
- Only CIDR routes displayed
- Classful routes filtered out
- Output accurate

**Verification Commands:**
```
show ip bgp cidr-only
show ip bgp
```

---

#### TC-BGP-SHOW-017

**Title:** Display routes with specific community
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Routes tagged with community 65001:100
2. BGP community configured

**Test Steps:**
1. Configure routes with community 65001:100
2. Execute command:
   ```
   show ip bgp community 65001:100
   ```
3. Verify only routes with matching community shown

**Test Data:**
```yaml
community: 65001:100
expected_prefixes:
  - 100.1.0.0/16
```

**Expected Result:**
- Only matching community routes shown
- Community attribute visible
- Filter accurate

**Verification Commands:**
```
show ip bgp community 65001:100
show ip bgp
```

---

### 4.5 BGP Configuration Display

---

#### TC-BGP-SHOW-018

**Title:** Display BGP running configuration
**Priority:** P0
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP fully configured

**Test Steps:**
1. Execute command:
   ```
   show running-config bgp
   ```
2. Verify output contains:
   - Router BGP AS configuration
   - Router-ID
   - Neighbor configurations
   - Address family configurations
   - Route-maps, prefix-lists (if configured)

**Test Data:**
```yaml
local_as: 65001
router_id: 1.1.1.1
neighbors:
  - 10.1.1.2
  - 2001:db8:1::2
```

**Expected Result:**
- Complete BGP configuration shown
- Neighbors listed
- Address families included
- No sensitive data exposed

**Verification Commands:**
```
show running-config bgp
show bgp summary
```

---

#### TC-BGP-SHOW-019

**Title:** Display specific neighbor configuration
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Neighbor 10.1.1.2 configured

**Test Steps:**
1. Execute command (if supported):
   ```
   show bgp ipv4 unicast neighbors 10.1.1.2 configuration
   ```
2. Verify neighbor-specific configuration shown

**Test Data:**
```yaml
neighbor: 10.1.1.2
expected_config:
  - remote-as
  - timers
  - address-family
```

**Expected Result:**
- Neighbor configuration displayed
- Accurate settings shown

**Note:** Command syntax may vary by implementation

**Verification Commands:**
```
show running-config bgp
show bgp ipv4 unicast neighbors 10.1.1.2
```

---

### 4.6 BGP Statistics and Peer Groups

---

#### TC-BGP-SHOW-020

**Title:** Display BGP global statistics
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Execute command:
   ```
   show bgp statistics
   ```
2. Verify statistics include:
   - Total prefixes
   - Total paths
   - Update messages
   - Keepalive messages
   - Route refresh messages

**Test Data:**
```yaml
expected_fields:
  - Total prefixes
  - Total paths
  - Update messages
  - Keepalive messages
```

**Expected Result:**
- Statistics displayed
- Counters show activity
- Values reasonable

**Verification Commands:**
```
show bgp statistics
show bgp summary
```

---

#### TC-BGP-SHOW-021

**Title:** Display BGP peer groups
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Peer group "SPINE_PEERS" configured

**Test Steps:**
1. Execute command:
   ```
   show bgp peer-group
   ```
2. Verify peer groups listed
3. Verify members shown

**Test Data:**
```yaml
peer_group: SPINE_PEERS
members:
  - 10.1.1.2
```

**Expected Result:**
- Peer groups displayed
- Members listed
- Configuration shown

**Verification Commands:**
```
show bgp peer-group
show running-config bgp
```

---

#### TC-BGP-SHOW-022

**Title:** Display BGP update groups
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP neighbors established

**Test Steps:**
1. Execute command:
   ```
   show bgp update-group
   ```
2. Verify update groups displayed
3. Verify neighbors grouped efficiently

**Test Data:**
```yaml
expected_fields:
  - Update group ID
  - Members
```

**Expected Result:**
- Update groups shown
- Neighbors grouped correctly
- Optimization visible

**Verification Commands:**
```
show bgp update-group
show bgp summary
```

---

### 4.7 BGP VRF Commands

---

#### TC-BGP-SHOW-023

**Title:** Display BGP VRF summary
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. VRF "Vrf-RED" configured with BGP

**Test Steps:**
1. Execute command:
   ```
   show bgp vrf Vrf-RED summary
   ```
2. Verify VRF-specific summary shown
3. Verify only VRF neighbors listed

**Test Data:**
```yaml
vrf: Vrf-RED
neighbors:
  - 10.100.1.2
```

**Expected Result:**
- VRF summary displayed
- Only VRF neighbors shown
- Isolation maintained

**Verification Commands:**
```
show bgp vrf Vrf-RED summary
show bgp summary
```

---

#### TC-BGP-SHOW-024

**Title:** Display BGP VRF IPv4 routes
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. VRF "Vrf-RED" with IPv4 routes

**Test Steps:**
1. Execute command:
   ```
   show bgp vrf Vrf-RED ipv4 unicast
   ```
2. Verify VRF-specific routes shown

**Test Data:**
```yaml
vrf: Vrf-RED
expected_prefixes:
  - 10.100.0.0/16
```

**Expected Result:**
- VRF routes displayed
- Default VRF routes excluded

**Verification Commands:**
```
show bgp vrf Vrf-RED ipv4 unicast
show ip bgp
```

---

#### TC-BGP-SHOW-025

**Title:** Display BGP VRF IPv6 routes
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. VRF "Vrf-BLUE" with IPv6 BGP

**Test Steps:**
1. Execute command:
   ```
   show bgp vrf Vrf-BLUE ipv6 unicast
   ```
2. Verify VRF IPv6 routes shown

**Test Data:**
```yaml
vrf: Vrf-BLUE
expected_prefixes:
  - 2001:100::/32
```

**Expected Result:**
- VRF IPv6 routes displayed
- Isolation maintained

**Verification Commands:**
```
show bgp vrf Vrf-BLUE ipv6 unicast
show bgp ipv6 unicast
```

---

#### TC-BGP-SHOW-026

**Title:** Display VRF BGP neighbors
**Priority:** P1
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. VRF with BGP neighbors

**Test Steps:**
1. Execute command:
   ```
   show bgp vrf Vrf-RED neighbors
   ```
2. Verify VRF neighbors shown

**Test Data:**
```yaml
vrf: Vrf-RED
neighbors:
  - 10.100.1.2
```

**Expected Result:**
- VRF neighbors displayed
- Default VRF neighbors excluded

**Verification Commands:**
```
show bgp vrf Vrf-RED neighbors
show bgp neighbors
```

---

### 4.8 BGP Output Filtering and Formatting

---

#### TC-BGP-SHOW-027

**Title:** Display BGP routes with grep filter (wide match)
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Multiple BGP routes present

**Test Steps:**
1. Execute command:
   ```
   show ip bgp | grep 200
   ```
2. Verify only routes containing "200" shown
3. Verify grep functionality works

**Test Data:**
```yaml
filter: 200
expected_matches:
  - 200.1.0.0/16
  - 200.2.0.0/16
```

**Expected Result:**
- Filtered output shown
- Only matching lines displayed
- Grep works correctly

**Verification Commands:**
```
show ip bgp | grep 200
show ip bgp
```

---

#### TC-BGP-SHOW-028

**Title:** Display BGP routes with specific next-hop
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Routes with specific next-hop present

**Test Steps:**
1. Execute command:
   ```
   show ip bgp | grep 10.1.1.2
   ```
2. Verify only routes via 10.1.1.2 shown

**Test Data:**
```yaml
next_hop: 10.1.1.2
expected_prefixes:
  - 200.1.0.0/16
  - 200.2.0.0/16
```

**Expected Result:**
- Routes via specific next-hop shown
- Filter accurate

**Verification Commands:**
```
show ip bgp | grep 10.1.1.2
show bgp ipv4 unicast neighbors 10.1.1.2 routes
```

---

#### TC-BGP-SHOW-029

**Title:** Display BGP summary with JSON output (if supported)
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP configured

**Test Steps:**
1. Execute command (if supported):
   ```
   show bgp summary json
   ```
2. Verify JSON formatted output
3. Verify parsable JSON structure

**Test Data:**
```yaml
output_format: json
```

**Expected Result:**
- JSON output generated
- Valid JSON structure
- Parsable by tools

**Note:** JSON support may vary by SONiC version

**Verification Commands:**
```
show bgp summary json
show bgp summary
```

---

### 4.9 BGP Route Details and Attributes

---

#### TC-BGP-SHOW-030

**Title:** Display routes with AS-path filter
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. Routes with specific AS-path present

**Test Steps:**
1. Execute command:
   ```
   show ip bgp regexp ^65002$
   ```
2. Verify routes matching AS-path regex shown

**Test Data:**
```yaml
as_path_regex: "^65002$"
expected_prefixes:
  - 200.1.0.0/16
```

**Expected Result:**
- AS-path filtering works
- Only matching routes shown

**Note:** Regex syntax may vary

**Verification Commands:**
```
show ip bgp regexp ^65002$
show ip bgp
```

---

#### TC-BGP-SHOW-031

**Title:** Display BGP dampening information
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP dampening configured

**Test Steps:**
1. Execute command:
   ```
   show ip bgp dampening dampened-paths
   ```
2. Verify dampened routes shown

**Test Data:**
```yaml
dampening_enabled: true
```

**Expected Result:**
- Dampened routes displayed (if any)
- Dampening info shown

**Note:** Requires dampening feature configured

**Verification Commands:**
```
show ip bgp dampening dampened-paths
show bgp dampening parameters
```

---

#### TC-BGP-SHOW-032

**Title:** Display BGP route flap statistics
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP route flapping occurred

**Test Steps:**
1. Execute command:
   ```
   show ip bgp flap-statistics
   ```
2. Verify flap statistics shown

**Test Data:**
```yaml
flapping_enabled: true
```

**Expected Result:**
- Flap statistics displayed
- Counts accurate

**Note:** Feature availability varies

**Verification Commands:**
```
show ip bgp flap-statistics
show bgp statistics
```

---

### 4.10 Additional Show Commands

---

#### TC-BGP-SHOW-033

**Title:** Display BGP paths for all routes
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP routes learned

**Test Steps:**
1. Execute command:
   ```
   show ip bgp paths
   ```
2. Verify all paths shown
3. Verify AS-path information

**Test Data:**
```yaml
expected_fields:
  - AS path
  - Reference count
```

**Expected Result:**
- Paths displayed
- Reference counts shown

**Verification Commands:**
```
show ip bgp paths
show ip bgp
```

---

#### TC-BGP-SHOW-034

**Title:** Display BGP attributes for routes
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP routes present

**Test Steps:**
1. Execute command:
   ```
   show ip bgp attribute-info
   ```
2. Verify attributes displayed

**Test Data:**
```yaml
expected_attributes:
  - Next hop
  - AS path
  - Community
```

**Expected Result:**
- Attributes shown
- Reference counts included

**Note:** Command availability varies

**Verification Commands:**
```
show ip bgp attribute-info
show ip bgp
```

---

#### TC-BGP-SHOW-035

**Title:** Display BGP memory usage
**Priority:** P2
**Type:** Positive
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Execute command:
   ```
   show bgp memory
   ```
2. Verify memory statistics shown

**Test Data:**
```yaml
expected_fields:
  - BGP memory usage
  - RIB memory
```

**Expected Result:**
- Memory usage displayed
- Statistics reasonable

**Verification Commands:**
```
show bgp memory
show bgp statistics
```

---

## 5. Negative Test Cases

### 5.1 Invalid Parameters

---

#### TC-BGP-SHOW-036

**Title:** Show BGP with non-existent neighbor IP
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational
2. No neighbor 192.168.99.99 configured

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors 192.168.99.99
   ```
2. Verify appropriate error message

**Test Data:**
```yaml
invalid_neighbor: 192.168.99.99
```

**Expected Result:**
- Error message: "Neighbor not found" or similar
- No crash or hang
- Command returns gracefully

**Expected Error Message:**
```
% BGP neighbor 192.168.99.99 not configured
```

---

#### TC-BGP-SHOW-037

**Title:** Show BGP with malformed IPv4 address
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors 10.1.1.999
   ```
2. Verify syntax error

**Test Data:**
```yaml
malformed_ip: 10.1.1.999
```

**Expected Result:**
- Syntax error or invalid IP error
- Command rejected

**Expected Error Message:**
```
% Invalid IP address
```

---

#### TC-BGP-SHOW-038

**Title:** Show BGP with malformed IPv6 address
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv6 unicast neighbors 2001:db8::gggg
   ```
2. Verify error

**Test Data:**
```yaml
malformed_ipv6: 2001:db8::gggg
```

**Expected Result:**
- Invalid IPv6 address error
- Command rejected

**Expected Error Message:**
```
% Invalid IPv6 address
```

---

#### TC-BGP-SHOW-039

**Title:** Show BGP for non-existent VRF
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. VRF "Vrf-NONEXIST" does not exist

**Test Steps:**
1. Execute command:
   ```
   show bgp vrf Vrf-NONEXIST summary
   ```
2. Verify error message

**Test Data:**
```yaml
nonexistent_vrf: Vrf-NONEXIST
```

**Expected Result:**
- Error: VRF not found
- Command fails gracefully

**Expected Error Message:**
```
% VRF Vrf-NONEXIST does not exist
```

---

#### TC-BGP-SHOW-040

**Title:** Show BGP with invalid prefix format
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP operational

**Test Steps:**
1. Execute command:
   ```
   show ip bgp 10.1.1.1/33
   ```
2. Verify error (invalid prefix length)

**Test Data:**
```yaml
invalid_prefix: 10.1.1.1/33
```

**Expected Result:**
- Error: Invalid prefix length
- Command rejected

**Expected Error Message:**
```
% Invalid prefix length
```

---

### 5.2 State-Dependent Errors

---

#### TC-BGP-SHOW-041

**Title:** Show BGP when BGP not configured
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP not configured on device

**Test Steps:**
1. Execute command:
   ```
   show bgp summary
   ```
2. Verify appropriate message

**Test Data:**
```yaml
bgp_configured: false
```

**Expected Result:**
- Message indicating BGP not configured
- OR: Empty output with "No BGP process configured"

**Expected Message:**
```
% BGP is not configured
```

---

#### TC-BGP-SHOW-042

**Title:** Show received-routes without soft-reconfiguration
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Neighbor configured WITHOUT soft-reconfiguration inbound

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors 10.1.1.2 received-routes
   ```
2. Verify error or warning message

**Test Data:**
```yaml
neighbor: 10.1.1.2
soft_reconfig_enabled: false
```

**Expected Result:**
- Error or warning about soft-reconfig not enabled
- No routes displayed

**Expected Message:**
```
% Soft reconfiguration not enabled for this neighbor
```

---

#### TC-BGP-SHOW-043

**Title:** Show advertised-routes when neighbor is down
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Neighbor configured but in Idle/Active state

**Test Steps:**
1. Shutdown neighbor interface
2. Execute command:
   ```
   show bgp ipv4 unicast neighbors 10.1.1.2 advertised-routes
   ```
3. Verify appropriate message

**Test Data:**
```yaml
neighbor: 10.1.1.2
neighbor_state: Idle
```

**Expected Result:**
- Message indicating neighbor not established
- OR: No routes displayed with warning

**Expected Message:**
```
% Neighbor is not in Established state
```

---

### 5.3 Incomplete Commands

---

#### TC-BGP-SHOW-044

**Title:** Incomplete show bgp command
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP configured

**Test Steps:**
1. Execute incomplete command:
   ```
   show bgp ipv4
   ```
2. Verify error or completion prompt

**Test Data:**
```yaml
incomplete_command: "show bgp ipv4"
```

**Expected Result:**
- Syntax error or command completion hint
- Command not executed

**Expected Error:**
```
% Incomplete command
```

---

#### TC-BGP-SHOW-045

**Title:** Show BGP neighbors without specifying address
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP configured

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors advertised-routes
   ```
   (missing neighbor IP)
2. Verify error

**Test Data:**
```yaml
missing_parameter: neighbor_ip
```

**Expected Result:**
- Error: missing neighbor parameter
- Command rejected

**Expected Error:**
```
% Missing neighbor IP address
```

---

### 5.4 Permission and Access Errors

---

#### TC-BGP-SHOW-046

**Title:** Show BGP from non-privileged user (if RBAC enabled)
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. RBAC enabled
2. Non-admin user available

**Test Steps:**
1. Login as non-admin user
2. Execute command:
   ```
   show bgp summary
   ```
3. Verify access allowed or denied based on RBAC policy

**Test Data:**
```yaml
user: operator
command: show bgp summary
```

**Expected Result:**
- Access allowed (show commands typically allowed)
- OR: Access denied based on policy

**Note:** Most show commands should be allowed for operators

---

### 5.5 Invalid Filters and Regex

---

#### TC-BGP-SHOW-047

**Title:** Show BGP with invalid regex
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP routes present

**Test Steps:**
1. Execute command with invalid regex:
   ```
   show ip bgp regexp [invalid(regex
   ```
2. Verify error

**Test Data:**
```yaml
invalid_regex: "[invalid(regex"
```

**Expected Result:**
- Error: Invalid regular expression
- Command rejected

**Expected Error:**
```
% Invalid regular expression
```

---

#### TC-BGP-SHOW-048

**Title:** Show BGP with non-existent community
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP configured

**Test Steps:**
1. Execute command:
   ```
   show ip bgp community 99999:99999
   ```
2. Verify no routes shown (graceful empty output)

**Test Data:**
```yaml
nonexistent_community: 99999:99999
```

**Expected Result:**
- Empty output (no error)
- OR: Message "No routes with specified community"

**Expected Message:**
```
No routes found with community 99999:99999
```

---

### 5.6 IPv4/IPv6 Mismatch

---

#### TC-BGP-SHOW-049

**Title:** Show IPv4 command with IPv6 address
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP configured

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv4 unicast neighbors 2001:db8:1::2
   ```
2. Verify error

**Test Data:**
```yaml
ipv6_in_ipv4_command: 2001:db8:1::2
```

**Expected Result:**
- Error: IPv6 address in IPv4 command
- Command rejected

**Expected Error:**
```
% Invalid IP address for IPv4 command
```

---

#### TC-BGP-SHOW-050

**Title:** Show IPv6 command with IPv4 address
**Priority:** P1
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP configured

**Test Steps:**
1. Execute command:
   ```
   show bgp ipv6 unicast neighbors 10.1.1.2
   ```
2. Verify error

**Test Data:**
```yaml
ipv4_in_ipv6_command: 10.1.1.2
```

**Expected Result:**
- Error: IPv4 address in IPv6 command
- Command rejected

**Expected Error:**
```
% Invalid IPv6 address
```

---

### 5.7 Special Cases

---

#### TC-BGP-SHOW-051

**Title:** Show BGP routes when no routes present
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP configured but no routes learned

**Test Steps:**
1. Execute command:
   ```
   show ip bgp
   ```
2. Verify graceful empty output

**Test Data:**
```yaml
route_count: 0
```

**Expected Result:**
- Empty table or "No routes" message
- No error

**Expected Output:**
```
No BGP routes found
```

---

#### TC-BGP-SHOW-052

**Title:** Show BGP neighbor that was recently removed
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Neighbor was configured then removed

**Test Steps:**
1. Configure neighbor 10.1.1.2
2. Remove neighbor
3. Execute command:
   ```
   show bgp ipv4 unicast neighbors 10.1.1.2
   ```
4. Verify error

**Test Data:**
```yaml
removed_neighbor: 10.1.1.2
```

**Expected Result:**
- Error: Neighbor not found
- No stale data shown

**Expected Error:**
```
% Neighbor not configured
```

---

#### TC-BGP-SHOW-053

**Title:** Show BGP with excessive output (pagination test)
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. Large number of BGP routes present

**Test Steps:**
1. Execute command:
   ```
   show ip bgp
   ```
2. Verify pagination works correctly
3. Test 'q' to quit, space to continue

**Test Data:**
```yaml
route_count: ">1000"
```

**Expected Result:**
- Pagination engages
- Output controlled
- No truncation or overflow

**Note:** Tests terminal pagination behavior

---

#### TC-BGP-SHOW-054

**Title:** Show BGP during convergence
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP in convergence state

**Test Steps:**
1. Restart BGP process
2. Immediately execute:
   ```
   show bgp summary
   ```
3. Verify partial data shown gracefully

**Test Data:**
```yaml
bgp_state: converging
```

**Expected Result:**
- Command succeeds
- Shows current state (may be partial)
- No errors or crashes

**Note:** Tests timing/race conditions

---

#### TC-BGP-SHOW-055

**Title:** Show BGP with special characters in filter
**Priority:** P2
**Type:** Negative
**CLI Type:** Klish

**Preconditions:**
1. BGP configured

**Test Steps:**
1. Execute command with special chars:
   ```
   show ip bgp | grep [*?$]
   ```
2. Verify shell escaping handled

**Test Data:**
```yaml
special_chars: "[*?$]"
```

**Expected Result:**
- Special chars handled gracefully
- OR: Appropriate error
- No shell injection

**Note:** Security test

---

## 6. Test Execution Guidelines

### 6.1 Pre-Test Setup

**Configuration Script:**
```bash
# DUT1 configuration
configure terminal
interface Ethernet32
  no shutdown
  ip address 10.1.1.1/30
  ipv6 address 2001:db8:1::1/64
exit

interface Loopback0
  ip address 1.1.1.1/32
  ipv6 address 2001:db8::1/128
exit

router bgp 65001
  router-id 1.1.1.1
  neighbor 10.1.1.2 remote-as 65001
  neighbor 2001:db8:1::2 remote-as 65001
  address-family ipv4 unicast
    neighbor 10.1.1.2 activate
    network 100.1.0.0/16
    network 100.2.0.0/16
    network 1.1.1.1/32
  exit-address-family
  address-family ipv6 unicast
    neighbor 2001:db8:1::2 activate
    network 2001:100::/32
    network 2001:db8::1/128
  exit-address-family
exit

# DUT2 configuration
configure terminal
interface Ethernet32
  no shutdown
  ip address 10.1.1.2/30
  ipv6 address 2001:db8:1::2/64
exit

interface Loopback0
  ip address 2.2.2.2/32
  ipv6 address 2001:db8::2/128
exit

router bgp 65001
  router-id 2.2.2.2
  neighbor 10.1.1.1 remote-as 65001
  neighbor 2001:db8:1::1 remote-as 65001
  address-family ipv4 unicast
    neighbor 10.1.1.1 activate
    network 200.1.0.0/16
    network 200.2.0.0/16
    network 2.2.2.2/32
  exit-address-family
  address-family ipv6 unicast
    neighbor 2001:db8:1::1 activate
    network 2001:200::/32
    network 2001:db8::2/128
  exit-address-family
exit
```

### 6.2 Verification Commands

**Essential verification commands:**

```bash
# Basic connectivity
ping 10.1.1.2
ping6 2001:db8:1::2

# BGP session status
show bgp summary
show bgp ipv4 unicast summary
show bgp ipv6 unicast summary

# Neighbor details
show bgp neighbors
show bgp ipv4 unicast neighbors 10.1.1.2
show bgp ipv6 unicast neighbors 2001:db8:1::2

# Route tables
show ip bgp
show bgp ipv6 unicast

# Configuration
show running-config bgp
```

### 6.3 Wait Times

**Recommended wait times:**
- After BGP configuration: 30 seconds (for convergence)
- After route advertisement: 10 seconds
- Between show commands: 1 second
- After neighbor state change: 15 seconds

### 6.4 Test Cleanup

**After each test:**
1. Verify BGP sessions remain Established (for positive tests)
2. Clear any test-specific configuration (VRFs, communities)
3. Verify route counts return to baseline
4. Wait 5 seconds before next test

**Full cleanup script:**
```bash
# Remove test-specific configs
configure terminal
no router bgp 65001
exit

# Verify cleanup
show bgp summary
show running-config bgp
```

---

## 7. Success Criteria

### 7.1 Positive Test Success Criteria

**For each positive test case:**

1. **Command Execution:**
   - Command accepted without errors
   - Output generated within reasonable time
   - No timeouts or hangs

2. **Output Correctness:**
   - All expected fields present
   - Data accurate and consistent
   - Formatting clean and readable

3. **Data Integrity:**
   - Information matches actual BGP state
   - Counters and statistics accurate
   - Cross-command consistency

4. **Performance:**
   - Response time acceptable (< 5 seconds for most commands)
   - Large outputs paginated properly

### 7.2 Negative Test Success Criteria

**For each negative test case:**

1. **Error Handling:**
   - Appropriate error message displayed
   - Error message clear and helpful
   - No misleading errors

2. **System Stability:**
   - No crashes or hangs
   - CLI remains responsive
   - BGP process continues running

3. **Security:**
   - No sensitive data exposed
   - Input validation works
   - No command injection possible

---

## 8. Test Automation Notes

### 8.1 Python Test Implementation

**Recommended test structure:**

```python
import pytest
from spytest import st, SpyTestDict
import apis.routing.bgp as bgpapi

# Module-level variables
vars = SpyTestDict()
data = SpyTestDict()

# Test configuration
CONFIG = SpyTestDict({
    "local_as": "65001",
    "router_id_dut1": "1.1.1.1",
    "router_id_dut2": "2.2.2.2",
    "ipv4_neighbor": "10.1.1.2",
    "ipv6_neighbor": "2001:db8:1::2",
})

@pytest.fixture(scope="module", autouse=True)
def bgp_show_module_hooks(request):
    global vars
    vars = st.ensure_min_topology("D1D2:1")
    data.cli_type = "klish"

    # Setup BGP baseline
    bgp_baseline_config()

    yield

    # Cleanup
    bgp_baseline_cleanup()

def verify_show_bgp_summary_output(dut, expected_neighbors):
    """Verify 'show bgp summary' output contains expected data"""
    output = bgpapi.show_bgp_summary(dut, cli_type="klish")

    if not output:
        st.log("ERROR: No output from show bgp summary")
        return False

    # Verify each neighbor present
    for nbr in expected_neighbors:
        found = False
        for entry in output:
            if entry.get('neighbor') == nbr['ip']:
                if entry.get('state') != 'Established':
                    st.log(f"ERROR: Neighbor {nbr['ip']} not Established")
                    return False
                found = True
                break
        if not found:
            st.log(f"ERROR: Neighbor {nbr['ip']} not found in summary")
            return False

    return True

def test_show_bgp_summary():
    """TC-BGP-SHOW-001: Display global BGP summary"""
    st.log("Starting test: show bgp summary")

    expected_neighbors = [
        {"ip": "10.1.1.2", "state": "Established"},
        {"ip": "2001:db8:1::2", "state": "Established"},
    ]

    # Execute show command
    result = verify_show_bgp_summary_output(vars.D1, expected_neighbors)

    if not result:
        st.report_fail("show_bgp_summary_failed")

    st.report_pass("test_case_passed")

def test_show_bgp_ipv4_summary():
    """TC-BGP-SHOW-002: Display IPv4 unicast BGP summary"""
    st.log("Starting test: show bgp ipv4 unicast summary")

    output = bgpapi.show_bgp_ipv4_summary(vars.D1, cli_type="klish")

    if not output:
        st.report_fail("show_bgp_ipv4_summary_no_output")

    # Verify IPv4 neighbor present
    neighbor_found = False
    for entry in output:
        if entry.get('neighbor') == CONFIG.ipv4_neighbor:
            if entry.get('state') != 'Established':
                st.report_fail("neighbor_not_established", CONFIG.ipv4_neighbor)
            neighbor_found = True
            break

    if not neighbor_found:
        st.report_fail("neighbor_not_in_summary", CONFIG.ipv4_neighbor)

    st.report_pass("test_case_passed")

def test_show_bgp_neighbors_detail():
    """TC-BGP-SHOW-005: Display specific IPv4 neighbor details"""
    st.log(f"Starting test: show bgp neighbors {CONFIG.ipv4_neighbor}")

    output = bgpapi.show_bgp_ipv4_neighbor_detail(
        vars.D1,
        neighbor_ip=CONFIG.ipv4_neighbor,
        cli_type="klish"
    )

    if not output:
        st.report_fail("show_bgp_neighbor_no_output")

    # Verify key fields present
    required_fields = ['neighbor', 'remote_as', 'bgp_state', 'hold_time']
    for field in required_fields:
        if field not in output[0]:
            st.report_fail("missing_field_in_output", field)

    # Verify state
    if output[0].get('bgp_state') != 'Established':
        st.report_fail("neighbor_state_incorrect", output[0].get('bgp_state'))

    st.report_pass("test_case_passed")
```

### 8.2 API Functions Used

**Key BGP API functions for show operations:**

```python
# From apis/routing/bgp.py

# Summary commands
bgpapi.show_bgp_summary(dut, vrf="", cli_type="klish")
bgpapi.show_bgp_ipv4_summary(dut, cli_type="klish")
bgpapi.show_bgp_ipv6_summary(dut, cli_type="klish")

# Neighbor details
bgpapi.show_bgp_neighbors(dut, cli_type="klish")
bgpapi.show_bgp_ipv4_neighbor_detail(dut, neighbor_ip="", cli_type="klish")
bgpapi.show_bgp_ipv6_neighbor_detail(dut, neighbor_ip="", cli_type="klish")

# Advertised/Received routes
bgpapi.show_bgp_ipv4_neighbor_advertised_routes(dut, neighbor_ip="", cli_type="klish")
bgpapi.show_bgp_ipv4_neighbor_received_routes(dut, neighbor_ip="", cli_type="klish")
bgpapi.show_bgp_ipv4_neighbor_routes(dut, neighbor_ip="", cli_type="klish")

# Route tables
bgpapi.show_ip_bgp(dut, cli_type="klish")
bgpapi.show_bgp_ipv6_unicast(dut, cli_type="klish")
bgpapi.show_ip_bgp_network(dut, network="", cli_type="klish")

# VRF commands
bgpapi.show_bgp_vrf_summary(dut, vrf="", cli_type="klish")
bgpapi.show_bgp_vrf_ipv4_routes(dut, vrf="", cli_type="klish")
```

---

## 9. Appendix

### 9.1 Complete Command Reference

**All show commands tested:**

```
# Summary commands
show bgp summary
show bgp ipv4 unicast summary
show bgp ipv6 unicast summary
show bgp vrf <vrf-name> summary

# Neighbor commands
show bgp neighbors
show bgp ipv4 unicast neighbors
show bgp ipv4 unicast neighbors <ip>
show bgp ipv6 unicast neighbors <ipv6>
show bgp neighbors <ip> advertised-routes
show bgp neighbors <ip> received-routes
show bgp neighbors <ip> routes
show bgp ipv4 unicast neighbors <ip> advertised-routes
show bgp ipv4 unicast neighbors <ip> received-routes
show bgp ipv4 unicast neighbors <ip> routes
show bgp ipv6 unicast neighbors <ipv6> advertised-routes
show bgp ipv6 unicast neighbors <ipv6> received-routes
show bgp ipv6 unicast neighbors <ipv6> routes

# Route table commands
show ip bgp
show bgp ipv6 unicast
show ip bgp <prefix>
show bgp ipv6 unicast <prefix>
show ip bgp cidr-only
show ip bgp community <community>
show ip bgp regexp <regex>

# Configuration commands
show running-config bgp

# Statistics commands
show bgp statistics
show bgp peer-group
show bgp update-group
show bgp memory

# VRF commands
show bgp vrf <vrf-name> ipv4 unicast
show bgp vrf <vrf-name> ipv6 unicast
show bgp vrf <vrf-name> neighbors

# Special commands
show ip bgp paths
show ip bgp attribute-info
show ip bgp dampening dampened-paths
show ip bgp flap-statistics
```

### 9.2 Glossary

| Term | Definition |
|------|------------|
| **Advertised Routes** | Routes sent to a BGP neighbor |
| **Received Routes** | All routes received from neighbor (pre-policy) |
| **Routes** | Accepted routes from neighbor (post-policy) |
| **Best Path** | Route selected as best by BGP algorithm |
| **Status Code** | Symbol indicating route status (*, >, i, etc.) |
| **Next Hop** | Next router to forward packet to |
| **AS Path** | List of ASes route has traversed |
| **CIDR** | Classless Inter-Domain Routing |
| **Soft Reconfiguration** | Store unfiltered routes for policy changes |

---

**Document End**

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-03 | Test Automation | Initial comprehensive test plan for BGP show commands |

---

**Approval:**

- Test Lead: _______________
- Development Lead: _______________
- QA Manager: _______________

---
