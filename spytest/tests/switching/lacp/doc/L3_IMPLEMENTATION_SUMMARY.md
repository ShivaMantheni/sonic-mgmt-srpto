# L3 Traffic Validation - Quick Implementation Summary

**Status:** ✅ Complete and Ready for Testing
**Date:** 2026-05-06

---

## What Was Done

Replaced **placeholder L3 test** with **full L3 traffic validation** for both LACP test cases.

### **Before (Placeholder)**
```python
def test_l3_traffic_validation():
    st.log("Expected IP configuration (if configured)...")
    st.log("Note: L3 validation requires IP configuration...")
    st.report_pass("test_case_passed")
```

### **After (Full Implementation)**
```python
def test_l3_traffic_validation():
    # Step 1: Configure IP on PortChannel
    ip_api.config_ip_addr_interface(...)

    # Step 2: Clear counters
    st.config(..., "clear interface counters", ...)

    # Step 3: Start tcpdump
    scapy_api.start_tcpdump(...)

    # Step 4: Send ICMP packets
    scapy_api.send_traffic(..., traffic_type="icmp")

    # Step 5: Verify tcpdump
    scapy_api.verify_tcpdump_capture(...)

    # Step 6: Verify counters
    st.show(..., "show interface counters")
```

---

## Changes Summary

| Aspect | LACP_CLI_001 | LACP_CLI_002 |
|--------|--------------|--------------|
| **IP Configuration** | D1: 10.1.1.1/30, D2: 10.1.1.2/30 | D1: (from CLI_001), D2: 10.1.1.2/30 |
| **Traffic Direction** | D1 → D2 (Active → Passive) | D2 → D1 (Passive → Active) |
| **Traffic Type** | ICMP Echo Request | ICMP Echo Request |
| **Duration** | 5 seconds @ 100 pps | 5 seconds @ 100 pps |
| **Total Packets** | ~500 packets | ~500 packets |
| **Verification** | tcpdump + counters | tcpdump + counters |
| **PCAP File** | `/tmp/lacp_cli_001_l3_traffic.pcap` | `/tmp/lacp_cli_002_l3_traffic.pcap` |
| **Import Added** | `import apis.routing.ip as ip_api` | `import apis.routing.ip as ip_api` |

---

## 6-Step Verification Process

### **Step 1: IP Configuration**
```python
ip_api.config_ip_addr_interface(
    dut=<D1 or D2>,
    interface_name="PortChannel1",
    ip_address="10.1.1.1" or "10.1.1.2",
    subnet="255.255.255.252"
)
```
✅ Both D1 and D2 PortChannels get IP addresses

### **Step 2: Baseline Counters**
```python
st.config(dut, "clear interface counters", type=data.cli_type)
```
✅ Clear counters to establish clean baseline

### **Step 3: Start Capture**
```python
scapy_api.start_tcpdump(dut, "PortChannel1", output_file="/tmp/lacp_cli_xxx_l3_traffic.pcap")
```
✅ Capture frames to PCAP file before sending traffic

### **Step 4: Send L3 Traffic**
```python
scapy_api.send_traffic(
    dut=<sender>,
    interface="PortChannel1",
    src_ip="10.1.1.1" or "10.1.1.2",
    dst_ip="10.1.1.2" or "10.1.1.1",
    duration=5,
    pps=100,
    traffic_type="icmp"  # <-- ICMP for L3
)
```
✅ Send ~500 ICMP packets from sender to receiver

### **Step 5: Verify tcpdump**
```python
scapy_api.verify_tcpdump_capture(dut, capture_file="/tmp/...", min_packets=pkt_count-1)
```
✅ Verify PCAP file contains captured ICMP packets

### **Step 6: Verify Counters**
```python
cmd = "show interface counters | no-more"
output = st.show(dut, cmd, type=data.cli_type)
# Check: PortChannel1 RX_OK ≥ sent packet count
```
✅ Verify interface counter shows received packets

---

## Cleanup Implementation

### **IP Address Removal**
```python
try:
    ip_api.delete_ip_interface(
        dut=dut,
        interface_name="PortChannel1",
        ip_address="10.1.1.1" or "10.1.1.2",
        subnet="30"
    )
except Exception:
    # Graceful if IP wasn't configured
    pass
```

### **Full Cleanup Sequence**
1. Remove IP from D1 PortChannel1
2. Remove IP from D2 PortChannel1
3. Remove member interfaces from PortChannel
4. Delete PortChannel
5. Clear counters
6. Return to baseline

---

## Key Differences from L2 Traffic Test

| Aspect | L2 Traffic (Test 007) | L3 Traffic (Test 008) |
|--------|----------------------|----------------------|
| **Layer** | Layer 2 (MAC addresses) | Layer 3 (IP addresses) |
| **Packet Type** | Ethernet frames | ICMP Echo Request (Ping) |
| **Required Config** | None (PortChannel creation sufficient) | IP address configuration on PortChannel |
| **PCAP File** | `/tmp/lacp_cli_001_l2_traffic.pcap` | `/tmp/lacp_cli_001_l3_traffic.pcap` |
| **Verification** | MAC address validation + counters | IP address validation + counters |
| **Scapy Parameters** | `traffic_type="ethernet"` | `traffic_type="icmp"` |

---

## Files Modified

```
tests/switching/lacp/
├── test_lacp_cli_001_active_portchannel.py       ✅ Updated
│   ├── Added: import apis.routing.ip as ip_api
│   ├── Modified: test_l3_traffic_validation()
│   └── Modified: cleanup_portchannel_config()
│
└── test_lacp_cli_002_passive_portchannel.py       ✅ Updated
    ├── Added: import apis.routing.ip as ip_api
    ├── Modified: test_l3_traffic_validation()
    └── Modified: cleanup_portchannel_config()
```

---

## Syntax Validation

```bash
✓ LACP_CLI_001 syntax valid
✓ LACP_CLI_002 syntax valid
```

Both test files validated with `python3 -m py_compile` ✅

---

## Ready for Testing

Both test cases are now complete with:

- ✅ **IP Configuration** on PortChannels (10.1.1.1/30 and 10.1.1.2/30)
- ✅ **ICMP Traffic Generation** via Scapy API
- ✅ **tcpdump Packet Capture** verification
- ✅ **Interface Counter** verification (RX_OK/TX_OK)
- ✅ **Proper Cleanup** of IP addresses
- ✅ **Error Handling** for graceful degradation
- ✅ **Python Syntax** valid for execution

**Next Step:** Execute the test cases to verify L3 traffic validation works correctly.

---

## Test Execution Commands

### **Run LACP_CLI_001 (with L3 validation)**
```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_lacp_vs.yaml \
  switching/lacp/test_lacp_cli_001_active_portchannel.py \
  --logs-path ./logs/lacp_cli_001_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

### **Run LACP_CLI_002 (with L3 validation)**
```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_lacp_vs.yaml \
  switching/lacp/test_lacp_cli_002_passive_portchannel.py \
  --logs-path ./logs/lacp_cli_002_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

