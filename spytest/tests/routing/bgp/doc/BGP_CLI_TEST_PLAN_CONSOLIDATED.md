# BGP CLI Command Validation Test Plan - Consolidated

**Document Version:** 1.0
**Date Created:** 2026-05-28
**Test Plan Type:** CLI Command Validation
**Status:** Ready for Automation
**Total Test Cases:** 267
**Priority:** P1-P2 (High to Medium)

---

## Document Purpose

This document consolidates all BGP CLI command validation test cases into a single reference. These tests focus on **CLI syntax, error handling, and configuration validation** - complementing the customer-approved functional test plan.

---

## 📊 Test Plan Statistics

| Category | Test Cases | Commands | Priority |
|----------|------------|----------|----------|
| **Neighbor Configuration** | 180 | 12 commands | P1 |
| **Redistribute & VRF Import** | 35 | 6 command groups | P1 |
| **Clear Commands** | 52 | 15+ variants | P2 |
| **TOTAL** | **267** | **30+** | **Mixed** |

---

## 🎯 Test Coverage

### **1. BGP Neighbor Configuration Commands (180 Test Cases)**

**Document:** `BGP_CLI_NEIGHBOR_CONFIG_TEST_CASES.md`
**Testbed:** `testbed_vs_3rr_reg.yaml`

| Command | Test Cases | Test Types |
|---------|------------|------------|
| `bfd check-control-plane-failure` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `disable-connected-check` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `enforce-first-as` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `enforce-multihop` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `advertisement-interval` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `capability dynamic` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `capability extended-nexthop` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `ebgp-multihop` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `local-as` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `shutdown message` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `timers connect` | 15 | Positive, Negative, Edge, Persistence, Functional |
| `v6only` | 15 | Positive, Negative, Edge, Persistence, Functional |

---

### **2. Redistribute & VRF Import Commands (35 Test Cases)**

**Document:** `BGP_REDISTRIBUTE_VRF_IMPORT_TEST_CASES.md`
**Testbed:** `testbed_vs_3rr_reg.yaml`

| Command Group | Positive | Negative | Edge | Total |
|---------------|----------|----------|------|-------|
| `redistribute ospf / ospfv3` | 2 | 2 | 2 | 6 |
| `redistribute metric` | 1 | 1 | 1 | 3 |
| `redistribute route-map` | 1 | 2 | 1 | 4 |
| `no redistribute` | 2 | 2 | 2 | 6 |
| `import vrf route-map` | 4 | 2 | 2 | 8 |
| `no import vrf` | 4 | 2 | 2 | 8 |
| **TOTAL** | **14** | **11** | **10** | **35** |

---

### **3. Clear BGP Commands (52 Test Cases)**

**Document:** `TC_BGP_CLEAR_COMMANDS_COMPREHENSIVE.md`
**Testbed:** `testbed_vs_3rr_reg.yaml`

| Command Category | Positive | Negative | Total |
|------------------|----------|----------|-------|
| `clear bgp all` | 1 | 2 | 3 |
| `clear bgp ipv4 unicast *` | 6 | 4 | 10 |
| `clear bgp ipv4 unicast (specific)` | 6 | 2 | 8 |
| `clear bgp ipv6 unicast *` | 6 | 4 | 10 |
| `clear bgp ipv6 unicast (specific)` | 6 | 2 | 8 |
| Soft reconfiguration | 12 | 1 | 13 |
| **TOTAL** | **37** | **15** | **52** |

---

## 🔗 Relationship with Customer-Approved Plan

### **Complementary Coverage:**

```
┌─────────────────────────────────────────────────────────┐
│ Customer-Approved Functional Test Plan (168 TCs)       │
│                                                         │
│ Focus: "Does BGP work correctly?"                       │
│ - Peering establishment                                 │
│ - Route exchange and policies                           │
│ - Scalability and HA                                    │
│ - Advanced features (EVPN, IPv6, etc.)                  │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Complements (no overlap)
                           ▼
┌─────────────────────────────────────────────────────────┐
│ CLI Command Validation Test Plan (267 TCs)             │
│                                                         │
│ Focus: "Does each CLI command work correctly?"          │
│ - Syntax validation                                     │
│ - Error handling                                        │
│ - Configuration persistence                             │
│ - Edge cases and boundaries                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Test Execution

### **Run All CLI Tests:**

```bash
cd /home/sonic-claude/athira/sonic-mgmt/spytest

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_cli_neighbor_config.py \
  tests/routing/bgp/test_bgp_cli_redistribute_vrf.py \
  tests/routing/bgp/test_bgp_cli_clear_commands.py \
  --logs-path ./logs/bgp_cli_all_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

### **Run by Category:**

**Neighbor Configuration Only:**
```bash
./bin/spytest --testbed ./testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_cli_neighbor_config.py \
  --logs-path ./logs/bgp_cli_neighbor_$(date +%F_%H%M%S)
```

**Redistribute/VRF Only:**
```bash
./bin/spytest --testbed ./testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_cli_redistribute_vrf.py \
  --logs-path ./logs/bgp_cli_redist_$(date +%F_%H%M%S)
```

**Clear Commands Only:**
```bash
./bin/spytest --testbed ./testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_cli_clear_commands.py \
  --logs-path ./logs/bgp_cli_clear_$(date +%F_%H%M%S)
```

---

## 📋 Test Case Naming Convention

### **Format:**
```
TC-BGP-CLI-[CATEGORY]-[NNN]
```

### **Examples:**
- `TC-BGP-CLI-NEIGHBOR-001`: BFD check-control-plane-failure positive test
- `TC-BGP-CLI-REDIST-015`: OSPF redistribution negative test
- `TC-BGP-CLI-CLEAR-029`: Invalid syntax for clear command

---

## 📁 Detailed Test Case Documents

### **For Complete Test Specifications, See:**

1. **Neighbor Configuration:** `BGP_CLI_NEIGHBOR_CONFIG_TEST_CASES.md`
   - 180 test cases with full procedures
   - Test Steps, Expected Results, Cleanup procedures
   - 74 KB document

2. **Redistribute & VRF Import:** `BGP_REDISTRIBUTE_VRF_IMPORT_TEST_CASES.md`
   - 35 test cases with full procedures
   - Test configuration tables, validation commands
   - 57 KB document

3. **Clear Commands:** `TC_BGP_CLEAR_COMMANDS_COMPREHENSIVE.md`
   - 52 test cases with full procedures
   - Session reset validation, soft reconfiguration tests
   - 56 KB document

---

## ✅ Automation Status

| Test Suite | Test Cases | Status | Priority |
|------------|------------|--------|----------|
| Neighbor Config | 180 | ⬜ Not Automated | P1 |
| Redistribute/VRF | 35 | ⬜ Not Automated | P1 |
| Clear Commands | 52 | ⬜ Not Automated | P2 |

**Next Step:** Implement Python test scripts for each suite

---

## 📝 Test Plan Maintenance

### **Adding New CLI Tests:**

1. Identify new CLI command to test
2. Create test cases following existing format
3. Add to appropriate category document
4. Update this consolidated plan
5. Implement automation script

### **Modifying Existing Tests:**

- Update individual test case documents
- Sync changes to consolidated plan
- Update automation scripts
- Re-run regression suite

---

## 📚 Related Documents

- **Customer-Approved Functional Plan:** `bgp_testplan.md` (168 TCs)
- **Organization Guide:** `README_BGP_TEST_DOCUMENTATION.md`
- **Redistribute/VRF Summary:** `BGP_REDIST_VRF_IMPORT_SUMMARY.md`
- **Redistribute/VRF README:** `README_BGP_REDIST_VRF_IMPORT_TESTS.md`

---

**Document Status:** Complete and Ready for Automation
**Last Updated:** 2026-05-28
