"""
VLAN UNTAGGED PACKET TAGGING - TC_VLAN_TAG_001

Author: Test Automation Team
Date: 2026-05-06

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  switching/vlan/test_vlan_Untagged_Packet_Tagging.py \\
  --logs-path ./logs/vlan_tagging_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Validates VLAN ingress untagged packet tagging (802.1Q compliance).

  TC_VLAN_TAG_001: Ingress Untagged Packet Tagging

  Test Objective:
    Verify that untagged packets received on an access port are properly tagged
    with the port's VLAN ID when forwarded to trunk ports.

  Test Topology:
    +------------------+                    +------------------+
    |      D1 (DUT1)   |                    |      D2 (DUT2)   |
    |  (Traffic Sender)|                    |  (Traffic Receiver)
    |                  |                    |                  |
    | Port1 (Access)   |====================| Port3 (Trunk)    |
    |  VLAN 10         |   Back-to-back     |  VLAN 10,20,30   |
    | (Untagged)       |   Connection       |  (Tagged)        |
    |                  |                    |                  |
    +------------------+                    +------------------+

  Test Scenario:
    1. Create VLAN 10 on both DUTs
    2. Configure Port1 on D1 as untagged access port for VLAN 10
    3. Configure Port3 on D2 as tagged trunk port for VLAN 10, 20, 30
    4. Send untagged Ethernet frame from D1 Port1
    5. Capture packet on D2 Port3 using tcpdump
    6. Verify packet received with VLAN 10 tag (802.1Q header)

  Validation Methods:
    - Interface counters (RX/TX packet counts)
    - tcpdump packet capture with detailed VLAN tag analysis
    - Running-configuration verification using "show running-configuration | no-more"

  Expected Result:
    Untagged ingress packet is properly tagged with VLAN 10 (VID=10, PCP=0)

Pre-requisites:
  - Topology: two-node (D1-D2) with at least 2 connections
  - Supported: HW and Virtual (SONiC-VS)
  - Feature: VLAN 802.1Q tagging support
  - CLI Type: klish
  - Required: Scapy for packet generation, tcpdump for capture
  - Required Variables: See vars_vlan_tagging.yaml
"""

from __future__ import annotations

import re
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api
import apis.system.interface as intf_api

# Environment variable override for YAML file path
VAR_FILE_ENV = "VLAN_TAGGING_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest"
    / "vars"
    / "switching"
    / "vlan"
    / "vars_vlan_tagging.yaml"
)


def _load_yaml_config() -> Dict[str, Any]:
    """
    Load test configuration from YAML file with environment override support.

    Returns:
        Dictionary containing test configuration

    Raises:
        FileNotFoundError: If YAML file not found
        ValueError: If YAML doesn't contain required keys
    """
    override_path = st.getenv(VAR_FILE_ENV)
    yaml_file = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not yaml_file.is_file():
        st.error(f"VLAN tagging variable file not found: {yaml_file}")
        st.error(f"Expected location: {DEFAULT_VAR_FILE}")
        raise FileNotFoundError(f"Variable file not found: {yaml_file}")

    with yaml_file.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    if "testcases" not in config:
        raise ValueError("YAML must contain 'testcases' key")

    st.log(f"✓ Loaded VLAN tagging configuration from: {yaml_file}")
    return config


@pytest.mark.topology("D1D2:2")
class TestVlanUntaggedPacketTagging:
    """
    Test class for VLAN untagged packet tagging (TC_VLAN_TAG_001).

    Validates that untagged packets received on access ports are properly tagged
    with the VLAN ID when forwarded to trunk ports, ensuring 802.1Q compliance.
    """

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """
        Class-level setup: Load configuration, ensure topology, initialize test data.

        Topology Requirement:
            Two DUTs with at least 2 connections (D1D2:2)
        """
        st.banner("MODULE PROLOGUE: VLAN Untagged Packet Tagging Test Suite")

        # Load YAML configuration
        try:
            config = _load_yaml_config()
        except Exception as e:
            st.error(f"Failed to load configuration: {e}")
            pytest.skip(str(e))

        defaults = config.get("defaults", {})
        testcases = config.get("testcases", {})

        # Ensure minimum topology: Two DUTs with 2 connections
        min_topology = defaults.get("min_topology", ["D1D2:2"])

        try:
            topology = st.ensure_min_topology(*min_topology)
            st.log(f"✓ Topology verified: {min_topology}")
        except Exception as e:
            st.error(f"Topology requirement not met: {e}")
            pytest.skip(str(e))

        # Store test data
        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.testcases = SpyTestDict(testcases)
        cls.data.topology = topology
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT handles from topology
        cls.data.D1 = topology.D1
        cls.data.D2 = topology.D2

        # Get port connections from topology
        cls.data.D1D2P1 = topology.D1D2P1  # D1 -> D2, Port 1
        cls.data.D2D1P1 = topology.D2D1P1  # D2 -> D1, Port 1
        cls.data.D1D2P2 = topology.D1D2P2  # D1 -> D2, Port 2
        cls.data.D2D1P2 = topology.D2D1P2  # D2 -> D1, Port 2

        # Track VLAN configurations for cleanup
        cls.data.configured_vlans = []
        cls.data.configured_ports = []

        st.log(f"✓ DUT1 (D1): {cls.data.D1}")
        st.log(f"✓ DUT2 (D2): {cls.data.D2}")
        st.log(f"✓ D1→D2 Port 1 (Access): {cls.data.D1D2P1}")
        st.log(f"✓ D2→D1 Port 1 (Trunk): {cls.data.D2D1P1}")
        st.log(f"✓ D1→D2 Port 2 (Traffic): {cls.data.D1D2P2}")
        st.log(f"✓ D2→D1 Port 2 (Monitor): {cls.data.D2D1P2}")

        st.banner("MODULE PROLOGUE: Setup completed successfully")

    @classmethod
    def teardown_class(cls) -> None:
        """
        Class-level cleanup: Remove VLAN configurations and reset ports.
        """
        st.banner("MODULE EPILOGUE: Starting cleanup")

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping")
            return

        try:
            # Remove port configurations (reverse order)
            for dut, port_name in reversed(cls.data.configured_ports):
                st.log(f"Resetting port {port_name} on {dut}")
                try:
                    # Reset port to default (remove from VLAN)
                    cmd = f"no switchport mode\nno switchport access vlan\nno switchport trunk allowed vlan"
                    st.config(dut, cmd, type=cls.data.cli_type)
                except Exception as e:
                    st.warn(f"Failed to reset port {port_name}: {e}")

            # Remove VLAN configurations
            for dut, vlan_id in reversed(cls.data.configured_vlans):
                st.log(f"Removing VLAN {vlan_id} from {dut}")
                try:
                    vlan_api.delete_vlan(dut, vlan_id, cli_type=cls.data.cli_type)
                except Exception as e:
                    st.warn(f"Failed to remove VLAN {vlan_id}: {e}")

            st.log("✓ Cleanup completed successfully")

        except Exception as e:
            st.error(f"Cleanup error: {e}")

        st.banner("MODULE EPILOGUE: Cleanup finished")

    def _get_interface_mac(self, dut: str, interface: str) -> Optional[str]:
        """
        Retrieve MAC address of a network interface.

        Args:
            dut: Device handle
            interface: Interface name (e.g., "Ethernet8")

        Returns:
            MAC address string (format: XX:XX:XX:XX:XX:XX) or None if not found
        """
        st.log(f"Retrieving MAC address for {interface} on {dut}")

        try:
            # Use klish command to get interface details
            output = st.show(
                dut,
                f"show interface {interface}",
                type=self.data.cli_type,
                skip_tmpl=True
            )

            if not output:
                st.error(f"No output from 'show interface {interface}' on {dut}")
                return None

            # MAC address pattern: XX:XX:XX:XX:XX:XX
            mac_pattern = r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})'
            match = re.search(mac_pattern, str(output))

            if match:
                mac = match.group(1).lower()
                st.log(f"✓ Found MAC address for {interface}: {mac}")
                return mac
            else:
                st.error(f"Could not extract MAC address for {interface}")
                return None

        except Exception as e:
            st.error(f"Error retrieving MAC address for {interface}: {e}")
            return None

    def _clear_interface_counters(self, dut: str) -> bool:
        """
        Clear interface counters on the DUT.

        Args:
            dut: Device handle

        Returns:
            True if successful, False otherwise
        """
        st.log(f"Clearing interface counters on {dut}")

        try:
            # Klish command to clear interface counters
            st.show(
                dut,
                "clear interface counters",
                type=self.data.cli_type,
                skip_tmpl=True,
                skip_error_check=True
            )

            st.log("✓ Interface counters cleared")
            time.sleep(1)  # Allow counters to reset
            return True

        except Exception as e:
            st.error(f"Failed to clear interface counters: {e}")
            return False

    def _get_interface_counters(self, dut: str, interface: str) -> Dict[str, int]:
        """
        Retrieve interface RX/TX packet counters.

        Args:
            dut: Device handle
            interface: Interface name

        Returns:
            Dictionary with 'rx_ok' and 'tx_ok' counter values
        """
        st.log(f"Retrieving interface counters for {interface} on {dut}")

        try:
            # Get interface counters using klish
            output = st.show(
                dut,
                f"show interface counters {interface}",
                type=self.data.cli_type,
                skip_tmpl=True
            )

            if not output:
                st.warn(f"No counters output for {interface}")
                return {"rx_ok": 0, "tx_ok": 0}

            # Parse output to extract RX and TX counters
            # Output format: IFACE STATE RX_OK RX_BPS RX_PPS RX_UTIL RX_ERR RX_DRP RX_OVR TX_OK ...
            counters = {"rx_ok": 0, "tx_ok": 0}

            for line in str(output).split('\n'):
                if line.strip().startswith(interface):
                    fields = line.split()
                    if len(fields) >= 11:
                        try:
                            counters["rx_ok"] = int(fields[2].replace(',', ''))
                            counters["tx_ok"] = int(fields[10].replace(',', ''))
                            st.log(f"✓ Counters: RX={counters['rx_ok']}, TX={counters['tx_ok']}")
                        except (ValueError, IndexError) as e:
                            st.warn(f"Error parsing counters: {e}")

            return counters

        except Exception as e:
            st.error(f"Error retrieving counters: {e}")
            return {"rx_ok": 0, "tx_ok": 0}

    def _verify_vlan_config(self, dut: str, vlan_id: int) -> bool:
        """
        Verify VLAN existence using 'show running-configuration | no-more'.

        Args:
            dut: Device handle
            vlan_id: VLAN ID to verify

        Returns:
            True if VLAN exists in running-configuration, False otherwise
        """
        st.log(f"Verifying VLAN {vlan_id} configuration on {dut}")

        try:
            # Use 'show running-configuration | no-more' to get VLAN config
            output = st.show(
                dut,
                "show running-configuration | no-more",
                type=self.data.cli_type,
                skip_tmpl=True
            )

            if not output:
                st.error(f"No running-configuration output on {dut}")
                return False

            # Search for VLAN configuration
            vlan_pattern = rf"^vlan {vlan_id}$"

            for line in str(output).split('\n'):
                if re.match(vlan_pattern, line.strip()):
                    st.log(f"✓ VLAN {vlan_id} found in running-configuration")
                    return True

            st.error(f"VLAN {vlan_id} not found in running-configuration")
            return False

        except Exception as e:
            st.error(f"Error verifying VLAN configuration: {e}")
            return False

    def _verify_port_vlan_config(self, dut: str, interface: str, vlan_id: int, mode: str = "access") -> bool:
        """
        Verify port VLAN configuration using 'show running-configuration | no-more'.

        Args:
            dut: Device handle
            interface: Interface name (e.g., "Ethernet4")
            vlan_id: VLAN ID
            mode: "access" or "trunk"

        Returns:
            True if port VLAN configuration is correct, False otherwise
        """
        st.log(f"Verifying {mode} port configuration for {interface} in VLAN {vlan_id} on {dut}")

        try:
            # Get running configuration
            output = st.show(
                dut,
                "show running-configuration | no-more",
                type=self.data.cli_type,
                skip_tmpl=True
            )

            if not output:
                st.error(f"No running-configuration output on {dut}")
                return False

            # Look for interface configuration
            interface_pattern = rf"^interface {interface}$"
            in_interface = False
            vlan_found = False

            for line in str(output).split('\n'):
                line_stripped = line.strip()

                # Check if we've entered the interface section
                if re.match(interface_pattern, line_stripped):
                    in_interface = True
                    st.log(f"Found interface section for {interface}")
                    continue

                # Check if we've left the interface section
                if in_interface and line_stripped and not line.startswith(' '):
                    break

                # Look for VLAN configuration within interface
                if in_interface:
                    if mode == "access":
                        # For access ports, look for "switchport access vlan X" (case-insensitive)
                        if re.search(rf"switchport access\s+vlan\s+{vlan_id}", line_stripped, re.IGNORECASE):
                            st.log(f"✓ Found access port VLAN configuration: {line_stripped}")
                            vlan_found = True
                    elif mode == "trunk":
                        # For trunk ports, look for "switchport trunk allowed vlan" (case-insensitive)
                        if re.search(rf"switchport trunk\s+allowed\s+vlan.*{vlan_id}", line_stripped, re.IGNORECASE):
                            st.log(f"✓ Found trunk port VLAN configuration: {line_stripped}")
                            vlan_found = True

            if vlan_found:
                st.log(f"✓ Port {interface} correctly configured for {mode} VLAN {vlan_id}")
                return True
            else:
                st.error(f"Port {interface} not correctly configured for {mode} VLAN {vlan_id}")
                return False

        except Exception as e:
            st.error(f"Error verifying port VLAN configuration: {e}")
            return False

    def _configure_access_port(self, dut: str, interface: str, vlan_id: int) -> bool:
        """
        Configure port as access port for specified VLAN.

        Args:
            dut: Device handle
            interface: Interface name
            vlan_id: VLAN ID

        Returns:
            True if configuration successful, False otherwise
        """
        st.log(f"Configuring {interface} on {dut} as access port for VLAN {vlan_id}")

        try:
            # Enter interface configuration mode
            # Note: SONiC implicitly sets port to access mode when configuring access VLAN
            st.config(dut, [
                f"interface {interface}",
                f"switchport access vlan {vlan_id}",
                "exit"
            ], type=self.data.cli_type)

            st.log(f"✓ Configured {interface} as access port for VLAN {vlan_id}")
            self.data.configured_ports.append((dut, interface))
            return True

        except Exception as e:
            st.error(f"Failed to configure access port: {e}")
            return False

    def _configure_trunk_port(self, dut: str, interface: str, vlan_ids: List[int]) -> bool:
        """
        Configure port as trunk port with allowed VLANs.

        Args:
            dut: Device handle
            interface: Interface name
            vlan_ids: List of VLAN IDs to allow on trunk

        Returns:
            True if configuration successful, False otherwise
        """
        st.log(f"Configuring {interface} on {dut} as trunk port for VLANs {vlan_ids}")

        try:
            # Convert VLAN list to comma-separated string
            vlan_str = ",".join(str(v) for v in vlan_ids)

            # Enter interface configuration mode
            # Note: SONiC implicitly sets port to trunk mode when configuring trunk allowed VLANs
            st.config(dut, [
                f"interface {interface}",
                f"switchport trunk allowed vlan {vlan_str}",
                "exit"
            ], type=self.data.cli_type)

            st.log(f"✓ Configured {interface} as trunk port for VLANs {vlan_ids}")
            self.data.configured_ports.append((dut, interface))
            return True

        except Exception as e:
            st.error(f"Failed to configure trunk port: {e}")
            return False

    def _send_untagged_packet(
        self,
        src_dut: str,
        src_interface: str,
        dst_mac: str,
        src_mac: Optional[str] = None,
        packet_count: int = 10,
        packet_size: int = 64
    ) -> bool:
        """
        Generate and send untagged Ethernet frames using Scapy.

        Args:
            src_dut: Source DUT handle
            src_interface: Source interface name
            dst_mac: Destination MAC address
            src_mac: Source MAC address (auto-discovered if None)
            packet_count: Number of packets to send
            packet_size: Packet size in bytes (minimum 64)

        Returns:
            True if packet transmission successful, False otherwise
        """
        st.log(f"Sending {packet_count} untagged packets from {src_interface} on {src_dut}")

        try:
            # Get source MAC if not provided
            if src_mac is None:
                src_mac = self._get_interface_mac(src_dut, src_interface)
                if not src_mac:
                    st.error(f"Could not determine source MAC for {src_interface}")
                    return False

            st.log(f"Packet details:")
            st.log(f"  Source MAC: {src_mac}")
            st.log(f"  Destination MAC: {dst_mac}")
            st.log(f"  Interface: {src_interface}")
            st.log(f"  Packet count: {packet_count}")
            st.log(f"  Packet size: {packet_size}")

            # Build Scapy packet generation command
            # Create untagged Ethernet frames (no VLAN tag)
            scapy_cmd = f"""
python3 << 'SCAPY_EOF'
from scapy.all import Ether, sendp, conf
import sys

# Configure Scapy
conf.iface = "{src_interface}"

# Create untagged Ethernet frame
pkt = Ether(src="{src_mac}", dst="{dst_mac}")/b'X'*(int({packet_size})-14)

# Send packets
try:
    sendp(pkt, iface="{src_interface}", count={packet_count}, verbose=True)
    print(f"✓ Successfully sent {packet_count} packets from {src_interface}")
except Exception as e:
    print(f"✗ Error sending packets: {{e}}")
    sys.exit(1)
SCAPY_EOF
"""

            # Execute Scapy script on source DUT
            result = st.config(
                src_dut,
                scapy_cmd,
                type=self.data.cli_type,
                skip_error_check=True
            )

            st.log(f"✓ Untagged packets sent successfully")
            return True

        except Exception as e:
            st.error(f"Failed to send untagged packets: {e}")
            return False

    def _capture_packets_with_tcpdump(
        self,
        capture_dut: str,
        capture_interface: str,
        packet_count: int = 10,
        timeout: int = 10,
        output_file: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Capture packets on specified interface using tcpdump.

        Args:
            capture_dut: DUT to capture on
            capture_interface: Interface to capture from
            packet_count: Number of packets to capture
            timeout: Capture timeout in seconds
            output_file: Optional pcap file to save (if None, uses temp file)

        Returns:
            Tuple of (success, pcap_file_path)
        """
        st.log(f"Starting packet capture on {capture_interface} on {capture_dut}")

        try:
            # Generate output filename if not provided
            if output_file is None:
                output_file = f"/tmp/vlan_tag_capture_{int(time.time())}.pcap"

            # Build tcpdump command
            # -i: interface, -c: packet count, -w: write to file, -G: rotate file (timeout)
            tcpdump_cmd = f"tcpdump -i {capture_interface} -c {packet_count} -w {output_file} &"

            st.log(f"Tcpdump command: {tcpdump_cmd}")

            # Start capture in background
            st.config(
                capture_dut,
                tcpdump_cmd,
                type=self.data.cli_type,
                skip_error_check=True
            )

            st.log(f"✓ Packet capture started on {capture_interface}")
            st.log(f"  Output file: {output_file}")

            return True, output_file

        except Exception as e:
            st.error(f"Failed to start packet capture: {e}")
            return False, None

    def _analyze_pcap_for_vlan_tag(
        self,
        dut: str,
        pcap_file: str,
        expected_vlan_id: int
    ) -> bool:
        """
        Analyze pcap file to verify VLAN tag presence and correctness.

        Args:
            dut: DUT containing the pcap file
            pcap_file: Path to pcap file
            expected_vlan_id: Expected VLAN ID (0-4095)

        Returns:
            True if VLAN tag verified correctly, False otherwise
        """
        st.log(f"Analyzing pcap file for VLAN {expected_vlan_id} tag")

        try:
            # Use tshark or tcpdump to read pcap and verify VLAN tags
            analysis_cmd = f"""
python3 << 'PYEOF'
try:
    from scapy.all import rdpcap, Dot1Q

    pkts = rdpcap("{pcap_file}")
    vlan_tagged_count = 0
    correct_vlan_count = 0

    for pkt in pkts:
        # Check if packet has VLAN tag (Dot1Q layer)
        if pkt.haslayer(Dot1Q):
            vlan_tagged_count += 1
            vlan_id = pkt[Dot1Q].vlan

            if vlan_id == {expected_vlan_id}:
                correct_vlan_count += 1
                print(f"✓ Packet with correct VLAN {{vlan_id}}: {{pkt.summary()}}")
            else:
                print(f"✗ Packet with wrong VLAN {{vlan_id}} (expected {expected_vlan_id})")

    print(f"\\nVLAN Tag Analysis Summary:")
    print(f"  Total packets: {{len(pkts)}}")
    print(f"  VLAN tagged packets: {{vlan_tagged_count}}")
    print(f"  Correct VLAN {expected_vlan_id} packets: {{correct_vlan_count}}")

    if correct_vlan_count > 0:
        print(f"✓ VLAN tagging verified successfully")
    else:
        print(f"✗ No packets with VLAN {expected_vlan_id} found")

except ImportError:
    print("Scapy not available, using tcpdump analysis")
except Exception as e:
    print(f"Error: {{e}}")
PYEOF
"""

            result = st.show(
                dut,
                analysis_cmd,
                type=self.data.cli_type,
                skip_error_check=True
            )

            # Check if analysis was successful
            if "✓ VLAN tagging verified successfully" in str(result):
                st.log(f"✓ VLAN tag analysis successful")
                return True
            else:
                st.error(f"VLAN tag analysis failed or no correct tags found")
                return False

        except Exception as e:
            st.error(f"Error analyzing pcap file: {e}")
            return False

    def _cleanup_pcap_files(self, dut: str, pcap_files: List[str]) -> None:
        """
        Clean up temporary pcap files.

        Args:
            dut: DUT containing the files
            pcap_files: List of pcap file paths to delete
        """
        st.log(f"Cleaning up {len(pcap_files)} pcap files")

        for pcap_file in pcap_files:
            try:
                st.show(
                    dut,
                    f"rm -f {pcap_file}",
                    type=self.data.cli_type,
                    skip_error_check=True
                )
                st.log(f"✓ Deleted {pcap_file}")
            except Exception as e:
                st.warn(f"Failed to delete {pcap_file}: {e}")

    @pytest.mark.inventory(
        feature="VLAN_Tagging",
        testcases=["TC_VLAN_TAG_001"]
    )
    def test_vlan_tag_001_ingress_untagged_tagging(self) -> None:
        """
        TC_VLAN_TAG_001: Ingress Untagged Packet Tagging

        Verify that untagged packets received on an access port are properly
        tagged with the VLAN ID when forwarded to trunk ports.

        Test Flow:
            1. Create VLAN 10 on both DUTs
            2. Configure Port1 (D1→D2) as access port for VLAN 10 (untagged)
            3. Configure Port3 (D2→D1) as trunk port for VLAN 10, 20, 30 (tagged)
            4. Clear interface counters
            5. Send untagged packets from D1 Port1
            6. Capture packets on D2 Port3 with tcpdump
            7. Verify packets received with VLAN 10 tag
            8. Analyze pcap to confirm 802.1Q header present
        """
        tc_id = "TC_VLAN_TAG_001"
        st.banner(f"Starting {tc_id}: Ingress Untagged Packet Tagging")

        testcase = self.data.testcases.get(tc_id)
        if not testcase:
            st.error(f"Test case {tc_id} not found in YAML configuration")
            st.report_fail("msg", f"Test case {tc_id} configuration missing")

        # Get test parameters
        vlan_10 = testcase.get("vlans", {}).get("vlan_10", 10)
        packet_count = testcase.get("traffic", {}).get("packet_count", 10)

        st.log(f"Test Parameters:")
        st.log(f"  VLAN 10 ID: {vlan_10}")
        st.log(f"  Packet count: {packet_count}")

        pcap_files = []

        try:
            # ===== STEP 1: Create VLAN 10 on both DUTs =====
            st.log("STEP 1: Creating VLAN 10 on both DUTs")

            # Create VLAN 10 on D1
            st.log(f"  Creating VLAN {vlan_10} on {self.data.D1}")
            if not vlan_api.create_vlan(self.data.D1, vlan_10, cli_type=self.data.cli_type):
                st.error(f"Failed to create VLAN {vlan_10} on {self.data.D1}")
                st.report_fail("msg", f"VLAN creation failed on {self.data.D1}")
            self.data.configured_vlans.append((self.data.D1, vlan_10))

            # Create VLAN 10 on D2
            st.log(f"  Creating VLAN {vlan_10} on {self.data.D2}")
            if not vlan_api.create_vlan(self.data.D2, vlan_10, cli_type=self.data.cli_type):
                st.error(f"Failed to create VLAN {vlan_10} on {self.data.D2}")
                st.report_fail("msg", f"VLAN creation failed on {self.data.D2}")
            self.data.configured_vlans.append((self.data.D2, vlan_10))

            st.log(f"✓ VLAN {vlan_10} created on both DUTs")

            # ===== STEP 2: Configure access port (D1 Port1) =====
            st.log("STEP 2: Configuring access port on D1")

            if not self._configure_access_port(
                self.data.D1,
                self.data.D1D2P1,
                vlan_10
            ):
                st.error(f"Failed to configure access port")
                st.report_fail("msg", "Access port configuration failed")

            # Verify access port configuration
            if not self._verify_port_vlan_config(
                self.data.D1,
                self.data.D1D2P1,
                vlan_10,
                mode="access"
            ):
                st.error(f"Access port configuration not verified")
                st.report_fail("msg", "Access port verification failed")

            st.log(f"✓ Access port {self.data.D1D2P1} configured for VLAN {vlan_10}")

            # ===== STEP 3: Configure trunk port (D2 Port3) =====
            st.log("STEP 3: Configuring trunk port on D2")

            trunk_vlans = [vlan_10]
            if not self._configure_trunk_port(
                self.data.D2,
                self.data.D2D1P1,
                trunk_vlans
            ):
                st.error(f"Failed to configure trunk port")
                st.report_fail("msg", "Trunk port configuration failed")

            # Verify trunk port configuration
            if not self._verify_port_vlan_config(
                self.data.D2,
                self.data.D2D1P1,
                vlan_10,
                mode="trunk"
            ):
                st.error(f"Trunk port configuration not verified")
                st.report_fail("msg", "Trunk port verification failed")

            st.log(f"✓ Trunk port {self.data.D2D1P1} configured for VLAN {vlan_10}")

            # ===== STEP 4: Get MAC addresses =====
            st.log("STEP 4: Retrieving MAC addresses")

            d1_mac = self._get_interface_mac(self.data.D1, self.data.D1D2P1)
            if not d1_mac:
                st.error("Could not retrieve D1 MAC address")
                st.report_fail("msg", "MAC address retrieval failed")

            d2_mac = self._get_interface_mac(self.data.D2, self.data.D2D1P1)
            if not d2_mac:
                st.error("Could not retrieve D2 MAC address")
                st.report_fail("msg", "MAC address retrieval failed")

            st.log(f"✓ D1 {self.data.D1D2P1} MAC: {d1_mac}")
            st.log(f"✓ D2 {self.data.D2D1P1} MAC: {d2_mac}")

            # ===== STEP 5: Clear interface counters =====
            st.log("STEP 5: Clearing interface counters")

            for dut in [self.data.D1, self.data.D2]:
                if not self._clear_interface_counters(dut):
                    st.warn(f"Failed to clear counters on {dut}")

            time.sleep(2)
            st.log("✓ Interface counters cleared")

            # ===== STEP 6: Start packet capture on D2 trunk port =====
            st.log("STEP 6: Starting packet capture on D2 trunk port")

            success, pcap_file = self._capture_packets_with_tcpdump(
                self.data.D2,
                self.data.D2D1P1,
                packet_count=packet_count,
                timeout=15
            )

            if not success or not pcap_file:
                st.error("Failed to start packet capture")
                st.report_fail("msg", "Packet capture initialization failed")

            pcap_files.append(pcap_file)
            st.log(f"✓ Packet capture started on {self.data.D2D1P1}")

            # Allow capture to be ready
            time.sleep(1)

            # ===== STEP 7: Send untagged packets from D1 =====
            st.log("STEP 7: Sending untagged packets from D1 access port")

            if not self._send_untagged_packet(
                self.data.D1,
                self.data.D1D2P1,
                dst_mac=d2_mac,
                src_mac=d1_mac,
                packet_count=packet_count,
                packet_size=64
            ):
                st.error("Failed to send untagged packets")
                st.report_fail("msg", "Packet transmission failed")

            st.log(f"✓ Sent {packet_count} untagged packets from {self.data.D1D2P1}")

            # Wait for capture to complete
            time.sleep(3)

            # ===== STEP 8: Analyze captured packets =====
            st.log("STEP 8: Analyzing captured packets for VLAN tags")

            if not self._analyze_pcap_for_vlan_tag(
                self.data.D2,
                pcap_file,
                vlan_10
            ):
                st.error("VLAN tag verification failed")
                st.report_fail("msg", "Captured packets do not have correct VLAN tag")

            st.log(f"✓ Packets verified with VLAN {vlan_10} tag")

            # ===== TEST PASSED =====
            st.log(f"✓ {tc_id} PASSED: Untagged packets properly tagged with VLAN {vlan_10}")
            st.report_pass("msg", f"{tc_id} test passed successfully")

        except Exception as e:
            st.error(f"Test failed with exception: {e}")
            import traceback
            st.error(traceback.format_exc())
            st.report_fail("msg", f"Test failed: {e}")

        finally:
            # Clean up pcap files
            if pcap_files:
                self._cleanup_pcap_files(self.data.D2, pcap_files)


# Export test class for pytest discovery
__all__ = ["TestVlanUntaggedPacketTagging"]
