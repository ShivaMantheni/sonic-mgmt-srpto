# VLAN Untagged Packet Tagging Test Suite

**Test Case**: TC_VLAN_TAG_001 - Ingress Untagged Packet Tagging
**Author**: Test Automation Team
**Date**: 2026-05-06
**Status**: Ready for Execution

---

## Overview

This test suite validates **VLAN 802.1Q compliance** by verifying that untagged packets received on an access port are properly tagged with the VLAN ID when forwarded to trunk ports.

### Test Objective

Verify that untagged Ethernet frames ingressing on an access port are correctly tagged with the VLAN 10 tag (802.1Q header with VID=10) when forwarded to trunk ports.

### Test Coverage

- **Feature**: VLAN Packet Tagging (802.1Q Compliance)
- **Test Case**: TC_VLAN_TAG_001
- **Specification**: IEEE 802.1Q VLAN Tagging Standard
- **Duration**: ~5-10 minutes

---

## Test Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌──────────────────────┐          ┌──────────────────────┐    │
│  │    D1 (DUT1)         │          │    D2 (DUT2)         │    │
│  │  (Traffic Sender)    │          │ (Traffic Receiver)   │    │
│  │                      │          │                      │    │
│  │  Ethernet4 (Access)  │ ────────▶│  Ethernet4 (Trunk)  │    │
│  │  VLAN 10 (Untagged)  │ (Link 1) │  VLAN 10,20,30      │    │
│  │                      │          │  (Tagged)           │    │
│  │  Ethernet8           │◀ ────────│  Ethernet8          │    │
│  │  (Monitor)           │ (Link 2) │  (Monitor)          │    │
│  │                      │          │                      │    │
│  └──────────────────────┘          └──────────────────────┘    │
│                                                                 │
│  Topology Requirements:                                         │
│    - Two DUTs (D1, D2)                                         │
│    - 2 back-to-back connections (Ethernet4, Ethernet8)         │
│    - VLAN support with 802.1Q tagging                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Port Configuration

| Port | Device | Mode | VLAN | Tagged/Untagged | Purpose |
|------|--------|------|------|-----------------|---------|
| Ethernet4 | D1 | Access | 10 | Untagged | Packet source |
| Ethernet4 | D2 | Trunk | 10,20,30 | Tagged | Packet capture |
| Ethernet8 | D1 | - | - | - | Monitoring |
| Ethernet8 | D2 | - | - | - | Monitoring |

---

## Test Execution Flow

### Step 1: VLAN Creation
```
D1: vlan 10
D2: vlan 10
```

### Step 2: Port Configuration
```
D1 Ethernet4:
  - switchport mode access
  - switchport access vlan 10

D2 Ethernet4:
  - switchport mode trunk
  - switchport trunk allowed vlan 10,20,30
```

### Step 3: Retrieve MAC Addresses
- Get D1 Ethernet4 MAC address
- Get D2 Ethernet4 MAC address

### Step 4: Clear Interface Counters
```
D1: clear interface counters
D2: clear interface counters
```

### Step 5: Start Packet Capture
```
D2: tcpdump -i Ethernet4 -c 10 -w /tmp/vlan_capture.pcap
```

### Step 6: Send Untagged Packets
```
Scapy on D1 Ethernet4:
  - Create untagged Ethernet frame
  - Source MAC: D1 Ethernet4 MAC
  - Destination MAC: D2 Ethernet4 MAC
  - No VLAN tag
  - Send 10 packets
```

### Step 7: Analyze Captured Packets
```
PCAP Analysis:
  - Check for 802.1Q header (VLAN tag)
  - Verify VLAN ID = 10
  - Verify PCP = 0
  - Count tagged packets
```

### Step 8: Verify Running Configuration
```
show running-configuration | no-more
  - Verify vlan 10 exists
  - Verify Ethernet4 switchport access vlan 10 on D1
  - Verify Ethernet4 switchport trunk allowed vlan on D2
```

---

## How to Run

### Prerequisites

1. **Testbed Setup**
   - Two SONiC devices (D1 and D2)
   - Connected via Ethernet4 and Ethernet8 (back-to-back)
   - SSH access enabled on both devices
   - Admin credentials configured

2. **Software Requirements**
   - SONiC OS with VLAN support
   - Python 3.8+ with Scapy
   - tcpdump installed on DUTs
   - SPyTest framework

3. **Connectivity**
   - D1 and D2 must be reachable via SSH
   - Direct L2 connectivity between test ports

### Basic Execution

```bash
# Run test with default testbed (testbed_vs_2node_vlan.yaml)
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/QOS/test_vlan_Untagged_Packet_Tagging.py \
  --logs-path ./logs/vlan_tagging_$(date +%F_%H%M%S) \
  --log-level debug \
  --skip-init-config \
  --ifname-type native
```

### With Custom Testbed

```bash
# Use custom testbed file
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/your_testbed.yaml \
  tests/QOS/test_vlan_Untagged_Packet_Tagging.py \
  --logs-path ./logs/vlan_test_$(date +%F_%H%M%S) \
  --log-level debug
```

### With Custom Variables

```bash
# Override YAML variables
export VLAN_TAGGING_VAR_FILE=/path/to/custom/vars_vlan_tagging.yaml

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/QOS/test_vlan_Untagged_Packet_Tagging.py \
  --logs-path ./logs/vlan_test \
  --log-level debug
```

### Run Specific Test Method

```bash
# Run only TC_VLAN_TAG_001 test
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/QOS/test_vlan_Untagged_Packet_Tagging.py::TestVlanUntaggedPacketTagging::test_vlan_tag_001_ingress_untagged_tagging \
  --logs-path ./logs/vlan_test \
  --log-level debug
```

---

## Configuration Files

### Test Script
- **Location**: `/home/hp/satish-demo/QOS/sonic-mgmt/spytest/tests/QOS/test_vlan_Untagged_Packet_Tagging.py`
- **Lines**: 600+
- **Dependencies**:
  - `spytest` (SPyTest framework)
  - `apis.switching.vlan` (VLAN API)
  - `apis.system.interface` (Interface API)
  - `scapy` (Packet generation)

### Variables File
- **Location**: `/home/hp/satish-demo/QOS/sonic-mgmt/spytest/vars/switching/vlan/vars_vlan_tagging.yaml`
- **Variables**:
  - VLAN IDs (10, 20, 30)
  - Port roles (access, trunk)
  - Traffic parameters (packet count, size, rate)
  - Capture settings (interface, timeout, filters)
  - Verification settings (thresholds, checks)

### Testbed File
- **Location**: `/home/hp/satish-demo/QOS/sonic-mgmt/spytest/testbeds/testbed_vs_2node_vlan.yaml`
- **Device Count**: 2 (D1, D2)
- **Connection Count**: 5 (Ethernet4, 8, 12, 16, 20)
- **Topology**: Back-to-back VLAN testing topology

---

## Expected Results

### Successful Test Execution

```
STEP 1: Creating VLAN 10 on both DUTs
✓ VLAN 10 created on both DUTs

STEP 2: Configuring access port on D1
✓ Access port Ethernet4 configured for VLAN 10

STEP 3: Configuring trunk port on D2
✓ Trunk port Ethernet4 configured for VLANs [10, 20, 30]

STEP 4: Retrieving MAC addresses
✓ D1 Ethernet4 MAC: aa:bb:cc:dd:ee:01
✓ D2 Ethernet4 MAC: aa:bb:cc:dd:ee:02

STEP 5: Clearing interface counters
✓ Interface counters cleared

STEP 6: Starting packet capture on D2 trunk port
✓ Packet capture started on Ethernet4
  Output file: /tmp/vlan_tag_capture_1715000000.pcap

STEP 7: Sending untagged packets from D1 access port
✓ Sent 10 untagged packets from Ethernet4

STEP 8: Analyzing captured packets for VLAN tags
✓ VLAN Tag Analysis Summary:
  Total packets: 10
  VLAN tagged packets: 10
  Correct VLAN 10 packets: 10
✓ VLAN tagging verified successfully

✓ TC_VLAN_TAG_001 PASSED: Untagged packets properly tagged with VLAN 10
```

### Packet Capture Analysis

```
Untagged Frame (Sent from D1):
  Ethernet Header:
    Destination MAC: aa:bb:cc:dd:ee:02
    Source MAC: aa:bb:cc:dd:ee:01
    EtherType: 0x0800 (IPv4)
  Payload: Data...
  (No VLAN tag)

Tagged Frame (Received on D2):
  Ethernet Header:
    Destination MAC: aa:bb:cc:dd:ee:02
    Source MAC: aa:bb:cc:dd:ee:01
    EtherType: 0x8100 (802.1Q VLAN Tag)
  802.1Q Header:
    Priority Code Point (PCP): 0
    Canonical Format Indicator (CFI): 0
    VLAN Identifier (VID): 10  ✓ CORRECT
  EtherType: 0x0800 (IPv4)
  Payload: Data...
```

---

## Failure Scenarios

### Scenario 1: VLAN Not Tagged on Trunk
```
✗ VLAN Tag Analysis Summary:
  Total packets: 10
  VLAN tagged packets: 0
  Correct VLAN 10 packets: 0
✗ VLAN tagging verified successfully

Cause: Access port not properly configured or VLAN not created
Solution:
  - Verify VLAN 10 exists
  - Verify access port configuration: "show running-configuration | no-more"
  - Check if packets actually reached trunk port
```

### Scenario 2: Wrong VLAN ID
```
✗ Packet with wrong VLAN 20 (expected 10)
✗ No packets with VLAN 10 found

Cause: Packets tagged with wrong VLAN
Solution:
  - Verify access port VLAN assignment
  - Check if packet source is correct
  - Verify trunk port VLAN list
```

### Scenario 3: Packet Loss
```
✗ Total packets sent: 10
✗ Packets captured: 5
✗ Packet loss: 50%

Cause: Link issues or interface problems
Solution:
  - Check link status: "show interface status"
  - Verify port counters for errors
  - Check for interface shutdown state
```

### Scenario 4: Capture Failed
```
✗ Packet capture initialization failed

Cause: tcpdump not available or permission denied
Solution:
  - Verify tcpdump is installed: "which tcpdump"
  - Check user permissions
  - Verify interface name is correct
```

---

## Troubleshooting Guide

### Issue: "Test case TC_VLAN_TAG_001 not found in YAML"

**Solution**: Verify YAML file exists and contains testcase definition
```bash
# Check YAML file
cat spytest/vars/switching/vlan/vars_vlan_tagging.yaml | grep "TC_VLAN_TAG_001"

# Verify YAML syntax
python3 -m yaml spytest/vars/switching/vlan/vars_vlan_tagging.yaml
```

### Issue: "Topology requirement not met"

**Solution**: Ensure testbed has required connectivity
```bash
# Check testbed connections
grep -A 10 "D1D2P" testbeds/testbed_vs_2node_vlan.yaml

# Verify D1 and D2 are reachable
ssh admin@192.168.100.170 "hostname"
ssh admin@192.168.100.231 "hostname"
```

### Issue: "Could not retrieve MAC address"

**Solution**: Verify interface exists and is up
```bash
# On DUT1
show interface Ethernet4
show interface Ethernet4 status

# Check if interface has IP address
show ip interface brief | grep Ethernet4
```

### Issue: "tcpdump not available"

**Solution**: Install tcpdump on DUT
```bash
# SSH to DUT
ssh admin@device_ip

# Install tcpdump
apt-get update
apt-get install tcpdump

# Verify installation
which tcpdump
```

### Issue: "Scapy not available for packet generation"

**Solution**: Install Scapy on DUT
```bash
# Install Scapy
pip3 install scapy

# Verify installation
python3 -c "from scapy.all import Ether; print('Scapy OK')"
```

---

## Performance Characteristics

### Expected Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Test Duration | 2-5 min | Including setup, teardown, capture |
| Packet Transmission Time | <100 ms | For 10 packets |
| Packet Capture Time | 3-5 sec | Depends on packet count and timeout |
| PCAP Analysis Time | 1-2 sec | Using Scapy for pcap reading |
| Total Test Time | 3-10 min | With all overheads |

### Resource Usage

| Resource | Typical | Notes |
|----------|---------|-------|
| Memory | <50 MB | Test process + Scapy + pcap analysis |
| CPU | <20% | Depends on packet rate and processing |
| Disk | <10 MB | For pcap file and logs |
| Network | 10 Mbps | Packet transmission bandwidth |

---

## Validation Checklist

Before running the test in production, verify:

- [ ] Testbed has two SONiC devices with back-to-back connectivity
- [ ] SSH access enabled with correct credentials
- [ ] tcpdump installed on both DUTs
- [ ] Scapy installed on both DUTs
- [ ] VLAN support confirmed on devices
- [ ] Test script and YAML files in correct locations
- [ ] Testbed YAML file properly configured
- [ ] No existing VLAN 10 configuration (or cleanup enabled)
- [ ] Interface naming matches testbed configuration
- [ ] Sufficient disk space for pcap files and logs

---

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run VLAN Tagging Test
  run: |
    ./bin/spytest --tryssh 1 \
      --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
      tests/QOS/test_vlan_Untagged_Packet_Tagging.py \
      --logs-path ./logs/vlan_test
```

### Jenkins Pipeline
```groovy
stage('VLAN Tagging Tests') {
  steps {
    sh '''
      ./bin/spytest --tryssh 1 \
        --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
        tests/QOS/test_vlan_Untagged_Packet_Tagging.py \
        --logs-path ./logs/vlan_test
    '''
  }
}
```

---

## Related Test Cases

This test is part of the VLAN Tagging test suite:

- **TC_VLAN_TAG_001** (This Test): Ingress Untagged Packet Tagging ✓ Implemented
- **TC_VLAN_TAG_002**: Egress Tagged Packet on Access Port (Planned)
- **TC_VLAN_TAG_003**: Tagged Packet on Trunk Port (Planned)
- **TC_VLAN_TAG_004**: Q-in-Q Double Tagged Packet Handling (Planned)

Related VLAN test cases:
- TC_VLAN_CREATE_001: Create Single VLAN
- TC_VLAN_ACCESS_001: Configure Untagged Port
- TC_VLAN_TRUNK_001: Configure Tagged Port
- TC_VLAN_MIXED_001: Hybrid Port Configuration

---

## Support and Documentation

### Key References

1. **Test Plan**: `/home/claudeuser/satish/vlan/sonic-mgmt/spytest/tests/switching/vlan/doc/vlan_testplan.md`
2. **IEEE 802.1Q Specification**: VLAN Tagging Standard
3. **SONiC CLI Commands**: https://github.com/sonic-net/sonic-buildimage/wiki
4. **Scapy Documentation**: https://scapy.readthedocs.io/
5. **SPyTest Framework**: Framework documentation in `spytest/Doc/`

### Contact

For issues or questions:
- Create GitHub Issue
- Review test logs in `--logs-path` directory
- Check `dlog-D1-*.log` and `dlog-D2-*.log` for device logs

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-06 | Test Team | Initial implementation of TC_VLAN_TAG_001 |

---

## Appendix: Quick Reference Commands

### Clear VLAN Configuration Manually
```bash
# SSH to DUT
ssh admin@device_ip

# Configure mode
config

# Remove VLAN
no vlan 10

# Exit
exit

# Verify
show vlan brief
```

### Show Interface VLAN Configuration
```bash
show interface Ethernet4 switchport
show running-configuration | grep "Ethernet4" -A 3
show vlan id 10
```

### Monitor Packet Transmission
```bash
# Start tcpdump on receiver
tcpdump -i Ethernet4 -v

# Send packets from sender (in another session)
python3
from scapy.all import Ether, sendp
pkt = Ether(src="aa:bb:cc:dd:ee:01", dst="aa:bb:cc:dd:ee:02")/b'X'*50
sendp(pkt, iface="Ethernet4", count=1)
```

### Check Pcap File Contents
```bash
# View pcap file summary
tcpdump -r /tmp/vlan_tag_capture.pcap -n

# View verbose pcap details
tcpdump -r /tmp/vlan_tag_capture.pcap -vv

# View VLAN tags in pcap
tcpdump -r /tmp/vlan_tag_capture.pcap -vvv | grep -i vlan
```

---

**End of Documentation**
