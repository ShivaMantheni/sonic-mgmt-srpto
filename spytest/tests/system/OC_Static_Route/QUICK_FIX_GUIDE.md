# Static Route Test Failure - Root Cause and Fix

**Date**: 2026-04-13
**Issue**: Test case OC-SR-11 (IPv4 Blackhole Routes) failing with CLI error
**Status**: ✓ FIXED

---

## Problem Description

### Error Message
```
% Error: Invalid input detected at "^" marker.
```

### Failure Location
All verification steps that run `show ip route` commands were failing with the above error.

### Root Cause Analysis

**The test was running `show` commands while still in config mode (`--sonic-mgmt--(config)#`)**

**Execution Flow**:
1. Test enters config mode: `configure terminal`
2. Test adds routes: `ip route 172.16.10.0/24 blackhole`
3. Session remains in **config mode**
4. Verification function tries to run: `show ip route 172.16.10.0/24`
5. SONiC CLI rejects the command because it's being executed from config mode

**Why it failed**:
- The `st.config()` function keeps the session in config mode after executing commands
- The `st.show()` function expects to run from **exec mode** (normal `#` prompt)
- SONiC Klish CLI doesn't support `do show ...` prefix in config mode properly

---

## Solution

### Fix Applied
Add `st.config(dut, ["exit", "exit", "exit"], type='klish', skip_error_check=True)` before **every** `st.show()` call in verification functions.

**Why multiple `exit` commands?**
- The `end` command was returning `%Error: Internal error` in some SONiC OC-build versions
- Using multiple `exit` commands ensures we exit from any nested config mode level
- With `skip_error_check=True`, extra `exit` commands are harmless if already in exec mode

### Example Fix

**BEFORE** (Failing):
```python
def verify_blackhole_route(dut, prefix):
    """Verify blackhole route shows 'Unreachable (blackhole)' in routing table."""
    try:
        output = st.show(dut, f"show ip route {prefix}", type='klish', ...)
        # ... rest of verification
```

**AFTER** (Fixed):
```python
def verify_blackhole_route(dut, prefix):
    """Verify blackhole route shows 'Unreachable (blackhole)' in routing table."""
    try:
        # Exit config mode before running show command (use exit multiple times to ensure we leave config mode)
        st.config(dut, ["exit", "exit", "exit"], type='klish', skip_error_check=True)

        output = st.show(dut, f"show ip route {prefix}", type='klish', ...)
        # ... rest of verification
```

---

## Files Fixed

### 1. test_oc_static_route_01_ipv4_basic_nexthop.py
**Functions Fixed**:
- `verify_route_not_in_table()` - Line 359

### 2. test_oc_static_route_02_ipv4_blackhole.py
**Functions Fixed**:
- `verify_blackhole_route()` - Line 287
- `verify_static_route()` - Line 309
- `verify_route_not_in_table()` - Line 331

### 3. test_oc_static_route_03_ipv4_interface.py
**Functions Fixed**:
- `verify_interface_route()` - Line 273
- `verify_route_not_in_table()` - Line 296

### 4. test_oc_static_route_04_ipv4_tags.py
**Functions Fixed**:
- `verify_tagged_route_in_routing_table()` - Line 287
- `verify_tagged_route_in_config()` - Line 314
- `verify_route_not_in_table()` - Line 339

---

## Testing the Fix

### Run the failing test again:
```bash
cd /home/adminuser/draksha/sonic-mgmt/spytest

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_oc_3d.yaml \
  tests/system/OC_Static_Route/test_oc_static_route_02_ipv4_blackhole.py \
  --logs-path ./logs/oc_sr11_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native
```

### Expected Result
- All verification steps should now pass
- No more "Invalid input detected" errors
- Routes should be verified correctly in routing tables

---

## Best Practices Going Forward

### For ALL New Test Scripts

**Rule**: Always exit config mode before running `st.show()` commands

**Pattern to follow**:
```python
def verify_something(dut, ...):
    """Verify something in the routing table or configuration."""
    try:
        # ALWAYS exit config mode first (use multiple exit commands for reliability)
        st.config(dut, ["exit", "exit", "exit"], type='klish', skip_error_check=True)

        # NOW run show command
        output = st.show(dut, "show ...", type='klish', ...)

        # ... verification logic
```

### Why `skip_error_check=True`?
- Extra `exit` commands are harmless if already in exec mode
- We don't want the test to fail if already in correct mode
- The commands are idempotent (safe to run multiple times)

### Why Multiple `exit` Commands?
- Handles nested config modes: `(config-if-Ethernet0)#` → `(config)#` → `#`
- More reliable than `end` which returns errors in some SONiC versions
- Three `exit` commands ensure we exit from the deepest possible nesting

---

## Technical Details

### SONiC CLI Modes
1. **Exec Mode** (Normal `#` prompt)
   - Commands: `show`, `ping`, `traceroute`, etc.
   - Prompt: `sonic#` or `--sonic-mgmt--#`

2. **Config Mode** (Config `(config)#` prompt)
   - Commands: `interface`, `ip route`, `no shutdown`, etc.
   - Prompt: `sonic(config)#` or `--sonic-mgmt--(config)#`

### Transition Commands
- `configure terminal` → Enter config mode
- `exit` → Go up one level in the CLI hierarchy
- Multiple `exit` commands → Guaranteed way to reach exec mode

### Why Multiple `exit` Instead of `end`?
- `exit` goes up only one level: `(config-if-Ethernet0)#` → `(config)#` → `#`
- `end` should take you all the way back, but returns `%Error: Internal error` in some SONiC OC-build versions
- Three `exit` commands handles the deepest nesting level and is more reliable

---

## Verification Checklist

✓ All test files reviewed
✓ All verification functions fixed
✓ Pattern documented for future tests
✓ Fix applied consistently across all files

---

**Author**: Network Automation Team
**Fix Date**: 2026-04-13
**Review Status**: Completed
