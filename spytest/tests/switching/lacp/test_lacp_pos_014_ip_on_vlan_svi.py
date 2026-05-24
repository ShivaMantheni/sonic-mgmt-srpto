"""
LACP-POS-014: Configure IP address on VLAN SVI above PortChannel

Author: Generated from testplan, 2026-05-20

Description:
  Validates L3 configuration (IP addressing) on VLAN SVI that sits above
  a PortChannel interface. Verifies connectivity via ping across the
  PortChannel+VLAN stack.

Pre-requisites:
  - VLAN 100 created with PortChannel as member
  - PortChannel synchronized with 4 members

Priority: P1
"""

import pytest
from spytest import st, SpyTestDict
import apis.switching.lacp as lacp_api
import apis.switching.vlan as vlan_api
import apis.routing.ip as ip_api
import apis.system.interface as intf_api

vars = SpyTestDict()
data = SpyTestDict()

PC_ID = 1
PC_NAME = f"PortChannel{PC_ID}"
VLAN_ID = 100
VLAN_NAME = f"Vlan{VLAN_ID}"

D1_IP = "10.1.1.1"
D2_IP = "10.1.1.2"
PREFIX_LEN = 24


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
        ip_addr = D1_IP if dut == data.dut1 else D2_IP
        # Remove IP configuration
        ip_api.delete_ip_interface(dut, VLAN_NAME, ip_addr, PREFIX_LEN, cli_type=data.cli_type, skip_error_check=True)

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
    st.banner("MODULE EPILOGUE: LACP-POS-014 Cleanup")
    for dut, members in [(data.dut1, data.members_d1), (data.dut2, data.members_d2)]:
        ip_addr = D1_IP if dut == data.dut1 else D2_IP
        # Remove IP configuration
        ip_api.delete_ip_interface(dut, VLAN_NAME, ip_addr, PREFIX_LEN, cli_type=data.cli_type, skip_error_check=True)

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


class TestLacpPos014IpOnVlanSvi:

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

        # Wait for LACP negotiation
        st.wait(5)
        return True

    @pytest.mark.lacp_positive
    @pytest.mark.lacp_l3
    @pytest.mark.lacp_pos_014
    def test_lacp_pos_014_ip_on_vlan_svi(self):
        """
        Test Steps:
          1. Create PortChannel and VLAN 100 on both DUTs
          2. Add PortChannel to VLAN 100
          3. Configure IP 10.1.1.1/24 on VLAN 100 SVI (D1)
          4. Configure IP 10.1.1.2/24 on VLAN 100 SVI (D2)
          5. Bring up VLAN SVI interfaces
          6. Ping from D1 to D2 and verify connectivity
        """
        st.banner("LACP-POS-014: Configure IP on VLAN SVI above PortChannel")

        # Step 1: Setup PortChannel and VLAN
        st.banner("Setup PortChannel and VLAN")

        for dut, members in [(data.dut1, data.members_d1), (data.dut2, data.members_d2)]:
            if not self._setup_portchannel(dut, members):
                st.report_fail("portchannel_create_fail", PC_NAME)

            vlan_api.create_vlan(dut, VLAN_ID, cli_type=data.cli_type)
            vlan_api.add_vlan_member(dut, VLAN_ID, PC_NAME, tagging_mode=False, cli_type=data.cli_type)

        st.log("✓ PortChannel and VLAN configured")

        # Step 2: Configure IP on VLAN SVI - D1
        st.banner(f"Configure IP {D1_IP}/{PREFIX_LEN} on VLAN {VLAN_ID} SVI (D1)")

        if not ip_api.config_ip_addr_interface(
            data.dut1, VLAN_NAME, D1_IP, PREFIX_LEN, family="ipv4", cli_type=data.cli_type
        ):
            st.report_fail("ip_routing_int_create_fail", VLAN_NAME)

        st.log(f"✓ IP {D1_IP}/{PREFIX_LEN} configured on D1")

        # Step 3: Configure IP on VLAN SVI - D2
        st.banner(f"Configure IP {D2_IP}/{PREFIX_LEN} on VLAN {VLAN_ID} SVI (D2)")

        if not ip_api.config_ip_addr_interface(
            data.dut2, VLAN_NAME, D2_IP, PREFIX_LEN, family="ipv4", cli_type=data.cli_type
        ):
            st.report_fail("ip_routing_int_create_fail", VLAN_NAME)

        st.log(f"✓ IP {D2_IP}/{PREFIX_LEN} configured on D2")

        # Step 4: Bring up VLAN SVI interfaces
        st.banner("Bring up VLAN SVI interfaces")

        for dut in [data.dut1, data.dut2]:
            intf_api.interface_operation(dut, VLAN_NAME, operation="startup", cli_type=data.cli_type)

        st.wait(5, "Wait for interfaces to come up")

        # Step 5: Verify IP connectivity with ping
        st.banner("Verify connectivity via ping")

        result = ip_api.ping(data.dut1, D2_IP, count=5, family="ipv4")

        if not result:
            st.report_fail("ping_fail", D1_IP, D2_IP)

        st.log(f"✓ Ping successful: {D1_IP} → {D2_IP}")

        st.report_pass("test_case_passed")
