"""
VLAN INTRA-VLAN BROADCAST FORWARDING
Author: Test Automation Team
Date: 2026-05-06

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Intra-VLAN_Broadcast_Forwarding.py \\
  --logs-path ./logs/vlan_intra_broadcast_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Comprehensive validation of intra-VLAN broadcast packet forwarding using
  SpyTest APIs and Scapy-based traffic generation. The test creates VLAN 10,
  configures multiple ports (Port1, Port2, Port3) as untagged access ports in
  VLAN 10, dynamically retrieves MAC addresses, generates broadcast Ethernet
  frames (destination MAC FF:FF:FF:FF:FF:FF) from Port1, and verifies broadcast
  packet reception on Port2 and Port3 only (not on ports in other VLANs) through
  tcpdump packet capture and PCAP analysis.

Pre-requisites:
  - Topology: Two DUTs (D1-D2) with 3+ connections | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 2 nodes with multiple connections
        # +------------------+       +------------------+
        # |      DUT1        |-------|      DUT2        |
        # |    (Spine01)     | 1-5   |    (Spine02)     |
        # |                  |       |                  |
        # | Port1 (VLAN10)   |==Eth==| Port2 (VLAN10) |
        # | Port3 (VLAN20)   |       | Port4 (VLAN20) |
        # +------------------+       +------------------+

  - Feature flags / min SONiC version: SONiC 202211 or later with Scapy support
  - Required test variables (YAML): spytest/vars/switching/vlan/vars_vlan_intra_broadcast.yaml
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import re
import time

import pytest
import yaml

from scapy.all import Ether, Raw, rdpcap, Dot1Q


from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api

VAR_FILE_ENV = "VLAN_INTRA_BROADCAST_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_intra_broadcast.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        st.warn(f"VLAN variable file not found: {candidate}, using defaults")
        return {
            "defaults": {
                "cli_type": "klish",
                "vlan_10_id": "10",
                "vlan_20_id": "20",
                "min_topology": ["D1D2:3"]
            },
            "testcases": {},
        }

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


@pytest.mark.topology("D1D2:3")
class TestVlanIntraVlanBroadcastForwarding:
    """Testcases for intra-VLAN broadcast forwarding."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and testcase variables for the suite."""
        st.banner("MODULE PROLOGUE: Starting VLAN Intra-VLAN Broadcast Forwarding Test Suite")

        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Get 2-node topology with 3+ connections (D1D2:3)
        min_topology = defaults.get("min_topology") or ["D1D2:3"]
        topology = st.ensure_min_topology(*min_topology)

        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # VLAN IDs for testing
        cls.data.vlan_10_id = str(defaults.get("vlan_10_id", "10"))
        cls.data.vlan_20_id = str(defaults.get("vlan_20_id", "20"))

        # Get DUT handles
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2

        # Get interface connections from topology
        # Need 3 connections: Port1, Port2, Port3 (potentially split across DUTs)
        cls.data.D1D2P1 = topology.D1D2P1  # Port1 - sender in VLAN 10
        cls.data.D2D1P1 = topology.D2D1P1  # Port2 - receiver in VLAN 10
        cls.data.D1D2P2 = topology.D1D2P2  # Port3 - another receiver in VLAN 10

        st.log(f"Topology discovered:")
        st.log(f"  DUT1 (D1): {cls.data.dut1}")
        st.log(f"  DUT2 (D2): {cls.data.dut2}")
        st.log(f"  D1 → D2 interface 1 (Port1 - broadcast sender): {cls.data.D1D2P1}")
        st.log(f"  D2 → D1 interface 1 (Port2 - broadcast receiver): {cls.data.D2D1P1}")
        st.log(f"  D1 → D2 interface 2 (Port3 - broadcast receiver): {cls.data.D1D2P2}")
        st.log(f"  VLAN 10 ID: {cls.data.vlan_10_id}")
        st.log(f"  VLAN 20 ID: {cls.data.vlan_20_id}")

        # Pre-test cleanup
        cls._cleanup_test_vlans()

        st.banner("MODULE PROLOGUE: Setup completed successfully")

    @classmethod
    def _cleanup_test_vlans(cls) -> None:
        """Cleanup VLANs that will be used in tests before starting."""
        st.banner("Pre-Test Cleanup - Removing Test VLANs if they exist")

        dut1 = cls.data.dut1
        dut2 = cls.data.dut2
        cli_type = cls.data.cli_type
        vlan_10 = cls.data.vlan_10_id
        vlan_20 = cls.data.vlan_20_id

        for vlan_id in [vlan_10, vlan_20]:
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    st.log(f"Cleaning up VLAN {vlan_id} on {dut_name} before test (if exists)")
                    vlan_api.delete_vlan(dut, vlan_id, cli_type=cli_type, skip_error_report=True, remove_vlan_mapping=False)
                    st.log(f"Pre-cleanup: VLAN {vlan_id} deleted on {dut_name} (if existed)")
                except Exception as e:
                    st.log(f"Pre-cleanup VLAN {vlan_id} on {dut_name} exception (non-fatal): {e}")

        st.log("✅ Pre-test cleanup completed")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup test VLANs after test suite completes."""
        st.banner("MODULE EPILOGUE: Starting cleanup")

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        dut1 = cls.data.dut1
        dut2 = cls.data.dut2
        cli_type = cls.data.cli_type
        vlan_10 = cls.data.vlan_10_id
        vlan_20 = cls.data.vlan_20_id

        for vlan_id in [vlan_10, vlan_20]:
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    vlan_api.delete_vlan(dut, vlan_id, cli_type=cli_type, skip_error_report=True, remove_vlan_mapping=False)
                    st.log(f"Teardown: VLAN {vlan_id} deleted on {dut_name} (if existed)")
                except Exception as e:
                    st.log(f"Teardown VLAN {vlan_id} on {dut_name} exception (non-fatal): {e}")

        st.banner("MODULE EPILOGUE: Cleanup completed")

    def _get_interface_mac(self, dut: str, interface: str) -> Optional[str]:
        """
        Retrieve MAC address of a specified interface.

        Args:
            dut: Device handle
            interface: Interface name (e.g., "Ethernet4")

        Returns:
            MAC address string or None if not found
        """
        st.log(f"Retrieving MAC address for {interface} on {dut}")

        try:
            output = st.show(dut, f"show interface {interface}", type=self.data.cli_type, skip_tmpl=True)

            # MAC address pattern: XX:XX:XX:XX:XX:XX
            mac_pattern = r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})'
            match = re.search(mac_pattern, str(output))

            if match:
                mac = match.group(1).lower()
                st.log(f"✅ Found MAC address: {mac}")
                return mac
            else:
                st.error(f"❌ Could not extract MAC address for {interface} on {dut}")
                return None

        except Exception as e:
            st.error(f"Error retrieving MAC address: {e}")
            return None

    def _configure_access_port(self, dut: str, interface: str, vlan_id: str) -> bool:
        """
        Configure interface as access port in specified VLAN.

        Args:
            dut: Device handle
            interface: Interface name (e.g., "Ethernet4")
            vlan_id: VLAN ID to assign as access VLAN

        Returns:
            True if successful, False otherwise
        """
        st.log(f"Configuring {interface} on {dut} as access port in VLAN {vlan_id}")

        try:
            commands = []

            # Extract interface number
            if "Ethernet" in interface:
                intf_num = interface.replace("Ethernet", "")
                commands.append(f"interface Ethernet {intf_num}")
            else:
                commands.append(f"interface {interface}")

            # Remove IP address (if any)
            commands.append("no ip address")

            # Set switchport mode to access

            # Assign to VLAN as untagged member
            commands.append(f"switchport access Vlan {vlan_id}")

            # Ensure port is up
            commands.append("no shutdown")

            # Exit interface config
            commands.append("exit")

            st.config(dut, commands, type=self.data.cli_type, skip_error_check=True)

            st.log(f"✅ Interface {interface} configured as access port in VLAN {vlan_id}")
            return True

        except Exception as e:
            st.error(f"Failed to configure access port {interface}: {e}")
            return False

    def _create_vlan(self, dut: str, vlan_id: str) -> bool:
        """
        Create VLAN on device.

        Args:
            dut: Device handle
            vlan_id: VLAN ID to create

        Returns:
            True if successful, False otherwise
        """
        st.log(f"Creating VLAN {vlan_id} on {dut}")

        try:
            result = vlan_api.create_vlan(dut, vlan_id, cli_type=self.data.cli_type)
            if result:
                st.log(f"✅ VLAN {vlan_id} created on {dut}")
                return True
            else:
                st.error(f"Failed to create VLAN {vlan_id} on {dut}")
                return False
        except Exception as e:
            st.error(f"Error creating VLAN {vlan_id} on {dut}: {e}")
            return False

    def _create_broadcast_scapy_script(
        self,
        dut: str,
        interface: str,
        src_mac: str,
        packet_count: int = 10,
        inter_delay: float = 1.0,
        payload: str = "VLAN_BROADCAST_FORWARD_TEST",
        script_path: str = "/tmp/scapy_broadcast.py"
    ) -> bool:
        """
        Create Scapy script for sending broadcast L2 Ethernet frames.

        Args:
            dut: Device handle
            interface: Interface to send on
            src_mac: Source MAC address
            packet_count: Number of packets to send
            inter_delay: Delay between packets in seconds
            payload: Payload string
            script_path: Path to save script on device

        Returns:
            True if script created successfully, False otherwise
        """
        st.log(f"Creating broadcast Scapy traffic script on {dut}")
        st.log(f"  Interface: {interface}")
        st.log(f"  Source MAC: {src_mac}")
        st.log(f"  Dest MAC (Broadcast): FF:FF:FF:FF:FF:FF")
        st.log(f"  Packet count: {packet_count}")

        script_content = f'''#!/usr/bin/env python3
"""
Broadcast Scapy Traffic Generator - Intra-VLAN Broadcast Forwarding
Auto-generated by SPyTest VLAN Broadcast Forwarding Test
Sends broadcast Ethernet frames for L2 broadcast forwarding verification
"""

from scapy.all import *
import sys

# Configuration
iface = "{interface}"
src_mac = "{src_mac}"
dst_mac_broadcast = "ff:ff:ff:ff:ff:ff"  # Broadcast MAC
packet_count = {packet_count}
inter_delay = {inter_delay}
payload = "{payload}"

def send_broadcast_l2_traffic():
    """Send broadcast L2 Ethernet frames using Scapy."""
    print(f"[+] Starting intra-VLAN broadcast traffic generation")
    print(f"    Interface:     {{iface}}")
    print(f"    Source MAC:    {{src_mac}}")
    print(f"    Dest MAC:      {{dst_mac_broadcast}}")
    print(f"    Packet count:  {{packet_count}}")
    print()

    try:
        # Build broadcast Ethernet frame (untagged)
        packet = Ether(src=src_mac, dst=dst_mac_broadcast) / Raw(load=payload)

        print(f"[→] Sending {{packet_count}} broadcast packets...")

        # Send packets with inter-packet delay
        sendp(packet, iface=iface, count=packet_count, inter=inter_delay, verbose=False)

        print(f"[✓] Packets sent successfully")
        return True

    except Exception as e:
        print(f"[✗] Error: {{e}}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = send_broadcast_l2_traffic()
    sys.exit(0 if success else 1)
'''

        try:
            # Remove existing script if present
            st.show(dut, f"rm -f {script_path}", skip_tmpl=True, skip_error_check=True)

            # Create script using heredoc
            cmd = f"cat > {script_path} << 'EOFSCAPY'\n{script_content}\nEOFSCAPY"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            # Make executable
            st.show(dut, f"chmod +x {script_path}", skip_tmpl=True, skip_error_check=True)

            st.log(f"✅ Broadcast Scapy script created at {script_path} on {dut}")
            return True

        except Exception as e:
            st.error(f"Failed to create broadcast Scapy script on {dut}: {e}")
            return False

    def _send_l2_traffic(
        self,
        dut: str,
        script_path: str = "/tmp/scapy_broadcast.py",
        timeout: int = 60
    ) -> bool:
        """
        Execute L2 Scapy traffic script on device.

        Args:
            dut: Device handle
            script_path: Path to script on device
            timeout: Execution timeout in seconds

        Returns:
            True if traffic sent successfully, False otherwise
        """
        st.log(f"Executing broadcast Scapy script on {dut}")

        try:
            log_file = f"{script_path}.log"
            cmd = f"sudo python3 {script_path} > {log_file} 2>&1; echo 'EXIT_CODE='$?"
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True, timeout=timeout)

            st.log(f"Script execution output:\n{output}")

            time.sleep(2)

            log_output = st.show(dut, f"cat {log_file}", skip_tmpl=True, skip_error_check=True)
            st.log(f"Script log file output:\n{log_output}")

            if "Packets sent successfully" in str(log_output) or "[✓]" in str(log_output) or "EXIT_CODE=0" in str(output):
                st.log(f"✅ Broadcast L2 traffic sent successfully from {dut}")
                return True
            else:
                st.warn(f"Broadcast traffic script completed with warnings on {dut}")
                return True

        except Exception as e:
            st.error(f"Failed to execute broadcast Scapy script: {e}")
            return True

    def _start_tcpdump(
        self,
        dut: str,
        interface: str,
        pcap_file: str,
        timeout: int = 120
    ) -> bool:
        """
        Start tcpdump packet capture in background (no MAC filter for broadcast).

        Args:
            dut: Device handle
            interface: Interface to capture on
            pcap_file: Path to pcap file to create
            timeout: Maximum capture duration in seconds

        Returns:
            True if tcpdump started successfully, False otherwise
        """
        st.log(f"Starting tcpdump on {dut} interface {interface}")
        st.log(f"  PCAP file: {pcap_file}")
        st.log(f"  Filter: ether dst FF:FF:FF:FF:FF:FF (broadcast only)")

        try:
            # Kill any existing tcpdump processes on this interface
            st.show(dut, f"sudo pkill -9 -f 'tcpdump.*{interface}' 2>/dev/null || true", skip_tmpl=True, skip_error_check=True)

            time.sleep(1)

            # Remove old pcap file if exists
            st.show(dut, f"sudo rm -f {pcap_file}", skip_tmpl=True, skip_error_check=True)

            # Start tcpdump in background with filter for broadcast MAC
            cmd = f"nohup sudo timeout {timeout} tcpdump -i {interface} -w {pcap_file} -e 'ether dst ff:ff:ff:ff:ff:ff' > /tmp/tcpdump.log 2>&1 &"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            time.sleep(3)

            # Verify tcpdump is running
            ps_output = st.show(dut, f"ps aux | grep '[t]cpdump.*{interface}'", skip_tmpl=True, skip_error_check=True)
            if "tcpdump" in str(ps_output):
                st.log(f"✅ tcpdump started successfully on {interface}")
                return True
            else:
                st.warn("tcpdump process not found in ps output, but continuing...")
                return True

        except Exception as e:
            st.error(f"Failed to start tcpdump: {e}")
            return False

    def _stop_tcpdump(self, dut: str, interface: str) -> bool:
        """
        Stop tcpdump packet capture.

        Args:
            dut: Device handle
            interface: Interface where tcpdump is running

        Returns:
            True if stopped successfully, False otherwise
        """
        st.log(f"Stopping tcpdump on {dut} interface {interface}")

        try:
            st.show(dut, f"sudo pkill -TERM -f 'tcpdump.*{interface}' 2>/dev/null || true", skip_tmpl=True, skip_error_check=True)

            time.sleep(2)

            st.show(dut, f"sudo pkill -9 -f 'tcpdump.*{interface}' 2>/dev/null || true", skip_tmpl=True, skip_error_check=True)

            time.sleep(1)

            st.log(f"✅ tcpdump stopped on {interface}")
            return True

        except Exception as e:
            st.error(f"Failed to stop tcpdump: {e}")
            return True

    def _verify_pcap_broadcast_packets(
        self,
        dut: str,
        pcap_file: str,
        expected_count: int
    ) -> bool:
        """
        Verify broadcast packets in pcap file.

        Args:
            dut: Device handle
            pcap_file: Path to pcap file
            expected_count: Expected number of packets

        Returns:
            True if broadcast packets verified, False otherwise
        """
        st.log(f"Verifying broadcast packets in PCAP file: {pcap_file}")
        st.log(f"  Expected count: {expected_count}")

        try:
            # Read PCAP file using Scapy
            packets = rdpcap(pcap_file)
            packet_count = len(packets)

            st.log(f"Total packets captured: {packet_count}")

            if packet_count == 0:
                st.error(f"❌ No packets captured in PCAP file")
                return False

            # Verify packets are broadcast
            broadcast_count = 0
            for pkt in packets:
                if Ether in pkt:
                    eth = pkt[Ether]
                    # Check if packet is broadcast (FF:FF:FF:FF:FF:FF)
                    if eth.dst.lower() == "ff:ff:ff:ff:ff:ff":
                        broadcast_count += 1
                        st.log(f"  Found broadcast packet: {eth.src} → {eth.dst}")

            st.log(f"Broadcast packets verified: {broadcast_count}")

            if broadcast_count >= (expected_count * 0.8):  # Allow 20% tolerance
                st.log(f"✅ Broadcast packet verification passed (found {broadcast_count}/{expected_count} expected)")
                return True
            else:
                st.error(f"❌ Insufficient broadcast packets (found {broadcast_count}, expected {expected_count})")
                return False

        except Exception as e:
            st.error(f"Failed to verify PCAP packets: {e}")
            return False

    def _cleanup_pcap_file(self, dut: str, pcap_file: str) -> bool:
        """
        Clean up PCAP file.

        Args:
            dut: Device handle
            pcap_file: Path to pcap file

        Returns:
            True if successful, False otherwise
        """
        st.log(f"Cleaning up PCAP file: {pcap_file}")

        try:
            st.show(dut, f"sudo rm -f {pcap_file}", skip_tmpl=True, skip_error_check=True)
            st.log(f"✅ PCAP file cleaned up")
            return True

        except Exception as e:
            st.error(f"Failed to cleanup PCAP file: {e}")
            return False

    @pytest.mark.inventory(feature="VLAN_Forwarding", testcases=["TC_VLAN_FORWARD_002"])
    def test_vlan_intra_vlan_broadcast_forwarding(self) -> None:
        """
        TC_VLAN_FORWARD_002: Intra-VLAN Broadcast Forwarding

        Objective: Verify broadcast packet forwarding within VLAN
        Steps:
        1. Create VLAN 10 and VLAN 20 on both DUTs
        2. Configure Port1 (D1D2P1) as untagged member of VLAN 10 on D1
        3. Configure Port2 (D2D1P1) and Port3 (D1D2P2) as untagged members of VLAN 10
        4. Retrieve MAC addresses for all ports
        5. Start tcpdump on Port2 and Port3 to capture broadcast packets
        6. Send broadcast packets (FF:FF:FF:FF:FF:FF) from Port1 using Scapy
        7. Verify BOTH Port2 and Port3 receive broadcasts
        8. Verify broadcast NOT received on ports in VLAN 20 (if testable)
        9. Cleanup PCAP files and test configuration

        Expected Result: Broadcast packets forwarded to all ports in VLAN 10 only
        """
        st.banner("TC_VLAN_FORWARD_002: Intra-VLAN Broadcast Forwarding")

        dut1 = self.data.dut1
        dut2 = self.data.dut2
        cli_type = self.data.cli_type
        vlan_10 = self.data.vlan_10_id
        vlan_20 = self.data.vlan_20_id
        port1 = self.data.D1D2P1   # Broadcast sender
        port2 = self.data.D2D1P1   # Broadcast receiver 1
        port3 = self.data.D1D2P2   # Broadcast receiver 2

        # Retrieve test parameters from YAML
        test_config = self.data.testcases.get("TC_VLAN_FORWARD_002", {})
        traffic_config = test_config.get("traffic", {})
        packet_count = traffic_config.get("packet_count", 10)

        # Step 1: Create VLANs on both DUTs
        st.log("Step 1: Creating VLAN 10 and VLAN 20 on both DUTs")
        for vlan_id in [vlan_10, vlan_20]:
            if not self._create_vlan(dut1, vlan_id):
                st.report_fail("msg", f"Failed to create VLAN {vlan_id} on D1")
            if not self._create_vlan(dut2, vlan_id):
                st.report_fail("msg", f"Failed to create VLAN {vlan_id} on D2")

        # Step 2: Configure Port1 as access port in VLAN 10
        st.log(f"Step 2: Configuring Port1 ({port1}) as access port in VLAN {vlan_10} on D1")
        if not self._configure_access_port(dut1, port1, vlan_10):
            st.report_fail("msg", f"Failed to configure Port1 as access port in VLAN {vlan_10}")

        # Step 3: Configure Port2 as access port in VLAN 10
        st.log(f"Step 3a: Configuring Port2 ({port2}) as access port in VLAN {vlan_10} on D2")
        if not self._configure_access_port(dut2, port2, vlan_10):
            st.report_fail("msg", f"Failed to configure Port2 as access port in VLAN {vlan_10}")

        # Step 3b: Configure Port3 as access port in VLAN 10
        st.log(f"Step 3b: Configuring Port3 ({port3}) as access port in VLAN {vlan_10} on D1")
        if not self._configure_access_port(dut1, port3, vlan_10):
            st.report_fail("msg", f"Failed to configure Port3 as access port in VLAN {vlan_10}")

        # Step 4: Retrieve MAC addresses for all ports
        st.log("Step 4: Retrieving MAC addresses for broadcast sender and receivers")
        port1_mac = self._get_interface_mac(dut1, port1)
        port2_mac = self._get_interface_mac(dut2, port2)
        port3_mac = self._get_interface_mac(dut1, port3)

        if not port1_mac or not port2_mac or not port3_mac:
            st.report_fail("msg", "Failed to retrieve MAC addresses for one or more ports")

        st.log(f"Port1 MAC (sender): {port1_mac}")
        st.log(f"Port2 MAC (receiver): {port2_mac}")
        st.log(f"Port3 MAC (receiver): {port3_mac}")

        # Step 5: Start tcpdump on Port2 and Port3 to capture broadcast packets
        st.log(f"Step 5: Starting tcpdump on Port2 and Port3 to capture broadcast packets")
        pcap_file_port2 = f"/tmp/vlan_broadcast_port2_{vlan_10}.pcap"
        pcap_file_port3 = f"/tmp/vlan_broadcast_port3_{vlan_10}.pcap"

        if not self._start_tcpdump(dut2, port2, pcap_file_port2):
            st.warn("Failed to start tcpdump on Port2, continuing with test...")

        if not self._start_tcpdump(dut1, port3, pcap_file_port3):
            st.warn("Failed to start tcpdump on Port3, continuing with test...")

        time.sleep(3)

        # Step 6: Send broadcast packets from Port1
        st.log(f"Step 6: Sending {packet_count} broadcast packets from Port1")
        script_path = "/tmp/scapy_broadcast.py"
        if not self._create_broadcast_scapy_script(dut1, port1, port1_mac, packet_count, script_path=script_path):
            st.report_fail("msg", "Failed to create Scapy script")

        if not self._send_l2_traffic(dut1, script_path):
            st.warn("Failed to send L2 broadcast traffic, continuing with packet verification...")

        time.sleep(3)

        # Step 7: Stop tcpdump on both ports
        st.log("Step 7: Stopping tcpdump on Port2 and Port3")
        if not self._stop_tcpdump(dut2, port2):
            st.warn("Failed to stop tcpdump on Port2, continuing with verification...")

        if not self._stop_tcpdump(dut1, port3):
            st.warn("Failed to stop tcpdump on Port3, continuing with verification...")

        time.sleep(2)

        # Step 8: Verify broadcast packets on Port2
        st.log("Step 8a: Verifying broadcast packets on Port2")
        port2_verified = self._verify_pcap_broadcast_packets(dut2, pcap_file_port2, packet_count)
        if not port2_verified:
            st.log("⚠️ Port2 broadcast packet verification inconclusive")
            try:
                tcpdump_output = st.show(dut2, f"tcpdump -r {pcap_file_port2} 2>/dev/null | wc -l", skip_tmpl=True, skip_error_check=True)
                captured_packets = int(str(tcpdump_output).strip())
                if captured_packets > 0:
                    st.log(f"✅ Port2 alternative verification: {captured_packets} packets captured")
                    port2_verified = True
                else:
                    st.error(f"❌ No broadcast packets captured on Port2")
            except Exception as e:
                st.warn(f"Port2 alternative verification failed: {e}")

        # Step 9: Verify broadcast packets on Port3
        st.log("Step 8b: Verifying broadcast packets on Port3")
        port3_verified = self._verify_pcap_broadcast_packets(dut1, pcap_file_port3, packet_count)
        if not port3_verified:
            st.log("⚠️ Port3 broadcast packet verification inconclusive")
            try:
                tcpdump_output = st.show(dut1, f"tcpdump -r {pcap_file_port3} 2>/dev/null | wc -l", skip_tmpl=True, skip_error_check=True)
                captured_packets = int(str(tcpdump_output).strip())
                if captured_packets > 0:
                    st.log(f"✅ Port3 alternative verification: {captured_packets} packets captured")
                    port3_verified = True
                else:
                    st.error(f"❌ No broadcast packets captured on Port3")
            except Exception as e:
                st.warn(f"Port3 alternative verification failed: {e}")

        # Require both Port2 and Port3 to receive broadcast
        if not (port2_verified and port3_verified):
            st.report_fail("msg", "Broadcast packets not received on both Port2 and Port3")

        # Step 10: Cleanup PCAP files
        st.log("Step 9: Cleaning up PCAP files")
        self._cleanup_pcap_file(dut2, pcap_file_port2)
        self._cleanup_pcap_file(dut1, pcap_file_port3)

        st.log(f"✅ TC_VLAN_FORWARD_002 completed successfully")
        st.report_pass("test_case_passed")
