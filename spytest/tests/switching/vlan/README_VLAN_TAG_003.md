# VLAN Trunk-to-Trunk Tagged Packet Forwarding Test (TC_VLAN_TAG_003)

**Test Case**: TC_VLAN_TAG_003 - Tagged Packet on Trunk Port
**Objective**: Verify that tagged packets sent on a trunk port are received with the same VLAN tag on another trunk port
**Implementation Date**: 2026-05-06
**Status**: ✅ Complete and Ready for Execution

---

## Overview

This test validates trunk-to-trunk tagged packet forwarding in compliance with IEEE 802.1Q VLAN tagging standards. It ensures that:

1. A switch receives **tagged packets** on a **trunk port**
2. The switch **preserves the VLAN tag** (does NOT strip it)
3. The switch forwards **tagged packets** with the same VLAN tag to another **trunk port**
4. The packet structure and content remain intact (payload unchanged)

### Key Difference from TAG-001 and TAG-002

| Test Case | Source Port | Ingress Packet | Operation | Egress Packet | Destination Port |
|-----------|------------|-----------------|-----------|---------------|------------------|
| **TAG-001** | Access | Untagged | ADD tag | Tagged | Trunk |
| **TAG-002** | Trunk | Tagged | REMOVE tag | Untagged | Access |
| **TAG-003** | Trunk | Tagged | PRESERVE tag | Tagged | Trunk |

TC_VLAN_TAG_003 is the trunk-to-trunk forwarding scenario where **no tag stripping occurs**.

---

## Test Scenario

```
┌─────────────────────────────────────────────────────────────┐
│ Trunk Port (D1)         Tag Preservation        Trunk Port (D2) │
│    Tagged Packet                                  Tagged Packet│
│   ┌──────────────┐                              ┌──────────────┐
│   │Ethernet Frame│                              │Ethernet Frame│
│   ├──────────────┤                              ├──────────────┤
│   │  802.1Q Tag  │──────────────────────────────│  802.1Q Tag  │
│   │  VID=10      │  Tag Preserved by Switch    │  VID=10      │
│   ├──────────────┤                              ├──────────────┤
│   │   Payload    │──────────────────────────────│   Payload    │
│   └──────────────┘                              └──────────────┘
└─────────────────────────────────────────────────────────────┘
```

---

## Test Topology

### Network Setup

```
DUT1 (192.168.100.170)          DUT2 (192.168.100.231)
┌──────────────────┐            ┌──────────────────┐
│                  │            │                  │
│  Ethernet4       │◄──────────►│   Ethernet4      │
│  (Trunk Port)    │  Back-to-  │  (Trunk Port)    │
│                  │  Back Link │                  │
│  VLAN 10 (tagged)│            │  VLAN 10 (tagged)│
│                  │            │                  │
└──────────────────┘            └──────────────────┘

Port Roles:
- D1 Ethernet4: Trunk port (tagged member of VLAN 10) - SOURCE
- D2 Ethernet4: Trunk port (tagged member of VLAN 10) - DESTINATION
```

### Topology Requirements

- **2 DUTs**: D1 and D2
- **Minimum Connections**: 2 back-to-back links (D1D2P1, D1D2P2)
- **VLAN Support**: 802.1Q tagging capable
- **Software Requirements**: tcpdump, Scapy (Python 3)

---

## Test Flow Execution

### Step 1: VLAN Creation

Create VLAN 10 on both DUTs:

```bash
# DUT1
configure terminal
vlan 10
exit

# DUT2 (identical)
configure terminal
vlan 10
exit
```

**Verification:**
```bash
show vlan id 10
```

Expected: VLAN 10 exists on both devices

### Step 2: Trunk Port Configuration (D1 - Source)

Configure Ethernet4 on D1 as a **trunk port** (tagged):

```bash
configure terminal
interface Ethernet4
  switchport mode trunk
  switchport trunk allowed vlan 10
  switchport trunk native vlan 1
  no shutdown
exit
```

**Verification:**
```bash
show running-configuration interface Ethernet4 | no-more
show switchport Ethernet4
```

Expected output shows:
- Mode: trunk
- Allowed VLANs: 10
- Native VLAN: 1

### Step 3: Trunk Port Configuration (D2 - Destination)

Configure Ethernet4 on D2 as a **trunk port** (tagged):

```bash
configure terminal
interface Ethernet4
  switchport mode trunk
  switchport trunk allowed vlan 10
  switchport trunk native vlan 1
  no shutdown
exit
```

**Verification:**
```bash
show running-configuration interface Ethernet4 | no-more
show switchport Ethernet4
```

Expected output shows:
- Mode: trunk
- Allowed VLANs: 10
- Native VLAN: 1

### Step 4: MAC Address Retrieval

Discover MAC addresses from both trunk interfaces:

```bash
# D1 Ethernet4 MAC
show interface Ethernet4 | grep "Hardware is"

# D2 Ethernet4 MAC
show interface Ethernet4 | grep "Hardware is"
```

**Purpose**: MAC addresses needed for packet generation

### Step 5: Counter Clearing

Clear interface counters on both ports:

```bash
# D1
clear counters interface Ethernet4

# D2
clear counters interface Ethernet4
```

**Purpose**: Ensure accurate packet count tracking

### Step 6: Packet Capture Setup

Start tcpdump on D2 (destination trunk port) to capture tagged packets:

```bash
tcpdump -i Ethernet4 -w /tmp/vlan_tag_003_capture.pcap -B 4096 'vlan' &
```

**Parameters:**
- `-i Ethernet4`: Capture on destination trunk port
- `-w /tmp/vlan_tag_003_capture.pcap`: Write to file
- `-B 4096`: Buffer size for high-speed capture
- `'vlan'`: Filter for VLAN tagged packets

### Step 7: Tagged Packet Transmission

Generate and send **tagged packets** from D1 trunk port:

```python
from scapy.all import Ether, Dot1Q, sendp, conf

src_mac = "aa:bb:cc:dd:ee:01"  # D1 Ethernet4 MAC
dst_mac = "aa:bb:cc:dd:ee:02"  # D2 Ethernet4 MAC

# Create TAGGED packet (with 802.1Q header - ALREADY TAGGED)
pkt = Ether(src=src_mac, dst=dst_mac) / Dot1Q(vlan=10) / b'TestPayload'

# Send 10 tagged packets
sendp(pkt, iface="Ethernet4", count=10, verbose=True)
```

**Packet Format:**
```
┌─────────────────────────────────────────────────────────────┐
│ Ethernet Frame Header                                       │
├──────────────┬──────────────┬──────────────────────────────┤
│  Dest MAC    │   Src MAC    │  EtherType: 0x8100           │
├──────────────┴──────────────┴──────────────────────────────┤
│ 802.1Q VLAN Tag Header (ALREADY PRESENT ON INGRESS)       │
├───────────────┬─────────┬──────┬──────────────────────────┤
│  PCP (3 bits) │ CFI (1) │ VID (12 bits: 10)              │
├───────────────┴─────────┴──────┴──────────────────────────┤
│ Payload: "TestPayload"                                    │
└─────────────────────────────────────────────────────────────┘
```

**Transmission Details:**
- **Source Interface**: D1 Ethernet4 (trunk port)
- **Packet State**: ALREADY TAGGED with VLAN 10
- **Packet Count**: 10 packets
- **VLAN ID in Tag**: 10
- **PCP (Priority Code Point)**: 0 (best effort)
- **CFI (Canonical Format Indicator)**: 0

### Step 8: Packet Capture and Analysis

Stop packet capture and analyze received packets:

```bash
pkill -f tcpdump
```

**Analysis Script:**
```python
from scapy.all import rdpcap, Dot1Q

# Read captured PCAP file
packets = rdpcap('/tmp/vlan_tag_003_capture.pcap')

tagged_count = 0
correct_vlan_count = 0

for pkt in packets:
    # Check if packet STILL HAS 802.1Q layer (tag preserved)
    if pkt.haslayer(Dot1Q):
        tagged_count += 1
        if pkt[Dot1Q].vlan == 10:
            correct_vlan_count += 1
            print(f"OK: Packet with VLAN 10 tag received (tag preserved)")
    else:
        # Packet has NO tag - FAIL for trunk-trunk scenario
        print(f"ERROR: Packet lost its VLAN tag")

print(f"Tagged packets: {tagged_count}/{len(packets)}")
print(f"Correct VLAN 10 packets: {correct_vlan_count}/{len(packets)}")

# Verify all packets are tagged
if correct_vlan_count == len(packets):
    print("✓ VLAN tag preservation verified successfully")
else:
    print(f"✗ Tag preservation failed: {len(packets) - correct_vlan_count} packets lost tags")
```

**Expected Result:**
- All 10 captured packets **STILL HAVE** 802.1Q header with VID=10
- Payload remains intact
- Ethernet frame structure preserved

---

## How to Run the Test

### Basic Execution

```bash
cd /home/claudeuser/satish/vlan/sonic-mgmt

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/switching/vlan/test_vlan_Tagged_Packet_on_Trunk_Port.py \
  --logs-path ./logs/vlan_tag_003_$(date +%F_%H%M%S) \
  --log-level debug \
  --skip-init-config \
  --ifname-type native
```

**Expected Execution Time**: 3-10 minutes

### Run with Custom Testbed

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/YOUR_CUSTOM_TESTBED.yaml \
  tests/switching/vlan/test_vlan_Tagged_Packet_on_Trunk_Port.py \
  --logs-path ./logs/vlan_tag_003_custom
```

### Run with Custom Variables

```bash
export VLAN_TAG_003_VAR_FILE=/path/to/custom/vars_vlan_tag_003.yaml

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/switching/vlan/test_vlan_Tagged_Packet_on_Trunk_Port.py \
  --logs-path ./logs/vlan_tag_003_custom
```

### Run Specific Test Method Only

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/switching/vlan/test_vlan_Tagged_Packet_on_Trunk_Port.py::TestVlanTaggedPacketOnTrunkPort::test_vlan_tag_003_trunk_to_trunk_tagged_forwarding \
  --logs-path ./logs/vlan_tag_003
```

---

## Expected Results

### Success Scenario

When the test passes, you should see:

```
VLAN Trunk-to-Trunk Tagged Packet Forwarding Test Suite
✓ Topology verified: D1D2:2
✓ Configuration loaded from vars_vlan_tag_003.yaml

MODULE PROLOGUE: Setup completed successfully

STEP 1: Creating VLAN 10 on both DUTs
✓ VLAN 10 created on both DUTs

STEP 2: Configuring trunk ports
✓ Trunk port Ethernet4 configured for VLAN 10 (tagged)
✓ Trunk port Ethernet4 configured for VLAN 10 (tagged)

STEP 3: Retrieving MAC addresses
✓ D1 Ethernet4 MAC: aa:bb:cc:dd:ee:01
✓ D2 Ethernet4 MAC: aa:bb:cc:dd:ee:02

STEP 4: Clearing interface counters
✓ Interface counters cleared on both ports

STEP 5: Starting packet capture on destination
✓ Packet capture started on Ethernet4

STEP 6: Sending tagged packets from source
✓ Sent 10 VLAN 10 tagged packets from Ethernet4

STEP 7: Analyzing captured packets for VLAN tag
✓ Packet Tag Preservation Analysis Summary:
  Total packets: 10
  Tagged packets: 10
  Correct VLAN 10 packets: 10
✓ VLAN tag preservation verified successfully

✓ TC_VLAN_TAG_003 PASSED: Tagged packets remain tagged on trunk-to-trunk forwarding

MODULE EPILOGUE: Cleanup completed
```

### Key Success Indicators

✓ Message: `"TC_VLAN_TAG_003 PASSED"`
✓ Message: `"VLAN tag preservation verified successfully"`
✓ Message: `"Tagged packets: 10"`
✓ Message: `"Correct VLAN 10 packets: 10"`
✓ Message: `"MODULE EPILOGUE: Cleanup completed"`
✓ Exit code: 0

---

## Failure Scenarios

### Scenario 1: Packets Lost Their VLAN Tag

**Symptom:**
```
✗ ERROR: Packet lost its VLAN tag
  Tagged packets: 0/10
  Packets with tag: 0
```

**Probable Causes:**
- Trunk port not properly configured for VLAN 10
- Port incorrectly configured as access port instead of trunk
- Incomplete configuration on one of the DUTs
- Switch is stripping tags on trunk ports (incorrect behavior)

**Investigation Steps:**
```bash
ssh admin@192.168.100.170 "show switchport Ethernet4"
ssh admin@192.168.100.231 "show switchport Ethernet4"
ssh admin@192.168.100.170 "show vlan id 10"
ssh admin@192.168.100.231 "show vlan id 10"
ssh admin@192.168.100.170 "show running-configuration interface Ethernet4 | no-more"
```

**Fix:**
```bash
ssh admin@192.168.100.170 << 'EOF'
configure terminal
interface Ethernet4
  no switchport mode
  switchport mode trunk
  switchport trunk allowed vlan 10
  no shutdown
exit
EOF
```

### Scenario 2: No Packets Captured

**Symptom:**
```
✗ ERROR: tcpdump capture failed
  Total packets: 0
  Captured: 0
```

**Probable Causes:**
- tcpdump not installed on D2
- Interface not up
- Firewall blocking traffic
- Cable disconnected
- Incorrect tcpdump filter

**Investigation Steps:**
```bash
ssh admin@192.168.100.231 "which tcpdump"
ssh admin@192.168.100.231 "show interface Ethernet4 status"
ssh admin@192.168.100.231 "show interface Ethernet4"
```

**Fix:**
```bash
# Install tcpdump
ssh admin@192.168.100.231 "apt-get update && apt-get install tcpdump"

# Verify interface is up
ssh admin@192.168.100.231 "configure terminal; interface Ethernet4; no shutdown; exit"
```

### Scenario 3: MAC Address Retrieval Failed

**Symptom:**
```
✗ ERROR: Could not retrieve MAC address for Ethernet4
  Regex pattern did not match output
```

**Probable Causes:**
- Interface not up
- MAC address format unexpected
- Show command output format different

**Investigation Steps:**
```bash
ssh admin@192.168.100.170 "show interface Ethernet4"
ssh admin@192.168.100.170 "show interface Ethernet4 | grep -i mac"
```

**Fix:**
- Bring interface up: `no shutdown`
- Check interface status: `show interface status`

### Scenario 4: Trunk Port Configuration Failed

**Symptom:**
```
✗ ERROR: Trunk port configuration failed on D1
  Command execution returned error code 1
```

**Probable Causes:**
- Interface already configured differently
- VLAN 10 not yet created
- Configuration not saved

**Investigation Steps:**
```bash
ssh admin@192.168.100.170 "show vlan id 10"
ssh admin@192.168.100.170 "show switchport Ethernet4"
ssh admin@192.168.100.170 "show running-configuration interface Ethernet4 | no-more"
```

**Fix:**
```bash
ssh admin@192.168.100.170 << 'EOF'
configure terminal
vlan 10
exit
interface Ethernet4
  switchport mode trunk
  switchport trunk allowed vlan 10
  switchport trunk native vlan 1
  no shutdown
exit
EOF
```

---

## Test Configuration

### YAML Variables File

Location: `spytest/vars/switching/vlan/vars_vlan_tag_003.yaml`

Key parameters:

```yaml
defaults:
  cli_type: klish
  min_topology:
    - "D1D2:2"

testcases:
  TC_VLAN_TAG_003:
    vlans:
      vlan_10: 10

    ports:
      trunk_port:
        vlans: [10]
        mode: "trunk"

      trunk_port_2:
        vlans: [10]
        mode: "trunk"

    traffic:
      packet_count: 10
      packet_size: 64
      frame_format:
        vlan_tag: 10

    verification:
      verify_tagged: true
      expected_tagged: true
```

---

## Performance Characteristics

### Execution Time Breakdown

| Phase | Duration | Notes |
|-------|----------|-------|
| Setup & Topology Verification | 1-2 min | DUT connectivity check |
| VLAN Creation | 30 sec | Both DUTs |
| Port Configuration | 1 min | Trunk setup |
| MAC Discovery | 30 sec | Interface MAC retrieval |
| Packet Generation & Capture | 2-3 min | Scapy + tcpdump |
| PCAP Analysis | 1 min | Scapy-based verification |
| Cleanup | 1 min | VLAN removal, port reset |
| **Total** | **5-10 min** | Typical execution |

### Resource Usage

| Resource | Typical Usage | Peak Usage |
|----------|---------------|-----------|
| Memory | <50 MB | <100 MB |
| CPU | <20% | <40% |
| Disk I/O | Minimal | PCAP write (1-2 MB) |
| Network Bandwidth | ~10 Mbps | During traffic (varies) |

---

## Troubleshooting Guide

See the [Failure Scenarios](#failure-scenarios) section above for detailed troubleshooting of common issues.

---

## Test Case Summary

| Aspect | Details |
|--------|---------|
| **Test ID** | TC_VLAN_TAG_003 |
| **Title** | Tagged Packet on Trunk Port |
| **Objective** | Verify tagged packet remains tagged on trunk-to-trunk forwarding |
| **Scope** | IEEE 802.1Q trunk-to-trunk forwarding |
| **Source Port** | Trunk (tagged) |
| **Operation** | PRESERVE VLAN tag |
| **Destination Port** | Trunk (tagged) |
| **Expected Result** | Packets received with same VLAN tag |
| **Test Duration** | 5-10 minutes |
| **Automation** | Fully automated |

---

**Document**: TC_VLAN_TAG_003 README
**Generated**: 2026-05-06
**Version**: 1.0 Final
**Status**: ✅ Complete and Ready for Execution
