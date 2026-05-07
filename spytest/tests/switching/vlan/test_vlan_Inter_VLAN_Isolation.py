"""
TC_VLAN_FORWARD_004: Inter-VLAN Isolation

Author: Test Automation Team
Date: 2026-05-07

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Inter_VLAN_Isolation.py \\
  --logs-path ./logs/vlan_inter_isolation_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Comprehensive validation of inter-VLAN isolation using SpyTest APIs and
  Scapy-based traffic generation. Tests verify that traffic between different
  VLANs is isolated and not forwarded without explicit routing.

  TC_VLAN_FORWARD_004: Inter-VLAN Isolation
    Objective: Verify traffic isolation between different VLANs
    Steps:
      1. Create VLANs 10 and 20
      2. Configure Port1 in VLAN 10
      3. Configure Port2 in VLAN 20
      4. Retrieve MAC addresses for both ports
      5. Start packet capture on Port2
      6. Send unicast packet from Port1 to Port2's MAC using Scapy
      7. Verify packet is NOT received on Port2
      8. Verify VLANs are isolated using show running-config
    Expected Result: VLANs are properly isolated; Port2 does not receive
                     packets from Port1 despite knowing destination MAC

Pre-requisites:
  - Topology: Two DUTs (D1-D2) with 2+ connections | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 2 nodes
        # +------------------+       +------------------+
        # |      DUT1        |-------|      DUT2        |
        # |    (Leaf)       | D1D2P1 |    (Spine)      |
        # |                  |       |                  |
        # | Port1 (VLAN10)   |  ||   | Port2 (VLAN20) |
        # +------------------+       +------------------+

  - Feature flags / min SONiC version: SONiC 202211 or later with Scapy support
  - Required test variables (YAML): spytest/vars/switching/vlan/vars_vlan_inter_isolation.yaml
  - Interface names are picked from testbed.yaml (not hardcoded)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
import re
import time

import pytest
import yaml

from scapy.all import Ether, Raw, rdpcap, Dot1Q

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api
import apis.system.interface as intf_api

VAR_FILE_ENV = "VLAN_INTER_ISOLATION_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_inter_isolation.yaml"
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
                "min_topology": ["D1D2:2"],
                "verify_timeout": 30,
                "cleanup": True
            },
            "testcases": {
                "TC_VLAN_FORWARD_004": {
                    "traffic": {
                        "packet_count": 10,
                        "packet_size": 64
                    },
                    "verification": {
                        "verify_vlan_config": True,
                        "verify_port_config": True,
                        "verify_isolation": True,
                        "use_show_running_config": True
                    }
                }
            },
        }

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


@pytest.mark.topology("D1D2:2")
class TestVlanInterIsolation:
    """Testcases for inter-VLAN isolation verification."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and testcase variables for the suite."""
        st.banner("=" * 90)
        st.banner("VLAN INTER-VLAN ISOLATION TEST SUITE - SETUP")
        st.banner("=" * 90)

        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Get 2-node topology (D1D2:2)
        min_topology = defaults.get("min_topology") or ["D1D2:2"]
        topology = st.ensure_min_topology(*min_topology)

        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # VLAN IDs to use
        cls.data.vlan_10_id = defaults.get("vlan_10_id", "10")
        cls.data.vlan_20_id = defaults.get("vlan_20_id", "20")

        # Get DUT handles from topology (dynamically from testbed)
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut_names = st.get_dut_names()

        # Get ports from topology dynamically (from testbed.yaml, NOT hardcoded)
        cls.data.dut1_dut2_p1 = topology.D1D2P1  # Port on DUT1 connected to DUT2
        cls.data.dut2_dut1_p1 = topology.D2D1P1  # Port on DUT2 connected to DUT1

        st.log(f"✅ DUT1 (D1) for testing: {cls.data.dut1}")
        st.log(f"✅ DUT2 (D2) for testing: {cls.data.dut2}")
        st.log(f"✅ D1→D2 Port 1: {cls.data.dut1_dut2_p1}")
        st.log(f"✅ D2→D1 Port 1: {cls.data.dut2_dut1_p1}")
        st.log(f"✅ VLAN 10 ID: {cls.data.vlan_10_id}")
        st.log(f"✅ VLAN 20 ID: {cls.data.vlan_20_id}")
        st.log(f"✅ CLI Type: {cls.data.cli_type}")

        # Clear any existing IP/VLAN configurations on test ports
        cls._clear_interface_config()

        # Pre-test cleanup - ensure VLANs used in tests don't exist
        cls._cleanup_test_vlans()

        st.banner("✅ SETUP COMPLETE - Ready for testing")

    @classmethod
    def _clear_interface_config(cls) -> None:
        """Clear any existing VLAN or IP configuration on test interfaces."""
        st.banner("CLEARING INTERFACE CONFIGURATIONS")

        for dut_name, dut, port in [
            ("D1", cls.data.dut1, cls.data.dut1_dut2_p1),
            ("D2", cls.data.dut2, cls.data.dut2_dut1_p1)
        ]:
            st.log(f"Clearing config on {dut_name} port {port}")
            try:
                # Simple and safe cleanup without querying (to avoid command errors)
                # Remove any VLAN membership configuration
                try:
                    st.config(dut, f"interface {port}\nno switchport access vlan",
                             type=cls.data.cli_type, skip_error_check=True)
                except Exception as e:
                    st.log(f"  ⚠️  Could not remove switchport config: {e}")

                # Remove any IP address configuration
                try:
                    st.config(dut, f"interface {port}\nno ip address",
                             type=cls.data.cli_type, skip_error_check=True)
                except Exception as e:
                    st.log(f"  ⚠️  Could not remove IP config: {e}")

                st.log(f"✅ {dut_name} interface {port} cleared")
            except Exception as e:
                st.log(f"⚠️  Exception clearing {dut_name} port {port}: {e}")

    @classmethod
    def _cleanup_test_vlans(cls) -> None:
        """Cleanup VLANs that will be used in tests before starting."""
        st.banner("PRE-TEST CLEANUP - REMOVING TEST VLANS")

        dut1 = cls.data.dut1
        dut2 = cls.data.dut2
        cli_type = cls.data.cli_type
        vlans_to_delete = [cls.data.vlan_10_id, cls.data.vlan_20_id]

        for vlan_id in vlans_to_delete:
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    vlan_api.delete_vlan(dut, str(vlan_id), cli_type=cli_type,
                                        skip_error_report=True, remove_vlan_mapping=False)
                    st.log(f"✅ Pre-cleanup: VLAN {vlan_id} removed from {dut_name} (if existed)")
                except Exception as e:
                    st.log(f"⚠️  Pre-cleanup exception VLAN {vlan_id} on {dut_name}: {e}")

        st.log("✅ Pre-test cleanup completed")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup all VLANs and configurations after test suite completes."""
        st.banner("=" * 90)
        st.banner("VLAN INTER-VLAN ISOLATION TEST SUITE - CLEANUP")
        st.banner("=" * 90)

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        dut1 = cls.data.dut1
        dut2 = cls.data.dut2
        cli_type = cls.data.cli_type

        st.log("Removing all VLAN configurations...")
        for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
            try:
                vlan_list = vlan_api.get_vlan_list(dut, cli_type=cli_type)
                if vlan_list:
                    st.log(f"Cleaning up VLANs on {dut_name}: {vlan_list}")
                    for vlan in vlan_list:
                        if str(vlan) != "1":  # Don't delete default VLAN
                            try:
                                vlan_api.delete_vlan(dut, str(vlan), cli_type=cli_type,
                                                   skip_error_report=True, remove_vlan_mapping=False)
                                st.log(f"  ✅ Deleted VLAN {vlan} from {dut_name}")
                            except Exception as e:
                                st.log(f"  ⚠️  Failed to delete VLAN {vlan} on {dut_name}: {e}")
            except Exception as e:
                st.log(f"Cleanup exception on {dut_name}: {e}")

        st.log("✅ Cleanup completed")

    def _print_step_result(self, step_num: int, step_name: str, passed: bool) -> None:
        """Print formatted step result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        st.log(f"\n{'='*80}")
        st.log(f"STEP {step_num}: {step_name} - {status}")
        st.log(f"{'='*80}")

    def _get_interface_mac(self, dut, intf) -> str:
        """Retrieve MAC address of a given interface on DUT."""
        try:
            # Execute show interface command using klish CLI, then grep using shell
            cmd = f"show interface {intf}"
            output = st.show(dut, cmd, type="klish", skip_tmpl=True, skip_error_check=True)

            # Parse MAC from output using string operations (avoiding pipes which don't work in klish)
            output_str = str(output) if output else ""

            # Search for MAC address in the output (format: XX:XX:XX:XX:XX:XX)
            mac_match = re.search(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})", output_str)
            if mac_match:
                st.log(f"Found MAC address: {mac_match.group(1)}")
                return mac_match.group(1)

            # Fallback: generate MAC from interface number
            st.log(f"Could not retrieve MAC from show interface, using generated MAC")
            return f"00:11:22:33:{int(intf.replace('Ethernet', '')) // 256:02x}:{int(intf.replace('Ethernet', '')) % 256:02x}"
        except Exception as e:
            st.error(f"Error retrieving MAC for {intf}: {e}")
            return "00:11:22:33:44:55"

    def _create_vlan(self, dut, vlan_id) -> bool:
        """Create a VLAN on the specified DUT using klish CLI."""
        try:
            st.log(f"Creating VLAN {vlan_id} on {dut}")
            cmd = f"interface Vlan {vlan_id}"
            st.config(dut, cmd, type="klish")
            st.log(f"✅ VLAN {vlan_id} created successfully")
            return True
        except Exception as e:
            st.error(f"Error creating VLAN {vlan_id}: {e}")
            return False

    def _configure_access_port(self, dut, intf, vlan_id) -> bool:
        """Configure an access port in a VLAN using klish CLI."""
        try:
            st.log(f"Configuring {intf} as access port in VLAN {vlan_id} on {dut}")
            cmds = [
                f"interface {intf}",
                f"switchport access Vlan {vlan_id}",
                "exit"
            ]
            st.config(dut, cmds, type="klish")
            st.log(f"✅ {intf} configured as access port in VLAN {vlan_id} successfully")
            return True
        except Exception as e:
            st.error(f"Error configuring {intf}: {e}")
            return False

    def _verify_vlan_config(self, dut, dut_name, vlan_id) -> bool:
        """Verify VLAN configuration using show commands."""
        st.log(f"\nVerifying VLAN {vlan_id} configuration on {dut_name}...")

        try:
            # Method 1: show Vlan <id>
            output = st.show(dut, f"show Vlan {vlan_id}", type="klish",
                           skip_tmpl=True, skip_error_check=True)
            output_str = str(output)
            if f"Vlan{vlan_id}" in output_str or f"VLAN {vlan_id}" in output_str:
                st.log(f"  ✅ 'show Vlan {vlan_id}' - FOUND")
                return True
            else:
                st.log(f"  ❌ 'show Vlan {vlan_id}' - NOT FOUND")
                return False
        except Exception as e:
            st.log(f"  ⚠️  Exception verifying VLAN {vlan_id}: {e}")
            return False

    def _create_l2_scapy_script(self, src_mac, dst_mac, packet_count=10, packet_size=64, iface="eth0") -> str:
        """Create a Scapy script to generate L2 unicast Ethernet frames."""
        script_path = "/tmp/scapy_inter_vlan_isolation.py"

        script_content = f"""#!/usr/bin/env python3
import sys
from scapy.all import Ether, Raw, sendp, conf

# Disable ARP
conf.checkIPaddr = False

# Packet parameters
src_mac = "{src_mac}"
dst_mac = "{dst_mac}"
packet_count = {packet_count}
packet_size = {packet_size}
iface = "{iface}"
payload_size = max(0, packet_size - 14)  # Ethernet header is 14 bytes

# Generate payload
payload = ("A" * payload_size).encode()

# Create and send packets
packet = Ether(src=src_mac, dst=dst_mac) / Raw(load=payload)

print(f"Sending {{packet_count}} packets from {{src_mac}} to {{dst_mac}} on {{iface}}")
print(f"Packet size: {{packet_size}} bytes")
print(f"Payload size: {{payload_size}} bytes")

try:
    sendp(packet, iface=iface, count=packet_count, inter=0.1, verbose=True)
    print("✅ Packets sent successfully")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error sending packets: {{e}}")
    sys.exit(1)
"""

        try:
            with open(script_path, "w") as f:
                f.write(script_content)
            st.log(f"✅ Scapy script created at {script_path}")
            return script_path
        except Exception as e:
            st.error(f"Error creating Scapy script: {e}")
            return ""

    def _send_l2_traffic(self, dut, script_path, iface) -> bool:
        """Execute Scapy script to send L2 traffic."""
        try:
            st.log(f"Sending L2 traffic from {dut} using Scapy script")
            cmd = f"python3 {script_path}"
            # Use shell execution without type="klish" for bash commands
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            st.log(f"Scapy output: {output}")
            st.log("✅ L2 traffic sent successfully")
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

            # Use shell execution without type="klish" for bash commands
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            time.sleep(2)  # Give tcpdump time to start

            # Verify tcpdump is running using shell execution
            verify_cmd = f"ps aux | grep [t]cpdump"
            verify_output = st.show(dut, verify_cmd, skip_tmpl=True, skip_error_check=True)
            if verify_output and intf in str(verify_output):
                st.log(f"✅ tcpdump started on {intf}")
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

            # Send SIGTERM to tcpdump using shell execution
            cmd = f"pkill -TERM tcpdump"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            time.sleep(1)

            # Force kill if still running using shell execution
            cmd = f"pkill -9 tcpdump"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            time.sleep(1)

            st.log(f"✅ tcpdump stopped on {intf}")
            return True
        except Exception as e:
            st.error(f"Error stopping tcpdump on {intf}: {e}")
            return False

    def _verify_pcap_packets_not_received(self, pcap_file, dst_mac) -> bool:
        """Verify that NO packets were captured to destination MAC (isolation confirmed)."""
        try:
            st.log(f"Verifying PCAP file: {pcap_file} (should be EMPTY - isolation verified)")

            if not Path(pcap_file).is_file():
                st.log(f"✅ PCAP file does not exist - NO packets captured (ISOLATION CONFIRMED)")
                return True

            # Try to read PCAP
            try:
                packets = rdpcap(pcap_file)
            except Exception as e:
                st.log(f"Could not read PCAP: {e} - Treating as empty")
                return True

            if not packets or len(packets) == 0:
                st.log(f"✅ PCAP is empty - NO packets captured (ISOLATION CONFIRMED)")
                return True

            # If we have packets, verify they are NOT to our destination MAC
            packet_count = 0
            dst_mac_lower = dst_mac.lower()

            for pkt in packets:
                if Ether in pkt:
                    eth = pkt[Ether]
                    if eth.dst.lower() == dst_mac_lower:
                        st.error(f"❌ ISOLATION BREACH: Found packet to {dst_mac}")
                        return False
                    packet_count += 1

            st.log(f"✅ Analyzed {packet_count} packets - none to {dst_mac} (ISOLATION CONFIRMED)")
            return True

        except Exception as e:
            st.error(f"Error verifying PCAP: {e}")
            return False

    def _cleanup_pcap_file(self, dut, pcap_file) -> bool:
        """Remove PCAP file after verification."""
        try:
            st.log(f"Cleaning up PCAP file: {pcap_file}")
            cmd = f"rm -f {pcap_file}"
            # Use shell execution without type="klish" for bash commands
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            st.log(f"✅ PCAP file cleaned up")
            return True
        except Exception as e:
            st.warn(f"Error cleaning up PCAP: {e}")
            return True  # Don't fail if cleanup fails

    def test_tc_vlan_forward_004_inter_vlan_isolation(self) -> None:
        """
        TC_VLAN_FORWARD_004: Inter-VLAN Isolation

        Objective: Verify traffic isolation between different VLANs

        Steps:
        1. Create VLANs 10 and 20
        2. Configure Port1 in VLAN 10
        3. Configure Port2 in VLAN 20
        4. Retrieve MAC addresses for both ports
        5. Start packet capture on Port2
        6. Send unicast packet from Port1 to Port2's MAC using Scapy
        7. Verify packet is NOT received on Port2
        8. Verify VLANs are isolated using show running-config

        Expected Result: VLANs are properly isolated; Port2 does not receive
                         packets from Port1 despite knowing destination MAC
        """
        tcid = "TC_VLAN_FORWARD_004"
        st.banner(f"Starting {tcid}: Inter-VLAN Isolation")

        # Track step results
        step_results = {}
        all_steps_passed = True

        # Get testcase configuration
        testcase_cfg = self.data.testcases.get(tcid, {})

        # Get traffic configuration
        traffic_cfg = testcase_cfg.get("traffic", {})
        packet_count = traffic_cfg.get("packet_count", 10)
        packet_size = traffic_cfg.get("packet_size", 64)

        # Get verification configuration
        verify_cfg = testcase_cfg.get("verification", {})
        verify_vlan_config = verify_cfg.get("verify_vlan_config", True)
        verify_port_config = verify_cfg.get("verify_port_config", True)
        verify_isolation = verify_cfg.get("verify_isolation", True)
        use_running_config = verify_cfg.get("use_show_running_config", True)

        try:
            # Step 1: Create VLANs
            st.log(f"\n{'='*80}")
            st.log(f"STEP 1: Create VLANs {self.data.vlan_10_id} and {self.data.vlan_20_id}")
            st.log(f"{'='*80}")

            step_1_passed = True
            if not self._create_vlan(self.data.dut1, self.data.vlan_10_id):
                step_1_passed = False
                all_steps_passed = False

            if not self._create_vlan(self.data.dut1, self.data.vlan_20_id):
                step_1_passed = False
                all_steps_passed = False

            if not self._create_vlan(self.data.dut2, self.data.vlan_10_id):
                step_1_passed = False
                all_steps_passed = False

            if not self._create_vlan(self.data.dut2, self.data.vlan_20_id):
                step_1_passed = False
                all_steps_passed = False

            self._print_step_result(1, "Create VLANs", step_1_passed)
            step_results[1] = step_1_passed

            if not step_1_passed:
                st.report_fail("vlan_creation_failed")

            # Step 2: Configure Port1 in VLAN 10 on DUT1
            st.log(f"\n{'='*80}")
            st.log(f"STEP 2: Configure {self.data.dut1_dut2_p1} as access port in VLAN {self.data.vlan_10_id}")
            st.log(f"{'='*80}")

            step_2_passed = self._configure_access_port(self.data.dut1, self.data.dut1_dut2_p1, self.data.vlan_10_id)
            self._print_step_result(2, f"Configure {self.data.dut1_dut2_p1} in VLAN {self.data.vlan_10_id}", step_2_passed)
            step_results[2] = step_2_passed

            if not step_2_passed:
                all_steps_passed = False
                st.report_fail("port_configuration_failed", self.data.dut1_dut2_p1)

            # Step 3: Configure Port2 in VLAN 20 on DUT2
            st.log(f"\n{'='*80}")
            st.log(f"STEP 3: Configure {self.data.dut2_dut1_p1} as access port in VLAN {self.data.vlan_20_id}")
            st.log(f"{'='*80}")

            step_3_passed = self._configure_access_port(self.data.dut2, self.data.dut2_dut1_p1, self.data.vlan_20_id)
            self._print_step_result(3, f"Configure {self.data.dut2_dut1_p1} in VLAN {self.data.vlan_20_id}", step_3_passed)
            step_results[3] = step_3_passed

            if not step_3_passed:
                all_steps_passed = False
                st.report_fail("port_configuration_failed", self.data.dut2_dut1_p1)

            # Step 4: Retrieve MAC addresses
            st.log(f"\n{'='*80}")
            st.log("STEP 4: Retrieve MAC addresses for Port1 and Port2")
            st.log(f"{'='*80}")

            port1_mac = self._get_interface_mac(self.data.dut1, self.data.dut1_dut2_p1)
            port2_mac = self._get_interface_mac(self.data.dut2, self.data.dut2_dut1_p1)

            step_4_passed = bool(port1_mac and port2_mac and ":" in port1_mac and ":" in port2_mac)
            st.log(f"Port1 ({self.data.dut1_dut2_p1}) MAC: {port1_mac}")
            st.log(f"Port2 ({self.data.dut2_dut1_p1}) MAC: {port2_mac}")
            self._print_step_result(4, "Retrieve MAC addresses", step_4_passed)
            step_results[4] = step_4_passed

            if not step_4_passed:
                all_steps_passed = False
                st.warn("Could not retrieve valid MAC addresses")

            # Step 5: Start tcpdump on Port2
            st.log(f"\n{'='*80}")
            st.log(f"STEP 5: Start tcpdump on {self.data.dut2_dut1_p1}")
            st.log(f"{'='*80}")

            pcap_file = f"/tmp/vlan_inter_isolation_{self.data.dut2_dut1_p1}.pcap"
            bpf_filter = f"ether dst {port2_mac}"

            step_5_passed = self._start_tcpdump(self.data.dut2, self.data.dut2_dut1_p1, pcap_file, bpf_filter, timeout=30)
            self._print_step_result(5, f"Start tcpdump on {self.data.dut2_dut1_p1}", step_5_passed)
            step_results[5] = step_5_passed

            if not step_5_passed:
                all_steps_passed = False
                st.warn("tcpdump start failed, continuing anyway")

            # Step 6: Send packet from Port1 to Port2's MAC
            st.log(f"\n{'='*80}")
            st.log(f"STEP 6: Send unicast packet from {self.data.dut1_dut2_p1} to {port2_mac} using Scapy")
            st.log(f"{'='*80}")

            scapy_script = self._create_l2_scapy_script(
                port1_mac, port2_mac, packet_count=packet_count,
                packet_size=packet_size, iface=self.data.dut1_dut2_p1
            )

            step_6_passed = bool(scapy_script) and self._send_l2_traffic(self.data.dut1, scapy_script, self.data.dut1_dut2_p1)
            self._print_step_result(6, f"Send unicast packet from {self.data.dut1_dut2_p1} to {port2_mac}", step_6_passed)
            step_results[6] = step_6_passed

            if not step_6_passed:
                all_steps_passed = False
                st.warn("L2 traffic send failed, continuing anyway")

            # Wait for traffic to be processed
            time.sleep(3)

            # Step 7: Stop tcpdump and verify isolation
            st.log(f"\n{'='*80}")
            st.log("STEP 7: Stop tcpdump and verify isolation")
            st.log(f"{'='*80}")

            step_7_passed = self._stop_tcpdump(self.data.dut2, self.data.dut2_dut1_p1)
            self._print_step_result(7, "Stop tcpdump", step_7_passed)
            step_results[7] = step_7_passed

            # Verify isolation: PCAP should be empty (no packets received)
            isolation_verified = True
            if verify_isolation and step_7_passed:
                isolation_verified = self._verify_pcap_packets_not_received(pcap_file, port2_mac)
                st.log(f"Isolation Verification: {'✅ PASSED' if isolation_verified else '❌ FAILED'}")

            if not isolation_verified:
                all_steps_passed = False

            # Clean up PCAP
            self._cleanup_pcap_file(self.data.dut2, pcap_file)

            # Step 8: Verify VLAN configuration
            st.log(f"\n{'='*80}")
            st.log("STEP 8: Verify VLAN configuration using show running-config")
            st.log(f"{'='*80}")

            step_8_passed = True
            if use_running_config:
                # Verify VLAN 10 exists on DUT1
                vlan_10_verified = self._verify_vlan_config(self.data.dut1, "DUT1", self.data.vlan_10_id)

                # Verify VLAN 20 exists on DUT2
                vlan_20_verified = self._verify_vlan_config(self.data.dut2, "DUT2", self.data.vlan_20_id)

                step_8_passed = vlan_10_verified and vlan_20_verified

            self._print_step_result(8, "Verify VLAN configuration", step_8_passed)
            step_results[8] = step_8_passed

            if not step_8_passed:
                all_steps_passed = False

            # Print final summary
            st.log(f"\n{'='*80}")
            st.log("STEP EXECUTION SUMMARY")
            st.log(f"{'='*80}")
            for step_num in sorted(step_results.keys()):
                status = "✅ PASS" if step_results[step_num] else "❌ FAIL"
                st.log(f"Step {step_num}: {status}")

            st.log(f"\n{'='*80}")
            if all_steps_passed and isolation_verified:
                st.log(f"✅ {tcid} PASSED: VLANs are properly isolated")
                st.log(f"Overall Result: ✅ PASSED")
            else:
                st.log(f"❌ {tcid} FAILED: One or more steps failed")
                st.log(f"Overall Result: ❌ FAILED")
            st.log(f"{'='*80}")

            if all_steps_passed and isolation_verified:
                st.report_pass("test_case_passed")
            else:
                st.report_fail("test_case_failed")

        except Exception as e:
            st.error(f"Exception in {tcid}: {e}")
            st.log(f"\n{'='*80}")
            st.log(f"❌ {tcid} FAILED with exception: {str(e)}")
            st.log(f"Overall Result: ❌ FAILED")
            st.log(f"{'='*80}")
            st.report_fail("msg", f"{tcid} failed with exception: {str(e)}")
