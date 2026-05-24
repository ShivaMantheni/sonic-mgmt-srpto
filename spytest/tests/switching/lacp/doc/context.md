# LACP Test Development - Critical Learnings & Context

**Last Updated**: 2026-05-22
**Status**: CLI Tests 001-008 ✅ | POS Tests 009-015 ✅

---

## 🎯 Critical Learnings (Test Development & Debugging)

### 1. Network Byte Order and IP Address Validation
**Issue**: `inet_pton() argument 2 must be str, not None` errors
**Root Cause**: Missing IP addresses passed to `inet.pton()` validation
**Fix**: Always validate IP addresses exist before socket operations
**Prevention**: Use `ip_addr/prefix` format or validate before conversion

### 2. API Function Signature Mismatches
**Issue**: Missing required parameters (family, cli_type) causing API errors
**Root Cause**: Incorrect function signatures - omitted required parameters
**Fix**: Always check API function signature in `apis/routing/ip.py`
**Example**: `config_ip_addr_interface(dut, intf, ip, subnet, family="ipv4", cli_type="")`

### 3. Template-Based Output Parsing (TextFSM)
**Issue**: Empty results from `st.show()` when using TextFSM templates
**Root Cause**: Wrong template path or missing `skip_tmpl=True` for raw parsing
**Fix**: Use `skip_tmpl=True` for custom parsing, verify template exists for structured parsing
**Templates**: Located in `templates/` with mapping in `templates/index`

### 4. Pagination Prevention - Critical for CLI Commands
**Issue**: `--more--` prompts cause test hangs and timeout/recovery
**Root Cause**: Long output triggers pagination, waits for user input
**Fix**: **Always** disable pagination before show commands:
```python
st.config(dut, "terminal length 0", type=cli_type, skip_error_check=True)
cmd = "show lacp portchannel | no-more"  # Double protection
```
**Impact**: All POS-009, POS-010, POS-011, POS-012 tests fixed

### 5. CLI Type Consistency - Klish vs Click
**Issue**: Click commands used when testing requires klish CLI
**Root Cause**: `st.get_ui_type(dut)` reads testbed default (often click)
**Fix**: **Force klish for testing**:
```python
data.cli_type = "klish"  # Don't rely on testbed default
```
**Impact**: POS-013 VLAN test fixed

### 6. L2 vs L3 Interface Modes (SONiC Behavior)
**Issue**: `Error: PortChannel1 is a router interface!` when adding to VLAN
**Root Cause**: PortChannels default to L3 (router) mode - cannot be VLAN members
**Fix**: Configure as switchport (L2) before VLAN membership:
```python
commands = [f"interface {PC_NAME}", "switchport", "exit"]
st.config(dut, commands, type="klish")
```
**Key Concept**: Only L2 (switchport) interfaces can be VLAN members

### 7. TFSM Field Names and API Wrapper Simplification
**Issue**: Empty VLAN list despite valid data in device output
**Root Cause**: API wrappers may simplify TFSM output (dicts → strings)
**Fix**: Handle multiple data types:
```python
for entry in vlan_list:
    if isinstance(entry, dict):
        vid = entry.get("vid") or entry.get("vlanid") or entry.get("vlan")
        vlan_ids.append(str(vid))
    elif isinstance(entry, str):
        vlan_ids.append(entry)  # Already simplified by API
```
**Always**: Add debug logging to inspect actual data structure

### 8. SONiC MTU Configuration Constraints
**Issue**: `Error: 'interface_name' is in portchannel!` when setting MTU on members
**Root Cause**: SONiC doesn't allow MTU config on member interfaces while in PortChannel
**Fix**: Set MTU on PortChannel itself (propagates to members automatically):
```python
# ❌ Wrong: Set on members
intf_api.interface_properties_set(dut, member, property="mtu", value=1500)

# ✅ Correct: Set on PortChannel
intf_api.interface_properties_set(dut, PC_NAME, property="mtu", value=1500)
```
**Impact**: POS-015 MTU test fixed

### 9. API Parameter Support - skip_error_check
**Issue**: `TypeError: interface_properties_set() got unexpected keyword 'skip_error_check'`
**Root Cause**: Not all APIs support `skip_error_check` parameter
**Fix**: Wrap in try-except for cleanup code:
```python
try:
    intf_api.interface_properties_set(dut, member, property="mtu", value=9100)
except Exception as e:
    st.log(f"Cleanup: Failed to restore MTU: {e}")
```

### 10. API Function Naming Conventions
**Issue**: `AttributeError: no attribute 'show_interface_status'`
**Root Cause**: Inconsistent naming - some APIs use verb_noun, others noun_verb
**Fix**: Verify function name in API module:
```python
# ❌ Wrong: show_interface_status()
# ✅ Correct: interface_status_show()
output = intf_api.interface_status_show(dut, interfaces=[intf])
```

### 11. Module/Function Imports - Always Use Absolute Imports
**Issue**: `NameError: name 'intf_api' is not defined`
**Fix**: Import required API modules at top of test file:
```python
import apis.system.interface as intf_api
import apis.routing.ip as ip_api
import apis.switching.lacp as lacp_api
import apis.switching.vlan as vlan_api
```

### 12. Traffic Counter Parsing - Exact String Matching
**Issue**: TX counter showing 0 despite packets sent
**Root Cause**: Parsing wrong interface name ("PortChannel1_0" vs "PortChannel1")
**Fix**: Exact string matching with interface name validation
**Always**: Log counter values for debugging

### 13. LACP Load Balancing Hash Validation
**Issue**: Hash mode not matching configured value
**Root Cause**: Dictionary key mismatch ("load_balancing_mode" vs "load_balance_mode")
**Fix**: Check actual dict keys returned by API (use debug logging)

### 14. MAC Address Parsing - Handle Dash vs Colon Formats
**Issue**: MAC lookup failing due to format mismatch
**Root Cause**: SONiC returns MAC as "aa:bb:cc:dd:ee:ff", scapy uses "aa-bb-cc-dd-ee-ff"
**Fix**: Normalize MAC format before comparison:
```python
mac_normalized = mac.replace("-", ":").lower()
```

### 15. Error Reporting - Valid Message Identifiers
**Issue**: `Invalid error code vlan_not_exist : unknown message identifier`
**Fix**: Use `"msg"` for custom error messages:
```python
st.report_fail("msg", f"VLAN {VLAN_ID} not found on {dut}")
```

### 16. st.log() is for Output, Not Execution
**Issue**: `TypeError: 'NoneType' object is not iterable` - st.log() returns None
**Fix**: Never use st.log() return value:
```python
# ❌ Wrong:
for entry in st.log(f"Members: {members}"):

# ✅ Correct:
st.log(f"Members: {members}")
for entry in members:
```

### 17. Debug Logging - Always Log Actual Data Structure
**Best Practice**: Add debug logging to see what APIs actually return:
```python
st.log(f"DEBUG: Raw API output type: {type(output)}")
st.log(f"DEBUG: Raw API output content: {output}")
```
**Impact**: Revealed VLAN API returning strings (not dicts), MTU propagation behavior

### 18. Configuration Cleanup - Use skip_error_check
**Pattern**: Module fixtures should cleanup gracefully without failing:
```python
# Cleanup existing config
lacp_api.delete_portchannel_member(
    dut, PC_NAME, [member], cli_type=cli_type, skip_error_check=True
)
lacp_api.delete_portchannel(dut, PC_NAME, cli_type=cli_type, skip_error_check=True)
```

### 19. Wait Times - Critical for LACP Convergence
**Guideline**:
- After PortChannel creation: `st.wait(2)`
- After member addition: `st.wait(5, "Wait for LACP sync")`
- After MTU change: `st.wait(5, "Wait for MTU change to propagate")`
- Before traffic test: `st.wait(3, "Wait before traffic test")`

### 20. Test Documentation - Essential Components
**Always Include**:
- Clear test ID and priority
- How to run command with exact testbed
- Description of what test validates
- Pre-requisites (topology, configuration)
- SONiC-specific behaviors and constraints

---

## 📋 Test Suite Overview

### CLI Tests (001-008)
**Purpose**: Basic PortChannel CLI operations
**Files**: `test_lacp_cli_001_create.py` through `test_lacp_cli_008_running_config.py`
**Status**: ✅ All API fixes applied (inet_pton, interface_config)

### POS Tests (009-015)
**Purpose**: Positive functional validation with traffic, VLAN, L3, MTU

- **POS-009**: Traffic Load Balancing Hash ✅
- **POS-010**: Member Removal with Traffic ✅
- **POS-011**: LACP PDU Exchange ✅ (pagination, LACP sync wait)
- **POS-012**: Traffic Statistics ✅
- **POS-013**: VLAN on PortChannel ✅ (klish CLI, L2 switchport, TFSM parsing)
- **POS-014**: IP on VLAN SVI ✅
- **POS-015**: MTU Configuration ✅ (PortChannel MTU, API params, function names)

---

## 🚀 Execution Checklist

**Before Running Tests**:
1. ✅ Verify testbed connectivity
2. ✅ Check DUT reachability via SSH
3. ✅ Ensure clean baseline (no existing PortChannel config)
4. ✅ Validate interface names match testbed YAML

**Common Failures to Watch**:
- Pagination hangs (ensure `terminal length 0` + `| no-more`)
- IP address validation errors (check inet_pton calls)
- LACP sync timeout (increase wait times if needed)
- API signature mismatches (verify required parameters)
- L2/L3 mode conflicts (use switchport for VLANs)

**Next Steps**: Execute full test suite and validate all tests pass
