# L2-02 Execution Guide
## MAC ACL - Deny Exact Source MAC (Manual Device Testing)

**Date**: 2026-04-25
**Status**: ✓ Documentation Complete - Ready for Manual Execution
**Test Case**: L2-02 (Inverse of L2-01)
**Device**: DUT1 (8011) at 192.168.100.137
**CLI**: sonic-cli (klish mode)

---

## Quick Summary

**L2-02 Purpose**: Verify MAC ACL correctly **blocks** traffic from a specific source MAC while **allowing** all others.

**Test Type**: Inverse of L2-01
- **L2-01** (PERMIT): Allows source MAC 00:AA:AA:AA:AA:01 → Denies all others (implicit)
- **L2-02** (DENY): Denies source MAC 00:AA:AA:AA:AA:01 → Allows all others (explicit rule 20)

**Execution Time**: ~15 minutes total
**Pass Criteria**: Both test scenarios PASS

---

## Step-by-Step Execution

### Step 1: SSH to Device

```bash
ssh admin@192.168.100.137
```

**Expected Output**:
```
admin@dut1's password:
Last login: [date/time]
admin@dut1:~$
```

---

### Step 2: Enter CLI

```bash
sonic-cli
```

**Expected Output**:
```
sonic#
```

---

### Step 3: Copy-Paste Complete Configuration

Select the entire block below and paste into CLI at `sonic#` prompt:

```
configure terminal
vlan 10
interface Ethernet 272
  switchport access vlan 10
exit
interface Ethernet 513
  switchport access vlan 10
exit
mac access-list test-l2-02
  seq 10 deny host 00:AA:AA:AA:AA:01 any
  seq 20 permit any any
exit
interface Ethernet 272
  mac access-group test-l2-02 in
exit
exit
```

**Expected Output** (after configuration):
- No error messages
- Returns to `sonic#` prompt after final `exit`

---

### Step 4: Verify Configuration (4 Show Commands)

Run these commands one at a time to verify configuration:

#### Command 1: Show MAC ACL Rules

```
show mac access-lists
```

**Expected Output**:
```
MAC Access Lists
  Name: test-l2-02
    seq 10 deny host 00:AA:AA:AA:AA:01 any
    seq 20 permit any any
```

✓ **Verify**: Both rules present - rule 10 (deny) and rule 20 (permit)

---

#### Command 2: Show ACL Bindings

```
show mac access-group
```

**Expected Output**:
```
Interface Ethernet272:
  Ingress:  test-l2-02
```

✓ **Verify**: ACL bound to Ethernet272, direction is Ingress (in)

---

#### Command 3: Show Interface Configuration

```
show running-config interface Ethernet 272
```

**Expected Output** (should include):
```
interface Ethernet 272
  switchport access vlan 10
  mac access-group test-l2-02 in
```

✓ **Verify**: Interface in VLAN 10 with ACL applied

---

#### Command 4: Show VLAN Membership

```
show vlan id 10
```

**Expected Output**:
```
VLAN: 10
Ports: Ethernet272, Ethernet513
```

✓ **Verify**: Both test ports in same VLAN

---

## Traffic Testing

Configuration is now ready for traffic testing. Two test scenarios required:

### Test Scenario 1: Send DENIED Source MAC

**Purpose**: Verify ACL rule 10 blocks traffic from 00:AA:AA:AA:AA:01

**TX Configuration**:
- Source MAC: `00:AA:AA:AA:AA:01` (MATCHES rule 10 → DENY)
- Destination MAC: `00:BB:BB:BB:BB:02`
- VLAN ID: `10`
- TX Port: Ethernet272 (ingress)
- Packet Count: `10`
- Interval: `50ms` between packets

**Expected Result**:
- TX: 10 packets sent
- RX: **0 packets received** (all dropped by rule 10)
- Test Result: **PASS ✓**

**Why 0 RX**:
```
Traffic Flow:
  1. Packet arrives at Ethernet272 (ingress)
  2. ACL checks rule 10: deny host 00:AA:AA:AA:AA:01 any
  3. Source MAC matches 00:AA:AA:AA:AA:01 → ACTION = DENY
  4. Packet is DROPPED (not forwarded)
  5. Rule 20 never checked (rule 10 already matched)
  6. Ethernet513 receives ZERO packets
```

**Python Scapy Code**:

```python
from scapy.all import *
import time

# Configuration - DENIED SOURCE MAC
SRC_MAC = "00:AA:AA:AA:AA:01"  # This will be DENIED by rule 10
DST_MAC = "00:BB:BB:BB:BB:02"
VLAN_ID = 10
TX_IFACE = "eth0"  # Your TX interface
TX_COUNT = 10
INTERVAL = 0.05

# Build packet with VLAN tag
packet = Ether(src=SRC_MAC, dst=DST_MAC) / Dot1Q(vlan=VLAN_ID) / IP(src="10.0.0.1", dst="20.0.0.2") / ICMP()

# Transmit
print(f"Test 1: Sending {TX_COUNT} packets with DENIED source MAC {SRC_MAC}...")
for i in range(TX_COUNT):
    sendp(packet, iface=TX_IFACE, verbose=False)
    time.sleep(INTERVAL)
    print(f"  Sent packet {i+1}/{TX_COUNT}")

print("✓ Transmission complete!")
print(f"Expected RX: 0 packets (all dropped by rule 10)")
print(f"Test Result: PASS ✓ (if RX = 0)")
```

---

### Test Scenario 2: Send ALLOWED Source MAC

**Purpose**: Verify ACL rule 20 allows traffic from different MAC addresses

**TX Configuration**:
- Source MAC: `00:CC:CC:CC:CC:CC` (different from denied MAC - NOT matched by rule 10)
- Destination MAC: `00:BB:BB:BB:BB:02`
- VLAN ID: `10`
- TX Port: Ethernet272 (ingress)
- Packet Count: `10`
- Interval: `50ms` between packets

**Expected Result**:
- TX: 10 packets sent
- RX: **≥ 9 packets received** (90% pass threshold; allowed by rule 20)
- Test Result: **PASS ✓**

**Why ≥9 RX**:
```
Traffic Flow:
  1. Packet arrives at Ethernet272 (ingress)
  2. ACL checks rule 10: deny host 00:AA:AA:AA:AA:01 any
  3. Source MAC is 00:CC:CC:CC:CC:CC (different) → NO MATCH
  4. Continue to rule 20: permit any any
  5. Source MAC matches any → ACTION = PERMIT
  6. Packet is FORWARDED to Ethernet513
  7. Ethernet513 receives the packet
```

**Python Scapy Code**:

```python
from scapy.all import *
import time

# Configuration - DIFFERENT SOURCE MAC (NOT denied)
SRC_MAC = "00:CC:CC:CC:CC:CC"  # Different from denied MAC → Matches rule 20 (permit)
DST_MAC = "00:BB:BB:BB:BB:02"
VLAN_ID = 10
TX_IFACE = "eth0"  # Your TX interface
TX_COUNT = 10
INTERVAL = 0.05

# Build packet
packet = Ether(src=SRC_MAC, dst=DST_MAC) / Dot1Q(vlan=VLAN_ID) / IP(src="10.0.0.1", dst="20.0.0.2") / ICMP()

# Transmit
print(f"Test 2: Sending {TX_COUNT} packets with ALLOWED source MAC {SRC_MAC}...")
for i in range(TX_COUNT):
    sendp(packet, iface=TX_IFACE, verbose=False)
    time.sleep(INTERVAL)
    print(f"  Sent packet {i+1}/{TX_COUNT}")

print("✓ Transmission complete!")
print(f"Expected RX: ≥ 9 packets (allowed by rule 20 - catch-all permit)")
print(f"Test Result: PASS ✓ (if RX ≥ 9)")
```

---

## Why Rule 20 Is Critical

### Without Rule 20:
```
Configuration:
  seq 10 deny host 00:AA:AA:AA:AA:01 any
  (No rule 20)

Behavior:
  ├─ Traffic with src MAC 00:AA:AA:AA:AA:01
  │  └─ Rule 10 matches → DENY ✓ (correct)
  │
  └─ Traffic with other src MACs
     └─ NO rules match → Implicit DENY ✗ (WRONG!)
     └─ ALL other traffic also blocked (bad!)
```

### With Rule 20 (Correct):
```
Configuration:
  seq 10 deny host 00:AA:AA:AA:AA:01 any
  seq 20 permit any any

Behavior:
  ├─ Traffic with src MAC 00:AA:AA:AA:AA:01
  │  └─ Rule 10 matches → DENY ✓ (blocks denied MAC)
  │
  └─ Traffic with other src MACs
     └─ Rule 10 no match
     └─ Rule 20 matches → PERMIT ✓ (allows other MACs)
```

**Key Principle**: DENY rules require explicit catch-all PERMIT for other traffic.

---

## Comparison: L2-01 vs L2-02

| Aspect | L2-01 (PERMIT) | L2-02 (DENY) |
|--------|---|---|
| **Rule 10 Action** | `permit` | `deny` |
| **Rule 10 Effect** | Allow 00:AA:AA:AA:AA:01 | Block 00:AA:AA:AA:AA:01 |
| **Rule 20** | None (implicit deny) | `permit any any` (catch-all) |
| **Test 1 MAC** | 00:AA:AA:AA:AA:01 | 00:AA:AA:AA:AA:01 |
| **Test 1 Expected RX** | ≥ 9 packets | 0 packets |
| **Test 2 MAC** | (not tested) | 00:CC:CC:CC:CC:CC |
| **Test 2 Expected RX** | (not tested) | ≥ 9 packets |
| **Total Tests** | 1 scenario | 2 scenarios |
| **Test Result** | PASS if RX ≥9 | PASS if both scenarios pass |

---

## Troubleshooting

### Issue: Traffic with denied MAC still passing through

**Cause**: ACL not bound to interface or rule is wrong
**Solution**:
1. Verify ACL binding: `show mac access-group` (should show Ethernet272:Ingress)
2. Verify rule syntax: `show mac access-lists test-l2-02` (should show `deny host 00:AA:AA:AA:AA:01 any`)
3. Verify interface config: `show running-config interface Ethernet 272` (should have `mac access-group test-l2-02 in`)

---

### Issue: All traffic blocked (even allowed MACs)

**Cause**: Missing rule 20 (catch-all permit)
**Solution**:
```
configure terminal
mac access-list test-l2-02
  seq 20 permit any any
exit
exit
```

Then re-verify with `show mac access-lists test-l2-02`

---

### Issue: ACL configuration fails with syntax error

**Cause**: Wrong syntax (using old `source-mac` pattern)
**Solution**: Use correct syntax with `host` keyword:
```
✓ CORRECT:   seq 10 deny host 00:AA:AA:AA:AA:01 any
❌ WRONG:    seq 10 deny source-mac 00:AA:AA:AA:AA:01
```

---

## Cleanup (Optional - After Testing)

### Remove ACL Rules

```
configure terminal
mac access-list test-l2-02
  no seq 10
  no seq 20
exit
exit
```

### Remove ACL from Interface

```
configure terminal
interface Ethernet 272
  no mac access-group test-l2-02 in
exit
exit
```

### Delete Entire ACL

```
configure terminal
no mac access-list test-l2-02
exit
```

### Remove Ports from VLAN

```
configure terminal
interface Ethernet 272
  no switchport access vlan
exit
interface Ethernet 513
  no switchport access vlan
exit
exit
```

### Delete VLAN (Optional)

```
configure terminal
no vlan 10
exit
```

---

## Summary Checklist

### Pre-Configuration
- [ ] SSH connectivity to DUT1 (192.168.100.137) verified
- [ ] Both Ethernet272 and Ethernet513 are UP
- [ ] No existing L2-02 configuration (optional cleanup first)

### Configuration
- [ ] Pasted complete configuration block without errors
- [ ] No error messages in CLI

### Verification (4 Commands)
- [ ] `show mac access-lists` shows both rules (10 and 20)
- [ ] `show mac access-group` shows Ethernet272:Ingress
- [ ] `show running-config interface Ethernet 272` shows ACL binding
- [ ] `show vlan id 10` shows both ports in VLAN 10

### Test Scenario 1 (Denied MAC)
- [ ] Sent 10 packets with src MAC 00:AA:AA:AA:AA:01
- [ ] RX Count: **0 packets** (all dropped)
- [ ] Result: **PASS ✓**

### Test Scenario 2 (Allowed MAC)
- [ ] Sent 10 packets with src MAC 00:CC:CC:CC:CC:CC
- [ ] RX Count: **≥ 9 packets** (allowed by rule 20)
- [ ] Result: **PASS ✓**

### Final Status
- [ ] Both test scenarios PASSED
- [ ] L2-02 Test Case: **COMPLETE ✓**

---

## Related Test Cases

- **L2-01**: Permit exact source MAC (inverse - allows the MAC)
- **L2-03**: Could test with EtherType matching
- **L2-04**: Could test destination MAC matching
- **L2-05**: Could test VLAN-based matching

---

**Document Created**: 2026-04-25
**Status**: ✓ READY FOR MANUAL EXECUTION
**Test Duration**: ~15 minutes (configuration + both test scenarios)
**Next Steps**: Execute on DUT1 and document results
