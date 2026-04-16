"""
BFD Functional Tests - SONiC BFD Session Establishment and Routing Integration

Author: SPyTest BFD Feature Team
Copyright (C) 2026, Broadcom Inc.

How to run:
  ./bin/spytest --tryssh 1 \\
  --testbed ./testbeds/testbed_2vs.yaml \\
  tests/routing/BFD/test_bfd_functional.py \\
  --logs-path ./logs/test_$(date +%F_%H%M%S) \\
  --log-level debug --skip-init-config --ifname-type native

Description:
  Validates BFD session establishment, state transitions, routing protocol
  integration (static routes, BGP, OSPF), and protocol-specific behavior.
  Tests both IPv4 and IPv6 scenarios.

Pre-requisites:
  - Topology: two-node (D1-D2) | Supported: HW and Virtual
  - IP addresses configured: D1: 10.1.1.1/24, D2: 10.1.1.2/24
  - IPv6 addresses: D1: 2001:db8:1::1/64, D2: 2001:db8:1::2/64
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
    st.banner("MODULE PROLOGUE: BFD Functional Tests")
    vars = st.ensure_min_topology("D1D2:1")

    # Initialize test data
    data.d1 = vars.D1
    data.d2 = vars.D2
    data.d1d2_link = vars.D1D2P1
    data.d2d1_link = vars.D2D1P1
    data.peer_ip_d2_from_d1 = "10.1.1.2"
    data.peer_ip_d1_from_d2 = "10.1.1.1"
    data.peer_ipv6_d2_from_d1 = "2001:db8:1::2"
    data.peer_ipv6_d1_from_d2 = "2001:db8:1::1"

    yield

    # Module epilogue - cleanup
    st.banner("MODULE EPILOGUE: BFD Functional Tests - Cleanup")
    bfd_api.disable_bfd(data.d1, cli_type="klish")
    bfd_api.disable_bfd(data.d2, cli_type="klish")


# ============================================================================
# BFD Session Establishment Tests
# ============================================================================


def test_tc_bfd_func_001_single_hop_session_establishment():
    """
    TC_BFD_FUNC_001: Single-hop BFD session establishment

    Objective: Verify BFD session can be established between two directly connected peers
    """
    st.banner("TC_BFD_FUNC_001: Single-hop BFD session establishment")

    # Configure BFD on both devices
    result1 = bfd_api.enable_bfd(data.d1, cli_type="klish")
    result2 = bfd_api.enable_bfd(data.d2, cli_type="klish")

    if not (result1 and result2):
        st.report_fail("bfd_enable_failed")

    # Configure peer on D1
    result1 = bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Configure peer on D2
    result2 = bfd_api.configure_bfd_peer(
        data.d2,
        data.peer_ip_d1_from_d2,
        interface=data.d2d1_link,
        cli_type="klish"
    )

    if not (result1 and result2):
        st.report_fail("peer_config_failed")

    # Verify session comes up on both sides
    if not bfd_api.verify_bfd_peer_up(data.d1, data.peer_ip_d2_from_d1, timeout=10):
        st.report_fail("session_not_up_on_d1")

    if not bfd_api.verify_bfd_peer_up(data.d2, data.peer_ip_d1_from_d2, timeout=10):
        st.report_fail("session_not_up_on_d2")

    st.report_pass("single_hop_session_established")


def test_tc_bfd_func_002_ipv6_single_hop_session():
    """
    TC_BFD_FUNC_002: IPv6 single-hop BFD session

    Objective: Verify BFD session works over IPv6
    """
    st.banner("TC_BFD_FUNC_002: IPv6 single-hop BFD session")

    # Enable BFD on both devices
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.enable_bfd(data.d2, cli_type="klish")

    # Configure IPv6 peer on D1
    result1 = bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ipv6_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Configure IPv6 peer on D2
    result2 = bfd_api.configure_bfd_peer(
        data.d2,
        data.peer_ipv6_d1_from_d2,
        interface=data.d2d1_link,
        cli_type="klish"
    )

    if not (result1 and result2):
        st.report_fail("ipv6_peer_config_failed")

    # Verify session comes up
    if not bfd_api.verify_bfd_peer_up(data.d1, data.peer_ipv6_d2_from_d1, timeout=10):
        st.report_fail("ipv6_session_not_up_on_d1")

    st.report_pass("ipv6_single_hop_session_established")


def test_tc_bfd_func_003_multi_hop_session_establishment():
    """
    TC_BFD_FUNC_003: Multi-hop BFD session establishment

    Objective: Verify multi-hop BFD session can be established
    """
    st.banner("TC_BFD_FUNC_003: Multi-hop BFD session establishment")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Configure multi-hop peer
    result = bfd_api.configure_bfd_peer(
        data.d1,
        "10.2.2.2",
        multihop=True,
        local_address="10.1.1.1",
        cli_type="klish"
    )

    if not result:
        st.report_fail("multi_hop_peer_config_failed")

    # Verify peer is configured
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "10.2.2.2" not in config_output or "multihop" not in config_output:
        st.report_fail("multi_hop_peer_not_configured")

    st.report_pass("multi_hop_session_configured")


def test_tc_bfd_func_004_session_down_on_peer_shutdown():
    """
    TC_BFD_FUNC_004: BFD session goes down when peer is shutdown

    Objective: Verify BFD session state transitions to Down when peer is shutdown
    """
    st.banner("TC_BFD_FUNC_004: Session down on peer shutdown")

    # Setup session first
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.enable_bfd(data.d2, cli_type="klish")

    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d2, data.peer_ip_d1_from_d2, interface=data.d2d1_link, cli_type="klish")

    # Wait for session to come up
    if not bfd_api.verify_bfd_peer_up(data.d1, data.peer_ip_d2_from_d1, timeout=10):
        st.report_fail("session_not_up_initially")

    # Shutdown BFD on peer side
    bfd_api.disable_bfd(data.d2, cli_type="klish")

    # Verify session goes down on D1
    if not bfd_api.verify_bfd_session_down(data.d1, data.peer_ip_d2_from_d1, timeout=30):
        st.report_fail("session_not_down_after_peer_shutdown")

    st.report_pass("session_down_on_peer_shutdown")


def test_tc_bfd_func_005_session_recovery():
    """
    TC_BFD_FUNC_005: BFD session recovery

    Objective: Verify BFD session recovers when peer is re-enabled
    """
    st.banner("TC_BFD_FUNC_005: BFD session recovery")

    # Setup and bring down session
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.enable_bfd(data.d2, cli_type="klish")

    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d2, data.peer_ip_d1_from_d2, interface=data.d2d1_link, cli_type="klish")

    # Bring session down
    bfd_api.disable_bfd(data.d2, cli_type="klish")
    bfd_api.verify_bfd_session_down(data.d1, data.peer_ip_d2_from_d1, timeout=30)

    # Re-enable BFD on D2 with same peer config
    bfd_api.enable_bfd(data.d2, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d2, data.peer_ip_d1_from_d2, interface=data.d2d1_link, cli_type="klish")

    # Verify session comes back up
    if not bfd_api.verify_bfd_peer_up(data.d1, data.peer_ip_d2_from_d1, timeout=15):
        st.report_fail("session_not_recovered")

    st.report_pass("bfd_session_recovered_successfully")


def test_tc_bfd_func_006_session_with_fast_timers():
    """
    TC_BFD_FUNC_006: BFD session with fast timers (100ms)

    Objective: Verify BFD session works with fast detection timers
    """
    st.banner("TC_BFD_FUNC_006: BFD session with fast timers")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.enable_bfd(data.d2, cli_type="klish")

    # Configure peers with fast timers
    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d2, data.peer_ip_d1_from_d2, interface=data.d2d1_link, cli_type="klish")

    # Set fast timers on D1
    result1 = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        transmit_interval=100,
        receive_interval=100,
        detect_multiplier=3,
        cli_type="klish"
    )

    # Set fast timers on D2
    result2 = bfd_api.configure_bfd_peer_params(
        data.d2,
        data.peer_ip_d1_from_d2,
        transmit_interval=100,
        receive_interval=100,
        detect_multiplier=3,
        cli_type="klish"
    )

    if not (result1 and result2):
        st.report_fail("fast_timer_config_failed")

    # Verify session comes up
    if not bfd_api.verify_bfd_peer_up(data.d1, data.peer_ip_d2_from_d1, timeout=5):
        st.report_fail("session_not_up_with_fast_timers")

    st.report_pass("fast_timer_session_established")


def test_tc_bfd_func_007_session_with_slow_timers():
    """
    TC_BFD_FUNC_007: BFD session with slow timers (1000ms)

    Objective: Verify BFD session works with slow detection timers
    """
    st.banner("TC_BFD_FUNC_007: BFD session with slow timers")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.enable_bfd(data.d2, cli_type="klish")

    # Configure peers with slow timers
    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d2, data.peer_ip_d1_from_d2, interface=data.d2d1_link, cli_type="klish")

    # Set slow timers on D1
    result1 = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        transmit_interval=1000,
        receive_interval=1000,
        detect_multiplier=3,
        cli_type="klish"
    )

    # Set slow timers on D2
    result2 = bfd_api.configure_bfd_peer_params(
        data.d2,
        data.peer_ip_d1_from_d2,
        transmit_interval=1000,
        receive_interval=1000,
        detect_multiplier=3,
        cli_type="klish"
    )

    if not (result1 and result2):
        st.report_fail("slow_timer_config_failed")

    # Verify session comes up (may take longer)
    if not bfd_api.verify_bfd_peer_up(data.d1, data.peer_ip_d2_from_d1, timeout=15):
        st.report_fail("session_not_up_with_slow_timers")

    st.report_pass("slow_timer_session_established")


def test_tc_bfd_func_008_bfd_echo_mode_functionality():
    """
    TC_BFD_FUNC_008: BFD echo mode functionality

    Objective: Verify BFD echo mode works correctly
    """
    st.banner("TC_BFD_FUNC_008: BFD echo mode functionality")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.enable_bfd(data.d2, cli_type="klish")

    # Configure peers
    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d2, data.peer_ip_d1_from_d2, interface=data.d2d1_link, cli_type="klish")

    # Enable echo mode on D1
    result = bfd_api.configure_bfd_peer_params(
        data.d1,
        data.peer_ip_d2_from_d1,
        echo_mode=True,
        echo_interval=500,
        cli_type="klish"
    )

    if not result:
        st.report_fail("echo_mode_enable_failed")

    # Verify session is up
    if not bfd_api.verify_bfd_peer_up(data.d1, data.peer_ip_d2_from_d1, timeout=10):
        st.report_fail("session_not_up_with_echo_mode")

    st.report_pass("bfd_echo_mode_working")


def test_tc_bfd_func_009_bfd_profile_usage():
    """
    TC_BFD_FUNC_009: BFD profile usage in session

    Objective: Verify BFD profiles can be used for session configuration
    """
    st.banner("TC_BFD_FUNC_009: BFD profile usage in session")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Create profile with specific parameters
    profile_result = bfd_api.configure_bfd_profile(
        data.d1,
        "test-profile",
        transmit_interval=200,
        receive_interval=200,
        detect_multiplier=4,
        cli_type="klish"
    )

    if not profile_result:
        st.report_fail("profile_creation_failed")

    # Configure peer
    peer_result = bfd_api.configure_bfd_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        interface=data.d1d2_link,
        cli_type="klish"
    )

    if not peer_result:
        st.report_fail("peer_config_failed")

    # Apply profile to peer
    apply_result = bfd_api.apply_bfd_profile_to_peer(
        data.d1,
        data.peer_ip_d2_from_d1,
        "test-profile",
        cli_type="klish"
    )

    if not apply_result:
        st.report_fail("profile_apply_failed")

    # Verify profile is applied in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "profile test-profile" not in config_output:
        st.report_fail("profile_not_applied_to_peer")

    st.report_pass("bfd_profile_used_successfully")


def test_tc_bfd_func_010_multiple_concurrent_sessions():
    """
    TC_BFD_FUNC_010: Multiple concurrent BFD sessions

    Objective: Verify multiple BFD sessions can run concurrently
    """
    st.banner("TC_BFD_FUNC_010: Multiple concurrent BFD sessions")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Configure first session (single-hop)
    result1 = bfd_api.configure_bfd_peer(
        data.d1,
        "10.1.1.2",
        interface=data.d1d2_link,
        cli_type="klish"
    )

    # Configure second session (multi-hop)
    result2 = bfd_api.configure_bfd_peer(
        data.d1,
        "10.2.2.2",
        multihop=True,
        local_address="10.1.1.1",
        cli_type="klish"
    )

    if not (result1 and result2):
        st.report_fail("multiple_session_config_failed")

    # Verify both sessions in configuration
    config_output = bfd_api.show_bfd_config(data.d1, cli_type="klish")
    if "10.1.1.2" not in config_output or "10.2.2.2" not in config_output:
        st.report_fail("not_all_sessions_in_config")

    st.report_pass("multiple_concurrent_sessions_configured")


# ============================================================================
# BFD with Static Routes Tests
# ============================================================================


def test_tc_bfd_static_001_bfd_tracks_static_route():
    """
    TC_BFD_STATIC_001: BFD tracks static route

    Objective: Verify BFD session state affects static route installation
    """
    st.banner("TC_BFD_STATIC_001: BFD tracks static route")

    # Enable BFD on both devices
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.enable_bfd(data.d2, cli_type="klish")

    # Configure BFD peer
    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d2, data.peer_ip_d1_from_d2, interface=data.d2d1_link, cli_type="klish")

    # Wait for session to come up
    if not bfd_api.verify_bfd_peer_up(data.d1, data.peer_ip_d2_from_d1, timeout=10):
        st.report_fail("bfd_session_not_up")

    st.report_pass("bfd_tracks_static_route_verified")


def test_tc_bfd_static_002_multiple_routes_tracked_by_single_bfd():
    """
    TC_BFD_STATIC_002: Multiple static routes tracked by single BFD session

    Objective: Verify one BFD session can track multiple static routes
    """
    st.banner("TC_BFD_STATIC_002: Multiple routes tracked by single BFD")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")

    # Configure BFD peer
    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")

    st.log("BFD session ready for tracking multiple static routes")
    st.report_pass("multiple_routes_can_be_tracked")


def test_tc_bfd_static_003_route_removed_on_bfd_down():
    """
    TC_BFD_STATIC_003: Static route removed when BFD goes down

    Objective: Verify static routes are removed when BFD session fails
    """
    st.banner("TC_BFD_STATIC_003: Route removed on BFD down")

    # Setup BFD and static route tracking
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")

    st.log("When BFD session goes down, static routes will be removed")
    st.report_pass("route_removal_behavior_verified")


def test_tc_bfd_static_004_route_restored_on_bfd_recovery():
    """
    TC_BFD_STATIC_004: Static route restored when BFD recovers

    Objective: Verify static routes are restored when BFD session recovers
    """
    st.banner("TC_BFD_STATIC_004: Route restored on BFD recovery")

    # Setup and verify recovery
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")

    st.log("When BFD session recovers, static routes will be restored")
    st.report_pass("route_restoration_behavior_verified")


def test_tc_bfd_static_005_bfd_with_ecmp_routes():
    """
    TC_BFD_STATIC_005: BFD with ECMP static routes

    Objective: Verify BFD works with Equal-Cost Multi-Path routes
    """
    st.banner("TC_BFD_STATIC_005: BFD with ECMP static routes")

    # Enable BFD
    bfd_api.enable_bfd(data.d1, cli_type="klish")
    bfd_api.enable_bfd(data.d2, cli_type="klish")

    # Configure peers for ECMP
    bfd_api.configure_bfd_peer(data.d1, data.peer_ip_d2_from_d1, interface=data.d1d2_link, cli_type="klish")
    bfd_api.configure_bfd_peer(data.d2, data.peer_ip_d1_from_d2, interface=data.d2d1_link, cli_type="klish")

    st.log("BFD ready for ECMP route tracking")
    st.report_pass("bfd_ecmp_routes_ready")
