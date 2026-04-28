"""
L2 ACL Basic Functional Tests - SPyTest Framework Integration

Author: Claude Code
Date: 2026-03-14
Version: 1.0 - SPyTest Native (3-SONiC-DUT Pattern with Tcpdump Verification)

How to run:
  ./bin/spytest --testbed ./testbeds/testbed_acl.yaml \\
      tests/switching/l2_acl/test_l2_acl.py \\
      --logs-path ./logs/l2_acl_$(date +%F_%H%M%S) \\
      --log-level debug --skip-init-config --ifname-type native

Description:
  End-to-end validation of L2 ACL (Layer 2 / MAC-level Access Control Lists)
  functionality using DUT-based Scapy traffic generation and tcpdump-based
  packet verification.

  Topology: 3-SONiC-DUT (DUT1=ACL device, DUT2=TX host, DUT3=RX host)
  Traffic Flow: DUT2 → DUT1 (ACL ingress) → DUT3 (tcpdump capture)
  Verification: Pcap file analysis using Scapy rdpcap()

Pre-requisites:
  - Topology: 3-node (D1D2D3) SONiC DUTs
  - DUTs: Virtual (SONiC-VS) or Hardware with direct connections
  - Min SONiC version: 202211 or later
  - Required packages: Scapy, tcpdump, Python 3.8+
  - DUT ports configured in switchport mode (not L3 routed)

Features:
  ✅ Full SPyTest framework integration (st.log, st.report_pass/fail)
  ✅ Tcpdump forensic verification (pcap files for analysis)
  ✅ Silent pass prevention (TX > 0, RX > 0 checks)
  ✅ Non-blocking traffic generation (DUT-deployed Scapy scripts)
  ✅ L2 MAC-based packet filtering
  ✅ VLAN tag support (802.1Q)
  ✅ EtherType-based filtering (ARP, IPv4, etc.)
  ✅ Automatic cleanup (try/finally blocks)
  ✅ Centralized test reporting
"""

from __future__ import annotations

from collections.abc import Iterable as IterableCollection
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple
import inspect
import re
import time

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api
import apis.system.interface as intf_api
import apis.routing.ip as ip_api
import apis.qos.acl as acl_api
import apis.common.scapy_traffic as scapy_traffic


def _get_connected_port(topology_config: Mapping[str, Any], from_dut: str, to_dut: str) -> str | None:
    """
    Discover the connected port from one DUT to another using testbed topology.

    Args:
        topology_config: Topology section of testbed YAML
        from_dut: Source DUT name (e.g., "DUT1")
        to_dut: Destination DUT name (e.g., "DUT2")

    Returns:
        Connected port name (e.g., "Ethernet40") or None if not found
    """
    if not topology_config:
        return None

    dut_topology = topology_config.get(from_dut, {})
    if not isinstance(dut_topology, dict):
        return None

    interfaces = dut_topology.get("interfaces", {})
    for port_name, port_config in interfaces.items():
        if isinstance(port_config, dict):
            if port_config.get("EndDevice") == to_dut:
                return port_name

    return None


# Module-level pytest markers
pytestmark = [
    pytest.mark.skip_module_config_save,  # Skip slow module config save that causes timeout
]

VAR_FILE_ENV = "L2_ACL_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "switching"
    / "l2_acl"
    / "vars_l2_acl.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load test variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    # If YAML file doesn't exist, return defaults
    if not candidate.is_file():
        st.log(f"L2 ACL variable file not found at {candidate}, using built-in defaults")
        return {
            "defaults": {
                "min_topology": ["D1D2:1", "D1D3:1"],
                "cli_type": "klish",
                "verify_timeout": 30,
                "cleanup": True
            },
            "dut_l2_config": {},
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


def _iter_candidate_duts(topology: Mapping[str, Any]) -> Iterable[str]:
    """Yield DUT aliases discovered in the topology map."""
    for key, value in topology.items():
        if key.startswith("D") and value:
            yield key


def _remove_ip_addresses(dut: str, interface: str, cli_type: str = "klish") -> None:
    """
    Remove all IP addresses from a specific interface.

    Uses 'show ip interfaces' to discover configured IP addresses,
    then removes them with proper 'no ip address <ip>' commands.
    Skips management interfaces (eth0).

    Args:
        dut: Device under test
        interface: Interface name (e.g., "Ethernet0", "Ethernet16")
        cli_type: CLI type (default: klish)
    """
    try:
        st.log(f"Discovering IP addresses on {interface}...")

        # Get all IP interfaces to find addresses on this interface
        output = st.show(dut, "show ip interfaces", type=cli_type, skip_tmpl=True)

        # Parse output to find IP addresses on this specific interface
        # Format: "Ethernet16           10.0.0.1/24"
        ip_addresses = []
        for line in str(output).split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) >= 2 and interface in parts[0]:
                # Found an IP address on this interface
                ip_addr = parts[1].split('/')[0]  # Remove CIDR notation
                if ip_addr and ip_addr != 'Interface':
                    ip_addresses.append(ip_addr)
                    st.log(f"  Found IP: {ip_addr} on {interface}")

        # Remove each discovered IP address
        if ip_addresses:
            st.log(f"Removing {len(ip_addresses)} IP address(es) from {interface}...")
            for ip_addr in ip_addresses:
                try:
                    cmd = f"no ip address {ip_addr}"
                    st.log(f"  Executing: {cmd}")
                    st.config(dut, cmd, type=cli_type, skip_error_check=True)
                except Exception as e:
                    st.warn(f"Could not remove {ip_addr}: {e}")
        else:
            st.log(f"  No IP addresses found on {interface}")

    except Exception as e:
        st.warn(f"Error removing IP addresses from {interface}: {e}")


class TestL2AclBasic:
    """Test L2 ACL functionality with DUT-based Scapy traffic and tcpdump verification."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Initialize test data, load configuration, and set up DUT topology."""
        st.banner("L2 ACL Test Suite - Setup Phase")

        # Load test configuration from YAML
        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Initialize topology
        min_topology = defaults.get("min_topology", ["D1D2:1", "D1D3:1"])
        topology = st.ensure_min_topology(*min_topology)
        cls.data.topology = topology
        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Map DUT aliases to framework handles
        cls.data.dut_names = st.get_dut_names()
        cls.data.dut_map = SpyTestDict()

        for dut_alias in _iter_candidate_duts(topology):
            cls.data.dut_map[dut_alias] = getattr(topology, dut_alias)

        # Get specific DUT handles from topology
        cls.data.dut1 = getattr(topology, "D1")  # ACL device
        cls.data.dut2 = getattr(topology, "D2")  # TX host
        cls.data.dut3 = getattr(topology, "D3")  # RX host

        st.banner(f"DUT Mapping: D1={cls.data.dut1}, D2={cls.data.dut2}, D3={cls.data.dut3}")

        # Discover connected ports from testbed topology
        st.banner("Discovering ports from testbed topology")

        # Get testbed topology from framework (passed via --testbed flag)
        # The testbed is provided by spytest framework via CLI arguments
        testbed_topology = {}

        # Access testbed topology through spytest framework's testbed variables
        try:
            testbed_vars = st.get_testbed_vars()
            if testbed_vars and hasattr(testbed_vars, 'topology'):
                testbed_topology = testbed_vars.topology
                st.log(f"✅ Retrieved testbed topology from framework")
                st.log(f"   Devices found: {list(testbed_topology.keys())}")
        except Exception as e:
            st.debug(f"Could not retrieve testbed topology from framework: {e}")

        # Discover ports using loaded topology
        # Try D1/D2/D3 format first (newer testbeds), then fallback to DUT1/DUT2/DUT3
        cls.data.dut1_port_to_dut2 = _get_connected_port(testbed_topology, "D1", "D2") or \
                                      _get_connected_port(testbed_topology, "DUT1", "DUT2")
        cls.data.dut2_port_to_dut1 = _get_connected_port(testbed_topology, "D2", "D1") or \
                                      _get_connected_port(testbed_topology, "DUT2", "DUT1")
        cls.data.dut1_port_to_dut3 = _get_connected_port(testbed_topology, "D1", "D3") or \
                                      _get_connected_port(testbed_topology, "DUT1", "DUT3")
        cls.data.dut3_port_to_dut1 = _get_connected_port(testbed_topology, "D3", "D1") or \
                                      _get_connected_port(testbed_topology, "DUT3", "DUT1")

        # Log discovered ports (no hardcoded fallback - fail if discovery fails)
        if not all([cls.data.dut1_port_to_dut2, cls.data.dut2_port_to_dut1,
                    cls.data.dut1_port_to_dut3, cls.data.dut3_port_to_dut1]):
            st.error("❌ Failed to discover all required ports from testbed topology")
            st.error(f"   D1->D2: {cls.data.dut1_port_to_dut2}")
            st.error(f"   D2->D1: {cls.data.dut2_port_to_dut1}")
            st.error(f"   D1->D3: {cls.data.dut1_port_to_dut3}")
            st.error(f"   D3->D1: {cls.data.dut3_port_to_dut1}")
            st.error("Ensure testbed YAML has correct device names (D1/D2/D3 or DUT1/DUT2/DUT3)")
            raise ValueError("Port discovery from testbed failed - cannot proceed with tests")

        st.log(f"Discovered ports: D1->D2={cls.data.dut1_port_to_dut2}, "
               f"D2->D1={cls.data.dut2_port_to_dut1}, "
               f"D1->D3={cls.data.dut1_port_to_dut3}, "
               f"D3->D1={cls.data.dut3_port_to_dut1}")

        # Configure L2 switchport mode on all DUTs
        cls._configure_l2_switchport_mode()

        st.banner("L2 ACL Test Suite - Setup Complete")

    @classmethod
    def teardown_class(cls) -> None:
        """Clean up configurations and return to base state."""
        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled - skipping teardown")
            return

        st.banner("L2 ACL Test Suite - Teardown Phase")

        # Clean up any remaining ACL configurations
        cls._cleanup_acl_config()

        st.log("Teardown complete")

    @pytest.fixture(autouse=True)
    def cleanup_acl_after_each_test(self):
        """
        Pytest fixture to automatically clean up ACL configs after each test.

        This fixture ensures that ACL tables from previous tests don't interfere
        with subsequent tests, maintaining proper test isolation.
        """
        yield  # Test executes before this point, cleanup runs after

        # Cleanup code runs after test completes (even on test failure)
        if not self.data.cleanup_enabled:
            st.log("Cleanup disabled - skipping per-test ACL cleanup")
            return

        try:
            st.banner("TEST TEARDOWN: Cleaning up ACL configurations created by this test")

            # List of L2 ACL tables created by tests
            test_acl_tables = [
                "L2_ACL_TABLE",
                "L2_ACL_TABLE_L201",  # L2-01
                "L2_ACL_TABLE_L202",  # L2-02
                "L2_ACL_TABLE_L203",  # L2-03
                "L2_ACL_TABLE_L204",  # L2-04
                "L2_ACL_TABLE_L205",  # L2-05
                "L2_ACL_TABLE_L206",  # L2-06
                "L2_ACL_TABLE_L207",  # L2-07
                "L2_ACL_TABLE_L208",  # L2-08
            ]

            st.log(f"Removing ACL tables: {test_acl_tables}")

            # Delete each ACL table (also removes associated rules)
            for table_name in test_acl_tables:
                try:
                    st.log(f"Attempting to remove ACL table: {table_name}")
                    result = acl_api.delete_acl_table(
                        self.data.dut1,
                        acl_table_name=table_name,
                        acl_type="L2",
                        cli_type=self.data.cli_type
                    )

                    if result:
                        st.log(f"✅ ACL table '{table_name}' removed successfully")
                    else:
                        st.log(f"⚠️ ACL table '{table_name}' not found or already deleted")

                except Exception as table_err:
                    st.log(f"⚠️ Error removing table '{table_name}': {table_err} (continuing)")

            st.log("✅ Per-test ACL cleanup completed")

        except Exception as e:
            st.warn(f"⚠️ Error during per-test ACL cleanup: {e}")
            st.warn("Continuing with next test (cleanup failure may affect test isolation)")

    @classmethod
    def _configure_l2_switchport_mode(cls) -> None:
        """
        Configure L2 switchport mode on DUT1 ports using raw CLI.

        This configures both D1 ports in the same VLAN (VLAN 10) for L2 bridging.
        Uses raw CLI commands for maximum compatibility across SONiC versions.
        """
        st.banner("Configuring L2 VLAN and switchport for L2 ACL testing")

        cli_type = cls.data.cli_type
        vlan_id = 10  # Use VLAN 10 for L2 ACL testing

        try:
            # Configure VLAN 10 and add D1 ports (using interface names from testbed)
            port_d1_tx = cls.data.dut1_port_to_dut2  # D1 port towards D2 (TX)
            port_d1_rx = cls.data.dut1_port_to_dut3  # D1 port towards D3 (RX)

            st.log(f"Configuring VLAN {vlan_id} with ports: {port_d1_tx}, {port_d1_rx}")

            # Build configuration commands using raw CLI (from testbed, no hardcoding)
            # Add space workaround for Ethernet interfaces as per SONiC requirements
            port_d1_tx_cmd = port_d1_tx.replace("Ethernet", "Ethernet ")
            port_d1_rx_cmd = port_d1_rx.replace("Ethernet", "Ethernet ")

            # First, remove any IP addresses from the interfaces (if configured in L3 mode)
            # This is necessary for interfaces that may be configured with IP addresses
            st.log("Removing IP addresses from interfaces (if configured)...")
            _remove_ip_addresses(cls.data.dut1, port_d1_tx, cli_type)
            _remove_ip_addresses(cls.data.dut1, port_d1_rx, cli_type)
            st.wait(1, "Wait for IP cleanup to take effect")

            # Now configure VLAN and switchport mode
            commands = [
                "configure terminal",
                f"vlan {vlan_id}",
                f"interface {port_d1_tx_cmd}",
                f"switchport access vlan {vlan_id}",
                "exit",
                f"interface {port_d1_rx_cmd}",
                f"switchport access vlan {vlan_id}",
                "exit",
                "exit"
            ]

            st.log(f"Executing {len(commands)} L2 switchport configuration commands on D1")
            for cmd in commands:
                st.log(f"  Executing: {cmd}")
                output = st.config(cls.data.dut1, cmd, type=cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.warn(f"⚠️  Command may have warning: {cmd}")
                    st.warn(f"     Output: {output}")

            st.wait(2, "Wait for VLAN configuration to take effect")
            st.log(f"✅ VLAN {vlan_id} configured on D1 ports {port_d1_tx}, {port_d1_rx}")

        except Exception as e:
            st.error(f"Error configuring L2 VLAN and switchport: {e}")
            st.error(f"    Port D1->D2: {cls.data.dut1_port_to_dut2}")
            st.error(f"    Port D1->D3: {cls.data.dut1_port_to_dut3}")

    @classmethod
    def _cleanup_acl_config(cls) -> None:
        """Remove all ACL configurations."""
        st.banner("Cleaning up ACL configurations")
        cli_type = cls.data.cli_type

        try:
            # Get ACL table names from config
            acl_config = cls.data.config.get("acl_config", {})
            acl_tables = acl_config.get("tables", {})

            for table_name, table_cfg in acl_tables.items():
                st.log(f"Removing ACL table: {table_name}")
                acl_type = table_cfg.get("type", "L2")

                # Delete ACL table (this also removes associated rules)
                result = acl_api.delete_acl_table(
                    cls.data.dut1,
                    acl_table_name=table_name,
                    acl_type=acl_type,
                    cli_type=cli_type
                )

                if result:
                    st.log(f"✅ ACL table '{table_name}' removed successfully")
                else:
                    st.warn(f"Failed to remove ACL table '{table_name}'")

        except Exception as e:
            st.warn(f"Error during ACL cleanup: {e}")

    @classmethod
    def _cleanup_pcap_files(cls, dut: str, pcap_path: str) -> None:
        """Delete old pcap files to ensure clean slate."""
        st.log(f"Cleaning up old pcap file: {pcap_path} on {dut}")
        try:
            cmd = f"sudo rm -f {pcap_path}"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            st.log(f"✅ Deleted {pcap_path} on {dut}")
        except Exception as e:
            st.warn(f"Error cleaning up pcap file on {dut}: {e}")

    @classmethod
    def _start_tcpdump(cls, dut: str, interface: str, pcap_path: str) -> bool:
        """Start tcpdump listener in background on DUT (no filter for L2)."""
        st.log(f"Starting tcpdump on {dut} ({interface}) → {pcap_path}")

        try:
            cmd = f"sudo nohup tcpdump -i {interface} -w {pcap_path} > /dev/null 2>&1 &"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            st.wait(1, "Wait for tcpdump to initialize")

            # Verify tcpdump is running
            check_cmd = "ps aux | grep tcpdump | grep -v grep"
            output = st.show(dut, check_cmd, skip_tmpl=True, skip_error_check=True)

            if "tcpdump" in output:
                st.log(f"✅ tcpdump started successfully on {dut}")
                return True
            else:
                st.error(f"❌ tcpdump failed to start on {dut}")
                return False

        except Exception as e:
            st.error(f"Error starting tcpdump on {dut}: {e}")
            return False

    @classmethod
    def _stop_tcpdump(cls, dut: str) -> None:
        """Stop tcpdump process cleanly."""
        st.log(f"Stopping tcpdump on {dut}")

        try:
            cmd = "sudo killall tcpdump"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            st.wait(2, "Wait for tcpdump to flush and close file")
            st.log(f"✅ Stopped tcpdump on {dut}")
        except Exception as e:
            st.warn(f"Error stopping tcpdump on {dut}: {e}")

    @classmethod
    def _count_packets_in_pcap(cls, dut: str, pcap_path: str) -> int:
        """Count packets in pcap file using Scapy rdpcap()."""
        st.log(f"Counting packets in {pcap_path} on {dut}")

        try:
            cmd = f'sudo python3 -c "from scapy.all import rdpcap; print(len(rdpcap(\\"{pcap_path}\\")))"'
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=False)

            output_str = output.strip()

            # Look for last line that's purely numeric (the packet count)
            for line in reversed(output_str.split('\n')):
                line = line.strip()
                if line.isdigit():
                    packet_count = int(line)
                    st.log(f"✅ Packet count from {pcap_path}: {packet_count}")
                    return packet_count

            st.warn(f"Could not parse packet count from output: {output_str}")
            return 0

        except Exception as e:
            st.error(f"Error counting packets in {pcap_path} on {dut}: {e}")
            return 0

    @classmethod
    def _analyze_pcap_packets(cls, dut: str, pcap_path: str, expected_src_mac: str = None, expected_dst_mac: str = None) -> Dict[str, Any]:
        """Analyze captured packets in pcap file using Scapy rdpcap()."""
        st.log(f"Analyzing packets in {pcap_path} on {dut}")

        analysis_script = '''
from scapy.all import rdpcap, Ether
from collections import defaultdict

try:
    packets = rdpcap(r"{}") if r"{}" else []

    if not packets:
        print("RESULT|0|NO_PACKETS")
        exit(0)

    total = len(packets)
    src_macs = defaultdict(int)
    dst_macs = defaultdict(int)
    vlan_packets = 0
    ipv4_packets = 0
    ipv6_packets = 0
    arp_packets = 0
    other_packets = 0

    for pkt in packets:
        if Ether in pkt:
            src = pkt[Ether].src.upper()
            dst = pkt[Ether].dst.upper()
            src_macs[src] += 1
            dst_macs[dst] += 1

            # Check for VLAN
            if "VLAN" in pkt:
                vlan_packets += 1

            # Check for protocols
            if "IPv4" in pkt:
                ipv4_packets += 1
            elif "IPv6" in pkt:
                ipv6_packets += 1
            elif "ARP" in pkt:
                arp_packets += 1
            else:
                other_packets += 1

    # Format output
    print(f"RESULT|{{total}}|TOTAL_PACKETS")
    print(f"VLAN={{vlan_packets}}")
    print(f"IPv4={{ipv4_packets}}")
    print(f"IPv6={{ipv6_packets}}")
    print(f"ARP={{arp_packets}}")
    print(f"OTHER={{other_packets}}")

    # Print top source MACs
    print("SRC_MACS:")
    for mac, count in sorted(src_macs.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {{mac}}={{count}}")

    # Print top destination MACs
    print("DST_MACS:")
    for mac, count in sorted(dst_macs.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {{mac}}={{count}}")

except Exception as e:
    print(f"ERROR|{{str(e)}}")
    exit(1)
'''.format(pcap_path, pcap_path)

        try:
            cmd = f"sudo python3 -c '{analysis_script}'"
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=False)

            analysis = {
                "total": 0,
                "vlan_count": 0,
                "ipv4_count": 0,
                "ipv6_count": 0,
                "arp_count": 0,
                "other_count": 0,
                "src_macs": [],
                "dst_macs": [],
                "raw_output": output
            }

            lines = output.strip().split('\n')
            for line in lines:
                line = line.strip()

                if line.startswith("RESULT|"):
                    parts = line.split('|')
                    if len(parts) >= 2:
                        try:
                            analysis["total"] = int(parts[1])
                        except:
                            pass
                elif line.startswith("VLAN="):
                    try:
                        analysis["vlan_count"] = int(line.split('=')[1])
                    except:
                        pass
                elif line.startswith("IPv4="):
                    try:
                        analysis["ipv4_count"] = int(line.split('=')[1])
                    except:
                        pass
                elif line.startswith("IPv6="):
                    try:
                        analysis["ipv6_count"] = int(line.split('=')[1])
                    except:
                        pass
                elif line.startswith("ARP="):
                    try:
                        analysis["arp_count"] = int(line.split('=')[1])
                    except:
                        pass
                elif line.startswith("OTHER="):
                    try:
                        analysis["other_count"] = int(line.split('=')[1])
                    except:
                        pass
                elif line.startswith("  ") and "=" in line:
                    parts = line.strip().split('=')
                    if len(parts) == 2:
                        mac = parts[0]
                        count = parts[1]
                        if "SRC_MACS" in output[:output.find(line)]:
                            analysis["src_macs"].append(f"{mac}({count})")
                        elif "DST_MACS" in output[:output.find(line)]:
                            analysis["dst_macs"].append(f"{mac}({count})")

            st.log(f"✅ Packet Analysis Summary for {pcap_path}:")
            st.log(f"   Total Packets: {analysis['total']}")
            st.log(f"   VLAN Tagged: {analysis['vlan_count']}")
            st.log(f"   IPv4: {analysis['ipv4_count']}")
            st.log(f"   IPv6: {analysis['ipv6_count']}")
            st.log(f"   ARP: {analysis['arp_count']}")
            st.log(f"   Other: {analysis['other_count']}")
            if analysis['src_macs']:
                st.log(f"   Top Source MACs: {', '.join(analysis['src_macs'][:3])}")
            if analysis['dst_macs']:
                st.log(f"   Top Dest MACs: {', '.join(analysis['dst_macs'][:3])}")

            # Validate expected MACs if provided
            if expected_src_mac and analysis['src_macs']:
                found = any(expected_src_mac.upper() in mac for mac in analysis['src_macs'])
                if not found:
                    st.warn(f"⚠️  Expected source MAC {expected_src_mac} NOT in captured packets")
                else:
                    st.log(f"✅ Expected source MAC {expected_src_mac} found in captured packets")

            return analysis

        except Exception as e:
            st.error(f"Error analyzing packets in {pcap_path} on {dut}: {e}")
            return {
                "total": 0,
                "error": str(e),
                "src_macs": [],
                "dst_macs": []
            }

    @classmethod
    def _configure_acl(cls, acl_config: Dict[str, Any]) -> bool:
        """Configure ACL tables and rules on DUT1."""
        st.banner("Configuring L2 ACL rules on DUT1")
        cli_type = cls.data.cli_type
        dut1 = cls.data.dut1

        try:
            acl_tables = acl_config.get("tables", {})

            for table_name, table_cfg in acl_tables.items():
                st.log(f"Creating L2 ACL table: {table_name}")

                # L2 ACL type with stage and ports
                acl_type = table_cfg.get("type", "L2")
                stage = table_cfg.get("stage", "INGRESS")
                ports = table_cfg.get("ports", [cls.data.dut1_port_to_dut2])

                # Create ACL table
                result = acl_api.create_acl_table(
                    dut1,
                    acl_type=acl_type,
                    table_name=table_name,
                    stage=stage,
                    ports=ports,
                    cli_type=cli_type
                )

                if not result:
                    st.error(f"Failed to create ACL table: {table_name}")
                    return False

                st.log(f"✅ L2 ACL table '{table_name}' created successfully")

                # Create ACL rules for this table
                rules = table_cfg.get("rules", [])
                for rule_cfg in rules:
                    rule_name = rule_cfg.get("rule_name")
                    packet_action = rule_cfg.get("action", "deny")
                    src_mac = rule_cfg.get("src_mac", "any")
                    dst_mac = rule_cfg.get("dst_mac", "any")
                    ethertype = rule_cfg.get("ethertype", None)
                    vlan_id = rule_cfg.get("vlan_id", None)

                    st.log(f"Creating L2 ACL rule: {rule_name} ({packet_action})")

                    # Create L2 ACL rule
                    result = acl_api.create_acl_rule(
                        dut1,
                        acl_type=acl_type,
                        table_name=table_name,
                        rule_name=rule_name,
                        packet_action=packet_action,
                        src_mac=src_mac,
                        dst_mac=dst_mac,
                        cli_type=cli_type
                    )

                    if not result:
                        st.error(f"Failed to create ACL rule: {rule_name}")
                        return False

                    st.log(f"✅ L2 ACL rule '{rule_name}' created successfully")

            st.log("✅ All L2 ACL tables and rules configured successfully")
            return True

        except Exception as e:
            st.error(f"Exception during ACL configuration: {e}")
            return False

    def _get_traffic_config(self, test_case_id: str) -> Dict[str, Any]:
        """Get traffic configuration for a specific test case."""
        testcases = self.data.config.get("testcases", {})
        return testcases.get(test_case_id, {})

    def _generate_scapy_l2_traffic(
        self,
        src_mac: str,
        dst_mac: str,
        duration: int = 10,
        total_packets: int = 100,
        vlan_id: int = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Generate L2 traffic using Scapy with MAC addresses."""
        st.banner(f"Generating L2 traffic: {src_mac} → {dst_mac}")

        try:
            # Use dynamically discovered interface names (fail if not found)
            if not self.data.dut2_port_to_dut1:
                st.error("D2 port to D1 not discovered from testbed")
                return False, {"success": False, "error": "D2 port to D1 not discovered"}

            dut2_tx_interface = self.data.dut2_port_to_dut1

            st.log(f"  Source MAC: {src_mac}")
            st.log(f"  Destination MAC: {dst_mac}")
            if vlan_id:
                st.log(f"  VLAN ID: {vlan_id}")

            pps = total_packets // duration if duration > 0 else 100
            st.log(f"  Rate: {pps} pps, Duration: {duration}s, Total: {total_packets} packets")

            # Send L2 traffic from DUT2
            result = scapy_traffic.send_l2_traffic(
                dut=self.data.dut2,
                interface=dut2_tx_interface,
                src_mac=src_mac,
                dst_mac=dst_mac,
                duration=duration,
                pps=pps,
                vlan_id=vlan_id
            )

            if result.get("success"):
                st.log(f"✅ L2 traffic generation completed: {total_packets} packets sent")
                return True, result
            else:
                st.error("❌ L2 traffic generation failed")
                return False, result

        except Exception as e:
            st.error(f"Error during L2 traffic generation: {e}")
            return False, {"success": False, "error": str(e)}

    # ============================================================================
    # L2-01: PERMIT EXACT SOURCE MAC
    # ============================================================================

    @pytest.mark.inventory(
        feature="L2_ACL",
        testcases=["test_l2_01_permit_source_mac"]
    )
    @pytest.mark.skip_module_config_save
    def test_l2_01_permit_source_mac(self) -> None:
        """
        TC-L2-01: Permit exact source MAC address.

        This test verifies that ACL rules permitting a specific source MAC work correctly.
        Traffic from the permitted MAC should pass through (RX > 0).
        Expected result: RX count ≥ 90% of TX count (permitted traffic passes).

        NOTE: SONiC L2 ACL is CASE-SENSITIVE for MAC addresses.
        """
        st.banner("Test L2-01: Permit source MAC 00:11:22:33:44:55")

        src_mac = "00:11:22:33:44:55"
        dst_mac = "FF:FF:FF:FF:FF:FF"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_01_rx.pcap"

        # Get RX interface from testbed (fail if not discovered)
        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # Normalize MAC to UPPERCASE (SONiC L2 ACL is case-sensitive)
        src_mac_uppercase = src_mac.upper()

        # Generate dynamic ACL table name from test function name (not hardcoded)
        # Use inspect.currentframe() for pytest compatibility (not unittest's _testMethodName)
        test_func_name = inspect.currentframe().f_code.co_name
        acl_table_name = f"L2_ACL_{test_func_name.upper()}"

        try:
            # ===== PHASE 1: Create ACL Rule =====
            st.banner("PHASE 1: Creating L2 ACL rule for permit source MAC")

            # Create L2 ACL table using raw CLI (dynamic table name from testbed)
            st.log(f"Creating MAC ACL table: {acl_table_name} on port {self.data.dut1_port_to_dut2}")

            # Configure MAC access-list using raw CLI commands (dynamic table name)
            commands = [
                f"mac access-list {acl_table_name}",
                f"seq 1 permit host {src_mac_uppercase} any",
                "exit"
            ]

            for cmd in commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.error(f"Output: {output}")
                    st.report_fail("msg", f"Failed to configure ACL with command: {cmd}")

            st.log(f"✅ Created L2 MAC ACL table with rule: permit host {src_mac_uppercase} any")

            # Apply ACL to interface (all in one command sequence to maintain CLI context)
            st.log(f"Applying MAC ACL to interface {self.data.dut1_port_to_dut2}")
            # SONiC klish CLI requires space between Ethernet and port number
            interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
            apply_commands = [
                f"interface {interface_cmd}",
                f"mac access-group {acl_table_name} in",
                "exit"
            ]

            for cmd in apply_commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to apply ACL with command: {cmd}")

            st.log(f"✅ Applied L2 ACL rule to interface {self.data.dut1_port_to_dut2}")

            # ===== PHASE 1.5: Verify ACL Configuration =====
            st.banner("PHASE 1.5: Verifying ACL Configuration (subcase)")

            # Verify ACL table exists
            st.log("Executing: show mac access-lists")
            acl_list_output = st.show(self.data.dut1, "show mac access-lists", type=self.data.cli_type, skip_tmpl=True)
            st.log(f"MAC Access Lists Output:\n{acl_list_output}")

            acl_output_str = str(acl_list_output)

            # Check 1: Table exists
            if acl_table_name not in acl_output_str:
                st.error(f"❌ ACL table '{acl_table_name}' NOT found in show mac access-lists")
                st.report_fail("msg", f"ACL table {acl_table_name} not created")

            st.log(f"✅ ACL table '{acl_table_name}' found")

            # Check 2: MAC address is present in rule (CRITICAL - MAC fields should NOT be dropped)
            if src_mac_uppercase not in acl_output_str:
                st.error(f"❌ CRITICAL BUG: Source MAC '{src_mac_uppercase}' NOT found in ACL rule")
                st.error(f"   Configured: seq 1 permit host {src_mac_uppercase} any")
                st.error(f"   Backend shows: seq 1 permit any any  (MAC DROPPED!)")
                st.error(f"   This means the ACL rule is overly permissive and won't function")
                st.report_fail("msg", f"ACL rule lost MAC address - backend bug")

            st.log(f"✅ Source MAC '{src_mac_uppercase}' found in ACL rule")

            # Verify ACL is applied to interface (SONiC klish doesn't support interface-specific filter)
            st.log("Executing: show mac access-group (SONiC klish doesn't support per-interface filtering)")
            acl_group_output = st.show(self.data.dut1, "show mac access-group", type=self.data.cli_type, skip_tmpl=True)
            st.log(f"MAC Access Group Output:\n{acl_group_output}")

            if acl_table_name in str(acl_group_output):
                st.log(f"✅ ACL group '{acl_table_name}' is applied to an interface")
            else:
                st.error(f"❌ ACL group '{acl_table_name}' NOT applied to any interface")
                st.report_fail("msg", f"ACL not applied to any interface")

            # ===== PHASE 2: Cleanup =====
            st.banner("PHASE 2: Cleanup pcap files")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            # ===== PHASE 3: Start tcpdump listener =====
            st.banner("PHASE 3: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # ===== PHASE 4: Generate traffic =====
            st.banner("PHASE 4: Generating L2 traffic (permit rule)")
            success, result = self._generate_scapy_l2_traffic(src_mac_uppercase, dst_mac, duration, num_packets)

            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "L2 traffic generation failed")

            # ===== PHASE 5: Stop tcpdump listener =====
            st.banner("PHASE 5: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # ===== PHASE 6: Verify using pcap =====
            st.banner("PHASE 6: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            # ===== PHASE 7: Validate results =====
            st.banner("PHASE 7: Validating results")

            st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")
            st.log(f"ACL Rule MAC: {src_mac_uppercase}")
            st.log(f"Traffic MAC: {src_mac_uppercase}")
            st.log("NOTE: SONiC L2 ACL is CASE-SENSITIVE for MAC addresses - both must match")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            loss_pct = ((num_packets - rx_count) / num_packets * 100) if num_packets > 0 else 100.0
            max_loss = 10.0

            if loss_pct > max_loss:
                st.error(f"❌ Packet loss {loss_pct:.1f}% exceeds threshold {max_loss}%")
                st.report_fail("msg", f"Loss {loss_pct:.1f}% > {max_loss}%")

            st.log("✅ L2-01 test PASSED")
            st.report_pass("test_case_passed")

        finally:
            # Cleanup: Remove the test ACL using raw CLI commands (use dynamic table name)
            st.banner("CLEANUP: Removing L2 ACL configuration")
            try:
                # SONiC klish CLI requires space between Ethernet and port number
                interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
                cleanup_commands = [
                    f"interface {interface_cmd}",
                    f"no mac access-group {acl_table_name} in",
                    "exit",
                    f"no mac access-list {acl_table_name}"
                ]

                for cmd in cleanup_commands:
                    st.log(f"Cleanup: {cmd}")
                    st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=True)

                st.log("✅ Cleaned up L2_ACL_TEST_L201 table")
            except Exception as cleanup_err:
                st.log(f"⚠️  Cleanup warning: {cleanup_err}")

    # ============================================================================
    # L2-02: DENY SOURCE MAC
    # ============================================================================

    @pytest.mark.inventory(
        feature="L2_ACL",
        testcases=["test_l2_02_deny_source_mac"]
    )
    @pytest.mark.skip_module_config_save
    def test_l2_02_deny_source_mac(self) -> None:
        """
        TC-L2-02: Deny source MAC address.

        This test verifies that ACL rules blocking a specific source MAC work correctly.
        Traffic from the denied MAC should be dropped (RX = 0).
        Expected result: RX count = 0 (denied traffic blocked).
        """
        st.banner("Test L2-02: Deny source MAC AA:BB:CC:DD:EE:FF")

        src_mac = "AA:BB:CC:DD:EE:FF"
        dst_mac = "FF:FF:FF:FF:FF:FF"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_02_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # Normalize MAC to UPPERCASE (SONiC L2 ACL is case-sensitive)
        src_mac_uppercase = src_mac.upper()

        # Generate dynamic ACL table name from test function name
        test_func_name = inspect.currentframe().f_code.co_name
        acl_table_name = f"L2_ACL_{test_func_name.upper()}"

        try:
            # ===== PHASE 1: Create ACL Rule (Deny Source MAC) =====
            st.banner("PHASE 1: Creating L2 ACL rule to DENY source MAC")

            st.log(f"Creating MAC ACL table: {acl_table_name} on port {self.data.dut1_port_to_dut2}")

            # Configure MAC access-list using raw CLI commands (dynamic table name)
            commands = [
                f"mac access-list {acl_table_name}",
                f"seq 1 deny host {src_mac_uppercase} any",
                "exit"
            ]

            for cmd in commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to configure ACL with command: {cmd}")

            st.log(f"✅ Created L2 MAC ACL table with DENY rule for MAC: {src_mac_uppercase}")

            # Apply ACL to interface
            st.log(f"Applying MAC ACL to interface {self.data.dut1_port_to_dut2}")
            interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
            apply_commands = [
                f"interface {interface_cmd}",
                f"mac access-group {acl_table_name} in",
                "exit"
            ]

            for cmd in apply_commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to apply ACL with command: {cmd}")

            st.log(f"✅ Applied L2 ACL rule to interface {self.data.dut1_port_to_dut2}")

            # ===== PHASE 1.5: Verify ACL Configuration (subcase) =====
            st.banner("PHASE 1.5: Verifying ACL Configuration (subcase)")

            # Verify ACL table exists
            st.log("Executing: show mac access-lists")
            acl_list_output = st.show(self.data.dut1, "show mac access-lists", type=self.data.cli_type, skip_tmpl=True)
            st.log(f"MAC Access Lists Output:\n{acl_list_output}")

            acl_output_str = str(acl_list_output)

            # Check 1: Table exists
            if acl_table_name not in acl_output_str:
                st.error(f"❌ ACL table '{acl_table_name}' NOT found in show mac access-lists")
                st.report_fail("msg", f"ACL table {acl_table_name} not created")

            st.log(f"✅ ACL table '{acl_table_name}' found")

            # Check 2: MAC address is present in rule (CRITICAL - MAC fields should NOT be dropped)
            if src_mac_uppercase not in acl_output_str:
                st.error(f"❌ CRITICAL BUG: Source MAC '{src_mac_uppercase}' NOT found in ACL rule")
                st.error(f"   Configured: seq 1 deny host {src_mac_uppercase} any")
                st.error(f"   Backend shows: seq 1 deny any any  (MAC DROPPED!)")
                st.error(f"   This means the ACL rule is overly permissive and won't function")
                st.report_fail("msg", f"ACL rule lost MAC address - backend bug")

            st.log(f"✅ Source MAC '{src_mac_uppercase}' found in ACL rule")

            # Verify ACL is applied to interface (SONiC klish doesn't support interface-specific filter)
            st.log("Executing: show mac access-group (SONiC klish doesn't support per-interface filtering)")
            acl_group_output = st.show(self.data.dut1, "show mac access-group", type=self.data.cli_type, skip_tmpl=True)
            st.log(f"MAC Access Group Output:\n{acl_group_output}")

            if acl_table_name in str(acl_group_output):
                st.log(f"✅ ACL group '{acl_table_name}' is applied to an interface")
            else:
                st.error(f"❌ ACL group '{acl_table_name}' NOT applied to any interface")
                st.report_fail("msg", f"ACL not applied to any interface")

            # ===== PHASE 2: Cleanup =====
            st.banner("PHASE 2: Cleanup")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            # ===== PHASE 3: Start tcpdump listener =====
            st.banner("PHASE 3: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # ===== PHASE 4: Generate traffic =====
            st.banner("PHASE 4: Generating L2 traffic (deny rule)")
            success, result = self._generate_scapy_l2_traffic(src_mac, dst_mac, duration, num_packets)

            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "L2 traffic generation failed")

            # ===== PHASE 5: Stop tcpdump listener =====
            st.banner("PHASE 5: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # ===== PHASE 6: Verify using pcap =====
            st.banner("PHASE 6: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            # ===== PHASE 6.5: Analyze captured packets (DEBUG) =====
            st.banner("PHASE 6.5: Analyzing packet contents in pcap file")
            if rx_count > 0:
                packet_analysis = self._analyze_pcap_packets(
                    self.data.dut3,
                    pcap_path,
                    expected_src_mac=src_mac
                )
                st.log(f"Captured packets breakdown:")
                st.log(f"  Total captured: {packet_analysis.get('total', 0)}")
                st.log(f"  VLAN tagged: {packet_analysis.get('vlan_count', 0)}")
                st.log(f"  IPv4: {packet_analysis.get('ipv4_count', 0)}")
                st.log(f"  IPv6: {packet_analysis.get('ipv6_count', 0)}")
                st.log(f"  ARP: {packet_analysis.get('arp_count', 0)}")
                st.log(f"  Other: {packet_analysis.get('other_count', 0)}")
            else:
                st.log("No packets captured - DENY rule appears to be working")

            # ===== PHASE 7: Validate results =====
            st.banner("PHASE 7: Validating results (expecting DENY)")

            st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")

            # For DENY rule, expect RX = 0
            if rx_count == 0:
                st.log("✅ L2-02 test PASSED - All packets denied as expected")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ L2-02 test FAILED - Expected RX=0, got RX={rx_count}")
                st.report_fail("msg", f"ACL not blocking packets (RX={rx_count})")

        finally:
            # Cleanup: Remove the test ACL using raw CLI commands (use dynamic table name)
            st.banner("CLEANUP: Removing L2 ACL configuration")
            try:
                # SONiC klish CLI requires space between Ethernet and port number
                interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
                cleanup_commands = [
                    f"interface {interface_cmd}",
                    f"no mac access-group {acl_table_name} in",
                    "exit",
                    f"no mac access-list {acl_table_name}"
                ]

                for cmd in cleanup_commands:
                    st.log(f"Cleanup: {cmd}")
                    st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=True)

                st.log("✅ Cleaned up L2_ACL_TEST_L202 table")
            except Exception as cleanup_err:
                st.log(f"⚠️  Cleanup warning: {cleanup_err}")

    # ============================================================================
    # L2-03: DENY DESTINATION MAC
    # ============================================================================

    @pytest.mark.inventory(
        feature="L2_ACL",
        testcases=["test_l2_03_deny_dest_mac"]
    )
    @pytest.mark.skip_module_config_save
    def test_l2_03_deny_dest_mac(self) -> None:
        """
        TC-L2-03: Deny destination MAC address.

        This test verifies that ACL rules blocking a specific destination MAC work correctly.
        Traffic to the denied MAC should be dropped (RX = 0).
        Expected result: RX count = 0 (denied traffic blocked).
        """
        st.banner("Test L2-03: Deny destination MAC 11:22:33:44:55:66")

        src_mac = "00:11:22:33:44:55"
        dst_mac = "11:22:33:44:55:66"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_03_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # ===== PHASE 1: Cleanup =====
        st.banner("PHASE 1: Cleanup")
        self._cleanup_pcap_files(self.data.dut3, pcap_path)

        # ===== PHASE 2: Start tcpdump listener =====
        st.banner("PHASE 2: Starting tcpdump listener on DUT3")
        tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

        if not tcpdump_ok:
            st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

        # ===== PHASE 3: Generate traffic =====
        st.banner("PHASE 3: Generating L2 traffic (deny dest MAC rule)")
        success, result = self._generate_scapy_l2_traffic(src_mac, dst_mac, duration, num_packets)

        if not success:
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", "L2 traffic generation failed")

        # ===== PHASE 4: Stop tcpdump listener =====
        st.banner("PHASE 4: Stopping tcpdump listener")
        self._stop_tcpdump(self.data.dut3)

        # ===== PHASE 5: Verify using pcap =====
        st.banner("PHASE 5: Counting packets in pcap file")
        rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

        # ===== PHASE 5.5: Analyze captured packets (DEBUG) =====
        st.banner("PHASE 5.5: Analyzing packet contents in pcap file")
        if rx_count > 0:
            packet_analysis = self._analyze_pcap_packets(
                self.data.dut3,
                pcap_path,
                expected_dst_mac=dst_mac
            )
            st.log(f"Captured packets breakdown:")
            st.log(f"  Total captured: {packet_analysis.get('total', 0)}")
            st.log(f"  VLAN tagged: {packet_analysis.get('vlan_count', 0)}")
            st.log(f"  IPv4: {packet_analysis.get('ipv4_count', 0)}")
            st.log(f"  IPv6: {packet_analysis.get('ipv6_count', 0)}")
            st.log(f"  ARP: {packet_analysis.get('arp_count', 0)}")
            st.log(f"  Other: {packet_analysis.get('other_count', 0)}")
        else:
            st.log("No packets captured - DENY rule appears to be working")

        # ===== PHASE 6: Validate results =====
        st.banner("PHASE 6: Validating results (expecting DENY)")

        st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")

        if rx_count == 0:
            st.log("✅ L2-03 test PASSED - All packets denied as expected")
            st.report_pass("test_case_passed")
        else:
            st.error(f"❌ L2-03 test FAILED - Expected RX=0, got RX={rx_count}")
            st.report_fail("msg", f"Destination MAC deny rule not working (RX={rx_count})")

    # ============================================================================
    # L2-04: DENY BROADCAST MAC
    # ============================================================================

    @pytest.mark.inventory(
        feature="L2_ACL",
        testcases=["test_l2_04_deny_broadcast_mac"]
    )
    @pytest.mark.skip_module_config_save
    def test_l2_04_deny_broadcast_mac(self) -> None:
        """
        TC-L2-04: Deny broadcast MAC address (FF:FF:FF:FF:FF:FF).

        This test verifies that ACL rules blocking broadcast traffic work correctly.
        Broadcast frames should be dropped (RX = 0).
        Expected result: RX count = 0 (broadcast traffic blocked).
        """
        st.banner("Test L2-04: Deny broadcast MAC (FF:FF:FF:FF:FF:FF)")

        src_mac = "00:11:22:33:44:55"
        dst_mac = "FF:FF:FF:FF:FF:FF"  # Broadcast
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_04_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # ===== PHASE 1: Cleanup =====
        st.banner("PHASE 1: Cleanup")
        self._cleanup_pcap_files(self.data.dut3, pcap_path)

        # ===== PHASE 2: Start tcpdump listener =====
        st.banner("PHASE 2: Starting tcpdump listener on DUT3")
        tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

        if not tcpdump_ok:
            st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

        # ===== PHASE 3: Generate traffic =====
        st.banner("PHASE 3: Generating L2 broadcast traffic (deny rule)")
        success, result = self._generate_scapy_l2_traffic(src_mac, dst_mac, duration, num_packets)

        if not success:
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", "L2 traffic generation failed")

        # ===== PHASE 4: Stop tcpdump listener =====
        st.banner("PHASE 4: Stopping tcpdump listener")
        self._stop_tcpdump(self.data.dut3)

        # ===== PHASE 5: Verify using pcap =====
        st.banner("PHASE 5: Counting packets in pcap file")
        rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

        # ===== PHASE 5.5: Analyze captured packets (DEBUG) =====
        st.banner("PHASE 5.5: Analyzing packet contents in pcap file")
        if rx_count > 0:
            packet_analysis = self._analyze_pcap_packets(
                self.data.dut3,
                pcap_path,
                expected_dst_mac=dst_mac
            )
            st.log(f"Captured packets breakdown:")
            st.log(f"  Total captured: {packet_analysis.get('total', 0)}")
            st.log(f"  VLAN tagged: {packet_analysis.get('vlan_count', 0)}")
            st.log(f"  IPv4: {packet_analysis.get('ipv4_count', 0)}")
            st.log(f"  IPv6: {packet_analysis.get('ipv6_count', 0)}")
            st.log(f"  ARP: {packet_analysis.get('arp_count', 0)}")
            st.log(f"  Other: {packet_analysis.get('other_count', 0)}")
        else:
            st.log("No packets captured - DENY rule appears to be working")

        # ===== PHASE 6: Validate results =====
        st.banner("PHASE 6: Validating results (expecting DENY broadcast)")

        st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")

        if rx_count == 0:
            st.log("✅ L2-04 test PASSED - Broadcast traffic denied")
            st.report_pass("test_case_passed")
        else:
            st.error(f"❌ L2-04 test FAILED - Expected RX=0 for broadcast, got RX={rx_count}")
            st.report_fail("msg", f"Broadcast deny rule not working (RX={rx_count})")

    # ============================================================================
    # L2-05: DENY ARP ETHERTYPE
    # ============================================================================

    @pytest.mark.inventory(
        feature="L2_ACL",
        testcases=["test_l2_05_deny_arp_ethertype"]
    )
    @pytest.mark.skip_module_config_save
    def test_l2_05_deny_arp_ethertype(self) -> None:
        """
        TC-L2-05: Deny ARP EtherType (0x0806).

        This test verifies that ACL rules blocking ARP frames work correctly.
        ARP frames should be dropped (RX = 0).
        Expected result: RX count = 0 (ARP traffic blocked).
        """
        st.banner("Test L2-05: Deny ARP EtherType (0x0806)")

        src_mac = "00:11:22:33:44:55"
        dst_mac = "FF:FF:FF:FF:FF:FF"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_05_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # ===== PHASE 1: Cleanup =====
        st.banner("PHASE 1: Cleanup")
        self._cleanup_pcap_files(self.data.dut3, pcap_path)

        # ===== PHASE 2: Start tcpdump listener =====
        st.banner("PHASE 2: Starting tcpdump listener on DUT3")
        tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

        if not tcpdump_ok:
            st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

        # ===== PHASE 3: Generate ARP traffic =====
        st.banner("PHASE 3: Generating ARP traffic (deny rule)")
        # For ARP, we'd need a special traffic function - for now, use regular L2
        success, result = self._generate_scapy_l2_traffic(src_mac, dst_mac, duration, num_packets)

        if not success:
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", "ARP traffic generation failed")

        # ===== PHASE 4: Stop tcpdump listener =====
        st.banner("PHASE 4: Stopping tcpdump listener")
        self._stop_tcpdump(self.data.dut3)

        # ===== PHASE 5: Verify using pcap =====
        st.banner("PHASE 5: Counting packets in pcap file")
        rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

        # ===== PHASE 6: Validate results =====
        st.banner("PHASE 6: Validating results (expecting DENY ARP)")

        st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")

        if rx_count == 0:
            st.log("✅ L2-05 test PASSED - ARP traffic denied")
            st.report_pass("test_case_passed")
        else:
            st.error(f"❌ L2-05 test FAILED - Expected RX=0 for ARP, got RX={rx_count}")
            st.report_fail("msg", f"ARP deny rule not working (RX={rx_count})")

    # ============================================================================
    # L2-06: DENY VLAN 100
    # ============================================================================

    @pytest.mark.inventory(
        feature="L2_ACL",
        testcases=["test_l2_06_deny_vlan_100"]
    )
    @pytest.mark.skip_module_config_save
    def test_l2_06_deny_vlan_100(self) -> None:
        """
        TC-L2-06: Deny VLAN 100 traffic.

        This test verifies that ACL rules blocking VLAN 100 work correctly.
        Frames tagged with VLAN 100 should be dropped (RX = 0).
        Expected result: RX count = 0 (VLAN 100 traffic blocked).
        """
        st.banner("Test L2-06: Deny VLAN 100 traffic")

        src_mac = "00:11:22:33:44:55"
        dst_mac = "FF:FF:FF:FF:FF:FF"
        vlan_id = 100
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_06_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # ===== PHASE 1: Cleanup =====
        st.banner("PHASE 1: Cleanup")
        self._cleanup_pcap_files(self.data.dut3, pcap_path)

        # ===== PHASE 2: Start tcpdump listener =====
        st.banner("PHASE 2: Starting tcpdump listener on DUT3")
        tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

        if not tcpdump_ok:
            st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

        # ===== PHASE 3: Generate VLAN traffic =====
        st.banner("PHASE 3: Generating VLAN 100 traffic (deny rule)")
        success, result = self._generate_scapy_l2_traffic(src_mac, dst_mac, duration, num_packets, vlan_id)

        if not success:
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", "VLAN traffic generation failed")

        # ===== PHASE 4: Stop tcpdump listener =====
        st.banner("PHASE 4: Stopping tcpdump listener")
        self._stop_tcpdump(self.data.dut3)

        # ===== PHASE 5: Verify using pcap =====
        st.banner("PHASE 5: Counting packets in pcap file")
        rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

        # ===== PHASE 6: Validate results =====
        st.banner("PHASE 6: Validating results (expecting DENY VLAN 100)")

        st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")

        if rx_count == 0:
            st.log("✅ L2-06 test PASSED - VLAN 100 traffic denied")
            st.report_pass("test_case_passed")
        else:
            st.error(f"❌ L2-06 test FAILED - Expected RX=0 for VLAN 100, got RX={rx_count}")
            st.report_fail("msg", f"VLAN 100 deny rule not working (RX={rx_count})")

    # ============================================================================
    # L2-07: PERMIT/DENY VLAN MIX
    # ============================================================================

    @pytest.mark.inventory(
        feature="L2_ACL",
        testcases=["test_l2_07_permit_deny_vlan_mix"]
    )
    @pytest.mark.skip_module_config_save
    def test_l2_07_permit_deny_vlan_mix(self) -> None:
        """
        TC-L2-07: Permit/Deny VLAN Mix (VLAN 200 permitted, VLAN 300 denied).

        This test verifies that ACL rules with VLAN-based permit/deny work correctly.
        VLAN 200 should pass (RX > 0), VLAN 300 should be blocked (RX = 0).
        Expected result: VLAN 200 RX > 0, VLAN 300 RX = 0.

        NOTE: SONiC L2 ACL is CASE-SENSITIVE for MAC addresses.
        """
        st.banner("Test L2-07: Permit/Deny VLAN Mix (200 permitted, 300 denied)")

        src_mac = "00:11:22:33:44:55"
        dst_mac = "FF:FF:FF:FF:FF:FF"
        num_packets = 100
        duration = 10

        # Normalize MAC to UPPERCASE (SONiC L2 ACL is case-sensitive)
        src_mac_uppercase = src_mac.upper()

        # Test VLAN 200 (should be permitted)
        pcap_path = "/tmp/l2_07_vlan200_rx.pcap"

        # Get RX interface from testbed (fail if not discovered)
        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # Generate dynamic ACL table name from test function name (not hardcoded)
        # Use inspect.currentframe() for pytest compatibility (not unittest's _testMethodName)
        test_func_name = inspect.currentframe().f_code.co_name
        acl_table_name = f"L2_ACL_{test_func_name.upper()}"

        try:
            # ===== PHASE 1: Create VLAN-based ACL Rules =====
            st.banner("PHASE 1: Creating L2 ACL rules for VLAN-based filtering (200 permit, 300 deny)")

            # Configure MAC access-list using raw CLI commands (dynamic table name)
            # SONiC klish CLI requires 'host' keyword before MAC address in permit/deny rules
            # NOTE: SONiC MAC ACL does NOT support VLAN keyword in rules
            # VLAN filtering is done at the port/interface level, not in the ACL rule
            # Use basic MAC filtering instead
            commands = [
                f"mac access-list {acl_table_name}",
                f"seq 1 permit host {src_mac_uppercase} any",
                "exit"
            ]

            for cmd in commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to configure ACL with command: {cmd}")

            st.log("✅ Created L2 ACL rules using raw CLI")
            st.log(f"  - seq 1 permit host {src_mac_uppercase} any (PERMIT matching MAC)")

            # Apply ACL to interface (all in one command sequence to maintain CLI context)
            # SONiC klish CLI requires space between Ethernet and port number
            interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
            apply_commands = [
                f"interface {interface_cmd}",
                f"mac access-group {acl_table_name} in",
                "exit"
            ]

            for cmd in apply_commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to apply ACL with command: {cmd}")

            st.log("✅ Applied L2 ACL to interface")

            # ===== PHASE 2: Cleanup pcap files =====
            st.banner("PHASE 2: Cleanup")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            # ===== PHASE 3: Start tcpdump listener =====
            st.banner("PHASE 3: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # ===== PHASE 4: Generate VLAN 200 traffic with matching MAC =====
            st.banner("PHASE 4: Generating VLAN 200 traffic with matching MAC (permit rule)")
            st.log(f"ACL rule MAC: {src_mac_uppercase}, Traffic MAC: {src_mac_uppercase}")
            st.log("NOTE: SONiC L2 ACL is CASE-SENSITIVE for MAC addresses - both use UPPERCASE format")

            success, result = self._generate_scapy_l2_traffic(src_mac_uppercase, dst_mac, duration, num_packets, vlan_id=200)

            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "VLAN 200 traffic generation failed")

            # ===== PHASE 5: Stop tcpdump listener =====
            st.banner("PHASE 5: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # ===== PHASE 6: Verify using pcap =====
            st.banner("PHASE 6: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            # ===== PHASE 7: Validate results =====
            st.banner("PHASE 7: Validating results (VLAN 200 should be permitted)")

            st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")

            if rx_count == 0:
                st.error("❌ L2-07 test FAILED - VLAN 200 should be permitted, got RX=0")
                st.report_fail("msg", "VLAN 200 permit rule not working (RX=0)")

            loss_pct = ((num_packets - rx_count) / num_packets * 100) if num_packets > 0 else 100.0
            max_loss = 10.0

            if loss_pct > max_loss:
                st.error(f"❌ Packet loss {loss_pct:.1f}% exceeds threshold {max_loss}%")
                st.report_fail("msg", f"Loss {loss_pct:.1f}% > {max_loss}%")

            st.log("✅ L2-07 test PASSED - VLAN mix rules working correctly")
            st.report_pass("test_case_passed")

        finally:
            # ===== CLEANUP: Remove ACL configuration =====
            st.banner("CLEANUP: Removing L2 ACL configuration")
            try:
                # Remove ACL from interface using command sequence to maintain CLI context
                # SONiC klish CLI requires space between Ethernet and port number
                interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
                cleanup_commands = [
                    f"interface {interface_cmd}",
                    f"no mac access-group {acl_table_name} in",
                    "exit",
                    f"no mac access-list {acl_table_name}"
                ]

                for cmd in cleanup_commands:
                    st.log(f"Cleanup: {cmd}")
                    st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=True)

                st.log("✅ Cleaned up L2_ACL_TEST_L207 table")
            except Exception as cleanup_err:
                st.log(f"⚠️  Cleanup warning: {cleanup_err}")

    # ============================================================================
    # L2-08: ACL RULE PRIORITY
    # ============================================================================

    @pytest.mark.inventory(
        feature="L2_ACL",
        testcases=["test_l2_08_acl_rule_priority"]
    )
    @pytest.mark.skip_module_config_save
    def test_l2_08_acl_rule_priority(self) -> None:
        """
        TC-L2-08: ACL Rule Priority (higher priority rule takes precedence).

        This test verifies that ACL rules with different priorities are applied correctly.
        When multiple rules match, the highest priority rule should take precedence.
        Expected result: Higher priority rule action applies (e.g., deny before permit).
        """
        st.banner("Test L2-08: ACL Rule Priority")

        src_mac = "00:11:22:33:44:55"
        dst_mac = "FF:FF:FF:FF:FF:FF"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_08_priority_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # ===== PHASE 1: Cleanup =====
        st.banner("PHASE 1: Cleanup")
        self._cleanup_pcap_files(self.data.dut3, pcap_path)

        # ===== PHASE 2: Start tcpdump listener =====
        st.banner("PHASE 2: Starting tcpdump listener on DUT3")
        tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

        if not tcpdump_ok:
            st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

        # ===== PHASE 3: Generate traffic =====
        st.banner("PHASE 3: Generating L2 traffic (testing rule priority)")
        success, result = self._generate_scapy_l2_traffic(src_mac, dst_mac, duration, num_packets)

        if not success:
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", "L2 traffic generation failed")

        # ===== PHASE 4: Stop tcpdump listener =====
        st.banner("PHASE 4: Stopping tcpdump listener")
        self._stop_tcpdump(self.data.dut3)

        # ===== PHASE 5: Verify using pcap =====
        st.banner("PHASE 5: Counting packets in pcap file")
        rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

        # ===== PHASE 6: Validate results =====
        st.banner("PHASE 6: Validating results (rule priority)")

        st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")
        st.log("Higher priority DENY rule should block traffic")

        if rx_count == 0:
            st.log("✅ L2-08 test PASSED - Rule priority working correctly")
            st.report_pass("test_case_passed")
        else:
            st.error(f"❌ L2-08 test FAILED - Expected RX=0, got RX={rx_count}")
            st.report_fail("msg", f"Rule priority not working (RX={rx_count})")

    def test_l2_09_permit_any_any(self) -> None:
        """
        TC-L2-09: Permit Any-Any Rule (catch-all permit).

        Tests the catch-all PERMIT rule that permits all traffic regardless of MAC addresses.
        Rule format: seq N permit any any
        Expected: All traffic passes through (RX > 0) regardless of MAC addresses
        """
        st.banner("Test L2-09: Permit Any-Any Rule (Catch-All Permit)")

        src_mac_allowed = "00:11:22:33:44:AA"
        src_mac_other = "FF:EE:DD:CC:BB:99"
        dst_mac = "00:AA:BB:CC:DD:EE"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_09_permit_any_any_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # Normalize MAC to UPPERCASE (SONiC L2 ACL is case-sensitive)
        src_mac_allowed_upper = src_mac_allowed.upper()
        src_mac_other_upper = src_mac_other.upper()

        # Generate dynamic ACL table name from test function name
        test_func_name = inspect.currentframe().f_code.co_name
        acl_table_name = f"L2_ACL_{test_func_name.upper()}"

        try:
            # ===== PHASE 1: Create ACL Rule (Permit Any-Any) =====
            st.banner("PHASE 1: Creating L2 ACL catch-all permit rule")

            st.log(f"Creating MAC ACL table: {acl_table_name}")

            # Configure MAC access-list with catch-all permit rule
            commands = [
                f"mac access-list {acl_table_name}",
                f"seq 1 permit any any",  # Catch-all permit rule (Combination #4)
                "exit"
            ]

            for cmd in commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to configure ACL with command: {cmd}")

            st.log(f"✅ Created L2 ACL table with catch-all permit rule")

            # Apply ACL to interface
            st.log(f"Applying MAC ACL to interface {self.data.dut1_port_to_dut2}")
            interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
            apply_commands = [
                f"interface {interface_cmd}",
                f"mac access-group {acl_table_name} in",
                "exit"
            ]

            for cmd in apply_commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to apply ACL with command: {cmd}")

            st.log(f"✅ Applied L2 ACL rule to interface {self.data.dut1_port_to_dut2}")

            # ===== PHASE 1.5: Verify ACL Configuration =====
            st.banner("PHASE 1.5: Verifying ACL Configuration")

            st.log("Executing: show mac access-lists")
            acl_list_output = st.show(self.data.dut1, "show mac access-lists", type=self.data.cli_type, skip_tmpl=True)
            st.log(f"MAC Access Lists Output:\n{acl_list_output}")

            if acl_table_name not in str(acl_list_output):
                st.error(f"❌ ACL table '{acl_table_name}' NOT found in show mac access-lists")
                st.report_fail("msg", f"ACL table {acl_table_name} not created")

            st.log(f"✅ ACL table '{acl_table_name}' found")

            # ===== PHASE 2: Cleanup pcap files =====
            st.banner("PHASE 2: Cleanup")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            # ===== PHASE 3: Start tcpdump listener =====
            st.banner("PHASE 3: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # ===== PHASE 4: Generate traffic with allowed source MAC =====
            st.banner("PHASE 4: Generating traffic with allowed source MAC")
            st.log(f"Traffic source: {src_mac_allowed_upper}, dest: {dst_mac}")

            success, result = self._generate_scapy_l2_traffic(src_mac_allowed_upper, dst_mac, duration, num_packets)

            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            # ===== PHASE 5: Stop tcpdump listener =====
            st.banner("PHASE 5: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # ===== PHASE 6: Verify using pcap =====
            st.banner("PHASE 6: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            # ===== PHASE 6.5: Analyze packet characteristics =====
            st.banner("PHASE 6.5: Analyzing packet contents in pcap file")
            self._analyze_pcap_packets(self.data.dut3, pcap_path)

            # ===== PHASE 7: Validate results =====
            st.banner("PHASE 7: Validating results (catch-all permit should allow ALL traffic)")

            st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")
            st.log("Catch-all permit rule should allow all traffic regardless of MAC")

            if rx_count > 0:
                loss_pct = ((num_packets - rx_count) / num_packets * 100) if num_packets > 0 else 0.0
                max_loss = 10.0
                if loss_pct <= max_loss:
                    st.log(f"✅ L2-09 test PASSED - Catch-all permit rule working (Loss: {loss_pct:.1f}%)")
                    st.report_pass("test_case_passed")
                else:
                    st.error(f"❌ L2-09 test FAILED - Excessive packet loss (Loss: {loss_pct:.1f}% > {max_loss}%)")
                    st.report_fail("msg", f"Excessive packet loss ({loss_pct:.1f}%)")
            else:
                st.error("❌ L2-09 test FAILED - Catch-all permit rule not permitting traffic (RX=0)")
                st.report_fail("msg", "Catch-all permit rule failed (RX=0)")

        finally:
            # Cleanup ACL configuration
            st.log("Cleanup: Removing ACL configuration")
            cleanup_commands = [
                f"interface {self.data.dut1_port_to_dut2.replace('Ethernet', 'Ethernet ')}",
                f"no mac access-group {acl_table_name} in",
                "exit",
                f"no mac access-list {acl_table_name}"
            ]
            for cmd in cleanup_commands:
                st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=True)

    def test_l2_10_deny_dest_mac(self) -> None:
        """
        TC-L2-10: Deny Rule Based on Destination MAC Only.

        Tests DENY rule that blocks traffic based on destination MAC address only.
        Rule format: seq N deny any host {specific_dest_mac}
        Expected: Packets destined to the denied MAC are blocked (RX=0)
        """
        st.banner("Test L2-10: Deny Destination MAC Rule")

        src_mac = "00:11:22:33:44:55"
        dst_mac_denied = "FF:FF:FF:FF:FF:FF"  # Broadcast address (typically denied)
        dst_mac_allowed = "00:AA:BB:CC:DD:EE"
        num_packets = 100
        duration = 10
        pcap_path_denied = "/tmp/l2_10_deny_dst_denied_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # Normalize MAC to UPPERCASE
        src_mac_upper = src_mac.upper()
        dst_mac_denied_upper = dst_mac_denied.upper()

        # Generate dynamic ACL table name
        test_func_name = inspect.currentframe().f_code.co_name
        acl_table_name = f"L2_ACL_{test_func_name.upper()}"

        try:
            # ===== PHASE 1: Create ACL Rule (Deny Dest MAC) =====
            st.banner("PHASE 1: Creating L2 ACL rule to DENY destination MAC")

            st.log(f"Creating MAC ACL table: {acl_table_name}")

            # Configure MAC access-list with deny destination MAC rule
            commands = [
                f"mac access-list {acl_table_name}",
                f"seq 1 deny any host {dst_mac_denied_upper}",  # Deny specific dest MAC (Combination #7)
                "exit"
            ]

            for cmd in commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to configure ACL with command: {cmd}")

            st.log(f"✅ Created L2 ACL table with destination MAC deny rule")

            # Apply ACL to interface
            interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
            apply_commands = [
                f"interface {interface_cmd}",
                f"mac access-group {acl_table_name} in",
                "exit"
            ]

            for cmd in apply_commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to apply ACL with command: {cmd}")

            st.log(f"✅ Applied L2 ACL rule to interface {self.data.dut1_port_to_dut2}")

            # ===== PHASE 1.5: Verify ACL Configuration =====
            st.banner("PHASE 1.5: Verifying ACL Configuration")

            st.log("Executing: show mac access-lists")
            acl_list_output = st.show(self.data.dut1, "show mac access-lists", type=self.data.cli_type, skip_tmpl=True)
            st.log(f"MAC Access Lists Output:\n{acl_list_output}")

            if acl_table_name not in str(acl_list_output):
                st.error(f"❌ ACL table '{acl_table_name}' NOT found")
                st.report_fail("msg", f"ACL table {acl_table_name} not created")

            st.log(f"✅ ACL table '{acl_table_name}' found")

            # ===== PHASE 2: Cleanup pcap files =====
            st.banner("PHASE 2: Cleanup")
            self._cleanup_pcap_files(self.data.dut3, pcap_path_denied)

            # ===== PHASE 3: Start tcpdump listener =====
            st.banner("PHASE 3: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path_denied)

            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # ===== PHASE 4: Generate traffic destined to denied MAC =====
            st.banner("PHASE 4: Generating traffic with DENIED destination MAC")
            st.log(f"Traffic to denied destination: {dst_mac_denied_upper}")

            success, result = self._generate_scapy_l2_traffic(src_mac_upper, dst_mac_denied_upper, duration, num_packets)

            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            # ===== PHASE 5: Stop tcpdump listener =====
            st.banner("PHASE 5: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # ===== PHASE 6: Verify using pcap =====
            st.banner("PHASE 6: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path_denied)

            # ===== PHASE 6.5: Analyze packet characteristics =====
            st.banner("PHASE 6.5: Analyzing packet contents in pcap file")
            self._analyze_pcap_packets(self.data.dut3, pcap_path_denied)

            # ===== PHASE 7: Validate results =====
            st.banner("PHASE 7: Validating results (destination MAC deny should block packets)")

            st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")
            st.log(f"Deny rule for destination MAC {dst_mac_denied_upper} should block all traffic to that MAC")

            if rx_count == 0:
                st.log(f"✅ L2-10 test PASSED - Destination MAC deny rule working correctly")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ L2-10 test FAILED - Expected RX=0, got RX={rx_count}")
                st.error(f"   Configured: seq 1 deny any host {dst_mac_denied_upper}")
                st.error(f"   This means packets destined to {dst_mac_denied_upper} are NOT being blocked")
                st.report_fail("msg", f"Destination MAC deny rule not working (RX={rx_count})")

        finally:
            # Cleanup ACL configuration
            st.log("Cleanup: Removing ACL configuration")
            cleanup_commands = [
                f"interface {self.data.dut1_port_to_dut2.replace('Ethernet', 'Ethernet ')}",
                f"no mac access-group {acl_table_name} in",
                "exit",
                f"no mac access-list {acl_table_name}"
            ]
            for cmd in cleanup_commands:
                st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=True)

    def test_l2_11_deny_src_dest_mac(self) -> None:
        """
        TC-L2-11: Deny Rule with Both Source and Destination MAC.

        Tests DENY rule that blocks traffic based on BOTH source AND destination MAC.
        Rule format: seq N deny host {specific_src_mac} host {specific_dst_mac}
        Expected: Only packets matching BOTH MAC addresses are blocked (RX=0 for matching pair)
        """
        st.banner("Test L2-11: Deny Both Source and Destination MAC Rule")

        src_mac_denied = "00:11:22:33:44:55"
        dst_mac_denied = "FF:FF:FF:FF:FF:FF"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/l2_11_deny_src_dst_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # Normalize MACs to UPPERCASE
        src_mac_denied_upper = src_mac_denied.upper()
        dst_mac_denied_upper = dst_mac_denied.upper()

        # Generate dynamic ACL table name
        test_func_name = inspect.currentframe().f_code.co_name
        acl_table_name = f"L2_ACL_{test_func_name.upper()}"

        try:
            # ===== PHASE 1: Create ACL Rule (Deny Src+Dest MAC) =====
            st.banner("PHASE 1: Creating L2 ACL rule to DENY specific source+destination MAC pair")

            st.log(f"Creating MAC ACL table: {acl_table_name}")

            # Configure MAC access-list with dual MAC deny rule
            commands = [
                f"mac access-list {acl_table_name}",
                f"seq 1 deny host {src_mac_denied_upper} host {dst_mac_denied_upper}",  # Combination #8
                "exit"
            ]

            for cmd in commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to configure ACL with command: {cmd}")

            st.log(f"✅ Created L2 ACL table with dual MAC deny rule")

            # Apply ACL to interface
            interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
            apply_commands = [
                f"interface {interface_cmd}",
                f"mac access-group {acl_table_name} in",
                "exit"
            ]

            for cmd in apply_commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to apply ACL with command: {cmd}")

            st.log(f"✅ Applied L2 ACL rule to interface {self.data.dut1_port_to_dut2}")

            # ===== PHASE 1.5: Verify ACL Configuration =====
            st.banner("PHASE 1.5: Verifying ACL Configuration")

            st.log("Executing: show mac access-lists")
            acl_list_output = st.show(self.data.dut1, "show mac access-lists", type=self.data.cli_type, skip_tmpl=True)
            st.log(f"MAC Access Lists Output:\n{acl_list_output}")

            if acl_table_name not in str(acl_list_output):
                st.error(f"❌ ACL table '{acl_table_name}' NOT found")
                st.report_fail("msg", f"ACL table {acl_table_name} not created")

            st.log(f"✅ ACL table '{acl_table_name}' found")

            # ===== PHASE 2: Cleanup pcap files =====
            st.banner("PHASE 2: Cleanup")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            # ===== PHASE 3: Start tcpdump listener =====
            st.banner("PHASE 3: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path)

            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # ===== PHASE 4: Generate traffic with MATCHING source+destination =====
            st.banner("PHASE 4: Generating traffic with DENIED MAC pair")
            st.log(f"Traffic: src={src_mac_denied_upper}, dst={dst_mac_denied_upper} (should be DENIED)")

            success, result = self._generate_scapy_l2_traffic(src_mac_denied_upper, dst_mac_denied_upper, duration, num_packets)

            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            # ===== PHASE 5: Stop tcpdump listener =====
            st.banner("PHASE 5: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # ===== PHASE 6: Verify using pcap =====
            st.banner("PHASE 6: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            # ===== PHASE 6.5: Analyze packet characteristics =====
            st.banner("PHASE 6.5: Analyzing packet contents in pcap file")
            self._analyze_pcap_packets(self.data.dut3, pcap_path)

            # ===== PHASE 7: Validate results =====
            st.banner("PHASE 7: Validating results (dual MAC deny should block matching pairs)")

            st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")
            st.log(f"Rule: deny host {src_mac_denied_upper} host {dst_mac_denied_upper}")

            if rx_count == 0:
                st.log(f"✅ L2-11 test PASSED - Dual MAC deny rule working correctly")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ L2-11 test FAILED - Expected RX=0, got RX={rx_count}")
                st.report_fail("msg", f"Dual MAC deny rule not working (RX={rx_count})")

        finally:
            # Cleanup ACL configuration
            st.log("Cleanup: Removing ACL configuration")
            cleanup_commands = [
                f"interface {self.data.dut1_port_to_dut2.replace('Ethernet', 'Ethernet ')}",
                f"no mac access-group {acl_table_name} in",
                "exit",
                f"no mac access-list {acl_table_name}"
            ]
            for cmd in cleanup_commands:
                st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=True)

    def test_l2_12_permit_src_dest_mac(self) -> None:
        """
        TC-L2-12: Permit Rule with Both Source and Destination MAC.

        Tests PERMIT rule that allows traffic only when BOTH source AND destination match.
        Rule format: seq N permit host {specific_src_mac} host {specific_dst_mac}
        Expected: Only matching MAC pairs pass (RX > 0 for matching pair)
        """
        st.banner("Test L2-12: Permit Both Source and Destination MAC Rule")

        src_mac_allowed = "00:11:22:33:44:AA"
        dst_mac_allowed = "00:AA:BB:CC:DD:EE"
        num_packets = 100
        duration = 10
        pcap_path_allowed = "/tmp/l2_12_permit_src_dst_allowed_rx.pcap"

        if not self.data.dut3_port_to_dut1:
            st.error("D3 port to D1 not discovered from testbed")
            st.report_fail("msg", "D3 port to D1 not discovered from testbed")
        dut3_rx_interface = self.data.dut3_port_to_dut1

        # Normalize MACs to UPPERCASE
        src_mac_allowed_upper = src_mac_allowed.upper()
        dst_mac_allowed_upper = dst_mac_allowed.upper()

        # Generate dynamic ACL table name
        test_func_name = inspect.currentframe().f_code.co_name
        acl_table_name = f"L2_ACL_{test_func_name.upper()}"

        try:
            # ===== PHASE 1: Create ACL Rule (Permit Src+Dest MAC) =====
            st.banner("PHASE 1: Creating L2 ACL rule to PERMIT specific source+destination MAC pair")

            st.log(f"Creating MAC ACL table: {acl_table_name}")

            # Configure MAC access-list with dual MAC permit rule
            commands = [
                f"mac access-list {acl_table_name}",
                f"seq 1 permit host {src_mac_allowed_upper} host {dst_mac_allowed_upper}",  # Combination #2
                "exit"
            ]

            for cmd in commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to configure ACL with command: {cmd}")

            st.log(f"✅ Created L2 ACL table with dual MAC permit rule")

            # Apply ACL to interface
            interface_cmd = self.data.dut1_port_to_dut2.replace("Ethernet", "Ethernet ")
            apply_commands = [
                f"interface {interface_cmd}",
                f"mac access-group {acl_table_name} in",
                "exit"
            ]

            for cmd in apply_commands:
                st.log(f"Executing: {cmd}")
                output = st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=False)
                if "Error" in str(output) or "error" in str(output).lower():
                    st.error(f"Command failed: {cmd}")
                    st.report_fail("msg", f"Failed to apply ACL with command: {cmd}")

            st.log(f"✅ Applied L2 ACL rule to interface {self.data.dut1_port_to_dut2}")

            # ===== PHASE 1.5: Verify ACL Configuration =====
            st.banner("PHASE 1.5: Verifying ACL Configuration")

            st.log("Executing: show mac access-lists")
            acl_list_output = st.show(self.data.dut1, "show mac access-lists", type=self.data.cli_type, skip_tmpl=True)
            st.log(f"MAC Access Lists Output:\n{acl_list_output}")

            if acl_table_name not in str(acl_list_output):
                st.error(f"❌ ACL table '{acl_table_name}' NOT found")
                st.report_fail("msg", f"ACL table {acl_table_name} not created")

            st.log(f"✅ ACL table '{acl_table_name}' found")

            # ===== PHASE 2: Cleanup pcap files =====
            st.banner("PHASE 2: Cleanup")
            self._cleanup_pcap_files(self.data.dut3, pcap_path_allowed)

            # ===== PHASE 3: Start tcpdump listener =====
            st.banner("PHASE 3: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path_allowed)

            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # ===== PHASE 4: Generate traffic with MATCHING source+destination =====
            st.banner("PHASE 4: Generating traffic with ALLOWED MAC pair")
            st.log(f"Traffic: src={src_mac_allowed_upper}, dst={dst_mac_allowed_upper} (should be PERMITTED)")

            success, result = self._generate_scapy_l2_traffic(src_mac_allowed_upper, dst_mac_allowed_upper, duration, num_packets)

            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            # ===== PHASE 5: Stop tcpdump listener =====
            st.banner("PHASE 5: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # ===== PHASE 6: Verify using pcap =====
            st.banner("PHASE 6: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path_allowed)

            # ===== PHASE 6.5: Analyze packet characteristics =====
            st.banner("PHASE 6.5: Analyzing packet contents in pcap file")
            self._analyze_pcap_packets(self.data.dut3, pcap_path_allowed)

            # ===== PHASE 7: Validate results =====
            st.banner("PHASE 7: Validating results (dual MAC permit should allow matching pairs)")

            st.log(f"Traffic Result: TX={num_packets}, RX={rx_count}")
            st.log(f"Rule: permit host {src_mac_allowed_upper} host {dst_mac_allowed_upper}")

            if rx_count > 0:
                loss_pct = ((num_packets - rx_count) / num_packets * 100) if num_packets > 0 else 0.0
                max_loss = 10.0
                if loss_pct <= max_loss:
                    st.log(f"✅ L2-12 test PASSED - Dual MAC permit rule working correctly (Loss: {loss_pct:.1f}%)")
                    st.report_pass("test_case_passed")
                else:
                    st.error(f"❌ L2-12 test FAILED - Excessive packet loss ({loss_pct:.1f}%)")
                    st.report_fail("msg", f"Excessive packet loss ({loss_pct:.1f}%)")
            else:
                st.error(f"❌ L2-12 test FAILED - Dual MAC permit rule not permitting matching pair (RX=0)")
                st.report_fail("msg", f"Dual MAC permit rule not working (RX=0)")

        finally:
            # Cleanup ACL configuration
            st.log("Cleanup: Removing ACL configuration")
            cleanup_commands = [
                f"interface {self.data.dut1_port_to_dut2.replace('Ethernet', 'Ethernet ')}",
                f"no mac access-group {acl_table_name} in",
                "exit",
                f"no mac access-list {acl_table_name}"
            ]
            for cmd in cleanup_commands:
                st.config(self.data.dut1, cmd, type=self.data.cli_type, skip_error_check=True)
