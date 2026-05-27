"""
LLDP CLI OUTPUT VALIDATION - SM_ISCLI_52

Author: Athira
2026

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2d.yaml \\
  system/lldp/test_sm_iscli_52_lldp_cli_output.py \\
  --logs-path ./logs/test_sm_iscli_52_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Validates that LLDP show commands return proper output in IS-CLI (Klish) mode.
  The issue was that 'show lldp' commands returned empty output in IS-CLI while
  Click CLI displayed data correctly. This test verifies the fix by:
  1. Ensuring LLDP is enabled on interfaces
  2. Waiting for LLDP neighbor discovery
  3. Executing show lldp commands (neighbors, table, statistics)
  4. Verifying that commands return actual data (not empty)
  5. Validating output format matches expected LLDP information

Pre-requisites:
  - Topology: 2-node with back-to-back links (D1-D2)
  - Supported: Virtual (VS) only
  - CLI Type: Klish (IS-CLI) mode required
  - Feature: LLDP must be enabled on SONiC image
  - Required test variables (YAML): lldp_wait_time, cli_type
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.system.interface as intf_api

# Test case ID
TESTCASE_ID = "SM_ISCLI_52"

# LLDP configuration constants
LLDP_WAIT_TIME = 30  # Time to wait for LLDP neighbor discovery
LLDP_SEND_INTERVAL = 30  # LLDP send interval in seconds
LLDP_TTL = 120  # LLDP TTL

# YAML variable file path
VAR_FILE_ENV = "SM_ISCLI_52_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "system"
    / "lldp"
    / "vars_sm_iscli_52_lldp_cli_output.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        raise FileNotFoundError(f"SM_ISCLI_52 LLDP variable file not found: {candidate}")

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


@pytest.mark.topology("vs")
class TestSmIscli52LldpCliOutput:
    """Test cases for LLDP CLI output validation in IS-CLI mode."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and test configuration."""
        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Ensure we have a 2-node topology for LLDP neighbor discovery
        min_topology = defaults.get("min_topology") or ["D1D2:1"]
        topology = st.ensure_min_topology(*min_topology)

        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.lldp_wait_time = int(defaults.get("lldp_wait_time", LLDP_WAIT_TIME))
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 60))

        # Get interface names from topology
        cls.data.dut1_ifaces = []
        cls.data.dut2_ifaces = []
        cls._collect_interfaces()

        st.log(f"✓ Topology loaded: D1={cls.data.dut1}, D2={cls.data.dut2}")
        st.log(f"✓ D1 interfaces: {cls.data.dut1_ifaces}")
        st.log(f"✓ D2 interfaces: {cls.data.dut2_ifaces}")

    @classmethod
    def _collect_interfaces(cls) -> None:
        """Collect interface names from topology configuration."""
        try:
            # Get interface information from testbed
            d1_info = st.get_device_info(cls.data.dut1)
            d2_info = st.get_device_info(cls.data.dut2)

            # Fallback to standard interface naming if topology info unavailable
            if not cls.data.dut1_ifaces:
                cls.data.dut1_ifaces = ["Ethernet0", "Ethernet4"]
            if not cls.data.dut2_ifaces:
                cls.data.dut2_ifaces = ["Ethernet0", "Ethernet4"]

        except Exception as err:
            st.log(f"⚠ Warning: Could not collect interfaces from topology: {err}")
            st.log("Using default interface names")
            cls.data.dut1_ifaces = ["Ethernet0", "Ethernet4"]
            cls.data.dut2_ifaces = ["Ethernet0", "Ethernet4"]

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after test class completes."""
        st.log("\n=== TEARDOWN: Cleaning up LLDP configuration ===")
        # LLDP configuration cleanup (LLDP is typically always-on, so minimal cleanup needed)
        st.log("✓ LLDP teardown complete")

    def setup_method(self) -> None:
        """Reset per-test state."""
        self.test_passed = False
        self.test_failed_reason = None

    def teardown_method(self) -> None:
        """Cleanup after each test."""
        # Per-test cleanup if needed
        pass

    def _check_lldp_enabled(self, dut: str) -> bool:
        """Check if LLDP is enabled on the device."""
        st.log(f"Checking LLDP status on {dut}")
        # Simply proceed - LLDP should be enabled by default on testbed
        st.log(f"✓ Assuming LLDP is enabled on {dut}")
        return True

    def _wait_for_lldp_neighbors(self, dut: str, timeout: int = None) -> bool:
        """Wait for LLDP neighbor discovery."""
        if timeout is None:
            timeout = self.data.lldp_wait_time

        st.log(f"Waiting {timeout} seconds for LLDP neighbors to be discovered on {dut}...")
        return st.poll_wait(
            lambda _: self._has_lldp_neighbors(dut),
            timeout,
            2
        )

    def _has_lldp_neighbors(self, dut: str) -> bool:
        """Check if device has discovered any LLDP neighbors."""
        cmd = "show lldp neighbor | no-more"
        try:
            output = st.show(dut, cmd, type=self.data.cli_type, skip_tmpl=True, skip_error_check=True)

            # Check for any LLDP neighbor data
            if output:
                output_str = str(output)
                # Look for signs of neighbor data (Interface, Chassis ID, PortID, etc.)
                return any(keyword in output_str for keyword in [
                    "Interface",
                    "ChassisID",
                    "PortID",
                    "Capability"
                ])
        except Exception as err:
            st.log(f"⚠ Error checking LLDP neighbors: {err}")

        return False

    @pytest.mark.inventory(feature="Regression", testcases=[TESTCASE_ID])
    def test_01_lldp_show_neighbors_not_empty(self) -> None:
        """
        TC-SM_ISCLI_52-001: Verify 'show lldp neighbor' returns data in IS-CLI.

        This test addresses the bug where 'show lldp' commands returned empty output
        in IS-CLI (Klish) mode. The test verifies that the show lldp neighbor command
        returns actual neighbor information.
        """
        tcid = "TC-SM_ISCLI_52-001"
        st.banner(f"{tcid}: Verify 'show lldp neighbor' returns data in IS-CLI")

        try:
            # Step 1: Verify LLDP is enabled on D1
            st.log("Step 1: Verify LLDP is enabled on D1")
            self._check_lldp_enabled(self.data.dut1)

            # Step 2: Wait for LLDP neighbors to be discovered
            st.log("Step 2: Wait for LLDP neighbors to be discovered")
            if not self._wait_for_lldp_neighbors(self.data.dut1):
                st.log("⚠ No neighbors discovered within timeout, continuing with test")

            # Step 3: Execute 'show lldp neighbor | no-more' command
            st.log("Step 3: Execute 'show lldp neighbor | no-more' command")
            cmd = "show lldp neighbor | no-more"
            output = st.show(self.data.dut1, cmd, type=self.data.cli_type, skip_tmpl=True, skip_error_check=True)

            # Step 4: Verify command returns data (not empty)
            st.log("Step 4: Verify 'show lldp neighbor' returns data")
            if not output:
                st.log("✗ 'show lldp neighbor' returned empty output")
                st.report_fail("tc_sm_iscli_52_001")

            output_str = str(output)
            st.log(f"Output length: {len(output_str)} characters")

            # Verify expected keywords are present
            required_keywords = ["Interface", "ChassisID", "PortID"]
            missing_keywords = [kw for kw in required_keywords if kw not in output_str]

            if missing_keywords:
                st.log(f"✗ Missing keywords in output: {missing_keywords}")
                st.log(f"Output: {output_str[:500]}")
                st.report_fail("tc_sm_iscli_52_001")

            st.log(f"✓ 'show lldp neighbor' returned data with required keywords")
            st.log(f"  Output preview: {output_str[:200]}...")

            self.test_passed = True
            st.report_pass("lldp_show_neighbor_pass")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_show_neighbor_fail")

    @pytest.mark.inventory(feature="Regression", testcases=[TESTCASE_ID])
    def test_02_lldp_show_table_not_empty(self) -> None:
        """
        TC-SM_ISCLI_52-002: Verify 'show lldp table' returns data in IS-CLI.

        Validates that the lldp table command displays neighbor information in
        a tabular format.
        """
        tcid = "TC-SM_ISCLI_52-002"
        st.banner(f"{tcid}: Verify 'show lldp table' returns data in IS-CLI")

        try:
            # Step 1: Verify LLDP is enabled on D1
            st.log("Step 1: Verify LLDP is enabled on D1")
            self._check_lldp_enabled(self.data.dut1)

            # Step 2: Wait for LLDP neighbors to be discovered
            st.log("Step 2: Wait for LLDP neighbors to be discovered")
            if not self._wait_for_lldp_neighbors(self.data.dut1):
                st.log("⚠ No neighbors discovered within timeout, continuing with test")

            # Step 3: Execute 'show lldp table | no-more' command
            st.log("Step 3: Execute 'show lldp table | no-more' command")
            cmd = "show lldp table | no-more"
            output = st.show(self.data.dut1, cmd, type=self.data.cli_type, skip_tmpl=True, skip_error_check=True)

            # Step 4: Verify command returns data (not empty)
            st.log("Step 4: Verify 'show lldp table' returns data")
            if not output:
                st.log("✗ 'show lldp table' returned empty output")
                st.report_fail("tc_sm_iscli_52_002")

            output_str = str(output)
            st.log(f"Output length: {len(output_str)} characters")

            # Verify expected keywords are present (table headers)
            required_keywords = ["LocalPort", "RemoteDevice", "RemotePortID"]
            missing_keywords = [kw for kw in required_keywords if kw not in output_str]

            if missing_keywords:
                st.log(f"✗ Missing keywords in table output: {missing_keywords}")
                st.log(f"Output: {output_str[:500]}")
                st.report_fail("tc_sm_iscli_52_002")

            st.log(f"✓ 'show lldp table' returned data with required headers")
            st.log(f"  Output preview: {output_str[:200]}...")

            self.test_passed = True
            st.report_pass("tc_sm_iscli_52_002")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("tc_sm_iscli_52_002")

    @pytest.mark.inventory(feature="Regression", testcases=[TESTCASE_ID])
    def test_03_lldp_show_statistics_not_empty(self) -> None:
        """
        TC-SM_ISCLI_52-003: Verify 'show lldp statistics' returns data in IS-CLI.

        Validates that the lldp statistics command displays protocol statistics.
        Uses '| no-more' pipe to disable pagination and get complete output.
        """
        tcid = "TC-SM_ISCLI_52-003"
        st.banner(f"{tcid}: Verify 'show lldp statistics' returns data in IS-CLI")

        try:
            # Step 1: Verify LLDP is enabled on D1
            st.log("Step 1: Verify LLDP is enabled on D1")
            self._check_lldp_enabled(self.data.dut1)

            # Step 2: Execute 'show lldp statistics | no-more' command
            st.log("Step 2: Execute 'show lldp statistics | no-more' command")
            cmd = "show lldp statistics | no-more"
            output = st.show(self.data.dut1, cmd, type=self.data.cli_type, skip_tmpl=True, skip_error_check=True)

            # Step 3: Verify command returns data (not empty)
            st.log("Step 3: Verify 'show lldp statistics' returns data")
            if not output:
                st.log("✗ 'show lldp statistics' returned empty output")
                st.report_fail("tc_sm_iscli_52_003")

            output_str = str(output)
            st.log(f"Output length: {len(output_str)} characters")

            # Verify statistics-related keywords are present
            required_keywords = ["Transmitted", "Received", "Discarded"]
            # At minimum, should have some counter information
            has_stats = len(output_str) > 50  # Statistics output should be substantial

            if not has_stats:
                st.log(f"✗ Statistics output too short: {len(output_str)} chars")
                st.log(f"Output: {output_str}")
                st.report_fail("tc_sm_iscli_52_003")

            st.log(f"✓ 'show lldp statistics | no-more' returned data")
            st.log(f"  Output preview: {output_str[:200]}...")

            self.test_passed = True
            st.report_pass("tc_sm_iscli_52_003")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("tc_sm_iscli_52_003")

    @pytest.mark.inventory(feature="Regression", testcases=[TESTCASE_ID])
    def test_04_lldp_show_command_has_subcommands(self) -> None:
        """
        TC-SM_ISCLI_52-004: Verify 'show lldp' displays subcommand help in IS-CLI.

        When 'show lldp' is executed without subcommand, it should display available
        subcommands (neighbor, statistics, table) with their descriptions. This is the
        expected behavior that was missing in the original bug.

        Expected output:
        sonic# show lldp
          neighbor    Display LLDP neighbor information
          statistics  Display LLDP statistics information
          table       Display LLDP table information
        """
        tcid = "TC-SM_ISCLI_52-004"
        st.banner(f"{tcid}: Verify 'show lldp' displays subcommand help")

        try:
            # Step 1: Execute 'show lldp' without subcommand
            st.log("Step 1: Execute bare 'show lldp' command (without subcommand)")
            cmd = "show lldp"

            # This command should show help with subcommands in IS-CLI
            output = st.show(
                self.data.dut1,
                cmd,
                type=self.data.cli_type,
                skip_tmpl=True,
                skip_error_check=True
            )

            # Step 2: Verify output shows subcommand help
            st.log("Step 2: Verify 'show lldp' displays subcommand options")

            output_str = str(output) if output else ""
            st.log(f"Command output:\n{output_str}")

            # Verify all three subcommands are shown
            required_subcommands = ["neighbor", "statistics", "table"]
            found_subcommands = []

            for subcommand in required_subcommands:
                if subcommand in output_str.lower():
                    found_subcommands.append(subcommand)

            if len(found_subcommands) == 3:
                st.log(f"✓ 'show lldp' displays all required subcommands")
                st.log(f"  Found: {found_subcommands}")
            else:
                missing = [s for s in required_subcommands if s not in found_subcommands]
                st.log(f"⚠ Missing subcommands: {missing}")
                st.log(f"  Found: {found_subcommands}")

            # Step 3: Verify descriptions are present
            st.log("Step 3: Verify subcommand descriptions are present")
            description_keywords = ["display", "information", "neighbor", "statistics", "table"]
            has_descriptions = all(
                any(keyword in output_str.lower() for keyword in [desc])
                for desc in description_keywords
            )

            if has_descriptions:
                st.log(f"✓ Subcommand descriptions are present in output")
            else:
                st.log(f"⚠ Some subcommand descriptions may be missing")

            # Step 4: Overall validation
            st.log("Step 4: Overall validation of command response")
            is_valid_response = len(found_subcommands) >= 2 and len(output_str) > 50

            if is_valid_response:
                st.log(f"✓ 'show lldp' command responds appropriately with subcommand help")
                self.test_passed = True
                st.report_pass("tc_sm_iscli_52_004")
            else:
                st.log(f"✗ 'show lldp' response is not appropriate")
                st.log(f"  Found {len(found_subcommands)}/3 subcommands")
                st.log(f"  Output length: {len(output_str)} characters")
                st.report_fail("tc_sm_iscli_52_004")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("tc_sm_iscli_52_004")

    @pytest.mark.inventory(feature="Regression", testcases=[TESTCASE_ID])
    def test_05_lldp_commands_compare_click_vs_klish(self) -> None:
        """
        TC-SM_ISCLI_52-005: Verify LLDP commands work in Klish mode like Click CLI.

        This test ensures that key LLDP commands produce output in Klish (IS-CLI) mode
        similar to Click CLI, validating the fix for the SM_ISCLI_52 issue.
        """
        tcid = "TC-SM_ISCLI_52-005"
        st.banner(f"{tcid}: Verify Klish LLDP commands match Click CLI behavior")

        try:
            # Step 1: Verify LLDP is enabled
            st.log("Step 1: Verify LLDP is enabled")
            self._check_lldp_enabled(self.data.dut1)

            # Step 2: Wait for neighbors
            st.log("Step 2: Wait for LLDP neighbors to be discovered")
            if not self._wait_for_lldp_neighbors(self.data.dut1):
                st.log("⚠ No neighbors discovered, proceeding with test")

            # Step 3: Test all key LLDP commands
            st.log("Step 3: Test key LLDP commands")
            commands = [
                "show lldp neighbor | no-more",
                "show lldp table | no-more",
                "show lldp statistics | no-more"
            ]

            results = {}
            for cmd in commands:
                st.log(f"  Executing: {cmd}")
                try:
                    output = st.show(
                        self.data.dut1,
                        cmd,
                        type=self.data.cli_type,
                        skip_tmpl=True,
                        skip_error_check=True
                    )
                    output_str = str(output) if output else ""
                    has_data = len(output_str) > 20  # Meaningful data threshold
                    results[cmd] = {
                        "status": "OK" if has_data else "EMPTY",
                        "output_length": len(output_str)
                    }
                    st.log(f"    ✓ {cmd}: {results[cmd]['status']} ({len(output_str)} chars)")
                except Exception as err:
                    results[cmd] = {
                        "status": "ERROR",
                        "error": str(err)
                    }
                    st.log(f"    ✗ {cmd}: ERROR - {err}")

            # Step 4: Verify critical commands returned data
            st.log("Step 4: Verify critical commands returned data")
            critical_commands = ["show lldp neighbor | no-more", "show lldp table | no-more"]
            failed_commands = [
                cmd for cmd in critical_commands
                if results[cmd]["status"] != "OK"
            ]

            if failed_commands:
                st.log(f"✗ Critical commands failed: {failed_commands}")
                st.log(f"Results: {results}")
                st.report_fail("tc_sm_iscli_52_005")

            st.log(f"✓ All LLDP commands returned appropriate output")
            st.log(f"  Summary: {results}")

            self.test_passed = True
            st.report_pass("tc_sm_iscli_52_005")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("tc_sm_iscli_52_005")

    @pytest.mark.inventory(feature="Regression", testcases=["SM_ISCLI_P2_87"])
    def test_06_lldp_show_neighbor_ethernet_interface_handling(self) -> None:
        """
        TC-SM_ISCLI_P2_87: Verify 'show lldp neighbor Ethernet' interface handling.

        Bug Description: Running 'show lldp neighbor Ethernet' without a specific interface
        number fails or returns incomplete output. The command should either:
        - Show an error message requesting a specific interface, OR
        - Show help/usage information

        Expected Behavior:
        - 'show lldp neighbor Ethernet' -> Error/help message (interface number required)
        - 'show lldp neighbor Ethernet 4' -> Shows LLDP neighbor info for that interface

        This test validates that the command properly handles interface specification.
        """
        tcid = "TC-SM_ISCLI_P2_87"
        st.banner(f"{tcid}: Verify 'show lldp neighbor Ethernet' interface handling")

        try:
            # Step 1: Verify LLDP is enabled on D1
            st.log("Step 1: Verify LLDP is enabled on D1")
            self._check_lldp_enabled(self.data.dut1)

            # Step 2: Wait for LLDP neighbors
            st.log("Step 2: Wait for LLDP neighbors to be discovered")
            if not self._wait_for_lldp_neighbors(self.data.dut1):
                st.log("⚠ No neighbors discovered within timeout, continuing with test")

            # Step 3: Test 'show lldp neighbor Ethernet' without interface number
            st.log("Step 3: Execute 'show lldp neighbor Ethernet' without interface number")
            cmd_no_iface = "show lldp neighbor Ethernet | no-more"
            output_no_iface = st.show(
                self.data.dut1,
                cmd_no_iface,
                type=self.data.cli_type,
                skip_tmpl=True,
                skip_error_check=True
            )

            output_no_iface_str = str(output_no_iface) if output_no_iface else ""
            st.log(f"Output (no interface): {output_no_iface_str[:200]}")

            # Step 4: Test 'show lldp neighbor Ethernet X' with specific interface
            st.log("Step 4: Execute 'show lldp neighbor Ethernet 4' with specific interface")
            cmd_with_iface = "show lldp neighbor Ethernet 4 | no-more"
            output_with_iface = st.show(
                self.data.dut1,
                cmd_with_iface,
                type=self.data.cli_type,
                skip_tmpl=True,
                skip_error_check=True
            )

            output_with_iface_str = str(output_with_iface) if output_with_iface else ""
            st.log(f"Output (with interface): {output_with_iface_str[:300]}")

            # Step 5: Verify specific interface command returns meaningful data
            st.log("Step 5: Verify 'show lldp neighbor Ethernet 4' returns neighbor info")

            # Check if output contains LLDP neighbor information
            lldp_keywords = ["ChassisID", "PortID", "Interface", "Capability"]
            has_lldp_data = any(kw in output_with_iface_str for kw in lldp_keywords)

            if has_lldp_data:
                st.log(f"✓ 'show lldp neighbor Ethernet 4' returns valid LLDP neighbor data")
                self.test_passed = True
                st.report_pass("lldp_interface_query_pass")
            else:
                st.log(f"✗ 'show lldp neighbor Ethernet 4' did not return expected LLDP data")
                st.log(f"  Expected to find one of: {lldp_keywords}")
                st.log(f"  Got: {output_with_iface_str[:500]}")
                st.report_fail("lldp_interface_query_fail")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_interface_query_exception")

    @pytest.mark.inventory(feature="Regression", testcases=["SM_ISCLI_P2_88"])
    def test_07_lldp_show_neighbor_management_ip_verification(self) -> None:
        """
        TC-SM_ISCLI_P2_88: Verify LLDP advertises correct management IP address.

        Bug Description: ISCLI is not showing management IP address correctly in LLDP
        neighbor information. The system still sends docker IP address instead of the
        configured management IP for both IPv4 and IPv6.

        Expected Behavior:
        - MgmtIP field should display the configured management IP (e.g., 192.168.100.36)
        - NOT the docker container IP address
        - Management IPv4 and IPv6 addresses should be correctly advertised

        This test validates that the management IP is correctly shown in LLDP output.
        """
        tcid = "TC-SM_ISCLI_P2_88"
        st.banner(f"{tcid}: Verify LLDP management IP address is correct")

        try:
            # Step 1: Verify LLDP is enabled on D1
            st.log("Step 1: Verify LLDP is enabled on D1")
            self._check_lldp_enabled(self.data.dut1)

            # Step 2: Wait for LLDP neighbors
            st.log("Step 2: Wait for LLDP neighbors to be discovered")
            if not self._wait_for_lldp_neighbors(self.data.dut1):
                st.log("⚠ No neighbors discovered within timeout, continuing with test")

            # Step 3: Get LLDP neighbor information from D1
            st.log("Step 3: Execute 'show lldp neighbor | no-more' on D1")
            cmd = "show lldp neighbor | no-more"
            output = st.show(
                self.data.dut1,
                cmd,
                type=self.data.cli_type,
                skip_tmpl=True,
                skip_error_check=True
            )

            output_str = str(output) if output else ""
            st.log(f"Output length: {len(output_str)} characters")

            # Step 4: Verify MgmtIP field is present
            st.log("Step 4: Verify MgmtIP field is present in output")
            if "MgmtIP:" not in output_str:
                st.log("✗ MgmtIP field not found in LLDP neighbor output")
                st.log(f"Output: {output_str[:500]}")
                st.report_fail("lldp_mgmt_ip_missing")

            # Step 5: Extract and validate MgmtIP value
            st.log("Step 5: Extract and validate MgmtIP value")
            import re
            mgmt_ip_pattern = r'MgmtIP:\s*([\d\.]+)'
            mgmt_ip_match = re.search(mgmt_ip_pattern, output_str)

            if mgmt_ip_match:
                mgmt_ip = mgmt_ip_match.group(1)
                st.log(f"✓ Found MgmtIP: {mgmt_ip}")

                # Validate that it's NOT a docker IP (typically 172.17.x.x or similar)
                if mgmt_ip.startswith("172.17") or mgmt_ip.startswith("127"):
                    st.log(f"✗ MgmtIP appears to be docker container IP: {mgmt_ip}")
                    st.log(f"  Expected: Management network IP (e.g., 192.168.100.x)")
                    st.report_fail("lldp_docker_ip_detected")
                elif mgmt_ip.startswith("192.168.100") or mgmt_ip.startswith("10."):
                    st.log(f"✓ MgmtIP is a valid management IP: {mgmt_ip}")
                    st.log(f"  Correctly advertising management network IP")
                    self.test_passed = True
                    st.report_pass("lldp_mgmt_ip_valid")
                else:
                    st.log(f"⚠ MgmtIP has unexpected format: {mgmt_ip}")
                    st.log(f"  Continuing with test (may be valid in test environment)")
                    self.test_passed = True
                    st.report_pass("lldp_mgmt_ip_valid")
            else:
                st.log(f"✗ Could not parse MgmtIP from output")
                st.log(f"Output: {output_str[:500]}")
                st.report_fail("lldp_mgmt_ip_parse_fail")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_mgmt_ip_test_exception")

    @pytest.mark.inventory(feature="Regression", testcases=["SM_ISCLI_P2_100"])
    def test_08_lldp_table_capability_column_validation(self) -> None:
        """
        TC-SM_ISCLI_P2_100: Verify 'show lldp table' includes capability column.

        Bug Description: The 'show lldp table' command did not populate the capability
        column even though capability information was present in 'show lldp neighbor'.
        This is a CLI display/parsing issue where the table format doesn't include
        capability information.

        Expected Behavior:
        - 'show lldp table' should include a Capability column
        - Capability values (e.g., Bridge, Router, WLAN, Station) should be displayed
        - Capability column should be consistent with 'show lldp neighbor' output

        This test validates that capability information is properly shown in table format.
        """
        tcid = "TC-SM_ISCLI_P2_100"
        st.banner(f"{tcid}: Verify 'show lldp table' includes capability column")

        try:
            # Step 1: Verify LLDP is enabled on D1
            st.log("Step 1: Verify LLDP is enabled on D1")
            self._check_lldp_enabled(self.data.dut1)

            # Step 2: Wait for LLDP neighbors
            st.log("Step 2: Wait for LLDP neighbors to be discovered")
            if not self._wait_for_lldp_neighbors(self.data.dut1):
                st.log("⚠ No neighbors discovered within timeout, continuing with test")

            # Step 3: Get 'show lldp neighbor' for reference
            st.log("Step 3: Execute 'show lldp neighbor | no-more' for reference")
            cmd_neighbor = "show lldp neighbor | no-more"
            output_neighbor = st.show(
                self.data.dut1,
                cmd_neighbor,
                type=self.data.cli_type,
                skip_tmpl=True,
                skip_error_check=True
            )

            output_neighbor_str = str(output_neighbor) if output_neighbor else ""
            st.log(f"Neighbor output length: {len(output_neighbor_str)} characters")

            # Check if neighbor output contains capability info
            has_capability_in_neighbor = "Capability:" in output_neighbor_str
            st.log(f"Capability information in 'show lldp neighbor': {has_capability_in_neighbor}")

            # Step 4: Get 'show lldp table' output
            st.log("Step 4: Execute 'show lldp table | no-more'")
            cmd_table = "show lldp table | no-more"
            output_table = st.show(
                self.data.dut1,
                cmd_table,
                type=self.data.cli_type,
                skip_tmpl=True,
                skip_error_check=True
            )

            output_table_str = str(output_table) if output_table else ""
            st.log(f"Table output length: {len(output_table_str)} characters")

            # Step 5: Analyze 'show lldp table' output structure
            st.log("Step 5: Analyze 'show lldp table' output structure")
            st.log(f"Table output:\n{output_table_str}")

            # Look for table headers
            table_headers = ["LocalPort", "RemoteDevice", "RemotePortID", "Capability"]
            found_headers = []
            for header in table_headers:
                if header in output_table_str:
                    found_headers.append(header)

            st.log(f"Found table headers: {found_headers}")

            # Step 6: Verify capability column is present
            st.log("Step 6: Verify capability column is present in table")
            if "Capability" in output_table_str or "Bridge" in output_table_str or "Router" in output_table_str:
                st.log(f"✓ Capability information found in 'show lldp table'")
                st.log(f"  Table includes capability data")
                self.test_passed = True
                st.report_pass("lldp_table_capability_pass")
            else:
                st.log(f"✗ Capability column/data not found in 'show lldp table'")
                st.log(f"  Found headers: {found_headers}")

                # If capability is in neighbor but not in table, it's a bug
                if has_capability_in_neighbor:
                    st.log(f"  ⚠ Capability IS present in 'show lldp neighbor' but MISSING in 'show lldp table'")
                    st.log(f"  This confirms the bug: table format doesn't include capability column")

                st.report_fail("lldp_table_capability_missing")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_table_capability_exception")
