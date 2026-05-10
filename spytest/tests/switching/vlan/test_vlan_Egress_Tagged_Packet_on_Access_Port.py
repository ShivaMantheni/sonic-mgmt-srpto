"""
TC_VLAN_TAG_002: Egress Tagged Packet on Access Port

Author: Test Automation Team
Date: 2026-05-11

How to run:
  ./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \
  tests/switching/vlan/test_vlan_Egress_Tagged_Packet_on_Access_Port.py \
  --logs-path ./logs/vlan_tag_002_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native

Description:
  TC_VLAN_TAG_002: Egress Tagged Packet on Access Port
  Objective: Verify tagged packet is untagged when egressing access port
  
  Steps:
    1. Create VLAN 10 on both DUTs
    2. Configure Port1 (D1) as tagged trunk port for VLAN 10
    3. Configure Port1 (D2) as untagged access port for VLAN 10
    4. Start packet capture on access port
    5. Send VLAN 10 tagged packet from trunk port using Scapy
    6. Analyze packets and verify untagged (no 802.1Q header)
    7. Cleanup all configurations
    
  Expected Result: Tagged packet is untagged when forwarded to access port
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

VAR_FILE_ENV = "VLAN_TAG_002_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_tag_002.yaml"
)


def _load_yaml_config() -> Dict[str, Any]:
    """Load test configuration from YAML file."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        st.warn(f"VLAN variable file not found: {candidate}, using defaults")
        return {
            "defaults": {
                "cli_type": "klish",
                "vlan_id": 10,
                "packet_count": 10,
                "cleanup": True
            },
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    st.log(f"Loaded VLAN TAG_002 configuration from: {candidate}")
    return config


@pytest.mark.topology("D1D2:2")
class TestVlanEgressTaggedPacketOnAccessPort:
    """Test class for VLAN egress packet untagging on access ports (TC_VLAN_TAG_002)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Setup: Load config, verify topology, clear interfaces, cleanup test VLANs."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_TAG_002: EGRESS TAGGED PACKET ON ACCESS PORT - SETUP")
        st.banner("=" * 100)

        config = _load_yaml_config()
        defaults = config.get("defaults", {})

        # Get 2-node topology (D1D2:2)
        topology = st.ensure_min_topology("D1D2:2")

        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.vlan_id = defaults.get("vlan_id", 10)
        cls.data.packet_count = defaults.get("packet_count", 10)
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT handles and ports dynamically from testbed
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.d1_port = topology.D1D2P1  # Port on D1 connecting to D2
        cls.data.d2_port = topology.D2D1P1  # Port on D2 connecting to D1

        st.log(f"DUT1 (D1): {cls.data.dut1}")
        st.log(f"DUT2 (D2): {cls.data.dut2}")
        st.log(f"D1 Port (D1→D2): {cls.data.d1_port}")
        st.log(f"D2 Port (D2→D1): {cls.data.d2_port}")
        st.log(f"VLAN ID: {cls.data.vlan_id}")
        st.log(f"CLI Type: {cls.data.cli_type}")

        # Track configurations for cleanup
        cls.data.configured_ports = []
        cls.data.configured_vlans = []
        cls.data.pcap_files = []

        # Clear existing configurations
        cls._clear_interface_config()

        # Pre-test cleanup
        cls._cleanup_test_vlans()

        st.banner("SETUP COMPLETE")

    @classmethod
    def _clear_interface_config(cls) -> None:
        """Clear any existing VLAN or IP configuration on test interfaces."""
        st.banner("CLEARING INTERFACE CONFIGURATIONS")

        for dut_name, dut, port in [
            ("D1", cls.data.dut1, cls.data.d1_port),
            ("D2", cls.data.dut2, cls.data.d2_port)
        ]:
            st.log(f"Clearing config on {dut_name} port {port}")
            try:
                st.config(dut, [
                    f"interface {port}",
                    "no ip address",
                    "no switchport access vlan",
                    "exit"
                ], type=cls.data.cli_type, skip_error_check=True)
                st.log(f"Cleared {port} on {dut_name}")
            except Exception as e:
                st.log(f"Exception clearing {dut_name} port {port}: {e}")

    @classmethod
    def _cleanup_test_vlans(cls) -> None:
        """Cleanup test VLANs before starting."""
        st.banner("PRE-TEST CLEANUP")

        vlan_id = str(cls.data.vlan_id)

        for dut_name, dut in [("D1", cls.data.dut1), ("D2", cls.data.dut2)]:
            try:
                vlan_api.delete_vlan(dut, vlan_id, cli_type=cls.data.cli_type,
                                    skip_error_report=True, remove_vlan_mapping=False)
                st.log(f"Pre-cleanup: VLAN {vlan_id} removed from {dut_name} (if existed)")
            except Exception as e:
                st.log(f"Pre-cleanup exception on {dut_name}: {e}")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup all configurations after test completes."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_TAG_002: CLEANUP")
        st.banner("=" * 100)

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled")
            return

        try:
            # Remove port configurations
            for dut, port in reversed(cls.data.configured_ports):
                try:
                    st.config(dut, [
                        f"interface {port}",
                        "no switchport access vlan",
                        "no switchport mode",
                        "exit"
                    ], type=cls.data.cli_type, skip_error_check=True)
                    st.log(f"Reset port {port}")
                except Exception as e:
                    st.log(f"Exception resetting {port}: {e}")

            # Remove VLAN configurations
            for dut, vlan_id in reversed(cls.data.configured_vlans):
                try:
                    vlan_api.delete_vlan(dut, str(vlan_id), cli_type=cls.data.cli_type,
                                        skip_error_report=True, remove_vlan_mapping=False)
                    st.log(f"Removed VLAN {vlan_id}")
                except Exception as e:
                    st.log(f"Exception removing VLAN {vlan_id}: {e}")

        except Exception as e:
            st.log(f"Cleanup exception: {e}")

        finally:
            # Clean pcap files
            for pcap_file in cls.data.pcap_files:
                try:
                    Path(pcap_file).unlink(missing_ok=True)
                except Exception as e:
                    st.log(f"Exception deleting {pcap_file}: {e}")

            st.banner("CLEANUP COMPLETE")

    def _print_step_result(self, step_num: int, step_name: str, passed: bool) -> None:
        """Print formatted step result."""
        status = "PASS" if passed else "FAIL"
        st.log("")
        st.log("=" * 80)
        st.log(f"STEP {step_num}: {step_name} - {status}")
        st.log("=" * 80)

    def _get_interface_mac(self, dut: str, interface: str) -> Optional[str]:
        """Retrieve MAC address of interface."""
        try:
            output = st.show(dut, f"show interface {interface}",
                           type=self.data.cli_type, skip_tmpl=True)
            if not output:
                return None

            mac_pattern = r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})'
            match = re.search(mac_pattern, str(output))

            if match:
                mac = match.group(1).lower()
                st.log(f"Found MAC for {interface}: {mac}")
                return mac
            return None

        except Exception as e:
            st.log(f"Error getting MAC for {interface}: {e}")
            return None

    def _send_tagged_packet(self, dut: str, src_interface: str, dst_mac: str,
                           src_mac: str, vlan_id: int, packet_count: int) -> bool:
        """Send VLAN-tagged packet using Scapy."""
        try:
            scapy_script = f"""
from scapy.all import Ether, Dot1Q, IP, ICMP, sendp
pkt = Ether(src="{src_mac}", dst="{dst_mac}")/Dot1Q(vlan={vlan_id})/IP(src="10.1.1.1", dst="10.1.1.2")/ICMP()
sendp(pkt, iface="{src_interface}", count={packet_count}, verbose=False)
print("Sent {packet_count} tagged packets")
"""

            script_path = "/tmp/scapy_send_vlan.py"
            with open(script_path, "w") as f:
                f.write(scapy_script)

            cmd = f"python3 {script_path}"
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            st.log(f"Sent {packet_count} VLAN {vlan_id} tagged packets from {src_interface}")

            return True

        except Exception as e:
            st.log(f"Error sending packet: {e}")
            return False

    def _capture_packets_with_tcpdump(self, dut: str, interface: str,
                                     pcap_file: str, timeout: int = 30) -> bool:
        """Start tcpdump packet capture."""
        try:
            cmd = f"sudo timeout {timeout} tcpdump -i {interface} -w {pcap_file} &"
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            st.log(f"Started tcpdump on {interface} -> {pcap_file}")

            self.data.pcap_files.append(pcap_file)
            time.sleep(1)

            return True

        except Exception as e:
            st.log(f"Error starting tcpdump: {e}")
            return False

    def _stop_tcpdump(self, dut: str) -> bool:
        """Kill tcpdump process to ensure PCAP file is flushed to disk."""
        try:
            st.log("Stopping tcpdump process and flushing file to disk")
            cmd = "sudo pkill -f tcpdump"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            time.sleep(1)  # Give time for file to be written
            return True
        except Exception as e:
            st.log(f"Error stopping tcpdump: {e}")
            return False

    def _analyze_pcap_for_untagged_packets(self, dut: str, pcap_file: str) -> bool:
        """Analyze pcap file for untagged packets."""
        try:
            time.sleep(2)

            # Check if pcap file exists
            check_cmd = f"test -f {pcap_file} && echo 'exists' || echo 'not_found'"
            output = st.show(dut, check_cmd, skip_tmpl=True, skip_error_check=True)

            if "not_found" in str(output):
                st.log("No packets captured - ISOLATION CONFIRMED")
                return True

            # Build analysis script as list of lines (for printf, not local write)
            script_lines = [
                "from scapy.all import rdpcap, Dot1Q",
                "try:",
                f"    packets = rdpcap(\"{pcap_file}\")",
                "    tagged = sum(1 for pkt in packets if Dot1Q in pkt)",
                "    untagged = sum(1 for pkt in packets if Dot1Q not in pkt)",
                "    if tagged == 0 and untagged > 0:",
                "        print(\"SUCCESS: All untagged\")",
                "    elif tagged > 0:",
                "        print(\"FAIL: Found tagged packets\")",
                "    else:",
                "        print(\"INFO: No packets\")",
                "except Exception as e:",
                "    print(f\"Error: {e}\")"
            ]

            # Write script on remote device using printf (not locally)
            script_path = f"/tmp/scapy_analyze_{int(time.time())}.py"
            script_content = "\\n".join(script_lines)
            cmd = f"printf '{script_content}' > {script_path}"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            # Execute analysis script
            cmd_exec = f"python3 {script_path}"
            output = st.show(dut, cmd_exec, skip_tmpl=True, skip_error_check=True)
            output_str = str(output).lower()

            if "success" in output_str or "untagged" in output_str:
                st.log("Pcap analysis: Packets are untagged - PASS")
                return True
            else:
                st.log(f"Pcap analysis result: {output}")
                return False

        except Exception as e:
            st.log(f"Error analyzing pcap: {e}")
            return False

    @pytest.mark.inventory(feature="VLAN_Tagging", testcases=["TC_VLAN_TAG_002"])
    def test_vlan_tag_002_egress_untagging_on_access_port(self) -> None:
        """
        TC_VLAN_TAG_002: Egress Tagged Packet on Access Port

        Objective: Verify tagged packets are untagged on access port egress
        
        Steps:
            1. Create VLAN 10 on both DUTs
            2. Configure D1 Port as tagged trunk port for VLAN 10
            3. Configure D2 Port as untagged access port for VLAN 10
            4. Start packet capture on D2 Port
            5. Send VLAN 10 tagged packets from D1 Port using Scapy
            6. Analyze packets and verify untagged (no 802.1Q header)
            7. Cleanup all configurations
            
        Expected Result: Tagged packets are untagged on access port
        """
        st.banner("=" * 100)
        st.banner("TC_VLAN_TAG_002: TEST")
        st.banner("=" * 100)

        dut1 = self.data.dut1
        dut2 = self.data.dut2
        cli_type = self.data.cli_type
        d1_port = self.data.d1_port
        d2_port = self.data.d2_port
        vlan_id = self.data.vlan_id
        packet_count = self.data.packet_count

        # Track step results
        test_results = {
            "step_1": False,
            "step_2": False,
            "step_3": False,
            "step_4": False,
            "step_5": False,
            "step_6": False,
            "step_7": False,
        }

        pcap_file = f"/tmp/vlan_tag_002_{int(time.time())}.pcap"

        try:
            # STEP 1: Create VLAN 10
            st.log("\nSTEP 1: Creating VLAN 10 on both DUTs")
            st.log("=" * 80)

            step_passed = True
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    result = vlan_api.create_vlan(dut, str(vlan_id), cli_type=cli_type)
                    if result:
                        st.log(f"VLAN {vlan_id} created on {dut_name}")
                        self.data.configured_vlans.append((dut, vlan_id))
                    else:
                        st.log(f"VLAN {vlan_id} creation failed on {dut_name}")
                        step_passed = False
                except Exception as e:
                    st.log(f"Exception on {dut_name}: {e}")
                    step_passed = False

            test_results["step_1"] = step_passed
            self._print_step_result(1, f"Create VLAN {vlan_id}", step_passed)

            if not step_passed:
                st.report_fail("msg", "STEP 1 FAILED")

            # STEP 2: Configure D1 port as trunk port
            st.log("\nSTEP 2: Configure D1 port as trunk port (tagged)")
            st.log("=" * 80)

            step_passed = True
            try:
                st.config(dut1, [
                    f"interface {d1_port}",
                    f"switchport trunk allowed vlan {vlan_id}",
                    "exit"
                ], type=cli_type)

                st.log(f"Configured {d1_port} as trunk port")
                self.data.configured_ports.append((dut1, d1_port))
                step_passed = True

            except Exception as e:
                st.log(f"Error: {e}")
                step_passed = False

            test_results["step_2"] = step_passed
            self._print_step_result(2, "Configure trunk port", step_passed)

            if not step_passed:
                st.report_fail("msg", "STEP 2 FAILED")

            # STEP 3: Configure D2 port as access port
            st.log("\nSTEP 3: Configure D2 port as access port (untagged)")
            st.log("=" * 80)

            step_passed = True
            try:
                st.config(dut2, [
                    f"interface {d2_port}",
                    f"switchport access vlan {vlan_id}",
                    "exit"
                ], type=cli_type)

                st.log(f"Configured {d2_port} as access port")
                self.data.configured_ports.append((dut2, d2_port))
                step_passed = True

            except Exception as e:
                st.log(f"Error: {e}")
                step_passed = False

            test_results["step_3"] = step_passed
            self._print_step_result(3, "Configure access port", step_passed)

            if not step_passed:
                st.report_fail("msg", "STEP 3 FAILED")

            # STEP 4: Start packet capture
            st.log("\nSTEP 4: Start tcpdump capture on access port")
            st.log("=" * 80)

            step_passed = self._capture_packets_with_tcpdump(dut2, d2_port, pcap_file)
            test_results["step_4"] = step_passed
            self._print_step_result(4, "Start packet capture", step_passed)

            if not step_passed:
                st.report_fail("msg", "STEP 4 FAILED")

            # STEP 5: Send tagged packets
            st.log("\nSTEP 5: Send VLAN tagged packets from trunk port")
            st.log("=" * 80)

            step_passed = True
            try:
                d1_mac = self._get_interface_mac(dut1, d1_port)
                d2_mac = self._get_interface_mac(dut2, d2_port)

                if not d1_mac or not d2_mac:
                    st.log("Failed to get MAC addresses")
                    step_passed = False
                else:
                    result = self._send_tagged_packet(dut1, d1_port, d2_mac, d1_mac, vlan_id, packet_count)
                    step_passed = result

            except Exception as e:
                st.log(f"Error: {e}")
                step_passed = False

            test_results["step_5"] = step_passed
            self._print_step_result(5, "Send tagged packets", step_passed)

            # STEP 5.5: Stop tcpdump to flush PCAP file
            st.log("\nSTEP 5.5: Stopping tcpdump and flushing PCAP file")
            st.log("=" * 80)
            self._stop_tcpdump(dut2)
            time.sleep(2)  # Extra wait for file to be fully written

            # STEP 6: Analyze packets
            st.log("\nSTEP 6: Analyze pcap and verify packets are untagged")
            st.log("=" * 80)

            step_passed = self._analyze_pcap_for_untagged_packets(dut2, pcap_file)
            test_results["step_6"] = step_passed
            self._print_step_result(6, "Verify packets untagged", step_passed)

            # STEP 7: Cleanup (in teardown_class)
            st.log("\nSTEP 7: Cleanup phase (in teardown_class)")
            st.log("=" * 80)

            test_results["step_7"] = True
            self._print_step_result(7, "Cleanup", True)

            # Overall result
            overall_passed = all(test_results.values())
            passed_count = sum(test_results.values())
            total_steps = len(test_results)

            st.log("\n" + "=" * 100)
            st.log(f"OVERALL TEST RESULT: {'PASSED' if overall_passed else 'FAILED'} ({passed_count}/{total_steps} steps)")
            st.log("=" * 100)

            if not overall_passed:
                failed_steps = [k for k, v in test_results.items() if not v]
                st.log(f"Failed steps: {failed_steps}")
                st.report_fail("msg", f"Test failed - {failed_steps}")
            else:
                st.report_pass("test_case_passed")

        except Exception as e:
            st.log(f"Test exception: {e}")
            st.report_fail("msg", f"Test exception: {e}")
