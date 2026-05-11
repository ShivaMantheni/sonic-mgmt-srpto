"""
TC_VLAN_CREATE_003: Create VLAN with Valid Range

Author: Test Automation Team
Date: 2026-05-11

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_Create_VLAN_with_Valid_Range.py \\
  --logs-path ./logs/vlan_create_valid_range_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  TC_VLAN_CREATE_003: Create VLAN with Valid Range

  Objective: Verify VLAN creation with valid VLAN IDs (1-4094)

  Steps:
    1. Create VLAN 1 (default VLAN)
    2. Create VLAN 4094 (maximum VLAN ID)
    3. Verify both VLANs exist using show running-config

  Expected Result: VLANs with valid IDs are created successfully

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

VAR_FILE_ENV = "VLAN_CREATE_VALID_RANGE_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_create_valid_range.yaml"
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
                "vlan_min": 1,
                "vlan_max": 4094,
                "cleanup": True
            },
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    st.log(f"Loaded VLAN CREATE_VALID_RANGE configuration from: {candidate}")
    return config


@pytest.mark.topology("D1D2:2")
class TestVlanCreateValidRange:
    """Test class for VLAN creation with valid range (TC_VLAN_CREATE_003)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Setup: Load config, verify topology, clear interfaces, cleanup test VLANs."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_CREATE_003: CREATE VLAN WITH VALID RANGE - SETUP")
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
        cls.data.vlan_min = int(defaults.get("vlan_min", 1))
        cls.data.vlan_max = int(defaults.get("vlan_max", 4094))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT and ports from topology
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut1_port = topology.D1D2P1
        cls.data.dut2_port = topology.D2D1P1

        st.log(f"DUT1: {cls.data.dut1}, DUT2: {cls.data.dut2}")
        st.log(f"DUT1 Port: {cls.data.dut1_port}, DUT2 Port: {cls.data.dut2_port}")
        st.log(f"CLI Type: {cls.data.cli_type}")
        st.log(f"VLAN Range: {cls.data.vlan_min} to {cls.data.vlan_max}")

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
        for vlan_id in [cls.data.vlan_min, cls.data.vlan_max]:
            try:
                vlan_api.delete_vlan(cls.data.dut1, str(vlan_id), cli_type=cls.data.cli_type, skip_error_report=True)
                vlan_api.delete_vlan(cls.data.dut2, str(vlan_id), cli_type=cls.data.cli_type, skip_error_report=True)
            except Exception as e:
                st.log(f"Pre-cleanup VLAN {vlan_id} exception (non-fatal): {e}")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after test: Remove all configurations."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_CREATE_003: CLEANUP")
        st.banner("=" * 100)

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        # Remove created VLANs
        for vlan_id in cls.data.created_vlans:
            try:
                vlan_api.delete_vlan(cls.data.dut1, str(vlan_id), cli_type=cls.data.cli_type, skip_error_report=True)
                vlan_api.delete_vlan(cls.data.dut2, str(vlan_id), cli_type=cls.data.cli_type, skip_error_report=True)
                st.log(f"✅ VLAN {vlan_id} deleted on both DUTs")
            except Exception as e:
                st.log(f"Teardown VLAN {vlan_id} exception (non-fatal): {e}")

    def _verify_vlan_exists(self, dut, vlan_id: int) -> bool:
        """Verify VLAN exists using show running-config."""
        try:
            cmd = f"show running-config | grep 'vlan {vlan_id}'"
            output = st.show(dut, cmd, skip_tmpl=True, skip_error_check=True)

            if output and f"vlan {vlan_id}" in str(output).lower():
                st.log(f"  ✅ VLAN {vlan_id} verified in running-config")
                return True
            else:
                st.log(f"  ❌ VLAN {vlan_id} NOT found in running-config")
                return False
        except Exception as e:
            st.log(f"  Error verifying VLAN {vlan_id}: {e}")
            return False

    def test_vlan_create_003_valid_range(self) -> None:
        """
        TC_VLAN_CREATE_003: Create VLAN with Valid Range Test

        Test execution with step tracking:
        1. Create VLAN 1 (default VLAN)
        2. Create VLAN 4094 (maximum VLAN ID)
        3. Verify both VLANs exist
        """
        st.banner("=" * 100)
        st.banner("TC_VLAN_CREATE_003: CREATE VLAN WITH VALID RANGE - EXECUTION")
        st.banner("=" * 100)

        test_results = {
            "step_1_create_vlan_1": False,
            "step_2_create_vlan_4094": False,
            "step_3_verify_vlan_1": False,
            "step_4_verify_vlan_4094": False,
        }

        try:
            # STEP 1: Create VLAN 1 (default VLAN)
            st.banner("STEP 1: Creating VLAN 1 (default VLAN)")
            vlan_1 = 1
            if vlan_api.create_vlan(self.data.dut1, str(vlan_1), cli_type=self.data.cli_type):
                st.log(f"✅ STEP 1 PASS: VLAN {vlan_1} created on DUT1")
                test_results["step_1_create_vlan_1"] = True
                self.data.created_vlans.append(vlan_1)
            else:
                st.log(f"❌ STEP 1 FAIL: Could not create VLAN {vlan_1} on DUT1")
                test_results["step_1_create_vlan_1"] = False

            # STEP 2: Create VLAN 4094 (maximum VLAN ID)
            st.banner("STEP 2: Creating VLAN 4094 (maximum VLAN ID)")
            vlan_4094 = 4094
            if vlan_api.create_vlan(self.data.dut1, str(vlan_4094), cli_type=self.data.cli_type):
                st.log(f"✅ STEP 2 PASS: VLAN {vlan_4094} created on DUT1")
                test_results["step_2_create_vlan_4094"] = True
                self.data.created_vlans.append(vlan_4094)
            else:
                st.log(f"❌ STEP 2 FAIL: Could not create VLAN {vlan_4094} on DUT1")
                test_results["step_2_create_vlan_4094"] = False

            # STEP 3: Verify VLAN 1 exists
            st.banner("STEP 3: Verifying VLAN 1 exists in running-config")
            if self._verify_vlan_exists(self.data.dut1, vlan_1):
                st.log(f"✅ STEP 3 PASS: VLAN {vlan_1} verified")
                test_results["step_3_verify_vlan_1"] = True
            else:
                st.log(f"❌ STEP 3 FAIL: VLAN {vlan_1} verification failed")
                test_results["step_3_verify_vlan_1"] = False

            # STEP 4: Verify VLAN 4094 exists
            st.banner("STEP 4: Verifying VLAN 4094 exists in running-config")
            if self._verify_vlan_exists(self.data.dut1, vlan_4094):
                st.log(f"✅ STEP 4 PASS: VLAN {vlan_4094} verified")
                test_results["step_4_verify_vlan_4094"] = True
            else:
                st.log(f"❌ STEP 4 FAIL: VLAN {vlan_4094} verification failed")
                test_results["step_4_verify_vlan_4094"] = False

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
            st.log("✅ TC_VLAN_CREATE_003: PASSED")
            st.report_pass("test_case_passed")
        else:
            st.log(f"❌ TC_VLAN_CREATE_003: FAILED ({total-passed} steps failed)")
            st.report_fail("test_case_failed", f"Failed steps: {total-passed} steps failed")
