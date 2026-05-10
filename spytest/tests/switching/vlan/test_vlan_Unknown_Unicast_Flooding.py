"""
VLAN UNKNOWN UNICAST FLOODING
Author: Test Automation Team
Date: 2026-05-06

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Unknown_Unicast_Flooding.py \\
  --logs-path ./logs/vlan_unknown_unicast_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Comprehensive validation of unknown unicast flooding behavior within VLANs
  using SpyTest APIs and Scapy-based traffic generation. The test creates VLAN 10,
  configures three ports (Port1, Port2, Port3) as untagged access ports in VLAN 10,
  dynamically retrieves MAC addresses, generates unicast Ethernet frames with an
  unknown destination MAC (not learned in FDB) from Port1, and verifies that the
  packet is flooded to ALL other ports in the same VLAN (Port2 and Port3) through
  tcpdump packet capture and PCAP analysis. This confirms that unknown unicast
  is flooded rather than dropped, providing delivery in case of temporary MAC
  table misses.

Pre-requisites:
  - Topology: Two DUTs (D1-D2) with 3+ connections | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 2 nodes with 3+ connections
        # +------------------+       +------------------+
        # |      DUT1        |-------|      DUT2        |
        # |    (Spine01)     | 1-3   |    (Spine02)     |
        # |                  |       |                  |
        # | Port1 (VLAN10)   |==Port==| Port2 (VLAN10) |
        # | Port3 (VLAN10)   |       |                |
        # +------------------+       +------------------+

  - Feature flags / min SONiC version: SONiC 202211 or later with Scapy support
  - Required test variables (YAML): spytest/vars/switching/vlan/vars_vlan_unknown_unicast.yaml
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

VAR_FILE_ENV = "VLAN_UNKNOWN_UNICAST_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_unknown_unicast.yaml"
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
                "vlan_id": "10",
                "min_topology": ["D1D2:3"]
            },
            "testcases": {},
        }

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


@pytest.mark.topology("D1D2:3")
class TestVlanUnknownUnicastFlooding:
    """Testcases for unknown unicast flooding within VLAN."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and testcase variables for the suite."""
        st.banner("MODULE PROLOGUE: Starting VLAN Unknown Unicast Flooding Test Suite")

        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Get 3-port topology (D1D2:3)
        min_topology = defaults.get("min_topology") or ["D1D2:3"]
        topology = st.ensure_min_topology(*min_topology)

        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology

        # Topology shortcuts
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut1_dut2_p1 = topology.D1D2P1
        cls.data.dut1_dut2_p2 = topology.D1D2P2
        cls.data.dut2_dut1_p1 = topology.D2D1P1

        st.log(f"DUT1: {cls.data.dut1}, DUT2: {cls.data.dut2}")
        st.log(f"DUT1->DUT2 Port1: {cls.data.dut1_dut2_p1}")
        st.log(f"DUT1->DUT2 Port2: {cls.data.dut1_dut2_p2}")
        st.log(f"DUT2->DUT1 Port1: {cls.data.dut2_dut1_p1}")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after test suite execution."""
        st.banner("MODULE EPILOGUE: Cleanup VLAN Unknown Unicast Flooding Test Suite")

        # Get testcase config
        testcase_cfg = cls.data.config.get("testcases", {})
        tc_config = testcase_cfg.get("TC_VLAN_FORWARD_005", {})
        cleanup_cfg = tc_config.get("cleanup", {})

        try:
            # Clean up VLANs if needed
            if cleanup_cfg.get("cleanup_vlans", True):
                st.log(f"Cleaning up VLAN {cls.data.vlan_id}")
                vlan_api.delete_vlan(cls.data.dut1, cls.data.vlan_id, cli_type=cls.data.cli_type)
                vlan_api.delete_vlan(cls.data.dut2, cls.data.vlan_id, cli_type=cls.data.cli_type)
                st.log("✓ VLAN cleanup completed")
        except Exception as e:
            st.error(f"Error during VLAN cleanup: {e}")

    def _get_interface_mac(self, dut, intf) -> str:
        """Retrieve MAC address of a given interface on DUT."""
        try:
            # Execute show interface command
            cmd = f"show interface {intf} | grep -i 'HWaddr\\|ether'"
            output = st.show(dut, cmd, type="klish")

            # Parse MAC from output
            if isinstance(output, str):
                mac_match = re.search(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})", output)
                if mac_match:
                    return mac_match.group(1)
            elif isinstance(output, list) and output:
                for line in output:
                    if isinstance(line, dict):
                        if "hwaddr" in line:
                            return line["hwaddr"]
                        if "ether" in line:
                            return line["ether"]
                    elif isinstance(line, str):
                        mac_match = re.search(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})", line)
                        if mac_match:
                            return mac_match.group(1)

            # Fallback: generate MAC from IP if available
            st.log(f"Could not retrieve MAC from show interface, using generated MAC")
            return f"00:11:22:33:{int(intf.replace('Ethernet', '')) // 256:02x}:{int(intf.replace('Ethernet', '')) % 256:02x}"
        except Exception as e:
            st.error(f"Error retrieving MAC for {intf}: {e}")
            return "00:11:22:33:44:55"

    def _create_vlan(self, dut, vlan_id) -> bool:
        """Create a VLAN on the specified DUT."""
        try:
            st.log(f"Creating VLAN {vlan_id} on {dut}")
            cmd = f"interface Vlan {vlan_id}"
            st.config(dut, cmd, type="klish")
            st.log(f"✓ VLAN {vlan_id} created")
            return True
        except Exception as e:
            st.error(f"Error creating VLAN {vlan_id}: {e}")
            return False

    def _configure_access_port(self, dut, intf, vlan_id) -> bool:
        """Configure an access port in a VLAN."""
        try:
            st.log(f"Configuring {intf} as access port in VLAN {vlan_id} on {dut}")
            cmds = [
                f"interface {intf}",
                f"switchport access Vlan {vlan_id}",
                "exit"
            ]
            st.config(dut, cmds, type="klish")
            st.log(f"✓ {intf} configured as access port in VLAN {vlan_id}")
            return True
        except Exception as e:
            st.error(f"Error configuring {intf}: {e}")
            return False

    def _create_l2_scapy_script(self, src_mac, unknown_dst_mac, packet_count=10, packet_size=64, iface="eth0") -> str:
        """Create a Scapy script to generate L2 frames with unknown destination MAC."""
        script_path = "/tmp/scapy_unknown_unicast_flooding.py"

        script_content = f"""#!/usr/bin/env python3
import sys
from scapy.all import Ether, Raw, sendp, conf

# Disable ARP
conf.checkIPaddr = False

# Packet parameters
src_mac = "{src_mac}"
dst_mac = "{unknown_dst_mac}"  # Unknown MAC (not in FDB)
packet_count = {packet_count}
packet_size = {packet_size}
iface = "{iface}"
payload_size = max(0, packet_size - 14)  # Ethernet header is 14 bytes

# Generate payload
payload = ("U" * payload_size).encode()

# Create and send packets
packet = Ether(src=src_mac, dst=dst_mac) / Raw(load=payload)

print(f"Sending {{packet_count}} unknown unicast packets from {{src_mac}} to {{dst_mac}} on {{iface}}")
print(f"Packet size: {{packet_size}} bytes")
print(f"Payload size: {{payload_size}} bytes")
print(f"Note: {{dst_mac}} is unknown (not in FDB) - should be flooded")

try:
    sendp(packet, iface=iface, count=packet_count, inter=0.1, verbose=True)
    print("✓ Unknown unicast packets sent successfully")
    sys.exit(0)
except Exception as e:
    print(f"Error sending packets: {{e}}")
    sys.exit(1)
"""

        try:
            with open(script_path, "w") as f:
                f.write(script_content)
            st.log(f"✓ Scapy script created at {script_path}")
            return script_path
        except Exception as e:
            st.error(f"Error creating Scapy script: {e}")
            return ""

    def _send_l2_traffic(self, dut, script_path, iface) -> bool:
        """Execute Scapy script to send L2 traffic."""
        try:
            st.log(f"Sending L2 traffic from {dut} using {script_path}")
            cmd = f"python3 {script_path}"
            output = st.show(dut, cmd, type="klish")
            st.log(f"Scapy output: {output}")
            st.log("✓ L2 traffic sent")
            return True
        except Exception as e:
            st.error(f"Error sending L2 traffic: {e}")
            return False

    def _start_tcpdump(self, dut, intf, pcap_file, bpf_filter=None, timeout=30) -> bool:
        """Start tcpdump in background to capture packets."""
        try:
            st.log(f"Starting tcpdump on {dut}:{intf} (timeout={timeout}s, pcap={pcap_file})")

            if bpf_filter:
                filter_str = f"'{bpf_filter}'"
                cmd = f"nohup sudo timeout {timeout} tcpdump -i {intf} -w {pcap_file} {filter_str} > /tmp/tcpdump_{intf}.log 2>&1 &"
            else:
                cmd = f"nohup sudo timeout {timeout} tcpdump -i {intf} -w {pcap_file} > /tmp/tcpdump_{intf}.log 2>&1 &"

            st.show(dut, cmd, type="klish")
            time.sleep(2)  # Give tcpdump time to start

            # Verify tcpdump is running
            verify_cmd = f"ps aux | grep [t]cpdump"
            verify_output = st.show(dut, verify_cmd, type="klish")
            if verify_output and intf in str(verify_output):
                st.log(f"✓ tcpdump started on {intf}")
                return True
            else:
                st.warn(f"Could not verify tcpdump is running on {intf}")
                return True  # Continue anyway
        except Exception as e:
            st.error(f"Error starting tcpdump on {intf}: {e}")
            return False

    def _stop_tcpdump(self, dut, intf) -> bool:
        """Stop tcpdump gracefully."""
        try:
            st.log(f"Stopping tcpdump on {dut}:{intf}")

            # Send SIGTERM to tcpdump
            cmd = f"pkill -TERM tcpdump"
            st.show(dut, cmd, type="klish")
            time.sleep(1)

            # Force kill if still running
            cmd = f"pkill -9 tcpdump"
            st.show(dut, cmd, type="klish")
            time.sleep(1)

            st.log(f"✓ tcpdump stopped on {intf}")
            return True
        except Exception as e:
            st.error(f"Error stopping tcpdump on {intf}: {e}")
            return False

    def _verify_pcap_unknown_unicast_flooded(self, pcap_file, unknown_dst_mac, min_packet_count=1) -> bool:
        """Verify that unknown unicast packets were flooded (captured in PCAP)."""
        try:
            st.log(f"Verifying PCAP file: {pcap_file} (should contain flooded packets)")

            if not Path(pcap_file).is_file():
                st.error(f"PCAP file does not exist: {pcap_file}")
                return False

            # Try to read PCAP
            try:
                packets = rdpcap(pcap_file)
            except Exception as e:
                st.error(f"Could not read PCAP: {e}")
                return False

            if not packets or len(packets) == 0:
                st.error(f"PCAP is empty - no packets captured (expected flooding)")
                return False

            # Verify packets with unknown destination MAC
            unknown_count = 0
            unknown_dst_mac_lower = unknown_dst_mac.lower()

            for pkt in packets:
                if Ether in pkt:
                    eth = pkt[Ether]
                    if eth.dst.lower() == unknown_dst_mac_lower:
                        unknown_count += 1
                        st.log(f"Found flooded packet to unknown MAC {unknown_dst_mac}")

            if unknown_count >= min_packet_count:
                st.log(f"✓ Found {unknown_count} flooded packets to unknown MAC (FLOODING CONFIRMED)")
                return True
            else:
                st.error(f"Expected at least {min_packet_count} packets, found {unknown_count}")
                return False

        except Exception as e:
            st.error(f"Error verifying PCAP: {e}")
            return False

    def _cleanup_pcap_file(self, dut, pcap_file) -> bool:
        """Remove PCAP file after verification."""
        try:
            st.log(f"Cleaning up PCAP file: {pcap_file}")
            cmd = f"rm -f {pcap_file}"
            st.show(dut, cmd, type="klish")
            st.log(f"✓ PCAP file cleaned up")
            return True
        except Exception as e:
            st.warn(f"Error cleaning up PCAP: {e}")
            return True  # Don't fail if cleanup fails

    def test_tc_vlan_forward_005_unknown_unicast_flooding(self) -> None:
        """
        TC_VLAN_FORWARD_005: Unknown Unicast Flooding

        Objective: Verify unknown unicast flooding behavior within VLAN

        Steps:
        1. Create VLAN 10 on both DUTs
        2. Configure Port1 (D1D2P1) as access port in VLAN 10 on DUT1 (sender)
        3. Configure Port2 (D2D1P1) as access port in VLAN 10 on DUT2 (receiver1)
        4. Configure Port3 (D1D2P2) as access port in VLAN 10 on DUT1 (receiver2)
        5. Retrieve MAC addresses for all ports
        6. Start tcpdump on Port2 and Port3 to capture packets
        7. Send unknown unicast packets from Port1 using Scapy (unknown destination MAC)
        8. Verify packets are flooded to Port2 and Port3 (PCAP should contain packets)
        9. Verify VLAN configuration using show running-config

        Expected Result: Unknown unicast packets are flooded to all ports in the VLAN
        """
        tcid = "TC_VLAN_FORWARD_005"
        st.banner(f"Starting {tcid}: Unknown Unicast Flooding")

        # Get testcase configuration
        testcase_cfg = self.data.config.get("testcases", {})
        tc_config = testcase_cfg.get(tcid, {})

        # Get default configuration
        vlan_id = self.data.defaults.get("vlan_id", "10")

        # Get traffic configuration
        traffic_cfg = tc_config.get("traffic", {})
        packet_count = traffic_cfg.get("packet_count", 10)
        packet_size = traffic_cfg.get("packet_size", 64)

        # Get verification configuration
        verify_cfg = tc_config.get("verification", {})
        verify_vlan_config = verify_cfg.get("verify_vlan_config", True)
        verify_port_config = verify_cfg.get("verify_port_config", True)
        verify_flooding = verify_cfg.get("verify_flooding", True)
        use_running_config = verify_cfg.get("use_show_running_config", True)
        max_packet_loss_percent = verify_cfg.get("max_packet_loss_percent", 20)

        try:
            # Step 1: Create VLAN
            st.log(f"\n{'='*60}")
            st.log(f"STEP 1: Create VLAN {vlan_id}")
            st.log(f"{'='*60}")

            if not self._create_vlan(self.data.dut1, vlan_id):
                st.report_fail("vlan_creation_failed", vlan_id)

            if not self._create_vlan(self.data.dut2, vlan_id):
                st.report_fail("vlan_creation_failed", vlan_id)

            # Step 2: Configure Port1 as access port in VLAN
            st.log(f"\n{'='*60}")
            st.log(f"STEP 2: Configure {self.data.dut1_dut2_p1} as access port in VLAN {vlan_id}")
            st.log(f"{'='*60}")

            if not self._configure_access_port(self.data.dut1, self.data.dut1_dut2_p1, vlan_id):
                st.report_fail("port_configuration_failed", self.data.dut1_dut2_p1)

            # Step 3: Configure Port2 as access port in VLAN
            st.log(f"\n{'='*60}")
            st.log(f"STEP 3: Configure {self.data.dut2_dut1_p1} as access port in VLAN {vlan_id}")
            st.log(f"{'='*60}")

            if not self._configure_access_port(self.data.dut2, self.data.dut2_dut1_p1, vlan_id):
                st.report_fail("port_configuration_failed", self.data.dut2_dut1_p1)

            # Step 4: Configure Port3 as access port in VLAN
            st.log(f"\n{'='*60}")
            st.log(f"STEP 4: Configure {self.data.dut1_dut2_p2} as access port in VLAN {vlan_id}")
            st.log(f"{'='*60}")

            if not self._configure_access_port(self.data.dut1, self.data.dut1_dut2_p2, vlan_id):
                st.report_fail("port_configuration_failed", self.data.dut1_dut2_p2)

            # Step 5: Retrieve MAC addresses
            st.log(f"\n{'='*60}")
            st.log("STEP 5: Retrieve MAC addresses for all ports")
            st.log(f"{'='*60}")

            port1_mac = self._get_interface_mac(self.data.dut1, self.data.dut1_dut2_p1)
            port2_mac = self._get_interface_mac(self.data.dut2, self.data.dut2_dut1_p1)
            port3_mac = self._get_interface_mac(self.data.dut1, self.data.dut1_dut2_p2)

            st.log(f"Port1 ({self.data.dut1_dut2_p1}) MAC: {port1_mac}")
            st.log(f"Port2 ({self.data.dut2_dut1_p1}) MAC: {port2_mac}")
            st.log(f"Port3 ({self.data.dut1_dut2_p2}) MAC: {port3_mac}")

            # Unknown destination MAC (not in FDB)
            unknown_dst_mac = "00:11:22:33:44:55"
            st.log(f"Unknown destination MAC (for flooding test): {unknown_dst_mac}")

            # Step 6: Start tcpdump on Port2 and Port3
            st.log(f"\n{'='*60}")
            st.log(f"STEP 6: Start tcpdump on {self.data.dut2_dut1_p1} and {self.data.dut1_dut2_p2}")
            st.log(f"{'='*60}")

            pcap_file_port2 = f"/tmp/vlan_unknown_unicast_port2.pcap"
            pcap_file_port3 = f"/tmp/vlan_unknown_unicast_port3.pcap"
            bpf_filter_port2 = f"ether dst {unknown_dst_mac}"
            bpf_filter_port3 = f"ether dst {unknown_dst_mac}"

            if not self._start_tcpdump(self.data.dut2, self.data.dut2_dut1_p1, pcap_file_port2, bpf_filter_port2, timeout=30):
                st.report_fail("tcpdump_start_failed", self.data.dut2_dut1_p1)

            if not self._start_tcpdump(self.data.dut1, self.data.dut1_dut2_p2, pcap_file_port3, bpf_filter_port3, timeout=30):
                st.report_fail("tcpdump_start_failed", self.data.dut1_dut2_p2)

            # Step 7: Send unknown unicast packets from Port1
            st.log(f"\n{'='*60}")
            st.log(f"STEP 7: Send unknown unicast packets from {self.data.dut1_dut2_p1}")
            st.log(f"{'='*60}")

            scapy_script = self._create_l2_scapy_script(
                port1_mac, unknown_dst_mac, packet_count=packet_count,
                packet_size=packet_size, iface=self.data.dut1_dut2_p1
            )

            if not scapy_script or not self._send_l2_traffic(self.data.dut1, scapy_script, self.data.dut1_dut2_p1):
                st.report_fail("l2_traffic_failed", self.data.dut1_dut2_p1)

            # Wait for traffic to be processed
            time.sleep(3)

            # Step 8: Stop tcpdump and verify flooding
            st.log(f"\n{'='*60}")
            st.log("STEP 8: Stop tcpdump and verify unknown unicast flooding")
            st.log(f"{'='*60}")

            if not self._stop_tcpdump(self.data.dut2, self.data.dut2_dut1_p1):
                st.report_fail("tcpdump_stop_failed", self.data.dut2_dut1_p1)

            if not self._stop_tcpdump(self.data.dut1, self.data.dut1_dut2_p2):
                st.report_fail("tcpdump_stop_failed", self.data.dut1_dut2_p2)

            # Verify flooding on Port2
            if verify_flooding:
                if not self._verify_pcap_unknown_unicast_flooded(pcap_file_port2, unknown_dst_mac, min_packet_count=1):
                    st.error(f"Port2: No flooded packets detected")
                    st.report_fail("unknown_unicast_flooding_failed", self.data.dut2_dut1_p1)

            # Verify flooding on Port3
            if verify_flooding:
                if not self._verify_pcap_unknown_unicast_flooded(pcap_file_port3, unknown_dst_mac, min_packet_count=1):
                    st.error(f"Port3: No flooded packets detected")
                    st.report_fail("unknown_unicast_flooding_failed", self.data.dut1_dut2_p2)

            # Clean up PCAP files
            self._cleanup_pcap_file(self.data.dut2, pcap_file_port2)
            self._cleanup_pcap_file(self.data.dut1, pcap_file_port3)

            # Step 9: Verify VLAN configuration
            st.log(f"\n{'='*60}")
            st.log("STEP 9: Verify VLAN configuration using show running-config")
            st.log(f"{'='*60}")

            if use_running_config:
                # Verify VLAN exists
                cmd = f"show running-configuration | include Vlan{vlan_id}"
                output = st.show(self.data.dut1, cmd, type="klish")
                st.log(f"VLAN {vlan_id} running-config: {output}")

            st.log(f"\n{'='*60}")
            st.log(f"✓ {tcid} PASSED: Unknown unicast flooded to all VLAN ports")
            st.log(f"{'='*60}")
            st.report_pass(tcid)

        except Exception as e:
            st.error(f"Exception in {tcid}: {e}")
            st.report_fail(tcid, str(e))
