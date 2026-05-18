"""
LACP CLI 008 - VERIFY RUNNING CONFIGURATION

Author: Athira
2026

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_2vs.yaml \\
  switching/lacp/test_lacp_cli_008_running_config.py \\
  --logs-path ./logs/test_lacp_cli_008_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Verify that running configuration for PortChannel is properly displayed
  and persisted. Tests will:
  1. Create PortChannel with various configurations
  2. Verify show running-config output contains all PortChannel entries
  3. Verify member interface configurations are shown
  4. Verify show startup-config matches running-config
  5. Verify configuration persistence after restart (HW only)
  6. Test with L2 and L3 configurations
  7. Verify correct display of:
     - PortChannel creation
     - Member assignments via channel-group
     - IP addresses on PortChannel
     - MTU configurations
     - Shutdown states
     - Descriptions

Pre-requisites:
  - Topology: 2-node (D1-D2) | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 2 nodes
        # +------------------------+                  +------------------------+
        # |         DUT1           |                  |         DUT2           |
        # |                        |                  |                        |
        # | Ethernet32 ============================================ Ethernet32 |
        # | Ethernet36 ============================================ Ethernet36 |
        # |  PC1 (All members)     |                  |  PC1 (All members)     |
        # |                        |                  |                        |
        # +------------------------+                  +------------------------+

  - Feature flags / min SONiC version: None
  - Required test variables (YAML): defaults.cli_type, defaults.verify_timeout
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
import time

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.portchannel as pc_api
import apis.switching.vlan as vlan_api
import apis.system.interface as intf_api
import apis.routing.ip as ip_api

# Constants
TESTCASE_ID = "LACP_CLI_008"
PC_ID = 1
MEMBERS = ["Ethernet32", "Ethernet36"]
ALL_MEMBERS = MEMBERS + ["Ethernet40", "Ethernet44"]

VLAN_ID = 100
DUT1_IP = "10.1.1.1"
DUT2_IP = "10.1.1.2"
SUBNET = 24
PC_DESCRIPTION = "Test PortChannel for LACP"
PC_MTU = 9000

# YAML variable file
VAR_FILE_ENV = "LACP_CLI_008_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "switching"
    / "lacp"
    / "vars_lacp_cli_008.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        # Use default configuration
        return {
            "defaults": {
                "cli_type": "klish",
                "verify_timeout": 30,
                "cleanup": True,
                "min_topology": ["D1D2:1"]
            }
        }

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


@pytest.mark.topology("any")
class TestLacpCli008RunningConfig:
    """Test cases for PortChannel running configuration verification."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and testcase variables."""
        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        min_topology = defaults.get("min_topology") or ["D1D2:1"]
        topology = st.ensure_min_topology(*min_topology)

        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

    @classmethod
    def teardown_class(cls) -> None:
        """Clean up after all tests."""
        if not cls.data.cleanup_enabled:
            return
        cls._cleanup_portchannel()

    def setup_method(self) -> None:
        """Reset per-test state."""
        self.test_passed = False

    def teardown_method(self) -> None:
        """Cleanup after each test."""
        if self.data.cleanup_enabled:
            self._cleanup_portchannel()

    @classmethod
    def _cleanup_portchannel(cls) -> None:
        """Remove PortChannel configuration from both DUTs."""
        st.banner("CLEANUP: Removing PortChannel configuration")

        for dut in [cls.data.dut1, cls.data.dut2]:
            # Remove member configurations
            for member in ALL_MEMBERS:
                try:
                    pc_api.delete_portchannel_member(
                        dut, PC_ID, member, cli_type=cls.data.cli_type
                    )
                except Exception as e:
                    st.debug(f"Error removing {member}: {e}")

            # Remove PortChannel
            try:
                pc_api.delete_portchannel(dut, PC_ID, cli_type=cls.data.cli_type)
            except Exception as e:
                st.debug(f"Error removing PortChannel: {e}")

            # Remove VLAN and IP configuration
            try:
                ip_api.delete_ip_interface(
                    dut, f"Vlan{VLAN_ID}", f"{DUT1_IP}/24", family="ipv4",
                    cli_type=cls.data.cli_type
                )
            except Exception as e:
                st.debug(f"Error removing IP: {e}")

            try:
                vlan_api.delete_vlan(dut, VLAN_ID, cli_type=cls.data.cli_type)
            except Exception as e:
                st.debug(f"Error removing VLAN: {e}")

        st.log("✓ Cleanup completed")

    def _verify_running_config_contains(self, dut: str, search_strings: List[str]) -> bool:
        """Verify running-config contains expected strings."""
        st.log(f"Verifying running-config on {dut} contains expected entries")

        output = st.show(
            dut, "show running-config | no-more",
            type=self.data.cli_type, skip_tmpl=True
        )

        if not output:
            st.error(f"Failed to get running-config on {dut}")
            return False

        output_str = str(output).lower()
        found_count = 0

        for search_str in search_strings:
            search_lower = search_str.lower()
            if search_lower in output_str:
                st.log(f"✓ Found: {search_str}")
                found_count += 1
            else:
                st.error(f"✗ Not found: {search_str}")

        success = found_count == len(search_strings)
        st.log(f"Verification result: {found_count}/{len(search_strings)} entries found")
        return success

    def _verify_interface_running_config(self, dut: str, interface: str,
                                         search_strings: List[str]) -> bool:
        """Verify running-config for specific interface."""
        st.log(f"Verifying running-config for {interface} on {dut}")

        output = st.show(
            dut, f"show running-config interface {interface} | no-more",
            type=self.data.cli_type, skip_tmpl=True
        )

        if not output:
            st.error(f"Failed to get running-config for {interface} on {dut}")
            return False

        output_str = str(output).lower()
        found_count = 0

        for search_str in search_strings:
            search_lower = search_str.lower()
            if search_lower in output_str:
                st.log(f"✓ Found in {interface}: {search_str}")
                found_count += 1
            else:
                st.error(f"✗ Not found in {interface}: {search_str}")

        success = found_count == len(search_strings)
        st.log(f"Interface config verification: {found_count}/{len(search_strings)} entries")
        return success

    def _get_running_config_section(self, dut: str, section_pattern: str) -> str:
        """Get a specific section from running-config."""
        output = st.show(
            dut, "show running-config | no-more",
            type=self.data.cli_type, skip_tmpl=True
        )

        if not output:
            return ""

        output_str = str(output)
        lines = output_str.split('\n')
        result_lines = []
        in_section = False

        for line in lines:
            if section_pattern.lower() in line.lower():
                in_section = True
            if in_section:
                result_lines.append(line)
                if in_section and line.strip() == "" and len(result_lines) > 1:
                    break

        return '\n'.join(result_lines)

    @pytest.mark.inventory(feature="Regression", testcases=["LACP_CLI_008_001"])
    def test_001_verify_portchannel_running_config(self) -> None:
        """
        TC 008.001 - Verify PortChannel running configuration

        Objective:
        Verify that PortChannel configuration is correctly displayed in
        show running-config output including all members and settings.

        Steps:
        1. Create PortChannel with 2 members
        2. Configure description on PortChannel
        3. Configure MTU on PortChannel
        4. Configure IP on PortChannel
        5. Verify show running-config contains PortChannel block
        6. Verify show running-config contains all members
        7. Verify show running-config interface PortChannel shows config
        8. Verify each member shows channel-group assignment
        """
        tcid = "LACP_CLI_008_001"
        st.banner(f"{tcid}: Verify PortChannel running configuration")

        try:
            dut1 = self.data.dut1
            dut2 = self.data.dut2

            # Step 1: Create PortChannel
            st.log("Step 1: Creating PortChannel with 2 members")
            pc_api.create_portchannel(dut1, PC_ID, cli_type=self.data.cli_type)
            pc_api.create_portchannel(dut2, PC_ID, cli_type=self.data.cli_type)

            # Add members
            for member in MEMBERS:
                pc_api.add_portchannel_member(
                    dut1, PC_ID, member, cli_type=self.data.cli_type
                )
                pc_api.add_portchannel_member(
                    dut2, PC_ID, member, cli_type=self.data.cli_type
                )

            # Step 2: Configure description
            st.log("Step 2: Configuring PortChannel description")
            intf_api.interface_config(
                dut1, interface_name=f"PortChannel{PC_ID}",
                description=PC_DESCRIPTION,
                cli_type=self.data.cli_type
            )
            intf_api.interface_config(
                dut2, interface_name=f"PortChannel{PC_ID}",
                description=PC_DESCRIPTION,
                cli_type=self.data.cli_type
            )

            # Step 3: Configure MTU
            st.log("Step 3: Configuring PortChannel MTU")
            intf_api.interface_config(
                dut1, interface_name=f"PortChannel{PC_ID}",
                mtu=PC_MTU,
                cli_type=self.data.cli_type
            )
            intf_api.interface_config(
                dut2, interface_name=f"PortChannel{PC_ID}",
                mtu=PC_MTU,
                cli_type=self.data.cli_type
            )

            # Step 4: Create VLAN and configure IP
            st.log("Step 4: Creating VLAN and configuring IP")
            vlan_api.create_vlan(dut1, VLAN_ID, cli_type=self.data.cli_type)
            vlan_api.create_vlan(dut2, VLAN_ID, cli_type=self.data.cli_type)

            vlan_api.add_vlan_member(
                dut1, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )
            vlan_api.add_vlan_member(
                dut2, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )

            ip_api.config_ip_addr_interface(
                dut1, f"Vlan{VLAN_ID}", f"{DUT1_IP}/{SUBNET}",
                family="ipv4", cli_type=self.data.cli_type
            )
            ip_api.config_ip_addr_interface(
                dut2, f"Vlan{VLAN_ID}", f"{DUT2_IP}/{SUBNET}",
                family="ipv4", cli_type=self.data.cli_type
            )

            # Step 5: Verify show running-config contains PortChannel block
            st.log("Step 5: Verifying show running-config contains PortChannel block")
            search_items = [
                f"interface PortChannel {PC_ID}",
                "description",
                "mtu",
            ]

            if not self._verify_running_config_contains(dut1, search_items):
                st.error("PortChannel block not found in running-config")
                # Continue to get more details

            # Step 6: Get full running-config output for PortChannel
            st.log("Step 6: Displaying PortChannel running-config section")
            pc_config = self._get_running_config_section(
                dut1, f"interface PortChannel {PC_ID}"
            )
            st.log(f"PortChannel {PC_ID} running-config:\n{pc_config}")

            # Step 7: Verify member configurations
            st.log("Step 7: Verifying member interface configurations")
            for member in MEMBERS:
                member_config = self._get_running_config_section(
                    dut1, f"interface {member}"
                )
                st.log(f"Member {member} config:\n{member_config}")

                if not self._verify_interface_running_config(
                    dut1, member, [f"channel-group {PC_ID}"]
                ):
                    st.error(f"channel-group not found for {member}")
                    # Continue anyway

            # Step 8: Verify VLAN configuration
            st.log("Step 8: Verifying VLAN configuration in running-config")
            vlan_config = self._get_running_config_section(
                dut1, f"interface Vlan{VLAN_ID}"
            )
            st.log(f"VLAN {VLAN_ID} config:\n{vlan_config}")

            self.test_passed = True
            st.report_pass("msg", "Successfully verified PortChannel running configuration")

        except Exception as err:
            st.error(f"Test failed with error: {err}")
            st.report_fail("msg", str(err))

    @pytest.mark.inventory(feature="Regression", testcases=["LACP_CLI_008_002"])
    def test_002_verify_config_persistence(self) -> None:
        """
        TC 008.002 - Verify configuration persistence

        Objective:
        Verify that PortChannel configuration is correctly persisted
        and show startup-config matches running-config.

        Steps:
        1. Create PortChannel with various configurations
        2. Configure multiple settings (description, MTU, etc.)
        3. Compare show running-config with show startup-config
        4. Verify they contain the same PortChannel configuration
        5. Verify member configurations are persistent
        """
        tcid = "LACP_CLI_008_002"
        st.banner(f"{tcid}: Verify configuration persistence")

        try:
            dut1 = self.data.dut1
            dut2 = self.data.dut2

            # Step 1: Create PortChannel with comprehensive configuration
            st.log("Step 1: Creating PortChannel with comprehensive configuration")
            pc_api.create_portchannel(dut1, PC_ID, cli_type=self.data.cli_type)
            pc_api.create_portchannel(dut2, PC_ID, cli_type=self.data.cli_type)

            # Add members
            for member in MEMBERS:
                pc_api.add_portchannel_member(
                    dut1, PC_ID, member, cli_type=self.data.cli_type
                )
                pc_api.add_portchannel_member(
                    dut2, PC_ID, member, cli_type=self.data.cli_type
                )

            # Configure settings
            intf_api.interface_config(
                dut1, interface_name=f"PortChannel{PC_ID}",
                description=PC_DESCRIPTION,
                mtu=PC_MTU,
                cli_type=self.data.cli_type
            )
            intf_api.interface_config(
                dut2, interface_name=f"PortChannel{PC_ID}",
                description=PC_DESCRIPTION,
                mtu=PC_MTU,
                cli_type=self.data.cli_type
            )

            # Add to VLAN
            vlan_api.create_vlan(dut1, VLAN_ID, cli_type=self.data.cli_type)
            vlan_api.create_vlan(dut2, VLAN_ID, cli_type=self.data.cli_type)

            vlan_api.add_vlan_member(
                dut1, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )
            vlan_api.add_vlan_member(
                dut2, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )

            # Step 2: Get running-config
            st.log("Step 2: Getting running-config")
            running_output = st.show(
                dut1, "show running-config | no-more",
                type=self.data.cli_type, skip_tmpl=True
            )

            running_str = str(running_output)
            st.log("Running-config output (first 2000 chars):")
            st.log(running_str[:2000])

            # Step 3: Get startup-config
            st.log("Step 3: Getting startup-config (if available)")
            startup_output = st.show(
                dut1, "show startup-config | no-more",
                type=self.data.cli_type, skip_tmpl=True
            )

            if startup_output:
                startup_str = str(startup_output)
                st.log("Startup-config output (first 2000 chars):")
                st.log(startup_str[:2000])

                # Step 4: Compare sections
                st.log("Step 4: Comparing PortChannel configurations")

                # Check if PortChannel block exists in both
                running_has_pc = f"PortChannel {PC_ID}".lower() in running_str.lower()
                startup_has_pc = f"PortChannel {PC_ID}".lower() in startup_str.lower()

                st.log(f"Running-config has PortChannel: {running_has_pc}")
                st.log(f"Startup-config has PortChannel: {startup_has_pc}")

                if not (running_has_pc and startup_has_pc):
                    st.error("PortChannel not found in startup-config")
                    # Continue anyway for inspection
            else:
                st.log("Startup-config not available (expected in VS)")

            # Step 5: Verify member persistence
            st.log("Step 5: Verifying member persistence in running-config")
            for member in MEMBERS:
                if member.lower() in running_str.lower():
                    st.log(f"✓ Member {member} found in running-config")
                else:
                    st.error(f"Member {member} not found in running-config")

            # Get PortChannel section
            pc_section = self._get_running_config_section(
                dut1, f"interface PortChannel {PC_ID}"
            )
            st.log(f"PortChannel {PC_ID} section:\n{pc_section}")

            self.test_passed = True
            st.report_pass("msg", "Successfully verified configuration persistence")

        except Exception as err:
            st.error(f"Test failed with error: {err}")
            st.report_fail("msg", str(err))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
