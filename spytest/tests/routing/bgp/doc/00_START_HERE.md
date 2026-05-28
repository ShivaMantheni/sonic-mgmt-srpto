# BGP Test Documentation - Start Here

**Location:** `/home/sonic-claude/athira/sonic-mgmt/spytest/tests/routing/bgp/doc/`
**Last Updated:** 2026-05-28

---

## 🚀 Quick Start

### **I want to:**

#### **Run functional BGP tests (customer-approved)**
→ See: `bgp_testplan.md` (168 test cases)

#### **Run CLI command validation tests**
→ See: `BGP_CLI_TEST_PLAN_CONSOLIDATED.md` (267 test cases)

#### **Understand the organization**
→ See: `README_BGP_TEST_DOCUMENTATION.md`

#### **Find specific test details**
→ See file listing below

---

## 📁 File Organization

### **Customer-Approved Tests** ✅

| File | Description | Test Cases |
|------|-------------|------------|
| **bgp_testplan.md** | Customer-approved functional test plan | 168 |

### **CLI Validation Tests** 🆕

| File | Description | Test Cases |
|------|-------------|------------|
| **BGP_CLI_TEST_PLAN_CONSOLIDATED.md** | Consolidated CLI test plan (all CLI tests) | 267 |
| **BGP_CLI_NEIGHBOR_CONFIG_TEST_CASES.md** | Neighbor configuration CLI tests | 180 |
| **BGP_REDISTRIBUTE_VRF_IMPORT_TEST_CASES.md** | Redistribute and VRF import tests | 35 |
| **TC_BGP_CLEAR_COMMANDS_COMPREHENSIVE.md** | Clear command tests | 52 |

### **Documentation & Support**

| File | Purpose |
|------|---------|
| **00_START_HERE.md** | This file - quick navigation guide |
| **README_BGP_TEST_DOCUMENTATION.md** | Complete organization guide |
| **BGP_REDIST_VRF_IMPORT_SUMMARY.md** | Summary for redistribute/VRF tests |
| **README_BGP_REDIST_VRF_IMPORT_TESTS.md** | Guide for redistribute/VRF tests |
| **BGP_CLI_COMPREHENSIVE_TEST_PLAN.md** | Master template for CLI tests |

---

## 📊 Test Coverage Summary

```
Total Test Cases: 435
├── Customer-Approved Functional: 168 ✅
└── CLI Command Validation: 267 🆕
    ├── Neighbor Config: 180
    ├── Redistribute/VRF: 35
    └── Clear Commands: 52
```

---

## 🎯 Common Tasks

### **Execute All Tests:**
```bash
cd /home/sonic-claude/athira/sonic-mgmt/spytest

# Functional tests
./bin/spytest --testbed testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_functional.py

# CLI tests
./bin/spytest --testbed testbeds/testbed_vs_3rr_reg.yaml \
  tests/routing/bgp/test_bgp_cli_*.py
```

### **View Test Case Details:**
```bash
cd /home/sonic-claude/athira/sonic-mgmt/spytest/tests/routing/bgp/doc/

# Customer-approved functional tests
less bgp_testplan.md

# CLI tests consolidated view
less BGP_CLI_TEST_PLAN_CONSOLIDATED.md
```

---

## ⚠️ Important Notes

### **Customer-Approved Plan:**
- File: `bgp_testplan.md`
- Status: **APPROVED - Do NOT modify without customer approval**
- Test Cases: 168
- Can only ADD new sections with approval

### **CLI Test Plans:**
- Status: **NEW - Can be modified internally**
- Test Cases: 267
- Can be extended as needed

---

## 📞 Need Help?

### **For Customer-Approved Tests:**
- Contact: Customer + QA Lead
- Process: Formal approval required

### **For CLI Tests:**
- Contact: QA Team
- Process: Internal review

---

## 🔗 Quick Links

| Document | Link |
|----------|------|
| Customer Test Plan | [bgp_testplan.md](./bgp_testplan.md) |
| CLI Tests (All) | [BGP_CLI_TEST_PLAN_CONSOLIDATED.md](./BGP_CLI_TEST_PLAN_CONSOLIDATED.md) |
| Organization Guide | [README_BGP_TEST_DOCUMENTATION.md](./README_BGP_TEST_DOCUMENTATION.md) |
| Neighbor CLI Tests | [BGP_CLI_NEIGHBOR_CONFIG_TEST_CASES.md](./BGP_CLI_NEIGHBOR_CONFIG_TEST_CASES.md) |
| Redistribute Tests | [BGP_REDISTRIBUTE_VRF_IMPORT_TEST_CASES.md](./BGP_REDISTRIBUTE_VRF_IMPORT_TEST_CASES.md) |
| Clear Command Tests | [TC_BGP_CLEAR_COMMANDS_COMPREHENSIVE.md](./TC_BGP_CLEAR_COMMANDS_COMPREHENSIVE.md) |

---

**Version:** 1.0
**Status:** Active
