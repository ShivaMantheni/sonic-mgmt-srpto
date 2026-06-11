# SM_ISCLI_P2_145: Global IPv4 ACL Application and Traffic Filtering

## Test Case Summary

**Title**: Verify IPv4 ACL global mode application with source IP denial rules

**Bug ID**: SM_ISCLI_P2_145

**Category**: Access Control List (ACL) - Global Mode

**Test Type**: Functional / Regression

**Severity**: Medium

**Status**: New / Needs Implementation

---

## Topology

**Source**: `testbeds/testbed_acl_vs.yaml` (Actual Port Definitions)

```
┌──────────────────┐                    ┌──────────────────┐
│   Server-P1      │                    │   Server-P2      │
│  172.0.0.2/24    │                    │  173.0.0.2/24    │
│                  │                    │                  │
│ (TX via Scapy)   │                    │ (RX via tcpdump) │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
    Ethernet0 (41G)                      Ethernet0 (41G)
         │                                       │
    [172.0.0.1/24]                        [173.0.0.1/24]
         │      ┌──────────────────────┐        │
         └──────┤  SONiC DUT1 (D1)     ├────────┘
                │                      │
                │ Ethernet0 ◄────────► │
                │          Ethernet16  │
                │                      │
                │ Global ACL Applied   │
                │ (ip access-group)    │
                └──────────────────────┘
```

**Device Mapping** (from testbed_acl_vs.yaml):
- **DUT1** (D1): ACL Device Under Test
  - Management IP: 192.168.100.41
  - **Ethernet0** (41G): 172.0.0.1/24 (TX gateway from DUT2)
  - **Ethernet16** (41G): 173.0.0.1/24 (RX gateway to DUT3)
  - **Connected Links**:
    - Ethernet0 ↔ DUT2:Ethernet0 (TX path, 41G)
    - Ethernet16 ↔ DUT3:Ethernet0 (RX path, 41G)

- **DUT2** (D2): TX Traffic Generator (Scapy source)
  - Management IP: 192.168.100.42
  - **Ethernet0** (41G): 172.0.0.2/24 (Server-P1)
  - Connected: Ethernet0 ↔ DUT1:Ethernet0

- **DUT3** (D3): RX Traffic Sink (tcpdump verification)
  - Management IP: 192.168.100.43
  - **Ethernet0** (41G): 173.0.0.2/24 (Server-P2)
  - Connected: Ethernet0 ↔ DUT1:Ethernet16

**Testbed File**: `testbeds/testbed_acl_vs.yaml`

---

## Test Parameters (YAML)

```yaml
defaults:
  min_topology:
    - D1D2:1  # DUT1-DUT2 link for TX traffic
    - D1D3:1  # DUT1-DUT3 link for RX traffic

  cli_type: klish
  verify_timeout: 30
  cleanup: true

dut_config:
  dut1_eth0_ip: 172.0.0.1/24     # Ethernet0 (41G) - TX gateway
  dut1_eth16_ip: 173.0.0.1/24    # Ethernet16 (41G) - RX gateway
  dut2_eth0_ip: 172.0.0.2/24     # Ethernet0 (41G) - TX source
  dut3_eth0_ip: 173.0.0.2/24     # Ethernet0 (41G) - RX sink

acl_config:
  acl_name: "aac"
  rule_seq: 1
  rule_action: "deny"
  rule_protocol: "ip"
  rule_src_ip: "host 172.0.0.2"
  rule_dst_ip: "any"
  apply_mode: "global"  # Key: Global mode, not interface-based
  apply_direction: "in"

traffic_config:
  src_ip: "172.0.0.2"
  dst_ip: "173.0.0.2"
  traffic_type: "L3_IP"
  packet_count: 100
  duration_seconds: 10
```

---

## Pre-requisites

- **Topology**: 3-node SONiC topology (D1=ACL device, D2=TX host, D3=RX host)
- **DUT Support**: SONiC 202211 or later
- **Features Required**:
  - IPv4 ACL support
  - Global ACL mode (`ip access-group ... in`)
  - Interface IP configuration (L3 mode)
  - Scapy traffic generation
  - tcpdump packet capture
- **Supported Platforms**: Virtual (SONiC-VS) and Hardware
- **CLI Type**: klish (sonic-cli)

---

## Test Case 1: SM_ISCLI_P2_145.1 - Create IPv4 ACL with Source IP Deny Rule

### Objective
Verify that an IPv4 ACL with source IP deny rule can be created and configured successfully.

### Steps

1. **Setup DUT interfaces** (D1)
   ```
   configure terminal
   interface Ethernet 0
   ip address 172.0.0.1/24
   !
   interface Ethernet 16
   ip address 173.0.0.1/24
   !
   exit
   ```

2. **Setup TX host interfaces** (D2)
   ```
   configure terminal
   interface Ethernet 0
   ip address 172.0.0.2/24
   !
   exit
   ```

3. **Setup RX host interfaces** (D3)
   ```
   configure terminal
   interface Ethernet 0
   ip address 173.0.0.2/24
   !
   exit
   ```

4. **Create IPv4 ACL on DUT** (D1)
   ```
   configure terminal
   ip access-list aac
   seq 1 deny ip host 172.0.0.2 any
   exit
   exit
   ```

5. **Verify ACL creation**
   ```
   show ip access-lists aac
   ```

   **Expected Output**:
   ```
   IP Access-List aac:
       seq 1 deny ip host 172.0.0.2 any
   ```

### Validation
- ACL "aac" is created
- Rule sequence 1 with deny action exists
- Source IP "host 172.0.0.2" is configured
- Destination "any" is configured

### Pass Criteria
- ACL appears in `show ip access-lists`
- Rule details match configuration
- No errors during creation

---

## Test Case 2: SM_ISCLI_P2_145.2 - Apply ACL in Global Mode

### Objective
Verify that IPv4 ACL can be applied in global mode (not per-interface).

### Steps

1. **Apply ACL in global mode** (D1)
   ```
   configure terminal
   ip access-group aac in
   exit
   ```

2. **Verify global ACL binding**
   ```
   show running-config | grep -A 2 "ip access-group"
   ```

   **Expected Output** (with pagination handling):
   ```
   ip access-group aac in
   ```

3. **Verify ACL direction is ingress**
   ```
   show ip access-lists
   ```

### Validation
- ACL "aac" is bound in global mode
- Direction is "in" (ingress)
- No interface-specific bindings visible
- Configuration persists in running-config

### Pass Criteria
- `show running-config` contains `ip access-group aac in`
- No configuration errors reported
- Global ACL binding confirmed

---

## Test Case 3: SM_ISCLI_P2_145.3 - Verify ACL Traffic Denial (Global Mode)

### Objective
Verify that traffic matching the global ACL deny rule is actually dropped.

### Steps

1. **Start traffic capture on RX side** (D3 - Ethernet 0 receiving from D1:Ethernet 16)
   ```bash
   sudo tcpdump -i Ethernet 0 -w /tmp/acl_test_p2_145.pcap "src 172.0.0.2 and dst 173.0.0.2" &
   # This captures packets arriving on DUT3:Ethernet 0 from DUT1:Ethernet 16
   ```

2. **Send test traffic from TX host** (D2)
   - Source IP: 172.0.0.2
   - Destination IP: 173.0.0.2
   - Packet Count: 100
   - Duration: 10 seconds
   - Protocol: IPv4/ICMP or IP (Scapy-based generation)

   **Scapy command example**:
   ```python
   from scapy.all import *
   src_mac = <DUT2-MAC>
   dst_mac = <DUT1-MAC>
   packets = [
       Ether(src=src_mac, dst=dst_mac) / IP(src="172.0.0.2", dst="173.0.0.2") / ICMP()
       for _ in range(100)
   ]
   send(packets, iface="Ethernet0", inter=0.1)
   ```

3. **Stop traffic capture** (D3)
   ```bash
   sudo killall tcpdump
   ```

4. **Analyze captured packets** (D3)
   ```bash
   sudo python3 -c "from scapy.all import rdpcap; pkts = rdpcap('/tmp/acl_test_p2_145.pcap'); print(f'Captured packets: {len(pkts)}')"
   ```

5. **Verify ACL counters** (D1)
   ```
   show ip access-lists aac
   show ip access-lists aac detailed
   ```

### Validation
- **RX packet count**: Should be **0** (traffic was denied by global ACL)
- **TX packet count**: Should be **100** (sent from source)
- **ACL hit counters**: Should show matches on sequence 1
- **No packets on RX**: pcap file contains 0 packets matching src=172.0.0.2, dst=173.0.0.2

### Pass Criteria
- Zero packets received on DUT3:Ethernet0 from 172.0.0.2 to 173.0.0.2
- ACL counters show "1" rule matched (deny sequence 1)
- Denial is due to global ACL, not interface-based ACL

### Expected Behavior
```
TX Count:  100 packets sent
RX Count:  0 packets received  (PASS - traffic was blocked)
ACL Hits:  100 hits on deny rule sequence 1
```

---

## Test Case 4: SM_ISCLI_P2_145.4 - Verify Global ACL Doesn't Affect Interface ACLs

### Objective
Verify that global ACL is independent and doesn't conflict with interface-based ACL rules.

### Steps

1. **Apply ACL to Ethernet 16 (RX interface)** (D1)
   ```
   configure terminal
   interface Ethernet 16
   ip access-group aac in
   exit
   ```

2. **Remove global ACL binding** (D1)
   ```
   configure terminal
   no ip access-group aac in
   exit
   ```

3. **Verify interface ACL is active** (D1)
   ```
   show running-config interface Ethernet 16 | grep access-group
   ```

4. **Send traffic again from TX host** (D2)
   - Same source/destination as Test Case 3
   - Should still be denied (but now via interface ACL on Ethernet16)

5. **Verify traffic denial via interface ACL** (D3)
   - Same pcap verification as Test Case 3

### Validation
- Interface ACL still applies correctly
- Traffic is denied at Ethernet4 (not globally)
- ACL functionality is independent of application mode

### Pass Criteria
- Interface ACL shows in `show running-config`
- Global ACL removed (`no ip access-group` worked)
- Traffic is still blocked via interface ACL
- RX count remains 0

---

## Test Case 5: SM_ISCLI_P2_145.5 - Cleanup and Remove Global ACL

### Objective
Verify clean removal of global ACL configuration.

### Steps

1. **Remove global ACL binding** (D1)
   ```
   configure terminal
   no ip access-group aac in
   exit
   ```

2. **Delete ACL** (D1)
   ```
   configure terminal
   no ip access-list aac
   exit
   ```

3. **Verify ACL removal** (D1)
   ```
   show ip access-lists
   show ip access-lists aac
   ```

   **Expected**: ACL "aac" should NOT appear in output

4. **Verify running-config is clean** (D1)
   ```
   show running-config | grep -c "aac"
   ```

   **Expected**: Count should be 0 or no lines returned

### Validation
- ACL "aac" is completely removed
- No orphaned ACL references
- Running-config is clean

### Pass Criteria
- `show ip access-lists` does NOT show "aac"
- No errors during `no ip access-list` execution
- Running-config grep for "aac" returns empty

---

## Test Case 6: SM_ISCLI_P2_145.6 - Global ACL with Different Rule Variants

### Objective
Verify that global ACL works with different deny/permit rule patterns.

### Steps (Run 3 sub-tests, all on DUT1)

### Sub-test 6.1: Deny Any-to-Any
```
configure terminal
ip access-list test_deny_any
seq 1 deny ip any any
exit
ip access-group test_deny_any in
exit
```
- **Test**: Send traffic from 172.0.0.2→173.0.0.2 via DUT1:Ethernet0
- **Verify**: All packets blocked (zero RX on DUT1:Ethernet16)

### Sub-test 6.2: Permit Specific, Deny Rest
```
configure terminal
ip access-list test_permit_specific
seq 1 permit ip host 173.0.0.2 host 172.0.0.2
seq 2 deny ip any any
exit
no ip access-group test_deny_any in
ip access-group test_permit_specific in
exit
```
- **Test**: Send traffic from 172.0.0.2→173.0.0.2 via DUT1:Ethernet0
- **Verify**: Traffic blocked (deny any-to-any except reverse direction)
- **Reverse test**: 173.0.0.2→172.0.0.2 should be permitted

### Sub-test 6.3: Deny Protocol-Specific (ICMP)
```
configure terminal
ip access-list test_deny_icmp
seq 1 deny icmp any any
seq 2 permit ip any any
exit
no ip access-group test_permit_specific in
ip access-group test_deny_icmp in
exit
```
- **Test**: Send ICMP traffic (ping) from 172.0.0.2→173.0.0.2
- **Verify**: ICMP packets blocked, IP traffic permitted
- **Test**: Send TCP/UDP traffic
- **Verify**: TCP/UDP passes through (seq 2 permit)

### Validation
- Each rule variant applies correctly in global mode
- Traffic matches expected permit/deny behavior
- No conflicts or unexpected side effects

### Pass Criteria
- All 3 rule variants work as expected
- Traffic filtering matches rule intention
- No rollover/interference between rule changes

---

## Test Case 7: SM_ISCLI_P2_145.7 - Pagination Handling in Show Commands

### Objective
Verify that `--more` pagination is handled correctly when displaying large ACLs or configurations.

### Steps

1. **Create large ACL with multiple rules** (D1)
   ```
   configure terminal
   ip access-list large_acl
   seq 1 deny ip host 172.0.0.2 any
   seq 5 deny ip host 172.0.0.3 any
   seq 10 deny ip host 172.0.0.4 any
   seq 15 deny ip host 172.0.0.5 any
   seq 20 permit ip any any
   exit
   ip access-group large_acl in
   exit
   ```

2. **Display ACL with pagination** (D1)
   ```
   show ip access-lists large_acl
   show running-config | grep -A 50 "ip access-list large_acl"
   ```

   **Expected**: Output should handle `--more` gracefully (if output spans multiple screens)

3. **Verify all rules appear** (D1)
   ```
   show ip access-lists large_acl detailed
   ```

   **Expected Output**:
   ```
   IP Access-List large_acl:
       seq 1 deny ip host 172.0.0.2 any
       seq 5 deny ip host 172.0.0.3 any
       seq 10 deny ip host 172.0.0.4 any
       seq 15 deny ip host 172.0.0.5 any
       seq 20 permit ip any any
   ```

### Validation
- All 5 rules visible in output
- No truncation of rule details
- Pagination handling works without hanging/errors
- CLI responds correctly to page-down/space key

### Pass Criteria
- All rules displayed completely
- No text wrapping or corruption
- Show commands complete successfully
- Detailed view matches configuration

---

## Expected Results Summary

| Test Case | Scenario | Expected Result | Pass/Fail |
|-----------|----------|-----------------|-----------|
| TC1 | Create ACL with deny rule | ACL created, rule visible in show output | PASS if ACL exists |
| TC2 | Apply ACL globally | `ip access-group aac in` in running-config | PASS if config persists |
| TC3 | Verify traffic denial | RX count = 0 packets, ACL hits = 100 | PASS if traffic blocked |
| TC4 | Interface vs Global | Interface ACL still works after global removal | PASS if both modes work |
| TC5 | Cleanup ACL | ACL removed, no orphaned configs | PASS if clean removal |
| TC6 | Rule variants | Multiple rule patterns work in global mode | PASS if all variants work |
| TC7 | Pagination | Large ACLs display with `--more` handling | PASS if all rules visible |

---

## Known Issues / Notes

- **Global ACL vs Interface ACL**: Global mode should NOT override interface mode; both should work independently
- **Direction**: `in` (ingress) is tested; `out` (egress) may need separate test
- **VRF**: Test assumes default VRF; may need VRF-specific tests separately
- **Management IP**: NOT changed during this test (per requirement)
- **Persistence**: Test should verify config survives DUT reboot (optional extended test)

---

## Automation Hints

### Python/Scapy Traffic Generation
```python
from scapy.all import Ether, IP, ICMP, sendp

def send_test_traffic(interface, src_ip, dst_ip, count=100, interval=0.1):
    """Send Scapy-based IP traffic"""
    packets = [
        IP(src=src_ip, dst=dst_ip) / ICMP()
        for _ in range(count)
    ]
    sendp(packets, iface=interface, inter=interval)
    return len(packets)
```

### Tcpdump Capture
```bash
# Start capture in background
sudo tcpdump -i <interface> -w <pcap_file> <filter> > /dev/null 2>&1 &
TCPDUMP_PID=$!

# Wait for traffic
sleep 15

# Stop capture
sudo kill $TCPDUMP_PID
sleep 1

# Count packets
sudo python3 -c "from scapy.all import rdpcap; print(len(rdpcap('<pcap_file>')))"
```

### ACL Verification
```bash
# Check ACL exists
show ip access-lists aac

# Check global binding
show running-config | grep "ip access-group"

# Check ACL counters
show ip access-lists aac detailed
```

---

## References

- **SONiC CLI Docs**: https://github.com/sonic-net/sonic-buildimage/wiki
- **ACL Feature**: IPv4/IPv6 Access Control Lists
- **Testbed**: testbeds/testbed_acl_vs.yaml (similar topology)
- **Related Tests**: test_l3_acl.py, test_l2_acl.py

---

## Revision History

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-04-29 | Claude Code | 1.0 | Initial test case design for SM_ISCLI_P2_145 |

