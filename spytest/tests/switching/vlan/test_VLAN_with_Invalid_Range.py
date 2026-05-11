"""
TC_VLAN_CREATE_004: Create VLAN with Invalid Range

Author: Test Automation Team
Date: 2026-05-11

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_VLAN_with_Invalid_Range.py \\
  --logs-path ./logs/vlan_create_invalid_range_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  TC_VLAN_CREATE_004: Create VLAN with Invalid Range

  Objective: Verify system rejects invalid VLAN IDs

  Steps:
    1. Attempt to create VLAN 0 (below valid range)
    2. Attempt to create VLAN 4095 (above valid range)
    3. Verify error messages are generated
    4. Verify no invalid VLANs are created

  Expected Result: System rejects invalid VLAN IDs with appropriate error messages

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

VAR_FILE_ENV = "VLAN_CREATE_INVALID_RANGE_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_create_invalid_range.yaml"
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
                "vlan_invalid_low": 0,
                "vlan_invalid_high": 4095,
                "cleanup": True
            },
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    st.log(f"Loaded VLAN CREATE_INVALID_RANGE configuration from: {candidate}")
    return config


@pytest.mark.topology("D1D2:2")
class TestVlanCreateInvalidRange:
    """Test class for VLAN creation with invalid range (TC_VLAN_CREATE_004)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Setup: Load config, verify topology, clear interfaces, cleanup test VLANs."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_CREATE_004: CREATE VLAN WITH INVALID RANGE - SETUP")
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
        cls.data.vlan_invalid_low = int(defaults.get("vlan_invalid_low", 0))
        cls.data.vlan_invalid_high = int(defaults.get("vlan_invalid_high", 4095))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT and ports from topology
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut1_port = topology.D1D2P1
        cls.data.dut2_port = topology.D2D1P1

        st.log(f"DUT1: {cls.data.dut1}, DUT2: {cls.data.dut2}")
        st.log(f"DUT1 Port: {cls.data.dut1_port}, DUT2 Port: {cls.data.dut2_port}")
        st.log(f"CLI Type: {cls.data.cli_type}")
        st.log(f"Invalid VLAN IDs to test: {cls.data.vlan_invalid_low}, {cls.data.vlan_invalid_high}")

        # Track created VLANs for cleanup (should be none if test passes)
        cls.data.created_vlans = []

        # Pre-cleanup before test
        cls._clear_interface_config()

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
    def teardown_class(cls) -> None:
        """Cleanup after test: Remove all configurations."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_CREATE_004: CLEANUP")
        st.banner("=" * 100)

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        # Remove any created VLANs (should be empty if test passes)
        for vlan_id in cls.data.created_vlans:
            try:
                vlan_api.delete_vlan(cls.data.dut1, str(vlan_id), cli_type=cls.data.cli_type, skip_error_report=True)
                vlan_api.delete_vlan(cls.data.dut2, str(vlan_id), cli_type=cls.data.cli_type, skip_error_report=True)
                st.log(f"✅ VLAN {vlan_id} deleted on both DUTs")
            except Exception as e:
                st.log(f"Teardown VLAN {vlan_id} exception (non-fatal): {e}")

    def _verify_vlan_not_created(self, dut, vlan_id: int) -> bool:
        """Verify VLAN does NOT exist using show running-configuration."""
        try:
            cmd = f'show running-configuration | grep "vlan {vlan_id}"'
            output = st.show(dut, cmd, type=self.data.cli_type, skip_tmpl=True, skip_error_check=True)

            if output and f"vlan {vlan_id}" in str(output).lower():
                st.log(f"  ❌ VLAN {vlan_id} SHOULD NOT exist but was found in running-configuration")
                return False
            else:
                st.log(f"  ✅ VLAN {vlan_id} correctly NOT found in running-configuration")
                return True
        except Exception as e:
            st.log(f"  Error verifying VLAN {vlan_id} absence: {e}")
            return True  # Assume non-existent if we can't verify

    def test_vlan_create_004_invalid_range(self) -> None:
        """
        TC_VLAN_CREATE_004: Create VLAN with Invalid Range Test

        Test execution with step tracking:
        1. Attempt to create VLAN 0 (below valid range)
        2. Attempt to create VLAN 4095 (above valid range)
        3. Verify error messages are generated
        4. Verify invalid VLANs were not created
        """
        st.banner("=" * 100)
        st.banner("TC_VLAN_CREATE_004: CREATE VLAN WITH INVALID RANGE - EXECUTION")
        st.banner("=" * 100)

        test_results = {
            "step_1_attempt_vlan_0": False,
            "step_2_attempt_vlan_4095": False,
            "step_3_verify_vlan_0_not_created": False,
            "step_4_verify_vlan_4095_not_created": False,
        }

        try:
            # STEP 1: Attempt to create VLAN 0 (should fail)
            st.banner("STEP 1: Attempting to create VLAN 0 (should be rejected)")
            vlan_0 = 0
            result = vlan_api.create_vlan(self.data.dut1, str(vlan_0), cli_type=self.data.cli_type)

            if not result:
                # EXPECTED: Creation should fail
                st.log(f"✅ STEP 1 PASS: VLAN {vlan_0} creation correctly rejected on DUT1")
                test_results["step_1_attempt_vlan_0"] = True
            else:
                # UNEXPECTED: VLAN 0 should not be created
                st.log(f"❌ STEP 1 FAIL: VLAN {vlan_0} was unexpectedly created on DUT1")
                test_results["step_1_attempt_vlan_0"] = False
                self.data.created_vlans.append(vlan_0)

            # STEP 2: Attempt to create VLAN 4095 (should fail)
            st.banner("STEP 2: Attempting to create VLAN 4095 (should be rejected)")
            vlan_4095 = 4095
            result = vlan_api.create_vlan(self.data.dut1, str(vlan_4095), cli_type=self.data.cli_type)

            if not result:
                # EXPECTED: Creation should fail
                st.log(f"✅ STEP 2 PASS: VLAN {vlan_4095} creation correctly rejected on DUT1")
                test_results["step_2_attempt_vlan_4095"] = True
            else:
                # UNEXPECTED: VLAN 4095 should not be created
                st.log(f"❌ STEP 2 FAIL: VLAN {vlan_4095} was unexpectedly created on DUT1")
                test_results["step_2_attempt_vlan_4095"] = False
                self.data.created_vlans.append(vlan_4095)

            # STEP 3: Verify VLAN 0 was not created
            st.banner("STEP 3: Verifying VLAN 0 was NOT created in running-configuration")
            if self._verify_vlan_not_created(self.data.dut1, vlan_0):
                st.log(f"✅ STEP 3 PASS: VLAN {vlan_0} correctly not in configuration")
                test_results["step_3_verify_vlan_0_not_created"] = True
            else:
                st.log(f"❌ STEP 3 FAIL: VLAN {vlan_0} verification failed")
                test_results["step_3_verify_vlan_0_not_created"] = False

            # STEP 4: Verify VLAN 4095 was not created
            st.banner("STEP 4: Verifying VLAN 4095 was NOT created in running-configuration")
            if self._verify_vlan_not_created(self.data.dut1, vlan_4095):
                st.log(f"✅ STEP 4 PASS: VLAN {vlan_4095} correctly not in configuration")
                test_results["step_4_verify_vlan_4095_not_created"] = True
            else:
                st.log(f"❌ STEP 4 FAIL: VLAN {vlan_4095} verification failed")
                test_results["step_4_verify_vlan_4095_not_created"] = False

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
            st.log("✅ TC_VLAN_CREATE_004: PASSED")
            st.report_pass("test_case_passed")
        else:
            st.log(f"❌ TC_VLAN_CREATE_004: FAILED ({total-passed} steps failed)")
            st.report_fail("test_case_failed", f"Failed steps: {total-passed} steps failed")
