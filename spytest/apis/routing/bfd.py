"""
BFD (Bidirectional Forwarding Detection) configuration and verification helpers for SpyTest test suites.

These utilities provide lightweight wrappers around SpyTest's CLI helpers so testcases can
push BFD configuration snippets and validate SONiC CLI outputs without re-implementing
common parsing logic.

Author: SPyTest BFD Feature Team
Created: 2026
"""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

from spytest import st
from utilities.common import make_list

__all__ = [
    "enable_bfd",
    "disable_bfd",
    "configure_bfd_peer",
    "remove_bfd_peer",
    "configure_bfd_peer_params",
    "configure_bfd_slow_timer",
    "configure_bfd_profile",
    "remove_bfd_profile",
    "apply_bfd_profile_to_peer",
    "show_bfd_config",
    "show_bfd_peers",
    "show_bfd_peer",
    "show_bfd_profile",
    "verify_bfd_peer_up",
    "verify_bfd_session_down",
    "get_bfd_peer_status",
    "apply_cli_sequence",
    "collect_cli_output",
    "check_cli_expectations",
]


def _normalize_command_sequence(commands: Union[List[str], str, None]) -> List[str]:
    """Return a sanitized list of CLI commands, dropping null or empty entries."""
    normalized: List[str] = []
    for entry in make_list(commands):
        if entry is None:
            continue
        line = str(entry).strip()
        if line:
            normalized.append(line)
    return normalized


def apply_cli_sequence(
    dut: str,
    commands: Union[List[str], str, None],
    cli_type: str = "klish",
    skip_error_check: bool = False,
) -> Tuple[bool, Dict[str, str]]:
    """
    Execute each command in ``commands`` on the given ``dut``.

    Returns ``True`` when all commands run without raising an exception. When any
    command fails, the function logs the error and returns ``False`` so tests can
    react accordingly.

    :param dut: Device Under Test
    :param commands: CLI commands to execute
    :param cli_type: CLI type (klish, click, vtysh)
    :param skip_error_check: Skip error checking
    :return: Tuple of (success_bool, error_details_dict)
    """
    sequence = _normalize_command_sequence(commands)
    if not sequence:
        st.log(f"[BFD] No commands to apply on {dut}")
        return True, {}

    def _normalize_response(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            return "\n".join(str(item) for item in value)
        return str(value)

    def _has_cli_error(text: str) -> bool:
        lowered = text.lower()
        return any(
            token in lowered
            for token in (
                "% error",
                "invalid input",
                "unknown command",
                "unrecognized command",
                "not found",
                "unsupported",
                "incomplete command",
            )
        )

    st.log(f"[BFD] Applying CLI sequence on {dut} via {cli_type}: {sequence}")
    try:
        for command in sequence:
            config_kwargs = {
                "type": cli_type,
                "skip_error_check": skip_error_check,
            }
            if cli_type == "vtysh":
                config_kwargs["conf"] = True

            response = st.config(
                dut,
                command,
                **config_kwargs,
            )
            text = _normalize_response(response)
            if text and _has_cli_error(text):
                st.error(
                    f"[BFD] CLI rejected '{command}' on {dut}: {text.strip()}"
                )
                return False, {
                    "command": command,
                    "output": text,
                    "dut": dut,
                }
    except Exception as exc:  # pylint: disable=broad-except
        st.error(f"[BFD] Failed to run '{command}' on {dut}: {exc}")
        return False, {
            "command": command,
            "output": str(exc),
            "dut": dut,
            "exception": "1",
        }
    return True, {}


def collect_cli_output(
    dut: str,
    command: str,
    cli_type: str = "klish",
    skip_error_check: bool = True,
    sudo: bool = False,
) -> str:
    """
    Run ``command`` on ``dut`` and return raw output as a single string.

    The helper normalizes list/tuple responses from ``st.show`` and always
    returns a string, easing downstream substring checks.

    :param dut: Device Under Test
    :param command: CLI command to execute
    :param cli_type: CLI type (klish, click, vtysh)
    :param skip_error_check: Skip error checking
    :param sudo: Execute with sudo
    :return: Command output as string
    """
    output = st.show(
        dut,
        command,
        type=cli_type,
        skip_tmpl=True,
        skip_error_check=skip_error_check,
        sudo=sudo,
    )
    if isinstance(output, (list, tuple)):
        return "\n".join(str(line) for line in output)
    if output is None:
        return ""
    return str(output)


def check_cli_expectations(
    dut: str,
    command: str,
    expectation: Optional[Mapping[str, Sequence[str]]] = None,
    cli_type: str = "klish",
    skip_error_check: bool = True,
    sudo: bool = False,
) -> Tuple[bool, Mapping[str, object]]:
    """
    Validate CLI output against expectation rules.

    Expectation keys:
        - ``all``: every string must be present
        - ``any``: at least one string must be present
        - ``none``: no string may be present

    Returns ``(ok, details)`` where ``details`` includes the captured output and
    any missing/unexpected strings to help build failure messages.

    :param dut: Device Under Test
    :param command: CLI command to execute
    :param expectation: Expectation rules mapping
    :param cli_type: CLI type (klish, click, vtysh)
    :param skip_error_check: Skip error checking
    :param sudo: Execute with sudo
    :return: Tuple of (success_bool, details_dict)
    """
    expectation = expectation or {}
    text = collect_cli_output(
        dut,
        command,
        cli_type=cli_type,
        skip_error_check=skip_error_check,
        sudo=sudo,
    )

    all_terms = [str(term) for term in make_list(expectation.get("all")) if term is not None]
    any_terms = [str(term) for term in make_list(expectation.get("any")) if term is not None]
    none_terms = [str(term) for term in make_list(expectation.get("none")) if term is not None]

    missing_all = [term for term in all_terms if term not in text]

    any_found = True
    missing_any: List[str] = []
    if any_terms:
        any_found = any(term in text for term in any_terms)
        if not any_found:
            missing_any = any_terms.copy()

    unexpected = [term for term in none_terms if term in text]

    ok = not missing_all and any_found and not unexpected
    details = {
        "command": command,
        "output": text,
        "missing_all": missing_all,
        "missing_any": missing_any,
        "unexpected": unexpected,
    }
    return ok, details


# ============================================================================
# BFD Configuration API Functions
# ============================================================================


def enable_bfd(dut: str, cli_type: str = "klish") -> bool:
    """
    Enable BFD globally on the device.

    :param dut: Device Under Test
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        if enable_bfd(dut1, "klish"):
            st.log("BFD enabled successfully on DUT1")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    command = "bfd"
    success, error_info = apply_cli_sequence(dut, [command], cli_type=cli_type)

    if success:
        st.log(f"[BFD] BFD globally enabled on {dut}")
    else:
        st.error(f"[BFD] Failed to enable BFD on {dut}: {error_info}")

    return success


def disable_bfd(dut: str, cli_type: str = "klish") -> bool:
    """
    Disable BFD globally on the device.

    :param dut: Device Under Test
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        if disable_bfd(dut1, "klish"):
            st.log("BFD disabled successfully on DUT1")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    command = "no bfd"
    success, error_info = apply_cli_sequence(dut, [command], cli_type=cli_type)

    if success:
        st.log(f"[BFD] BFD globally disabled on {dut}")
    else:
        st.error(f"[BFD] Failed to disable BFD on {dut}: {error_info}")

    return success


def configure_bfd_peer(
    dut: str,
    peer_ip: str,
    interface: str = None,
    multihop: bool = False,
    local_address: str = None,
    vrf: str = None,
    cli_type: str = "klish",
) -> bool:
    """
    Configure a BFD peer on the device.

    :param dut: Device Under Test
    :param peer_ip: Peer IP address
    :param interface: Physical interface name (for single-hop)
    :param multihop: Enable multi-hop mode
    :param local_address: Local address for multi-hop
    :param vrf: VRF name for the peer
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        # Configure single-hop peer
        configure_bfd_peer(dut1, "10.1.1.2", interface="Ethernet0")

        # Configure multi-hop peer
        configure_bfd_peer(dut1, "10.2.2.2", multihop=True, local_address="10.1.1.1")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    commands = []

    # Build the peer configuration command
    if multihop:
        if not local_address:
            st.error("[BFD] local_address required for multi-hop BFD")
            return False
        peer_cmd = f"peer {peer_ip} multihop local-address {local_address}"
    else:
        if not interface:
            st.error("[BFD] interface required for single-hop BFD")
            return False
        peer_cmd = f"peer {peer_ip} interface {interface}"

    # Add VRF if specified
    if vrf:
        peer_cmd = f"peer {peer_ip} vrf {vrf}"
        if multihop:
            peer_cmd += f" multihop local-address {local_address}"
        else:
            peer_cmd += f" interface {interface}"

    commands.append("bfd")
    commands.append(peer_cmd)

    success, error_info = apply_cli_sequence(dut, commands, cli_type=cli_type)

    if success:
        st.log(f"[BFD] Peer {peer_ip} configured successfully on {dut}")
    else:
        st.error(f"[BFD] Failed to configure peer {peer_ip} on {dut}: {error_info}")

    return success


def remove_bfd_peer(dut: str, peer_ip: str, vrf: str = None, cli_type: str = "klish") -> bool:
    """
    Remove a BFD peer configuration from the device.

    :param dut: Device Under Test
    :param peer_ip: Peer IP address to remove
    :param vrf: VRF name (if peer is in non-default VRF)
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        if remove_bfd_peer(dut1, "10.1.1.2"):
            st.log("BFD peer removed successfully")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    commands = ["bfd"]

    if vrf:
        commands.append(f"no peer {peer_ip} vrf {vrf}")
    else:
        commands.append(f"no peer {peer_ip}")

    success, error_info = apply_cli_sequence(dut, commands, cli_type=cli_type)

    if success:
        st.log(f"[BFD] Peer {peer_ip} removed successfully from {dut}")
    else:
        st.error(f"[BFD] Failed to remove peer {peer_ip} from {dut}: {error_info}")

    return success


def configure_bfd_peer_params(
    dut: str,
    peer_ip: str,
    transmit_interval: int = None,
    receive_interval: int = None,
    detect_multiplier: int = None,
    echo_mode: bool = None,
    echo_interval: int = None,
    vrf: str = None,
    cli_type: str = "klish",
) -> bool:
    """
    Configure BFD peer parameters like timers and echo mode.

    :param dut: Device Under Test
    :param peer_ip: Peer IP address
    :param transmit_interval: TX interval in milliseconds (10-60000 ms)
    :param receive_interval: RX interval in milliseconds (10-60000 ms)
    :param detect_multiplier: Detect multiplier (3-50)
    :param echo_mode: Enable/disable echo mode
    :param echo_interval: Echo interval in milliseconds
    :param vrf: VRF name
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        configure_bfd_peer_params(dut1, "10.1.1.2", transmit_interval=300,
                                  receive_interval=300, detect_multiplier=3)
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    commands = ["bfd"]

    if vrf:
        commands.append(f"peer {peer_ip} vrf {vrf}")
    else:
        commands.append(f"peer {peer_ip}")

    if transmit_interval is not None:
        commands.append(f"transmit-interval {transmit_interval}")

    if receive_interval is not None:
        commands.append(f"receive-interval {receive_interval}")

    if detect_multiplier is not None:
        commands.append(f"detect-multiplier {detect_multiplier}")

    if echo_mode is not None:
        if echo_mode:
            commands.append("echo-mode")
        else:
            commands.append("no echo-mode")

    if echo_interval is not None and echo_mode:
        commands.append(f"echo-interval {echo_interval}")

    success, error_info = apply_cli_sequence(dut, commands, cli_type=cli_type)

    if success:
        st.log(f"[BFD] Peer {peer_ip} parameters configured on {dut}")
    else:
        st.error(f"[BFD] Failed to configure peer {peer_ip} parameters: {error_info}")

    return success


def configure_bfd_slow_timer(dut: str, slow_timer: int, cli_type: str = "klish") -> bool:
    """
    Configure BFD global slow-timer (used when no peers are configured).

    :param dut: Device Under Test
    :param slow_timer: Slow timer value in milliseconds (1000-60000 ms)
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        if configure_bfd_slow_timer(dut1, 5000):
            st.log("BFD slow-timer set to 5000ms")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    commands = [
        "bfd",
        f"slow-timer {slow_timer}",
    ]

    success, error_info = apply_cli_sequence(dut, commands, cli_type=cli_type)

    if success:
        st.log(f"[BFD] Slow-timer set to {slow_timer}ms on {dut}")
    else:
        st.error(f"[BFD] Failed to configure slow-timer: {error_info}")

    return success


def configure_bfd_profile(
    dut: str,
    profile_name: str,
    transmit_interval: int = None,
    receive_interval: int = None,
    detect_multiplier: int = None,
    echo_mode: bool = None,
    echo_interval: int = None,
    cli_type: str = "klish",
) -> bool:
    """
    Create or update a BFD profile with predefined parameters.

    :param dut: Device Under Test
    :param profile_name: Profile name
    :param transmit_interval: TX interval in milliseconds
    :param receive_interval: RX interval in milliseconds
    :param detect_multiplier: Detect multiplier
    :param echo_mode: Enable/disable echo mode
    :param echo_interval: Echo interval in milliseconds
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        configure_bfd_profile(dut1, "fast-bfd", transmit_interval=100,
                            receive_interval=100, detect_multiplier=5)
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    commands = [
        "bfd",
        f"profile {profile_name}",
    ]

    if transmit_interval is not None:
        commands.append(f"transmit-interval {transmit_interval}")

    if receive_interval is not None:
        commands.append(f"receive-interval {receive_interval}")

    if detect_multiplier is not None:
        commands.append(f"detect-multiplier {detect_multiplier}")

    if echo_mode is not None:
        if echo_mode:
            commands.append("echo-mode")
        else:
            commands.append("no echo-mode")

    if echo_interval is not None and echo_mode:
        commands.append(f"echo-interval {echo_interval}")

    success, error_info = apply_cli_sequence(dut, commands, cli_type=cli_type)

    if success:
        st.log(f"[BFD] Profile '{profile_name}' created/updated on {dut}")
    else:
        st.error(f"[BFD] Failed to configure profile '{profile_name}': {error_info}")

    return success


def remove_bfd_profile(dut: str, profile_name: str, cli_type: str = "klish") -> bool:
    """
    Remove a BFD profile from the device.

    :param dut: Device Under Test
    :param profile_name: Profile name to remove
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        if remove_bfd_profile(dut1, "fast-bfd"):
            st.log("BFD profile removed")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    commands = [
        "bfd",
        f"no profile {profile_name}",
    ]

    success, error_info = apply_cli_sequence(dut, commands, cli_type=cli_type)

    if success:
        st.log(f"[BFD] Profile '{profile_name}' removed from {dut}")
    else:
        st.error(f"[BFD] Failed to remove profile '{profile_name}': {error_info}")

    return success


def apply_bfd_profile_to_peer(
    dut: str,
    peer_ip: str,
    profile_name: str,
    vrf: str = None,
    cli_type: str = "klish",
) -> bool:
    """
    Apply a BFD profile to an existing BFD peer.

    :param dut: Device Under Test
    :param peer_ip: Peer IP address
    :param profile_name: Profile name to apply
    :param vrf: VRF name
    :param cli_type: CLI type (klish, click)
    :return: True if successful, False otherwise

    Example:
        apply_bfd_profile_to_peer(dut1, "10.1.1.2", "fast-bfd")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    commands = ["bfd"]

    if vrf:
        commands.append(f"peer {peer_ip} vrf {vrf}")
    else:
        commands.append(f"peer {peer_ip}")

    commands.append(f"profile {profile_name}")

    success, error_info = apply_cli_sequence(dut, commands, cli_type=cli_type)

    if success:
        st.log(f"[BFD] Profile '{profile_name}' applied to peer {peer_ip} on {dut}")
    else:
        st.error(f"[BFD] Failed to apply profile to peer: {error_info}")

    return success


# ============================================================================
# BFD Verification API Functions
# ============================================================================


def show_bfd_config(dut: str, cli_type: str = "klish") -> str:
    """
    Display BFD running configuration.

    :param dut: Device Under Test
    :param cli_type: CLI type (klish, click)
    :return: Configuration output as string

    Example:
        config_output = show_bfd_config(dut1)
        if "bfd" in config_output:
            st.log("BFD is configured")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    command = "show running-config bfd"
    output = collect_cli_output(dut, command, cli_type=cli_type)

    return output


def show_bfd_peers(dut: str, cli_type: str = "klish") -> str:
    """
    Display all BFD peers and their status.

    :param dut: Device Under Test
    :param cli_type: CLI type (klish, click)
    :return: Peers output as string

    Example:
        peers_output = show_bfd_peers(dut1)
        if "10.1.1.2" in peers_output:
            st.log("Peer 10.1.1.2 is configured")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    command = "show bfd peers"
    output = collect_cli_output(dut, command, cli_type=cli_type)

    return output


def show_bfd_peer(dut: str, peer_ip: str, cli_type: str = "klish") -> str:
    """
    Display detailed information about a specific BFD peer.

    :param dut: Device Under Test
    :param peer_ip: Peer IP address
    :param cli_type: CLI type (klish, click)
    :return: Peer details output as string

    Example:
        peer_details = show_bfd_peer(dut1, "10.1.1.2")
        if "State: Up" in peer_details:
            st.log("BFD peer is Up")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    command = f"show bfd peer {peer_ip}"
    output = collect_cli_output(dut, command, cli_type=cli_type)

    return output


def show_bfd_profile(dut: str, profile_name: str = None, cli_type: str = "klish") -> str:
    """
    Display BFD profile configuration.

    :param dut: Device Under Test
    :param profile_name: Profile name (show all if None)
    :param cli_type: CLI type (klish, click)
    :return: Profile details output as string

    Example:
        profile_output = show_bfd_profile(dut1, "fast-bfd")
        if "transmit-interval" in profile_output:
            st.log("Profile parameters found")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    if profile_name:
        command = f"show bfd profile {profile_name}"
    else:
        command = "show bfd profile"

    output = collect_cli_output(dut, command, cli_type=cli_type)

    return output


# ============================================================================
# BFD Verification Helper Functions
# ============================================================================


def verify_bfd_peer_up(
    dut: str,
    peer_ip: str,
    timeout: int = 30,
    cli_type: str = "klish",
) -> bool:
    """
    Verify that a BFD peer is in Up state.

    :param dut: Device Under Test
    :param peer_ip: Peer IP address
    :param timeout: Maximum time to wait in seconds
    :param cli_type: CLI type (klish, click)
    :return: True if peer is Up, False otherwise

    Example:
        if verify_bfd_peer_up(dut1, "10.1.1.2", timeout=10):
            st.log("BFD peer is up")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    for attempt in range(timeout):
        output = show_bfd_peer(dut, peer_ip, cli_type=cli_type)

        # Check for various "Up" indicators in output
        if any(indicator in output for indicator in ["State: Up", "state: Up", "State: up", "state: up"]):
            st.log(f"[BFD] Peer {peer_ip} is Up on {dut}")
            return True

        if attempt < timeout - 1:
            st.wait(1, "Waiting for BFD peer to come up")

    st.error(f"[BFD] Peer {peer_ip} did not come up within {timeout} seconds")
    return False


def verify_bfd_session_down(
    dut: str,
    peer_ip: str,
    timeout: int = 30,
    cli_type: str = "klish",
) -> bool:
    """
    Verify that a BFD session goes Down.

    :param dut: Device Under Test
    :param peer_ip: Peer IP address
    :param timeout: Maximum time to wait in seconds
    :param cli_type: CLI type (klish, click)
    :return: True if session is Down, False otherwise

    Example:
        if verify_bfd_session_down(dut1, "10.1.1.2"):
            st.log("BFD session is down as expected")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    for attempt in range(timeout):
        output = show_bfd_peer(dut, peer_ip, cli_type=cli_type)

        # Check for Down state
        if any(indicator in output for indicator in ["State: Down", "state: Down", "State: down", "state: down"]):
            st.log(f"[BFD] Peer {peer_ip} is Down on {dut}")
            return True

        if attempt < timeout - 1:
            st.wait(1, "Waiting for BFD session to go down")

    st.error(f"[BFD] Session {peer_ip} did not go down within {timeout} seconds")
    return False


def get_bfd_peer_status(dut: str, peer_ip: str, cli_type: str = "klish") -> str:
    """
    Get the current state of a BFD peer.

    :param dut: Device Under Test
    :param peer_ip: Peer IP address
    :param cli_type: CLI type (klish, click)
    :return: Peer state (Up, Down, Init, AdminDown) or None if not found

    Example:
        state = get_bfd_peer_status(dut1, "10.1.1.2")
        if state == "Up":
            st.log("Peer is up")
    """
    output = show_bfd_peer(dut, peer_ip, cli_type=cli_type)

    # Try to extract state from output
    for line in output.split('\n'):
        line = line.strip()
        if 'state' in line.lower():
            # Extract state value (e.g., "State: Up" -> "Up")
            parts = line.split(':')
            if len(parts) > 1:
                state = parts[-1].strip()
                st.log(f"[BFD] Peer {peer_ip} state: {state}")
                return state

    st.error(f"[BFD] Could not determine state for peer {peer_ip}")
    return None
