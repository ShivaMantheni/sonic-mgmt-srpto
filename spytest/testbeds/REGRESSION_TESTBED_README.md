# Regression Testbed Configuration Summary

**Last Updated:** 2026-04-21  
**Location:** `/home/sonic/regression/sonic-mgmt/spytest/testbeds/`

## Overview

All regression testbed files (`*_reg.yaml`) have been updated with the new regression topology details.

---

## Topology Details

### 6-Node Topology (Primary)

| Device | Management IP | Console Port | Role |
|--------|--------------|--------------|------|
| D1 | 192.168.100.35 | 7381 | Core Router |
| D2 | 192.168.100.36 | 7382 | Core Router |
| D3 | 192.168.100.37 | 7383 | Core Router |
| D4 | 192.168.100.38 | 7384 | Core Router |
| D5 | 192.168.100.39 | 7385 | Aggregation Node |
| D6 | 192.168.100.40 | 7386 | Aggregation Node |

**Credentials:**
- Username: `admin`
- Password: `root@123`
- Alt Password: `YourPaSsWoRd`

### 4-Node Topology (Secondary)

| Device | Management IP | Console Port | Role |
|--------|--------------|--------------|------|
| D1 | 192.168.100.41 | 7391 | Core Router |
| D2 | 192.168.100.42 | 7392 | Core Router |
| D3 | 192.168.100.43 | 7393 | Core Router |
| D4 | 192.168.100.44 | 7394 | Core Router |

---

## Connectivity Matrix

### Core Mesh (D1-D4)

#### Interface Groups
- **Group 1:** Ethernet 0, 4, 8, 12
- **Group 2:** Ethernet 16, 20, 24, 28
- **Group 3:** Ethernet 32, 36, 40, 44
- **Group 4 (Uplinks):** Ethernet 48, 52, 56, 60

#### Connections
```
D1 ↔ D2: D1[Eth0,4,8,12] ↔ D2[Eth0,4,8,12]
D1 ↔ D3: D1[Eth16,20,24,28] ↔ D3[Eth0,4,8,12]
D1 ↔ D4: D1[Eth32,36,40,44] ↔ D4[Eth0,4,8,12]
D2 ↔ D3: D2[Eth32,36,40,44] ↔ D3[Eth16,20,24,28]
D2 ↔ D4: D2[Eth16,20,24,28] ↔ D4[Eth16,20,24,28]
D3 ↔ D4: D3[Eth32,36,40,44] ↔ D4[Eth32,36,40,44]
```

### D5 Aggregation Connections (6-node only)
```
D5 → D1: D5[Eth0,4] ↔ D1[Eth48,52]
D5 → D2: D5[Eth8,12] ↔ D2[Eth48,52]
D5 → D3: D5[Eth16,20] ↔ D3[Eth48,52]
D5 → D4: D5[Eth24,28] ↔ D4[Eth48,52]
```

### D6 Aggregation Connections (6-node only)
```
D6 → D1: D6[Eth0,4] ↔ D1[Eth56,60]
D6 → D2: D6[Eth8,12] ↔ D2[Eth56,60]
D6 → D3: D6[Eth16,20] ↔ D3[Eth56,60]
D6 → D4: D6[Eth24,28] ↔ D4[Eth56,60]
D6 → D5: D6[Eth32,36] ↔ D5[Eth32,36]
```

---

## Updated Testbed Files

### 1. testbed_vs_1node_reg.yaml
- **Topology:** Single node (D1)
- **Devices:** D1 (192.168.100.35)
- **Use Case:** Single-DUT tests (Interface, VRF, NTP, AAA, etc.)

### 2. ztp_standalone_reg.yaml
- **Topology:** Standalone (D1)
- **Devices:** D1 (192.168.100.35)
- **Use Case:** ZTP testing, management interface tests

### 3. testbed_2vs_reg.yaml
- **Topology:** 2-node with 4 links
- **Devices:** D1, D2 (192.168.100.35-36)
- **Connections:** D1[Eth0,4,8,12] ↔ D2[Eth0,4,8,12]
- **Use Case:** BGP, VLAN, Static Route 2-node tests

### 4. testbed_vs_2d_reg.yaml
- **Topology:** 2-node with 3 links
- **Devices:** D1, D2 (192.168.100.35-36)
- **Connections:** D1[Eth4,8,12] ↔ D2[Eth4,8,12]
- **Use Case:** Alternative 2-node setup for diverse tests

### 5. testbed_vs_3rr_reg.yaml
- **Topology:** 3-node Route Reflector
- **Devices:** D1, D2, D3 (192.168.100.35-37)
- **Connections:**
  - D1 ↔ D2: D1[Eth0] ↔ D2[Eth0] (RR Client to RR Server)
  - D2 ↔ D3: D2[Eth4] ↔ D3[Eth0] (RR Server to RR Client)
- **Use Case:** BGP Route Reflector testing

### 6. testbed_acl_reg.yaml
- **Topology:** 3-node ACL testing
- **Devices:** D1 (DUT), D2 (TX), D3 (RX)
- **Management IPs:** 192.168.100.35-37
- **Connections:**
  - D2[Eth0] ↔ D1[Eth0] (TX → ACL ingress)
  - D1[Eth4] ↔ D3[Eth0] (ACL egress → RX)
- **Use Case:** L2/L3 ACL traffic validation
- **Traffic Flow:** D2 (Scapy TX) → D1 (ACL) → D3 (tcpdump RX)

### 7. testbed_vs_1node_ntp_reg.yaml
- **Topology:** Single node (D1)
- **Devices:** D1 (192.168.100.35)
- **Use Case:** NTP feature validation

### 8. testbed_4node_reg.yaml (NEW)
- **Topology:** 4-node full mesh
- **Devices:** D1-D4 (192.168.100.41-44)
- **Use Case:** OSPF 4-node tests, complex routing scenarios
- **Connections:** Full mesh between all 4 devices

---

## Usage Examples

### Run 1-Node Test
```bash
cd /home/sonic/regression/sonic-mgmt/spytest
./bin/spytest --testbed ./testbeds/testbed_vs_1node_reg.yaml \
  tests/system/ntp/test_ntp_iscli.py \
  --logs-path ./logs/ntp_test
```

### Run 2-Node BGP Test
```bash
./bin/spytest --testbed ./testbeds/testbed_2vs_reg.yaml \
  tests/routing/BGP/test_bgp_ipv4_basic.py \
  --logs-path ./logs/bgp_test
```

### Run 3-Node Route Reflector Test
```bash
./bin/spytest --testbed ./testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_ipv4_bgp_route_reflector.py \
  --logs-path ./logs/rr_test
```

### Run 4-Node OSPF Test
```bash
./bin/spytest --testbed ./testbeds/testbed_4node_reg.yaml \
  tests/routing/isCLI/testcases_OSPF_2_iscli_Basic_4_node.py \
  --logs-path ./logs/ospf_4node_test
```

### Run ACL Test
```bash
./bin/spytest --testbed ./testbeds/testbed_acl_reg.yaml \
  tests/routing/l3_acl/test_l3_acl.py \
  --logs-path ./logs/acl_test
```

---

## Testbed Selection Guide

| Test Type | Recommended Testbed | Devices Used |
|-----------|---------------------|--------------|
| Interface, VRF, NTP, AAA | testbed_vs_1node_reg.yaml | D1 |
| ZTP, Management | ztp_standalone_reg.yaml | D1 |
| BGP basic, VLAN, Static Route | testbed_2vs_reg.yaml | D1, D2 |
| BGP Route Reflector | testbed_vs_3rr_reg.yaml | D1, D2, D3 |
| L2/L3 ACL with traffic | testbed_acl_reg.yaml | D1, D2, D3 |
| OSPF 4-node | testbed_4node_reg.yaml | D1-D4 (4-node topo) |

---

## Verification

### Check Device Connectivity
```bash
# From regression VM (10.4.160.186)
for ip in 192.168.100.35 192.168.100.36 192.168.100.37 192.168.100.38; do
    echo -n "Testing $ip... "
    sshpass -p 'root@123' ssh -o StrictHostKeyChecking=no admin@$ip "hostname"
done
```

### Validate Testbed Files
```bash
cd /home/sonic/regression/sonic-mgmt/spytest/testbeds
python3 -c "import yaml; yaml.safe_load(open('testbed_vs_1node_reg.yaml'))" && echo "✓ testbed_vs_1node_reg.yaml is valid"
python3 -c "import yaml; yaml.safe_load(open('testbed_2vs_reg.yaml'))" && echo "✓ testbed_2vs_reg.yaml is valid"
python3 -c "import yaml; yaml.safe_load(open('testbed_acl_reg.yaml'))" && echo "✓ testbed_acl_reg.yaml is valid"
```

---

## Notes

1. **Device Type:** All devices are configured as `sonic` or `vsonic` (virtual SONiC)
2. **SSH Access:** All devices use port 22 for SSH (console ports 7381-7386, 7391-7394 are for console access)
3. **Credentials:** Consistent across all devices (admin/root@123)
4. **Interface Naming:** Uses native SONiC naming (Ethernet0, Ethernet4, etc.)
5. **Connectivity:** Physical/virtual links match the topology diagram provided

---

## Troubleshooting

### Device Not Reachable
```bash
# Check SSH connectivity
sshpass -p 'root@123' ssh -o ConnectTimeout=5 admin@192.168.100.35 "show version"
```

### Wrong Topology in Test
- Verify testbed file matches test requirements
- Check `st.ensure_min_topology()` in test script
- Ensure correct number of devices and links

### Interface Not Found
- Verify interface names match testbed (Ethernet0, Ethernet4, etc.)
- Check physical cabling matches topology diagram

---

## Support

For questions or issues, refer to:
- SPyTest documentation: `/home/sonic/regression/sonic-mgmt/spytest/Doc/`
- Original testbed files (backup): `*_reg.yaml.bak`
- Topology diagram: See sections above

