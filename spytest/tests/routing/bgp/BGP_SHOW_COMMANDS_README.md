# BGP Show Commands Test Suite

**Author**: Athira
**Date**: June 7, 2026
**Framework**: SpyTest (SONiC Test Automation)

---

## Overview

Comprehensive SpyTest framework test suite for validating all 91 BGP show command test cases. Follows SpyTest coding guidelines with proper structure, YAML-based configuration, and support for both hardware and virtual environments.

### Test Coverage

| Category | Test Cases | Description |
|----------|-----------|-------------|
| BGP Summary | TC-001 to TC-010 | Global/IPv4/IPv6 summary, VRF, JSON formats |
| BGP Neighbors | TC-011 to TC-025 | Neighbor details, routes, capabilities, timers |
| BGP Routes | TC-026 to TC-040 | Route display, filtering, communities, AS-path |
| BGP Configuration | TC-041 to TC-050 | Running config, peer-groups, route-maps |
| BGP Statistics | TC-051 to TC-060 | Counters, memory, performance metrics |
| VRF Support | TC-061 to TC-070 | VRF-specific BGP commands |
| Advanced Filtering | TC-071 to TC-080 | Complex filters, regex, prefix-lists |
| Negative Tests | TC-081 to TC-091 | Invalid inputs, error handling |

**Total**: 91 comprehensive test cases

---

## File Structure

```
sonic-mgmt/spytest/
├── tests/routing/bgp/
│   ├── test_bgp_show_commands.py              # Main test script
│   ├── BGP_SHOW_COMMANDS_README.md            # This file
│   └── doc/
│       └── TC_BGP_SHOW_COMMANDS_COMPREHENSIVE.md  # Full test plan
├── vars/bgp/
│   └── vars_bgp_show_commands.yaml            # Test configuration
└── testbeds/
    └── testbed_vs_2d.yaml                     # Topology definition
```

---

## Prerequisites

### 1. Topology Requirements

- **Minimum**: 2-node topology (D1-D2) with 1 link
- **BGP Session**: Must be pre-established between D1 and D2
- **Supported**: Both HW and Virtual environments

**Topology Diagram**:
```
+----------------------+                       +----------------------+
|   DUT1 (AS 65001)    |                       |   DUT2 (AS 65002)    |
| Eth32 10.0.24.1/24   |=======================| Eth32 10.0.24.2/24   |
| BGP neighbor config  |<-- BGP Session -->    | Routes advertised    |
+----------------------+                       +----------------------+
```

### 2. BGP Configuration

**D1 Configuration**:
```bash
router bgp 65001
  neighbor 10.0.24.2 remote-as 65002
  address-family ipv4 unicast
    neighbor 10.0.24.2 activate
```

**D2 Configuration**:
```bash
router bgp 65002
  neighbor 10.0.24.1 remote-as 65001
  address-family ipv4 unicast
    neighbor 10.0.24.1 activate
    network 10.10.10.0/24  # Example advertised route
```

### 3. Software Requirements

- **SONiC Version**: Any version with FRR BGP support
- **Python**: 3.8+
- **SpyTest Framework**: Latest version
- **Required APIs**: `apis.routing.bgp`, `apis.routing.ip`

---

## Configuration

### YAML Variables (`vars/bgp/vars_bgp_show_commands.yaml`)

**Default Configuration**:
```yaml
defaults:
  cli_type: klish                # CLI type: klish, vtysh, click
  verify_timeout: 30             # Timeout for verifications
  cleanup: true                  # Enable cleanup after tests
  min_topology:
    - "D1D2:1"                   # Minimum topology requirement

  # BGP Configuration
  local_asn: 65001               # D1 AS number
  remote_asn: 65002              # D2 AS number
  d1_bgp_neighbor: "10.0.24.2"   # D1's BGP neighbor (D2's IP)
  d2_bgp_neighbor: "10.0.24.1"   # D2's BGP neighbor (D1's IP)
  d1_ipv6: "2001:db8::1"         # D1 IPv6 address (optional)
  d2_ipv6: "2001:db8::2"         # D2 IPv6 address (optional)
```

**Customization**:

Override using environment variable:
```bash
export BGP_SHOW_VAR_FILE=/path/to/custom_vars.yaml
```

Or modify the default file:
```bash
vi vars/bgp/vars_bgp_show_commands.yaml
```

---

## How to Run

### 1. Run All Test Cases (Recommended)

```bash
cd /home/sonic-claude/athira/sonic-mgmt/spytest

./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2d.yaml \
  routing/bgp/test_bgp_show_commands.py \
  --logs-path ./logs/test_bgp_show_$(date +%F_%H%M%S) \
  --log-level debug \
  --skip-init-config \
  --ifname-type native \
  --get-tech-support none \
  --syslog-check none
```

### 2. Run Specific Test Case

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2d.yaml \
  routing/bgp/test_bgp_show_commands.py::TestBgpShowCommands::test_bgp_show_tc001_global_summary \
  --logs-path ./logs/test_bgp_show_tc001_$(date +%F_%H%M%S) \
  --log-level debug \
  --ifname-type native
```

### 3. Run by Category (Using Markers)

**Run only negative tests**:
```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2d.yaml \
  routing/bgp/test_bgp_show_commands.py \
  -m negative \
  --logs-path ./logs/test_bgp_show_negative_$(date +%F_%H%M%S)
```

**Run regression tests**:
```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2d.yaml \
  routing/bgp/test_bgp_show_commands.py \
  -m "Regression" \
  --logs-path ./logs/test_bgp_show_regression_$(date +%F_%H%M%S)
```

### 4. Run with Custom Testbed

```bash
./bin/spytest --tryssh 1 \
  --testbed ./testbeds/my_custom_testbed.yaml \
  routing/bgp/test_bgp_show_commands.py \
  --logs-path ./logs/test_bgp_show_custom_$(date +%F_%H%M%S)
```

---

## Test Structure

### Class Hierarchy

```python
TestBgpShowCommands
├── setup_class()              # Initialize topology, verify BGP session
├── teardown_class()           # Cleanup (minimal for show commands)
├── setup_method()             # Per-test setup
├── teardown_method()          # Per-test teardown
└── test_bgp_show_tcXXX_*()    # Individual test cases
```

### Test Method Pattern

Each test follows this pattern:

```python
def test_bgp_show_tcXXX_description(self) -> None:
    """TC-XXX: Test description."""
    # 1. Get test configuration from YAML
    testcase = self._get_testcase("TC-XXX")

    # 2. Execute show command
    command = testcase.get("command", "show bgp summary")
    output = self._execute_show_command(self.data.D1, command)

    # 3. Validate output
    if not self._validate_output_contains(output, expected_fields):
        st.report_fail("msg", "Validation failed")

    # 4. Report result
    st.report_pass("test_case_passed")
```

---

## Test Categories

### 1. BGP Summary Commands (TC-001 to TC-010)

Tests global and address-family specific summary displays:
- Global BGP summary
- IPv4/IPv6 unicast summary
- VRF-specific summary
- JSON/wide format output
- Established/failed neighbor filtering

**Key Commands**:
- `show bgp summary`
- `show bgp ipv4 unicast summary`
- `show bgp ipv6 unicast summary`
- `show bgp ipv4 unicast vrf all summary`

### 2. BGP Neighbor Commands (TC-011 to TC-025)

Tests neighbor-specific information display:
- All neighbors listing
- Specific neighbor details
- Advertised/received routes
- Neighbor capabilities
- Connection details
- Timers and statistics

**Key Commands**:
- `show bgp ipv4 unicast neighbors`
- `show bgp ipv4 unicast neighbors <ip>`
- `show bgp ipv4 unicast neighbors <ip> advertised-routes`
- `show bgp ipv4 unicast neighbors <ip> received-routes`

### 3. BGP Route Display (TC-026 to TC-040)

Tests route table display and filtering:
- All routes display
- Specific route lookup
- Community-based filtering
- AS-path regex filtering
- Bestpath display
- Longer prefix matching

**Key Commands**:
- `show bgp ipv4 unicast`
- `show bgp ipv4 unicast <prefix>`
- `show bgp ipv4 unicast community <value>`
- `show bgp ipv4 unicast regexp <regex>`

### 4. BGP Configuration Display (TC-041 to TC-050)

Tests configuration retrieval:
- Running configuration
- Neighbor configuration
- Address-family configuration
- Peer-group configuration
- Route-map/prefix-list display

**Key Commands**:
- `show running-config bgp`
- `show running-config bgp neighbor <ip>`
- `show running-config route-map`

### 5. Negative Tests (TC-081 to TC-091)

Tests error handling for invalid inputs:
- Invalid IP addresses
- Non-existent neighbors
- Invalid VRF names
- Invalid prefix formats
- Invalid AS-path regex
- Non-existent filters

---

## Output and Logging

### Log Files Location

```
logs/test_bgp_show_YYYY-MM-DD_HHMMSS/
├── dlog-D1-<hostname>.log       # Per-device command logs
├── dlog-D2-<hostname>.log
├── module_test_bgp_show_commands.log  # Module-level logs
├── results.html                  # HTML test report
└── consolidated_report.html      # Aggregated results
```

### Log Contents

**Per-Test Logs**:
- Test banner (start/end)
- Command executed
- Output received
- Validation results
- Pass/fail status

**Example Log Entry**:
```
=================================================
TEST SETUP: test_bgp_show_tc001_global_summary
=================================================
Executing: show bgp summary
[Command output...]
✓ Global BGP summary displayed successfully
PASS: test_case_passed
```

---

## Validation Methods

### 1. Output Field Validation

Checks for presence of expected keywords/fields:

```python
expected_fields = ["router identifier", "local AS number", "Neighbor"]
if not self._validate_output_contains(output, expected_fields):
    st.report_fail("msg", "Missing expected fields")
```

### 2. Neighbor Presence Validation

Validates specific neighbor IP is displayed:

```python
if not self._validate_bgp_summary_output(output, neighbor_ip):
    st.report_fail("msg", "Neighbor not found")
```

### 3. Session State Validation

Verifies BGP session is established before running tests:

```python
if not st.poll_wait(bgp_api.verify_bgp_summary, timeout, dut, state="Established"):
    st.report_fail("bgp_neighbor_not_established")
```

---

## Extending the Test Suite

### Adding New Test Cases

1. **Add test case to YAML**:

```yaml
testcases:
  TC-092:
    title: "New test case description"
    command: "show bgp new-command"
    cli_type: "klish"
    expected_fields:
      - "field1"
      - "field2"
```

2. **Add test method to Python script**:

```python
@pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC092"])
def test_bgp_show_tc092_new_test(self) -> None:
    """TC-092: New test description."""
    testcase = self._get_testcase("TC-092")
    command = testcase.get("command")

    output = self._execute_show_command(self.data.D1, command)
    if not output:
        st.report_fail("msg", f"Command '{command}' failed")

    st.log("✓ New test passed")
    st.report_pass("test_case_passed")
```

### Adding Custom Validation

Create new validation method:

```python
def _validate_custom_output(self, output: Any, criteria: Dict) -> bool:
    """Custom validation logic."""
    # Implement validation
    return True
```

---

## Troubleshooting

### Common Issues

**1. BGP Session Not Established**

**Error**:
```
BGP session not established on D1 with neighbor 10.0.24.2
FAIL: bgp_neighbor_not_established
```

**Solution**:
```bash
# Check BGP configuration on both devices
sudo vtysh -c "show bgp ipv4 summary"
sudo vtysh -c "show bgp neighbors"

# Verify interface is up
show interface Ethernet32

# Check BGP logs
show logging | include bgp
```

**2. Command Not Supported**

**Error**:
```
Command 'show bgp statistics' failed
```

**Solution**:
- Check SONiC version compatibility
- Try alternative commands (e.g., `show ip bgp summary` vs `show bgp ipv4 unicast summary`)
- Verify CLI type (klish vs vtysh)

**3. Output Validation Failing**

**Error**:
```
Missing expected fields: ['router identifier']
```

**Solution**:
- Check YAML expected_fields configuration
- Verify actual output format
- Update validation logic if output format changed

**4. Testbed Connection Issues**

**Error**:
```
Failed to connect to device
```

**Solution**:
```bash
# Verify testbed YAML configuration
cat testbeds/testbed_vs_2d.yaml

# Test SSH connectivity
ssh admin@192.168.100.39

# Check credentials
```

---

## Best Practices

### 1. Before Running Tests

- ✅ Verify BGP session is established
- ✅ Check BGP configuration on both devices
- ✅ Ensure test network routes are advertised
- ✅ Review testbed YAML for correct device IPs
- ✅ Confirm SONiC version compatibility

### 2. During Test Execution

- Monitor logs in real-time: `tail -f logs/.../module_test_bgp_show_commands.log`
- Watch for command execution errors
- Check for timeout issues (increase verify_timeout if needed)

### 3. After Test Execution

- Review HTML report: `logs/.../results.html`
- Check failed test logs for root cause
- Validate unexpected failures aren't due to configuration issues
- Save logs for future reference

### 4. Continuous Integration

- Run tests regularly as part of CI/CD pipeline
- Monitor pass rate trends
- Update expected outputs when BGP output format changes
- Add new tests for new BGP features

---

## Performance Considerations

| Metric | Value | Notes |
|--------|-------|-------|
| Total Test Cases | 91 | Full suite |
| Estimated Runtime | 15-20 minutes | Depends on timeout settings |
| Parallel Execution | Not recommended | Show commands are sequential |
| Memory Usage | Low | Read-only operations |
| Network Impact | Minimal | No configuration changes |

---

## Related Documentation

- **Test Plan**: `tests/routing/bgp/doc/TC_BGP_SHOW_COMMANDS_COMPREHENSIVE.md`
- **BGP Clear Commands**: `tests/routing/bgp/test_bgp_clear_commands_comprehensive.py`
- **BGP API Reference**: `apis/routing/bgp.py`
- **SpyTest Guidelines**: `spy_test_coding_guideline.md`

---

## Support and Contribution

### Reporting Issues

Create an issue with:
- Test case ID (e.g., TC-042)
- SONiC version
- Error message
- Log file excerpt
- Expected vs actual behavior

### Contributing

1. Follow SpyTest coding guidelines
2. Add test cases to YAML first
3. Implement test methods with proper validation
4. Add documentation for new features
5. Test on both HW and Virtual environments

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-06-07 | 1.0.0 | Initial release with 91 test cases |

---

**Author**: Athira
**Contact**: [Your contact information]
**Last Updated**: June 7, 2026
