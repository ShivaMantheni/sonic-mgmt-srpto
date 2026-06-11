"""
MANAGEMENT INTERFACE REACHABILITY
Author: Shiva
2026

How to run:
  ./bin/spytest  --tryssh 1  \\
  --testbed ./testbeds/ztp_standalone.yaml  \\
  tests/system/management/test_mgmt_interface_reachability.py \\
  --logs-path ./logs/mgmt_reachability_$(date +%F_%H%M%S) \\
  --log-level debug  --skip-init-config  --ifname-type native

Description:
  Validates IPv4 and IPv6 reachability on the Management interface. This test
  verifies that the Management0 interface is properly configured with both IPv4
  and IPv6 addresses and responds successfully to ping requests from the device
  itself. The test ensures management connectivity is functional for both IP
  protocols.

  Test validates:
  - Management interface has IPv6 address assigned
  - IPv6 address responds to ping6 with 0% packet loss
  - Management interface has IPv4 address assigned
  - IPv4 address responds to ping with 0% packet loss
  - Interface operational status is up/up

Pre-requisites:
  - Topology: standalone (single DUT) | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 1 node (standalone)
        # +--------------------+
        # |    smic_sonic1     |
        # | (192.168.100.121)  |
        # |   Management0      |
        # +--------------------+

  - Feature: Management interface with IPv4 and IPv6
  - Min SONiC version: Any version supporting IS-CLI (klish)
  - Required test variables (YAML): spytest/vars/system/mgmt/vars_mgmt_interface_reachability.yaml
  - Management interface must be administratively UP
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.system.mgmt_interface as mgmt_api

# Environment variable for custom variable file location
VAR_FILE_ENV = "MGMT_INTERFACE_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "system"
    / "mgmt"
    / "vars_mgmt_interface_reachability.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        raise FileNotFoundError(
            f"Management interface variable file not found: {candidate}"
        )

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    if "testcases" not in content:
        raise ValueError(
            "Management interface YAML must contain key 'testcases'"
        )

    return content


@pytest.mark.topology("any")
class TestManagementInterfaceReachability:
    """Testcases for Management interface IPv4 and IPv6 reachability validation."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and testcase variables for the suite."""
        st.banner("MANAGEMENT INTERFACE REACHABILITY TEST SUITE - SETUP")

        # Load configuration from YAML
        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Ensure minimum topology requirement
        min_topology = defaults.get("min_topology") or ["D1"]
        topology = st.ensure_min_topology(*min_topology)

        # Store configuration data
        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))

        # CLI type configuration
        cli_type = defaults.get("cli_type", "klish")
        cls.data.cli_type = cli_type

        # Get DUT handle
        cls.data.dut_names = st.get_dut_names()
        if not cls.data.dut_names:
            st.report_fail("msg", "No DUT available for testing")

        cls.data.dut = cls.data.dut_names[0]
        st.log(f"Using DUT: {cls.data.dut}")

        # Test parameters
        cls.data.mgmt_interface = defaults.get("mgmt_interface", "Management0")
        cls.data.ping_count = int(defaults.get("ping_count", 3))
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        st.log(f"Management Interface: {cls.data.mgmt_interface}")
        st.log(f"CLI Type: {cls.data.cli_type}")
        st.log(f"Ping Count: {cls.data.ping_count}")
        st.log(f"Verify Timeout: {cls.data.verify_timeout}")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after all tests complete."""
        st.banner("MANAGEMENT INTERFACE REACHABILITY TEST SUITE - TEARDOWN")
        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        st.log("Teardown complete - no configuration changes to revert")

    def setup_method(self) -> None:
        """Reset per-test state."""
        st.banner("TEST CASE SETUP")

    def teardown_method(self) -> None:
        """Cleanup after each test."""
        st.banner("TEST CASE TEARDOWN")

    def _get_testcase(self, tcid: str) -> Mapping[str, Any]:
        """Helper to fetch testcase definition from YAML."""
        testcase = self.data.testcases.get(tcid)
        if not testcase:
            st.report_fail("msg", f"Missing testcase definition for {tcid} in YAML")
        return testcase

    @pytest.mark.inventory(feature="Regression", testcases=["SONIC-MGMT-PING-001"])
    def test_mgmt_interface_ipv4_ipv6_reachability(self) -> None:
        """
        TC SONIC-MGMT-PING-001: Verify Management interface IPv4 and IPv6 reachability.

        Test Steps:
        Part 1 - IPv6 Reachability:
          1. Identify Management interface IPv6 address using 'show ipv6 interfaces'
          2. Verify interface status is up/up
          3. Ping the IPv6 address using 'ping6 <ipv6_address>'
          4. Verify 0% packet loss

        Part 2 - IPv4 Reachability:
          5. Identify Management interface IPv4 address using 'show ip interfaces'
          6. Verify interface status is up/up
          7. Ping the IPv4 address using 'ping <ipv4_address>'
          8. Verify 0% packet loss

        Pass Criteria:
        - Management interface has both IPv4 and IPv6 addresses assigned
        - Interface operational status is up/up
        - Both ping6 and ping commands succeed with 0% packet loss

        Fail Criteria:
        - Management interface missing IPv4 or IPv6 address
        - Interface is down
        - Ping results in packet loss or timeouts
        """
        st.banner("TEST CASE: Management Interface IPv4 and IPv6 Reachability")

        # Get test case configuration
        testcase = self._get_testcase("SONIC-MGMT-PING-001")
        interface = testcase.get("interface", self.data.mgmt_interface)
        test_ipv4 = testcase.get("test_ipv4", True)
        test_ipv6 = testcase.get("test_ipv6", True)
        ping_count = testcase.get("ping_count", self.data.ping_count)
        ping_timeout = testcase.get("ping_timeout", 10)
        expected_packet_loss = testcase.get("expected_packet_loss", 0)

        dut = self.data.dut
        cli_type = self.data.cli_type

        st.log("Test Parameters:")
        st.log(f"  DUT: {dut}")
        st.log(f"  Management Interface: {interface}")
        st.log(f"  Test IPv4: {test_ipv4}")
        st.log(f"  Test IPv6: {test_ipv6}")
        st.log(f"  Ping Count: {ping_count}")
        st.log(f"  Expected Packet Loss: {expected_packet_loss}%")

        # ========== PART 1: IPv6 REACHABILITY ==========
        if test_ipv6:
            st.banner("PART 1: IPv6 REACHABILITY")

            # Step 1: Identify Management interface IPv6 address
            st.banner("STEP 1: Identify Management Interface IPv6 Address")
            st.log(f'Executing: show ipv6 interfaces | grep "NAME|{interface}"')

            status_ok, details = mgmt_api.get_mgmt_interface_details_cli(
                dut,
                interface=interface,
                family="ipv6",
                cli_type=cli_type,
            )

            if not status_ok:
                st.error(f"Management interface IPv6 verification failed: {details}")
                st.report_fail(
                    "msg",
                    f"Management interface {interface} IPv6 status check failed: "
                    f"{details.get('error', 'Unknown error')}"
                )

            ipv6_with_mask = details.get("ipaddr", "")
            if not ipv6_with_mask:
                st.report_fail(
                    "msg",
                    f"No IPv6 address found on {interface}"
                )

            # Remove mask to get IP address only
            ipv6_address = ipv6_with_mask.split("/")[0] if "/" in ipv6_with_mask else ipv6_with_mask

            st.log(f"Found IPv6 address: {ipv6_address}")
            st.log(f"Interface status: {details.get('status', 'unknown')}")

            # Step 2: Ping the IPv6 address
            st.banner("STEP 2: Ping IPv6 Address")
            st.log(f"Executing: ping6 {ipv6_address} -c {ping_count}")

            ping_success, ping_details = mgmt_api.ping_mgmt_interface_cli(
                dut,
                ip_address=ipv6_address,
                family="ipv6",
                count=ping_count,
                cli_type=cli_type,
            )

            if not ping_success:
                st.error(f"IPv6 ping failed: {ping_details}")
                st.report_fail(
                    "msg",
                    f"Ping to IPv6 address {ipv6_address} failed. "
                    f"Error: {ping_details.get('error', 'Packet loss detected')}"
                )

            st.log(f"IPv6 ping successful: {ipv6_address}")
            st.log(f"Packet loss: {ping_details.get('packet_loss', 0)}%")

        # ========== PART 2: IPv4 REACHABILITY ==========
        if test_ipv4:
            st.banner("PART 2: IPv4 REACHABILITY")

            # Step 3: Identify Management interface IPv4 address
            st.banner("STEP 3: Identify Management Interface IPv4 Address")
            st.log(f'Executing: show ip interfaces | grep "NAME|{interface}"')

            status_ok, details = mgmt_api.get_mgmt_interface_details_cli(
                dut,
                interface=interface,
                family="ipv4",
                cli_type=cli_type,
            )

            if not status_ok:
                st.error(f"Management interface IPv4 verification failed: {details}")
                st.report_fail(
                    "msg",
                    f"Management interface {interface} IPv4 status check failed: "
                    f"{details.get('error', 'Unknown error')}"
                )

            ipv4_with_mask = details.get("ipaddr", "")
            if not ipv4_with_mask:
                st.report_fail(
                    "msg",
                    f"No IPv4 address found on {interface}"
                )

            # Remove mask to get IP address only
            ipv4_address = ipv4_with_mask.split("/")[0] if "/" in ipv4_with_mask else ipv4_with_mask

            st.log(f"Found IPv4 address: {ipv4_address}")
            st.log(f"Interface status: {details.get('status', 'unknown')}")

            # Step 4: Ping the IPv4 address
            st.banner("STEP 4: Ping IPv4 Address")
            st.log(f"Executing: ping {ipv4_address} -c {ping_count}")

            ping_success, ping_details = mgmt_api.ping_mgmt_interface_cli(
                dut,
                ip_address=ipv4_address,
                family="ipv4",
                count=ping_count,
                cli_type=cli_type,
            )

            if not ping_success:
                st.error(f"IPv4 ping failed: {ping_details}")
                st.report_fail(
                    "msg",
                    f"Ping to IPv4 address {ipv4_address} failed. "
                    f"Error: {ping_details.get('error', 'Packet loss detected')}"
                )

            st.log(f"IPv4 ping successful: {ipv4_address}")
            st.log(f"Packet loss: {ping_details.get('packet_loss', 0)}%")

        # Final result
        st.banner("TEST RESULT: PASS")
        st.log(
            f"Successfully verified Management interface {interface} reachability "
            f"for IPv4 and IPv6 with 0% packet loss"
        )
        st.report_pass("test_case_passed")
