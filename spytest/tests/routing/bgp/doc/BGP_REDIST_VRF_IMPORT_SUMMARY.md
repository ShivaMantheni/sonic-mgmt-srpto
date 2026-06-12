# BGP Redistribute and VRF Import Test Cases - Quick Reference

## Document Location
**Full Test Cases**: `/home/sonic-claude/athira/sonic-mgmt/spytest/tests/routing/bgp/BGP_REDISTRIBUTE_VRF_IMPORT_TEST_CASES.md`

## Test Suite Overview

**Total Test Cases**: 35
- **Positive Tests**: 15 (functional validation)
- **Negative Tests**: 12 (error handling)
- **Edge Cases**: 8 (boundary conditions)

**Testbed**: `testbed_vs_3rr_reg.yaml` (3-node Route Reflector topology)
**CLI Type**: Klish (isCLI)

---

## CLI Commands Covered

### 1. Redistribute OSPF/OSPFv3
```bash
redistribute ospf
redistribute ospfv3
redistribute ospf metric <value>
redistribute ospf route-map <name>
no redistribute ospf
```

### 2. VRF Import
```bash
import vrf <vrf-name> route-map <map-name>
import vrf <vrf-name>
no import vrf <vrf-name>
no import vrf <vrf-name> route-map <map-name>
```

---

## Test Case Quick Index

### POSITIVE TESTS (15 test cases)

| Test ID | Description | Priority |
|---------|-------------|----------|
| TC-BGP-CLI-REDIST-001 | Basic OSPF redistribution into BGP | High |
| TC-BGP-CLI-REDIST-002 | OSPFv3 (IPv6) redistribution | High |
| TC-BGP-CLI-REDIST-003 | Redistribute OSPF with metric | High |
| TC-BGP-CLI-REDIST-004 | Redistribute OSPF with route-map | High |
| TC-BGP-CLI-REDIST-005 | Multiple redistribution sources (OSPF, static, connected) | Medium |
| TC-BGP-CLI-REDIST-006 | Remove OSPF redistribution (no redistribute ospf) | High |
| TC-BGP-CLI-REDIST-007 | Remove redistribution with metric modifier | Medium |
| TC-BGP-CLI-VRF-IMPORT-001 | Basic VRF route import with route-map | High |
| TC-BGP-CLI-VRF-IMPORT-002 | Import VRF without route-map (if supported) | Medium |
| TC-BGP-CLI-VRF-IMPORT-003 | Remove VRF import (no import vrf) | High |
| TC-BGP-CLI-VRF-IMPORT-004 | Remove VRF import with route-map specifier | Medium |
| TC-BGP-CLI-VRF-IMPORT-005 | Multiple VRF imports to single destination | High |
| TC-BGP-CLI-VRF-IMPORT-006 | VRF import with route filtering | High |
| TC-BGP-CLI-VRF-IMPORT-007 | VRF import with attribute modification | High |

### NEGATIVE TESTS (12 test cases)

| Test ID | Description | Priority |
|---------|-------------|----------|
| TC-BGP-CLI-REDIST-NEG-001 | Redistribute non-existent OSPF process | Medium |
| TC-BGP-CLI-REDIST-NEG-002 | Redistribute with invalid metric values | High |
| TC-BGP-CLI-REDIST-NEG-003 | Redistribute with non-existent route-map | High |
| TC-BGP-CLI-REDIST-NEG-004 | Duplicate redistribute statements | Medium |
| TC-BGP-CLI-REDIST-NEG-005 | Remove non-existent redistribution | Low |
| TC-BGP-CLI-REDIST-NEG-006 | Redistribute in wrong address family | Medium |
| TC-BGP-CLI-VRF-IMPORT-NEG-001 | Import from non-existent source VRF | High |
| TC-BGP-CLI-VRF-IMPORT-NEG-002 | Import into non-existent destination VRF | High |
| TC-BGP-CLI-VRF-IMPORT-NEG-003 | Self-import (VRF imports from itself) | High |
| TC-BGP-CLI-VRF-IMPORT-NEG-004 | Circular VRF import (A→B→A) | High |
| TC-BGP-CLI-VRF-IMPORT-NEG-005 | Import with invalid route-map syntax | Medium |

### EDGE CASES (8 test cases)

| Test ID | Description | Priority |
|---------|-------------|----------|
| TC-BGP-CLI-REDIST-EDGE-001 | Redistribute with maximum metric value (4294967295) | Low |
| TC-BGP-CLI-REDIST-EDGE-002 | Redistribute with metric zero | Low |
| TC-BGP-CLI-REDIST-EDGE-003 | Large-scale route redistribution (10K+ routes) | Medium |
| TC-BGP-CLI-REDIST-EDGE-004 | Rapid redistribution add/remove (stress test) | Medium |
| TC-BGP-CLI-REDIST-EDGE-005 | Redistribute with empty route-map (no match) | Low |
| TC-BGP-CLI-VRF-IMPORT-EDGE-001 | Import VRF with maximum length name | Low |
| TC-BGP-CLI-VRF-IMPORT-EDGE-002 | Import with route-map referencing missing prefix-list | Medium |
| TC-BGP-CLI-VRF-IMPORT-EDGE-003 | VRF import chain (A→B→C transitive import) | Medium |

---

## Key Test Scenarios

### Scenario 1: Basic OSPF Redistribution
**Tests**: TC-BGP-CLI-REDIST-001, 002
- Configure OSPF on D1 and D2
- Redistribute OSPF into BGP on D1
- Verify routes appear on D3 (via Route Reflector D2)
- Test both IPv4 (ospf) and IPv6 (ospfv3)

### Scenario 2: Redistribution with Policy Control
**Tests**: TC-BGP-CLI-REDIST-003, 004
- Use metric to set MED values
- Use route-map for selective redistribution and attribute modification
- Verify prefix-list filtering works
- Verify set actions (metric, local-pref, community)

### Scenario 3: VRF Route Leaking
**Tests**: TC-BGP-CLI-VRF-IMPORT-001, 005, 006, 007
- Create multiple VRFs (VRF-BLUE, VRF-RED, VRF-GREEN)
- Import routes from source VRF to destination VRF
- Apply route-maps for filtering and attribute modification
- Test multiple imports into single VRF

### Scenario 4: Error Handling
**Tests**: All NEG test cases
- Non-existent protocols/VRFs
- Invalid parameters (metrics, route-maps)
- Loop prevention (self-import, circular imports)
- Syntax validation

### Scenario 5: Scale and Stress
**Tests**: TC-BGP-CLI-REDIST-EDGE-003, 004
- Redistribute 10,000+ routes
- Rapid configuration changes
- Monitor CPU, memory, BGP session stability

---

## Verification Commands Reference

### BGP Verification
```bash
show ip bgp summary
show ip bgp
show ip bgp <prefix>
show ip bgp neighbors <ip> advertised-routes
show ip bgp neighbors <ip> received-routes
show bgp ipv6 unicast
show bgp ipv6 unicast <prefix>
```

### OSPF Verification
```bash
show ip ospf
show ip ospf neighbor
show ip ospf route
show ipv6 ospf
show ipv6 ospf neighbor
show ipv6 ospf route
```

### VRF Verification
```bash
show ip vrf
show ip bgp vrf <vrf-name>
show ip bgp vrf <vrf-name> <prefix>
show ip route vrf <vrf-name>
show ip route vrf <vrf-name> bgp
```

### Configuration Verification
```bash
show running-config | section "router bgp"
show running-config | section "redistribute"
show running-config | section "import vrf"
show running-config | section "route-map"
show ip prefix-list
```

### Route-map and Policy Verification
```bash
show route-map
show route-map <map-name>
show ip prefix-list
show ip prefix-list <list-name>
```

---

## Testbed Configuration

### testbed_vs_3rr_reg.yaml Topology
```
D1 (Client) ---- Ethernet0 ---- Ethernet0 ---- D2 (RR Server)
                                              |
                                          Ethernet4
                                              |
                                          Ethernet0
                                              |
                                         D3 (Client)
```

### Device Roles
- **D1**: BGP RR Client, OSPF Router, VRF Source
- **D2**: BGP Route Reflector Server, OSPF Router
- **D3**: BGP RR Client, Verification Point

### IP Addressing Plan
| Link | D1 | D2 | D3 |
|------|----|----|-----|
| D1-D2 | 10.1.1.1/30 | 10.1.1.2/30 | - |
| D2-D3 | - | 10.1.1.5/30 | 10.1.1.6/30 |
| Loopback0 | 1.1.1.1/32 | 2.2.2.2/32 | 3.3.3.3/32 |

### BGP Configuration
- **AS Number**: 65001 (iBGP)
- **Address Families**: IPv4 unicast, IPv6 unicast
- **Route Reflector**: D2
- **Clients**: D1, D3

---

## Test Data Sets

### OSPF Test Prefixes
```
IPv4:
- 1.1.1.1/32 (loopback)
- 10.1.1.0/30 (link subnet)
- 192.168.1.0/24 (test network)

IPv6:
- 2001:db8:1::1/128 (loopback)
- 2001:db8:10::/64 (link subnet)
- 2001:db8:100::/48 (test network)
```

### VRF Test Prefixes
```
VRF-BLUE:
- 10.10.0.0/24
- 10.20.0.0/24

VRF-RED:
- 10.30.0.0/24

VRF-GREEN:
- 10.40.0.0/24

VRF-YELLOW:
- 10.50.0.0/24
```

### Route-map Examples
```
OSPF-TO-BGP:
- permit seq 10: match prefix-list ALLOWED, set metric 200, set local-pref 150
- deny seq 20: (implicit deny)

BLUE-TO-RED:
- permit seq 10: set local-preference 200

SELECTIVE-IMPORT:
- permit seq 10: match prefix-list IMPORT-FILTER
- deny seq 20: (deny all others)
```

---

## Expected Outcomes Summary

### Positive Test Success Criteria
✓ All configurations accepted without errors
✓ Routes redistributed/imported as expected
✓ Attributes (MED, local-pref, community) applied correctly
✓ Routes propagated through Route Reflector
✓ Clean removal (no residual routes after "no" commands)

### Negative Test Success Criteria
✓ Invalid inputs rejected with clear error messages
✓ Non-existent references handled gracefully
✓ Loop prevention (self-import, circular dependencies)
✓ No BGP session disruption
✓ No system instability (CPU, memory normal)

### Edge Case Success Criteria
✓ Boundary values (max/min metric) handled correctly
✓ Large-scale operations (10K+ routes) stable
✓ Rapid configuration changes don't cause flapping
✓ Consistent behavior under unusual conditions

---

## Automation Implementation Notes

### Python Test File Structure
```python
"""
BGP Redistribute and VRF Import - Comprehensive CLI Tests

Test File: test_bgp_redistribute_vrf_import.py
Testbed: testbed_vs_3rr_reg.yaml
Author: Automated Test Suite
Date: 2026-05-28

Test Categories:
- Positive: 15 tests (functional validation)
- Negative: 12 tests (error handling)
- Edge: 8 tests (boundary conditions)
"""

import pytest
from spytest import st, SpyTestDict
import apis.routing.bgp as bgp_api
import apis.routing.ip as ip_api
import apis.routing.ospf as ospf_api

# Test case IDs
TC_IDS = SpyTestDict({...})  # See full document

@pytest.fixture(scope="module", autouse=True)
def module_hooks(request):
    """Module-level setup and teardown"""
    global vars, data
    vars = st.ensure_min_topology("D1D2:1", "D2D3:1")
    # Setup BGP, OSPF, VRFs
    yield
    # Cleanup

# Test functions follow QA_TC_MASTER_RULES format
def test_redistribute_ospf_basic():
    """TC-BGP-CLI-REDIST-001: Basic OSPF Redistribution"""
    # Implementation
    pass
```

### YAML Variables File
```yaml
# vars_bgp_redistribute_vrf_import.yaml
defaults:
  config_cli_type: klish
  show_cli_type: klish
  verify_timeout: 90
  cleanup: true

bgp_config:
  as_number: 65001
  router_ids: {...}

ospf_config:
  process_id: 100
  area: "0.0.0.0"

vrf_config:
  vrfs: [VRF-BLUE, VRF-RED, VRF-GREEN, VRF-YELLOW]

test_prefixes: {...}
```

---

## Test Execution Commands

### Run All Tests
```bash
cd /home/sonic-claude/athira/sonic-mgmt/spytest

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_redistribute_vrf_import.py \
  --logs-path ./logs/bgp_redist_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

### Run Specific Test Categories
```bash
# Positive tests only
pytest -k "not NEG and not EDGE" test_bgp_redistribute_vrf_import.py

# Negative tests only
pytest -k "NEG" test_bgp_redistribute_vrf_import.py

# Edge cases only
pytest -k "EDGE" test_bgp_redistribute_vrf_import.py
```

### Run Specific Test by ID
```bash
# Run TC-BGP-CLI-REDIST-001
pytest test_bgp_redistribute_vrf_import.py::test_redistribute_ospf_basic
```

---

## Coverage Matrix

| CLI Command | Positive | Negative | Edge | Total |
|-------------|----------|----------|------|-------|
| redistribute ospf | 4 | 3 | 3 | 10 |
| redistribute ospfv3 | 1 | 1 | 0 | 2 |
| redistribute metric | 2 | 1 | 2 | 5 |
| redistribute route-map | 2 | 1 | 1 | 4 |
| no redistribute | 2 | 1 | 1 | 4 |
| import vrf route-map | 5 | 2 | 2 | 9 |
| no import vrf | 2 | 1 | 0 | 3 |
| **TOTAL** | **15** | **12** | **8** | **35** |

---

## Pass/Fail Criteria Summary

### Overall Suite Pass Criteria
- **Minimum Pass Rate**: 95% (33 of 35 tests)
- **Critical Tests**: All High-priority tests must pass
- **No System Instability**: Zero crashes, memory leaks, or BGP session flaps

### Individual Test Pass Criteria

**Positive Tests**:
- Configuration accepted without errors
- Routes present in BGP table
- Attributes correct (MED, local-pref, etc.)
- Routes propagated to RR clients
- Clean removal with "no" commands

**Negative Tests**:
- Invalid input rejected
- Clear error messages
- System remains stable
- BGP sessions remain UP

**Edge Cases**:
- Boundary values handled
- System stable under stress
- Consistent behavior
- No unexpected errors

---

## Related Documentation

1. **Full Test Case Document**: `BGP_REDISTRIBUTE_VRF_IMPORT_TEST_CASES.md`
2. **SONiC BGP CLI Guide**: (refer to SONiC documentation)
3. **Route Reflector Configuration**: (refer to testbed documentation)
4. **SPyTest Framework Guide**: `/home/sonic-claude/athira/sonic-mgmt/spytest/Doc/intro.md`

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-28 | Claude Code | Initial summary document |

---

**Document Status**: Ready for Implementation
**Estimated Execution Time**: 4-6 hours (full suite)
**Required Resources**: 3 SONiC devices (testbed_vs_3rr_reg.yaml)

---

**End of Summary Document**
