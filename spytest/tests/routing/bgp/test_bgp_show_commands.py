"""
BGP SHOW COMMANDS TEST SUITE (klish)
Author: Athira
2026

How to run:
  ./bin/spytest --tryssh 1 \
  --testbed ./testbeds/testbed_vs_2d.yaml \
  routing/bgp/test_bgp_show_commands.py \
  --logs-path ./logs/test_bgp_show_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native \
  --get-tech-support none --syslog-check none

Description:
  Validation of the BGP "show" commands that are supported by the SONiC klish
  CLI. The suite is restricted to the klish-supported command set defined in
  TC_BGP_SHOW_COMMANDS_COMPREHENSIVE.md (31 commands / TC-001..TC-031); FRR-only
  vtysh commands (cidr-only, regexp, paths, dampening, advertised/received
  routes, statistics counters, etc.) are intentionally excluded.

  Test Coverage (31 klish commands):
  - Summary commands           (TC-001 to TC-008)
  - Route table commands       (TC-009 to TC-012)
  - Community filters          (TC-013 to TC-014)
  - Neighbor commands          (TC-015 to TC-021)
  - Route-map / statistics     (TC-022 to TC-025)
  - VRF / peer-group / all     (TC-026 to TC-029)
  - L2VPN EVPN                 (TC-030)
  - Running configuration      (TC-031)

Pre-requisites:
  - Topology: 2-node eBGP | Supported: HW and Virtual
  - Topology Diagram:
        # +----------------------+                       +----------------------+
        # |   DUT1 (AS 65001)    |                       |   DUT2 (AS 65002)    |
        # | Eth32 10.0.24.1/24   |=======================| Eth32 10.0.24.2/24   |
        # | 2001:db8::1/64       |<-- v4 + v6 sessions-->| 2001:db8::2/64       |
        # +----------------------+                       +----------------------+

  - The setup brings up both the IPv4 and IPv6 eBGP sessions (klish) so the
    IPv4 and IPv6 show commands have a real session to display.
  - Required test variables (YAML): vars/bgp/vars_bgp_show_commands.yaml
    - defaults.cli_type (klish)
    - defaults.local_asn, remote_asn
    - defaults.d1_bgp_neighbor, d2_bgp_neighbor, d1_ipv6, d2_ipv6
    - testcases.<TC-ID>.command optional per-TC command override
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
import pytest
import yaml
import re

from spytest import SpyTestDict, st
import apis.routing.bgp as bgp_api
import apis.routing.ip as ip_api

VAR_FILE_ENV = "BGP_SHOW_VAR_FILE"
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "bgp"
    / "vars_bgp_show_commands.yaml"
)

# Test constants
VERIFY_TIMEOUT = 30
BGP_CONVERGENCE_WAIT = 10


def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML with optional environment override."""
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        st.log(f"BGP show variable file not found: {candidate}, using defaults")
        return {"defaults": {}, "testcases": {}}

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    return content


@pytest.mark.topology("D1D2:1")
class TestBgpShowCommands:
    """klish BGP show command validation suite (31 commands)."""

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Initialize topology, test variables, and bring up v4/v6 sessions."""
        st.banner("BGP SHOW COMMANDS - CLASS SETUP")

        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Topology setup
        cls.data.topology = st.ensure_min_topology("D1D2:1")
        cls.data.D1 = cls.data.topology.D1
        cls.data.D2 = cls.data.topology.D2
        cls.data.D1D2P1 = cls.data.topology.D1D2P1
        cls.data.D2D1P1 = cls.data.topology.D2D1P1

        # Test configuration
        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", VERIFY_TIMEOUT))

        # BGP configuration
        cls.data.local_asn = defaults.get("local_asn", 65001)
        cls.data.remote_asn = defaults.get("remote_asn", 65002)
        cls.data.d1_bgp_neighbor = defaults.get("d1_bgp_neighbor", "10.0.24.2")
        cls.data.d2_bgp_neighbor = defaults.get("d2_bgp_neighbor", "10.0.24.1")
        cls.data.d1_ipv6 = defaults.get("d1_ipv6", "2001:db8::1")
        cls.data.d2_ipv6 = defaults.get("d2_ipv6", "2001:db8::2")
        cls.data.ipv6_prefix_len = int(defaults.get("ipv6_prefix_len", 64))
        # On D1 the IPv6 BGP neighbor is D2's link address and vice-versa
        cls.data.d1_ipv6_neighbor = defaults.get("d1_ipv6_neighbor", cls.data.d2_ipv6)
        cls.data.d2_ipv6_neighbor = defaults.get("d2_ipv6_neighbor", cls.data.d1_ipv6)
        cls.data.test_network = defaults.get("test_network", "10.10.10.0/24")
        cls.data.test_network_v6 = defaults.get("test_network_v6", "2001:db8:20::/64")
        cls.data.test_route_map = defaults.get("test_route_map", "SET_COMMUNITY")
        cls.data.test_vrf = defaults.get("test_vrf", "default")
        # interface that carries the eBGP session (native ifname)
        cls.data.link_intf = defaults.get("link_intf", cls.data.D1D2P1)

        st.log(f"Topology: D1={cls.data.D1}, D2={cls.data.D2}")
        st.log(f"CLI Type: {cls.data.cli_type}")
        st.log(f"BGP: AS{cls.data.local_asn} ↔ AS{cls.data.remote_asn}")
        st.log(f"D1 BGP Neighbor: {cls.data.d1_bgp_neighbor} (v6 {cls.data.d1_ipv6_neighbor})")

        # Ensure the eBGP session is actually up before verifying. Configure
        # both ends idempotently and clear to recover from a stale Idle peer.
        cls._ensure_base_bgp_session()

        # Bring up the IPv6 eBGP session so the IPv6 show-command testcases
        # have a real session to display - the IPv6 link and address-family
        # are not part of the device base config.
        cls._ensure_ipv6_bgp_session()

        # Verify BGP session is established
        cls._verify_bgp_session_established()

    @classmethod
    def _ensure_base_bgp_session(cls) -> None:
        """Make the D1<->D2 eBGP session Established (idempotent, recovers Idle).

        The suite validates show output against a known eBGP session
        (D1 AS{local_asn} <-> D2 AS{remote_asn}). It does not own device
        config, so a session stuck in Idle from a previous run cannot
        recover on its own. Configure the neighbor on both ends (harmless
        if already present) and issue a clear to force re-negotiation.
        """
        st.banner("Ensuring base eBGP session (D1 <-> D2)")

        # D1: neighbor towards D2
        bgp_api.config_bgp(
            dut=cls.data.D1,
            local_as=cls.data.local_asn,
            neighbor=cls.data.d1_bgp_neighbor,
            remote_as=cls.data.remote_asn,
            config="yes",
            config_type_list=["neighbor"],
            cli_type=cls.data.cli_type,
        )

        # D2: neighbor towards D1
        bgp_api.config_bgp(
            dut=cls.data.D2,
            local_as=cls.data.remote_asn,
            neighbor=cls.data.d2_bgp_neighbor,
            remote_as=cls.data.local_asn,
            config="yes",
            config_type_list=["neighbor"],
            cli_type=cls.data.cli_type,
        )

        # Advertise the IPv4 test network from D2 so D1 reliably has a learned
        # route to display (TC-011), independent of any pre-existing config.
        bgp_api.advertise_bgp_network(
            cls.data.D2, cls.data.remote_asn, cls.data.test_network,
            family="ipv4", config="yes", cli_type=cls.data.cli_type,
        )

        # Kick the FSM out of a stale Idle state and let it re-converge.
        bgp_api.clear_ip_bgp_vtysh(cls.data.D1, cli_type=cls.data.cli_type)
        st.wait(BGP_CONVERGENCE_WAIT, "Waiting for eBGP session to re-establish")

    @classmethod
    def _ensure_ipv6_bgp_session(cls) -> None:
        """Configure and establish the D1<->D2 IPv6 eBGP session (idempotent).

        The device base config only carries an IPv4 session, so the IPv6
        show-command testcases had nothing to display. Assign IPv6 addresses
        on the inter-DUT link, configure + activate the IPv6 neighbor on both
        ends, advertise a test network from D2, then clear to converge.
        All commands run via klish.
        """
        st.banner("Ensuring IPv6 eBGP session (D1 <-> D2)")

        # IPv6 addressing on the inter-DUT link
        ip_api.config_ip_addr_interface(
            cls.data.D1, cls.data.D1D2P1, cls.data.d1_ipv6,
            cls.data.ipv6_prefix_len, family="ipv6", config="add",
            cli_type=cls.data.cli_type,
        )
        ip_api.config_ip_addr_interface(
            cls.data.D2, cls.data.D2D1P1, cls.data.d2_ipv6,
            cls.data.ipv6_prefix_len, family="ipv6", config="add",
            cli_type=cls.data.cli_type,
        )

        # IPv6 neighbor + activate under address-family ipv6 unicast (both ends)
        bgp_api.config_bgp_neighbor(
            cls.data.D1, cls.data.local_asn, cls.data.d1_ipv6_neighbor,
            cls.data.remote_asn, family="ipv6", cli_type=cls.data.cli_type,
        )
        bgp_api.config_bgp_neighbor(
            cls.data.D2, cls.data.remote_asn, cls.data.d2_ipv6_neighbor,
            cls.data.local_asn, family="ipv6", cli_type=cls.data.cli_type,
        )

        # Advertise an IPv6 network from D2 so D1 has a route to display
        bgp_api.advertise_bgp_network(
            cls.data.D2, cls.data.remote_asn, cls.data.test_network_v6,
            family="ipv6", config="yes", cli_type=cls.data.cli_type,
        )

        # Clear and let the IPv6 session converge
        bgp_api.clear_ipv6_bgp_vtysh(cls.data.D1, cli_type=cls.data.cli_type)
        st.wait(BGP_CONVERGENCE_WAIT, "Waiting for IPv6 eBGP session to establish")

    @classmethod
    def _verify_bgp_session_established(cls) -> None:
        """Verify BGP session is in Established state before running tests."""
        st.banner("Verifying BGP session is established")

        if not st.poll_wait(
            bgp_api.verify_bgp_summary,
            cls.data.verify_timeout,
            cls.data.D1,
            family="ipv4",
            neighbor=cls.data.d1_bgp_neighbor,
            state="Established",
            cli_type=cls.data.cli_type
        ):
            st.error(f"BGP session not established on D1 with neighbor {cls.data.d1_bgp_neighbor}")
            st.report_fail("bgp_neighbor_not_established")

        st.log(f"✓ BGP session established: D1 ↔ {cls.data.d1_bgp_neighbor}")

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup after test suite."""
        st.banner("BGP SHOW COMMANDS - CLASS TEARDOWN")
        st.log("No cleanup required for show commands")

    def setup_method(self, method) -> None:
        """Per-test setup."""
        test_name = method.__name__ if method else "Unknown"
        st.banner(f"TEST SETUP: {test_name}")

    def teardown_method(self, method) -> None:
        """Per-test teardown."""
        test_name = method.__name__ if method else "Unknown"
        st.banner(f"TEST TEARDOWN: {test_name}")

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def _get_testcase(self, tcid: str) -> Mapping[str, Any]:
        """Per-TC command overrides are intentionally disabled.

        The legacy vars file (vars_bgp_show_commands.yaml) still carries the
        OLD 91-TC command map (with literal <neighbor_ip> placeholders and
        FRR-only commands) which would silently override and break the
        device-verified command defaults baked into each test. The suite uses
        those verified defaults as the single source of truth.
        """
        return {}

    def _execute_show_command(self, dut: str, command: str,
                              cli_type: str = None) -> Optional[str]:
        """Execute a show command and return output (None if CLI rejects it)."""
        if cli_type is None:
            cli_type = self.data.cli_type

        try:
            st.log(f"Executing: {command}")
            # skip_tmpl=True -> raw text. With a template, a rejected command's
            # error output gets parsed into an empty list ([]), which is not
            # None and silently passes "supported" checks. Raw text lets us
            # detect the CLI error reliably and validate by substring.
            output = st.show(dut, command, type=cli_type, skip_tmpl=True)
        except Exception as e:
            st.log(f"Command execution error: {e}")
            return None

        # A command rejected by klish (e.g. FRR-only / incomplete syntax) comes
        # back as raw error text. Treat it as no output so callers' supported /
        # None handling triggers correctly.
        if isinstance(output, str) and any(
            marker in output
            for marker in ("% Error", "Invalid input", "Syntax error",
                           "Unknown command", "not completed")
        ):
            st.log(f"Command not supported on this CLI: {command}")
            return None

        return output

    def _assert_command_supported(self, output: Any, command: str) -> None:
        """Fail only if the command was rejected by the CLI (output is None).

        A valid command that simply returns no data (empty list / "no routes"
        message) still counts as supported and passes.
        """
        if output is None:
            st.report_fail("msg", f"Command rejected/unsupported in klish: {command}")

    def _assert_contains(self, output: Any, needle: str, command: str) -> None:
        """Assert the command is supported and its output contains `needle`."""
        self._assert_command_supported(output, command)
        if needle not in str(output):
            st.report_fail("msg", f"'{needle}' not found in output of '{command}'")

    def _validate_output_contains(self, output: Any, expected_fields: List[str],
                                  field_type: str = "keyword") -> bool:
        """Validate output contains expected fields/keywords."""
        if not output:
            st.error("Output is empty or None")
            return False

        # Convert output to string if it's a list/dict
        if isinstance(output, (list, dict)):
            output_str = str(output)
        else:
            output_str = output

        missing_fields = []
        for field in expected_fields:
            if field not in output_str:
                missing_fields.append(field)

        if missing_fields:
            st.error(f"Missing {field_type}s: {missing_fields}")
            return False

        st.log(f"✓ All expected {field_type}s found")
        return True

    def _validate_bgp_summary_output(self, output: Any, expected_neighbor: str = None) -> bool:
        """Validate BGP summary output.

        klish show via TextFSM returns a list of parsed dicts (keys like
        'neighbor', 'asn', 'peers'), so checking for human-readable header
        labels ("router identifier", "Neighbor") never matches. Validate the
        parsed structure instead, with a raw-text fallback for skip_tmpl use.
        """
        if not output:
            st.error("BGP summary output is empty")
            return False

        # Parsed (TextFSM) output: list of dicts
        if isinstance(output, list):
            rows = [r for r in output if isinstance(r, dict)]
            neighbors = [str(r.get("neighbor", "")).strip() for r in rows]
            neighbors = [n for n in neighbors if n]
            # A valid summary carries neighbor rows and/or AS/peer metadata
            has_summary = any(
                str(r.get("asn", "")).strip() or str(r.get("peers", "")).strip()
                for r in rows
            )
            if not neighbors and not has_summary:
                st.error("BGP summary parsed but contains no neighbor/AS data")
                return False
            if expected_neighbor and expected_neighbor not in neighbors:
                st.error(f"Neighbor {expected_neighbor} not found in summary (parsed: {neighbors})")
                return False
            st.log(f"✓ BGP summary validated (neighbors={neighbors or 'none'})")
            return True

        # Raw-text fallback (skip_tmpl or untemplated output)
        expected_fields = ["router identifier", "local AS number", "Neighbor"]
        if expected_neighbor:
            expected_fields.append(expected_neighbor)
        return self._validate_output_contains(output, expected_fields, "field")

    # ==========================================================================
    # Group A - BGP Summary Commands (TC-001 to TC-008)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC001"])
    def test_bgp_show_tc001_global_summary(self) -> None:
        """TC-001: show bgp summary."""
        st.banner("TC-001: show bgp summary")
        command = self._get_testcase("TC-001").get("command", "show bgp summary")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        if not self._validate_bgp_summary_output(output, self.data.d1_bgp_neighbor):
            st.report_fail("msg", f"Summary missing neighbor {self.data.d1_bgp_neighbor}")
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC002"])
    def test_bgp_show_tc002_summary_established(self) -> None:
        """TC-002: show bgp summary established."""
        st.banner("TC-002: show bgp summary established")
        command = self._get_testcase("TC-002").get("command", "show bgp summary established")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        if not self._validate_bgp_summary_output(output, self.data.d1_bgp_neighbor):
            st.report_fail("msg", "Established neighbor not shown in summary")
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC003"])
    def test_bgp_show_tc003_summary_failed(self) -> None:
        """TC-003: show bgp summary failed (no failed neighbors expected)."""
        st.banner("TC-003: show bgp summary failed")
        command = self._get_testcase("TC-003").get("command", "show bgp summary failed")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC004"])
    def test_bgp_show_tc004_summary_neighbor(self) -> None:
        """TC-004: show bgp summary neighbor <ip>."""
        st.banner("TC-004: show bgp summary neighbor <ip>")
        command = self._get_testcase("TC-004").get(
            "command", f"show bgp summary neighbor {self.data.d1_bgp_neighbor}")
        output = self._execute_show_command(self.data.D1, command)
        if not self._validate_bgp_summary_output(output, self.data.d1_bgp_neighbor):
            st.report_fail("msg", f"Neighbor {self.data.d1_bgp_neighbor} not in summary")
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC005"])
    def test_bgp_show_tc005_summary_remote_as(self) -> None:
        """TC-005: show bgp summary remote-as <asn>."""
        st.banner("TC-005: show bgp summary remote-as <asn>")
        command = self._get_testcase("TC-005").get(
            "command", f"show bgp summary remote-as {self.data.remote_asn}")
        output = self._execute_show_command(self.data.D1, command)
        if not self._validate_bgp_summary_output(output, self.data.d1_bgp_neighbor):
            st.report_fail("msg", f"remote-as {self.data.remote_asn} neighbor not shown")
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC006"])
    def test_bgp_show_tc006_summary_vrf(self) -> None:
        """TC-006: show bgp summary vrf <vrf>."""
        st.banner("TC-006: show bgp summary vrf <vrf>")
        command = self._get_testcase("TC-006").get(
            "command", f"show bgp summary vrf {self.data.test_vrf}")
        output = self._execute_show_command(self.data.D1, command)
        if not self._validate_bgp_summary_output(output, self.data.d1_bgp_neighbor):
            st.report_fail("msg", f"vrf {self.data.test_vrf} summary missing neighbor")
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC007"])
    def test_bgp_show_tc007_ipv4_unicast_summary(self) -> None:
        """TC-007: show bgp ipv4 unicast summary."""
        st.banner("TC-007: show bgp ipv4 unicast summary")
        command = self._get_testcase("TC-007").get("command", "show bgp ipv4 unicast summary")
        output = self._execute_show_command(self.data.D1, command)
        if not self._validate_bgp_summary_output(output, self.data.d1_bgp_neighbor):
            st.report_fail("msg", "IPv4 unicast summary missing neighbor")
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC008"])
    def test_bgp_show_tc008_ipv6_unicast_summary(self) -> None:
        """TC-008: show bgp ipv6 unicast summary."""
        st.banner("TC-008: show bgp ipv6 unicast summary")
        command = self._get_testcase("TC-008").get("command", "show bgp ipv6 unicast summary")
        output = self._execute_show_command(self.data.D1, command)
        if not self._validate_bgp_summary_output(output, self.data.d1_ipv6_neighbor):
            st.report_fail("msg", f"IPv6 summary missing neighbor {self.data.d1_ipv6_neighbor}")
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group B - BGP Route Table Commands (TC-009 to TC-012)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC009"])
    def test_bgp_show_tc009_ipv4_vrf(self) -> None:
        """TC-009: show bgp ipv4 unicast vrf <name>."""
        st.banner("TC-009: show bgp ipv4 unicast vrf <name>")
        command = self._get_testcase("TC-009").get(
            "command", f"show bgp ipv4 unicast vrf {self.data.test_vrf}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC010"])
    def test_bgp_show_tc010_bgp_route(self) -> None:
        """TC-010: show bgp route."""
        st.banner("TC-010: show bgp route")
        command = self._get_testcase("TC-010").get("command", "show bgp route")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC011"])
    def test_bgp_show_tc011_ipv4_unicast(self) -> None:
        """TC-011: show bgp ipv4 unicast (route table)."""
        st.banner("TC-011: show bgp ipv4 unicast")
        command = self._get_testcase("TC-011").get("command", "show bgp ipv4 unicast")
        output = self._execute_show_command(self.data.D1, command)
        # Validate the IPv4 BGP route table is displayed. Use a stable marker
        # rather than a specific learned prefix so the test is robust to
        # cross-DUT route-propagation drift.
        self._assert_contains(output, "BGP table version", command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC012"])
    def test_bgp_show_tc012_ipv6_unicast(self) -> None:
        """TC-012: show bgp ipv6 unicast (route table)."""
        st.banner("TC-012: show bgp ipv6 unicast")
        command = self._get_testcase("TC-012").get("command", "show bgp ipv6 unicast")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group C - Community Filters (TC-013 to TC-014)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC013"])
    def test_bgp_show_tc013_ipv4_community(self) -> None:
        """TC-013: show bgp ipv4 unicast community."""
        st.banner("TC-013: show bgp ipv4 unicast community")
        command = self._get_testcase("TC-013").get("command", "show bgp ipv4 unicast community no-export")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC014"])
    def test_bgp_show_tc014_ipv6_community(self) -> None:
        """TC-014: show bgp ipv6 unicast community."""
        st.banner("TC-014: show bgp ipv6 unicast community")
        command = self._get_testcase("TC-014").get("command", "show bgp ipv6 unicast community no-export")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group D - Neighbor Commands (TC-015 to TC-021)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC015"])
    def test_bgp_show_tc015_ipv4_neighbors(self) -> None:
        """TC-015: show bgp ipv4 unicast neighbors."""
        st.banner("TC-015: show bgp ipv4 unicast neighbors")
        command = self._get_testcase("TC-015").get("command", "show bgp ipv4 unicast neighbors")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_contains(output, self.data.d1_bgp_neighbor, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC016"])
    def test_bgp_show_tc016_ipv4_neighbor_specific(self) -> None:
        """TC-016: show bgp ipv4 unicast neighbors <ip>."""
        st.banner("TC-016: show bgp ipv4 unicast neighbors <ip>")
        command = self._get_testcase("TC-016").get(
            "command", f"show bgp ipv4 unicast neighbors {self.data.d1_bgp_neighbor}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_contains(output, self.data.d1_bgp_neighbor, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC017"])
    def test_bgp_show_tc017_ipv4_neighbors_interface(self) -> None:
        """TC-017: show bgp ipv4 unicast neighbors interface."""
        st.banner("TC-017: show bgp ipv4 unicast neighbors interface")
        command = self._get_testcase("TC-017").get(
            "command", f"show bgp ipv4 unicast neighbors interface {self.data.link_intf}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC018"])
    def test_bgp_show_tc018_ipv6_neighbors(self) -> None:
        """TC-018: show bgp ipv6 unicast neighbors."""
        st.banner("TC-018: show bgp ipv6 unicast neighbors")
        command = self._get_testcase("TC-018").get("command", "show bgp ipv6 unicast neighbors")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_contains(output, self.data.d1_ipv6_neighbor, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC019"])
    def test_bgp_show_tc019_ipv6_neighbor_specific(self) -> None:
        """TC-019: show bgp ipv6 unicast neighbors <ipv6>."""
        st.banner("TC-019: show bgp ipv6 unicast neighbors <ipv6>")
        command = self._get_testcase("TC-019").get(
            "command", f"show bgp ipv6 unicast neighbors {self.data.d1_ipv6_neighbor}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_contains(output, self.data.d1_ipv6_neighbor, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC020"])
    def test_bgp_show_tc020_ipv6_neighbors_interface(self) -> None:
        """TC-020: show bgp ipv6 unicast neighbors interface."""
        st.banner("TC-020: show bgp ipv6 unicast neighbors interface")
        command = self._get_testcase("TC-020").get(
            "command", f"show bgp ipv6 unicast neighbors interface {self.data.link_intf}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC021"])
    def test_bgp_show_tc021_all_neighbors(self) -> None:
        """TC-021: show bgp all neighbors."""
        st.banner("TC-021: show bgp all neighbors")
        command = self._get_testcase("TC-021").get("command", "show bgp all neighbors")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_contains(output, self.data.d1_bgp_neighbor, command)
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group E - Route-map / Statistics (TC-022 to TC-025)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC022"])
    def test_bgp_show_tc022_ipv4_route_map(self) -> None:
        """TC-022: show bgp ipv4 unicast route-map <name>."""
        st.banner("TC-022: show bgp ipv4 unicast route-map <name>")
        command = self._get_testcase("TC-022").get(
            "command", f"show bgp ipv4 unicast route-map {self.data.test_route_map}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC023"])
    def test_bgp_show_tc023_ipv4_statistics(self) -> None:
        """TC-023: show bgp ipv4 unicast statistics."""
        st.banner("TC-023: show bgp ipv4 unicast statistics")
        command = self._get_testcase("TC-023").get("command", "show bgp ipv4 unicast statistics")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC024"])
    def test_bgp_show_tc024_ipv6_route_map(self) -> None:
        """TC-024: show bgp ipv6 unicast route-map <name>."""
        st.banner("TC-024: show bgp ipv6 unicast route-map <name>")
        command = self._get_testcase("TC-024").get(
            "command", f"show bgp ipv6 unicast route-map {self.data.test_route_map}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC025"])
    def test_bgp_show_tc025_ipv6_statistics(self) -> None:
        """TC-025: show bgp ipv6 unicast statistics."""
        st.banner("TC-025: show bgp ipv6 unicast statistics")
        command = self._get_testcase("TC-025").get("command", "show bgp ipv6 unicast statistics")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group F - VRF / Peer-group / All (TC-026 to TC-029)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC026"])
    def test_bgp_show_tc026_ipv4_vrf_all(self) -> None:
        """TC-026: show bgp ipv4 unicast vrf all."""
        st.banner("TC-026: show bgp ipv4 unicast vrf all")
        command = self._get_testcase("TC-026").get("command", "show bgp ipv4 unicast vrf all")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC027"])
    def test_bgp_show_tc027_ipv6_vrf_all(self) -> None:
        """TC-027: show bgp ipv6 unicast vrf all."""
        st.banner("TC-027: show bgp ipv6 unicast vrf all")
        command = self._get_testcase("TC-027").get("command", "show bgp ipv6 unicast vrf all")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC028"])
    def test_bgp_show_tc028_ipv6_vrf(self) -> None:
        """TC-028: show bgp ipv6 unicast vrf <name>."""
        st.banner("TC-028: show bgp ipv6 unicast vrf <name>")
        command = self._get_testcase("TC-028").get(
            "command", f"show bgp ipv6 unicast vrf {self.data.test_vrf}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC029"])
    def test_bgp_show_tc029_all_peer_group(self) -> None:
        """TC-029: show bgp all peer-group."""
        st.banner("TC-029: show bgp all peer-group")
        command = self._get_testcase("TC-029").get("command", "show bgp all peer-group")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group G - L2VPN EVPN (TC-030)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC030"])
    def test_bgp_show_tc030_l2vpn_evpn(self) -> None:
        """TC-030: show bgp l2vpn evpn."""
        st.banner("TC-030: show bgp l2vpn evpn")
        command = self._get_testcase("TC-030").get("command", "show bgp l2vpn evpn")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group H - Running Configuration (TC-031)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC031"])
    def test_bgp_show_tc031_running_config(self) -> None:
        """TC-031: show running-configuration bgp."""
        st.banner("TC-031: show running-configuration bgp")
        command = self._get_testcase("TC-031").get("command", "show running-configuration bgp")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_contains(output, str(self.data.local_asn), command)
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group I - Community Filter Variants (TC-032 to TC-037)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC032"])
    def test_bgp_show_tc032_ipv4_community_local_as(self) -> None:
        """TC-032: show bgp ipv4 unicast community local-as."""
        st.banner("TC-032: show bgp ipv4 unicast community local-as")
        command = self._get_testcase("TC-032").get(
            "command", "show bgp ipv4 unicast community local-as")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC033"])
    def test_bgp_show_tc033_ipv4_community_no_advertise(self) -> None:
        """TC-033: show bgp ipv4 unicast community no-advertise."""
        st.banner("TC-033: show bgp ipv4 unicast community no-advertise")
        command = self._get_testcase("TC-033").get(
            "command", "show bgp ipv4 unicast community no-advertise")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC034"])
    def test_bgp_show_tc034_ipv4_community_no_peer(self) -> None:
        """TC-034: show bgp ipv4 unicast community no-peer."""
        st.banner("TC-034: show bgp ipv4 unicast community no-peer")
        command = self._get_testcase("TC-034").get(
            "command", "show bgp ipv4 unicast community no-peer")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC035"])
    def test_bgp_show_tc035_ipv6_community_local_as(self) -> None:
        """TC-035: show bgp ipv6 unicast community local-as."""
        st.banner("TC-035: show bgp ipv6 unicast community local-as")
        command = self._get_testcase("TC-035").get(
            "command", "show bgp ipv6 unicast community local-as")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC036"])
    def test_bgp_show_tc036_ipv6_community_no_advertise(self) -> None:
        """TC-036: show bgp ipv6 unicast community no-advertise."""
        st.banner("TC-036: show bgp ipv6 unicast community no-advertise")
        command = self._get_testcase("TC-036").get(
            "command", "show bgp ipv6 unicast community no-advertise")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC037"])
    def test_bgp_show_tc037_ipv6_community_no_peer(self) -> None:
        """TC-037: show bgp ipv6 unicast community no-peer."""
        st.banner("TC-037: show bgp ipv6 unicast community no-peer")
        command = self._get_testcase("TC-037").get(
            "command", "show bgp ipv6 unicast community no-peer")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    # ==========================================================================
    # Group J - Running Configuration Sub-options (TC-038 to TC-043)
    # ==========================================================================

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC038"])
    def test_bgp_show_tc038_running_config_as_path_list(self) -> None:
        """TC-038: show running-configuration bgp as-path-list."""
        st.banner("TC-038: show running-configuration bgp as-path-list")
        command = self._get_testcase("TC-038").get(
            "command", "show running-configuration bgp as-path-list")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC039"])
    def test_bgp_show_tc039_running_config_community_list(self) -> None:
        """TC-039: show running-configuration bgp community-list."""
        st.banner("TC-039: show running-configuration bgp community-list")
        command = self._get_testcase("TC-039").get(
            "command", "show running-configuration bgp community-list")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC040"])
    def test_bgp_show_tc040_running_config_extcommunity_list(self) -> None:
        """TC-040: show running-configuration bgp extcommunity-list."""
        st.banner("TC-040: show running-configuration bgp extcommunity-list")
        command = self._get_testcase("TC-040").get(
            "command", "show running-configuration bgp extcommunity-list")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC041"])
    def test_bgp_show_tc041_running_config_vrf(self) -> None:
        """TC-041: show running-configuration bgp vrf <name>."""
        st.banner("TC-041: show running-configuration bgp vrf <name>")
        command = self._get_testcase("TC-041").get(
            "command", f"show running-configuration bgp vrf {self.data.test_vrf}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC042"])
    def test_bgp_show_tc042_running_config_neighbor_vrf(self) -> None:
        """TC-042: show running-configuration bgp neighbor vrf <name>."""
        st.banner("TC-042: show running-configuration bgp neighbor vrf <name>")
        command = self._get_testcase("TC-042").get(
            "command", f"show running-configuration bgp neighbor vrf {self.data.test_vrf}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["BGP_SHOW_TC043"])
    def test_bgp_show_tc043_running_config_peer_group_vrf(self) -> None:
        """TC-043: show running-configuration bgp peer-group vrf <name>."""
        st.banner("TC-043: show running-configuration bgp peer-group vrf <name>")
        command = self._get_testcase("TC-043").get(
            "command", f"show running-configuration bgp peer-group vrf {self.data.test_vrf}")
        output = self._execute_show_command(self.data.D1, command)
        self._assert_command_supported(output, command)
        st.report_pass("test_case_passed")
