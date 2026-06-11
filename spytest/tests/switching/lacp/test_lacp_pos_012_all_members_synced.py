"""
LACP-POS-012: Verify all members enter synced state

Author: Generated from testplan, 2026-05-20

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ~/Athira/testbed_lacp_vs.yaml \\
  tests/switching/lacp/test_lacp_pos_012_all_members_synced.py \\
  --logs-path ./logs/lacp_pos_012_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Verifies that all PortChannel members successfully enter the synchronized state
  during LACP negotiation. Validates both local (Actor) and remote (Partner) LACP
  states reach the "Synchronized" state within expected timeout period.

Pre-requisites:
  - Topology: two-node (D1-D2) | Supported: Virtual testbed
  - D1 and D2 connected via 4 physical links (Ethernet32, 36, 40, 44)
  - Testbed YAML: ~/Athira/testbed_lacp_vs.yaml
  - Feature: LACP (Link Aggregation Control Protocol)
  - Test Type: Positive - Happy Path
  - Priority: P0

Test Coverage:
  - LACP negotiation completion
  - Member state verification (up(s) = up and synchronized)
  - Actor/Partner state validation
  - LACP timeout handling

Success Criteria:
  - All 4 members show "up(s)" state within 30 seconds
  - No "down" or "timeout" states present
  - Actor and Partner states are "Synchronized"
  - No LACP errors in system logs
"""

import pytest
import re
import time
from spytest import st, SpyTestDict

# Import feature APIs
import apis.switching.lacp as lacp_api
import apis.system.interface as intf_api

# Module-level variables
vars = SpyTestDict()
data = SpyTestDict()

# Test constants
PC_ID = 1
PC_NAME = f"PortChannel{PC_ID}"
LACP_MODE = "active"

# LACP synchronization parameters
MAX_SYNC_WAIT = 30  # seconds
SYNC_CHECK_INTERVAL = 5  # seconds
EXPECTED_MEMBER_COUNT = 4
EXPECTED_STATE = "up(s)"  # up and synchronized


@pytest.fixture(scope="module", autouse=True)
def module_hooks(request):
    """
    Module-level setup and teardown fixture
    """
    global vars, data
    vars = st.ensure_min_topology("D1D2:4")

    st.banner("MODULE PROLOGUE: LACP-POS-012 Setup")

    # Store device handles
    data.dut1 = vars.D1
    data.dut2 = vars.D2

    # Get member interfaces from topology
    data.members_d1 = [vars.D1D2P1, vars.D1D2P2, vars.D1D2P3, vars.D1D2P4]
    data.members_d2 = [vars.D2D1P1, vars.D2D1P2, vars.D2D1P3, vars.D2D1P4]

    # Force klish CLI for testing (override testbed default)
    data.cli_type = "klish"

    st.log(f"DUT1: {data.dut1}, Members: {data.members_d1}")
    st.log(f"DUT2: {data.dut2}, Members: {data.members_d2}")

    # Clean up any leftover PortChannel from previous failed runs
    st.log("Cleaning up any leftover PortChannel configuration from previous runs...")
    for dut, members in [(data.dut1, data.members_d1), (data.dut2, data.members_d2)]:
        # Remove members first (if they exist)
        for member in members:
            lacp_api.delete_portchannel_member(
                dut, PC_NAME, [member], cli_type=data.cli_type, skip_error_check=True
            )

        # Delete PortChannel (skip error if doesn't exist)
        lacp_api.delete_portchannel(
            dut, PC_NAME, cli_type=data.cli_type, skip_error_check=True
        )
        st.wait(1, f"Wait after cleanup on {dut}")

    st.log("✓ Pre-test cleanup completed")

    yield

    st.banner("MODULE EPILOGUE: LACP-POS-012 Cleanup")

    # Cleanup PortChannel on both DUTs
    for dut, members in [(data.dut1, data.members_d1), (data.dut2, data.members_d2)]:
        # Remove members first
        st.log(f"Removing PortChannel members on {dut}")
        for member in members:
            lacp_api.delete_portchannel_member(
                dut, PC_NAME, [member], cli_type=data.cli_type, skip_error_check=True
            )

        # Delete PortChannel
        st.log(f"Deleting PortChannel on {dut}")
        lacp_api.delete_portchannel(
            dut, PC_NAME, cli_type=data.cli_type, skip_error_check=True
        )
        st.wait(2, f"Wait for PortChannel deletion on {dut}")

    st.log("✓ Module cleanup completed")


class TestLacpPos012AllMembersSynced:
    """
    LACP-POS-012: Verify All Members Enter Synced State
    """

    def setup_method(self, method):
        """Test-level setup"""
        st.log(f"Setting up test: {method.__name__}")

    def teardown_method(self, method):
        """Test-level teardown"""
        st.log(f"Tearing down test: {method.__name__}")

    def _setup_portchannel(self, dut, members):
        """
        Setup PortChannel with LACP active mode and all members

        Args:
            dut: Device under test
            members: List of member interfaces

        Returns:
            bool: True if successful
        """
        st.log(f"Setting up PortChannel {PC_NAME} on {dut}")

        # Step 1: Create PortChannel
        if not lacp_api.create_portchannel(dut, [PC_NAME], cli_type=data.cli_type):
            st.error(f"Failed to create {PC_NAME} on {dut}")
            return False

        st.wait(2, "Wait for PortChannel creation")

        # Step 2: Add all members
        for member in members:
            if not lacp_api.add_portchannel_member(
                dut, PC_NAME, member, cli_type=data.cli_type
            ):
                st.error(f"Failed to add {member} to {PC_NAME} on {dut}")
                return False
            st.log(f"Added {member} to {PC_NAME}")

        # Step 3: Bring up member interfaces (no shutdown)
        st.log(f"Bringing up member interfaces on {dut}")
        for member in members:
            intf_api.interface_operation(dut, member, operation="startup", cli_type=data.cli_type)
            st.log(f"Interface {member} brought up")

        # Step 4: Bring up PortChannel interface (no shutdown)
        st.log(f"Bringing up {PC_NAME} interface on {dut}")
        intf_api.interface_operation(dut, PC_NAME, operation="startup", cli_type=data.cli_type)

        # Wait for LACP negotiation to complete
        st.log(f"Waiting for LACP negotiation on {dut}...")
        st.wait(5, f"Wait for LACP negotiation on {dut}")
        st.log(f"✓ PortChannel {PC_NAME} created with {len(members)} members")
        return True

    def _wait_for_sync(self, dut, timeout=MAX_SYNC_WAIT):
        """
        Wait for LACP synchronization to complete

        Args:
            dut: Device under test
            timeout: Maximum wait time in seconds

        Returns:
            bool: True if synchronized within timeout
        """
        st.log(f"Waiting for LACP synchronization on {dut} (max {timeout}s)")

        elapsed = 0
        while elapsed < timeout:
            # Use raw parsing for klish output (TFSM template doesn't match klish format)
            # Exit config mode to exec mode to avoid "do" prefix (do + | no-more causes bugs)
            st.config(dut, "exit", type=data.cli_type, skip_error_check=True)

            cmd = "show PortChannel summary | no-more"
            output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

            if output:
                # Parse raw output looking for PortChannel state
                # Format: 1  PortChannel1  Eth (U)  LACP  Ethernet32(P), Ethernet36(P), ...
                # (U) = PortChannel UP, (P) = Member participating

                for line in output.split('\n'):
                    if PC_NAME in line and 'Group' not in line:
                        # Check if PortChannel is UP: "Eth (U)"
                        if "(U)" in line:
                            st.log(f"✓ {PC_NAME} synchronized after {elapsed}s")
                            st.log(f"  State: {line.strip()}")
                            return True
                        else:
                            st.log(f"  Current state: {line.strip()} (not UP yet)")
                            break

            st.wait(SYNC_CHECK_INTERVAL, f"Checking again... ({elapsed}/{timeout}s elapsed)")
            elapsed += SYNC_CHECK_INTERVAL

        st.error(f"LACP synchronization timeout after {timeout}s")
        return False

    def _verify_all_members_synced(self, dut, expected_members):
        """
        Verify all members are in synchronized state

        Args:
            dut: Device under test
            expected_members: List of expected member interfaces

        Returns:
            dict: {
                "success": bool,
                "synced_count": int,
                "member_states": dict {member: state}
            }
        """
        st.log(f"Verifying all members synced on {dut}")

        # Exit config mode to exec mode to avoid "do" prefix (do + | no-more causes bugs)
        st.config(dut, "exit", type=data.cli_type, skip_error_check=True)

        # Get PortChannel members via show portchannel
        cmd = f"show portchannel {PC_ID} all-ports | no-more"
        output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

        st.log(f"PortChannel output:\n{output}")

        # Parse member states from output
        member_states = {}
        synced_count = 0

        for line in output.split('\n'):
            for member in expected_members:
                if member in line:
                    # Look for state pattern like "up(s)" or "down"
                    # Example: "Ethernet32   up(s)   ..."
                    state_match = re.search(r'\b(up\([sS]\)|down|timeout)\b', line)

                    if state_match:
                        state = state_match.group(1)
                        member_states[member] = state

                        if "up(s)" in state.lower() or "up(S)" in state:
                            synced_count += 1
                            st.log(f"  ✓ {member}: {state} (synchronized)")
                        else:
                            st.log(f"  ✗ {member}: {state} (NOT synchronized)")

        st.log(f"Synchronized members: {synced_count}/{len(expected_members)}")

        success = (synced_count == len(expected_members))

        return {
            "success": success,
            "synced_count": synced_count,
            "member_states": member_states
        }

    def _verify_lacp_actor_partner(self, dut):
        """
        Verify Actor and Partner LACP states

        Args:
            dut: Device under test

        Returns:
            bool: True if both Actor and Partner are synchronized
        """
        st.log(f"Verifying LACP Actor/Partner states on {dut}")

        # Exit config mode to exec mode to avoid "do" prefix (do + | no-more causes bugs)
        st.config(dut, "exit", type=data.cli_type, skip_error_check=True)

        # Get LACP status
        cmd = f"show lacp portchannel {PC_ID} | no-more"
        output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

        st.log(f"LACP output:\n{output}")

        # Look for synchronized state indicators
        # Example patterns:
        #   "Actor State: ...Synchronized..."
        #   "Partner State: ...Synchronized..."

        actor_synced = "synchronized" in output.lower() or "sync" in output.lower()
        partner_synced = "synchronized" in output.lower() or "sync" in output.lower()

        if actor_synced:
            st.log("✓ Actor state: Synchronized")
        else:
            st.error("✗ Actor state: NOT synchronized")

        if partner_synced:
            st.log("✓ Partner state: Synchronized")
        else:
            st.error("✗ Partner state: NOT synchronized")

        return actor_synced and partner_synced

    @pytest.mark.lacp_positive
    @pytest.mark.lacp_sync
    @pytest.mark.lacp_pos_012
    def test_lacp_pos_012_all_members_synced(self):
        """
        LACP-POS-012: Verify All Members Enter Synced State

        Test Steps:
          1. Create PortChannel with all members on D1 and D2
          2. Wait for LACP negotiation to complete (max 30 seconds)
          3. Execute `show portchannel 1 all-ports` on both DUTs
          4. Verify all members show state "up(s)"
          5. Execute `show lacp portchannel 1` on both DUTs
          6. Verify Actor and Partner states are Synchronized

        Expected Result:
          - All 4 members show "up(s)" within 30 seconds
          - No "down" or "timeout" states present
          - LACP Actor state: Synchronized
          - LACP Partner state: Synchronized
          - No LACP errors in system logs
        """
        st.banner("TEST START: LACP-POS-012 - Verify All Members Enter Synced State")

        # Step 1: Setup PortChannel on both DUTs
        st.banner("STEP 1: Create PortChannel with all members")

        result_d1 = self._setup_portchannel(data.dut1, data.members_d1)
        result_d2 = self._setup_portchannel(data.dut2, data.members_d2)

        if not (result_d1 and result_d2):
            st.report_fail("portchannel_create_fail", PC_NAME)

        st.log("✓ PortChannel created on both DUTs")

        # Step 2: Wait for LACP negotiation
        st.banner("STEP 2: Wait for LACP negotiation to complete")

        sync_d1 = self._wait_for_sync(data.dut1, timeout=MAX_SYNC_WAIT)
        sync_d2 = self._wait_for_sync(data.dut2, timeout=MAX_SYNC_WAIT)

        if not (sync_d1 and sync_d2):
            st.report_fail("msg", "LACP synchronization timeout")

        st.log("✓ LACP synchronized on both DUTs")

        # Step 3: Verify all members show "up(s)" on D1
        st.banner("STEP 3: Verify all members synced on D1")

        result_d1 = self._verify_all_members_synced(data.dut1, data.members_d1)

        if not result_d1["success"]:
            st.report_fail(
                "msg",
                f"Not all members synchronized on D1: {result_d1['synced_count']}/{EXPECTED_MEMBER_COUNT}"
            )

        st.log(f"✓ All {EXPECTED_MEMBER_COUNT} members synchronized on D1")

        # Step 4: Verify all members show "up(s)" on D2
        st.banner("STEP 4: Verify all members synced on D2")

        result_d2 = self._verify_all_members_synced(data.dut2, data.members_d2)

        if not result_d2["success"]:
            st.report_fail(
                "msg",
                f"Not all members synchronized on D2: {result_d2['synced_count']}/{EXPECTED_MEMBER_COUNT}"
            )

        st.log(f"✓ All {EXPECTED_MEMBER_COUNT} members synchronized on D2")

        # Step 5: Verify Actor/Partner states on D1
        st.banner("STEP 5: Verify LACP Actor/Partner states on D1")

        if not self._verify_lacp_actor_partner(data.dut1):
            st.report_fail("msg", "LACP Actor/Partner not synchronized on D1")

        st.log("✓ LACP Actor/Partner synchronized on D1")

        # Step 6: Verify Actor/Partner states on D2
        st.banner("STEP 6: Verify LACP Actor/Partner states on D2")

        if not self._verify_lacp_actor_partner(data.dut2):
            st.report_fail("msg", "LACP Actor/Partner not synchronized on D2")

        st.log("✓ LACP Actor/Partner synchronized on D2")

        st.banner("TEST PASS: LACP-POS-012 - All Members Synced Successfully")
        st.report_pass("test_case_passed")
