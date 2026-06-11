# BFD (Bidirectional Forwarding Detection) - Comprehensive Test Plan

## Test Overview

### Topology
- **Type**: Leaf-Spine (2-node topology)
- **Setup**: 2 nodes running SONiC-VS image
- **Configuration**: All configurations via SONiC Klish CLI
- **Validation**: Scapy-based packet transmission and verification
- **Verification**: All configs verified using `show running-config`

### Topology Diagram

```
                    ┌─────────────────────────────────────┐
                    │         Test Topology               │
                    └─────────────────────────────────────┘

                           TGen (T1)
                               │
                               │ T1D1P1
                               │
                    ┌──────────▼──────────┐
                    │                     │
                    │    DUT1 (D1)        │
                    │    SONiC Device     │
                    │                     │
                    └──────────┬──────────┘
                               │
                               │ D1D2P1
                               │ (BFD Test Link)
                               │
                    ┌──────────▼──────────┐
                    │                     │
                    │    DUT2 (D2)        │
                    │    SONiC Device     │
                    │                     │
                    └──────────┬──────────┘
                               │
                               │ T1D2P1
                               │
                           TGen (T1)


    Link Details:
    ═══════════════════════════════════════════════════════════

    D1 <──> D2  :  Primary BFD session link
                   - IPv4: 10.1.1.1/24 (D1) <-> 10.1.1.2/24 (D2)
                   - IPv6: 2001:db8:1::1/64 (D1) <-> 2001:db8:1::2/64 (D2)
                   - Interface: Ethernet0 (both sides)

    D1 <──> TGen:  Traffic generation for validation
                   - Interface: Ethernet4 (D1)

    D2 <──> TGen:  Traffic reception for validation
                   - Interface: Ethernet4 (D2)


    Extended Topology (for advanced tests):
    ═══════════════════════════════════════════════════════════

    ┌─────────────┐         ┌─────────────┐
    │             │         │             │
    │    D1       │◄────────┤    D2       │  Link 1: Primary BFD
    │             │────────►│             │
    │             │         │             │
    └──────┬──────┘         └──────┬──────┘
           │                       │
           │  PortChannel          │  PortChannel
           │  (for LAG tests)      │  (for LAG tests)
           │                       │
    ┌──────▼──────┐         ┌──────▼──────┐
    │  Ethernet8  │◄────────┤  Ethernet8  │  Link 2: LAG Member 1
    │  Ethernet12 │────────►│  Ethernet12 │  Link 3: LAG Member 2
    └─────────────┘         └─────────────┘


    VLAN Topology (for VLAN interface tests):
    ═══════════════════════════════════════════════════════════

         D1                          D2
    ┌─────────┐                 ┌─────────┐
    │ Vlan100 │ 10.10.10.1      │ Vlan100 │ 10.10.10.2
    └────┬────┘                 └────┬────┘
         │                           │
         └───────────────────────────┘
              Tagged on Ethernet0
              (BFD over VLAN interface)
```

### Test Case ID Format
`TC_BFD_<SUBMODULE>_<THREE_DIGIT_NUMBER>`

### Test Coverage
1. CLI Tests - Configuration and show commands
2. Functional Tests - Protocol behavior validation
3. Negative Tests - Error handling and invalid configurations
4. Scaling Tests - Multiple sessions and stress scenarios

---

## Test Case Summary

**Total Test Cases: 121**

This comprehensive BFD test plan covers end-to-end validation of Bidirectional Forwarding Detection functionality across all operational aspects.

### Test Case Breakdown by Category

| Category | Test Cases | Count | Description |
|----------|------------|-------|-------------|
| **BFD CLI Tests** | TC_BFD_CLI_001 - TC_BFD_CLI_027 | 27 | Configuration commands, show commands, and profile management |
| **BFD Functional Tests** | TC_BFD_FUNC_001 - TC_BFD_VRF_004 | 56 | Core BFD functionality, routing protocol integration, state transitions, and traffic validation |
| **BFD Negative Tests** | TC_BFD_NEG_001 - TC_BFD_NEG_020 | 20 | Error handling, invalid configurations, and failure scenarios |
| **BFD Scaling Tests** | TC_BFD_SCALE_001 - TC_BFD_SCALE_018 | 18 | Session scaling, performance, and stress testing |

### Test Distribution by Functional Area

**CLI Tests (27 total)**
- Global Configuration: 3 test cases
- Peer Configuration: 11 test cases
- Show Commands: 7 test cases
- Profile Configuration: 6 test cases

**Functional Tests (56 total)**
- Session Establishment: 10 test cases
- Static Routes Integration: 5 test cases
- BGP Integration: 6 test cases
- OSPF Integration: 4 test cases
- State Transitions: 6 test cases
- Echo Mode: 4 test cases
- Timers and Parameters: 7 test cases
- Traffic Validation (Scapy): 10 test cases
- VRF Support: 4 test cases

**Negative Tests (20 total)**
- Configuration Errors: 9 test cases
- Session Failures: 6 test cases
- Error Handling: 5 test cases

**Scaling Tests (18 total)**
- Session Scaling: 6 test cases
- Performance Scaling: 7 test cases
- Stress Testing: 5 test cases

---

## 1. BFD CLI Tests

### 1.1 BFD Global Configuration

#### TC_BFD_CLI_001: Enable BFD globally

**Objective**: Verify BFD global configuration can be enabled successfully

**Test Steps**:
1. Connect to DUT1 via SSH/console
2. Enter configuration mode:
   ```
   sonic# configure terminal
   ```
3. Enable BFD globally:
   ```
   sonic(config)# bfd
   ```
4. Exit BFD configuration mode:
   ```
   sonic(config-bfd)# exit
   ```
5. Verify BFD is enabled in running configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Command executes without errors
- Output shows `bfd` in running configuration
- BFD configuration mode is accessible

**Validation**:
```
bfd
!
```

---

#### TC_BFD_CLI_002: Configure BFD global slow-timer

**Objective**: Verify BFD global slow-timer can be configured with valid values

**Test Steps**:
1. Enter configuration mode:
   ```
   sonic# configure terminal
   sonic(config)# bfd
   ```
2. Configure slow-timer with value 5000ms:
   ```
   sonic(config-bfd)# slow-timer 5000
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```
4. Modify slow-timer to different value 10000ms:
   ```
   sonic(config-bfd)# slow-timer 10000
   ```
5. Verify updated configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Slow-timer accepts valid range (1000-60000 ms)
- Configuration is saved and displayed correctly
- Timer value is reflected in running-config

**Validation**:
```
bfd
 slow-timer 10000
!
```

---

#### TC_BFD_CLI_003: Remove BFD global configuration

**Objective**: Verify BFD global configuration can be removed

**Pre-requisites**:
- BFD globally configured (TC_BFD_CLI_001)
- No active BFD peers configured

**Test Steps**:
1. Verify BFD is currently configured:
   ```
   sonic# show running-config bfd
   ```
2. Enter configuration mode:
   ```
   sonic# configure terminal
   ```
3. Remove BFD global configuration:
   ```
   sonic(config)# no bfd
   ```
4. Verify BFD is removed:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Command executes without errors
- BFD configuration is completely removed
- No BFD entries in running-config

**Validation**:
- Running config should not contain `bfd` section
- Command `show bfd peers` should show no entries or error

---

### 1.2 BFD Peer Configuration

#### TC_BFD_CLI_004: Configure single-hop BFD peer

**Objective**: Verify single-hop BFD peer can be configured on physical interface

**Pre-requisites**:
- DUT1 and DUT2 connected via Ethernet0
- IP addresses configured: D1: 10.1.1.1/24, D2: 10.1.1.2/24

**Test Steps**:
1. On DUT1, enable BFD globally:
   ```
   sonic(config)# bfd
   ```
2. Configure single-hop BFD peer:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
3. Exit peer configuration mode:
   ```
   sonic(config-bfd-peer)# exit
   ```
4. Verify peer configuration:
   ```
   sonic# show running-config bfd
   ```
5. Check BFD peer status:
   ```
   sonic# show bfd peers
   ```

**Expected Result**:
- Peer is configured successfully
- Peer appears in running-config
- Peer status shows in `show bfd peers` output
- Initial state should be Down or Init

**Validation**:
```
bfd
 peer 10.1.1.2 interface Ethernet0
 !
!
```

---

#### TC_BFD_CLI_005: Configure multi-hop BFD peer

**Objective**: Verify multi-hop BFD peer can be configured

**Pre-requisites**:
- DUT1 has IP 10.1.1.1/24
- DUT2 has IP 10.1.1.2/24 (may be multiple hops away)

**Test Steps**:
1. On DUT1, enable BFD globally:
   ```
   sonic(config)# bfd
   ```
2. Configure multi-hop BFD peer with local address:
   ```
   sonic(config-bfd)# peer 10.1.1.2 multihop local-address 10.1.1.1
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```
4. Check peer details:
   ```
   sonic# show bfd peer 10.1.1.2
   ```

**Expected Result**:
- Multi-hop peer is configured successfully
- Local address is associated with peer
- Peer shown with multihop flag in configuration

**Validation**:
```
bfd
 peer 10.1.1.2 multihop local-address 10.1.1.1
 !
!
```

---

#### TC_BFD_CLI_006: Configure BFD peer with VRF

**Objective**: Verify BFD peer can be configured in a non-default VRF

**Pre-requisites**:
- VRF "Vrf-Blue" created and configured
- Interface in Vrf-Blue with IP 192.168.10.1/24

**Test Steps**:
1. Configure BFD peer in VRF:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 192.168.10.2 vrf Vrf-Blue interface Ethernet4
   ```
2. Verify configuration:
   ```
   sonic# show running-config bfd
   ```
3. Check BFD peers in VRF:
   ```
   sonic# show bfd peers vrf Vrf-Blue
   ```

**Expected Result**:
- Peer is configured in specified VRF
- VRF name appears in configuration
- Peer is isolated to VRF context

**Validation**:
```
bfd
 peer 192.168.10.2 vrf Vrf-Blue interface Ethernet4
 !
!
```

---

#### TC_BFD_CLI_007: Configure BFD transmit interval

**Objective**: Verify BFD transmit interval can be configured for a peer

**Pre-requisites**:
- BFD peer 10.1.1.2 already configured

**Test Steps**:
1. Enter BFD peer configuration mode:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Configure transmit interval to 300ms:
   ```
   sonic(config-bfd-peer)# transmit-interval 300
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```
4. Check peer details:
   ```
   sonic# show bfd peer 10.1.1.2
   ```

**Expected Result**:
- Transmit interval is set to 300ms
- Configuration is reflected in show commands
- Valid range: 10-60000 ms

**Validation**:
```
bfd
 peer 10.1.1.2 interface Ethernet0
  transmit-interval 300
 !
!
```

---

#### TC_BFD_CLI_008: Configure BFD receive interval

**Objective**: Verify BFD receive interval can be configured for a peer

**Pre-requisites**:
- BFD peer 10.1.1.2 already configured

**Test Steps**:
1. Enter BFD peer configuration mode:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Configure receive interval to 300ms:
   ```
   sonic(config-bfd-peer)# receive-interval 300
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Receive interval is set to 300ms
- Configuration is saved correctly
- Valid range: 10-60000 ms

**Validation**:
```
bfd
 peer 10.1.1.2 interface Ethernet0
  receive-interval 300
 !
!
```

---

#### TC_BFD_CLI_009: Configure BFD detect multiplier

**Objective**: Verify BFD detect multiplier can be configured

**Pre-requisites**:
- BFD peer 10.1.1.2 already configured

**Test Steps**:
1. Enter BFD peer configuration mode:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Configure detect multiplier to 5:
   ```
   sonic(config-bfd-peer)# detect-multiplier 5
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```
4. Verify detection time calculation:
   - Detection time = receive-interval × multiplier

**Expected Result**:
- Multiplier is set to 5
- Detection time is calculated correctly
- Valid range: 3-50

**Validation**:
```
bfd
 peer 10.1.1.2 interface Ethernet0
  detect-multiplier 5
 !
!
```

---

#### TC_BFD_CLI_010: Configure BFD echo mode

**Objective**: Verify BFD echo mode can be enabled on a peer

**Pre-requisites**:
- BFD peer 10.1.1.2 already configured

**Test Steps**:
1. Enter BFD peer configuration mode:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Enable echo mode:
   ```
   sonic(config-bfd-peer)# echo-mode
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```
4. Check peer details for echo mode status:
   ```
   sonic# show bfd peer 10.1.1.2
   ```

**Expected Result**:
- Echo mode is enabled
- Echo mode flag appears in configuration
- Echo packets will be transmitted (UDP port 3785)

**Validation**:
```
bfd
 peer 10.1.1.2 interface Ethernet0
  echo-mode
 !
!
```

---

#### TC_BFD_CLI_011: Configure BFD echo interval

**Objective**: Verify BFD echo interval can be configured

**Pre-requisites**:
- BFD peer configured with echo-mode enabled

**Test Steps**:
1. Enter BFD peer configuration mode:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Configure echo interval to 200ms:
   ```
   sonic(config-bfd-peer)# echo-interval 200
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Echo interval is set to 200ms
- Echo mode must be enabled for this to take effect
- Valid range: 10-60000 ms

**Validation**:
```
bfd
 peer 10.1.1.2 interface Ethernet0
  echo-mode
  echo-interval 200
 !
!
```

---

#### TC_BFD_CLI_012: Shutdown BFD peer

**Objective**: Verify BFD peer can be administratively shutdown

**Pre-requisites**:
- BFD peer 10.1.1.2 configured and in Up state

**Test Steps**:
1. Check current peer status:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
2. Enter BFD peer configuration mode:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
3. Shutdown the peer:
   ```
   sonic(config-bfd-peer)# shutdown
   ```
4. Verify peer state:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Check running configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Peer state changes to AdminDown
- BFD packets stop being transmitted
- Configuration shows shutdown

**Validation**:
- Peer Status: AdminDown
- Configuration contains `shutdown` command

---

#### TC_BFD_CLI_013: No shutdown BFD peer

**Objective**: Verify administratively shutdown BFD peer can be re-enabled

**Pre-requisites**:
- BFD peer in AdminDown state (from TC_BFD_CLI_012)

**Test Steps**:
1. Verify peer is currently shutdown:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
2. Enter BFD peer configuration mode:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
3. Enable the peer:
   ```
   sonic(config-bfd-peer)# no shutdown
   ```
4. Verify peer state changes:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Wait for session establishment (may take a few seconds)

**Expected Result**:
- Peer state changes from AdminDown
- BFD session re-establishes
- State transitions: AdminDown → Down → Init → Up

**Validation**:
- Final Peer Status: Up
- BFD packets resume transmission

---

#### TC_BFD_CLI_014: Remove BFD peer

**Objective**: Verify BFD peer configuration can be completely removed

**Pre-requisites**:
- BFD peer 10.1.1.2 configured

**Test Steps**:
1. List current BFD peers:
   ```
   sonic# show bfd peers
   ```
2. Enter BFD configuration mode:
   ```
   sonic(config)# bfd
   ```
3. Remove the peer:
   ```
   sonic(config-bfd)# no peer 10.1.1.2 interface Ethernet0
   ```
4. Verify peer is removed:
   ```
   sonic# show bfd peers
   ```
5. Check running configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Peer is completely removed
- No entry in `show bfd peers`
- No peer configuration in running-config

**Validation**:
- Peer 10.1.1.2 should not appear in any show command
- BFD session terminated

---

### 1.3 BFD Show Commands

#### TC_BFD_CLI_015: Show all BFD peers

**Objective**: Verify `show bfd peers` command displays all configured BFD sessions

**Pre-requisites**:
- Multiple BFD peers configured (at least 2-3 peers)

**Test Steps**:
1. Configure multiple BFD peers:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd)# peer 10.2.2.2 interface Ethernet4
   sonic(config-bfd)# peer 2001:db8::2 interface Ethernet8
   ```
2. Execute show command:
   ```
   sonic# show bfd peers
   ```
3. Verify output contains all peers

**Expected Result**:
- All configured peers are listed
- Output includes: Peer IP, Local IP, Interface, Status, Uptime/Downtime

**Sample Output**:
```
Peer                 Local                Interface    Status    Uptime
10.1.1.2             10.1.1.1             Ethernet0    Up        00:05:23
10.2.2.2             10.2.2.1             Ethernet4    Down      00:00:00
2001:db8::2          2001:db8::1          Ethernet8    Up        00:03:45
```

---

#### TC_BFD_CLI_016: Show specific BFD peer

**Objective**: Verify detailed information for a specific BFD peer

**Pre-requisites**:
- BFD peer 10.1.1.2 configured

**Test Steps**:
1. Execute show command for specific peer:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
2. Verify detailed output

**Expected Result**:
- Detailed peer information displayed
- Includes: Status, timers, discriminators, counters, diagnostic info

**Sample Output**:
```
Peer: 10.1.1.2
  Local Address: 10.1.1.1
  Interface: Ethernet0
  Status: Up
  Uptime: 00:10:34
  Diagnostics: None
  Remote Diagnostics: None
  Local Discriminator: 1234567
  Remote Discriminator: 7654321
  Transmit Interval: 300ms
  Receive Interval: 300ms
  Echo Interval: Disabled
  Detect Multiplier: 3
  Packets:
    Control Tx: 2105
    Control Rx: 2098
    Echo Tx: 0
    Echo Rx: 0
```

---

#### TC_BFD_CLI_017: Show BFD peers brief

**Objective**: Verify brief summary of BFD peers

**Pre-requisites**:
- Multiple BFD peers configured

**Test Steps**:
1. Execute brief show command:
   ```
   sonic# show bfd peers brief
   ```

**Expected Result**:
- Condensed output with essential information
- Quick overview of all peers
- Minimal columns: Peer, Status, Interface

**Sample Output**:
```
Peer             Status    Interface
10.1.1.2         Up        Ethernet0
10.2.2.2         Down      Ethernet4
2001:db8::2      Up        Ethernet8

Total Sessions: 3  Up: 2  Down: 1
```

---

#### TC_BFD_CLI_018: Show BFD peers by VRF

**Objective**: Verify BFD peers can be filtered by VRF

**Pre-requisites**:
- BFD peers configured in VRF "Vrf-Blue"
- BFD peers configured in default VRF

**Test Steps**:
1. Show peers in specific VRF:
   ```
   sonic# show bfd peers vrf Vrf-Blue
   ```
2. Verify only VRF-specific peers are shown

**Expected Result**:
- Only peers in specified VRF are displayed
- VRF isolation is maintained

---

#### TC_BFD_CLI_019: Show BFD peers counters

**Objective**: Verify BFD packet counters for all peers

**Pre-requisites**:
- BFD peers in Up state with active packet exchange

**Test Steps**:
1. Execute counters command:
   ```
   sonic# show bfd peers counters
   ```
2. Wait 10 seconds and execute again
3. Verify counters increment

**Expected Result**:
- Tx/Rx counters displayed for all peers
- Counters increment over time
- Echo counters shown if echo mode enabled

**Sample Output**:
```
Peer             Control Tx  Control Rx  Echo Tx  Echo Rx
10.1.1.2         5234        5230        0        0
10.2.2.2         120         0           0        0
2001:db8::2      3456        3450        0        0
```

---

#### TC_BFD_CLI_020: Show BFD running config

**Objective**: Verify BFD configuration can be displayed

**Test Steps**:
1. Execute running config command:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- All BFD configuration displayed in CLI format
- Can be used for backup/restore
- Shows global config, peers, profiles

**Sample Output**:
```
bfd
 slow-timer 5000
 peer 10.1.1.2 interface Ethernet0
  transmit-interval 300
  receive-interval 300
  detect-multiplier 3
 !
 peer 10.2.2.2 interface Ethernet4
 !
!
```

---

#### TC_BFD_CLI_021: Show BFD peer status

**Objective**: Verify BFD peer status summary

**Test Steps**:
1. Execute status command:
   ```
   sonic# show bfd peers status
   ```

**Expected Result**:
- Status for all peers displayed
- Shows state transitions
- Diagnostic codes if available

---

### 1.4 BFD Profile Configuration

#### TC_BFD_CLI_022: Create BFD profile

**Objective**: Verify BFD profile can be created

**Test Steps**:
1. Enter configuration mode:
   ```
   sonic(config)# bfd
   ```
2. Create profile named "fast-detect":
   ```
   sonic(config-bfd)# profile fast-detect
   ```
3. Exit profile configuration:
   ```
   sonic(config-bfd-profile)# exit
   ```
4. Verify profile creation:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Profile is created successfully
- Profile mode is accessible
- Profile appears in configuration

**Validation**:
```
bfd
 profile fast-detect
 !
!
```

---

#### TC_BFD_CLI_023: Configure profile transmit interval

**Objective**: Verify transmit interval can be configured in profile

**Pre-requisites**:
- BFD profile "fast-detect" created

**Test Steps**:
1. Enter profile configuration mode:
   ```
   sonic(config-bfd)# profile fast-detect
   ```
2. Configure transmit interval:
   ```
   sonic(config-bfd-profile)# transmit-interval 100
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Transmit interval set in profile
- Value: 100ms

**Validation**:
```
bfd
 profile fast-detect
  transmit-interval 100
 !
!
```

---

#### TC_BFD_CLI_024: Configure profile receive interval

**Objective**: Verify receive interval can be configured in profile

**Pre-requisites**:
- BFD profile "fast-detect" created

**Test Steps**:
1. Enter profile configuration mode:
   ```
   sonic(config-bfd)# profile fast-detect
   ```
2. Configure receive interval:
   ```
   sonic(config-bfd-profile)# receive-interval 100
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Receive interval set in profile
- Value: 100ms

**Validation**:
```
bfd
 profile fast-detect
  receive-interval 100
 !
!
```

---

#### TC_BFD_CLI_025: Configure profile multiplier

**Objective**: Verify detect multiplier can be configured in profile

**Pre-requisites**:
- BFD profile "fast-detect" created

**Test Steps**:
1. Enter profile configuration mode:
   ```
   sonic(config-bfd)# profile fast-detect
   ```
2. Configure detect multiplier:
   ```
   sonic(config-bfd-profile)# detect-multiplier 3
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Detect multiplier set in profile
- Value: 3

**Validation**:
```
bfd
 profile fast-detect
  transmit-interval 100
  receive-interval 100
  detect-multiplier 3
 !
!
```

---

#### TC_BFD_CLI_026: Apply profile to peer

**Objective**: Verify BFD profile can be applied to a peer

**Pre-requisites**:
- BFD profile "fast-detect" configured with timers
- BFD peer 10.1.1.2 configured

**Test Steps**:
1. Enter BFD peer configuration:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Apply profile to peer:
   ```
   sonic(config-bfd-peer)# profile fast-detect
   ```
3. Verify configuration:
   ```
   sonic# show running-config bfd
   ```
4. Check peer details:
   ```
   sonic# show bfd peer 10.1.1.2
   ```

**Expected Result**:
- Profile is applied to peer
- Peer inherits profile parameters
- Profile name shown in peer configuration

**Validation**:
```
bfd
 profile fast-detect
  transmit-interval 100
  receive-interval 100
  detect-multiplier 3
 !
 peer 10.1.1.2 interface Ethernet0
  profile fast-detect
 !
!
```

---

#### TC_BFD_CLI_027: Remove BFD profile

**Objective**: Verify BFD profile can be removed

**Pre-requisites**:
- BFD profile created but NOT applied to any peer

**Test Steps**:
1. Create a test profile:
   ```
   sonic(config-bfd)# profile test-profile
   sonic(config-bfd-profile)# exit
   ```
2. Verify profile exists:
   ```
   sonic# show running-config bfd
   ```
3. Remove the profile:
   ```
   sonic(config-bfd)# no profile test-profile
   ```
4. Verify profile is removed:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- Profile is deleted successfully
- Profile does not appear in configuration

**Note**: Profile removal should fail if applied to any peer (test in negative tests section)

**Validation**:
- Profile "test-profile" should not exist in running-config

---

## 2. BFD Functional Tests

### 2.1 BFD Session Establishment

#### TC_BFD_FUNC_001: Single-hop BFD session up

**Objective**: Verify single-hop BFD session can be established between directly connected peers

**Pre-requisites**:
- D1 and D2 connected via Ethernet0
- IP configuration: D1: 10.1.1.1/24, D2: 10.1.1.2/24
- Interfaces in up state

**Test Steps**:
1. On DUT1, configure BFD peer:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 300
   sonic(config-bfd-peer)# receive-interval 300
   sonic(config-bfd-peer)# detect-multiplier 3
   sonic(config-bfd-peer)# exit
   ```
2. On DUT2, configure BFD peer:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 10.1.1.1 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 300
   sonic(config-bfd-peer)# receive-interval 300
   sonic(config-bfd-peer)# detect-multiplier 3
   sonic(config-bfd-peer)# exit
   ```
3. Wait for session establishment (up to 3 seconds)
4. Verify BFD session status on DUT1:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Verify BFD session status on DUT2:
   ```
   sonic# show bfd peer 10.1.1.1
   ```
6. Check BFD counters increment:
   ```
   sonic# show bfd peers counters
   ```

**Expected Result**:
- BFD session state: Up on both devices
- State transitions: Down → Init → Up
- Control packets exchanged (Tx and Rx counters incrementing)
- Session uptime starts counting

**Validation**:
- Session Status: Up
- Uptime > 0
- Control Tx > 0, Control Rx > 0

---

#### TC_BFD_FUNC_002: Multi-hop BFD session up

**Objective**: Verify multi-hop BFD session can be established between non-directly connected peers

**Pre-requisites**:
- D1 IP: 10.1.1.1/24
- D2 IP: 10.2.2.2/24
- Routing configured between D1 and D2 (static routes or IGP)
- Reachability verified via ping

**Test Steps**:
1. On DUT1, configure multi-hop BFD peer:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 10.2.2.2 multihop local-address 10.1.1.1
   sonic(config-bfd-peer)# transmit-interval 500
   sonic(config-bfd-peer)# receive-interval 500
   sonic(config-bfd-peer)# exit
   ```
2. On DUT2, configure multi-hop BFD peer:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 10.1.1.1 multihop local-address 10.2.2.2
   sonic(config-bfd-peer)# transmit-interval 500
   sonic(config-bfd-peer)# receive-interval 500
   sonic(config-bfd-peer)# exit
   ```
3. Verify BFD session establishment:
   ```
   sonic# show bfd peers
   ```
4. Capture BFD packets on D1:
   ```
   tcpdump -i any udp port 4784 -vv
   ```

**Expected Result**:
- Multi-hop BFD session state: Up
- BFD packets use UDP port 4784 (not 3784)
- IP TTL > 1 (not restricted to 255)
- Local and remote addresses correctly associated

**Validation**:
- Session Status: Up
- Multihop flag: Enabled
- UDP destination port: 4784

---

#### TC_BFD_FUNC_003: BFD session over physical interface

**Objective**: Verify BFD session establishment on physical Ethernet interface

**Pre-requisites**:
- Physical link between D1 Ethernet0 and D2 Ethernet0
- IP addresses configured

**Test Steps**:
1. Verify interface status:
   ```
   sonic# show interface status Ethernet0
   ```
2. Configure IP addresses:
   ```
   D1: sonic(config)# interface Ethernet0
   D1: sonic(config-if)# ip address 10.1.1.1/24

   D2: sonic(config)# interface Ethernet0
   D2: sonic(config-if)# ip address 10.1.1.2/24
   ```
3. Configure BFD on both sides (single-hop)
4. Verify BFD session up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Verify interface statistics:
   ```
   sonic# show interface counters Ethernet0
   ```

**Expected Result**:
- BFD session establishes successfully
- Session binds to physical interface Ethernet0
- Interface counters show BFD traffic

**Validation**:
- Session Status: Up
- Interface: Ethernet0
- Interface status: Up

---

#### TC_BFD_FUNC_004: BFD session over PortChannel

**Objective**: Verify BFD session can be established over LAG/PortChannel interface

**Pre-requisites**:
- PortChannel10 configured on D1 and D2
- Member interfaces: Ethernet8, Ethernet12
- IP addresses: D1: 10.10.10.1/24, D2: 10.10.10.2/24

**Test Steps**:
1. Configure PortChannel on D1:
   ```
   sonic(config)# interface PortChannel10
   sonic(config-if)# ip address 10.10.10.1/24
   sonic(config)# interface Ethernet8
   sonic(config-if)# channel-group 10 mode active
   sonic(config)# interface Ethernet12
   sonic(config-if)# channel-group 10 mode active
   ```
2. Configure PortChannel on D2 (similarly)
3. Verify PortChannel status:
   ```
   sonic# show interface PortChannel 10
   ```
4. Configure BFD over PortChannel:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 10.10.10.2 interface PortChannel10
   ```
5. Verify BFD session:
   ```
   sonic# show bfd peer 10.10.10.2
   ```
6. Test resilience - shutdown one LAG member:
   ```
   sonic(config)# interface Ethernet8
   sonic(config-if)# shutdown
   ```
7. Verify BFD session remains Up:
   ```
   sonic# show bfd peer 10.10.10.2
   ```

**Expected Result**:
- BFD session establishes over PortChannel
- Session remains Up when one LAG member fails
- Session goes Down only when all members fail

**Validation**:
- Session Status: Up
- Interface: PortChannel10
- Resilience: Session survives single member failure

---

#### TC_BFD_FUNC_005: BFD session over VLAN interface

**Objective**: Verify BFD session over VLAN (L3 VLAN interface)

**Pre-requisites**:
- VLAN 100 created on both D1 and D2
- Ethernet0 configured as trunk with VLAN 100

**Test Steps**:
1. Create VLAN on D1:
   ```
   sonic(config)# vlan 100
   sonic(config-vlan)# exit
   sonic(config)# interface Vlan 100
   sonic(config-if)# ip address 10.100.100.1/24
   sonic(config)# interface Ethernet0
   sonic(config-if)# switchport mode trunk
   sonic(config-if)# switchport trunk allowed vlan 100
   ```
2. Create VLAN on D2 (similarly with IP 10.100.100.2/24)
3. Verify VLAN interface status:
   ```
   sonic# show vlan brief
   sonic# show interface Vlan 100
   ```
4. Configure BFD over VLAN interface:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 10.100.100.2 interface Vlan100
   ```
5. Verify BFD session:
   ```
   sonic# show bfd peers
   ```
6. Capture packets to verify VLAN tagging:
   ```
   tcpdump -i Ethernet0 -e vlan 100 and udp port 3784
   ```

**Expected Result**:
- BFD session establishes over Vlan100
- BFD packets are VLAN-tagged (VLAN ID 100)
- Session state: Up

**Validation**:
- Session Status: Up
- Interface: Vlan100
- VLAN tag present in packet capture

---

#### TC_BFD_FUNC_006: BFD IPv4 session establishment

**Objective**: Verify BFD session establishment using IPv4 addressing

**Pre-requisites**:
- IPv4 connectivity between D1 and D2

**Test Steps**:
1. Configure IPv4 addresses:
   ```
   D1: 192.168.10.1/24
   D2: 192.168.10.2/24
   ```
2. Configure IPv4 BFD peer on D1:
   ```
   sonic(config-bfd)# peer 192.168.10.2 interface Ethernet0
   ```
3. Configure IPv4 BFD peer on D2:
   ```
   sonic(config-bfd)# peer 192.168.10.1 interface Ethernet0
   ```
4. Verify session establishment:
   ```
   sonic# show bfd peers
   ```
5. Verify IPv4 packet headers via tcpdump:
   ```
   tcpdump -i Ethernet0 host 192.168.10.2 and udp port 3784 -n
   ```

**Expected Result**:
- BFD session Up with IPv4 peer addresses
- IPv4 headers in BFD packets
- Source IP: 192.168.10.1, Dest IP: 192.168.10.2

**Validation**:
- Session Status: Up
- Peer address type: IPv4
- Packet capture shows IPv4 headers

---

#### TC_BFD_FUNC_007: BFD IPv6 session establishment

**Objective**: Verify BFD session establishment using IPv6 addressing

**Pre-requisites**:
- IPv6 connectivity between D1 and D2
- IPv6 enabled on interfaces

**Test Steps**:
1. Configure IPv6 addresses:
   ```
   D1: sonic(config-if)# ipv6 address 2001:db8:1::1/64
   D2: sonic(config-if)# ipv6 address 2001:db8:1::2/64
   ```
2. Verify IPv6 connectivity:
   ```
   sonic# ping ipv6 2001:db8:1::2
   ```
3. Configure IPv6 BFD peer on D1:
   ```
   sonic(config-bfd)# peer 2001:db8:1::2 interface Ethernet0
   ```
4. Configure IPv6 BFD peer on D2:
   ```
   sonic(config-bfd)# peer 2001:db8:1::1 interface Ethernet0
   ```
5. Verify session establishment:
   ```
   sonic# show bfd peers
   ```
6. Capture IPv6 BFD packets:
   ```
   tcpdump -i Ethernet0 ip6 and udp port 3784 -vv
   ```

**Expected Result**:
- BFD session Up with IPv6 peer addresses
- IPv6 headers in BFD packets
- Hop limit = 255 for single-hop BFD

**Validation**:
- Session Status: Up
- Peer address type: IPv6
- IPv6 hop limit: 255

---

#### TC_BFD_FUNC_008: BFD session with default timers

**Objective**: Verify BFD session establishment with default timer values

**Pre-requisites**:
- D1 and D2 connected and configured

**Test Steps**:
1. Configure BFD peer without specifying timers:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Check default timer values:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
3. Verify session establishes with defaults:
   ```
   sonic# show bfd peers
   ```

**Expected Result**:
- Session establishes successfully
- Default timers applied:
  - Transmit interval: 300ms (typical default)
  - Receive interval: 300ms (typical default)
  - Detect multiplier: 3 (typical default)

**Validation**:
- Session Status: Up
- Timers match system defaults
- Detection time = rx_interval × multiplier

---

#### TC_BFD_FUNC_009: BFD session with custom timers

**Objective**: Verify BFD session with user-configured custom timers

**Pre-requisites**:
- D1 and D2 connected

**Test Steps**:
1. Configure BFD with custom timers on D1:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 100
   sonic(config-bfd-peer)# receive-interval 100
   sonic(config-bfd-peer)# detect-multiplier 5
   ```
2. Configure matching timers on D2:
   ```
   sonic(config-bfd)# peer 10.1.1.1 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 100
   sonic(config-bfd-peer)# receive-interval 100
   sonic(config-bfd-peer)# detect-multiplier 5
   ```
3. Verify session establishment:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
4. Calculate and verify detection time:
   - Expected: 100ms × 5 = 500ms
5. Monitor packet rate:
   ```
   sonic# show bfd peers counters
   ```
   - Wait 10 seconds, check again
   - Expected packets in 10s: ~100 packets (at 100ms interval)

**Expected Result**:
- Session establishes with custom timers
- Transmit interval: 100ms
- Receive interval: 100ms
- Detect multiplier: 5
- Detection time: 500ms
- Packet rate matches configured interval

**Validation**:
- Session Status: Up
- Configured timers active
- Packet rate: ~10 packets/second

---

#### TC_BFD_FUNC_010: BFD session with minimum timers

**Objective**: Verify BFD session with minimum allowed timer values

**Pre-requisites**:
- D1 and D2 connected
- Verify minimum timer support (typically 10ms or 50ms)

**Test Steps**:
1. Configure BFD with minimum timers on D1:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 50
   sonic(config-bfd-peer)# receive-interval 50
   sonic(config-bfd-peer)# detect-multiplier 3
   ```
2. Configure matching timers on D2
3. Verify session establishment:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
4. Monitor CPU utilization:
   ```
   sonic# show processes cpu
   ```
5. Verify packet rate is very high:
   - Expected: ~20 packets/second (at 50ms)

**Expected Result**:
- Session establishes with minimum timers
- Very fast failure detection (150ms = 50ms × 3)
- High packet rate
- CPU utilization acceptable
- Session stable

**Validation**:
- Session Status: Up
- Timers: 50ms tx/rx
- Detection time: 150ms
- CPU usage within acceptable limits

### 2.2 BFD with Routing Protocols

#### 2.2.1 BFD with Static Routes

#### TC_BFD_STATIC_001: BFD with IPv4 static route

**Objective**: Verify static IPv4 route tracks BFD session state

**Pre-requisites**:
- D1 and D2 connected via 10.1.1.0/24
- D2 has network 192.168.100.0/24 behind it
- BFD session between D1 and D2

**Test Steps**:
1. Configure BFD session between D1 (10.1.1.1) and D2 (10.1.1.2)
2. On D1, configure static route with BFD tracking:
   ```
   sonic(config)# ip route 192.168.100.0/24 10.1.1.2 track bfd
   ```
3. Verify BFD session is Up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
4. Verify route is installed in RIB:
   ```
   sonic# show ip route 192.168.100.0/24
   ```
5. Send traffic to 192.168.100.0/24 network using Scapy:
   ```python
   # Send ICMP packets via spytest
   tg.tg_traffic_config(mode='create', transmit_mode='continuous',
                        src_mac='00:00:00:00:00:01', dst_mac=D1_mac,
                        ip_src_addr='10.1.1.10', ip_dst_addr='192.168.100.50',
                        rate_pps=100)
   ```
6. Verify traffic forwarding via counters

**Expected Result**:
- Static route installed when BFD Up
- Traffic forwards to 192.168.100.0/24
- Route shown in RIB with BFD tracking

**Validation**:
- Route present in RIB
- Route protocol: Static
- BFD tracking: Enabled
- Next-hop reachable

---

#### TC_BFD_STATIC_002: BFD static route failover

**Objective**: Verify static route is removed when BFD session goes down

**Pre-requisites**:
- TC_BFD_STATIC_001 completed
- Static route with BFD tracking active

**Test Steps**:
1. Verify route is currently in RIB:
   ```
   sonic# show ip route 192.168.100.0/24
   ```
2. Start traffic flow to destination network
3. Shutdown BFD peer administratively on D1:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# shutdown
   ```
4. Verify BFD session goes to AdminDown:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Verify route is removed from RIB:
   ```
   sonic# show ip route 192.168.100.0/24
   ```
6. Verify traffic stops (check counters)

**Expected Result**:
- BFD session: AdminDown
- Static route removed from RIB immediately
- Traffic forwarding stops
- Fast convergence (< 1 second)

**Validation**:
- Route NOT in RIB
- Traffic drops
- BFD-triggered route withdrawal

---

#### TC_BFD_STATIC_003: BFD static route recovery

**Objective**: Verify static route is restored when BFD session recovers

**Pre-requisites**:
- TC_BFD_STATIC_002 completed
- BFD session currently AdminDown

**Test Steps**:
1. Verify route is absent:
   ```
   sonic# show ip route 192.168.100.0/24
   ```
2. Re-enable BFD peer on D1:
   ```
   sonic(config-bfd-peer)# no shutdown
   ```
3. Wait for BFD session re-establishment (2-3 seconds)
4. Verify BFD session Up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Verify route is re-installed:
   ```
   sonic# show ip route 192.168.100.0/24
   ```
6. Resume traffic and verify forwarding

**Expected Result**:
- BFD session: Up
- Static route automatically re-installed
- Traffic forwarding resumes
- Fast recovery

**Validation**:
- Route present in RIB
- Next-hop reachable via BFD
- Traffic resumes

---

#### TC_BFD_STATIC_004: BFD with IPv6 static route

**Objective**: Verify static IPv6 route tracks BFD session

**Pre-requisites**:
- IPv6 connectivity: D1 (2001:db8:1::1), D2 (2001:db8:1::2)
- IPv6 network 2001:db8:100::/64 behind D2

**Test Steps**:
1. Configure IPv6 BFD session
2. Configure IPv6 static route with BFD on D1:
   ```
   sonic(config)# ipv6 route 2001:db8:100::/64 2001:db8:1::2 track bfd
   ```
3. Verify BFD session Up
4. Verify IPv6 route in RIB:
   ```
   sonic# show ipv6 route 2001:db8:100::/64
   ```
5. Test IPv6 traffic using Scapy
6. Shutdown BFD and verify route withdrawal
7. Re-enable BFD and verify route restoration

**Expected Result**:
- IPv6 static route tracks BFD session
- Route installed/removed based on BFD state
- IPv6 traffic forwarding follows route state

**Validation**:
- IPv6 route in RIB when BFD Up
- Route removed when BFD Down
- Traffic behavior matches route state

---

#### TC_BFD_STATIC_005: Multiple static routes with BFD

**Objective**: Verify multiple static routes can track same BFD session

**Pre-requisites**:
- BFD session between D1 and D2
- Multiple networks behind D2

**Test Steps**:
1. Configure multiple static routes on D1, all tracking same BFD:
   ```
   sonic(config)# ip route 192.168.10.0/24 10.1.1.2 track bfd
   sonic(config)# ip route 192.168.20.0/24 10.1.1.2 track bfd
   sonic(config)# ip route 192.168.30.0/24 10.1.1.2 track bfd
   sonic(config)# ip route 192.168.40.0/24 10.1.1.2 track bfd
   ```
2. Verify all routes installed:
   ```
   sonic# show ip route | include 192.168
   ```
3. Verify all routes show BFD tracking
4. Shutdown BFD session
5. Verify all routes removed simultaneously:
   ```
   sonic# show ip route | include 192.168
   ```
6. Re-enable BFD
7. Verify all routes restored

**Expected Result**:
- All static routes installed when BFD Up
- All routes removed together when BFD Down
- All routes restored together when BFD recovers
- Single BFD session controls multiple routes

**Validation**:
- 4 routes installed when BFD Up
- 0 routes when BFD Down
- Consistent state across all routes

#### 2.2.2 BFD with BGP
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_BGP_001 | BFD for BGP neighbor | Enable BFD on BGP neighbor | BFD session tracks BGP |
| TC_BFD_BGP_002 | BGP fast failover with BFD | BFD down event | BGP session tears down fast |
| TC_BFD_BGP_003 | BGP recovery with BFD | BFD session recovery | BGP session re-establishes |
| TC_BFD_BGP_004 | BFD with eBGP single-hop | Configure BFD for eBGP | Fast failure detection |
| TC_BFD_BGP_005 | BFD with eBGP multi-hop | Configure multi-hop BFD for eBGP | Multi-hop BFD tracks eBGP |
| TC_BFD_BGP_006 | BFD with iBGP | Configure BFD for iBGP | BFD tracks iBGP session |

#### 2.2.3 BFD with OSPF
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_OSPF_001 | BFD for OSPF interface | Enable BFD on OSPF interface | BFD detects OSPF neighbor |
| TC_BFD_OSPF_002 | OSPF fast convergence with BFD | BFD down event | OSPF converges rapidly |
| TC_BFD_OSPF_003 | BFD with OSPFv2 | Configure BFD for OSPFv2 | OSPFv2 uses BFD |
| TC_BFD_OSPF_004 | BFD with OSPFv3 | Configure BFD for OSPFv3 | OSPFv3 uses BFD |

### 2.3 BFD Session State Transitions
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_STATE_001 | BFD session Down to Init | Initial configuration | State: Init |
| TC_BFD_STATE_002 | BFD session Init to Up | Both peers configured | State: Up |
| TC_BFD_STATE_003 | BFD session Up to Down | Link failure | State: Down |
| TC_BFD_STATE_004 | BFD session AdminDown | Shutdown peer | State: AdminDown |
| TC_BFD_STATE_005 | BFD session AdminDown to Up | No shutdown peer | State: Up |
| TC_BFD_STATE_006 | BFD session timeout detection | Stop BFD packets | Detect timeout, go Down |

### 2.4 BFD Echo Mode
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_ECHO_001 | Enable BFD echo mode | Configure echo-mode | Echo packets transmitted |
| TC_BFD_ECHO_002 | BFD echo interval configuration | Set echo interval | Verify echo timing |
| TC_BFD_ECHO_003 | BFD echo mode failover | Link down with echo mode | Fast detection via echo |
| TC_BFD_ECHO_004 | Disable BFD echo mode | Remove echo-mode | Control packets only |

### 2.5 BFD Timers and Parameters
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_TIMER_001 | Modify transmit interval runtime | Change tx interval on active session | Session adapts to new interval |
| TC_BFD_TIMER_002 | Modify receive interval runtime | Change rx interval on active session | Session adapts to new interval |
| TC_BFD_TIMER_003 | Modify detect multiplier runtime | Change multiplier on active session | Detection time updated |
| TC_BFD_TIMER_004 | Asymmetric timer negotiation | Different tx/rx on each peer | Session uses negotiated values |
| TC_BFD_TIMER_005 | Fast BFD timers (50ms) | Configure 50ms intervals | Fast failure detection |
| TC_BFD_TIMER_006 | Slow BFD timers (1000ms) | Configure 1000ms intervals | Slower detection |
| TC_BFD_TIMER_007 | BFD multiplier effect | Test with multiplier 3,5,7 | Detection time = rx * multiplier |

### 2.6 BFD Traffic Validation (Scapy)

#### TC_BFD_TRAFFIC_001: Capture BFD control packets

**Objective**: Verify BFD control packets are transmitted and received correctly

**Pre-requisites**:
- BFD session Up between D1 (10.1.1.1) and D2 (10.1.1.2)
- Tcpdump available on both devices
- Scapy installed for packet verification

**Test Steps**:
1. Establish BFD session:
   ```
   D1: sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   D1: sonic(config-bfd-peer)# transmit-interval 300
   D1: sonic(config-bfd-peer)# receive-interval 300

   D2: sonic(config-bfd)# peer 10.1.1.1 interface Ethernet0
   D2: sonic(config-bfd-peer)# transmit-interval 300
   D2: sonic(config-bfd-peer)# receive-interval 300
   ```
2. Verify session Up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
3. Start tcpdump on D1 Ethernet0:
   ```
   sonic# tcpdump -i Ethernet0 'udp port 3784' -w /tmp/bfd_control.pcap -c 20
   ```
4. Wait for 20 packets (approximately 6 seconds at 300ms interval)
5. Stop tcpdump and verify file:
   ```
   sonic# ls -lh /tmp/bfd_control.pcap
   ```
6. Parse packets with Scapy:
   ```python
   from scapy.all import rdpcap
   packets = rdpcap('/tmp/bfd_control.pcap')

   for pkt in packets:
       if pkt.haslayer('UDP'):
           udp = pkt['UDP']
           if udp.dport == 3784 or udp.sport == 3784:
               print(f"BFD Control packet: {pkt['IP'].src} -> {pkt['IP'].dst}")
   ```
7. Verify packet count:
   ```python
   bfd_packets = [p for p in packets if p.haslayer('UDP') and
                  (p['UDP'].dport == 3784 or p['UDP'].sport == 3784)]
   print(f"Total BFD control packets captured: {len(bfd_packets)}")
   ```
8. Clean up:
   ```
   sonic# rm /tmp/bfd_control.pcap
   ```

**Expected Result**:
- 20 BFD control packets captured
- Packets alternate between D1→D2 and D2→D1
- UDP destination port 3784 for control packets
- Packets arrive at ~300ms intervals
- Packet size: typically 24-48 bytes (depending on extensions)

**Validation**:
- Packet count: 20
- Port: 3784
- Interval: ~300ms (±10%)
- Packet size: > 20 bytes

**Cleanup**: Remove tcpdump files after execution (per user instructions)

---

#### TC_BFD_TRAFFIC_002: Verify BFD packet format

**Objective**: Verify BFD packets have correct RFC 5880 format and fields

**Pre-requisites**:
- BFD session Up and stable
- Tcpdump capture from TC_BFD_TRAFFIC_001 or fresh capture

**Test Steps**:
1. Capture BFD packets:
   ```
   sonic# tcpdump -i Ethernet0 'udp port 3784' -w /tmp/bfd_format.pcap -c 5
   ```
2. Parse with Scapy and verify format:
   ```python
   from scapy.all import rdpcap, Raw
   import struct

   packets = rdpcap('/tmp/bfd_format.pcap')

   for pkt in packets:
       if pkt.haslayer('Raw'):
           bfd_payload = pkt['Raw'].load

           # BFD packet structure (RFC 5880)
           # Byte 0: Version (3 bits), Diagnostic (5 bits)
           # Byte 1: State (2 bits), Poll (1 bit), Final (1 bit),
           #         Control Plane Independent (1 bit), Auth Present (1 bit), Reserved (2 bits)
           # Byte 2: Detect Multiplier (1 byte)
           # Bytes 3: Message Length (1 byte)
           # Bytes 4-7: My Discriminator (4 bytes)
           # Bytes 8-11: Your Discriminator (4 bytes)
           # Bytes 12-15: Desired Min TX Interval (4 bytes, microseconds)
           # Bytes 16-19: Required Min RX Interval (4 bytes, microseconds)
           # Bytes 20-23: Required Min Echo RX Interval (4 bytes, microseconds)

           if len(bfd_payload) >= 24:
               version_diag = bfd_payload[0]
               version = (version_diag >> 5) & 0x07
               diagnostic = version_diag & 0x1F

               state_flags = bfd_payload[1]
               state = (state_flags >> 6) & 0x03

               multiplier = bfd_payload[2]
               msg_length = bfd_payload[3]

               print(f"Version: {version}, Diagnostic: {diagnostic}")
               print(f"State: {state}, Detect Multiplier: {multiplier}")
               print(f"Message Length: {msg_length}")
   ```
3. Verify each field:
   - Version = 3 (RFC 5880)
   - Diagnostic codes: 0=No diagnostic, 1=Detect time expired, etc.
   - State: 0=AdminDown, 1=Down, 2=Init, 3=Up
   - Message length: ≥ 24 bytes
   - Discriminators: non-zero unique values
4. Verify intervals (in microseconds):
   ```python
   desired_tx_us = struct.unpack('!I', bfd_payload[12:16])[0]
   required_rx_us = struct.unpack('!I', bfd_payload[16:20])[0]

   desired_tx_ms = desired_tx_us / 1000
   required_rx_ms = required_rx_us / 1000

   print(f"Desired Min TX: {desired_tx_ms}ms")
   print(f"Required Min RX: {required_rx_ms}ms")
   ```

**Expected Result**:
- Version: 3
- Message length: ≥ 24 bytes
- State field: 2 (Init) or 3 (Up)
- Detect multiplier: 3-50
- TX/RX intervals match configuration
- All mandatory fields present and valid

**Validation**:
- RFC 5880 compliance verified
- All fields correctly formatted
- Interval values in microseconds
- Version correct

---

#### TC_BFD_TRAFFIC_003: Verify BFD echo packets

**Objective**: Verify BFD echo packets are transmitted when echo mode enabled

**Pre-requisites**:
- BFD session configured with echo-mode enabled
- Session Up and stable

**Test Steps**:
1. Configure BFD with echo mode on D1:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# echo-mode
   sonic(config-bfd-peer)# echo-interval 100
   ```
2. Configure matching echo mode on D2
3. Verify session remains Up:
   ```
   sonic# show bfd peer 10.1.1.2 | include echo
   ```
4. Capture both control and echo packets:
   ```
   sonic# tcpdump -i Ethernet0 'udp port 3784 or udp port 3785' -w /tmp/bfd_echo.pcap -c 30
   ```
5. Analyze packet types:
   ```python
   from scapy.all import rdpcap

   packets = rdpcap('/tmp/bfd_echo.pcap')
   control_pkts = []
   echo_pkts = []

   for pkt in packets:
       if pkt.haslayer('UDP'):
           dport = pkt['UDP'].dport
           sport = pkt['UDP'].sport

           if dport == 3784 or sport == 3784:
               control_pkts.append(pkt)
           elif dport == 3785 or sport == 3785:
               echo_pkts.append(pkt)

   print(f"Control packets (port 3784): {len(control_pkts)}")
   print(f"Echo packets (port 3785): {len(echo_pkts)}")
   ```
6. Verify echo packet format (same as control but on port 3785)
7. Disable echo mode and verify echo packets stop:
   ```
   sonic(config-bfd-peer)# no echo-mode
   # Wait and capture again - should see only control packets
   ```

**Expected Result**:
- Control packets on port 3784 (continuous)
- Echo packets on port 3785 (when echo mode enabled)
- Echo interval: 100ms (as configured)
- Echo packets cease when echo-mode disabled
- Packet rate: control (300ms) + echo (100ms)

**Validation**:
- Echo packets present on port 3785
- Echo interval matches configuration
- Packet count: ~2 echo packets per 1 control packet (300ms/100ms)
- Echo packets stop when disabled

---

#### TC_BFD_TRAFFIC_004: BFD packet rate verification

**Objective**: Verify BFD packet transmission rate matches configured intervals

**Pre-requisites**:
- BFD session with known transmit interval (e.g., 300ms)
- System time synchronized

**Test Steps**:
1. Configure BFD with specific interval:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 200
   sonic(config-bfd-peer)# receive-interval 200
   ```
2. Wait for session to stabilize (10 seconds)
3. Capture packets with timestamps:
   ```
   sonic# tcpdump -i Ethernet0 'udp port 3784' -w /tmp/bfd_rate.pcap -c 50
   ```
4. Analyze timestamps and calculate intervals:
   ```python
   from scapy.all import rdpcap
   import statistics

   packets = rdpcap('/tmp/bfd_rate.pcap')

   # Extract timestamps
   timestamps = []
   for pkt in packets:
       if pkt.haslayer('UDP'):
           timestamps.append(pkt.time)

   # Calculate intervals between packets
   intervals_ms = []
   for i in range(1, len(timestamps)):
       interval = (timestamps[i] - timestamps[i-1]) * 1000  # Convert to ms
       intervals_ms.append(interval)

   # Statistics
   avg_interval = statistics.mean(intervals_ms)
   min_interval = min(intervals_ms)
   max_interval = max(intervals_ms)
   stdev_interval = statistics.stdev(intervals_ms)

   print(f"Average interval: {avg_interval:.2f}ms")
   print(f"Min interval: {min_interval:.2f}ms")
   print(f"Max interval: {max_interval:.2f}ms")
   print(f"Std Dev: {stdev_interval:.2f}ms")
   ```
5. Verify with different intervals:
   - Test with 50ms intervals
   - Test with 1000ms intervals
   - Verify consistency

**Expected Result**:
- Average interval matches configured tx-interval (±5%)
- No missed packets (intervals should be consistent)
- Standard deviation < 10% of configured interval
- No extreme outliers

**Validation**:
- Packet rate matches configuration
- Interval consistency good (low std dev)
- No packets lost or duplicated
- Linear relationship between interval and rate

---

#### TC_BFD_TRAFFIC_005: BFD discriminator validation

**Objective**: Verify discriminator fields are correctly set and negotiated

**Pre-requisites**:
- BFD session Up between D1 and D2

**Test Steps**:
1. Capture BFD packets:
   ```
   sonic# tcpdump -i Ethernet0 'udp port 3784' -w /tmp/bfd_disc.pcap -c 10
   ```
2. Extract discriminators from packets:
   ```python
   from scapy.all import rdpcap
   import struct

   packets = rdpcap('/tmp/bfd_disc.pcap')

   for pkt in packets:
       if pkt.haslayer('Raw'):
           bfd_payload = pkt['Raw'].load

           if len(bfd_payload) >= 12:
               my_disc = struct.unpack('!I', bfd_payload[4:8])[0]
               your_disc = struct.unpack('!I', bfd_payload[8:12])[0]

               src_ip = pkt['IP'].src
               print(f"From {src_ip}:")
               print(f"  My Discriminator: {my_disc}")
               print(f"  Your Discriminator: {your_disc}")
   ```
3. Verify discriminator properties:
   - My Discriminator: Non-zero unique value per device
   - Your Discriminator: Matches remote's My Discriminator (negotiated)
4. Check consistency across packets:
   ```python
   my_discs = set()
   your_discs = set()

   for pkt in packets:
       if pkt.haslayer('Raw'):
           bfd_payload = pkt['Raw'].load
           if len(bfd_payload) >= 12:
               my_disc = struct.unpack('!I', bfd_payload[4:8])[0]
               your_disc = struct.unpack('!I', bfd_payload[8:12])[0]
               my_discs.add(my_disc)
               your_discs.add(your_disc)

   print(f"Unique My Discriminators: {len(my_discs)}")
   print(f"Unique Your Discriminators: {len(your_discs)}")
   ```
5. Verify with show command:
   ```
   sonic# show bfd peer 10.1.1.2 | include Discriminator
   ```

**Expected Result**:
- My Discriminator: Non-zero, unique per session
- Your Discriminator: Non-zero, matches peer's My Discriminator
- Discriminators stable (same across all packets)
- Both 32-bit values

**Validation**:
- Discriminators correctly populated
- Negotiation successful (Your Disc matches peer's My Disc)
- Consistent across all packets
- Matches CLI output

---

#### TC_BFD_TRAFFIC_006: BFD state field validation

**Objective**: Verify BFD packet State field matches actual session state

**Pre-requisites**:
- BFD session at different states (Down, Init, Up)

**Test Steps**:
1. Capture initial packets (Down/Init state):
   ```
   sonic# tcpdump -i Ethernet0 'udp port 3784' -w /tmp/bfd_state_down.pcap -c 5
   ```
2. Extract state field:
   ```python
   from scapy.all import rdpcap

   def get_bfd_state(bfd_payload):
       state_flags = bfd_payload[1]
       state = (state_flags >> 6) & 0x03

       state_names = {
           0: 'AdminDown',
           1: 'Down',
           2: 'Init',
           3: 'Up'
       }
       return state_names.get(state, 'Unknown')

   packets = rdpcap('/tmp/bfd_state_down.pcap')
   for pkt in packets:
       if pkt.haslayer('Raw'):
           bfd_payload = pkt['Raw'].load
           state = get_bfd_state(bfd_payload)
           print(f"Packet state: {state}")
   ```
3. Wait for session to come Up (20-30 seconds)
4. Capture Up state packets:
   ```
   sonic# tcpdump -i Ethernet0 'udp port 3784' -w /tmp/bfd_state_up.pcap -c 5
   ```
5. Verify state changed to Up:
   ```python
   packets_up = rdpcap('/tmp/bfd_state_up.pcap')
   for pkt in packets_up:
       if pkt.haslayer('Raw'):
           bfd_payload = pkt['Raw'].load
           state = get_bfd_state(bfd_payload)
           assert state == 'Up', f"Expected Up, got {state}"
   ```
6. Shutdown peer and capture AdminDown:
   ```
   sonic(config-bfd-peer)# shutdown
   sonic# tcpdump -i Ethernet0 'udp port 3784' -w /tmp/bfd_state_admin.pcap -c 5
   ```
7. Verify AdminDown state:
   ```python
   packets_admin = rdpcap('/tmp/bfd_state_admin.pcap')
   for pkt in packets_admin:
       if pkt.haslayer('Raw'):
           bfd_payload = pkt['Raw'].load
           state = get_bfd_state(bfd_payload)
           assert state == 'AdminDown', f"Expected AdminDown, got {state}"
   ```

**Expected Result**:
- Packet State field matches CLI-reported session state
- Down state: initial packets show Down
- Init state: intermediate state before Up
- Up state: stable after convergence
- AdminDown: immediately after shutdown

**Validation**:
- State field changes match state transitions
- Consistent with `show bfd peer` output
- Correct state encoding (0-3)

---

#### TC_BFD_TRAFFIC_007: BFD diagnostic code

**Objective**: Verify BFD diagnostic field contains appropriate codes

**Pre-requisites**:
- BFD session in various states

**Test Steps**:
1. Capture packets and extract diagnostic code:
   ```python
   from scapy.all import rdpcap

   def get_diagnostic_code(bfd_payload):
       version_diag = bfd_payload[0]
       diagnostic = version_diag & 0x1F

       diag_codes = {
           0: 'No Diagnostic',
           1: 'Detect Time Expired',
           2: 'Echo Function Failed',
           3: 'Neighbor Signaled Session Down',
           4: 'Forwarding Plane Reset',
           5: 'Path Down',
           6: 'Concatenated Path Down',
           7: 'Administratively Down',
           8: 'Reverse Concatenated Path Down',
           9: 'Reserved for future use'
       }
       return diag_codes.get(diagnostic, f'Unknown ({diagnostic})')

   packets = rdpcap('/tmp/bfd_diag.pcap')
   for pkt in packets:
       if pkt.haslayer('Raw'):
           bfd_payload = pkt['Raw'].load
           diag = get_diagnostic_code(bfd_payload)
           print(f"Diagnostic: {diag}")
   ```
2. Test various scenarios:
   - Normal Up state: Diagnostic = 0 (No Diagnostic)
   - After shutdown: Diagnostic = 7 (Administratively Down)
   - After interface down: Diagnostic = 5 (Path Down)
3. Verify field values match expected codes
4. Check diagnostic persistence across packets

**Expected Result**:
- No Diagnostic (0) during normal operation
- Administratively Down (7) when peer shutdown
- Path Down (5) when interface down
- Diagnostic codes follow RFC 5880
- Codes persist for given condition

**Validation**:
- Diagnostic codes match RFC 5880
- Codes reflect current session condition
- Consistent across multiple packets

---

#### TC_BFD_TRAFFIC_008: Send malformed BFD packet

**Objective**: Verify system handles malformed BFD packets gracefully

**Pre-requisites**:
- BFD session Up between D1 and D2
- Scapy available for packet injection

**Test Steps**:
1. Verify session before injection:
   ```
   sonic# show bfd peer 10.1.1.2 | include State
   ```
2. Inject malformed packet (too short):
   ```python
   from scapy.all import IP, UDP, Raw, send

   # Create packet shorter than minimum (24 bytes)
   malformed = IP(dst='10.1.1.1')/UDP(dport=3784)/Raw(load=b'\x00' * 10)
   send(malformed)
   ```
3. Wait 2 seconds
4. Verify session still Up:
   ```
   sonic# show bfd peer 10.1.1.2 | include State
   ```
5. Check for error logging:
   ```
   sonic# show logging | include -i error | include -i bfd
   ```
6. Inject packet with invalid version:
   ```python
   # Invalid version (not 3)
   invalid_version = IP(dst='10.1.1.1')/UDP(dport=3784)/Raw(load=bytes([0x40]) + b'\x00' * 23)
   send(invalid_version)
   ```
7. Inject packet with invalid message length:
   ```python
   # Message length too large
   invalid_length = IP(dst='10.1.1.1')/UDP(dport=3784)/Raw(load=bytes([0xC0, 0x00, 0x03, 255]) + b'\x00' * 20)
   send(invalid_length)
   ```
8. Verify session stability

**Expected Result**:
- Session remains Up after malformed packets
- No session state change
- Error messages logged (optional but expected)
- System remains stable
- No daemon crashes

**Validation**:
- Session State: Up (unchanged)
- No disruption to normal packets
- Graceful error handling
- System responsive

---

#### TC_BFD_TRAFFIC_009: BFD packet with wrong discriminator

**Objective**: Verify packets with incorrect discriminators are discarded

**Pre-requisites**:
- BFD session Up with known discriminators
- Scapy available for packet injection

**Test Steps**:
1. Capture valid packet to extract discriminators:
   ```python
   from scapy.all import rdpcap
   import struct

   packets = rdpcap('/tmp/bfd_valid.pcap')
   valid_pkt = packets[0]
   bfd_payload = valid_pkt['Raw'].load

   my_disc = struct.unpack('!I', bfd_payload[4:8])[0]
   your_disc = struct.unpack('!I', bfd_payload[8:12])[0]

   print(f"Valid My Discriminator: {my_disc}")
   print(f"Valid Your Discriminator: {your_disc}")
   ```
2. Check current session counters:
   ```
   sonic# show bfd peers counters
   ```
3. Inject packet with wrong My Discriminator:
   ```python
   from scapy.all import IP, UDP, Raw, send
   import struct

   # Create packet with wrong My Discriminator
   bfd_pkt = bytearray(b'\xC0\x00\x03\x18')  # Version, State, Multiplier, Length
   bfd_pkt += struct.pack('!I', 99999)  # Wrong My Discriminator
   bfd_pkt += struct.pack('!I', your_disc)  # Correct Your Discriminator
   bfd_pkt += struct.pack('!I', 300000)  # TX interval (300ms in microseconds)
   bfd_pkt += struct.pack('!I', 300000)  # RX interval
   bfd_pkt += struct.pack('!I', 0)  # Echo RX interval

   pkt = IP(dst='10.1.1.2')/UDP(sport=3784, dport=3784)/Raw(load=bytes(bfd_pkt))
   send(pkt)
   ```
4. Wait 2 seconds
5. Check counter changes:
   ```
   sonic# show bfd peers counters
   ```
6. Verify session still Up with no change in Rx count

**Expected Result**:
- Packet discarded (not counted in Rx)
- Session remains Up
- Rx counter unchanged
- No session state change
- No error messages (expected behavior)

**Validation**:
- Rx packet count unchanged
- Session remains operational
- Discriminator validation working
- Malicious packets filtered

---

#### TC_BFD_TRAFFIC_010: BFD TTL/hop limit check

**Objective**: Verify correct IP TTL values in BFD packets

**Pre-requisites**:
- BFD sessions: single-hop (TTL=255) and multi-hop (TTL>1)

**Test Steps**:
1. Single-hop BFD session:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Capture single-hop packets:
   ```
   sonic# tcpdump -i Ethernet0 'udp port 3784' -w /tmp/bfd_ttl_single.pcap -c 5
   ```
3. Extract and verify TTL:
   ```python
   from scapy.all import rdpcap

   packets = rdpcap('/tmp/bfd_ttl_single.pcap')

   for pkt in packets:
       if pkt.haslayer('IP') and pkt.haslayer('UDP'):
           ttl = pkt['IP'].ttl
           dport = pkt['UDP'].dport

           if dport == 3784:
               print(f"Single-hop BFD packet TTL: {ttl}")
               assert ttl == 255, f"Expected TTL 255, got {ttl}"
   ```
4. Configure multi-hop BFD:
   ```
   sonic(config-bfd)# peer 10.2.2.2 multihop local-address 10.1.1.1
   ```
5. Capture multi-hop packets:
   ```
   sonic# tcpdump -i any 'udp port 4784' -w /tmp/bfd_ttl_multi.pcap -c 5
   ```
6. Extract and verify TTL for multi-hop:
   ```python
   packets_multi = rdpcap('/tmp/bfd_ttl_multi.pcap')

   for pkt in packets_multi:
       if pkt.haslayer('IP') and pkt.haslayer('UDP'):
           ttl = pkt['IP'].ttl
           dport = pkt['UDP'].dport

           if dport == 4784:
               print(f"Multi-hop BFD packet TTL: {ttl}")
               assert ttl > 1 and ttl <= 255, f"TTL {ttl} invalid for multi-hop"
   ```
7. Verify IPv6 Hop Limit for IPv6 BFD:
   ```python
   # For IPv6 sessions, check Hop Limit field
   # Single-hop IPv6 BFD: Hop Limit = 255
   # Multi-hop IPv6 BFD: Hop Limit <= 255
   ```

**Expected Result**:
- Single-hop TTL: exactly 255
- Multi-hop TTL: < 255 (typically 64 or configured value)
- IPv6 single-hop Hop Limit: 255
- IPv6 multi-hop Hop Limit: < 255
- TTL/Hop Limit consistent across all packets

**Validation**:
- Single-hop TTL: 255
- Multi-hop TTL: variable but < 255
- RFC 5881 compliance (TTL=255 for single-hop)
- Consistent across packets

**Cleanup**: Remove all tcpdump files after execution

### 2.7 BFD VRF Support
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_VRF_001 | BFD session in non-default VRF | Configure BFD in VRF instance | Session up in VRF |
| TC_BFD_VRF_002 | BFD with multiple VRFs | BFD sessions in different VRFs | Isolated BFD sessions |
| TC_BFD_VRF_003 | BFD VRF with static routes | Static route in VRF with BFD | Route tracked by BFD in VRF |
| TC_BFD_VRF_004 | BFD VRF with BGP | BGP in VRF with BFD | BFD tracks VRF BGP neighbor |

---

## 3. BFD Negative Tests

### 3.1 Configuration Errors

#### TC_BFD_NEG_001: Invalid transmit interval

**Objective**: Verify system rejects BFD transmit interval values outside valid range

**Pre-requisites**:
- Valid range: 10-60000 ms (check platform specifications)
- BFD globally enabled

**Test Steps**:
1. Configure BFD peer:
   ```
   sonic(config)# bfd
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Attempt to configure transmit interval below minimum (e.g., 5ms):
   ```
   sonic(config-bfd-peer)# transmit-interval 5
   ```
3. Verify error message is displayed
4. Verify configuration is not applied:
   ```
   sonic# show running-config bfd
   ```
5. Attempt to configure transmit interval above maximum (e.g., 70000ms):
   ```
   sonic(config-bfd-peer)# transmit-interval 70000
   ```
6. Verify error message is displayed
7. Test with invalid non-numeric values:
   ```
   sonic(config-bfd-peer)# transmit-interval abc
   ```

**Expected Result**:
- Error message: "Invalid value" or "Out of range"
- Configuration rejected
- No change to running-config
- CLI shows valid range in error message

**Validation**:
- Configuration remains unchanged
- Error logged in syslog
- Peer uses default or previously configured value

---

#### TC_BFD_NEG_002: Invalid receive interval

**Objective**: Verify system rejects BFD receive interval values outside valid range

**Pre-requisites**:
- Valid range: 10-60000 ms
- BFD peer configured

**Test Steps**:
1. Configure BFD peer:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Attempt receive interval below minimum:
   ```
   sonic(config-bfd-peer)# receive-interval 8
   ```
3. Verify error message and configuration rejection
4. Attempt receive interval above maximum:
   ```
   sonic(config-bfd-peer)# receive-interval 100000
   ```
5. Verify error message
6. Test with zero value:
   ```
   sonic(config-bfd-peer)# receive-interval 0
   ```
7. Test with negative value:
   ```
   sonic(config-bfd-peer)# receive-interval -100
   ```

**Expected Result**:
- All invalid values rejected
- Error messages displayed
- Running configuration unchanged
- System remains stable

**Validation**:
- No receive interval configured outside valid range
- Error messages appropriate for each invalid input

---

#### TC_BFD_NEG_003: Invalid detect multiplier

**Objective**: Verify system rejects BFD detect multiplier values outside valid range

**Pre-requisites**:
- Valid range: 3-50 (typical)
- BFD peer configured

**Test Steps**:
1. Configure BFD peer:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Attempt multiplier below minimum:
   ```
   sonic(config-bfd-peer)# detect-multiplier 1
   ```
3. Verify error: "Multiplier must be >= 3"
4. Attempt multiplier above maximum:
   ```
   sonic(config-bfd-peer)# detect-multiplier 100
   ```
5. Verify error message
6. Test with zero:
   ```
   sonic(config-bfd-peer)# detect-multiplier 0
   ```
7. Verify configuration using valid edge values:
   ```
   sonic(config-bfd-peer)# detect-multiplier 3
   sonic(config-bfd-peer)# detect-multiplier 50
   ```

**Expected Result**:
- Values < 3 rejected
- Values > 50 rejected
- Edge values (3, 50) accepted
- Configuration protected from invalid values

**Validation**:
- Multiplier remains within valid range
- Default used if no valid configuration

---

#### TC_BFD_NEG_004: Invalid peer IP address

**Objective**: Verify system rejects invalid IP address formats for BFD peer

**Pre-requisites**:
- BFD globally enabled

**Test Steps**:
1. Enter BFD configuration mode:
   ```
   sonic(config)# bfd
   ```
2. Attempt to configure peer with malformed IPv4:
   ```
   sonic(config-bfd)# peer 10.1.1.256 interface Ethernet0
   ```
3. Verify error: "Invalid IP address"
4. Attempt with invalid format:
   ```
   sonic(config-bfd)# peer 10.1.1 interface Ethernet0
   ```
5. Attempt with text instead of IP:
   ```
   sonic(config-bfd)# peer invalidip interface Ethernet0
   ```
6. Attempt with malformed IPv6:
   ```
   sonic(config-bfd)# peer 2001:db8::gggg interface Ethernet0
   ```
7. Verify running config shows no invalid peers:
   ```
   sonic# show running-config bfd
   ```

**Expected Result**:
- All invalid IP formats rejected
- Error messages clearly indicate "Invalid IP address"
- No peer configured with invalid IP
- Parser validates IP before accepting

**Validation**:
- Only valid IP addresses accepted
- Both IPv4 and IPv6 validation enforced

---

#### TC_BFD_NEG_005: Non-existent interface

**Objective**: Verify system rejects BFD configuration on non-existent interfaces

**Pre-requisites**:
- Know which interfaces do NOT exist (e.g., Ethernet999)

**Test Steps**:
1. List existing interfaces:
   ```
   sonic# show interface status
   ```
2. Attempt to configure BFD on non-existent interface:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet999
   ```
3. Verify error message: "Interface does not exist"
4. Attempt with wrong interface type:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface FakeInterface0
   ```
5. Verify configuration not applied:
   ```
   sonic# show bfd peers
   ```
6. Test with existing but down interface (should be allowed):
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet4
   ```
   (This should succeed even if interface is down)

**Expected Result**:
- Non-existent interfaces rejected with error
- Existing interfaces accepted (even if down)
- Clear error message indicating interface doesn't exist
- System validates interface existence

**Validation**:
- BFD only configured on valid interfaces
- Interface validation occurs before configuration

---

#### TC_BFD_NEG_006: Non-existent VRF

**Objective**: Verify system rejects BFD configuration in non-existent VRF

**Pre-requisites**:
- VRF support enabled
- Know which VRFs do NOT exist

**Test Steps**:
1. List existing VRFs:
   ```
   sonic# show vrf
   ```
2. Attempt BFD configuration in non-existent VRF:
   ```
   sonic(config-bfd)# peer 10.1.1.2 vrf NonExistentVrf interface Ethernet0
   ```
3. Verify error: "VRF does not exist"
4. Attempt with misspelled VRF name:
   ```
   sonic(config-bfd)# peer 10.1.1.2 vrf Vrf-Bluee interface Ethernet0
   ```
5. Verify configuration not applied
6. Create VRF and verify BFD can now be configured:
   ```
   sonic(config)# ip vrf TestVrf
   sonic(config-bfd)# peer 10.1.1.2 vrf TestVrf interface Ethernet0
   ```

**Expected Result**:
- Non-existent VRF rejected
- Error message: "VRF does not exist" or similar
- Configuration allowed after VRF created
- VRF validation enforced

**Validation**:
- BFD peers only in valid VRFs
- VRF existence checked before configuration

---

#### TC_BFD_NEG_007: Apply non-existent profile

**Objective**: Verify system rejects applying non-existent BFD profile to peer

**Pre-requisites**:
- BFD peer configured
- Profile "test-profile" does NOT exist

**Test Steps**:
1. List existing BFD profiles:
   ```
   sonic# show running-config bfd
   ```
2. Verify target profile doesn't exist
3. Attempt to apply non-existent profile to peer:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# profile non-existent-profile
   ```
4. Verify error message: "Profile does not exist"
5. Check peer configuration unchanged:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
6. Create profile and verify application succeeds:
   ```
   sonic(config-bfd)# profile test-profile
   sonic(config-bfd-profile)# transmit-interval 200
   sonic(config-bfd-profile)# exit
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# profile test-profile
   ```

**Expected Result**:
- Non-existent profile rejected
- Clear error message
- Peer configuration unchanged
- Profile application succeeds after profile creation

**Validation**:
- Profile existence validated before application
- Referential integrity maintained

---

#### TC_BFD_NEG_008: Delete profile in use

**Objective**: Verify system prevents or warns when deleting BFD profile that is in use

**Pre-requisites**:
- BFD profile "test-profile" created
- Profile applied to at least one peer

**Test Steps**:
1. Create and apply profile:
   ```
   sonic(config-bfd)# profile test-profile
   sonic(config-bfd-profile)# transmit-interval 100
   sonic(config-bfd-profile)# exit
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# profile test-profile
   sonic(config-bfd-peer)# exit
   ```
2. Verify profile is applied:
   ```
   sonic# show running-config bfd
   ```
3. Attempt to delete the profile while in use:
   ```
   sonic(config-bfd)# no profile test-profile
   ```
4. Verify system response (one of):
   - Error: "Profile in use, cannot delete"
   - Warning: "Profile in use by X peers"
   - Profile deleted and peers revert to defaults

**Expected Result**:
- System either:
  - Prevents deletion with error message, OR
  - Allows deletion with warning and reverts peers to defaults
- Behavior is predictable and documented
- No system instability

**Validation**:
- Profile deletion handling is graceful
- Peers remain operational
- Configuration consistency maintained

---

#### TC_BFD_NEG_009: Conflicting timer values

**Objective**: Verify system handles timer values that conflict with system minimums

**Pre-requisites**:
- Know platform minimum timer support

**Test Steps**:
1. Configure BFD with timer just at minimum:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 10
   sonic(config-bfd-peer)# receive-interval 10
   ```
2. Check if accepted or adjusted:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
3. Configure asymmetric timers:
   ```
   sonic(config-bfd-peer)# transmit-interval 50
   sonic(config-bfd-peer)# receive-interval 500
   ```
4. Verify session negotiates properly
5. Test extreme asymmetry:
   ```
   D1: transmit-interval 50, receive-interval 1000
   D2: transmit-interval 1000, receive-interval 50
   ```
6. Verify negotiation and session establishment

**Expected Result**:
- System accepts minimum supported values
- Values below minimum either rejected or adjusted with warning
- Asymmetric timers handled via negotiation
- Session establishes with negotiated values

**Validation**:
- Timer negotiation follows BFD RFC
- System protects against unsupported values
- Clear indication of actual values in use

### 3.2 Session Failures

#### TC_BFD_NEG_010: BFD session with unreachable peer

**Objective**: Verify BFD session remains Down when peer is unreachable

**Pre-requisites**:
- D1 configured and operational
- IP address 10.99.99.99 is NOT reachable from D1

**Test Steps**:
1. Verify IP 10.99.99.99 is unreachable:
   ```
   sonic# ping 10.99.99.99 count 5
   ```
2. Configure BFD to unreachable peer:
   ```
   sonic(config-bfd)# peer 10.99.99.99 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 300
   sonic(config-bfd-peer)# receive-interval 300
   ```
3. Verify BFD session state:
   ```
   sonic# show bfd peer 10.99.99.99
   ```
4. Wait 30 seconds
5. Verify session still Down:
   ```
   sonic# show bfd peers
   ```
6. Check BFD counters:
   ```
   sonic# show bfd peers counters
   ```
7. Verify system stability (no crashes, no high CPU)

**Expected Result**:
- BFD session remains in Down state
- Control Tx counter increments (packets sent)
- Control Rx counter stays 0 (no packets received)
- System remains stable
- No error messages or crashes

**Validation**:
- Session State: Down
- Control Tx > 0
- Control Rx = 0
- System CPU and memory normal

---

#### TC_BFD_NEG_011: BFD one-way communication

**Objective**: Verify BFD session fails with one-way communication

**Pre-requisites**:
- D1 and D2 connected and BFD session Up
- Ability to filter packets using ACL or iptables

**Test Steps**:
1. Establish BFD session between D1 and D2:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
   Verify State: Up
2. On D2, block inbound BFD packets using ACL:
   ```
   sonic(config)# ip access-list BFD-BLOCK
   sonic(config-acl)# deny udp any any eq 3784
   sonic(config-acl)# permit ip any any
   sonic(config)# interface Ethernet0
   sonic(config-if)# ip access-group BFD-BLOCK in
   ```
3. Monitor BFD session on D1:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
4. Wait for detection time (rx_interval × multiplier)
5. Verify session goes Down on D1:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
6. Check diagnostic code indicates timeout
7. Remove ACL and verify session recovery:
   ```
   sonic(config-if)# no ip access-group BFD-BLOCK in
   ```

**Expected Result**:
- BFD session transitions from Up to Down
- Detection occurs within configured detection time
- Diagnostic code indicates "Control Detection Time Expired"
- Session recovers after removing block

**Validation**:
- Session goes Down when packets blocked
- Timeout detection works correctly
- Session recovers when communication restored

---

#### TC_BFD_NEG_012: BFD mismatched parameters

**Objective**: Verify BFD handles mismatched timer parameters between peers

**Pre-requisites**:
- D1 and D2 connected

**Test Steps**:
1. Configure D1 with fast timers:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 100
   sonic(config-bfd-peer)# receive-interval 100
   sonic(config-bfd-peer)# detect-multiplier 3
   ```
2. Configure D2 with slow timers:
   ```
   sonic(config-bfd)# peer 10.1.1.1 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 1000
   sonic(config-bfd-peer)# receive-interval 1000
   sonic(config-bfd-peer)# detect-multiplier 5
   ```
3. Wait for session establishment
4. Verify session comes Up:
   ```
   sonic# show bfd peers
   ```
5. Check negotiated parameters:
   ```
   D1: sonic# show bfd peer 10.1.1.2
   D2: sonic# show bfd peer 10.1.1.1
   ```
6. Verify packet timing matches negotiated values
7. Test with very different multipliers (3 vs 50)

**Expected Result**:
- Session establishes despite parameter mismatch
- System negotiates compatible values per BFD RFC
- Session uses slowest of the configured values
- Both sides agree on final parameters

**Validation**:
- Session State: Up
- Negotiated values = max(D1_rx, D2_tx) and max(D2_rx, D1_tx)
- Session stable with asymmetric configuration

---

#### TC_BFD_NEG_013: Interface flapping

**Objective**: Verify BFD correctly tracks rapid interface state changes

**Pre-requisites**:
- BFD session established between D1 and D2
- Ability to toggle interface administratively

**Test Steps**:
1. Establish BFD session and verify Up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
2. Rapidly shutdown/no-shutdown interface on D1:
   ```
   sonic(config)# interface Ethernet0
   sonic(config-if)# shutdown
   ```
   Wait 2 seconds
   ```
   sonic(config-if)# no shutdown
   ```
3. Repeat flap 5 times with 2-3 second intervals
4. Monitor BFD state during flaps:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Check logs for state transitions:
   ```
   sonic# show logging | include BFD
   ```
6. Verify final state after flapping stops
7. Check system stability (CPU, memory)

**Expected Result**:
- BFD session tracks each interface state change
- Session goes Down when interface down
- Session re-establishes when interface up
- Multiple rapid transitions handled gracefully
- System remains stable
- All state changes logged

**Validation**:
- BFD state follows interface state
- No missed transitions
- System stable throughout
- Final state: Up (after interface stabilizes)

---

#### TC_BFD_NEG_014: BFD session timeout

**Objective**: Verify BFD detects session timeout when packets stop arriving

**Pre-requisites**:
- BFD session Up between D1 and D2
- Known timer configuration (e.g., rx=300ms, multiplier=3)

**Test Steps**:
1. Verify BFD session Up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
2. Record detection time: rx_interval × multiplier (e.g., 300ms × 3 = 900ms)
3. On D2, shutdown BFD peer (stops sending packets):
   ```
   sonic(config-bfd)# peer 10.1.1.1 interface Ethernet0
   sonic(config-bfd-peer)# shutdown
   ```
4. On D1, capture timestamp and monitor session:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Note time when session transitions to Down
6. Verify detection time is within expected range:
   - Should be approximately: rx_interval × multiplier
   - Allowed variance: ±10%
7. Check diagnostic code:
   ```
   sonic# show bfd peer 10.1.1.2 | include Diagnostic
   ```

**Expected Result**:
- D1 detects timeout within detection time window
- Session transitions from Up to Down
- Detection time = rx_interval × multiplier (±10%)
- Diagnostic code: "Control Detection Time Expired" or "Neighbor Signaled Session Down"

**Validation**:
- Timeout detection works correctly
- Detection time within expected bounds
- Appropriate diagnostic code set

---

#### TC_BFD_NEG_015: BFD with disabled peer

**Objective**: Verify BFD session shows AdminDown when peer is shutdown

**Pre-requisites**:
- BFD session configured on both D1 and D2

**Test Steps**:
1. Establish BFD session:
   ```
   D1: sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   D2: sonic(config-bfd)# peer 10.1.1.1 interface Ethernet0
   ```
2. Verify session Up
3. On D1, shutdown BFD peer:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# shutdown
   ```
4. Verify D1 shows AdminDown:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
5. Verify D2 receives AdminDown notification:
   ```
   sonic# show bfd peer 10.1.1.1
   ```
6. Check that D2 state reflects peer AdminDown
7. Verify D1 sends packets with State=AdminDown
8. Verify no timeout occurs (immediate notification)

**Expected Result**:
- D1 immediately shows State: AdminDown
- D1 sends BFD packets with State field = AdminDown
- D2 receives AdminDown and reflects it (Down or AdminDown)
- Fast convergence (< 1 second, no timeout wait)
- Diagnostic code indicates admin down

**Validation**:
- D1 State: AdminDown
- D2 receives notification immediately
- No timeout period required
- Session properly communicates shutdown state

### 3.3 Error Handling

#### TC_BFD_NEG_016: BFD with interface down

**Objective**: Verify BFD session behavior when configured on a down interface

**Pre-requisites**:
- D1 and D2 connected via Ethernet0
- Ethernet0 currently in shutdown state

**Test Steps**:
1. Shutdown interface on both sides:
   ```
   sonic(config)# interface Ethernet0
   sonic(config-if)# shutdown
   ```
2. Configure IP addresses:
   ```
   sonic(config-if)# ip address 10.1.1.1/24
   ```
3. Configure BFD while interface is down:
   ```
   sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 300
   sonic(config-bfd-peer)# receive-interval 300
   ```
4. Verify configuration accepted:
   ```
   sonic# show running-config bfd
   ```
5. Check BFD session state (should be Down):
   ```
   sonic# show bfd peer 10.1.1.2
   ```
6. Bring interface up on both sides:
   ```
   sonic(config)# interface Ethernet0
   sonic(config-if)# no shutdown
   ```
7. Wait for interface to come up
8. Verify BFD session transitions to Up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```

**Expected Result**:
- BFD configuration accepted on down interface
- BFD session state: Down while interface down
- Session automatically transitions to Up when interface comes up
- No manual intervention required for session establishment

**Validation**:
- Configuration successful on down interface
- Session Down initially
- Session Up after interface brought up
- Automatic state tracking

---

#### TC_BFD_NEG_017: BFD peer IP not configured

**Objective**: Verify BFD session fails when peer IP is not reachable/configured

**Pre-requisites**:
- D1 Ethernet0: 10.1.1.1/24
- D2 Ethernet0: 10.1.1.2/24
- Both interfaces up

**Test Steps**:
1. On D1, configure BFD to peer IP not configured on D2:
   ```
   sonic(config-bfd)# peer 10.1.1.99 interface Ethernet0
   sonic(config-bfd-peer)# transmit-interval 300
   sonic(config-bfd-peer)# receive-interval 300
   ```
2. Verify configuration accepted:
   ```
   sonic# show running-config bfd
   ```
3. Check BFD session state:
   ```
   sonic# show bfd peer 10.1.1.99
   ```
4. Wait 30 seconds
5. Verify session remains Down
6. Check ARP table:
   ```
   sonic# show arp | include 10.1.1.99
   ```
7. On D2, configure the IP address:
   ```
   sonic(config)# interface Ethernet0
   sonic(config-if)# ip address 10.1.1.99/24 secondary
   ```
8. Configure matching BFD on D2
9. Verify session now establishes

**Expected Result**:
- BFD configuration allowed even if peer unreachable
- Session remains Down without configured peer
- ARP resolution may fail for unreachable peer
- Session establishes once peer properly configured

**Validation**:
- Session Down initially
- No crashes or errors
- Session Up after proper peer configuration

---

#### TC_BFD_NEG_018: Remove interface with BFD

**Objective**: Verify BFD session handling when interface is removed

**Pre-requisites**:
- BFD session Up on VLAN interface (easier to delete than physical)
- VLAN100 with IP 10.100.100.1/24
- BFD peer 10.100.100.2 configured

**Test Steps**:
1. Verify BFD session Up on Vlan100:
   ```
   sonic# show bfd peer 10.100.100.2
   ```
2. Verify VLAN interface exists:
   ```
   sonic# show interface Vlan 100
   ```
3. Delete the VLAN interface:
   ```
   sonic(config)# no interface Vlan 100
   ```
4. Check BFD session status:
   ```
   sonic# show bfd peers
   ```
5. Verify BFD configuration:
   ```
   sonic# show running-config bfd
   ```
6. Check for error messages or system logs:
   ```
   sonic# show logging | include BFD
   ```
7. Attempt to recreate interface:
   ```
   sonic(config)# interface Vlan 100
   sonic(config-if)# ip address 10.100.100.1/24
   ```
8. Check if BFD session automatically restores

**Expected Result**:
- Interface deletion should either:
  - Automatically remove BFD peer configuration, OR
  - Keep BFD configuration but session goes Down
- No system crash or instability
- BFD handles gracefully with appropriate logging
- Clear indication of configuration/session state

**Validation**:
- System remains stable
- BFD session removed or moved to Down
- Appropriate log messages
- Configuration consistency maintained

---

#### TC_BFD_NEG_019: Change interface IP with BFD

**Objective**: Verify BFD session behavior when interface IP address changes

**Pre-requisites**:
- BFD session Up between D1 (10.1.1.1) and D2 (10.1.1.2)

**Test Steps**:
1. Verify BFD session Up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
2. On D1, change interface IP address:
   ```
   sonic(config)# interface Ethernet0
   sonic(config-if)# no ip address 10.1.1.1/24
   sonic(config-if)# ip address 10.1.1.10/24
   ```
3. Monitor BFD session:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
4. Verify session goes Down (source IP changed)
5. Check BFD configuration:
   ```
   sonic# show running-config bfd
   ```
6. Update BFD peer IP on D2:
   ```
   sonic(config-bfd)# peer 10.1.1.10 interface Ethernet0
   ```
7. Change D2 IP to match subnet:
   ```
   sonic(config-if)# no ip address 10.1.1.2/24
   sonic(config-if)# ip address 10.1.1.20/24
   ```
8. Reconfigure BFD peers with new IPs
9. Verify session re-establishes

**Expected Result**:
- BFD session goes Down when IP changes
- Source/destination IP mismatch prevents session
- Session re-establishes after proper reconfiguration
- System handles IP changes gracefully

**Validation**:
- Session Down after IP change
- No system instability
- Session Up after proper reconfiguration
- Local IP in packets matches configured interface IP

---

#### TC_BFD_NEG_020: BFD session limit exceeded

**Objective**: Verify system behavior when attempting to exceed maximum BFD sessions

**Pre-requisites**:
- Know platform maximum BFD session limit (e.g., 128, 256, 512)
- Sufficient interfaces or loopback addresses for testing

**Test Steps**:
1. Query or document platform BFD session limit:
   ```
   sonic# show platform capabilities | include BFD
   ```
2. Configure BFD sessions up to the limit:
   ```
   # Loop to create sessions 1 through MAX
   for i in 1 to MAX:
       sonic(config-bfd)# peer 10.10.{subnet}.{host} interface Ethernet{N}
   ```
3. Verify all sessions configured:
   ```
   sonic# show bfd peers | count
   ```
4. Attempt to configure one more session beyond limit:
   ```
   sonic(config-bfd)# peer 10.99.99.99 interface Ethernet0
   ```
5. Verify system response:
   - Error message: "Maximum BFD sessions reached", OR
   - Configuration accepted but session doesn't establish, OR
   - Oldest session replaced (implementation-specific)
6. Check system stability:
   ```
   sonic# show processes cpu
   sonic# show memory
   ```
7. Remove one session and verify new session can be added

**Expected Result**:
- System clearly indicates or enforces session limit
- Error message if limit exceeded
- No system crash or instability
- Existing sessions remain operational
- Clear documentation of limit behavior

**Validation**:
- Session count ≤ maximum limit
- Appropriate error handling
- System remains stable
- Existing sessions unaffected

**Note**: If platform limit is very high (>256), test with a subset and verify error handling mechanism

---

## 4. BFD Scaling Tests

### 4.1 Session Scaling

#### TC_BFD_SCALE_001: 10 BFD sessions

**Objective**: Verify system can handle 10 concurrent BFD sessions

**Pre-requisites**:
- D1 and D2 connected
- Multiple IP addresses configured or loopback interfaces available
- Sufficient interfaces for 10 sessions

**Test Steps**:
1. Configure 10 loopback interfaces on D1:
   ```
   for i in 1 to 10:
       sonic(config)# interface Loopback{i}
       sonic(config-if)# ip address 10.10.{i}.1/32
   ```
2. Configure corresponding loopbacks on D2:
   ```
   for i in 1 to 10:
       sonic(config)# interface Loopback{i}
       sonic(config-if)# ip address 10.10.{i}.2/32
   ```
3. Configure static routes for reachability
4. Configure 10 BFD sessions on D1:
   ```
   for i in 1 to 10:
       sonic(config-bfd)# peer 10.10.{i}.2 multihop local-address 10.10.{i}.1
       sonic(config-bfd-peer)# transmit-interval 300
       sonic(config-bfd-peer)# receive-interval 300
   ```
5. Configure matching sessions on D2
6. Wait for all sessions to establish (30 seconds)
7. Verify all 10 sessions are Up:
   ```
   sonic# show bfd peers | count
   sonic# show bfd peers
   ```
8. Check system resources:
   ```
   sonic# show processes cpu
   sonic# show memory
   ```
9. Verify BFD counters for all sessions:
   ```
   sonic# show bfd peers counters
   ```

**Expected Result**:
- All 10 sessions establish successfully
- Session count: 10
- All sessions state: Up
- CPU utilization acceptable (<20%)
- Memory usage normal
- Packet counters incrementing for all sessions

**Validation**:
- `show bfd peers | count` returns 10
- All sessions show Status: Up
- Control Tx/Rx > 0 for all sessions
- System stable and responsive

---

#### TC_BFD_SCALE_002: 50 BFD sessions

**Objective**: Verify system can handle 50 concurrent BFD sessions

**Pre-requisites**:
- D1 and D2 connected
- Sufficient IP addressing (50 loopbacks or secondary IPs)

**Test Steps**:
1. Use automation script to configure 50 loopback interfaces:
   ```python
   # Via spytest automation
   for i in range(1, 51):
       ip_api.config_loopback(dut, f"Loopback{i}", f"10.10.{i}.1/32")
   ```
2. Configure 50 BFD sessions programmatically:
   ```python
   for i in range(1, 51):
       bfd_api.config_bfd_peer(dut, f"10.10.{i}.2",
                               local_addr=f"10.10.{i}.1",
                               multihop=True,
                               tx_interval=300, rx_interval=300)
   ```
3. Monitor session establishment progress:
   ```
   watch -n 5 'show bfd peers brief'
   ```
4. Wait for all sessions (up to 2 minutes)
5. Verify session count:
   ```
   sonic# show bfd peers | include "Total Sessions"
   ```
6. Sample check 10 random sessions for Up state
7. Monitor system performance:
   ```
   sonic# show processes cpu
   sonic# show memory
   sonic# show interface counters rate
   ```
8. Leave running for 5 minutes to verify stability

**Expected Result**:
- All 50 sessions establish successfully
- Total time to establish: < 2 minutes
- All sessions remain stable
- CPU utilization < 40%
- Memory increase proportional to session count
- No packet loss or session flapping

**Validation**:
- Session count: 50
- All sampled sessions: Up
- System CPU/memory within acceptable limits
- No error messages in logs

---

#### TC_BFD_SCALE_003: 100 BFD sessions

**Objective**: Verify system can handle 100 concurrent BFD sessions

**Pre-requisites**:
- Extended topology or use of secondary IPs
- D1 and D2 with capacity for 100 sessions

**Test Steps**:
1. Configure 100 loopback interfaces on both D1 and D2
2. Configure routing for all loopbacks (redistribute connected or static routes)
3. Use automation to configure 100 BFD sessions:
   ```python
   for i in range(1, 101):
       subnet = (i - 1) // 254 + 1
       host = i % 254 or 254
       local_ip = f"10.{subnet}.{host}.1"
       peer_ip = f"10.{subnet}.{host}.2"
       bfd_api.config_bfd_peer(dut, peer_ip, local_addr=local_ip,
                               multihop=True, tx_interval=300, rx_interval=300)
   ```
4. Monitor establishment:
   ```
   # Check every 10 seconds
   while not all_sessions_up():
       count = get_up_session_count()
       print(f"Sessions Up: {count}/100")
       time.sleep(10)
   ```
5. Verify all 100 sessions established:
   ```
   sonic# show bfd peers brief | include "Total Sessions"
   ```
6. Performance monitoring for 10 minutes:
   - CPU utilization
   - Memory usage
   - BFD process memory/CPU
   - Packet rate on interfaces
7. Randomly select 20 sessions and verify details:
   ```
   for session in random_sample(20):
       show bfd peer {session}
   ```

**Expected Result**:
- All 100 sessions establish successfully
- Establishment time: < 5 minutes
- CPU utilization < 60%
- Memory usage < 500MB increase from baseline
- All sessions stable for duration of test
- No session flapping or timeouts

**Validation**:
- `show bfd peers brief` shows 100 total sessions
- Sample verification: 20/20 sessions Up
- System performance acceptable
- No errors in syslog

---

#### TC_BFD_SCALE_004: Maximum BFD sessions

**Objective**: Verify system can handle maximum platform-supported BFD sessions

**Pre-requisites**:
- Know platform maximum (e.g., 256, 512, 1024)
- Sufficient IP addressing scheme
- Extended test time allocation

**Test Steps**:
1. Determine platform maximum:
   ```
   sonic# show platform capabilities | include BFD
   # Or reference platform documentation
   MAX_SESSIONS = 256  # example
   ```
2. Create automation script for MAX_SESSIONS:
   ```python
   MAX = get_platform_bfd_limit(dut)
   log.info(f"Platform supports {MAX} BFD sessions")

   for i in range(1, MAX + 1):
       configure_bfd_session(dut, session_id=i)
   ```
3. Configure sessions in batches of 50 to monitor progress:
   ```python
   for batch in range(0, MAX, 50):
       configure_batch(start=batch, count=50)
       wait_for_sessions_up(timeout=120)
       verify_batch_established()
   ```
4. Monitor system during configuration:
   - CPU percentage
   - Memory usage
   - BFD daemon process stats
5. Verify all sessions established:
   ```
   session_count = get_bfd_session_count(dut)
   assert session_count == MAX
   ```
6. Stability test - run for 1 hour:
   - Monitor for session flaps
   - Check packet loss
   - Verify no timeouts
7. Stress test - flap one interface and verify recovery
8. Collect performance metrics:
   ```
   sonic# show processes top
   sonic# show bfd peers counters
   ```

**Expected Result**:
- System accepts MAX_SESSIONS configuration
- All sessions establish successfully
- Establishment time: < 10 minutes for 256 sessions
- CPU utilization < 80% during steady state
- Memory usage within system limits
- All sessions stable for test duration
- System responsive to CLI commands

**Validation**:
- Session count matches platform maximum
- All sessions in Up state
- No memory exhaustion
- No CPU starvation
- System remains manageable

---

#### TC_BFD_SCALE_005: Mixed IPv4/IPv6 sessions

**Objective**: Verify system handles mixed IPv4 and IPv6 BFD sessions

**Pre-requisites**:
- IPv4 and IPv6 addressing configured
- D1 and D2 dual-stack capable

**Test Steps**:
1. Configure 50 loopback interfaces with dual-stack:
   ```
   for i in 1 to 50:
       sonic(config)# interface Loopback{i}
       sonic(config-if)# ip address 10.10.{i}.1/32
       sonic(config-if)# ipv6 address 2001:db8:{i}::1/128
   ```
2. Configure 25 IPv4 BFD sessions:
   ```python
   for i in range(1, 26):
       bfd_api.config_bfd_peer(dut, f"10.10.{i}.2",
                               local_addr=f"10.10.{i}.1",
                               multihop=True)
   ```
3. Configure 25 IPv6 BFD sessions:
   ```python
   for i in range(26, 51):
       bfd_api.config_bfd_peer(dut, f"2001:db8:{i}::2",
                               local_addr=f"2001:db8:{i}::1",
                               multihop=True)
   ```
4. Verify mixed session establishment:
   ```
   sonic# show bfd peers | include IPv4
   sonic# show bfd peers | include IPv6
   ```
5. Count each type:
   ```
   ipv4_count = count_bfd_sessions(dut, family='ipv4')
   ipv6_count = count_bfd_sessions(dut, family='ipv6')
   ```
6. Verify session details for both types:
   ```
   sonic# show bfd peer 10.10.5.2
   sonic# show bfd peer 2001:db8:30::2
   ```
7. Capture traffic to verify both IPv4 and IPv6 BFD packets:
   ```
   tcpdump -i any 'udp port 3784 or udp port 4784' -c 100
   ```
8. Monitor system resources

**Expected Result**:
- 25 IPv4 sessions establish successfully
- 25 IPv6 sessions establish successfully
- Total: 50 sessions, all Up
- Both IPv4 and IPv6 packets observed in capture
- Even resource utilization across both types
- No preference or bias toward either family

**Validation**:
- IPv4 session count: 25
- IPv6 session count: 25
- All sessions Up
- Packet capture shows both IPv4 and IPv6 BFD packets

---

#### TC_BFD_SCALE_006: BFD sessions across VRFs

**Objective**: Verify BFD sessions can be distributed across multiple VRFs

**Pre-requisites**:
- VRF support enabled
- 4 VRFs configured (Vrf-Red, Vrf-Blue, Vrf-Green, Vrf-Yellow)
- Each VRF has dedicated interfaces

**Test Steps**:
1. Create 4 VRFs on D1 and D2:
   ```
   sonic(config)# ip vrf Vrf-Red
   sonic(config)# ip vrf Vrf-Blue
   sonic(config)# ip vrf Vrf-Green
   sonic(config)# ip vrf Vrf-Yellow
   ```
2. Assign interfaces to VRFs:
   ```
   sonic(config)# interface Ethernet4
   sonic(config-if)# ip vrf forwarding Vrf-Red
   sonic(config-if)# ip address 192.168.1.1/24

   # Repeat for other VRFs with different interfaces
   ```
3. Configure 10 BFD sessions in each VRF (40 total):
   ```python
   vrfs = ['Vrf-Red', 'Vrf-Blue', 'Vrf-Green', 'Vrf-Yellow']
   for vrf in vrfs:
       for i in range(1, 11):
           peer_ip = f"192.168.{vrfs.index(vrf)+1}.{i+1}"
           bfd_api.config_bfd_peer(dut, peer_ip, vrf=vrf, interface=get_vrf_interface(vrf))
   ```
4. Verify sessions per VRF:
   ```
   for vrf in ['Vrf-Red', 'Vrf-Blue', 'Vrf-Green', 'Vrf-Yellow']:
       sonic# show bfd peers vrf {vrf}
   ```
5. Count sessions in each VRF:
   ```python
   for vrf in vrfs:
       count = count_bfd_sessions(dut, vrf=vrf)
       assert count == 10, f"VRF {vrf} has {count} sessions, expected 10"
   ```
6. Verify VRF isolation:
   - Sessions in Vrf-Red should not appear in Vrf-Blue, etc.
7. Verify total session count:
   ```
   sonic# show bfd peers | include "Total Sessions: 40"
   ```
8. Test VRF-specific operations:
   - Shutdown all sessions in one VRF
   - Verify other VRFs unaffected

**Expected Result**:
- 40 total sessions established (10 per VRF)
- VRF isolation maintained
- Sessions properly segregated by VRF
- No cross-VRF interference
- Independent VRF operations work correctly

**Validation**:
- Each VRF shows exactly 10 sessions
- Total sessions: 40
- VRF isolation verified
- All sessions Up

---

### 4.2 Performance Scaling

#### TC_BFD_SCALE_007: All sessions with fast timers

**Objective**: Verify system can handle maximum sessions with aggressive (fast) timers

**Pre-requisites**:
- Platform maximum sessions known (e.g., 128)
- Baseline CPU/memory metrics collected

**Test Steps**:
1. Configure maximum supported sessions
2. Set all sessions to fast timers (50ms):
   ```python
   for i in range(1, MAX_SESSIONS + 1):
       bfd_api.config_bfd_peer(dut, get_peer_ip(i),
                               local_addr=get_local_ip(i),
                               tx_interval=50,
                               rx_interval=50,
                               multiplier=3)
   ```
3. Monitor system during establishment:
   ```
   # Baseline before BFD
   baseline_cpu = get_cpu_usage(dut)
   baseline_mem = get_memory_usage(dut)
   ```
4. Wait for all sessions to establish
5. Monitor performance metrics:
   ```
   sonic# show processes cpu | include bfd
   sonic# show processes memory | include bfd
   ```
6. Calculate packet rate:
   - Expected: 20 packets/sec per session × MAX_SESSIONS
   - For 128 sessions: 2,560 packets/sec total
7. Monitor for 30 minutes:
   - CPU usage every minute
   - Memory usage every minute
   - Check for session flaps
   - Verify packet counters continuously increment
8. Record performance data:
   ```python
   metrics = {
       'cpu_avg': average_cpu_over_30min,
       'cpu_max': max_cpu_over_30min,
       'mem_usage': memory_increase,
       'session_flaps': count_session_flaps(),
       'packet_loss': calculate_packet_loss()
   }
   ```

**Expected Result**:
- All sessions establish with 50ms timers
- CPU utilization < 70% average
- CPU spikes < 90% max
- Memory increase < 1GB
- No session flaps
- Packet loss < 0.1%
- System remains responsive
- CLI commands execute within 2 seconds

**Validation**:
- All sessions Up with 50ms tx/rx
- CPU within acceptable limits
- No memory leak over 30 minutes
- Packet rate matches expected (±5%)
- System stable and responsive

---

#### TC_BFD_SCALE_008: BFD session flap test

**Objective**: Verify system handles repeated session flapping at scale

**Pre-requisites**:
- 50 BFD sessions configured and Up

**Test Steps**:
1. Establish 50 BFD sessions:
   ```python
   for i in range(1, 51):
       configure_bfd_session(dut, session_id=i)
   verify_all_sessions_up(dut, expected_count=50)
   ```
2. Start monitoring:
   ```python
   start_continuous_monitoring(metrics=['cpu', 'memory', 'session_count'])
   ```
3. Flap sessions in groups of 10:
   ```python
   for cycle in range(1, 11):  # 10 cycles
       log.info(f"Flap cycle {cycle}/10")

       # Shutdown 10 sessions
       for i in range(1, 11):
           bfd_api.shutdown_bfd_peer(dut, get_peer_ip(i))

       time.sleep(5)
       verify_sessions_down(dut, count=10)

       # Re-enable 10 sessions
       for i in range(1, 11):
           bfd_api.no_shutdown_bfd_peer(dut, get_peer_ip(i))

       time.sleep(5)
       verify_sessions_up(dut, count=10)

       # Move to next group
       rotate_group()
   ```
4. After flapping, verify all 50 sessions return to Up:
   ```
   final_count = count_sessions_up(dut)
   assert final_count == 50
   ```
5. Check for errors:
   ```
   sonic# show logging | include BFD | include ERROR
   ```
6. Verify system stability:
   ```
   sonic# show processes cpu
   sonic# show memory
   ```
7. Check for memory leaks:
   ```python
   memory_before = baseline_memory
   memory_after = get_memory_usage(dut)
   memory_increase = memory_after - memory_before
   assert memory_increase < 50MB  # Acceptable leak threshold
   ```

**Expected Result**:
- All sessions successfully flap 10 times each
- Sessions transition: Up → AdminDown → Up correctly
- No sessions stuck in Down state
- No memory leaks detected
- CPU returns to normal after flapping
- System stable throughout test
- No crashes or daemon restarts

**Validation**:
- All 50 sessions Up at end of test
- Total flaps: 500 (50 sessions × 10 cycles)
- No unexpected session state
- Memory increase < 50MB
- No errors in syslog

---

#### TC_BFD_SCALE_009: Bulk session addition

**Objective**: Verify system handles simultaneous addition of many BFD sessions

**Pre-requisites**:
- No BFD sessions currently configured
- Configuration file prepared with 100 BFD sessions

**Test Steps**:
1. Prepare configuration file with 100 BFD sessions:
   ```python
   config_lines = []
   for i in range(1, 101):
       config_lines.extend([
           f"bfd",
           f"peer {get_peer_ip(i)} interface {get_interface(i)}",
           f"transmit-interval 300",
           f"receive-interval 300",
           f"detect-multiplier 3",
           f"exit"
       ])
   write_config_file(config_lines)
   ```
2. Record baseline metrics:
   ```python
   baseline_cpu = get_cpu_usage(dut)
   baseline_memory = get_memory_usage(dut)
   start_time = time.time()
   ```
3. Apply configuration in bulk:
   ```python
   st.config(dut, config_lines, type='klish')
   # OR
   load_config_from_file(dut, 'bfd_100_sessions.conf')
   ```
4. Monitor session establishment:
   ```python
   while not all_sessions_up(dut, expected=100, timeout=300):
       current_up = count_sessions_up(dut)
       elapsed = time.time() - start_time
       log.info(f"Sessions Up: {current_up}/100 (Elapsed: {elapsed}s)")
       time.sleep(5)
   ```
5. Record establishment time:
   ```python
   total_time = time.time() - start_time
   log.info(f"All 100 sessions established in {total_time} seconds")
   ```
6. Verify all sessions operational:
   ```
   sonic# show bfd peers brief
   ```
7. Check system impact:
   ```python
   peak_cpu = max_cpu_during_establishment
   peak_memory = max_memory_during_establishment
   ```
8. Verify no errors during bulk add:
   ```
   sonic# show logging | include BFD | include -i error
   ```

**Expected Result**:
- All 100 sessions configured successfully
- Total establishment time < 5 minutes
- Sessions come up in parallel (not sequentially)
- CPU spike < 90% during establishment
- CPU returns to normal after establishment
- No configuration errors
- All sessions reach Up state
- System remains responsive during process

**Validation**:
- Final session count: 100
- All sessions Up
- Establishment time < 300 seconds
- No errors in configuration
- System stable after bulk addition

---

#### TC_BFD_SCALE_010: Bulk session removal

**Objective**: Verify system handles simultaneous removal of many BFD sessions

**Pre-requisites**:
- 100 BFD sessions configured and Up

**Test Steps**:
1. Verify starting state:
   ```python
   initial_count = count_bfd_sessions(dut)
   assert initial_count == 100
   verify_all_sessions_up(dut)
   ```
2. Record baseline:
   ```python
   baseline_cpu = get_cpu_usage(dut)
   baseline_memory = get_memory_usage(dut)
   start_time = time.time()
   ```
3. Remove all sessions in bulk:
   ```python
   removal_commands = []
   for i in range(1, 101):
       removal_commands.extend([
           "bfd",
           f"no peer {get_peer_ip(i)} interface {get_interface(i)}"
       ])

   st.config(dut, removal_commands, type='klish')
   ```
4. Monitor removal process:
   ```python
   while count_bfd_sessions(dut) > 0:
       remaining = count_bfd_sessions(dut)
       elapsed = time.time() - start_time
       log.info(f"Sessions remaining: {remaining}/100 (Elapsed: {elapsed}s)")
       time.sleep(1)
   ```
5. Record removal time:
   ```python
   total_time = time.time() - start_time
   log.info(f"All 100 sessions removed in {total_time} seconds")
   ```
6. Verify complete removal:
   ```
   sonic# show bfd peers
   # Should show no sessions or "No BFD peers configured"
   ```
7. Check memory reclamation:
   ```python
   time.sleep(30)  # Allow garbage collection
   final_memory = get_memory_usage(dut)
   memory_reclaimed = baseline_memory - final_memory
   log.info(f"Memory reclaimed: {memory_reclaimed}MB")
   ```
8. Verify clean state:
   ```
   sonic# show running-config bfd
   # Should show minimal/no BFD configuration
   ```

**Expected Result**:
- All 100 sessions removed successfully
- Removal time < 2 minutes
- Memory properly reclaimed (>90% of BFD memory freed)
- No orphaned sessions
- No configuration remnants
- System CPU returns to baseline
- No daemon crashes or restarts
- Clean BFD state after removal

**Validation**:
- Final session count: 0
- Running config clean
- Memory returned to near baseline
- No BFD processes consuming resources
- System stable

---

#### TC_BFD_SCALE_011: BFD with route scale

**Objective**: Verify BFD session handling with large number of tracked routes

**Pre-requisites**:
- BFD session capable of tracking multiple routes
- Ability to configure 1000+ static routes

**Test Steps**:
1. Configure single BFD session between D1 and D2:
   ```
   D1: sonic(config-bfd)# peer 10.1.1.2 interface Ethernet0
   ```
2. Verify BFD session Up:
   ```
   sonic# show bfd peer 10.1.1.2
   ```
3. Configure 1000 static routes tracking this BFD session:
   ```python
   for i in range(1, 1001):
       subnet = i // 254 + 1
       host = i % 254 or 254
       route = f"100.{subnet}.{host}.0/24"
       st.config(dut, f"ip route {route} 10.1.1.2 track bfd", type='klish')

       if i % 100 == 0:
           log.info(f"Configured {i}/1000 routes")
   ```
4. Verify all routes installed:
   ```
   route_count = count_routes_tracking_bfd(dut)
   assert route_count == 1000
   ```
5. Verify routes are active (BFD Up):
   ```
   sonic# show ip route | include "via 10.1.1.2"
   ```
6. Shutdown BFD session:
   ```
   sonic(config-bfd-peer)# shutdown
   ```
7. Measure route withdrawal time:
   ```python
   start_time = time.time()
   while count_active_routes(dut) > 0:
       time.sleep(0.1)
   withdrawal_time = time.time() - start_time
   log.info(f"All 1000 routes withdrawn in {withdrawal_time} seconds")
   ```
8. Verify all routes removed from RIB:
   ```
   active_routes = count_active_routes(dut)
   assert active_routes == 0
   ```
9. Re-enable BFD session:
   ```
   sonic(config-bfd-peer)# no shutdown
   ```
10. Measure route installation time:
    ```python
    start_time = time.time()
    while count_active_routes(dut) < 1000:
        time.sleep(0.1)
    installation_time = time.time() - start_time
    log.info(f"All 1000 routes installed in {installation_time} seconds")
    ```
11. Verify all routes restored:
    ```
    route_count = count_active_routes(dut)
    assert route_count == 1000
    ```

**Expected Result**:
- All 1000 routes configured successfully
- All routes track BFD session correctly
- Route withdrawal time: < 2 seconds
- Route installation time: < 3 seconds
- No partial failures
- BFD state changes propagate to all routes
- System remains stable

**Validation**:
- 1000 routes tracking BFD
- Fast withdrawal on BFD down (< 2s)
- Fast installation on BFD up (< 3s)
- Consistent behavior across all routes

---

#### TC_BFD_SCALE_012: BFD CPU utilization

**Objective**: Measure and verify CPU utilization with maximum BFD sessions

**Pre-requisites**:
- Platform maximum sessions known
- CPU monitoring tools available

**Test Steps**:
1. Record baseline CPU with no BFD:
   ```python
   baseline_cpu = {
       'overall': get_overall_cpu(dut),
       'bfdd_process': 0,
       'kernel': get_kernel_cpu(dut)
   }
   ```
2. Configure maximum BFD sessions with standard timers (300ms):
   ```python
   MAX = get_platform_bfd_limit(dut)
   for i in range(1, MAX + 1):
       configure_bfd_session(dut, i, tx=300, rx=300)
   ```
3. Wait for all sessions Up and system stabilization (5 minutes)
4. Monitor CPU usage over 30 minutes:
   ```python
   cpu_samples = []
   for minute in range(30):
       sample = {
           'timestamp': time.time(),
           'overall_cpu': get_overall_cpu(dut),
           'bfdd_cpu': get_process_cpu(dut, 'bfdd'),
           'session_count': count_sessions_up(dut)
       }
       cpu_samples.append(sample)
       time.sleep(60)
   ```
5. Calculate statistics:
   ```python
   stats = {
       'avg_overall_cpu': mean([s['overall_cpu'] for s in cpu_samples]),
       'max_overall_cpu': max([s['overall_cpu'] for s in cpu_samples]),
       'avg_bfdd_cpu': mean([s['bfdd_cpu'] for s in cpu_samples]),
       'max_bfdd_cpu': max([s['bfdd_cpu'] for s in cpu_samples])
   }
   ```
6. Change to aggressive timers (50ms) and re-measure:
   ```python
   for i in range(1, MAX + 1):
       update_bfd_timers(dut, i, tx=50, rx=50)

   # Wait for stabilization
   time.sleep(300)

   # Monitor again for 30 minutes
   aggressive_cpu_samples = collect_cpu_samples(duration=30)
   ```
7. Generate CPU utilization report:
   ```python
   report = generate_report(baseline_cpu, standard_timer_stats, aggressive_timer_stats)
   log.info(report)
   ```

**Expected Result**:
- Standard timers (300ms):
  - Overall CPU: < 50% average, < 70% peak
  - BFD process CPU: < 30%
- Aggressive timers (50ms):
  - Overall CPU: < 70% average, < 90% peak
  - BFD process CPU: < 50%
- CPU usage stable over time (no increasing trend)
- Linear relationship between packet rate and CPU
- No CPU starvation of other processes

**Validation**:
- CPU within acceptable thresholds
- No CPU spikes > 95%
- BFD process CPU proportional to session count and timer values
- System remains responsive

---

#### TC_BFD_SCALE_013: BFD memory utilization

**Objective**: Measure and verify memory utilization with maximum BFD sessions

**Pre-requisites**:
- Platform maximum sessions known
- Memory monitoring tools available

**Test Steps**:
1. Record baseline memory:
   ```python
   baseline = {
       'total_memory': get_total_memory(dut),
       'used_memory': get_used_memory(dut),
       'free_memory': get_free_memory(dut),
       'bfdd_memory': 0
   }
   ```
2. Configure BFD sessions incrementally and measure:
   ```python
   memory_data = []
   increments = [10, 25, 50, 100, 150, 200, MAX]

   for target in increments:
       current = count_bfd_sessions(dut)
       for i in range(current + 1, target + 1):
           configure_bfd_session(dut, i)

       wait_for_sessions_up(dut, target)
       time.sleep(60)  # Stabilization

       memory_data.append({
           'session_count': target,
           'total_used': get_used_memory(dut),
           'bfdd_memory': get_process_memory(dut, 'bfdd'),
           'bfdd_resident': get_resident_memory(dut, 'bfdd')
       })
   ```
3. Calculate memory per session:
   ```python
   for i in range(1, len(memory_data)):
       prev = memory_data[i-1]
       curr = memory_data[i]

       session_delta = curr['session_count'] - prev['session_count']
       memory_delta = curr['bfdd_memory'] - prev['bfdd_memory']

       memory_per_session = memory_delta / session_delta
       log.info(f"Memory per session: {memory_per_session}KB")
   ```
4. Test for memory leaks:
   ```python
   # Monitor memory for 2 hours with stable sessions
   leak_test_start = get_process_memory(dut, 'bfdd')

   for hour in range(2):
       time.sleep(3600)
       current_mem = get_process_memory(dut, 'bfdd')
       increase = current_mem - leak_test_start
       log.info(f"Hour {hour+1}: Memory increase = {increase}KB")

   total_increase = get_process_memory(dut, 'bfdd') - leak_test_start
   leak_rate = total_increase / 2  # KB per hour
   ```
5. Test memory release on session deletion:
   ```python
   memory_before_delete = get_process_memory(dut, 'bfdd')

   # Delete half the sessions
   for i in range(1, MAX//2 + 1):
       delete_bfd_session(dut, i)

   time.sleep(120)  # Allow garbage collection

   memory_after_delete = get_process_memory(dut, 'bfdd')
   memory_freed = memory_before_delete - memory_after_delete
   percent_freed = (memory_freed / memory_before_delete) * 100
   ```

**Expected Result**:
- Memory per BFD session: < 50KB
- Total BFD memory with MAX sessions: < 20MB
- Memory leak rate: < 10KB/hour
- Memory freed on deletion: > 85%
- No system memory exhaustion
- No swap usage increase

**Validation**:
- Memory usage linear with session count
- Memory leak rate acceptable (< 10KB/hour)
- Memory properly released on session deletion
- Total system memory healthy

---

### 4.3 Stress Testing

#### TC_BFD_SCALE_014: Rapid config add/remove

**Objective**: Verify system stability under rapid BFD configuration changes

**Pre-requisites**:
- System ready for stress testing
- Monitoring tools active

**Test Steps**:
1. Start system monitoring:
   ```python
   monitor = start_background_monitoring(
       metrics=['cpu', 'memory', 'session_count', 'errors'],
       interval=1  # Every second
   )
   ```
2. Execute rapid config add/remove cycle:
   ```python
   for cycle in range(1, 101):  # 100 cycles
       log.info(f"Rapid config cycle {cycle}/100")

       # Add 20 sessions rapidly (no wait)
       for i in range(1, 21):
           st.config(dut, [
               "bfd",
               f"peer {get_peer_ip(i)} interface {get_interface(i)}",
               "transmit-interval 300",
               "receive-interval 300",
               "exit"
           ], type='klish', skip_error_check=False)

       # Immediately remove them (no stabilization)
       for i in range(1, 21):
           st.config(dut, [
               "bfd",
               f"no peer {get_peer_ip(i)} interface {get_interface(i)}"
           ], type='klish')

       # No sleep between cycles - continuous stress
   ```
3. Verify system stability after stress:
   ```python
   # Stop monitoring
   results = stop_background_monitoring(monitor)

   # Check for anomalies
   errors = check_for_errors(dut)
   cpu_spikes = [s for s in results if s['cpu'] > 95]
   daemon_restarts = check_daemon_restarts(dut, 'bfdd')
   ```
4. Verify clean final state:
   ```
   sonic# show bfd peers
   sonic# show running-config bfd
   sonic# show logging | include BFD | include ERROR
   ```
5. Test system responsiveness:
   ```python
   # CLI command response time
   start = time.time()
   st.show(dut, "show version")
   response_time = time.time() - start
   assert response_time < 5, "CLI response time degraded"
   ```

**Expected Result**:
- System survives 100 rapid config cycles
- No daemon crashes or restarts
- No configuration corruption
- CPU spikes acceptable (< 95%)
- Memory stable (no continual increase)
- Final state clean (no orphaned config)
- System responsive after stress
- No errors in syslog

**Validation**:
- 2000 total config operations completed (100 cycles × 20 add/remove)
- Zero daemon restarts
- Clean final state
- System responsive
- No memory leaks detected

---

#### TC_BFD_SCALE_015: BFD during config reload

**Objective**: Verify BFD configuration persists across config reload

**Pre-requisites**:
- 50 BFD sessions configured and Up

**Test Steps**:
1. Configure 50 BFD sessions:
   ```python
   for i in range(1, 51):
       configure_bfd_session(dut, i, tx=300, rx=300)
   verify_all_sessions_up(dut, 50)
   ```
2. Save configuration:
   ```
   sonic# write memory
   # OR
   sonic# copy running-config startup-config
   ```
3. Record pre-reload state:
   ```python
   pre_reload_state = {
       'session_count': count_bfd_sessions(dut),
       'sessions_up': count_sessions_up(dut),
       'bfd_config': get_bfd_running_config(dut)
   }
   ```
4. Execute config reload:
   ```
   sonic# config reload -y
   ```
5. Wait for system to come back:
   ```python
   wait_for_system_ready(dut, timeout=300)
   ```
6. Verify BFD configuration restored:
   ```python
   post_reload_state = {
       'session_count': count_bfd_sessions(dut),
       'sessions_up': count_sessions_up(dut),
       'bfd_config': get_bfd_running_config(dut)
   }

   assert pre_reload_state == post_reload_state
   ```
7. Wait for all sessions to re-establish:
   ```python
   wait_for_sessions_up(dut, expected=50, timeout=120)
   ```
8. Verify session details match:
   ```python
   for i in range(1, 51):
       session = get_bfd_session_details(dut, get_peer_ip(i))
       assert session['state'] == 'Up'
       assert session['tx_interval'] == 300
       assert session['rx_interval'] == 300
   ```

**Expected Result**:
- Configuration saved successfully
- System reloads without errors
- BFD configuration fully restored
- All 50 sessions re-establish
- Session parameters unchanged
- Re-establishment time < 2 minutes
- No configuration loss

**Validation**:
- Pre-reload session count == Post-reload session count
- All sessions return to Up state
- Configuration identical before/after
- No errors during reload

---

#### TC_BFD_SCALE_016: BFD during system reboot

**Objective**: Verify BFD survives system reboot (warm and cold)

**Pre-requisites**:
- 50 BFD sessions configured and Up
- Saved configuration with BFD

**Test Steps - Warm Reboot**:
1. Verify starting state:
   ```python
   verify_sessions_up(dut, 50)
   ```
2. Save configuration:
   ```
   sonic# write memory
   ```
3. Execute warm reboot:
   ```
   sonic# reboot -w
   # OR via API
   st.reboot(dut, 'warm')
   ```
4. Wait for system online:
   ```python
   wait_for_system_ready(dut, timeout=600)
   ```
5. Verify BFD sessions restored:
   ```python
   wait_for_sessions_up(dut, 50, timeout=180)
   ```
6. Check session continuity (for warm reboot, minimal downtime expected)

**Test Steps - Cold Reboot**:
1. Verify starting state:
   ```python
   verify_sessions_up(dut, 50)
   ```
2. Execute cold reboot:
   ```
   sonic# reboot
   # OR
   st.reboot(dut, 'fast')
   ```
3. Wait for system online:
   ```python
   wait_for_system_ready(dut, timeout=600)
   ```
4. Verify BFD configuration loaded:
   ```python
   assert count_bfd_sessions(dut) == 50
   ```
5. Wait for sessions to establish:
   ```python
   wait_for_sessions_up(dut, 50, timeout=180)
   ```

**Expected Result - Warm Reboot**:
- System performs warm reboot successfully
- BFD configuration persists
- Sessions re-establish quickly (< 1 minute)
- Minimal session downtime
- All 50 sessions return to Up

**Expected Result - Cold Reboot**:
- System performs cold reboot successfully
- BFD configuration persists in startup-config
- All sessions re-establish (< 3 minutes)
- No configuration loss
- All 50 sessions return to Up

**Validation**:
- Configuration survives reboot
- All sessions operational after boot
- No missing sessions
- Session parameters correct

---

#### TC_BFD_SCALE_017: BFD with process restart

**Objective**: Verify BFD handles daemon/process restarts gracefully

**Pre-requisites**:
- 30 BFD sessions Up
- BFD integrated with BGP (for BGP process restart test)

**Test Steps - BFD Daemon Restart**:
1. Verify sessions Up:
   ```python
   verify_sessions_up(dut, 30)
   ```
2. Identify BFD daemon process:
   ```
   sonic# show processes | include bfd
   ```
3. Restart BFD daemon:
   ```
   sonic# systemctl restart bfdd
   # OR
   docker exec bgp supervisorctl restart bfdd
   ```
4. Monitor session recovery:
   ```python
   start_time = time.time()
   wait_for_sessions_up(dut, 30, timeout=60)
   recovery_time = time.time() - start_time
   log.info(f"BFD sessions recovered in {recovery_time} seconds")
   ```
5. Verify all sessions restored:
   ```python
   assert count_sessions_up(dut) == 30
   ```

**Test Steps - BGP Process Restart with BFD**:
1. Configure BFD for BGP:
   ```
   sonic(config)# router bgp 65001
   sonic(config-router)# neighbor 10.1.1.2 bfd
   ```
2. Verify BGP session Up with BFD:
   ```
   sonic# show ip bgp summary
   sonic# show bfd peers
   ```
3. Restart BGP process:
   ```
   sonic# systemctl restart bgp
   ```
4. Monitor BGP recovery:
   ```python
   wait_for_bgp_neighbor_up(dut, '10.1.1.2', timeout=120)
   ```
5. Verify BFD session re-establishes:
   ```python
   wait_for_bfd_session_up(dut, '10.1.1.2', timeout=60)
   ```
6. Verify BGP-BFD integration intact:
   ```
   sonic# show ip bgp neighbor 10.1.1.2 | include BFD
   ```

**Expected Result - BFD Daemon Restart**:
- BFD daemon restarts successfully
- All sessions re-establish within 1 minute
- No sessions lost
- Session parameters preserved
- Connected applications (BGP, static routes) handle gracefully

**Expected Result - BGP Restart**:
- BGP restarts without affecting BFD daemon
- BFD sessions remain Up during BGP restart
- BGP-BFD association restored after BGP recovers
- BGP neighbor re-establishes quickly with BFD

**Validation**:
- All sessions recover after daemon restart
- No permanent session loss
- Integration with applications intact
- System stable after restart

---

#### TC_BFD_SCALE_018: BFD packet storm handling

**Objective**: Verify system handles excessive BFD packet injection gracefully

**Pre-requisites**:
- 1 BFD session Up between D1 and D2
- Scapy installed for packet injection
- Packet capture capability

**Test Steps**:
1. Establish baseline BFD session:
   ```python
   configure_bfd_session(dut1, peer_ip='10.1.1.2', tx=300, rx=300)
   verify_session_up(dut1, '10.1.1.2')
   ```
2. Record normal packet rate:
   ```python
   baseline_rate = get_bfd_packet_rate(dut1)
   # Expected: ~3.33 packets/sec (300ms interval)
   ```
3. Start packet storm using Scapy:
   ```python
   # Inject 1000 BFD packets per second
   storm_config = {
       'src_ip': '10.1.1.10',  # Different source
       'dst_ip': '10.1.1.1',   # D1
       'udp_dport': 3784,
       'rate_pps': 1000,
       'duration': 60  # 1 minute
   }

   start_bfd_packet_injection(tgen, storm_config)
   ```
4. Monitor legitimate BFD session during storm:
   ```python
   for second in range(60):
       session = get_bfd_session_status(dut1, '10.1.1.2')
       cpu = get_cpu_usage(dut1)

       storm_data.append({
           'time': second,
           'session_state': session['state'],
           'cpu': cpu,
           'rx_packets': session['rx_count']
       })

       time.sleep(1)
   ```
5. Stop packet storm:
   ```python
   stop_packet_injection(tgen)
   ```
6. Verify legitimate session still Up:
   ```python
   session = get_bfd_session_status(dut1, '10.1.1.2')
   assert session['state'] == 'Up'
   ```
7. Check for rate limiting or filtering:
   ```python
   # Check if storm packets were processed or dropped
   total_rx = storm_data[-1]['rx_packets'] - storm_data[0]['rx_packets']
   expected_legitimate = 60 / 0.3  # 60 seconds / 300ms

   if total_rx > expected_legitimate * 1.5:
       log.warning("System may be processing storm packets")
   else:
       log.info("System appears to filter/rate-limit storm packets")
   ```
8. Verify system stability:
   ```
   sonic# show processes cpu
   sonic# show memory
   sonic# show logging | include BFD
   ```

**Expected Result**:
- Legitimate BFD session remains Up during storm
- System detects or filters malicious packets
- CPU increase < 80% during storm
- No daemon crashes
- No legitimate session impact
- System recovers immediately after storm stops
- Appropriate logging of unusual activity

**Validation**:
- Legitimate session stable throughout test
- System remains responsive
- No service disruption
- Appropriate handling of excessive packets

---

---

## 5. BFD Integration Tests

### 5.1 BFD with L2 Features
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_INTEG_001 | BFD over VLAN | BFD session on VLAN interface | Session Up |
| TC_BFD_INTEG_002 | BFD over LAG/PortChannel | BFD session on LAG | Session Up, survives member link failure |
| TC_BFD_INTEG_003 | BFD with LAG member failure | Remove LAG member with BFD | BFD stays up if other members active |
| TC_BFD_INTEG_004 | BFD with STP topology change | Trigger STP topology change | BFD adapts to new topology |

### 5.2 BFD System Integration
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_INTEG_005 | BFD config save/restore | Save config, reload | BFD config persists |
| TC_BFD_INTEG_006 | BFD with config replace | Replace running config | BFD in new config works |
| TC_BFD_INTEG_007 | BFD syslog messages | Various BFD events | Appropriate syslog entries |
| TC_BFD_INTEG_008 | BFD SNMP support | Query BFD MIB objects | SNMP returns BFD data |
| TC_BFD_INTEG_009 | BFD with management VRF | Management traffic with BFD | No interference |

### 5.3 BFD Convergence Tests
| Test Case ID | Test Scenario | Steps | Expected Result |
|--------------|---------------|-------|-----------------|
| TC_BFD_CONV_001 | Measure BFD detection time | Time from link down to BFD down | < (rx_interval * multiplier) |
| TC_BFD_CONV_002 | BGP convergence with BFD | Time from BFD down to BGP down | Faster than BGP holdtime |
| TC_BFD_CONV_003 | OSPF convergence with BFD | Time from BFD down to OSPF reconvergence | Faster than OSPF dead interval |
| TC_BFD_CONV_004 | Static route convergence with BFD | Time from BFD down to route removal | Immediate route withdrawal |
| TC_BFD_CONV_005 | BFD recovery time | Time from link up to BFD up | Fast session re-establishment |

---

## 6. Test Execution Strategy

### 6.1 Prerequisites
- 2-node SONiC-VS testbed configured
- Klish CLI access enabled
- Scapy installed for traffic generation
- Tcpdump available for packet capture

### 6.2 Test Data Requirements
- IPv4 address ranges for test interfaces
- IPv6 address ranges for test interfaces
- VRF names for VRF tests
- BGP AS numbers for BGP tests
- OSPF area IDs for OSPF tests

### 6.3 Validation Approach
1. **Configuration Validation**: `show running-config` after each config
2. **State Validation**: `show bfd peers` to verify session state
3. **Traffic Validation**: Scapy packet capture and analysis
4. **Counter Validation**: `show bfd peers counters` for packet counts
5. **Cleanup**: Remove tcpdump files after execution (per user instructions)

### 6.4 Test Dependencies
```
Phase 1: CLI Tests (TC_BFD_CLI_*)
  └─> Phase 2: Functional Tests (TC_BFD_FUNC_*)
      └─> Phase 3: Integration Tests (TC_BFD_INTEG_*)
          └─> Phase 4: Scaling Tests (TC_BFD_SCALE_*)
              └─> Phase 5: Negative Tests (TC_BFD_NEG_*)
```

### 6.5 Success Criteria
- All CLI commands execute without errors
- BFD sessions establish correctly with proper state
- Scapy traffic validation confirms BFD packet exchange
- Counters increment appropriately
- System remains stable under scaling scenarios
- Error conditions handled gracefully

---

## 7. Test Automation Guidelines

### 7.1 SPyTest Framework Integration
- Use SpyTest APIs for all device interactions
- Create reusable BFD APIs in `apis/routing/bfd.py`
- Follow SPyTest test structure (module hooks, fixtures)
- Use `st.show()` for show commands with Klish CLI type
- Use `st.config()` for configuration commands

### 7.2 Traffic Generation (Scapy)
- Use SPyTest Scapy APIs for traffic generation
- Verify packets using both tcpdump and counters
- Remove tcpdump files after execution (per user instructions)
- Validate BFD control packets (UDP port 3784)
- Validate BFD echo packets (UDP port 3785)

### 7.3 Test Variables
- Define test data in YAML files (`spytest/vars/routing/bfd_vars.yaml`)
- Use `st.ensure_min_topology("D1D2:1")` for 2-node topology
- Store BFD session parameters in SpyTestDict

### 7.4 Reporting
- Use `st.report_pass()` / `st.report_fail()` for test results
- Use `st.banner()` for test section headers
- Log detailed steps with `st.log()`
- Report test case results with `st.report_tc_pass()` / `st.report_tc_fail()`

---

## 8. Future Enhancements

### Potential Additional Test Scenarios
1. BFD with MPLS
2. BFD with segment routing
3. BFD with GRE tunnels
4. BFD with VXLAN
5. BFD authentication (if supported)
6. BFD demand mode
7. BFD with active/standby routing protocols
8. BFD hitless restart scenarios

---

## Appendix A: BFD Klish CLI Reference

### Global Configuration
```
sonic(config)# bfd
sonic(config-bfd)# slow-timer <1000-60000>
```

### Peer Configuration
```
sonic(config-bfd)# peer <ip-address> [vrf <vrf-name>] [interface <interface>] [local-address <ip>] [multihop]
sonic(config-bfd-peer)# transmit-interval <10-60000>
sonic(config-bfd-peer)# receive-interval <10-60000>
sonic(config-bfd-peer)# detect-multiplier <3-50>
sonic(config-bfd-peer)# echo-mode
sonic(config-bfd-peer)# echo-interval <10-60000>
sonic(config-bfd-peer)# shutdown
```

### Profile Configuration
```
sonic(config)# bfd profile <profile-name>
sonic(config-bfd-profile)# transmit-interval <10-60000>
sonic(config-bfd-profile)# receive-interval <10-60000>
sonic(config-bfd-profile)# detect-multiplier <3-50>
```

### Show Commands
```
sonic# show bfd peers
sonic# show bfd peer <ip-address>
sonic# show bfd peers brief
sonic# show bfd peers vrf <vrf-name>
sonic# show bfd peers counters
sonic# show running-config bfd
```

---

## Appendix B: BFD Packet Structure (for Scapy Validation)

### BFD Control Packet Format
- Version: 1
- Diagnostic: Varies by state
- State: 0=AdminDown, 1=Down, 2=Init, 3=Up
- Detect Multiplier: Configured value
- My Discriminator: Local unique ID
- Your Discriminator: Remote discriminator
- Desired Min TX Interval: Microseconds
- Required Min RX Interval: Microseconds
- Required Min Echo RX Interval: Microseconds

### Transport
- Single-hop: IP TTL=255, UDP destination port 3784
- Multi-hop: IP TTL>1, UDP destination port 4784
- Echo: UDP destination port 3785

---

**Total Test Cases: ~150+ test cases covering all aspects of BFD functionality**
