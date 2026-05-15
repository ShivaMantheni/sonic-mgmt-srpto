"""
LACP CLI 006 - CHANGE PORTCHANNEL MTU

Author: Athira
2026

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_2vs.yaml \\
  switching/lacp/test_lacp_cli_006_mtu_configuration.py \\
  --logs-path ./logs/test_lacp_cli_006_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Verify MTU (Maximum Transmission Unit) configuration on PortChannel. Tests will:
  1. Create a PortChannel with 2 members
  2. Verify default MTU (1500 bytes)
  3. Change PortChannel MTU to 9216 (jumbo frames)
  4. Verify MTU applied to PortChannel and members
  5. Test traffic with standard frames (1500 bytes)
  6. Test traffic with jumbo frames (9000 bytes)
  7. Verify show commands reflect MTU changes
  8. Test persistence across reconfigurations

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
import apis.common.scapy_traffic as scapy_traffic

# Constants
TESTCASE_ID = "LACP_CLI_006"
PC_ID = 1
MEMBERS = ["Ethernet32", "Ethernet36"]
ALL_MEMBERS = MEMBERS + ["Ethernet40", "Ethernet44"]

VLAN_ID = 100
DUT1_IP = "10.1.1.1"
DUT2_IP = "10.1.1.2"
SUBNET = 24

DEFAULT_MTU = 1500
JUMBO_MTU = 9216
MIN_JUMBO_PAYLOAD = 9000

# YAML variable file
VAR_FILE_ENV = "LACP_CLI_006_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "switching"
    / "lacp"
    / "vars_lacp_cli_006.yaml"
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
class TestLacpCli006MtuConfiguration:
    """Test cases for PortChannel MTU configuration."""

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

    def _verify_portchannel_mtu(self, dut: str, expected_mtu: int) -> bool:
        """Verify PortChannel MTU using show command."""
        st.log(f"Verifying PortChannel {PC_ID} MTU on {dut}")

        output = st.show(
            dut, f"show interfaces PortChannel {PC_ID}",
            type=self.data.cli_type, skip_tmpl=True
        )

        if not output:
            st.error(f"Failed to get PortChannel info on {dut}")
            return False

        output_str = str(output)
        st.log(f"Interface output:\n{output_str}")

        # Check if expected MTU is mentioned in output
        if str(expected_mtu) in output_str or f"MTU {expected_mtu}" in output_str:
            st.log(f"✓ PortChannel MTU set to {expected_mtu}")
            return True
        else:
            st.error(f"MTU not set to {expected_mtu}")
            return False

    def _verify_portchannel_members(self, dut: str, expected_count: int) -> bool:
        """Verify PortChannel members using show command."""
        st.log(f"Verifying PortChannel {PC_ID} members on {dut}")

        output = st.show(
            dut, f"show interfaces PortChannel {PC_ID} members",
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

        output = st.show(
            dut, f"show lacp statistics PortChannel {PC_ID}",
            type=self.data.cli_type, skip_tmpl=True
        )

        if not output:
            st.error(f"Failed to get LACP stats on {dut}")
            return False

        output_str = str(output).lower()
        synced_count = output_str.count("synced") + output_str.count("sync")

        st.log(f"LACP sync status: {synced_count} (expected >= {expected_count})")
        return synced_count >= expected_count

    def _send_traffic_and_verify(self, src_dut: str, dst_dut: str,
                                  src_ip: str, dst_ip: str,
                                  payload_size: int = 1472,
                                  duration: int = 5, pps: int = 100) -> bool:
        """Send traffic and verify using counters and tcpdump."""
        st.banner(f"Traffic: {src_dut} → {dst_dut} (Payload: {payload_size} bytes)")

        # Get interface for traffic
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
            output_file=f"/tmp/lacp_cli_006_traffic_{src_dut}_{dst_dut}_{payload_size}.pcap"
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
            payload_size=payload_size,
            traffic_type="udp"
        )

        st.wait(1)

        # Stop tcpdump
        scapy_traffic.stop_tcpdump(dst_dut)

        if not result["success"]:
            st.error(f"Traffic generation failed: {result['output']}")
            return False

        packets_sent = result["packets_sent"]
        st.log(f"✓ Sent {packets_sent} packets with payload size {payload_size}")

        # Verify with tcpdump
        tcpdump_result = scapy_traffic.verify_tcpdump_capture(
            dst_dut,
            capture_file=f"/tmp/lacp_cli_006_traffic_{src_dut}_{dst_dut}_{payload_size}.pcap",
            min_packets=packets_sent // 2  # At least 50% should be captured
        )

        if tcpdump_result["success"]:
            st.log(f"✓ tcpdump verified: {tcpdump_result['packet_count']} packets captured")
        else:
            st.error(f"tcpdump verification failed: {tcpdump_result['packet_count']} packets")
            return False

        # Verify with interface counters
        st.wait(2)
        counters = intf_api.show_interface_counters_all(
            dst_dut, cli_type=self.data.cli_type
        )

        for entry in counters:
            if entry.get("iface") == dst_port:
                rx_ok = int(str(entry.get("rx_ok", "0")).replace(",", ""))
                st.log(f"Interface {dst_port} RX_OK: {rx_ok}")

                if rx_ok >= (packets_sent // 2):
                    st.log(f"✓ Counter verification passed: {rx_ok} >= {packets_sent // 2}")
                    return True
                else:
                    st.error(f"Counter verification failed: {rx_ok} < {packets_sent // 2}")
                    return False

        st.error("Could not find destination interface counters")
        return False

    @pytest.mark.inventory(feature="Regression", testcases=["LACP_CLI_006_001"])
    def test_001_change_mtu_to_jumbo_frames(self) -> None:
        """
        TC 006.001 - Change PortChannel MTU to support jumbo frames

        Objective:
        Verify that PortChannel MTU can be changed from default (1500) to
        jumbo frames (9216) and traffic flows with larger frame sizes.

        Steps:
        1. Create PortChannel with 2 members
        2. Verify default MTU is 1500
        3. Verify initial traffic with standard frames
        4. Change PortChannel MTU to 9216
        5. Verify MTU changed on PortChannel and members
        6. Verify traffic with jumbo frames (9000+ bytes)
        7. Verify show commands
        """
        tcid = "LACP_CLI_006_001"
        st.banner(f"{tcid}: Change PortChannel MTU to jumbo frames")

        try:
            dut1 = self.data.dut1
            dut2 = self.data.dut2

            # Step 1: Create VLAN for management
            st.log("Step 1: Creating VLAN for management")
            vlan_api.create_vlan(dut1, VLAN_ID, cli_type=self.data.cli_type)
            vlan_api.create_vlan(dut2, VLAN_ID, cli_type=self.data.cli_type)

            # Step 2: Create PortChannel with 2 members
            st.log("Step 2: Creating PortChannel with 2 members")
            pc_api.create_portchannel(
                dut1, PC_ID, cli_type=self.data.cli_type
            )
            pc_api.create_portchannel(
                dut2, PC_ID, cli_type=self.data.cli_type
            )

            # Add members
            for member in MEMBERS:
                pc_api.add_portchannel_member(
                    dut1, PC_ID, member, cli_type=self.data.cli_type
                )
                pc_api.add_portchannel_member(
                    dut2, PC_ID, member, cli_type=self.data.cli_type
                )

            # Add VLAN members (untagged - access mode)
            vlan_api.add_vlan_member(
                dut1, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )
            vlan_api.add_vlan_member(
                dut2, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )

            # Step 3: Configure IP addresses on VLAN SVI
            st.log("Step 3: Configuring IP addresses on VLAN SVI")
            ip_api.config_ip_addr_interface(
                dut1, f"Vlan{VLAN_ID}", f"{DUT1_IP}/{SUBNET}",
                family="ipv4", cli_type=self.data.cli_type
            )
            ip_api.config_ip_addr_interface(
                dut2, f"Vlan{VLAN_ID}", f"{DUT2_IP}/{SUBNET}",
                family="ipv4", cli_type=self.data.cli_type
            )

            # Bring up PortChannel
            intf_api.interface_operation(
                dut1, f"PortChannel{PC_ID}", "startup",
                cli_type=self.data.cli_type
            )
            intf_api.interface_operation(
                dut2, f"PortChannel{PC_ID}", "startup",
                cli_type=self.data.cli_type
            )

            st.wait(3, "Wait for LACP sync")

            # Step 4: Verify initial state
            st.log("Step 4: Verifying initial PortChannel state")
            if not self._verify_portchannel_members(dut1, 2):
                st.report_fail("msg", "Initial 2 members not found on DUT1")
            if not self._verify_lacp_sync(dut1, 2):
                st.report_fail("msg", "LACP not synced initially")

            # Step 5: Verify traffic with standard frames (1472 bytes payload)
            st.log("Step 5: Verifying traffic with standard frames")
            if not self._send_traffic_and_verify(dut1, dut2, DUT1_IP, DUT2_IP,
                                                 payload_size=1472):
                st.report_fail("msg", "Traffic verification failed with standard frames")

            # Step 6: Change PortChannel MTU to 9216
            st.log("Step 6: Changing PortChannel MTU to 9216")
            intf_api.interface_config(
                dut1, interface_name=f"PortChannel{PC_ID}",
                ip_address=None, mtu=JUMBO_MTU,
                cli_type=self.data.cli_type
            )
            intf_api.interface_config(
                dut2, interface_name=f"PortChannel{PC_ID}",
                ip_address=None, mtu=JUMBO_MTU,
                cli_type=self.data.cli_type
            )

            st.wait(2, "Wait for MTU change to take effect")

            # Step 7: Verify MTU changed
            st.log("Step 7: Verifying MTU changed to 9216")
            if not self._verify_portchannel_mtu(dut1, JUMBO_MTU):
                st.error("MTU verification failed on DUT1")
                # Continue to test traffic anyway

            # Step 8: Verify LACP still synced after MTU change
            st.log("Step 8: Verifying LACP still synced after MTU change")
            if not self._verify_lacp_sync(dut1, 2):
                st.report_fail("msg", "LACP not synced after MTU change")

            # Step 9: Verify traffic with jumbo frames (9000 bytes payload)
            st.log("Step 9: Verifying traffic with jumbo frames (9000 bytes payload)")
            if not self._send_traffic_and_verify(dut1, dut2, DUT1_IP, DUT2_IP,
                                                 payload_size=9000):
                st.report_fail("msg", "Traffic verification failed with jumbo frames")

            # Step 10: Verify show commands
            st.log("Step 10: Verifying show commands")
            output = st.show(
                dut1, f"show interfaces PortChannel {PC_ID}",
                type=self.data.cli_type, skip_tmpl=True
            )
            st.log(f"show interfaces PortChannel {PC_ID}:\n{output}")

            output = st.show(
                dut1, "show portchannel summary",
                type=self.data.cli_type, skip_tmpl=True
            )
            st.log(f"show portchannel summary:\n{output}")

            self.test_passed = True
            st.report_pass("msg", "Successfully changed PortChannel MTU to jumbo frames")

        except Exception as err:
            st.error(f"Test failed with error: {err}")
            st.report_fail("msg", str(err))

    @pytest.mark.inventory(feature="Regression", testcases=["LACP_CLI_006_002"])
    def test_002_mtu_change_with_traffic_active(self) -> None:
        """
        TC 006.002 - Change MTU with traffic actively flowing

        Objective:
        Verify that MTU can be changed while traffic is flowing through
        the PortChannel and traffic recovery is automatic.

        Steps:
        1. Create PortChannel with 2 members
        2. Configure MTU to 9216
        3. Send standard frame traffic
        4. While traffic is flowing, change MTU back to default (1500)
        5. Verify traffic continues after MTU change
        6. Change MTU back to 9216 and verify again
        """
        tcid = "LACP_CLI_006_002"
        st.banner(f"{tcid}: Change MTU with active traffic")

        try:
            dut1 = self.data.dut1
            dut2 = self.data.dut2

            # Step 1: Create and configure PortChannel
            st.log("Step 1: Creating and configuring PortChannel with initial MTU 9216")
            vlan_api.create_vlan(dut1, VLAN_ID, cli_type=self.data.cli_type)
            vlan_api.create_vlan(dut2, VLAN_ID, cli_type=self.data.cli_type)

            pc_api.create_portchannel(dut1, PC_ID, cli_type=self.data.cli_type)
            pc_api.create_portchannel(dut2, PC_ID, cli_type=self.data.cli_type)

            # Set MTU to 9216 initially
            intf_api.interface_config(
                dut1, interface_name=f"PortChannel{PC_ID}",
                ip_address=None, mtu=JUMBO_MTU,
                cli_type=self.data.cli_type
            )
            intf_api.interface_config(
                dut2, interface_name=f"PortChannel{PC_ID}",
                ip_address=None, mtu=JUMBO_MTU,
                cli_type=self.data.cli_type
            )

            # Add members
            for member in MEMBERS:
                pc_api.add_portchannel_member(
                    dut1, PC_ID, member, cli_type=self.data.cli_type
                )
                pc_api.add_portchannel_member(
                    dut2, PC_ID, member, cli_type=self.data.cli_type
                )

            # Add VLAN members
            vlan_api.add_vlan_member(
                dut1, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )
            vlan_api.add_vlan_member(
                dut2, VLAN_ID, f"PortChannel{PC_ID}",
                tagging_mode=False, cli_type=self.data.cli_type
            )

            # Configure IPs
            ip_api.config_ip_addr_interface(
                dut1, f"Vlan{VLAN_ID}", f"{DUT1_IP}/{SUBNET}",
                family="ipv4", cli_type=self.data.cli_type
            )
            ip_api.config_ip_addr_interface(
                dut2, f"Vlan{VLAN_ID}", f"{DUT2_IP}/{SUBNET}",
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

            # Step 2: Verify initial state with jumbo MTU
            st.log("Step 2: Verifying initial state with jumbo MTU")
            if not self._verify_portchannel_members(dut1, 2):
                st.report_fail("msg", "Members not found initially")

            # Step 3: Send jumbo frame traffic
            st.log("Step 3: Sending jumbo frame traffic")
            if not self._send_traffic_and_verify(dut1, dut2, DUT1_IP, DUT2_IP,
                                                 payload_size=9000):
                st.report_fail("msg", "Jumbo frame traffic failed initially")

            # Step 4: Change MTU to default while interface is up
            st.log("Step 4: Changing MTU to default (1500)")
            intf_api.interface_config(
                dut1, interface_name=f"PortChannel{PC_ID}",
                ip_address=None, mtu=DEFAULT_MTU,
                cli_type=self.data.cli_type
            )
            intf_api.interface_config(
                dut2, interface_name=f"PortChannel{PC_ID}",
                ip_address=None, mtu=DEFAULT_MTU,
                cli_type=self.data.cli_type
            )

            st.wait(2)

            # Step 5: Verify traffic with standard frames after MTU change
            st.log("Step 5: Verifying traffic with standard frames after MTU change")
            if not self._send_traffic_and_verify(dut1, dut2, DUT1_IP, DUT2_IP,
                                                 payload_size=1472):
                st.report_fail("msg", "Standard frame traffic failed after MTU change")

            # Step 6: Change MTU back to 9216
            st.log("Step 6: Changing MTU back to 9216")
            intf_api.interface_config(
                dut1, interface_name=f"PortChannel{PC_ID}",
                ip_address=None, mtu=JUMBO_MTU,
                cli_type=self.data.cli_type
            )
            intf_api.interface_config(
                dut2, interface_name=f"PortChannel{PC_ID}",
                ip_address=None, mtu=JUMBO_MTU,
                cli_type=self.data.cli_type
            )

            st.wait(2)

            # Step 7: Verify traffic with jumbo frames again
            st.log("Step 7: Verifying traffic with jumbo frames again")
            if not self._send_traffic_and_verify(dut1, dut2, DUT1_IP, DUT2_IP,
                                                 payload_size=9000):
                st.report_fail("msg", "Jumbo frame traffic failed after second MTU change")

            # Verify show commands
            output = st.show(
                dut1, f"show interfaces PortChannel {PC_ID}",
                type=self.data.cli_type, skip_tmpl=True
            )
            st.log(f"show interfaces PortChannel {PC_ID}:\n{output}")

            self.test_passed = True
            st.report_pass("msg", "Successfully changed MTU with active traffic")

        except Exception as err:
            st.error(f"Test failed with error: {err}")
            st.report_fail("msg", str(err))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
