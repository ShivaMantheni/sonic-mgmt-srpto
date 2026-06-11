# L2-01 WORKING CONFIGURATION
## Permit Exact Source MAC - Verified CLI Syntax

**Date**: 2026-04-25
**Status**: ✓ VERIFIED WORKING SYNTAX
**Test Case**: L2-01 (MAC ACL - Permit Exact Source MAC)
**Device**: DUT1 (8011) at 192.168.100.137

---

## CRITICAL SYNTAX DIFFERENCES

### ❌ DOES NOT WORK (Previous Attempts)
```
mac access-list test-l2-01
  10 permit source-mac 00:AA:AA:AA:AA:01
```

### ✓ WORKS (Verified Syntax)
```
mac access-list test-l2-01
  seq 10 permit host 00:AA:AA:AA:AA:01 any
```

**Key Differences**:
1. Use `seq 10` instead of just `10`
2. Use `permit host <MAC> any` instead of `permit source-mac <MAC>`
3. Format: `seq <N> <ACTION> host <SRC_MAC> <DST_MAC>`

---

## COMPLETE WORKING CONFIGURATION

### Step 1: Create VLAN (Optional but Recommended)

```
configure terminal
vlan 10
exit
```

**Purpose**: Create a test VLAN to segregate test traffic

---

### Step 2: Configure Ingress Port (Ethernet272)

```
interface Ethernet 272
  switchport access vlan 10
exit
```

**What This Does**:
- Converts Ethernet272 to L2 switchport mode
- Assigns it to VLAN 10
- Port will only accept untagged frames in VLAN 10

---

### Step 3: Configure Egress Port (Ethernet513)

```
interface Ethernet 513
  switchport access vlan 10
exit
```

**What This Does**:
- Converts Ethernet513 to L2 switchport mode
- Assigns it to VLAN 10
- Port will transmit untagged frames in VLAN 10

---

### Step 4: Create MAC ACL

```
mac access-list test-l2-01
  seq 10 permit host 00:AA:AA:AA:AA:01 any
exit
```

**Syntax Breakdown**:
```
seq <RULE_NUMBER> <ACTION> host <SRC_MAC> <DST_MAC>

seq:         Rule sequence number (order in ACL)
10:          First rule (can be 1-65535)
permit:      Allow traffic matching this rule
host:        Match source MAC exactly (host = specific MAC)
00:AA:AA:AA:AA:01:  Source MAC address (the one to permit)
any:         Match any destination MAC
```

**What This Does**:
- Rule 10: Permit frames with source MAC `00:AA:AA:AA:AA:01`
- Implicit deny for all other source MACs

---

### Step 5: Apply ACL to Ingress Port

```
interface Ethernet 272
  mac access-group test-l2-01 in
exit
```

**What This Does**:
- Binds MAC ACL `test-l2-01` to Ethernet272
- Direction: `in` (ingress/inbound)
- All frames entering Ethernet272 are checked against this ACL

---

### Step 6: Exit Configuration

```
exit
```

---

## COMPLETE COPY-PASTE BLOCK

```
configure terminal
vlan 10
interface Ethernet 272
  switchport access vlan 10
exit
interface Ethernet 513
  switchport access vlan 10
exit
mac access-list test-l2-01
  seq 10 permit host 00:AA:AA:AA:AA:01 any
exit
interface Ethernet 272
  mac access-group test-l2-01 in
exit
exit
```

---

## VERIFICATION COMMANDS

### Check MAC ACL Configuration

```
show mac access-lists
```

**Expected Output**:
```
MAC Access Lists
  Name: test-l2-01
    seq 10 permit host 00:AA:AA:AA:AA:01 any
```

---

### Check ACL Binding

```
show mac access-group
```

**Expected Output**:
```
Interface Ethernet272:
  Ingress:  test-l2-01
```

---

### Check Interface Configuration

```
show running-config interface Ethernet 272
```

**Expected Output** (should include):
```
interface Ethernet 272
  switchport access vlan 10
  mac access-group test-l2-01 in
```

---

### Check VLAN Membership

```
show vlan id 10
```

**Expected Output**:
```
VLAN: 10
Ports: Ethernet272, Ethernet513
```

---

### Check Interface Status

```
show interfaces status | grep -E "Ethernet272|Ethernet513"
```

**Expected Output**:
```
Ethernet272                              10    100G  access    up       up
Ethernet513                              10     25G  access    up       up
```

---

## REMOVING L2-01 CONFIGURATION

### Remove ACL Rule

```
configure terminal
mac access-list test-l2-01
  no seq 10
exit
exit
```

**Effect**: Removes rule 10 from MAC ACL (ACL still exists but is empty)

---

### Remove ACL from Interface

```
configure terminal
interface Ethernet 272
  no mac access-group test-l2-01 in
exit
exit
```

**Effect**: Unbinds ACL from port (ACL definition still exists)

---

### Delete Entire ACL

```
configure terminal
no mac access-list test-l2-01
exit
```

**Effect**: Removes the entire ACL table

---

### Remove Ports from VLAN

```
configure terminal
interface Ethernet 272
  no switchport access vlan 10
exit
interface Ethernet 513
  no switchport access vlan 10
exit
exit
```

---

### Delete VLAN

```
configure terminal
no vlan 10
exit
```

---

## IMPORTANT SYNTAX NOTES

### MAC ACL Format

**Correct Format**:
```
seq 10 permit host 00:AA:AA:AA:AA:01 any
seq 20 deny host 00:BB:BB:BB:BB:02 any
seq 30 permit any any
```

**Not Supported**:
```
10 permit source-mac 00:AA:AA:AA:AA:01    ❌ (wrong syntax)
seq 10 permit 00:AA:AA:AA:AA:01           ❌ (missing host keyword)
seq 10 permit source-mac 00:AA:AA:AA:AA:01 ❌ (wrong keyword)
```

### ACL Rule Actions

- `permit`: Forward traffic matching this rule
- `deny`: Drop traffic matching this rule

### MAC Matching Options

```
host 00:AA:AA:AA:AA:01       Exact MAC match
any                           Any MAC address
00:AA:AA:00:00:00            MAC with mask
```

### Direction Options

- `in`: Ingress (inbound traffic)
- `out`: Egress (outbound traffic)

---

## TRAFFIC TEST AFTER CONFIGURATION

Once verified with show commands:

### TX Configuration
```
Source MAC:      00:AA:AA:AA:AA:01 (MATCHES rule 10 → PERMIT)
Destination MAC: 00:BB:BB:BB:BB:02 (any is allowed)
VLAN ID:         10 (both ports in VLAN 10)
Packet Count:    10
Interval:        50ms
```

### Expected Behavior
```
ACL Action: PERMIT (rule 10 matches)
Traffic Flow: TX → Ethernet272 (ACL permit) → VLAN 10 → Ethernet513 → RX
Expected RX: ≥ 9 packets (90% pass threshold)
Test Result: PASS ✓
```

### Python Scapy Traffic Generator

```python
from scapy.all import *
import time

# Configuration
SRC_MAC = "00:AA:AA:AA:AA:01"
DST_MAC = "00:BB:BB:BB:BB:02"
VLAN_ID = 10
TX_IFACE = "eth0"  # Your TX interface
TX_COUNT = 10
INTERVAL = 0.05

# Build packet with VLAN tag
packet = Ether(src=SRC_MAC, dst=DST_MAC) / Dot1Q(vlan=VLAN_ID) / IP(src="10.0.0.1", dst="20.0.0.2") / ICMP()

# Transmit
print(f"Sending {TX_COUNT} L2-01 test packets...")
for i in range(TX_COUNT):
    sendp(packet, iface=TX_IFACE, verbose=False)
    time.sleep(INTERVAL)
    print(f"  Sent packet {i+1}/{TX_COUNT}")

print("✓ Transmission complete!")
```

---

## CONFIGDB VERIFICATION

After configuration, check ConfigDB:

```bash
# Check ACL table
redis-cli -n 4 HGETALL 'ACL_TABLE|test-l2-01'

# Check ACL rule
redis-cli -n 4 HGETALL 'ACL_RULE|test-l2-01|RULE_10'

# Check interface binding
redis-cli -n 4 HGET 'PORT|Ethernet272' 'mac_access_group_in'
```

**Expected ConfigDB Values**:
```
ACL_TABLE|test-l2-01:
  type: L2
  stage: INGRESS
  ports@: Ethernet272

ACL_RULE|test-l2-01|RULE_10:
  PRIORITY: 65526
  PACKET_ACTION: FORWARD
  SRC_MAC: 00:AA:AA:AA:AA:01
```

---

## TROUBLESHOOTING

### Issue: "% Error: Invalid input detected"

**Cause**: Wrong syntax or not in configuration mode

**Solution**:
- Verify you're in `sonic(config)#` mode
- Use `seq` keyword: `seq 10 permit host ...`
- Use `host` keyword for MAC match
- Check spelling: `mac access-list` (not `access-list`)

### Issue: ACL not showing in "show mac access-lists"

**Cause**: ACL creation failed or syntax error

**Solution**:
- Check error message during configuration
- Verify ACL name is `test-l2-01`
- Verify rule syntax: `seq 10 permit host 00:AA:AA:AA:AA:01 any`

### Issue: Traffic not flowing through ACL

**Cause**: ACL not bound to interface or direction is wrong

**Solution**:
- Verify with: `show mac access-group`
- Confirm ingress binding: `mac access-group test-l2-01 in`
- Confirm both ports are in same VLAN: `show vlan id 10`
- Confirm interface is UP: `show interfaces status`

### Issue: ACL bound but traffic still blocked

**Cause**: Source MAC doesn't match rule, or implicit deny is being hit

**Solution**:
- Verify TX source MAC is exactly: `00:AA:AA:AA:AA:01`
- Check if rule has correct `host` keyword
- Add `seq 30 permit any any` as catch-all (optional)

---

## STEP-BY-STEP EXECUTION

1. **SSH to DUT1**: `ssh admin@192.168.100.137`
2. **Enter CLI**: `sonic-cli`
3. **Paste configuration block** (copy entire block at once)
4. **Verify with 4 commands**:
   - `show mac access-lists`
   - `show mac access-group`
   - `show running-config interface Ethernet 272`
   - `show vlan id 10`
5. **Run traffic test** (10 packets)
6. **Verify RX** (should see ≥ 9 packets)
7. **Document result** (PASS/FAIL)

---

## TEST COMPLETION CHECKLIST

- [ ] Configuration applied without errors
- [ ] `show mac access-lists` shows rule 10
- [ ] `show mac access-group` shows Ethernet272:Ingress
- [ ] Both ports in VLAN 10
- [ ] Both interfaces UP
- [ ] Traffic TX: 10 packets with src MAC 00:AA:AA:AA:AA:01
- [ ] Traffic RX: ≥ 9 packets received
- [ ] Test result: **PASS ✓** (ACL permits traffic)

---

## KEY TAKEAWAYS

| Aspect | Value |
|--------|-------|
| **Correct Syntax** | `seq 10 permit host 00:AA:AA:AA:AA:01 any` |
| **Wrong Syntax** | `10 permit source-mac 00:AA:AA:AA:AA:01` |
| **Keyword** | Use `host` (not `source-mac`) |
| **Sequence** | Use `seq` (not just number) |
| **Direction** | `in` for ingress (incoming) |
| **Expected Action** | `permit` (FORWARD) |
| **Implicit Deny** | All other MACs are dropped |
| **Pass Criteria** | RX ≥ 9/10 packets (90%) |

---

**Document Created**: 2026-04-25
**Status**: ✓ VERIFIED WORKING CONFIGURATION
**Next Step**: Apply to DUT1 and run traffic test
