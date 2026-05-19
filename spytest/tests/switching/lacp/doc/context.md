# LACP Automation - Learnings & Context

## Overview
Implementing comprehensive LACP (Link Aggregation Control Protocol) automation with L2/L3 traffic validation using Scapy, tcpdump, and interface counters.

## CLI Learnings

### Critical CLI Issues Fixed
1. **Show running-config**: Use `show running-configuration interface PortChannel1` (NOT `show running-config | grep`)
   - SONiC isCLI does NOT support piping in direct commands
   - Must use direct `show` commands with proper parameters

2. **IP Address Format**: Use CIDR notation for SONiC isCLI
   - ✅ CORRECT: `ip address 10.1.1.1 30` (CIDR prefix length)
   - ❌ WRONG: `ip address 10.1.1.1/255.255.255.252` (netmask format)
   - Subnet mask 255.255.255.252 = /30 (point-to-point, 4 IPs)

3. **Interface Configuration**
   - Configure via `interface PortChannel1` context
   - Add members via `channel-group 1` on physical interfaces
   - Verify with `show interface PortChannel1`, `show portchannel summary`

## L3 Traffic Validation Architecture

### Strict 5-Level Mandatory Validation Chain
Tests FAIL immediately if ANY level fails (no graceful degradation):

1. **IP Configuration** - Configure 10.1.1.0/30 on both PortChannels
2. **MAC Retrieval** - Get interface MAC addresses for Scapy
3. **Traffic Generation** - Send 500 ICMP packets (5 sec @ 100 pps)
4. **tcpdump Verification** - Verify capture file contains 500+ packets
5. **Counter Verification** - Check RX_OK/TX_OK counters incremented

**Key requirement**: Each validation returns IMMEDIATELY on failure with specific error code.

## Scapy Traffic API

### MAC Address Handling
- Retrieve via `scapy_api.get_interface_mac(dut, interface_name, cli_type)`
- Fallback to `scapy_api.get_default_mac(dut_id)` if retrieval fails
- MAC addresses are REQUIRED parameters for `send_traffic()`

### send_traffic() Parameters
```python
result = scapy_api.send_traffic(
    dut=vars.D1,
    interface=pc_interface,
    src_ip=pc_ip_d1,
    dst_ip=pc_ip_d2,
    src_mac=dut1_mac,        # REQUIRED
    dst_mac=dut2_mac,        # REQUIRED
    duration=5,              # seconds
    pps=100,                 # packets per second
    traffic_type="icmp"      # ICMP ping
)
```

## tcpdump Packet Count Parsing Fix

**Critical Bug Fixed**: Extracting FIRST digit instead of LAST
- tcpdump output contains "snapshot length 262144" THEN actual packet count
- ✅ CORRECT: `all_numbers = re.findall(r'\d+'); count = int(all_numbers[-1])`
- ❌ WRONG: `count_match = re.search(r'(\d+)'); count = int(count_match.group(1))`

## Test Case Organization

### LACP CLI 001 - Active Mode (8 tests)
- TC-001: PortChannel creation
- TC-002: Member addition (Ethernet32/36/40/44)
- TC-003: Show interface verification
- TC-004: Show running-configuration
- TC-005: LACP status verification
- TC-006: L2 traffic validation (500 packets, tcpdump, counters)
- TC-007: L3 traffic validation (IP config → traffic → tcpdump → counters)
- TC-008: Cleanup

### LACP CLI 002 - Passive Mode (8 tests)
- Parallel to CLI 001 but from passive side
- Traffic direction: D2 → D1 (reverse of CLI 001)

## Testbed Configuration

**testbed_lacp_vs.yaml**
- D1: 192.168.100.39 (Active initiator)
- D2: 192.168.100.40 (Passive responder)
- Topology: 4 back-to-back links (Ethernet32/36/40/44)
- CLI Type: Klish (isCLI)

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid input at ^" | Piping in CLI | Use direct show commands |
| "IP config failed" | Netmask format | Use CIDR notation (/30) |
| "tcpdump FAIL 1 packets" | Parsing first digit | Extract last number |
| "send_traffic missing MAC" | No src_mac/dst_mac | Retrieve and pass MACs |

## Files & Status

✅ test_lacp_cli_001_active_portchannel.py - Complete, verified
✅ test_lacp_cli_002_passive_portchannel.py - Complete, verified
✅ testbeds/testbed_lacp_vs.yaml - Complete
✅ apis/common/scapy_traffic.py - Tcpdump parsing fixed

## Execution Results - CLI 001 & CLI 002 (✅ PASSED)

### Test Status
- ✅ **test_lacp_cli_001_active_portchannel.py** - ALL 8 TEST CASES PASSED
- ✅ **test_lacp_cli_002_passive_portchannel.py** - ALL 8 TEST CASES PASSED

### Critical Fixes Applied During Execution

#### Fix 1: tcpdump Capture Interface Selection
**Problem**:
- Scapy sent 500 packets ✅
- Interface RX_OK showed 502 packets received ✅
- tcpdump captured only 4 packets ❌
- **Root Cause**: L3 ICMP traffic flows through physical member interfaces (Ethernet32/36/40/44), not logical PortChannel1. tcpdump on PortChannel1 only captured protocol overhead (4 packets).

**Solution Applied**:
```python
# BEFORE (WRONG):
scapy_api.start_tcpdump(vars.D2, pc_interface, output_file=pcap_file)  # PortChannel1

# AFTER (CORRECT):
capture_interface = data.members[0] if data.members else pc_interface  # Ethernet32
scapy_api.start_tcpdump(vars.D2, capture_interface, output_file=pcap_file)
```

**Files Modified**:
- test_lacp_cli_001_active_portchannel.py (Lines 443-450)
- test_lacp_cli_002_passive_portchannel.py (Lines 496-503)

**Result**: tcpdump now captures 450-500 packets on member interface (Ethernet32) correctly

---

#### Fix 2: TextFSM Parsing - Interface Counters
**Problem**:
- `show interface counters | no-more` returned empty list `[]` from TextFSM
- Cannot extract RX_OK/TX_OK values for counter validation
- Error: "Could not retrieve interface counters"

**Solution Applied**:
```python
# BEFORE (WRONG - Uses TextFSM template parsing):
output = st.show(vars.D2, cmd, type=data.cli_type)

# AFTER (CORRECT - Gets raw output for manual parsing):
output = st.show(vars.D2, cmd, type=data.cli_type, skip_tmpl=True)
```

**Key Insight**: Counter validation doesn't need TextFSM parsing. Raw output string can be manually parsed to extract RX_OK/TX_OK values more reliably.

**Files Modified**:
- test_lacp_cli_001_active_portchannel.py (Lines 497-549)
- test_lacp_cli_002_passive_portchannel.py (Lines 547-598)

**Result**: Counter validation now works correctly, extracting RX_OK=502 packets

---

#### Fix 3: Invalid Framework Error Codes
**Problem**: Tests used undefined error codes:
- `l3_counter_verification_failed` (undefined)
- `l3_traffic_validation_error` (undefined)
- Framework validation failed with "Invalid error code"

**Solution Applied**:
```python
# BEFORE (WRONG):
st.report_fail("l3_counter_verification_failed")
st.report_fail("l3_traffic_validation_error")

# AFTER (CORRECT - Using valid framework codes):
st.report_fail("counter_verification_failed")
st.report_fail("test_failure", str(e))
```

**Files Modified**:
- test_lacp_cli_001_active_portchannel.py (Lines 503, 550, 555)
- test_lacp_cli_002_passive_portchannel.py (Lines 553, 598, 608)

**Result**: Error codes now validate successfully through framework

---

#### Fix 4: Enhanced Cleanup with Removal Verification
**Problem**: Cleanup testcase (TC-008) simply logged "removing members" without actual verification. Config success didn't guarantee removal worked.

**Solution Applied**:
4-Step Cleanup Process:
1. **Remove members**: Execute `no channel-group` on each physical interface
2. **Remove PortChannel**: Execute `no interface PortChannel1`
3. **Verify removal in config**: `show running-configuration interface PortChannel1` should fail or be empty
4. **Verify removal in summary**: `show portchannel summary` should not list the removed members

```python
# Step 1: Remove members using "no channel-group"
for member in data.members:
    cmd = "no channel-group"
    output = st.config(vars.D1, "interface " + member, type=cli_type)
    output = st.config(vars.D1, cmd, type=cli_type)

# Step 2: Remove PortChannel interface
cmd = f"no interface PortChannel{data.portchannel_id}"
output = st.config(vars.D1, cmd, type=cli_type)

# Step 3: Verify removal in running-configuration
cmd = f"show running-configuration interface PortChannel{data.portchannel_id}"
output = st.show(vars.D1, cmd, type=cli_type, skip_tmpl=True)
if "PortChannel" in output or len(output) > 5:
    st.report_fail("portchannel_removal_failed")

# Step 4: Verify removal in portchannel summary
cmd = "show portchannel summary"
output = st.show(vars.D1, cmd, type=cli_type)
if data.portchannel_id in output:
    st.report_fail("portchannel_members_still_listed")
```

**Files Modified**:
- test_lacp_cli_001_active_portchannel.py (Lines 559-634, Enhanced from simple cleanup)
- test_lacp_cli_002_passive_portchannel.py (Lines 612-692, Same enhancement)

**Result**: Cleanup now properly validates removal and fails if removal incomplete

---

## Key Learnings from Successful Execution

1. **L3 Traffic Data Path**: L3 ICMP packets flow through physical member interfaces, not logical PortChannel. Validate via:
   - tcpdump on member interface (e.g., Ethernet32)
   - Interface counters on member interfaces (RX_OK/TX_OK)
   - NOT tcpdump on logical PortChannel (gives ~4 packets of overhead)

2. **Interface Counter Parsing**: Use `skip_tmpl=True` when direct output parsing is needed, avoid TextFSM templates for counter extraction

3. **Framework Error Codes**: Always use valid framework codes from spytest error registry. Invalid codes cause test failure.

4. **Cleanup Verification**: Cleanup must verify removal, not just execute commands. Use show commands to confirm deletion.

5. **Member Interface Selection**: For multi-member PortChannels, verify which member interface carries the traffic (usually first member due to LACP hash)

---

## Preserved Instructions for Incremental LACP Testcase Automation

⚠️ **IMPORTANT**: These instructions define the automation process for all remaining LACP testcases. Do NOT deviate from this process.

### Automation Engineer Role
Act as a spytest automation engineer and follow this EXACT process:

1. **Take ONE testcase at a time** from testplan_lacp.md
2. **Use proper cleanup** after every testcase
3. **Follow guidelines**:
   - Use spy_test_coding_guideline.md for code structure
   - Use SCAPY_TRAFFIC_API_GUIDE.md for traffic generation
   - Use "show interface counters" and "clear interface counters" to validate traffic
   - Use tcpdump to validate exact traffic captured

4. **Validate with Show Commands** (after every testcase):
   ```bash
   show interface PortChannel 1
   show running-config interface PortChannel
   show portchannel summary
   ```

5. **Test All Scenarios**:
   - ✅ L2 traffic cases (Ethernet frame forwarding)
   - ✅ L3 traffic cases (IP/ICMP with IP configuration)
   - ✅ All CLI combinations (show, config, verify)
   - ✅ Interface types: Ethernet, VLAN, PortChannel

6. **Incremental Process** (MANDATORY):
   - Implement ONE testcase at a time
   - DO NOT automate all testcases at once
   - After each testcase implementation:
     - Provide complete testcase code to user
     - **STOP and inform user**: "Testcase [ID] is ready for testing"
     - **WAIT for user feedback**: User tests the case
     - **ONLY proceed to next testcase** after user confirms: "tested and passed"

7. **Cleanup Requirements**:
   - Clear interface counters before test
   - Validate traffic via counters and tcpdump
   - Clean up all configuration after test
   - Verify removal via show commands

### Success Criteria
- All show commands execute without errors
- Interface counters increment correctly (RX_OK/TX_OK > 0)
- tcpdump captures expected packet counts (accounting for loss)
- Cleanup removes all configuration traces

### Next Automation Checkpoint
**Waiting for user confirmation to proceed with FIRST testcase from testplan_lacp.md**
- Ready to implement: LACP_CLI_001 or next available from testplan
- Process: Implement → Test → Get Feedback → Next

---

## CRITICAL API FIXES - 2026-05-19

### Fix 5: inet_pton() Type Error - PortChannel ID Normalization

**Problem**:
- Tests passed integer PortChannel IDs (`PC_ID = 1`) to portchannel APIs
- API chain: `delete_portchannel(1)` → `get_interface_number_from_name(1)` → `is_valid_ipv4_address(1)` → `socket.inet_pton(AF_INET, 1)`
- Error: `inet_pton() argument 2 must be str, not int`
- Root cause: IP validation function expected string, received integer

**Solution - New LACP API Wrapper**:
Created `apis/switching/lacp.py` with automatic type normalization:
```python
def normalize_portchannel_name(portchannel):
    """Convert int/str to 'PortChannelN' format"""
    if isinstance(portchannel, int):
        return f"PortChannel{portchannel}"
    if isinstance(portchannel, str) and portchannel.isdigit():
        return f"PortChannel{portchannel}"
    return portchannel  # Already normalized

# Wrapper functions
def delete_lacp_portchannel(dut, portchannel_list, **kwargs):
    normalized = normalize_portchannel_name(portchannel_list)
    return pc_api.delete_portchannel(dut, normalized, **kwargs)
```

**Benefits**:
- ✅ Accepts: `1`, `"1"`, or `"PortChannel1"` - all work correctly
- ✅ Prevents type errors before calling underlying APIs
- ✅ All 7 LACP test files now use `lacp_api` instead of `pc_api`
- ✅ Future-proof: New tests can use flexible input formats

**Files Created**:
- `apis/switching/lacp.py` (492 lines) - Full wrapper with 15+ functions

**Files Modified** (Import change: `pc_api` → `lacp_api`):
- test_lacp_cli_001_active_portchannel.py
- test_lacp_cli_002_passive_portchannel.py
- test_lacp_cli_004_add_members.py
- test_lacp_cli_005_remove_members.py
- test_lacp_cli_006_mtu_configuration.py
- test_lacp_cli_007_shutdown_enable.py
- test_lacp_cli_008_running_config.py

**Usage Examples**:
```python
import apis.switching.lacp as lacp_api

# All these work now:
lacp_api.create_lacp_portchannel(dut, 1)                    # int
lacp_api.create_lacp_portchannel(dut, "1")                  # str
lacp_api.create_lacp_portchannel(dut, "PortChannel1")       # full name
lacp_api.delete_lacp_portchannel(dut, 1)                    # ✅ Fixed!
lacp_api.add_lacp_member(dut, 1, ["Ethernet32"])
lacp_api.verify_lacp_portchannel_state(dut, 1, state="up")
```

---

### Fix 6: interface_config() - Non-existent API Function

**Problem**:
- Tests called `intf_api.interface_config(dut, interface_name=..., description=..., mtu=...)`
- Error: `module 'apis.system.interface' has no attribute 'interface_config'`
- Function does not exist in `apis/system/interface.py`

**Solution - Use Correct API**:
Use `interface_properties_set(dut, interface, property, value, cli_type=...)`:
```python
# BEFORE (WRONG):
intf_api.interface_config(
    dut1, interface_name=f"PortChannel{PC_ID}",
    description=PC_DESCRIPTION,
    mtu=PC_MTU,
    cli_type=cli_type
)

# AFTER (CORRECT):
intf_api.interface_properties_set(
    dut1, f"PortChannel{PC_ID}",
    "description", PC_DESCRIPTION,
    cli_type=cli_type
)
intf_api.interface_properties_set(
    dut1, f"PortChannel{PC_ID}",
    "mtu", PC_MTU,
    cli_type=cli_type
)
```

**Key Differences**:
- ✅ `interface_properties_set()` sets ONE property at a time
- ✅ Parameters: `(dut, interface, property, value, cli_type=...)`
- ✅ Supported properties: `"description"`, `"mtu"`, `"speed"`, `"fec"`, `"autoneg"`
- ❌ Cannot set multiple properties in one call (split into multiple calls)

**Files Modified**:
- test_lacp_cli_006_mtu_configuration.py (4 occurrences fixed)
- test_lacp_cli_008_running_config.py (3 occurrences fixed)

**Locations Fixed**:
- CLI 006: Lines 446-455, 530-539, 594-603, 615-624
- CLI 008: Lines 310-332, 442-461

---

### Validation Results

**Syntax Validation**: ✅ ALL TESTS PASS
```bash
✓ test_lacp_cli_001_active_portchannel.py
✓ test_lacp_cli_002_passive_portchannel.py
✓ test_lacp_cli_004_add_members.py
✓ test_lacp_cli_005_remove_members.py
✓ test_lacp_cli_006_mtu_configuration.py
✓ test_lacp_cli_007_shutdown_enable.py
✓ test_lacp_cli_008_running_config.py
```

**Normalization Test**: ✅ 9/9 PASSED
- Integer input (1, 100) → "PortChannel1", "PortChannel100"
- String input ("1", "100") → "PortChannel1", "PortChannel100"
- Full name ("PortChannel1") → "PortChannel1" (preserved)
- List input ([1, 2, 3]) → ["PortChannel1", "PortChannel2", "PortChannel3"]

---

### Key Learnings for Future Development

1. **Type Safety**: Always normalize inputs before passing to underlying APIs
   - Create wrapper layers when dealing with flexible input formats
   - Prevent type errors at the wrapper level, not deep in the call stack

2. **API Discovery**: Check actual function signatures before use
   - `interface_config()` doesn't exist → use `interface_properties_set()`
   - Read API module first: `grep "^def " apis/system/interface.py | head -40`

3. **Wrapper Benefits**:
   - Cleaner test code: `lacp_api.delete_lacp_portchannel(dut, 1)`
   - Type safety: Works with int, str, or full names
   - Future-proof: Easier to maintain and extend

4. **Property Setting**:
   - One property per call with `interface_properties_set()`
   - Supported: description, mtu, speed, fec, autoneg, diag-mode
   - Always pass property name as string: `"mtu"`, not `mtu`

---

**Last Updated**: 2026-05-19
**Execution Status**: CLI 001-002 ✅ PASSED | CLI 004-008 ✅ API FIXED
**Critical Fixes**: inet_pton() resolved, interface_config() resolved
**Next Action**: Run tests to validate fixes in live environment
