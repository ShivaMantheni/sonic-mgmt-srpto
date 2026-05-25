# L2 ACL Test Suite - Documentation Index

**Date**: 2026-04-25
**Status**: ✓ COMPLETE - Ready for Manual Device Execution
**Project**: SONiC MAC ACL Testing on DUT1 (192.168.100.137)

---

## Overview

This directory contains comprehensive documentation for testing MAC ACL (Layer 2 Access Control List) functionality on SONiC network devices. The test suite covers L2 ACL configuration, verification, and traffic testing using industry-standard Scapy packet generation.

**Key Achievement**: Identified and corrected MAC ACL CLI syntax through device validation. All documentation reflects verified working patterns.

---

## Document Structure

### Quick Start (5 minutes)

**For users in a hurry:**
1. Read: `/tmp/L2-02-COMPLETE-TEST-PACKAGE.txt` → "QUICK START - 4 MINUTE SUMMARY" section
2. Copy configuration block
3. Paste into device
4. Run 4 verification commands
5. Execute 2 test scenarios

---

### Core Documentation Files

#### 1. L2-01: Permit Exact Source MAC
**Purpose**: Test MAC ACL permitting traffic from a specific source MAC address

**Files**:
- `L2-01-WORKING-CONFIG.md` (detailed configuration guide with verified syntax)
- `/tmp/L2-01-QUICK-REFERENCE-CORRECTED.txt` (quick lookup reference)
- `/tmp/L2-01-CONFIGDB-VERIFICATION.txt` (ConfigDB verification guide)

**Key Concept**:
- Rule 10: `seq 10 permit host 00:AA:AA:AA:AA:01 any` (allow specific MAC)
- Implicit: Deny all other MACs
- Test: Send 10 packets → Expect ≥9 RX (90% pass)

**Status**: ✓ Configuration verified in ConfigDB on DUT1

---

#### 2. L2-02: Deny Exact Source MAC (NEW)
**Purpose**: Test MAC ACL denying traffic from a specific source MAC address (inverse of L2-01)

**Files** (START HERE):
- `L2-02-EXECUTION-GUIDE.md` ← **PRIMARY DOCUMENT** (step-by-step execution)
- `L2-02-WORKING-CONFIG.md` (detailed reference with full context)
- `/tmp/L2-02-QUICK-REFERENCE.txt` (quick lookup reference)
- `/tmp/L2-02-COMPLETE-TEST-PACKAGE.txt` (complete package summary)

**Key Concept**:
- Rule 10: `seq 10 deny host 00:AA:AA:AA:AA:01 any` (block specific MAC)
- Rule 20: `seq 20 permit any any` (CRITICAL: catch-all permit for others)
- Without Rule 20: All traffic blocked (incorrect)
- With Rule 20: Only denied MAC blocked (correct)
- Test 1: Send denied MAC → Expect 0 RX (all dropped)
- Test 2: Send other MAC → Expect ≥9 RX (allowed by catch-all)

**Status**: ✓ Documentation complete - Ready for manual execution

---

### Reference Documents

#### 3. ACL CLI Hook (`/home/claudeuser/.claude/acl_cli_hook.md`)
**Purpose**: Memorized central reference with 183 production-ready ACL commands

**Content**:
- MAC ACL syntax patterns (corrected - uses `host` keyword)
- IP/IPv6 ACL syntax patterns
- ACL binding patterns for all interface types
- 28 show commands for verification
- Common patterns and examples
- Infrastructure support matrix (Ethernet, PortChannel, VLAN, Global, CtrlPlane, CPU)

**Key Update**: Changed from `seq 10 permit source-mac 00:AA:AA:AA:AA:01` to `seq 10 permit host 00:AA:AA:AA:AA:01 any`

**Status**: ✓ Updated with verified syntax

---

## Critical Syntax Correction

### The Error
Initial documentation used incorrect MAC ACL syntax:
```
❌ WRONG:
  seq 10 permit source-mac 00:AA:AA:AA:AA:01
```

### The Fix
User provided working pattern; verified on device:
```
✓ CORRECT:
  seq 10 permit host 00:AA:AA:AA:AA:01 any
```

### Key Differences
1. **Must use `seq` keyword** (not just rule number)
2. **Must use `host` keyword** (not `source-mac`)
3. **Must specify destination MAC** (or `any`)

---

## Execution Paths

### Path 1: Quick Execution (15 minutes)
```
1. Read: L2-02-EXECUTION-GUIDE.md
2. Step 1: SSH to device
3. Step 2: Enter sonic-cli
4. Step 3: Copy-paste configuration
5. Step 4: Verify with 4 show commands
6. Run Test Scenario 1 (denied MAC)
7. Run Test Scenario 2 (allowed MAC)
8. Mark complete if both PASS
```

### Path 2: Detailed Understanding (30 minutes)
```
1. Read: L2-02-EXECUTION-GUIDE.md (overview)
2. Read: L2-02-WORKING-CONFIG.md (detailed context)
3. Understand: "Why Rule 20 Is Critical" section
4. Review: L2-01-WORKING-CONFIG.md (comparison)
5. Execute: Steps 1-7 from Path 1
6. Verify: ConfigDB values (optional)
```

### Path 3: Complete Learning (45 minutes)
```
1. Read: L2-01-WORKING-CONFIG.md (understand permit first)
2. Read: L2-02-WORKING-CONFIG.md (understand deny)
3. Read: L2-02-EXECUTION-GUIDE.md (detailed execution)
4. Review: acl_cli_hook.md (syntax patterns)
5. Execute: Both L2-01 and L2-02 tests
6. Document: Results and observations
7. Explore: Additional L2 ACL patterns
```

---

## File Navigation

### Essential Files (Start Here)

```
/home/claudeuser/Athira/sonic-mgmt/spytest/tests/switching/l2_acl/report/manual/
├── L2-02-EXECUTION-GUIDE.md ← PRIMARY: Step-by-step L2-02 execution
├── L2-02-WORKING-CONFIG.md ← DETAILED: Full L2-02 context and explanations
├── L2-01-WORKING-CONFIG.md ← REFERENCE: L2-01 (permit) for comparison
├── INDEX.md ← THIS FILE (navigation guide)
└── [other files]
```

### Quick Reference Files (In /tmp/)

```
/tmp/
├── L2-02-COMPLETE-TEST-PACKAGE.txt ← SUMMARY: Complete L2-02 package overview
├── L2-02-QUICK-REFERENCE.txt ← QUICK: Fast lookup reference card
├── L2-01-QUICK-REFERENCE-CORRECTED.txt ← QUICK: Fast lookup for L2-01
└── [other files]
```

### Memorized Reference

```
/home/claudeuser/.claude/acl_cli_hook.md ← ACL CLI patterns (183 commands)
```

---

## How to Use This Index

### For Execution
1. **Recommended**: Use `L2-02-EXECUTION-GUIDE.md` (primary document)
2. **Reference**: Use `L2-02-WORKING-CONFIG.md` for detailed context during execution
3. **Quick Lookup**: Use `/tmp/L2-02-QUICK-REFERENCE.txt` for syntax patterns

### For Learning
1. **First**: Read `L2-01-WORKING-CONFIG.md` to understand PERMIT rules
2. **Second**: Read `L2-02-WORKING-CONFIG.md` to understand DENY rules and catch-all
3. **Reference**: Use `acl_cli_hook.md` for syntax patterns and examples

### For Troubleshooting
1. **Check**: `L2-02-EXECUTION-GUIDE.md` → "Troubleshooting" section
2. **Verify**: ConfigDB using commands in `L2-02-WORKING-CONFIG.md` → "ConfigDB Verification"
3. **Reference**: `acl_cli_hook.md` for correct syntax patterns

---

## Test Case Specifications

### L2-01: Permit Exact Source MAC
| Aspect | Value |
|--------|-------|
| **Purpose** | Allow traffic from specific MAC |
| **Action** | PERMIT |
| **Target MAC** | 00:AA:AA:AA:AA:01 |
| **Rule 10** | `seq 10 permit host 00:AA:AA:AA:AA:01 any` |
| **Implicit** | Deny all other MACs |
| **Test MAC** | 00:AA:AA:AA:AA:01 |
| **Expected RX** | ≥ 9 packets (90% pass) |
| **Pass Criteria** | RX ≥ 9 |
| **Status** | ✓ Verified in ConfigDB |

### L2-02: Deny Exact Source MAC (NEW)
| Aspect | Value |
|--------|-------|
| **Purpose** | Block traffic from specific MAC |
| **Action** | DENY |
| **Target MAC** | 00:AA:AA:AA:AA:01 |
| **Rule 10** | `seq 10 deny host 00:AA:AA:AA:AA:01 any` |
| **Rule 20** | `seq 20 permit any any` (catch-all) |
| **Critical** | MUST include Rule 20 |
| **Test 1 MAC** | 00:AA:AA:AA:AA:01 (denied) |
| **Test 1 RX** | 0 packets (all blocked) |
| **Test 2 MAC** | 00:CC:CC:CC:CC:CC (allowed) |
| **Test 2 RX** | ≥ 9 packets (allowed by rule 20) |
| **Pass Criteria** | Both tests PASS |
| **Status** | ✓ Documentation complete |

---

## Key Concepts

### L2 MAC ACL Syntax (Corrected)

**Rule Format**:
```
seq <N> <ACTION> host <SRC_MAC> <DST_MAC>
```

**Parameters**:
- `seq` = Sequence number (rule order)
- `<N>` = Number (10, 20, 30, etc.)
- `<ACTION>` = permit or deny
- `host` = Keyword for specific MAC match (required for exact MAC)
- `<SRC_MAC>` = Source MAC in xx:xx:xx:xx:xx:xx format
- `<DST_MAC>` = Destination MAC or `any`

**Examples**:
```
✓ seq 10 permit host 00:AA:AA:AA:AA:01 any
✓ seq 10 deny host 00:AA:AA:AA:AA:01 any
✓ seq 20 permit any any
✓ seq 30 permit host 00:CC:00:00:00:00 host 00:DD:00:00:00:00
❌ seq 10 permit source-mac 00:AA:AA:AA:AA:01 (WRONG)
❌ 10 permit 00:AA:AA:AA:AA:01 (WRONG)
```

### Rule 20 (Catch-All Permit) in L2-02

**Why Critical**:
- DENY rules require explicit catch-all PERMIT for non-denied traffic
- Without Rule 20: All traffic blocked (incorrect)
- With Rule 20: Only denied MAC blocked (correct)

**Impact**:
```
WITHOUT Rule 20:
  ├─ Denied MAC → DENY (correct)
  └─ Other MACs → Implicit DENY (incorrect - blocks all!)

WITH Rule 20:
  ├─ Denied MAC → DENY (blocks denied MAC)
  └─ Other MACs → PERMIT (allows others through)
```

### Verification (4 Show Commands)

```bash
show mac access-lists           # View all MAC ACLs
show mac access-group           # View ACL bindings to interfaces
show running-config interface Ethernet 272  # View interface config
show vlan id 10                 # View VLAN membership
```

---

## Test Execution Timeline

### Execution Overview
```
Total Time: ~15-25 minutes depending on path

Configuration: ~2 minutes
├─ SSH to device
├─ Enter sonic-cli
└─ Copy-paste configuration

Verification: ~3 minutes
├─ 4 show commands

Test Scenario 1 (Denied MAC): ~5 minutes
├─ Setup Scapy traffic generator
├─ Send 10 packets
└─ Verify RX = 0

Test Scenario 2 (Allowed MAC): ~5 minutes
├─ Setup Scapy traffic generator
├─ Send 10 packets
└─ Verify RX ≥ 9

Optional:
├─ ConfigDB verification: ~2 minutes
├─ Detailed understanding: +15 minutes
└─ Cleanup commands: ~2 minutes
```

---

## Next Steps After L2-02

Once L2-02 is complete, consider testing:

1. **L2-03**: Destination MAC matching (permit/deny destination MAC)
2. **L2-04**: EtherType matching (permit/deny protocol types)
3. **L2-05**: VLAN-based matching (permit/deny based on VLAN ID)
4. **L2-06**: Multiple rules (test 3+ rules and priority ordering)
5. **L2-07**: Egress binding (apply ACL to outgoing direction)
6. **L3-01**: L3 ACL (IPv4 source IP matching)
7. **L3-02**: L3 ACL (IPv4 destination IP matching)

---

## Document Relationships

```
EXECUTION:
  L2-02-EXECUTION-GUIDE.md
  └─ Detailed step-by-step (primary)

LEARNING:
  L2-01-WORKING-CONFIG.md
  └─ Understand PERMIT (base concept)
  L2-02-WORKING-CONFIG.md
  └─ Understand DENY + catch-all (advanced)

REFERENCE:
  acl_cli_hook.md
  └─ Syntax patterns (183 commands)
  /tmp/L2-02-QUICK-REFERENCE.txt
  └─ Quick lookup (copy-paste)
  /tmp/L2-02-COMPLETE-TEST-PACKAGE.txt
  └─ Complete summary (overview)
```

---

## File Locations Summary

| Document | Location | Purpose |
|----------|----------|---------|
| L2-02-EXECUTION-GUIDE.md | `tests/switching/l2_acl/report/manual/` | Primary execution guide |
| L2-02-WORKING-CONFIG.md | `tests/switching/l2_acl/report/manual/` | Detailed reference |
| L2-01-WORKING-CONFIG.md | `tests/switching/l2_acl/report/manual/` | Permit reference (comparison) |
| acl_cli_hook.md | `/home/claudeuser/.claude/` | Memorized CLI patterns (183 commands) |
| L2-02-COMPLETE-TEST-PACKAGE.txt | `/tmp/` | Complete summary |
| L2-02-QUICK-REFERENCE.txt | `/tmp/` | Quick lookup card |
| L2-01-QUICK-REFERENCE-CORRECTED.txt | `/tmp/` | L2-01 quick reference |
| INDEX.md | `tests/switching/l2_acl/report/manual/` | This file (navigation) |

---

## Status Summary

### Completed Tasks ✓
- [x] Identify correct MAC ACL CLI syntax (seq + host keywords)
- [x] Create L2-01 working configuration documentation
- [x] Create L2-02 working configuration documentation
- [x] Create L2-02 execution guide (step-by-step)
- [x] Create L2-02 quick reference card
- [x] Create comprehensive test package summary
- [x] Update acl_cli_hook.md with correct syntax
- [x] Document critical importance of Rule 20 (catch-all)
- [x] Provide Scapy traffic generator code for both tests
- [x] Document troubleshooting guide
- [x] Create navigation index (this file)

### Ready for Execution ✓
- [x] L2-02 configuration guide complete
- [x] Syntax verified on device
- [x] Test scenarios documented
- [x] Verification procedures documented
- [x] Troubleshooting guide provided
- [x] All files organized and accessible

### Pending Tasks
- [ ] User executes L2-02 on DUT1
- [ ] User documents test results
- [ ] User provides feedback or issues
- [ ] Create additional L2 ACL tests (L2-03 onwards) if requested

---

## Questions & Support

### Common Questions

**Q: Which file should I read first?**
A: Start with `L2-02-EXECUTION-GUIDE.md` (primary document). It has everything you need for execution.

**Q: Why is Rule 20 critical?**
A: Rule 20 (`seq 20 permit any any`) is the catch-all permit. Without it, all traffic is blocked (not just denied MAC). See "Why Rule 20 Is Critical" section in `L2-02-EXECUTION-GUIDE.md`.

**Q: What's the difference between L2-01 and L2-02?**
A: L2-01 permits a specific MAC (denies others implicitly). L2-02 denies a specific MAC (permits others explicitly via Rule 20).

**Q: How long does execution take?**
A: ~15 minutes for execution + 5-10 minutes for understanding = 20-25 minutes total.

**Q: What if I encounter errors?**
A: See "Troubleshooting" section in `L2-02-EXECUTION-GUIDE.md`.

### Support Resources

1. **Syntax Issues**: Check `acl_cli_hook.md` (memorized reference)
2. **Execution Issues**: Check `L2-02-EXECUTION-GUIDE.md` → "Troubleshooting"
3. **Understanding Issues**: Check `L2-02-WORKING-CONFIG.md` → detailed explanations
4. **ConfigDB Issues**: Check `L2-02-WORKING-CONFIG.md` → "ConfigDB Verification"

---

## Metadata

**Created**: 2026-04-25
**Last Updated**: 2026-04-25
**Status**: ✓ COMPLETE - Ready for Manual Execution
**Device**: DUT1 (8011) at 192.168.100.137
**CLI**: sonic-cli (klish mode)
**Testbed Port 1**: Ethernet272 (100G)
**Testbed Port 2**: Ethernet513 (25G)
**Test VLAN**: VLAN 10

**Key Achievement**: Corrected MAC ACL CLI syntax from `source-mac` to `host` keyword pattern, verified on device, and documented comprehensively.

---

## Navigation Quick Links

- **Start Here**: `L2-02-EXECUTION-GUIDE.md` (step-by-step execution)
- **For Context**: `L2-02-WORKING-CONFIG.md` (detailed explanations)
- **For Comparison**: `L2-01-WORKING-CONFIG.md` (understand permit first)
- **For Reference**: `acl_cli_hook.md` (183 ACL commands)
- **For Summary**: `/tmp/L2-02-COMPLETE-TEST-PACKAGE.txt` (overview)
- **For Quick Lookup**: `/tmp/L2-02-QUICK-REFERENCE.txt` (syntax card)

---

**Ready to execute? Start with `L2-02-EXECUTION-GUIDE.md`**
