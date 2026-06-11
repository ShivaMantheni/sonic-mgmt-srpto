# LACP Configuration Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Basic Configuration](#basic-configuration)
4. [Advanced Configuration](#advanced-configuration)
5. [VLAN Configuration](#vlan-configuration)
6. [Interface-Specific Configuration](#interface-specific-configuration)
7. [Validation & Troubleshooting](#validation--troubleshooting)
8. [Use Cases](#use-cases)
9. [Best Practices](#best-practices)
10. [Migration from Static to LACP](#migration-from-static-to-lacp)

---

## Overview

### What is LACP?

LACP (Link Aggregation Control Protocol) is IEEE 802.3ad standard that dynamically aggregates multiple physical links into a single logical PortChannel. This provides:

**Key Benefits:**
- **Increased Bandwidth:** Multiple 1Gbps links = 2Gbps aggregated
- **Active Redundancy:** If one link fails, others carry full traffic
- **Dynamic Monitoring:** Automatic member status via LACP PDUs
- **Load Balancing:** Traffic distributed across members
- **Zero Manual Intervention:** Automatic member sync

### Supported Platforms
- SONiC 3.0+
- Broadcom ASIC switches (BCM5600, BCM5700, BCM5800 series)
- Dell switches (S4048, S4148, S5212, S5232, S5248, S5296, Z9100, etc.)
- Cumulus NetQ ecosystem compatible

### LACP vs Static Bundling

| Feature | LACP (Dynamic) | Static Bundling |
|---------|---|---|
| **Member Detection** | Automatic (PDU-based) | Manual config |
| **Failure Recovery** | Automatic (~1 sec) | Manual failover |
| **Speed/Duplex Check** | Yes (prevents mismatch) | Manual verification |
| **PDU Exchange** | Yes (every 1-30 sec) | None |
| **Standards** | IEEE 802.3ad | Proprietary |
| **Recommended** | ✅ Yes | Only for legacy |

---

## Architecture

### LACP Message Flow

```
┌─────────────────────────────────────────────────────┐
│ Physical Links (Ethernet0, Ethernet1)               │
│                                                     │
│  Eth0: 1Gbps duplex, speed=1000, duplex=full       │
│  Eth1: 1Gbps duplex, speed=1000, duplex=full       │
│                                                     │
│           ↓ (LACP negotiation)                      │
│                                                     │
│ PortChannel1 (2Gbps aggregated)                    │
│  - Bandwidth: 2 × 1Gbps = 2Gbps                    │
│  - Members: Eth0, Eth1 (synced)                    │
│  - Load balancing: Hash-based distribution         │
│  - Failover: Auto to remaining member              │
│                                                     │
│           ↓ (Optional layer)                        │
│                                                     │
│ VLAN100 (tagged on PortChannel1)                   │
│  - Multiple VLANs can share PortChannel            │
│  - Each VLAN isolated via 802.1Q tags              │
│                                                     │
│           ↓ (Application layer)                     │
│                                                     │
│ IP Services                                         │
│  - IP addressing on PortChannel or VLAN            │
│  - Routing, BGP, etc. work transparently           │
└─────────────────────────────────────────────────────┘
```

### LACP State Machine

```
DISABLED (no LACP config)
    ↓
UNSELECTED (config exists, waiting for peer)
    ↓
STANDBY (LACP PDUs received from peer, not yet synced)
    ↓
COLLECTING (receiving traffic on path)
    ↓
DISTRIBUTING (sending traffic, partner synced)
    ↓
SYNCED (stable state - both collecting & distributing)

Failure modes:
SYNCED → COLLECTING (received PDU timeout, stop forwarding)
SYNCED → UNSELECTED (config removed)
SYNCED → STANDBY (speed/duplex mismatch detected)
```

---

## Basic Configuration

### Minimum Required Configuration

#### Step 1: Create PortChannel and Add Members (Active Mode)

```bash
# Enter configuration mode
sonic-cli> enable
sonic-cli# configure terminal

# Create PortChannel
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# exit

# Add first member (Ethernet0)
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 1
sonic-cli(conf-if-Ethernet0)# exit

# Add second member (Ethernet1)
sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# channel-group 1
sonic-cli(conf-if-Ethernet1)# exit

# Bring up PortChannel
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit

# Save configuration
sonic-cli(config)# end
sonic-cli# write memory
```

#### Step 2: Configure IP Address (Optional)

```bash
sonic-cli# configure terminal
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit
sonic-cli(config)# end
sonic-cli# write memory
```

#### Step 3: Verify Configuration

```bash
# Check PortChannel status
sonic-cli# show interfaces PortChannel 1
# Expected: PortChannel1 is up, line protocol is up

# Check members
sonic-cli# show interfaces PortChannel 1 members
# Expected: Ethernet0, Ethernet1

# Check LACP status
sonic-cli# show lacp statistics PortChannel 1
# Expected: Both members SYNCED, ACTIVE
```

---

### Simple Single-PortChannel Example

```bash
# Configuration for basic 2-member PortChannel
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "Server Uplink - Active LACP"
sonic-cli(conf-if-Po1)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit

sonic-cli(config)# interface Ethernet48
sonic-cli(conf-if-Ethernet48)# description "Member 1 of PC1"
sonic-cli(conf-if-Ethernet48)# channel-group 1
sonic-cli(conf-if-Ethernet48)# exit

sonic-cli(config)# interface Ethernet49
sonic-cli(conf-if-Ethernet49)# description "Member 2 of PC1"
sonic-cli(conf-if-Ethernet49)# channel-group 1
sonic-cli(conf-if-Ethernet49)# exit

sonic-cli(config)# interface Ethernet50
sonic-cli(conf-if-Ethernet50)# description "Member 3 of PC1"
sonic-cli(conf-if-Ethernet50)# channel-group 1
sonic-cli(conf-if-Ethernet50)# exit

sonic-cli(config)# end
sonic-cli# write memory
```

**Result:** PortChannel1 with 3 members, 3Gbps aggregated bandwidth (3 × 1Gbps)

---

## Advanced Configuration

### Multiple PortChannels

#### Configuration

```bash
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "Uplink to Core Switch"
sonic-cli(conf-if-Po1)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit

# PortChannel 1 members
sonic-cli(config)# interface Ethernet48
sonic-cli(conf-if-Ethernet48)# channel-group 1
sonic-cli(conf-if-Ethernet48)# exit

sonic-cli(config)# interface Ethernet49
sonic-cli(conf-if-Ethernet49)# channel-group 1
sonic-cli(conf-if-Ethernet49)# exit

# Second PortChannel
sonic-cli(config)# interface PortChannel 2
sonic-cli(conf-if-Po2)# description "Server Farm Connection"
sonic-cli(conf-if-Po2)# ip address 10.0.2.1/24
sonic-cli(conf-if-Po2)# no shutdown
sonic-cli(conf-if-Po2)# exit

# PortChannel 2 members
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 2
sonic-cli(conf-if-Ethernet0)# exit

sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# channel-group 2
sonic-cli(conf-if-Ethernet1)# exit

# Third PortChannel
sonic-cli(config)# interface PortChannel 3
sonic-cli(conf-if-Po3)# description "Storage Network"
sonic-cli(conf-if-Po3)# ip address 10.0.3.1/24
sonic-cli(conf-if-Po3)# no shutdown
sonic-cli(conf-if-Po3)# exit

# PortChannel 3 members
sonic-cli(config)# interface Ethernet2
sonic-cli(conf-if-Ethernet2)# channel-group 3
sonic-cli(conf-if-Ethernet2)# exit

sonic-cli(config)# interface Ethernet3
sonic-cli(conf-if-Ethernet3)# channel-group 3
sonic-cli(conf-if-Ethernet3)# exit

sonic-cli(config)# end
sonic-cli# write memory
```

**Result:** Three independent PortChannels operating simultaneously

---

### LACP Mode Configuration

#### Active Mode (DUT Initiates LACP)

```bash
# Best for: Connecting to other switches or devices that support LACP
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 1
sonic-cli(conf-if-Ethernet0)# exit
```

**Behavior:**
- Sends LACP PDUs immediately
- Waits for peer to respond
- Can negotiate with passive side
- Recommended for inter-switch links

---

#### Passive Mode (DUT Waits for Peer to Initiate LACP)

```bash
# Best for: When peer switch always uses active mode
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 1 mode passive
sonic-cli(conf-if-Ethernet0)# exit
```

**Behavior:**
- Waits for peer LACP PDUs
- Responds to active side
- Works with active-mode peers
- Lower resource usage (rarely used)

---

#### Static Mode (No LACP - Always Bundled)

```bash
# Best for: Legacy devices without LACP support
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 1 mode on
sonic-cli(conf-if-Ethernet0)# exit
```

**Behavior:**
- No LACP negotiation
- Members always active
- Manual speed/duplex verification required
- Use only when LACP unavailable

---

### Load Balancing Configuration

#### Hash Algorithm Selection

```bash
# Default: src-dst-ip (source and destination IP)
sonic-cli# config portchannel load-balance-hash algorithm src-dst-ip

# Other options available:
# src-dst-mac (Ethernet addresses)
# src-dst-port (TCP/UDP ports)
# src-dst-l4port (Layer 4 ports)

# View current setting
sonic-cli# show portchannel load-balance
```

#### Verification

```bash
# Show load balance configuration
sonic-cli# show portchannel load-balance
# Expected: Current hash algorithm

# Monitor distribution during traffic
sonic-cli# show interface statistics Ethernet0 Ethernet1
# Expected: Similar packet counts on both interfaces
```

---

### PortChannel MTU Configuration

#### Set MTU Size

```bash
# Standard MTU (1500 bytes)
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# mtu 1500
sonic-cli(conf-if-Po1)# exit

# Jumbo frames (9216 bytes)
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# mtu 9216
sonic-cli(conf-if-Po1)# exit

# Note: Member interfaces should have same or higher MTU
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# mtu 9216
sonic-cli(conf-if-Ethernet0)# exit
```

#### Verification

```bash
sonic-cli# show interfaces PortChannel 1 | grep -i mtu
# Expected: MTU 9216 (or configured value)

sonic-cli# show interfaces Ethernet0 | grep -i mtu
# Expected: Member MTU matches PortChannel
```

---

### Speed and Duplex Configuration

#### Set Member Speed

```bash
# Verify current speed
sonic-cli# show interfaces Ethernet0 | grep Speed
# Expected: Speed: 1000 Mbps

# Set speed explicitly
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# speed 1000
sonic-cli(conf-if-Ethernet0)# duplex full
sonic-cli(conf-if-Ethernet0)# exit

# Auto-negotiate (default)
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# speed auto
sonic-cli(conf-if-Ethernet0)# duplex auto
sonic-cli(conf-if-Ethernet0)# exit
```

#### Member Speed Matching

**Best Practice:** All PortChannel members should have same speed

```bash
# Check all members have matching speed
sonic-cli# show interfaces Ethernet0 Ethernet1 | grep Speed
# Expected: Both show same speed (e.g., 1000 Mbps)

# If mismatch detected
# Option 1: Adjust slower interface to match faster
# Option 2: Disable LACP and use static (if speeds must differ)
```

---

## VLAN Configuration

### PortChannel as Access Port (Single VLAN)

#### Configuration

```bash
# Create VLAN
sonic-cli(config)# vlan 100
sonic-cli(conf-vlan-100)# exit

# Configure PortChannel as access port
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# switchport mode access
sonic-cli(conf-if-Po1)# switchport access vlan 100
sonic-cli(conf-if-Po1)# exit

# Assign IP to VLAN (optional)
sonic-cli(config)# interface Vlan 100
sonic-cli(conf-if-Vlan100)# ip address 10.0.100.1/24
sonic-cli(conf-if-Vlan100)# no shutdown
sonic-cli(conf-if-Vlan100)# exit
```

#### Verification

```bash
sonic-cli# show vlan 100
# Expected: PortChannel1 as member (untagged)

sonic-cli# show interfaces PortChannel 1 switchport
# Expected: Access mode, VLAN 100
```

---

### PortChannel as Trunk Port (Multiple VLANs)

#### Configuration

```bash
# Create multiple VLANs
sonic-cli(config)# vlan 100,200,300
sonic-cli(conf-vlan-100)# exit

# Configure PortChannel as trunk
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# switchport mode trunk
sonic-cli(conf-if-Po1)# switchport trunk allowed vlan 100,200,300
sonic-cli(conf-if-Po1)# exit

# Assign IPs to VLANs (optional)
sonic-cli(config)# interface Vlan 100
sonic-cli(conf-if-Vlan100)# ip address 10.0.100.1/24
sonic-cli(conf-if-Vlan100)# no shutdown
sonic-cli(conf-if-Vlan100)# exit

sonic-cli(config)# interface Vlan 200
sonic-cli(conf-if-Vlan200)# ip address 10.0.200.1/24
sonic-cli(conf-if-Vlan200)# no shutdown
sonic-cli(conf-if-Vlan200)# exit

sonic-cli(config)# interface Vlan 300
sonic-cli(conf-if-Vlan300)# ip address 10.0.300.1/24
sonic-cli(conf-if-Vlan300)# no shutdown
sonic-cli(conf-if-Vlan300)# exit
```

#### Verification

```bash
sonic-cli# show vlan brief
# Expected: VLAN 100, 200, 300 with PortChannel1 as tagged member

sonic-cli# show interfaces PortChannel 1 switchport
# Expected: Trunk mode, allowed VLANs 100,200,300

# Test connectivity on each VLAN
sonic-cli# ping 10.0.100.1
sonic-cli# ping 10.0.200.1
sonic-cli# ping 10.0.300.1
# Expected: All successful
```

---

### Mixed Access and Trunk Ports

#### Configuration

```bash
# PortChannel1: Trunk (multiple VLANs)
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# switchport mode trunk
sonic-cli(conf-if-Po1)# switchport trunk allowed vlan 100,200,300
sonic-cli(conf-if-Po1)# exit

# PortChannel2: Access (single VLAN)
sonic-cli(config)# interface PortChannel 2
sonic-cli(conf-if-Po2)# switchport mode access
sonic-cli(conf-if-Po2)# switchport access vlan 100
sonic-cli(conf-if-Po2)# exit

# Verification
sonic-cli# show interfaces PortChannel 1 switchport
# Expected: Trunk mode

sonic-cli# show interfaces PortChannel 2 switchport
# Expected: Access mode, VLAN 100
```

---

## Interface-Specific Configuration

### Ethernet Interface Member Configuration

#### Configuration

```bash
# Single member interface
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# description "Link to Core - PC1 Member"
sonic-cli(conf-if-Ethernet0)# channel-group 1
sonic-cli(conf-if-Ethernet0)# no shutdown
sonic-cli(conf-if-Ethernet0)# exit

# Multiple member interfaces
sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# description "Link to Core - PC1 Member"
sonic-cli(conf-if-Ethernet1)# channel-group 1
sonic-cli(conf-if-Ethernet1)# no shutdown
sonic-cli(conf-if-Ethernet1)# exit
```

#### Verification

```bash
sonic-cli# show interfaces Ethernet0 Ethernet1
# Expected: Both show "member of PortChannel1"

sonic-cli# show interfaces PortChannel 1 members
# Expected: Ethernet0, Ethernet1 listed
```

---

### Interface Range Configuration

#### Bulk Configuration for Multiple Members

```bash
# Configure range of interfaces
sonic-cli(config)# interface range Ethernet0-3
sonic-cli(conf-if-range-Eth*)# description "PortChannel 1 Members"
sonic-cli(conf-if-range-Eth*)# channel-group 1
sonic-cli(conf-if-range-Eth*)# no shutdown
sonic-cli(conf-if-range-Eth*)# exit

# Note: Above adds all 4 interfaces to PortChannel 1
# Result: PC1 has 4 members (Eth0, Eth1, Eth2, Eth3)
```

#### Verification

```bash
sonic-cli# show interfaces PortChannel 1 members
# Expected: Ethernet0, Ethernet1, Ethernet2, Ethernet3

sonic-cli# show interfaces PortChannel 1 | grep bandwidth
# Expected: Bandwidth 4000000 (4Gbps for 4×1Gbps links)
```

---

### PortChannel Interface Configuration

#### Configure PortChannel Attributes

```bash
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "Aggregated Uplink to Core"
sonic-cli(conf-if-Po1)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po1)# mtu 9216
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit
```

#### Configure QoS on PortChannel

```bash
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# service-policy input policy-map-in
sonic-cli(conf-if-Po1)# service-policy output policy-map-out
sonic-cli(conf-if-Po1)# exit
```

---

## Validation & Troubleshooting

### Verification Commands

#### 1. Check PortChannel Status

```bash
sonic-cli# show interfaces PortChannel 1
# Expected Output:
PortChannel1 is up, line protocol is up
  Hardware is Ethernet PortChannel, address is 00:11:22:33:44:55
  MTU 9216 bytes, BW 2000000 kbit/sec (2Gbps for 2×1Gbps)
  Encapsulation ARPA
  IP address is 10.0.1.1/24
```

---

#### 2. Check Member Status

```bash
sonic-cli# show interfaces PortChannel 1 members
# Expected Output:
Members of PortChannel1:
  Ethernet0
  Ethernet1
```

---

#### 3. Check LACP Statistics

```bash
sonic-cli# show lacp statistics PortChannel 1
# Expected Output:
PortChannel1:
  Ethernet0:
    LACP: Synced (Active) (Forwarding)
    RxPDU: 30, TxPDU: 32
    Mux state: Distributing, Rx state: Collecting
  Ethernet1:
    LACP: Synced (Active) (Forwarding)
    RxPDU: 30, TxPDU: 32
    Mux state: Distributing, Rx state: Collecting
```

**State Meaning:**
- **Synced:** Member in sync with partner
- **Active:** LACP mode (active or passive)
- **Forwarding:** Traffic being forwarded
- **Collecting:** Receiving traffic
- **Distributing:** Sending traffic

---

#### 4. Check Interface Statistics

```bash
sonic-cli# show interface statistics PortChannel 1
# Expected Output:
IFACE    RX_OK    RX_ERR    RX_DRP    TX_OK    TX_ERR    TX_DRP
------   -----    ------    ------    -----    ------    ------
Po1      1000000  0         0         1000000  0         0

# Check member interfaces separately
sonic-cli# show interface statistics Ethernet0 Ethernet1
# Expected: Similar packet counts on both (load balanced)
```

---

#### 5. Verify Bandwidth Aggregation

```bash
sonic-cli# show interfaces PortChannel 1 | grep Bandwidth
# Expected: Bandwidth 2000000 kbit/sec (2Gbps for dual 1Gbps)
# Calculation: 2 members × 1000 Mbps = 2000 Mbps = 2000000 kbit/sec
```

---

### Troubleshooting Common Issues

#### Issue 1: LACP Members Not Syncing

**Symptoms:**
- `show lacp statistics` shows "Out of Sync"
- Members show "Waiting for Peer" state
- Traffic only on one member

**Diagnosis:**

```bash
# 1. Verify PortChannel exists on both sides
sonic-cli# show interfaces PortChannel 1
# Should show on both DUT1 and DUT2

# 2. Check LACP mode consistency
sonic-cli# show running-config interface Ethernet0 | grep channel-group
# Verify both sides use "active" or one is "passive"

# 3. Check physical link status
sonic-cli# show interfaces Ethernet0 Ethernet1
# Should show "administratively up, line protocol is up"

# 4. Verify no firewall blocking LACP PDUs
# LACP uses multicast destination 01:80:C2:00:00:02

# 5. Check speed/duplex matching
sonic-cli# show interfaces Ethernet0 Ethernet1 | grep Speed
# Both should be identical (e.g., 1000 Mbps)
```

**Solutions:**

1. **Mode Mismatch:**
```bash
# If DUT1 active, DUT2 must be active or passive (not static)
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 1  # or passive
sonic-cli(conf-if-Ethernet0)# exit
```

2. **Speed Mismatch:**
```bash
# Force same speed on all members
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# speed 1000
sonic-cli(conf-if-Ethernet0)# duplex full
sonic-cli(conf-if-Ethernet0)# exit

sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# speed 1000
sonic-cli(conf-if-Ethernet1)# duplex full
sonic-cli(conf-if-Ethernet1)# exit
```

3. **Link Down:**
```bash
# Bring up interfaces
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# no shutdown
sonic-cli(conf-if-Ethernet0)# exit
```

---

#### Issue 2: Traffic Only on One Member (No Load Balancing)

**Symptoms:**
- PC operational, members synced
- Tcpdump shows traffic on Eth0 only, not Eth1
- Interface statistics show unbalanced packet counts

**Diagnosis:**

```bash
# 1. Verify both members synced
sonic-cli# show lacp statistics PortChannel 1
# Expected: Both show "Synced" and "Distributing"

# 2. Check load balance algorithm
sonic-cli# show portchannel load-balance
# Default: src-dst-ip (hash based on source/destination IP)

# 3. Monitor traffic distribution
sonic-cli# show interface statistics Ethernet0 Ethernet1
# Check RX_OK columns for both interfaces
```

**Solutions:**

1. **Verify Diverse Traffic Flows:**
   - Single flow (same src/dst) always uses same member
   - Multiple flows with different src/dst should distribute
   - Test with multiple pings to different destinations:
     ```bash
     sonic-cli# ping 10.0.2.1
     sonic-cli# ping 10.0.2.2
     sonic-cli# ping 10.0.2.3
     # Different hash buckets, better distribution
     ```

2. **Check Hash Algorithm:**
```bash
sonic-cli# config portchannel load-balance-hash algorithm src-dst-ip
# This is default, change only if needed:
sonic-cli# config portchannel load-balance-hash algorithm src-dst-mac
```

3. **Increase Members:**
   - With 2 members, single flow → 1 member only
   - Add third member for better distribution:
```bash
sonic-cli(config)# interface Ethernet2
sonic-cli(conf-if-Ethernet2)# channel-group 1
sonic-cli(conf-if-Ethernet2)# exit
# Now traffic can distribute across 3 buckets
```

---

#### Issue 3: PortChannel Down After Member Addition

**Symptoms:**
- PC was Up, add member → PC goes Down
- All members show "down" or "out of sync"
- No traffic flows

**Diagnosis:**

```bash
# 1. Check PortChannel status
sonic-cli# show interfaces PortChannel 1
# If down, check members

# 2. Check member status
sonic-cli# show interfaces Ethernet0 Ethernet1 Ethernet2
# Should show member of PortChannel1

# 3. Check error log
sonic-cli# show system alarms
# May show member compatibility issue
```

**Solutions:**

1. **Speed/Duplex Mismatch:**
```bash
# Verify all members have same speed
sonic-cli# show interfaces Ethernet0 Ethernet1 Ethernet2 | grep Speed
# If mismatch, set all to same speed

sonic-cli(config)# interface Ethernet2
sonic-cli(conf-if-Ethernet2)# speed 1000
sonic-cli(conf-if-Ethernet2)# duplex full
sonic-cli(conf-if-Ethernet2)# exit
```

2. **Member Already in Different PortChannel:**
```bash
# Check if Ethernet2 is in another PC
sonic-cli# show interfaces Ethernet2 | grep "member of"
# If in PC2, remove first

sonic-cli(config)# interface Ethernet2
sonic-cli(conf-if-Ethernet2)# no channel-group 2
sonic-cli(conf-if-Ethernet2)# channel-group 1
sonic-cli(conf-if-Ethernet2)# exit
```

3. **Reload PortChannel:**
```bash
# As last resort, reload PortChannel
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# shutdown
sonic-cli(conf-if-Po1)# exit

sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit

# Wait 10 seconds for LACP sync
sonic-cli# show lacp statistics PortChannel 1
# Should show synced state
```

---

#### Issue 4: Packet Loss During Link Failure

**Symptoms:**
- One member link fails
- Packet loss detected (ping drops)
- Traffic interrupted for 1-2 seconds

**Diagnosis:**

```bash
# 1. Monitor traffic during failure
sonic-cli# ping -c 100 10.0.X.X
# If one link fails, expect 1-5 packets lost

# 2. Check LACP timeout
sonic-cli# show running-config all | grep lacp
# Look for timeout settings (default: 30 sec slow, 3 sec fast)

# 3. Verify spanning tree not interfering (if STP enabled)
sonic-cli# show spanning-tree
# STP can cause additional delays on topology change
```

**Solutions:**

1. **Enable Fast LACP Timeout (if available):**
```bash
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# lacp rate fast
sonic-cli(conf-if-Po1)# exit
# Changes timeout from 30s to 3s for faster detection
```

2. **Disable Spanning Tree (if not needed):**
```bash
sonic-cli(config)# spanning-tree shutdown
sonic-cli(config)# end
# If STP enabled, it adds extra delay on topology change
```

3. **Verify Remaining Member Can Handle Traffic:**
```bash
# With 2 members, losing 1 = 50% bandwidth
# Ensure single link sufficient for traffic demand
sonic-cli# show interface statistics Ethernet0 Ethernet1
# Monitor before adding links to confirm capacity
```

---

#### Issue 5: VLAN Traffic Not Working on PortChannel

**Symptoms:**
- PC operational, members synced
- Ping works on untagged traffic
- Ping fails on VLAN traffic
- Packets seen on PortChannel but not delivered to VLAN

**Diagnosis:**

```bash
# 1. Verify VLAN configuration
sonic-cli# show vlan 100
# Should show PortChannel1 as member

# 2. Check PortChannel switchport mode
sonic-cli# show interfaces PortChannel 1 switchport
# Should show correct mode (access/trunk) and VLAN assignment

# 3. Verify IP address on VLAN
sonic-cli# show interfaces Vlan 100 brief
# Should show IP address configured

# 4. Test with tcpdump
sonic-cli# show interface status PortChannel 1
# Check if VLAN traffic (tagged) being received
```

**Solutions:**

1. **Configure as Trunk (if multiple VLANs):**
```bash
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# switchport mode trunk
sonic-cli(conf-if-Po1)# switchport trunk allowed vlan 100,200
sonic-cli(conf-if-Po1)# exit
```

2. **Configure as Access (if single VLAN):**
```bash
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# switchport mode access
sonic-cli(conf-if-Po1)# switchport access vlan 100
sonic-cli(conf-if-Po1)# exit
```

3. **Ensure VLAN has IP Address:**
```bash
sonic-cli(config)# interface Vlan 100
sonic-cli(conf-if-Vlan100)# ip address 10.0.100.1/24
sonic-cli(conf-if-Vlan100)# no shutdown
sonic-cli(conf-if-Vlan100)# exit
```

---

## Use Cases

### Use Case 1: Server Uplink Aggregation

**Scenario:** Aggregate 4 server ports for load balancing to core switch

**Configuration:**

```bash
# Create 4-member PortChannel to core switch
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "Uplink to Core - 4Gbps"
sonic-cli(conf-if-Po1)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit

# Add members Eth48-51 (typical uplink ports)
sonic-cli(config)# interface range Ethernet48-51
sonic-cli(conf-if-range-Eth48-51)# channel-group 1
sonic-cli(conf-if-range-Eth48-51)# no shutdown
sonic-cli(conf-if-range-Eth48-51)# exit

sonic-cli(config)# end
sonic-cli# write memory
```

**Benefits:**
- 4Gbps aggregated bandwidth (4 × 1Gbps)
- Automatic failover if one link fails
- Load balancing across 4 links
- Active redundancy with LACP protection

---

### Use Case 2: Multi-VLAN Trunk to Distribution Switch

**Scenario:** Trunk multiple VLANs across PortChannel to distribution layer

**Configuration:**

```bash
# Create VLANs
sonic-cli(config)# vlan 10,20,30,40,50
sonic-cli(conf-vlan-10)# exit

# Create PortChannel as trunk
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "Trunk to Distribution"
sonic-cli(conf-if-Po1)# switchport mode trunk
sonic-cli(conf-if-Po1)# switchport trunk allowed vlan 10,20,30,40,50
sonic-cli(conf-if-Po1)# exit

# Add members
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 1
sonic-cli(conf-if-Ethernet0)# exit

sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# channel-group 1
sonic-cli(conf-if-Ethernet1)# exit

# Configure VLAN IPs
sonic-cli(config)# interface Vlan 10
sonic-cli(conf-if-Vlan10)# ip address 10.0.10.1/24
sonic-cli(conf-if-Vlan10)# no shutdown
sonic-cli(conf-if-Vlan10)# exit

# Repeat for other VLANs (20, 30, 40, 50)

sonic-cli(config)# end
sonic-cli# write memory
```

**Benefits:**
- 5 VLANs share 2Gbps aggregated link
- Automatic failover maintains all VLAN connectivity
- Reduced physical link count (2 vs 10)
- Simplified cabling

---

### Use Case 3: Storage Network with High Availability

**Scenario:** Create redundant PortChannel to storage array with both active members

**Configuration:**

```bash
# Storage PortChannel with jumbo frames
sonic-cli(config)# interface PortChannel 10
sonic-cli(conf-if-Po10)# description "Storage SAN - Jumbo Frames"
sonic-cli(conf-if-Po10)# ip address 10.0.50.1/24
sonic-cli(conf-if-Po10)# mtu 9216
sonic-cli(conf-if-Po10)# no shutdown
sonic-cli(conf-if-Po10)# exit

# High-speed storage links
sonic-cli(config)# interface Ethernet40
sonic-cli(conf-if-Ethernet40)# description "Storage Link 1"
sonic-cli(conf-if-Ethernet40)# speed 10000
sonic-cli(conf-if-Ethernet40)# mtu 9216
sonic-cli(conf-if-Ethernet40)# channel-group 10
sonic-cli(conf-if-Ethernet40)# no shutdown
sonic-cli(conf-if-Ethernet40)# exit

sonic-cli(config)# interface Ethernet41
sonic-cli(conf-if-Ethernet41)# description "Storage Link 2"
sonic-cli(conf-if-Ethernet41)# speed 10000
sonic-cli(conf-if-Ethernet41)# mtu 9216
sonic-cli(conf-if-Ethernet41)# channel-group 10
sonic-cli(conf-if-Ethernet41)# no shutdown
sonic-cli(conf-if-Ethernet41)# exit

sonic-cli(config)# end
sonic-cli# write memory
```

**Benefits:**
- 20Gbps aggregated bandwidth
- Jumbo frames for large file transfers
- Active-active redundancy
- Storage traffic isolated on dedicated PortChannel

---

### Use Case 4: Datacenter Leaf-Spine with Multiple PortChannels

**Scenario:** Leaf switch with multiple spine connections

**Configuration:**

```bash
# PortChannel to Spine 1
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "To Spine 1"
sonic-cli(conf-if-Po1)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po1)# exit

sonic-cli(config)# interface Ethernet48
sonic-cli(conf-if-Ethernet48)# channel-group 1
sonic-cli(conf-if-Ethernet48)# exit

sonic-cli(config)# interface Ethernet49
sonic-cli(conf-if-Ethernet49)# channel-group 1
sonic-cli(conf-if-Ethernet49)# exit

# PortChannel to Spine 2
sonic-cli(config)# interface PortChannel 2
sonic-cli(conf-if-Po2)# description "To Spine 2"
sonic-cli(conf-if-Po2)# ip address 10.0.2.1/24
sonic-cli(conf-if-Po2)# exit

sonic-cli(config)# interface Ethernet50
sonic-cli(conf-if-Ethernet50)# channel-group 2
sonic-cli(conf-if-Ethernet50)# exit

sonic-cli(config)# interface Ethernet51
sonic-cli(conf-if-Ethernet51)# channel-group 2
sonic-cli(conf-if-Ethernet51)# exit

sonic-cli(config)# end
sonic-cli# write memory
```

**Benefits:**
- Two independent 2Gbps uplinks to different spines
- Automatic failover if spine fails
- Load balancing across uplinks
- Typical datacenter redundancy pattern

---

## Best Practices

### Configuration Best Practices

#### 1. Use Consistent Naming Convention

```bash
# ✅ GOOD - Descriptive names
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "Uplink to Core Switch 1 - Active"

sonic-cli(config)# interface Ethernet48
sonic-cli(conf-if-Ethernet48)# description "Uplink PC1 Member 1"

# ❌ BAD - Generic names
# description "PC1"
# description "Link"
```

**Reason:** Easier to identify purpose and members during troubleshooting

---

#### 2. Always Use Active Mode (Default)

```bash
# ✅ GOOD - Active mode
sonic-cli(conf-if-Ethernet0)# channel-group 1

# ❌ AVOID - Passive unless specific reason
# channel-group 1 mode passive

# ❌ NEVER - Static mode unless legacy device
# channel-group 1 mode on
```

**Reason:** Active mode is standard for inter-switch LACP

---

#### 3. Match Speed on All Members

```bash
# ✅ GOOD - All members same speed
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# speed 1000
sonic-cli(conf-if-Ethernet0)# exit

sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# speed 1000
sonic-cli(conf-if-Ethernet1)# exit

# ❌ BAD - Mixed speeds
# interface Ethernet0: speed 1000
# interface Ethernet1: speed 10000
```

**Reason:** Mixed speeds cause sync issues and reduced performance

---

#### 4. Configure Minimum 2 Members

```bash
# ✅ GOOD - At least 2 members for redundancy
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 1
sonic-cli(conf-if-Ethernet0)# exit

sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# channel-group 1
sonic-cli(conf-if-Ethernet1)# exit

# ⚠️ WARNING - Single member PortChannel
# This provides no redundancy, defeats purpose of LACP
```

**Reason:** Single member PC is pointless, provides no HA

---

#### 5. Use Jumbo Frames Consistently

```bash
# ✅ GOOD - Jumbo frames on storage/high-performance links
sonic-cli(config)# interface PortChannel 10
sonic-cli(conf-if-Po10)# mtu 9216
sonic-cli(conf-if-Po10)# exit

sonic-cli(config)# interface Ethernet40
sonic-cli(conf-if-Ethernet40)# mtu 9216
sonic-cli(conf-if-Ethernet40)# exit

# Standard frames fine for regular links
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# mtu 1500  # Default
sonic-cli(conf-if-Po1)# exit
```

**Reason:** Jumbo frames reduce overhead for large transfers, improves performance

---

### Operational Best Practices

#### 1. Verify Before Adding Members

```bash
# Before adding interface to PortChannel, verify:
sonic-cli# show interfaces Ethernet0 detailed
# Check:
#   - Physically up (line protocol up)
#   - Not already member of another PortChannel
#   - Speed matches other members
#   - Duplex is full
```

---

#### 2. Test Failover Scenarios

```bash
# Regularly test what happens when member fails
sonic-cli# ping -c 100 10.0.1.2  # Start ping

# In another terminal, bring down member
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# shutdown
sonic-cli(conf-if-Ethernet0)# exit

# Check ping results:
# Expected: Max 1-5 packets lost during failover
# Then recovery on remaining member
```

---

#### 3. Monitor Load Distribution

```bash
# Periodically check if traffic balanced
sonic-cli# show interface statistics Ethernet0 Ethernet1
# Expected: Similar packet counts on both members
# If significantly different, may indicate hash algorithm issue
```

---

#### 4. Document Configuration Changes

```bash
# Track all changes
# Example log:
# 2024-01-15 10:30 - Added Ethernet2 to PC1 (upgraded 2->3 members)
# 2024-01-15 10:35 - Verified load balanced across all 3
# 2024-01-15 10:40 - Updated PortChannel description

# Use config backup
sonic-cli# config save /backup/config_$(date +%Y%m%d).json
```

---

#### 5. Plan Maintenance Windows

```bash
# Schedule maintenance during low-traffic hours
# Example maintenance procedure:

# 1. Announce maintenance window to users
# 2. Redirect traffic if possible
sonic-cli# show interface statistics PortChannel 1
#    Note current utilization

# 3. Perform change (add/remove member)
sonic-cli(config)# interface Ethernet2
sonic-cli(conf-if-Ethernet2)# channel-group 1
sonic-cli(conf-if-Ethernet2)# exit

# 4. Verify LACP sync
sonic-cli# show lacp statistics PortChannel 1
#    Wait for all members to reach SYNCED state

# 5. Monitor for issues (15-30 minutes)
sonic-cli# show interface statistics
#    Verify no errors or dropped packets

# 6. Update documentation
# 7. Announce completion
```

---

### Security Best Practices

#### 1. Use LACP on Trusted Links Only

```bash
# ✅ GOOD - LACP on internal switch-to-switch links
# Uplinks, storage, internal datacenter

# ❌ RISKY - LACP on untrusted networks
# Don't expose LACP to external/WAN links
# Would allow attacker to interfere with LACP
```

---

#### 2. Disable LACP on Untrusted Ports

```bash
# Access ports to unmanaged devices
sonic-cli(config)# interface Ethernet20
sonic-cli(conf-if-Ethernet20)# switchport mode access
sonic-cli(conf-if-Ethernet20)# switchport access vlan 100
# No channel-group - access port, no LACP
sonic-cli(conf-if-Ethernet20)# exit
```

---

#### 3. Verify LACP PDU Reception

```bash
# Periodically verify LACP PDUs being received
sonic-cli# show lacp statistics PortChannel 1 | grep RxPDU
# Expected: RxPDU count increasing (one per second minimum)

# If RxPDU not increasing:
# - Possible firewall blocking LACP multicast
# - Link may be administratively down
# - LACP negotiation failed
```

---

## Migration from Static to LACP

### Step-by-Step Migration Procedure

#### Pre-Migration Planning

```bash
# 1. Identify current configuration
sonic-cli# show running-config | grep -A 5 "interface PortChannel"
# Look for "channel-group" entries
# Note current mode (on = static, active/passive = LACP)

# 2. Verify peer switch
# Ensure peer supports LACP (most modern switches do)

# 3. Plan maintenance window
# Schedule during low-traffic period
```

---

#### Step 1: Configure New LACP PortChannel (Parallel)

```bash
# Create new LACP PC while keeping old static PC
sonic-cli(config)# interface PortChannel 100
sonic-cli(conf-if-Po100)# description "New LACP PC (migration)"
sonic-cli(conf-if-Po100)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po100)# no shutdown
sonic-cli(conf-if-Po100)# exit

# Add members with LACP
sonic-cli(config)# interface Ethernet4
sonic-cli(conf-if-Ethernet4)# channel-group 100
sonic-cli(conf-if-Ethernet4)# exit

sonic-cli(config)# interface Ethernet5
sonic-cli(conf-if-Ethernet5)# channel-group 100
sonic-cli(conf-if-Ethernet5)# exit
```

---

#### Step 2: Verify New LACP PortChannel

```bash
# Verify sync with peer
sonic-cli# show lacp statistics PortChannel 100
# Expected: Both members SYNCED

# Test connectivity
sonic-cli# ping 10.0.X.100  # IP of peer's PC100
# Expected: Successful
```

---

#### Step 3: Migrate Traffic to LACP PortChannel

```bash
# Update VLAN membership (if VLANs configured)
sonic-cli(config)# vlan 100
sonic-cli(conf-vlan-100)# no member PortChannel 1  # Remove from static PC
sonic-cli(conf-vlan-100)# member PortChannel 100   # Add to LACP PC
sonic-cli(conf-vlan-100)# exit

# Or update routes if using PortChannel IPs
sonic-cli# show ip route
# Should show traffic via PC100 instead of PC1
```

---

#### Step 4: Decommission Static PortChannel

```bash
# Once traffic fully migrated:

# 1. Stop using old PC
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# shutdown
sonic-cli(conf-if-Po1)# exit

# 2. Verify no traffic on old PC
sonic-cli# show interface statistics PortChannel 1
# RX_OK and TX_OK should not be changing

# 3. Remove members from old PC
sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# no channel-group 1
sonic-cli(conf-if-Ethernet0)# exit

sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# no channel-group 1
sonic-cli(conf-if-Ethernet1)# exit

# 4. Delete old PC
sonic-cli(config)# no interface PortChannel 1
sonic-cli(config)# exit
```

---

#### Step 5: Rename LACP PortChannel to Original

```bash
# Rename PC100 to PC1 for consistency
# Note: PortChannel renaming not directly supported in CLI
# Instead: Recreate with original ID after deleting old one
# (Already done in step 4)

# Create PortChannel 1 with LACP
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "Uplink - Active LACP"
sonic-cli(conf-if-Po1)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit

sonic-cli(config)# interface Ethernet0
sonic-cli(conf-if-Ethernet0)# channel-group 1
sonic-cli(conf-if-Ethernet0)# exit

sonic-cli(config)# interface Ethernet1
sonic-cli(conf-if-Ethernet1)# channel-group 1
sonic-cli(conf-if-Ethernet1)# exit

sonic-cli(config)# end
sonic-cli# write memory
```

---

#### Step 6: Verify Final Configuration

```bash
# Verify new LACP PC1 operational
sonic-cli# show lacp statistics PortChannel 1
# Expected: Both members SYNCED

sonic-cli# ping 10.0.X.2
# Expected: Successful connectivity
```

---

## Appendix: Complete Configuration Example

### Full Multi-PortChannel Deployment

```bash
# Complete working configuration for datacenter leaf switch

sonic-cli> enable
sonic-cli# configure terminal

# ========== PORTCHANNEL 1: Uplink to Core (Active LACP) ==========
sonic-cli(config)# interface PortChannel 1
sonic-cli(conf-if-Po1)# description "Uplink to Core Switch - 2Gbps"
sonic-cli(conf-if-Po1)# ip address 10.0.1.1/24
sonic-cli(conf-if-Po1)# mtu 9216
sonic-cli(conf-if-Po1)# no shutdown
sonic-cli(conf-if-Po1)# exit

sonic-cli(config)# interface Ethernet48
sonic-cli(conf-if-Ethernet48)# description "Core Uplink Member 1"
sonic-cli(conf-if-Ethernet48)# speed 1000
sonic-cli(conf-if-Ethernet48)# channel-group 1
sonic-cli(conf-if-Ethernet48)# no shutdown
sonic-cli(conf-if-Ethernet48)# exit

sonic-cli(config)# interface Ethernet49
sonic-cli(conf-if-Ethernet49)# description "Core Uplink Member 2"
sonic-cli(conf-if-Ethernet49)# speed 1000
sonic-cli(conf-if-Ethernet49)# channel-group 1
sonic-cli(conf-if-Ethernet49)# no shutdown
sonic-cli(conf-if-Ethernet49)# exit

# ========== PORTCHANNEL 2: Storage Network (Jumbo Frames) ==========
sonic-cli(config)# interface PortChannel 2
sonic-cli(conf-if-Po2)# description "Storage SAN - 4Gbps with Jumbo"
sonic-cli(conf-if-Po2)# ip address 10.0.50.1/24
sonic-cli(conf-if-Po2)# mtu 9216
sonic-cli(conf-if-Po2)# no shutdown
sonic-cli(conf-if-Po2)# exit

sonic-cli(config)# interface Ethernet40
sonic-cli(conf-if-Ethernet40)# description "Storage Link 1"
sonic-cli(conf-if-Ethernet40)# speed 10000
sonic-cli(conf-if-Ethernet40)# mtu 9216
sonic-cli(conf-if-Ethernet40)# channel-group 2
sonic-cli(conf-if-Ethernet40)# no shutdown
sonic-cli(conf-if-Ethernet40)# exit

sonic-cli(config)# interface Ethernet41
sonic-cli(conf-if-Ethernet41)# description "Storage Link 2"
sonic-cli(conf-if-Ethernet41)# speed 10000
sonic-cli(conf-if-Ethernet41)# mtu 9216
sonic-cli(conf-if-Ethernet41)# channel-group 2
sonic-cli(conf-if-Ethernet41)# no shutdown
sonic-cli(conf-if-Ethernet41)# exit

sonic-cli(config)# interface Ethernet42
sonic-cli(conf-if-Ethernet42)# description "Storage Link 3"
sonic-cli(conf-if-Ethernet42)# speed 10000
sonic-cli(conf-if-Ethernet42)# mtu 9216
sonic-cli(conf-if-Ethernet42)# channel-group 2
sonic-cli(conf-if-Ethernet42)# no shutdown
sonic-cli(conf-if-Ethernet42)# exit

sonic-cli(config)# interface Ethernet43
sonic-cli(conf-if-Ethernet43)# description "Storage Link 4"
sonic-cli(conf-if-Ethernet43)# speed 10000
sonic-cli(conf-if-Ethernet43)# mtu 9216
sonic-cli(conf-if-Ethernet43)# channel-group 2
sonic-cli(conf-if-Ethernet43)# no shutdown
sonic-cli(conf-if-Ethernet43)# exit

# ========== PORTCHANNEL 3: Server Trunk (Multi-VLAN) ==========
sonic-cli(config)# vlan 10,20,30,40,50
sonic-cli(conf-vlan-10)# exit

sonic-cli(config)# interface PortChannel 3
sonic-cli(conf-if-Po3)# description "Server Trunk - Multi-VLAN"
sonic-cli(conf-if-Po3)# switchport mode trunk
sonic-cli(conf-if-Po3)# switchport trunk allowed vlan 10,20,30,40,50
sonic-cli(conf-if-Po3)# no shutdown
sonic-cli(conf-if-Po3)# exit

sonic-cli(config)# interface Ethernet50
sonic-cli(conf-if-Ethernet50)# description "Server Trunk Member 1"
sonic-cli(conf-if-Ethernet50)# speed 1000
sonic-cli(conf-if-Ethernet50)# channel-group 3
sonic-cli(conf-if-Ethernet50)# no shutdown
sonic-cli(conf-if-Ethernet50)# exit

sonic-cli(config)# interface Ethernet51
sonic-cli(conf-if-Ethernet51)# description "Server Trunk Member 2"
sonic-cli(conf-if-Ethernet51)# speed 1000
sonic-cli(conf-if-Ethernet51)# channel-group 3
sonic-cli(conf-if-Ethernet51)# no shutdown
sonic-cli(conf-if-Ethernet51)# exit

# ========== VLAN IP CONFIGURATION ==========
sonic-cli(config)# interface Vlan 10
sonic-cli(conf-if-Vlan10)# ip address 10.10.1.1/24
sonic-cli(conf-if-Vlan10)# no shutdown
sonic-cli(conf-if-Vlan10)# exit

sonic-cli(config)# interface Vlan 20
sonic-cli(conf-if-Vlan20)# ip address 10.20.1.1/24
sonic-cli(conf-if-Vlan20)# no shutdown
sonic-cli(conf-if-Vlan20)# exit

sonic-cli(config)# interface Vlan 30
sonic-cli(conf-if-Vlan30)# ip address 10.30.1.1/24
sonic-cli(conf-if-Vlan30)# no shutdown
sonic-cli(conf-if-Vlan30)# exit

sonic-cli(config)# interface Vlan 40
sonic-cli(conf-if-Vlan40)# ip address 10.40.1.1/24
sonic-cli(conf-if-Vlan40)# no shutdown
sonic-cli(conf-if-Vlan40)# exit

sonic-cli(config)# interface Vlan 50
sonic-cli(conf-if-Vlan50)# ip address 10.50.1.1/24
sonic-cli(conf-if-Vlan50)# no shutdown
sonic-cli(conf-if-Vlan50)# exit

# ========== SAVE CONFIGURATION ==========
sonic-cli(config)# end
sonic-cli# write memory

# ========== VERIFICATION ==========
sonic-cli# show interfaces PortChannel
sonic-cli# show lacp statistics
sonic-cli# show interface statistics
```

---

## Conclusion

LACP provides critical redundancy and bandwidth aggregation for production networks. This guide covers:

✅ **Basic setup** - Simple PortChannel creation  
✅ **Advanced features** - Multiple PCs, VLAN support, jumbo frames  
✅ **Troubleshooting** - 5 common issues with solutions  
✅ **Best practices** - Security, operations, migration  
✅ **Use cases** - Datacenter, storage, server connectivity  
✅ **Complete examples** - Production-ready configurations  

Key Takeaways:
1. Always use **active mode** for inter-switch LACP
2. Ensure all members have **same speed/duplex**
3. Minimum **2 members** for redundancy
4. Use **jumbo frames** for storage/high-performance
5. **Verify** LACP sync before relying on link

For more information:
- IEEE 802.3ad Standard
- Broadcom SONiC CLI documentation
- Switch vendor-specific guides

