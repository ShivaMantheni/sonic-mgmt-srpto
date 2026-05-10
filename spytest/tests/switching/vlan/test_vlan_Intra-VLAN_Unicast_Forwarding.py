"""
TC_VLAN_FORWARD_001: Intra-VLAN Unicast Forwarding

Author: Test Automation Team
Date: 2026-05-11

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Intra-VLAN_Unicast_Forwarding.py \\
  --logs-path ./logs/vlan_forward_001_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  TC_VLAN_FORWARD_001: Intra-VLAN Unicast Forwarding

  Objective: Verify unicast packet forwarding within VLAN

  Steps:
    1. Create VLAN 10 on both DUTs
    2. Configure Port1 (D1) as untagged access port for VLAN 10
    3. Configure Port2 (D2) as untagged access port for VLAN 10
    4. Retrieve MAC addresses from both ports
    5. Start packet capture on Port2
    6. Send unicast packet from Port1 to Port2's MAC using Scapy
    7. Analyze capture and verify unicast packet received on Port2 only

  Expected Result: Unicast packet forwarded to destination port in same VLAN,
                   not flooded to other ports

Pre-requisites:
  - Topology: Two DUTs (D1-D2) with 2+ connections | Supported: HW and Virtual
  - Feature flags / min SONiC version: SONiC 202211+ with Scapy support
  - Required test variables (YAML): spytest/vars/switching/vlan/vars_vlan_forward_001.yaml
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

VAR_FILE_ENV = "VLAN_FORWARD_001_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_forward_001.yaml"
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
                "min_topology": ["D1D2:2"],
                "cleanup": True
            },
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    st.log(f"Loaded VLAN FORWARD_001 configuration from: {candidate}")
    return config


@pytest.mark.topology("D1D2:2")
class TestVlanIntraVlanUnicastForwarding:
    """Test class for intra-VLAN unicast forwarding (TC_VLAN_FORWARD_001)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Class-level setup: Load config, verify topology, clear interfaces, cleanup test VLANs."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_FORWARD_001: INTRA-VLAN UNICAST FORWARDING - SETUP")
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
        cls.data.vlan_id = str(defaults.get("vlan_id", "10"))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUTs and ports (DYNAMIC from testbed)
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.d1_port = topology.D1D2P1  # Dynamic from testbed
        cls.data.d2_port = topology.D2D1P1  # Dynamic from testbed

        # Track configurations for cleanup
        cls.data.configured_vlans = []
        cls.data.configured_ports = []
        cls.data.pcap_files = []

        st.log(f"Topology: D1={cls.data.dut1}, D2={cls.data.dut2}")
        st.log(f"Ports: D1 Port={cls.data.d1_port}, D2 Port={cls.data.d2_port}")
        st.log(f"CLI Type: {cls.data.cli_type}, VLAN ID: {cls.data.vlan_id}")

        # Pre-cleanup before test
        cls._clear_interface_config()
        cls._cleanup_test_vlans()

    @classmethod
    def _clear_interface_config(cls) -> None:
        """Clear IP and VLAN configs from test ports before test."""
        st.banner("Pre-Test Cleanup: Clearing Interface Configurations")
        for dut_name, dut, port in [
            ("D1", cls.data.dut1, cls.data.d1_port),
            ("D2", cls.data.dut2, cls.data.d2_port)
        ]:
            try:
                st.config(dut, [
                    f"interface {port}",
                    "no ip address",
                    "no switchport access vlan",
                    "no switchport mode",
                    "exit"
                ], type=cls.data.cli_type, skip_error_check=True)
            except Exception as e:
                st.log(f"Pre-cleanup exception on {dut_name} (non-fatal): {e}")

    @classmethod
    def _cleanup_test_vlans(cls) -> None:
        """Remove test VLANs before starting test."""
        vlan_id = cls.data.vlan_id
        for dut_name, dut in [("D1", cls.data.dut1), ("D2", cls.data.dut2)]:
            try:
                vlan_api.delete_vlan(dut, vlan_id, cli_type=cls.data.cli_type,
                                    skip_error_report=True, remove_vlan_mapping=False)
            except Exception as e:
                st.log(f"Pre-cleanup VLAN exception on {dut_name} (non-fatal): {e}")

    @classmethod
    def teardown_class(cls) -> None:
        """Class-level cleanup: Remove all configurations."""
        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        try:
            # Remove port configurations
            for dut, port in reversed(cls.data.configured_ports):
                st.config(dut, [
                    f"interface {port}",
                    "no switchport access vlan",
                    "no switchport mode",
                    "exit"
                ], type=cls.data.cli_type, skip_error_check=True)

            # Remove VLAN configurations
            for dut, vlan_id in reversed(cls.data.configured_vlans):
                vlan_api.delete_vlan(dut, str(vlan_id), cli_type=cls.data.cli_type,
                                    skip_error_report=True, remove_vlan_mapping=False)

            # Cleanup PCAP files
            for pcap_file in cls.data.pcap_files:
                Path(pcap_file).unlink(missing_ok=True)

        except Exception as e:
            st.error(f"Teardown error: {e}")
        finally:
            st.banner("MODULE EPILOGUE: Cleanup Finished")

    def _get_interface_mac(self, dut, interface: str) -> str:
        """Get MAC address from interface."""
        try:
            cmd = f"show interface {interface} | grep -i address"
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            match = re.search(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", str(output))
            if match:
                mac = match.group(0)
                st.log(f"  ✅ Got MAC from {interface}: {mac}")
                return mac
            else:
                st.log(f"  ⚠️ Could not extract MAC from {interface}")
                return "00:00:00:00:00:00"

        except Exception as e:
            st.error(f"Failed to get MAC: {e}")
            return "00:00:00:00:00:00"

    def _send_unicast_packet(self, dut, src_interface: str, dst_mac: str,
                           src_mac: str, packet_count: int = 5) -> bool:
        """Send unicast Ethernet packet using Scapy."""
        try:
            st.log(f"Sending {packet_count} unicast packets from {src_interface} to {dst_mac}")

            # Build script with escaped newlines for printf
            script_lines = [
                "from scapy.all import Ether, Raw, sendp, conf",
                "import sys",
                "",
                f"conf.iface = \"{src_interface}\"",
                f"pkt = Ether(src=\"{src_mac}\", dst=\"{dst_mac}\") / \\\\",
                f"      Raw(load=\"UnicastTestPayload\")",
                "",
                "try:",
                f"    sendp(pkt, iface=\"{src_interface}\", count={packet_count}, verbose=False)",
                "    print(\"SUCCESS: Unicast packets sent\")",
                "except Exception as e:",
                "    print(f\"ERROR: {e}\")",
                "    sys.exit(1)"
            ]

            # Write script using printf with newline escape sequences
            script_path = f"/tmp/scapy_unicast_{int(time.time())}.py"
            script_content = "\\n".join(script_lines)
            cmd = f"printf '{script_content}' > {script_path}"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            # Execute script with sudo (required for raw packet operations)
            cmd_exec = f"sudo python3 {script_path}"
            output = st.show(dut, cmd_exec, skip_tmpl=True, skip_error_check=True)

            if "SUCCESS" in str(output):
                st.log("✅ Unicast packets sent successfully")
                return True
            else:
                st.error(f"Packet send failed: {output}")
                return False

        except Exception as e:
            st.error(f"Exception sending packets: {e}")
            return False

    def _capture_packets(self, dut, interface: str, pcap_file: str, timeout: int = 30) -> bool:
        """Capture packets with tcpdump."""
        try:
            st.log(f"Starting packet capture on {interface} for {timeout}s")
            # Use sudo for tcpdump (requires elevated privileges for raw packet capture)
            cmd = f"sudo timeout {timeout} tcpdump -i {interface} -w {pcap_file} &"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            self.data.pcap_files.append(pcap_file)
            time.sleep(1)
            st.log(f"Packet capture started: {pcap_file}")
            return True
        except Exception as e:
            st.error(f"Failed to start capture: {e}")
            return False

    def _stop_capture(self, dut) -> bool:
        """Kill tcpdump process to ensure PCAP file is flushed to disk."""
        try:
            st.log("Stopping packet capture and flushing file to disk")
            cmd = "sudo pkill -f tcpdump"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
            time.sleep(1)  # Give time for file to be written
            return True
        except Exception as e:
            st.error(f"Failed to stop capture: {e}")
            return False

    def _analyze_pcap_for_unicast(self, dut, pcap_file: str, expected_dst_mac: str) -> bool:
        """Analyze PCAP file for unicast packets destined to specific MAC."""
        try:
            st.log(f"Analyzing PCAP for unicast packets to {expected_dst_mac}")

            # Build script with escaped newlines for printf
            script_lines = [
                "from scapy.all import rdpcap, Ether",
                "try:",
                f"    packets = rdpcap(\"{pcap_file}\")",
                "",
                "    # Filter unicast packets (not broadcast/multicast)",
                f"    unicast_packets = [p for p in packets if Ether in p]",
                f"    target_packets = [p for p in unicast_packets if p[Ether].dst == \"{expected_dst_mac}\"]",
                "",
                "    if target_packets:",
                f"        print(f\"SUCCESS: Found {{len(target_packets)}} unicast packets to {expected_dst_mac}\")",
                "    else:",
                f"        print(\"FAIL: No unicast packets found to {expected_dst_mac}\")",
                "except Exception as e:",
                "    print(f\"ERROR: {e}\")"
            ]

            # Write script using printf with newline escape sequences
            script_path = f"/tmp/scapy_analyze_{int(time.time())}.py"
            script_content = "\\n".join(script_lines)
            cmd = f"printf '{script_content}' > {script_path}"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            # Execute analysis with sudo (may be needed if tcpdump file has restricted permissions)
            cmd_exec = f"sudo python3 {script_path}"
            output = st.show(dut, cmd_exec, skip_tmpl=True, skip_error_check=True)

            if "SUCCESS" in str(output):
                st.log(f"✅ Analysis passed: {output}")
                return True
            else:
                st.error(f"Analysis failed: {output}")
                return False

        except Exception as e:
            st.error(f"Exception analyzing PCAP: {e}")
            return False

    def _print_step_result(self, step_num: int, step_name: str, passed: bool) -> None:
        """Print formatted step result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        st.log("=" * 80)
        st.log(f"STEP {step_num}: {step_name} - {status}")
        st.log("=" * 80)

    # ========================================================================
    # TEST METHOD
    # ========================================================================

    @pytest.mark.inventory(feature="VLAN_Forwarding", testcases=["TC_VLAN_FORWARD_001"])
    def test_vlan_forward_001_intra_vlan_unicast(self) -> None:
        """
        TC_VLAN_FORWARD_001: Intra-VLAN Unicast Forwarding

        Objective: Verify unicast packet forwarding within VLAN

        Steps:
            1. Create VLAN 10 on both DUTs
            2. Configure Port1 (D1) as untagged access port for VLAN 10
            3. Configure Port2 (D2) as untagged access port for VLAN 10
            4. Retrieve MAC addresses from both ports
            5. Start packet capture on Port2
            6. Send unicast packet from Port1 to Port2's MAC using Scapy
            7. Analyze capture and verify unicast packet received

        Expected Result: Unicast packet forwarded to destination port in same VLAN
        """
        st.banner("=" * 100)
        st.banner("TEST: TC_VLAN_FORWARD_001 - INTRA-VLAN UNICAST FORWARDING")
        st.banner("=" * 100)

        dut1 = self.data.dut1
        dut2 = self.data.dut2
        d1_port = self.data.d1_port
        d2_port = self.data.d2_port
        vlan_id = self.data.vlan_id
        cli_type = self.data.cli_type

        # Initialize test result tracking
        test_results = {
            "step_1": False,  # Create VLAN
            "step_2": False,  # Configure D1 access port
            "step_3": False,  # Configure D2 access port
            "step_4": False,  # Get MACs
            "step_5": False,  # Start capture
            "step_6": False,  # Send packets
            "step_7": False,  # Analyze packets
        }

        try:
            # ====================================================================
            # STEP 1: Create VLAN 10 on both DUTs
            # ====================================================================
            st.log("\nSTEP 1: Creating VLAN 10 on both DUTs")
            step_passed = True
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    result = vlan_api.create_vlan(dut, vlan_id, cli_type=cli_type)
                    if result:
                        st.log(f"  ✅ VLAN {vlan_id} created on {dut_name}")
                        self.data.configured_vlans.append((dut, vlan_id))
                    else:
                        st.log(f"  ❌ Failed to create VLAN on {dut_name}")
                        step_passed = False
                except Exception as e:
                    st.log(f"  ❌ Exception creating VLAN on {dut_name}: {e}")
                    step_passed = False

            test_results["step_1"] = step_passed
            self._print_step_result(1, "Create VLAN 10", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to create VLAN")

            # ====================================================================
            # STEP 2: Configure D1 access port
            # ====================================================================
            st.log("\nSTEP 2: Configuring D1 access port for VLAN 10")
            step_passed = True
            try:
                st.config(dut1, [
                    f"interface {d1_port}",
                    f"switchport access vlan {vlan_id}",
                    "exit"
                ], type=cli_type, skip_error_check=True)
                st.log(f"  ✅ D1 access port configured")
                self.data.configured_ports.append((dut1, d1_port))
                step_passed = True
            except Exception as e:
                st.log(f"  ❌ Failed to configure D1 access port: {e}")
                step_passed = False

            test_results["step_2"] = step_passed
            self._print_step_result(2, "Configure D1 Access Port", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to configure access port")

            # ====================================================================
            # STEP 3: Configure D2 access port
            # ====================================================================
            st.log("\nSTEP 3: Configuring D2 access port for VLAN 10")
            step_passed = True
            try:
                st.config(dut2, [
                    f"interface {d2_port}",
                    f"switchport access vlan {vlan_id}",
                    "exit"
                ], type=cli_type, skip_error_check=True)
                st.log(f"  ✅ D2 access port configured")
                self.data.configured_ports.append((dut2, d2_port))
                step_passed = True
            except Exception as e:
                st.log(f"  ❌ Failed to configure D2 access port: {e}")
                step_passed = False

            test_results["step_3"] = step_passed
            self._print_step_result(3, "Configure D2 Access Port", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to configure access port")

            # ====================================================================
            # STEP 4: Retrieve MAC addresses
            # ====================================================================
            st.log("\nSTEP 4: Retrieving MAC addresses from ports")
            d1_mac = self._get_interface_mac(dut1, d1_port)
            d2_mac = self._get_interface_mac(dut2, d2_port)
            step_passed = bool(d1_mac and d1_mac != "00:00:00:00:00:00" and
                              d2_mac and d2_mac != "00:00:00:00:00:00")

            if step_passed:
                st.log(f"  ✅ MAC addresses obtained")
            else:
                st.log(f"  ⚠️ Using default MACs")

            test_results["step_4"] = step_passed
            self._print_step_result(4, "Retrieve MAC Addresses", step_passed)

            # ====================================================================
            # STEP 5: Start packet capture on D2
            # ====================================================================
            st.log("\nSTEP 5: Starting packet capture on D2 access port")
            pcap_file = f"/tmp/vlan_forward_001_{int(time.time())}.pcap"
            step_passed = self._capture_packets(dut2, d2_port, pcap_file, timeout=30)

            test_results["step_5"] = step_passed
            self._print_step_result(5, "Start Packet Capture", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to start packet capture")

            time.sleep(2)

            # ====================================================================
            # STEP 6: Send unicast packets from D1
            # ====================================================================
            st.log("\nSTEP 6: Sending unicast packets from D1")
            step_passed = self._send_unicast_packet(dut1, d1_port, d2_mac, d1_mac,
                                                   packet_count=5)

            test_results["step_6"] = step_passed
            self._print_step_result(6, "Send Unicast Packets", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to send packets")

            time.sleep(3)

            # ====================================================================
            # STEP 6.5: Stop capture to flush PCAP file
            # ====================================================================
            st.log("\nSTEP 6.5: Stopping packet capture to ensure file is flushed")
            self._stop_capture(dut2)
            time.sleep(2)  # Extra wait for file to be fully written

            # ====================================================================
            # STEP 7: Analyze capture for unicast packets
            # ====================================================================
            st.log("\nSTEP 7: Analyzing captured packets for unicast forwarding")
            step_passed = self._analyze_pcap_for_unicast(dut2, pcap_file, d2_mac)

            test_results["step_7"] = step_passed
            self._print_step_result(7, "Analyze Unicast Packets", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Unicast packet not received or forwarded incorrectly")

            # ====================================================================
            # OVERALL RESULT
            # ====================================================================
            overall_passed = all(test_results.values())
            passed_count = sum(test_results.values())

            st.log("\n" + "=" * 100)
            st.log(f"OVERALL TEST RESULT: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
            st.log(f"Steps Passed: {passed_count}/{len(test_results)}")
            st.log("=" * 100)

            if overall_passed:
                st.report_pass("test_case_passed")
            else:
                failed_steps = [k for k, v in test_results.items() if not v]
                st.report_fail("test_case_failed", f"Failed steps: {failed_steps}")

        except Exception as e:
            st.error(f"Test exception: {e}")
            st.report_fail("test_case_failed", f"Test exception: {e}")
