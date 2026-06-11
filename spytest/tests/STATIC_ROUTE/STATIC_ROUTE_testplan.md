# Static Route Test Plan

## Table of Contents
1. [Overview](#overview)
2. [Test Environment](#test-environment)
3. [Topology](#topology)
4. [Test Objectives](#test-objectives)
5. [Test Summary](#test-summary)
6. [Test Cases](#test-cases)
   - [6.1 Basic Functionality](#61-basic-functionality)
   - [6.2 IPv6 Functionality](#62-ipv6-functionality)
   - [6.3 VRF Integration](#63-vrf-integration)
   - [6.4 Interface Integration](#64-interface-integration)
   - [6.5 Route Priority and Selection](#65-route-priority-and-selection)
   - [6.6 Negative Test Cases](#66-negative-test-cases)
   - [6.7 Scaling Test Cases](#67-scaling-test-cases)
   - [6.8 CLI and Configuration Validation](#68-cli-and-configuration-validation)
   - [6.9 Reboot and Persistence](#69-reboot-and-persistence)
7. [Test Execution Guidelines](#test-execution-guidelines)

---

## 1. Overview

This test plan covers comprehensive validation of Static Route functionality in SONiC Network Operating System. Static routes are manually configured routes that define explicit paths for network traffic. This plan validates IPv4/IPv6 static routes, next-hop configurations, route metrics, VRF integration, blackhole routes, and various edge cases.

**Feature**: Static Routing
**Component**: FRRouting (FRR) / Zebra
**CLI Types**: Click, Klish, REST API, gNMI

---

## 2. Test Environment

### Hardware/Software Requirements:
- **Topology**: 3-node linear topology (DEV-A ↔ DEV-B ↔ DEV-C)
- **DUT**: DEV-B (Device Under Test) running SONiC
- **Peer Devices**: DEV-A and DEV-C running SONiC-VS
- **Traffic Generator**: Scapy (running on same system as SONiC-VS)
- **Connection**: 2 ports between each device pair
- **SONiC Version**: Any supported version
- **Test Framework**: SPyTest

### Configuration Prerequisites:
- All devices have IP connectivity established
- Management interfaces configured
- Base network configuration applied
- No conflicting routing protocols enabled

---

## 3. Topology

### 3.1 Physical Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Test System (Host Machine)                       │
│                                                                           │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐    │
│  │   DEV-A      │         │   DEV-B      │         │   DEV-C      │    │
│  │ (SONiC-VS)   │◄───────►│   (DUT)      │◄───────►│ (SONiC-VS)   │    │
│  │              │         │              │         │              │    │
│  │  Scapy       │         │ SONiC Device │         │  Scapy       │    │
│  │  Traffic Gen │         │              │         │  Traffic Gen │    │
│  └──────────────┘         └──────────────┘         └──────────────┘    │
│         │                        │                         │             │
│      Eth0/1,2                 Eth0/1,2,3,4              Eth0/1,2        │
│         │                        │                         │             │
│         └────────────────────────┴─────────────────────────┘            │
│                      Virtual Network Bridges                             │
└─────────────────────────────────────────────────────────────────────────┘

Legend:
  DEV-A: Source device (SONiC-VS with Scapy)
  DEV-B: Device Under Test (DUT) - SONiC device
  DEV-C: Destination device (SONiC-VS with Scapy)
  ◄───►: Dual port connections (2 links between each pair)
```

### 3.2 Connection Details

| Link | DEV-A Port | DEV-B Port | Purpose |
|------|------------|------------|---------|
| Link-1 | Ethernet0 | Ethernet0 | Primary connection A-B |
| Link-2 | Ethernet4 | Ethernet4 | Secondary connection A-B |
| Link-3 | - | Ethernet8 | Primary connection B-C (DEV-B side) |
| Link-4 | - | Ethernet12 | Secondary connection B-C (DEV-B side) |
| Link-5 | Ethernet8 (DEV-C) | - | Primary connection B-C (DEV-C side) |
| Link-6 | Ethernet12 (DEV-C) | - | Secondary connection B-C (DEV-C side) |

### 3.3 IP Addressing Scheme

#### IPv4 Network Plan:
- **Network A-B Primary**: 10.1.1.0/24
  - DEV-A: 10.1.1.1/24
  - DEV-B: 10.1.1.2/24
- **Network A-B Secondary**: 10.1.2.0/24
  - DEV-A: 10.1.2.1/24
  - DEV-B: 10.1.2.2/24
- **Network B-C Primary**: 10.2.1.0/24
  - DEV-B: 10.2.1.1/24
  - DEV-C: 10.2.1.2/24
- **Network B-C Secondary**: 10.2.2.0/24
  - DEV-B: 10.2.2.1/24
  - DEV-C: 10.2.2.2/24
- **Test Networks**: 192.168.0.0/16, 172.16.0.0/12

#### IPv6 Network Plan:
- **Network A-B Primary**: 2001:1:1::/64
  - DEV-A: 2001:1:1::1/64
  - DEV-B: 2001:1:1::2/64
- **Network A-B Secondary**: 2001:1:2::/64
  - DEV-A: 2001:1:2::1/64
  - DEV-B: 2001:1:2::2/64
- **Network B-C Primary**: 2001:2:1::/64
  - DEV-B: 2001:2:1::1/64
  - DEV-C: 2001:2:1::2/64
- **Network B-C Secondary**: 2001:2:2::/64
  - DEV-B: 2001:2:2::1/64
  - DEV-C: 2001:2:2::2/64

---

## 4. Test Objectives

1. **Validate basic static route configuration and forwarding**
   - Add, modify, and delete static routes
   - Verify route installation in routing table and FIB
   - Test packet forwarding through static routes

2. **Test IPv4 and IPv6 static route functionality**
   - IPv4 static routes with various prefix lengths
   - IPv6 static routes with various prefix lengths
   - Mixed IPv4/IPv6 routing scenarios

3. **Validate next-hop variations**
   - Next-hop IP address
   - Next-hop interface
   - Next-hop IP + interface combination
   - Null0/blackhole routes

4. **Test route metrics and administrative distance**
   - Configure routes with different metrics
   - Test route preference based on administrative distance
   - Verify route selection with equal-cost multi-path (ECMP)

5. **Validate VRF integration**
   - Static routes in non-default VRFs
   - Route leaking between VRFs
   - VRF-aware forwarding

6. **Test interface state interaction**
   - Route behavior when next-hop interface goes down
   - Route recovery when interface comes back up
   - Track next-hop reachability

7. **Validate negative scenarios**
   - Invalid configurations
   - Routing loops
   - Unreachable next-hops
   - Configuration conflicts

8. **Test scaling limits**
   - Maximum number of static routes
   - Multiple next-hops per route
   - Large number of routes per VRF

9. **Validate persistence and recovery**
   - Configuration persistence across reboots
   - Warm reboot behavior
   - Fast reboot behavior
   - Configuration rollback

10. **Test multi-CLI support**
    - Configuration via Click CLI
    - Configuration via Klish CLI
    - Configuration via REST API
    - Configuration via gNMI

---

## 5. Test Summary

### Test Case Count by Category

| Category | Test Cases | Description |
|----------|------------|-------------|
| Basic Functionality (IPv4) | 15 | Core IPv4 static route operations |
| IPv6 Functionality | 12 | Core IPv6 static route operations |
| VRF Integration | 10 | Static routes with VRF |
| Interface Integration | 8 | Interface state and route interaction |
| Route Priority/Selection | 8 | Metrics, admin distance, ECMP |
| Negative Scenarios | 15 | Invalid configs, edge cases |
| Scaling Scenarios | 8 | Performance and limits |
| CLI/Config Validation | 8 | Multi-CLI and config management |
| Reboot/Persistence | 6 | Persistence across reboots |
| **Total** | **90** | **Complete test coverage** |

### Test Execution Time Estimate
- **Setup Time**: 10 minutes
- **Per Test Case**: 2-5 minutes average
- **Total Estimated Time**: 5-8 hours (depending on hardware)

---

## 6. Test Cases

### 6.1 Basic Functionality (IPv4)

#### TC_STATIC_ROUTE_BASIC_001: Add IPv4 Static Route with Next-Hop IP
**Objective**: Verify basic IPv4 static route configuration with next-hop IP address

**Test Procedure**:
1. Configure static route on DEV-B: `ip route 192.168.10.0/24 10.2.1.2`
2. Verify configuration in running-config: `show running-config | grep "ip route"`
3. Verify route in routing table: `show ip route 192.168.10.0/24`
4. Verify route in FIB: `show ip fib 192.168.10.0/24`
5. Send test packet from DEV-A (src: 10.1.1.1, dst: 192.168.10.100)
6. Capture packet on DEV-C and verify reception
7. Verify packet forwarding statistics

**Expected Result**:
- Route appears in running-config
- Route installed in routing table with protocol "S" (static)
- Route programmed in hardware FIB
- Packets forwarded successfully from DEV-A to DEV-C
- No packet loss

**CLI Commands** (Klish):
```
configure terminal
ip route 192.168.10.0/24 10.2.1.2
exit
show running-config | grep "ip route"
show ip route 192.168.10.0/24
```

**CLI Commands** (Click):
```
config route add prefix 192.168.10.0/24 nexthop 10.2.1.2
show runningconfig route
show ip route 192.168.10.0/24
```

---

#### TC_STATIC_ROUTE_BASIC_002: Add IPv4 Static Route with Next-Hop Interface
**Objective**: Verify IPv4 static route configuration with next-hop interface

**Test Procedure**:
1. Configure static route: `ip route 192.168.20.0/24 Ethernet8`
2. Verify configuration appears in running-config
3. Verify route in routing table with interface as next-hop
4. Send test packet from DEV-A to 192.168.20.100
5. Verify packet egresses through Ethernet8
6. Capture and verify packet on DEV-C

**Expected Result**:
- Route configured with interface-only next-hop
- Route installed with directly connected interface
- ARP resolution occurs on egress interface
- Packets forwarded successfully

---

#### TC_STATIC_ROUTE_BASIC_003: Add IPv4 Static Route with Next-Hop IP and Interface
**Objective**: Verify static route with both next-hop IP and interface specified

**Test Procedure**:
1. Configure: `ip route 192.168.30.0/24 Ethernet8 10.2.1.2`
2. Verify configuration in running-config
3. Verify route shows both interface and IP in routing table
4. Send test traffic and verify forwarding
5. Test failover behavior if interface goes down

**Expected Result**:
- Route installed with both IP and interface
- More specific next-hop resolution
- Proper forwarding behavior

---

#### TC_STATIC_ROUTE_BASIC_004: Delete IPv4 Static Route
**Objective**: Verify static route removal and cleanup

**Test Procedure**:
1. Add static route: `ip route 192.168.40.0/24 10.2.1.2`
2. Verify route installation
3. Delete route: `no ip route 192.168.40.0/24 10.2.1.2`
4. Verify route removed from running-config
5. Verify route removed from routing table and FIB
6. Send test packet and verify it's dropped (no route)

**Expected Result**:
- Route successfully removed from all tables
- No residual configuration
- Packets dropped due to missing route

---

#### TC_STATIC_ROUTE_BASIC_005: Modify IPv4 Static Route Next-Hop
**Objective**: Verify changing next-hop of existing static route

**Test Procedure**:
1. Configure: `ip route 192.168.50.0/24 10.2.1.2`
2. Verify forwarding through primary path
3. Modify route: Delete old, add new with different next-hop
4. Configure: `ip route 192.168.50.0/24 10.2.2.2`
5. Verify route updated in routing table
6. Verify traffic now forwards through new next-hop

**Expected Result**:
- Route modification successful
- Traffic switches to new path
- No packet loss during transition (if properly sequenced)

---

#### TC_STATIC_ROUTE_BASIC_006: Add Multiple Static Routes
**Objective**: Verify configuration of multiple distinct static routes

**Test Procedure**:
1. Configure 5 different static routes:
   - `ip route 192.168.60.0/24 10.2.1.2`
   - `ip route 192.168.61.0/24 10.2.1.2`
   - `ip route 192.168.62.0/24 10.2.1.2`
   - `ip route 192.168.63.0/24 10.2.1.2`
   - `ip route 192.168.64.0/24 10.2.1.2`
2. Verify all routes in running-config
3. Verify all routes in routing table
4. Test forwarding for each destination network
5. Verify independent operation of each route

**Expected Result**:
- All routes configured and installed
- Each route operates independently
- All destinations reachable

---

#### TC_STATIC_ROUTE_BASIC_007: Static Route with /32 Host Route
**Objective**: Verify host-specific static route

**Test Procedure**:
1. Configure: `ip route 192.168.70.100/32 10.2.1.2`
2. Verify host route in routing table
3. Send packet to 192.168.70.100 - should be forwarded
4. Send packet to 192.168.70.101 - should be dropped
5. Verify route specificity

**Expected Result**:
- Host route installed correctly
- Only exact IP match forwarded
- Other IPs in same /24 not affected

---

#### TC_STATIC_ROUTE_BASIC_008: Static Route with Default Route (0.0.0.0/0)
**Objective**: Verify default route configuration

**Test Procedure**:
1. Remove all existing static routes
2. Configure: `ip route 0.0.0.0/0 10.2.1.2`
3. Verify default route in routing table
4. Send packets to various unknown destinations
5. Verify all packets use default route

**Expected Result**:
- Default route becomes catch-all for unmatched traffic
- All unknown destinations forward via default route

---

#### TC_STATIC_ROUTE_BASIC_009: Static Route with Various Prefix Lengths
**Objective**: Test routes with different subnet masks

**Test Procedure**:
1. Configure routes with different masks:
   - `ip route 172.16.0.0/12 10.2.1.2` (/12)
   - `ip route 172.20.0.0/16 10.2.1.2` (/16)
   - `ip route 172.20.10.0/24 10.2.1.2` (/24)
   - `ip route 172.20.10.50/32 10.2.1.2` (/32)
2. Verify longest prefix match behavior
3. Send packets to 172.20.10.50 - should use /32 route
4. Send packets to 172.20.10.100 - should use /24 route
5. Send packets to 172.20.20.1 - should use /16 route
6. Send packets to 172.17.1.1 - should use /12 route

**Expected Result**:
- Routes with different masks coexist
- Longest prefix match algorithm works correctly
- Most specific route always preferred

---

#### TC_STATIC_ROUTE_BASIC_010: Static Route Replaces Connected Route
**Objective**: Verify static route can override connected route

**Test Procedure**:
1. Verify connected route exists for directly connected network
2. Configure static route with better metric for same prefix
3. Verify static route installed (may not override connected)
4. Test which route is actually used for forwarding
5. Delete static route and verify connected route active again

**Expected Result**:
- Behavior depends on administrative distance
- Connected routes typically preferred (AD=0)
- Static routes (AD=1) may not override connected

---

#### TC_STATIC_ROUTE_BASIC_011: Blackhole Route (Null0)
**Objective**: Verify blackhole/null route functionality

**Test Procedure**:
1. Configure: `ip route 192.168.80.0/24 Null0`
2. Verify route installed with Null0 interface
3. Send packets to 192.168.80.100
4. Verify packets are silently dropped (blackholed)
5. Verify no ICMP errors generated
6. Check interface statistics on Null0

**Expected Result**:
- Packets matching route are dropped
- No forwarding occurs
- No ICMP destination unreachable sent
- Useful for preventing routing loops or filtering

---

#### TC_STATIC_ROUTE_BASIC_012: Static Route Forwarding Statistics
**Objective**: Verify packet and byte counters for static routes

**Test Procedure**:
1. Configure static route: `ip route 192.168.90.0/24 10.2.1.2`
2. Clear interface statistics
3. Send 100 packets (1500 bytes each) to 192.168.90.100
4. Verify routing statistics increment
5. Check interface counters on egress interface
6. Verify packet/byte counts match expected values

**Expected Result**:
- Forwarding statistics accurately tracked
- Counters increment per packet/byte
- Interface statistics consistent with routing stats

---

#### TC_STATIC_ROUTE_BASIC_013: Multiple Next-Hops (ECMP) for Same Prefix
**Objective**: Verify equal-cost multi-path static routing

**Test Procedure**:
1. Configure multiple next-hops for same destination:
   - `ip route 192.168.100.0/24 10.2.1.2`
   - `ip route 192.168.100.0/24 10.2.2.2`
2. Verify both routes appear in routing table
3. Send multiple flows to destination
4. Verify traffic load-balanced across both paths
5. Check per-flow hashing behavior

**Expected Result**:
- Both next-hops installed (ECMP group)
- Traffic distributed across paths
- Per-flow consistency maintained (same flow uses same path)

---

#### TC_STATIC_ROUTE_BASIC_014: Static Route via Gateway Not in Same Subnet
**Objective**: Test recursive route resolution

**Test Procedure**:
1. Configure: `ip route 192.168.110.0/24 10.3.3.1` (next-hop not directly connected)
2. Verify route in routing table shows "via" next-hop
3. Verify recursive lookup to find actual egress interface
4. Send traffic and verify proper forwarding
5. If next-hop becomes unreachable, verify route marked as inactive

**Expected Result**:
- Recursive next-hop resolution works
- Route only active if next-hop is reachable
- Proper route withdrawal if next-hop unreachable

---

#### TC_STATIC_ROUTE_BASIC_015: Static Route Configuration Persistence
**Objective**: Verify static route config saved and reloaded

**Test Procedure**:
1. Configure static route: `ip route 192.168.120.0/24 10.2.1.2`
2. Save configuration: `write memory`
3. Verify route in startup-config
4. Reload device: `reload`
5. After reload, verify route still present
6. Test forwarding to verify route is active

**Expected Result**:
- Configuration persists across reloads
- Route automatically restored after reboot
- No manual intervention needed

---

### 6.2 IPv6 Functionality

#### TC_STATIC_ROUTE_IPV6_001: Add IPv6 Static Route with Next-Hop IP
**Objective**: Verify basic IPv6 static route configuration

**Test Procedure**:
1. Configure: `ipv6 route 2001:db8:100::/64 2001:2:1::2`
2. Verify configuration in running-config
3. Verify route in IPv6 routing table: `show ipv6 route`
4. Send ICMPv6 echo request from DEV-A to 2001:db8:100::100
5. Verify packet forwarded to DEV-C
6. Check IPv6 neighbor discovery (NDP) on next-hop

**Expected Result**:
- IPv6 route installed correctly
- NDP resolution for next-hop successful
- IPv6 packets forwarded properly

**CLI Commands**:
```
configure terminal
ipv6 route 2001:db8:100::/64 2001:2:1::2
show running-config | grep "ipv6 route"
show ipv6 route 2001:db8:100::/64
```

---

#### TC_STATIC_ROUTE_IPV6_002: Add IPv6 Static Route with Next-Hop Interface
**Objective**: Verify IPv6 route with interface-only next-hop

**Test Procedure**:
1. Configure: `ipv6 route 2001:db8:200::/64 Ethernet8`
2. Verify route shows interface as next-hop
3. Send IPv6 packet to destination
4. Verify link-local neighbor discovery occurs
5. Confirm packet forwarding

**Expected Result**:
- Interface-based IPv6 forwarding works
- NDP uses link-local addresses for next-hop

---

#### TC_STATIC_ROUTE_IPV6_003: IPv6 Route with Link-Local Next-Hop
**Objective**: Test IPv6 route using link-local address as next-hop

**Test Procedure**:
1. Discover link-local address of DEV-C on Ethernet8: `fe80::xxx`
2. Configure: `ipv6 route 2001:db8:300::/64 Ethernet8 fe80::xxx`
3. Verify route installation
4. Test IPv6 packet forwarding
5. Verify NDP cache entries

**Expected Result**:
- Link-local next-hop resolution works
- Packets forwarded using link-local addressing

---

#### TC_STATIC_ROUTE_IPV6_004: Delete IPv6 Static Route
**Objective**: Verify IPv6 route deletion

**Test Procedure**:
1. Add IPv6 route: `ipv6 route 2001:db8:400::/64 2001:2:1::2`
2. Verify route installation
3. Delete route: `no ipv6 route 2001:db8:400::/64 2001:2:1::2`
4. Verify removal from routing table
5. Send packet and verify it's dropped

**Expected Result**:
- Route cleanly removed
- No IPv6 connectivity to destination

---

#### TC_STATIC_ROUTE_IPV6_005: IPv6 Host Route (/128)
**Objective**: Verify IPv6 /128 host route

**Test Procedure**:
1. Configure: `ipv6 route 2001:db8:500::100/128 2001:2:1::2`
2. Verify host route in table
3. Send packet to 2001:db8:500::100 - forwarded
4. Send packet to 2001:db8:500::101 - dropped
5. Verify route specificity

**Expected Result**:
- Host-specific IPv6 route works
- Only exact address match forwarded

---

#### TC_STATIC_ROUTE_IPV6_006: IPv6 Default Route (::/0)
**Objective**: Verify IPv6 default route

**Test Procedure**:
1. Configure: `ipv6 route ::/0 2001:2:1::2`
2. Verify default route in IPv6 table
3. Send packets to various IPv6 destinations
4. Verify all use default route

**Expected Result**:
- Default route catches all unmatched IPv6 traffic

---

#### TC_STATIC_ROUTE_IPV6_007: Multiple IPv6 Next-Hops (ECMP)
**Objective**: Verify IPv6 ECMP static routing

**Test Procedure**:
1. Configure:
   - `ipv6 route 2001:db8:600::/64 2001:2:1::2`
   - `ipv6 route 2001:db8:600::/64 2001:2:2::2`
2. Verify both paths in routing table
3. Send multiple IPv6 flows
4. Verify load balancing

**Expected Result**:
- IPv6 ECMP functions correctly
- Traffic distributed across paths

---

#### TC_STATIC_ROUTE_IPV6_008: IPv6 Blackhole Route
**Objective**: Test IPv6 null route

**Test Procedure**:
1. Configure: `ipv6 route 2001:db8:700::/64 Null0`
2. Send packets to destination
3. Verify packets silently dropped
4. Verify no ICMPv6 errors

**Expected Result**:
- IPv6 blackhole route works
- Packets dropped without notification

---

#### TC_STATIC_ROUTE_IPV6_009: IPv6 Route Various Prefix Lengths
**Objective**: Test IPv6 longest prefix match

**Test Procedure**:
1. Configure routes:
   - `ipv6 route 2001:db8::/32 2001:2:1::2`
   - `ipv6 route 2001:db8:800::/48 2001:2:1::2`
   - `ipv6 route 2001:db8:800::/64 2001:2:1::2`
   - `ipv6 route 2001:db8:800::100/128 2001:2:1::2`
2. Test packets to each prefix
3. Verify longest match selection

**Expected Result**:
- Most specific IPv6 route always used

---

#### TC_STATIC_ROUTE_IPV6_010: IPv6 Route with Interface + Address
**Objective**: Test IPv6 route with both interface and next-hop IP

**Test Procedure**:
1. Configure: `ipv6 route 2001:db8:900::/64 Ethernet8 2001:2:1::2`
2. Verify route shows both
3. Test forwarding behavior
4. Compare with interface-only configuration

**Expected Result**:
- More explicit next-hop specification works

---

#### TC_STATIC_ROUTE_IPV6_011: Mixed IPv4 and IPv6 Static Routes
**Objective**: Verify coexistence of IPv4 and IPv6 static routes

**Test Procedure**:
1. Configure both IPv4 and IPv6 routes
2. Verify separate routing tables maintained
3. Send both IPv4 and IPv6 traffic
4. Verify independent forwarding

**Expected Result**:
- Dual-stack static routing works
- No interference between protocols

---

#### TC_STATIC_ROUTE_IPV6_012: IPv6 Route Persistence
**Objective**: Verify IPv6 route config persistence

**Test Procedure**:
1. Configure IPv6 static routes
2. Save config and reload
3. Verify routes restored
4. Test forwarding after reload

**Expected Result**:
- IPv6 routes persist across reboots

---

### 6.3 VRF Integration

#### TC_STATIC_ROUTE_VRF_001: Static Route in Non-Default VRF
**Objective**: Verify static route configuration in VRF

**Test Procedure**:
1. Create VRF: `ip vrf VRF-RED`
2. Bind interface to VRF: `interface Ethernet8` → `ip vrf forwarding VRF-RED`
3. Configure route in VRF: `ip route vrf VRF-RED 192.168.200.0/24 10.2.1.2`
4. Verify route in VRF routing table: `show ip route vrf VRF-RED`
5. Send packet in VRF context and verify forwarding

**Expected Result**:
- VRF-aware static routing works
- Routes isolated per VRF
- Forwarding respects VRF boundaries

---

#### TC_STATIC_ROUTE_VRF_002: Static Routes in Multiple VRFs
**Objective**: Test static routes across multiple VRFs

**Test Procedure**:
1. Create VRF-RED and VRF-BLUE
2. Configure same destination in both VRFs with different next-hops
3. Verify isolation between VRF routing tables
4. Test forwarding in each VRF independently

**Expected Result**:
- Multiple VRFs operate independently
- Same prefix in different VRFs doesn't conflict

---

#### TC_STATIC_ROUTE_VRF_003: Static Route Leaking Between VRFs
**Objective**: Verify route import/export between VRFs

**Test Procedure**:
1. Configure route in VRF-RED
2. Configure route-target export/import
3. Verify route appears in VRF-BLUE
4. Test inter-VRF forwarding

**Expected Result**:
- Route leaking works as configured
- Proper route-target filtering

---

#### TC_STATIC_ROUTE_VRF_004: Delete VRF with Static Routes
**Objective**: Test cleanup when VRF is deleted

**Test Procedure**:
1. Create VRF and add static routes
2. Delete VRF
3. Verify all routes removed
4. Verify no orphaned routes

**Expected Result**:
- VRF deletion cleans up all associated routes

---

#### TC_STATIC_ROUTE_VRF_005: Management VRF Static Routes
**Objective**: Test static routes in management VRF

**Test Procedure**:
1. Configure route in mgmt VRF
2. Verify management traffic uses route
3. Verify isolation from data plane

**Expected Result**:
- Management VRF routing isolated

---

#### TC_STATIC_ROUTE_VRF_006: VRF Static Route Next-Hop Resolution
**Objective**: Verify next-hop must be in same VRF

**Test Procedure**:
1. Configure route in VRF-RED with next-hop in VRF-BLUE
2. Verify route not installed (invalid config)
3. Configure correct same-VRF next-hop
4. Verify route installs

**Expected Result**:
- Cross-VRF next-hops rejected
- Proper validation enforced

---

#### TC_STATIC_ROUTE_VRF_007: IPv6 Static Routes in VRF
**Objective**: Test IPv6 static routing with VRF

**Test Procedure**:
1. Configure IPv6 route in VRF
2. Verify installation in VRF IPv6 table
3. Test IPv6 forwarding in VRF context

**Expected Result**:
- IPv6 VRF static routes work

---

#### TC_STATIC_ROUTE_VRF_008: VRF Route with Default Route
**Objective**: Test default route in VRF

**Test Procedure**:
1. Configure: `ip route vrf VRF-RED 0.0.0.0/0 10.2.1.2`
2. Verify VRF default route
3. Test catch-all behavior in VRF

**Expected Result**:
- Per-VRF default routes work independently

---

#### TC_STATIC_ROUTE_VRF_009: VRF Static Route Persistence
**Objective**: Verify VRF routes persist across reboot

**Test Procedure**:
1. Configure VRF with static routes
2. Save and reload
3. Verify VRF and routes restored

**Expected Result**:
- VRF configuration and routes persist

---

#### TC_STATIC_ROUTE_VRF_010: VRF Interface Down Impact on Static Routes
**Objective**: Test route behavior when VRF interface fails

**Test Procedure**:
1. Configure VRF route via interface
2. Shutdown interface
3. Verify route marked inactive
4. Bring interface up
5. Verify route active again

**Expected Result**:
- VRF routes track interface state

---

### 6.4 Interface Integration

#### TC_STATIC_ROUTE_INTF_001: Static Route Next-Hop Interface Goes Down
**Objective**: Verify route withdrawal when interface fails

**Test Procedure**:
1. Configure: `ip route 192.168.150.0/24 Ethernet8`
2. Verify route active and forwarding works
3. Shutdown Ethernet8: `config interface shutdown Ethernet8`
4. Verify route marked as inactive in routing table
5. Verify packets to destination are dropped
6. Check routing protocol events/logs

**Expected Result**:
- Route automatically withdrawn when interface down
- Traffic stops forwarding
- Route marked inactive but remains in config

---

#### TC_STATIC_ROUTE_INTF_002: Static Route Recovery After Interface Comes Up
**Objective**: Verify automatic route restoration

**Test Procedure**:
1. Start with interface down and inactive route
2. Bring interface up: `config interface startup Ethernet8`
3. Verify route becomes active
4. Verify forwarding resumes
5. Check convergence time

**Expected Result**:
- Route automatically re-installed when interface up
- Fast convergence (< 1 second)
- Forwarding restored

---

#### TC_STATIC_ROUTE_INTF_003: Static Route with Next-Hop IP - Interface Down
**Objective**: Test IP-based next-hop when interface fails

**Test Procedure**:
1. Configure: `ip route 192.168.160.0/24 10.2.1.2`
2. Verify route active
3. Shutdown interface to next-hop
4. Verify route becomes inactive (next-hop unreachable)
5. Bring interface up
6. Verify route active again

**Expected Result**:
- Route tracks reachability of IP next-hop
- Route withdrawn if next-hop unreachable

---

#### TC_STATIC_ROUTE_INTF_004: Interface Flap Behavior
**Objective**: Test route stability during interface flapping

**Test Procedure**:
1. Configure static route via interface
2. Rapidly flap interface (down/up) 10 times
3. Verify route stability
4. Check for route flapping in logs
5. Verify final state is correct

**Expected Result**:
- Route follows interface state
- No route installation errors
- System remains stable

---

#### TC_STATIC_ROUTE_INTF_005: LAG Interface Static Route
**Objective**: Test static route via PortChannel

**Test Procedure**:
1. Create PortChannel: `config portchannel add PortChannel1`
2. Add members to PortChannel
3. Configure: `ip route 192.168.170.0/24 PortChannel1`
4. Verify route installation
5. Test forwarding via LAG
6. Remove LAG member and verify forwarding continues

**Expected Result**:
- Static routes work with LAG interfaces
- LAG member changes don't affect route

---

#### TC_STATIC_ROUTE_INTF_006: VLAN Interface Static Route
**Objective**: Test static route via VLAN interface

**Test Procedure**:
1. Create VLAN interface: `config vlan add 100`
2. Configure IP on VLAN interface
3. Configure: `ip route 192.168.180.0/24 Vlan100`
4. Verify route installation
5. Test L3 forwarding via VLAN interface

**Expected Result**:
- Static routes via VLAN interfaces work

---

#### TC_STATIC_ROUTE_INTF_007: Loopback Interface Static Route
**Objective**: Test static route via loopback

**Test Procedure**:
1. Create loopback: `config loopback add Loopback0`
2. Configure IP on loopback
3. Test static route with loopback as next-hop
4. Verify route behavior

**Expected Result**:
- Loopback-based static routes work (if supported)

---

#### TC_STATIC_ROUTE_INTF_008: Interface Speed/MTU Change Impact
**Objective**: Verify static routes unaffected by interface parameter changes

**Test Procedure**:
1. Configure static route via interface
2. Change interface speed
3. Change interface MTU
4. Verify route remains active
5. Verify forwarding continues

**Expected Result**:
- Interface parameter changes don't affect route
- Forwarding continues normally

---

### 6.5 Route Priority and Selection

#### TC_STATIC_ROUTE_PRIO_001: Static Route with Metric/Distance
**Objective**: Test administrative distance configuration

**Test Procedure**:
1. Configure: `ip route 192.168.190.0/24 10.2.1.2 distance 50`
2. Configure: `ip route 192.168.190.0/24 10.2.2.2 distance 100`
3. Verify route with distance 50 is active
4. Delete primary route
5. Verify route with distance 100 becomes active

**Expected Result**:
- Lower distance preferred
- Automatic failover to backup route

---

#### TC_STATIC_ROUTE_PRIO_002: Equal-Cost Multi-Path (ECMP)
**Objective**: Test load balancing across equal-cost paths

**Test Procedure**:
1. Configure multiple routes with same distance:
   - `ip route 192.168.200.0/24 10.2.1.2`
   - `ip route 192.168.200.0/24 10.2.2.2`
2. Verify both routes installed
3. Send 1000 packets with different 5-tuple
4. Verify traffic distributed across both paths
5. Check load distribution ratio

**Expected Result**:
- Load balanced across paths (roughly 50/50)
- Per-flow consistency maintained

---

#### TC_STATIC_ROUTE_PRIO_003: Floating Static Route (Backup)
**Objective**: Test backup route with higher distance

**Test Procedure**:
1. Configure primary dynamic route (e.g., BGP)
2. Configure floating static: `ip route 192.168.210.0/24 10.2.1.2 distance 250`
3. Verify static not used (higher distance than BGP)
4. Remove BGP route
5. Verify static route becomes active

**Expected Result**:
- Floating static only used when primary fails

---

#### TC_STATIC_ROUTE_PRIO_004: Maximum ECMP Paths
**Objective**: Test ECMP path limit

**Test Procedure**:
1. Configure maximum supported ECMP paths (e.g., 64)
2. Verify all paths installed
3. Test load distribution
4. Add one more path beyond limit
5. Verify behavior (rejected or replaces existing)

**Expected Result**:
- System respects maximum ECMP limit
- Proper handling of exceeding limit

---

#### TC_STATIC_ROUTE_PRIO_005: Route Preference - Static vs Connected
**Objective**: Test route selection between static and connected

**Test Procedure**:
1. Configure IP on interface (creates connected route)
2. Configure static route for same prefix
3. Verify which route is active (connected should win, AD=0 < AD=1)
4. Test forwarding behavior

**Expected Result**:
- Connected routes preferred over static
- Administrative distance hierarchy respected

---

#### TC_STATIC_ROUTE_PRIO_006: Route Preference - Static vs Dynamic (BGP)
**Objective**: Compare static and BGP route selection

**Test Procedure**:
1. Configure static route (AD=1)
2. Configure BGP route for same prefix (AD=20 for eBGP)
3. Verify static route active
4. Increase static distance to 30
5. Verify BGP route becomes active

**Expected Result**:
- Lower AD always wins
- Proper route selection based on protocol preferences

---

#### TC_STATIC_ROUTE_PRIO_007: ECMP with Different Metrics
**Objective**: Test that unequal metrics prevent ECMP

**Test Procedure**:
1. Configure:
   - `ip route 192.168.220.0/24 10.2.1.2 distance 50`
   - `ip route 192.168.220.0/24 10.2.2.2 distance 60`
2. Verify only route with distance 50 is active
3. Verify no load balancing occurs

**Expected Result**:
- Only lowest distance route installed
- No ECMP with different distances

---

#### TC_STATIC_ROUTE_PRIO_008: Tag-Based Route Filtering
**Objective**: Test route tagging and filtering (if supported)

**Test Procedure**:
1. Configure route with tag: `ip route 192.168.230.0/24 10.2.1.2 tag 100`
2. Verify tag appears in routing table
3. Configure route-map to filter based on tag
4. Verify tag-based policy application

**Expected Result**:
- Route tags work for policy application

---

### 6.6 Negative Test Cases

#### TC_STATIC_ROUTE_NEG_001: Invalid Next-Hop IP Address
**Objective**: Test error handling for invalid next-hop

**Test Procedure**:
1. Attempt to configure: `ip route 192.168.240.0/24 999.999.999.999`
2. Verify command rejected with error
3. Verify no route installed
4. Verify system stability

**Expected Result**:
- Invalid IP address rejected
- Appropriate error message
- No system crash or instability

---

#### TC_STATIC_ROUTE_NEG_002: Invalid Prefix Format
**Objective**: Test error handling for malformed prefix

**Test Procedure**:
1. Attempt to configure invalid prefixes:
   - `ip route 192.168.0.0/33 10.2.1.2` (invalid mask)
   - `ip route 192.168.300.0/24 10.2.1.2` (invalid octet)
   - `ip route 192.168.0 10.2.1.2` (incomplete address)
2. Verify all rejected with errors
3. Verify no partial configuration

**Expected Result**:
- All invalid formats rejected
- Clear error messages
- No routes installed

---

#### TC_STATIC_ROUTE_NEG_003: Non-Existent Interface as Next-Hop
**Objective**: Test using invalid interface

**Test Procedure**:
1. Attempt: `ip route 192.168.250.0/24 Ethernet9999`
2. Verify command rejected or route installed as inactive
3. Check error handling

**Expected Result**:
- Route rejected or marked inactive
- Error message about invalid interface

---

#### TC_STATIC_ROUTE_NEG_004: Routing Loop Creation
**Objective**: Test loop detection and prevention

**Test Procedure**:
1. On DEV-B: `ip route 192.168.0.0/16 10.1.1.1`
2. On DEV-A: `ip route 192.168.0.0/16 10.1.1.2`
3. Send packet to 192.168.1.1 from DEV-A
4. Verify loop detection (TTL expiry)
5. Monitor for system instability

**Expected Result**:
- Packet loops until TTL=0
- ICMP time exceeded generated
- System remains stable

---

#### TC_STATIC_ROUTE_NEG_005: Maximum Routes Exceeded
**Objective**: Test behavior at routing table limits

**Test Procedure**:
1. Determine maximum static route limit
2. Configure maximum number of routes
3. Attempt to add one more route
4. Verify behavior (rejected or oldest removed)
5. Check system performance under load

**Expected Result**:
- Limit enforced gracefully
- System remains stable
- Clear indication of limit reached

---

#### TC_STATIC_ROUTE_NEG_006: Unreachable Next-Hop
**Objective**: Test route with permanently unreachable next-hop

**Test Procedure**:
1. Configure: `ip route 192.168.255.0/24 10.99.99.99` (no route to next-hop)
2. Verify route installed but marked inactive
3. Send packet to destination
4. Verify packet dropped
5. Check routing protocol events

**Expected Result**:
- Route marked inactive due to unreachable next-hop
- Periodic reachability checks occur

---

#### TC_STATIC_ROUTE_NEG_007: Delete Non-Existent Route
**Objective**: Test deletion of non-configured route

**Test Procedure**:
1. Attempt: `no ip route 192.168.99.0/24 10.2.1.2` (route doesn't exist)
2. Verify error handling
3. Verify system stability

**Expected Result**:
- Error message indicating route not found
- No system impact

---

#### TC_STATIC_ROUTE_NEG_008: Conflicting Configuration Sequence
**Objective**: Test race conditions in configuration

**Test Procedure**:
1. Rapidly add and delete same route multiple times
2. Simultaneously configure same route from multiple sessions
3. Verify final state is consistent
4. Check for any leaked resources

**Expected Result**:
- System handles rapid changes gracefully
- Final state is deterministic
- No resource leaks

---

#### TC_STATIC_ROUTE_NEG_009: Route with Source Address (Invalid)
**Objective**: Test rejection of source-specific routing (if not supported)

**Test Procedure**:
1. Attempt: `ip route 192.168.1.0/24 from 10.1.1.0/24 via 10.2.1.2`
2. Verify command rejected (if feature not supported)

**Expected Result**:
- Invalid syntax rejected
- Policy routing requires different commands

---

#### TC_STATIC_ROUTE_NEG_010: IPv4 Route with IPv6 Next-Hop
**Objective**: Test rejection of mixed protocol configuration

**Test Procedure**:
1. Attempt: `ip route 192.168.1.0/24 2001:db8::1`
2. Verify command rejected
3. Verify proper error message

**Expected Result**:
- IPv4/IPv6 mixing rejected
- Clear error about protocol mismatch

---

#### TC_STATIC_ROUTE_NEG_011: IPv6 Route with IPv4 Next-Hop
**Objective**: Test reverse protocol mixing

**Test Procedure**:
1. Attempt: `ipv6 route 2001:db8::/32 10.2.1.2`
2. Verify rejection

**Expected Result**:
- Protocol mixing prevented

---

#### TC_STATIC_ROUTE_NEG_012: Route with Invalid Distance Value
**Objective**: Test administrative distance validation

**Test Procedure**:
1. Attempt: `ip route 192.168.1.0/24 10.2.1.2 distance 256` (out of range 1-255)
2. Verify rejection

**Expected Result**:
- Out-of-range distance rejected

---

#### TC_STATIC_ROUTE_NEG_013: Duplicate Route Configuration
**Objective**: Test handling of duplicate route adds

**Test Procedure**:
1. Configure: `ip route 192.168.1.0/24 10.2.1.2`
2. Configure again: `ip route 192.168.1.0/24 10.2.1.2`
3. Verify handled gracefully (idempotent)

**Expected Result**:
- Duplicate ignored or handled gracefully
- No error or warning acceptable

---

#### TC_STATIC_ROUTE_NEG_014: Configuration During High CPU Load
**Objective**: Test config under stress

**Test Procedure**:
1. Generate high CPU load on system
2. Configure multiple static routes
3. Verify all routes properly installed
4. Verify forwarding works correctly

**Expected Result**:
- Configuration succeeds under load
- All routes function properly

---

#### TC_STATIC_ROUTE_NEG_015: Route with Multicast Destination
**Objective**: Test multicast prefix rejection

**Test Procedure**:
1. Attempt: `ip route 224.0.0.0/4 10.2.1.2`
2. Verify handling (may be rejected or ignored)

**Expected Result**:
- Multicast prefixes handled appropriately
- No system instability

---

### 6.7 Scaling Test Cases

#### TC_STATIC_ROUTE_SCALE_001: Maximum IPv4 Static Routes
**Objective**: Validate system limit for IPv4 static routes

**Test Procedure**:
1. Determine documented maximum (e.g., 4000, 8000, 16000)
2. Configure maximum number of unique static routes
3. Verify all routes installed in routing table
4. Verify all routes programmed in hardware FIB
5. Test forwarding for random sample of destinations
6. Monitor system resource usage (CPU, memory)
7. Measure route installation time

**Expected Result**:
- All routes successfully installed
- FIB programming complete
- Forwarding works for all routes
- Memory usage within limits
- CPU usage acceptable

---

#### TC_STATIC_ROUTE_SCALE_002: Maximum IPv6 Static Routes
**Objective**: Validate IPv6 static route scaling

**Test Procedure**:
1. Configure maximum IPv6 static routes
2. Verify installation and FIB programming
3. Test IPv6 forwarding at scale
4. Monitor resource usage

**Expected Result**:
- IPv6 scaling meets specifications
- System performance acceptable

---

#### TC_STATIC_ROUTE_SCALE_003: Maximum ECMP Next-Hops per Route
**Objective**: Test maximum equal-cost paths

**Test Procedure**:
1. Configure single prefix with maximum ECMP paths (e.g., 64, 128)
2. Verify all next-hops installed
3. Send high-volume traffic
4. Verify load distribution across all paths
5. Check forwarding performance

**Expected Result**:
- All ECMP paths functional
- Even load distribution
- Line-rate forwarding maintained

---

#### TC_STATIC_ROUTE_SCALE_004: Mixed Scale (IPv4 + IPv6 + VRF)
**Objective**: Test combined scaling scenario

**Test Procedure**:
1. Create multiple VRFs (e.g., 10 VRFs)
2. In each VRF, configure:
   - 500 IPv4 static routes
   - 500 IPv6 static routes
3. Verify total routes: 10,000 routes (5000 IPv4 + 5000 IPv6)
4. Test forwarding in all VRFs
5. Monitor system health

**Expected Result**:
- Combined scaling works
- Per-VRF isolation maintained
- System stable

---

#### TC_STATIC_ROUTE_SCALE_005: Route Add/Delete Performance
**Objective**: Measure route manipulation speed

**Test Procedure**:
1. Time adding 1000 routes sequentially
2. Calculate routes/second
3. Time deleting 1000 routes
4. Test bulk configuration via config file
5. Measure convergence time

**Expected Result**:
- Route add: > 100 routes/sec
- Route delete: > 100 routes/sec
- Bulk config faster than sequential

---

#### TC_STATIC_ROUTE_SCALE_006: FIB Capacity Test
**Objective**: Test hardware FIB limits

**Test Procedure**:
1. Configure routes up to hardware FIB limit
2. Verify FIB full condition handling
3. Attempt to add more routes
4. Verify behavior (overflow to software, rejected, etc.)

**Expected Result**:
- FIB limits properly enforced
- Overflow handled gracefully

---

#### TC_STATIC_ROUTE_SCALE_007: Convergence Time at Scale
**Objective**: Measure failover time with many routes

**Test Procedure**:
1. Configure 5000 static routes with primary and backup next-hops
2. Send traffic to all destinations
3. Fail primary next-hop interface
4. Measure time until traffic switches to backup
5. Verify no packet loss during failover

**Expected Result**:
- Convergence time < 1 second
- Minimal packet loss (<1%)

---

#### TC_STATIC_ROUTE_SCALE_008: Long-Term Stability Test
**Objective**: Validate stability over extended period

**Test Procedure**:
1. Configure maximum static routes
2. Run continuous forwarding traffic for 24 hours
3. Monitor for memory leaks
4. Monitor for route disappearances
5. Verify forwarding statistics accuracy

**Expected Result**:
- No memory leaks detected
- All routes remain active
- Zero route flaps
- Consistent forwarding

---

### 6.8 CLI and Configuration Validation

#### TC_STATIC_ROUTE_CLI_001: Configuration via Click CLI
**Objective**: Validate Click CLI configuration commands

**Test Procedure**:
1. Configure routes using Click CLI:
   ```
   config route add prefix 192.168.1.0/24 nexthop 10.2.1.2
   config route add prefix 192.168.2.0/24 nexthop 10.2.1.2 distance 50
   ```
2. Verify routes in routing table
3. Delete via Click CLI:
   ```
   config route del prefix 192.168.1.0/24 nexthop 10.2.1.2
   ```
4. Verify deletion

**Expected Result**:
- Click CLI commands work correctly
- All parameters supported

---

#### TC_STATIC_ROUTE_CLI_002: Configuration via Klish CLI
**Objective**: Validate Klish CLI configuration

**Test Procedure**:
1. Configure routes using Klish CLI:
   ```
   configure terminal
   ip route 192.168.3.0/24 10.2.1.2
   ip route 192.168.4.0/24 10.2.1.2 50
   ```
2. Verify routes installed
3. Delete via Klish:
   ```
   no ip route 192.168.3.0/24 10.2.1.2
   ```

**Expected Result**:
- Klish CLI commands functional
- Syntax matches industry standards

---

#### TC_STATIC_ROUTE_CLI_003: Configuration via REST API
**Objective**: Test REST API for static routes

**Test Procedure**:
1. POST route via REST API
2. GET route to verify
3. PATCH to modify route
4. DELETE to remove route
5. Verify all operations via CLI

**Expected Result**:
- REST API fully functional
- Proper JSON formatting
- Status codes correct

---

#### TC_STATIC_ROUTE_CLI_004: Configuration via gNMI
**Objective**: Test gNMI interface for static routes

**Test Procedure**:
1. Use gNMI Set to add route
2. Use gNMI Get to retrieve route
3. Use gNMI Subscribe to monitor changes
4. Delete via gNMI
5. Verify operations

**Expected Result**:
- gNMI operations successful
- OpenConfig model compliance

---

#### TC_STATIC_ROUTE_CLI_005: Show Commands Validation
**Objective**: Verify all show commands

**Test Procedure**:
1. Test various show commands:
   - `show ip route`
   - `show ip route static`
   - `show ip route 192.168.1.0/24`
   - `show running-config | grep "ip route"`
2. Verify output format and accuracy
3. Test filtering and sorting options

**Expected Result**:
- All show commands work
- Output formatted correctly
- Data accurate

---

#### TC_STATIC_ROUTE_CLI_006: Configuration File Load
**Objective**: Test loading routes from config file

**Test Procedure**:
1. Create config file with static routes
2. Load config: `config load <file>`
3. Verify all routes applied
4. Test incremental config load

**Expected Result**:
- Bulk config load successful
- All routes properly applied

---

#### TC_STATIC_ROUTE_CLI_007: Config Save and Restore
**Objective**: Validate configuration persistence

**Test Procedure**:
1. Configure static routes
2. Save: `config save`
3. Verify in startup config
4. Reload device
5. Verify routes restored

**Expected Result**:
- Config save works
- Routes persist across reboot

---

#### TC_STATIC_ROUTE_CLI_008: CLI Error Messages
**Objective**: Validate error message quality

**Test Procedure**:
1. Execute various invalid commands
2. Verify error messages are clear and actionable
3. Verify no cryptic error codes
4. Test help text availability

**Expected Result**:
- Error messages helpful
- Proper syntax guidance provided

---

### 6.9 Reboot and Persistence

#### TC_STATIC_ROUTE_REBOOT_001: Cold Reboot Persistence
**Objective**: Verify routes survive cold reboot

**Test Procedure**:
1. Configure 100 static routes
2. Save configuration
3. Perform cold reboot: `reboot`
4. After boot, verify all routes restored
5. Test forwarding for sample routes

**Expected Result**:
- All routes restored after cold boot
- Forwarding works immediately

---

#### TC_STATIC_ROUTE_REBOOT_002: Warm Reboot Persistence
**Objective**: Test warm reboot behavior

**Test Procedure**:
1. Configure static routes
2. Perform warm reboot: `reboot -w`
3. Monitor route state during reboot
4. Verify minimal traffic disruption
5. Verify all routes active after reboot

**Expected Result**:
- Routes maintained during warm reboot
- Minimal downtime (< 30 seconds)

---

#### TC_STATIC_ROUTE_REBOOT_003: Fast Reboot Persistence
**Objective**: Test fast reboot with static routes

**Test Procedure**:
1. Configure routes and save
2. Perform fast reboot: `fast-reboot`
3. Monitor forwarding continuity
4. Verify routes active after reboot

**Expected Result**:
- Zero packet loss during fast reboot
- Routes immediately available

---

#### TC_STATIC_ROUTE_REBOOT_004: Config Rollback
**Objective**: Test configuration rollback feature

**Test Procedure**:
1. Save checkpoint: `config checkpoint create`
2. Configure additional routes
3. Rollback: `config checkpoint rollback`
4. Verify only original routes present

**Expected Result**:
- Rollback successfully removes new routes
- Original config restored

---

#### TC_STATIC_ROUTE_REBOOT_005: Unsaved Config Loss
**Objective**: Verify unsaved routes lost on reboot

**Test Procedure**:
1. Configure routes without saving
2. Reboot device
3. Verify routes not restored (expected)
4. Verify startup config unchanged

**Expected Result**:
- Unsaved config properly lost
- Startup config intact

---

#### TC_STATIC_ROUTE_REBOOT_006: Upgrade Persistence
**Objective**: Test routes survive SONiC upgrade

**Test Procedure**:
1. Configure and save routes
2. Perform SONiC image upgrade
3. After upgrade, verify routes present
4. Test forwarding functionality

**Expected Result**:
- Routes survive upgrade
- No manual reconfiguration needed

---

## 7. Test Execution Guidelines

### 7.1 Prerequisites

Before executing tests, ensure:

1. **Testbed Setup**:
   - 3 devices connected per topology diagram
   - All devices have management connectivity
   - Scapy installed on DEV-A and DEV-C
   - SONiC-VS properly configured

2. **Base Configuration**:
   ```bash
   # On each device
   config interface ip add Ethernet0 <IP>/<mask>
   config interface startup Ethernet0
   # Repeat for all required interfaces
   ```

3. **Verification**:
   ```bash
   # Test connectivity between devices
   ping -c 5 <neighbor-ip>
   ```

### 7.2 Test Execution Commands

**Run all tests**:
```bash
cd /home/hp/jitendra/sonic-mgmt/spytest
./bin/spytest --testbed testbeds/testbed_3vs.yaml \
    tests/STATIC_ROUTE/ \
    --logs-path ./logs/static_route_$(date +%F_%H%M%S) \
    --log-level debug
```

**Run specific test category**:
```bash
# Basic functionality only
./bin/spytest --testbed testbeds/testbed_3vs.yaml \
    tests/STATIC_ROUTE/ \
    -k "TC_STATIC_ROUTE_BASIC" \
    --logs-path ./logs/static_route_basic
```

**Run single test**:
```bash
./bin/spytest --testbed testbeds/testbed_3vs.yaml \
    tests/STATIC_ROUTE/test_static_route.py::test_basic_001 \
    --logs-path ./logs/single_test
```

### 7.3 Traffic Generation with Scapy

Example Scapy script for packet generation:

```python
from scapy.all import *

# Create packet
pkt = Ether()/IP(src="10.1.1.1", dst="192.168.10.100")/ICMP()

# Send packet
sendp(pkt, iface="eth0", count=10)

# Capture on receiver
pkts = sniff(iface="eth0", count=10, timeout=10)
```

### 7.4 Verification Methods

**1. Route Table Verification**:
```bash
show ip route static
show ipv6 route static
```

**2. FIB Verification**:
```bash
show ip fib
show ipv6 fib
```

**3. Configuration Verification**:
```bash
show running-config | grep "ip route"
```

**4. Forwarding Verification**:
```bash
# Send ICMP and verify response
ping -c 10 <destination>
```

### 7.5 Result Analysis

After test execution, check:

1. **Test Report**: `<logs-path>/results.html`
2. **Summary**: `<logs-path>/summary.txt`
3. **Device Logs**: `<logs-path>/dlog-D1-*.log`

**Success Criteria**:
- All test cases pass (or expected failures documented)
- No system crashes or hangs
- No memory leaks detected
- Forwarding statistics accurate

### 7.6 Cleanup Procedures

After test completion:

```bash
# Remove all static routes
configure terminal
no ip route 0.0.0.0/0 0.0.0.0
# Repeat for each configured route

# Or use bulk delete
config route flush
```

### 7.7 Known Limitations

- Some platforms may have lower FIB limits
- IPv6 ECMP may have different limits than IPv4
- VRF support varies by SONiC version
- Hardware-specific limitations apply

---

## Document Information

**Document Version**: 1.0
**Created Date**: 2026-03-23
**Last Updated**: 2026-03-23
**Author**: SPyTest Automation Team
**Status**: Ready for Review

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-23 | SPyTest Team | Initial comprehensive test plan |

---

**End of Document**
