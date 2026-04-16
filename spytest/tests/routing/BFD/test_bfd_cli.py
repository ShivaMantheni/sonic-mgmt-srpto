"""
BFD CLI Tests - SONiC BFD Configuration and Show Command Validation

Author: SPyTest BFD Feature Team
Copyright (C) 2026, Broadcom Inc.

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_2vs.yaml \\
  tests/routing/BFD/test_bfd_cli.py \\
  --logs-path ./logs/test_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Validates BFD global configuration, peer configuration, parameter configuration,
  profile management, and related show commands. Tests both single-hop and multi-hop
  BFD session configuration through CLI.

Pre-requisites:
  - Topology: two-node (D1-D2) | Supported: HW and Virtual
  - IP addresses configured: D1: 10.1.1.1/24, D2: 10.1.1.2/24
  - Required test variables: None (uses default D1D2 topology)
"""

import pytest
from spytest import st, SpyTestDict

# Module-level variables
vars = SpyTestDict()
data = SpyTestDict()

# Import BFD API
import apis.routing.bfd as bfd_api


@pytest.fixture(scope="module", autouse=True)
def module_hooks(request):
    """
    Module-level fixture for setup and cleanup.
    """
    global vars

    # Module prologue - setup
    st.banner("MODULE PROLOGUE: BFD CLI Tests")
    vars = st.ensure_min_topology("D1D2:1")

    # Initialize test data
    data.d1 = vars.D1
    data.d2 = vars.D2
    data.d1d2_link = vars.D1D2P1
    data.d2d1_link = vars.D2D1P1
    data.peer_ip_d2_from_d1 = "10.1.1.2"
    data.peer_ip_d1_from_d2 = "10.1.1.1"

    yield

    # Module epilogue - cleanup
    st.banner("MODULE EPILOGUE: BFD CLI Tests - Cleanup")
    bfd_api.disable_bfd(data.d1, cli_type="klish")
    bfd_api.disable_bfd(data.d2, cli_type="klish")


# ============================================================================
# BFD Global Configuration Tests
# ============================================================================


def test_tc_bfd_cli_001_enable_bfd_globally():
    """
    TC_BFD_CLI_001: Enable BFD globally

    Objective: Verify BFD global configuration can be enabled successfully
    """
    st.banner("TC_BFD_CLI_001: Enable BFD globally")

    # Enable BFD
    result = bfd_api.enable_bfd(data.d1, cli_type="klish")
    if not result:
        st.report_fail("bfd_enable_failed")

    # Verify BFD is in running configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "bfd" not in config_output:
        st.report_fail("bfd_not_in_config")

    st.report_pass("bfd_enabled_successfully")


def test_tc_bfd_cli_002_configure_bfd_global_slow_timer():
    """
    TC_BFD_CLI_002: Configure BFD global slow-timer

    Objective: Verify BFD global slow-timer can be configured with valid values
    """
    st.banner("TC_BFD_CLI_002: Configure BFD global slow-timer")

    # Enable BFD first if not already enabled
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Configure slow-timer to 5000ms
    result = bfd_api.configure_bfd_slow_timer(data.d1, 5000, cli_type="klish")
    if not result:
        st.report_fail("slow_timer_config_failed")

    # Verify in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "slow-timer 5000" not in config_output:
        st.report_fail("slow_timer_not_in_config")

    # Modify to different value
    result = bfd_api.configure_bfd_slow_timer(data.d1, 10000, cli_type="klish")
    if not result:
        st.report_fail("slow_timer_modify_failed")

    # Verify updated configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "slow-timer 10000" not in config_output:
        st.report_fail("slow_timer_update_not_in_config")

    st.report_pass("slow_timer_configured_successfully")


def test_tc_bfd_cli_003_remove_bfd_global_configuration():
    """
    TC_BFD_CLI_003: Remove BFD global configuration

    Objective: Verify BFD global configuration can be removed
    """
    st.banner("TC_BFD_CLI_003: Remove BFD global configuration")

    # Enable BFD first
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Verify BFD is configured
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "bfd" not in config_output:
        st.report_fail("bfd_not_configured")

    # Remove BFD
    result = bfd_api.disable_bfd(data.d1, cli_type="klish")
    if not result:
        st.report_fail("bfd_disable_failed")

    # Verify BFD is removed
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "bfd" in config_output:
        st.report_fail("bfd_not_removed")

    st.report_pass("bfd_removed_successfully")


# ============================================================================
# BFD Peer Configuration Tests
# ============================================================================


def test_tc_bfd_cli_004_configure_single_hop_bfd_peer():
    """
    TC_BFD_CLI_004: Configure single-hop BFD peer

    Objective: Verify single-hop BFD peer can be configured on physical interface
    """
    st.banner("TC_BFD_CLI_004: Configure single-hop BFD peer")

    # Enable BFD globally
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Configure single-hop BFD peer
    result = bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )
    if not result:
        st.report_fail("single_hop_peer_config_failed")

    # Verify peer in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if data.peer_ip_d2_from_d1 not in config_output or data.d1d2_link not in config_output:
        st.report_fail("peer_not_in_config")

    # Verify peer is shown in peers list
    peers_output = bfd_api.show_bfd_peers(data.d1, cli_type="klish")
    if data.peer_ip_d2_from_d1 not in peers_output:
        st.report_fail("peer_not_in_peers_list")

    st.report_pass("single_hop_peer_configured_successfully")


def test_tc_bfd_cli_005_configure_multi_hop_bfd_peer():
    """
    TC_BFD_CLI_005: Configure multi-hop BFD peer

    Objective: Verify multi-hop BFD peer can be configured
    """
    st.banner("TC_BFD_CLI_005: Configure multi-hop BFD peer")

    # Enable BFD globally
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Configure multi-hop BFD peer
    result = bfd_api.configure_bfd_peer(
        data.d1,
        "10.2.2.2",
        multihop=True,
        local_address="10.1.1.1",
        cli_type="klish"
    )
    if not result:
        st.report_fail("multi_hop_peer_config_failed")

    # Verify peer in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "10.2.2.2" not in config_output or "multihop" not in config_output:
        st.report_fail("multi_hop_peer_not_in_config")

    st.report_pass("multi_hop_peer_configured_successfully")


def test_tc_bfd_cli_006_remove_bfd_peer():
    """
    TC_BFD_CLI_006: Remove BFD peer configuration

    Objective: Verify BFD peer can be removed
    """
    st.banner("TC_BFD_CLI_006: Remove BFD peer configuration")

    # Configure a peer first
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Verify peer is configured
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if data.peer_ip_d2_from_d1 not in config_output:
        st.report_fail("peer_not_configured")

    # Remove peer
    result = bfd_api.remove_bfd_peer(data.d1, data.peer_ip_d2_from_d1, cli_type="klish")
    if not result:
        st.report_fail("peer_remove_failed")

    # Verify peer is removed
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if data.peer_ip_d2_from_d1 in config_output:
        st.report_fail("peer_not_removed")

    st.report_pass("bfd_peer_removed_successfully")


# ============================================================================
# BFD Peer Parameters Tests
# ============================================================================


def test_tc_bfd_cli_007_configure_bfd_transmit_interval():
    """
    TC_BFD_CLI_007: Configure BFD transmit interval

    Objective: Verify BFD transmit interval can be configured
    """
    st.banner("TC_BFD_CLI_007: Configure BFD transmit interval")

    # Configure peer with transmit interval
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Set transmit interval
    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        transmit_interval=300,
        cli_type="klish"
    )
    if not result:
        st.report_fail("transmit_interval_config_failed")

    # Verify in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "transmit-interval 300" not in config_output:
        st.report_fail("transmit_interval_not_in_config")

    st.report_pass("transmit_interval_configured_successfully")


def test_tc_bfd_cli_008_configure_bfd_receive_interval():
    """
    TC_BFD_CLI_008: Configure BFD receive interval

    Objective: Verify BFD receive interval can be configured
    """
    st.banner("TC_BFD_CLI_008: Configure BFD receive interval")

    # Configure peer
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Set receive interval
    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        receive_interval=300,
        cli_type="klish"
    )
    if not result:
        st.report_fail("receive_interval_config_failed")

    # Verify in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "receive-interval 300" not in config_output:
        st.report_fail("receive_interval_not_in_config")

    st.report_pass("receive_interval_configured_successfully")


def test_tc_bfd_cli_009_configure_bfd_detect_multiplier():
    """
    TC_BFD_CLI_009: Configure BFD detect multiplier

    Objective: Verify BFD detect multiplier can be configured
    """
    st.banner("TC_BFD_CLI_009: Configure BFD detect multiplier")

    # Configure peer
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Set detect multiplier
    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        detect_multiplier=3,
        cli_type="klish"
    )
    if not result:
        st.report_fail("detect_multiplier_config_failed")

    # Verify in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "detect-multiplier 3" not in config_output:
        st.report_fail("detect_multiplier_not_in_config")

    st.report_pass("detect_multiplier_configured_successfully")


def test_tc_bfd_cli_010_configure_bfd_all_parameters():
    """
    TC_BFD_CLI_010: Configure all BFD parameters together

    Objective: Verify all parameters can be configured together
    """
    st.banner("TC_BFD_CLI_010: Configure all BFD parameters together")

    # Configure peer with all parameters
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        transmit_interval=300,
        receive_interval=300,
        detect_multiplier=3,
        cli_type="klish"
    )
    if not result:
        st.report_fail("all_parameters_config_failed")

    # Verify all parameters in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if not all(param in config_output for param in ["transmit-interval 300", "receive-interval 300", "detect-multiplier 3"]):
        st.report_fail("not_all_parameters_in_config")

    st.report_pass("all_parameters_configured_successfully")


# ============================================================================
# BFD Echo Mode Tests
# ============================================================================


def test_tc_bfd_cli_011_enable_bfd_echo_mode():
    """
    TC_BFD_CLI_011: Enable BFD echo mode

    Objective: Verify BFD echo mode can be enabled
    """
    st.banner("TC_BFD_CLI_011: Enable BFD echo mode")

    # Configure peer
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Enable echo mode
    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        echo_mode=True,
        cli_type="klish"
    )
    if not result:
        st.report_fail("echo_mode_enable_failed")

    # Verify in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "echo-mode" not in config_output:
        st.report_fail("echo_mode_not_in_config")

    st.report_pass("echo_mode_enabled_successfully")


def test_tc_bfd_cli_012_configure_bfd_echo_interval():
    """
    TC_BFD_CLI_012: Configure BFD echo interval

    Objective: Verify BFD echo interval can be configured
    """
    st.banner("TC_BFD_CLI_012: Configure BFD echo interval")

    # Configure peer with echo mode and interval
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        echo_mode=True,
        echo_interval=500,
        cli_type="klish"
    )
    if not result:
        st.report_fail("echo_interval_config_failed")

    # Verify in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "echo-interval 500" not in config_output:
        st.report_fail("echo_interval_not_in_config")

    st.report_pass("echo_interval_configured_successfully")


def test_tc_bfd_cli_013_disable_bfd_echo_mode():
    """
    TC_BFD_CLI_013: Disable BFD echo mode

    Objective: Verify BFD echo mode can be disabled
    """
    st.banner("TC_BFD_CLI_013: Disable BFD echo mode")

    # Configure peer with echo mode
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        echo_mode=True,
        cli_type="klish"
    )

    # Disable echo mode
    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        echo_mode=False,
        cli_type="klish"
    )
    if not result:
        st.report_fail("echo_mode_disable_failed")

    st.report_pass("echo_mode_disabled_successfully")


# ============================================================================
# BFD Profile Tests
# ============================================================================


def test_tc_bfd_cli_014_create_bfd_profile():
    """
    TC_BFD_CLI_014: Create BFD profile

    Objective: Verify BFD profile can be created with parameters
    """
    st.banner("TC_BFD_CLI_014: Create BFD profile")

    # Enable BFD first
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Create BFD profile
    result = bfd_api.configure_bfd_profile(
        data.d1,
        "test-profile",
        transmit_interval=100,
        receive_interval=100,
        detect_multiplier=5,
        cli_type="klish"
    )
    if not result:
        st.report_fail("profile_creation_failed")

    # Verify profile in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "test-profile" not in config_output:
        st.report_fail("profile_not_in_config")

    st.report_pass("bfd_profile_created_successfully")


def test_tc_bfd_cli_015_apply_bfd_profile_to_peer():
    """
    TC_BFD_CLI_015: Apply BFD profile to peer

    Objective: Verify BFD profile can be applied to a peer
    """
    st.banner("TC_BFD_CLI_015: Apply BFD profile to peer")

    # Enable BFD and create profile
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_profile(
        data.d1,
        "fast-profile",
        transmit_interval=100,
        receive_interval=100,
        detect_multiplier=5,
        cli_type="klish"
    )

    # Configure peer
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Apply profile to peer
    result = bfd_api.apply_bfd_profile_to_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        "fast-profile",
        cli_type="klish"
    )
    if not result:
        st.report_fail("profile_apply_failed")

    # Verify profile is applied
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "profile fast-profile" not in config_output:
        st.report_fail("profile_not_applied")

    st.report_pass("bfd_profile_applied_successfully")


def test_tc_bfd_cli_016_remove_bfd_profile():
    """
    TC_BFD_CLI_016: Remove BFD profile

    Objective: Verify BFD profile can be removed
    """
    st.banner("TC_BFD_CLI_016: Remove BFD profile")

    # Enable BFD and create profile
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_profile(
        data.d1,
        "remove-profile",
        transmit_interval=100,
        receive_interval=100,
        detect_multiplier=5,
        cli_type="klish"
    )

    # Verify profile exists
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "remove-profile" not in config_output:
        st.report_fail("profile_not_created")

    # Remove profile
    result = bfd_api.remove_bfd_profile(data.d1, "remove-profile", cli_type="klish")
    if not result:
        st.report_fail("profile_removal_failed")

    # Verify profile is removed
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "remove-profile" in config_output:
        st.report_fail("profile_not_removed")

    st.report_pass("bfd_profile_removed_successfully")


# ============================================================================
# BFD Show Command Tests
# ============================================================================


def test_tc_bfd_cli_017_show_bfd_peers_empty():
    """
    TC_BFD_CLI_017: Show BFD peers (empty)

    Objective: Verify show bfd peers when no peers configured
    """
    st.banner("TC_BFD_CLI_017: Show BFD peers (empty)")

    # Ensure no peers configured
    bfd_api.disable_bfd(data.d1, cli_type="klish")

    # Show peers
    peers_output = bfd_api.show_bfd_peers(data.d1, cli_type="klish")
    st.log(f"BFD Peers output (empty): {peers_output}")

    st.report_pass("show_bfd_peers_works_empty")


def test_tc_bfd_cli_018_show_bfd_peers_with_peer():
    """
    TC_BFD_CLI_018: Show BFD peers with configured peer

    Objective: Verify show bfd peers displays configured peers
    """
    st.banner("TC_BFD_CLI_018: Show BFD peers with configured peer")

    # Configure BFD peer
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Show peers
    peers_output = bfd_api.show_bfd_peers(data.d1, cli_type="klish")
    if data.peer_ip_d2_from_d1 not in peers_output:
        st.report_fail("peer_not_in_show_output")

    st.report_pass("show_bfd_peers_displays_peer")


def test_tc_bfd_cli_019_show_specific_bfd_peer():
    """
    TC_BFD_CLI_019: Show specific BFD peer details

    Objective: Verify show bfd peer <IP> displays peer details
    """
    st.banner("TC_BFD_CLI_019: Show specific BFD peer details")

    # Configure peer
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Show specific peer
    peer_output = bfd_api.show_bfd_peer(data.d1, data.peer_ip_d2_from_d1, cli_type="klish")
    if data.peer_ip_d2_from_d1 not in peer_output:
        st.report_fail("peer_not_in_detail_output")

    st.log(f"BFD Peer details: {peer_output}")
    st.report_pass("show_bfd_peer_displays_details")


def test_tc_bfd_cli_020_show_running_config_bfd():
    """
    TC_BFD_CLI_020: Show running-config bfd

    Objective: Verify show running-config bfd displays BFD configuration
    """
    st.banner("TC_BFD_CLI_020: Show running-config bfd")

    # Configure BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_slow_timer(data.d1, 5000, cli_type="klish")

    # Show running configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "bfd" not in config_output:
        st.report_fail("bfd_not_in_running_config")

    st.log(f"BFD Configuration: {config_output}")
    st.report_pass("show_running_config_bfd_works")


# ============================================================================
# BFD Peer Configuration Variations
# ============================================================================


def test_tc_bfd_cli_021_configure_multiple_bfd_peers():
    """
    TC_BFD_CLI_021: Configure multiple BFD peers

    Objective: Verify multiple BFD peers can be configured
    """
    st.banner("TC_BFD_CLI_021: Configure multiple BFD peers")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Configure first peer
    result1 = bfd_api.configure_bfd_peer(
        data.d1,
        "10.1.1.2",
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Configure second peer (multi-hop)
    result2 = bfd_api.configure_bfd_peer(
        data.d1,
        "10.2.2.2",
        multihop=True,
        local_address="10.1.1.1",
        cli_type="klish"
    )

    if not (result1 and result2):
        st.report_fail("multiple_peers_config_failed")

    # Verify both peers in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "10.1.1.2" not in config_output or "10.2.2.2" not in config_output:
        st.report_fail("not_all_peers_in_config")

    st.report_pass("multiple_bfd_peers_configured_successfully")


def test_tc_bfd_cli_022_bfd_with_vrf():
    """
    TC_BFD_CLI_022: Configure BFD peer in non-default VRF

    Objective: Verify BFD peer can be configured in VRF
    """
    st.banner("TC_BFD_CLI_022: Configure BFD peer in non-default VRF")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Configure peer in VRF (note: VRF must be created first in real scenario)
    # This is a basic test to verify API supports VRF parameter
    result = bfd_api.configure_bfd_peer(
        data.d1,
        "10.1.1.2",
        interface=data.d1d2_link,
        vrf="default",
        cli_type="klish"
    )

    if not result:
        st.report_fail("bfd_peer_vrf_config_failed")

    st.report_pass("bfd_peer_vrf_configured_successfully")


def test_tc_bfd_cli_023_configure_bfd_peer_without_interface():
    """
    TC_BFD_CLI_023: Attempt to configure single-hop BFD without interface

    Objective: Verify system rejects single-hop configuration without interface
    """
    st.banner("TC_BFD_CLI_023: Attempt to configure single-hop BFD without interface")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Attempt to configure without interface (should fail)
    result = bfd_api.configure_bfd_peer(
        data.d1,
        "10.1.1.2",
        cli_type="klish"
    )

    if result:
        st.report_fail("bfd_peer_should_require_interface")

    st.report_pass("bfd_peer_correctly_requires_interface")


def test_tc_bfd_cli_024_configure_bfd_peer_without_local_address():
    """
    TC_BFD_CLI_024: Attempt to configure multi-hop BFD without local address

    Objective: Verify system rejects multi-hop configuration without local address
    """
    st.banner("TC_BFD_CLI_024: Attempt to configure multi-hop BFD without local address")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Attempt to configure without local address (should fail)
    result = bfd_api.configure_bfd_peer(
        data.d1,
        "10.2.2.2",
        multihop=True,
        cli_type="klish"
    )

    if result:
        st.report_fail("bfd_peer_multihop_should_require_local_address")

    st.report_pass("bfd_peer_multihop_correctly_requires_local_address")


# ============================================================================
# BFD Parameter Validation Tests
# ============================================================================


def test_tc_bfd_cli_025_modify_bfd_parameters_on_active_peer():
    """
    TC_BFD_CLI_025: Modify BFD parameters on active peer

    Objective: Verify BFD parameters can be modified without removing peer
    """
    st.banner("TC_BFD_CLI_025: Modify BFD parameters on active peer")

    # Configure peer with initial parameters
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        transmit_interval=300,
        receive_interval=300,
        detect_multiplier=3,
        cli_type="klish"
    )

    # Modify parameters
    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        transmit_interval=500,
        receive_interval=500,
        detect_multiplier=5,
        cli_type="klish"
    )

    if not result:
        st.report_fail("parameter_modification_failed")

    # Verify new parameters in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "transmit-interval 500" not in config_output or "detect-multiplier 5" not in config_output:
        st.report_fail("modified_parameters_not_in_config")

    st.report_pass("bfd_parameters_modified_successfully")


def test_tc_bfd_cli_026_configure_fast_bfd_timers():
    """
    TC_BFD_CLI_026: Configure fast BFD timers (50ms)

    Objective: Verify BFD can be configured with fast timers
    """
    st.banner("TC_BFD_CLI_026: Configure fast BFD timers (50ms)")

    # Configure peer with fast timers
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        transmit_interval=50,
        receive_interval=50,
        detect_multiplier=3,
        cli_type="klish"
    )

    if not result:
        st.report_fail("fast_timer_config_failed")

    # Verify fast timers in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "transmit-interval 50" not in config_output or "receive-interval 50" not in config_output:
        st.report_fail("fast_timers_not_in_config")

    st.report_pass("fast_bfd_timers_configured_successfully")


def test_tc_bfd_cli_027_configure_slow_bfd_timers():
    """
    TC_BFD_CLI_027: Configure slow BFD timers (1000ms)

    Objective: Verify BFD can be configured with slow timers
    """
    st.banner("TC_BFD_CLI_027: Configure slow BFD timers (1000ms)")

    # Configure peer with slow timers
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        transmit_interval=1000,
        receive_interval=1000,
        detect_multiplier=3,
        cli_type="klish"
    )

    if not result:
        st.report_fail("slow_timer_config_failed")

    # Verify slow timers in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "transmit-interval 1000" not in config_output or "receive-interval 1000" not in config_output:
        st.report_fail("slow_timers_not_in_config")

    st.report_pass("slow_bfd_timers_configured_successfully")
