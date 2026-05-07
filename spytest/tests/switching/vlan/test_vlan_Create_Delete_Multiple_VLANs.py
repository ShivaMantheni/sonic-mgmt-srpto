"""
TC_VLAN_CREATE_002: Create Multiple VLANs
TC_VLAN_DELETE_001: Delete Single VLAN

Author: Test Automation Team
Date: 2026-05-07

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_vs_2node_vlan.yaml \\
  tests/switching/vlan/test_vlan_Create_Multiple_VLANs.py \\
  --logs-path ./logs/vlan_create_multiple_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Comprehensive validation of multiple VLAN creation and deletion using SpyTest APIs
  and klish CLI. Tests verify creation of VLANs 10, 20, 30, 40, and 50 on both DUTs.

  TC_VLAN_CREATE_002: Create Multiple VLANs
    Objective: Verify multiple VLAN creation
    Steps:
      1. Create VLANs 10, 20, 30, 40, 50
      2. Execute show running-config to verify all VLANs exist
      3. Verify all VLANs appear in VLAN database
    Expected Result: All VLANs are created successfully

  TC_VLAN_DELETE_001: Delete Single VLAN
    Objective: Verify single VLAN deletion
    Steps:
      1. Create VLAN 100
      2. Verify VLAN 100 exists
      3. Delete VLAN 100
      4. Verify VLAN 100 is deleted
    Expected Result: VLAN is deleted successfully

Pre-requisites:
  - Topology: Two DUTs (D1-D2) with 2+ connections | Supported: HW and Virtual
  - Feature flags / min SONiC version: VLAN support required
  - Required test variables (YAML): spytest/vars/switching/vlan/vars_vlan_create_multiple.yaml
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.switching.vlan as vlan_api
import apis.system.interface as intf_api

VAR_FILE_ENV = "VLAN_CREATE_MULTIPLE_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "spytest/vars/switching/vlan/vars_vlan_create_multiple.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        st.warn(f"VLAN variable file not found: {candidate}, using defaults")
        return {
            "defaults": {"cli_type": "klish", "vlans": [10, 20, 30, 40, 50]},
            "testcases": {},
        }

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


@pytest.mark.topology("D1D2:2")
class TestVlanCreateMultiple:
    """Testcases covering multiple VLAN creation and deletion operations."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and testcase variables for the suite."""
        st.banner("=" * 90)
        st.banner("VLAN CREATE/DELETE TEST SUITE - SETUP")
        st.banner("=" * 90)

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

        # VLANs to create
        cls.data.vlans_to_create = defaults.get("vlans", [10, 20, 30, 40, 50])

        # Get DUT handles from topology (dynamically from testbed)
        cls.data.dut1 = topology.D1
        cls.data.dut2 = topology.D2
        cls.data.dut_names = st.get_dut_names()

        # Get ports from topology dynamically
        cls.data.d1d2p1 = topology.D1D2P1
        cls.data.d2d1p1 = topology.D2D1P1

        st.log(f"✅ DUT1 (D1) for testing: {cls.data.dut1}")
        st.log(f"✅ DUT2 (D2) for testing: {cls.data.dut2}")
        st.log(f"✅ D1→D2 Port 1: {cls.data.d1d2p1}")
        st.log(f"✅ D2→D1 Port 1: {cls.data.d2d1p1}")
        st.log(f"✅ VLANs to create: {cls.data.vlans_to_create}")
        st.log(f"✅ CLI Type: {cls.data.cli_type}")

        # Clear any existing IP/VLAN configurations on test ports
        cls._clear_interface_config()

        # Pre-test cleanup - ensure VLANs used in tests don't exist
        cls._cleanup_test_vlans()

        st.banner("✅ SETUP COMPLETE - Ready for testing")

    @classmethod
    def _clear_interface_config(cls) -> None:
        """Clear any existing VLAN or IP configuration on test interfaces."""
        st.banner("CLEARING INTERFACE CONFIGURATIONS")

        for dut_name, dut, port in [
            ("D1", cls.data.dut1, cls.data.d1d2p1),
            ("D2", cls.data.dut2, cls.data.d2d1p1)
        ]:
            st.log(f"Clearing config on {dut_name} port {port}")
            try:
                # Check if port has any IP addresses
                output = st.show(dut, f"show ip interface {port}",
                               type=cls.data.cli_type, skip_error_check=True, skip_tmpl=True)
                if output and "IP Address" in str(output):
                    st.log(f"  - Removing IP configuration from {port}")
                    st.config(dut, f"interface {port}\nno ip address", type=cls.data.cli_type)

                # Check if port is in a VLAN
                output = st.show(dut, f"show vlan members {port}",
                               type=cls.data.cli_type, skip_error_check=True, skip_tmpl=True)
                if output:
                    st.log(f"  - Removing VLAN membership from {port}")
                    st.config(dut, f"interface {port}\nno switchport access vlan", type=cls.data.cli_type)

                st.log(f"✅ {dut_name} interface {port} cleared")
            except Exception as e:
                st.log(f"⚠️  Exception clearing {dut_name} port {port}: {e}")

    @classmethod
    def _cleanup_test_vlans(cls) -> None:
        """Cleanup VLANs that will be used in tests before starting."""
        st.banner("PRE-TEST CLEANUP - REMOVING TEST VLANS")

        dut1 = cls.data.dut1
        dut2 = cls.data.dut2
        cli_type = cls.data.cli_type
        vlans_to_delete = cls.data.vlans_to_create + [100]  # Include test VLAN 100

        for vlan_id in vlans_to_delete:
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    vlan_api.delete_vlan(dut, str(vlan_id), cli_type=cli_type,
                                        skip_error_report=True, remove_vlan_mapping=False)
                    st.log(f"✅ Pre-cleanup: VLAN {vlan_id} removed from {dut_name} (if existed)")
                except Exception as e:
                    st.log(f"⚠️  Pre-cleanup exception VLAN {vlan_id} on {dut_name}: {e}")

        st.log("✅ Pre-test cleanup completed")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup all VLANs after test suite completes."""
        st.banner("=" * 90)
        st.banner("VLAN CREATE/DELETE TEST SUITE - CLEANUP")
        st.banner("=" * 90)

        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        dut1 = cls.data.dut1
        dut2 = cls.data.dut2
        cli_type = cls.data.cli_type

        st.log("Removing all VLAN configurations...")
        for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
            try:
                vlan_list = vlan_api.get_vlan_list(dut, cli_type=cli_type)
                if vlan_list:
                    st.log(f"Cleaning up VLANs on {dut_name}: {vlan_list}")
                    for vlan in vlan_list:
                        if str(vlan) != "1":  # Don't delete default VLAN
                            try:
                                vlan_api.delete_vlan(dut, str(vlan), cli_type=cli_type,
                                                   skip_error_report=True, remove_vlan_mapping=False)
                                st.log(f"  ✅ Deleted VLAN {vlan} from {dut_name}")
                            except Exception as e:
                                st.log(f"  ⚠️  Failed to delete VLAN {vlan} on {dut_name}: {e}")
            except Exception as e:
                st.log(f"Cleanup exception on {dut_name}: {e}")

        st.log("✅ Cleanup completed")

    def _print_step_result(self, step_num: int, step_name: str, passed: bool) -> None:
        """Print formatted step result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        st.log(f"\n{'='*80}")
        st.log(f"STEP {step_num}: {step_name} - {status}")
        st.log(f"{'='*80}")

    def _verify_vlan_exists(self, dut: str, dut_name: str, vlan_id: str) -> bool:
        """Verify if a VLAN exists on device using multiple methods."""
        cli_type = self.data.cli_type
        all_passed = True

        st.log(f"\nVerifying VLAN {vlan_id} on {dut_name}...")

        # Method 1: show Vlan <id>
        try:
            output = st.show(dut, f"show Vlan {vlan_id}", type=cli_type,
                           skip_tmpl=True, skip_error_check=True)
            output_str = str(output)
            if f"Vlan{vlan_id}" in output_str or f"VLAN {vlan_id}" in output_str:
                st.log(f"  ✅ 'show Vlan {vlan_id}' - FOUND")
            else:
                st.log(f"  ❌ 'show Vlan {vlan_id}' - NOT FOUND")
                all_passed = False
        except Exception as e:
            st.log(f"  ❌ 'show Vlan {vlan_id}' exception: {e}")
            all_passed = False

        # Method 2: show running-config grep
        try:
            cmd = f"show running-configuration | grep -i vlan{vlan_id}"
            output = st.show(dut, cmd, type=cli_type, skip_tmpl=True, skip_error_check=True)
            if output and len(str(output)) > 5:
                st.log(f"  ✅ Running-config grep - FOUND")
            else:
                st.log(f"  ⚠️  Running-config grep - NOT FOUND (may be new VLAN)")
        except Exception as e:
            st.log(f"  ⚠️  Running-config grep exception: {e}")

        # Method 3: VLAN database
        try:
            vlan_list = vlan_api.get_vlan_list(dut, cli_type=cli_type)
            if vlan_id in [str(v) for v in vlan_list]:
                st.log(f"  ✅ VLAN database - FOUND")
            else:
                st.log(f"  ❌ VLAN database - NOT FOUND")
                all_passed = False
        except Exception as e:
            st.log(f"  ❌ VLAN database check exception: {e}")
            all_passed = False

        return all_passed

    def _verify_vlan_deleted(self, dut: str, dut_name: str, vlan_id: str) -> bool:
        """Verify if a VLAN is successfully deleted."""
        cli_type = self.data.cli_type
        all_passed = True

        st.log(f"\nVerifying VLAN {vlan_id} deletion on {dut_name}...")

        # Check if VLAN still exists in database
        try:
            vlan_list = vlan_api.get_vlan_list(dut, cli_type=cli_type)
            if vlan_id not in [str(v) for v in vlan_list]:
                st.log(f"  ✅ VLAN {vlan_id} successfully deleted from database")
            else:
                st.log(f"  ❌ VLAN {vlan_id} still exists in database")
                all_passed = False
        except Exception as e:
            st.log(f"  ❌ VLAN database check exception: {e}")
            all_passed = False

        # Verify using show Vlan command
        try:
            output = st.show(dut, f"show Vlan {vlan_id}", type=cli_type,
                           skip_tmpl=True, skip_error_check=True)
            output_str = str(output)
            if "not found" in output_str.lower() or "%" in output_str:
                st.log(f"  ✅ 'show Vlan {vlan_id}' - NOT FOUND (deleted)")
            else:
                st.log(f"  ❌ 'show Vlan {vlan_id}' - Still exists")
                all_passed = False
        except Exception as e:
            st.log(f"  ⚠️  'show Vlan' exception (expected): {e}")

        return all_passed

    @pytest.mark.inventory(feature="VLAN_Basic", testcases=["TC_VLAN_CREATE_002"])
    def test_vlan_create_multiple(self) -> None:
        """
        TC_VLAN_CREATE_002: Create Multiple VLANs

        Objective: Verify multiple VLAN creation (VLANs 10, 20, 30, 40, 50)

        Steps:
            1. Create VLANs 10, 20, 30, 40, 50 on both DUTs
            2. Execute show running-config to verify all VLANs exist
            3. Verify all VLANs appear in VLAN database on both DUTs

        Expected Result: All VLANs are created successfully
        """
        st.banner("=" * 90)
        st.banner("TC_VLAN_CREATE_002: Create Multiple VLANs")
        st.banner("=" * 90)

        dut1 = self.data.dut1
        dut2 = self.data.dut2
        cli_type = self.data.cli_type
        vlans_to_create = self.data.vlans_to_create

        # Track results
        test_results = {
            "step_1": False,  # Create VLANs
            "step_2": False,  # Verify running-config
            "step_3": False,  # Verify VLAN database
        }

        try:
            # STEP 1: Create VLANs 10, 20, 30, 40, 50 on both DUTs
            st.log("\n" + "=" * 80)
            st.log("STEP 1: Creating VLANs on both DUTs")
            st.log("=" * 80)

            step_passed = True
            for vlan_id in vlans_to_create:
                for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                    try:
                        st.log(f"Creating VLAN {vlan_id} on {dut_name}...")
                        result = vlan_api.create_vlan(dut, str(vlan_id), cli_type=cli_type)
                        if result:
                            st.log(f"  ✅ VLAN {vlan_id} created on {dut_name}")
                        else:
                            st.log(f"  ❌ VLAN {vlan_id} creation failed on {dut_name}")
                            step_passed = False
                    except Exception as e:
                        st.log(f"  ❌ VLAN {vlan_id} creation exception on {dut_name}: {e}")
                        step_passed = False

            test_results["step_1"] = step_passed
            self._print_step_result(1, "Create VLANs", step_passed)

            if not step_passed:
                st.report_fail("msg", "STEP 1 FAILED: Failed to create one or more VLANs")

            # STEP 2: Execute show running-config to verify all VLANs exist
            st.log("\n" + "=" * 80)
            st.log("STEP 2: Verifying all VLANs in running-config")
            st.log("=" * 80)

            step_passed = True
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                st.log(f"\nVerifying running-config on {dut_name}...")
                try:
                    output = st.show(dut, "show running-configuration | no-more", type=cli_type,
                                   skip_tmpl=True, skip_error_check=True)
                    output_str = str(output).lower()

                    for vlan_id in vlans_to_create:
                        if f"vlan {vlan_id}" in output_str:
                            st.log(f"  ✅ VLAN {vlan_id} found in running-config")
                        else:
                            st.log(f"  ❌ VLAN {vlan_id} NOT found in running-config")
                            step_passed = False
                except Exception as e:
                    st.log(f"  ❌ Running-config verification exception: {e}")
                    step_passed = False

            test_results["step_2"] = step_passed
            self._print_step_result(2, "Verify running-config", step_passed)

            # STEP 3: Verify all VLANs appear in VLAN database
            st.log("\n" + "=" * 80)
            st.log("STEP 3: Verifying all VLANs in VLAN database")
            st.log("=" * 80)

            step_passed = True
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                st.log(f"\nVerifying VLAN database on {dut_name}...")
                try:
                    vlan_list = vlan_api.get_vlan_list(dut, cli_type=cli_type)
                    vlan_list_str = [str(v) for v in vlan_list]
                    st.log(f"  Current VLANs on {dut_name}: {vlan_list_str}")

                    for vlan_id in vlans_to_create:
                        if str(vlan_id) in vlan_list_str:
                            st.log(f"  ✅ VLAN {vlan_id} found in database")
                        else:
                            st.log(f"  ❌ VLAN {vlan_id} NOT found in database")
                            step_passed = False
                except Exception as e:
                    st.log(f"  ❌ VLAN database check exception: {e}")
                    step_passed = False

            test_results["step_3"] = step_passed
            self._print_step_result(3, "Verify VLAN database", step_passed)

            # Overall result
            st.log("\n" + "=" * 90)
            st.log("TC_VLAN_CREATE_002: TEST SUMMARY")
            st.log("=" * 90)
            st.log(f"STEP 1 (Create VLANs):        {'✅ PASS' if test_results['step_1'] else '❌ FAIL'}")
            st.log(f"STEP 2 (Verify running-config): {'✅ PASS' if test_results['step_2'] else '❌ FAIL'}")
            st.log(f"STEP 3 (Verify VLAN database):  {'✅ PASS' if test_results['step_3'] else '❌ FAIL'}")

            overall_passed = all(test_results.values())
            overall_status = "✅ PASSED" if overall_passed else "❌ FAILED"
            st.log(f"\nOVERALL RESULT: {overall_status}")
            st.log("=" * 90)

            if overall_passed:
                st.report_pass("test_case_passed")
            else:
                st.report_fail("msg", "TC_VLAN_CREATE_002 FAILED: One or more steps failed")

        except Exception as e:
            st.log(f"\n❌ TEST EXCEPTION: {e}")
            st.report_fail("msg", f"TC_VLAN_CREATE_002 EXCEPTION: {e}")

        finally:
            # Cleanup - always remove created VLANs
            st.log("\n" + "=" * 80)
            st.log("CLEANUP: Removing all created VLANs")
            st.log("=" * 80)

            for vlan_id in vlans_to_create:
                for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                    try:
                        vlan_api.delete_vlan(dut, str(vlan_id), cli_type=cli_type)
                        st.log(f"  ✅ VLAN {vlan_id} deleted from {dut_name}")
                    except Exception as e:
                        st.log(f"  ⚠️  Failed to delete VLAN {vlan_id} from {dut_name}: {e}")

    @pytest.mark.inventory(feature="VLAN_Basic", testcases=["TC_VLAN_DELETE_001"])
    def test_vlan_delete_single(self) -> None:
        """
        TC_VLAN_DELETE_001: Delete Single VLAN

        Objective: Verify single VLAN deletion

        Steps:
            1. Create VLAN 100 on both DUTs
            2. Verify VLAN 100 exists on both DUTs
            3. Delete VLAN 100 from both DUTs
            4. Verify VLAN 100 is deleted from both DUTs

        Expected Result: VLAN is deleted successfully
        """
        st.banner("=" * 90)
        st.banner("TC_VLAN_DELETE_001: Delete Single VLAN")
        st.banner("=" * 90)

        dut1 = self.data.dut1
        dut2 = self.data.dut2
        cli_type = self.data.cli_type
        test_vlan = "100"

        # Track results
        test_results = {
            "step_1": False,  # Create VLAN
            "step_2": False,  # Verify creation
            "step_3": False,  # Delete VLAN
            "step_4": False,  # Verify deletion
        }

        try:
            # STEP 1: Create VLAN 100 on both DUTs
            st.log("\n" + "=" * 80)
            st.log(f"STEP 1: Creating VLAN {test_vlan} on both DUTs")
            st.log("=" * 80)

            step_passed = True
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    st.log(f"Creating VLAN {test_vlan} on {dut_name}...")
                    result = vlan_api.create_vlan(dut, test_vlan, cli_type=cli_type)
                    if result:
                        st.log(f"  ✅ VLAN {test_vlan} created on {dut_name}")
                    else:
                        st.log(f"  ❌ VLAN {test_vlan} creation failed on {dut_name}")
                        step_passed = False
                except Exception as e:
                    st.log(f"  ❌ VLAN {test_vlan} creation exception on {dut_name}: {e}")
                    step_passed = False

            test_results["step_1"] = step_passed
            self._print_step_result(1, f"Create VLAN {test_vlan}", step_passed)

            if not step_passed:
                st.report_fail("msg", f"STEP 1 FAILED: Failed to create VLAN {test_vlan}")

            # STEP 2: Verify VLAN 100 exists on both DUTs
            st.log("\n" + "=" * 80)
            st.log(f"STEP 2: Verifying VLAN {test_vlan} exists on both DUTs")
            st.log("=" * 80)

            step_passed = True
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                if self._verify_vlan_exists(dut, dut_name, test_vlan):
                    st.log(f"  ✅ VLAN {test_vlan} verified on {dut_name}")
                else:
                    st.log(f"  ❌ VLAN {test_vlan} verification failed on {dut_name}")
                    step_passed = False

            test_results["step_2"] = step_passed
            self._print_step_result(2, f"Verify VLAN {test_vlan} exists", step_passed)

            if not step_passed:
                st.report_fail("msg", f"STEP 2 FAILED: VLAN {test_vlan} verification failed")

            # STEP 3: Delete VLAN 100 from both DUTs
            st.log("\n" + "=" * 80)
            st.log(f"STEP 3: Deleting VLAN {test_vlan} from both DUTs")
            st.log("=" * 80)

            step_passed = True
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    st.log(f"Deleting VLAN {test_vlan} from {dut_name}...")
                    vlan_api.delete_vlan(dut, test_vlan, cli_type=cli_type)
                    st.log(f"  ✅ VLAN {test_vlan} deleted from {dut_name}")
                except Exception as e:
                    st.log(f"  ❌ VLAN {test_vlan} deletion exception on {dut_name}: {e}")
                    step_passed = False

            test_results["step_3"] = step_passed
            self._print_step_result(3, f"Delete VLAN {test_vlan}", step_passed)

            # STEP 4: Verify VLAN 100 is deleted from both DUTs
            st.log("\n" + "=" * 80)
            st.log(f"STEP 4: Verifying VLAN {test_vlan} is deleted on both DUTs")
            st.log("=" * 80)

            step_passed = True
            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                if self._verify_vlan_deleted(dut, dut_name, test_vlan):
                    st.log(f"  ✅ VLAN {test_vlan} deletion verified on {dut_name}")
                else:
                    st.log(f"  ❌ VLAN {test_vlan} still exists on {dut_name}")
                    step_passed = False

            test_results["step_4"] = step_passed
            self._print_step_result(4, f"Verify VLAN {test_vlan} deleted", step_passed)

            # Overall result
            st.log("\n" + "=" * 90)
            st.log("TC_VLAN_DELETE_001: TEST SUMMARY")
            st.log("=" * 90)
            st.log(f"STEP 1 (Create VLAN):           {'✅ PASS' if test_results['step_1'] else '❌ FAIL'}")
            st.log(f"STEP 2 (Verify creation):       {'✅ PASS' if test_results['step_2'] else '❌ FAIL'}")
            st.log(f"STEP 3 (Delete VLAN):           {'✅ PASS' if test_results['step_3'] else '❌ FAIL'}")
            st.log(f"STEP 4 (Verify deletion):       {'✅ PASS' if test_results['step_4'] else '❌ FAIL'}")

            overall_passed = all(test_results.values())
            overall_status = "✅ PASSED" if overall_passed else "❌ FAILED"
            st.log(f"\nOVERALL RESULT: {overall_status}")
            st.log("=" * 90)

            if overall_passed:
                st.report_pass("test_case_passed")
            else:
                st.report_fail("msg", "TC_VLAN_DELETE_001 FAILED: One or more steps failed")

        except Exception as e:
            st.log(f"\n❌ TEST EXCEPTION: {e}")
            st.report_fail("msg", f"TC_VLAN_DELETE_001 EXCEPTION: {e}")

        finally:
            # Cleanup - ensure VLAN 100 is removed
            st.log("\n" + "=" * 80)
            st.log(f"CLEANUP: Removing VLAN {test_vlan}")
            st.log("=" * 80)

            for dut_name, dut in [("D1", dut1), ("D2", dut2)]:
                try:
                    vlan_api.delete_vlan(dut, test_vlan, cli_type=cli_type)
                    st.log(f"  ✅ VLAN {test_vlan} cleaned up from {dut_name}")
                except Exception as e:
                    st.log(f"  ⚠️  Cleanup exception for VLAN {test_vlan} on {dut_name}: {e}")


# Export test class for pytest discovery
__all__ = ["TestVlanCreateMultiple"]
