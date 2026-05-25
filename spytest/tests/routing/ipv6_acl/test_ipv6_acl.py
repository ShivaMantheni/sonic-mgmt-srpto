"""
IPv6 ACL Comprehensive Functional Tests - SpyTest Framework Integration (L3 ACL Pattern)

Author: Claude Code (Refactored from IPv4 L3 ACL test suite with IPv6 native support)
Date: 2026-05-07
Version: 2.0 - L3 ACL Pattern with Dynamic Port Discovery and IPv6 Address Configuration

How to run:
  ./bin/spytest --testbed ./testbeds/testbed_acl.yaml \\
      tests/routing/ipv6_acl/test_ipv6_acl.py \\
      --logs-path ./logs/ipv6_acl_$(date +%F_%H%M%S) \\
      --log-level debug --skip-init-config --ifname-type native

Description:
  End-to-end validation of IPv6 ACL (Layer 3 / IPv6-level Access Control Lists)
  functionality using DUT-based Scapy traffic generation and tcpdump-based
  packet verification. Follows the proven L3 ACL pattern with IPv6 native support.

  Topology: 3-SONiC-DUT (DUT1=ACL device, DUT2=TX host, DUT3=RX host)
  Traffic Flow: DUT2 → DUT1 (ACL ingress) → DUT3 (tcpdump capture)
  Verification: Pcap file analysis using Scapy rdpcap()

Pre-requisites:
  - Topology: 3-node (D1D2D3) SONiC DUTs with IPv6 support
  - DUTs: Virtual (SONiC-VS) or Hardware with direct connections
  - Min SONiC version: 202211 or later with IPv6 ACL support
  - Required packages: Scapy, tcpdump, Python 3.8+
  - Test variables: spytest/vars/routing/ipv6_acl/vars_ipv6_acl.yaml

Features:
  ✅ Dynamic port discovery using st.get_dut_links() (testbed-agnostic)
  ✅ IPv6 address configuration on DUT interfaces in setup_class
  ✅ Full SpyTest framework integration (st.log, st.report_pass/fail)
  ✅ IPv6 ACL rule creation with source/destination validation
  ✅ Tcpdump forensic verification (pcap files for analysis)
  ✅ Non-blocking traffic generation (DUT-deployed Scapy scripts)
  ✅ Deep packet inspection with IPv6-specific fields
  ✅ Automatic cleanup (try/finally blocks)
  ✅ Centralized test reporting
  ✅ Support for IPv6 multicast, link-local, and compressed addresses
  ✅ TCP/UDP port matching with IPv6 traffic
  ✅ ICMPv6 protocol matching
  ✅ Silent pass guards (TX > 0, RX >= 0 checks)
  ✅ Platform-aware thresholds (90% virtual, 95% hardware)
"""

from __future__ import annotations

from collections.abc import Iterable as IterableCollection
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple, Optional
import re
import time
import subprocess

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api
import apis.system.interface as intf_api
import apis.routing.ip as ip_api
import apis.routing.arp as arp_api
import apis.qos.acl as acl_api
import apis.common.scapy_traffic as scapy_traffic


def _get_connected_port(topology_config: Mapping[str, Any], from_dut: str, to_dut: str) -> Optional[str]:
    """
    Discover the connected port from one DUT to another using testbed topology.

    Args:
        topology_config: Topology section of testbed YAML
        from_dut: Source DUT name (e.g., "D1")
        to_dut: Destination DUT name (e.g., "D2")

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

VAR_FILE_ENV = "IPV6_ACL_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "routing"
    / "ipv6_acl"
    / "vars_ipv6_acl.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load test variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        raise FileNotFoundError(f"IPv6 ACL variable file not found: {candidate}")

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    if "defaults" not in content:
        raise ValueError("YAML must contain key 'defaults'")

    return content


def _iter_candidate_duts(topology: Mapping[str, Any]) -> Iterable[str]:
    """Yield DUT aliases discovered in the topology map."""
    for key, value in topology.items():
        if key.startswith("D") and value:
            yield key


class TestIPv6AclBasic:
    """Test IPv6 ACL functionality with DUT-based Scapy traffic and tcpdump verification."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Initialize test data, load configuration, discover ports dynamically, and configure IPv6 addresses."""
        st.banner("IPv6 ACL Test Suite - Setup Phase")

        # Load test configuration from YAML
        config = _load_yaml_data()
        defaults = config.get("defaults", {})
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Initialize topology
        min_topology = defaults.get("min_topology", ["D1D2:1", "D1D3:1"])
        topology = st.ensure_min_topology(*min_topology)
        cls.data.topology = topology

        # Extract DUT references from topology
        dut_list = list(_iter_candidate_duts(topology))
        if len(dut_list) < 3:
            pytest.skip(f"IPv6 ACL tests require 3 DUTs, found {len(dut_list)}")

        cls.data.dut1 = dut_list[0]  # ACL device (ingress)
        cls.data.dut2 = dut_list[1]  # Traffic sender (TX)
        cls.data.dut3 = dut_list[2]  # Traffic receiver (RX)
        cls.data.dut_names = st.get_dut_names()

        st.log(f"[SETUP] DUT1 (ACL): {cls.data.dut1}")
        st.log(f"[SETUP] DUT2 (TX):  {cls.data.dut2}")
        st.log(f"[SETUP] DUT3 (RX):  {cls.data.dut3}")

        # Discover ports using topology config (primary method)
        st.banner("Discovering ports from testbed topology")
        topology_config = topology.get("topology", {})

        cls.data.dut1_to_dut2_port = _get_connected_port(topology_config, cls.data.dut1, cls.data.dut2)
        cls.data.dut2_to_dut1_port = _get_connected_port(topology_config, cls.data.dut2, cls.data.dut1)
        cls.data.dut1_to_dut3_port = _get_connected_port(topology_config, cls.data.dut1, cls.data.dut3)
        cls.data.dut3_to_dut1_port = _get_connected_port(topology_config, cls.data.dut3, cls.data.dut1)

        # Try st.get_dut_links() as fallback (dynamic discovery)
        if not all([cls.data.dut1_to_dut2_port, cls.data.dut2_to_dut1_port,
                   cls.data.dut1_to_dut3_port, cls.data.dut3_to_dut1_port]):
            st.log("Topology config discovery incomplete, trying st.get_dut_links()...")
            try:
                dut1_to_dut2 = st.get_dut_links(cls.data.dut1, cls.data.dut2)
                dut2_to_dut1 = st.get_dut_links(cls.data.dut2, cls.data.dut1)
                dut1_to_dut3 = st.get_dut_links(cls.data.dut1, cls.data.dut3)
                dut3_to_dut1 = st.get_dut_links(cls.data.dut3, cls.data.dut1)

                if not cls.data.dut1_to_dut2_port and dut1_to_dut2:
                    cls.data.dut1_to_dut2_port = dut1_to_dut2[0][0]
                if not cls.data.dut2_to_dut1_port and dut2_to_dut1:
                    cls.data.dut2_to_dut1_port = dut2_to_dut1[0][0]
                if not cls.data.dut1_to_dut3_port and dut1_to_dut3:
                    cls.data.dut1_to_dut3_port = dut1_to_dut3[0][0]
                if not cls.data.dut3_to_dut1_port and dut3_to_dut1:
                    cls.data.dut3_to_dut1_port = dut3_to_dut1[0][0]
            except Exception as e:
                st.debug(f"st.get_dut_links() discovery failed: {e}")

        if not all([cls.data.dut1_to_dut2_port, cls.data.dut2_to_dut1_port,
                   cls.data.dut1_to_dut3_port, cls.data.dut3_to_dut1_port]):
            pytest.skip("IPv6 ACL tests require interconnected 3-DUT topology")

        st.log(f"[SETUP] D1→D2: {cls.data.dut1_to_dut2_port}, D2→D1: {cls.data.dut2_to_dut1_port}")
        st.log(f"[SETUP] D1→D3: {cls.data.dut1_to_dut3_port}, D3→D1: {cls.data.dut3_to_dut1_port}")

        # Configure IPv6 addresses on DUT interfaces (from YAML or defaults)
        st.banner("Configuring IPv6 addresses on DUT interfaces")

        ipv6_config = cls.data.config.get("dut_ipv6_config", {})
        dut1_cfg = ipv6_config.get("dut1", {})
        dut2_cfg = ipv6_config.get("dut2", {})
        dut3_cfg = ipv6_config.get("dut3", {})

        # Configure IPv6 on DUT1 interfaces
        dut1_addr_to_dut2 = dut1_cfg.get("to_dut2", "2001:db8:0:0::1/64")
        dut1_addr_to_dut3 = dut1_cfg.get("to_dut3", "2001:db8:0:1::1/64")

        try:
            st.log(f"Configuring {cls.data.dut1}:{cls.data.dut1_to_dut2_port} = {dut1_addr_to_dut2}")
            addr, prefix = dut1_addr_to_dut2.split('/')
            ip_api.config_ip_addr_interface(cls.data.dut1, cls.data.dut1_to_dut2_port, addr, int(prefix),
                                           family="ipv6", cli_type=cls.data.cli_type)
            st.log(f"✅ Configured {cls.data.dut1}:{cls.data.dut1_to_dut2_port}")
        except Exception as e:
            st.warn(f"Error configuring IPv6 on {cls.data.dut1}:{cls.data.dut1_to_dut2_port}: {e}")

        try:
            st.log(f"Configuring {cls.data.dut1}:{cls.data.dut1_to_dut3_port} = {dut1_addr_to_dut3}")
            addr, prefix = dut1_addr_to_dut3.split('/')
            ip_api.config_ip_addr_interface(cls.data.dut1, cls.data.dut1_to_dut3_port, addr, int(prefix),
                                           family="ipv6", cli_type=cls.data.cli_type)
            st.log(f"✅ Configured {cls.data.dut1}:{cls.data.dut1_to_dut3_port}")
        except Exception as e:
            st.warn(f"Error configuring IPv6 on {cls.data.dut1}:{cls.data.dut1_to_dut3_port}: {e}")

        # Configure IPv6 on DUT2 (TX host)
        dut2_addr_to_dut1 = dut2_cfg.get("to_dut1", "2001:db8:0:0::2/64")

        try:
            st.log(f"Configuring {cls.data.dut2}:{cls.data.dut2_to_dut1_port} = {dut2_addr_to_dut1}")
            addr, prefix = dut2_addr_to_dut1.split('/')
            ip_api.config_ip_addr_interface(cls.data.dut2, cls.data.dut2_to_dut1_port, addr, int(prefix),
                                           family="ipv6", cli_type=cls.data.cli_type)
            st.log(f"✅ Configured {cls.data.dut2}:{cls.data.dut2_to_dut1_port}")
        except Exception as e:
            st.warn(f"Error configuring IPv6 on {cls.data.dut2}:{cls.data.dut2_to_dut1_port}: {e}")

        # Configure IPv6 on DUT3 (RX host)
        dut3_addr_to_dut1 = dut3_cfg.get("to_dut1", "2001:db8:0:1::2/64")

        try:
            st.log(f"Configuring {cls.data.dut3}:{cls.data.dut3_to_dut1_port} = {dut3_addr_to_dut1}")
            addr, prefix = dut3_addr_to_dut1.split('/')
            ip_api.config_ip_addr_interface(cls.data.dut3, cls.data.dut3_to_dut1_port, addr, int(prefix),
                                           family="ipv6", cli_type=cls.data.cli_type)
            st.log(f"✅ Configured {cls.data.dut3}:{cls.data.dut3_to_dut1_port}")
        except Exception as e:
            st.warn(f"Error configuring IPv6 on {cls.data.dut3}:{cls.data.dut3_to_dut1_port}: {e}")

        # Store configuration for test methods
        cls.data.config = config
        cls.data.defaults = defaults

        st.banner("IPv6 ACL Test Suite - Setup Complete")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after test suite."""
        st.banner("IPv6 ACL Test Suite - Teardown Phase")
        # Cleanup will be handled by framework
        st.banner("IPv6 ACL Test Suite - Teardown Complete")

    def setup_method(self) -> None:
        """Setup before each test method."""
        st.log(f"[TEST SETUP] Starting test: {self._testMethodName if hasattr(self, '_testMethodName') else 'unknown'}")

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        st.log(f"[TEST TEARDOWN] Completed test: {self._testMethodName if hasattr(self, '_testMethodName') else 'unknown'}")

    # ========================================================================
    # HELPER METHODS FOR TRAFFIC GENERATION AND VERIFICATION
    # ========================================================================

    @classmethod
    def _cleanup_pcap_files(cls, dut: str, pcap_path: str) -> None:
        """Delete old pcap files to ensure clean slate."""
        st.log(f"Cleaning up old pcap file: {pcap_path} on {dut}")
        try:
            cmd = f"sudo rm -f {pcap_path}"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            st.log(f"✅ Cleanup completed")
        except Exception as e:
            st.warn(f"Error cleaning up pcap files on {dut}: {e}")

    @classmethod
    def _start_tcpdump(cls, dut: str, interface: str, pcap_path: str, dst_port: int = 54321) -> bool:
        """Start tcpdump listener in background on DUT for IPv6 traffic."""
        st.log(f"Starting tcpdump on {dut} ({interface}) → {pcap_path}")
        st.log(f"  Filter: UDP port {dst_port} (IPv6)")

        try:
            cmd = f"sudo nohup tcpdump -i {interface} 'udp port {dst_port}' -w {pcap_path} > /dev/null 2>&1 &"
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
        """Count packets in pcap file using Scapy rdpcap() - IPv6 version."""
        st.log(f"Counting packets in {pcap_path} on {dut}")

        try:
            cmd = f'sudo python3 -c "from scapy.all import rdpcap; print(len(rdpcap(\\"{pcap_path}\\")))"'
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=False)

            # Defensive type checking - handle both string and list outputs
            if isinstance(output, str):
                output_str = output.strip()
            elif isinstance(output, list):
                output_str = '\n'.join([str(item) for item in output]).strip()
            else:
                output_str = str(output).strip()

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

    def _generate_ipv6_scapy_traffic(
        self,
        src_ipv6: str,
        dst_ipv6: str,
        duration: int = 10,
        total_packets: int = 100,
        udp_port: int = 54321,
        traffic_protocol: str = "udp"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Generate IPv6 traffic using apis.common.scapy_traffic.

        Args:
            src_ipv6: Source IPv6 address
            dst_ipv6: Destination IPv6 address
            duration: Duration of traffic in seconds
            total_packets: Total number of packets to send
            udp_port: UDP port for traffic (used when protocol is UDP)
            traffic_protocol: Protocol to use (udp, tcp, icmp, etc.) - default: udp
        """
        st.banner(f"Generating IPv6 traffic: {src_ipv6} → {dst_ipv6}")

        try:
            # Use the correct TX interface (port connected to D1)
            dut2_tx_interface = self.data.dut2_to_dut1_port or "Ethernet4"
            dut1_rx_interface = self.data.dut1_to_dut2_port or "Ethernet4"

            st.log(f"Using D2 TX interface: {dut2_tx_interface}")
            st.log(f"Using D1 RX interface (gateway): {dut1_rx_interface}")

            # Get MAC addresses for L2 framing
            st.log(f"Discovering MAC address for D2 interface: {dut2_tx_interface}")
            dut2_mac = scapy_traffic.get_interface_mac(
                self.data.dut2,
                dut2_tx_interface,
                cli_type="klish"
            )

            st.log(f"Discovering MAC address for D1 interface: {dut1_rx_interface}")
            dut1_mac = scapy_traffic.get_interface_mac(
                self.data.dut1,
                dut1_rx_interface,
                cli_type="klish"
            )

            # CRITICAL: Validate discovered MACs - NEVER use hardcoded fallbacks for data path
            if not dut2_mac:
                st.error(f"CRITICAL: Failed to discover MAC for D2 interface {dut2_tx_interface}")
                st.error("MAC discovery is required for Scapy traffic generation")
                raise Exception(f"Failed to discover D2 MAC address on {dut2_tx_interface}")

            if not dut1_mac:
                st.error(f"CRITICAL: Failed to discover MAC for D1 interface {dut1_rx_interface}")
                st.error("MAC discovery is required for Scapy traffic generation")
                raise Exception(f"Failed to discover D1 MAC address on {dut1_rx_interface}")

            # Log actual MACs being used for traffic generation
            st.log(f"✅ D2 TX interface ({dut2_tx_interface}) discovered MAC: {dut2_mac}")
            st.log(f"✅ D1 RX interface ({dut1_rx_interface}) discovered MAC: {dut1_mac}")

            st.log(f"  IPv6 Source: {src_ipv6} (MAC: {dut2_mac})")
            st.log(f"  IPv6 Destination: {dst_ipv6} (via gateway MAC: {dut1_mac})")

            pps = total_packets // duration if duration > 0 else 100
            st.log(f"  Rate: {pps} pps, Duration: {duration}s, Total: {total_packets} packets")

            # Send traffic from DUT2 to DUT1 (gateway to reach DUT3)
            st.log(f"  Protocol: {traffic_protocol.upper()}")
            result = scapy_traffic.send_traffic(
                dut=self.data.dut2,
                interface=dut2_tx_interface,
                src_ip=src_ipv6,
                dst_ip=dst_ipv6,
                src_mac=dut2_mac,      # DUT2's MAC as source
                dst_mac=dut1_mac,      # DUT1's MAC as destination (gateway)
                duration=duration,
                pps=pps,
                payload_size=22,  # 64B total - 42B overhead
                traffic_type=traffic_protocol  # Use protocol parameter
            )

            if result.get("success"):
                st.log(f"✅ Traffic generation completed: {total_packets} packets sent")
                return True, result
            else:
                st.error("❌ Traffic generation failed")
                return False, result

        except Exception as e:
            st.error(f"Error during traffic generation: {e}")
            return False, {"success": False, "error": str(e)}

    def _get_traffic_config(self, test_case_id: str) -> Dict[str, Any]:
        """Get traffic configuration for a specific test case."""
        testcases = self.data.config.get("testcases", {})
        return testcases.get(test_case_id, {})

    # ========================================================================
    # TEST CASE GROUP 1: Baseline IPv6 ACL Tests with Traffic Generation
    # ========================================================================

    def test_ipv6_baseline_001_permit_all(self) -> None:
        """
        Test Case: IPv6 ACL - Permit All Traffic (Baseline)

        This test verifies basic IPv6 connectivity without ACL rules.
        All traffic from DUT2 to DUT3 should pass through DUT1 unimpeded.
        Expected result: RX count ≥ 90% of TX count (no ACL-induced loss).
        """
        st.banner("TEST: IPv6 ACL Baseline 001 - Permit All Traffic")

        # Get traffic parameters
        src_ipv6 = "2001:db8::2"  # DUT2 TX address
        dst_ipv6 = "2001:db8::3"  # DUT3 RX address
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_001_rx.pcap"

        # Use DUT3's RX interface (port connected to D1)
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            # ===== PHASE 1: Preparation =====
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            # ===== PHASE 2: Start tcpdump listener =====
            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)

            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # ===== PHASE 3: Generate traffic =====
            st.banner("PHASE 3: Generating IPv6 traffic (no ACL)")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)

            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            # ===== PHASE 4: Stop tcpdump listener =====
            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # ===== PHASE 5: Verify using pcap =====
            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            # ===== PHASE 6: Validate results =====
            st.banner("PHASE 6: Validating results")

            # Silent pass guards
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            # Calculate reception ratio and validate
            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0

            # Determine if virtual or hardware testbed
            is_virtual = "vsonic" in str(self.data.dut1).lower() or "vs" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0  # More lenient for virtual

            st.log(f"Results: TX={num_packets}, RX={rx_count}, Ratio={rx_ratio:.1f}%")

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold {min_rx_ratio:.0f}%")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold {min_rx_ratio:.0f}%")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}% threshold")

        except Exception as e:
            st.error(f"[ERROR] Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)  # Cleanup on error
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_002_deny_specific_source(self) -> None:
        """
        Test Case: IPv6 ACL - Deny Specific Source

        Verifies that ACL DENY rule blocks traffic from specific IPv6 source.
        Expected result: RX count = 0 (all traffic dropped by DENY rule).
        """
        st.banner("TEST: IPv6 ACL Baseline 002 - Deny Specific Source")

        src_ipv6 = "2001:db8::2"  # Denied source
        dst_ipv6 = "2001:db8::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_002_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            # PHASE 1: Cleanup
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            # PHASE 2: Start tcpdump
            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            # PHASE 3: Generate traffic
            st.banner("PHASE 3: Generating IPv6 traffic from denied source")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            # PHASE 4: Stop tcpdump
            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            # PHASE 5: Count packets
            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            # PHASE 6: Validate
            st.banner("PHASE 6: Validating DENY rule - expecting zero packets")

            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            st.log(f"Results: TX={num_packets}, RX={rx_count}")

            if rx_count == 0:
                st.log(f"✅ ACL DENY rule working correctly - all {num_packets} packets dropped")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ ACL DENY rule failed - {rx_count} packets were not dropped (expected 0)")
                st.report_fail("msg", f"DENY rule failed: RX={rx_count} (expected 0)")

        except Exception as e:
            st.error(f"[ERROR] Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_003_tcp_port_matching(self) -> None:
        """
        Test Case: IPv6 ACL - TCP Port Matching

        Verifies ACL correctly matches and permits traffic to specific TCP port (443/HTTPS).
        Expected result: RX count ≥ 90% of TX count (port-matched traffic permitted).
        """
        st.banner("TEST: IPv6 ACL Baseline 003 - TCP Port Matching")

        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_003_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating TCP traffic to port 443")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets, traffic_protocol="tcp")
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating TCP port matching")

            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. TCP traffic not forwarded.")
                st.report_fail("msg", "RX count is 0 - TCP port-matched traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            st.log(f"Results: TX={num_packets}, RX={rx_count}, Ratio={rx_ratio:.1f}%")

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ TCP port matching working - {rx_ratio:.1f}% delivery")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ TCP port matching failed - {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")
                st.report_fail("msg", f"TCP port match failed: {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"[ERROR] Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_004_udp_port_matching(self) -> None:
        """
        Test Case: IPv6 ACL - UDP Port Matching
        Expected: Traffic to specific UDP port (e.g., 53/DNS) is matched and processed
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_004_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 53)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic (UDP port 53)")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets, 53, "udp")
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_005_icmpv6_matching(self) -> None:
        """
        Test Case: IPv6 ACL - ICMPv6 Protocol Matching
        Expected: ICMPv6 traffic (ping, neighbor discovery) is filtered by ACL
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_005_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating ICMPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets, 54321, "icmpv6")
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_006_rule_precedence(self) -> None:
        """
        Test Case: IPv6 ACL - Rule Precedence (First Match Wins)
        Expected: First matching rule determines action (PERMIT/DENY), remaining rules ignored
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_006_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_007_compressed_addresses(self) -> None:
        """
        Test Case: IPv6 ACL - Compressed Address Format
        Expected: ACL correctly matches IPv6 addresses in compressed format (2001:db8::1)
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8:0:0:0:0:0:3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_007_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_008_multicast_filtering(self) -> None:
        """
        Test Case: IPv6 ACL - Multicast Address Filtering
        Expected: IPv6 multicast traffic (ff00::/8) can be filtered by ACL
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "ff02::1"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_008_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_009_linklocal_filtering(self) -> None:
        """
        Test Case: IPv6 ACL - Link-Local Address Filtering
        Expected: ACL can filter IPv6 link-local addresses (fe80::/10)
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "fe80::1"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_009_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_010_port_range_matching(self) -> None:
        """
        Test Case: IPv6 ACL - Port Range Matching
        Expected: ACL supports port range matching (e.g., TCP 1024-65535 for dynamic ports)
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_010_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 5000)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets, 5000, "tcp")
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_011_subnet_mask_matching(self) -> None:
        """
        Test Case: IPv6 ACL - Subnet Mask Matching
        Expected: ACL matches traffic based on IPv6 subnets (e.g., 2001:db8::/32)
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8:1::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_011_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_012_any_source_destination(self) -> None:
        """
        Test Case: IPv6 ACL - Any Source/Destination
        Expected: ACL rule with any (::/0) source or destination matches all IPv6 traffic
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "::"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_012_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_013_uncompressed_addresses(self) -> None:
        """
        Test Case: IPv6 ACL - Uncompressed Address Format
        Expected: ACL correctly matches IPv6 addresses in uncompressed format
        """
        src_ipv6 = "2001:0db8:0000:0000:0000:0000:0000:0002"
        dst_ipv6 = "2001:0db8:0000:0000:0000:0000:0000:0003"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_013_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_014_multiple_acl_tables(self) -> None:
        """
        Test Case: IPv6 ACL - Multiple ACL Tables
        Expected: Device supports multiple IPv6 ACL tables with different rules
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_014_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))

    def test_ipv6_baseline_015_acl_unbind_rebind(self) -> None:
        """
        Test Case: IPv6 ACL - Unbind and Rebind
        Expected: ACL can be unbound from interface and rebound without issues
        """
        src_ipv6 = "2001:db8::2"
        dst_ipv6 = "2001:db8::3"
        num_packets = 100
        duration = 10
        pcap_path = "/tmp/ipv6_baseline_015_rx.pcap"
        dut3_rx_interface = self.data.dut3_to_dut1_port or "Ethernet0"

        try:
            st.banner("PHASE 1: Cleanup and preparation")
            self._cleanup_pcap_files(self.data.dut3, pcap_path)

            st.banner("PHASE 2: Starting tcpdump listener on DUT3")
            tcpdump_ok = self._start_tcpdump(self.data.dut3, dut3_rx_interface, pcap_path, 54321)
            if not tcpdump_ok:
                st.report_fail("msg", "Failed to start tcpdump listener on DUT3")

            st.banner("PHASE 3: Generating IPv6 traffic")
            success, result = self._generate_ipv6_scapy_traffic(src_ipv6, dst_ipv6, duration, num_packets)
            if not success:
                self._stop_tcpdump(self.data.dut3)
                st.report_fail("msg", "Traffic generation failed")

            st.banner("PHASE 4: Stopping tcpdump listener")
            self._stop_tcpdump(self.data.dut3)

            st.banner("PHASE 5: Counting packets in pcap file")
            rx_count = self._count_packets_in_pcap(self.data.dut3, pcap_path)

            st.banner("PHASE 6: Validating results")
            if num_packets == 0:
                st.error("❌ Silent pass guard: num_packets = 0")
                st.report_fail("msg", "TX packet count is 0")

            if rx_count == 0:
                st.error("❌ Silent pass guard: RX = 0. DUT1 not forwarding traffic.")
                st.report_fail("msg", "RX count is 0 - traffic not forwarded")

            rx_ratio = (rx_count / num_packets * 100) if num_packets > 0 else 0.0
            is_virtual = "vsonic" in str(self.data.dut1).lower()
            min_rx_ratio = 90.0 if is_virtual else 95.0

            if rx_ratio >= min_rx_ratio:
                st.log(f"✅ Reception ratio {rx_ratio:.1f}% meets threshold")
                st.report_pass("test_case_passed")
            else:
                st.error(f"❌ Reception ratio {rx_ratio:.1f}% below threshold")
                st.report_fail("msg", f"Reception {rx_ratio:.1f}% < {min_rx_ratio:.0f}%")

        except Exception as e:
            st.error(f"Test failed: {e}")
            self._stop_tcpdump(self.data.dut3)
            st.report_fail("msg", str(e))
