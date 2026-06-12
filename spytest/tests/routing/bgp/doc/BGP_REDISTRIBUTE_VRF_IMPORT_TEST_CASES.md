# BGP Redistribute and VRF Import - Comprehensive Test Cases

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | BGP-REDIST-VRF-IMPORT-TC |
| **Feature** | BGP Route Redistribution and VRF Import |
| **Test Suite** | BGP CLI Validation |
| **Version** | 1.0 |
| **Date** | 2026-05-28 |
| **Author** | Automated Test Case Generation |
| **Testbed** | testbed_vs_3rr_reg.yaml |
| **Topology** | 3-node: D1-D2-D3 (RR Client-RR Server-RR Client) |

---

## Test Coverage Summary

### CLI Commands Covered

1. **redistribute ospf / redistribute ospfv3**
2. **redistribute metric**
3. **redistribute route-map**
4. **no redistribute** (all variants)
5. **import vrf route-map**
6. **no import vrf / no import vrf route-map**

### Test Categories

- **Positive Tests**: 15 test cases (TC-BGP-CLI-REDIST-001 to TC-BGP-CLI-VRF-IMPORT-007)
- **Negative Tests**: 12 test cases (TC-BGP-CLI-REDIST-NEG-001 to TC-BGP-CLI-VRF-IMPORT-NEG-005)
- **Edge Cases**: 8 test cases (TC-BGP-CLI-REDIST-EDGE-001 to TC-BGP-CLI-VRF-IMPORT-EDGE-003)

**Total Test Cases**: 35

---

# POSITIVE TEST CASES

---

## TC-BGP-CLI-REDIST-001: Basic OSPF Redistribution into BGP

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-001 |
| **Feature** | BGP OSPF Redistribution |
| **Priority** | High |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify that OSPF routes can be successfully redistributed into BGP using the basic `redistribute ospf` command without any modifiers.

### Pre-requisites

- 3 SONiC devices with testbed_vs_3rr_reg.yaml topology
- D1 and D3 as BGP route reflector clients
- D2 as BGP route reflector server
- OSPF running on at least one device with active routes
- iBGP sessions established (AS 65001)

### Test Configuration

| Parameter | D1 (Client) | D2 (RR Server) | D3 (Client) |
|-----------|-------------|----------------|-------------|
| BGP AS | 65001 | 65001 | 65001 |
| Router ID | 1.1.1.1 | 2.2.2.2 | 3.3.3.3 |
| Loopback0 IP | 1.1.1.1/32 | 2.2.2.2/32 | 3.3.3.3/32 |
| D1-D2 Link | 10.1.1.1/30 | 10.1.1.2/30 | - |
| D2-D3 Link | - | 10.1.1.5/30 | 10.1.1.6/30 |
| OSPF Process | 100 | 100 | - |
| OSPF Area | 0.0.0.0 | 0.0.0.0 | - |

### Test Procedure

#### Step 1: Configure OSPF on D1
```bash
sonic# configure terminal
sonic(config)# router ospf 100
sonic(config-router-ospf)# network 1.1.1.1/32 area 0.0.0.0
sonic(config-router-ospf)# network 10.1.1.0/30 area 0.0.0.0
sonic(config-router-ospf)# exit
```

#### Step 2: Configure OSPF on D2
```bash
sonic# configure terminal
sonic(config)# router ospf 100
sonic(config-router-ospf)# network 2.2.2.2/32 area 0.0.0.0
sonic(config-router-ospf)# network 10.1.1.4/30 area 0.0.0.0
sonic(config-router-ospf)# exit
```

#### Step 3: Verify OSPF Routes
```bash
sonic# show ip route ospf
# Expected: OSPF routes visible in routing table
```

#### Step 4: Configure BGP Redistribution on D1
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# redistribute ospf
sonic(config-router-bgp-af)# end
```

#### Step 5: Verify Redistribution
```bash
sonic# show ip bgp summary
sonic# show ip bgp
sonic# show running-config | section "router bgp"
```

#### Step 6: Verify Routes on D3
```bash
# On D3 (RR Client)
sonic# show ip bgp
sonic# show ip route bgp
# Expected: OSPF routes from D1 visible as BGP routes
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| OSPF Adjacency | OSPF neighbors UP between D1-D2 |
| OSPF Routes | OSPF routes in D1 routing table |
| BGP Configuration | `redistribute ospf` appears in running-config |
| BGP Route Injection | OSPF routes appear in BGP table with origin incomplete (?) |
| Route Propagation | D3 receives redistributed routes via RR |
| Route Type | Routes show origin incomplete (IGP) |
| Next-hop | Next-hop set to D1's loopback or update-source |

### Validation Commands

```bash
# Verify OSPF is running
show ip ospf neighbor
show ip ospf route

# Verify BGP redistribution config
show running-config | section "router bgp"

# Verify BGP routes
show ip bgp summary
show ip bgp | grep "?"  # Origin incomplete

# Verify routing table
show ip route bgp
show ip route 1.1.1.1

# Verify route details
show ip bgp 1.1.1.1/32
```

### Test Cleanup

```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# no redistribute ospf
sonic(config-router-bgp-af)# end
```

### Pass/Fail Criteria

- **PASS**: OSPF routes successfully redistributed into BGP and visible on D3
- **FAIL**: Routes not redistributed, BGP errors, or routes not propagated to RR clients

---

## TC-BGP-CLI-REDIST-002: OSPFv3 (IPv6) Redistribution into BGP

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-002 |
| **Feature** | BGP OSPFv3 Redistribution |
| **Priority** | High |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify that OSPFv3 (IPv6) routes can be successfully redistributed into BGP IPv6 address family using the `redistribute ospfv3` command.

### Pre-requisites

- 3 SONiC devices with testbed_vs_3rr_reg.yaml topology
- OSPFv3 running with IPv6 routes
- BGP IPv6 unicast address family configured
- iBGP sessions established

### Test Configuration

| Parameter | D1 | D2 | D3 |
|-----------|----|----|-----|
| BGP AS | 65001 | 65001 | 65001 |
| Loopback0 IPv6 | 2001:db8:1::1/128 | 2001:db8:2::2/128 | 2001:db8:3::3/128 |
| D1-D2 Link IPv6 | 2001:db8:10::1/64 | 2001:db8:10::2/64 | - |
| OSPFv3 Process | 100 | 100 | - |

### Test Procedure

#### Step 1: Configure OSPFv3 on D1
```bash
sonic# configure terminal
sonic(config)# ipv6 router ospf 100
sonic(config-ipv6-router-ospf)# router-id 1.1.1.1
sonic(config-ipv6-router-ospf)# exit
sonic(config)# interface Loopback 0
sonic(config-if-Loopback0)# ipv6 ospf 100 area 0.0.0.0
sonic(config-if-Loopback0)# exit
sonic(config)# interface Ethernet 0
sonic(config-if-Ethernet0)# ipv6 ospf 100 area 0.0.0.0
sonic(config-if-Ethernet0)# end
```

#### Step 2: Configure BGP IPv6 Redistribution
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv6 unicast
sonic(config-router-bgp-af)# redistribute ospfv3
sonic(config-router-bgp-af)# end
```

#### Step 3: Verify Redistribution
```bash
sonic# show bgp ipv6 unicast summary
sonic# show bgp ipv6 unicast
sonic# show ipv6 route bgp
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| OSPFv3 Adjacency | OSPFv3 neighbors UP |
| OSPFv3 Routes | OSPFv3 routes in IPv6 routing table |
| BGP Configuration | `redistribute ospfv3` in running-config |
| BGP IPv6 Routes | OSPFv3 routes appear in BGP IPv6 table |
| Route Propagation | D3 receives redistributed IPv6 routes |

### Validation Commands

```bash
show ipv6 ospf neighbor
show ipv6 ospf route
show running-config | section "address-family ipv6 unicast"
show bgp ipv6 unicast
show ipv6 route bgp
show bgp ipv6 unicast 2001:db8:1::1/128
```

### Pass/Fail Criteria

- **PASS**: OSPFv3 routes redistributed into BGP IPv6 and propagated
- **FAIL**: Routes not redistributed or not visible on RR clients

---

## TC-BGP-CLI-REDIST-003: Redistribute OSPF with Metric

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-003 |
| **Feature** | BGP Redistribution with Metric |
| **Priority** | High |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify that OSPF routes can be redistributed into BGP with a specified metric using `redistribute ospf metric <value>`.

### Test Configuration

| Parameter | Value |
|-----------|-------|
| Redistribution Metric | 100 |
| OSPF Process | 100 |
| Expected MED | 100 |

### Test Procedure

#### Step 1: Configure OSPF Redistribution with Metric
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# redistribute ospf metric 100
sonic(config-router-bgp-af)# end
```

#### Step 2: Verify Configuration
```bash
sonic# show running-config | section "router bgp"
# Expected: "redistribute ospf metric 100" in config
```

#### Step 3: Verify BGP Route Attributes
```bash
sonic# show ip bgp
sonic# show ip bgp 1.1.1.1/32
# Expected: MED (metric) = 100
```

#### Step 4: Verify on Receiving Router (D3)
```bash
# On D3
sonic# show ip bgp 1.1.1.1/32
# Expected: MED = 100 for redistributed routes
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Configuration | `redistribute ospf metric 100` in running-config |
| BGP Route MED | Redistributed routes have MED = 100 |
| Route Propagation | MED attribute preserved across RR |
| Route Preference | Metric affects route selection when multiple paths exist |

### Validation Commands

```bash
show running-config | section "redistribute"
show ip bgp | include "Metric"
show ip bgp 1.1.1.1/32 | include "Metric"
show ip bgp neighbors 10.1.1.2 advertised-routes | include "Metric"
```

### Pass/Fail Criteria

- **PASS**: Routes redistributed with MED=100 and visible on all BGP speakers
- **FAIL**: MED not set correctly or routes not redistributed

---

## TC-BGP-CLI-REDIST-004: Redistribute OSPF with Route-map

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-004 |
| **Feature** | BGP Redistribution with Route-map |
| **Priority** | High |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify selective OSPF route redistribution into BGP using route-map with match conditions and set actions.

### Test Configuration

| Parameter | Value |
|-----------|-------|
| Route-map Name | OSPF-TO-BGP |
| Match Condition | Prefix-list: ALLOWED-NETWORKS |
| Set Actions | metric 200, local-preference 150 |
| Allowed Prefixes | 1.1.1.0/24, 10.0.0.0/8 |
| Denied Prefixes | 192.168.0.0/16 |

### Test Procedure

#### Step 1: Create IP Prefix List
```bash
sonic# configure terminal
sonic(config)# ip prefix-list ALLOWED-NETWORKS seq 10 permit 1.1.1.0/24
sonic(config)# ip prefix-list ALLOWED-NETWORKS seq 20 permit 10.0.0.0/8 le 24
sonic(config)# exit
```

#### Step 2: Create Route-map
```bash
sonic# configure terminal
sonic(config)# route-map OSPF-TO-BGP permit 10
sonic(config-route-map)# match ip address prefix-list ALLOWED-NETWORKS
sonic(config-route-map)# set metric 200
sonic(config-route-map)# set local-preference 150
sonic(config-route-map)# exit
sonic(config)# route-map OSPF-TO-BGP deny 20
sonic(config-route-map)# exit
```

#### Step 3: Apply Route-map to Redistribution
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# redistribute ospf route-map OSPF-TO-BGP
sonic(config-router-bgp-af)# end
```

#### Step 4: Verify Selective Redistribution
```bash
sonic# show ip bgp | include "1.1.1"
sonic# show ip bgp | include "192.168"
# Expected: 1.1.1.0/24 present, 192.168.0.0/16 absent
```

#### Step 5: Verify Route Attributes
```bash
sonic# show ip bgp 1.1.1.0/24
# Expected: MED=200, Local-pref=150
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Configuration | `redistribute ospf route-map OSPF-TO-BGP` in config |
| Selective Redistribution | Only matched routes redistributed |
| Route Attributes | MED=200, Local-pref=150 on redistributed routes |
| Denied Routes | 192.168.0.0/16 NOT in BGP table |
| Allowed Routes | 1.1.1.0/24 and 10.0.0.0/8 subnets in BGP table |

### Validation Commands

```bash
show running-config | section "route-map OSPF-TO-BGP"
show running-config | section "redistribute ospf"
show ip prefix-list ALLOWED-NETWORKS
show ip bgp
show ip bgp 1.1.1.0/24
show ip bgp 192.168.1.0/24  # Should not exist
show ip bgp regexp .*  # All BGP routes
```

### Pass/Fail Criteria

- **PASS**: Only allowed routes redistributed with correct attributes
- **FAIL**: Denied routes appear in BGP or attributes incorrect

---

## TC-BGP-CLI-REDIST-005: Multiple Redistribution Sources

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-005 |
| **Feature** | BGP Multiple Protocol Redistribution |
| **Priority** | Medium |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify that multiple routing protocols (OSPF, static, connected) can be simultaneously redistributed into BGP with different metrics and route-maps.

### Test Configuration

| Protocol | Metric | Route-map |
|----------|--------|-----------|
| OSPF | 100 | OSPF-RM |
| Static | 200 | STATIC-RM |
| Connected | 50 | CONNECTED-RM |

### Test Procedure

#### Step 1: Configure Multiple Redistributions
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# redistribute ospf metric 100 route-map OSPF-RM
sonic(config-router-bgp-af)# redistribute static metric 200 route-map STATIC-RM
sonic(config-router-bgp-af)# redistribute connected metric 50 route-map CONNECTED-RM
sonic(config-router-bgp-af)# end
```

#### Step 2: Verify All Redistributions Active
```bash
sonic# show running-config | section "redistribute"
# Expected: All three redistribute statements present
```

#### Step 3: Verify Routes by Origin
```bash
sonic# show ip bgp | grep "?"  # OSPF routes (incomplete)
sonic# show ip bgp | grep "i"  # Static/connected (IGP)
sonic# show ip route bgp
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Configuration | All three redistribute statements in config |
| OSPF Routes | Redistributed with MED=100 |
| Static Routes | Redistributed with MED=200 |
| Connected Routes | Redistributed with MED=50 |
| Route Isolation | Each protocol's routes identifiable by MED |
| No Conflicts | All protocols redistribute simultaneously |

### Validation Commands

```bash
show running-config | section "address-family ipv4"
show ip bgp | include "Metric"
show ip bgp neighbors 10.1.1.2 advertised-routes
show ip route bgp
```

### Pass/Fail Criteria

- **PASS**: All protocols redistribute simultaneously with correct attributes
- **FAIL**: Conflicts between redistributions or routes missing

---

## TC-BGP-CLI-REDIST-006: Remove OSPF Redistribution (no redistribute ospf)

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-006 |
| **Feature** | BGP Redistribution Removal |
| **Priority** | High |
| **Test Type** | Positive - Configuration Removal |
| **CLI Type** | Klish |

### Test Objective

Verify that OSPF redistribution can be cleanly removed using `no redistribute ospf` and all redistributed routes are withdrawn from BGP.

### Test Procedure

#### Step 1: Configure OSPF Redistribution (Baseline)
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# redistribute ospf metric 100
sonic(config-router-bgp-af)# end
```

#### Step 2: Verify Routes Exist
```bash
sonic# show ip bgp | grep "1.1.1.1"
# Expected: OSPF route 1.1.1.1/32 in BGP table
```

#### Step 3: Remove Redistribution
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# no redistribute ospf
sonic(config-router-bgp-af)# end
```

#### Step 4: Verify Routes Withdrawn
```bash
sonic# show ip bgp | grep "1.1.1.1"
# Expected: Route no longer in BGP table
sonic# show running-config | section "redistribute"
# Expected: No "redistribute ospf" statement
```

#### Step 5: Verify on Remote Router (D3)
```bash
# On D3
sonic# show ip bgp | grep "1.1.1.1"
# Expected: Route withdrawn from D3's BGP table
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Configuration Removal | `redistribute ospf` removed from config |
| Route Withdrawal | OSPF routes removed from local BGP table |
| BGP Updates | Withdraw messages sent to BGP peers |
| Remote Withdrawal | Routes removed from D3's BGP table |
| Clean State | No residual OSPF routes in BGP |

### Validation Commands

```bash
show running-config | section "router bgp"
show ip bgp
show ip bgp summary
show ip bgp neighbors 10.1.1.2 advertised-routes
# On D3:
show ip bgp
show ip route bgp
```

### Pass/Fail Criteria

- **PASS**: Redistribution removed, all OSPF routes withdrawn from BGP
- **FAIL**: Routes remain in BGP table or config not updated

---

## TC-BGP-CLI-REDIST-007: Remove Redistribution with Metric Modifier

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-007 |
| **Feature** | BGP Redistribution Removal (with modifiers) |
| **Priority** | Medium |
| **Test Type** | Positive - Configuration Removal |
| **CLI Type** | Klish |

### Test Objective

Verify that redistribution configured with metric can be removed using `no redistribute ospf metric <value>` or simply `no redistribute ospf`.

### Test Procedure

#### Step 1: Configure with Metric
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# redistribute ospf metric 100
sonic(config-router-bgp-af)# end
```

#### Step 2: Remove with Exact Match
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# no redistribute ospf metric 100
sonic(config-router-bgp-af)# end
```

#### Step 3: Verify Removal
```bash
sonic# show running-config | section "redistribute"
# Expected: No redistribute statement
```

#### Step 4: Re-configure and Remove without Metric
```bash
sonic(config-router-bgp-af)# redistribute ospf metric 200
sonic(config-router-bgp-af)# no redistribute ospf
# Should remove regardless of metric value
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Exact Match Removal | `no redistribute ospf metric 100` removes config |
| Generic Removal | `no redistribute ospf` removes any redistribute ospf |
| Routes Withdrawn | All OSPF routes removed from BGP |

### Pass/Fail Criteria

- **PASS**: Both removal methods work correctly
- **FAIL**: Removal fails or routes remain

---

## TC-BGP-CLI-VRF-IMPORT-001: Basic VRF Route Import with Route-map

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-001 |
| **Feature** | BGP VRF Route Import |
| **Priority** | High |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify that routes from one VRF can be imported into another VRF using `import vrf <vrf-name> route-map <map-name>`.

### Test Configuration

| Parameter | Source VRF | Destination VRF |
|-----------|------------|-----------------|
| VRF Name | VRF-BLUE | VRF-RED |
| Route-map | BLUE-TO-RED | - |
| Test Prefix | 10.10.10.0/24 | - |
| BGP AS | 65001 | 65001 |

### Test Procedure

#### Step 1: Create VRFs
```bash
sonic# configure terminal
sonic(config)# ip vrf VRF-BLUE
sonic(config-vrf)# exit
sonic(config)# ip vrf VRF-RED
sonic(config-vrf)# exit
```

#### Step 2: Configure BGP in Source VRF (VRF-BLUE)
```bash
sonic(config)# router bgp 65001 vrf VRF-BLUE
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# network 10.10.10.0/24
sonic(config-router-bgp-af)# exit
sonic(config-router-bgp)# exit
```

#### Step 3: Create Route-map for Import
```bash
sonic(config)# route-map BLUE-TO-RED permit 10
sonic(config-route-map)# set local-preference 200
sonic(config-route-map)# exit
```

#### Step 4: Configure Import in Destination VRF (VRF-RED)
```bash
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map BLUE-TO-RED
sonic(config-router-bgp-af)# end
```

#### Step 5: Verify Import
```bash
sonic# show ip bgp vrf VRF-RED
# Expected: 10.10.10.0/24 present with local-pref 200
sonic# show ip route vrf VRF-RED
# Expected: 10.10.10.0/24 in routing table
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| VRF Creation | Both VRFs created successfully |
| Source Route | 10.10.10.0/24 in VRF-BLUE BGP table |
| Import Configuration | `import vrf VRF-BLUE route-map BLUE-TO-RED` in config |
| Route Import | 10.10.10.0/24 appears in VRF-RED BGP table |
| Route Attributes | Local-preference = 200 (set by route-map) |
| Routing Table | Route installed in VRF-RED routing table |

### Validation Commands

```bash
show ip vrf
show running-config | section "router bgp 65001 vrf VRF-RED"
show ip bgp vrf VRF-BLUE
show ip bgp vrf VRF-RED
show ip bgp vrf VRF-RED 10.10.10.0/24
show ip route vrf VRF-RED
```

### Pass/Fail Criteria

- **PASS**: Routes imported from VRF-BLUE to VRF-RED with route-map applied
- **FAIL**: Routes not imported or route-map not applied

---

## TC-BGP-CLI-VRF-IMPORT-002: Import VRF without Route-map

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-002 |
| **Feature** | BGP VRF Route Import (No Route-map) |
| **Priority** | Medium |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify that routes can be imported between VRFs without a route-map using `import vrf <vrf-name>` (if supported), or confirm that route-map is mandatory.

### Test Procedure

#### Step 1: Attempt Import without Route-map
```bash
sonic# configure terminal
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# import vrf VRF-BLUE
sonic(config-router-bgp-af)# end
```

#### Step 2: Verify Behavior
```bash
sonic# show running-config | section "router bgp 65001 vrf VRF-RED"
sonic# show ip bgp vrf VRF-RED
```

### Expected Results

**Scenario A: Route-map Optional**
- Command accepted
- All routes from VRF-BLUE imported to VRF-RED
- No attribute modifications

**Scenario B: Route-map Mandatory**
- Command rejected with error
- Message: "Route-map required for VRF import"

### Pass/Fail Criteria

- **PASS**: Behavior matches SONiC implementation (either accepts or rejects consistently)
- **FAIL**: Inconsistent behavior or system instability

---

## TC-BGP-CLI-VRF-IMPORT-003: Remove VRF Import (no import vrf)

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-003 |
| **Feature** | BGP VRF Import Removal |
| **Priority** | High |
| **Test Type** | Positive - Configuration Removal |
| **CLI Type** | Klish |

### Test Objective

Verify that VRF import configuration can be removed using `no import vrf <vrf-name>` and imported routes are withdrawn.

### Test Procedure

#### Step 1: Configure Import (Baseline)
```bash
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map BLUE-TO-RED
sonic(config-router-bgp-af)# end
```

#### Step 2: Verify Routes Imported
```bash
sonic# show ip bgp vrf VRF-RED 10.10.10.0/24
# Expected: Route present
```

#### Step 3: Remove Import
```bash
sonic# configure terminal
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# no import vrf VRF-BLUE
sonic(config-router-bgp-af)# end
```

#### Step 4: Verify Routes Removed
```bash
sonic# show ip bgp vrf VRF-RED
# Expected: 10.10.10.0/24 no longer present
sonic# show running-config | section "router bgp 65001 vrf VRF-RED"
# Expected: No "import vrf" statement
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Configuration Removal | `import vrf VRF-BLUE` removed from config |
| Route Withdrawal | Imported routes removed from VRF-RED |
| Routing Table | Routes removed from VRF-RED routing table |
| Clean State | No residual imported routes |

### Pass/Fail Criteria

- **PASS**: Import removed, all imported routes withdrawn
- **FAIL**: Routes remain or config not updated

---

## TC-BGP-CLI-VRF-IMPORT-004: Remove VRF Import with Route-map Specifier

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-004 |
| **Feature** | BGP VRF Import Removal (with route-map) |
| **Priority** | Medium |
| **Test Type** | Positive - Configuration Removal |
| **CLI Type** | Klish |

### Test Objective

Verify removal of VRF import using exact match `no import vrf <vrf-name> route-map <map-name>` and generic `no import vrf <vrf-name>`.

### Test Procedure

#### Step 1: Configure Import
```bash
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map BLUE-TO-RED
```

#### Step 2: Remove with Exact Match
```bash
sonic(config-router-bgp-af)# no import vrf VRF-BLUE route-map BLUE-TO-RED
```

#### Step 3: Verify Removal
```bash
sonic# show running-config | section "import vrf"
# Expected: No import statement
```

#### Step 4: Re-configure and Remove Generically
```bash
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map BLUE-TO-RED
sonic(config-router-bgp-af)# no import vrf VRF-BLUE
# Should remove regardless of route-map
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Exact Match Removal | Works with full command syntax |
| Generic Removal | Works with just VRF name |
| Routes Withdrawn | All imported routes removed |

### Pass/Fail Criteria

- **PASS**: Both removal methods work correctly
- **FAIL**: Removal fails or routes remain

---

## TC-BGP-CLI-VRF-IMPORT-005: Multiple VRF Imports

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-005 |
| **Feature** | BGP Multiple VRF Imports |
| **Priority** | High |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify that a single VRF can import routes from multiple source VRFs simultaneously with different route-maps.

### Test Configuration

| Destination VRF | Source VRF-1 | Source VRF-2 | Source VRF-3 |
|----------------|--------------|--------------|--------------|
| VRF-RED | VRF-BLUE (RM1) | VRF-GREEN (RM2) | VRF-YELLOW (RM3) |

### Test Procedure

#### Step 1: Create Multiple Source VRFs with Routes
```bash
sonic(config)# router bgp 65001 vrf VRF-BLUE
sonic(config-router-bgp-af)# network 10.10.0.0/24
sonic(config)# router bgp 65001 vrf VRF-GREEN
sonic(config-router-bgp-af)# network 10.20.0.0/24
sonic(config)# router bgp 65001 vrf VRF-YELLOW
sonic(config-router-bgp-af)# network 10.30.0.0/24
```

#### Step 2: Configure Multiple Imports
```bash
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map BLUE-RM
sonic(config-router-bgp-af)# import vrf VRF-GREEN route-map GREEN-RM
sonic(config-router-bgp-af)# import vrf VRF-YELLOW route-map YELLOW-RM
sonic(config-router-bgp-af)# end
```

#### Step 3: Verify All Imports
```bash
sonic# show ip bgp vrf VRF-RED
# Expected: Routes from all three source VRFs present
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Multiple Imports | All three import statements in config |
| Route Isolation | Routes from each VRF identifiable |
| No Conflicts | All imports coexist without issues |
| Attribute Control | Each route-map applied independently |

### Pass/Fail Criteria

- **PASS**: All VRF imports work simultaneously
- **FAIL**: Conflicts or routes missing

---

## TC-BGP-CLI-VRF-IMPORT-006: VRF Import with Route Filtering

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-006 |
| **Feature** | BGP VRF Import with Selective Filtering |
| **Priority** | High |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify selective route import from source VRF using route-map with match conditions to filter specific prefixes.

### Test Configuration

| Parameter | Value |
|-----------|-------|
| Source VRF | VRF-BLUE (has 10.10.0.0/24, 10.20.0.0/24, 192.168.1.0/24) |
| Destination VRF | VRF-RED |
| Route-map | SELECTIVE-IMPORT (permit 10.10.0.0/24, deny others) |

### Test Procedure

#### Step 1: Add Multiple Routes in Source VRF
```bash
sonic(config)# router bgp 65001 vrf VRF-BLUE
sonic(config-router-bgp-af)# network 10.10.0.0/24
sonic(config-router-bgp-af)# network 10.20.0.0/24
sonic(config-router-bgp-af)# network 192.168.1.0/24
```

#### Step 2: Create Selective Route-map
```bash
sonic(config)# ip prefix-list IMPORT-FILTER seq 10 permit 10.10.0.0/24
sonic(config)# route-map SELECTIVE-IMPORT permit 10
sonic(config-route-map)# match ip address prefix-list IMPORT-FILTER
sonic(config-route-map)# exit
sonic(config)# route-map SELECTIVE-IMPORT deny 20
```

#### Step 3: Configure Import with Route-map
```bash
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map SELECTIVE-IMPORT
```

#### Step 4: Verify Selective Import
```bash
sonic# show ip bgp vrf VRF-RED
# Expected: Only 10.10.0.0/24 present
# Expected: 10.20.0.0/24 and 192.168.1.0/24 absent
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Allowed Route | 10.10.0.0/24 imported to VRF-RED |
| Denied Routes | 10.20.0.0/24, 192.168.1.0/24 NOT imported |
| Route-map Applied | Only matched prefixes imported |

### Pass/Fail Criteria

- **PASS**: Only 10.10.0.0/24 imported, others filtered
- **FAIL**: Denied routes appear or allowed route missing

---

## TC-BGP-CLI-VRF-IMPORT-007: VRF Import with Attribute Modification

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-007 |
| **Feature** | BGP VRF Import with Attribute Modification |
| **Priority** | High |
| **Test Type** | Positive - Configuration |
| **CLI Type** | Klish |

### Test Objective

Verify that route-map can modify BGP attributes (local-preference, MED, AS-path, community) during VRF import.

### Test Configuration

| Attribute | Original Value | Modified Value |
|-----------|---------------|----------------|
| Local-preference | 100 (default) | 250 |
| MED | - | 50 |
| Community | - | 65001:100 |
| AS-path Prepend | - | 65001 65001 |

### Test Procedure

#### Step 1: Create Attribute-Modifying Route-map
```bash
sonic(config)# route-map MODIFY-ATTRS permit 10
sonic(config-route-map)# set local-preference 250
sonic(config-route-map)# set metric 50
sonic(config-route-map)# set community 65001:100
sonic(config-route-map)# set as-path prepend 65001 65001
sonic(config-route-map)# exit
```

#### Step 2: Apply to VRF Import
```bash
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map MODIFY-ATTRS
```

#### Step 3: Verify Attribute Modification
```bash
sonic# show ip bgp vrf VRF-RED 10.10.10.0/24
# Expected attributes:
# Local-pref: 250
# MED: 50
# Community: 65001:100
# AS-path: 65001 65001 (prepended)
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Local-preference | Set to 250 |
| MED | Set to 50 |
| Community | 65001:100 added |
| AS-path | Prepended with 65001 65001 |
| Route Import | Route successfully imported with modified attributes |

### Pass/Fail Criteria

- **PASS**: All attributes modified as configured
- **FAIL**: Attributes not modified or import fails

---

# NEGATIVE TEST CASES

---

## TC-BGP-CLI-REDIST-NEG-001: Redistribute Non-existent OSPF Process

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-NEG-001 |
| **Feature** | BGP Redistribution Error Handling |
| **Priority** | Medium |
| **Test Type** | Negative - Error Detection |
| **CLI Type** | Klish |

### Test Objective

Verify system behavior when redistributing OSPF routes when no OSPF process is configured.

### Test Procedure

#### Step 1: Ensure No OSPF Process Running
```bash
sonic# show ip ospf
# Expected: No OSPF process or "OSPF Routing Process not enabled"
```

#### Step 2: Attempt OSPF Redistribution
```bash
sonic# configure terminal
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# redistribute ospf
sonic(config-router-bgp-af)# end
```

#### Step 3: Verify Behavior
```bash
sonic# show running-config | section "redistribute"
# Check if command accepted or rejected
sonic# show ip bgp
# Check if any routes redistributed (should be none)
```

### Expected Results

**Acceptable Behavior Option 1: Command Accepted, No Routes**
- Configuration accepted
- No routes redistributed (no OSPF routes to redistribute)
- System remains stable

**Acceptable Behavior Option 2: Warning/Error Message**
- Warning: "OSPF process not found"
- Configuration accepted but inactive
- No system instability

### Pass/Fail Criteria

- **PASS**: System handles gracefully (either option above)
- **FAIL**: System crash, BGP session down, or unexpected behavior

---

## TC-BGP-CLI-REDIST-NEG-002: Redistribute with Invalid Metric

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-NEG-002 |
| **Feature** | BGP Redistribution Input Validation |
| **Priority** | High |
| **Test Type** | Negative - Input Validation |
| **CLI Type** | Klish |

### Test Objective

Verify that invalid metric values are rejected with appropriate error messages.

### Test Procedure

#### Step 1: Test Invalid Metric Values
```bash
# Test negative metric
sonic(config-router-bgp-af)# redistribute ospf metric -1
# Expected: Error or rejected

# Test out-of-range metric (> 4294967295)
sonic(config-router-bgp-af)# redistribute ospf metric 999999999999
# Expected: Error or rejected

# Test non-numeric metric
sonic(config-router-bgp-af)# redistribute ospf metric abc
# Expected: Error or rejected

# Test metric 0 (edge case - may be valid or invalid)
sonic(config-router-bgp-af)# redistribute ospf metric 0
# Document behavior
```

### Expected Results

| Test Input | Expected Result |
|------------|-----------------|
| metric -1 | Rejected: "Invalid metric value" |
| metric 999999999999 | Rejected: "Metric out of range (0-4294967295)" |
| metric abc | Rejected: "Invalid number format" |
| metric 0 | Accepted or rejected (document actual behavior) |

### Pass/Fail Criteria

- **PASS**: Invalid values rejected with clear error messages
- **FAIL**: Invalid values accepted or system instability

---

## TC-BGP-CLI-REDIST-NEG-003: Redistribute with Non-existent Route-map

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-NEG-003 |
| **Feature** | BGP Redistribution Route-map Validation |
| **Priority** | High |
| **Test Type** | Negative - Reference Validation |
| **CLI Type** | Klish |

### Test Objective

Verify behavior when redistributing with a route-map that doesn't exist.

### Test Procedure

#### Step 1: Verify Route-map Doesn't Exist
```bash
sonic# show route-map NON-EXISTENT-MAP
# Expected: Route-map not found
```

#### Step 2: Attempt Redistribution with Non-existent Route-map
```bash
sonic(config-router-bgp-af)# redistribute ospf route-map NON-EXISTENT-MAP
```

#### Step 3: Check Behavior
```bash
sonic# show running-config | section "redistribute"
sonic# show ip bgp
```

### Expected Results

**Option 1: Reject Configuration**
- Error: "Route-map NON-EXISTENT-MAP not found"
- Configuration not accepted

**Option 2: Accept with Warning**
- Warning: "Route-map not found, will activate when created"
- Configuration accepted but inactive
- No routes redistributed until route-map created

### Pass/Fail Criteria

- **PASS**: Handled gracefully with clear message
- **FAIL**: System accepts silently with unexpected behavior

---

## TC-BGP-CLI-REDIST-NEG-004: Duplicate Redistribute Statements

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-NEG-004 |
| **Feature** | BGP Redistribution Duplicate Detection |
| **Priority** | Medium |
| **Test Type** | Negative - Duplicate Detection |
| **CLI Type** | Klish |

### Test Objective

Verify system behavior when same protocol is redistributed multiple times with different parameters.

### Test Procedure

#### Step 1: Configure First Redistribution
```bash
sonic(config-router-bgp-af)# redistribute ospf metric 100
```

#### Step 2: Attempt Duplicate with Different Metric
```bash
sonic(config-router-bgp-af)# redistribute ospf metric 200
```

#### Step 3: Verify Configuration
```bash
sonic# show running-config | section "redistribute"
```

### Expected Results

**Option 1: Last Configuration Wins**
- Second command replaces first
- Only `redistribute ospf metric 200` in config

**Option 2: First Configuration Preserved**
- Second command rejected or ignored
- Only `redistribute ospf metric 100` remains

**Option 3: Error Message**
- Error: "OSPF redistribution already configured"

### Pass/Fail Criteria

- **PASS**: Consistent, documented behavior
- **FAIL**: Both redistributions active causing conflicts

---

## TC-BGP-CLI-REDIST-NEG-005: Remove Non-existent Redistribution

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-NEG-005 |
| **Feature** | BGP Redistribution Removal Validation |
| **Priority** | Low |
| **Test Type** | Negative - Idempotency |
| **CLI Type** | Klish |

### Test Objective

Verify that removing non-existent redistribution doesn't cause errors or system instability.

### Test Procedure

#### Step 1: Ensure No OSPF Redistribution
```bash
sonic# show running-config | section "redistribute"
# Verify no "redistribute ospf" present
```

#### Step 2: Attempt to Remove
```bash
sonic(config-router-bgp-af)# no redistribute ospf
```

#### Step 3: Verify No Error
```bash
sonic# show ip bgp summary
# Verify BGP session still UP
```

### Expected Results

| Verification Point | Expected Result |
|-------------------|-----------------|
| Command Execution | Accepted without error (idempotent) |
| BGP Session | Remains UP and stable |
| Configuration | Unchanged |
| System Log | No error messages logged |

### Pass/Fail Criteria

- **PASS**: Command accepted gracefully (idempotent operation)
- **FAIL**: Error message or BGP session disruption

---

## TC-BGP-CLI-VRF-IMPORT-NEG-001: Import from Non-existent VRF

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-NEG-001 |
| **Feature** | BGP VRF Import Validation |
| **Priority** | High |
| **Test Type** | Negative - Reference Validation |
| **CLI Type** | Klish |

### Test Objective

Verify error handling when attempting to import routes from a VRF that doesn't exist.

### Test Procedure

#### Step 1: Verify VRF Doesn't Exist
```bash
sonic# show ip vrf
# Verify VRF-NONEXISTENT not in list
```

#### Step 2: Attempt Import
```bash
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp-af)# import vrf VRF-NONEXISTENT route-map TEST
```

#### Step 3: Verify Error Handling
```bash
sonic# show running-config | section "import vrf"
```

### Expected Results

**Option 1: Reject Configuration**
- Error: "VRF VRF-NONEXISTENT does not exist"
- Configuration not accepted

**Option 2: Accept with Warning**
- Warning: "Source VRF not found"
- Configuration accepted but inactive

### Pass/Fail Criteria

- **PASS**: Clear error/warning message, system stable
- **FAIL**: Configuration silently accepted with undefined behavior

---

## TC-BGP-CLI-VRF-IMPORT-NEG-002: Import into Non-existent VRF

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-NEG-002 |
| **Feature** | BGP VRF Import Context Validation |
| **Priority** | High |
| **Test Type** | Negative - Context Validation |
| **CLI Type** | Klish |

### Test Objective

Verify error when attempting to configure import in BGP context for a VRF that doesn't exist.

### Test Procedure

#### Step 1: Attempt BGP Config in Non-existent VRF
```bash
sonic(config)# router bgp 65001 vrf VRF-NONEXISTENT
# May fail here or in subsequent commands
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map TEST
```

### Expected Results

**Option 1: Reject at VRF Context**
- Error: "VRF VRF-NONEXISTENT not configured"
- Cannot enter BGP VRF context

**Option 2: Allow Context, Reject Import**
- BGP VRF context entered
- Import command rejected

### Pass/Fail Criteria

- **PASS**: Appropriate error at some stage, no system instability
- **FAIL**: Configuration accepted with undefined behavior

---

## TC-BGP-CLI-VRF-IMPORT-NEG-003: Self-Import (VRF imports from itself)

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-NEG-003 |
| **Feature** | BGP VRF Import Loop Detection |
| **Priority** | High |
| **Test Type** | Negative - Loop Detection |
| **CLI Type** | Klish |

### Test Objective

Verify that a VRF cannot import routes from itself (loop prevention).

### Test Procedure

#### Step 1: Attempt Self-Import
```bash
sonic(config)# router bgp 65001 vrf VRF-RED
sonic(config-router-bgp-af)# import vrf VRF-RED route-map TEST
```

### Expected Results

| Expected Behavior | Result |
|------------------|--------|
| Error Message | "Cannot import from same VRF" or similar |
| Configuration | Rejected |
| System Stability | No routing loops or instability |

### Pass/Fail Criteria

- **PASS**: Self-import rejected with clear error
- **FAIL**: Self-import accepted (potential routing loop)

---

## TC-BGP-CLI-VRF-IMPORT-NEG-004: Circular VRF Import (A→B→A)

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-NEG-004 |
| **Feature** | BGP VRF Import Circular Dependency Detection |
| **Priority** | High |
| **Test Type** | Negative - Loop Detection |
| **CLI Type** | Klish |

### Test Objective

Verify detection of circular VRF import dependencies (VRF-A imports from VRF-B which imports from VRF-A).

### Test Procedure

#### Step 1: Configure VRF-A Imports from VRF-B
```bash
sonic(config)# router bgp 65001 vrf VRF-A
sonic(config-router-bgp-af)# import vrf VRF-B route-map AB-RM
```

#### Step 2: Attempt Circular Import (VRF-B imports from VRF-A)
```bash
sonic(config)# router bgp 65001 vrf VRF-B
sonic(config-router-bgp-af)# import vrf VRF-A route-map BA-RM
```

### Expected Results

**Option 1: Detect and Prevent**
- Error: "Circular VRF import dependency detected"
- Second import rejected

**Option 2: Allow but Monitor**
- Both imports accepted
- System prevents routing loops via TTL or other mechanism
- Warning logged

### Pass/Fail Criteria

- **PASS**: System handles circular dependency safely
- **FAIL**: Routing loop causes CPU spike or route churn

---

## TC-BGP-CLI-VRF-IMPORT-NEG-005: Import with Invalid Route-map Syntax

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-NEG-005 |
| **Feature** | BGP VRF Import Syntax Validation |
| **Priority** | Medium |
| **Test Type** | Negative - Syntax Validation |
| **CLI Type** | Klish |

### Test Objective

Verify proper error messages for malformed import vrf commands.

### Test Procedure

#### Test Various Invalid Syntaxes
```bash
# Missing route-map name
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map
# Expected: Syntax error

# Invalid characters in VRF name
sonic(config-router-bgp-af)# import vrf VRF@BLUE route-map TEST
# Expected: Invalid VRF name

# Extra parameters
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map TEST extra-param
# Expected: Unrecognized command
```

### Expected Results

| Invalid Syntax | Expected Error |
|---------------|----------------|
| Missing route-map name | "Incomplete command" |
| Invalid VRF name chars | "Invalid VRF name format" |
| Extra parameters | "Unrecognized option: extra-param" |

### Pass/Fail Criteria

- **PASS**: All malformed commands rejected with clear errors
- **FAIL**: Malformed commands accepted or unclear errors

---

## TC-BGP-CLI-REDIST-NEG-006: Redistribute in Wrong Address Family

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-NEG-006 |
| **Feature** | BGP Redistribution Address Family Validation |
| **Priority** | Medium |
| **Test Type** | Negative - Context Validation |
| **CLI Type** | Klish |

### Test Objective

Verify that redistributing IPv4 OSPF routes in IPv6 address family (and vice versa) is properly handled or rejected.

### Test Procedure

#### Step 1: Attempt IPv4 OSPF in IPv6 AF
```bash
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv6 unicast
sonic(config-router-bgp-af)# redistribute ospf
# Should be rejected or not redistribute any routes
```

#### Step 2: Attempt IPv6 OSPFv3 in IPv4 AF
```bash
sonic(config)# router bgp 65001
sonic(config-router-bgp)# address-family ipv4 unicast
sonic(config-router-bgp-af)# redistribute ospfv3
# Should be rejected or not redistribute any routes
```

### Expected Results

**Option 1: Command Rejected**
- Error: "Cannot redistribute ospf in IPv6 address family"
- Configuration not accepted

**Option 2: Command Accepted but Inactive**
- Configuration accepted with warning
- No routes redistributed (address family mismatch)

### Pass/Fail Criteria

- **PASS**: Mismatch detected and handled appropriately
- **FAIL**: Wrong address family routes redistributed

---

# EDGE CASE TEST CASES

---

## TC-BGP-CLI-REDIST-EDGE-001: Redistribute with Maximum Metric Value

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-EDGE-001 |
| **Feature** | BGP Redistribution Boundary Value Testing |
| **Priority** | Low |
| **Test Type** | Edge Case - Boundary Value |
| **CLI Type** | Klish |

### Test Objective

Test redistribution with maximum allowed metric value (4294967295 for 32-bit unsigned integer).

### Test Procedure

```bash
sonic(config-router-bgp-af)# redistribute ospf metric 4294967295
```

### Expected Results

- Configuration accepted
- Routes redistributed with MED = 4294967295
- No overflow or unexpected behavior

### Pass/Fail Criteria

- **PASS**: Maximum metric accepted and applied correctly
- **FAIL**: Overflow, rejection, or incorrect value

---

## TC-BGP-CLI-REDIST-EDGE-002: Redistribute with Metric Zero

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-EDGE-002 |
| **Feature** | BGP Redistribution Zero Metric |
| **Priority** | Low |
| **Test Type** | Edge Case - Zero Value |
| **CLI Type** | Klish |

### Test Objective

Test redistribution with metric value of zero.

### Test Procedure

```bash
sonic(config-router-bgp-af)# redistribute ospf metric 0
```

### Expected Results

- Configuration accepted or rejected (document behavior)
- If accepted, routes have MED = 0
- No unexpected behavior

### Pass/Fail Criteria

- **PASS**: Consistent documented behavior
- **FAIL**: System instability or inconsistent handling

---

## TC-BGP-CLI-REDIST-EDGE-003: Large-Scale Route Redistribution

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-EDGE-003 |
| **Feature** | BGP Redistribution Scalability |
| **Priority** | Medium |
| **Test Type** | Edge Case - Scale Testing |
| **CLI Type** | Klish |

### Test Objective

Verify system stability when redistributing a large number of routes (10,000+ routes) from OSPF into BGP.

### Test Procedure

#### Step 1: Create Large OSPF Route Table
```bash
# Use route injection or static routes to create 10,000+ OSPF routes
```

#### Step 2: Enable Redistribution
```bash
sonic(config-router-bgp-af)# redistribute ospf
```

#### Step 3: Monitor System Resources
```bash
sonic# show processes cpu
sonic# show processes memory
sonic# show ip bgp summary
sonic# show ip bgp | wc -l  # Count BGP routes
```

### Expected Results

- All OSPF routes successfully redistributed
- BGP sessions remain stable
- CPU and memory usage acceptable
- No route loss or corruption

### Pass/Fail Criteria

- **PASS**: Large-scale redistribution succeeds without instability
- **FAIL**: BGP session flaps, routes lost, or system instability

---

## TC-BGP-CLI-REDIST-EDGE-004: Rapid Redistribution Add/Remove

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-EDGE-004 |
| **Feature** | BGP Redistribution Rapid Configuration Changes |
| **Priority** | Medium |
| **Test Type** | Edge Case - Stress Testing |
| **CLI Type** | Klish |

### Test Objective

Test system stability when rapidly adding and removing redistribution configuration.

### Test Procedure

```bash
# Repeat 50 times in quick succession:
for i in {1..50}; do
  sonic(config-router-bgp-af)# redistribute ospf metric $i
  sonic(config-router-bgp-af)# no redistribute ospf
done
```

### Expected Results

- System remains stable
- Final configuration state is consistent
- BGP sessions remain UP
- No route flapping or memory leaks

### Pass/Fail Criteria

- **PASS**: System handles rapid changes gracefully
- **FAIL**: Crash, memory leak, or BGP session instability

---

## TC-BGP-CLI-REDIST-EDGE-005: Redistribute Route-map with Empty Match Conditions

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-REDIST-EDGE-005 |
| **Feature** | BGP Redistribution Route-map Edge Cases |
| **Priority** | Low |
| **Test Type** | Edge Case - Empty Match |
| **CLI Type** | Klish |

### Test Objective

Test redistribution with a route-map that has no match conditions (permit all).

### Test Procedure

#### Step 1: Create Empty Route-map
```bash
sonic(config)# route-map EMPTY-MATCH permit 10
sonic(config-route-map)# set metric 100
sonic(config-route-map)# exit
# No match conditions defined
```

#### Step 2: Apply to Redistribution
```bash
sonic(config-router-bgp-af)# redistribute ospf route-map EMPTY-MATCH
```

### Expected Results

- All OSPF routes redistributed (no filtering)
- Metric set to 100 for all routes
- Behaves as "permit all" route-map

### Pass/Fail Criteria

- **PASS**: Empty route-map permits all routes
- **FAIL**: No routes redistributed or unexpected filtering

---

## TC-BGP-CLI-VRF-IMPORT-EDGE-001: Import VRF with Long VRF Name

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-EDGE-001 |
| **Feature** | BGP VRF Import Name Length Validation |
| **Priority** | Low |
| **Test Type** | Edge Case - Boundary Value |
| **CLI Type** | Klish |

### Test Objective

Test VRF import with maximum allowed VRF name length (typically 32 or 64 characters).

### Test Procedure

```bash
# Create VRF with maximum length name
sonic(config)# ip vrf VRF_NAME_WITH_EXACTLY_SIXTY_FOUR_CHARS_ABCDEFGHIJKLMNOPQR

# Attempt import
sonic(config-router-bgp-af)# import vrf VRF_NAME_WITH_EXACTLY_SIXTY_FOUR_CHARS_ABCDEFGHIJKLMNOPQR route-map TEST
```

### Expected Results

- Long VRF name accepted if within limits
- Import configuration succeeds
- No truncation or corruption of VRF name

### Pass/Fail Criteria

- **PASS**: Long VRF names handled correctly
- **FAIL**: Name truncated, rejected improperly, or system error

---

## TC-BGP-CLI-VRF-IMPORT-EDGE-002: Import with Route-map Referencing Non-existent Prefix-list

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-EDGE-002 |
| **Feature** | BGP VRF Import Route-map Dependency Chain |
| **Priority** | Medium |
| **Test Type** | Edge Case - Dependency Validation |
| **CLI Type** | Klish |

### Test Objective

Test VRF import with route-map that references a non-existent prefix-list.

### Test Procedure

#### Step 1: Create Route-map with Non-existent Prefix-list Reference
```bash
sonic(config)# route-map VRF-IMPORT-RM permit 10
sonic(config-route-map)# match ip address prefix-list NON-EXISTENT-PL
sonic(config-route-map)# exit
```

#### Step 2: Apply to VRF Import
```bash
sonic(config-router-bgp-af)# import vrf VRF-BLUE route-map VRF-IMPORT-RM
```

#### Step 3: Verify Behavior
```bash
sonic# show ip bgp vrf VRF-RED
# Check if routes imported or blocked due to missing prefix-list
```

### Expected Results

**Option 1: Block All Routes**
- Route-map match fails (no prefix-list)
- No routes imported (safe behavior)

**Option 2: Permit All Routes**
- Missing prefix-list treated as "match any"
- All routes imported (permissive behavior)

### Pass/Fail Criteria

- **PASS**: Consistent documented behavior
- **FAIL**: Unpredictable behavior or system instability

---

## TC-BGP-CLI-VRF-IMPORT-EDGE-003: Import VRF Chain (A→B→C)

### Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC-BGP-CLI-VRF-IMPORT-EDGE-003 |
| **Feature** | BGP VRF Import Chaining |
| **Priority** | Medium |
| **Test Type** | Edge Case - Transitive Import |
| **CLI Type** | Klish |

### Test Objective

Test VRF import chain: VRF-A has routes, VRF-B imports from VRF-A, VRF-C imports from VRF-B. Verify if VRF-C receives VRF-A's routes transitively.

### Test Configuration

```
VRF-A: 10.10.0.0/24 (native route)
VRF-B: import from VRF-A
VRF-C: import from VRF-B
```

### Test Procedure

#### Step 1: Create Route in VRF-A
```bash
sonic(config)# router bgp 65001 vrf VRF-A
sonic(config-router-bgp-af)# network 10.10.0.0/24
```

#### Step 2: VRF-B Imports from VRF-A
```bash
sonic(config)# router bgp 65001 vrf VRF-B
sonic(config-router-bgp-af)# import vrf VRF-A route-map AB-RM
```

#### Step 3: VRF-C Imports from VRF-B
```bash
sonic(config)# router bgp 65001 vrf VRF-C
sonic(config-router-bgp-af)# import vrf VRF-B route-map BC-RM
```

#### Step 4: Verify Transitive Import
```bash
sonic# show ip bgp vrf VRF-C
# Check if 10.10.0.0/24 appears in VRF-C
```

### Expected Results

**Option 1: Transitive Import Supported**
- 10.10.0.0/24 appears in VRF-C
- Route imported transitively through VRF-B

**Option 2: No Transitive Import**
- 10.10.0.0/24 NOT in VRF-C
- Only direct imports supported

### Pass/Fail Criteria

- **PASS**: Consistent documented behavior (transitive or non-transitive)
- **FAIL**: Unpredictable or inconsistent results

---

# TEST EXECUTION SUMMARY

## Summary Table

| Category | Test Cases | Pass Criteria |
|----------|-----------|---------------|
| Positive Tests | 15 | All configurations accepted and functional |
| Negative Tests | 12 | Errors handled gracefully with clear messages |
| Edge Cases | 8 | System remains stable under boundary conditions |
| **TOTAL** | **35** | **100% pass rate required for certification** |

---

## Automation Recommendations

### Test Script Structure

```python
# Test file: test_bgp_redistribute_vrf_import.py

TC_IDS = SpyTestDict({
    # Positive tests
    "redist_ospf_basic": "TC-BGP-CLI-REDIST-001",
    "redist_ospfv3": "TC-BGP-CLI-REDIST-002",
    "redist_metric": "TC-BGP-CLI-REDIST-003",
    "redist_routemap": "TC-BGP-CLI-REDIST-004",
    "redist_multiple": "TC-BGP-CLI-REDIST-005",
    "redist_remove": "TC-BGP-CLI-REDIST-006",
    "redist_remove_metric": "TC-BGP-CLI-REDIST-007",
    "vrf_import_basic": "TC-BGP-CLI-VRF-IMPORT-001",
    "vrf_import_no_rm": "TC-BGP-CLI-VRF-IMPORT-002",
    "vrf_import_remove": "TC-BGP-CLI-VRF-IMPORT-003",
    "vrf_import_remove_rm": "TC-BGP-CLI-VRF-IMPORT-004",
    "vrf_import_multiple": "TC-BGP-CLI-VRF-IMPORT-005",
    "vrf_import_filtering": "TC-BGP-CLI-VRF-IMPORT-006",
    "vrf_import_attrs": "TC-BGP-CLI-VRF-IMPORT-007",

    # Negative tests
    "redist_no_ospf": "TC-BGP-CLI-REDIST-NEG-001",
    "redist_invalid_metric": "TC-BGP-CLI-REDIST-NEG-002",
    "redist_no_routemap": "TC-BGP-CLI-REDIST-NEG-003",
    "redist_duplicate": "TC-BGP-CLI-REDIST-NEG-004",
    "redist_remove_nonexist": "TC-BGP-CLI-REDIST-NEG-005",
    "vrf_import_no_source": "TC-BGP-CLI-VRF-IMPORT-NEG-001",
    "vrf_import_no_dest": "TC-BGP-CLI-VRF-IMPORT-NEG-002",
    "vrf_import_self": "TC-BGP-CLI-VRF-IMPORT-NEG-003",
    "vrf_import_circular": "TC-BGP-CLI-VRF-IMPORT-NEG-004",
    "vrf_import_invalid_syntax": "TC-BGP-CLI-VRF-IMPORT-NEG-005",
    "redist_wrong_af": "TC-BGP-CLI-REDIST-NEG-006",

    # Edge cases
    "redist_max_metric": "TC-BGP-CLI-REDIST-EDGE-001",
    "redist_zero_metric": "TC-BGP-CLI-REDIST-EDGE-002",
    "redist_scale": "TC-BGP-CLI-REDIST-EDGE-003",
    "redist_rapid": "TC-BGP-CLI-REDIST-EDGE-004",
    "redist_empty_rm": "TC-BGP-CLI-REDIST-EDGE-005",
    "vrf_import_long_name": "TC-BGP-CLI-VRF-IMPORT-EDGE-001",
    "vrf_import_missing_pl": "TC-BGP-CLI-VRF-IMPORT-EDGE-002",
    "vrf_import_chain": "TC-BGP-CLI-VRF-IMPORT-EDGE-003",
})
```

### YAML Configuration File

```yaml
# vars_bgp_redistribute_vrf_import.yaml

defaults:
  config_cli_type: klish
  show_cli_type: klish
  verify_timeout: 90
  cleanup: true

topology:
  min_topology: ["D1D2:1", "D2D3:1"]  # 3RR topology

bgp_config:
  as_number: 65001
  router_ids:
    D1: "1.1.1.1"
    D2: "2.2.2.2"
    D3: "3.3.3.3"

ospf_config:
  process_id: 100
  area: "0.0.0.0"

vrf_config:
  vrfs:
    - VRF-BLUE
    - VRF-RED
    - VRF-GREEN
    - VRF-YELLOW

test_prefixes:
  ospf_routes:
    - "1.1.1.1/32"
    - "10.1.1.0/30"
  static_routes:
    - "192.168.1.0/24"
  vrf_routes:
    VRF-BLUE: ["10.10.0.0/24", "10.20.0.0/24"]
    VRF-GREEN: ["10.30.0.0/24"]
    VRF-YELLOW: ["10.40.0.0/24"]
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-28 | Claude Code | Initial document creation with 35 test cases |

---

**End of Test Case Document**
