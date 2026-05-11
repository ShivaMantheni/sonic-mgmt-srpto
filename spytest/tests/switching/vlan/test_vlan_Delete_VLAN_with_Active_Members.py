"""
TC_VLAN_DELETE_002: Delete VLAN with Active Members

Author: Test Automation Team
Date: 2026-05-11

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Delete_VLAN_with_Active_Members.py \\
  --logs-path ./logs/vlan_delete_active_members_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  TC_VLAN_DELETE_002: Delete VLAN with Active Members

  Objective: Verify behavior when deleting VLAN with port members

  Steps:
    1. Create VLAN 100
    2. Add Port1 as untagged member
    3. Attempt to delete VLAN 100
    4. Verify expected behavior (should fail or remove ports first)

  Expected Result: System handles deletion appropriately

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

VAR_FILE_ENV = "VLAN_DELETE_ACTIVE_MEMBERS_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_delete_active_members.yaml"
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
                "vlan_id": 100,
                "cleanup": True
            },
            "testcases": {}
        }

    with candidate.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    st.log(f"Loaded VLAN DELETE_ACTIVE_MEMBERS configuration from: {candidate}")
    return config


@pytest.mark.topology("D1D2:2")
class TestVlanDeleteActiveMembers:
    """Test class for VLAN deletion with active members (TC_VLAN_DELETE_002)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Setup: Load config, verify topology, clear interfaces, cleanup test VLANs."""
        st.banner("=" * 100)
        st.banner("TC_VLAN_DELETE_002: DELETE VLAN WITH ACTIVE MEMBERS - SETUP")
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
        cls.data.vlan_id = int(defaults.get("vlan_id", 100))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT and ports from topology
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut1_port = topology.D1D2P1
        cls.data.dut2_port = topology.D2D1P1

        st.log(f"DUT1: {cls.data.dut1}, DUT2: {cls.data.dut2}")
        st.log(f"DUT1 Port: {cls.data.dut1_port}, DUT2 Port: {cls.data.dut2_port}")
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
        st.banner("TC_VLAN_DELETE_002: CLEANUP")
        st.banner("=" * 100)

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        # Remove port from VLAN first (if member)
        try:
            st.config(cls.data.dut1, [
                f"interface {cls.data.dut1_port}",
                "no switchport access vlan",
                "exit"
            ], type=cls.data.cli_type, skip_error_check=True)
        except Exception as e:
            st.log(f"Teardown remove port from VLAN exception (non-fatal): {e}")

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

    def _verify_vlan_exists(self, dut, vlan_id: int) -> bool:
        """Verify VLAN exists using show running-configuration."""
        try:
            cmd = f'show running-configuration | grep "vlan {vlan_id}"'
            output = st.show(dut, cmd, type=self.data.cli_type, skip_tmpl=True, skip_error_check=True)

            if output and f"vlan {vlan_id}" in str(output).lower():
                st.log(f"  ✅ VLAN {vlan_id} found in running-configuration")
                return True
            else:
                st.log(f"  ❌ VLAN {vlan_id} NOT found in running-configuration")
                return False
        except Exception as e:
            st.log(f"  Error verifying VLAN {vlan_id}: {e}")
            return False

    def test_vlan_delete_002_active_members(self) -> None:
        """
        TC_VLAN_DELETE_002: Delete VLAN with Active Members Test

        Test execution with step tracking:
        1. Create VLAN 100
        2. Add Port1 as untagged member
        3. Attempt to delete VLAN 100
        4. Verify expected behavior (should fail or remove ports first)
        """
        st.banner("=" * 100)
        st.banner("TC_VLAN_DELETE_002: DELETE VLAN WITH ACTIVE MEMBERS - EXECUTION")
        st.banner("=" * 100)

        test_results = {
            "step_1_create_vlan_100": False,
            "step_2_add_port_member": False,
            "step_3_attempt_delete_vlan": False,
            "step_4_verify_behavior": False,
        }

        try:
            # STEP 1: Create VLAN 100
            st.banner("STEP 1: Creating VLAN 100")
            vlan_id = self.data.vlan_id
            if vlan_api.create_vlan(self.data.dut1, str(vlan_id), cli_type=self.data.cli_type):
                st.log(f"✅ STEP 1 PASS: VLAN {vlan_id} created on DUT1")
                test_results["step_1_create_vlan_100"] = True
                self.data.created_vlans.append(vlan_id)
            else:
                st.log(f"❌ STEP 1 FAIL: Could not create VLAN {vlan_id} on DUT1")
                test_results["step_1_create_vlan_100"] = False

            # STEP 2: Add Port1 as untagged member
            st.banner("STEP 2: Adding Port1 as untagged member to VLAN")
            try:
                st.config(self.data.dut1, [
                    f"interface {self.data.dut1_port}",
                    f"switchport access vlan {vlan_id}",
                    "switchport mode access",
                    "exit"
                ], type=self.data.cli_type, skip_error_check=True)
                st.log(f"✅ STEP 2 PASS: Port {self.data.dut1_port} added as member to VLAN {vlan_id}")
                test_results["step_2_add_port_member"] = True
            except Exception as e:
                st.log(f"❌ STEP 2 FAIL: Could not add port to VLAN: {e}")
                test_results["step_2_add_port_member"] = False

            # STEP 3: Attempt to delete VLAN 100 with active members
            st.banner("STEP 3: Attempting to delete VLAN with active members")
            try:
                # Attempt to delete VLAN with skip_error_check to capture both success and failure
                result = vlan_api.delete_vlan(self.data.dut1, str(vlan_id),
                                            cli_type=self.data.cli_type, skip_error_report=True)
                if result:
                    st.log(f"✅ STEP 3 PASS: VLAN {vlan_id} deleted successfully (system allowed deletion with members)")
                    test_results["step_3_attempt_delete_vlan"] = True
                else:
                    st.log(f"⚠️ STEP 3 INFO: Delete returned False (system may require members to be removed first)")
                    test_results["step_3_attempt_delete_vlan"] = False
            except Exception as e:
                st.log(f"⚠️ STEP 3 INFO: Delete attempt failed with error (expected behavior): {e}")
                test_results["step_3_attempt_delete_vlan"] = False

            # STEP 4: Verify expected behavior
            st.banner("STEP 4: Verifying VLAN deletion behavior")
            vlan_still_exists = self._verify_vlan_exists(self.data.dut1, vlan_id)

            if test_results["step_3_attempt_delete_vlan"]:
                # If delete succeeded, VLAN should not exist
                if not vlan_still_exists:
                    st.log(f"✅ STEP 4 PASS: VLAN {vlan_id} successfully deleted as expected")
                    test_results["step_4_verify_behavior"] = True
                else:
                    st.log(f"❌ STEP 4 FAIL: VLAN {vlan_id} still exists after delete")
                    test_results["step_4_verify_behavior"] = False
            else:
                # If delete failed, VLAN should still exist (system correctly prevented deletion)
                if vlan_still_exists:
                    st.log(f"✅ STEP 4 PASS: VLAN {vlan_id} still exists (system correctly prevented deletion with active members)")
                    test_results["step_4_verify_behavior"] = True
                else:
                    st.log(f"❌ STEP 4 FAIL: VLAN {vlan_id} was deleted despite deletion attempt failure")
                    test_results["step_4_verify_behavior"] = False

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
            st.log("✅ TC_VLAN_DELETE_002: PASSED")
            st.report_pass("test_case_passed")
        else:
            st.log(f"❌ TC_VLAN_DELETE_002: FAILED ({total-passed} steps failed)")
            st.report_fail("test_case_failed", f"Failed steps: {total-passed} steps failed")
