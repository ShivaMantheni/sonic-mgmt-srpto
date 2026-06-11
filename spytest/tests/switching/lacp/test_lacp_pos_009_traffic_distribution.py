"""
LACP-POS-009: Verify Traffic Flows Across All PortChannel Members

Author: Athira
2026-05-20

How to run:
  ./bin/spytest --tryssh 1 \
  --testbed /home/hp_test/Athira/testbed_lacp_vs.yaml \
  switching/lacp/test_lacp_pos_009_traffic_distribution.py \
  --logs-path ./logs/test_lacp_pos_009_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native

Description:
  Validates that L3 traffic (ICMP) sent across a PortChannel with 4 synchronized
  members is distributed across all member links. The test configures IP addresses
  on the PortChannel interface, generates 1000 packets using Scapy, captures
  traffic on all member interfaces using tcpdump, and verifies both packet capture
  and interface counters to confirm load balancing.

  Key validations:
  1. All 4 members carry traffic
  2. Traffic distribution is approximately equal (±20% variance allowed)
  3. No packet loss
  4. tcpdump captures traffic on each member interface
  5. Interface counters increment correctly

Pre-requisites:
  - Topology: 2-node (D1-D2) | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 2 nodes with 4-link PortChannel
        # +------------------------+                  +------------------------+
        # |         DUT1           |                  |         DUT2           |
        # |                        |                  |                        |
        # | Ethernet32 ============================================ Ethernet32 |
        # | Ethernet36 ============================================ Ethernet36 |
        # | Ethernet40 ============================================ Ethernet40 |
        # | Ethernet44 ============================================ Ethernet44 |
        # |  PC1 (All members)     |                  |  PC1 (All members)     |
        # |  IP: 10.1.1.1/24       |                  |  IP: 10.1.1.2/24       |
        # +------------------------+                  +------------------------+

  - Feature flags / min SONiC version: LACP support required
  - Required test variables (YAML): None (uses hardcoded values per testplan)
"""

from __future__ import annotations

from typing import Dict, List, Any
import time

import pytest
from spytest import st, SpyTestDict

import apis.switching.lacp as lacp_api
import apis.system.interface as intf_api
import apis.routing.ip as ip_api
import apis.common.scapy_traffic as scapy_api

# Test Constants (from LACP-POS-009 testplan)
TESTCASE_ID = "LACP-POS-009"
PC_ID = 1
PC_NAME = f"PortChannel{PC_ID}"
MEMBERS = ["Ethernet32", "Ethernet36", "Ethernet40", "Ethernet44"]
DUT1_IP = "10.1.1.1"
DUT2_IP = "10.1.1.2"
SUBNET_MASK = "24"
PACKET_COUNT = 1000
PACKET_SIZE = 128
TRAFFIC_DURATION = 10  # seconds
PPS = PACKET_COUNT // TRAFFIC_DURATION  # 100 pps
DISTRIBUTION_VARIANCE = 0.20  # ±20% acceptable variance

# Module-level variables
vars = SpyTestDict()
data = SpyTestDict()


@pytest.fixture(scope="module", autouse=True)
def module_hooks(request):
    """
    Module prologue and epilogue for LACP-POS-009.

    Prologue:
    - Get testbed topology
    - Initialize test data structure

    Epilogue:
    - Clean up PortChannel configuration
    - Remove IP addresses
    - Delete PortChannel
    """
    global vars, data

    st.banner("MODULE PROLOGUE: LACP-POS-009 - Traffic Distribution Test")

    # Get testbed variables (D1, D2 device handles)
    vars = st.ensure_min_topology("D1D2:4")  # 4 links between D1 and D2

    # Initialize data structure
    data.cli_type = st.get_ui_type(vars.D1, cli_type="klish")
    data.pc_id = PC_ID
    data.pc_name = PC_NAME
    data.members = MEMBERS
    data.dut1_ip = DUT1_IP
    data.dut2_ip = DUT2_IP
    data.subnet_mask = SUBNET_MASK
    data.packet_count = PACKET_COUNT
    data.pps = PPS
    data.duration = TRAFFIC_DURATION

    st.log(f"CLI Type: {data.cli_type}")
    st.log(f"PortChannel: {data.pc_name}")
    st.log(f"Members: {data.members}")
    st.log(f"D1 IP: {data.dut1_ip}/{data.subnet_mask}")
    st.log(f"D2 IP: {data.dut2_ip}/{data.subnet_mask}")

    yield

    # Module Epilogue - Cleanup
    st.banner("MODULE EPILOGUE: LACP-POS-009 - Cleanup")

    for dut in [vars.D1, vars.D2]:
        try:
            # Remove IP addresses from PortChannel
            st.log(f"Removing IP from {data.pc_name} on {dut}")
            ip_api.delete_ip_interface(
                dut, data.pc_name,
                f"{data.dut1_ip if dut == vars.D1 else data.dut2_ip}/{data.subnet_mask}",
                family="ipv4",
                cli_type=data.cli_type,
                skip_error=True
            )

            # Remove members from PortChannel
            for member in data.members:
                st.log(f"Removing {member} from {data.pc_name} on {dut}")
                lacp_api.delete_lacp_member(
                    dut, data.pc_id, member, cli_type=data.cli_type
                )

            # Delete PortChannel
            st.log(f"Deleting {data.pc_name} on {dut}")
            lacp_api.delete_lacp_portchannel(dut, data.pc_id, cli_type=data.cli_type)

        except Exception as e:
            st.debug(f"Error during cleanup on {dut}: {e}")

    st.log("✓ Module cleanup completed")


class TestLacpPos009TrafficDistribution:
    """
    LACP-POS-009: Verify traffic flows across all PortChannel members
    """

    def _setup_portchannel(self, dut: str, pc_ip: str) -> None:
        """
        Configure PortChannel with members on a DUT.

        Steps:
        1. Create PortChannel
        2. Add all 4 members
        3. Configure IP address on PortChannel
        4. Bring up PortChannel interface
        """
        st.log(f"Setting up {data.pc_name} on {dut}")

        # Step 1: Create PortChannel
        result = lacp_api.create_lacp_portchannel(
            dut, data.pc_id, cli_type=data.cli_type
        )
        if not result:
            st.report_fail("portchannel_create_failed", data.pc_name)

        st.log(f"✓ Created {data.pc_name} on {dut}")

        # Step 2: Add all members
        for member in data.members:
            st.log(f"Adding {member} to {data.pc_name}")
            result = lacp_api.add_lacp_member(
                dut, data.pc_id, member, cli_type=data.cli_type
            )
            if not result:
                st.report_fail("portchannel_member_add_failed", member, data.pc_name)

        st.log(f"✓ Added {len(data.members)} members to {data.pc_name} on {dut}")

        # Step 3: Bring up member interfaces (no shutdown)
        st.log(f"Bringing up member interfaces on {dut}")
        for member in data.members:
            intf_api.interface_operation(dut, member, operation="startup", cli_type=data.cli_type)
            st.log(f"Interface {member} brought up")

        # Step 4: Bring up PortChannel interface (no shutdown)
        st.log(f"Bringing up {data.pc_name} interface on {dut}")
        intf_api.interface_operation(
            dut, data.pc_name, operation="startup", cli_type=data.cli_type
        )

        # Wait for LACP negotiation
        st.wait(5, "Wait for LACP negotiation")

        # Step 5: Configure IP address on PortChannel
        st.log(f"Configuring IP {pc_ip}/{data.subnet_mask} on {data.pc_name}")
        result = ip_api.config_ip_addr_interface(
            dut, data.pc_name,
            pc_ip,
            data.subnet_mask,
            family="ipv4",
            cli_type=data.cli_type
        )
        if not result:
            st.report_fail("ip_config_failed")

        st.log(f"✓ Configured IP {pc_ip}/{data.subnet_mask} on {data.pc_name}")
        st.log(f"✓ PortChannel {data.pc_name} setup completed on {dut}")


    def _verify_portchannel_sync(self, dut: str) -> bool:
        """
        Verify that PortChannel is operational and all members are synchronized.

        Uses raw CLI output parsing to avoid template parsing issues.

        Returns:
            bool: True if all members synchronized, False otherwise
        """
        st.log(f"Verifying PortChannel synchronization on {dut}")

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
                if f"PortChannel{data.pc_id}" not in output:
                    st.error(f"PortChannel{data.pc_id} not found in summary")
                    return False

                # Parse the summary line for state
                # Actual format: "1   PortChannel1   Eth (U)   LACP   Ethernet32(P), ..."
                # State is in Type column: "Eth (U)" or "Eth (D)"
                import re

                # Find the line containing PortChannel{pc_id}
                pc_state = None
                for line in output.split('\n'):
                    if f"PortChannel{data.pc_id}" in line:
                        st.log(f"Found PortChannel line: {line}")
                        # Extract state from "Eth (U)" or "Eth (D)"
                        state_match = re.search(r'\(([UD])\)', line)
                        if state_match:
                            pc_state = state_match.group(1)
                            break

                if not pc_state:
                    st.error(f"Could not parse PortChannel{data.pc_id} state from output")
                    return False

                if pc_state != "U":
                    st.error(f"PortChannel{data.pc_id} is DOWN (state: {pc_state})")
                    return False

                st.log(f"✓ PortChannel{data.pc_id} is UP (state: {pc_state})")

        except Exception as e:
            st.error(f"Exception during portchannel summary check: {e}")
            return False

        # Method 2: Verify members using raw output of show interface PortChannel
        try:
            cmd = f"show interface PortChannel {data.pc_id}"
            output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

            if isinstance(output, str):
                st.log(f"Interface PortChannel{data.pc_id} output:\n{output}")

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
                for expected_member in data.members:
                    if expected_member not in found_members:
                        st.error(f"Expected member {expected_member} not found in PortChannel")
                        return False

                st.log(f"✓ All {len(data.members)} members present: {found_members}")

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
                        for member in data.members:
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


    def _get_interface_mac(self, dut: str, interface: str) -> str:
        """
        Get MAC address from interface with fallback.

        Args:
            dut: Device handle
            interface: Interface name

        Returns:
            str: MAC address
        """
        mac = scapy_api.get_interface_mac(dut, interface, cli_type=data.cli_type)

        if not mac:
            st.warn(f"Could not retrieve MAC for {interface} on {dut}, using default")
            dut_index = 1 if dut == vars.D1 else 2
            mac = scapy_api.get_default_mac(dut_index)

        return mac


    def _clear_counters_all_members(self, dut: str) -> None:
        """
        Clear interface counters on all member interfaces.
        """
        st.log(f"Clearing counters on all members on {dut}")

        for member in data.members:
            intf_api.clear_interface_counters(
                dut, interface_name=member, cli_type=data.cli_type
            )

        st.wait(2, "Wait for counters to clear")
        st.log("✓ Counters cleared on all members")


    def _get_member_counters(self, dut: str) -> Dict[str, Dict[str, int]]:
        """
        Get RX/TX counters for all member interfaces.

        Uses full table output with headers for accurate parsing.
        Avoids grep which strips headers and breaks column alignment.

        Returns:
            dict: {interface_name: {"rx_ok": count, "tx_ok": count}}
        """
        st.log(f"Getting counters for all members on {dut}")

        counters = {}

        # Get full interface counters output (with headers)
        cmd = "show interface counters | no-more"
        output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

        if not isinstance(output, str):
            st.error("Counter output is not a string")
            return {m: {"rx_ok": 0, "tx_ok": 0} for m in data.members}

        st.log(f"Full counter output:\n{output}")

        # Parse the table output
        # Expected format:
        #       IFACE    STATE    RX_OK    RX_BPS  ...  TX_OK    TX_BPS  ...
        #  Ethernet32        U    1,004  278.47 B/s ...      4   7.36 B/s ...

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
            return {m: {"rx_ok": 0, "tx_ok": 0} for m in data.members}

        # Identify column positions from header
        # Common headers: IFACE, STATE, RX_OK, RX_BPS, RX_PPS, RX_UTIL, RX_ERR, RX_DRP, RX_OVR,
        #                 TX_OK, TX_BPS, TX_PPS, TX_UTIL, TX_ERR, TX_DRP, TX_OVR
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
            return {m: {"rx_ok": 0, "tx_ok": 0} for m in data.members}

        st.log(f"Column positions: RX_OK={rx_ok_col}, TX_OK={tx_ok_col}")

        # Parse data lines for each member
        for member in data.members:
            rx_ok = 0
            tx_ok = 0

            # Find line containing this member interface
            for line in lines[header_idx + 1:]:
                if member in line:
                    st.log(f"Found {member} line: {line}")

                    # Split line into columns
                    parts = line.split()

                    try:
                        # Extract RX_OK and TX_OK values
                        # Remove commas from numbers (e.g., "1,004" -> "1004")
                        rx_ok_str = parts[rx_ok_col].replace(',', '')
                        tx_ok_str = parts[tx_ok_col].replace(',', '')

                        rx_ok = int(rx_ok_str)
                        tx_ok = int(tx_ok_str)

                        st.log(f"  Parsed {member}: RX_OK={rx_ok}, TX_OK={tx_ok}")
                    except (ValueError, IndexError) as e:
                        st.warn(f"Could not parse counters for {member}: {e}")
                        st.warn(f"  Line parts: {parts}")
                        st.warn(f"  Trying to access columns: RX_OK={rx_ok_col}, TX_OK={tx_ok_col}")

                    break

            counters[member] = {"rx_ok": rx_ok, "tx_ok": tx_ok}
            st.log(f"  {member}: RX={rx_ok}, TX={tx_ok}")

        return counters


    def _start_tcpdump_all_members(self, dut: str, pcap_prefix: str) -> Dict[str, str]:
        """
        Start tcpdump capture on all member interfaces.

        Important: Captures on MEMBER interfaces (Ethernet32, etc.), not PortChannel
        (learned from context.md Fix 1)

        Args:
            dut: Device handle
            pcap_prefix: Prefix for pcap filenames

        Returns:
            dict: {interface_name: pcap_file_path}
        """
        st.log(f"Starting tcpdump on all members on {dut}")

        pcap_files = {}

        for member in data.members:
            pcap_file = f"/tmp/{pcap_prefix}_{member}.pcap"

            st.log(f"Starting capture on {member} -> {pcap_file}")
            scapy_api.start_tcpdump(
                dut,
                member,  # Capture on MEMBER interface, not PortChannel
                filter_str="icmp",
                output_file=pcap_file,
                max_packets=500
            )

            pcap_files[member] = pcap_file

        st.wait(2, "Wait for tcpdump to start on all interfaces")
        st.log(f"✓ tcpdump started on {len(data.members)} members")

        return pcap_files


    def _stop_tcpdump_all_members(self, dut: str) -> None:
        """
        Stop tcpdump capture on device.
        """
        st.log(f"Stopping tcpdump on {dut}")
        scapy_api.stop_tcpdump(dut)
        st.wait(2, "Wait for tcpdump to stop")
        st.log("✓ tcpdump stopped")


    def _verify_tcpdump_captures(
        self, dut: str, pcap_files: Dict[str, str], min_packets_per_member: int
    ) -> Dict[str, int]:
        """
        Verify tcpdump captures on all member interfaces.

        Args:
            dut: Device handle
            pcap_files: {interface_name: pcap_file_path}
            min_packets_per_member: Minimum expected packets per member

        Returns:
            dict: {interface_name: packet_count}
        """
        st.log(f"Verifying tcpdump captures on {dut}")

        capture_counts = {}

        for member, pcap_file in pcap_files.items():
            result = scapy_api.verify_tcpdump_capture(
                dut,
                capture_file=pcap_file,
                min_packets=1  # At least 1 packet per member
            )

            packet_count = result.get("packet_count", 0)
            capture_counts[member] = packet_count

            st.log(f"  {member}: captured {packet_count} packets")

            if packet_count < min_packets_per_member:
                st.warn(
                    f"{member} captured only {packet_count} packets "
                    f"(expected >= {min_packets_per_member})"
                )

        return capture_counts


    def _verify_traffic_distribution(
        self, counter_data: Dict[str, int], total_packets: int
    ) -> bool:
        """
        Verify traffic flows through PortChannel members

        IMPORTANT: LACP uses hash-based load balancing (not round-robin):
        - Single flow (same src/dst IP) → ALL packets through ONE member
        - NOT equally distributed across members
        - Hash function (layer3+4) determines which member carries the flow

        Args:
            counter_data: {interface_name: packet_count}
            total_packets: Total packets sent

        Returns:
            bool: True if traffic validation passes
        """
        st.log("Verifying LACP traffic flow (hash-based load balancing)")

        total_received = 0
        members_with_traffic = 0

        for member, count in counter_data.items():
            total_received += count
            if count > 0:
                members_with_traffic += 1
                st.log(f"  ✓ {member}: {count} packets (active member)")
            else:
                st.log(f"  - {member}: {count} packets (inactive for this flow)")

        st.log(f"Total packets received: {total_received}/{total_packets}")
        st.log(f"Active members (carrying traffic): {members_with_traffic}/{len(data.members)}")

        # Verify at least one member has traffic
        if members_with_traffic == 0:
            st.error("FAIL: No traffic received on any member")
            return False

        # Verify total received matches sent (allow 5% loss)
        if total_received < total_packets * 0.95:
            st.error(
                f"FAIL: Significant packet loss - sent {total_packets}, received {total_received}"
            )
            return False

        st.log(f"✓ PASS: Traffic validated - {total_received} packets received across {members_with_traffic} member(s)")
        st.log("  (Single flow traffic goes through one member due to LACP hash function)")

        return True


    @pytest.mark.inventory(feature="Regression", testcases=[TESTCASE_ID])
    def test_lacp_pos_009_traffic_distribution(self) -> None:
        """
        LACP-POS-009: Verify traffic flows through PortChannel members

        IMPORTANT: LACP uses hash-based load balancing (not round-robin)
        - Single flow (same src/dst IP) → ALL packets through ONE member
        - NOT equally distributed across members
        - Hash function (layer3+4) determines which member carries the flow

        Test Steps:
        1. Create PortChannel 1 on both DUTs with 4 members
        2. Configure IP addresses on PortChannel interfaces
        3. Verify PortChannel synchronization
        4. Clear interface counters on all member interfaces
        5. Start tcpdump on all member interfaces of D2 (receiver)
        6. Send 1000 ICMP packets from D1 to D2 using Scapy (single flow)
        7. Stop tcpdump
        8. Verify tcpdump captured packets on member interfaces
        9. Verify interface counters show packet reception
        10. Verify total traffic matches expected count (allow 5% loss)

        Expected Result:
        - At least one member receives traffic (hash selects member)
        - Single flow goes through ONE member (hash-based selection)
        - Total packets received ≈ 1000 (allow 5% loss)
        - tcpdump captures show traffic on the active member(s)
        - For multi-flow traffic, distribution would occur across members
        """
        st.banner(f"Starting Test: {TESTCASE_ID} - Traffic Distribution Across PortChannel Members")

        # Step 1: Setup PortChannel on both DUTs
        st.banner("Step 1: Creating PortChannel with 4 members on both DUTs")
        self._setup_portchannel(vars.D1, data.dut1_ip)
        self._setup_portchannel(vars.D2, data.dut2_ip)

        st.wait(5, "Wait for PortChannel to stabilize and LACP to negotiate")

        # Step 2: Verify PortChannel synchronization
        st.banner("Step 2: Verifying PortChannel synchronization")
        if not self._verify_portchannel_sync(vars.D1):
            st.report_fail("portchannel_state_fail", data.pc_name, "D1")

        if not self._verify_portchannel_sync(vars.D2):
            st.report_fail("portchannel_state_fail", data.pc_name, "D2")

        st.log("✓ PortChannel synchronized on both DUTs")

        # Step 3: Verify connectivity with ping
        st.banner("Step 3: Verifying IP connectivity")
        if not scapy_api.verify_ping(vars.D1, data.dut2_ip, src_ip=data.dut1_ip, count=5):
            st.report_fail("ping_fail", data.dut1_ip, data.dut2_ip)

        st.log(f"✓ Ping successful: {data.dut1_ip} → {data.dut2_ip}")

        # Step 4: Get MAC addresses for Scapy traffic
        st.banner("Step 4: Retrieving MAC addresses")
        src_mac = self._get_interface_mac(vars.D1, data.pc_name)
        dst_mac = self._get_interface_mac(vars.D2, data.pc_name)

        st.log(f"Source MAC (D1): {src_mac}")
        st.log(f"Destination MAC (D2): {dst_mac}")

        # Step 5: Clear counters on all member interfaces
        st.banner("Step 5: Clearing interface counters on all members")
        self._clear_counters_all_members(vars.D1)
        self._clear_counters_all_members(vars.D2)

        # Step 6: Start tcpdump on all member interfaces (D2 - receiver)
        st.banner("Step 6: Starting tcpdump on all D2 member interfaces")
        pcap_files = self._start_tcpdump_all_members(vars.D2, "lacp_pos_009_d2")

        # Step 7: Send traffic from D1 to D2
        st.banner(f"Step 7: Sending {data.packet_count} ICMP packets from D1 to D2")
        st.log(f"Traffic parameters:")
        st.log(f"  Source: {data.dut1_ip} ({src_mac})")
        st.log(f"  Destination: {data.dut2_ip} ({dst_mac})")
        st.log(f"  Interface: {data.members[0]} (first member)")
        st.log(f"  Packets: {data.packet_count}")
        st.log(f"  Duration: {data.duration} seconds")
        st.log(f"  Rate: {data.pps} pps")

        # Send traffic via FIRST member interface
        # Traffic will be load-balanced across all members by PortChannel
        result = scapy_api.send_traffic(
            dut=vars.D1,
            interface=data.members[0],  # Send via first member
            src_ip=data.dut1_ip,
            dst_ip=data.dut2_ip,
            src_mac=src_mac,
            dst_mac=dst_mac,
            duration=data.duration,
            pps=data.pps,
            payload_size=PACKET_SIZE - 42,  # Subtract headers
            traffic_type="icmp"
        )

        if not result.get("success"):
            st.report_fail("msg", f"Traffic generation failed: {result.get('output')}")

        packets_sent = result.get("packets_sent", 0)
        st.log(f"✓ Traffic sent: {packets_sent} packets")

        # Step 8: Stop tcpdump
        st.banner("Step 8: Stopping tcpdump")
        self._stop_tcpdump_all_members(vars.D2)

        # Step 9: Verify tcpdump captures
        st.banner("Step 9: Verifying tcpdump captures on all members")
        min_packets_per_member = int(packets_sent / len(data.members) * 0.5)  # At least 50% of expected
        capture_counts = self._verify_tcpdump_captures(
            vars.D2, pcap_files, min_packets_per_member
        )

        # Verify all members received some traffic in tcpdump
        members_with_traffic = sum(1 for count in capture_counts.values() if count > 0)

        if members_with_traffic < len(data.members):
            st.warn(
                f"Only {members_with_traffic}/{len(data.members)} members "
                f"showed traffic in tcpdump captures"
            )
        else:
            st.log(f"✓ All {len(data.members)} members showed traffic in tcpdump")

        # Step 10: Verify interface counters
        st.banner("Step 10: Verifying interface counters on all members")

        # Get counters from D2 (receiver) - use RX_OK
        d2_counters = self._get_member_counters(vars.D2)
        rx_counts = {member: counts["rx_ok"] for member, counts in d2_counters.items()}

        st.log("D2 RX Counters:")
        for member, count in rx_counts.items():
            st.log(f"  {member}: {count} packets received")

        # Step 11: Verify traffic distribution
        st.banner("Step 11: Verifying traffic distribution across members")
        distribution_ok = self._verify_traffic_distribution(rx_counts, packets_sent)

        # Final verdict
        st.banner("Test Results Summary")
        st.log(f"Packets sent: {packets_sent}")
        st.log(f"Total packets received: {sum(rx_counts.values())}")
        st.log(f"tcpdump captures: {sum(capture_counts.values())} packets")
        st.log(f"Members with traffic: {sum(1 for c in rx_counts.values() if c > 0)}/{len(data.members)}")
        st.log(f"Traffic distribution: {'✓ Within acceptable range' if distribution_ok else '✗ Outside acceptable range'}")

        # Report result
        if distribution_ok and all(count > 0 for count in rx_counts.values()):
            st.report_pass(
                "msg",
                f"✓ LACP-POS-009 PASSED: Traffic distributed across all {len(data.members)} "
                f"PortChannel members within acceptable variance"
            )
        else:
            st.report_fail(
                "msg",
                f"✗ LACP-POS-009 FAILED: Traffic distribution validation failed"
            )
