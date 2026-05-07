"""
VLAN TRUNK-TO-TRUNK TAGGED PACKET FORWARDING TEST (TC_VLAN_TAG_003)

Author: Test Automation Team
Date: 2026-05-06

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Tagged_Packet_on_Trunk_Port.py \\
  --logs-path ./logs/vlan_tag_003_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Validates trunk-to-trunk tagged packet forwarding in compliance with IEEE 802.1Q.
  TC_VLAN_TAG_003 tests that tagged packets sent on a trunk port are received
  with the same VLAN tag on another trunk port (no tag stripping on trunk-to-trunk).
  This validates the core VLAN forwarding behavior for trunk ports.

  Test Scenario:
    Source: Trunk port (Port3, D1) sends VLAN 10 tagged packet
    Operation: Switch forwards tagged packet between trunk ports
    Destination: Trunk port (Port5, D2) receives packet with VLAN 10 tag intact

Pre-requisites:
  - Topology: two-node (D1-D2) with 2+ connections | Supported: HW and Virtual
  - Topology Diagram:
        ┌────────────────────┐                  ┌────────────────────┐
        │   D1 (Leaf/DUT)    │                  │   D2 (Spine/TGen)  │
        │                    │                  │                    │
        │  Ethernet4         │══════════════════│  Ethernet4         │
        │  (Trunk Port)      │    Back-to-Back  │  (Trunk Port)      │
        │  VLAN 10 (tagged)  │                  │  VLAN 10 (tagged)  │
        │                    │                  │                    │
        └────────────────────┘                  └────────────────────┘

  - Feature flags / min SONiC version: VLAN support required
  - Required test variables (YAML): spytest/vars/switching/vlan/vars_vlan_tag_003.yaml
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api
import apis.system.interface as interface_api

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

# Default YAML variable file location
VAR_FILE_ENV = "VLAN_TAG_003_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest"
    / "vars"
    / "switching"
    / "vlan"
    / "vars_vlan_tag_003.yaml"
)

# Test case identifier
TC_VLAN_TAG_003 = "TC_VLAN_TAG_003"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _load_yaml_config() -> Dict[str, Any]:
    """
    Load test configuration from YAML file.

    Returns:
        Dictionary containing test configuration

    Raises:
        FileNotFoundError: If YAML file not found
        ValueError: If YAML is missing required keys
    """
    override_path = st.getenv(VAR_FILE_ENV)
    yaml_file = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not yaml_file.is_file():
        st.error(f"VLAN TAG-003 variable file not found: {yaml_file}")
        raise FileNotFoundError(f"VLAN TAG-003 variable file not found: {yaml_file}")

    with yaml_file.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    if "testcases" not in config:
        raise ValueError("YAML must contain 'testcases' key")

    st.log(f"✓ YAML configuration loaded from: {yaml_file}")
    return config


# ============================================================================
# TEST CLASS
# ============================================================================


@pytest.mark.topology("D1D2:2")
class TestVlanTaggedPacketOnTrunkPort:
    """
    Test class for VLAN trunk-to-trunk tagged packet forwarding.

    Tests that tagged packets remain tagged when forwarded between trunk ports.
    This validates IEEE 802.1Q trunk port behavior.
    """

    data = SpyTestDict()

    # ========================================================================
    # CLASS-LEVEL SETUP AND TEARDOWN
    # ========================================================================

    @classmethod
    def setup_class(cls) -> None:
        """
        Class-level setup: Load configuration and verify minimum topology.

        Topology requirement: Two DUTs with 2+ connections (D1D2:2).
        """
        st.banner("MODULE PROLOGUE: TC_VLAN_TAG_003 Setup")

        try:
            # Load YAML configuration
            config = _load_yaml_config()
            defaults = config.get("defaults", {})
            testcases = config.get("testcases", {})

            # Ensure minimum topology: Two DUTs with 2+ connections
            min_topology = defaults.get("min_topology", ["D1D2:2"])
            topology = st.ensure_min_topology(*min_topology)

            # Store configuration
            cls.data.config = SpyTestDict(config)
            cls.data.defaults = SpyTestDict(defaults)
            cls.data.testcases = SpyTestDict(testcases)
            cls.data.topology = topology
            cls.data.cli_type = defaults.get("cli_type", "klish")

            st.log(f"✓ Topology verified: {topology}")
            st.log(f"✓ CLI Type: {cls.data.cli_type}")

            # Get TC_VLAN_TAG_003 configuration
            tc_config = testcases.get(TC_VLAN_TAG_003, {})
            cls.data.tc_config = SpyTestDict(tc_config)

            st.log(f"✓ Test configuration loaded for {TC_VLAN_TAG_003}")

        except Exception as e:
            st.error(f"Setup failed: {e}")
            st.report_tc_fail(TC_VLAN_TAG_003, "setup_failed", str(e))
            raise

    @classmethod
    def teardown_class(cls) -> None:
        """Class-level teardown: cleanup configuration."""
        st.banner("MODULE EPILOGUE: TC_VLAN_TAG_003 Cleanup")

        try:
            # Get DUT handles
            d1 = cls.data.topology.dut_list[0]
            d2 = cls.data.topology.dut_list[1]

            # Get test ports
            d1_port = cls.data.tc_config.get("ports", {}).get("trunk_port_1", cls.data.topology.D1D2P1)
            d2_port = cls.data.tc_config.get("ports", {}).get("trunk_port_2", cls.data.topology.D2D1P1)

            st.log("Cleaning up VLAN configuration...")

            # Get VLAN ID from config
            vlan_config = cls.data.tc_config.get("vlans", {})
            vlan_id = vlan_config.get("vlan_10", 10)

            # Remove ports from VLAN
            try:
                st.config(d1, f"interface {d1_port}", type=cls.data.cli_type)
                st.config(d1, "no switchport trunk allowed vlan 10", type=cls.data.cli_type)
                st.config(d1, "exit", type=cls.data.cli_type)
                st.log(f"✓ Removed {d1_port} from VLAN configuration (D1)")
            except Exception as e:
                st.warn(f"Failed to remove port config from D1: {e}")

            try:
                st.config(d2, f"interface {d2_port}", type=cls.data.cli_type)
                st.config(d2, "no switchport trunk allowed vlan 10", type=cls.data.cli_type)
                st.config(d2, "exit", type=cls.data.cli_type)
                st.log(f"✓ Removed {d2_port} from VLAN configuration (D2)")
            except Exception as e:
                st.warn(f"Failed to remove port config from D2: {e}")

            # Delete VLAN
            try:
                st.config(d1, f"no vlan {vlan_id}", type=cls.data.cli_type)
                st.log(f"✓ VLAN {vlan_id} deleted from D1")
            except Exception as e:
                st.warn(f"Failed to delete VLAN from D1: {e}")

            try:
                st.config(d2, f"no vlan {vlan_id}", type=cls.data.cli_type)
                st.log(f"✓ VLAN {vlan_id} deleted from D2")
            except Exception as e:
                st.warn(f"Failed to delete VLAN from D2: {e}")

            st.log("✓ Cleanup completed")

        except Exception as e:
            st.error(f"Cleanup error: {e}")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_interface_mac(self, dut: str, interface: str) -> Optional[str]:
        """
        Retrieve MAC address from interface.

        Args:
            dut: Device handle
            interface: Interface name (e.g., 'Ethernet4')

        Returns:
            MAC address string or None if retrieval fails
        """
        try:
            st.log(f"Retrieving MAC address for {interface} on {dut}...")
            output = st.show(dut, f"show interface {interface}", type=self.data.cli_type)

            # Search for MAC address pattern in output
            mac_pattern = r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})"
            match = re.search(mac_pattern, str(output))

            if match:
                mac = match.group(1)
                st.log(f"✓ MAC address retrieved: {mac}")
                return mac
            else:
                st.error(f"MAC address pattern not found in output")
                return None

        except Exception as e:
            st.error(f"Failed to retrieve MAC address: {e}")
            return None

    def _clear_interface_counters(self, dut: str) -> bool:
        """
        Clear interface counters on the DUT.

        Args:
            dut: Device handle

        Returns:
            True if successful
        """
        try:
            st.log(f"Clearing interface counters on {dut}")
            cmd = "clear interface counters"
            st.config(dut, cmd, type=self.data.cli_type, skip_error_check=True, conf=False)
            time.sleep(2)
            st.log("✓ Interface counters cleared")
            return True

        except Exception as e:
            st.error(f"Failed to clear counters: {e}")
            return False

    def _get_interface_counters(self, dut: str, interface: str) -> Dict[str, int]:
        """
        Get interface RX/TX counters.

        Args:
            dut: Device handle
            interface: Interface name

        Returns:
            Dictionary with 'rx' and 'tx' counters
        """
        try:
            output = st.show(dut, f"show interface {interface} counters", type=self.data.cli_type)
            counters = {"rx": 0, "tx": 0}

            # Parse output for RX_OK and TX_OK
            for line in str(output).split("\n"):
                if "RX_OK" in line:
                    match = re.search(r"RX_OK\s+(\d+)", line)
                    if match:
                        counters["rx"] = int(match.group(1))
                if "TX_OK" in line:
                    match = re.search(r"TX_OK\s+(\d+)", line)
                    if match:
                        counters["tx"] = int(match.group(1))

            st.log(f"✓ Counters retrieved - RX: {counters['rx']}, TX: {counters['tx']}")
            return counters

        except Exception as e:
            st.error(f"Failed to get counters: {e}")
            return {"rx": 0, "tx": 0}

    def _verify_vlan_config(self, dut: str, vlan_id: int) -> bool:
        """
        Verify VLAN exists using show running-configuration.

        Args:
            dut: Device handle
            vlan_id: VLAN ID to verify

        Returns:
            True if VLAN configuration found
        """
        try:
            st.log(f"Verifying VLAN {vlan_id} on {dut}...")
            output = st.show(dut, "show running-configuration | grep -A 5 vlan", type=self.data.cli_type)

            if f"vlan {vlan_id}" in str(output):
                st.log(f"✓ VLAN {vlan_id} found in running-configuration")
                return True
            else:
                st.error(f"VLAN {vlan_id} NOT found in running-configuration")
                return False

        except Exception as e:
            st.error(f"Failed to verify VLAN config: {e}")
            return False

    def _verify_port_vlan_config(self, dut: str, interface: str, vlan_id: int, is_trunk: bool = True) -> bool:
        """
        Verify port VLAN configuration using show running-configuration.

        Args:
            dut: Device handle
            interface: Interface name
            vlan_id: VLAN ID
            is_trunk: True if trunk port, False if access port

        Returns:
            True if configuration is correct
        """
        try:
            st.log(f"Verifying port {interface} VLAN configuration on {dut}...")
            output = st.show(dut, f"show running-configuration interface {interface}", type=self.data.cli_type)

            output_str = str(output)

            if is_trunk:
                    st.log(f"✓ Port {interface} correctly configured as trunk for VLAN {vlan_id}")
                    return True
                else:
                    st.error(f"✗ Port {interface} trunk configuration incomplete for VLAN {vlan_id}")
                    return False
            else:
                    st.log(f"✓ Port {interface} correctly configured as access for VLAN {vlan_id}")
                    return True
                else:
                    st.error(f"✗ Port {interface} access configuration incomplete for VLAN {vlan_id}")
                    return False

        except Exception as e:
            st.error(f"Failed to verify port config: {e}")
            return False

    def _configure_trunk_port(self, dut: str, interface: str, vlans: List[int]) -> bool:
        """
        Configure a port as trunk for specified VLANs.

        Args:
            dut: Device handle
            interface: Interface name
            vlans: List of VLAN IDs to allow

        Returns:
            True if successful
        """
        try:
            st.log(f"Configuring {interface} as trunk port on {dut}...")
            vlan_list = ",".join(str(v) for v in vlans)

            commands = [
                f"interface {interface}",
                f"switchport trunk allowed vlan {vlan_list}",
                "no shutdown",
                "exit",
            ]

            for cmd in commands:
                st.config(dut, cmd, type=self.data.cli_type)

            st.log(f"✓ Port {interface} configured as trunk for VLANs {vlan_list}")
            return True

        except Exception as e:
            st.error(f"Failed to configure trunk port: {e}")
            return False

    def _send_tagged_packet(
        self, dut: str, interface: str, src_mac: str, dst_mac: str, vlan_id: int, packet_count: int = 10
    ) -> bool:
        """
        Send VLAN tagged packet using Scapy.

        Args:
            dut: Device handle
            interface: Source interface
            src_mac: Source MAC address
            dst_mac: Destination MAC address
            vlan_id: VLAN ID for tagging
            packet_count: Number of packets to send

        Returns:
            True if successful
        """
        try:
            st.log(f"Sending {packet_count} VLAN {vlan_id} tagged packets from {interface} on {dut}...")

            scapy_cmd = f"""
python3 << 'SCAPY_EOF'
from scapy.all import Ether, Dot1Q, sendp, conf
conf.iface = "{interface}"
pkt = Ether(src="{src_mac}", dst="{dst_mac}")/Dot1Q(vlan={vlan_id})/b'TestPayload'
sendp(pkt, iface="{interface}", count={packet_count}, verbose=False)
print(f"Sent {{packet_count}} packets")
SCAPY_EOF
"""

            st.config(dut, scapy_cmd, type=self.data.cli_type, conf=False, skip_error_check=True)
            time.sleep(1)
            st.log(f"✓ Sent {packet_count} tagged packets from {interface}")
            return True

        except Exception as e:
            st.error(f"Failed to send tagged packets: {e}")
            return False

    def _capture_packets(self, dut: str, interface: str, timeout: int = 15) -> bool:
        """
        Capture packets using tcpdump.

        Args:
            dut: Device handle
            interface: Interface to capture on
            timeout: Capture timeout in seconds

        Returns:
            True if successful
        """
        try:
            st.log(f"Starting packet capture on {interface} on {dut}...")

            # Start tcpdump in background
            cmd = f'tcpdump -i {interface} -w /tmp/vlan_tag_003_capture.pcap -B 4096 -Q in "vlan" &'
            st.config(dut, cmd, type=self.data.cli_type, conf=False, skip_error_check=True)
            time.sleep(2)
            st.log("✓ Packet capture started")
            return True

        except Exception as e:
            st.error(f"Failed to start packet capture: {e}")
            return False

    def _stop_and_analyze_capture(self, dut: str, vlan_id: int) -> bool:
        """
        Stop tcpdump and analyze captured packets.

        Args:
            dut: Device handle
            vlan_id: Expected VLAN ID

        Returns:
            True if expected VLAN tag found
        """
        try:
            st.log("Stopping packet capture...")
            time.sleep(2)

            # Stop tcpdump
            st.config(dut, "pkill -f tcpdump", type=self.data.cli_type, conf=False, skip_error_check=True)
            time.sleep(2)

            st.log("Analyzing captured packets...")

            # Analyze PCAP using Scapy
            analysis_cmd = f"""
python3 << 'SCAPY_EOF'
from scapy.all import rdpcap, Dot1Q

try:
    packets = rdpcap('/tmp/vlan_tag_003_capture.pcap')
    tagged_count = 0
    correct_vlan_count = 0

    for pkt in packets:
        if pkt.haslayer(Dot1Q):
            tagged_count += 1
            if pkt[Dot1Q].vlan == {vlan_id}:
                correct_vlan_count += 1

    print(f"Tagged packets: {{tagged_count}}")
    print(f"Correct VLAN {vlan_id} packets: {{correct_vlan_count}}")

    if correct_vlan_count > 0:
        print("SUCCESS: VLAN tag verified")
    else:
        print("FAILURE: No packets with correct VLAN tag found")
except Exception as e:
    print(f"Error: {{e}}")
SCAPY_EOF
"""

            output = st.show(dut, analysis_cmd, type=self.data.cli_type)
            output_str = str(output)

            if "SUCCESS" in output_str or f"Correct VLAN {vlan_id} packets: " in output_str:
                # Extract packet count
                import re

                match = re.search(r"Correct VLAN \d+ packets: (\d+)", output_str)
                if match:
                    count = int(match.group(1))
                    st.log(f"✓ {count} packets with correct VLAN {vlan_id} tag captured")
                    return count > 0
                return True
            else:
                st.error("✗ VLAN tag verification failed")
                return False

        except Exception as e:
            st.error(f"Failed to analyze capture: {e}")
            return False

    # ========================================================================
    # TEST METHODS
    # ========================================================================

    def test_vlan_tag_003_trunk_to_trunk_tagged_forwarding(self) -> None:
        """
        TC_VLAN_TAG_003: Verify tagged packet remains tagged on trunk-to-trunk forwarding.

        Test Steps:
        1. Create VLAN 10
        2. Configure Port3 and Port5 as trunk ports for VLAN 10
        3. Get MAC addresses from both interfaces
        4. Clear interface counters
        5. Start packet capture on destination (Port5)
        6. Send VLAN 10 tagged packets from source (Port3)
        7. Verify packets received with VLAN 10 tag intact
        """

        # Get DUT handles
        d1 = self.data.topology.dut_list[0]
        d2 = self.data.topology.dut_list[1]

        # Get ports from config
        ports_config = self.data.tc_config.get("ports", {})
        trunk_port_1 = ports_config.get("trunk_port", self.data.topology.D1D2P1)
        trunk_port_2 = ports_config.get("trunk_port_2", self.data.topology.D2D1P1)

        # Get VLAN ID
        vlan_config = self.data.tc_config.get("vlans", {})
        vlan_id = vlan_config.get("vlan_10", 10)

        # Get traffic parameters
        traffic_config = self.data.tc_config.get("traffic", {})
        packet_count = traffic_config.get("packet_count", 10)

        st.log(f"Starting {TC_VLAN_TAG_003}: Trunk-to-Trunk Tagged Packet Forwarding")

        # STEP 1: Create VLAN 10 on both DUTs
        st.banner("STEP 1: Creating VLAN 10 on both DUTs")
        try:
            st.config(d1, f"vlan {vlan_id}", type=self.data.cli_type)
            st.log(f"✓ VLAN {vlan_id} created on D1")

            st.config(d2, f"vlan {vlan_id}", type=self.data.cli_type)
            st.log(f"✓ VLAN {vlan_id} created on D2")

        except Exception as e:
            st.error(f"Failed to create VLAN: {e}")
            st.report_tc_fail(TC_VLAN_TAG_003, "vlan_create_failed", str(e))
            return

        # STEP 2: Configure trunk ports for VLAN 10
        st.banner("STEP 2: Configuring trunk ports")
        if not self._configure_trunk_port(d1, trunk_port_1, [vlan_id]):
            st.report_tc_fail(TC_VLAN_TAG_003, "trunk_config_failed", f"Failed to configure {trunk_port_1} on D1")
            return

        if not self._configure_trunk_port(d2, trunk_port_2, [vlan_id]):
            st.report_tc_fail(TC_VLAN_TAG_003, "trunk_config_failed", f"Failed to configure {trunk_port_2} on D2")
            return

        # STEP 3: Get MAC addresses
        st.banner("STEP 3: Retrieving MAC addresses")
        src_mac = self._get_interface_mac(d1, trunk_port_1)
        if not src_mac:
            st.report_tc_fail(TC_VLAN_TAG_003, "mac_discovery_failed", f"Failed to get MAC from {trunk_port_1}")
            return

        dst_mac = self._get_interface_mac(d2, trunk_port_2)
        if not dst_mac:
            st.report_tc_fail(TC_VLAN_TAG_003, "mac_discovery_failed", f"Failed to get MAC from {trunk_port_2}")
            return

        st.log(f"✓ Source MAC (D1 {trunk_port_1}): {src_mac}")
        st.log(f"✓ Destination MAC (D2 {trunk_port_2}): {dst_mac}")

        # STEP 4: Clear interface counters
        st.banner("STEP 4: Clearing interface counters")
        if not self._clear_interface_counters(d1):
            st.warn("Failed to clear counters on D1")

        if not self._clear_interface_counters(d2):
            st.warn("Failed to clear counters on D2")

        # STEP 5: Start packet capture on destination
        st.banner("STEP 5: Starting packet capture on destination")
        if not self._capture_packets(d2, trunk_port_2):
            st.warn("Failed to start packet capture")

        # STEP 6: Send tagged packets from source
        st.banner("STEP 6: Sending tagged packets from source")
        if not self._send_tagged_packet(d1, trunk_port_1, src_mac, dst_mac, vlan_id, packet_count):
            st.report_tc_fail(TC_VLAN_TAG_003, "packet_generation_failed", f"Failed to send tagged packets")
            return

        # STEP 7: Verify packets with VLAN tag intact
        st.banner("STEP 7: Analyzing captured packets for VLAN tag")
        if not self._stop_and_analyze_capture(d2, vlan_id):
            st.report_tc_fail(TC_VLAN_TAG_003, "vlan_tag_verification_failed", "Packets did not retain VLAN tag")
            return

        # STEP 8: Verify running-configuration
        st.banner("STEP 8: Verifying running-configuration")
        if not self._verify_vlan_config(d1, vlan_id):
            st.warn(f"VLAN {vlan_id} config not found on D1")

        if not self._verify_port_vlan_config(d1, trunk_port_1, vlan_id, is_trunk=True):
            st.warn(f"Port configuration not verified on D1")

        if not self._verify_port_vlan_config(d2, trunk_port_2, vlan_id, is_trunk=True):
            st.warn(f"Port configuration not verified on D2")

        # TEST PASSED
        st.log(f"✓ {TC_VLAN_TAG_003} PASSED: Tagged packets remain tagged on trunk-to-trunk forwarding")
        st.report_tc_pass(TC_VLAN_TAG_003, "test_passed")


# ============================================================================
# MODULE-LEVEL MARKERS
# ============================================================================


@pytest.fixture(scope="module", autouse=True)
def module_hooks(request):
    """Module-level setup and teardown."""
    yield
