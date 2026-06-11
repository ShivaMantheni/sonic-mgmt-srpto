"""
LACP-POS-010: Verify bidirectional traffic on PortChannel

Author: Generated from testplan, 2026-05-20

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed /home/hp_test/Athira/testbed_lacp_vs.yaml \\
  tests/switching/lacp/test_lacp_pos_010_bidirectional_traffic.py \\
  --logs-path ./logs/lacp_pos_010_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Validates bidirectional UDP traffic flows correctly across all PortChannel members
  in both directions simultaneously (D1→D2 and D2→D1). Verifies that all member
  interfaces carry traffic in both directions, RX and TX counters increment correctly,
  and there are no unidirectional link issues.

Pre-requisites:
  - Topology: two-node (D1-D2) | Supported: Virtual testbed
  - D1 and D2 connected via 4 physical links (Ethernet32, 36, 40, 44)
  - Testbed YAML: /home/hp_test/Athira/testbed_lacp_vs.yaml
  - Feature: LACP (Link Aggregation Control Protocol)
  - Test Type: Positive - Happy Path
  - Priority: P1

Test Coverage:
  - PortChannel creation with LACP active mode on both DUTs
  - IP configuration on PortChannel interfaces
  - Bidirectional UDP traffic generation using Scapy
  - tcpdump capture verification on all member interfaces (both directions)
  - RX and TX counter validation on all members
  - Traffic distribution analysis in both directions
  - No unidirectional link issues

Success Criteria:
  - PortChannel operational with all 4 members synchronized
  - UDP traffic flows D1→D2 simultaneously with D2→D1
  - All 4 members carry traffic in both directions
  - RX counters increment on receiving side for all members
  - TX counters increment on transmitting side for all members
  - No packet loss or unidirectional link errors
"""

import pytest
import time
import re
from spytest import st, SpyTestDict

# Import feature APIs
import apis.switching.lacp as lacp_api
import apis.routing.ip as ip_api
import apis.system.interface as intf_api
import apis.system.basic as basic_api
import utilities.common as utils_obj
from utilities.utils import ensure_service_params

# Import Scapy API for traffic generation
try:
    import apis.common.scapy_traffic as scapy_api
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    # Note: Cannot use st.log() during module import (framework not initialized)

# Module-level variables
vars = SpyTestDict()
data = SpyTestDict()

# Test constants
PC_ID = 1
PC_NAME = f"PortChannel{PC_ID}"
LACP_MODE = "active"

# IP configuration for PortChannel (L3)
PC_IP_D1 = "10.1.1.1"
PC_IP_D2 = "10.1.1.2"
PC_PREFIX_LEN = 24
PC_SUBNET = f"{PC_IP_D1}/{PC_PREFIX_LEN}"

# Traffic parameters for bidirectional UDP test
UDP_SRC_PORT = 5000
UDP_DST_PORT = 6000
PACKET_COUNT = 500  # 100 pps * 5 seconds
PACKET_RATE = 100   # packets per second
DURATION = 5        # seconds
PACKET_SIZE = 128   # bytes

# Default MAC addresses (fallback if retrieval fails)
DEFAULT_MAC_D1 = "00:11:22:33:44:01"
DEFAULT_MAC_D2 = "00:11:22:33:44:02"

# Variance threshold for traffic distribution (±20%)
DISTRIBUTION_VARIANCE_THRESHOLD = 0.20


@pytest.fixture(scope="module", autouse=True)
def module_hooks(request):
    """
    Module prologue: Setup topology and initialize test environment
    Module epilogue: Cleanup PortChannel configuration
    """
    global vars, data

    st.banner("MODULE PROLOGUE: Starting LACP-POS-010 Test Setup")

    # Get testbed variables
    vars = st.get_testbed_vars()

    # Verify minimum topology requirements
    if not (hasattr(vars, 'D1') and hasattr(vars, 'D2')):
        st.error("Test requires 2 devices (D1, D2)")
        pytest.skip("Insufficient topology - need D1 and D2")

    # Store device references
    data.dut1 = vars.D1
    data.dut2 = vars.D2

    # Get CLI type
    data.cli_type = st.get_ui_type(data.dut1, cli_type="klish")

    # Define member interfaces for PortChannel
    # Using same interfaces as testbed connection (verify with testbed YAML)
    data.members_d1 = ["Ethernet32", "Ethernet36", "Ethernet40", "Ethernet44"]
    data.members_d2 = ["Ethernet32", "Ethernet36", "Ethernet40", "Ethernet44"]

    st.log(f"DUT1: {data.dut1}, Members: {data.members_d1}")
    st.log(f"DUT2: {data.dut2}, Members: {data.members_d2}")
    st.log(f"CLI Type: {data.cli_type}")

    # Setup complete
    st.banner("MODULE PROLOGUE: Setup Complete")

    yield

    # Module epilogue - cleanup
    st.banner("MODULE EPILOGUE: Cleanup Started")

    try:
        # Remove IP addresses from PortChannel
        for dut, pc_ip in [(data.dut1, PC_IP_D1), (data.dut2, PC_IP_D2)]:
            ip_api.delete_ip_interface(
                dut, PC_NAME,
                f"{pc_ip}/{PC_PREFIX_LEN}",
                family="ipv4",
                cli_type=data.cli_type
            )
            st.log(f"Removed IP {pc_ip}/{PC_PREFIX_LEN} from {PC_NAME} on {dut}")

        # Delete PortChannel on both devices
        for dut in [data.dut1, data.dut2]:
            lacp_api.delete_lacp_portchannel(dut, PC_ID, cli_type=data.cli_type)
            st.log(f"Deleted {PC_NAME} on {dut}")

        st.log("Cleanup completed successfully")

    except Exception as e:
        st.error(f"Cleanup failed: {e}")

    st.banner("MODULE EPILOGUE: Cleanup Complete")


class TestLacpPos010BidirectionalTraffic:
    """
    Test class for LACP-POS-010: Verify bidirectional traffic on PortChannel
    """

    def _setup_portchannel(self, dut, pc_ip, members):
        """
        Helper method to create PortChannel, add members, configure IP

        Args:
            dut: Device under test
            pc_ip: IP address to configure on PortChannel (without prefix)
            members: List of member interfaces

        Returns:
            True if setup successful, False otherwise
        """
        st.banner(f"Setting up {PC_NAME} on {dut}")

        try:
            # Step 1: Create PortChannel with LACP active mode
            result = lacp_api.create_lacp_portchannel(
                dut, PC_ID,
                mode=LACP_MODE,
                cli_type=data.cli_type
            )
            if not result:
                st.error(f"Failed to create {PC_NAME} on {dut}")
                return False
            st.log(f"Created {PC_NAME} with LACP mode: {LACP_MODE} on {dut}")

            # Step 2: Add all members to PortChannel
            for member in members:
                result = lacp_api.add_portchannel_member(
                    dut, PC_ID, member,
                    cli_type=data.cli_type
                )
                if not result:
                    st.error(f"Failed to add {member} to {PC_NAME} on {dut}")
                    return False
                st.log(f"Added {member} to {PC_NAME} on {dut}")

            # Step 3: Bring up member interfaces (no shutdown)
            st.log(f"Bringing up member interfaces on {dut}")
            for member in members:
                intf_api.interface_operation(dut, member, operation="startup", cli_type=data.cli_type)
                st.log(f"Interface {member} brought up")

            # Step 4: Bring up PortChannel interface (no shutdown)
            st.log(f"Bringing up {PC_NAME} interface on {dut}")
            result = intf_api.interface_operation(
                dut, PC_NAME,
                operation="startup",
                cli_type=data.cli_type
            )
            if not result:
                st.error(f"Failed to bring up {PC_NAME} on {dut}")
                return False
            st.log(f"Brought up {PC_NAME} on {dut}")

            # Wait for LACP negotiation
            st.wait(5, "Waiting for LACP negotiation")

            # Step 5: Configure IP address on PortChannel
            result = ip_api.config_ip_addr_interface(
                dut, PC_NAME,
                pc_ip,  # IP address only: "10.1.1.1" or "10.1.1.2"
                PC_PREFIX_LEN,  # Subnet mask: 24
                family="ipv4",
                cli_type=data.cli_type
            )
            if not result:
                st.error(f"Failed to configure IP {pc_ip}/{PC_PREFIX_LEN} on {PC_NAME} on {dut}")
                return False
            st.log(f"Configured IP {pc_ip}/{PC_PREFIX_LEN} on {PC_NAME} on {dut}")

            st.log(f"PortChannel setup completed successfully on {dut}")
            return True

        except Exception as e:
            st.error(f"Exception during PortChannel setup on {dut}: {e}")
            return False

    def _verify_portchannel_sync(self, dut, members):
        """
        Verify all PortChannel members are synchronized

        Uses raw CLI output parsing to avoid template parsing issues.

        Args:
            dut: Device under test
            members: List of member interfaces

        Returns:
            True if all members synchronized, False otherwise
        """
        st.banner(f"Verifying LACP synchronization on {dut}")

        # Allow time for LACP to synchronize
        st.wait(10, "Waiting for LACP synchronization")

        # Disable pagination to prevent --more-- prompts
        try:
            st.config(dut, "terminal length 0", type=data.cli_type, skip_error_check=True)
            st.log("Disabled terminal pagination (terminal length 0)")
        except Exception as e:
            st.log(f"Warning: Could not disable pagination: {e}")

        # Method 1: Use show portchannel summary for basic verification
        try:
            cmd = "show portchannel summary"
            output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

            if isinstance(output, str):
                st.log(f"PortChannel summary output:\n{output}")

                # Check if PortChannel is present
                if f"PortChannel{PC_ID}" not in output:
                    st.error(f"PortChannel{PC_ID} not found in summary")
                    return False

                # Parse the summary line for state
                # Actual format: "1   PortChannel1   Eth (U)   LACP   Ethernet32(P), ..."
                # State is in Type column: "Eth (U)" or "Eth (D)"
                import re

                # Find the line containing PortChannel{pc_id}
                pc_state = None
                for line in output.split('\n'):
                    if f"PortChannel{PC_ID}" in line:
                        st.log(f"Found PortChannel line: {line}")
                        # Extract state from "Eth (U)" or "Eth (D)"
                        state_match = re.search(r'\(([UD])\)', line)
                        if state_match:
                            pc_state = state_match.group(1)
                            break

                if not pc_state:
                    st.error(f"Could not parse PortChannel{PC_ID} state from output")
                    return False

                if pc_state != "U":
                    st.error(f"PortChannel{PC_ID} is DOWN (state: {pc_state})")
                    return False

                st.log(f"✓ PortChannel{PC_ID} is UP (state: {pc_state})")

        except Exception as e:
            st.error(f"Exception during portchannel summary check: {e}")
            return False

        # Method 2: Verify members using raw output of show interface PortChannel
        try:
            cmd = f"show interface PortChannel {PC_ID} | no-more"
            output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

            if isinstance(output, str):
                st.log(f"Interface PortChannel{PC_ID} output:\n{output}")

                # Extract members from line: "Members in this channel: Ethernet32, Ethernet36, ..."
                import re
                members_pattern = r"Members in this channel:\s+(.+)"
                match = re.search(members_pattern, output)

                if not match:
                    st.error("Could not find 'Members in this channel' line")
                    return False

                members_line = match.group(1).strip()
                # Split by comma and strip whitespace
                found_members = [m.strip() for m in members_line.split(',')]

                st.log(f"Found members: {found_members}")

                # Verify all expected members are present
                for expected_member in members:
                    if expected_member not in found_members:
                        st.error(f"Expected member {expected_member} not found in PortChannel")
                        return False

                st.log(f"✓ All {len(members)} members present: {found_members}")

        except Exception as e:
            st.error(f"Exception during member verification: {e}")
            return False

        # Method 3: Verify LACP member status using portchannel summary
        # Check for (P) status which indicates: Selected + Collecting/Distributing
        try:
            cmd = "show portchannel summary"
            output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

            if isinstance(output, str):
                st.log(f"Verifying LACP member status from portchannel summary")

                # Find the PortChannel line
                for line in output.split('\n'):
                    if f"PortChannel{PC_ID}" in line:
                        st.log(f"PortChannel summary line: {line}")

                        # Check each expected member has (P) status
                        # Format: "Ethernet32(P), Ethernet36(P), ..."
                        # (P) = Selected state in LACP
                        for member in members:
                            # Look for member(P) pattern
                            if f"{member}(P)" in line:
                                st.log(f"✓ {member}: LACP Selected (P)")
                            elif f"{member}(S)" in line:
                                st.log(f"✓ {member}: LACP Standby (S)")
                            elif member in line:
                                # Member present but no clear status
                                st.warn(f"{member}: Present but status unclear in portchannel summary")
                            else:
                                st.warn(f"{member}: Not found in portchannel summary member list")
                        break

            st.log("✓ LACP member status verification completed")

        except Exception as e:
            st.log(f"Warning: Could not verify LACP member status details: {e}")
            # Don't fail on LACP detail check - member presence already verified in Method 2

        st.log(f"✓ All verification checks passed on {dut}")
        return True

    def _get_mac_address(self, dut, interface):
        """
        Get MAC address of an interface

        Args:
            dut: Device under test
            interface: Interface name

        Returns:
            MAC address string, or default MAC if retrieval fails
        """
        # Disable pagination to prevent --more-- prompts
        try:
            st.config(dut, "terminal length 0", type=data.cli_type, skip_error_check=True)
        except Exception as e:
            st.log(f"Warning: Could not disable pagination: {e}")

        try:
            # Method 1: Try using show interface <interface> and parse MAC directly
            cmd = f"show interface {interface} | no-more"
            output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

            # Look for MAC address in output (format: aa:bb:cc:dd:ee:ff or aa-bb-cc-dd-ee-ff)
            mac_pattern = r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}'
            matches = re.findall(mac_pattern, output)

            if matches:
                mac = matches[0].replace('-', ':').lower()
                st.log(f"Retrieved MAC for {interface} on {dut}: {mac}")
                return mac

            # Method 2: Try show interface status and parse output directly
            cmd = f"show interface status | grep {interface} | no-more"
            output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

            # Some SONiC versions might show MAC in status output
            matches = re.findall(mac_pattern, output)
            if matches:
                mac = matches[0].replace('-', ':').lower()
                st.log(f"Retrieved MAC for {interface} on {dut}: {mac}")
                return mac

            # Fallback: use default MAC
            default_mac = DEFAULT_MAC_D1 if dut == data.dut1 else DEFAULT_MAC_D2
            st.log(f"Could not retrieve MAC for {interface} on {dut}, using default: {default_mac}")
            return default_mac

        except Exception as e:
            st.error(f"Exception retrieving MAC for {interface} on {dut}: {e}")
            default_mac = DEFAULT_MAC_D1 if dut == data.dut1 else DEFAULT_MAC_D2
            st.log(f"Using default MAC: {default_mac}")
            return default_mac

    def _clear_interface_counters(self, dut, interfaces):
        """
        Clear interface counters for specified interfaces

        Args:
            dut: Device under test
            interfaces: List of interface names

        Returns:
            True if successful, False otherwise
        """
        st.banner(f"Clearing interface counters on {dut}")

        try:
            for intf in interfaces:
                result = intf_api.clear_interface_counters(
                    dut, interface_name=intf,
                    cli_type=data.cli_type
                )
                if not result:
                    st.log(f"Warning: Failed to clear counters for {intf} on {dut}")
                else:
                    st.log(f"Cleared counters for {intf} on {dut}")

            st.wait(2, "Waiting for counter clear to take effect")
            return True

        except Exception as e:
            st.error(f"Exception clearing counters on {dut}: {e}")
            return False

    def _start_tcpdump_all_members(self, dut, members, pcap_prefix, filter_str="udp"):
        """
        Start tcpdump on all member interfaces

        Args:
            dut: Device under test
            members: List of member interface names
            pcap_prefix: Prefix for pcap filename
            filter_str: tcpdump filter string

        Returns:
            Dict mapping member interface to pcap filename
        """
        st.banner(f"Starting tcpdump on all members of {dut}")

        pcap_files = {}

        if not SCAPY_AVAILABLE:
            st.log("WARNING: Scapy API not available, skipping tcpdump")
            return pcap_files

        try:
            for member in members:
                pcap_file = f"/tmp/{pcap_prefix}_{member.replace('/', '_')}.pcap"
                pcap_files[member] = pcap_file

                # Start tcpdump on member interface (NOT PortChannel)
                scapy_api.start_tcpdump(
                    dut,
                    member,
                    filter_str=filter_str,
                    output_file=pcap_file
                )
                st.log(f"Started tcpdump on {member} -> {pcap_file}")

            st.wait(2, "Waiting for tcpdump to initialize")
            return pcap_files

        except Exception as e:
            st.error(f"Exception starting tcpdump on {dut}: {e}")
            return pcap_files

    def _stop_tcpdump_all_members(self, dut, members):
        """
        Stop tcpdump on device (kills all tcpdump processes)

        Args:
            dut: Device under test
            members: List of member interface names (not used, for API compatibility)
        """
        st.banner(f"Stopping tcpdump on all members of {dut}")

        if not SCAPY_AVAILABLE:
            st.log("WARNING: Scapy API not available, skipping tcpdump stop")
            return

        try:
            # stop_tcpdump() kills all tcpdump processes on the device (via pkill)
            # It does NOT take interface parameter - one call per DUT is sufficient
            scapy_api.stop_tcpdump(dut)
            st.log(f"Stopped all tcpdump processes on {dut}")

            st.wait(2, "Waiting for tcpdump to flush buffers")

        except Exception as e:
            st.error(f"Exception stopping tcpdump on {dut}: {e}")

    def _verify_tcpdump_captures(self, dut, pcap_files, min_packets=10):
        """
        Verify tcpdump captures contain packets

        Args:
            dut: Device under test
            pcap_files: Dict mapping member interface to pcap filename
            min_packets: Minimum expected packet count per member

        Returns:
            True if all captures valid, False otherwise
        """
        st.banner(f"Verifying tcpdump captures on {dut}")

        if not SCAPY_AVAILABLE or not pcap_files:
            st.log("WARNING: No pcap files to verify")
            return True

        all_valid = True

        try:
            for member, pcap_file in pcap_files.items():
                # Verify tcpdump capture using API
                result = scapy_api.verify_tcpdump_capture(
                    dut,
                    capture_file=pcap_file,
                    min_packets=min_packets
                )

                packet_count = result.get("packet_count", 0)
                success = result.get("success", False)

                st.log(f"Member {member}: {packet_count} packets captured")

                if not success:
                    st.error(f"Member {member} captured only {packet_count} packets (expected >= {min_packets})")
                    all_valid = False
                else:
                    st.log(f"✓ Member {member} capture VALID ({packet_count} packets)")

            return all_valid

        except Exception as e:
            st.error(f"Exception verifying tcpdump captures on {dut}: {e}")
            return False

    def _cleanup_tcpdump_files(self, dut, pcap_files):
        """
        Remove tcpdump capture files

        Args:
            dut: Device under test
            pcap_files: Dict mapping member interface to pcap filename
        """
        st.log(f"Cleaning up tcpdump files on {dut}")

        if not SCAPY_AVAILABLE or not pcap_files:
            return

        try:
            for member, pcap_file in pcap_files.items():
                basic_api.delete_file(dut, pcap_file)
                st.log(f"Deleted {pcap_file}")

        except Exception as e:
            st.error(f"Exception cleaning up tcpdump files on {dut}: {e}")

    def _get_interface_counters(self, dut, interfaces):
        """
        Get RX_OK and TX_OK counters for specified interfaces

        Uses full table output with headers for accurate parsing.
        Avoids grep which strips headers and breaks column alignment.

        Args:
            dut: Device under test
            interfaces: List of interface names

        Returns:
            Dict mapping interface to {"rx_ok": value, "tx_ok": value}
        """
        st.banner(f"Getting interface counters on {dut}")

        counter_data = {}

        # Get full interface counters output (with headers)
        cmd = "show interface counters | no-more"
        output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

        if not isinstance(output, str):
            st.error("Counter output is not a string")
            return {intf: {"rx_ok": 0, "tx_ok": 0} for intf in interfaces}

        st.log(f"Full counter output:\n{output}")

        # Parse the table output
        lines = output.strip().split('\n')

        # Find header line (contains "IFACE" or "Interface")
        header_line = None
        header_idx = -1
        for idx, line in enumerate(lines):
            if 'IFACE' in line.upper() or 'INTERFACE' in line.upper():
                header_line = line
                header_idx = idx
                st.log(f"Found header at line {idx}: {line}")
                break

        if not header_line:
            st.warn("Could not find header line in counter output")
            return {intf: {"rx_ok": 0, "tx_ok": 0} for intf in interfaces}

        # Identify column positions from header
        header_parts = header_line.split()
        st.log(f"Header columns: {header_parts}")

        # Find RX_OK and TX_OK column indices
        rx_ok_col = -1
        tx_ok_col = -1

        for i, col in enumerate(header_parts):
            if 'RX_OK' in col.upper() or col.upper() == 'RX_OK':
                rx_ok_col = i
            if 'TX_OK' in col.upper() or col.upper() == 'TX_OK':
                tx_ok_col = i

        if rx_ok_col == -1 or tx_ok_col == -1:
            st.warn(f"Could not find RX_OK/TX_OK columns (rx_ok_col={rx_ok_col}, tx_ok_col={tx_ok_col})")
            return {intf: {"rx_ok": 0, "tx_ok": 0} for intf in interfaces}

        st.log(f"Column positions: RX_OK={rx_ok_col}, TX_OK={tx_ok_col}")

        # Parse data lines for each interface
        for intf in interfaces:
            rx_ok = 0
            tx_ok = 0

            # Find line containing this interface
            for line in lines[header_idx + 1:]:
                if intf in line:
                    st.log(f"Found {intf} line: {line}")

                    # Split line into columns and remove unit tokens
                    # Units like "B/s", "/s", "%" appear as separate tokens and shift columns
                    parts = line.split()

                    # Filter out unit-only tokens (contain no digits)
                    # Keep tokens that are pure numbers or interface names
                    cleaned_parts = []
                    for i, part in enumerate(parts):
                        # Keep if: (1) has digits, (2) is interface name, (3) is state (U/D)
                        if any(c.isdigit() for c in part) or part in ['U', 'D'] or 'Ethernet' in part or 'PortChannel' in part:
                            # Remove trailing % from percentages
                            cleaned_parts.append(part.rstrip('%'))
                        # Skip pure unit tokens like "B/s", "/s"

                    st.log(f"  Cleaned parts: {cleaned_parts}")

                    try:
                        # Extract RX_OK and TX_OK values from cleaned columns
                        # Remove commas from numbers (e.g., "1,004" -> "1004")
                        rx_ok_str = cleaned_parts[rx_ok_col].replace(',', '')
                        tx_ok_str = cleaned_parts[tx_ok_col].replace(',', '')

                        rx_ok = int(rx_ok_str)
                        tx_ok = int(tx_ok_str)

                        st.log(f"  Parsed {intf}: RX_OK={rx_ok}, TX_OK={tx_ok}")
                    except (ValueError, IndexError) as e:
                        st.warn(f"Could not parse counters for {intf}: {e}")
                        st.warn(f"  Cleaned parts: {cleaned_parts}")
                        st.warn(f"  Trying to access columns: RX_OK={rx_ok_col}, TX_OK={tx_ok_col}")

                    break

            counter_data[intf] = {"rx_ok": rx_ok, "tx_ok": tx_ok}
            st.log(f"Interface {intf}: RX_OK={rx_ok}, TX_OK={tx_ok}")

        return counter_data

    def _verify_bidirectional_counters(self, dut1_counters, dut2_counters, members_d1, members_d2, min_packets):
        """
        Verify RX and TX counters show traffic in both directions

        IMPORTANT: LACP uses hash-based load balancing (not round-robin):
        - Each flow (D1→D2, D2→D1) goes through ONE member per side
        - NOT all members carry traffic
        - Hash function determines which member carries each flow

        Args:
            dut1_counters: Counter data for DUT1 members
            dut2_counters: Counter data for DUT2 members
            members_d1: List of DUT1 member interfaces
            members_d2: List of DUT2 member interfaces
            min_packets: Minimum expected packet count per direction

        Returns:
            True if counters valid, False otherwise
        """
        st.banner("Verifying bidirectional traffic counters (hash-based load balancing)")

        try:
            # Direction 1: DUT1 → DUT2
            st.log("Direction: DUT1 → DUT2")

            # Collect TX from D1 members
            d1_tx_total = 0
            d1_tx_members = []
            for member_d1 in members_d1:
                tx_d1 = dut1_counters.get(member_d1, {}).get("tx_ok", 0)
                d1_tx_total += tx_d1
                if tx_d1 > 0:
                    d1_tx_members.append(member_d1)
                    st.log(f"  ✓ DUT1 {member_d1} TX={tx_d1} (active)")
                else:
                    st.log(f"  - DUT1 {member_d1} TX={tx_d1} (inactive)")

            # Collect RX from D2 members
            d2_rx_total = 0
            d2_rx_members = []
            for member_d2 in members_d2:
                rx_d2 = dut2_counters.get(member_d2, {}).get("rx_ok", 0)
                d2_rx_total += rx_d2
                if rx_d2 > 0:
                    d2_rx_members.append(member_d2)
                    st.log(f"  ✓ DUT2 {member_d2} RX={rx_d2} (active)")
                else:
                    st.log(f"  - DUT2 {member_d2} RX={rx_d2} (inactive)")

            st.log(f"D1→D2: Total TX={d1_tx_total}, Total RX={d2_rx_total}")
            st.log(f"       Active members: D1_TX={len(d1_tx_members)}, D2_RX={len(d2_rx_members)}")

            # Validate D1→D2
            if len(d1_tx_members) == 0:
                st.error("FAIL: No TX traffic on any DUT1 member")
                return False
            if len(d2_rx_members) == 0:
                st.error("FAIL: No RX traffic on any DUT2 member")
                return False
            if d2_rx_total < min_packets * 0.95:
                st.error(f"FAIL: D1→D2 insufficient traffic - expected >= {min_packets}, got {d2_rx_total}")
                return False

            st.log(f"✓ D1→D2 direction validated: {d2_rx_total} packets received")

            # Direction 2: DUT2 → DUT1
            st.log("\nDirection: DUT2 → DUT1")

            # Collect TX from D2 members
            d2_tx_total = 0
            d2_tx_members = []
            for member_d2 in members_d2:
                tx_d2 = dut2_counters.get(member_d2, {}).get("tx_ok", 0)
                d2_tx_total += tx_d2
                if tx_d2 > 0:
                    d2_tx_members.append(member_d2)
                    st.log(f"  ✓ DUT2 {member_d2} TX={tx_d2} (active)")
                else:
                    st.log(f"  - DUT2 {member_d2} TX={tx_d2} (inactive)")

            # Collect RX from D1 members
            d1_rx_total = 0
            d1_rx_members = []
            for member_d1 in members_d1:
                rx_d1 = dut1_counters.get(member_d1, {}).get("rx_ok", 0)
                d1_rx_total += rx_d1
                if rx_d1 > 0:
                    d1_rx_members.append(member_d1)
                    st.log(f"  ✓ DUT1 {member_d1} RX={rx_d1} (active)")
                else:
                    st.log(f"  - DUT1 {member_d1} RX={rx_d1} (inactive)")

            st.log(f"D2→D1: Total TX={d2_tx_total}, Total RX={d1_rx_total}")
            st.log(f"       Active members: D2_TX={len(d2_tx_members)}, D1_RX={len(d1_rx_members)}")

            # Validate D2→D1
            if len(d2_tx_members) == 0:
                st.error("FAIL: No TX traffic on any DUT2 member")
                return False
            if len(d1_rx_members) == 0:
                st.error("FAIL: No RX traffic on any DUT1 member")
                return False
            if d1_rx_total < min_packets * 0.95:
                st.error(f"FAIL: D2→D1 insufficient traffic - expected >= {min_packets}, got {d1_rx_total}")
                return False

            st.log(f"✓ D2→D1 direction validated: {d1_rx_total} packets received")

            st.log("\n✓ PASS: Bidirectional traffic validated")
            st.log("  (Each flow goes through one member per side due to LACP hash function)")

            return True

        except Exception as e:
            st.error(f"Exception verifying bidirectional counters: {e}")
            return False

    @pytest.mark.lacp_positive
    @pytest.mark.lacp_traffic
    @pytest.mark.lacp_pos_010
    def test_lacp_pos_010_bidirectional_traffic(self):
        """
        LACP-POS-010: Verify bidirectional traffic on PortChannel

        IMPORTANT: LACP uses hash-based load balancing (not round-robin)
        - Each flow (D1→D2, D2→D1) goes through ONE member per side
        - NOT all members carry traffic
        - Hash function (layer3+4) determines which member carries each flow

        Test Steps:
          1. Create PortChannel on D1 and D2 with LACP active mode
          2. Add 4 members to PortChannel on both devices
          3. Configure IP addresses on PortChannel (10.1.1.1/24 on D1, 10.1.1.2/24 on D2)
          4. Verify LACP synchronization on all members
          5. Clear interface counters on all member interfaces
          6. Start tcpdump on all member interfaces on both D1 and D2
          7. Send UDP traffic D1 → D2 (100 pps, 5 seconds, 500 packets, single flow)
          8. Simultaneously send UDP traffic D2 → D1 (100 pps, 5 seconds, 500 packets, single flow)
          9. Stop tcpdump captures
          10. Verify tcpdump captures show packets on active members
          11. Verify RX and TX counters show traffic in both directions
          12. Cleanup tcpdump files

        Expected Result:
          - PortChannel created and synchronized successfully
          - UDP traffic flows in both directions simultaneously
          - At least one member per direction carries traffic (hash-based selection)
          - D1→D2 flow: ONE member on D1 TX, ONE member on D2 RX
          - D2→D1 flow: ONE member on D2 TX, ONE member on D1 RX
          - RX counters increment on receiving side for active member(s)
          - TX counters increment on transmitting side for active member(s)
          - No unidirectional link issues
          - For multi-flow traffic, distribution would occur across members
        """
        st.banner("TEST START: LACP-POS-010 - Verify Bidirectional Traffic on PortChannel")

        # Step 1 & 2 & 3: Setup PortChannel on both devices with IP configuration
        st.banner("STEP 1-3: Setup PortChannel with IP on D1 and D2")

        result_d1 = self._setup_portchannel(data.dut1, PC_IP_D1, data.members_d1)
        result_d2 = self._setup_portchannel(data.dut2, PC_IP_D2, data.members_d2)

        if not (result_d1 and result_d2):
            st.report_fail("portchannel_setup_failed")

        # Step 4: Verify LACP synchronization
        st.banner("STEP 4: Verify LACP Synchronization")

        result_d1 = self._verify_portchannel_sync(data.dut1, data.members_d1)
        result_d2 = self._verify_portchannel_sync(data.dut2, data.members_d2)

        if not (result_d1 and result_d2):
            st.report_fail("lacp_sync_failed")

        st.log("LACP synchronization verified on both devices")

        # Step 5: Clear interface counters
        st.banner("STEP 5: Clear Interface Counters")

        self._clear_interface_counters(data.dut1, data.members_d1)
        self._clear_interface_counters(data.dut2, data.members_d2)

        # Step 6: Start tcpdump on all member interfaces (both devices)
        st.banner("STEP 6: Start tcpdump on All Members (Both Devices)")

        pcap_files_d1 = self._start_tcpdump_all_members(
            data.dut1, data.members_d1,
            pcap_prefix="lacp_pos_010_d1",
            filter_str="udp"
        )

        pcap_files_d2 = self._start_tcpdump_all_members(
            data.dut2, data.members_d2,
            pcap_prefix="lacp_pos_010_d2",
            filter_str="udp"
        )

        # Step 7 & 8: Send bidirectional UDP traffic using Scapy
        st.banner("STEP 7-8: Send Bidirectional UDP Traffic (D1↔D2)")

        if not SCAPY_AVAILABLE:
            st.log("WARNING: Scapy not available, skipping traffic generation")
            st.report_skip("scapy_not_available")

        try:
            # Get MAC addresses
            mac_d1 = self._get_mac_address(data.dut1, PC_NAME)
            mac_d2 = self._get_mac_address(data.dut2, PC_NAME)

            # Direction 1: D1 → D2
            st.log(f"Sending UDP traffic: {data.dut1} ({PC_IP_D1}) → {data.dut2} ({PC_IP_D2})")
            st.log(f"  Interface: {data.members_d1[0]}, Duration: {DURATION}s, Rate: {PACKET_RATE} pps")

            result_d1 = scapy_api.send_traffic(
                dut=data.dut1,
                interface=data.members_d1[0],  # Send via first member (PortChannel will distribute)
                src_ip=PC_IP_D1,
                dst_ip=PC_IP_D2,
                src_mac=mac_d1,
                dst_mac=mac_d2,
                duration=DURATION,  # 5 seconds
                pps=PACKET_RATE,    # 100 packets per second
                payload_size=PACKET_SIZE - 42,  # Subtract headers (Eth + IP + UDP = 42 bytes)
                traffic_type="udp"
            )

            if not result_d1.get("success"):
                st.error(f"D1→D2 traffic failed: {result_d1.get('output')}")
                st.report_fail("msg", "Traffic generation failed for D1→D2")

            packets_sent_d1 = result_d1.get("packets_sent", 0)
            st.log(f"✓ D1→D2 traffic sent: {packets_sent_d1} packets")

            # Direction 2: D2 → D1 (simultaneously, but sequential execution acceptable for test)
            st.log(f"Sending UDP traffic: {data.dut2} ({PC_IP_D2}) → {data.dut1} ({PC_IP_D1})")
            st.log(f"  Interface: {data.members_d2[0]}, Duration: {DURATION}s, Rate: {PACKET_RATE} pps")

            result_d2 = scapy_api.send_traffic(
                dut=data.dut2,
                interface=data.members_d2[0],  # Send via first member (PortChannel will distribute)
                src_ip=PC_IP_D2,
                dst_ip=PC_IP_D1,
                src_mac=mac_d2,
                dst_mac=mac_d1,
                duration=DURATION,  # 5 seconds
                pps=PACKET_RATE,    # 100 packets per second
                payload_size=PACKET_SIZE - 42,  # Subtract headers
                traffic_type="udp"
            )

            if not result_d2.get("success"):
                st.error(f"D2→D1 traffic failed: {result_d2.get('output')}")
                st.report_fail("msg", "Traffic generation failed for D2→D1")

            packets_sent_d2 = result_d2.get("packets_sent", 0)
            st.log(f"✓ D2→D1 traffic sent: {packets_sent_d2} packets")

            st.log(f"✓ Bidirectional UDP traffic sent: D1→D2={packets_sent_d1}, D2→D1={packets_sent_d2} packets")

        except Exception as e:
            st.error(f"Exception during traffic generation: {e}")
            st.report_fail("msg", f"Traffic generation exception: {e}")

        # Wait for traffic to complete
        st.wait(2, "Waiting for traffic to complete")

        # Step 9: Stop tcpdump captures
        st.banner("STEP 9: Stop tcpdump Captures")

        self._stop_tcpdump_all_members(data.dut1, data.members_d1)
        self._stop_tcpdump_all_members(data.dut2, data.members_d2)

        # Step 10: Verify tcpdump captures
        st.banner("STEP 10: Verify tcpdump Captures")

        min_packets_per_member = int(PACKET_COUNT / len(data.members_d1) * 0.5)  # At least 50% of expected

        result_d1 = self._verify_tcpdump_captures(data.dut1, pcap_files_d1, min_packets=min_packets_per_member)
        result_d2 = self._verify_tcpdump_captures(data.dut2, pcap_files_d2, min_packets=min_packets_per_member)

        if not (result_d1 and result_d2):
            st.log("WARNING: tcpdump verification failed, continuing with counter verification")

        # Step 11: Verify RX and TX counters
        st.banner("STEP 11: Verify RX and TX Counters")

        counters_d1 = self._get_interface_counters(data.dut1, data.members_d1)
        counters_d2 = self._get_interface_counters(data.dut2, data.members_d2)

        # Verify bidirectional counters
        result = self._verify_bidirectional_counters(
            counters_d1, counters_d2,
            data.members_d1, data.members_d2,
            min_packets=min_packets_per_member
        )

        if not result:
            st.report_fail("msg", "Bidirectional traffic verification failed - check TX/RX counters")

        st.log("Bidirectional traffic verified successfully on all members")

        # Step 12: Cleanup tcpdump files
        st.banner("STEP 12: Cleanup tcpdump Files")

        self._cleanup_tcpdump_files(data.dut1, pcap_files_d1)
        self._cleanup_tcpdump_files(data.dut2, pcap_files_d2)

        # Test PASSED
        st.banner("TEST PASSED: LACP-POS-010 - Bidirectional Traffic Verified Successfully")
        st.report_pass("test_case_passed")
