# LACP Test Plan

## Table of Contents
1. [Introduction](#introduction)
2. [Test Environment](#test-environment)
3. [Topology](#topology)
4. [Feature Overview](#feature-overview)
5. [Test Scenarios](#test-scenarios)
   - [Basic Functionality Tests](#basic-functionality-tests)
   - [LACP Mode Tests](#lacp-mode-tests)
   - [LACP Fallback Tests](#lacp-fallback-tests)
   - [Min-Links Tests](#min-links-tests)
   - [LACP Timer Tests](#lacp-timer-tests)
   - [Traffic Load Balancing Tests](#traffic-load-balancing-tests)
   - [System Configuration Tests](#system-configuration-tests)
   - [Negative Test Scenarios](#negative-test-scenarios)
   - [Scaling Test Scenarios](#scaling-test-scenarios)
   - [Interoperability Tests](#interoperability-tests)
6. [Test Summary](#test-summary)

---

## Introduction

This document describes the comprehensive test plan for validating Link Aggregation Control Protocol (LACP) functionality in SONiC. LACP (IEEE 802.3ad/802.1AX) enables the bundling of multiple physical links into a single logical link for increased bandwidth and redundancy.

**Testbed Configuration:**
- This test plan requires a two-node topology with minimum 4 interconnected ports
- Uses two SONiC devices (physical or virtual) with back-to-back connections
- Port connections: D1D2P1-P4 mapped as described in Section 3 (Topology)
- Testbed file should be configured according to your specific environment

**Test Scope:**
- LACP protocol functionality validation
- Port channel creation, deletion, and member management
- LACP modes (Active, Passive, Static/On)
- LACP timers (Fast/Slow rate)
- LACP fallback mechanism
- Min-links functionality
- Traffic load balancing across LAG members
- System MAC configuration
- Negative scenarios and error handling
- Scaling scenarios with multiple LAGs and members

---

## Test Environment

### Hardware/Software Requirements
- **DUT1**: SONiC device (physical or virtual)
- **DUT2**: SONiC device (physical or virtual)
- **Testbed File**: Your environment-specific testbed YAML file
- **Traffic Generator**: Scapy-based traffic generation or external traffic generator (Ixia/Spirent)
- **Physical Links**: Minimum 4 ports between DUT1 and DUT2
- **Test Framework**: SPyTest
- **Access Protocol**: SSH (port 22)
- **Credentials**: As configured in your testbed file

### Configuration Management
- All configurations will be verified using `show running-config`
- Test packets will be transmitted using Scapy from DUTs
- CLI types tested: Click, Klish, REST, gNMI
- Interface naming: Native mode (Ethernet* format)

---

## Topology

### Two-Node Back-to-Back Topology

```
                                    PortChannel7
    ┌─────────────┐      ╔═══════════════════════════╗      ┌─────────────┐
    │             │      ║   D1D2P1     ◄──────►   D2D1P1   ║      │             │
    │             │      ║   D1D2P2     ◄──────►   D2D1P2   ║      │             │
    │    DUT1     │◄─────╬   D1D2P3     ◄──────►   D2D1P3   ╬─────►│    DUT2     │
    │   (SONiC)   │      ║   D1D2P4     ◄──────►   D2D1P4   ║      │   (SONiC)   │
    │             │      ╚═══════════════════════════╝      │             │
    └─────────────┘                                           └─────────────┘
```

### Topology Details
- **D1**: Primary DUT running SONiC
- **D2**: Secondary DUT/Partner running SONiC
- **D1D2P1-P4**: Four interconnected ports between D1 and D2
  - D1D2P1 ↔ D2D1P1 (First port pair)
  - D1D2P2 ↔ D2D1P2 (Second port pair)
  - D1D2P3 ↔ D2D1P3 (Third port pair)
  - D1D2P4 ↔ D2D1P4 (Fourth port pair)
- **Note**: Port names will vary based on your testbed configuration (e.g., Ethernet0, Ethernet4, etc.)
- **Traffic Generation**: Scapy-based traffic from DUTs or external traffic generators

---

## Feature Overview

### LACP Protocol Features
1. **Port Aggregation**: Bundle multiple physical links into logical interface
2. **LACP Modes**:
   - **Active**: Actively sends LACP PDUs
   - **Passive**: Waits for partner to initiate LACP
   - **Static/On**: No LACP protocol, static aggregation
3. **LACP Timers**:
   - **Slow Rate**: LACP PDUs every 30 seconds (default)
   - **Fast Rate**: LACP PDUs every 1 second
4. **Fallback**: Allows one member to forward traffic if LACP negotiation fails
5. **Min-Links**: Minimum number of active members required for LAG to be operational
6. **Load Balancing**: Traffic distribution across LAG members based on hash

### Configuration Parameters
- Port channel name/ID
- Member interfaces
- LACP mode (active/passive/on)
- LACP rate (fast/slow)
- Fallback enable/disable
- Min-links value
- System MAC address
- System priority
- Port priority

---

## Traffic Testing Methodology

This section provides detailed explanation of how Layer 2 (L2) and Layer 3 (L3) traffic will be tested across the LACP port channel to validate load balancing, redundancy, and forwarding behavior.

### L2 Traffic Testing

Layer 2 traffic testing validates Ethernet frame forwarding across the LAG without IP routing. This tests MAC-based switching and load balancing at the data link layer.

#### L2 Traffic Test Setup

**Configuration Steps:**
1. Configure PortChannel7 on both DUT1 and DUT2 with 4 member ports (D1D2P1-P4)
2. Create VLAN (e.g., VLAN 100) on both DUTs
3. Add PortChannel7 as a tagged or untagged member to VLAN 100
4. Ensure L2 forwarding is enabled (no IP addresses on PortChannel)
5. Configure MAC aging time (optional, for MAC learning tests)

**Traffic Generation Methods:**

**Method 1: Scapy-based L2 Traffic (from DUTs)**
```python
# Generate L2 frames with varied source MACs
from scapy.all import Ether, sendp

# Test 1: Source MAC variation
for i in range(100):
    src_mac = f"00:11:22:33:44:{i:02x}"
    dst_mac = "00:aa:bb:cc:dd:ee"
    frame = Ether(src=src_mac, dst=dst_mac) / Raw(load="X"*1400)
    sendp(frame, iface="PortChannel7", count=100)

# Test 2: Destination MAC variation
src_mac = "00:11:22:33:44:55"
for i in range(100):
    dst_mac = f"00:aa:bb:cc:dd:{i:02x}"
    frame = Ether(src=src_mac, dst=dst_mac) / Raw(load="X"*1400)
    sendp(frame, iface="PortChannel7", count=100)

# Test 3: Both source and destination MAC variation
for i in range(100):
    src_mac = f"00:11:22:33:{i//16:02x}:{i%16:02x}"
    dst_mac = f"00:aa:bb:cc:{i//16:02x}:{i%16:02x}"
    frame = Ether(src=src_mac, dst=dst_mac) / Raw(load="X"*1400)
    sendp(frame, iface="PortChannel7", count=100)
```

**Method 2: External Traffic Generator (Ixia/Spirent)**
- Configure traffic streams with L2 Ethernet frames
- Vary source MAC addresses: Generate 1000+ unique source MACs
- Vary destination MAC addresses: Generate 1000+ unique destination MACs
- Frame size variation: 64, 128, 512, 1500, 9000 bytes (if jumbo frames enabled)
- Traffic rate: 10%, 50%, 100% of line rate
- Duration: Continuous traffic for 60+ seconds

#### L2 Traffic Validation Points

**1. MAC Address Learning:**
```bash
# Verify MACs learned on PortChannel
show mac address-table | grep PortChannel7

# Verify MAC count matches traffic streams
show mac address-table count
```

**2. Load Balancing Verification:**
```bash
# Check per-member interface statistics
show interfaces counters | grep -E "Ethernet(20|16|8|12)"  # or your ports

# Verify traffic distribution across members (should be roughly equal)
# Example output analysis:
# Member 1: 250,000 packets (25%)
# Member 2: 255,000 packets (25.5%)
# Member 3: 245,000 packets (24.5%)
# Member 4: 250,000 packets (25%)
# Distribution variance should be < 10%
```

**3. Hash Algorithm Testing:**
- **Source MAC Hash**: Same source MAC always uses same member port
- **Destination MAC Hash**: Same destination MAC always uses same member port
- **Src+Dst MAC Hash**: Same MAC pair always uses same member port
- **VLAN Tag Hash**: Same VLAN ID contributes to hash calculation

**4. Forwarding Verification:**
```bash
# Zero packet drops expected
show interfaces counters errors

# Verify frame forwarding
show interfaces counters | grep -A5 PortChannel7
```

#### L2 Traffic Test Scenarios

**Scenario 1: Broadcast Traffic**
- Send broadcast frames (dst MAC: FF:FF:FF:FF:FF:FF)
- Verify broadcast forwarded on all LAG members
- Check for packet duplication (should not occur)

**Scenario 2: Multicast Traffic**
- Send multicast frames (dst MAC: 01:00:5E:xx:xx:xx)
- Verify multicast forwarding behavior
- Test IGMP snooping if enabled

**Scenario 3: Unknown Unicast Flooding**
- Send unicast frames with unknown destination MAC
- Verify flooding behavior across VLAN
- Monitor MAC learning

**Scenario 4: VLAN Tagged Traffic**
```python
from scapy.all import Ether, Dot1Q, Raw, sendp

# Tagged frames for different VLANs
for vlan_id in [100, 200, 300]:
    for i in range(50):
        src_mac = f"00:11:22:33:{vlan_id//100}:{i:02x}"
        dst_mac = f"00:aa:bb:cc:{vlan_id//100}:{i:02x}"
        frame = Ether(src=src_mac, dst=dst_mac) / \
                Dot1Q(vlan=vlan_id) / \
                Raw(load="X"*1400)
        sendp(frame, iface=interface, count=100)
```

**Scenario 5: Jumbo Frames**
- Configure MTU 9000 on PortChannel7
- Send frames up to 9000 bytes
- Verify forwarding without fragmentation

### L3 Traffic Testing (IPv4)

Layer 3 IPv4 traffic testing validates IP routing and forwarding across the LAG, including IP-based load balancing.

#### L3 IPv4 Traffic Test Setup

**Configuration Steps:**
1. Configure PortChannel7 on both DUT1 and DUT2 with 4 member ports
2. Assign IPv4 address to PortChannel7 on both DUTs
   - DUT1: `ip address 10.1.1.1/24` on PortChannel7
   - DUT2: `ip address 10.1.1.2/24` on PortChannel7
3. Verify IP interface is up
4. Configure additional routes if needed for traffic testing
5. Enable routing protocols if testing dynamic scenarios (BGP, OSPF, etc.)

**Traffic Generation Methods:**

**Method 1: Scapy-based IPv4 Traffic (from DUTs)**
```python
from scapy.all import Ether, IP, TCP, UDP, ICMP, Raw, send, sr1

# Test 1: Source IP variation
base_dst_ip = "10.1.1.100"
for i in range(1000):
    src_ip = f"192.168.{i//256}.{i%256}"
    packet = IP(src=src_ip, dst=base_dst_ip) / \
             TCP(sport=1024, dport=80) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)

# Test 2: Destination IP variation
base_src_ip = "192.168.1.100"
for i in range(1000):
    dst_ip = f"10.2.{i//256}.{i%256}"
    packet = IP(src=base_src_ip, dst=dst_ip) / \
             TCP(sport=1024, dport=80) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)

# Test 3: Source and Destination IP variation
for i in range(1000):
    src_ip = f"192.168.{i//256}.{i%256}"
    dst_ip = f"10.2.{i//256}.{i%256}"
    packet = IP(src=src_ip, dst=dst_ip) / \
             TCP(sport=1024, dport=80) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)

# Test 4: L4 port variation (for 5-tuple hashing)
base_src_ip = "192.168.1.100"
base_dst_ip = "10.1.1.100"
for i in range(1000):
    src_port = 1024 + i
    dst_port = 8000 + i
    packet = IP(src=base_src_ip, dst=base_dst_ip) / \
             TCP(sport=src_port, dport=dst_port) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)
```

**Method 2: External Traffic Generator (Ixia/Spirent)**
- Configure IPv4 traffic streams
- Source IP range: 192.168.0.1 - 192.168.255.254 (65,000+ IPs)
- Destination IP range: 10.1.1.1 - 10.1.255.254 (65,000+ IPs)
- Protocol variations: TCP, UDP, ICMP
- L4 port range: 1024-65535 (for TCP/UDP)
- Packet size: 64, 128, 512, 1500, 9000 bytes
- Traffic rate: 10%, 50%, 100% line rate
- Duration: 60-300 seconds continuous

#### L3 IPv4 Traffic Validation Points

**1. IP Routing Verification:**
```bash
# Verify IP interface status
show ip interface PortChannel7

# Check routing table
show ip route | grep PortChannel7

# Verify IP connectivity
ping 10.1.1.2 -I PortChannel7
```

**2. Load Balancing Verification:**
```bash
# Check per-member interface packet counters
show interfaces counters

# Verify L3 hash distribution
# With source IP variation: Different source IPs use different members
# With destination IP variation: Different dest IPs use different members
# With 5-tuple hash: Best distribution with varied src/dst IP and ports
```

**3. Protocol-Specific Testing:**

**TCP Traffic:**
```python
# TCP SYN flood test (connection-oriented)
for i in range(1000):
    src_ip = f"192.168.{i//256}.{i%256}"
    dst_ip = "10.1.1.100"
    packet = IP(src=src_ip, dst=dst_ip) / \
             TCP(sport=1024+i, dport=80, flags="S")
    send(packet, iface="PortChannel7", count=10)

# Verify TCP statistics
show ip tcp statistics
```

**UDP Traffic:**
```python
# UDP traffic with port variation
for i in range(1000):
    src_ip = f"192.168.{i//256}.{i%256}"
    dst_ip = "10.1.1.100"
    packet = IP(src=src_ip, dst=dst_ip) / \
             UDP(sport=5000+i, dport=6000+i) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)
```

**ICMP Traffic:**
```python
# ICMP echo requests with varied source IPs
for i in range(1000):
    src_ip = f"192.168.{i//256}.{i%256}"
    dst_ip = "10.1.1.100"
    packet = IP(src=src_ip, dst=dst_ip) / \
             ICMP(type=8, code=0, id=i) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=10)
```

**4. Performance Metrics:**
```bash
# Throughput measurement
show interfaces counters rate

# Latency measurement (if supported)
show interface PortChannel7 performance

# Packet loss check
show interfaces counters errors
show interfaces counters discards
```

#### L3 IPv4 Traffic Test Scenarios

**Scenario 1: Routed Traffic Across LAG**
- Configure PortChannel7 as L3 interface with IP
- Send traffic from subnet A (via DUT1) to subnet B (via DUT2)
- Verify routing and load balancing

**Scenario 2: Multi-Subnet Testing**
- Configure multiple IP subnets on subinterfaces (PortChannel7.100, PortChannel7.200)
- Send traffic to different subnets
- Verify VLAN tag and IP-based hashing

**Scenario 3: QoS and DSCP Testing**
```python
# Traffic with different DSCP values
for dscp in [0, 8, 16, 24, 32, 40, 46, 48]:
    packet = IP(src="192.168.1.100", dst="10.1.1.100", tos=dscp<<2) / \
             TCP(sport=1024, dport=80) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=1000)
```

### L3 Traffic Testing (IPv6)

Layer 3 IPv6 traffic testing validates IPv6 routing and forwarding across the LAG, including IPv6-specific features.

#### L3 IPv6 Traffic Test Setup

**Configuration Steps:**
1. Configure PortChannel7 on both DUT1 and DUT2 with 4 member ports
2. Enable IPv6 on both DUTs
3. Assign IPv6 addresses to PortChannel7
   - DUT1: `ipv6 address 2001:db8:1::1/64` on PortChannel7
   - DUT2: `ipv6 address 2001:db8:1::2/64` on PortChannel7
4. Configure link-local addresses (auto-generated or manual)
5. Enable IPv6 routing
6. Configure IPv6 routing protocols if needed (OSPFv3, BGP)

**Traffic Generation Methods:**

**Method 1: Scapy-based IPv6 Traffic (from DUTs)**
```python
from scapy.all import Ether, IPv6, TCP, UDP, ICMPv6EchoRequest, Raw, send

# Test 1: IPv6 Source Address Variation
base_dst_ipv6 = "2001:db8:2::100"
for i in range(1000):
    src_ipv6 = f"2001:db8:1::{i:x}"
    packet = IPv6(src=src_ipv6, dst=base_dst_ipv6) / \
             TCP(sport=1024, dport=80) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)

# Test 2: IPv6 Destination Address Variation
base_src_ipv6 = "2001:db8:1::100"
for i in range(1000):
    dst_ipv6 = f"2001:db8:2::{i:x}"
    packet = IPv6(src=base_src_ipv6, dst=dst_ipv6) / \
             TCP(sport=1024, dport=80) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)

# Test 3: IPv6 with Flow Label Variation
for i in range(1000):
    src_ipv6 = f"2001:db8:1::{i:x}"
    dst_ipv6 = f"2001:db8:2::{i:x}"
    packet = IPv6(src=src_ipv6, dst=dst_ipv6, fl=i) / \
             TCP(sport=1024+i, dport=8000+i) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)

# Test 4: ICMPv6 Traffic
for i in range(1000):
    src_ipv6 = f"2001:db8:1::{i:x}"
    dst_ipv6 = "2001:db8:2::100"
    packet = IPv6(src=src_ipv6, dst=dst_ipv6) / \
             ICMPv6EchoRequest(id=i, seq=1) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=10)
```

**Method 2: External Traffic Generator (Ixia/Spirent)**
- Configure IPv6 traffic streams
- Source IPv6 range: 2001:db8:1::1 - 2001:db8:1::ffff (65,535 addresses)
- Destination IPv6 range: 2001:db8:2::1 - 2001:db8:2::ffff (65,535 addresses)
- Flow label variation: 0 - 1048575 (20-bit field)
- Protocol: TCP, UDP, ICMPv6
- L4 port range: 1024-65535
- Traffic class: 0-255 (for QoS testing)
- Packet size: 64, 128, 512, 1500, 9000 bytes
- Rate: 10%, 50%, 100% line rate

#### L3 IPv6 Traffic Validation Points

**1. IPv6 Routing Verification:**
```bash
# Verify IPv6 interface status
show ipv6 interface PortChannel7

# Check IPv6 routing table
show ipv6 route | grep PortChannel7

# Verify IPv6 connectivity
ping6 2001:db8:1::2 -I PortChannel7

# Check neighbor discovery
show ipv6 neighbors | grep PortChannel7
```

**2. IPv6 Load Balancing Verification:**
```bash
# Check interface statistics
show interfaces counters

# IPv6 hash fields typically include:
# - Source IPv6 address (128 bits)
# - Destination IPv6 address (128 bits)
# - Flow label (20 bits)
# - Next header (protocol)
# - Source/Dest L4 ports (for TCP/UDP)
```

**3. IPv6-Specific Feature Testing:**

**Neighbor Discovery Protocol (NDP):**
```python
from scapy.all import IPv6, ICMPv6ND_NS, ICMPv6ND_NA, send

# Neighbor Solicitation
ns = IPv6(dst="ff02::1:ff00:2") / \
     ICMPv6ND_NS(tgt="2001:db8:1::2")
send(ns, iface="PortChannel7")

# Verify NDP cache
# show ipv6 neighbors
```

**Router Advertisement:**
```bash
# Verify RA messages on PortChannel
show ipv6 interface PortChannel7

# Should show router advertisement info
```

**4. IPv6 Extension Headers:**
```python
# Test with IPv6 extension headers
from scapy.all import IPv6, IPv6ExtHdrHopByHop, TCP, Raw

packet = IPv6(src="2001:db8:1::100", dst="2001:db8:2::100") / \
         IPv6ExtHdrHopByHop() / \
         TCP(sport=1024, dport=80) / \
         Raw(load="X"*1400)
send(packet, iface="PortChannel7", count=1000)
```

#### L3 IPv6 Traffic Test Scenarios

**Scenario 1: Basic IPv6 Routing**
- Send IPv6 traffic across LAG
- Verify routing and load balancing
- Check for ICMPv6 errors

**Scenario 2: IPv6 Multicast**
```python
# IPv6 multicast traffic
multicast_addrs = [
    "ff02::1",      # All nodes
    "ff02::2",      # All routers
    "ff02::1:2",    # All DHCP agents
]

for mcast_addr in multicast_addrs:
    packet = IPv6(src="2001:db8:1::100", dst=mcast_addr) / \
             ICMPv6EchoRequest() / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)
```

**Scenario 3: Dual-Stack Testing**
```python
# Simultaneous IPv4 and IPv6 traffic
# IPv4 stream
ipv4_packet = IP(src="192.168.1.100", dst="10.1.1.100") / \
              TCP(sport=1024, dport=80)

# IPv6 stream
ipv6_packet = IPv6(src="2001:db8:1::100", dst="2001:db8:2::100") / \
              TCP(sport=1024, dport=80)

# Send both simultaneously
send([ipv4_packet, ipv6_packet], iface="PortChannel7", inter=0.001, count=10000)
```

**Scenario 4: IPv6 Flow Label Hashing**
```python
# Test flow label contribution to hash
base_src = "2001:db8:1::100"
base_dst = "2001:db8:2::100"

# Same src/dst but different flow labels
for flow_label in range(1000):
    packet = IPv6(src=base_src, dst=base_dst, fl=flow_label) / \
             TCP(sport=1024, dport=80) / \
             Raw(load="X"*1400)
    send(packet, iface="PortChannel7", count=100)

# Verify different flow labels use different LAG members
```

### Traffic Testing Best Practices

1. **Pre-Test Verification:**
   - Clear all interface counters before testing
   - Verify all LAG members are "up" and "Selected"
   - Check LACP state on all members
   - Baseline system resources (CPU, memory)

2. **During Test Monitoring:**
   - Monitor interface counters in real-time
   - Check for errors, discards, drops
   - Monitor system resources
   - Capture LACP PDUs to verify stability

3. **Post-Test Analysis:**
   - Calculate traffic distribution variance
   - Analyze packet loss (if any)
   - Verify no LACP state changes during test
   - Check system logs for warnings/errors

4. **Traffic Distribution Calculation:**
```bash
# Example calculation for 4-member LAG
# Total packets sent: 1,000,000
# Expected per-member: 250,000 (25%)
# Acceptable variance: ±5% (237,500 - 262,500 packets)

Member1: 248,523 packets (24.85%) ✓
Member2: 251,847 packets (25.18%) ✓
Member3: 246,092 packets (24.61%) ✓
Member4: 253,538 packets (25.35%) ✓
Variance: 0.74% ✓ PASS
```

5. **Performance Benchmarks:**
   - **Throughput**: Should achieve line rate (e.g., 40Gbps for 4x10G LAG)
   - **Latency**: < 1ms for local LAG switching
   - **Packet Loss**: 0% in steady state
   - **Convergence**: < 3 seconds with fast LACP rate

---

## Test Scenarios

### Basic Functionality Tests

#### TC_LACP_BASIC_001: Create Port Channel with Single Member
**Objective**: Verify port channel creation with single member interface

**Test Procedure**:
1. Configure PortChannel7 on DUT1
2. Add Ethernet20 (D1D2P1) as member to PortChannel7
3. Configure PortChannel7 on DUT2
4. Add Ethernet24 (D2D1P1) as member to PortChannel7
5. Verify PortChannel7 is created on both DUTs
6. Verify member interface is part of PortChannel7
7. Check LACP protocol state is "up"

**Expected Result**:
- PortChannel7 created successfully on both DUTs
- Member interface shows as member in `show interface PortChannel 7`
- LACP state transitions to "up"
- LACP PDUs exchanged between partners

**Verification Commands**:
```bash
show interface PortChannel 7
show running-config interface PortChannel 7
show lacp neighbor
```

---

#### TC_LACP_BASIC_002: Create Port Channel with Multiple Members
**Objective**: Verify port channel creation with multiple member interfaces

**Test Procedure**:
1. Configure PortChannel7 on DUT1
2. Add Ethernet20, Ethernet16, Ethernet8, Ethernet12 (D1D2P1-P4) as members to PortChannel7
3. Configure PortChannel7 on DUT2
4. Add Ethernet24, Ethernet20, Ethernet8, Ethernet16 (D2D1P1-P4) as members to PortChannel7
5. Verify all members are added successfully
6. Verify PortChannel7 protocol state is "up"
7. Verify all member states are "Selected"

**Expected Result**:
- All 4 members successfully added to PortChannel7
- All member ports in "Selected" state
- LACP negotiation successful on all members
- PortChannel7 operational state is "up"

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp neighbor
show lacp interface PortChannel 7
```

---

#### TC_LACP_BASIC_003: Delete Port Channel Member
**Objective**: Verify member removal from port channel

**Test Procedure**:
1. Start with PortChannel7 having 4 members (from TC_LACP_BASIC_002)
2. Remove D1D2P4 (Ethernet12 on D1, Ethernet16 on D2) from PortChannel7 on both DUTs
3. Verify the member is removed from PortChannel7
4. Verify remaining 3 members still operational
5. Verify PortChannel7 remains "up" with 3 members

**Expected Result**:
- Member successfully removed from PortChannel7 on both DUTs
- Remaining members (D1D2P1-P3) continue forwarding
- No traffic loss on remaining members
- PortChannel7 stays operational

**Verification Commands**:
```bash
show interface PortChannel 7
show interface Ethernet12  # on D1
show interface Ethernet16  # on D2
show running-config interface PortChannel 7
```

---

#### TC_LACP_BASIC_004: Delete Port Channel
**Objective**: Verify port channel deletion

**Test Procedure**:
1. Start with configured PortChannel7 with members
2. Remove all members from PortChannel7 on both DUTs
3. Delete PortChannel7 on both DUTs
4. Verify PortChannel7 is deleted
5. Verify member interfaces return to default state

**Expected Result**:
- PortChannel7 successfully deleted on both DUTs
- PortChannel7 not present in `show interface PortChannel`
- Member interfaces operational as independent ports
- Configuration cleaned up in running-config

**Verification Commands**:
```bash
show interface PortChannel
show interface status
show running-config
```

---

#### TC_LACP_BASIC_005: Add Member to Existing Port Channel
**Objective**: Verify dynamic addition of member to operational port channel

**Test Procedure**:
1. Create PortChannel7 with 2 members (D1D2P1-P2: Ethernet20/Ethernet24 and Ethernet16/Ethernet20)
2. Verify PortChannel7 is operational
3. Dynamically add D1D2P3 (Ethernet8 on both DUTs) to PortChannel7
4. Verify new member joins PortChannel7
5. Verify LACP negotiation on new member
6. Verify traffic distribution includes new member

**Expected Result**:
- New member successfully added to operational PortChannel7
- LACP negotiation completes on new member
- No disruption to existing traffic on other members
- Traffic load-balancing includes new member

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp interface PortChannel 7
show lacp neighbor
```

---

### LACP Mode Tests

#### TC_LACP_MODE_001: LACP Active-Active Mode
**Objective**: Verify LACP operation with both sides in Active mode

**Test Procedure**:
1. Configure PortChannel7 on DUT1 in LACP Active mode (default)
2. Configure PortChannel7 on DUT2 in LACP Active mode (default)
3. Add members to both sides
4. Verify LACP PDUs sent from both sides
5. Verify LACP negotiation succeeds
6. Check LACP activity status

**Expected Result**:
- Both sides send LACP PDUs
- LACP negotiation successful
- Port channel becomes operational
- Member ports in "Selected" state

**Verification Commands**:
```bash
show lacp neighbor
show lacp counters
show lacp interface PortChannel 7
```

---

#### TC_LACP_MODE_002: LACP Active-Passive Mode
**Objective**: Verify LACP operation with Active-Passive configuration

**Test Procedure**:
1. Configure PortChannel7 on DUT1 in LACP Active mode
2. Configure PortChannel7 on DUT2 in LACP Passive mode
3. Add members to both sides
4. Verify DUT1 (Active) sends LACP PDUs first
5. Verify DUT2 (Passive) responds to LACP PDUs
6. Verify LACP negotiation succeeds

**Expected Result**:
- Active side initiates LACP negotiation
- Passive side responds to LACP PDUs
- LACP negotiation successful
- Port channel operational with correct mode display

**Verification Commands**:
```bash
show lacp neighbor
show lacp interface PortChannel 7
```

---

#### TC_LACP_MODE_003: Static LAG (Mode On)
**Objective**: Verify static port channel without LACP protocol

**Test Procedure**:
1. Configure PortChannel7 on DUT1 with mode "on" (static)
2. Configure PortChannel7 on DUT2 with mode "on" (static)
3. Add members to both sides
4. Verify no LACP PDUs exchanged
5. Verify port channel is operational
6. Send traffic and verify forwarding

**Expected Result**:
- PortChannel7 operational without LACP protocol
- No LACP PDUs exchanged
- Traffic forwards across static LAG
- Member ports operational without LACP state machine

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp neighbor (should show no LACP activity)
```

---

#### TC_LACP_MODE_004: LACP Passive-Passive Mode (Negative)
**Objective**: Verify LACP fails with both sides in Passive mode

**Test Procedure**:
1. Configure PortChannel7 on DUT1 in LACP Passive mode
2. Configure PortChannel7 on DUT2 in LACP Passive mode
3. Add members to both sides
4. Verify LACP negotiation does not complete
5. Verify port channel remains down

**Expected Result**:
- No LACP PDUs exchanged (both sides waiting)
- LACP negotiation fails
- Port channel protocol state remains "down"
- Member ports in "Standby" or "down" state

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp neighbor
show lacp interface PortChannel 7
```

---

### LACP Fallback Tests

#### TC_LACP_FALLBACK_001: Enable LACP Fallback
**Objective**: Verify LACP fallback configuration and operation

**Test Procedure**:
1. Configure PortChannel7 on DUT1 with fallback enabled
2. Add multiple members to PortChannel7
3. Configure DUT2 without LACP (or disable LACP on partner)
4. Verify fallback activates on DUT1
5. Verify one member port becomes operational
6. Send traffic and verify forwarding through fallback port

**Expected Result**:
- Fallback enabled in configuration
- One member port operational in fallback mode
- Traffic forwards through fallback port
- Fallback status shown in output

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp interface PortChannel 7
show running-config interface PortChannel 7
```

---

#### TC_LACP_FALLBACK_002: LACP Fallback to Normal Transition
**Objective**: Verify transition from fallback mode to normal LACP operation

**Test Procedure**:
1. Start with PortChannel7 in fallback mode (one port active)
2. Configure LACP on partner device (DUT2)
3. Verify LACP negotiation begins
4. Verify transition from fallback to normal LACP mode
5. Verify all member ports become operational
6. Verify traffic redistributes across all members

**Expected Result**:
- LACP negotiation starts when partner sends PDUs
- All members transition to "Selected" state
- Fallback mode exits, normal LACP operation begins
- Traffic load-balances across all members

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp neighbor
show lacp interface PortChannel 7
```

---

#### TC_LACP_FALLBACK_003: LACP Fallback with Min-Links
**Objective**: Verify interaction between fallback and min-links

**Test Procedure**:
1. Configure PortChannel7 with fallback enabled and min-links 2
2. Add 4 members to PortChannel7
3. Bring partner side without LACP
4. Verify fallback activates with single member
5. Verify PortChannel7 operational state (may be down if min-links not met)
6. Enable LACP on partner and verify normal operation

**Expected Result**:
- Fallback activates with single member
- PortChannel7 state depends on min-links requirement
- If min-links > 1, PortChannel may be down despite fallback
- Normal operation resumes when LACP negotiated on sufficient members

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp interface PortChannel 7
show lacp fallback
```

---

#### TC_LACP_FALLBACK_004: Disable LACP Fallback
**Objective**: Verify disabling fallback configuration

**Test Procedure**:
1. Start with PortChannel7 having fallback enabled
2. Disable fallback on PortChannel7
3. Configure partner without LACP
4. Verify fallback does not activate
5. Verify PortChannel7 remains down without LACP negotiation

**Expected Result**:
- Fallback disabled in configuration
- PortChannel7 does not become operational without LACP
- No member ports in fallback state
- PortChannel requires LACP negotiation to be operational

**Verification Commands**:
```bash
show interface PortChannel 7
show running-config interface PortChannel 7
```

---

### Min-Links Tests

#### TC_LACP_MINLINKS_001: Configure Min-Links
**Objective**: Verify min-links configuration on port channel

**Test Procedure**:
1. Create PortChannel7 with 4 members
2. Configure min-links 2 on PortChannel7 (both DUTs)
3. Verify min-links configuration
4. Verify PortChannel7 operational with 4 members up
5. Check configuration in running-config

**Expected Result**:
- Min-links 2 configured successfully
- PortChannel7 operational with 4 active members
- Min-links value shown in `show interface PortChannel 7`

**Verification Commands**:
```bash
show interface PortChannel 7
show running-config interface PortChannel 7
```

---

#### TC_LACP_MINLINKS_002: Min-Links Threshold Met
**Objective**: Verify port channel operational when min-links threshold is met

**Test Procedure**:
1. Configure PortChannel7 with min-links 2 and 4 members
2. Bring up all 4 members
3. Verify PortChannel7 is operational (4 >= 2)
4. Shutdown 2 members (leaving 2 active)
5. Verify PortChannel7 remains operational (2 >= 2)
6. Verify traffic continues forwarding

**Expected Result**:
- PortChannel7 operational with 4 members (exceeds min-links)
- PortChannel7 remains operational with exactly 2 members
- Traffic forwards when min-links requirement met

**Verification Commands**:
```bash
show interface PortChannel 7
show interface status
```

---

#### TC_LACP_MINLINKS_003: Min-Links Threshold Not Met
**Objective**: Verify port channel goes down when min-links not met

**Test Procedure**:
1. Configure PortChannel7 with min-links 3 and 4 members
2. Bring up all 4 members, verify operational
3. Shutdown 2 members (leaving 2 active)
4. Verify PortChannel7 goes down (2 < 3)
5. Verify no traffic forwarding
6. Bring up 1 more member (total 3 active)
7. Verify PortChannel7 comes back up

**Expected Result**:
- PortChannel7 operational with 4 members
- PortChannel7 goes down when only 2 members active (< min-links 3)
- No traffic forwarding when min-links not met
- PortChannel7 recovers when min-links threshold met again

**Verification Commands**:
```bash
show interface PortChannel 7
show interface status
show lacp interface PortChannel 7
```

---

#### TC_LACP_MINLINKS_004: Modify Min-Links Value
**Objective**: Verify dynamic modification of min-links value

**Test Procedure**:
1. Configure PortChannel7 with min-links 2 and 4 members
2. Verify PortChannel7 operational
3. Change min-links to 4
4. Verify new min-links value applied
5. Shutdown 1 member
6. Verify PortChannel7 goes down (3 < 4)
7. Change min-links back to 2
8. Verify PortChannel7 comes back up (3 >= 2)

**Expected Result**:
- Min-links value modifiable on operational PortChannel
- PortChannel state changes based on new min-links value
- Configuration updates reflected in running-config

**Verification Commands**:
```bash
show interface PortChannel 7
show running-config interface PortChannel 7
```

---

#### TC_LACP_MINLINKS_005: Min-Links with Value 1
**Objective**: Verify min-links functionality with value 1

**Test Procedure**:
1. Configure PortChannel7 with min-links 1 and 4 members
2. Verify PortChannel7 operational with all members
3. Shutdown 3 members (leaving 1 active)
4. Verify PortChannel7 remains operational with single member
5. Verify traffic forwards through single member

**Expected Result**:
- PortChannel7 operational with single active member
- Traffic forwards through the one active member
- PortChannel provides redundancy as additional members can be added

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp interface PortChannel 7
```

---

### LACP Timer Tests

#### TC_LACP_TIMER_001: LACP Slow Rate (Default)
**Objective**: Verify LACP operation with slow rate (30-second timer)

**Test Procedure**:
1. Configure PortChannel7 with default timer (slow rate)
2. Add members and bring up port channel
3. Capture LACP PDU transmission timing
4. Verify LACP PDUs sent every 30 seconds
5. Verify LACP timeout is 90 seconds (3x slow rate)

**Expected Result**:
- LACP PDUs transmitted every 30 seconds
- LACP timeout period is 90 seconds
- Normal LACP operation with slow rate

**Verification Commands**:
```bash
show lacp neighbor
show lacp counters
show lacp interface PortChannel 7
```

---

#### TC_LACP_TIMER_002: LACP Fast Rate
**Objective**: Verify LACP operation with fast rate (1-second timer)

**Test Procedure**:
1. Configure PortChannel7 with fast_rate enabled
2. Add members and bring up port channel
3. Capture LACP PDU transmission timing
4. Verify LACP PDUs sent every 1 second
5. Verify LACP timeout is 3 seconds (3x fast rate)
6. Verify faster convergence on member failure

**Expected Result**:
- LACP PDUs transmitted every 1 second
- LACP timeout period is 3 seconds
- Faster failure detection and convergence
- Fast rate reflected in configuration

**Verification Commands**:
```bash
show lacp neighbor
show lacp counters
show lacp interface PortChannel 7
show running-config interface PortChannel 7
```

---

#### TC_LACP_TIMER_003: LACP Timer Convergence Test
**Objective**: Verify faster convergence with fast rate vs slow rate

**Test Procedure**:
1. Configure PortChannel7 with slow rate
2. Simulate member link failure
3. Measure time to detect failure and reconverge
4. Configure PortChannel7 with fast rate
5. Simulate member link failure
6. Measure time to detect failure and reconverge
7. Compare convergence times

**Expected Result**:
- Slow rate: ~90 seconds to detect failure
- Fast rate: ~3 seconds to detect failure
- Fast rate provides significantly faster convergence
- Traffic downtime reduced with fast rate

**Verification Commands**:
```bash
show lacp interface PortChannel 7
show lacp neighbor
```

---

#### TC_LACP_TIMER_004: Change LACP Rate Dynamically
**Objective**: Verify changing LACP rate on operational port channel

**Test Procedure**:
1. Configure PortChannel7 with slow rate (default)
2. Bring up port channel with members
3. Change to fast rate on PortChannel7
4. Verify LACP PDU rate changes to 1 second
5. Change back to slow rate
6. Verify LACP PDU rate changes to 30 seconds
7. Verify no disruption to port channel operation

**Expected Result**:
- LACP rate modifiable on operational PortChannel
- PDU transmission rate changes according to configuration
- No traffic disruption during rate change
- Both sides negotiate new rate

**Verification Commands**:
```bash
show lacp neighbor
show lacp counters
show running-config interface PortChannel 7
```

---

### Traffic Load Balancing Tests

#### TC_LACP_LOADBAL_001: L2 Hash - Source MAC
**Objective**: Verify traffic distribution based on source MAC address

**Test Procedure**:
1. Configure PortChannel7 with 4 members on both DUTs
2. Configure L2 hash mode with source MAC
3. Send traffic with 100 different source MACs, same destination MAC
4. Verify traffic distributed across members based on source MAC hash
5. Collect per-member traffic statistics

**Expected Result**:
- Traffic distributed across all 4 members
- Same source MAC always uses same member port
- Distribution follows hash algorithm
- All members carry traffic

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel 7
show mac address-table
```

---

#### TC_LACP_LOADBAL_002: L2 Hash - Destination MAC
**Objective**: Verify traffic distribution based on destination MAC address

**Test Procedure**:
1. Configure PortChannel7 with 4 members
2. Configure L2 hash mode with destination MAC
3. Send traffic with same source MAC, 100 different destination MACs
4. Verify traffic distributed across members based on dest MAC hash
5. Collect per-member traffic statistics

**Expected Result**:
- Traffic distributed across all 4 members
- Same destination MAC always uses same member port
- Distribution follows hash algorithm
- Approximately equal traffic distribution

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel 7
```

---

#### TC_LACP_LOADBAL_003: L2 Hash - Source and Destination MAC
**Objective**: Verify traffic distribution based on both source and dest MAC

**Test Procedure**:
1. Configure PortChannel7 with 4 members
2. Configure L2 hash mode with source + destination MAC
3. Send traffic with varied source and destination MAC pairs
4. Verify traffic distributed across members based on both MACs
5. Verify better distribution than single MAC hashing

**Expected Result**:
- Traffic distributed across all 4 members
- Hash considers both source and destination MAC
- Better traffic distribution granularity
- Same MAC pair uses same member consistently

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel 7
```

---

#### TC_LACP_LOADBAL_004: L3 Hash - Source IP
**Objective**: Verify L3 traffic distribution based on source IP address

**Test Procedure**:
1. Configure PortChannel7 with 4 members, add L3 configuration
2. Configure L3 hash mode with source IP
3. Send IP traffic with 1000 different source IPs, same destination IP
4. Verify traffic distributed across members based on source IP hash
5. Collect per-member traffic statistics

**Expected Result**:
- IP traffic distributed across all 4 members
- Same source IP always uses same member port
- Distribution follows hash algorithm
- L3 hash working correctly

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel 7
show ip route
```

---

#### TC_LACP_LOADBAL_005: L3 Hash - Destination IP
**Objective**: Verify L3 traffic distribution based on destination IP address

**Test Procedure**:
1. Configure PortChannel7 with 4 members, add L3 configuration
2. Configure L3 hash mode with destination IP
3. Send IP traffic with same source IP, 1000 different destination IPs
4. Verify traffic distributed across members based on dest IP hash
5. Collect per-member traffic statistics

**Expected Result**:
- IP traffic distributed across all 4 members
- Same destination IP always uses same member port
- Distribution follows hash algorithm
- Approximately equal traffic distribution

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel 7
```

---

#### TC_LACP_LOADBAL_006: L3 Hash - Source and Destination IP
**Objective**: Verify traffic distribution based on both source and dest IP

**Test Procedure**:
1. Configure PortChannel7 with 4 members, add L3 configuration
2. Configure L3 hash mode with source + destination IP
3. Send traffic with varied source and destination IP pairs
4. Verify traffic distributed across members based on both IPs
5. Verify better distribution than single IP hashing

**Expected Result**:
- Traffic distributed across all 4 members
- Hash considers both source and destination IP
- Better traffic distribution granularity
- Same IP pair uses same member consistently

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel 7
```

---

#### TC_LACP_LOADBAL_007: L4 Hash - Source and Destination Ports
**Objective**: Verify traffic distribution based on L4 port numbers

**Test Procedure**:
1. Configure PortChannel7 with 4 members, add L3 configuration
2. Configure hash mode including L4 ports
3. Send TCP/UDP traffic with varied source/destination port combinations
4. Verify traffic distributed across members based on L4 port hash
5. Collect per-member traffic statistics

**Expected Result**:
- Traffic distributed across all 4 members
- Hash considers L4 source and destination ports
- Excellent traffic distribution for multiple flows
- Same 5-tuple uses same member consistently

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel 7
```

---

#### TC_LACP_LOADBAL_008: Verify Load Balancing with Member Failure
**Objective**: Verify traffic redistribution when member fails

**Test Procedure**:
1. Configure PortChannel7 with 4 members
2. Send continuous traffic distributed across all members
3. Shutdown one member port
4. Verify traffic redistributes to remaining 3 members
5. Verify no traffic loss after redistribution
6. Bring up failed member
7. Verify traffic redistributes to include recovered member

**Expected Result**:
- Traffic initially distributed across 4 members
- On member failure, traffic redistributes to 3 members
- Minimal packet loss during transition
- Traffic rebalances when member recovers
- Hash recalculation maintains flow affinity

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel 7
show interface status
```

---

### System Configuration Tests

#### TC_LACP_SYSTEM_001: Configure System MAC Address
**Objective**: Verify custom system MAC configuration for LAG

**Test Procedure**:
1. Configure PortChannel7 on DUT1
2. Configure custom system MAC address on PortChannel7
3. Verify system MAC configuration applied
4. Configure PortChannel7 on DUT2
5. Verify LACP negotiation uses configured system MAC
6. Check LACP neighbor shows correct system MAC

**Expected Result**:
- Custom system MAC configured successfully
- LACP uses configured system MAC in PDUs
- LACP neighbor shows configured system MAC
- Configuration persists in running-config

**Verification Commands**:
```bash
show lacp interface PortChannel 7
show lacp neighbor
show running-config interface PortChannel 7
```

---

#### TC_LACP_SYSTEM_002: System Priority Configuration
**Objective**: Verify LACP system priority configuration

**Test Procedure**:
1. Configure PortChannel7 with default system priority
2. Verify default system priority value (32768)
3. Configure custom system priority (e.g., 100)
4. Verify LACP negotiation with new priority
5. Check LACP neighbor shows correct system priority

**Expected Result**:
- Default system priority is 32768
- Custom system priority configured successfully
- LACP uses configured priority in negotiation
- Priority affects LAG selection in multi-LAG scenarios

**Verification Commands**:
```bash
show lacp interface PortChannel 7
show lacp neighbor
```

---

#### TC_LACP_SYSTEM_003: Port Priority Configuration
**Objective**: Verify LACP port priority configuration

**Test Procedure**:
1. Configure PortChannel7 with 4 members
2. Set different port priorities on each member
3. Verify port priority configuration
4. Configure min-links 2
5. Verify higher priority ports selected first
6. Check LACP port selection based on priority

**Expected Result**:
- Port priorities configured successfully
- Higher priority ports selected when not all members needed
- Port selection follows priority order
- Configuration reflected in LACP state

**Verification Commands**:
```bash
show lacp interface PortChannel 7
show lacp neighbor
```

---

#### TC_LACP_SYSTEM_004: MTU Configuration on Port Channel
**Objective**: Verify MTU configuration on LAG interface

**Test Procedure**:
1. Configure PortChannel7 with members
2. Set MTU 9000 on PortChannel7
3. Verify MTU applied to PortChannel and members
4. Send jumbo frames (9000 bytes) through PortChannel
5. Verify jumbo frames forwarded successfully

**Expected Result**:
- MTU 9000 configured on PortChannel7
- Member interfaces inherit MTU setting
- Jumbo frames forwarded without fragmentation
- MTU mismatch detected if partner has different MTU

**Verification Commands**:
```bash
show interface PortChannel 7
show interface Ethernet0
```

---

#### TC_LACP_SYSTEM_005: Description Configuration
**Objective**: Verify description field on port channel interface

**Test Procedure**:
1. Configure PortChannel7
2. Add description "Test LAG for Validation"
3. Verify description shown in interface output
4. Modify description
5. Verify updated description
6. Remove description
7. Verify description removed

**Expected Result**:
- Description configured successfully
- Description displayed in `show interface PortChannel`
- Description modifiable
- Description persists in running-config

**Verification Commands**:
```bash
show interface PortChannel 7
show running-config interface PortChannel 7
```

---

### Negative Test Scenarios

#### TC_LACP_NEG_001: Add Member Already in Another LAG
**Objective**: Verify error when adding member already in different LAG

**Test Procedure**:
1. Configure PortChannel7 with member D1D2P1 (Ethernet20 on D1)
2. Configure PortChannel8
3. Attempt to add same member (Ethernet20) to PortChannel8
4. Verify operation fails with appropriate error
5. Verify member remains in PortChannel7 only

**Expected Result**:
- Error message indicating port already in LAG
- Operation rejected by system
- Member remains in PortChannel7 only
- System integrity maintained

**Verification Commands**:
```bash
show interface PortChannel 7
show interface PortChannel 8
show interface Ethernet20  # on D1
```

---

#### TC_LACP_NEG_002: Delete Port Channel with Members
**Objective**: Verify behavior when deleting LAG without removing members first

**Test Procedure**:
1. Configure PortChannel7 with 4 members
2. Attempt to delete PortChannel7 without removing members
3. Verify operation handling (error or auto-removal of members)
4. Check system behavior and error messages

**Expected Result**:
- System either rejects deletion or auto-removes members
- Appropriate warning/error message displayed
- If deletion succeeds, members return to standalone state
- No configuration inconsistency

**Verification Commands**:
```bash
show interface PortChannel
show interface status
show running-config
```

---

#### TC_LACP_NEG_003: Invalid Port Channel ID
**Objective**: Verify error handling for invalid PortChannel ID

**Test Procedure**:
1. Attempt to create PortChannel with ID 0
2. Attempt to create PortChannel with ID > maximum allowed
3. Attempt to create PortChannel with alphabetic characters
4. Verify all operations fail with appropriate errors

**Expected Result**:
- Invalid IDs rejected with error messages
- Valid ID range documented in error message
- No PortChannel created with invalid ID
- System remains stable

**Verification Commands**:
```bash
show interface PortChannel
```

---

#### TC_LACP_NEG_004: Min-Links Greater Than Member Count
**Objective**: Verify behavior when min-links exceeds number of members

**Test Procedure**:
1. Configure PortChannel7 with 2 members
2. Attempt to set min-links to 4
3. Verify configuration accepted but PortChannel stays down
4. Verify appropriate status indication
5. Add more members to meet min-links
6. Verify PortChannel comes up when requirement met

**Expected Result**:
- Min-links configuration accepted
- PortChannel remains down (insufficient members)
- Clear indication of reason for down state
- PortChannel becomes operational when min-links met

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp interface PortChannel 7
```

---

#### TC_LACP_NEG_005: LACP Mode Mismatch
**Objective**: Verify detection of LACP mode mismatch between partners

**Test Procedure**:
1. Configure PortChannel7 on DUT1 with LACP mode (active)
2. Configure PortChannel7 on DUT2 with static mode (on)
3. Verify LACP negotiation fails
4. Verify PortChannel remains down
5. Check for mode mismatch indication

**Expected Result**:
- LACP negotiation fails due to mode mismatch
- PortChannel remains down on both sides
- Error/warning indication of mode mismatch
- Members show as "Unselected" or "Standby"

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp neighbor
show lacp interface PortChannel 7
```

---

#### TC_LACP_NEG_006: Add Incompatible Interface Types
**Objective**: Verify error when mixing incompatible interface types in LAG

**Test Procedure**:
1. Configure PortChannel7 with Ethernet20 (physical port on D1)
2. Attempt to add management port to PortChannel7
3. Verify operation rejected
4. Attempt to add VLAN interface to PortChannel7
5. Verify operation rejected

**Expected Result**:
- Incompatible interface types rejected
- Appropriate error messages displayed
- Only compatible interfaces can be LAG members
- PortChannel remains functional with valid members

**Verification Commands**:
```bash
show interface PortChannel 7
```

---

#### TC_LACP_NEG_007: Shutdown Port Channel Interface
**Objective**: Verify behavior when PortChannel interface is shutdown

**Test Procedure**:
1. Configure PortChannel7 with 4 members, all operational
2. Shutdown PortChannel7 interface (not individual members)
3. Verify PortChannel goes down
4. Verify member links remain physically up
5. Verify no traffic forwarding
6. No-shutdown PortChannel7
7. Verify PortChannel and traffic resume

**Expected Result**:
- Shutdown applies to logical PortChannel interface
- Member ports remain physically up
- No traffic forwarding when PortChannel shutdown
- PortChannel recovers when brought up again
- LACP PDUs may still be exchanged (implementation-dependent)

**Verification Commands**:
```bash
show interface PortChannel 7
show interface status
show lacp interface PortChannel 7
```

---

#### TC_LACP_NEG_008: Fallback on Static LAG
**Objective**: Verify fallback not applicable to static LAG

**Test Procedure**:
1. Configure PortChannel7 with static mode (on)
2. Attempt to enable fallback on PortChannel7
3. Verify configuration rejected or ignored
4. Verify appropriate error message

**Expected Result**:
- Fallback configuration rejected on static LAG
- Error message indicating fallback requires LACP mode
- Static LAG operates without fallback
- Configuration consistency maintained

**Verification Commands**:
```bash
show interface PortChannel 7
show running-config interface PortChannel 7
```

---

#### TC_LACP_NEG_009: Invalid Min-Links Value
**Objective**: Verify error handling for invalid min-links values

**Test Procedure**:
1. Attempt to configure min-links 0 on PortChannel7
2. Verify operation rejected
3. Attempt to configure negative min-links value
4. Verify operation rejected
5. Attempt to configure non-numeric min-links
6. Verify operation rejected

**Expected Result**:
- Invalid min-links values rejected
- Appropriate error messages
- Valid range documented in error
- PortChannel remains in valid state

**Verification Commands**:
```bash
show interface PortChannel 7
```

---

#### TC_LACP_NEG_010: Duplicate Port Channel Creation
**Objective**: Verify error when creating already existing PortChannel

**Test Procedure**:
1. Configure PortChannel7
2. Attempt to create PortChannel7 again
3. Verify operation rejected or idempotent
4. Verify appropriate message
5. Verify existing PortChannel7 unaffected

**Expected Result**:
- Duplicate creation rejected or treated as no-op
- Appropriate message displayed
- Existing PortChannel7 configuration unchanged
- No system instability

**Verification Commands**:
```bash
show interface PortChannel 7
show running-config interface PortChannel 7
```

---

### Scaling Test Scenarios

#### TC_LACP_SCALE_001: Maximum Port Channels
**Objective**: Verify system supports maximum number of port channels

**Test Procedure**:
1. Determine maximum PortChannel limit for platform
2. Create maximum number of PortChannels (e.g., PortChannel1-128)
3. Verify all PortChannels created successfully
4. Add at least one member to each PortChannel
5. Verify all PortChannels operational
6. Check system resource utilization

**Expected Result**:
- All PortChannels up to maximum created successfully
- System operates stably with maximum PortChannels
- Resource utilization within acceptable limits
- No performance degradation

**Verification Commands**:
```bash
show interface PortChannel
show interface summary
show system resources
```

---

#### TC_LACP_SCALE_002: Maximum Members per Port Channel
**Objective**: Verify maximum members supported per port channel

**Test Procedure**:
1. Determine maximum members per LAG for platform
2. Configure PortChannel7
3. Add maximum number of members (typically 8, 16, 32, or 64)
4. Verify all members added successfully
5. Verify PortChannel operational with all members
6. Verify traffic load-balances across all members

**Expected Result**:
- Maximum members added successfully to single PortChannel
- All members operational in LAG
- Traffic distributes across all members
- LACP operates correctly with maximum members

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp interface PortChannel 7
show interfaces counters
```

---

#### TC_LACP_SCALE_003: Multiple LAGs with Multiple Members
**Objective**: Verify multiple LAGs with multiple members each

**Test Procedure**:
1. Create 8 PortChannels (PortChannel1-8)
2. Add 4 members to each PortChannel (32 total ports)
3. Verify all PortChannels operational
4. Configure L3 on all PortChannels
5. Send traffic through all LAGs simultaneously
6. Verify traffic forwarding on all LAGs
7. Check system performance and stability

**Expected Result**:
- All 8 PortChannels operational with 4 members each
- Traffic forwards correctly through all LAGs
- No performance degradation
- System resources within limits
- LACP operates correctly on all LAGs

**Verification Commands**:
```bash
show interface PortChannel
show lacp neighbor
show interfaces counters
show system resources
```

---

#### TC_LACP_SCALE_004: High Traffic Load Across Multiple LAGs
**Objective**: Verify system performance with high traffic load

**Test Procedure**:
1. Configure multiple LAGs (4-8 LAGs)
2. Send line-rate traffic through each LAG
3. Monitor traffic distribution across members
4. Check for packet loss
5. Monitor system CPU and memory utilization
6. Verify LACP PDUs continue exchanging
7. Run for extended duration (10+ minutes)

**Expected Result**:
- Line-rate traffic forwarding on all LAGs
- Minimal/zero packet loss
- Traffic distributes across LAG members
- LACP remains stable under load
- System resources stable
- No protocol flapping

**Verification Commands**:
```bash
show interfaces counters
show interface PortChannel
show lacp counters
show system cpu
show system memory
```

---

#### TC_LACP_SCALE_005: LAG Member Churn
**Objective**: Verify system stability with frequent member add/remove

**Test Procedure**:
1. Configure PortChannel7 with 4 members
2. Continuously add and remove members in loop (50 iterations)
3. Monitor PortChannel state transitions
4. Check for memory leaks or resource exhaustion
5. Verify final configuration matches expected
6. Check system logs for errors

**Expected Result**:
- PortChannel handles member churn gracefully
- State transitions correct for each add/remove
- No memory leaks detected
- System remains stable
- Final configuration correct
- No unexpected errors in logs

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp interface PortChannel 7
show system resources
show logging
```

---

#### TC_LACP_SCALE_006: LAG with VLANs
**Objective**: Verify LAG operation with multiple VLANs

**Test Procedure**:
1. Configure PortChannel7 with 4 members
2. Create 100 VLANs (VLAN 100-199)
3. Add PortChannel7 as tagged member to all 100 VLANs
4. Verify PortChannel operational with all VLANs
5. Send tagged traffic for different VLANs
6. Verify traffic forwarding for all VLANs
7. Verify load balancing includes VLAN tag in hash

**Expected Result**:
- PortChannel operational with 100 VLANs
- Tagged traffic forwards correctly for all VLANs
- Load balancing works across members
- VLAN tag considered in hash distribution
- No performance issues

**Verification Commands**:
```bash
show vlan brief
show interface PortChannel 7
show interfaces counters
show mac address-table
```

---

#### TC_LACP_SCALE_007: Multiple LAG Flaps
**Objective**: Verify system stability with multiple LAG flaps

**Test Procedure**:
1. Configure multiple PortChannels (8 LAGs)
2. Bring all LAGs up
3. Shutdown and no-shutdown all LAGs simultaneously (20 iterations)
4. Monitor LAG state transitions
5. Check LACP reconvergence time
6. Verify all LAGs return to operational state
7. Check system resources and logs

**Expected Result**:
- All LAGs handle flapping correctly
- State transitions clean for each flap
- LACP reconverges after each flap
- No resource leaks
- System remains stable
- All LAGs operational after test

**Verification Commands**:
```bash
show interface PortChannel
show lacp interface PortChannel
show system resources
show logging
```

---

#### TC_LACP_SCALE_008: LAG with L3 Subinterfaces
**Objective**: Verify LAG with multiple L3 subinterfaces (802.1Q)

**Test Procedure**:
1. Configure PortChannel7 with 4 members
2. Create 50 subinterfaces on PortChannel7 (PortChannel7.100-149)
3. Configure IP address on each subinterface
4. Verify all subinterfaces operational
5. Send traffic to different subinterfaces
6. Verify routing and forwarding through LAG subinterfaces

**Expected Result**:
- 50 subinterfaces created successfully on LAG
- All subinterfaces operational
- IP routing works through LAG subinterfaces
- Traffic load-balances across LAG members
- No performance degradation

**Verification Commands**:
```bash
show interface PortChannel 7
show ip interface
show ip route
show interfaces counters
```

---

### Interoperability Tests

#### TC_LACP_INTEROP_001: SONiC to SONiC LACP
**Objective**: Verify LACP interoperability between SONiC devices

**Test Procedure**:
1. Configure PortChannel7 on DUT1 (SONiC)
2. Configure PortChannel7 on DUT2 (SONiC)
3. Add members to both sides
4. Verify LACP negotiation succeeds
5. Verify full interoperability
6. Test various LACP features (fallback, min-links, fast rate)

**Expected Result**:
- LACP negotiation successful between SONiC devices
- All LACP features work correctly
- Traffic forwards bidirectionally
- Full protocol compatibility

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp neighbor
show lacp interface PortChannel 7
```

---

#### TC_LACP_INTEROP_002: SONiC to Third-Party Vendor
**Objective**: Verify LACP interoperability with third-party devices

**Test Procedure**:
1. Configure PortChannel on SONiC DUT
2. Configure LAG on third-party device (e.g., Cisco, Arista)
3. Add members to both sides
4. Verify LACP negotiation succeeds
5. Test basic LACP features
6. Verify traffic forwarding

**Expected Result**:
- LACP negotiation successful with third-party device
- Basic LACP features work
- Traffic forwards bidirectionally
- Protocol interoperability confirmed

**Verification Commands**:
```bash
show interface PortChannel 7
show lacp neighbor
show lacp interface PortChannel 7
```

---

#### TC_LACP_INTEROP_003: Mixed Fast/Slow Rate Negotiation
**Objective**: Verify LACP negotiation with different timer rates

**Test Procedure**:
1. Configure PortChannel7 on DUT1 with fast rate
2. Configure PortChannel7 on DUT2 with slow rate (default)
3. Verify LACP negotiation succeeds
4. Verify negotiated rate (should use slower of the two)
5. Check LACP PDU exchange rate

**Expected Result**:
- LACP negotiation succeeds despite rate mismatch
- System negotiates to compatible rate
- Typically slower rate used for compatibility
- Both sides communicate successfully

**Verification Commands**:
```bash
show lacp neighbor
show lacp interface PortChannel 7
show lacp counters
```

---

#### TC_LACP_INTEROP_004: Different System Priority
**Objective**: Verify LACP operation with different system priorities

**Test Procedure**:
1. Configure PortChannel7 on DUT1 with system priority 100
2. Configure PortChannel7 on DUT2 with system priority 200
3. Verify LACP negotiation succeeds
4. Verify higher priority system takes precedence in selection
5. Check LACP state reflects priorities

**Expected Result**:
- LACP negotiation successful with different priorities
- System priorities affect LAG selection logic
- Protocol operates correctly
- Higher priority system has preference

**Verification Commands**:
```bash
show lacp interface PortChannel 7
show lacp neighbor
```

---

#### TC_LACP_INTEROP_005: MTU Mismatch Detection
**Objective**: Verify detection of MTU mismatch across LAG

**Test Procedure**:
1. Configure PortChannel7 on both DUTs
2. Set MTU 9000 on DUT1 PortChannel7
3. Set MTU 1500 on DUT2 PortChannel7
4. Verify LACP negotiation status
5. Send packets of different sizes
6. Verify MTU mismatch detection/handling

**Expected Result**:
- MTU mismatch detected
- Warning/error indication of mismatch
- LACP may still negotiate but with warnings
- Packets larger than minimum MTU may be dropped
- System indicates configuration issue

**Verification Commands**:
```bash
show interface PortChannel 7
show logging | grep MTU
```

---

## Test Summary

### Total Test Case Count

| **Category**                      | **Test Cases** | **Test IDs**                  |
|-----------------------------------|----------------|-------------------------------|
| Basic Functionality Tests         | 5              | TC_LACP_BASIC_001 to 005      |
| LACP Mode Tests                   | 4              | TC_LACP_MODE_001 to 004       |
| LACP Fallback Tests               | 4              | TC_LACP_FALLBACK_001 to 004   |
| Min-Links Tests                   | 5              | TC_LACP_MINLINKS_001 to 005   |
| LACP Timer Tests                  | 4              | TC_LACP_TIMER_001 to 004      |
| Traffic Load Balancing Tests      | 8              | TC_LACP_LOADBAL_001 to 008    |
| System Configuration Tests        | 5              | TC_LACP_SYSTEM_001 to 005     |
| Negative Test Scenarios           | 10             | TC_LACP_NEG_001 to 010        |
| Scaling Test Scenarios            | 8              | TC_LACP_SCALE_001 to 008      |
| Interoperability Tests            | 5              | TC_LACP_INTEROP_001 to 005    |
| **TOTAL**                         | **58**         | -                             |

### Test Distribution

```
┌──────────────────────────────────────────────┐
│         Test Case Distribution               │
├──────────────────────────────────────────────┤
│                                              │
│  Basic Functionality    [████] 5 (9%)        │
│  LACP Mode Tests        [███] 4 (7%)         │
│  LACP Fallback          [███] 4 (7%)         │
│  Min-Links Tests        [████] 5 (9%)        │
│  LACP Timer Tests       [███] 4 (7%)         │
│  Load Balancing         [███████] 8 (14%)    │
│  System Configuration   [████] 5 (9%)        │
│  Negative Scenarios     [████████] 10 (17%)  │
│  Scaling Scenarios      [███████] 8 (14%)    │
│  Interoperability       [████] 5 (9%)        │
│                                              │
└──────────────────────────────────────────────┘
```

### Test Execution Strategy

#### Phase 1: Core Functionality (Priority: High)
- Basic Functionality Tests (5 tests)
- LACP Mode Tests (4 tests)
- Min-Links Tests (5 tests)
- **Total: 14 tests**

#### Phase 2: Advanced Features (Priority: High)
- LACP Fallback Tests (4 tests)
- LACP Timer Tests (4 tests)
- System Configuration Tests (5 tests)
- **Total: 13 tests**

#### Phase 3: Traffic and Performance (Priority: Medium)
- Traffic Load Balancing Tests (8 tests)
- Scaling Test Scenarios (8 tests)
- **Total: 16 tests**

#### Phase 4: Robustness and Compatibility (Priority: Medium)
- Negative Test Scenarios (10 tests)
- Interoperability Tests (5 tests)
- **Total: 15 tests**

### Success Criteria

#### Functional Requirements
- [ ] 100% pass rate for Basic Functionality tests
- [ ] 100% pass rate for LACP Mode tests
- [ ] 90%+ pass rate for all feature-specific tests
- [ ] All negative scenarios handle errors gracefully
- [ ] No system crashes or hangs during testing

#### Performance Requirements
- [ ] Line-rate traffic forwarding through LAGs
- [ ] < 3 seconds convergence time with fast rate
- [ ] < 90 seconds convergence time with slow rate
- [ ] Equal traffic distribution across LAG members (±5%)
- [ ] No packet loss during steady-state operation

#### Scaling Requirements
- [ ] Support platform maximum number of LAGs
- [ ] Support platform maximum members per LAG
- [ ] Stable operation under maximum configuration
- [ ] Resource utilization within acceptable limits

#### Interoperability Requirements
- [ ] 100% compatibility with SONiC to SONiC
- [ ] Basic LACP interoperability with third-party vendors
- [ ] Proper handling of feature mismatches

### Test Environment Setup

#### Prerequisites
```bash
# Install SPyTest framework
cd /path/to/sonic-mgmt/spytest
./bin/upgrade_requirements.sh

# Verify testbed connectivity (replace with your testbed file)
./bin/spytest --testbed testbeds/your_testbed.yaml --test-suite validation
```

#### Running Tests
```bash
# Run all LACP tests (replace with your testbed file)
./bin/spytest --testbed testbeds/your_testbed.yaml \
    tests/LACP/ \
    --logs-path ./logs/lacp_$(date +%F_%H%M%S) \
    --log-level debug --skip-init-config --ifname-type native

# Run specific test category
./bin/spytest --testbed testbeds/your_testbed.yaml \
    tests/LACP/test_lacp_basic.py \
    --logs-path ./logs/lacp_basic

# Run by test marker
./bin/spytest --testbed testbeds/your_testbed.yaml \
    -m lacp_sanity \
    --logs-path ./logs/lacp_sanity
```

### Test Reporting

#### Report Structure
Each test execution generates:
- **results.html**: Detailed test results with pass/fail status
- **dashboard.html**: High-level overview and statistics
- **summary.txt**: Quick text summary
- **dlog-D1-*.log**: Per-device command logs
- **module_*.log**: Per-module execution logs

#### Key Metrics Tracked
1. **Pass Rate**: Percentage of passed tests
2. **Execution Time**: Total and per-test execution time
3. **Coverage**: Feature coverage percentage
4. **Defect Density**: Bugs found per test
5. **System Stability**: Crashes, hangs, resource leaks

### Risk Assessment

#### High Risk Areas
- Scaling tests with maximum configuration
- High traffic load tests
- Member churn tests
- Negative scenarios (configuration errors)

#### Mitigation Strategies
- Incremental testing approach
- Comprehensive logging and monitoring
- Automated test environment recovery
- Regular test environment validation

### Dependencies

#### Framework Dependencies
- SPyTest framework
- Scapy for packet generation
- Python 3.8+
- Ansible for device orchestration

#### Device Dependencies
- SONiC image with LACP support
- Minimum 4 interconnected ports
- Traffic generator support

#### API Dependencies
- `apis/switching/portchannel.py`
- `apis/system/interface.py`
- `apis/switching/vlan.py`
- `apis/routing/ip.py`

---

## Appendix

### LACP Protocol Overview

**IEEE 802.3ad / 802.1AX** - Link Aggregation Control Protocol

**Key Concepts:**
- **Actor**: Local system sending LACP PDUs
- **Partner**: Remote system receiving LACP PDUs
- **Actor System ID**: MAC address + system priority
- **Port Key**: Identifies ports that can aggregate together
- **Port State**: Aggregatable, Synchronized, Collecting, Distributing

**LACP PDU Format:**
- Subtype: 0x01 (LACP)
- Version: 0x01
- Actor Information TLV
- Partner Information TLV
- Collector Information TLV

**State Machine:**
```
┌─────────┐      LACP PDU Received       ┌─────────┐
│ Initial │ ───────────────────────────► │ Current │
└─────────┘                              └─────────┘
     │                                        │
     │ Timeout                                │ Synchronized
     ▼                                        ▼
┌─────────┐                              ┌─────────┐
│ Expired │ ◄───────────────────────────│Selected │
└─────────┘     Timeout / Mismatch      └─────────┘
```

### CLI Reference

#### Show Commands
```bash
# Display all PortChannels
show interface PortChannel

# Display specific PortChannel
show interface PortChannel 7

# Display LACP neighbor information
show lacp neighbor

# Display LACP interface details
show lacp interface PortChannel 7

# Display LACP counters
show lacp counters

# Display LACP fallback status
show lacp fallback

# Display interface status
show interface status
```

#### Configuration Commands (Klish)
```bash
# Create PortChannel
interface PortChannel 7

# Set LACP mode
interface PortChannel 7 mode active

# Enable fallback
interface PortChannel 7 fallback

# Set min-links
interface PortChannel 7 min-links 2

# Enable fast rate
interface PortChannel 7 fast_rate

# Add member to PortChannel (D1 example)
interface Ethernet20
  channel-group 7 mode active

# Add multiple members (D1 example)
interface Ethernet16
  channel-group 7 mode active
interface Ethernet8
  channel-group 7 mode active
interface Ethernet12
  channel-group 7 mode active
```

#### Configuration Commands (Click)
```bash
# Create PortChannel
config portchannel add PortChannel7

# Add members (D1 example - use corresponding ports on D2: Ethernet24, Ethernet20, Ethernet8, Ethernet16)
config portchannel member add PortChannel7 Ethernet20
config portchannel member add PortChannel7 Ethernet16
config portchannel member add PortChannel7 Ethernet8
config portchannel member add PortChannel7 Ethernet12

# Remove member
config portchannel member del PortChannel7 Ethernet20

# Delete PortChannel
config portchannel del PortChannel7

# Create PortChannel with fallback
config portchannel add PortChannel7 --fallback=true --min-links 1

# Create static PortChannel
config portchannel add PortChannel7 --static=true
```

### Troubleshooting Guide

#### Common Issues

**Issue 1: PortChannel Not Coming Up**
- Check LACP mode compatibility (both passive not supported)
- Verify member interfaces are up
- Check LACP PDU exchange with `show lacp neighbor`
- Verify no configuration mismatch

**Issue 2: Member Not Joining LAG**
- Verify member not already in another LAG
- Check interface status (`show interface status`)
- Verify compatible interface type
- Check port key matching

**Issue 3: Traffic Not Load Balancing**
- Check hash configuration
- Verify all members in "Selected" state
- Test with varied traffic patterns (different IPs/MACs)
- Check per-interface counters

**Issue 4: LACP Flapping**
- Check for physical layer issues
- Verify LACP timer configuration
- Check for configuration changes
- Review system logs for errors

### References

1. **IEEE 802.3ad-2000**: Link Aggregation Standard
2. **IEEE 802.1AX-2008**: Link Aggregation (updated standard)
3. **RFC 7275**: LACP MIB
4. **SONiC Documentation**: https://github.com/sonic-net/SONiC/wiki
5. **SPyTest Documentation**: Doc/intro.md

---

**Document Version**: 1.0
**Last Updated**: 2026-03-05
**Author**: Test Team
**Review Status**: Draft
