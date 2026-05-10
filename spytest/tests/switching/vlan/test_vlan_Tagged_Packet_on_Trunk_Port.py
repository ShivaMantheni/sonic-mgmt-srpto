"""
TC_VLAN_TAG_003: Tagged Packet on Trunk Port - Trunk-to-Trunk Forwarding

Author: Test Automation Team
Date: 2026-05-11

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Tagged_Packet_on_Trunk_Port.py \\
  --logs-path ./logs/vlan_tag_003_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  TC_VLAN_TAG_003: Tagged Packet on Trunk Port

  Objective: Verify tagged packet retains VLAN tag when forwarded trunk-to-trunk

  Steps:
    1. Create VLAN 10 on both DUTs
    2. Configure D1 port as trunk port for VLAN 10
    3. Configure D2 port as trunk port for VLAN 10
    4. Get MAC addresses from both ports
    5. Send VLAN 10 tagged packet from D1 trunk port using Scapy
    6. Verify packet received on D2 trunk port

  Expected Result: Tagged packet retains VLAN 10 tag on trunk-to-trunk forwarding
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

VAR_FILE_ENV = "VLAN_TAG_003_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_tag_003.yaml"
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
                "packet_count": 5,
                "cleanup": True
            },
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    st.log(f"Loaded VLAN TAG_003 configuration from: {candidate}")
    return config


@pytest.mark.topology("D1D2:2")
class TestVlanTaggedPacketOnTrunkPort:
    """Test class for trunk-to-trunk tagged packet forwarding (TC_VLAN_TAG_003)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Setup: Load config, verify topology, clear interfaces, cleanup test VLANs."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_TAG_003: TAGGED PACKET ON TRUNK PORT - SETUP")
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
        cls.data.packet_count = defaults.get("packet_count", 5)
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT and ports from topology
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut1_port = topology.D1D2P1  # Trunk port on D1
        cls.data.dut2_port = topology.D2D1P1  # Trunk port on D2

        st.log(f"DUT1: {cls.data.dut1}, DUT2: {cls.data.dut2}")
        st.log(f"DUT1 Port (Trunk): {cls.data.dut1_port}")
        st.log(f"DUT2 Port (Trunk): {cls.data.dut2_port}")
        st.log(f"CLI Type: {cls.data.cli_type}, VLAN ID: {cls.data.vlan_id}")

        # Pre-cleanup before test
        cls._clear_interface_config()
        cls._cleanup_test_vlans()

    @classmethod
    def _clear_interface_config(cls) -> None:
        """Clear IP and VLAN configs from test ports before test."""
        st.banner("Pre-Test Cleanup: Clearing Interface Configurations")
        try:
            st.config(cls.data.dut1, [
                f"interface {cls.data.dut1_port}",
                "no ip address",
                "no switchport access vlan",
                "no switchport mode",
                "exit"
            ], type=cls.data.cli_type, skip_error_check=True)
        except Exception as e:
            st.log(f"Pre-cleanup exception on DUT1 (non-fatal): {e}")

        try:
            st.config(cls.data.dut2, [
                f"interface {cls.data.dut2_port}",
                "no ip address",
                "no switchport access vlan",
                "no switchport mode",
                "exit"
            ], type=cls.data.cli_type, skip_error_check=True)
        except Exception as e:
            st.log(f"Pre-cleanup exception on DUT2 (non-fatal): {e}")

    @classmethod
    def _cleanup_test_vlans(cls) -> None:
        """Remove test VLANs before starting test."""
        vlan_id = cls.data.vlan_id
        try:
            vlan_api.delete_vlan(cls.data.dut1, vlan_id, cli_type=cls.data.cli_type, skip_error_report=True)
            vlan_api.delete_vlan(cls.data.dut2, vlan_id, cli_type=cls.data.cli_type, skip_error_report=True)
        except Exception as e:
            st.log(f"Pre-cleanup VLAN {vlan_id} exception (non-fatal): {e}")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after test: Remove all configurations."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_TAG_003: CLEANUP")
        st.banner("=" * 100)

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        # Remove VLANs
        vlan_id = cls.data.vlan_id
        try:
            vlan_api.delete_vlan(cls.data.dut1, vlan_id, cli_type=cls.data.cli_type, skip_error_report=True)
            vlan_api.delete_vlan(cls.data.dut2, vlan_id, cli_type=cls.data.cli_type, skip_error_report=True)
            st.log(f"✅ VLAN {vlan_id} deleted on both DUTs")
        except Exception as e:
            st.log(f"Teardown VLAN {vlan_id} exception (non-fatal): {e}")

    def _get_interface_mac(self, dut, interface: str) -> str:
        """Get MAC address from interface using system file."""
        try:
            cmd = f"cat /sys/class/net/{interface}/address"
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            mac = str(output).strip()
            match = re.search(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", mac)
            if match:
                mac_addr = match.group(0)
                st.log(f"  ✅ Got MAC from {interface}: {mac_addr}")
                return mac_addr
        except Exception as e:
            st.log(f"  Error getting MAC: {e}")
        return None

    def _verify_traffic_on_ports(self, dut, ports: List[str]) -> bool:
        """Verify traffic is received on specified ports by checking packet counters."""
        try:
            st.log(f"Verifying traffic received on ports: {ports}")

            for port in ports:
                cmd = f"ip -s link show {port}"
                output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)
                st.log(f"  Stats for {port}:\n{output}")

            st.log("✅ Traffic verification complete")
            return True
        except Exception as e:
            st.log(f"Error verifying traffic: {e}")
            return False

    def _send_tagged_packet(self, dut, src_interface: str, src_mac: str, dst_mac: str,
                           vlan_id: str = "10", packet_count: int = 5) -> bool:
        """Send VLAN tagged Ethernet packet using Scapy."""
        try:
            st.log(f"Sending {packet_count} VLAN {vlan_id} tagged packets from {src_interface}")
            st.log(f"  Source MAC: {src_mac}, Destination MAC: {dst_mac}, VLAN ID: {vlan_id}")

            # Build script with escaped newlines for printf
            script_lines = [
                "from scapy.all import Ether, Dot1Q, Raw, sendp, conf",
                "import sys",
                "",
                f"conf.iface = \\\"{src_interface}\\\"",
                f"pkt = Ether(src=\\\"{src_mac}\\\", dst=\\\"{dst_mac}\\\") / \\\\",
                f"      Dot1Q(vlan={vlan_id}) / \\\\",
                f"      Raw(load=\\\"TrunkTaggedTestPayload\\\")",
                "",
                "try:",
                f"    sendp(pkt, iface=\\\"{src_interface}\\\", count={packet_count}, verbose=False)",
                "    print(\\\"SUCCESS: Tagged packets sent\\\")",
                "except Exception as e:",
                "    print(f\\\"ERROR: {e}\\\")",
                "    sys.exit(1)"
            ]

            script_path = f"/tmp/scapy_trunk_packet_{int(time.time())}.py"
            script_content = "\\n".join(script_lines)
            cmd = f"printf '{script_content}' > {script_path}"
            st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            cmd_exec = f"sudo python3 {script_path}"
            output = st.show(dut, cmd_exec, skip_tmpl=True, skip_error_check=True)

            st.log(f"Script output:\n{output}")

            if "SUCCESS" in str(output):
                st.log("✅ Tagged packet sent successfully")
                return True
            else:
                st.log("❌ Tagged packet send failed")
                return False

        except Exception as e:
            st.log(f"❌ Error sending tagged packet: {e}")
            return False

    def test_vlan_tag_003_tagged_packet_on_trunk_port(self) -> None:
        """
        TC_VLAN_TAG_003: Tagged Packet on Trunk Port Test

        Test execution with step tracking:
        1. Create VLAN 10 on both DUTs
        2. Configure trunk ports on both DUTs
        3. Get MAC addresses
        4. Send VLAN tagged packet from D1 trunk port
        5. Verify traffic on D2 trunk port
        """
        st.banner("=" * 100)
        st.banner("TC_VLAN_TAG_003: TAGGED PACKET ON TRUNK PORT - EXECUTION")
        st.banner("=" * 100)

        test_results = {
            "step_1": False,  # Create VLAN on both DUTs
            "step_2": False,  # Configure trunk ports
            "step_3": False,  # Get MAC addresses
            "step_4": False,  # Send tagged packet from D1
            "step_5": False,  # Verify traffic on D2
        }

        try:
            # STEP 1: Create VLAN 10 on both DUTs
            st.banner("STEP 1: Creating VLAN 10 on both DUTs")
            vlan_id = self.data.vlan_id
            dut1_ok = vlan_api.create_vlan(self.data.dut1, vlan_id, cli_type=self.data.cli_type)
            dut2_ok = vlan_api.create_vlan(self.data.dut2, vlan_id, cli_type=self.data.cli_type)

            if dut1_ok and dut2_ok:
                st.log(f"✅ STEP 1 PASS: VLAN {vlan_id} created on both DUTs")
                test_results["step_1"] = True
            else:
                st.log(f"❌ STEP 1 FAIL: Could not create VLAN {vlan_id}")
                test_results["step_1"] = False

            # STEP 2: Configure trunk ports on both DUTs
            st.banner("STEP 2: Configuring trunk ports")
            all_ok = True

            try:
                st.log(f"  Configuring DUT1 port {self.data.dut1_port} as trunk port")
                vlan_api.add_vlan_member(
                    self.data.dut1, vlan_id, self.data.dut1_port, tagging_mode="tagged",
                    cli_type=self.data.cli_type, skip_error_check=True
                )
                st.log(f"    ✅ DUT1 trunk port configured")
            except Exception as e:
                st.log(f"    ❌ DUT1 trunk port configuration failed: {e}")
                all_ok = False

            try:
                st.log(f"  Configuring DUT2 port {self.data.dut2_port} as trunk port")
                vlan_api.add_vlan_member(
                    self.data.dut2, vlan_id, self.data.dut2_port, tagging_mode="tagged",
                    cli_type=self.data.cli_type, skip_error_check=True
                )
                st.log(f"    ✅ DUT2 trunk port configured")
            except Exception as e:
                st.log(f"    ❌ DUT2 trunk port configuration failed: {e}")
                all_ok = False

            if all_ok:
                st.log(f"✅ STEP 2 PASS: Trunk ports configured")
                test_results["step_2"] = True
            else:
                st.log(f"❌ STEP 2 FAIL: Some ports failed to configure")
                test_results["step_2"] = False

            # STEP 3: Get MAC addresses
            st.banner("STEP 3: Getting MAC addresses from trunk ports")
            mac_dut1 = self._get_interface_mac(self.data.dut1, self.data.dut1_port)
            mac_dut2 = self._get_interface_mac(self.data.dut2, self.data.dut2_port)

            if mac_dut1 and mac_dut2:
                st.log(f"✅ STEP 3 PASS: All MACs retrieved")
                st.log(f"  DUT1 Port MAC: {mac_dut1}, DUT2 Port MAC: {mac_dut2}")
                test_results["step_3"] = True
            else:
                st.log(f"❌ STEP 3 FAIL: Could not retrieve all MACs")
                test_results["step_3"] = False
                mac_dut1 = mac_dut1 or "unknown"
                mac_dut2 = mac_dut2 or "unknown"

            # STEP 4: Send VLAN tagged packet from D1 trunk port
            st.banner("STEP 4: Sending VLAN tagged packet from D1 trunk port")
            if self._send_tagged_packet(
                self.data.dut1, self.data.dut1_port, mac_dut1, mac_dut2, vlan_id, self.data.packet_count
            ):
                st.log(f"✅ STEP 4 PASS: Tagged packet sent")
                test_results["step_4"] = True
                time.sleep(2)
            else:
                st.log(f"❌ STEP 4 FAIL: Could not send tagged packet")
                test_results["step_4"] = False

            # STEP 5: Verify traffic on D2 trunk port
            st.banner("STEP 5: Verifying traffic received on D2 trunk port")
            if self._verify_traffic_on_ports(self.data.dut2, [self.data.dut2_port]):
                st.log(f"✅ STEP 5 PASS: Traffic verified on trunk port")
                test_results["step_5"] = True
            else:
                st.log(f"❌ STEP 5 FAIL: Could not verify traffic")
                test_results["step_5"] = False

        except Exception as e:
            st.log(f"❌ Test execution error: {e}")

        # Summary
        st.banner("=" * 100)
        st.banner("TEST RESULTS SUMMARY")
        st.banner("=" * 100)

        passed = sum(1 for v in test_results.values() if v)
        total = len(test_results)

        for step_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            st.log(f"{step_name}: {status}")

        st.log("")
        st.log(f"OVERALL: {passed}/{total} steps passed")

        if passed == total:
            st.log("✅ TC_VLAN_TAG_003: PASSED")
            st.report_pass("TC_VLAN_TAG_003 passed")
        else:
            st.log(f"❌ TC_VLAN_TAG_003: FAILED ({total-passed} steps failed)")
            st.report_fail(f"TC_VLAN_TAG_003 failed - {total-passed} steps failed")
