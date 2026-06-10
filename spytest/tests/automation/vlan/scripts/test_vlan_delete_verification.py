"""
VLAN DELETION VERIFICATION - TC_VLAN_DELETE_001
Author: Shiva
2026

How to run:
  ./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_1d_spine02.yaml \
  tests/switching/vlan/test_vlan_delete_verification.py \
  --logs-path ./logs/vlan_delete_verify_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native

Description:
  Focused test case to verify VLAN deletion using show running-config command.
  This test creates VLAN 100, verifies its existence, deletes it, and confirms
  removal by checking running-configuration output.

Test Case:
  TC_VLAN_DELETE_001: Delete Single VLAN
  - Create VLAN 100
  - Verify VLAN 100 exists
  - Delete VLAN 100
  - Execute show running-config to verify VLAN 100 is removed

Pre-requisites:
  - Topology: Single DUT (spine02) | Supported: HW and Virtual
  - Device: spine02 (192.168.100.75)
  - Feature flags: VLAN support, klish CLI
  - Testbed: testbed_1d_spine02.yaml
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api

# Test configuration
TC_ID = "TC_VLAN_DELETE_001"
TEST_VLAN_ID = "100"
DEFAULT_CLI_TYPE = "klish"


@pytest.mark.topology("D1")
class TestVlanDeleteVerification:
    """Test case for VLAN deletion verification using running-config."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Setup test environment and collect topology handles."""
        st.banner(f"{TC_ID}: VLAN Deletion Verification - Setup")

        # Get single DUT topology
        topology = st.ensure_min_topology("D1")
        cls.data.topology = topology
        cls.data.dut = topology.D1
        cls.data.cli_type = DEFAULT_CLI_TYPE

        st.log(f"DUT for testing: {cls.data.dut} (spine02)")
        st.log(f"CLI Type: {cls.data.cli_type}")

        # Pre-test cleanup - ensure VLAN 100 doesn't exist
        st.log(f"Pre-test cleanup: Removing VLAN {TEST_VLAN_ID} if it exists")
        try:
            vlan_api.delete_vlan(
                cls.data.dut,
                TEST_VLAN_ID,
                cli_type=cls.data.cli_type,
                skip_error_report=True,
                remove_vlan_mapping=False
            )
            st.log(f"✓ Pre-cleanup completed for VLAN {TEST_VLAN_ID}")
        except Exception as e:
            st.log(f"Pre-cleanup exception (non-fatal): {e}")

        st.banner(f"{TC_ID}: Setup Complete")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup test environment."""
        st.banner(f"{TC_ID}: Cleanup")

        # Ensure VLAN 100 is removed
        try:
            vlan_api.delete_vlan(
                cls.data.dut,
                TEST_VLAN_ID,
                cli_type=cls.data.cli_type,
                skip_error_report=True,
                remove_vlan_mapping=False
            )
            st.log(f"✓ Cleanup: VLAN {TEST_VLAN_ID} removed")
        except Exception as e:
            st.log(f"Cleanup exception (non-fatal): {e}")

    def _verify_vlan_exists(self, vlan_id: str) -> bool:
        """
        Verify VLAN exists using show Vlan command.

        Args:
            vlan_id: VLAN ID to verify

        Returns:
            True if VLAN exists, False otherwise
        """
        dut = self.data.dut
        cli_type = self.data.cli_type
        vlan_name = f"Vlan{vlan_id}"

        st.log(f"Verifying VLAN {vlan_id} exists using 'show Vlan {vlan_id}'")

        try:
            output = st.show(dut, f"show Vlan {vlan_id}", type=cli_type, skip_tmpl=True, skip_error_check=True)
            output_str = str(output)

            if vlan_name in output_str or vlan_id in output_str:
                st.log(f"✓ VLAN {vlan_id} exists")
                return True
            else:
                st.log(f"✗ VLAN {vlan_id} does not exist")
                return False
        except Exception as e:
            st.log(f"Exception while verifying VLAN {vlan_id}: {e}")
            return False

    def _verify_vlan_in_running_config(self, vlan_id: str, should_exist: bool = True) -> bool:
        """
        Verify VLAN presence in running-configuration.

        Args:
            vlan_id: VLAN ID to verify
            should_exist: True if VLAN should exist, False if it should not

        Returns:
            True if verification passes, False otherwise
        """
        dut = self.data.dut
        cli_type = self.data.cli_type
        vlan_name = f"Vlan{vlan_id}"

        st.log(f"Verifying VLAN {vlan_id} in running-configuration (should_exist={should_exist})")

        try:
            # Execute show running-configuration with no-more to avoid pagination
            output = st.show(dut, "show running-configuration | no-more", type=cli_type, skip_tmpl=True, skip_error_check=True)
            output_str = str(output)

            # Log first 500 characters for debugging
            st.log(f"Running-config output (first 500 chars): {output_str[:500]}")

            # Check for VLAN interface configuration
            vlan_interface_pattern = f"interface {vlan_name}"
            vlan_found = vlan_interface_pattern in output_str or vlan_name in output_str

            if should_exist:
                if vlan_found:
                    st.log(f"✓ VLAN {vlan_id} found in running-configuration")
                    st.log(f"  Pattern matched: {vlan_interface_pattern}")
                    return True
                else:
                    st.error(f"✗ VLAN {vlan_id} NOT found in running-configuration (but should exist)")
                    return False
            else:
                # VLAN should NOT exist
                if not vlan_found:
                    st.log(f"✓ VLAN {vlan_id} correctly NOT in running-configuration")
                    return True
                else:
                    st.error(f"✗ VLAN {vlan_id} still in running-configuration (but should be deleted)")
                    st.log(f"  Found pattern: {vlan_interface_pattern}")
                    return False

        except Exception as e:
            st.error(f"Exception while checking running-configuration: {e}")
            return False

    @pytest.mark.inventory(feature="VLAN_Basic", testcases=[TC_ID])
    def test_vlan_delete_verification(self) -> None:
        """
        TC_VLAN_DELETE_001: Delete Single VLAN

        Objective: Verify VLAN deletion using running-configuration
        Steps:
        1. Create VLAN 100
        2. Verify VLAN 100 exists (using show Vlan 100)
        3. Verify VLAN 100 in running-configuration (should exist)
        4. Delete VLAN 100
        5. Verify VLAN 100 is removed from running-configuration

        Expected Result: VLAN 100 is deleted successfully
        """
        st.banner(f"{TC_ID}: Delete Single VLAN {TEST_VLAN_ID}")

        dut = self.data.dut
        cli_type = self.data.cli_type
        vlan_id = TEST_VLAN_ID

        # STEP 1: Create VLAN 100
        st.banner("STEP 1: Creating VLAN 100")
        st.log(f"Creating VLAN {vlan_id} using VLAN API")
        result = vlan_api.create_vlan(dut, vlan_id, cli_type=cli_type)
        if not result:
            st.report_fail("msg", f"Failed to create VLAN {vlan_id}")
        st.log(f"✓ VLAN {vlan_id} created successfully")

        # STEP 2: Verify VLAN 100 exists
        st.banner("STEP 2: Verifying VLAN 100 exists")
        vlan_exists = self._verify_vlan_exists(vlan_id)
        if not vlan_exists:
            st.report_fail("msg", f"VLAN {vlan_id} not found after creation")
        st.log(f"✓ VLAN {vlan_id} verified to exist")

        # STEP 3: Verify VLAN 100 in running-configuration (should exist)
        st.banner("STEP 3: Verifying VLAN 100 in running-configuration (before deletion)")
        config_before = self._verify_vlan_in_running_config(vlan_id, should_exist=True)
        if not config_before:
            st.report_fail("msg", f"VLAN {vlan_id} not found in running-configuration (but should exist)")
        st.log(f"✓ VLAN {vlan_id} confirmed in running-configuration")

        # STEP 4: Delete VLAN 100
        st.banner("STEP 4: Deleting VLAN 100")
        st.log(f"Deleting VLAN {vlan_id} using VLAN API")
        result = vlan_api.delete_vlan(dut, vlan_id, cli_type=cli_type)
        if not result:
            st.report_fail("msg", f"Failed to delete VLAN {vlan_id}")
        st.log(f"✓ VLAN {vlan_id} deleted successfully")

        # STEP 5: Verify VLAN 100 is removed from running-configuration
        st.banner("STEP 5: Verifying VLAN 100 is removed from running-configuration")
        config_after = self._verify_vlan_in_running_config(vlan_id, should_exist=False)
        if not config_after:
            st.report_fail("msg", f"VLAN {vlan_id} still in running-configuration after deletion")
        st.log(f"✓ VLAN {vlan_id} confirmed removed from running-configuration")

        # Test passed
        st.banner(f"{TC_ID}: TEST PASSED")
        st.log("=" * 80)
        st.log(f"| {TC_ID}: VLAN Deletion Verification - SUCCESS")
        st.log("=" * 80)
        st.log(f"✓ VLAN {vlan_id} created successfully")
        st.log(f"✓ VLAN {vlan_id} verified in running-configuration (before deletion)")
        st.log(f"✓ VLAN {vlan_id} deleted successfully")
        st.log(f"✓ VLAN {vlan_id} confirmed removed from running-configuration")
        st.log("=" * 80)

        st.report_pass("test_case_passed")
