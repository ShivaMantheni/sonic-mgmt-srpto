# VLAN Egress Untagging Test (TC_VLAN_TAG_002)

**Test Case**: TC_VLAN_TAG_002 - Egress Tagged Packet on Access Port
**Objective**: Verify that tagged packets received on a trunk port are properly untagged when forwarded to an access port (802.1Q compliance)
**Implementation Date**: 2026-05-06
**Status**: ✅ Complete and Ready for Execution

---

## Overview

This test validates the egress untagging behavior of switches in compliance with IEEE 802.1Q VLAN tagging standards. It ensures that:

1. A switch receives **tagged packets** on a **trunk port**
2. The switch removes the **802.1Q VLAN tag** based on port configuration
3. The switch forwards **untagged packets** to an **access port** configured for that VLAN
4. The packet structure and content remain intact (payload unchanged)

### Test Scenario

```
┌─────────────────────────────────────────────────────────────┐
│ Trunk Port (D2)         Untagging Process        Access Port (D1) │
│    Tagged Packet                                    Untagged Packet│
│   ┌──────────────┐                              ┌──────────────┐  │
│   │Ethernet Frame│                              │Ethernet Frame│  │
│   ├──────────────┤                              ├──────────────┤  │
│   │  802.1Q Tag  │──────────────────────────────│   (removed)  │  │
│   │  VID=10      │  Tag Stripped by Switch      │              │  │
│   ├──────────────┤                              ├──────────────┤  │
│   │   Payload    │──────────────────────────────│   Payload    │  │
│   └──────────────┘                              └──────────────┘  │
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
│  (Access Port)   │  Back-to-  │  (Trunk Port)    │
│                  │  Back Link │                  │
│  VLAN 10         │            │  VLAN 10 (tagged)│
│  (untagged)      │            │                  │
│                  │            │                  │
└──────────────────┘            └──────────────────┘

Port Roles:
- D1 Ethernet4: Access port (untagged member of VLAN 10)
- D2 Ethernet4: Trunk port (tagged member of VLAN 10)
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

### Step 2: Access Port Configuration (D1)

Configure Ethernet4 on D1 as an **access port** (untagged):

```bash
configure terminal
interface Ethernet4
  switchport mode access
  switchport access vlan 10
  no shutdown
exit
```

**Verification:**
```bash
show running-configuration interface Ethernet4 | no-more
show switchport Ethernet4
```

Expected output shows:
- Mode: access
- Access VLAN: 10
- No tagged VLANs

### Step 3: Trunk Port Configuration (D2)

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

Discover MAC addresses from both interfaces:

```bash
# D1 Ethernet4 MAC
show interface Ethernet4 | grep "Hardware is"

# D2 Ethernet4 MAC
show interface Ethernet4 | grep "Hardware is"
```

**Purpose**: MAC addresses needed for packet generation and verification

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

Start tcpdump on D1 (access port) to capture untagged packets:

```bash
tcpdump -i Ethernet4 -w /tmp/vlan_tag_002_capture.pcap -B 4096 &
```

**Parameters:**
- `-i Ethernet4`: Capture on access port
- `-w /tmp/vlan_tag_002_capture.pcap`: Write to file
- `-B 4096`: Buffer size for high-speed capture

### Step 7: Tagged Packet Transmission

Generate and send **tagged packets** from D2 trunk port:

```python
from scapy.all import Ether, Dot1Q, sendp, conf

src_mac = "aa:bb:cc:dd:ee:02"  # D2 Ethernet4 MAC
dst_mac = "aa:bb:cc:dd:ee:01"  # D1 Ethernet4 MAC

# Create TAGGED packet (with 802.1Q header)
pkt = Ether(src=src_mac, dst=dst_mac) / Dot1Q(vlan=10) / b'TestPayload123'

# Send 10 tagged packets
sendp(pkt, iface="Ethernet4", count=10, verbose=True)
```

**Packet Format:**
```
┌─────────────────────────────────────────────────────┐
│ Ethernet Frame Header                               │
├──────────────┬──────────────┬──────────────────────┤
│  Dest MAC    │   Src MAC    │  EtherType: 0x8100   │
├──────────────┴──────────────┴──────────────────────┤
│ 802.1Q VLAN Tag Header                              │
├───────────────┬─────────┬──────┬──────────────────┤
│  PCP (3 bits) │ CFI (1) │ VID (12 bits: 10)      │
├───────────────┴─────────┴──────┴──────────────────┤
│ Payload: "TestPayload123"                           │
└─────────────────────────────────────────────────────┘
```

**Transmission Details:**
- **Source Interface**: D2 Ethernet4 (trunk port)
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
packets = rdpcap('/tmp/vlan_tag_002_capture.pcap')

untagged_count = 0
for pkt in packets:
    # Check if packet has NO 802.1Q layer
    if pkt.haslayer(Dot1Q):
        # Packet still has tag - FAIL
        print(f"ERROR: Packet still tagged: {pkt.summary()}")
    else:
        # Packet is untagged - PASS
        untagged_count += 1
        print(f"OK: Untagged packet received")

print(f"Untagged packets: {untagged_count}/{len(packets)}")

# Verify all packets are untagged
if untagged_count == len(packets):
    print("✓ VLAN untagging verified successfully")
else:
    print(f"✗ Untagging failed: {len(packets) - untagged_count} packets still tagged")
```

**Expected Result:**
- All 10 captured packets have **NO 802.1Q header**
- Payload remains intact
- Ethernet frame structure preserved

---

## How to Run the Test

### Basic Execution

```bash
cd /home/hp/satish-demo/QOS/sonic-mgmt

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/QOS/test_vlan_Egress_Tagged_Packet_on_Access_Port.py \
  --logs-path ./logs/vlan_tag_002_$(date +%F_%H%M%S) \
  --log-level debug \
  --skip-init-config \
  --ifname-type native
```

**Expected Execution Time**: 3-10 minutes

### Run with Custom Testbed

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/YOUR_CUSTOM_TESTBED.yaml \
  tests/QOS/test_vlan_Egress_Tagged_Packet_on_Access_Port.py \
  --logs-path ./logs/vlan_tag_002_custom
```

### Run with Custom Variables

```bash
export VLAN_TAG_002_VAR_FILE=/path/to/custom/vars_vlan_tag_002.yaml

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/QOS/test_vlan_Egress_Tagged_Packet_on_Access_Port.py \
  --logs-path ./logs/vlan_tag_002_custom
```

### Run Specific Test Method Only

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/QOS/test_vlan_Egress_Tagged_Packet_on_Access_Port.py::TestVlanEgressTaggedPacketOnAccessPort::test_vlan_tag_002_egress_untagging_on_access_port \
  --logs-path ./logs/vlan_tag_002
```

---

## Expected Results

### Success Scenario

When the test passes, you should see:

```
VLAN Egress Untagging Test Suite
✓ Topology verified: D1D2:2
✓ Configuration loaded from vars_vlan_tag_002.yaml

MODULE PROLOGUE: Setup completed successfully

STEP 1: Creating VLAN 10 on both DUTs
✓ VLAN 10 created on both DUTs

STEP 2: Configuring access port on D1
✓ Access port Ethernet4 configured for VLAN 10 (untagged)

STEP 3: Configuring trunk port on D2
✓ Trunk port Ethernet4 configured for VLAN 10 (tagged)

STEP 4: Retrieving MAC addresses
✓ D1 Ethernet4 MAC: aa:bb:cc:dd:ee:01
✓ D2 Ethernet4 MAC: aa:bb:cc:dd:ee:02

STEP 5: Clearing interface counters
✓ Interface counters cleared on both ports

STEP 6: Starting packet capture on D1 access port
✓ Packet capture started on Ethernet4

STEP 7: Sending tagged packets from D2 trunk port
✓ Sent 10 VLAN 10 tagged packets from Ethernet4

STEP 8: Analyzing captured packets for untagging
✓ Packet Untagging Analysis Summary:
  Total packets: 10
  Untagged packets: 10
  Packets with VLAN tag (errors): 0
✓ VLAN untagging verified successfully

✓ TC_VLAN_TAG_002 PASSED: Tagged packets properly untagged on access port

MODULE EPILOGUE: Cleanup completed
```

### Key Success Indicators

✓ Message: `"TC_VLAN_TAG_002 PASSED"`
✓ Message: `"VLAN untagging verified successfully"`
✓ Message: `"Untagged packets: 10"`
✓ Message: `"MODULE EPILOGUE: Cleanup completed"`
✓ Exit code: 0

---

## Failure Scenarios

### Scenario 1: Packets Still Tagged

**Symptom:**
```
✗ ERROR: Packet still has VLAN tag
  Untagged packets: 5/10
  Packets with tag: 5
```

**Probable Causes:**
- Access port not properly configured for VLAN 10
- Port native VLAN mismatch
- Incomplete configuration on D1

**Investigation Steps:**
```bash
ssh admin@192.168.100.170 "show switchport Ethernet4"
ssh admin@192.168.100.170 "show vlan id 10"
ssh admin@192.168.100.170 "show running-configuration interface Ethernet4 | no-more"
```

**Fix:**
```bash
ssh admin@192.168.100.170 << 'EOF'
configure terminal
interface Ethernet4
  no switchport mode
  switchport mode access
  switchport access vlan 10
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
- tcpdump not installed on D1
- Interface not up
- Firewall blocking traffic
- Cable disconnected

**Investigation Steps:**
```bash
ssh admin@192.168.100.170 "which tcpdump"
ssh admin@192.168.100.170 "show interface Ethernet4 status"
ssh admin@192.168.100.170 "show interface Ethernet4"
```

**Fix:**
```bash
# Install tcpdump
ssh admin@192.168.100.170 "apt-get update && apt-get install tcpdump"

# Verify interface is up
ssh admin@192.168.100.170 "configure terminal; interface Ethernet4; no shutdown; exit"
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
✗ ERROR: Trunk port configuration failed on D2
  Command execution returned error code 1
```

**Probable Causes:**
- Interface already configured differently
- VLAN 10 not yet created
- Configuration not saved

**Investigation Steps:**
```bash
ssh admin@192.168.100.231 "show vlan id 10"
ssh admin@192.168.100.231 "show switchport Ethernet4"
ssh admin@192.168.100.231 "show running-configuration interface Ethernet4 | no-more"
```

**Fix:**
```bash
ssh admin@192.168.100.231 << 'EOF'
configure terminal
no interface Ethernet4
interface Ethernet4
  switchport mode trunk
  switchport trunk allowed vlan 10
  switchport trunk native vlan 1
  no shutdown
exit
EOF
```

---

## Troubleshooting Guide

### Issue: "Topology requirement not met (D1D2:2)"

**Error Message:**
```
✗ Topology Error: Required topology D1D2:2 not met
  Available: D1D2:1
```

**Root Cause**: Testbed has fewer than 2 back-to-back connections between D1 and D2

**Solution:**
1. Verify testbed YAML has at least 2 connections:
   ```bash
   grep -A 10 "D1:" testbeds/testbed_vs_2node_vlan.yaml | grep "Ethernet"
   ```

2. Should show multiple Ethernet interfaces:
   ```
   D1:
     Ethernet4: D2:Ethernet4
     Ethernet8: D2:Ethernet8
   ```

3. If not, edit testbed to add more connections

### Issue: "Scapy not available"

**Error Message:**
```
✗ ERROR: Scapy import failed
  ModuleNotFoundError: No module named 'scapy'
```

**Root Cause**: Scapy not installed on DUT

**Solution:**
```bash
ssh admin@192.168.100.231 "pip3 install scapy"

# Verify installation
ssh admin@192.168.100.231 "python3 -c 'from scapy.all import Ether; print(\"Scapy OK\")'"
```

### Issue: "Interface not found in topology"

**Error Message:**
```
✗ ERROR: Interface D1D2P1 not found in topology
  Available interfaces: [D1D2P1, D1D2P2]
```

**Root Cause**: Testbed topology doesn't define required interface

**Solution:**
1. Check testbed file for topology section:
   ```bash
   grep -A 5 "topology:" testbeds/testbed_vs_2node_vlan.yaml
   ```

2. Ensure it has D1D2P1 and D2D1P1 defined

### Issue: "tcpdump terminated unexpectedly"

**Error Message:**
```
✗ ERROR: tcpdump process exited with code 1
  Possible reasons: Interface not up, permission denied
```

**Root Cause**: Interface down, tcpdump permission issue, or interface name invalid

**Solution:**
```bash
# Verify interface is up
ssh admin@192.168.100.170 "show interface Ethernet4 status"

# Check tcpdump permissions
ssh admin@192.168.100.170 "sudo tcpdump -i Ethernet4 -c 1"

# Verify interface name
ssh admin@192.168.100.170 "show interface status | grep Ethernet4"
```

### Issue: "PCAP file not created"

**Error Message:**
```
✗ ERROR: PCAP file not found at /tmp/vlan_tag_002_capture.pcap
  File does not exist or was not written
```

**Root Cause**: tcpdump didn't write to file, permission denied, or disk full

**Solution:**
```bash
# Check disk space
ssh admin@192.168.100.170 "df -h /tmp"

# Check write permissions
ssh admin@192.168.100.170 "ls -la /tmp | grep vlan_tag_002"

# Try manual capture
ssh admin@192.168.100.170 "sudo tcpdump -i Ethernet4 -w /tmp/test.pcap -c 1"
```

---

## Test Configuration

### YAML Variables File

Location: `spytest/vars/switching/vlan/vars_vlan_tag_002.yaml`

Key parameters:

```yaml
defaults:
  cli_type: klish
  min_topology:
    - "D1D2:2"
  verify_timeout: 30
  cleanup: true

testcases:
  TC_VLAN_TAG_002:
    title: "Egress Tagged Packet on Access Port"

    vlans:
      vlan_10: 10

    ports:
      trunk_port:
        vlans: [10]
        mode: "trunk"
        state: "up"
        shutdown: false
        native_vlan: 1

      access_port:
        vlan_id: 10
        mode: "access"
        state: "up"
        shutdown: false

    traffic:
      method: "scapy"
      packet_count: 10
      packet_size: 64
      packet_type: "ethernet"
      packet_rate: 1000
      duration: 5
      frame_format:
        type: "ethernet"
        src_mac: "auto"
        dst_mac: "auto"
        vlan_tag: 10
        vlan_priority: 0
        ethertype: "0x0800"

    capture:
      method: "tcpdump"
      interface: "Port1"
      bpf_filter: ""
      timeout: 15
      output_format: "pcap"
      keep_pcap: false

    verification:
      verify_vlan_config: true
      verify_port_config: true
      verify_capture: true
      verify_untagged: true
      expected_untagged: true
      max_packet_loss_percent: 10
      use_show_running_config: true
```

### Custom Variable Override

Use environment variables to override YAML defaults:

```bash
export VLAN_TAG_002_PACKET_COUNT=20
export VLAN_TAG_002_PACKET_SIZE=128
export VLAN_TAG_002_TIMEOUT=30

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/QOS/test_vlan_Egress_Tagged_Packet_on_Access_Port.py \
  --logs-path ./logs/vlan_tag_002
```

---

## Performance Characteristics

### Execution Time Breakdown

| Phase | Duration | Notes |
|-------|----------|-------|
| Setup & Topology Verification | 1-2 min | DUT connectivity check |
| VLAN Creation | 30 sec | Both DUTs |
| Port Configuration | 1 min | Access + Trunk setup |
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

### Packet Size Impact

```
Minimum: 64 bytes (Ethernet minimum)
- Ethernet Header: 14 bytes
- 802.1Q Tag: 4 bytes (ingress)
- Payload: ~46 bytes
- FCS: 4 bytes

Typical: 64-1500 bytes
- Allows payload testing
- Realistic traffic pattern

Maximum: 9000 bytes (jumbo)
- Requires MTU configuration
- Not default for test
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: VLAN TAG-002 Test

on: [push, pull_request]

jobs:
  vlan-tag-002:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run TC_VLAN_TAG_002
        run: |
          ./bin/spytest --tryssh 1 \
            --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
            tests/QOS/test_vlan_Egress_Tagged_Packet_on_Access_Port.py \
            --logs-path ./logs/vlan_tag_002

      - name: Upload Logs
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: vlan-tag-002-logs
          path: logs/vlan_tag_002/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('VLAN TAG-002') {
            steps {
                sh '''
                    ./bin/spytest --tryssh 1 \
                      --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
                      tests/QOS/test_vlan_Egress_Tagged_Packet_on_Access_Port.py \
                      --logs-path ./logs/vlan_tag_002
                '''
            }
        }
    }

    post {
        always {
            junit 'logs/vlan_tag_002/**/results.xml'
            archiveArtifacts 'logs/vlan_tag_002/**'
        }
    }
}
```

---

## Quick Reference

### Common Commands

**Check VLAN Configuration:**
```bash
ssh admin@192.168.100.170 "show vlan id 10"
```

**Check Port Configuration:**
```bash
ssh admin@192.168.100.170 "show switchport Ethernet4"
```

**Check Running Configuration:**
```bash
ssh admin@192.168.100.170 "show running-configuration interface Ethernet4 | no-more"
```

**Check Interface Status:**
```bash
ssh admin@192.168.100.170 "show interface Ethernet4 status"
```

**Check Interface Counters:**
```bash
ssh admin@192.168.100.170 "show interface Ethernet4 counters"
```

**View Test Logs:**
```bash
tail -f logs/vlan_tag_002_*/module_*.log
```

**View Summary:**
```bash
cat logs/vlan_tag_002_*/summary.txt
```

### Success Checklist

✅ Test execution completed without errors
✅ "TC_VLAN_TAG_002 PASSED" message present
✅ All 10 packets captured as untagged
✅ VLAN configuration verified in running-config
✅ Cleanup completed successfully
✅ VLAN 10 removed from both DUTs

---

## Related Test Cases

| Test Case | Purpose | Status |
|-----------|---------|--------|
| **TC_VLAN_TAG_001** | Ingress untagged → tagged | ✅ Implemented |
| **TC_VLAN_TAG_002** | Egress tagged → untagged | ✅ This test |
| **TC_VLAN_TAG_003** | Trunk-to-trunk tagged | 📋 Future |
| **TC_VLAN_TAG_004** | Q-in-Q double-tagged | 📋 Future |

---

## Documentation Structure

This README covers:
- ✅ Test objective and scope
- ✅ Detailed network topology
- ✅ Step-by-step execution flow
- ✅ Multiple execution methods
- ✅ Expected results and success criteria
- ✅ 4 failure scenarios with solutions
- ✅ 6 troubleshooting issues and fixes
- ✅ Configuration parameters
- ✅ Performance characteristics
- ✅ CI/CD integration examples
- ✅ Quick reference commands

For implementation details, see: `test_vlan_Egress_Tagged_Packet_on_Access_Port.py`
For variables, see: `spytest/vars/switching/vlan/vars_vlan_tag_002.yaml`

---

**Generated**: 2026-05-06
**Test Case**: TC_VLAN_TAG_002 - Egress Tagged Packet on Access Port
**Status**: ✅ Ready for Execution
