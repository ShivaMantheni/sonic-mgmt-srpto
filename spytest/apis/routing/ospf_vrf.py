"""
OSPF VRF configuration and verification API for SpyTest test suites.

This module provides functions to configure and verify OSPF routing instances
associated with VRFs, including negative testing support.

Author: Shiva
Year: 2026
"""

from __future__ import annotations

import re
from typing import Dict, Tuple

from spytest import st
from apis.routing import ospf


def configure_ospf_router_vrf(
    dut: str,
    vrf_name: str,
    cli_type: str = "klish",
    skip_error_check: bool = False,
) -> Tuple[bool, Dict[str, str]]:
    """
    Configure OSPF router instance for a specific VRF.

    Args:
        dut: Device under test
        vrf_name: VRF name to associate with OSPF
        cli_type: CLI type (klish, click, vtysh)
        skip_error_check: If True, ignore CLI errors (for negative testing)

    Returns:
        Tuple of (success: bool, details: dict)
        - success: True if command executed without error
        - details: Dictionary containing command, output, and error info

    Example:
        >>> success, details = configure_ospf_router_vrf("D1", "Vrftest", skip_error_check=False)
        >>> if not success:
        ...     print(f"Error: {details['output']}")
    """
    st.log(f"[OSPF-VRF] Configuring OSPF router for VRF '{vrf_name}' on {dut}")

    if cli_type == "klish":
        command = f"router ospf vrf {vrf_name}"
    elif cli_type == "vtysh":
        command = f"router ospf vrf {vrf_name}"
    elif cli_type == "click":
        st.error("[OSPF-VRF] Click CLI does not support OSPF VRF configuration")
        return False, {
            "command": "N/A",
            "output": "Click CLI does not support OSPF VRF configuration",
            "dut": dut,
        }
    else:
        st.error(f"[OSPF-VRF] Unsupported CLI type: {cli_type}")
        return False, {
            "command": "N/A",
            "output": f"Unsupported CLI type: {cli_type}",
            "dut": dut,
        }

    # Use the existing apply_cli_sequence function from ospf module
    success, details = ospf.apply_cli_sequence(
        dut,
        [command],
        cli_type=cli_type,
        skip_error_check=skip_error_check,
    )

    return success, details


def verify_ospf_vrf_error(
    dut: str,
    vrf_name: str,
    expected_error_pattern: str,
    cli_output: str,
) -> Tuple[bool, str]:
    """
    Verify that the CLI output contains the expected error message for OSPF VRF configuration.

    Args:
        dut: Device under test
        vrf_name: VRF name that was attempted
        expected_error_pattern: Regular expression pattern to match against error output
        cli_output: The actual CLI output received

    Returns:
        Tuple of (matched: bool, message: str)
        - matched: True if expected error pattern found in output
        - message: Descriptive message about the match result

    Example:
        >>> matched, msg = verify_ospf_vrf_error("D1", "Vrftest", "(?i)error.*vrf.*does not exist", output)
        >>> if matched:
        ...     print(f"Expected error found: {msg}")
    """
    st.log(f"[OSPF-VRF] Verifying error message for VRF '{vrf_name}' on {dut}")
    st.log(f"[OSPF-VRF] Expected pattern: {expected_error_pattern}")
    st.log(f"[OSPF-VRF] CLI output: {cli_output}")

    if not cli_output:
        return False, "No CLI output received"

    # Check for exact match first
    if expected_error_pattern in cli_output:
        st.log(f"[OSPF-VRF] Exact match found for expected error")
        return True, f"Expected error message found: {expected_error_pattern}"

    # Try regex pattern matching
    try:
        pattern = re.compile(expected_error_pattern, re.IGNORECASE | re.MULTILINE)
        match = pattern.search(cli_output)
        if match:
            st.log(f"[OSPF-VRF] Pattern match found: {match.group(0)}")
            return True, f"Expected error pattern matched: {match.group(0)}"
    except re.error as exc:
        st.error(f"[OSPF-VRF] Invalid regex pattern: {exc}")
        return False, f"Invalid regex pattern: {exc}"

    # Check for common error indicators
    error_indicators = [
        "error",
        "fail",
        "invalid",
        "does not exist",
        "not found",
        "unknown",
    ]

    output_lower = cli_output.lower()
    found_indicators = [ind for ind in error_indicators if ind in output_lower]

    if found_indicators:
        st.log(f"[OSPF-VRF] Error indicators found: {found_indicators}")
        return False, (
            f"CLI returned an error but did not match expected pattern. "
            f"Output: {cli_output[:200]}"
        )

    return False, f"Expected error not found. Output: {cli_output[:200]}"


def unconfigure_ospf_router_vrf(
    dut: str,
    vrf_name: str,
    cli_type: str = "klish",
    skip_error_check: bool = True,
) -> Tuple[bool, Dict[str, str]]:
    """
    Remove OSPF router instance for a specific VRF.

    Args:
        dut: Device under test
        vrf_name: VRF name associated with OSPF
        cli_type: CLI type (klish, click, vtysh)
        skip_error_check: If True, ignore CLI errors during cleanup

    Returns:
        Tuple of (success: bool, details: dict)

    Example:
        >>> success, details = unconfigure_ospf_router_vrf("D1", "Vrftest")
    """
    st.log(f"[OSPF-VRF] Removing OSPF router for VRF '{vrf_name}' on {dut}")

    if cli_type == "klish":
        command = f"no router ospf vrf {vrf_name}"
    elif cli_type == "vtysh":
        command = f"no router ospf vrf {vrf_name}"
    elif cli_type == "click":
        st.warn("[OSPF-VRF] Click CLI does not support OSPF VRF unconfiguration")
        return True, {}
    else:
        st.warn(f"[OSPF-VRF] Unsupported CLI type for cleanup: {cli_type}")
        return True, {}

    success, details = ospf.apply_cli_sequence(
        dut,
        [command],
        cli_type=cli_type,
        skip_error_check=skip_error_check,
    )

    return success, details
