# IPv6 ACL Test Script Implementation Plan

**Project**: IPv6 ACL Comprehensive Testing
**Status**: 📋 PLANNING
**Date**: 2026-04-30
**Scope**: New test script for IPv6 ACL functionality

---

## Executive Summary

This document outlines the plan for creating a comprehensive IPv6 ACL test script (`test_ipv6_acl.py`) similar to the existing L3 IPv4 ACL test suite. The IPv6 ACL testing will cover positive (baseline), negative (edge cases), and robustness scenarios.

---

## Objectives

### Primary Objectives
- ✅ Create comprehensive IPv6 ACL baseline test suite
- ✅ Create IPv6 ACL negative test suite (edge cases)
- ✅ Create IPv6 ACL robustness test suite
- ✅ Validate IPv6 address filtering, port matching, and protocol matching
- ✅ Test ACL rule precedence with IPv6 traffic

### Secondary Objectives
- ✅ Reuse patterns from successful IPv4 ACL tests
- ✅ Apply lessons learned from IPv4 ACL bug fixes
- ✅ Establish reusable IPv6 traffic generation patterns
- ✅ Document IPv6-specific ACL behaviors

### Success Criteria
- All test cases execute without syntax/API errors
- 95%+ test pass rate on virtual platforms
- 98%+ test pass rate on hardware platforms
- Comprehensive code documentation
- Reusable patterns for future IPv6 feature tests

---

## Scope

### In Scope
| Category | Coverage |
|----------|----------|
| **IPv6 Addresses** | Source, Destination, any, specific subnets |
| **Port Matching** | TCP/UDP with specific ports, port ranges |
| **Protocol Matching** | TCP, UDP, ICMPv6, IGMP, custom protocols |
| **ACL Rules** | PERMIT, DENY, with different priorities |
| **Traffic Types** | Unicast, Multicast, broadcast-equivalent |
| **Edge Cases** | IPv4-mapped IPv6, link-local, multicast |
| **Platforms** | Virtual (SONiC-VS) and Hardware |
| **Rule Precedence** | First-match, multiple rules, complex scenarios |

### Out of Scope (For Future)
- IPv6 fragmentation handling (Phase 2)
- Extension headers testing (Phase 2)
- IPv6 over tunnel scenarios (Phase 2)
- QoS with IPv6 ACLs (Phase 2)
- VRF-based IPv6 ACLs (Phase 2)

---

## Test Script Structure

### File Organization
```
tests/routing/ipv6_acl/
├── test_ipv6_acl.py                    # Main IPv6 ACL baseline tests
├── test_ipv6_acl_negative.py           # IPv6 ACL negative/edge case tests
├── test_ipv6_acl_robustness.py         # IPv6 ACL stress/robustness tests
└── (in future)
    ├── test_ipv6_acl_extended.py       # Extended IPv6 ACL features
    └── test_ipv6_acl_performance.py    # Performance/scale tests

vars/routing/ipv6_acl/
├── vars_ipv6_acl.yaml                  # IPv6 ACL test configuration
└── ipv6_traffic_profiles.yaml          # IPv6 traffic generation profiles
```

---

## Test Cases

### 1. Baseline Tests (test_ipv6_acl.py)

#### Test Suite Structure
```
TestIPv6AclBasic:
  ├── test_ipv6_baseline_permit_all
  ├── test_ipv6_baseline_permit_specific_source
  ├── test_ipv6_baseline_permit_specific_destination
  ├── test_ipv6_baseline_deny_specific_source
  ├── test_ipv6_baseline_deny_specific_destination
  ├── test_ipv6_baseline_tcp_port_matching
  ├── test_ipv6_baseline_udp_port_matching
  ├── test_ipv6_baseline_icmpv6_matching
  ├── test_ipv6_baseline_rule_precedence
  ├── test_ipv6_baseline_port_ranges
  ├── test_ipv6_baseline_multiple_acl_tables
  ├── test_ipv6_baseline_acl_unbind_rebind
  └── test_ipv6_baseline_acl_delete

TestIPv6AclInterfaces:
  ├── test_ipv6_acl_on_ethernet
  ├── test_ipv6_acl_on_portchannel
  ├── test_ipv6_acl_on_vlan_interface
  ├── test_ipv6_acl_ingress
  └── test_ipv6_acl_egress
```

#### Sample Baseline Test Cases

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| IPv6-B01 | PERMIT all IPv6 traffic | RX = TX (all forwarded) |
| IPv6-B02 | PERMIT specific source :: /64 | Only matching source forwarded |
| IPv6-B03 | PERMIT specific destination :: /64 | Only matching destination forwarded |
| IPv6-B04 | DENY specific source, PERMIT rest | Non-matching source forwarded |
| IPv6-B05 | TCP port 443 matching | Only TCP:443 forwarded |
| IPv6-B06 | UDP port 53 matching | Only UDP:53 forwarded |
| IPv6-B07 | ICMPv6 echo request | Echo request forwarded |
| IPv6-B08 | Multiple rules with precedence | First match evaluated |
| IPv6-B09 | Port range 1000-2000 | Traffic in range forwarded |
| IPv6-B10 | ACL table binding/unbinding | Rules applied/removed correctly |

### 2. Negative Tests (test_ipv6_acl_negative.py)

#### Test Suite Structure
```
TestIPv6AclNegative:
  ├── test_ipv6_n01_invalid_source_addressing
  ├── test_ipv6_n02_multicast_denial
  ├── test_ipv6_n03_link_local_handling
  ├── test_ipv6_n04_ipv4_mapped_addressing
  ├── test_ipv6_n05_tcp_flags_matching
  ├── test_ipv6_n06_port_zero_behavior
  ├── test_ipv6_n07_protocol_zero
  ├── test_ipv6_n08_protocol_255
  ├── test_ipv6_n09_overlapping_subnets
  ├── test_ipv6_n10_contradictory_rules
  ├── test_ipv6_n11_rule_priority_conflicts
  └── test_ipv6_n12_ipv6_compression_variants
```

#### Sample Negative Test Cases

| Test ID | Edge Case | Purpose |
|---------|-----------|---------|
| IPv6-N01 | Invalid IPv6 address format | Validate input checking |
| IPv6-N02 | ff00::/8 multicast addressing | Verify multicast filtering |
| IPv6-N03 | fe80::/10 link-local addresses | Test link-local handling |
| IPv6-N04 | ::ffff:192.0.2.1 IPv4-mapped | Validate dual-stack behavior |
| IPv6-N05 | TCP flags with IPv6 | Verify TCP flag extraction |
| IPv6-N06 | Port 0 (dynamic range start) | Edge case port validation |
| IPv6-N07 | Protocol 0 (HOPOPT) | Reserved protocol handling |
| IPv6-N08 | Protocol 255 (reserved) | Reserved protocol handling |
| IPv6-N09 | Overlapping CIDR ranges | Rule evaluation order |
| IPv6-N10 | PERMIT all + DENY specific | Logical contradiction |
| IPv6-N11 | Same priority rules | Precedence validation |
| IPv6-N12 | Compressed vs. uncompressed | Address variant handling |

### 3. Robustness Tests (test_ipv6_acl_robustness.py)

#### Test Suite Structure
```
TestIPv6AclRobustness:
  ├── test_ipv6_scale_large_acl_table
  ├── test_ipv6_scale_many_rules
  ├── test_ipv6_high_traffic_rate
  ├── test_ipv6_burst_traffic
  ├── test_ipv6_acl_with_vlan_tagging
  ├── test_ipv6_acl_with_portchannel
  ├── test_ipv6_acl_with_lag_failover
  ├── test_ipv6_acl_persistence_reboot
  ├── test_ipv6_acl_persistence_config_save
  ├── test_ipv6_acl_concurrent_updates
  ├── test_ipv6_acl_dynamic_rule_changes
  └── test_ipv6_acl_hardware_limits
```

---

## Configuration Structure

### vars_ipv6_acl.yaml

```yaml
# IPv6 ACL Test Configuration

min_topology:
  - "D1D2:1"      # Two DUTs with direct link
  - "D1T1:1"      # DUT1 to Traffic Generator

dut_l3_config:
  dut1:
    eth0_ipv6: "2001:db8:1::1/64"    # Management IPv6
  dut2:
    eth0_ipv6: "2001:db8:2::1/64"    # Management IPv6
  dut3:
    eth0_ipv6: "2001:db8:3::1/64"    # Management IPv6 (RX side)

testcases:
  ipv6_baseline:
    title: "IPv6 PERMIT all traffic"
    description: "Verify all IPv6 traffic passes ACL PERMIT rule"
    acl:
      tables:
        IPV6_ACL_TABLE_BASELINE:
          type: "L3"
          direction: "INGRESS"
          rules:
            - seq: 10
              rule_name: "RULE_1_PERMIT_ALL"
              action: "permit"
              src_ipv6: "any"
              dst_ipv6: "any"
              protocol: "tcp"

    traffic:
      protocol: "tcp"
      src_ipv6: "2001:db8:100::1"
      dst_ipv6: "2001:db8:200::1"
      src_port: 12345
      dst_port: 443
      expected_rx: 100          # All 100 packets expected
      expected_rx_min_pct: 98   # 98% for hardware, 95% for VS

    validation:
      method: "packet_count"
      threshold_hw: 98          # Hardware threshold
      threshold_vs: 95          # Virtual threshold

  ipv6_deny_multicast:
    title: "IPv6 DENY multicast traffic"
    description: "Verify multicast traffic is denied"
    acl:
      tables:
        IPV6_ACL_TABLE_MCAST:
          type: "L3"
          direction: "INGRESS"
          rules:
            - seq: 10
              rule_name: "RULE_1_DENY_MULTICAST"
              action: "deny"
              dst_ipv6: "ff00::/8"      # Multicast range
            - seq: 20
              rule_name: "RULE_2_PERMIT_REST"
              action: "permit"
              src_ipv6: "any"
              dst_ipv6: "any"

    traffic:
      protocol: "icmpv6"
      src_ipv6: "2001:db8:100::1"
      dst_ipv6: "ff02::1"               # Multicast address
      expected_rx: 0                    # All denied

    validation:
      method: "packet_count"
      threshold: 0
```

---

## Implementation Phases

### Phase 1: Infrastructure Setup (Week 1)
- ✅ Create test file structure
- ✅ Create YAML configuration files
- ✅ Setup IPv6 testbed configuration
- ✅ Validate IPv6 connectivity between DUTs
- **Deliverable**: Working test skeleton

### Phase 2: Baseline Tests (Week 2-3)
- ✅ Implement basic PERMIT/DENY tests
- ✅ Add port matching tests
- ✅ Add protocol matching tests
- ✅ Add rule precedence tests
- ✅ Validate all baseline tests pass
- **Deliverable**: Comprehensive baseline test suite

### Phase 3: Negative Tests (Week 3-4)
- ✅ Implement edge case tests
- ✅ Add IPv6-specific scenarios
- ✅ Add address variant handling
- ✅ Validate error handling
- **Deliverable**: Negative test coverage

### Phase 4: Robustness Tests (Week 4-5)
- ✅ Implement scale tests
- ✅ Add high-traffic scenarios
- ✅ Add persistence tests
- ✅ Add reboot validation
- **Deliverable**: Production-level robustness tests

### Phase 5: Documentation & Review (Week 5)
- ✅ Create comprehensive documentation
- ✅ Code review and optimization
- ✅ Performance baseline establishment
- **Deliverable**: Production-ready test suite

---

## Reusable Patterns (from IPv4 ACL)

### Pattern 1: ACL Rule Creation with Parameter Extraction
```python
@classmethod
def _create_acl_rules(cls, dut, acl_config):
    """Create ACL rules dynamically from YAML configuration.

    Extracts and validates:
    - Source/destination IPv6 addresses
    - Protocol (TCP, UDP, ICMPv6, etc.)
    - Port ranges and specific ports
    - TCP flags
    """
    # Implementation reuses IPv4 pattern
```

### Pattern 2: Traffic Generation with Protocol Support
```python
def _generate_ipv6_traffic(
    self,
    src_ipv6: str,
    dst_ipv6: str,
    protocol: str = "tcp",
    dst_port: int = None,
    duration: int = 10
):
    """Generate IPv6 traffic with protocol-specific parameters.

    Routes to:
    - send_traffic() for basic UDP/TCP
    - send_traffic_with_tcp_flags() for TCP with specific flags
    """
```

### Pattern 3: Platform-Specific Thresholds
```python
is_virtual = "vsonic" in str(self.data.dut1).lower()
min_rx_ratio = 95.0 if is_virtual else 98.0
```

### Pattern 4: Defensive Type Checking
```python
if isinstance(output, str):
    lines = output.split('\n')
elif isinstance(output, list):
    lines = [str(item) for item in output]
else:
    lines = str(output).split('\n')
```

---

## IPv6-Specific Considerations

### IPv6 Address Formats
```python
# Compressed form (default)
src_ipv6 = "2001:db8::1"

# Uncompressed form
src_ipv6 = "2001:0db8:0000:0000:0000:0000:0000:0001"

# IPv4-mapped IPv6
src_ipv6 = "::ffff:192.0.2.1"

# Link-local
src_ipv6 = "fe80::1"

# Multicast
src_ipv6 = "ff02::1"

# Any address
src_ipv6 = "any" or "::/0"
```

### IPv6 Protocol Numbers
```python
TCP = 6
UDP = 17
ICMPv6 = 58
IGMP = 2
HOPOPT = 0        # Hop-by-hop options
```

### IPv6-Specific Traffic Patterns
```python
# Echo request (ping)
send_ipv6_icmp_echo_request(src, dst, count=100)

# ICMPv6 Neighbor Discovery
send_ipv6_nd_request(src, dst, count=100)

# Multicast listener query
send_ipv6_mld_query(src, mcast_addr, count=100)

# TCP SYN to specific port
send_ipv6_tcp_syn(src, dst, dst_port=443, count=100)
```

---

## Success Metrics

### Test Coverage
| Category | Target |
|----------|--------|
| Baseline Tests | 15+ test cases |
| Negative Tests | 15+ test cases |
| Robustness Tests | 15+ test cases |
| Total Code Lines | 2,000+ lines |

### Quality Metrics
| Metric | Target |
|--------|--------|
| Syntax Check | 100% PASS |
| Code Coverage | 90%+ |
| Test Pass Rate | 95%+ (VS), 98%+ (HW) |
| Documentation | Comprehensive |

### Performance Metrics
| Metric | Target |
|--------|--------|
| Test Execution Time | <5 min (baseline), <10 min (all) |
| Packet Loss | <2% (HW), <5% (VS) |
| Traffic Throughput | 10K+ pps |

---

## Dependencies & Requirements

### Framework Dependencies
- ✅ SpyTest framework (existing)
- ✅ Scapy traffic generator (existing)
- ✅ IPv6 support in SONiC
- ✅ IPv6-enabled testbed

### API Functions Needed
```python
# ACL API
acl_api.create_acl_table()
acl_api.create_acl_rule()
acl_api.bind_acl_table()
acl_api.unbind_acl_table()
acl_api.delete_acl_rule()
acl_api.delete_acl_table()
acl_api.show_acl()
acl_api.show_acl_rules()

# Traffic API
scapy_traffic.send_traffic(protocol="tcp", ...)
scapy_traffic_advanced.send_traffic_with_tcp_flags()
scapy_traffic.get_interface_mac()
scapy_traffic.start_tcpdump()
scapy_traffic.stop_tcpdump()

# Verification API
st.show(dut, "show ipv6 interface")
st.show(dut, "show ip access-lists")
st.show(dut, "show statistics")
```

---

## Risk Assessment

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| IPv6 not supported | Low | High | Verify SONiC IPv6 support early |
| API incompatibility | Low | Medium | Validate API signatures |
| Testbed IPv6 issues | Medium | High | Pre-test IPv6 connectivity |
| Traffic generation | Low | High | Reuse proven IPv4 patterns |

### Schedule Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | High | Medium | Strict phase boundaries |
| Resource constraints | Low | Medium | Parallel development |
| Integration issues | Medium | Medium | Early integration testing |

---

## Resource Requirements

### Development Team
- 1-2 Test Engineers (Full-time)
- 1 QA Reviewer (Part-time)
- 1 Framework Support (As needed)

### Infrastructure
- 2-3 Test Devices (SONiC-based)
- Traffic Generator (Scapy-based)
- Testbed with IPv6 connectivity
- CI/CD pipeline for test execution

### Time Estimate
- **Total Duration**: 4-5 weeks
- **Phase 1**: 3-5 days
- **Phase 2**: 5-7 days
- **Phase 3**: 5-7 days
- **Phase 4**: 5-7 days
- **Phase 5**: 2-3 days

---

## Deliverables

### Code Deliverables
1. `test_ipv6_acl.py` - Baseline tests (500+ lines)
2. `test_ipv6_acl_negative.py` - Negative tests (500+ lines)
3. `test_ipv6_acl_robustness.py` - Robustness tests (500+ lines)
4. `vars_ipv6_acl.yaml` - Test configuration (300+ lines)

### Documentation Deliverables
1. IPv6 ACL Test Plan (this document)
2. IPv6 ACL Test Case Documentation
3. IPv6 ACL Configuration Guide
4. IPv6 ACL Troubleshooting Guide
5. Test Execution Report

### Quality Deliverables
1. Syntax verification report
2. Test coverage report
3. Performance baseline report
4. Code review sign-off

---

## Success Criteria

- ✅ All test cases execute without errors
- ✅ 95%+ pass rate on virtual platforms
- ✅ 98%+ pass rate on hardware platforms
- ✅ Comprehensive documentation
- ✅ Code review approval
- ✅ Performance baseline established
- ✅ Production-ready status

---

## Future Enhancements (Phase 2)

### Extended IPv6 ACL Features
- IPv6 fragmentation handling
- IPv6 extension headers
- ICMPv6 specific type/code matching
- Neighbor Discovery filtering
- MLD (Multicast Listener Discovery) filtering

### Advanced Testing
- IPv6 over tunnel scenarios
- Dual-stack (IPv4+IPv6) ACLs
- IPv6 with VRF and QoS
- Scale testing (10,000+ rules)
- Performance optimization

### Integration Testing
- IPv6 ACL with BGP/OSPFv3
- IPv6 ACL with PortChannel
- IPv6 ACL with LAG failover
- IPv6 ACL with VLAN tagging

---

## Approval & Sign-off

| Role | Approval | Date |
|------|----------|------|
| Test Lead | Pending | TBD |
| Framework Owner | Pending | TBD |
| Quality Lead | Pending | TBD |

---

**Document Status**: 📋 READY FOR REVIEW & APPROVAL

This plan is ready for stakeholder review and approval before implementation begins.

