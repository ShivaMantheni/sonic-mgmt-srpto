"""
LACP API Module - Safe wrapper for PortChannel operations

Author: Athira, 2026

This module provides a safe wrapper around the portchannel API with automatic
type normalization to prevent inet_pton() and other type errors. It accepts
both integer IDs and string names for PortChannel operations.

Key Features:
- Accepts portchannel as int (1), str ("1"), or full name ("PortChannel1")
- Automatically normalizes inputs to prevent type errors
- Provides consistent interface for all LACP/PortChannel operations
- Wraps underlying portchannel.py APIs with safer interfaces

Usage Example:
    import apis.switching.lacp as lacp_api

    # All of these work:
    lacp_api.create_lacp_portchannel(dut, 1)
    lacp_api.create_lacp_portchannel(dut, "1")
    lacp_api.create_lacp_portchannel(dut, "PortChannel1")

    lacp_api.add_lacp_member(dut, 1, ["Ethernet32", "Ethernet36"])
    lacp_api.delete_lacp_portchannel(dut, 1)
"""

from spytest import st
import apis.switching.portchannel as pc_api
import utilities.utils as utils


def normalize_portchannel_name(portchannel):
    """
    Convert various portchannel formats to standard "PortChannelN" format.

    This function ensures that regardless of how the PortChannel is specified
    (as an integer, string number, or full name), it's converted to the proper
    format expected by the underlying APIs.

    Args:
        portchannel: Can be:
            - int: 1, 2, 100, etc.
            - str (number): "1", "2", "100"
            - str (full name): "PortChannel1", "PortChannel2"
            - list: Will process each element

    Returns:
        str: Normalized PortChannel name (e.g., "PortChannel1")
        list: If input was a list, returns list of normalized names

    Examples:
        >>> normalize_portchannel_name(1)
        'PortChannel1'
        >>> normalize_portchannel_name("1")
        'PortChannel1'
        >>> normalize_portchannel_name("PortChannel1")
        'PortChannel1'
        >>> normalize_portchannel_name([1, 2, "3"])
        ['PortChannel1', 'PortChannel2', 'PortChannel3']
    """
    # Handle list input
    if isinstance(portchannel, list):
        return [normalize_portchannel_name(pc) for pc in portchannel]

    # Handle integer input
    if isinstance(portchannel, int):
        return f"PortChannel{portchannel}"

    # Handle string input
    if isinstance(portchannel, str):
        # Already in correct format
        if portchannel.startswith("PortChannel"):
            return portchannel

        # String number like "1", "2", "100"
        if portchannel.isdigit():
            return f"PortChannel{portchannel}"

        # Try to extract number from formats like "Po1", "PC1", etc.
        import re
        match = re.search(r'(\d+)', portchannel)
        if match:
            return f"PortChannel{match.group(1)}"

    # Fallback: convert to string
    st.warn(f"Unusual portchannel format: {portchannel}, converting to string")
    return str(portchannel)


def create_lacp_portchannel(dut, portchannel_list=[], fallback=False, min_link="", static=None, cli_type="", **kwargs):
    """
    Create PortChannel with automatic ID normalization.

    This is a safe wrapper around portchannel.create_portchannel() that accepts
    various input formats and normalizes them before passing to the underlying API.

    Args:
        dut: Device Under Test
        portchannel_list: PortChannel ID(s) - int, str, or list of either
        fallback: Enable fallback mode (bool)
        min_link: Minimum links for PortChannel to be up (str)
        static: Create static PortChannel (bool). Default: None (omit flag, uses LACP)
        cli_type: CLI type (click, klish, rest-patch, rest-put)
        **kwargs: Additional arguments passed to underlying API

    Returns:
        bool: True if successful, False otherwise

    Examples:
        >>> create_lacp_portchannel(dut, 1)
        >>> create_lacp_portchannel(dut, [1, 2, 3])
        >>> create_lacp_portchannel(dut, "PortChannel1", min_link="2")

    Note:
        static parameter defaults to None (not False) to avoid --static flag
        on SONiC versions that don't support it. Omitting the flag creates
        LACP (dynamic) PortChannel by default.
    """
    normalized_list = normalize_portchannel_name(utils.make_list(portchannel_list))
    st.log(f"Creating PortChannel(s): {normalized_list}", dut=dut)

    # Only pass static parameter if explicitly set to True
    # Omitting it (None/False) avoids --static flag on unsupported versions
    if static is True:
        return pc_api.create_portchannel(
            dut,
            portchannel_list=normalized_list,
            fallback=fallback,
            min_link=min_link,
            static=True,
            cli_type=cli_type,
            **kwargs
        )
    else:
        # Don't pass static parameter - let API use default (LACP mode)
        return pc_api.create_portchannel(
            dut,
            portchannel_list=normalized_list,
            fallback=fallback,
            min_link=min_link,
            cli_type=cli_type,
            **kwargs
        )


def delete_lacp_portchannel(dut, portchannel_list, **kwargs):
    """
    Delete PortChannel with automatic ID normalization.

    Safe wrapper that prevents inet_pton() errors by ensuring proper string format.

    Args:
        dut: Device Under Test
        portchannel_list: PortChannel ID(s) - int, str, or list of either
        **kwargs: Additional arguments (cli_type, skip_error, etc.)

    Returns:
        bool: True if successful, False otherwise

    Examples:
        >>> delete_lacp_portchannel(dut, 1)
        >>> delete_lacp_portchannel(dut, [1, 2, 3], cli_type="klish")
    """
    normalized_list = normalize_portchannel_name(utils.make_list(portchannel_list))
    st.log(f"Deleting PortChannel(s): {normalized_list}", dut=dut)

    return pc_api.delete_portchannel(dut, normalized_list, **kwargs)


def add_lacp_member(dut, portchannel, members, cli_type="", **kwargs):
    """
    Add member(s) to PortChannel with automatic ID normalization.

    Args:
        dut: Device Under Test
        portchannel: PortChannel ID - int, str, or full name
        members: List of member interfaces (e.g., ["Ethernet32", "Ethernet36"])
        cli_type: CLI type
        **kwargs: Additional arguments (skip_error_check, etc.)

    Returns:
        bool: True if successful, False otherwise

    Examples:
        >>> add_lacp_member(dut, 1, ["Ethernet32", "Ethernet36"])
        >>> add_lacp_member(dut, "PortChannel1", ["Ethernet32"], cli_type="klish")
        >>> add_lacp_member(dut, 1, ["Ethernet32"], skip_error_check=True)
    """
    normalized_pc = normalize_portchannel_name(portchannel)
    st.log(f"Adding members {members} to {normalized_pc}", dut=dut)

    return pc_api.add_portchannel_member(
        dut,
        portchannel=normalized_pc,
        members=members,
        cli_type=cli_type,
        **kwargs
    )


def delete_lacp_member(dut, portchannel, members, cli_type="", **kwargs):
    """
    Remove member(s) from PortChannel with automatic ID normalization.

    Args:
        dut: Device Under Test
        portchannel: PortChannel ID - int, str, or full name
        members: List of member interfaces to remove
        cli_type: CLI type
        **kwargs: Additional arguments (skip_error_check, etc.)

    Returns:
        bool: True if successful, False otherwise

    Examples:
        >>> delete_lacp_member(dut, 1, ["Ethernet32"])
        >>> delete_lacp_member(dut, "PortChannel1", ["Ethernet36"], cli_type="klish")
        >>> delete_lacp_member(dut, 1, ["Ethernet32"], skip_error_check=True)
    """
    normalized_pc = normalize_portchannel_name(portchannel)
    st.log(f"Removing members {members} from {normalized_pc}", dut=dut)

    return pc_api.delete_portchannel_member(
        dut,
        portchannel=normalized_pc,
        members=members,
        cli_type=cli_type,
        **kwargs
    )


def verify_lacp_portchannel(dut, portchannel_name, cli_type="", **kwargs):
    """
    Verify PortChannel configuration with automatic ID normalization.

    Args:
        dut: Device Under Test
        portchannel_name: PortChannel ID - int, str, or full name
        cli_type: CLI type
        **kwargs: Additional verification parameters

    Returns:
        bool: True if verification passes, False otherwise

    Examples:
        >>> verify_lacp_portchannel(dut, 1, state="up")
        >>> verify_lacp_portchannel(dut, "PortChannel1", protocol="LACP")
    """
    normalized_pc = normalize_portchannel_name(portchannel_name)
    st.log(f"Verifying PortChannel: {normalized_pc}", dut=dut)

    return pc_api.verify_portchannel(
        dut,
        portchannel_name=normalized_pc,
        cli_type=cli_type,
        **kwargs
    )


def get_lacp_portchannel(dut, portchannel_name="", cli_type="", **kwargs):
    """
    Get PortChannel information with automatic ID normalization.

    Args:
        dut: Device Under Test
        portchannel_name: PortChannel ID - int, str, or full name (empty for all)
        cli_type: CLI type
        **kwargs: Additional parameters

    Returns:
        list: PortChannel information

    Examples:
        >>> get_lacp_portchannel(dut)  # Get all PortChannels
        >>> get_lacp_portchannel(dut, 1)  # Get specific PortChannel
    """
    if portchannel_name:
        normalized_pc = normalize_portchannel_name(portchannel_name)
        st.log(f"Getting PortChannel info: {normalized_pc}", dut=dut)
    else:
        normalized_pc = ""
        st.log("Getting all PortChannel info", dut=dut)

    return pc_api.get_portchannel(
        dut,
        portchannel_name=normalized_pc,
        cli_type=cli_type,
        **kwargs
    )


def verify_lacp_portchannel_state(dut, portchannel, state="up", error_msg=True, cli_type=""):
    """
    Verify PortChannel state with automatic ID normalization.

    Args:
        dut: Device Under Test
        portchannel: PortChannel ID - int, str, or full name
        state: Expected state ("up" or "down")
        error_msg: Show error message if verification fails (bool)
        cli_type: CLI type

    Returns:
        bool: True if state matches, False otherwise

    Examples:
        >>> verify_lacp_portchannel_state(dut, 1, state="up")
        >>> verify_lacp_portchannel_state(dut, "PortChannel1", state="down")
    """
    normalized_pc = normalize_portchannel_name(portchannel)
    st.log(f"Verifying {normalized_pc} state: {state}", dut=dut)

    return pc_api.verify_portchannel_state(
        dut,
        portchannel=normalized_pc,
        state=state,
        error_msg=error_msg,
        cli_type=cli_type
    )


def verify_lacp_member(dut, portchannel, members, flag='add', cli_type="", **kwargs):
    """
    Verify PortChannel member status with automatic ID normalization.

    Args:
        dut: Device Under Test
        portchannel: PortChannel ID - int, str, or full name
        members: List of member interfaces to verify
        flag: 'add' or 'del' - check if members are added or deleted
        cli_type: CLI type
        **kwargs: Additional verification parameters

    Returns:
        bool: True if verification passes, False otherwise

    Examples:
        >>> verify_lacp_member(dut, 1, ["Ethernet32"], flag='add')
        >>> verify_lacp_member(dut, "PortChannel1", ["Ethernet36"], flag='del')
    """
    normalized_pc = normalize_portchannel_name(portchannel)
    st.log(f"Verifying members {members} in {normalized_pc} (flag={flag})", dut=dut)

    return pc_api.verify_portchannel_member(
        dut,
        portchannel=normalized_pc,
        members=members,
        flag=flag,
        cli_type=cli_type,
        **kwargs
    )


def config_lacp_portchannel(dut1, dut2, portchannel_name, members_dut1, members_dut2, config='add', thread=True, cli_type=""):
    """
    Configure PortChannel on both DUTs with automatic ID normalization.

    Args:
        dut1: First Device Under Test
        dut2: Second Device Under Test
        portchannel_name: PortChannel ID - int, str, or full name
        members_dut1: List of member interfaces on dut1
        members_dut2: List of member interfaces on dut2
        config: 'add' or 'del'
        thread: Use threading for parallel configuration (bool)
        cli_type: CLI type

    Returns:
        bool: True if successful, False otherwise

    Examples:
        >>> config_lacp_portchannel(dut1, dut2, 1,
        ...     ["Ethernet32"], ["Ethernet32"], config='add')
    """
    normalized_pc = normalize_portchannel_name(portchannel_name)
    st.log(f"Configuring {normalized_pc} on both DUTs (config={config})")

    return pc_api.config_portchannel(
        dut1, dut2,
        portchannel_name=normalized_pc,
        members_dut1=members_dut1,
        members_dut2=members_dut2,
        config=config,
        thread=thread,
        cli_type=cli_type
    )


def clear_lacp_configuration(dut_list, thread=True, cli_type=""):
    """
    Clear all PortChannel configuration from device(s).

    Args:
        dut_list: Single DUT or list of DUTs
        thread: Use threading for parallel operation (bool)
        cli_type: CLI type

    Returns:
        None

    Examples:
        >>> clear_lacp_configuration(dut)
        >>> clear_lacp_configuration([dut1, dut2], thread=True)
    """
    st.log("Clearing all PortChannel configuration")

    return pc_api.clear_portchannel_configuration(
        dut_list,
        thread=thread,
        cli_type=cli_type
    )


def get_lacp_portchannel_list(dut, cli_type=""):
    """
    Get list of all PortChannels on device.

    Args:
        dut: Device Under Test
        cli_type: CLI type

    Returns:
        list: List of PortChannel information

    Examples:
        >>> pc_list = get_lacp_portchannel_list(dut)
    """
    st.log("Getting list of all PortChannels", dut=dut)

    return pc_api.get_portchannel_list(dut, cli_type=cli_type)


def get_lacp_portchannel_names(dut, cli_type=''):
    """
    Get list of PortChannel names on device.

    Args:
        dut: Device Under Test
        cli_type: CLI type

    Returns:
        list: List of PortChannel names

    Examples:
        >>> names = get_lacp_portchannel_names(dut)
        >>> print(names)
        ['PortChannel1', 'PortChannel2']
    """
    st.log("Getting PortChannel names", dut=dut)

    return pc_api.get_portchannel_names(dut, cli_type=cli_type)


# Backwards compatibility aliases (for tests that may use alternate naming)
create_portchannel = create_lacp_portchannel
delete_portchannel = delete_lacp_portchannel
add_portchannel_member = add_lacp_member
delete_portchannel_member = delete_lacp_member
verify_portchannel = verify_lacp_portchannel
verify_portchannel_state = verify_lacp_portchannel_state
verify_portchannel_member = verify_lacp_member
