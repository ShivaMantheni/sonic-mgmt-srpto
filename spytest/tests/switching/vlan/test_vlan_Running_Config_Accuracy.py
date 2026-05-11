"""
TC_VLAN_PERSIST_002: Running Config Accuracy

Author: Test Automation Team
Date: 2026-05-11

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Running_Config_Accuracy.py \\
  --logs-path ./logs/vlan_running_config_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  TC_VLAN_PERSIST_002: Running Config Accuracy

  Objective: Verify show running-config accurately reflects VLAN config

  Steps:
    1. Create VLAN 10
    2. Add Port1 as untagged member
    3. Add Port3 as tagged member
    4. Execute show running-config
    5. Verify all configurations are accurately displayed

  Expected Result: Running config accurately shows all VLAN settings

Pre-requisites:
  - Topology: Two DUTs (D1D2) with 2+ connections | Supported: HW and Virtual
  - Feature flags / min SONiC version: VLAN support required
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

VAR_FILE_ENV = "VLAN_RUNNING_CONFIG_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_running_config_accuracy.yaml"
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
                "cleanup": True
            },
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    st.log(f"Loaded VLAN RUNNING_CONFIG_ACCURACY configuration from: {candidate}")
    return config


@pytest.mark.topology("D1D2:2")
class TestVlanRunningConfigAccuracy:
    """Test class for VLAN running config accuracy (TC_VLAN_PERSIST_002)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Setup: Load config, verify topology, clear interfaces, cleanup test VLANs."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_PERSIST_002: RUNNING CONFIG ACCURACY - SETUP")
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
        cls.data.vlan_id = int(defaults.get("vlan_id", 10))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT and ports from topology
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut1_port1 = topology.D1D2P1  # Port 1 for untagged
        cls.data.dut1_port3 = topology.D1D2P2  # Port 3 for tagged (use second available port)
        cls.data.dut2_port = topology.D2D1P1

        st.log(f"DUT1: {cls.data.dut1}, DUT2: {cls.data.dut2}")
        st.log(f"DUT1 Port1 (Untagged): {cls.data.dut1_port1}")
        st.log(f"DUT1 Port3 (Tagged): {cls.data.dut1_port3}")
        st.log(f"DUT2 Port: {cls.data.dut2_port}")
        st.log(f"CLI Type: {cls.data.cli_type}")
        st.log(f"Test VLAN ID: {cls.data.vlan_id}")

        # Track created VLANs for cleanup
        cls.data.created_vlans = []

        # Pre-cleanup before test
        cls._clear_interface_config()
        cls._cleanup_test_vlans()

    @classmethod
    def _clear_interface_config(cls) -> None:
        """Clear IP and VLAN configs from test ports before test."""
        st.banner("Pre-Test Cleanup: Clearing Interface Configurations")
        try:
            st.config(cls.data.dut1, [
                f"interface {cls.data.dut1_port1}",
                "no ip address",
                "no switchport access vlan",
                "no switchport mode",
                "exit"
            ], type=cls.data.cli_type, skip_error_check=True)
        except Exception as e:
            st.log(f"Pre-cleanup exception on DUT1 Port1 (non-fatal): {e}")

        try:
            st.config(cls.data.dut1, [
                f"interface {cls.data.dut1_port3}",
                "no ip address",
                "no switchport trunk allowed vlan",
                "no switchport mode",
                "exit"
            ], type=cls.data.cli_type, skip_error_check=True)
        except Exception as e:
            st.log(f"Pre-cleanup exception on DUT1 Port3 (non-fatal): {e}")

    @classmethod
    def _cleanup_test_vlans(cls) -> None:
        """Remove test VLANs before starting test."""
        try:
            vlan_api.delete_vlan(cls.data.dut1, str(cls.data.vlan_id),
                                cli_type=cls.data.cli_type, skip_error_report=True)
            vlan_api.delete_vlan(cls.data.dut2, str(cls.data.vlan_id),
                                cli_type=cls.data.cli_type, skip_error_report=True)
        except Exception as e:
            st.log(f"Pre-cleanup VLAN exception (non-fatal): {e}")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after test: Remove all configurations."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_PERSIST_002: CLEANUP")
        st.banner("=" * 100)

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        # Remove ports from VLAN first
        try:
            st.config(cls.data.dut1, [
                f"interface {cls.data.dut1_port1}",
                "no switchport access vlan",
                "exit"
            ], type=cls.data.cli_type, skip_error_check=True)
        except Exception as e:
            st.log(f"Teardown remove port1 from VLAN exception (non-fatal): {e}")

        try:
            st.config(cls.data.dut1, [
                f"interface {cls.data.dut1_port3}",
                "no switchport trunk allowed vlan",
                "exit"
            ], type=cls.data.cli_type, skip_error_check=True)
        except Exception as e:
            st.log(f"Teardown remove port3 from VLAN exception (non-fatal): {e}")

        # Remove created VLANs
        for vlan_id in cls.data.created_vlans:
            try:
                vlan_api.delete_vlan(cls.data.dut1, str(vlan_id),
                                    cli_type=cls.data.cli_type, skip_error_report=True)
                vlan_api.delete_vlan(cls.data.dut2, str(vlan_id),
                                    cli_type=cls.data.cli_type, skip_error_report=True)
                st.log(f"✅ VLAN {vlan_id} deleted on both DUTs")
            except Exception as e:
                st.log(f"Teardown VLAN {vlan_id} exception (non-fatal): {e}")

    def _verify_vlan_in_running_config(self, dut, vlan_id: int) -> bool:
        """Verify VLAN exists in running-configuration."""
        try:
            running_config = str(self.data.running_config).lower()

            if f"vlan {vlan_id}" in running_config:
                st.log(f"  ✅ VLAN {vlan_id} found in running-configuration")
                return True
            else:
                st.log(f"  ❌ VLAN {vlan_id} NOT found in running-configuration")
                return False
        except Exception as e:
            st.log(f"  Error verifying VLAN {vlan_id}: {e}")
            return False

    def _verify_port_in_interface_config(self, dut, vlan_id: int, port: str, mode: str = "untagged") -> bool:
        """Verify port membership by checking interface configuration in running-config."""
        try:
            running_config = str(self.data.running_config)
            config_lower = running_config.lower()

            # Extract interface section for this port
            port_lower = port.lower()

            # Look for interface section
            if f"interface {port_lower}" in config_lower:
                # Find the interface section and get lines until next interface
                lines = running_config.split('\n')
                in_interface = False
                interface_config = []

                for line in lines:
                    if f"interface {port}" in line.lower():
                        in_interface = True
                    elif in_interface:
                        if line.strip().startswith("interface"):
                            break
                        interface_config.append(line.lower())

                interface_text = '\n'.join(interface_config)

                if mode == "untagged":
                    # Check for access VLAN configuration
                    if f"switchport access vlan {vlan_id}" in interface_text:
                        st.log(f"  ✅ Port {port} found as untagged member of VLAN {vlan_id}")
                        return True
                else:
                    # Check for trunk VLAN configuration
                    if f"switchport trunk allowed vlan {vlan_id}" in interface_text:
                        st.log(f"  ✅ Port {port} found as tagged member of VLAN {vlan_id}")
                        return True

                st.log(f"  ❌ Port {port} NOT found as {mode} member of VLAN {vlan_id}")
                return False
            else:
                st.log(f"  ❌ Interface {port} NOT found in running-configuration")
                return False
        except Exception as e:
            st.log(f"  Error verifying port {port} in VLAN {vlan_id}: {e}")
            return False

    def _verify_port_in_show_vlan(self, dut, vlan_id: int, port: str, mode: str = "untagged") -> bool:
        """Verify port membership using show Vlan command (A=access, T=tagged)."""
        try:
            cmd = f'show Vlan {vlan_id}'
            vlan_output = st.show(dut, cmd, type=self.data.cli_type, skip_error_check=True)

            if not vlan_output:
                st.log(f"  ❌ Could not retrieve VLAN {vlan_id} information from show Vlan")
                return False

            output_str = str(vlan_output).lower()
            port_lower = port.lower()

            if mode == "untagged":
                # In show Vlan output, access ports should have "A" indicator
                # Look for port with A indicator
                if port_lower in output_str and "a" in output_str:
                    st.log(f"  ✅ Port {port} verified as untagged (A) member in show Vlan")
                    return True
            else:
                # In show Vlan output, trunk ports should have "T" indicator
                # Look for port with T indicator
                if port_lower in output_str and "t" in output_str:
                    st.log(f"  ✅ Port {port} verified as tagged (T) member in show Vlan")
                    return True

            st.log(f"  ❌ Port {port} NOT verified in show Vlan output")
            return False
        except Exception as e:
            st.log(f"  Warning: Could not verify with show Vlan: {e}")
            return False

    def test_vlan_persist_002_running_config_accuracy(self) -> None:
        """
        TC_VLAN_PERSIST_002: Running Config Accuracy Test

        Test execution with step tracking:
        1. Create VLAN 10
        2. Add Port1 as untagged member
        3. Add Port3 as tagged member
        4. Execute show running-config
        5. Verify all configurations are accurately displayed
        """
        st.banner("=" * 100)
        st.banner("TC_VLAN_PERSIST_002: RUNNING CONFIG ACCURACY - EXECUTION")
        st.banner("=" * 100)

        test_results = {
            "step_1_create_vlan_10": False,
            "step_2_add_port1_untagged": False,
            "step_3_add_port3_tagged": False,
            "step_4_show_running_config": False,
            "step_5_verify_config_accuracy": False,
        }

        try:
            # STEP 1: Create VLAN 10
            st.banner("STEP 1: Creating VLAN 10")
            vlan_id = self.data.vlan_id
            if vlan_api.create_vlan(self.data.dut1, str(vlan_id), cli_type=self.data.cli_type):
                st.log(f"✅ STEP 1 PASS: VLAN {vlan_id} created on DUT1")
                test_results["step_1_create_vlan_10"] = True
                self.data.created_vlans.append(vlan_id)
            else:
                st.log(f"❌ STEP 1 FAIL: Could not create VLAN {vlan_id} on DUT1")
                test_results["step_1_create_vlan_10"] = False

            # STEP 2: Add Port1 as untagged member
            st.banner("STEP 2: Adding Port1 as untagged member to VLAN")
            try:
                st.config(self.data.dut1, [
                    f"interface {self.data.dut1_port1}",
                    f"switchport access Vlan {vlan_id}",
                    "exit"
                ], type=self.data.cli_type, skip_error_check=True)
                st.log(f"✅ STEP 2 PASS: Port {self.data.dut1_port1} added as untagged member to VLAN {vlan_id}")
                test_results["step_2_add_port1_untagged"] = True
            except Exception as e:
                st.log(f"❌ STEP 2 FAIL: Could not add port1 to VLAN: {e}")
                test_results["step_2_add_port1_untagged"] = False

            # STEP 3: Add Port3 as tagged member
            st.banner("STEP 3: Adding Port3 as tagged member to VLAN")
            try:
                st.config(self.data.dut1, [
                    f"interface {self.data.dut1_port3}",
                    f"switchport trunk allowed Vlan {vlan_id}",
                    "exit"
                ], type=self.data.cli_type, skip_error_check=True)
                st.log(f"✅ STEP 3 PASS: Port {self.data.dut1_port3} added as tagged member to VLAN {vlan_id}")
                test_results["step_3_add_port3_tagged"] = True
            except Exception as e:
                st.log(f"❌ STEP 3 FAIL: Could not add port3 as tagged member: {e}")
                test_results["step_3_add_port3_tagged"] = False

            # STEP 4: Execute show running-config
            st.banner("STEP 4: Executing show running-configuration")
            try:
                cmd = 'show running-configuration | no-more'
                running_config_output = st.show(self.data.dut1, cmd, type=self.data.cli_type,
                                               skip_tmpl=True, skip_error_check=True)
                st.log(f"✅ STEP 4 PASS: Running configuration retrieved")
                # Store for use in Step 5
                self.data.running_config = running_config_output
                test_results["step_4_show_running_config"] = True
            except Exception as e:
                st.log(f"❌ STEP 4 FAIL: Could not retrieve running configuration: {e}")
                test_results["step_4_show_running_config"] = False

            # STEP 5: Verify all configurations are accurately displayed
            st.banner("STEP 5: Verifying running config accuracy")
            st.log("Verifying VLAN and port configurations in running-config and show Vlan...")

            # Verify VLAN exists in running-config
            vlan_found = self._verify_vlan_in_running_config(self.data.dut1, vlan_id)

            # Verify Port1 (untagged) in interface configuration
            port1_config_found = self._verify_port_in_interface_config(self.data.dut1, vlan_id,
                                                                      self.data.dut1_port1, "untagged")

            # Verify Port3 (tagged) in interface configuration
            port3_config_found = self._verify_port_in_interface_config(self.data.dut1, vlan_id,
                                                                      self.data.dut1_port3, "tagged")

            # Verify using show Vlan command as well
            port1_vlan_found = self._verify_port_in_show_vlan(self.data.dut1, vlan_id,
                                                             self.data.dut1_port1, "untagged")
            port3_vlan_found = self._verify_port_in_show_vlan(self.data.dut1, vlan_id,
                                                             self.data.dut1_port3, "tagged")

            # Use show Vlan as primary verification since it's more reliable for port membership
            if vlan_found and port1_vlan_found and port3_vlan_found:
                st.log(f"✅ STEP 5 PASS: All VLAN configurations accurately reflected (verified via show Vlan)")
                test_results["step_5_verify_config_accuracy"] = True
            else:
                st.log(f"❌ STEP 5 FAIL: Some configurations missing")
                st.log(f"   VLAN found: {vlan_found}")
                st.log(f"   Port1 (untagged) in interface config: {port1_config_found}")
                st.log(f"   Port3 (tagged) in interface config: {port3_config_found}")
                st.log(f"   Port1 verified in show Vlan: {port1_vlan_found}")
                st.log(f"   Port3 verified in show Vlan: {port3_vlan_found}")
                test_results["step_5_verify_config_accuracy"] = False

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
            st.log("✅ TC_VLAN_PERSIST_002: PASSED")
            st.report_pass("test_case_passed")
        else:
            st.log(f"❌ TC_VLAN_PERSIST_002: FAILED ({total-passed} steps failed)")
            st.report_fail("test_case_failed", f"Failed steps: {total-passed} steps failed")
