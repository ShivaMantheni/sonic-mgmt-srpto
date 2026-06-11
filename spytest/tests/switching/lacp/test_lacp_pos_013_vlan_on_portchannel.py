"""
LACP-POS-013: Create VLAN on PortChannel

Author: Generated from testplan, 2026-05-20

Description:
  Validates L2 VLAN configuration on PortChannel interface.
  Creates VLAN and adds PortChannel as untagged member.
  Uses klish CLI for all operations.

Pre-requisites:
  - Two-node topology (D1-D2) with 4-link PortChannel
  - PortChannel configured as L2 switchport (not L3 router interface)
  - PortChannel operational with synchronized members

Test Flow:
  1. Create PortChannel and configure as switchport (L2)
  2. Create VLAN 100
  3. Add PortChannel as untagged member to VLAN
  4. Verify VLAN configuration and membership

Key Concepts:
  - L2 vs L3 interfaces: Only L2 (switchport) interfaces can be VLAN members
  - Router interface: L3 interface with IP config (cannot be in VLAN)
  - Switchport: L2 interface without IP config (can be in VLAN)
  - klish command: "switchport" configures interface as L2

Priority: P1
"""

import pytest
from spytest import st, SpyTestDict
import apis.switching.lacp as lacp_api
import apis.switching.vlan as vlan_api
import apis.system.interface as intf_api

vars = SpyTestDict()
data = SpyTestDict()

PC_ID = 1
PC_NAME = f"PortChannel{PC_ID}"
VLAN_ID = 100


@pytest.fixture(scope="module", autouse=True)
def module_hooks(request):
    global vars, data
    vars = st.ensure_min_topology("D1D2:4")

    data.dut1 = vars.D1
    data.dut2 = vars.D2
    data.members_d1 = [vars.D1D2P1, vars.D1D2P2, vars.D1D2P3, vars.D1D2P4]
    data.members_d2 = [vars.D2D1P1, vars.D2D1P2, vars.D2D1P3, vars.D2D1P4]
    # Force klish CLI for testing (override testbed default)
    data.cli_type = "klish"

    # Clean up any leftover configuration from previous failed runs
    st.log("Cleaning up any leftover configuration from previous runs...")
    for dut, members in [(data.dut1, data.members_d1), (data.dut2, data.members_d2)]:
        # Remove VLAN configuration
        vlan_api.delete_vlan_member(dut, VLAN_ID, PC_NAME, cli_type=data.cli_type, skip_error_check=True)
        vlan_api.delete_vlan(dut, VLAN_ID, cli_type=data.cli_type, skip_error_check=True)

        # Remove PortChannel members
        for member in members:
            lacp_api.delete_portchannel_member(
                dut, PC_NAME, [member], cli_type=data.cli_type, skip_error_check=True
            )

        # Delete PortChannel
        lacp_api.delete_portchannel(
            dut, PC_NAME, cli_type=data.cli_type, skip_error_check=True
        )
        st.wait(1, f"Wait after cleanup on {dut}")

    st.log("✓ Pre-test cleanup completed")

    yield

    # Cleanup
    st.banner("MODULE EPILOGUE: LACP-POS-013 Cleanup")
    for dut, members in [(data.dut1, data.members_d1), (data.dut2, data.members_d2)]:
        # Remove VLAN configuration
        vlan_api.delete_vlan_member(dut, VLAN_ID, PC_NAME, cli_type=data.cli_type, skip_error_check=True)
        vlan_api.delete_vlan(dut, VLAN_ID, cli_type=data.cli_type, skip_error_check=True)

        # Remove PortChannel members
        for member in members:
            lacp_api.delete_portchannel_member(
                dut, PC_NAME, [member], cli_type=data.cli_type, skip_error_check=True
            )

        # Delete PortChannel
        lacp_api.delete_portchannel(
            dut, PC_NAME, cli_type=data.cli_type, skip_error_check=True
        )
        st.wait(2, f"Wait for cleanup on {dut}")

    st.log("✓ Module cleanup completed")


class TestLacpPos013VlanOnPortchannel:

    def _setup_portchannel(self, dut, members):
        """Setup PortChannel with LACP and bring up interfaces"""
        # Step 1: Create PortChannel
        if not lacp_api.create_portchannel(dut, [PC_NAME], cli_type=data.cli_type):
            return False
        st.wait(2)

        # Step 2: Add members
        for member in members:
            lacp_api.add_portchannel_member(dut, PC_NAME, member, cli_type=data.cli_type)

        # Step 3: Bring up member interfaces (no shutdown)
        st.log(f"Bringing up member interfaces on {dut}")
        for member in members:
            intf_api.interface_operation(dut, member, operation="startup", cli_type=data.cli_type)

        # Step 4: Bring up PortChannel interface (no shutdown)
        st.log(f"Bringing up {PC_NAME} interface on {dut}")
        intf_api.interface_operation(dut, PC_NAME, operation="startup", cli_type=data.cli_type)

        # Step 5: Configure PortChannel as switchport (L2) - CRITICAL for VLAN membership
        st.log(f"Configuring {PC_NAME} as switchport (L2 interface) on {dut}")
        self._configure_switchport(dut, PC_NAME)

        # Wait for LACP negotiation
        st.wait(5, "Wait for LACP sync")
        return True

    def _configure_switchport(self, dut, interface):
        """Configure interface as L2 switchport (required for VLAN membership)"""
        if data.cli_type == "klish":
            # klish commands to configure switchport
            commands = [
                f"interface {interface}",
                "switchport",
                "exit"
            ]
            st.config(dut, commands, type=data.cli_type)
            st.log(f"✓ {interface} configured as switchport on {dut}")
        else:
            # For click mode, interface should be clean (no IP config)
            # SONiC click doesn't have explicit switchport command
            st.log(f"⚠ Click mode - ensure {interface} has no IP configured on {dut}")

    @pytest.mark.lacp_positive
    @pytest.mark.lacp_vlan
    @pytest.mark.lacp_pos_013
    def test_lacp_pos_013_vlan_on_portchannel(self):
        """
        Test Steps:
          1. Create PortChannel with 4 members (D1 and D2)
          2. Create VLAN 100 on both DUTs
          3. Add PortChannel as untagged member to VLAN 100
          4. Verify VLAN configuration
          5. Verify PortChannel shows as VLAN member
        """
        st.banner("LACP-POS-013: Create VLAN on PortChannel")

        # Step 1: Setup PortChannel
        if not self._setup_portchannel(data.dut1, data.members_d1):
            st.report_fail("portchannel_create_fail", PC_NAME)
        if not self._setup_portchannel(data.dut2, data.members_d2):
            st.report_fail("portchannel_create_fail", PC_NAME)

        st.log("✓ PortChannel operational")

        # Step 2: Create VLAN 100 on both DUTs
        st.banner("Create VLAN 100")

        for dut in [data.dut1, data.dut2]:
            if not vlan_api.create_vlan(dut, VLAN_ID, cli_type=data.cli_type):
                st.report_fail("vlan_create_fail", VLAN_ID)

        st.log(f"✓ VLAN {VLAN_ID} created")

        # Step 3: Add PortChannel to VLAN as untagged member
        st.banner("Add PortChannel to VLAN 100")

        for dut in [data.dut1, data.dut2]:
            if not vlan_api.add_vlan_member(
                dut, VLAN_ID, PC_NAME, tagging_mode=False, cli_type=data.cli_type
            ):
                st.report_fail("vlan_member_add_fail", PC_NAME, VLAN_ID)

        st.log(f"✓ {PC_NAME} added to VLAN {VLAN_ID}")

        # Step 4: Verify VLAN configuration
        st.banner("Verify VLAN configuration")

        for dut in [data.dut1, data.dut2]:
            vlan_list = vlan_api.get_vlan_list(dut, cli_type=data.cli_type)

            # Debug: Log what we actually got from API
            st.log(f"DEBUG: Raw vlan_list type: {type(vlan_list)}")
            st.log(f"DEBUG: Raw vlan_list content: {vlan_list}")

            if not vlan_list:
                st.report_fail("msg", f"No VLAN data returned from {dut}")

            # API wrapper already simplifies TFSM output
            # Can return either list of dicts OR list of strings (already extracted)
            vlan_ids = []
            for entry in vlan_list:
                if isinstance(entry, dict):
                    # Entry is dict - extract VID field
                    vid = entry.get("vid") or entry.get("vlanid") or entry.get("vlan")
                    if vid:
                        vlan_ids.append(str(vid))
                elif isinstance(entry, str):
                    # Entry is already a string (API simplified it)
                    vlan_ids.append(entry)
                else:
                    # Entry is something else (int, etc.)
                    vlan_ids.append(str(entry))

            st.log(f"DEBUG: Extracted VLAN IDs: {vlan_ids}")

            if str(VLAN_ID) not in vlan_ids:
                st.report_fail("msg", f"VLAN {VLAN_ID} not found on {dut}. Available VLANs: {vlan_ids}")

            st.log(f"✓ VLAN {VLAN_ID} exists on {dut}")

        # Step 5: Verify PortChannel is VLAN member
        st.banner("Verify PortChannel as VLAN member")

        for dut in [data.dut1, data.dut2]:
            members = vlan_api.get_vlan_member(dut, VLAN_ID, cli_type=data.cli_type)

            st.log(f"DEBUG: VLAN {VLAN_ID} members on {dut}: {members}")

            if PC_NAME not in str(members):
                st.report_fail("msg", f"{PC_NAME} is not a member of VLAN {VLAN_ID} on {dut}")

            st.log(f"✓ {PC_NAME} is member of VLAN {VLAN_ID} on {dut}")

        st.banner("TEST PASS: VLAN Configuration on PortChannel Successful")
        st.report_pass("test_case_passed")
