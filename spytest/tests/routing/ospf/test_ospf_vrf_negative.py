"""
OSPF VRF NEGATIVE TESTING
Author: Shiva
2026

How to run:
  ./bin/spytest  --tryssh 1  \\
  --testbed ./testbeds/ztp_standalone.yaml  \\
  tests/routing/ospf/test_ospf_vrf_negative.py \\
  --logs-path ./logs/ospf_vrf_negative_$(date +%F_%H%M%S) \\
  --log-level debug  --skip-init-config  --ifname-type native

Description:
  Negative test suite for OSPF VRF configuration validation. This test verifies
  that SONiC correctly rejects attempts to configure OSPF routing processes on
  non-existent VRFs with appropriate error messages. The test ensures the system
  maintains configuration integrity by preventing orphaned OSPF instances tied
  to invalid VRF contexts.

  Test validates:
  - OSPF configuration rejection when VRF does not exist
  - Correct error message format and content
  - System stability after rejected configuration attempt

Pre-requisites:
  - Topology: standalone (single DUT) | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 1 node (standalone)
        # +--------------------+
        # |    smic_sonic1     |
        # | (192.168.100.121)  |
        # |   Ethernet16       |
        # +--------------------+

  - Feature: OSPF routing with VRF support
  - Min SONiC version: Any version supporting IS-CLI (klish)
  - Required test variables (YAML): spytest/vars/routing/ospf/vars_ospf_vrf_negative.yaml
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.routing.ospf_vrf as ospf_vrf_api
import apis.routing.vrf as vrf_api

# Environment variable for custom variable file location
VAR_FILE_ENV = "OSPF_VRF_NEGATIVE_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "routing"
    / "ospf"
    / "vars_ospf_vrf_negative.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        raise FileNotFoundError(f"OSPF VRF negative variable file not found: {candidate}")

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    if "testcases" not in content:
        raise ValueError("OSPF VRF negative YAML must contain key 'testcases'")

    return content


@pytest.mark.topology("any")
class TestOspfVrfNegative:
    """Negative testcases for OSPF VRF configuration validation."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Collect topology handles and testcase variables for the suite."""
        st.banner("OSPF VRF NEGATIVE TEST SUITE - SETUP")

        # Load configuration from YAML
        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Ensure minimum topology requirement
        min_topology = defaults.get("min_topology") or ["D1"]
        topology = st.ensure_min_topology(*min_topology)

        # Store configuration data
        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))

        # CLI type configuration
        cli_type = defaults.get("cli_type", "klish")
        cls.data.cli_type = cli_type

        # Get DUT handle
        cls.data.dut_names = st.get_dut_names()
        if not cls.data.dut_names:
            st.report_fail("msg", "No DUT available for testing")

        cls.data.dut = cls.data.dut_names[0]
        st.log(f"Using DUT: {cls.data.dut}")

        # Test parameters
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        st.log(f"CLI Type: {cls.data.cli_type}")
        st.log(f"Verify Timeout: {cls.data.verify_timeout}")
        st.log(f"Cleanup Enabled: {cls.data.cleanup_enabled}")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after all tests complete."""
        st.banner("OSPF VRF NEGATIVE TEST SUITE - TEARDOWN")
        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled, skipping teardown")
            return

        # No specific cleanup needed for negative tests as configurations should fail
        st.log("Teardown complete")

    def setup_method(self) -> None:
        """Reset per-test state."""
        st.banner("TEST CASE SETUP")

    def teardown_method(self) -> None:
        """Cleanup after each test."""
        st.banner("TEST CASE TEARDOWN")

    def _get_testcase(self, tcid: str) -> Mapping[str, Any]:
        """Helper to fetch testcase definition from YAML."""
        testcase = self.data.testcases.get(tcid)
        if not testcase:
            st.report_fail("msg", f"Missing testcase definition for {tcid} in YAML")
        return testcase

    @pytest.mark.inventory(feature="Regression", testcases=["SONIC-OSPF-VRF-NEG-001"])
    @pytest.mark.negative
    def test_ospf_config_nonexistent_vrf(self) -> None:
        """
        TC SONIC-OSPF-VRF-NEG-001: Verify OSPF configuration rejection for non-existent VRF.

        Test Steps:
        1. Verify the target VRF does not exist on the device
        2. Attempt to configure OSPF router for the non-existent VRF
        3. Verify the configuration is rejected with correct error message
        4. Verify system stability (no crash or unexpected behavior)

        Pass Criteria:
        - CLI rejects the configuration attempt
        - Error message matches expected pattern: "%Error: VRF <vrf_name> does not exist"
        - System remains stable after rejected configuration

        Fail Criteria:
        - Configuration is accepted without error
        - System crashes or throws unhandled exception
        - Incorrect or misleading error message
        """
        st.banner("TEST CASE: OSPF Configuration with Non-Existent VRF")

        # Get test case configuration
        testcase = self._get_testcase("SONIC-OSPF-VRF-NEG-001")
        vrf_name = testcase.get("vrf_name", "Vrftest")
        expected_error = testcase.get("expected_error", "%Error: VRF Vrftest does not exist")
        expected_error_pattern = testcase.get(
            "expected_error_pattern",
            "(?i)error.*vrf.*does not exist"
        )

        dut = self.data.dut
        cli_type = self.data.cli_type

        st.log(f"Test Parameters:")
        st.log(f"  DUT: {dut}")
        st.log(f"  VRF Name: {vrf_name}")
        st.log(f"  CLI Type: {cli_type}")
        st.log(f"  Expected Error: {expected_error}")

        # Step 1: Verify VRF does not exist
        st.banner("STEP 1: Verify VRF Does Not Exist")
        st.log(f"Checking if VRF '{vrf_name}' exists on {dut}")

        vrf_exists = vrf_api.verify_vrf(
            dut,
            vrfname=vrf_name,
            cli_type=cli_type,
        )

        if vrf_exists:
            st.log(f"VRF '{vrf_name}' already exists, cleaning it up for test")
            # Note: In a real scenario, we might want to fail here or use a different VRF name
            st.report_fail(
                "msg",
                f"Pre-condition failed: VRF '{vrf_name}' already exists on {dut}. "
                f"Please use a non-existent VRF name for this negative test."
            )
        else:
            st.log(f"Confirmed: VRF '{vrf_name}' does not exist (as expected)")

        # Step 2: Attempt OSPF configuration on non-existent VRF
        st.banner("STEP 2: Attempt OSPF Configuration on Non-Existent VRF")
        st.log(f"Attempting to configure: router ospf vrf {vrf_name}")

        # Execute command directly to capture output properly
        command = f"router ospf vrf {vrf_name}"
        st.log(f"Executing command: {command}")

        # Use st.config with skip_error_check=True to capture the error message
        config_kwargs = {"type": cli_type, "skip_error_check": True}
        response = st.config(dut, command, **config_kwargs)

        # Normalize response to string
        if response is None:
            cli_output = ""
        elif isinstance(response, (list, tuple)):
            cli_output = "\n".join(str(item) for item in response)
        else:
            cli_output = str(response)

        st.log(f"Configuration result - CLI Output: {cli_output}")

        # Step 3: Verify configuration was rejected
        st.banner("STEP 3: Verify Configuration Rejection")

        # Check if output contains error message
        has_error = any(
            indicator in cli_output.lower()
            for indicator in ["error", "does not exist", "not found"]
        )

        if not has_error:
            # This is a failure - configuration should have been rejected
            st.error("FAIL: Configuration was accepted when it should have been rejected")
            st.report_fail(
                "msg",
                f"OSPF configuration for non-existent VRF '{vrf_name}' was incorrectly "
                f"accepted by the system. Expected rejection with error message. "
                f"Output received: {cli_output}"
            )

        matched, message = ospf_vrf_api.verify_ospf_vrf_error(
            dut,
            vrf_name=vrf_name,
            expected_error_pattern=expected_error_pattern,
            cli_output=cli_output,
        )

        if not matched:
            st.error(f"FAIL: Error message validation failed: {message}")
            st.report_fail(
                "msg",
                f"OSPF configuration was rejected (correct) but error message did not match "
                f"expected pattern. Expected: '{expected_error}' or pattern '{expected_error_pattern}'. "
                f"Received: '{cli_output}'"
            )

        st.log(f"PASS: Error message validation successful: {message}")

        # Step 4: Verify system stability
        st.banner("STEP 4: Verify System Stability")
        st.log("Checking system stability after rejected configuration")

        # Verify VRF list is still accessible (system is responsive)
        try:
            vrf_check = vrf_api.verify_vrf(
                dut,
                vrfname="default",
                cli_type=cli_type,
            )
            if vrf_check:
                st.log("System is stable and responsive")
            else:
                st.log("Default VRF check returned unexpected result, but system is responsive")
        except Exception as exc:
            st.error(f"System stability check failed: {exc}")
            st.report_fail(
                "msg",
                f"System became unstable after rejected OSPF VRF configuration: {exc}"
            )

        # Final result
        st.banner("TEST RESULT: PASS")
        st.log(
            f"Successfully verified that OSPF configuration for non-existent VRF '{vrf_name}' "
            f"was rejected with correct error message"
        )
        st.report_pass("test_case_passed")
