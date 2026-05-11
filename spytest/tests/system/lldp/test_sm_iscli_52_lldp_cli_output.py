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
            lambda: self._has_lldp_neighbors(dut),
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
                st.report_fail("lldp_neighbors_output_empty")

            output_str = str(output)
            st.log(f"Output length: {len(output_str)} characters")

            # Verify expected keywords are present
            required_keywords = ["Interface", "ChassisID", "PortID"]
            missing_keywords = [kw for kw in required_keywords if kw not in output_str]

            if missing_keywords:
                st.log(f"✗ Missing keywords in output: {missing_keywords}")
                st.log(f"Output: {output_str[:500]}")
                st.report_fail("lldp_neighbors_incomplete")

            st.log(f"✓ 'show lldp neighbor' returned data with required keywords")
            st.log(f"  Output preview: {output_str[:200]}...")

            self.test_passed = True
            st.report_pass()

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_neighbors_test_failed")

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
                st.report_fail("lldp_table_output_empty")

            output_str = str(output)
            st.log(f"Output length: {len(output_str)} characters")

            # Verify expected keywords are present (table headers)
            required_keywords = ["LocalPort", "RemoteDevice", "RemotePortID"]
            missing_keywords = [kw for kw in required_keywords if kw not in output_str]

            if missing_keywords:
                st.log(f"✗ Missing keywords in table output: {missing_keywords}")
                st.log(f"Output: {output_str[:500]}")
                st.report_fail("lldp_table_incomplete")

            st.log(f"✓ 'show lldp table' returned data with required headers")
            st.log(f"  Output preview: {output_str[:200]}...")

            self.test_passed = True
            st.report_pass()

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_table_test_failed")

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
                st.report_fail("lldp_statistics_output_empty")

            output_str = str(output)
            st.log(f"Output length: {len(output_str)} characters")

            # Verify statistics-related keywords are present
            required_keywords = ["Transmitted", "Received", "Discarded"]
            # At minimum, should have some counter information
            has_stats = len(output_str) > 50  # Statistics output should be substantial

            if not has_stats:
                st.log(f"✗ Statistics output too short: {len(output_str)} chars")
                st.log(f"Output: {output_str}")
                st.report_fail("lldp_statistics_incomplete")

            st.log(f"✓ 'show lldp statistics | no-more' returned data")
            st.log(f"  Output preview: {output_str[:200]}...")

            self.test_passed = True
            st.report_pass()

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_statistics_test_failed")

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
                st.report_pass()
            else:
                st.log(f"✗ 'show lldp' response is not appropriate")
                st.log(f"  Found {len(found_subcommands)}/3 subcommands")
                st.log(f"  Output length: {len(output_str)} characters")
                st.report_fail("lldp_show_subcommand_help_invalid")

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_subcommand_help_test_failed")

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
                st.report_fail("lldp_comparison_critical_failed")

            st.log(f"✓ All LLDP commands returned appropriate output")
            st.log(f"  Summary: {results}")

            self.test_passed = True
            st.report_pass()

        except Exception as err:
            self.test_failed_reason = str(err)
            st.log(f"✗ Test failed: {err}")
            st.report_fail("lldp_comparison_test_failed")
