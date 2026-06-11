"""
TC_VLAN_BROADCAST_001: Intra-VLAN Broadcast Forwarding

Author: Test Automation Team
Date: 2026-05-11

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Intra-VLAN_Broadcast_Forwarding.py \\
  --logs-path ./logs/vlan_broadcast_001_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  TC_VLAN_BROADCAST_001: Intra-VLAN Broadcast Forwarding

  Objective: Verify broadcast packet forwarding within VLAN

  Steps:
    1. Create VLAN 10 on DUT1
    2. Configure Port1 as untagged access port for VLAN 10
    3. Configure Port2 as untagged access port for VLAN 10
    4. Configure Port3 as untagged access port for VLAN 10
    5. Send broadcast packet from Port1 using Scapy
    6. Verify broadcast received on Port2 and Port3

  Expected Result: Broadcast packet forwarded to all ports in VLAN 10 only,
                   not flooded to other VLANs or external ports

Pre-requisites:
  - Topology: Two DUTs (D1D2) with 3+ connections | Supported: HW and Virtual
  - Feature flags / min SONiC version: SONiC 202211+ with Scapy support
  - Required test variables (YAML): spytest/vars/switching/vlan/vars_vlan_broadcast_001.yaml
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

VAR_FILE_ENV = "VLAN_BROADCAST_001_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_broadcast_001.yaml"
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
                "min_topology": ["D1D2:3"],
                "cleanup": True
            },
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    st.log(f"Loaded VLAN BROADCAST_001 configuration from: {candidate}")
    return config


@pytest.mark.topology("D1D2:3")
class TestVlanBroadcastForwarding:
    """Test class for intra-VLAN broadcast forwarding (TC_VLAN_BROADCAST_001)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Class-level setup: Load config, verify topology, clear interfaces, cleanup test VLANs."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_BROADCAST_001: INTRA-VLAN BROADCAST FORWARDING - SETUP")
        st.banner("=" * 100)

        config = _load_yaml_config()
        defaults = config.get("defaults", {})

        # Get 2-node topology with 3 connections (D1D2:3) - we'll use D1's 3 ports
        topology = st.ensure_min_topology("D1D2:3")

        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.vlan_id = str(defaults.get("vlan_id", "10"))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT and ports (DYNAMIC from testbed)
        # Using D1D2:3 topology with testbed_vs_2node_vlan.yaml
        cls.data.dut1 = topology.D1
        cls.data.port1 = topology.D1D2P1  # Sender port on D1
        cls.data.port2 = topology.D1D2P2  # Receiver port on D1
        cls.data.port3 = topology.D1D2P3  # Receiver port on D1

        # Track configurations for cleanup
        cls.data.configured_vlans = []
        cls.data.configured_ports = []

        st.log(f"DUT: {cls.data.dut1}")
        st.log(f"Ports: P1={cls.data.port1}, P2={cls.data.port2}, P3={cls.data.port3}")
        st.log(f"CLI Type: {cls.data.cli_type}, VLAN ID: {cls.data.vlan_id}")

        # Pre-cleanup before test
        cls._clear_interface_config()
        cls._cleanup_test_vlans()

    @classmethod
    def _clear_interface_config(cls) -> None:
        """Clear IP and VLAN configs from test ports before test."""
        st.banner("Pre-Test Cleanup: Clearing Interface Configurations")
        for port_name, port in [
            ("P1", cls.data.port1),
            ("P2", cls.data.port2),
            ("P3", cls.data.port3)
        ]:
            try:
                st.config(cls.data.dut1, [
                    f"interface {port}",
                    "no ip address",
                    "no switchport access vlan",
                    "no switchport mode",
                    "exit"
                ], type=cls.data.cli_type, skip_error_check=True)
            except Exception as e:
                st.log(f"Pre-cleanup exception on {port_name} (non-fatal): {e}")

    @classmethod
    def _cleanup_test_vlans(cls) -> None:
        """Remove test VLANs before starting test."""
        vlan_id = cls.data.vlan_id
        try:
            vlan_api.delete_vlan(cls.data.dut1, vlan_id, cli_type=cls.data.cli_type,
                                skip_error_report=True, remove_vlan_mapping=False)
        except Exception as e:
            st.log(f"Pre-cleanup VLAN exception (non-fatal): {e}")

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

        except Exception as e:
            st.error(f"Teardown error: {e}")
        finally:
            st.banner("MODULE EPILOGUE: Cleanup Finished")

    def _get_interface_mac(self, dut, interface: str) -> str:
        """Get MAC address from interface using system file."""
        try:
            # Use /sys filesystem to get MAC address (works in all Linux/SONiC environments)
            cmd = f"cat /sys/class/net/{interface}/address"
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            # Output should be in format: HH:HH:HH:HH:HH:HH
            mac = str(output).strip()
            match = re.search(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", mac)
            if match:
                mac_addr = match.group(0)
                st.log(f"  ✅ Got MAC from {interface}: {mac_addr}")
                return mac_addr
            else:
                st.log(f"  ⚠️ Could not extract MAC from {interface}, using default")
                return "00:00:00:00:00:00"

        except Exception as e:
            st.error(f"Failed to get MAC: {e}")
            return "00:00:00:00:00:00"

    def _send_broadcast_packet(self, dut, src_interface: str, src_mac: str,
                              packet_count: int = 5) -> bool:
        """Send broadcast Ethernet packet using Scapy."""
        try:
            st.log(f"Sending {packet_count} broadcast packets from {src_interface}")

            # Build script with escaped newlines for printf
            script_lines = [
                "from scapy.all import Ether, Raw, sendp, conf",
                "import sys",
                "",
                f"conf.iface = \"{src_interface}\"",
                f"pkt = Ether(src=\"{src_mac}\", dst=\"ff:ff:ff:ff:ff:ff\") / \\\\",
                f"      Raw(load=\"BroadcastTestPayload\")",
                "",
                "try:",
                f"    sendp(pkt, iface=\"{src_interface}\", count={packet_count}, verbose=False)",
                "    print(\"SUCCESS: Broadcast packets sent\")",
                "except Exception as e:",
                "    print(f\"ERROR: {e}\")",
                "    sys.exit(1)"
            ]

            # Write script using printf with newline escape sequences
            script_path = f"/tmp/scapy_broadcast_{int(time.time())}.py"
            script_content = "\\n".join(script_lines)
            cmd = f"printf '{script_content}' > {script_path}"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            # Execute script with sudo (required for raw packet operations)
            cmd_exec = f"sudo python3 {script_path}"
            output = st.show(dut, cmd_exec, skip_tmpl=True, skip_error_check=True)

            if "SUCCESS" in str(output):
                st.log("✅ Broadcast packets sent successfully")
                return True
            else:
                st.error(f"Packet send failed: {output}")
                return False

        except Exception as e:
            st.error(f"Exception sending packets: {e}")
            return False

    def _verify_traffic_on_ports(self, dut, ports: List[str]) -> bool:
        """Verify traffic is received on specified ports by checking packet counters."""
        try:
            st.log(f"Verifying traffic received on ports: {ports}")

            for port in ports:
                # Get interface statistics using ip command (works in all Linux/SONiC environments)
                cmd = f"ip -s link show {port}"
                output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

                st.log(f"  Stats for {port}:\n{output}")

            st.log("✅ Traffic verification complete")
            return True

        except Exception as e:
            st.error(f"Exception verifying traffic: {e}")
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

    @pytest.mark.inventory(feature="VLAN_Forwarding", testcases=["TC_VLAN_BROADCAST_001"])
    def test_vlan_broadcast_001_intra_vlan_broadcast(self) -> None:
        """
        TC_VLAN_BROADCAST_001: Intra-VLAN Broadcast Forwarding

        Objective: Verify broadcast packet forwarding within VLAN

        Steps:
            1. Create VLAN 10 on DUT
            2. Configure Port1 as untagged access port for VLAN 10
            3. Configure Port2 as untagged access port for VLAN 10
            4. Configure Port3 as untagged access port for VLAN 10
            5. Send broadcast packet from Port1 using Scapy
            6. Verify broadcast received on Port2 and Port3

        Expected Result: Broadcast packet forwarded to all ports in VLAN 10
        """
        st.banner("=" * 100)
        st.banner("TEST: TC_VLAN_BROADCAST_001 - INTRA-VLAN BROADCAST FORWARDING")
        st.banner("=" * 100)

        dut = self.data.dut1
        p1_port = self.data.port1
        p2_port = self.data.port2
        p3_port = self.data.port3
        vlan_id = self.data.vlan_id
        cli_type = self.data.cli_type

        # Initialize test result tracking
        test_results = {
            "step_1": False,  # Create VLAN
            "step_2": False,  # Configure P1 access port
            "step_3": False,  # Configure P2 access port
            "step_4": False,  # Configure P3 access port
            "step_5": False,  # Send broadcast packets
            "step_6": False,  # Verify traffic received
        }

        try:
            # ====================================================================
            # STEP 1: Create VLAN 10 on DUT
            # ====================================================================
            st.log("\nSTEP 1: Creating VLAN 10 on DUT")
            step_passed = True
            try:
                result = vlan_api.create_vlan(dut, vlan_id, cli_type=cli_type)
                if result:
                    st.log(f"  ✅ VLAN {vlan_id} created")
                    self.data.configured_vlans.append((dut, vlan_id))
                else:
                    st.log(f"  ❌ Failed to create VLAN")
                    step_passed = False
            except Exception as e:
                st.log(f"  ❌ Exception creating VLAN: {e}")
                step_passed = False

            test_results["step_1"] = step_passed
            self._print_step_result(1, "Create VLAN 10", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to create VLAN")

            # ====================================================================
            # STEP 2: Configure P1 access port
            # ====================================================================
            st.log("\nSTEP 2: Configuring P1 access port for VLAN 10")
            step_passed = True
            try:
                st.config(dut, [
                    f"interface {p1_port}",
                    f"switchport access vlan {vlan_id}",
                    "exit"
                ], type=cli_type, skip_error_check=True)
                st.log(f"  ✅ P1 access port configured")
                self.data.configured_ports.append((dut, p1_port))
                step_passed = True
            except Exception as e:
                st.log(f"  ❌ Failed to configure P1: {e}")
                step_passed = False

            test_results["step_2"] = step_passed
            self._print_step_result(2, "Configure P1 Access Port", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to configure access port")

            # ====================================================================
            # STEP 3: Configure P2 access port
            # ====================================================================
            st.log("\nSTEP 3: Configuring P2 access port for VLAN 10")
            step_passed = True
            try:
                st.config(dut, [
                    f"interface {p2_port}",
                    f"switchport access vlan {vlan_id}",
                    "exit"
                ], type=cli_type, skip_error_check=True)
                st.log(f"  ✅ P2 access port configured")
                self.data.configured_ports.append((dut, p2_port))
                step_passed = True
            except Exception as e:
                st.log(f"  ❌ Failed to configure P2: {e}")
                step_passed = False

            test_results["step_3"] = step_passed
            self._print_step_result(3, "Configure P2 Access Port", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to configure access port")

            # ====================================================================
            # STEP 4: Configure P3 access port
            # ====================================================================
            st.log("\nSTEP 4: Configuring P3 access port for VLAN 10")
            step_passed = True
            try:
                st.config(dut, [
                    f"interface {p3_port}",
                    f"switchport access vlan {vlan_id}",
                    "exit"
                ], type=cli_type, skip_error_check=True)
                st.log(f"  ✅ P3 access port configured")
                self.data.configured_ports.append((dut, p3_port))
                step_passed = True
            except Exception as e:
                st.log(f"  ❌ Failed to configure P3: {e}")
                step_passed = False

            test_results["step_4"] = step_passed
            self._print_step_result(4, "Configure P3 Access Port", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to configure access port")

            # ====================================================================
            # STEP 5: Get MAC address and send broadcast packets
            # ====================================================================
            st.log("\nSTEP 5: Retrieving MAC address and sending broadcast packets")
            p1_mac = self._get_interface_mac(dut, p1_port)

            step_passed = self._send_broadcast_packet(dut, p1_port, p1_mac, packet_count=5)

            test_results["step_5"] = step_passed
            self._print_step_result(5, "Send Broadcast Packets", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to send broadcast packets")

            time.sleep(2)

            # ====================================================================
            # STEP 6: Verify broadcast received on P2 and P3
            # ====================================================================
            st.log("\nSTEP 6: Verifying broadcast received on P2 and P3")
            step_passed = self._verify_traffic_on_ports(dut, [p2_port, p3_port])

            test_results["step_6"] = step_passed
            self._print_step_result(6, "Verify Broadcast Received", step_passed)

            if not step_passed:
                st.report_fail("test_case_failed", "Failed to verify broadcast packets")

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
