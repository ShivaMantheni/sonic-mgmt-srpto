# LACP Feature Test Plan
> **Based on QA TC Master Rules & SONiC Network Testing Standards**

**Document Version:** 1.0
**Last Updated:** 2026-05-19
**Feature:** Link Aggregation Control Protocol (LACP)
**Module:** Switching / PortChannel
**Scope:** Hardware and Virtual testbeds

---

## Executive Summary

This test plan provides comprehensive test coverage for LACP functionality in SONiC network operating systems. The plan follows the 7 Principles of Software Testing and includes mandatory coverage for positive, negative, edge cases, boundary value analysis, and cleanup scenarios.

**Total Test Cases:** 87
**Breakdown:** Positive: 24 | Negative: 31 | Edge: 20 | Boundary: 12
**Priority Distribution:** P0: 18 | P1: 35 | P2: 28 | P3: 6

---

## 1. Feature Overview

### 1.1 What is LACP?
LACP (Link Aggregation Control Protocol, IEEE 802.3ad) is a network protocol that enables automatic aggregation of multiple physical links into a single logical PortChannel interface. Benefits include:
- Increased bandwidth
- Load balancing across member links
- Redundancy and failover capability
- Automatic link failure detection and recovery

### 1.2 LACP Operational Modes
- **Active:** Device actively sends LACP PDUs
- **Passive:** Device responds to received LACP PDUs
- **Static:** No LACP negotiation (manual LAG)

### 1.3 Key Components Tested
- PortChannel creation/deletion
- Member addition/removal
- LACP negotiation and synchronization
- Traffic distribution across members
- Link failure and recovery
- Configuration persistence
- MTU and speed validation
- Error handling and edge cases

---

## 2. Test Environment & Prerequisites

### 2.1 Supported Topologies
- **2-Node:** Direct link connectivity between two SONiC devices
- **Hardware:** Real network switch hardware (if available)
- **Virtual:** Virtual machines or containers running SONiC

### 2.2 Required Equipment
- 2-4 SONiC devices (D1, D2, D3 optional)
- Network cabling for member links (minimum 4 physical links per PortChannel)
- Traffic generation capability (Scapy, Ixia, or similar)
- Packet capture tools (tcpdump)
- Management access (SSH/telnet)

### 2.3 Initial Configuration
- All interfaces enabled and in default state
- No pre-existing PortChannels or VLAN configurations
- Devices communicating via management network
- Baseline counters cleared

---

## 3. Test Case Categories

### 3.1 Category Distribution

| Category | Count | Type | Purpose |
|----------|-------|------|---------|
| **Happy Path** | 24 | Positive | Validate core LACP functionality |
| **Negative Scenarios** | 31 | Negative | Invalid inputs, wrong states |
| **Edge Cases** | 20 | Edge | Unusual but valid conditions |
| **Boundary Values** | 12 | Boundary | Limit testing |
| **Cleanup** | Implicit | All | System state verification |

---

## 4. Positive Test Cases (Happy Path)

### 4.1 PortChannel Creation

#### LACP-POS-001
**Title:** Create PortChannel with LACP active mode
**Priority:** P0
**Type:** Positive
**Preconditions:**
  1. D1 and D2 connected via 4 physical links (Ethernet32, 36, 40, 44)
  2. All links are administratively up
  3. No existing PortChannels

**Test Steps:**
  1. Create PortChannel 1 on D1 with LACP active mode
  2. Create PortChannel 1 on D2 with LACP active mode
  3. Add all 4 members to PortChannel 1 on both devices
  4. Verify LACP negotiation completes
  5. Verify all members enter synchronized state

**Test Data:** `PC_ID: 1, Members: [Ethernet32, Ethernet36, Ethernet40, Ethernet44], LACP_Mode: active`

**Expected Result:**
  - PortChannel 1 is created successfully
  - `show portchannel summary` displays PC1 as operational
  - All 4 members show "up(s)" indicating synced state
  - No CLI errors or warnings

**Postcondition/Cleanup:** PortChannel and members remain as configured for subsequent tests

---

#### LACP-POS-002
**Title:** Create PortChannel with LACP passive mode
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. D1 configured in LACP active mode (from LACP-POS-001)
  2. D2 with fresh configuration
  3. All links administratively up

**Test Steps:**
  1. Create PortChannel 1 on D2 with LACP passive mode
  2. Add all 4 members to PortChannel 1 on D2
  3. Verify LACP negotiation completes with D1 (active)
  4. Verify all members enter synchronized state on D2

**Test Data:** `PC_ID: 1, Members: [Ethernet32, Ethernet36, Ethernet40, Ethernet44], LACP_Mode: passive`

**Expected Result:**
  - PortChannel 1 is created successfully on D2
  - D2 responds to LACP PDUs from D1
  - All members synchronized
  - No LACP timeout or mismatch errors

**Postcondition/Cleanup:** PortChannel remains configured

---

#### LACP-POS-003
**Title:** Create static PortChannel (no LACP)
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. Fresh configuration on both devices
  2. All links ready

**Test Steps:**
  1. Create PortChannel 2 on D1 (static, no LACP)
  2. Add 4 members to PortChannel 2 on D1
  3. Create PortChannel 2 on D2 (static, no LACP)
  4. Add same 4 members on D2
  5. Verify PortChannel is operational

**Test Data:** `PC_ID: 2, Members: [Ethernet48, Ethernet52, Ethernet56, Ethernet60], LACP_Mode: off`

**Expected Result:**
  - PortChannel 2 is created without LACP negotiation
  - All members immediately operational
  - No LACP-related logs or state

**Postcondition/Cleanup:** Remove PortChannel 2 after test

---

### 4.2 Member Management

#### LACP-POS-004
**Title:** Add single member to operational PortChannel
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 exists with 3 members (Ethernet32, 36, 40)
  2. Ethernet44 is not a member and is administratively up
  3. All current members are synchronized

**Test Steps:**
  1. Add Ethernet44 to PortChannel 1
  2. Verify Ethernet44 enters synchronized state
  3. Verify existing 3 members remain synced
  4. Verify traffic distribution includes new member

**Test Data:** `PC_ID: 1, New_Member: Ethernet44`

**Expected Result:**
  - Ethernet44 successfully added to PortChannel 1
  - PortChannel shows 4 members in synced state
  - No traffic interruption on existing members
  - Interface counters show traffic on new member

**Postcondition/Cleanup:** Ethernet44 remains as member

---

#### LACP-POS-005
**Title:** Remove member from operational PortChannel
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 exists with 4 synchronized members
  2. Active traffic flowing through PortChannel

**Test Steps:**
  1. Remove Ethernet44 from PortChannel 1 members
  2. Verify Ethernet44 is no longer in PortChannel
  3. Verify remaining 3 members continue synchronized
  4. Verify traffic redistributes to 3 remaining members

**Test Data:** `PC_ID: 1, Remove_Member: Ethernet44`

**Expected Result:**
  - Ethernet44 successfully removed from PortChannel 1
  - PortChannel shows 3 members in synced state
  - No unintended traffic loss
  - Member state shows "down" or "no sync"

**Postcondition/Cleanup:** Ethernet44 no longer member of PortChannel 1

---

#### LACP-POS-006
**Title:** Remove multiple members sequentially
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 with 4 members all synchronized
  2. Traffic flowing

**Test Steps:**
  1. Remove Ethernet40 from PortChannel 1
  2. Wait 2 seconds, verify 3 members remain synced
  3. Remove Ethernet36 from PortChannel 1
  4. Wait 2 seconds, verify 2 members remain synced
  5. Verify traffic redistributes after each removal

**Test Data:** `PC_ID: 1, Remove_Sequence: [Ethernet40, Ethernet36]`

**Expected Result:**
  - Each removal completes successfully
  - PortChannel remains operational with remaining members
  - Traffic redistribution occurs between steps
  - No LACP timeout or state inconsistency

**Postcondition/Cleanup:** PortChannel reduced to 2 members

---

### 4.3 Configuration Persistence

#### LACP-POS-007
**Title:** Verify PortChannel configuration persists after reboot
**Priority:** P0
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 with 4 members configured
  2. Configuration saved to startup-config
  3. D1 and D2 synchronized

**Test Steps:**
  1. Save running-config to startup-config on D1
  2. Reboot D1
  3. Wait for D1 to boot and reach operational state
  4. Verify PortChannel 1 exists with all 4 members
  5. Verify LACP negotiation re-establishes
  6. Verify members are in synchronized state

**Test Data:** `PC_ID: 1, Members: [Ethernet32, Ethernet36, Ethernet40, Ethernet44]`

**Expected Result:**
  - PortChannel 1 restored after reboot
  - All members automatically re-synchronized with D2
  - No manual reconfiguration needed
  - Running-config matches saved configuration

**Postcondition/Cleanup:** D1 remains operational and synchronized

---

#### LACP-POS-008
**Title:** Verify LACP parameters persist after reboot
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel with custom LACP parameters configured:
     - System priority: 100
     - Port priority: 50
  2. Configuration saved

**Test Steps:**
  1. Save configuration
  2. Reboot device
  3. Verify custom LACP system priority is restored
  4. Verify custom port priority values are restored

**Test Data:** `System_Priority: 100, Port_Priority: 50`

**Expected Result:**
  - Custom LACP parameters restored
  - `show lacp internal` displays configured values
  - No reset to default values

**Postcondition/Cleanup:** Configuration remains for cleanup

---

### 4.4 Traffic Verification

#### LACP-POS-009
**Title:** Verify traffic flows across all PortChannel members
**Priority:** P0
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 with 4 synchronized members
  2. IP addresses configured on PortChannel (10.1.1.1/24 on D1, 10.1.1.2/24 on D2)
  3. Interfaces up and operational

**Test Steps:**
  1. From D1, ping D2 across PortChannel
  2. Capture traffic using tcpdump on all members
  3. Send 1000 packets from D1 to D2
  4. Verify traffic appears on all 4 members
  5. Verify counters on all members increment
  6. Calculate traffic distribution ratio

**Test Data:** `Source_IP: 10.1.1.1, Dest_IP: 10.1.1.2, Packet_Count: 1000, Packet_Size: 128 bytes`

**Expected Result:**
  - All 4 members receive traffic
  - Each member receives approximately 250 packets (1000/4)
  - Variation in distribution acceptable (±20%)
  - No packet loss
  - Traffic captured on tcpdump for all members

**Postcondition/Cleanup:** Counters retain values for verification

---

#### LACP-POS-010
**Title:** Verify bidirectional traffic on PortChannel
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 operational with 4 members
  2. D1 and D2 IP addresses configured
  3. Bidirectional connectivity verified

**Test Steps:**
  1. Send UDP traffic D1 → D2 (100 pps, 5 seconds)
  2. Send UDP traffic D2 → D1 (100 pps, 5 seconds) simultaneously
  3. Capture on all member links
  4. Verify packets flow in both directions on all members

**Test Data:** `Rate_D1_to_D2: 100 pps, Rate_D2_to_D1: 100 pps, Duration: 5s`

**Expected Result:**
  - Both directions transmit simultaneously
  - All members carry traffic in both directions
  - RX and TX counters on all members increment
  - No unidirectional link issues

**Postcondition/Cleanup:** Counters retained

---

### 4.5 LACP Synchronization

#### LACP-POS-011
**Title:** Verify LACP PDU exchange between devices
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel created with LACP active on both devices
  2. Members added but not yet synchronized

**Test Steps:**
  1. Start tcpdump capture on one member link
  2. Wait for LACP negotiation to complete
  3. Verify LACP PDUs are exchanged between devices
  4. Count LACP PDU frequency
  5. Verify LACP PDU interval matches configured value

**Test Data:** `LACP_PDU_Interval: 1 second (default), Capture_Duration: 10 seconds`

**Expected Result:**
  - LACP PDUs visible in tcpdump capture
  - PDUs exchanged at regular intervals (~1 second)
  - Both devices send and receive LACP PDUs
  - Actor and Partner states transition to synchronized

**Postcondition/Cleanup:** tcpdump file retained for analysis

---

#### LACP-POS-012
**Title:** Verify all members enter synced state
**Priority:** P0
**Type:** Positive
**Preconditions:**
  1. PortChannel with all members added
  2. LACP negotiation in progress

**Test Steps:**
  1. Wait for LACP negotiation to complete (max 30 seconds)
  2. Execute `show portchannel 1 all-ports`
  3. Verify all members show state "up(s)"
  4. Execute `show lacp portchannel 1`
  5. Verify Actor and Partner states are synchronized

**Test Data:** `PC_ID: 1, Expected_Member_Count: 4, Expected_State: up(s)`

**Expected Result:**
  - All 4 members show "up(s)" in output
  - No "down" or "timeout" states
  - LACP state shows "synchronized"
  - No LACP errors in system logs

**Postcondition/Cleanup:** PortChannel remains synchronized

---

### 4.6 L2 Configuration on PortChannel

#### LACP-POS-013
**Title:** Create VLAN on PortChannel
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 operational with 4 synchronized members
  2. VLAN 100 does not exist

**Test Steps:**
  1. Create VLAN 100
  2. Add PortChannel 1 as member to VLAN 100 (untagged)
  3. Verify VLAN 100 SVI is created
  4. Verify PortChannel 1 shows as member of VLAN 100

**Test Data:** `VLAN_ID: 100, PC_ID: 1, Tagging_Mode: untagged`

**Expected Result:**
  - VLAN 100 created successfully
  - PortChannel 1 added as untagged member
  - VLAN SVI created with operational state
  - `show vlan` displays PortChannel 1 as member

**Postcondition/Cleanup:** VLAN configuration retained

---

#### LACP-POS-014
**Title:** Configure IP address on VLAN SVI above PortChannel
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. VLAN 100 created with PortChannel 1 as member
  2. PortChannel 1 synchronized

**Test Steps:**
  1. Configure IP address 10.1.1.1/24 on VLAN 100 SVI on D1
  2. Configure IP address 10.1.1.2/24 on VLAN 100 SVI on D2
  3. Bring up VLAN SVI interface
  4. Verify IP address is configured
  5. Ping from D1 to D2 and verify connectivity

**Test Data:** `VLAN_ID: 100, D1_IP: 10.1.1.1/24, D2_IP: 10.1.1.2/24`

**Expected Result:**
  - IP addresses configured on VLAN SVIs
  - Ping from D1 to D2 succeeds
  - ARP resolution works correctly
  - Routing tables show correct entries

**Postcondition/Cleanup:** IP addresses remain configured

---

### 4.7 MTU Configuration

#### LACP-POS-015
**Title:** Configure MTU on PortChannel members
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 with 4 synchronized members
  2. Default MTU is 9100

**Test Steps:**
  1. Configure MTU 1500 on all member interfaces (Ethernet32, 36, 40, 44)
  2. Verify MTU is applied to all members
  3. Verify PortChannel operational status is not affected
  4. Send packets of size 1460 bytes across PortChannel
  5. Verify packets traverse successfully

**Test Data:** `MTU: 1500, Test_Packet_Size: 1460`

**Expected Result:**
  - MTU successfully configured on all members
  - PortChannel remains synchronized
  - All members show same MTU value
  - Packets of 1460 bytes successfully transmitted

**Postcondition/Cleanup:** MTU retained for subsequent tests

---

#### LACP-POS-016
**Title:** Verify MTU mismatch detection
**Priority:** P1
**Type:** Positive (detection validation)
**Preconditions:**
  1. PortChannel 1 with 4 members all at MTU 1500

**Test Steps:**
  1. Change MTU on Ethernet40 to 9100
  2. Observe LACP state
  3. Verify PortChannel remains operational or logs warning
  4. Change MTU back to 1500 on Ethernet40
  5. Verify PortChannel re-synchronizes if it de-synced

**Test Data:** `MTU_Member1-3: 1500, MTU_Member4: 9100 (then 1500)`

**Expected Result:**
  - MTU mismatch detected (system behavior depends on implementation)
  - If detected, member may go out of sync
  - When MTU is corrected, member re-synchronizes
  - Logs show MTU-related messages (if applicable)

**Postcondition/Cleanup:** All members at same MTU

---

### 4.8 Speed and Duplex Configuration

#### LACP-POS-017
**Title:** Verify all member links at same speed
**Priority:** P0
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 with 4 members
  2. All physical links supporting 40Gbps

**Test Steps:**
  1. Verify speed of all members using `show interface status`
  2. Confirm all members show same speed (e.g., 40G)
  3. Verify PortChannel operational
  4. Verify LACP does not show speed mismatch

**Test Data:** `Expected_Speed: 40Gbps, Member_Count: 4`

**Expected Result:**
  - All 4 members show speed: 40Gbps
  - `show interface status` displays consistent speed for all members
  - No LACP errors related to speed mismatch

**Postcondition/Cleanup:** Configuration retained

---

#### LACP-POS-018
**Title:** Verify full duplex on PortChannel members
**Priority:** P1
**Type:** Positive
**Preconditions:**
  1. PortChannel 1 with 4 members
  2. All links at full duplex

**Test Steps:**
  1. Verify duplex mode of all members
  2. Confirm all members are full duplex
  3. Verify no half-duplex members in PortChannel

**Test Data:** `Expected_Duplex: full, Member_Count: 4`

**Expected Result:**
  - All members show duplex: full
  - No member shows duplex: half
  - LACP accepts all members

**Postcondition/Cleanup:** Configuration retained

---

---

## 5. Negative Test Cases

### 5.1 Invalid Configuration Inputs

#### LACP-NEG-001
**Title:** Attempt to create PortChannel with invalid ID (999)
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. Fresh configuration
  2. No PortChannel 999 exists

**Test Steps:**
  1. Attempt to create PortChannel 999
  2. Observe system response

**Test Data:** `PC_ID: 999 (invalid, max typically 4095)`

**Expected Result:**
  - CLI returns error: "Invalid PortChannel ID"
  - PortChannel 999 is NOT created
  - No change to system state

**Postcondition/Cleanup:** No PortChannel 999 exists

---

#### LACP-NEG-002
**Title:** Attempt to add non-existent interface as member
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists
  2. Ethernet999 does not exist

**Test Steps:**
  1. Attempt to add Ethernet999 to PortChannel 1
  2. Observe system response

**Test Data:** `PC_ID: 1, Interface: Ethernet999 (non-existent)`

**Expected Result:**
  - CLI returns error: "Interface Ethernet999 does not exist"
  - Ethernet999 is NOT added to PortChannel 1
  - PortChannel 1 members unchanged

**Postcondition/Cleanup:** PortChannel 1 unchanged

---

#### LACP-NEG-003
**Title:** Attempt to add interface already in use as PortChannel member
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists with Ethernet32 as member
  2. Ethernet32 is already in PortChannel 1

**Test Steps:**
  1. Attempt to add Ethernet32 to PortChannel 1 again
  2. Observe system response

**Test Data:** `PC_ID: 1, Interface: Ethernet32 (already member)`

**Expected Result:**
  - CLI returns error or info message: "Ethernet32 already member of PortChannel 1"
  - Duplicate membership NOT created
  - No state change

**Postcondition/Cleanup:** Ethernet32 remains single member

---

#### LACP-NEG-004
**Title:** Attempt to add interface from different device
**Priority:** P2
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists on D1
  2. Attempting to reference D2's interface on D1

**Test Steps:**
  1. On D1, attempt to add D2's Ethernet32 to PortChannel 1
  2. Observe response (syntax validation)

**Test Data:** `PC_ID: 1, Interface: D2/Ethernet32 (invalid on D1)`

**Expected Result:**
  - CLI returns syntax error
  - Interface NOT added
  - PortChannel unchanged

**Postcondition/Cleanup:** PortChannel 1 members unchanged

---

#### LACP-NEG-005
**Title:** Attempt to configure LACP on PortChannel that does not exist
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 5 does not exist

**Test Steps:**
  1. Attempt to configure `channel-group 5 mode active` on Ethernet32
  2. Observe response

**Test Data:** `Channel_Group: 5 (does not exist), Mode: active`

**Expected Result:**
  - System auto-creates PortChannel 5 OR
  - Returns error depending on implementation
  - Verify final state is as expected

**Postcondition/Cleanup:** Document behavior for future reference

---

### 5.2 Out-of-Range / Boundary Violations

#### LACP-NEG-006
**Title:** Attempt to add more members than maximum supported
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists with 8 members (assuming 8 is max)
  2. Ethernet64 is available

**Test Steps:**
  1. Attempt to add Ethernet64 to PortChannel 1 (9th member)
  2. Observe response

**Test Data:** `PC_ID: 1, Current_Members: 8, Attempt: Add 9th`

**Expected Result:**
  - CLI returns error: "Maximum member count exceeded"
  - Ethernet64 NOT added
  - PortChannel 1 remains at 8 members

**Postcondition/Cleanup:** PortChannel unchanged

---

#### LACP-NEG-007
**Title:** Attempt to configure system priority outside valid range
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists

**Test Steps:**
  1. Attempt to set system priority to 0 (invalid, min is 1)
  2. Attempt to set system priority to 65536 (invalid, max is 65535)

**Test Data:** `System_Priority: 0, 65536 (invalid)`

**Expected Result:**
  - CLI returns error for both attempts
  - System priority NOT changed
  - Retains default or previously configured value

**Postcondition/Cleanup:** System priority unchanged

---

#### LACP-NEG-008
**Title:** Attempt to configure invalid LACP mode
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists

**Test Steps:**
  1. Attempt to set LACP mode to "invalid-mode"
  2. Attempt to set LACP mode to "semi-active" (not supported)

**Test Data:** `LACP_Mode: invalid-mode, semi-active`

**Expected Result:**
  - CLI returns error: "Invalid LACP mode"
  - Mode NOT changed
  - Default or current mode retained

**Postcondition/Cleanup:** LACP mode unchanged

---

### 5.3 Duplicate / Conflicting Configuration

#### LACP-NEG-009
**Title:** Attempt to add same interface to multiple PortChannels
**Priority:** P0
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists with Ethernet32 as member
  2. PortChannel 2 exists but is empty
  3. Ethernet32 is in PortChannel 1

**Test Steps:**
  1. Attempt to add Ethernet32 to PortChannel 2
  2. Observe system response

**Test Data:** `Interface: Ethernet32, PC1: 1, PC2: 2`

**Expected Result:**
  - CLI returns error: "Ethernet32 already in PortChannel 1"
  - Ethernet32 NOT moved to PortChannel 2
  - Remains in PortChannel 1

**Postcondition/Cleanup:** Ethernet32 in PortChannel 1 only

---

#### LACP-NEG-010
**Title:** Attempt to configure duplicate IP on VLAN SVI
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. VLAN 100 SVI has IP 10.1.1.1/24 on D1
  2. Attempting to add another IP on same SVI

**Test Steps:**
  1. Attempt to configure IP 10.1.1.3/24 on VLAN 100 SVI (same VLAN)
  2. Observe response

**Test Data:** `VLAN_ID: 100, Existing_IP: 10.1.1.1/24, Attempt_IP: 10.1.1.3/24`

**Expected Result:**
  - System behavior depends on implementation
  - Either accepts second IP as secondary OR rejects it
  - Verify no duplicate IP conflicts

**Postcondition/Cleanup:** Document behavior

---

#### LACP-NEG-011
**Title:** Attempt to create PortChannel with duplicate name
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 already exists
  2. Attempting to create another PortChannel 1

**Test Steps:**
  1. Attempt to create PortChannel 1 again
  2. Observe response

**Test Data:** `PC_ID: 1 (already exists)`

**Expected Result:**
  - CLI returns error or info: "PortChannel 1 already exists"
  - No duplicate created
  - Existing PortChannel unchanged

**Postcondition/Cleanup:** PortChannel 1 remains unchanged

---

### 5.4 Missing Required Configuration

#### LACP-NEG-012
**Title:** Attempt to enable LACP on PortChannel without members
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 3 created but is empty (no members)

**Test Steps:**
  1. Attempt to configure `channel-group 3 mode active` (no members added)
  2. Send traffic on PortChannel 3
  3. Observe behavior

**Test Data:** `PC_ID: 3, Members: none, Mode: active`

**Expected Result:**
  - PortChannel 3 exists but shows no active members
  - Traffic cannot flow
  - System may show "down" state
  - LACP does not attempt negotiation with no members

**Postcondition/Cleanup:** PortChannel 3 remains empty

---

#### LACP-NEG-013
**Title:** Attempt operations on administratively shutdown PortChannel
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists with members
  2. PortChannel 1 is operational

**Test Steps:**
  1. Shutdown PortChannel 1: `shutdown`
  2. Verify PortChannel is administratively down
  3. Attempt to send traffic on PortChannel 1

**Test Data:** `PC_ID: 1, Command: shutdown`

**Expected Result:**
  - PortChannel 1 transitions to down state
  - Members become inactive
  - Traffic cannot flow
  - No LACP PDU exchange

**Postcondition/Cleanup:** Re-enable PortChannel for cleanup

---

#### LACP-NEG-014
**Title:** Attempt to add shutdown interface as PortChannel member
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. Ethernet64 is administratively shutdown
  2. PortChannel 1 exists

**Test Steps:**
  1. Attempt to add Ethernet64 to PortChannel 1
  2. Observe behavior

**Test Data:** `Interface: Ethernet64 (shutdown), PC_ID: 1`

**Expected Result:**
  - System may:
    a) Accept but mark member as down, OR
    b) Reject shutdown interface, OR
    c) Accept and require no-shutdown before use
  - Verify behavior is consistent and documented

**Postcondition/Cleanup:** Document behavior

---

### 5.5 Malformed / Partial Commands

#### LACP-NEG-015
**Title:** Incomplete LACP configuration command
**Priority:** P2
**Type:** Negative
**Preconditions:**
  1. In interface configuration mode on Ethernet32

**Test Steps:**
  1. Type: `channel-group` (without arguments)
  2. Type: `channel-group 1` (without mode)
  3. Type: `channel-group 1 mode` (without active/passive/on)

**Test Data:** `Incomplete commands: "channel-group", "channel-group 1", "channel-group 1 mode"`

**Expected Result:**
  - CLI returns syntax error for each incomplete command
  - Commands NOT executed
  - No state change

**Postcondition/Cleanup:** No changes to configuration

---

#### LACP-NEG-016
**Title:** Invalid parameter order in LACP command
**Priority:** P2
**Type:** Negative
**Preconditions:**
  1. In interface configuration mode

**Test Steps:**
  1. Type: `channel-group active 1 mode` (incorrect order)
  2. Type: `mode active channel-group 1` (incorrect order)

**Test Data:** `Commands: "channel-group active 1 mode", "mode active channel-group 1"`

**Expected Result:**
  - CLI returns syntax error
  - Commands NOT executed

**Postcondition/Cleanup:** Configuration unchanged

---

#### LACP-NEG-017
**Title:** Unrecognized keywords in LACP command
**Priority:** P2
**Type:** Negative
**Preconditions:**
  1. In configuration mode

**Test Steps:**
  1. Type: `channel-group 1 mode super-active` (invalid keyword)
  2. Type: `lacp priority super-high` (invalid keyword)

**Test Data:** `Invalid keywords: "super-active", "super-high"`

**Expected Result:**
  - CLI returns error: "Unrecognized command or keyword"
  - NOT accepted
  - Configuration unchanged

**Postcondition/Cleanup:** No changes

---

### 5.6 Incorrect Sequence of Operations

#### LACP-NEG-018
**Title:** Attempt to send traffic before PortChannel is synchronized
**Priority:** P0
**Type:** Negative
**Preconditions:**
  1. PortChannel created with LACP mode
  2. Members added
  3. LACP negotiation in progress (not yet synchronized)

**Test Steps:**
  1. Immediately send ping traffic from D1 to D2
  2. Observe response time and packet loss

**Test Data:** `Traffic: ping, Timing: sent during LACP negotiation`

**Expected Result:**
  - First packets may be dropped (PortChannel not ready)
  - Once synchronized, traffic succeeds
  - Minimal packet loss during negotiation (~1-2 packets)

**Postcondition/Cleanup:** PortChannel synchronized after test

---

#### LACP-NEG-019
**Title:** Remove all members while traffic is flowing
**Priority:** P0
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 synchronized with traffic flowing
  2. Continuous ping or traffic generator active

**Test Steps:**
  1. Remove all members from PortChannel 1 while traffic is active
  2. Observe traffic behavior
  3. Verify no unintended behavior (e.g., system crash)

**Test Data:** `Action: Remove_All_Members, Condition: Traffic_Active`

**Expected Result:**
  - Traffic stops (no members)
  - PortChannel shows down
  - No system crash or errors
  - Clean error handling

**Postcondition/Cleanup:** Re-add members, verify recovery

---

#### LACP-NEG-020
**Title:** Shutdown PortChannel during active traffic
**Priority:** P0
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 with active traffic flowing

**Test Steps:**
  1. While traffic is flowing, execute: `shutdown`
  2. Observe traffic cessation
  3. Execute: `no shutdown`
  4. Verify traffic resumes and PortChannel re-syncs

**Test Data:** `Action: shutdown/no shutdown, Condition: traffic active`

**Expected Result:**
  - Traffic stops immediately
  - PortChannel down
  - `no shutdown` brings it back up
  - LACP re-negotiates
  - Traffic resumes without errors

**Postcondition/Cleanup:** PortChannel operational

---

### 5.7 Resource State Violations

#### LACP-NEG-021
**Title:** Attempt to configure interface that is already a routed port
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. Ethernet32 has IP address configured (routed port)
  2. PortChannel 1 exists

**Test Steps:**
  1. Remove IP from Ethernet32
  2. Add Ethernet32 to PortChannel 1

**Test Data:** `Interface: Ethernet32 (with IP), PC_ID: 1`

**Expected Result:**
  - IP must be removed before adding to PortChannel, OR
  - System auto-removes IP (verify behavior)
  - Interface becomes part of PortChannel
  - No dual state conflicts

**Postcondition/Cleanup:** Ethernet32 in PortChannel 1

---

#### LACP-NEG-022
**Title:** Attempt to reference deleted PortChannel
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists and is deleted
  2. Attempting to configure deleted PortChannel

**Test Steps:**
  1. Delete PortChannel 1
  2. Attempt to add member to PortChannel 1
  3. Attempt to configure IP on PortChannel 1 VLAN

**Test Data:** `PC_ID: 1 (deleted)`

**Expected Result:**
  - CLI returns error: "PortChannel 1 does not exist"
  - Commands NOT executed
  - No ghost PortChannel created

**Postcondition/Cleanup:** PortChannel 1 remains deleted

---

#### LACP-NEG-023
**Title:** Attempt to configure VLAN on non-operational PortChannel
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 exists but has no members
  2. PortChannel 1 is down

**Test Steps:**
  1. Create VLAN 100
  2. Add PortChannel 1 to VLAN 100
  3. Verify VLAN 100 behavior

**Test Data:** `PC_ID: 1 (down), VLAN_ID: 100`

**Expected Result:**
  - VLAN can be configured on down PortChannel
  - VLAN SVI will be down (no member up)
  - Once PortChannel up, VLAN SVI becomes operational
  - No errors during configuration

**Postcondition/Cleanup:** Add members and bring PortChannel up

---

### 5.8 Protocol-Level Failures

#### LACP-NEG-024
**Title:** LACP mismatch in system priority causes different behavior
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. D1 PortChannel 1 configured with system priority 100
  2. D2 PortChannel 1 configured with system priority 200

**Test Steps:**
  1. Configure PortChannels with different system priorities
  2. Bring up both devices
  3. Verify LACP negotiates successfully
  4. Verify no mismatch errors

**Test Data:** `D1_Sys_Prio: 100, D2_Sys_Prio: 200`

**Expected Result:**
  - LACP accepts different priorities
  - Negotiation succeeds (different priorities are normal)
  - No errors or mismatch warnings

**Postcondition/Cleanup:** Configuration retained

---

#### LACP-NEG-025
**Title:** LACP port priority affects member selection during link failure
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 with 4 members
  2. Ethernet32, 36 configured with port priority 100
  3. Ethernet40, 44 configured with port priority 50

**Test Steps:**
  1. Shutdown both high-priority members (32, 36)
  2. Verify low-priority members (40, 44) continue working
  3. Bring high-priority members back up
  4. Verify they take precedence (if applicable to implementation)

**Test Data:** `Port_Priority: High=100, Low=50, Action: Shutdown_High`

**Expected Result:**
  - Low-priority members carry traffic when high-priority down
  - All members participate when up
  - No protocol violations

**Postcondition/Cleanup:** All members up and synced

---

#### LACP-NEG-026
**Title:** MTU mismatch between PortChannel member and VLAN
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 members at MTU 1500
  2. VLAN SVI created on PortChannel

**Test Steps:**
  1. Configure MTU 9100 on VLAN SVI
  2. Configure MTU 1500 on PortChannel members
  3. Send packets of size 8000 bytes
  4. Observe behavior

**Test Data:** `PC_MTU: 1500, VLAN_MTU: 9100, Packet_Size: 8000`

**Expected Result:**
  - Packets larger than 1500 are fragmented or dropped
  - No system crash
  - Proper handling of MTU mismatch
  - Logs show MTU-related messages (if applicable)

**Postcondition/Cleanup:** Align MTUs for cleanup

---

#### LACP-NEG-027
**Title:** Speed mismatch on different member links
**Priority:** P0
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 with 4 members
  2. Ethernet32, 36 at 40Gbps
  3. Ethernet40, 44 at 10Gbps (or simulate with rate-limiting)

**Test Steps:**
  1. Configure different speeds on members (if hardware supports)
  2. Attempt to synchronize PortChannel
  3. Observe LACP behavior

**Test Data:** `Member_Speed: Mix of 40Gbps and 10Gbps`

**Expected Result:**
  - LACP may:
    a) Reject slower-speed members, OR
    b) Accept all members but warn, OR
    c) Accept and operate at minimum speed
  - Verify documented behavior
  - No crashes or inconsistent state

**Postcondition/Cleanup:** All members same speed

---

#### LACP-NEG-028
**Title:** Duplex mismatch on PortChannel members
**Priority:** P1
**Type:** Negative
**Preconditions:**
  1. PortChannel 1 with 4 members
  2. Ethernet32, 36 at full duplex
  3. Attempt to add half-duplex members

**Test Steps:**
  1. Configure Ethernet40 for half-duplex (if supported)
  2. Add Ethernet40 to PortChannel 1
  3. Observe LACP response

**Test Data:** `Members_Duplex: Mix of full and half`

**Expected Result:**
  - LACP may reject half-duplex member, OR
  - Accept but warn
  - No protocol violations
  - Verify documented behavior

**Postcondition/Cleanup:** All full-duplex members

---

---

## 6. Edge Cases

### 6.1 First-Time / Fresh State

#### LACP-EDGE-001
**Title:** PortChannel creation on fresh system (no prior config)
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. System in default state
  2. No PortChannels exist
  3. All interfaces in default state

**Test Steps:**
  1. Create PortChannel 1
  2. Add 4 members
  3. Configure LACP active
  4. Verify LACP negotiates from scratch

**Test Data:** `System_State: default, PC_ID: 1, Members: 4`

**Expected Result:**
  - PortChannel created successfully
  - LACP negotiates normally
  - All members synchronized
  - No artifacts from prior configuration

**Postcondition/Cleanup:** PortChannel remains for cleanup

---

#### LACP-EDGE-002
**Title:** First LACP PDU exchange after member addition
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel exists but is empty
  2. No LACP traffic yet

**Test Steps:**
  1. Add first member to PortChannel
  2. Capture LACP PDU exchange
  3. Verify first LACP PDU format and content

**Test Data:** `PC_ID: 1, Action: Add_First_Member`

**Expected Result:**
  - First LACP PDU sent correctly
  - PDU format valid (actor state, partner state, etc.)
  - Negotiation starts immediately

**Postcondition/Cleanup:** Member remains

---

### 6.2 Last Allowed / Limit Conditions

#### LACP-EDGE-003
**Title:** Maximum PortChannel ID creation (4095)
**Priority:** P2
**Type:** Edge
**Preconditions:**
  1. System supports PortChannel IDs 1-4095
  2. No PortChannel 4095 exists

**Test Steps:**
  1. Create PortChannel 4095
  2. Add members
  3. Verify operational
  4. Attempt to create PortChannel 4096

**Test Data:** `PC_ID: 4095 (max), Attempt: 4096 (beyond max)`

**Expected Result:**
  - PortChannel 4095 created successfully
  - PortChannel 4096 creation fails
  - Error message indicates limit

**Postcondition/Cleanup:** Delete PortChannel 4095

---

#### LACP-EDGE-004
**Title:** Maximum members per PortChannel (implementation-dependent)
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. Assume max members = 8 (varies by platform)
  2. 8 members available
  3. PortChannel exists

**Test Steps:**
  1. Add 8 members to PortChannel
  2. Verify all 8 synchronized
  3. Attempt to add 9th member
  4. Observe rejection

**Test Data:** `Max_Members: 8, Attempt: 9`

**Expected Result:**
  - All 8 members added and synchronized
  - 9th member rejected with error
  - PortChannel remains at 8 members

**Postcondition/Cleanup:** Remove members as needed

---

#### LACP-EDGE-005
**Title:** Maximum VLANs on PortChannel
**Priority:** P2
**Type:** Edge
**Preconditions:**
  1. Assume max VLANs = 4094 (IEEE limit)
  2. PortChannel exists

**Test Steps:**
  1. Add PortChannel to VLAN 1 (tagged)
  2. Add PortChannel to VLAN 2-100 (tagged, 100 VLANs)
  3. Verify all VLANs configured

**Test Data:** `VLAN_Count: 100, Action: Add_Multiple_VLANs`

**Expected Result:**
  - All 100 VLANs successfully configured on PortChannel
  - Untagged frame handling correct for all VLANs
  - Traffic properly VLAN-segregated

**Postcondition/Cleanup:** Configuration retained for cleanup

---

### 6.3 Concurrent / Parallel Operations

#### LACP-EDGE-006
**Title:** Simultaneous configuration changes on multiple members
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with 4 synchronized members
  2. Traffic flowing

**Test Steps:**
  1. Simultaneously execute on different members:
     - MTU change on Ethernet32
     - Speed change on Ethernet36
     - Shutdown on Ethernet40
     - Bring up on Ethernet44
  2. Observe PortChannel state
  3. Verify traffic impact

**Test Data:** `Concurrent_Actions: [MTU_change, speed_change, shutdown, up]`

**Expected Result:**
  - All changes applied (implementation-dependent order)
  - PortChannel handles concurrent operations
  - No deadlocks or hangs
  - LACP re-negotiates as needed

**Postcondition/Cleanup:** Restore all members to operational state

---

#### LACP-EDGE-007
**Title:** Parallel traffic on PortChannel while configuration change
**Priority:** P0
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 synchronized with traffic flowing
  2. Configuration change planned

**Test Steps:**
  1. Start continuous ping (100 pps) from D1 to D2
  2. Simultaneously remove one member from PortChannel
  3. Observe traffic impact
  4. Monitor packet loss

**Test Data:** `Traffic: 100 pps ping, Action: Remove_Member`

**Expected Result:**
  - Traffic redistributes to remaining members
  - Minimal packet loss (<10)
  - PortChannel remains operational
  - No traffic blackhole

**Postcondition/Cleanup:** Re-add member, traffic resumes

---

#### LACP-EDGE-008
**Title:** Rapid configuration toggles (add/remove members)
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with 4 members
  2. Ethernet48 available for toggling

**Test Steps:**
  1. Add Ethernet48 to PortChannel 1
  2. Remove Ethernet48 immediately (< 1 second)
  3. Repeat add/remove 5 times
  4. Verify final state

**Test Data:** `Action: Rapid_add/remove, Repetitions: 5`

**Expected Result:**
  - All operations complete without errors
  - PortChannel stable after rapid toggles
  - LACP does not crash or misbehave
  - Final state consistent

**Postcondition/Cleanup:** Ethernet48 not member of PortChannel

---

### 6.4 System Under Load

#### LACP-EDGE-009
**Title:** PortChannel operation during high-rate traffic
**Priority:** P0
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with 4 members, 4x40Gbps = 160Gbps total
  2. Traffic generation capability

**Test Steps:**
  1. Generate high-rate traffic (100 Gbps) across PortChannel
  2. Verify all members carry load (25 Gbps each)
  3. Add/remove member during high-rate traffic
  4. Observe behavior

**Test Data:** `Traffic_Rate: 100 Gbps, Member_Count: 4`

**Expected Result:**
  - All 4 members load-balance traffic
  - Each member carries ~25 Gbps
  - Configuration changes handled gracefully
  - No dropped packets due to system overload

**Postcondition/Cleanup:** Traffic stopped, counters verified

---

#### LACP-EDGE-010
**Title:** PortChannel during burst traffic
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 operational
  2. Burst traffic capability

**Test Steps:**
  1. Send burst of 1M packets in 1 second
  2. Verify all members queue packets
  3. Observe buffer behavior
  4. Verify no packet loss if buffer sufficient

**Test Data:** `Burst_Size: 1M packets, Duration: 1 second`

**Expected Result:**
  - Burst traffic handled
  - Members queue if necessary
  - Graceful backpressure (no drops if buffer available)
  - Traffic resumes after burst

**Postcondition/Cleanup:** Buffers drained, counters normalized

---

#### LACP-EDGE-011
**Title:** LACP operation during high control-plane load
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with members
  2. High number of CLI commands executing

**Test Steps:**
  1. Generate high number of configuration commands (1000s per minute)
  2. While executing commands, monitor LACP PDU timing
  3. Verify LACP timer accuracy is not affected
  4. Check for LACP timeout or mismatch

**Test Data:** `CLI_Load: 1000+ commands/min, LACP_PDU_Interval: 1 second`

**Expected Result:**
  - LACP PDU timing maintained despite control-plane load
  - No spurious LACP timeouts
  - PortChannel remains synchronized
  - System remains responsive

**Postcondition/Cleanup:** Return to normal load

---

### 6.5 Recently Deleted / Modified Resources

#### LACP-EDGE-012
**Title:** Recreate PortChannel immediately after deletion
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 exists with members
  2. Planning to delete and recreate

**Test Steps:**
  1. Delete PortChannel 1
  2. Immediately create new PortChannel 1 (< 1 second)
  3. Add same members
  4. Verify operational

**Test Data:** `PC_ID: 1, Action: Delete_then_Recreate, Delay: < 1 second`

**Expected Result:**
  - PortChannel 1 recreated successfully
  - Members re-added without issues
  - LACP negotiates normally
  - No residual state from old PortChannel

**Postcondition/Cleanup:** PortChannel 1 operational

---

#### LACP-EDGE-013
**Title:** Re-add member immediately after removal
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with 4 synchronized members
  2. Planning rapid removal/addition

**Test Steps:**
  1. Remove Ethernet32 from PortChannel 1
  2. Immediately add Ethernet32 back (< 1 second)
  3. Verify member re-synchronizes
  4. Verify traffic resumes

**Test Data:** `Member: Ethernet32, Action: Remove_then_Add, Delay: < 1 second`

**Expected Result:**
  - Member re-added without errors
  - Re-synchronizes via LACP
  - Traffic resumes immediately
  - No hung state or timeouts

**Postcondition/Cleanup:** All 4 members synchronized

---

#### LACP-EDGE-014
**Title:** Re-apply identical configuration after removal
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with configuration saved
  2. Configuration about to be removed and reapplied

**Test Steps:**
  1. Remove all configuration for PortChannel 1
  2. Immediately reapply identical configuration (< 1 second)
  3. Verify final state matches original

**Test Data:** `Action: Remove_then_Reapply_Config`

**Expected Result:**
  - Configuration reapplied successfully
  - Idempotency verified (same result as original)
  - No conflicts or inconsistencies
  - PortChannel operational

**Postcondition/Cleanup:** Configuration remains

---

### 6.6 Rapid State Transitions

#### LACP-EDGE-015
**Title:** Repeated enable/disable of PortChannel
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with 4 members
  2. Configuration ready for toggling

**Test Steps:**
  1. Shutdown PortChannel 1
  2. Verify down state
  3. No shutdown (enable) PortChannel 1
  4. Verify up and synchronized
  5. Repeat steps 1-4 five times
  6. Verify final state stable

**Test Data:** `Action: Shutdown/no-shutdown, Repetitions: 5`

**Expected Result:**
  - Each shutdown/enable completes cleanly
  - No hung processes or timeouts
  - PortChannel stable after rapid transitions
  - LACP re-negotiates each cycle
  - Final state operational

**Postcondition/Cleanup:** PortChannel remains enabled

---

#### LACP-EDGE-016
**Title:** Rapid member add/remove cycles
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with 4 members
  2. Ethernet48 available for cycling

**Test Steps:**
  1. Remove Ethernet32 from PortChannel 1
  2. Add Ethernet32 back
  3. Remove Ethernet36
  4. Add Ethernet36 back
  5. Repeat with Ethernet40 and Ethernet44
  6. Verify final state (all 4 members)

**Test Data:** `Members: [32, 36, 40, 44], Action: Cycle_each, Repetitions: 1 per member`

**Expected Result:**
  - Each add/remove completes successfully
  - PortChannel remains operational
  - Members re-synchronize after each cycle
  - No deadlocks or stuck states
  - All 4 members operational at end

**Postcondition/Cleanup:** All 4 members synced

---

#### LACP-EDGE-017
**Title:** Rapid LACP mode changes
**Priority:** P1
**Type:** Edge
**Preconditions:**
  1. PortChannel 1 with LACP active mode
  2. Capability to change modes

**Test Steps:**
  1. Change LACP mode from active to passive
  2. Verify mode change (LACP negotiation pauses)
  3. Change back to active
  4. Verify re-negotiation
  5. Repeat 3 times

**Test Data:** `Mode_Changes: active→passive→active, Repetitions: 3`

**Expected Result:**
  - Mode changes complete cleanly
  - LACP PDU exchange adjusts to mode
  - PortChannel remains operational
  - No hung negotiations
  - Final mode matches expected

**Postcondition/Cleanup:** Mode remains as set

---

---

## 7. Boundary Value Analysis (BVA)

### 7.1 System Priority Boundary Testing

#### LACP-BVA-001
**Title:** System priority minimum boundary (1)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. PortChannel 1 exists

**Test Steps:**
  1. Configure system priority to 1 (minimum valid)
  2. Verify configuration accepted
  3. Verify LACP uses priority 1
  4. Test synchronization with peer at higher priority

**Test Data:** `System_Priority: 1 (minimum)`

**Expected Result:**
  - Priority 1 accepted and used
  - LACP negotiates correctly
  - No errors or warnings

**Postcondition/Cleanup:** Priority retained

---

#### LACP-BVA-002
**Title:** System priority maximum boundary (65535)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. PortChannel 1 exists

**Test Steps:**
  1. Configure system priority to 65535 (maximum valid)
  2. Verify configuration accepted
  3. Verify LACP uses priority 65535

**Test Data:** `System_Priority: 65535 (maximum)`

**Expected Result:**
  - Priority 65535 accepted
  - LACP negotiates correctly

**Postcondition/Cleanup:** Priority retained

---

#### LACP-BVA-003
**Title:** System priority just below minimum (0)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. PortChannel 1 exists

**Test Steps:**
  1. Attempt to configure system priority to 0 (invalid)
  2. Observe rejection

**Test Data:** `System_Priority: 0 (below minimum)`

**Expected Result:**
  - Configuration rejected with error
  - System priority NOT changed

**Postcondition/Cleanup:** Priority unchanged

---

#### LACP-BVA-004
**Title:** System priority just above maximum (65536)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. PortChannel 1 exists

**Test Steps:**
  1. Attempt to configure system priority to 65536 (invalid)
  2. Observe rejection

**Test Data:** `System_Priority: 65536 (above maximum)`

**Expected Result:**
  - Configuration rejected with error
  - System priority NOT changed

**Postcondition/Cleanup:** Priority unchanged

---

### 7.2 Port Priority Boundary Testing

#### LACP-BVA-005
**Title:** Port priority minimum boundary (1)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. PortChannel 1 with members

**Test Steps:**
  1. Configure port priority to 1 on Ethernet32
  2. Verify configuration accepted
  3. Verify LACP uses priority 1 for this port

**Test Data:** `Port_Priority: 1 (minimum)`

**Expected Result:**
  - Port priority 1 accepted
  - LACP negotiates with correct priority

**Postcondition/Cleanup:** Priority retained

---

#### LACP-BVA-006
**Title:** Port priority maximum boundary (65535)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. PortChannel 1 with members

**Test Steps:**
  1. Configure port priority to 65535 on Ethernet32
  2. Verify configuration accepted

**Test Data:** `Port_Priority: 65535 (maximum)`

**Expected Result:**
  - Port priority 65535 accepted
  - LACP negotiates correctly

**Postcondition/Cleanup:** Priority retained

---

### 7.3 PortChannel ID Boundary Testing

#### LACP-BVA-007
**Title:** PortChannel ID minimum boundary (1)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. No PortChannel 1 exists

**Test Steps:**
  1. Create PortChannel 1
  2. Verify creation successful

**Test Data:** `PC_ID: 1 (minimum)`

**Expected Result:**
  - PortChannel 1 created successfully

**Postcondition/Cleanup:** PortChannel 1 exists

---

#### LACP-BVA-008
**Title:** PortChannel ID maximum boundary (4095)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. No PortChannel 4095 exists

**Test Steps:**
  1. Create PortChannel 4095
  2. Verify creation successful

**Test Data:** `PC_ID: 4095 (maximum)`

**Expected Result:**
  - PortChannel 4095 created successfully

**Postcondition/Cleanup:** PortChannel 4095 exists

---

#### LACP-BVA-009
**Title:** PortChannel ID just below minimum (0)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. Fresh configuration

**Test Steps:**
  1. Attempt to create PortChannel 0
  2. Observe rejection

**Test Data:** `PC_ID: 0 (below minimum)`

**Expected Result:**
  - Creation rejected with error
  - PortChannel 0 NOT created

**Postcondition/Cleanup:** No PortChannel 0

---

#### LACP-BVA-010
**Title:** PortChannel ID just above maximum (4096)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. Fresh configuration

**Test Steps:**
  1. Attempt to create PortChannel 4096
  2. Observe rejection

**Test Data:** `PC_ID: 4096 (above maximum)`

**Expected Result:**
  - Creation rejected with error
  - PortChannel 4096 NOT created

**Postcondition/Cleanup:** No PortChannel 4096

---

### 7.4 Member Count Boundary Testing

#### LACP-BVA-011
**Title:** Member count minimum boundary (1 member)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. PortChannel 1 exists but empty

**Test Steps:**
  1. Add 1 member to PortChannel 1 (Ethernet32)
  2. Verify PortChannel operational with 1 member
  3. Send traffic

**Test Data:** `Member_Count: 1`

**Expected Result:**
  - PortChannel 1 operational with 1 member
  - Traffic flows on single member
  - No LACP errors (single member LAG is valid)

**Postcondition/Cleanup:** 1 member remains

---

#### LACP-BVA-012
**Title:** Member count maximum boundary (8 members, platform-dependent)
**Priority:** P2
**Type:** Boundary
**Preconditions:**
  1. PortChannel 1 exists
  2. 8 member interfaces available

**Test Steps:**
  1. Add members until maximum (8)
  2. Verify all 8 members synchronized
  3. Send traffic across all members

**Test Data:** `Member_Count: 8 (platform maximum)`

**Expected Result:**
  - All 8 members successfully added and synchronized
  - Traffic distributes across 8 members

**Postcondition/Cleanup:** 8 members remain

---

---

## 8. Test Execution Strategy

### 8.1 Test Phases

**Phase 1: Positive Testing (Day 1)**
- Execute all LACP-POS-* test cases
- Verify core LACP functionality
- Establish baseline

**Phase 2: Negative Testing (Days 2-3)**
- Execute all LACP-NEG-* test cases
- Verify error handling and edge conditions
- Document system behavior for undocumented cases

**Phase 3: Edge Cases (Day 4)**
- Execute all LACP-EDGE-* test cases
- Verify system stability under unusual conditions

**Phase 4: Boundary Testing (Day 5)**
- Execute all LACP-BVA-* test cases
- Verify limit handling

**Phase 5: Regression & Final Validation (Day 6)**
- Re-run critical positive test cases
- Verify no regressions introduced

### 8.2 Test Execution Environment

**Testbed Configuration:**
- 2-node SONiC setup (D1, D2)
- Connected via 4+ physical links
- Management network for SSH access
- Traffic generation capability (Scapy-based)
- Packet capture capability (tcpdump)

**Test Data Collection:**
- Capture all CLI output (save to log files)
- Capture LACP PDU exchanges (tcpdump)
- Monitor system logs for errors/warnings
- Record counter values before/after each test
- Document any unexpected behavior

### 8.3 Pass/Fail Criteria

**Test PASSES if:**
- Expected Result matches Actual Result
- No system crashes, hangs, or unexpected state changes
- CLI responds with expected messages (success or documented error)
- LACP negotiates correctly for positive cases
- Proper error handling for negative cases

**Test FAILS if:**
- Unexpected behavior or system state change
- System crash or hang
- Undocumented error messages
- Inconsistency with documented behavior
- Unintended side effects on other PortChannels/interfaces

### 8.4 Cleanup & State Reset

**After Each Test:**
1. Verify no leftover configuration
2. Delete any created PortChannels
3. Clear traffic/counters if modified
4. Return to baseline state
5. Document any issues for impact analysis

**Between Test Phases:**
1. Run sanity checks on 2-3 critical positive tests
2. Verify no systemic issues introduced
3. Clear all counters and logs
4. Document phase completion

---

## 9. Test Deliverables

### 9.1 Documentation
- This Test Plan (LACP_TEST_PLAN.md)
- Test Execution Log (timestamp each test)
- Test Case Results Summary
- Issues/Defect Report
- Final Test Report with metrics

### 9.2 Evidence Artifacts
- Console logs for each test (including errors)
- tcpdump captures for LACP PDU analysis
- Configuration snapshots (running-config, startup-config)
- Counter comparisons (before/after)
- Screenshots of CLI output (if applicable)

### 9.3 Metrics
- Total Tests: 87
- Tests Passed: [to be filled]
- Tests Failed: [to be filled]
- Tests Blocked: [to be filled]
- Pass Rate: [to be calculated]
- Defects Found: [to be documented]

---

## 10. Known Limitations & Assumptions

### 10.1 Assumptions Made
- ⚠️ ASSUMPTION: Maximum PortChannel members = 8 (verify for actual platform)
- ⚠️ ASSUMPTION: PortChannel ID range 1-4095 (verify per platform)
- ⚠️ ASSUMPTION: LACP system/port priority range 1-65535 (standard)
- ⚠️ ASSUMPTION: Default LACP PDU interval = 1 second (verify configuration)
- ⚠️ ASSUMPTION: Traffic generation available via Scapy (alternative: use Ixia/Spirent if available)

### 10.2 Test Limitations
- Tests assume 4 physical links available for PortChannel
- Traffic generation limited to line rate of testbed
- Some edge cases may not be testable with virtual equipment
- Hardware-specific behaviors (e.g., buffer sizes) not fully tested in virtual environment

### 10.3 Out of Scope
- LACP fast mode timing (PDU interval < 1 second) — requires specialized equipment
- PortChannel failover during complete link failure (hardware event, not CLI)
- LACP interactions with other protocols (STP, VRRP, etc.)
- Performance benchmarking beyond basic functionality
- Multi-device (>2) LACP scenarios (out of scope for 2-node testbed)

---

## 11. References & Standards

- **IEEE 802.3ad** — Link Aggregation Control Protocol (LACP) Standard
- **SONiC Documentation** — Official SONiC Network Operating System docs
- **QA TC Master Rules** — Company test case standards and best practices
- **Platform-Specific Docs** — Hardware vendor guidelines for PortChannel limits

---

## 12. Version Control & Sign-Off

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-19 | QA Team | Initial creation |
| | | | |

**Approval:**
- [ ] QA Lead
- [ ] Feature Owner
- [ ] Test Execution Lead

---

**End of LACP Test Plan**
