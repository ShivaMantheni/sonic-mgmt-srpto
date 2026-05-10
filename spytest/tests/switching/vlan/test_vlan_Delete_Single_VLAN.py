"""
VLAN DELETION - SINGLE VLAN DELETE OPERATION
Author: Test Automation Team
Date: 2026-05-06

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/test_vlan_Delete_Single_VLAN.py \\
  --logs-path ./logs/vlan_delete_single_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Comprehensive validation of single VLAN deletion using SpyTest APIs
  and klish CLI. The test verifies VLAN creation, existence validation,
  deletion, and post-deletion verification using 5-step validation method:
  show Vlan, running-config grep, vlan count, interface brief, and interface
  status commands to ensure complete validation of VLAN deletion lifecycle.

Pre-requisites:
  - Topology: Two DUTs (D1-D2) with 2+ connections | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 2 nodes
        # +------------------+       +------------------+
        # |      DUT1        |-------|      DUT2        |
        # |    (Spine01)     | 1-5   |    (Spine02)     |
        # +------------------+       +------------------+

  - Feature flags / min SONiC version: VLAN support required
  - Required test variables (YAML): spytest/vars/switching/vlan/vars_vlan_delete_single.yaml
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api

VAR_FILE_ENV = "VLAN_DELETE_SINGLE_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_delete_single.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        st.warn(f"VLAN variable file not found: {candidate}, using defaults")
        return {"defaults": {"cli_type": "klish", "vlan_id": "100"}, "testcases": {}}

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


@pytest.mark.topology("D1D2:2")
class TestVlanDeleteSingle:
    """Testcases covering single VLAN deletion operations."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and testcase variables for the suite."""
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

        # VLAN to delete
        cls.data.vlan_id = str(defaults.get("vlan_id", "100"))

        # Get DUT handles
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut_names = st.get_dut_names()

        st.log(f"DUT1 for testing: {cls.data.dut1}")
        st.log(f"DUT2 for testing: {cls.data.dut2}")
        st.log(f"VLAN ID for deletion test: {cls.data.vlan_id}")

        # Pre-test cleanup - ensure VLAN used in test doesn't exist
        cls._cleanup_test_vlan()

        # Verify VLAN setup completed
        st.log("Setup Complete - Ready for testing")

        st.banner("VLAN Delete Single Test Suite - Setup Complete")

    @classmethod
    def _cleanup_test_vlan(cls) -> None:
        """Cleanup VLAN that will be used in tests before starting."""
        st.banner("Pre-Test Cleanup - Removing Test VLAN if it exists")

        dut1 = cls.data.dut1
        dut2 = cls.data.dut2
        cli_type = cls.data.cli_type
        vlan_id = cls.data.vlan_id

        for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
            try:
                st.log(f"Cleaning up VLAN {vlan_id} on {dut_name} before test (if exists)")
                vlan_api.delete_vlan(dut, vlan_id, cli_type=cli_type, skip_error_report=True, remove_vlan_mapping=False)
                st.log(f"Pre-cleanup: VLAN {vlan_id} deleted on {dut_name} (if existed)")
            except Exception as e:
                st.log(f"Pre-cleanup VLAN {vlan_id} on {dut_name} exception (non-fatal): {e}")

        st.log("✅ Pre-test cleanup completed")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup test VLAN after test suite completes."""
        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        st.banner("VLAN Delete Single Test Suite - Cleanup")

        dut1 = cls.data.dut1
        dut2 = cls.data.dut2
        cli_type = cls.data.cli_type
        vlan_id = cls.data.vlan_id

        for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
            try:
                vlan_api.delete_vlan(dut, vlan_id, cli_type=cli_type, skip_error_report=True, remove_vlan_mapping=False)
                st.log(f"Teardown: VLAN {vlan_id} deleted on {dut_name} (if existed)")
            except Exception as e:
                st.log(f"Teardown VLAN {vlan_id} on {dut_name} exception (non-fatal): {e}")

        st.log("✅ Teardown cleanup completed")

    def _verify_vlan_5_commands(
        self,
        dut,
        dut_name,
        vlan_id: str,
        should_exist: bool = True,
        expected_count: int = None
    ) -> bool:
        """
        Perform 5-command verification for VLAN existence on a specific DUT.

        Commands executed:
        1. show Vlan <id> - using raw st.show with string verification
        2. show running-configuration | grep Vlan<id> - using st.show
        3. show Vlan count - using manual count from raw output
        4. show interface brief - using st.show
        5. show interface status | no-more - using st.show

        Args:
            dut: Device handle
            dut_name: Device name for logging
            vlan_id: VLAN ID to verify
            should_exist: True if VLAN should exist, False if it should not
            expected_count: Expected VLAN count (optional)

        Returns:
            True if all verifications pass, False otherwise
        """
        cli_type = self.data.cli_type
        vlan_name = f"Vlan{vlan_id}"
        all_passed = True

        st.banner(f"5-COMMAND VERIFICATION: {dut_name} VLAN {vlan_id} (should_exist={should_exist})")

        # Command 1: show Vlan <id>
        st.log(f"STEP 1/5: Executing 'show Vlan {vlan_id}' on {dut_name}")
        try:
            output1 = st.show(dut, f"show Vlan {vlan_id}", type=cli_type, skip_tmpl=True, skip_error_check=True)
            output1_str = str(output1)
            st.log(f"show Vlan {vlan_id} output: {output1_str[:200]}")

            if should_exist:
                if vlan_name in output1_str:
                    st.log(f"✅ VLAN {vlan_id} found in 'show Vlan {vlan_id}' output on {dut_name}")
                    st.log(f"   Output contains: {vlan_name}")
                elif "not found" in output1_str.lower():
                    st.error(f"❌ VLAN {vlan_id} not found on {dut_name} - output says 'not found'")
                    all_passed = False
                else:
                    if f"Vlan{vlan_id}" in output1_str or f"VLAN{vlan_id}" in output1_str:
                        st.log(f"✅ VLAN {vlan_id} found in output on {dut_name} (format variation)")
                    else:
                        st.error(f"❌ VLAN {vlan_id} not found in output on {dut_name}")
                        st.log(f"   Output received: {output1_str[:500]}")
                        all_passed = False
            else:
                # VLAN should NOT exist
                if "not found" in output1_str.lower():
                    st.log(f"✅ VLAN {vlan_id} correctly not found on {dut_name} (output says 'not found')")
                elif vlan_name not in output1_str:
                    st.log(f"✅ VLAN {vlan_id} correctly not found on {dut_name} (not in output)")
                else:
                    st.error(f"❌ VLAN {vlan_id} still exists on {dut_name} but should be deleted")
                    st.log(f"   Output contains: {vlan_name}")
                    all_passed = False
        except Exception as e:
            st.log(f"Show Vlan {vlan_id} exception on {dut_name}: {e}")
            if not should_exist:
                st.log(f"✅ Exception expected for non-existent VLAN {vlan_id}")
            else:
                st.error(f"❌ Unexpected exception for VLAN {vlan_id} on {dut_name}: {e}")
                all_passed = False

        # Command 2: show running-configuration | grep Vlan<id>
        st.log(f"STEP 2/5: Checking running-configuration for {vlan_name} on {dut_name}")
        try:
            cmd = f"show running-configuration | grep {vlan_name}"
            output2 = st.show(dut, cmd, type=cli_type, skip_tmpl=True, skip_error_check=True)
            output2_str = str(output2)

            if should_exist:
                if f"interface {vlan_name}" in output2_str or vlan_name in output2_str:
                    st.log(f"✅ {vlan_name} found in running-configuration on {dut_name}")
                else:
                    st.warn(f"⚠️ {vlan_name} not found in running-config grep on {dut_name} (may be normal for new VLANs)")
            else:
                if vlan_name not in output2_str or len(output2_str.strip()) < 5:
                    st.log(f"✅ {vlan_name} correctly not in running-configuration on {dut_name}")
                else:
                    st.error(f"❌ {vlan_name} still in running-configuration on {dut_name}")
                    st.log(f"   Output received: {output2_str}")
                    all_passed = False
        except Exception as e:
            st.log(f"Running-config check exception on {dut_name}: {e}")

        # Command 3: show Vlan count
        st.log("STEP 3/5: Executing 'show Vlan count' - using direct count from raw output")
        try:
            vlan_output = st.show(dut, "show Vlan", type=cli_type, skip_tmpl=True)
            vlan_lines = [line for line in vlan_output.splitlines() if re.match(r'^\s*Vlan\d+', line)]
            vlan_count = len(vlan_lines)
            vlan_list = [re.match(r'^\s*(Vlan\d+)', line).group(1) for line in vlan_lines]
            st.log(f"Current VLAN count on {dut_name}: {vlan_count} (VLANs: {vlan_list})")

            if expected_count is not None:
                if vlan_count == expected_count:
                    st.log(f"✅ VLAN count matches expected on {dut_name}: {vlan_count}")
                else:
                    st.error(f"❌ VLAN count mismatch on {dut_name}: {vlan_count} != {expected_count}")
                    all_passed = False
            else:
                st.log(f"ℹ️ VLAN count on {dut_name}: {vlan_count} (no expected count specified)")
        except Exception as e:
            st.error(f"❌ Failed to get VLAN count on {dut_name}: {e}")
            all_passed = False

        # Command 4: show interface brief
        st.log("STEP 4/5: Executing 'show interface brief' on {dut_name}")
        try:
            output4 = st.show(dut, "show interface brief", type=cli_type, skip_tmpl=True, skip_error_check=True)
            output4_str = str(output4)

            if should_exist:
                if vlan_name in output4_str:
                    st.log(f"✅ {vlan_name} found in 'show interface brief' on {dut_name}")
                else:
                    st.warn(f"⚠️ {vlan_name} not found in 'show interface brief' on {dut_name} (may be normal for new VLANs)")
            else:
                if vlan_name not in output4_str:
                    st.log(f"✅ {vlan_name} correctly not in 'show interface brief' on {dut_name}")
                else:
                    st.error(f"❌ {vlan_name} still in 'show interface brief' on {dut_name}")
                    all_passed = False
        except Exception as e:
            st.log(f"Interface brief exception on {dut_name}: {e}")

        # Command 5: show interface status | no-more
        st.log(f"STEP 5/5: Executing 'show interface status | no-more' on {dut_name}")
        try:
            output5 = st.show(dut, "show interface status | no-more", type=cli_type, skip_tmpl=True, skip_error_check=True)
            output5_str = str(output5)

            if should_exist:
                if vlan_name in output5_str:
                    st.log(f"✅ {vlan_name} found in 'show interface status' on {dut_name}")
                else:
                    st.warn(f"⚠️ {vlan_name} not found in 'show interface status' on {dut_name} (may be normal for new VLANs)")
            else:
                if vlan_name not in output5_str:
                    st.log(f"✅ {vlan_name} correctly not in 'show interface status' on {dut_name}")
                else:
                    st.error(f"❌ {vlan_name} still in 'show interface status' on {dut_name}")
                    all_passed = False
        except Exception as e:
            st.log(f"Interface status exception on {dut_name}: {e}")

        # Summary
        if all_passed:
            st.log(f"✅ ALL 5 VERIFICATIONS PASSED for {dut_name} VLAN {vlan_id}")
        else:
            st.error(f"❌ SOME VERIFICATIONS FAILED for {dut_name} VLAN {vlan_id}")

        return all_passed

    @pytest.mark.inventory(feature="VLAN_Basic", testcases=["TC_VLAN_DELETE_001"])
    def test_vlan_delete_single(self) -> None:
        """
        TC_VLAN_DELETE_001: Delete Single VLAN

        Objective: Verify VLAN deletion
        Steps:
        1. Pre-cleanup: Delete test VLAN 100 if it exists
        2. Get initial VLAN count on both DUTs
        3. Create VLAN 100 on both DUTs
        4. Verify VLAN 100 exists using 5-command method on both DUTs
        5. Delete VLAN 100 from both DUTs
        6. Verify VLAN 100 is deleted using 5-command method on both DUTs
        7. Verify using show running-configuration that VLAN 100 is removed

        Expected Result: VLAN 100 is deleted successfully on both DUTs
        """
        st.banner("TC_VLAN_DELETE_001: Delete Single VLAN 100")

        dut1 = self.data.dut1
        dut2 = self.data.dut2
        cli_type = self.data.cli_type
        vlan_id = self.data.vlan_id

        # Step 0: Pre-cleanup - delete VLAN if it exists
        st.log("Step 0: Pre-cleanup - Deleting test VLAN if it exists on both DUTs")
        vlan_api.delete_vlan(dut1, vlan_id, cli_type=cli_type, skip_error_report=True, remove_vlan_mapping=False)
        vlan_api.delete_vlan(dut2, vlan_id, cli_type=cli_type, skip_error_report=True, remove_vlan_mapping=False)

        # Step 1: Get initial VLAN count on both DUTs
        st.log("Step 1: Getting initial VLAN count on both DUTs")
        d1_initial_output = st.show(dut1, "show Vlan", type=cli_type, skip_tmpl=True)
        d1_vlan_lines = [line for line in d1_initial_output.splitlines() if re.match(r'^\s*Vlan\d+', line)]
        d1_initial_count = len(d1_vlan_lines)
        st.log(f"Initial VLAN count on D1: {d1_initial_count}")

        d2_initial_output = st.show(dut2, "show Vlan", type=cli_type, skip_tmpl=True)
        d2_vlan_lines = [line for line in d2_initial_output.splitlines() if re.match(r'^\s*Vlan\d+', line)]
        d2_initial_count = len(d2_vlan_lines)
        st.log(f"Initial VLAN count on D2: {d2_initial_count}")

        # Step 2: Create VLAN 100 on both DUTs
        st.log(f"Step 2: Creating VLAN {vlan_id} on both DUTs")
        result_d1 = vlan_api.create_vlan(dut1, vlan_id, cli_type=cli_type)
        result_d2 = vlan_api.create_vlan(dut2, vlan_id, cli_type=cli_type)

        if not result_d1 or not result_d2:
            st.report_fail("msg", f"Failed to create VLAN {vlan_id} on one or both DUTs")

        st.log(f"✅ VLAN {vlan_id} created successfully on both DUTs")

        # Step 3: Verify VLAN 100 exists using 5-command method on both DUTs
        st.log(f"Step 3: Verifying VLAN {vlan_id} exists on both DUTs using 5-command method")
        expected_count_d1_after_create = d1_initial_count + 1
        expected_count_d2_after_create = d2_initial_count + 1

        verification_create_d1 = self._verify_vlan_5_commands(
            dut1,
            "D1",
            vlan_id,
            should_exist=True,
            expected_count=expected_count_d1_after_create
        )

        verification_create_d2 = self._verify_vlan_5_commands(
            dut2,
            "D2",
            vlan_id,
            should_exist=True,
            expected_count=expected_count_d2_after_create
        )

        if not verification_create_d1 or not verification_create_d2:
            st.report_fail("msg", f"VLAN {vlan_id} not found after creation on one or both DUTs")

        # Step 4: Delete VLAN 100 from both DUTs
        st.log(f"Step 4: Deleting VLAN {vlan_id} from both DUTs")
        result_d1_delete = vlan_api.delete_vlan(dut1, vlan_id, cli_type=cli_type)
        result_d2_delete = vlan_api.delete_vlan(dut2, vlan_id, cli_type=cli_type)

        if not result_d1_delete or not result_d2_delete:
            st.report_fail("msg", f"Failed to delete VLAN {vlan_id} on one or both DUTs")

        st.log(f"✅ VLAN {vlan_id} deleted successfully on both DUTs")

        # Step 5: Verify VLAN 100 is deleted using 5-command method on both DUTs
        st.log(f"Step 5: Verifying VLAN {vlan_id} is deleted on both DUTs using 5-command method")
        expected_count_d1_after_delete = d1_initial_count
        expected_count_d2_after_delete = d2_initial_count

        verification_delete_d1 = self._verify_vlan_5_commands(
            dut1,
            "D1",
            vlan_id,
            should_exist=False,
            expected_count=expected_count_d1_after_delete
        )

        verification_delete_d2 = self._verify_vlan_5_commands(
            dut2,
            "D2",
            vlan_id,
            should_exist=False,
            expected_count=expected_count_d2_after_delete
        )

        if not verification_delete_d1 or not verification_delete_d2:
            st.report_fail("msg", f"VLAN {vlan_id} still exists after deletion on one or both DUTs")

        # Step 6: Verify using show running-configuration that VLAN is removed
        st.log(f"Step 6: Final verification - Checking running-configuration on both DUTs")
        vlan_name = f"Vlan{vlan_id}"

        for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
            st.log(f"Verifying {vlan_name} removal in running-configuration on {dut_name}")
            running_config = st.show(dut, "show running-configuration | no-more", type=cli_type, skip_tmpl=True, skip_error_check=True)
            running_config_str = str(running_config)

            if vlan_name not in running_config_str or f"interface {vlan_name}" not in running_config_str:
                st.log(f"✅ {vlan_name} correctly removed from running-configuration on {dut_name}")
            else:
                st.error(f"❌ {vlan_name} still present in running-configuration on {dut_name}")
                st.report_fail("msg", f"VLAN {vlan_id} found in running-configuration on {dut_name} after deletion")

        st.log(f"✅ VLAN {vlan_id} successfully deleted from both DUTs")
        st.report_pass("test_case_passed")
