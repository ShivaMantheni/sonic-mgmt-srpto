"""
Management Interface API for SpyTest test suites.

This module provides functions to interact with and verify Management interface
configurations, including IPv4 and IPv6 address retrieval and reachability testing.

Author: Shiva
Year: 2026
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from spytest import st
import apis.routing.ip as ip_api


def get_mgmt_interface_details_cli(
    dut: str,
    interface: str = "Management0",
    family: str = "ipv4",
    cli_type: str = "klish",
) -> Tuple[bool, Dict[str, str]]:
    """
    Get Management interface details using CLI command with grep.

    Args:
        dut: Device under test
        interface: Management interface name (default: Management0)
        family: Address family (ipv4, ipv6)
        cli_type: CLI type (klish, click)

    Returns:
        Tuple of (success: bool, details: dict)
        - success: True if interface found with IP address
        - details: Dictionary with ipaddr, status, and raw output

    Example:
        >>> success, details = get_mgmt_interface_details_cli("D1", "Management0", "ipv6")
        >>> if success:
        ...     print(f"IPv6: {details['ipaddr']}")
    """
    st.log(f"[MGMT-INTF] Getting {family} details for {interface} on {dut}")

    if family == "ipv6":
        command = f'show ipv6 interfaces | grep "NAME|{interface}"'
    else:
        command = f'show ip interfaces | grep "NAME|{interface}"'

    st.log(f"[MGMT-INTF] Executing command: {command}")

    # Execute command using st.show with skip_tmpl to get raw output
    output = st.show(
        dut,
        command,
        type=cli_type,
        skip_tmpl=True,
        skip_error_check=True,
    )

    # Normalize output to string
    if isinstance(output, list):
        output_text = "\n".join(str(line) for line in output)
    else:
        output_text = str(output) if output else ""

    st.log(f"[MGMT-INTF] Command output:\n{output_text}")

    if not output_text or interface not in output_text:
        st.log(f"[MGMT-INTF] Interface {interface} not found in output")
        return False, {
            "interface": interface,
            "output": output_text,
            "error": f"Interface {interface} not found",
        }

    # Parse the output to extract IP address
    # Expected format: Management0    192.168.100.121/24    up/up    ...
    # or: Management0    fe80::5054:ff:fed3:7935/64    up/up    ...
    lines = output_text.split("\n")
    for line in lines:
        if interface in line and "NAME" not in line:
            # Split by whitespace
            parts = line.split()
            if len(parts) >= 3:
                ip_with_mask = parts[1]  # Second column is IP address
                status = parts[2]  # Third column is status (up/up)

                st.log(f"[MGMT-INTF] Found {interface}: IP={ip_with_mask}, Status={status}")

                return True, {
                    "interface": interface,
                    "ipaddr": ip_with_mask,
                    "status": status,
                    "output": output_text,
                }

    st.log(f"[MGMT-INTF] Could not parse IP address from output")
    return False, {
        "interface": interface,
        "output": output_text,
        "error": "Could not parse IP address from output",
    }


def get_mgmt_interface_ipv4_address(
    dut: str,
    interface: str = "Management0",
    cli_type: str = "klish",
) -> Optional[str]:
    """
    Get IPv4 address of the Management interface.

    Args:
        dut: Device under test
        interface: Management interface name (default: Management0)
        cli_type: CLI type (klish, click)

    Returns:
        IPv4 address without mask (e.g., "192.168.100.121") or None if not found

    Example:
        >>> ipv4 = get_mgmt_interface_ipv4_address("D1", "Management0")
        >>> print(ipv4)  # "192.168.100.121"
    """
    st.log(f"[MGMT-INTF] Getting IPv4 address for {interface} on {dut}")

    # Use existing API to get interface IP address
    result = ip_api.get_interface_ip_address(
        dut,
        interface_name=interface,
        family="ipv4",
        cli_type=cli_type,
    )

    if not result:
        st.log(f"[MGMT-INTF] No IPv4 address found for {interface}")
        return None

    # Result is a list of dictionaries with 'ipaddr' key
    if isinstance(result, list) and len(result) > 0:
        # Get first IP address (remove mask if present)
        ip_with_mask = result[0].get("ipaddr", "")
        if "/" in ip_with_mask:
            ipv4_addr = ip_with_mask.split("/")[0]
        else:
            ipv4_addr = ip_with_mask

        st.log(f"[MGMT-INTF] Found IPv4 address: {ipv4_addr}")
        return ipv4_addr

    st.log(f"[MGMT-INTF] Could not parse IPv4 address from result: {result}")
    return None


def get_mgmt_interface_ipv6_address(
    dut: str,
    interface: str = "Management0",
    cli_type: str = "klish",
    link_local: bool = True,
) -> Optional[str]:
    """
    Get IPv6 address of the Management interface.

    Args:
        dut: Device under test
        interface: Management interface name (default: Management0)
        cli_type: CLI type (klish, click)
        link_local: If True, return link-local address (fe80::); otherwise global

    Returns:
        IPv6 address without mask (e.g., "fe80::5054:ff:fed3:7935") or None if not found

    Example:
        >>> ipv6 = get_mgmt_interface_ipv6_address("D1", "Management0")
        >>> print(ipv6)  # "fe80::5054:ff:fed3:7935"
    """
    st.log(f"[MGMT-INTF] Getting IPv6 address for {interface} on {dut}")

    # Use existing API to get interface IP address
    result = ip_api.get_interface_ip_address(
        dut,
        interface_name=interface,
        family="ipv6",
        cli_type=cli_type,
    )

    if not result:
        st.log(f"[MGMT-INTF] No IPv6 address found for {interface}")
        return None

    # Result is a list of dictionaries with 'ipaddr' key
    if isinstance(result, list):
        for entry in result:
            ip_with_mask = entry.get("ipaddr", "")
            if not ip_with_mask:
                continue

            # Remove mask if present
            if "/" in ip_with_mask:
                ipv6_addr = ip_with_mask.split("/")[0]
            else:
                ipv6_addr = ip_with_mask

            # Filter based on link-local or global
            is_link_local = ipv6_addr.lower().startswith("fe80:")

            if link_local and is_link_local:
                st.log(f"[MGMT-INTF] Found link-local IPv6 address: {ipv6_addr}")
                return ipv6_addr
            elif not link_local and not is_link_local:
                st.log(f"[MGMT-INTF] Found global IPv6 address: {ipv6_addr}")
                return ipv6_addr

    st.log(f"[MGMT-INTF] Could not find suitable IPv6 address. Link-local={link_local}")
    return None


def verify_mgmt_interface_status(
    dut: str,
    interface: str = "Management0",
    family: str = "ipv4",
    cli_type: str = "klish",
) -> Tuple[bool, Dict[str, str]]:
    """
    Verify Management interface status and address configuration.

    Args:
        dut: Device under test
        interface: Management interface name (default: Management0)
        family: Address family (ipv4, ipv6)
        cli_type: CLI type (klish, click)

    Returns:
        Tuple of (status_ok: bool, details: dict)
        - status_ok: True if interface is up and has IP address
        - details: Dictionary with status, ipaddr, and error info

    Example:
        >>> ok, details = verify_mgmt_interface_status("D1", "Management0", "ipv4")
        >>> if ok:
        ...     print(f"IPv4: {details['ipaddr']}")
    """
    st.log(f"[MGMT-INTF] Verifying {interface} status for {family} on {dut}")

    result = ip_api.get_interface_ip_address(
        dut,
        interface_name=interface,
        family=family,
        cli_type=cli_type,
    )

    if not result:
        return False, {
            "status": "down",
            "ipaddr": None,
            "error": f"No {family} configuration found on {interface}",
        }

    if isinstance(result, list) and len(result) > 0:
        entry = result[0]
        ipaddr = entry.get("ipaddr", "")
        status = entry.get("status", "").lower()

        # Check if interface is up
        if "up" in status or not status:
            st.log(f"[MGMT-INTF] Interface {interface} is UP with {family} address: {ipaddr}")
            return True, {
                "status": "up",
                "ipaddr": ipaddr,
                "interface": interface,
            }
        else:
            st.log(f"[MGMT-INTF] Interface {interface} status: {status}")
            return False, {
                "status": status,
                "ipaddr": ipaddr,
                "error": f"Interface {interface} is not UP",
            }

    return False, {
        "status": "unknown",
        "ipaddr": None,
        "error": f"Could not parse {family} interface status",
    }


def ping_mgmt_interface(
    dut: str,
    ip_address: str,
    family: str = "ipv4",
    count: int = 3,
    timeout: int = 10,
    cli_type: str = "klish",
) -> Tuple[bool, Dict[str, any]]:
    """
    Ping an IP address on the Management interface.

    Args:
        dut: Device under test
        ip_address: IP address to ping (without mask)
        family: Address family (ipv4, ipv6)
        count: Number of ping packets (default: 3)
        timeout: Timeout in seconds (default: 10)
        cli_type: CLI type (klish, click)

    Returns:
        Tuple of (success: bool, details: dict)
        - success: True if ping succeeds with 0% packet loss
        - details: Dictionary with transmitted, received, packet_loss, etc.

    Example:
        >>> success, details = ping_mgmt_interface("D1", "192.168.100.121", "ipv4")
        >>> if success:
        ...     print(f"Ping successful: {details['packet_loss']}% loss")
    """
    st.log(f"[MGMT-INTF] Pinging {family} address {ip_address} on {dut}")

    # Use existing ping API
    result = ip_api.ping(
        dut,
        addresses=ip_address,
        family=family,
        count=count,
        timeout=timeout,
        cli_type=cli_type,
    )

    if result:
        st.log(f"[MGMT-INTF] Ping to {ip_address} successful")
        return True, {
            "success": True,
            "ip_address": ip_address,
            "family": family,
            "packet_loss": 0,
        }
    else:
        st.log(f"[MGMT-INTF] Ping to {ip_address} failed")
        return False, {
            "success": False,
            "ip_address": ip_address,
            "family": family,
            "error": "Ping failed or packet loss detected",
        }


def ping_mgmt_interface_cli(
    dut: str,
    ip_address: str,
    family: str = "ipv4",
    count: int = 3,
    cli_type: str = "klish",
) -> Tuple[bool, Dict[str, any]]:
    """
    Ping an IP address using direct CLI command execution.

    Args:
        dut: Device under test
        ip_address: IP address to ping (without mask)
        family: Address family (ipv4, ipv6)
        count: Number of ping packets (default: 3)
        cli_type: CLI type (klish, click)

    Returns:
        Tuple of (success: bool, details: dict)
        - success: True if ping succeeds with 0% packet loss
        - details: Dictionary with output, packet_loss, etc.

    Example:
        >>> success, details = ping_mgmt_interface_cli("D1", "192.168.100.121", "ipv4", 3)
        >>> if success:
        ...     print("Ping successful with 0% packet loss")
    """
    st.log(f"[MGMT-INTF] Pinging {family} address {ip_address} on {dut} (CLI)")

    # Build ping command
    if family == "ipv6":
        command = f"ping6 {ip_address} -c {count}"
    else:
        command = f"ping {ip_address} -c {count}"

    st.log(f"[MGMT-INTF] Executing: {command}")

    # Execute ping command
    output = st.show(
        dut,
        command,
        type=cli_type,
        skip_tmpl=True,
        skip_error_check=True,
    )

    # Normalize output to string
    if isinstance(output, list):
        output_text = "\n".join(str(line) for line in output)
    else:
        output_text = str(output) if output else ""

    st.log(f"[MGMT-INTF] Ping output:\n{output_text}")

    # Parse output for packet loss
    # Pattern: "3 packets transmitted, 3 received, 0% packet loss"
    packet_loss_pattern = r'(\d+)\s+packets\s+transmitted,\s+(\d+)\s+received,.*?(\d+)%\s+packet\s+loss'
    match = re.search(packet_loss_pattern, output_text)

    if match:
        transmitted = int(match.group(1))
        received = int(match.group(2))
        packet_loss = int(match.group(3))

        st.log(f"[MGMT-INTF] Ping results: {transmitted} transmitted, {received} received, {packet_loss}% loss")

        if packet_loss == 0:
            return True, {
                "success": True,
                "ip_address": ip_address,
                "family": family,
                "transmitted": transmitted,
                "received": received,
                "packet_loss": packet_loss,
                "output": output_text,
            }
        else:
            return False, {
                "success": False,
                "ip_address": ip_address,
                "family": family,
                "transmitted": transmitted,
                "received": received,
                "packet_loss": packet_loss,
                "output": output_text,
                "error": f"{packet_loss}% packet loss detected",
            }
    else:
        st.log(f"[MGMT-INTF] Could not parse ping results from output")
        # Check for common error indicators
        if "unreachable" in output_text.lower() or "failed" in output_text.lower():
            return False, {
                "success": False,
                "ip_address": ip_address,
                "family": family,
                "output": output_text,
                "error": "Destination unreachable or ping failed",
            }

        # If we can't parse but there's output, consider it a failure
        return False, {
            "success": False,
            "ip_address": ip_address,
            "family": family,
            "output": output_text,
            "error": "Could not parse ping output",
        }
