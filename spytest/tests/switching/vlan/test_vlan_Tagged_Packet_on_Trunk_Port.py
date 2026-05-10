"""
TC_VLAN_TAG_003: Tagged Packet on Trunk Port - Full Trunk-to-Trunk Forwarding

Author: Test Automation Team
Date: 2026-05-11

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
    Step 1: Create VLAN 10 on both DUTs
    Step 2: Configure Port on D1 as trunk port for VLAN 10
    Step 3: Configure Port on D2 as trunk port for VLAN 10
    Step 4: Start packet capture on D2 trunk port
    Step 5: Send VLAN 10 tagged packet from D1 trunk port using Scapy
    Step 6: Analyze capture and verify packet retains VLAN 10 tag
    Step 7: Cleanup all configurations

Pre-requisites:
  - Topology: Two DUTs (D1-D2) with 2+ back-to-back connections
  - Supported: HW and Virtual SONiC environments
  - Scapy installed on DUTs
  - tcpdump available for packet capture
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

VAR_FILE_ENV = "VLAN_TAG_003_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_tag_003.yaml"
)

TC_VLAN_TAG_003 = "TC_VLAN_TAG_003"


def _load_yaml_config() -> Dict[str, Any]:
    """Load test configuration from YAML with environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    yaml_file = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not yaml_file.is_file():
        st.warn(f"VLAN TAG-003 config not found at {yaml_file}, using defaults")
        return {
            "defaults": {
                "cli_type": "klish",
                "vlan_id": "10",
                "min_topology": ["D1D2:2"],
                "cleanup": True
            },
            "testcases": {
                TC_VLAN_TAG_003: {}
            }
        }

    with yaml_file.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ============================================================================
# TEST CLASS
# ============================================================================

@pytest.mark.topology("D1D2:2")
class TestVlanTaggedPacketOnTrunkPort:
    """Test trunk-to-trunk tagged VLAN packet forwarding (TC_VLAN_TAG_003)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Class-level setup: Load config and initialize topology."""
        st.banner("MODULE PROLOGUE: TC_VLAN_TAG_003 - Trunk Port Tagged Forwarding")

        # Load configuration
        config = _load_yaml_config()
        defaults = config.get("defaults", {})

        # Get topology
        min_topology = defaults.get("min_topology", ["D1D2:2"])
        topology = st.ensure_min_topology(*min_topology)

        # Store configuration
        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))

        # Get DUT handles
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.d1_port = topology.D1D2P1  # Dynamic port from testbed
        cls.data.d2_port = topology.D2D1P1  # Dynamic port from testbed

        # Configuration parameters
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.vlan_id = str(defaults.get("vlan_id", "10"))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Track configurations for cleanup
        cls.data.configured_ports = []
        cls.data.configured_vlans = []
        cls.data.pcap_files = []

        st.log(f"DUT1: {cls.data.dut1} | Port: {cls.data.d1_port}")
        st.log(f"DUT2: {cls.data.dut2} | Port: {cls.data.d2_port}")
        st.log(f"VLAN ID: {cls.data.vlan_id} | CLI Type: {cls.data.cli_type}")

        # Pre-cleanup: Clear configurations
        cls._clear_interface_config()
        cls._cleanup_test_vlans()

        st.banner("MODULE PROLOGUE: Setup Complete")

    @classmethod
    def _clear_interface_config(cls) -> None:
        """Clear IP and VLAN configs from test ports before test."""
        st.banner("Pre-Test Cleanup: Clearing Interface Configurations")
        for dut_name, dut, port in [
            ("D1", cls.data.dut1, cls.data.d1_port),
            ("D2", cls.data.dut2, cls.data.d2_port)
        ]:
            try:
                st.log(f"Clearing configs on {dut_name}:{port}")
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
                st.log(f"Pre-cleanup: VLAN {vlan_id} removed from {dut_name} (if existed)")
            except Exception as e:
                st.log(f"Pre-cleanup VLAN exception on {dut_name} (non-fatal): {e}")

    @classmethod
    def teardown_class(cls) -> None:
        """Class-level cleanup: Remove all configurations."""
        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        st.banner("MODULE EPILOGUE: TC_VLAN_TAG_003 Cleanup")

        try:
            # Remove port configurations
            for dut, port in reversed(cls.data.configured_ports):
                try:
                    st.log(f"Removing port config: {port}")
                    st.config(dut, [
                        f"interface {port}",
                        "no switchport access vlan",
                        "no switchport trunk allowed vlan",
                        "no switchport mode",
                        "exit"
                    ], type=cls.data.cli_type, skip_error_check=True)
                except Exception as e:
                    st.warn(f"Port cleanup exception: {e}")

            # Remove VLAN configurations
            for dut, vlan_id in reversed(cls.data.configured_vlans):
                try:
                    vlan_api.delete_vlan(dut, str(vlan_id), cli_type=cls.data.cli_type,
                                       skip_error_report=True, remove_vlan_mapping=False)
                    st.log(f"VLAN {vlan_id} removed")
                except Exception as e:
                    st.warn(f"VLAN cleanup exception: {e}")

            # Cleanup PCAP files
            for pcap_file in cls.data.pcap_files:
                try:
                    Path(pcap_file).unlink(missing_ok=True)
                    st.log(f"Cleaned up: {pcap_file}")
                except Exception as e:
                    st.log(f"PCAP cleanup exception: {e}")

            st.log("✅ Teardown cleanup completed successfully")

        except Exception as e:
            st.error(f"Teardown error: {e}")
        finally:
            st.banner("MODULE EPILOGUE: Cleanup Finished")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _print_step_result(self, step_num: int, step_name: str, passed: bool) -> None:
        """Print formatted step result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        st.log("")
        st.log("=" * 80)
        st.log(f"STEP {step_num}: {step_name} - {status}")
        st.log("=" * 80)

    def _get_interface_mac(self, dut, interface: str) -> str:
        """Get MAC address of an interface."""
        try:
            output = st.show(dut, f"show interface {interface} | grep -i 'address'",
                           skip_tmpl=True, skip_error_check=True)
            output_str = str(output).lower()

            # Extract MAC from output
            import re
            match = re.search(r'([0-9a-f]{2}[:-]){5}([0-9a-f]{2})', output_str)
            if match:
                mac = match.group(0)
                st.log(f"Interface {interface} MAC: {mac}")
                return mac

            st.warn(f"Could not extract MAC from {interface}")
            return "00:00:00:00:00:00"
        except Exception as e:
            st.error(f"Failed to get MAC: {e}")
            return "00:00:00:00:00:00"

    def _send_tagged_packet(self, dut, src_interface: str, dst_mac: str,
                          src_mac: str, vlan_id: int, packet_count: int = 5) -> bool:
        """Send VLAN-tagged packet using Scapy."""
        try:
            st.log(f"Sending {packet_count} tagged packets (VLAN {vlan_id}) from {src_interface}")

            # Create Scapy script using printf to avoid st.config() adding unwanted prefixes
            script_path = f"/tmp/scapy_send_tag_{int(time.time())}.py"

            # Build script with escaped newlines for printf
            script_lines = [
                "from scapy.all import Ether, Dot1Q, IP, ICMP, sendp, conf",
                "import sys",
                "",
                f"conf.iface = \"{src_interface}\"",
                f"pkt = Ether(src=\"{src_mac}\", dst=\"{dst_mac}\") / \\\\",
                f"      Dot1Q(vlan={vlan_id}) / \\\\",
                "      IP(src=\"10.1.1.1\", dst=\"10.1.1.2\") / \\\\",
                "      ICMP()",
                "",
                "try:",
                f"    sendp(pkt, iface=\"{src_interface}\", count={packet_count}, verbose=False)",
                "    print(\"SUCCESS: Tagged packets sent\")",
                "except Exception as e:",
                "    print(f\"ERROR: {e}\")",
                "    sys.exit(1)"
            ]

            # Write script using printf with newline escape sequences
            script_content = "\\n".join(script_lines)
            cmd = f"printf '{script_content}' > {script_path}"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            # Execute script with sudo (required for raw packet operations)
            cmd_exec = f"sudo python3 {script_path}"
            output = st.show(dut, cmd_exec, skip_tmpl=True, skip_error_check=True)

            if "SUCCESS" in str(output):
                st.log("✅ Tagged packets sent successfully")
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

    def _analyze_pcap_for_tagged(self, dut, pcap_file: str, vlan_id: int) -> bool:
        """Analyze PCAP file for VLAN-tagged packets."""
        try:
            st.log(f"Analyzing PCAP for VLAN {vlan_id} tags")

            # Create analysis script using printf to avoid st.config() adding unwanted prefixes
            script_path = f"/tmp/scapy_analyze_{int(time.time())}.py"

            # Build script with escaped newlines for printf
            script_lines = [
                "from scapy.all import rdpcap, Dot1Q",
                "try:",
                f"    packets = rdpcap(\"{pcap_file}\")",
                "",
                f"    # Check for VLAN {vlan_id} tags",
                "    vlan_packets = [p for p in packets if Dot1Q in p]",
                f"    vlan_{vlan_id}_packets = [p for p in vlan_packets if p[Dot1Q].vlan == {vlan_id}]",
                "",
                f"    if vlan_{vlan_id}_packets:",
                f"        print(f\"SUCCESS: Found {{len(vlan_{vlan_id}_packets)}} VLAN {vlan_id} tagged packets\")",
                f"    else:",
                f"        print(\"FAIL: No VLAN {vlan_id} tagged packets found\")",
                "except Exception as e:",
                "    print(f\"ERROR: {e}\")"
            ]

            # Write script using printf with newline escape sequences
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

    # ========================================================================
    # TEST METHOD
    # ========================================================================

    def test_vlan_tag_003_trunk_tagged_forwarding(self) -> None:
        """
        TC_VLAN_TAG_003: Verify tagged packets remain tagged on trunk-to-trunk forwarding.

        This test validates IEEE 802.1Q trunk port behavior:
        - Trunk ports should PRESERVE VLAN tags when forwarding
        - No tag stripping occurs on trunk-to-trunk forwarding
        """

        st.banner(f"TEST: {TC_VLAN_TAG_003} - Trunk Port Tagged Packet Forwarding")

        # Initialize test result tracking
        test_results = {
            "step_1": False,
            "step_2": False,
            "step_3": False,
            "step_4": False,
            "step_5": False,
            "step_6": False,
            "step_7": False,
        }

        dut1 = self.data.dut1
        dut2 = self.data.dut2
        d1_port = self.data.d1_port
        d2_port = self.data.d2_port
        vlan_id = self.data.vlan_id
        cli_type = self.data.cli_type

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
            # STEP 2: Configure D1 trunk port
            # ====================================================================
            st.log("\nSTEP 2: Configuring D1 trunk port for VLAN 10")
            step_passed = True
            try:
                st.config(dut1, [
                    f"interface {d1_port}",
                    f"switchport trunk allowed vlan {vlan_id}",
                    "exit"
                ], type=cli_type, skip_error_check=True)
                st.log(f"  ✅ D1 trunk port configured")
                self.data.configured_ports.append((dut1, d1_port))
                step_passed = True
            except Exception as e:
                st.log(f"  ❌ Failed to configure D1 trunk port: {e}")
                step_passed = False

            test_results["step_2"] = step_passed
            self._print_step_result(2, "Configure D1 Trunk Port", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to configure trunk port")

            # ====================================================================
            # STEP 3: Configure D2 trunk port
            # ====================================================================
            st.log("\nSTEP 3: Configuring D2 trunk port for VLAN 10")
            step_passed = True
            try:
                st.config(dut2, [
                    f"interface {d2_port}",
                    f"switchport trunk allowed vlan {vlan_id}",
                    "exit"
                ], type=cli_type, skip_error_check=True)
                st.log(f"  ✅ D2 trunk port configured")
                self.data.configured_ports.append((dut2, d2_port))
                step_passed = True
            except Exception as e:
                st.log(f"  ❌ Failed to configure D2 trunk port: {e}")
                step_passed = False

            test_results["step_3"] = step_passed
            self._print_step_result(3, "Configure D2 Trunk Port", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to configure trunk port")

            # ====================================================================
            # STEP 4: Get MAC addresses
            # ====================================================================
            st.log("\nSTEP 4: Retrieving MAC addresses")
            step_passed = True
            try:
                d1_mac = self._get_interface_mac(dut1, d1_port)
                d2_mac = self._get_interface_mac(dut2, d2_port)

                if d1_mac and d2_mac:
                    st.log(f"  ✅ MAC addresses obtained")
                    step_passed = True
                else:
                    st.log(f"  ❌ Failed to get MAC addresses")
                    step_passed = False
            except Exception as e:
                st.log(f"  ❌ Exception: {e}")
                step_passed = False

            test_results["step_4"] = step_passed
            self._print_step_result(4, "Retrieve MAC Addresses", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to get MAC addresses")

            # ====================================================================
            # STEP 5: Start packet capture on D2
            # ====================================================================
            st.log("\nSTEP 5: Starting packet capture on D2 trunk port")
            pcap_file = f"/tmp/vlan_tag_003_{int(time.time())}.pcap"
            step_passed = self._capture_packets(dut2, d2_port, pcap_file, timeout=30)

            test_results["step_5"] = step_passed
            self._print_step_result(5, "Start Packet Capture", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to start packet capture")

            time.sleep(2)

            # ====================================================================
            # STEP 6: Send VLAN-tagged packets from D1
            # ====================================================================
            st.log("\nSTEP 6: Sending VLAN-tagged packets from D1")
            step_passed = self._send_tagged_packet(dut1, d1_port, d2_mac, d1_mac,
                                                  int(vlan_id), packet_count=5)

            test_results["step_6"] = step_passed
            self._print_step_result(6, "Send Tagged Packets", step_passed)

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
            # STEP 7: Analyze capture for tagged packets
            # ====================================================================
            st.log("\nSTEP 7: Analyzing captured packets for VLAN tags")
            step_passed = self._analyze_pcap_for_tagged(dut2, pcap_file, int(vlan_id))

            test_results["step_7"] = step_passed
            self._print_step_result(7, "Analyze Tagged Packets", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Tagged packets not received with tag")

            # ====================================================================
            # OVERALL RESULT
            # ====================================================================
            overall_passed = all(test_results.values())
            passed_count = sum(test_results.values())
            total_steps = len(test_results)

            st.log("")
            st.log("=" * 80)
            st.log(f"OVERALL TEST RESULT: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
            st.log(f"Steps Passed: {passed_count}/{total_steps}")
            st.log("=" * 80)

            if overall_passed:
                st.report_pass("test_case_passed")
            else:
                failed_steps = [k for k, v in test_results.items() if not v]
                st.report_fail("test_case_failed", f"Failed steps: {failed_steps}")

        except Exception as e:
            st.error(f"Test exception: {e}")
            st.report_fail("test_case_failed", f"Test exception: {e}")
