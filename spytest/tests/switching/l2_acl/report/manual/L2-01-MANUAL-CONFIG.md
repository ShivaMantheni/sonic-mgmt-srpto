# L2-01 Manual Configuration Guide
## Permit Exact Source MAC - Complete Command Reference

**Test Case**: L2-01
**Date**: 2026-04-25
**Configuration Type**: Manual (via sonic-cli terminal)

---

## Quick Reference - Copy/Paste Commands

### Step 1: SSH to DUT1 (8011)

```bash
ssh admin@192.168.100.137
Password: sonic@123
```

---

### Step 2: Enter sonic-cli

```bash
sonic-cli
```

Expected output:
```
sonic#
```

---

### Step 3: Complete Configuration (Copy all lines below)

```
configure terminal
int Ethernet272
  switchport mode access
exit
int Ethernet513
  switchport mode access
exit
mac access-list test-l2-01
  10 permit source-mac 00:AA:AA:AA:AA:01
exit
int Ethernet272
  mac access-group test-l2-01 in
exit
exit
```

---

## Detailed Step-by-Step Instructions

### **PHASE 1: CONNECT TO DEVICE**

#### Command:
```bash
ssh admin@192.168.100.137
```

#### When Prompted:
```
Password: sonic@123
```

#### Expected Output:
```
Linux sonic 6.1.0-29-2-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.123-1 (2025-01-02) x86_64
You are on
  ____   ___  _   _ _  ____
 / ___| / _ \| \ | (_)/ ___|
 \___ \| | | |  \| | | |
  ___) | |_| | |\  | | |___
 |____/ \___/|_| \_|_|\____|

-- Software for Open Networking in the Cloud --

Last login: Sat Apr 25 10:31:39 2026 from 192.168.100.175
[01;32madmin@sonic[00m:[01;34m~[00m$
```

---

### **PHASE 2: ENTER sonic-cli**

#### Command:
```
sonic-cli
```

#### Expected Output:
```
sonic#
```

---

### **PHASE 3: CONFIGURE SWITCHPORT MODE**

#### Step 3.1 - Enter Configuration Terminal

```
configure terminal
```

**Expected Output:**
```
sonic(config)#
```

---

#### Step 3.2 - Configure Ethernet272 (Ingress Port)

```
int Ethernet272
```

**Expected Output:**
```
sonic(config-if)#
```

Configure as L2 switchport:
```
switchport mode access
```

**Expected Output:**
```
sonic(config-if)#
```

Exit interface configuration:
```
exit
```

**Expected Output:**
```
sonic(config)#
```

---

#### Step 3.3 - Configure Ethernet513 (Egress Port)

```
int Ethernet513
```

**Expected Output:**
```
sonic(config-if)#
```

Configure as L2 switchport:
```
switchport mode access
```

**Expected Output:**
```
sonic(config-if)#
```

Exit interface configuration:
```
exit
```

**Expected Output:**
```
sonic(config)#
```

---

### **PHASE 4: CREATE MAC ACL**

#### Step 4.1 - Create MAC Access List

```
mac access-list test-l2-01
```

**Expected Output:**
```
sonic(config-macl)#
```

#### Step 4.2 - Add Permit Rule for Source MAC

```
10 permit source-mac 00:AA:AA:AA:AA:01
```

**Expected Output:**
```
sonic(config-macl)#
```

Exit MAC ACL configuration:
```
exit
```

**Expected Output:**
```
sonic(config)#
```

---

### **PHASE 5: APPLY ACL TO INTERFACE**

#### Step 5.1 - Enter Ethernet272 Configuration

```
int Ethernet272
```

**Expected Output:**
```
sonic(config-if)#
```

#### Step 5.2 - Apply MAC ACL to Ingress

```
mac access-group test-l2-01 in
```

**Expected Output:**
```
sonic(config-if)#
```

Exit interface configuration:
```
exit
```

**Expected Output:**
```
sonic(config)#
```

---

### **PHASE 6: EXIT CONFIGURATION MODE**

```
exit
```

**Expected Output:**
```
sonic#
```

---

## Verification Commands

### **Command 1: Verify MAC ACL Rules**

```
show mac access-list
```

**Expected Output:**
```
sonic# show mac access-list
MAC Access Lists
  Name: test-l2-01
    10 permit source-mac 00:AA:AA:AA:AA:01
```

---

### **Command 2: Verify Ethernet272 Configuration**

```
show running-config interface Ethernet 272 | include access-group
```

**Expected Output:**
```
sonic# show running-config interface Ethernet 272 | include access-group
  mac access-group test-l2-01 in
```

---

### **Command 3: Verify Ethernet513 Configuration**

```
show running-config interface Ethernet 513 | include switchport
```

**Expected Output:**
```
sonic# show running-config interface Ethernet 513 | include switchport
  switchport mode access
```

---

### **Command 4: Verify Ethernet272 Switchport Mode**

```
show running-config interface Ethernet 272 | include switchport
```

**Expected Output:**
```
sonic# show running-config interface Ethernet 272 | include switchport
  switchport mode access
```

---

### **Command 5: Show All Interface Details**

```
show interfaces status | grep -E "Ethernet272|Ethernet513"
```

**Expected Output:**
```
sonic# show interfaces status | grep -E "Ethernet272|Ethernet513"
Ethernet272                  161,162,163,164     100G   9100     rs    Eth37    1      up       up
Ethernet513                              513      25G   9100   none    Eth98    1      up       up
```

---

## Configuration Summary Table

| Item | Configuration |
|------|----------------|
| **Interface 1** | Ethernet272 (port37) |
| **Interface 1 Mode** | switchport mode access |
| **Interface 2** | Ethernet513 (port98) |
| **Interface 2 Mode** | switchport mode access |
| **ACL Name** | test-l2-01 |
| **ACL Rule 10** | permit source-mac 00:AA:AA:AA:AA:01 |
| **ACL Application** | int Ethernet272, mac access-group test-l2-01 in |

---

## Common Issues & Solutions

### **Issue 1: Command Not Found**
```
sonic(config)# int Ethernet272
% Unknown command.
```

**Solution**: Make sure you're in `configure terminal` mode. Verify prompt shows `sonic(config)#`

---

### **Issue 2: Invalid Input Detected**
```
sonic(config)# interface Ethernet 272
% Error: Invalid input detected at "^" marker.
```

**Solution**: Use abbreviated command `int` instead of `interface`

---

### **Issue 3: ACL Rule Not Showing**
```
sonic# show mac access-list
[No output]
```

**Solution**: Verify you typed `mac access-list test-l2-01` (not `access-list`)

---

### **Issue 4: Cannot Apply ACL**
```
sonic(config-if)# mac access-group test-l2-01 in
% Error: Invalid input detected at "^" marker.
```

**Solution**:
- Make sure interface is in switchport mode first
- Verify you're in interface config mode `sonic(config-if)#`
- Verify ACL was created with `show mac access-list`

---

## Post-Configuration Checklist

After completing all configuration steps, verify with these commands:

- [ ] `show mac access-list` shows rule 10 with permit source-mac 00:AA:AA:AA:AA:01
- [ ] `show running-config interface Ethernet 272` shows `mac access-group test-l2-01 in`
- [ ] `show running-config interface Ethernet 272` shows `switchport mode access`
- [ ] `show running-config interface Ethernet 513` shows `switchport mode access`
- [ ] `show interfaces status` shows both Ethernet272 and Ethernet513 UP

---

## Saving Configuration

To save the configuration persistently (optional):

```
exit
write memory
```

Or use copy command:

```
copy running-config startup-config
```

---

## Complete Configuration Script (All-in-One)

If you want to paste everything at once, use this script:

```
configure terminal
int Ethernet272
switchport mode access
exit
int Ethernet513
switchport mode access
exit
mac access-list test-l2-01
10 permit source-mac 00:AA:AA:AA:AA:01
exit
int Ethernet272
mac access-group test-l2-01 in
exit
exit
show mac access-list
show running-config interface Ethernet 272 | include access-group
show running-config interface Ethernet 513 | include switchport
```

---

## Network Diagram - Configuration Points

```
┌──────────────────────────────────────────────────────────────┐
│                        DUT1 (8011)                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Ethernet272 [100G, port37]                                 │
│  ├─ switchport mode access          ← CONFIGURE              │
│  ├─ mac access-group test-l2-01 in  ← APPLY ACL             │
│  └─ Connected to: DUT2:Ethernet48                            │
│                                                               │
│  Ethernet513 [25G, port98]                                  │
│  ├─ switchport mode access          ← CONFIGURE              │
│  └─ Connected to: DUT3:Ethernet513                           │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  MAC Access List: test-l2-01                                │
│  ├─ Rule 10: permit source-mac 00:AA:AA:AA:AA:01  ← CREATE  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Test Execution After Configuration

Once configuration is complete, proceed to:

1. **Start RX Capture** on DUT1:Ethernet513
2. **Generate TX Traffic** with permitted source MAC: 00:AA:AA:AA:AA:01
3. **Verify RX Count** - Should receive ≥ 9/10 packets (90% pass threshold)
4. **ACL Behavior** - PERMIT (forward frames from this MAC)

---

## Support Commands

If you need to undo configuration:

```
configure terminal
int Ethernet272
no mac access-group test-l2-01 in
no switchport mode access
exit
int Ethernet513
no switchport mode access
exit
no mac access-list test-l2-01
exit
```

---

**Configuration Guide Generated**: 2026-04-25
**Device**: DUT1 (8011) - 192.168.100.137
**Test Case**: L2-01 - Permit Exact Source MAC
