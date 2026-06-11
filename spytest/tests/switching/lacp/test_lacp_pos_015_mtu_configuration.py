"""
LACP-POS-015: Configure MTU on PortChannel

Author: Generated from testplan, 2026-05-20

Description:
  Validates MTU configuration on PortChannel interface.
  In SONiC, MTU is set on the PortChannel itself (not on individual
  member interfaces). PortChannel MTU and member interface MTU are
  independent - members retain their original MTU values.
  Verifies PortChannel remains operational and packets traverse successfully.

Pre-requisites:
  - PortChannel with 4 synchronized members
  - Default PortChannel MTU is 9100

SONiC Behavior:
  - Cannot set MTU on member interfaces while in PortChannel
  - Error: "'interface_name' is in portchannel!"
  - Solution: Set MTU on PortChannel (member MTU remains independent)
  - PortChannel MTU ≠ Member interface MTU (they are independent)

Priority: P1
"""

import pytest
from spytest import st, SpyTestDict
import apis.switching.lacp as lacp_api
import apis.routing.ip as ip_api
import apis.system.interface as intf_api
import apis.common.scapy_traffic as scapy_api

vars = SpyTestDict()
data = SpyTestDict()

PC_ID = 1
PC_NAME = f"PortChannel{PC_ID}"

# MTU parameters
DEFAULT_MTU = 9100
TEST_MTU = 1500
TEST_PACKET_SIZE = 1460  # bytes (less than MTU to allow headers)

# IP configuration for traffic test
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

        # Restore default MTU on members (wrap in try-except - API doesn't support skip_error_check)
        for member in members:
            try:
                intf_api.interface_properties_set(
                    dut, member, property="mtu", value=DEFAULT_MTU, cli_type=data.cli_type
                )
            except Exception as e:
                st.log(f"Cleanup: Failed to restore MTU on {member}: {e}")

        # Remove IP configuration
        ip_api.delete_ip_interface(
            dut, PC_NAME, ip_addr, PREFIX_LEN,
            cli_type=data.cli_type, skip_error_check=True
        )

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

    # Cleanup - restore default MTU and remove PortChannel
    st.banner("MODULE EPILOGUE: LACP-POS-015 Cleanup")
    for dut, members in [(data.dut1, data.members_d1), (data.dut2, data.members_d2)]:
        ip_addr = D1_IP if dut == data.dut1 else D2_IP

        # Restore default MTU on members (wrap in try-except - API doesn't support skip_error_check)
        for member in members:
            try:
                intf_api.interface_properties_set(
                    dut, member, property="mtu", value=DEFAULT_MTU, cli_type=data.cli_type
                )
            except Exception as e:
                st.log(f"Cleanup: Failed to restore MTU on {member}: {e}")

        # Remove IP configuration
        ip_api.delete_ip_interface(
            dut, PC_NAME, ip_addr, PREFIX_LEN,
            cli_type=data.cli_type, skip_error_check=True
        )

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


class TestLacpPos015MtuConfiguration:

    def _setup_portchannel_with_ip(self, dut, members, ip_addr):
        """Setup PortChannel with members and IP address"""
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
        st.wait(5, "Wait for LACP sync")

        # Configure IP on PortChannel
        if not ip_api.config_ip_addr_interface(
            dut, PC_NAME, ip_addr, PREFIX_LEN, family="ipv4", cli_type=data.cli_type
        ):
            return False

        return True

    def _configure_mtu(self, dut, mtu_value):
        """
        Configure MTU on PortChannel

        Note: In SONiC, you cannot set MTU on member interfaces while they're
        part of a PortChannel. MTU must be set on the PortChannel itself.
        PortChannel MTU and member interface MTU are independent.
        """
        st.log(f"Configuring MTU {mtu_value} on {PC_NAME} on {dut}")

        result = intf_api.interface_properties_set(
            dut, PC_NAME, property="mtu", value=mtu_value, cli_type=data.cli_type
        )

        if not result:
            st.error(f"Failed to set MTU on {PC_NAME}")
            return False

        st.log(f"  ✓ MTU {mtu_value} set on {PC_NAME}")
        return True

    def _verify_mtu(self, dut, expected_mtu):
        """
        Verify MTU is configured correctly on PortChannel

        Note: In SONiC, PortChannel MTU and member interface MTU are independent.
        Member interfaces retain their original MTU values.
        """
        st.log(f"Verifying MTU on {dut}")

        # Only verify PortChannel MTU (member MTU remains unchanged in SONiC)
        interfaces_to_check = [PC_NAME]

        for intf in interfaces_to_check:
            # Use raw parsing for klish output (TFSM template doesn't match klish format)
            # Exit config mode to exec mode to avoid "do" prefix (do + pipes causes bugs)
            st.config(dut, "exit", type=data.cli_type, skip_error_check=True)

            cmd = f"show interface status | grep {intf} | no-more"
            output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

            if not output:
                st.error(f"No output for {intf}")
                return False

            # Parse MTU from raw output
            # Format: Name Alias Admin Oper Speed MTU Lanes FEC DHCP RL Sub
            # Example: PortChannel1   PortChannel1        up        up        160000      1500
            actual_mtu = None
            for line in output.split('\n'):
                if intf in line and 'Name' not in line:
                    # Split by whitespace and extract MTU field (index 5)
                    fields = line.split()
                    if len(fields) >= 6:
                        actual_mtu = fields[5]
                        break

            if not actual_mtu:
                st.error(f"Could not find MTU for {intf} in output: {output}")
                return False

            if actual_mtu != str(expected_mtu):
                st.error(f"{intf} MTU mismatch: expected {expected_mtu}, got {actual_mtu}")
                return False

            st.log(f"  ✓ {intf} MTU: {actual_mtu}")

        return True

    def _verify_portchannel_operational(self, dut):
        """Verify PortChannel is still operational after MTU change"""
        # Use raw parsing for klish output (TFSM template doesn't match klish format)
        # Exit config mode to exec mode to avoid "do" prefix (do + | no-more causes bugs)
        st.config(dut, "exit", type=data.cli_type, skip_error_check=True)

        cmd = "show PortChannel summary | no-more"
        output = st.show(dut, cmd, type=data.cli_type, skip_tmpl=True)

        if not output:
            return False

        # Parse raw output looking for PortChannel state
        # Format: 1  PortChannel1  Eth (U)  LACP  Ethernet32(P), Ethernet36(P), ...
        # (U) = PortChannel UP

        for line in output.split('\n'):
            if PC_NAME in line and 'Group' not in line:
                # Check if PortChannel is UP: "Eth (U)"
                if "(U)" in line:
                    st.log(f"✓ {PC_NAME} operational")
                    st.log(f"  State: {line.strip()}")
                    return True
                else:
                    st.log(f"✗ {PC_NAME} not operational: {line.strip()}")
                    return False

        st.log(f"✗ {PC_NAME} not found in output")
        return False

    @pytest.mark.lacp_positive
    @pytest.mark.lacp_mtu
    @pytest.mark.lacp_pos_015
    def test_lacp_pos_015_mtu_configuration(self):
        """
        Test Steps:
          1. Create PortChannel with 4 members on both DUTs
          2. Configure IP addresses for connectivity test
          3. Configure MTU 1500 on PortChannel
          4. Verify MTU is configured on PortChannel
          5. Verify PortChannel remains operational
          6. Send packets of size 1460 bytes
          7. Verify packets traverse successfully
        """
        st.banner("LACP-POS-015: Configure MTU on PortChannel")

        # Step 1: Setup PortChannel with IP
        st.banner("Setup PortChannel with IP addresses")

        if not self._setup_portchannel_with_ip(data.dut1, data.members_d1, D1_IP):
            st.report_fail("portchannel_create_fail", PC_NAME)

        if not self._setup_portchannel_with_ip(data.dut2, data.members_d2, D2_IP):
            st.report_fail("portchannel_create_fail", PC_NAME)

        st.log("✓ PortChannel operational with IP addresses")

        # Step 2: Verify baseline connectivity
        st.banner("Verify baseline connectivity")

        if not ip_api.ping(data.dut1, D2_IP, count=3, family="ipv4"):
            st.report_fail("ping_fail", D1_IP, D2_IP)

        st.log("✓ Baseline ping successful")

        # Step 3: Configure MTU on PortChannel
        st.banner(f"Configure MTU {TEST_MTU} on PortChannel")

        if not self._configure_mtu(data.dut1, TEST_MTU):
            st.report_fail("msg", "Failed to configure MTU on D1")

        if not self._configure_mtu(data.dut2, TEST_MTU):
            st.report_fail("msg", "Failed to configure MTU on D2")

        st.log(f"✓ MTU {TEST_MTU} configured on PortChannel")

        # Step 4: Verify MTU configuration
        st.banner("Verify PortChannel MTU configuration")

        if not self._verify_mtu(data.dut1, TEST_MTU):
            st.report_fail("msg", "MTU verification failed on D1")

        if not self._verify_mtu(data.dut2, TEST_MTU):
            st.report_fail("msg", "MTU verification failed on D2")

        st.log("✓ MTU verified on PortChannel")

        # Step 5: Verify PortChannel still operational
        st.banner("Verify PortChannel operational after MTU change")

        st.wait(5, "Wait for MTU change to propagate")

        if not self._verify_portchannel_operational(data.dut1):
            st.report_fail("msg", "PortChannel not operational on D1 after MTU change")

        if not self._verify_portchannel_operational(data.dut2):
            st.report_fail("msg", "PortChannel not operational on D2 after MTU change")

        st.log("✓ PortChannel remains operational")

        # Step 6: Verify connectivity with MTU-sized packets
        st.banner(f"Verify connectivity with {TEST_PACKET_SIZE}-byte packets")

        if not ip_api.ping(data.dut1, D2_IP, count=5, family="ipv4", packet_size=TEST_PACKET_SIZE):
            st.report_fail("ping_fail", D1_IP, D2_IP)

        st.log(f"✓ Ping successful with {TEST_PACKET_SIZE}-byte packets")

        st.banner("TEST PASS: MTU Configuration Successful")
        st.report_pass("test_case_passed")
