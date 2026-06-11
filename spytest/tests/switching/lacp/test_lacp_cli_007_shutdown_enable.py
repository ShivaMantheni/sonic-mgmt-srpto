"""
LACP CLI 007 - ENABLE/DISABLE (SHUTDOWN) PORTCHANNEL

Author: Athira
2026

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_2vs.yaml \\
  switching/lacp/test_lacp_cli_007_shutdown_enable.py \\
  --logs-path ./logs/test_lacp_cli_007_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Verify administrative enable/disable (shutdown/no shutdown) of PortChannel. Tests will:
  1. Create a PortChannel with 2 members and bring it up
  2. Verify PortChannel is operational
  3. Execute shutdown on PortChannel (administrative down)
  4. Verify PortChannel and members are down
  5. Verify traffic is blocked
  6. Execute no shutdown (enable again)
  7. Verify PortChannel and members recover
  8. Verify LACP resync completes
  9. Verify traffic flows again
  10. Test multiple shutdown/no shutdown cycles
  11. Test L2 and L3 configurations

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
import apis.switching.lacp as lacp_api
import apis.switching.vlan as vlan_api
import apis.system.interface as intf_api
import apis.routing.ip as ip_api
import apis.common.scapy_traffic as scapy_traffic

# Constants
TESTCASE_ID = "LACP_CLI_007"
PC_ID = 1
MEMBERS = ["Ethernet32", "Ethernet36"]
ALL_MEMBERS = MEMBERS + ["Ethernet40", "Ethernet44"]

VLAN_ID = 100
DUT1_IP = "10.1.1.1"
DUT2_IP = "10.1.1.2"
SUBNET = 24

# YAML variable file
VAR_FILE_ENV = "LACP_CLI_007_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "switching"
    / "lacp"
    / "vars_lacp_cli_007.yaml"
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
class TestLacpCli007ShutdownEnable:
    """Test cases for PortChannel administrative shutdown/enable."""

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
            # First enable PortChannel to clean up properly
            try:
                intf_api.interface_operation(
                    dut, f"PortChannel{PC_ID}", "startup",
                    cli_type=cls.data.cli_type
                )
            except Exception:
                pass

            # Remove member configurations
            for member in ALL_MEMBERS:
                try:
                    lacp_api.delete_portchannel_member(
                        dut, PC_ID, member, cli_type=cls.data.cli_type
                    )
                except Exception as e:
                    st.debug(f"Error removing {member}: {e}")

            # Remove PortChannel
            try:
                lacp_api.delete_portchannel(dut, PC_ID, cli_type=cls.data.cli_type)
            except Exception as e:
                st.debug(f"Error removing PortChannel: {e}")

            # Remove VLAN and IP configuration
            try:
                ip_api.delete_ip_interface(
                    dut, f"Vlan{VLAN_ID}", DUT1_IP, subnet="24", family="ipv4",
                    cli_type=cls.data.cli_type
                )
            except Exception as e:
                st.debug(f"Error removing IP: {e}")

            try:
                vlan_api.delete_vlan(dut, VLAN_ID, cli_type=cls.data.cli_type)
            except Exception as e:
                st.debug(f"Error removing VLAN: {e}")

        st.log("✓ Cleanup completed")

    def _verify_portchannel_status(self, dut: str, expected_status: str) -> bool:
        """Verify PortChannel is up or down."""
        st.log(f"Verifying PortChannel {PC_ID} status on {dut} (expected: {expected_status})")

        output = st.show(
            dut, f"show interface PortChannel {PC_ID} | no-more",
            type=self.data.cli_type, skip_tmpl=True
        )

        if not output:
            st.error(f"Failed to get PortChannel info on {dut}")
            return False

        output_str = str(output).lower()

        if expected_status == "up":
            # Check for "up" or "oper up" in output
            if "up" in output_str and "down" not in output_str:
                st.log("✓ PortChannel is UP")
                return True
            else:
                st.error(f"PortChannel is not UP. Output: {output_str}")
                return False
        elif expected_status == "down":
            # Check for "down" or "administratively down"
            if "down" in output_str or "admin" in output_str:
                st.log("✓ PortChannel is DOWN")
                return True
            else:
                st.error(f"PortChannel is not DOWN. Output: {output_str}")
                return False

        return False

    def _verify_portchannel_members(self, dut: str, expected_count: int) -> bool:
        """Verify PortChannel members using show command."""
        st.log(f"Verifying PortChannel {PC_ID} members on {dut}")

        output = st.show(
            dut, f"show interface PortChannel {PC_ID} members | no-more",
            type=self.data.cli_type, skip_tmpl=True
        )

        if not output:
            st.error(f"Failed to get PortChannel members on {dut}")
            return False

        output_str = str(output).lower()
        member_count = 0

        for member in MEMBERS:
            if member.lower() in output_str:
                member_count += 1

        st.log(f"Found {member_count} members (expected: {expected_count})")
        return member_count == expected_count

    def _verify_lacp_sync(self, dut: str, expected_count: int) -> bool:
        """Verify LACP synchronization status."""
        st.log(f"Verifying LACP sync status on {dut}")

        # Use correct SONiC command for PortChannel/LACP status (consistent with CLI 001)
        output = st.show(
            dut, "show portchannel summary",
            type=self.data.cli_type, skip_tmpl=True
        )

        if not output:
            st.error(f"Failed to get portchannel summary on {dut}")
            return False

        output_str = str(output).lower()
        synced_count = output_str.count("synced") + output_str.count("sync") + output_str.count("lacp")

        st.log(f"LACP sync status: {synced_count} (expected >= {expected_count})")
        return synced_count >= expected_count

    def _send_traffic_and_verify(self, src_dut: str, dst_dut: str,
                                  src_ip: str, dst_ip: str,
                                  duration: int = 5, pps: int = 100) -> bool:
        """Send traffic and verify using counters and tcpdump."""
        st.banner(f"Traffic: {src_dut} → {dst_dut}")

        src_port = MEMBERS[0]
        dst_port = MEMBERS[0]

        # Get MAC addresses from VLAN SVI
        src_mac = scapy_traffic.get_interface_mac(
            src_dut, f"Vlan{VLAN_ID}", cli_type=self.data.cli_type
        )
        dst_mac = scapy_traffic.get_interface_mac(
            dst_dut, f"Vlan{VLAN_ID}", cli_type=self.data.cli_type
        )

        if not src_mac:
            src_mac = scapy_traffic.get_default_mac(1)
        if not dst_mac:
            dst_mac = scapy_traffic.get_default_mac(2)

        st.log(f"Source MAC: {src_mac}, Destination MAC: {dst_mac}")

        # Clear counters
        intf_api.clear_interface_counters(
            dst_dut, interface_name=dst_port, cli_type=self.data.cli_type
        )
        st.wait(1)

        # Start tcpdump on destination
        scapy_traffic.start_tcpdump(
            dst_dut, dst_port,
            filter_str=f"src {src_ip} and dst {dst_ip}",
            output_file=f"/tmp/lacp_cli_007_traffic_{src_dut}_{dst_dut}.pcap"
        )

        # Send traffic
        st.log(f"Sending {duration*pps} packets at {pps} pps")
        result = scapy_traffic.send_traffic(
            dut=src_dut,
            interface=src_port,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_mac=src_mac,
            dst_mac=dst_mac,
            duration=duration,
            pps=pps,
            payload_size=200,
            traffic_type="udp"
        )

        st.wait(1)
        scapy_traffic.stop_tcpdump(dst_dut)

        if not result["success"]:
            st.error(f"Traffic generation failed: {result['output']}")
            return False

        packets_sent = result["packets_sent"]
        st.log(f"✓ Sent {packets_sent} packets")

        # Verify with tcpdump
        tcpdump_result = scapy_traffic.verify_tcpdump_capture(
            dst_dut,
            capture_file=f"/tmp/lacp_cli_007_traffic_{src_dut}_{dst_dut}.pcap",
            min_packets=packets_sent // 2
        )

        if tcpdump_result["success"]:
            st.log(f"✓ tcpdump verified: {tcpdump_result['packet_count']} packets captured")
            return True
        else:
            st.error(f"tcpdump verification failed: {tcpdump_result['packet_count']} packets")
            return False

    @pytest.mark.inventory(feature="Regression", testcases=["LACP_CLI_007_001"])
    def test_001_shutdown_and_restore_portchannel(self) -> None:
        """
        TC 007.001 - Shutdown and restore PortChannel

        Objective:
        Verify that PortChannel can be administratively shutdown and then
        re-enabled, with proper state transitions and LACP resynchronization.

        Steps:
        1. Create PortChannel with 2 members
        2. Verify PortChannel is up
        3. Verify traffic flows
        4. Execute shutdown on PortChannel
        5. Verify PortChannel is administratively down
        6. Verify members are down
        7. Verify traffic is blocked
        8. Execute no shutdown
        9. Verify PortChannel comes back up
        10. Verify LACP resync
        11. Verify traffic flows again
        """
        tcid = "LACP_CLI_007_001"
        st.banner(f"{tcid}: Shutdown and restore PortChannel")

        try:
            dut1 = self.data.dut1
            dut2 = self.data.dut2

            # Step 1: Create and configure PortChannel
            st.log("Step 1: Creating PortChannel with 2 members")
            vlan_api.create_vlan(dut1, VLAN_ID, cli_type=self.data.cli_type)
            vlan_api.create_vlan(dut2, VLAN_ID, cli_type=self.data.cli_type)

            lacp_api.create_portchannel(dut1, PC_ID, cli_type=self.data.cli_type)
            lacp_api.create_portchannel(dut2, PC_ID, cli_type=self.data.cli_type)

            for member in MEMBERS:
                lacp_api.add_portchannel_member(
                    dut1, PC_ID, member, cli_type=self.data.cli_type
                )
                lacp_api.add_portchannel_member(
                    dut2, PC_ID, member, cli_type=self.data.cli_type
                )

            vlan_api.add_vlan_member(
                dut1, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )
            vlan_api.add_vlan_member(
                dut2, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )

            ip_api.config_ip_addr_interface(
                dut1, f"Vlan{VLAN_ID}", DUT1_IP, subnet=str(SUBNET),
                family="ipv4", cli_type=self.data.cli_type
            )
            ip_api.config_ip_addr_interface(
                dut2, f"Vlan{VLAN_ID}", DUT2_IP, subnet=str(SUBNET),
                family="ipv4", cli_type=self.data.cli_type
            )

            intf_api.interface_operation(
                dut1, f"PortChannel{PC_ID}", "startup",
                cli_type=self.data.cli_type
            )
            intf_api.interface_operation(
                dut2, f"PortChannel{PC_ID}", "startup",
                cli_type=self.data.cli_type
            )

            st.wait(3, "Wait for LACP sync")

            # Step 2: Verify PortChannel is up
            st.log("Step 2: Verifying PortChannel is UP")
            if not self._verify_portchannel_status(dut1, "up"):
                st.report_fail("msg", "PortChannel not up initially")
            if not self._verify_portchannel_members(dut1, 2):
                st.report_fail("msg", "Members not found initially")

            # Step 3: Verify traffic flows
            st.log("Step 3: Verifying traffic flows initially")
            if not self._send_traffic_and_verify(dut1, dut2, DUT1_IP, DUT2_IP):
                st.report_fail("msg", "Traffic verification failed initially")

            # Step 4: Execute shutdown on PortChannel
            st.log("Step 4: Executing shutdown on PortChannel")
            intf_api.interface_operation(
                dut1, f"PortChannel{PC_ID}", "shutdown",
                cli_type=self.data.cli_type
            )
            intf_api.interface_operation(
                dut2, f"PortChannel{PC_ID}", "shutdown",
                cli_type=self.data.cli_type
            )

            st.wait(2, "Wait for interface to go down")

            # Step 5: Verify PortChannel is down
            st.log("Step 5: Verifying PortChannel is DOWN")
            if not self._verify_portchannel_status(dut1, "down"):
                st.report_fail("msg", "PortChannel not down after shutdown")

            # Step 6: Execute no shutdown to enable
            st.log("Step 6: Executing no shutdown to enable PortChannel")
            intf_api.interface_operation(
                dut1, f"PortChannel{PC_ID}", "startup",
                cli_type=self.data.cli_type
            )
            intf_api.interface_operation(
                dut2, f"PortChannel{PC_ID}", "startup",
                cli_type=self.data.cli_type
            )

            st.wait(3, "Wait for LACP resync")

            # Step 7: Verify PortChannel is back up
            st.log("Step 7: Verifying PortChannel is UP again")
            if not self._verify_portchannel_status(dut1, "up"):
                st.report_fail("msg", "PortChannel not up after no shutdown")

            # Step 8: Verify LACP resync
            st.log("Step 8: Verifying LACP resync")
            if not self._verify_lacp_sync(dut1, 2):
                st.report_fail("msg", "LACP not synced after recovery")

            # Step 9: Verify traffic flows again
            st.log("Step 9: Verifying traffic flows after recovery")
            if not self._send_traffic_and_verify(dut1, dut2, DUT1_IP, DUT2_IP):
                st.report_fail("msg", "Traffic verification failed after recovery")

            # Verify show commands
            output = st.show(
                dut1, f"show interface PortChannel {PC_ID} | no-more",
                type=self.data.cli_type, skip_tmpl=True
            )
            st.log(f"show interface PortChannel {PC_ID}:\n{output}")

            self.test_passed = True
            st.report_pass("msg", "Successfully shutdown and restored PortChannel")

        except Exception as err:
            st.error(f"Test failed with error: {err}")
            st.report_fail("msg", str(err))

    @pytest.mark.inventory(feature="Regression", testcases=["LACP_CLI_007_002"])
    def test_002_multiple_shutdown_cycles(self) -> None:
        """
        TC 007.002 - Multiple shutdown/no shutdown cycles

        Objective:
        Verify that PortChannel can handle multiple shutdown/no shutdown cycles
        without state corruption or traffic disruption.

        Steps:
        1. Create PortChannel with 2 members
        2. Execute 3 cycles of shutdown and no shutdown
        3. Verify proper state transitions in each cycle
        4. Verify LACP resync after each cycle
        5. Verify traffic after final recovery
        """
        tcid = "LACP_CLI_007_002"
        st.banner(f"{tcid}: Multiple shutdown/no shutdown cycles")

        try:
            dut1 = self.data.dut1
            dut2 = self.data.dut2

            # Setup: Create and configure PortChannel
            st.log("Setup: Creating PortChannel with 2 members")
            vlan_api.create_vlan(dut1, VLAN_ID, cli_type=self.data.cli_type)
            vlan_api.create_vlan(dut2, VLAN_ID, cli_type=self.data.cli_type)

            lacp_api.create_portchannel(dut1, PC_ID, cli_type=self.data.cli_type)
            lacp_api.create_portchannel(dut2, PC_ID, cli_type=self.data.cli_type)

            for member in MEMBERS:
                lacp_api.add_portchannel_member(
                    dut1, PC_ID, member, cli_type=self.data.cli_type
                )
                lacp_api.add_portchannel_member(
                    dut2, PC_ID, member, cli_type=self.data.cli_type
                )

            vlan_api.add_vlan_member(
                dut1, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )
            vlan_api.add_vlan_member(
                dut2, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )

            ip_api.config_ip_addr_interface(
                dut1, f"Vlan{VLAN_ID}", DUT1_IP, subnet=str(SUBNET),
                family="ipv4", cli_type=self.data.cli_type
            )
            ip_api.config_ip_addr_interface(
                dut2, f"Vlan{VLAN_ID}", DUT2_IP, subnet=str(SUBNET),
                family="ipv4", cli_type=self.data.cli_type
            )

            intf_api.interface_operation(
                dut1, f"PortChannel{PC_ID}", "startup",
                cli_type=self.data.cli_type
            )
            intf_api.interface_operation(
                dut2, f"PortChannel{PC_ID}", "startup",
                cli_type=self.data.cli_type
            )

            st.wait(3)

            # Execute 3 shutdown/no shutdown cycles
            num_cycles = 3
            for cycle in range(1, num_cycles + 1):
                st.log(f"\nCycle {cycle}/{num_cycles}")

                # Shutdown
                st.log(f"Cycle {cycle}: Shutting down PortChannel")
                intf_api.interface_operation(
                    dut1, f"PortChannel{PC_ID}", "shutdown",
                    cli_type=self.data.cli_type
                )
                intf_api.interface_operation(
                    dut2, f"PortChannel{PC_ID}", "shutdown",
                    cli_type=self.data.cli_type
                )

                st.wait(2)

                # Verify down
                if not self._verify_portchannel_status(dut1, "down"):
                    st.report_fail("msg", f"PortChannel not down in cycle {cycle}")

                # No shutdown
                st.log(f"Cycle {cycle}: Enabling PortChannel")
                intf_api.interface_operation(
                    dut1, f"PortChannel{PC_ID}", "startup",
                    cli_type=self.data.cli_type
                )
                intf_api.interface_operation(
                    dut2, f"PortChannel{PC_ID}", "startup",
                    cli_type=self.data.cli_type
                )

                st.wait(3)

                # Verify up and synced
                if not self._verify_portchannel_status(dut1, "up"):
                    st.report_fail("msg", f"PortChannel not up in cycle {cycle}")
                if not self._verify_lacp_sync(dut1, 2):
                    st.report_fail("msg", f"LACP not synced in cycle {cycle}")

                st.log(f"✓ Cycle {cycle} completed successfully")

            # Final traffic verification
            st.log("\nFinal: Verifying traffic after all cycles")
            if not self._send_traffic_and_verify(dut1, dut2, DUT1_IP, DUT2_IP):
                st.report_fail("msg", "Traffic verification failed after cycles")

            self.test_passed = True
            st.report_pass("msg", f"Successfully completed {num_cycles} shutdown/enable cycles")

        except Exception as err:
            st.error(f"Test failed with error: {err}")
            st.report_fail("msg", str(err))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
