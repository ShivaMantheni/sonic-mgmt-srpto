# BGP Test Documentation - Organization Guide

**Location:** `/home/sonic-claude/athira/sonic-mgmt/spytest/tests/routing/bgp/doc/`
**Last Updated:** 2026-05-28
**Purpose:** Clear organization of BGP test plans and documentation

---

## 📋 Document Organization

This directory contains **TWO SEPARATE** BGP test plan categories:

### 1. **Customer-Approved Functional Test Plan** ✅
### 2. **CLI Command Validation Test Plans** 🆕

---

## 📁 File Structure

### **Category 1: Customer-Approved Functional Tests**

#### **bgp_testplan.md** (1.2 MB - 42,592 lines)
```
Status:     ✅ CUSTOMER APPROVED
Test Cases: 168 comprehensive functional tests
Sections:   19 (Sections 1-19)
Focus:      BGP functional behavior and operations
Priority:   P0 - Critical for production
```

**Coverage:**
- BGP Basic Functionality (12 TCs)
- BGP Unnumbered Interfaces (10 TCs)
- BGP over Loopback Interfaces (10 TCs)
- BGP VLAN Integration (10 TCs)
- BGP Path Attributes (8 TCs)
- BGP Route Policies (10 TCs)
- BGP Scalability (12 TCs)
- BGP High Availability (8 TCs)
- BGP Advanced Features (10 TCs)
- BGP Packet Validation (12 TCs)
- BGP Negative Testing (10 TCs)
- BGP Configuration Verification (8 TCs)
- IPv6 Address Family Explicit (8 TCs)
- L2VPN EVPN Address Family (6 TCs)
- ECMP Hardware Limits (4 TCs)
- Peer Groups & Dynamic Peers (6 TCs)
- Next-Hop-Self (4 TCs)
- Advertisement Intervals & Soft Reconfiguration (5 TCs)
- Route Map Advanced Features (8 TCs)

**⚠️ IMPORTANT:** This test plan is customer-approved and must NOT be modified.

---

### **Category 2: CLI Command Validation Tests**

These test plans focus on CLI command syntax, error handling, and configuration validation.

#### **BGP_CLI_COMPREHENSIVE_TEST_PLAN.md** (21 KB)
```
Status:     🆕 NEW - Master Template
Purpose:    Consolidation template for all CLI tests
Test Cases: Template for 300+ CLI tests
Focus:      CLI command validation framework
```

**Role:** Master template that consolidates all CLI test plans below.

---

#### **BGP_CLI_NEIGHBOR_CONFIG_TEST_CASES.md** (74 KB)
```
Status:     🆕 NEW - Ready for Automation
Test Cases: 180 test cases
Commands:   12 neighbor configuration commands
Focus:      BGP neighbor CLI validation
```

**Coverage:**
- BFD check-control-plane-failure (15 TCs)
- disable-connected-check (15 TCs)
- enforce-first-as (15 TCs)
- enforce-multihop (15 TCs)
- advertisement-interval (15 TCs)
- capability dynamic (15 TCs)
- capability extended-nexthop (15 TCs)
- ebgp-multihop (15 TCs)
- local-as (15 TCs)
- shutdown message (15 TCs)
- timers connect (15 TCs)
- v6only (15 TCs)

**Test Types per Command:**
- Positive tests (valid configurations)
- Negative tests (invalid inputs)
- Edge tests (boundary conditions)
- Persistence tests (save/reload)
- Functional tests (operational behavior)

---

#### **BGP_REDISTRIBUTE_VRF_IMPORT_TEST_CASES.md** (57 KB)
```
Status:     🆕 NEW - Ready for Automation
Test Cases: 35 test cases
Commands:   6 command groups
Focus:      Route redistribution and VRF import
```

**Coverage:**
- redistribute ospf / ospfv3 (6 TCs)
- redistribute metric (3 TCs)
- redistribute route-map (4 TCs)
- no redistribute variants (6 TCs)
- import vrf route-map (8 TCs)
- no import vrf variants (8 TCs)

**Test Types:**
- Positive: 15 test cases
- Negative: 12 test cases
- Edge Cases: 8 test cases

---

#### **TC_BGP_CLEAR_COMMANDS_COMPREHENSIVE.md** (56 KB)
```
Status:     🆕 NEW - Ready for Automation
Test Cases: 52 test cases
Commands:   BGP clear/reset commands
Focus:      Session reset and soft reconfiguration
```

**Coverage:**
- clear bgp all (3 TCs)
- clear bgp ipv4 unicast variants (14 TCs)
- clear bgp ipv6 unicast variants (14 TCs)
- clear bgp soft reconfiguration (12 TCs)
- Negative tests (9 TCs)

---

#### **BGP_REDIST_VRF_IMPORT_SUMMARY.md** (13 KB)
```
Purpose:    Quick reference for redistribute/VRF tests
Content:    Test case index, automation notes, verification commands
```

---

#### **README_BGP_REDIST_VRF_IMPORT_TESTS.md** (13 KB)
```
Purpose:    Documentation index for redistribute/VRF tests
Content:    Overview, implementation guide, execution instructions
```

---

## 🎯 Usage Guidelines

### **For Test Execution:**

#### **Functional Testing (Customer-Approved):**
```bash
# Execute customer-approved functional tests
cd /home/sonic-claude/athira/sonic-mgmt/spytest
./bin/spytest --testbed testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_functional.py \
  --logs-path ./logs/bgp_functional_$(date +%F_%H%M%S)
```

#### **CLI Command Validation:**
```bash
# Execute CLI command tests
./bin/spytest --testbed testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_cli_commands.py \
  --logs-path ./logs/bgp_cli_$(date +%F_%H%M%S)
```

---

### **For Test Development:**

#### **Adding to Customer-Approved Plan:**
⚠️ **RESTRICTED** - Requires customer approval
- Cannot modify existing 168 test cases
- Can only ADD new sections with customer review

#### **Adding to CLI Plans:**
✅ **ALLOWED** - Internal test development
- Add new CLI command tests as needed
- Follow existing test case format
- Update CLI comprehensive plan accordingly

---

## 📊 Test Coverage Summary

### **Combined Coverage:**

| Category | Test Cases | Commands Covered | Status |
|----------|------------|------------------|--------|
| **Functional (Approved)** | 168 | 50+ functional scenarios | ✅ Approved |
| **CLI Neighbor Config** | 180 | 12 neighbor commands | 🆕 New |
| **CLI Redistribute/VRF** | 35 | 6 command groups | 🆕 New |
| **CLI Clear Commands** | 52 | Clear/reset commands | 🆕 New |
| **TOTAL** | **435** | **Comprehensive** | **Mixed** |

---

## 🔄 Relationship Between Test Plans

```
┌────────────────────────────────────────────────────────┐
│  Customer-Approved Functional Test Plan (168 TCs)     │
│  • End-to-end BGP functionality                        │
│  • Production-critical scenarios                       │
│  • MUST NOT be modified without approval               │
└────────────────────────────────────────────────────────┘
                          │
                          │ Complements
                          ▼
┌────────────────────────────────────────────────────────┐
│  CLI Command Validation Test Plans (267 TCs)           │
│  • Individual CLI command testing                      │
│  • Syntax and error handling validation                │
│  • Can be extended independently                       │
└────────────────────────────────────────────────────────┘
```

**Key Difference:**
- **Functional Tests:** "Does BGP work correctly?"
- **CLI Tests:** "Does each CLI command work correctly?"

---

## 📝 Document Maintenance

### **Customer-Approved Plan (bgp_testplan.md):**
- **Owner:** Customer + QA Team
- **Changes:** Require customer approval
- **Updates:** Version controlled with customer sign-off
- **Frequency:** Major releases only

### **CLI Test Plans:**
- **Owner:** QA Team
- **Changes:** Internal approval only
- **Updates:** As needed for CLI coverage
- **Frequency:** Sprint-based updates

---

## 🚀 Next Steps

### **Immediate Actions:**

1. **Execute Customer-Approved Tests:**
   - Priority: P0 (Critical)
   - Run against all supported SONiC versions
   - Track results in dashboard

2. **Automate CLI Tests:**
   - Implement test scripts for 267 CLI test cases
   - Create Python test files
   - Add to regression suite

3. **Gap Analysis:**
   - Compare BGP cheatsheet commands with both test plans
   - Identify missing coverage
   - Create additional test cases as needed

---

## 📞 Contact & Support

### **For Customer-Approved Plan:**
- **Questions:** Contact customer and QA lead
- **Changes:** Formal approval process required
- **Issues:** Log in approved channels

### **For CLI Test Plans:**
- **Questions:** Contact QA team
- **Changes:** Internal review process
- **Issues:** Track in QA ticketing system

---

## 📚 References

### **Related Documentation:**
- SPyTest Framework: `../../../README.md`
- BGP API: `../../../apis/routing/bgp.py`
- Testbed Files: `../../../testbeds/`

### **External References:**
- SONiC BGP HLD: https://github.com/sonic-net/SONiC/blob/master/doc/bgp/BGP-HLD.md
- FRR BGP: https://docs.frrouting.org/en/latest/bgp.html

---

**Document Version:** 1.0
**Last Updated:** 2026-05-28
**Status:** Active
