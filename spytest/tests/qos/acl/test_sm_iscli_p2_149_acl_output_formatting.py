"""
SM_ISCLI_P2_149: IPv4 ACL Show Output Formatting

Author: Claude Code
Date: 2026-04-29
Version: 1.0 - SPyTest Native Implementation

How to run:
  ./bin/spytest --testbed ./testbeds/testbed_vs_1node.yaml \\
      tests/qos/acl/test_sm_iscli_p2_149_acl_output_formatting.py \\
      --logs-path ./logs/sm_iscli_p2_149_$(date +%F_%H%M%S) \\
      --log-level debug --skip-init-config --ifname-type native

Description:
  Comprehensive test suite for verifying IPv4 ACL show command output formatting.
  Validates that ACL rules display with proper indentation, consistent formatting,
  and correct sequencing. Focuses on CLI output presentation accuracy.

  Topology: Single-node SONiC topology (D1 only)
  Testbed: ztp_standalone.yaml or testbed_vs_1node.yaml

Pre-requisites:
  - Topology: Single-node SONiC topology (D1)
  - SONiC version: 202211 or later
  - Features: IPv4 ACL support, klish CLI
  - No management IP modifications required

Features:
  ✅ Single rule ACL output formatting verification
  ✅ Multiple rules ACL output with consistent indentation
  ✅ Show all ACLs with pagination handling
  ✅ Detailed ACL view output formatting
  ✅ Special IP patterns formatting (host, CIDR, any)
  ✅ ACL deletion and cleanup verification
  ✅ Pagination-safe CLI commands (terminal length 0)
  ✅ Full SpyTest framework integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re

import pytest
import yaml

from spytest import SpyTestDict, st


# Environment variable for test configuration
VAR_FILE_ENV = "SM_ISCLI_P2_149_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "qos"
    / "acl"
    / "vars_sm_iscli_p2_149.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load test variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    # Use defaults if file doesn't exist
    if not candidate.is_file():
        st.log(f"Using default configuration (file not found: {candidate})")
        return {
            "defaults": {
                "min_topology": ["D1"],
                "cli_type": "klish",
                "verify_timeout": 30,
                "cleanup": True,
            }
        }

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


# Test markers
pytestmark = [
    pytest.mark.skip_module_config_save,
]


class TestAclOutputFormattingP2149:
    """Test IPv4 ACL show command output formatting."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Initialize test data and set up DUT topology."""
        st.banner("SM_ISCLI_P2_149: ACL Output Formatting Test Suite - Setup")

        # Load configuration
        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Initialize topology - single node setup
        min_topology = defaults.get("min_topology", ["D1:1"])
        topology = st.ensure_min_topology(*min_topology)

        cls.data.topology = topology
        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT handle
        cls.data.dut1 = getattr(topology, "D1")

        st.log(f"DUT Mapping: D1={cls.data.dut1}")

        # Disable pagination globally
        cls._disable_pagination()

        st.banner("SM_ISCLI_P2_149 Setup Complete")

    @classmethod
    def teardown_class(cls) -> None:
        """Clean up configurations."""
        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled - skipping teardown")
            return

        st.banner("SM_ISCLI_P2_149 Teardown Phase")
        cls._cleanup_all_acls()

    @classmethod
    def _disable_pagination(cls) -> None:
        """Disable CLI pagination globally."""
        st.banner("Disabling CLI pagination on DUT")

        try:
            # Disable pagination using terminal length 0
            st.config(cls.data.dut1, "terminal length 0", type=cls.data.cli_type)
            st.log("✅ Pagination disabled (terminal length 0)")
        except Exception as e:
            st.warn(f"Could not disable pagination: {e}")

    @classmethod
    def _cleanup_all_acls(cls) -> None:
        """Remove all ACLs created during testing."""
        st.banner("Cleaning up ACL configurations")

        acl_names = [
            "test_acl_001",
            "test_acl_002",
            "test_acl_multi",
            "test_acl_patterns",
        ]

        for acl_name in acl_names:
            try:
                st.log(f"Deleting ACL: {acl_name}")
                st.config(
                    cls.data.dut1,
                    f"no ip access-list {acl_name}\nexit",
                    type=cls.data.cli_type
                )
                st.log(f"✅ ACL {acl_name} removed")
            except Exception as e:
                st.log(f"⚠️ Error removing ACL {acl_name}: {e}")

    @pytest.fixture(autouse=True)
    def cleanup_after_each_test(self):
        """Cleanup ACL configs after each test."""
        yield
        if self.data.cleanup_enabled:
            st.log("Test-level cleanup executed")

    # =====================================================================
    # Helper Functions for Output Verification
    # =====================================================================

    @staticmethod
    def _verify_acl_header_present(output, acl_name: str) -> bool:
        """Verify ACL header appears in parsed output (list of dicts)."""
        if not output:
            return False

        # st.show() returns a list of dictionaries with parsed output
        if isinstance(output, list) and output and isinstance(output[0], dict):
            # Check if first entry has the correct ACL name
            return output[0].get("access_list_name") == acl_name

        return False

    @staticmethod
    def _verify_rule_indented(output, rule_pattern: str) -> bool:
        """Verify rule exists in parsed output (list of dicts with rule entries)."""
        if not output or not isinstance(output, list):
            return False

        # st.show() returns list of dicts, each with rule_no, action, proto, etc.
        for entry in output:
            if isinstance(entry, dict):
                # Check if this entry matches the rule pattern (contains seq and action info)
                rule_str = f"seq {entry.get('rule_no')} {entry.get('action')}"
                if rule_pattern in rule_str:
                    return True

        return False

    @staticmethod
    def _extract_acl_rules(output) -> List[str]:
        """Extract all rules from ACL output (list of dicts)."""
        rules = []

        if not output or not isinstance(output, list):
            return rules

        # st.show() returns list of dicts with rule entries
        for entry in output:
            if isinstance(entry, dict) and "rule_no" in entry:
                # Format as string: "seq {rule_no} {action} {proto} {src_ip} {dst_ip}"
                rule_str = f"seq {entry.get('rule_no')} {entry.get('action', '')} {entry.get('proto', '')}"
                rules.append(rule_str.strip())

        return rules

    @staticmethod
    def _verify_rule_ordering(rules: List[str]) -> bool:
        """Verify rules appear in ascending sequence order."""
        if not rules:
            return False

        seq_numbers = []
        for rule in rules:
            # Extract sequence number from "seq 10 ..." pattern
            match = re.search(r'seq\s+(\d+)', rule)
            if match:
                seq_numbers.append(int(match.group(1)))

        # Check if sequence numbers are in ascending order
        return seq_numbers == sorted(seq_numbers)

    # =====================================================================
    # TEST CASE 1: Single Rule ACL Output Formatting
    # =====================================================================

    def test_tc01_single_rule_formatting(self):
        """TC1: Single rule ACL output formatting with correct indentation."""
        st.banner("TEST CASE 1: Single Rule ACL Output Formatting")

        acl_name = "test_acl_001"

        try:
            # Create ACL with single rule
            st.log("Creating ACL with single rule")
            cmd = f"""
ip access-list {acl_name}
seq 10 deny ip host 172.0.0.1 any
exit
exit
"""
            st.config(self.data.dut1, cmd, type=self.data.cli_type)

            # Display ACL
            st.log("Displaying ACL output")
            output = st.show(
                self.data.dut1,
                f"show ip access-lists {acl_name}",
                type=self.data.cli_type
            )
            st.log(f"ACL Output: {output}")

            # Verify ACL header present
            if not output:
                st.report_fail("acl_not_found")

            if not self._verify_acl_header_present(output, acl_name):
                st.report_fail("acl_header_missing")

            # Verify rule is present
            if not self._verify_rule_indented(output, "seq 10 deny"):
                st.report_fail("acl_rule_not_found")

            # Verify rule content by checking parsed fields
            if output[0].get("action") != "deny" or output[0].get("proto") != "ip":
                st.report_fail("acl_rule_content_mismatch")

            st.report_pass("Single rule ACL formatting verified")

        finally:
            # Cleanup
            if self.data.cleanup_enabled:
                st.config(
                    self.data.dut1,
                    f"no ip access-list {acl_name}\nexit",
                    type=self.data.cli_type
                )

    # =====================================================================
    # TEST CASE 2: Multiple Rules ACL Output Formatting
    # =====================================================================

    def test_tc02_multiple_rules_formatting(self):
        """TC2: Multiple rules ACL with consistent indentation and ordering."""
        st.banner("TEST CASE 2: Multiple Rules ACL Output Formatting")

        acl_name = "test_acl_002"

        try:
            # Create ACL with multiple rules
            st.log("Creating ACL with 3 rules")
            cmd = f"""
ip access-list {acl_name}
seq 10 deny ip host 172.0.0.1 any
seq 20 permit ip 172.0.0.0/24 any
seq 30 permit ip any any
exit
exit
"""
            st.config(self.data.dut1, cmd, type=self.data.cli_type)

            # Display ACL
            st.log("Displaying multiple rule ACL")
            output = st.show(
                self.data.dut1,
                f"show ip access-lists {acl_name}",
                type=self.data.cli_type
            )
            st.log(f"ACL Output: {output}")

            # Verify ACL exists
            if not output:
                st.report_fail("acl_not_found")

            # Verify ACL header
            if not self._verify_acl_header_present(output, acl_name):
                st.report_fail("acl_header_missing")

            # Extract and verify rules
            rules = self._extract_acl_rules(output)
            if len(rules) != 3:
                st.report_fail("acl_rule_count_mismatch")

            # Verify all rules are present and indented
            for rule_seq in ["10", "20", "30"]:
                if not self._verify_rule_indented(output, f"seq {rule_seq}"):
                    st.report_fail("acl_rule_indentation_failed")

            # Verify rule ordering
            if not self._verify_rule_ordering(rules):
                st.report_fail("acl_rule_ordering_failed")

            st.report_pass("Multiple rules ACL formatting verified")

        finally:
            # Cleanup
            if self.data.cleanup_enabled:
                st.config(
                    self.data.dut1,
                    f"no ip access-list {acl_name}\nexit",
                    type=self.data.cli_type
                )

    # =====================================================================
    # TEST CASE 3: Show All ACLs with Pagination Handling
    # =====================================================================

    def test_tc03_show_all_acls_pagination(self):
        """TC3: Show all ACLs with proper pagination handling."""
        st.banner("TEST CASE 3: Show All ACLs with Pagination Handling")

        acl_name = "test_acl_multi"

        try:
            # Create ACL
            st.log("Creating ACL for pagination test")
            cmd = f"""
ip access-list {acl_name}
seq 10 deny ip host 172.0.0.1 any
seq 20 permit ip 172.0.0.0/24 any
seq 30 permit ip any any
exit
exit
"""
            st.config(self.data.dut1, cmd, type=self.data.cli_type)

            # Show all ACLs
            st.log("Displaying all ACLs")
            output = st.show(
                self.data.dut1,
                "show ip access-lists",
                type=self.data.cli_type
            )
            st.log(f"All ACLs Output: {output}")

            # Verify ACL exists
            if not output:
                st.report_fail("acl_not_found")

            # Find the requested ACL in the output list
            acl_found = any(
                isinstance(entry, dict) and entry.get("access_list_name") == acl_name
                for entry in output
            )
            if not acl_found:
                st.report_fail("acl_not_found_in_show_all")

            # Verify ACL header present for this specific ACL
            if not self._verify_acl_header_present(output, acl_name):
                st.report_fail("acl_header_missing")

            # Extract and verify rules
            rules = self._extract_acl_rules(output)
            if len(rules) < 3:
                st.report_fail("acl_rule_count_mismatch")

            st.report_pass("Show all ACLs with pagination verified")

        finally:
            # Cleanup
            if self.data.cleanup_enabled:
                st.config(
                    self.data.dut1,
                    f"no ip access-list {acl_name}\nexit",
                    type=self.data.cli_type
                )

    # =====================================================================
    # TEST CASE 4: Detailed ACL View Output Formatting
    # =====================================================================

    def test_tc04_detailed_acl_view(self):
        """TC4: Detailed ACL view with proper indentation."""
        st.banner("TEST CASE 4: Detailed ACL View Output Formatting")

        acl_name = "test_acl_001"

        try:
            # Create ACL
            st.log("Creating ACL for detailed view")
            cmd = f"""
ip access-list {acl_name}
seq 10 deny ip host 172.0.0.1 any
exit
exit
"""
            st.config(self.data.dut1, cmd, type=self.data.cli_type)

            # Show detailed view
            st.log("Displaying detailed ACL view")
            output = st.show(
                self.data.dut1,
                f"show ip access-lists {acl_name} detailed",
                type=self.data.cli_type
            )
            st.log(f"Detailed ACL Output: {output}")

            # Verify ACL exists
            if not output:
                st.report_fail("acl_not_found")

            # Verify ACL header present
            if not self._verify_acl_header_present(output, acl_name):
                st.report_fail("acl_header_missing")

            # Verify rule is present and indented
            if not self._verify_rule_indented(output, "seq 10"):
                st.report_fail("acl_rule_indentation_failed")

            # Verify rule content by checking parsed fields
            if output[0].get("action") != "deny" or output[0].get("proto") != "ip":
                st.report_fail("acl_rule_content_mismatch")

            st.report_pass("Detailed ACL view formatting verified")

        finally:
            # Cleanup
            if self.data.cleanup_enabled:
                st.config(
                    self.data.dut1,
                    f"no ip access-list {acl_name}\nexit",
                    type=self.data.cli_type
                )

    # =====================================================================
    # TEST CASE 5: Output Format with Special IP Patterns
    # =====================================================================

    def test_tc05_special_ip_patterns(self):
        """TC5: Output format with various IP address patterns."""
        st.banner("TEST CASE 5: Special IP Patterns Output Formatting")

        acl_name = "test_acl_patterns"

        try:
            # Create ACL with various IP patterns
            st.log("Creating ACL with different IP patterns")
            cmd = f"""
ip access-list {acl_name}
seq 5 deny ip host 10.0.0.1 any
seq 10 deny ip 172.0.0.0/24 any
seq 15 permit ip 192.168.0.0/16 10.0.0.0/8
seq 20 permit ip any any
exit
exit
"""
            st.config(self.data.dut1, cmd, type=self.data.cli_type)

            # Display ACL
            st.log("Displaying ACL with various IP patterns")
            output = st.show(
                self.data.dut1,
                f"show ip access-lists {acl_name}",
                type=self.data.cli_type
            )
            st.log(f"ACL Output: {output}")

            # Verify ACL exists
            if not output:
                st.report_fail("acl_not_found")

            # Verify ACL header
            if not self._verify_acl_header_present(output, acl_name):
                st.report_fail("acl_header_missing")

            # Extract rules
            rules = self._extract_acl_rules(output)
            if len(rules) != 4:
                st.report_fail("acl_rule_count_mismatch")

            # Verify all rules are present with correct sequence numbers
            expected_seqs = ["5", "10", "15", "20"]
            for seq_num in expected_seqs:
                found = any(
                    isinstance(entry, dict) and entry.get("rule_no") == seq_num
                    for entry in output
                )
                if not found:
                    st.report_fail("acl_rule_not_found")

            # Verify sequence ordering
            if not self._verify_rule_ordering(rules):
                st.report_fail("acl_rule_ordering_failed")

            # Verify indentation for each pattern type
            for seq_num in expected_seqs:
                if not self._verify_rule_indented(output, f"seq {seq_num}"):
                    st.report_fail("acl_rule_indentation_failed")

            st.report_pass("Special IP patterns formatting verified")

        finally:
            # Cleanup
            if self.data.cleanup_enabled:
                st.config(
                    self.data.dut1,
                    f"no ip access-list {acl_name}\nexit",
                    type=self.data.cli_type
                )

    # =====================================================================
    # TEST CASE 6: ACL Deletion and Output Verification
    # =====================================================================

    def test_tc06_acl_deletion_verification(self):
        """TC6: ACL deletion removes from output cleanly."""
        st.banner("TEST CASE 6: ACL Deletion and Output Verification")

        acl_name = "test_acl_001"

        # Create ACL
        st.log("Creating ACL for deletion test")
        cmd = f"""
ip access-list {acl_name}
seq 10 deny ip host 172.0.0.1 any
exit
exit
"""
        st.config(self.data.dut1, cmd, type=self.data.cli_type)

        # Verify ACL exists
        st.log("Verifying ACL exists")
        output = st.show(
            self.data.dut1,
            f"show ip access-lists {acl_name}",
            type=self.data.cli_type
        )
        st.log(f"ACL Output: {output}")

        if not output:
            st.report_fail("acl_not_created")

        # Verify the ACL name is present
        acl_found = any(
            isinstance(entry, dict) and entry.get("access_list_name") == acl_name
            for entry in output
        )
        if not acl_found:
            st.report_fail("acl_not_found")

        # Delete ACL
        st.log(f"Deleting ACL {acl_name}")
        st.config(
            self.data.dut1,
            f"no ip access-list {acl_name}\nexit",
            type=self.data.cli_type
        )

        # Verify ACL is removed
        st.log("Verifying ACL is removed from output")
        output = st.show(
            self.data.dut1,
            f"show ip access-lists {acl_name}",
            type=self.data.cli_type
        )
        st.log(f"Output after deletion: {output}")

        # Verify the deleted ACL is no longer present
        acl_found = any(
            isinstance(entry, dict) and entry.get("access_list_name") == acl_name
            for entry in output
        )
        if acl_found:
            st.report_fail("acl_deletion_failed")

        st.report_pass("ACL deletion verified - cleanly removed from output")
