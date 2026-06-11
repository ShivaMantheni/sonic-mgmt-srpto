# LACP Test Development - Critical Learnings & Context

**Last Updated**: 2026-05-26
**Status**: CLI Tests 001-008 + CLI-003 ✅ | POS Tests 009-015 ✅ | FEAT Tests 006-007 ✅

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

### 21. Traffic Counter Collection and Validation
**Pattern**: Use interface counters to validate load balancing and traffic flow
**Implementation**:
```python
# Always clear counters before traffic tests
def clear_interface_counters(dut: str) -> None:
    st.config(dut, "terminal length 0", type=cli_type, skip_error_check=True)
    st.config(dut, "clear counters interface all", type=cli_type, skip_error_check=True)
    st.wait(2, "Wait for counters to clear")

# Get counters from show interface counters all
output = intf_api.show_interface_counters_all(dut)
for entry in output:
    if entry.get("iface") == interface_name:
        tx_packets = int(str(entry.get("tx_ok", "0")).replace(",", ""))
```
**Impact**: FEAT-006 load balancing validation

### 22. Topology Link Discovery - Use vars Attributes
**Issue**: Hardcoding interfaces breaks portability across testbeds
**Fix**: Access interface names directly from vars object returned by `st.ensure_min_topology()`
```python
# After st.ensure_min_topology("D1D2:2")
# Framework provides: vars.D1D2P1, vars.D1D2P2 (D1 interfaces)
#                     vars.D2D1P1, vars.D2D1P2 (D2 interfaces)
data.d1_interfaces = [vars.D1D2P1, vars.D1D2P2]
data.d2_interfaces = [vars.D2D1P1, vars.D2D1P2]
```
**Wrong Approach**: `st.get_tg_links()` is for Traffic Generator links, not DUT-to-DUT links
**Best Practice**: Use vars attributes (D1D2P1, D1D2P2, etc.) for DUT-to-DUT connections
**Impact**: Makes tests portable across different testbed configurations
**Note**: Naming convention = `{Source}{Dest}P{Number}` (e.g., D1D2P1 = D1's first port to D2)

### 23. ICMP Traffic Generation for Connectivity Tests
**Pattern**: Use ping via CLI for basic traffic tests when TGen not available
**Implementation**:
```python
def send_icmp_traffic(source_dut: str, dest_ip: str, count: int = 100) -> int:
    cmd = f"ping {dest_ip} count {count} timeout {timeout}"
    output = st.show(source_dut, cmd, type=cli_type, skip_error_check=True)
    # Parse output for "X packets transmitted, Y received"
    return received_count
```
**Note**: VS platforms may show different traffic patterns than HW
**Impact**: FEAT-006, FEAT-007 traffic validation

### 24. Load Balance Variance Calculation
**Concept**: Verify traffic distribution across LAG members
**Calculation**:
```python
total_rx = member1_rx + member2_rx
member1_percent = (member1_rx / total_rx) * 100
variance = abs(member1_percent - 50.0)  # Deviation from ideal 50/50
```
**Threshold**: Accept 20% variance for small packet counts due to hash distribution
**Warning**: Small sample sizes may show higher variance due to flow hashing
**Impact**: FEAT-006 pass/fail criteria

### 25. Function-Level vs Module-Level Fixtures
**Pattern**: Use separate fixture scopes for setup/teardown
**Function-level fixture** (`function_hooks_with_portchannel`):
- Creates PortChannel for each test
- Configures IPs and waits for convergence
- Used with `@pytest.mark.usefixtures()` or as parameter
**Module-level fixture** (`module_hooks`):
- Loads configuration, discovers topology
- Cleanup only (to avoid state conflicts between tests)
**Best Practice**: Module fixture for discovery, function fixture for per-test setup

### 26. PortChannel Member Addition - No Interface Range Support
**Issue**: `interface range Ethernet32,36` command not supported in SONiC Klish
**Error**: `% Error: Invalid input detected at "^" marker`
**Root Cause**: LACP API tries to use interface range when list is passed
**Fix**: Add members one by one in a loop
```python
# ❌ WRONG: Passing list triggers interface range (not supported)
lacp_api.add_portchannel_member(dut, "PortChannel1", ["Ethernet32", "Ethernet36"], cli_type="klish")

# ✅ CORRECT: Add members one by one
for member in ["Ethernet32", "Ethernet36"]:
    lacp_api.add_portchannel_member(dut, "PortChannel1", member, cli_type="klish")
```
**Impact**: FEAT-006, FEAT-007 PortChannel setup
**Same for Deletion**: Also apply to `delete_portchannel_member()` - delete one at a time
**Note**: This limitation is specific to SONiC Klish CLI, may differ in other CLI types

### 27. PortChannel Graceful Shutdown
**Feature**: Graceful shutdown ensures PortChannels terminate properly during system restarts
**Purpose**: Minimizes traffic loss and maintains LACP state during reboot/reload operations
**API**: `pc_api.config_portchannel_gshut()` (alias: `config_po_graceful_shutdown()`)

**CLI Commands**:
```python
# Klish CLI - Global level
# Enable graceful shutdown globally
pc_api.config_portchannel_gshut(dut, config='add', config_level='global', cli_type='klish')
# Generated: portchannel graceful-shutdown

# Disable graceful shutdown globally
pc_api.config_portchannel_gshut(dut, config='del', config_level='global', cli_type='klish')
# Generated: no portchannel graceful-shutdown

# Click CLI - Global level
# Enable graceful shutdown
pc_api.config_portchannel_gshut(dut, config='add', config_level='global', cli_type='click')
# Generated: config portchannel graceful-shutdown enable

# Disable graceful shutdown
pc_api.config_portchannel_gshut(dut, config='del', config_level='global', cli_type='click')
# Generated: config portchannel graceful-shutdown disable
```

**Interface-Level Configuration**:
```python
# Enable graceful shutdown on specific PortChannel (overrides global)
# Note: config='del' at interface level ENABLES graceful shutdown (negates global disable)
pc_api.config_portchannel_gshut(
    dut,
    config='del',
    config_level='interface',
    exception_po_list=['PortChannel1'],
    cli_type='klish'
)
# Generated: interface PortChannel 1; graceful-shutdown; exit

# Exception list - enable globally except for specific PortChannels
pc_api.config_portchannel_gshut(
    dut,
    config='add',
    exception_po_list=['PortChannel1'],
    cli_type='klish'
)
# Generated: interface PortChannel 1; no graceful-shutdown; exit
#           portchannel graceful-shutdown
```

**Syslog Verification**:
```python
# After reboot/reload, verify graceful termination messages
# Expected syslogs (severity=NOTICE):
# 1. "teamd#teammgrd: :- sig_handler: --- Received SIGTERM. Terminating PortChannels gracefully"
# 2. "teamd#teammgrd: :- sig_handler: --- PortChannels terminated gracefully"

count_msg1 = slog_api.get_logging_count(
    dut,
    severity="NOTICE",
    filter_list=["Received SIGTERM. Terminating PortChannels gracefully"]
)
count_msg2 = slog_api.get_logging_count(
    dut,
    severity="NOTICE",
    filter_list=["PortChannels terminated gracefully"]
)
```

**Key Concepts**:
- **Global vs Interface Level**: Interface-level config overrides global setting
- **Config Mode Logic**: At interface level, `config='del'` enables graceful shutdown (negates global disable)
- **Exception List**: Exclude specific PortChannels from global graceful shutdown
- **REST API**: Uses `openconfig-interfaces-ext:graceful-shutdown-mode` (ENABLE/DISABLE)
- **Reboot Safety**: Always save config before testing graceful restart with reboot

**Use Cases**:
1. **Cold Reboot**: Enable graceful shutdown → Save config → Reboot → Verify syslogs
2. **Config Reload**: Enable graceful shutdown → Save → Reload → Verify recovery
3. **Selective Exclusion**: Enable globally with exception list for critical PortChannels

**Test Implementation**: `test_lacp_cli_003_graceful_shutdown.py`
- 10 test cases covering global, interface, and reboot scenarios
- Both Klish and Click CLI validation
- Syslog verification for graceful termination
- Exception list functionality

**Important Notes**:
- Graceful shutdown requires SONiC version with teamd support
- Reboot tests may take 3-5 minutes to complete
- Clear syslog before testing to avoid false positives
- Verify command availability with `show help` before testing

---

## 📋 Test Suite Overview

### CLI Tests (001-008 + 003)
**Purpose**: Basic PortChannel CLI operations and graceful shutdown
**Files**:
- `test_lacp_cli_001_create.py` through `test_lacp_cli_008_running_config.py`
- `test_lacp_cli_003_graceful_shutdown.py` (NEW)
**Status**: ✅ All API fixes applied (inet_pton, interface_config, graceful shutdown added)

### POS Tests (009-015)
**Purpose**: Positive functional validation with traffic, VLAN, L3, MTU

- **POS-009**: Traffic Load Balancing Hash ✅
- **POS-010**: Member Removal with Traffic ✅
- **POS-011**: LACP PDU Exchange ✅ (pagination, LACP sync wait)
- **POS-012**: Traffic Statistics ✅
- **POS-013**: VLAN on PortChannel ✅ (klish CLI, L2 switchport, TFSM parsing)
- **POS-014**: IP on VLAN SVI ✅
- **POS-015**: MTU Configuration ✅ (PortChannel MTU, API params, function names)

### FEAT Tests (006-007)
**Purpose**: Basic feature validation - load balancing and bandwidth aggregation
**Files**: `test_lacp_feat_006_007_load_balance_bandwidth.py`
**Status**: ✅ All implemented with dynamic topology discovery

- **FEAT-006**: Load Balancing Across Members ✅
  - Verifies traffic distribution across PortChannel members
  - Uses interface counters to measure per-member traffic
  - Validates load balance variance within 20% threshold
  - Key learnings: Counter collection, variance calculation, dynamic link discovery

- **FEAT-007**: Bandwidth Aggregation ✅
  - Validates cumulative bandwidth across LAG members
  - Confirms both members actively transmitting traffic
  - Measures effective utilization ratio
  - Key learnings: Sustained traffic tests, multi-member verification

**Implementation Highlights**:
- Dynamic interface discovery via vars attributes (D1D2P1, D2D1P1, etc.)
- Function-level fixture for per-test PortChannel setup
- Module-level cleanup to prevent state leakage
- ICMP-based traffic generation for VS/HW portability
- Proper counter clearing and collection patterns

**Critical Fix**:
- Initial implementation incorrectly used `st.get_tg_links()` (for TGen)
- Corrected to use vars.D1D2P1, vars.D1D2P2 (for DUT-to-DUT links)
- Naming convention: `{Source}{Dest}P{Number}` (D1D2P1 = D1's port 1 to D2)

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
