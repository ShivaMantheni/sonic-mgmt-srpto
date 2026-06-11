# Static Route Test Plan - Complete Test Case Breakdown

**Document Version:** 1.0  
**Last Updated:** April 2, 2026  
**Total Test Cases:** 90  
**Currently Implemented:** 7 (7.8%)

---

## Table of Contents

1. [Overview](#overview)
2. [Test Coverage Summary](#test-coverage-summary)
3. [Topology Requirements](#topology-requirements)
4. [Test Cases by Category](#test-cases-by-category)
   - [1. Basic Functionality (IPv4)](#1-basic-functionality-ipv4---15-test-cases)
   - [2. IPv6 Functionality](#2-ipv6-functionality---12-test-cases)
   - [3. VRF Integration](#3-vrf-integration---10-test-cases)
   - [4. Interface Integration](#4-interface-integration---8-test-cases)
   - [5. Route Priority and Selection](#5-route-priority-and-selection---8-test-cases)
   - [6. Negative Test Cases](#6-negative-test-cases---15-test-cases)
   - [7. Scaling Test Cases](#7-scaling-test-cases---8-test-cases)
   - [8. CLI and Configuration Validation](#8-cli-and-configuration-validation---8-test-cases)
   - [9. Reboot and Persistence](#9-reboot-and-persistence---6-test-cases)
5. [Implementation Priority](#implementation-priority)
6. [Test Execution Guide](#test-execution-guide)

---

## Overview

This document provides a complete breakdown of all 90 test cases from the Static Route Test Plan. Each test case is categorized by functionality area with implementation status tracking.

**Test Framework:** spytest  
**CLI Modes:** Click, Klish (ISCLI)  
**Traffic Tool:** Scapy  
**Topology:** 3-node linear (DEV-A ↔ DEV-B ↔ DEV-C)

---

## Test Coverage Summary

### Overall Statistics

| Metric | Value |
|--------|-------|
| **Total Test Cases** | 90 |
| **Implemented** | 7 |
| **Missing** | 83 |
| **Coverage** | 7.8% |

### Coverage by Category

| Category | Total | Covered | Missing | Coverage % |
|----------|-------|---------|---------|------------|
| **Basic Functionality (IPv4)** | 15 | 3 | 12 | 20% |
| **IPv6 Functionality** | 12 | 2 | 10 | 17% |
| **VRF Integration** | 10 | 2 | 8 | 20% |
| **Interface Integration** | 8 | 0 | 8 | 0% |
| **Route Priority/Selection** | 8 | 1 | 7 | 13% |
| **Negative Test Cases** | 15 | 0 | 15 | 0% |
| **Scaling Test Cases** | 8 | 0 | 8 | 0% |
| **CLI/Config Validation** | 8 | 0 | 8 | 0% |
| **Reboot/Persistence** | 6 | 0 | 6 | 0% |

### Currently Implemented Scripts

1. ✅ `test_static_route_01_ipv4_basic.py`
2. ✅ `test_static_route_02_ipv4_blackhole.py`
3. ✅ `test_static_route_03_ipv4_vrf.py`
4. ✅ `test_static_route_05_ipv6_basic.py`
5. ✅ `test_static_route_06_ipv6_blackhole.py`
6. ✅ `test_static_route_07_ipv6_vrf.py`
7. ✅ `test_static_route_09_ecmp.py`

---

## Topology Requirements

### 3-Node Linear Topology

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   DEV-A      │         │   DEV-B      │         │   DEV-C      │
│ sp-Sonic-106 │◄───────►│ sp-Sonic-107 │◄───────►│ sp-Sonic-108 │
│ Port 7206    │ 2 ports │ Port 7207    │ 2 ports │ Port 7208    │
│              │         │    (DUT)     │         │              │
│  Scapy       │         │              │         │  Scapy       │
└──────────────┘         └──────────────┘         └──────────────┘
```

### Connection Details

| Link | DEV-A Port | DEV-B Port | DEV-C Port | Purpose |
|------|------------|------------|------------|---------|
| Link-1 | Ethernet0 | Ethernet0 | - | Primary A-B |
| Link-2 | Ethernet4 | Ethernet4 | - | Secondary A-B |
| Link-3 | - | Ethernet8 | Ethernet0 | Primary B-C |
| Link-4 | - | Ethernet12 | Ethernet4 | Secondary B-C |

### IP Addressing

**IPv4 Networks:**
- Network A-B Primary: 10.1.1.0/24
- Network A-B Secondary: 10.1.2.0/24
- Network B-C Primary: 10.2.1.0/24
- Network B-C Secondary: 10.2.2.0/24

**IPv6 Networks:**
- Network A-B Primary: 2001:1:1::/64
- Network A-B Secondary: 2001:1:2::/64
- Network B-C Primary: 2001:2:1::/64
- Network B-C Secondary: 2001:2:2::/64

---

## Test Cases by Category

---

## 1. Basic Functionality (IPv4) - 15 Test Cases

### TC_STATIC_ROUTE_BASIC_001: Add IPv4 Static Route with Next-Hop IP ✅

**Status:** ✅ **COVERED** (test_static_route_01_ipv4_basic.py)

**Objective:** Verify basic IPv4 static route configuration with next-hop IP address

**Configuration:**
```bash
ip route 192.168.10.0/24 10.2.1.2
```

**Verification:**
- Route appears in running-config
- Route installed in routing table (protocol "S")
- Route programmed in hardware FIB
- Packets forwarded successfully

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_BASIC_002: Add IPv4 Static Route with Next-Hop Interface

**Status:** ❌ **MISSING**

**Objective:** Verify IPv4 static route configuration with next-hop interface

**Configuration:**
```bash
ip route 192.168.20.0/24 Ethernet8
```

**Expected Behavior:**
- Route configured with interface-only next-hop
- ARP resolution occurs on egress interface
- Packets forwarded through specified interface

**Test Steps:**
1. Configure static route with interface next-hop
2. Verify route in routing table
3. Send test traffic from DEV-A
4. Capture packets on DEV-C
5. Verify forwarding statistics

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_BASIC_003: Add IPv4 Static Route with Next-Hop IP and Interface

**Status:** ❌ **MISSING**

**Objective:** Verify static route with both next-hop IP and interface specified

**Configuration:**
```bash
ip route 192.168.30.0/24 Ethernet8 10.2.1.2
```

**Expected Behavior:**
- Route installed with both interface and IP
- More specific next-hop resolution
- Proper forwarding behavior

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_BASIC_004: Delete IPv4 Static Route

**Status:** ❌ **MISSING**

**Objective:** Verify static route removal and cleanup

**Configuration:**
```bash
# Add route
ip route 192.168.40.0/24 10.2.1.2

# Delete route
no ip route 192.168.40.0/24 10.2.1.2
```

**Expected Behavior:**
- Route removed from running-config
- Route removed from routing table and FIB
- Packets to destination are dropped

**Test Steps:**
1. Add static route and verify installation
2. Delete static route
3. Verify removal from all tables
4. Send test packet and verify drop

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_BASIC_005: Modify IPv4 Static Route Next-Hop

**Status:** ❌ **MISSING**

**Objective:** Verify changing next-hop of existing static route

**Test Procedure:**
1. Configure: `ip route 192.168.50.0/24 10.2.1.2`
2. Verify forwarding through primary path
3. Modify: Delete old and add new next-hop
4. Configure: `ip route 192.168.50.0/24 10.2.2.2`
5. Verify traffic switches to new path

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_BASIC_006: Add Multiple Static Routes

**Status:** ❌ **MISSING**

**Objective:** Verify configuration of multiple distinct static routes

**Configuration:**
```bash
ip route 192.168.60.0/24 10.2.1.2
ip route 192.168.61.0/24 10.2.1.2
ip route 192.168.62.0/24 10.2.1.2
ip route 192.168.63.0/24 10.2.1.2
ip route 192.168.64.0/24 10.2.1.2
```

**Expected Behavior:**
- All routes configured and installed
- Each route operates independently
- All destinations reachable

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_BASIC_007: Static Route with /32 Host Route

**Status:** ❌ **MISSING**

**Objective:** Verify host-specific static route

**Configuration:**
```bash
ip route 192.168.70.100/32 10.2.1.2
```

**Expected Behavior:**
- Host route installed correctly
- Only exact IP match forwarded (192.168.70.100)
- Other IPs in same /24 not affected (192.168.70.101 dropped)

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_BASIC_008: Static Route with Default Route (0.0.0.0/0)

**Status:** ❌ **MISSING**

**Objective:** Verify default route configuration

**Configuration:**
```bash
ip route 0.0.0.0/0 10.2.1.2
```

**Expected Behavior:**
- Default route becomes catch-all for unmatched traffic
- All unknown destinations forward via default route

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_BASIC_009: Static Route with Various Prefix Lengths

**Status:** ❌ **MISSING**

**Objective:** Test routes with different subnet masks and longest prefix match

**Configuration:**
```bash
ip route 172.16.0.0/12 10.2.1.2
ip route 172.20.0.0/16 10.2.1.2
ip route 172.20.10.0/24 10.2.1.2
ip route 172.20.10.50/32 10.2.1.2
```

**Expected Behavior:**
- Routes with different masks coexist
- Longest prefix match works correctly:
  - 172.20.10.50 → uses /32 route
  - 172.20.10.100 → uses /24 route
  - 172.20.20.1 → uses /16 route
  - 172.17.1.1 → uses /12 route

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_BASIC_010: Static Route Replaces Connected Route

**Status:** ❌ **MISSING**

**Objective:** Verify static route behavior with connected routes

**Test Procedure:**
1. Verify connected route exists
2. Configure static route for same prefix
3. Verify which route is active (depends on admin distance)
4. Test forwarding behavior
5. Delete static route and verify connected route active

**Expected Behavior:**
- Connected routes typically preferred (AD=0)
- Static routes (AD=1) may not override connected

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_BASIC_011: Blackhole Route (Null0) ✅

**Status:** ✅ **COVERED** (test_static_route_02_ipv4_blackhole.py)

**Objective:** Verify blackhole/null route functionality

**Configuration:**
```bash
ip route 192.168.80.0/24 Null0
```

**Expected Behavior:**
- Packets matching route are silently dropped
- No ICMP destination unreachable sent
- Useful for preventing routing loops

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_BASIC_012: Static Route Forwarding Statistics

**Status:** ❌ **MISSING**

**Objective:** Verify packet and byte counters for static routes

**Test Procedure:**
1. Configure static route
2. Clear interface statistics
3. Send 100 packets (1500 bytes each)
4. Verify routing statistics increment
5. Check interface counters match expected values

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_BASIC_013: Multiple Next-Hops (ECMP) for Same Prefix ✅

**Status:** ✅ **COVERED** (test_static_route_09_ecmp.py)

**Objective:** Verify equal-cost multi-path static routing

**Configuration:**
```bash
ip route 192.168.100.0/24 10.2.1.2
ip route 192.168.100.0/24 10.2.2.2
```

**Expected Behavior:**
- Both next-hops installed (ECMP group)
- Traffic load-balanced across both paths
- Per-flow consistency maintained

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_BASIC_014: Static Route via Gateway Not in Same Subnet

**Status:** ❌ **MISSING**

**Objective:** Test recursive route resolution

**Configuration:**
```bash
ip route 192.168.110.0/24 10.3.3.1
# Next-hop 10.3.3.1 is not directly connected
```

**Expected Behavior:**
- Recursive next-hop resolution works
- Route only active if next-hop is reachable
- Route marked inactive if next-hop unreachable

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_BASIC_015: Static Route Configuration Persistence

**Status:** ❌ **MISSING**

**Objective:** Verify static route config saved and reloaded

**Test Procedure:**
1. Configure static route
2. Save configuration: `write memory`
3. Verify route in startup-config
4. Reload device
5. Verify route still present after reload

**Priority:** P0 (Critical)

---

## 2. IPv6 Functionality - 12 Test Cases

### TC_STATIC_ROUTE_IPV6_001: Add IPv6 Static Route with Next-Hop IP ✅

**Status:** ✅ **COVERED** (test_static_route_05_ipv6_basic.py)

**Objective:** Verify basic IPv6 static route configuration

**Configuration:**
```bash
ipv6 route 2001:db8:100::/64 2001:2:1::2
```

**Expected Behavior:**
- IPv6 route installed correctly
- NDP resolution for next-hop successful
- IPv6 packets forwarded properly

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_IPV6_002: Add IPv6 Static Route with Next-Hop Interface

**Status:** ❌ **MISSING**

**Objective:** Verify IPv6 route with interface-only next-hop

**Configuration:**
```bash
ipv6 route 2001:db8:200::/64 Ethernet8
```

**Expected Behavior:**
- Interface-based IPv6 forwarding works
- NDP uses link-local addresses for next-hop

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_IPV6_003: IPv6 Route with Link-Local Next-Hop

**Status:** ❌ **MISSING**

**Objective:** Test IPv6 route using link-local address as next-hop

**Configuration:**
```bash
ipv6 route 2001:db8:300::/64 Ethernet8 fe80::xxx
```

**Expected Behavior:**
- Link-local next-hop resolution works
- Packets forwarded using link-local addressing

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_IPV6_004: Delete IPv6 Static Route

**Status:** ❌ **MISSING**

**Objective:** Verify IPv6 route deletion

**Configuration:**
```bash
# Add
ipv6 route 2001:db8:400::/64 2001:2:1::2

# Delete
no ipv6 route 2001:db8:400::/64 2001:2:1::2
```

**Expected Behavior:**
- Route cleanly removed
- No IPv6 connectivity to destination

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_IPV6_005: IPv6 Host Route (/128)

**Status:** ❌ **MISSING**

**Objective:** Verify IPv6 /128 host route

**Configuration:**
```bash
ipv6 route 2001:db8:500::100/128 2001:2:1::2
```

**Expected Behavior:**
- Host-specific IPv6 route works
- Only exact address match forwarded

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_IPV6_006: IPv6 Default Route (::/0)

**Status:** ❌ **MISSING**

**Objective:** Verify IPv6 default route

**Configuration:**
```bash
ipv6 route ::/0 2001:2:1::2
```

**Expected Behavior:**
- Default route catches all unmatched IPv6 traffic

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_IPV6_007: Multiple IPv6 Next-Hops (ECMP)

**Status:** ❌ **MISSING**

**Objective:** Verify IPv6 ECMP static routing

**Configuration:**
```bash
ipv6 route 2001:db8:600::/64 2001:2:1::2
ipv6 route 2001:db8:600::/64 2001:2:2::2
```

**Expected Behavior:**
- IPv6 ECMP functions correctly
- Traffic distributed across paths

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_IPV6_008: IPv6 Blackhole Route ✅

**Status:** ✅ **COVERED** (test_static_route_06_ipv6_blackhole.py)

**Objective:** Test IPv6 null route

**Configuration:**
```bash
ipv6 route 2001:db8:700::/64 Null0
```

**Expected Behavior:**
- IPv6 blackhole route works
- Packets dropped without notification

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_IPV6_009: IPv6 Route Various Prefix Lengths

**Status:** ❌ **MISSING**

**Objective:** Test IPv6 longest prefix match

**Configuration:**
```bash
ipv6 route 2001:db8::/32 2001:2:1::2
ipv6 route 2001:db8:800::/48 2001:2:1::2
ipv6 route 2001:db8:800::/64 2001:2:1::2
ipv6 route 2001:db8:800::100/128 2001:2:1::2
```

**Expected Behavior:**
- Most specific IPv6 route always used

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_IPV6_010: IPv6 Route with Interface + Address

**Status:** ❌ **MISSING**

**Objective:** Test IPv6 route with both interface and next-hop IP

**Configuration:**
```bash
ipv6 route 2001:db8:900::/64 Ethernet8 2001:2:1::2
```

**Expected Behavior:**
- More explicit next-hop specification works

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_IPV6_011: Mixed IPv4 and IPv6 Static Routes

**Status:** ❌ **MISSING**

**Objective:** Verify coexistence of IPv4 and IPv6 static routes

**Test Procedure:**
1. Configure both IPv4 and IPv6 routes
2. Verify separate routing tables maintained
3. Send both IPv4 and IPv6 traffic
4. Verify independent forwarding

**Expected Behavior:**
- Dual-stack static routing works
- No interference between protocols

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_IPV6_012: IPv6 Route Persistence

**Status:** ❌ **MISSING**

**Objective:** Verify IPv6 route config persistence

**Test Procedure:**
1. Configure IPv6 static routes
2. Save config and reload
3. Verify routes restored
4. Test forwarding after reload

**Priority:** P0 (Critical)

---

## 3. VRF Integration - 10 Test Cases

### TC_STATIC_ROUTE_VRF_001: Static Route in Non-Default VRF ✅

**Status:** ✅ **COVERED** (test_static_route_03_ipv4_vrf.py)

**Objective:** Verify static route configuration in VRF

**Configuration:**
```bash
ip vrf VRF-RED
interface Ethernet8
  ip vrf forwarding VRF-RED
ip route vrf VRF-RED 192.168.200.0/24 10.2.1.2
```

**Expected Behavior:**
- VRF-aware static routing works
- Routes isolated per VRF

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_VRF_002: Static Routes in Multiple VRFs

**Status:** ❌ **MISSING**

**Objective:** Test static routes across multiple VRFs

**Test Procedure:**
1. Create VRF-RED and VRF-BLUE
2. Configure same destination in both with different next-hops
3. Verify isolation between VRF routing tables
4. Test forwarding in each VRF independently

**Expected Behavior:**
- Multiple VRFs operate independently
- Same prefix in different VRFs doesn't conflict

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_VRF_003: Static Route Leaking Between VRFs

**Status:** ❌ **MISSING**

**Objective:** Verify route import/export between VRFs

**Test Procedure:**
1. Configure route in VRF-RED
2. Configure route-target export/import
3. Verify route appears in VRF-BLUE
4. Test inter-VRF forwarding

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_VRF_004: Delete VRF with Static Routes

**Status:** ❌ **MISSING**

**Objective:** Test cleanup when VRF is deleted

**Test Procedure:**
1. Create VRF and add static routes
2. Delete VRF
3. Verify all routes removed
4. Verify no orphaned routes

**Expected Behavior:**
- VRF deletion cleans up all associated routes

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_VRF_005: Management VRF Static Routes

**Status:** ❌ **MISSING**

**Objective:** Test static routes in management VRF

**Test Procedure:**
1. Configure route in mgmt VRF
2. Verify management traffic uses route
3. Verify isolation from data plane

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_VRF_006: VRF Static Route Next-Hop Resolution

**Status:** ❌ **MISSING**

**Objective:** Verify next-hop must be in same VRF

**Test Procedure:**
1. Configure route in VRF-RED with next-hop in VRF-BLUE
2. Verify route not installed (invalid config)
3. Configure correct same-VRF next-hop
4. Verify route installs

**Expected Behavior:**
- Cross-VRF next-hops rejected

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_VRF_007: IPv6 Static Routes in VRF ✅

**Status:** ✅ **COVERED** (test_static_route_07_ipv6_vrf.py)

**Objective:** Test IPv6 static routing with VRF

**Configuration:**
```bash
ipv6 route vrf VRF-RED 2001:db8:100::/64 2001:2:1::2
```

**Expected Behavior:**
- IPv6 VRF static routes work

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_VRF_008: VRF Route with Default Route

**Status:** ❌ **MISSING**

**Objective:** Test default route in VRF

**Configuration:**
```bash
ip route vrf VRF-RED 0.0.0.0/0 10.2.1.2
```

**Expected Behavior:**
- Per-VRF default routes work independently

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_VRF_009: VRF Static Route Persistence

**Status:** ❌ **MISSING**

**Objective:** Verify VRF routes persist across reboot

**Test Procedure:**
1. Configure VRF with static routes
2. Save and reload
3. Verify VRF and routes restored

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_VRF_010: VRF Interface Down Impact on Static Routes

**Status:** ❌ **MISSING**

**Objective:** Test route behavior when VRF interface fails

**Test Procedure:**
1. Configure VRF route via interface
2. Shutdown interface
3. Verify route marked inactive
4. Bring interface up
5. Verify route active again

**Priority:** P1 (High)

---

## 4. Interface Integration - 8 Test Cases

### TC_STATIC_ROUTE_INTF_001: Static Route Next-Hop Interface Goes Down

**Status:** ❌ **MISSING**

**Objective:** Verify route withdrawal when interface fails

**Test Procedure:**
1. Configure: `ip route 192.168.150.0/24 Ethernet8`
2. Verify route active
3. Shutdown Ethernet8
4. Verify route marked inactive
5. Verify packets dropped

**Expected Behavior:**
- Route automatically withdrawn when interface down

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_INTF_002: Static Route Recovery After Interface Up

**Status:** ❌ **MISSING**

**Objective:** Verify automatic route restoration

**Test Procedure:**
1. Start with interface down
2. Bring interface up
3. Verify route becomes active
4. Verify forwarding resumes

**Expected Behavior:**
- Route automatically re-installed
- Fast convergence (< 1 second)

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_INTF_003: Static Route with Next-Hop IP - Interface Down

**Status:** ❌ **MISSING**

**Objective:** Test IP-based next-hop when interface fails

**Test Procedure:**
1. Configure: `ip route 192.168.160.0/24 10.2.1.2`
2. Shutdown interface to next-hop
3. Verify route becomes inactive
4. Bring interface up
5. Verify route active

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_INTF_004: Interface Flap Behavior

**Status:** ❌ **MISSING**

**Objective:** Test route stability during interface flapping

**Test Procedure:**
1. Configure static route via interface
2. Rapidly flap interface 10 times
3. Verify route stability
4. Verify final state correct

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_INTF_005: LAG Interface Static Route

**Status:** ❌ **MISSING**

**Objective:** Test static route via PortChannel

**Configuration:**
```bash
config portchannel add PortChannel1
ip route 192.168.170.0/24 PortChannel1
```

**Expected Behavior:**
- Static routes work with LAG interfaces
- LAG member changes don't affect route

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_INTF_006: VLAN Interface Static Route

**Status:** ❌ **MISSING**

**Objective:** Test static route via VLAN interface

**Configuration:**
```bash
config vlan add 100
ip route 192.168.180.0/24 Vlan100
```

**Expected Behavior:**
- Static routes via VLAN interfaces work

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_INTF_007: Loopback Interface Static Route

**Status:** ❌ **MISSING**

**Objective:** Test static route via loopback

**Configuration:**
```bash
config loopback add Loopback0
```

**Expected Behavior:**
- Loopback-based static routes work (if supported)

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_INTF_008: Interface Speed/MTU Change Impact

**Status:** ❌ **MISSING**

**Objective:** Verify static routes unaffected by interface parameter changes

**Test Procedure:**
1. Configure static route via interface
2. Change interface speed
3. Change interface MTU
4. Verify route remains active

**Priority:** P2 (Medium)

---

## 5. Route Priority and Selection - 8 Test Cases

### TC_STATIC_ROUTE_PRIO_001: Static Route with Metric/Distance

**Status:** ❌ **MISSING**

**Objective:** Test administrative distance configuration

**Configuration:**
```bash
ip route 192.168.190.0/24 10.2.1.2 distance 100
```

**Expected Behavior:**
- Route installed with specified admin distance
- Used for route preference

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_PRIO_002: Multiple Routes Different Metrics

**Status:** ❌ **MISSING**

**Objective:** Test metric-based route selection

**Configuration:**
```bash
ip route 192.168.191.0/24 10.2.1.2 distance 50
ip route 192.168.191.0/24 10.2.2.2 distance 100
```

**Expected Behavior:**
- Lower distance route preferred
- Backup route used if primary fails

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_PRIO_003: Static vs Connected Route Priority

**Status:** ❌ **MISSING**

**Objective:** Verify route type priority

**Test Procedure:**
1. Verify connected route (AD=0)
2. Add static route for same prefix (AD=1)
3. Verify connected route preferred
4. Remove connected route
5. Verify static route becomes active

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_PRIO_004: Static vs Dynamic Protocol Priority

**Status:** ❌ **MISSING**

**Objective:** Test static route priority against BGP/OSPF

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_PRIO_005: ECMP Load Balancing Verification ✅

**Status:** ✅ **COVERED** (test_static_route_09_ecmp.py)

**Objective:** Verify traffic distribution in ECMP

**Expected Behavior:**
- Traffic load-balanced across paths
- Per-flow consistency maintained

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_PRIO_006: ECMP with Unequal Metrics

**Status:** ❌ **MISSING**

**Objective:** Test unequal-cost load balancing

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_PRIO_007: Route Preference Modification

**Status:** ❌ **MISSING**

**Objective:** Test changing route preference at runtime

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_PRIO_008: Longest Prefix Match Verification

**Status:** ❌ **MISSING**

**Objective:** Verify LPM algorithm works correctly

**Priority:** P1 (High)

---

## 6. Negative Test Cases - 15 Test Cases

### TC_STATIC_ROUTE_NEG_001: Invalid Next-Hop IP

**Status:** ❌ **MISSING**

**Objective:** Test handling of non-existent next-hop

**Configuration:**
```bash
ip route 192.168.200.0/24 10.99.99.99
```

**Expected Behavior:**
- Route configured but marked inactive
- Error logged appropriately

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_NEG_002: Invalid Interface Name

**Status:** ❌ **MISSING**

**Objective:** Test invalid interface handling

**Configuration:**
```bash
ip route 192.168.201.0/24 Ethernet999
```

**Expected Behavior:**
- Configuration rejected with error

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_NEG_003: Unreachable Next-Hop

**Status:** ❌ **MISSING**

**Objective:** Test next-hop not reachable

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_NEG_004: Routing Loop Detection

**Status:** ❌ **MISSING**

**Objective:** Test self-referencing routes

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_NEG_005: Invalid Prefix Format

**Status:** ❌ **MISSING**

**Objective:** Test malformed prefix

**Configuration:**
```bash
ip route 192.168.300.0/24 10.2.1.2  # Invalid IP
```

**Expected Behavior:**
- Configuration rejected

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_NEG_006: Conflicting Route Configuration

**Status:** ❌ **MISSING**

**Objective:** Test route conflicts

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_NEG_007: Duplicate Route Addition

**Status:** ❌ **MISSING**

**Objective:** Test adding same route twice

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_NEG_008: Delete Non-Existent Route

**Status:** ❌ **MISSING**

**Objective:** Test removing route that doesn't exist

**Configuration:**
```bash
no ip route 192.168.999.0/24 10.2.1.2
```

**Expected Behavior:**
- Graceful error handling
- No system instability

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_NEG_009: Route with Incorrect VRF

**Status:** ❌ **MISSING**

**Objective:** Test wrong VRF reference

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_NEG_010: Next-Hop in Different VRF

**Status:** ❌ **MISSING**

**Objective:** Test cross-VRF next-hop

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_NEG_011: Blackhole with Next-Hop IP

**Status:** ❌ **MISSING**

**Objective:** Test invalid combination

**Configuration:**
```bash
ip route 192.168.210.0/24 Null0 10.2.1.2
```

**Expected Behavior:**
- Configuration rejected (conflicting parameters)

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_NEG_012: Invalid Metric Value

**Status:** ❌ **MISSING**

**Objective:** Test out of range metric

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_NEG_013: Route Without Required Parameters

**Status:** ❌ **MISSING**

**Objective:** Test missing parameters

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_NEG_014: Simultaneous Add/Delete Operations

**Status:** ❌ **MISSING**

**Objective:** Test race conditions

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_NEG_015: Configuration Error Handling

**Status:** ❌ **MISSING**

**Objective:** Test error recovery

**Priority:** P2 (Medium)

---

## 7. Scaling Test Cases - 8 Test Cases

### TC_STATIC_ROUTE_SCALE_001: Maximum Static Routes

**Status:** ❌ **MISSING**

**Objective:** Test maximum route limit

**Test Procedure:**
1. Determine max route limit
2. Add routes up to limit
3. Verify all routes installed
4. Attempt to exceed limit
5. Verify error handling

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_SCALE_002: Large Number Routes per VRF

**Status:** ❌ **MISSING**

**Objective:** Test VRF route scaling

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_SCALE_003: Multiple Next-Hops per Route

**Status:** ❌ **MISSING**

**Objective:** Test max ECMP paths

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_SCALE_004: Route Add/Delete Performance

**Status:** ❌ **MISSING**

**Objective:** Test operation speed

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_SCALE_005: Memory Usage with Many Routes

**Status:** ❌ **MISSING**

**Objective:** Test resource consumption

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_SCALE_006: CPU Utilization During Bulk Adds

**Status:** ❌ **MISSING**

**Objective:** Test CPU impact

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_SCALE_007: Convergence Time with Many Routes

**Status:** ❌ **MISSING**

**Objective:** Test convergence performance

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_SCALE_008: Mixed IPv4/IPv6 Scaling

**Status:** ❌ **MISSING**

**Objective:** Test dual-stack scaling

**Priority:** P2 (Medium)

---

## 8. CLI and Configuration Validation - 8 Test Cases

### TC_STATIC_ROUTE_CLI_001: Click CLI Configuration

**Status:** ❌ **MISSING**

**Objective:** Test Click CLI commands

**CLI Commands:**
```bash
config route add prefix 192.168.220.0/24 nexthop 10.2.1.2
show runningconfig route
```

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_CLI_002: Klish CLI Configuration

**Status:** ❌ **MISSING**

**Objective:** Test Klish CLI commands

**CLI Commands:**
```bash
configure terminal
ip route 192.168.220.0/24 10.2.1.2
show running-config | grep "ip route"
```

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_CLI_003: REST API Configuration

**Status:** ❌ **MISSING**

**Objective:** Test REST API calls

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_CLI_004: gNMI Configuration

**Status:** ❌ **MISSING**

**Objective:** Test gNMI protocol

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_CLI_005: Show Command Verification

**Status:** ❌ **MISSING**

**Objective:** Verify all show commands work

**Show Commands:**
```bash
show ip route
show ip route 192.168.220.0/24
show ip route static
show running-config | grep route
```

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_CLI_006: Running Config Verification

**Status:** ❌ **MISSING**

**Objective:** Verify config display

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_CLI_007: Config File Edit and Reload

**Status:** ❌ **MISSING**

**Objective:** Test manual config edit

**Priority:** P2 (Medium)

---

### TC_STATIC_ROUTE_CLI_008: Multi-CLI Consistency

**Status:** ❌ **MISSING**

**Objective:** Test cross-CLI validation

**Test Procedure:**
1. Configure route via Click CLI
2. Verify visible in Klish CLI
3. Configure another route via Klish
4. Verify visible in Click CLI
5. Test via REST API and gNMI

**Priority:** P1 (High)

---

## 9. Reboot and Persistence - 6 Test Cases

### TC_STATIC_ROUTE_REBOOT_001: Cold Reboot Persistence

**Status:** ❌ **MISSING**

**Objective:** Verify config after cold reboot

**Test Procedure:**
1. Configure static routes
2. Save configuration
3. Perform cold reboot
4. Verify all routes restored
5. Test forwarding

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_REBOOT_002: Warm Reboot Persistence

**Status:** ❌ **MISSING**

**Objective:** Verify config after warm reboot

**Test Procedure:**
1. Configure static routes
2. Save configuration
3. Perform warm reboot
4. Verify routes maintained
5. Verify no traffic loss

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_REBOOT_003: Fast Reboot Persistence

**Status:** ❌ **MISSING**

**Objective:** Verify config after fast reboot

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_REBOOT_004: Config Save Before Reboot

**Status:** ❌ **MISSING**

**Objective:** Verify save and reload

**Test Procedure:**
1. Configure routes
2. Save: `write memory`
3. Reload device
4. Verify routes present

**Priority:** P0 (Critical)

---

### TC_STATIC_ROUTE_REBOOT_005: Unsaved Config Loss

**Status:** ❌ **MISSING**

**Objective:** Verify unsaved config is lost

**Test Procedure:**
1. Configure routes
2. Do NOT save
3. Reload device
4. Verify routes NOT present

**Priority:** P1 (High)

---

### TC_STATIC_ROUTE_REBOOT_006: FRR Container Restart

**Status:** ❌ **MISSING**

**Objective:** Test service restart

**Test Procedure:**
1. Configure static routes
2. Restart FRR/BGP container
3. Verify routes restored
4. Test forwarding

**Priority:** P1 (High)

---

## Implementation Priority

### Priority 0 (Critical - Must Have) - 25 Test Cases

| Test Case | Category | Reason |
|-----------|----------|--------|
| TC_BASIC_002 | Interface next-hop | Core functionality |
| TC_BASIC_004 | Route deletion | Core functionality |
| TC_BASIC_008 | Default route | Core functionality |
| TC_BASIC_009 | Prefix lengths | Core functionality |
| TC_BASIC_015 | Persistence | Production requirement |
| TC_IPV6_002 | IPv6 interface | Dual-stack support |
| TC_IPV6_004 | IPv6 deletion | Core functionality |
| TC_IPV6_006 | IPv6 default | Core functionality |
| TC_IPV6_012 | IPv6 persistence | Production requirement |
| TC_INTF_001 | Interface down | High availability |
| TC_INTF_002 | Interface recovery | High availability |
| TC_INTF_003 | Next-hop tracking | High availability |
| TC_REBOOT_001 | Cold reboot | Production requirement |
| TC_REBOOT_002 | Warm reboot | Production requirement |
| TC_REBOOT_003 | Fast reboot | Production requirement |
| TC_REBOOT_004 | Save/reload | Production requirement |

### Priority 1 (High - Should Have) - 35 Test Cases

Includes:
- Advanced interface scenarios
- VRF advanced features
- Route priority and metrics
- Negative test coverage
- CLI validation

### Priority 2 (Medium - Nice to Have) - 30 Test Cases

Includes:
- Scaling tests
- Performance tests
- Edge cases
- Multi-protocol scenarios

---

## Test Execution Guide

### Prerequisites

1. **Topology Setup:**
   - 3 SONiC-VS instances (DEV-A, DEV-B, DEV-C)
   - sp-Sonic-106, 107, 108 configured
   - Network connectivity established

2. **Software Requirements:**
   - spytest framework
   - Scapy for traffic generation
   - All VMs updated with Mar27 build

3. **Testbed Configuration:**
   - File: `testbed_3node_static_route.yaml`
   - Location: `/home/adminuser/draksha/sonic-mgmt/spytest/testbeds/`

### Running Tests

**Run All Implemented Tests:**
```bash
cd /home/adminuser/draksha/sonic-mgmt/spytest

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_3node_static_route.yaml \
  tests/system/Static_Route/test_static_route_*.py \
  --logs-path ./logs/$(date +%Y%m%d)/STATIC_ROUTE/$(date +%H%M%S) \
  --log-level debug \
  --skip-init-config \
  --ifname-type native
```

**Run Specific Category:**
```bash
# Run only IPv4 basic tests
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_3node_static_route.yaml \
  tests/system/Static_Route/test_static_route_01_ipv4_basic.py \
  --logs-path ./logs/$(date +%Y%m%d)/STATIC_ROUTE_IPV4/$(date +%H%M%S)
```

**Run with Screen (for long tests):**
```bash
screen -S static_route_tests
./bin/spytest --tryssh 1 --testbed ./testbeds/testbed_3node_static_route.yaml \
  tests/system/Static_Route/test_static_route_*.py
# Ctrl+A, D to detach
```

### Test Results Location

```
logs/
└── 20260402/
    └── STATIC_ROUTE/
        └── 143522/
            ├── results.xml
            ├── results.html
            ├── dut.log
            └── test_results/
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-02 | Test Team | Initial document with complete test breakdown |

---

## References

- **Test Plan:** STATIC_ROUTE_testplan.md
- **Requirements:** Requirements.txt
- **Test Scripts:** /home/adminuser/draksha/sonic-mgmt/spytest/tests/system/Static_Route/
- **Testbed:** testbed_3node_static_route.yaml

---

**END OF DOCUMENT**
