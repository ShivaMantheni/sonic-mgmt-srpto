"""
IP PREFIX-LIST MANAGEMENT
Author: Shiva
2026

How to run:
  ./bin/spytest  --tryssh 1  \\
  --testbed ./testbeds/ztp_standalone.yaml  \\
  tests/routing/prefix_list/test_ip_prefix_list.py \\
  --logs-path ./logs/ip_prefix_list_$(date +%F_%H%M%S) \\
  --log-level debug  --skip-init-config  --ifname-type native

Description:
  Validates IPv4 prefix-list CRUD operations in SONiC using the klish
  (sonic-cli) interface.  The suite covers all four entry variants
  documented in ip_prifix.md:
    1. Exact match  (no ge/le)
    2. Both ge and le bounds
    3. Upper bound only (le)
    4. Lower bound only (ge)
  Each entry is verified after configuration via both
  'show ip prefix-list' and 'show running-configuration ip prefix-list'.
  Teardown removes the entire prefix-list so the DUT is left clean.

Pre-requisites:
  - Topology: standalone single-DUT | Supported: HW and Virtual
  - Topology Diagram:
        # +--------------------+
        # |     smic_sonic1    |
        # |  (standalone DUT)  |
        # +--------------------+

  - SONiC version: any version with klish (sonic-cli) support
  - Required test variables (YAML):
      vars/routing/prefix_list/vars_ip_prefix_list.yaml
"""

# Test cases for IPv4 prefix-list management scenarios from ip_prifix.md.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml

from spytest import SpyTestDict, st
from apis.routing.ip import PrefixList
import apis.routing.ip_prefix_list as pl_api

# ---------------------------------------------------------------------------
# Variable file location
# ---------------------------------------------------------------------------

DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "routing"
    / "prefix_list"
    / "vars_ip_prefix_list.yaml"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from the YAML var file."""
    if not DEFAULT_VAR_FILE.is_file():
        raise FileNotFoundError(
            "Prefix-list variable file not found: {}".format(DEFAULT_VAR_FILE)
        )
    with DEFAULT_VAR_FILE.open(encoding="utf-8") as fh:
        content = yaml.safe_load(fh) or {}
    if "testcases" not in content:
        raise ValueError(
            "Prefix-list YAML must contain key 'testcases': {}".format(DEFAULT_VAR_FILE)
        )
    return content


def _entry_to_expected(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a YAML entry dict to the expected format for verify APIs."""
    exp: Dict[str, Any] = {
        "seq": str(entry["seq"]),
        "action": str(entry["action"]),
        "prefix": str(entry["prefix"]),
    }
    if entry.get("ge") is not None:
        exp["ge"] = str(entry["ge"])
    if entry.get("le") is not None:
        exp["le"] = str(entry["le"])
    return exp


def _build_prefix_list(
    name: str,
    entries: List[Dict[str, Any]],
    cli_type: str,
) -> PrefixList:
    """Build a PrefixList object from a list of entry dicts."""
    pl = PrefixList(name, family="ipv4", cli_type=cli_type)
    for e in entries:
        ge = str(e["ge"]) if e.get("ge") is not None else ""
        le = str(e["le"]) if e.get("le") is not None else ""
        seq = str(e.get("seq", ""))
        if e["action"].lower() == "permit":
            pl.add_match_permit_sequence(e["prefix"], ge=ge, le=le, seq_num=seq)
        else:
            pl.add_match_deny_sequence(e["prefix"], ge=ge, le=le, seq_num=seq)
    return pl


def _remove_prefix_list(dut: str, name: str, cli_type: str) -> None:
    """Remove an entire named prefix-list from the device."""
    ip_cmd = "ip"
    if cli_type in ("klish",):
        cmd = "no {} prefix-list {}".format(ip_cmd, name)
        st.config(dut, cmd, type="klish", conf=True, skip_error_check=True)
    else:
        cmd = "no {} prefix-list {}".format(ip_cmd, name)
        st.config(dut, cmd, type="vtysh", skip_error_check=True)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@pytest.mark.topology("any")
class TestIpPrefixList:
    """
    Test suite for IPv4 prefix-list create / verify / delete operations.

    All scenarios are driven from vars/routing/prefix_list/vars_ip_prefix_list.yaml
    and correspond to the CLI examples in ip_prifix.md.
    """

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Load topology handles and YAML test variables."""
        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        min_topo = defaults.get("min_topology") or ["D1"]
        topology = st.ensure_min_topology(*min_topo)

        cls.data.dut = topology.D1
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 10))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))

        # Pre-suite cleanup: wipe any existing 'Test' prefix-list left over
        # from a previous run or manual configuration so tests start clean.
        st.banner("TestIpPrefixList: setup_class – pre-suite cleanup of 'Test' prefix-list")
        _remove_prefix_list(topology.D1, "Test", defaults.get("cli_type", "klish"))

        st.banner("TestIpPrefixList: setup_class complete – DUT={}  CLI={}".format(
            cls.data.dut, cls.data.cli_type
        ))

    @classmethod
    def teardown_class(cls) -> None:
        """
        Safety net: remove the 'Test' prefix-list if any testcase left
        residue behind.  Each testcase runs its own cleanup; this is a
        belt-and-suspenders guard.
        """
        if not cls.data.get("cleanup_enabled", True):
            return
        st.banner("TestIpPrefixList: teardown_class – removing residual prefix-lists")
        _remove_prefix_list(cls.data.dut, "Test", cls.data.cli_type)

    def setup_method(self) -> None:
        """
        Per-test pre-cleanup: ensure the 'Test' prefix-list is absent
        before each testcase so stale entries never interfere.
        """
        _remove_prefix_list(self.data.dut, "Test", self.data.cli_type)

    # ------------------------------------------------------------------
    # TC_PL_001 – Exact match (no ge / le)
    # ------------------------------------------------------------------

    @pytest.mark.inventory(feature="Regression", testcases=["TC_PL_001"])
    def test_prefix_list_exact_match(self) -> None:
        """
        TC_PL_001 – Configure a prefix-list with an exact-match entry
        (no ge/le bounds) and verify it appears in both
        'show ip prefix-list' and 'show running-configuration'.

        CLI equivalent from ip_prifix.md:
            sonic(config)# ip prefix-list Test seq 10 permit 180.0.0.0/16
        """
        tc = self.data.testcases.get("TC_PL_001")
        if not tc:
            st.report_fail("msg", "Testcase TC_PL_001 not found in YAML")

        name = tc["prefix_list_name"]
        entry = tc["entry"]
        expected = [_entry_to_expected(entry)]
        dut = self.data.dut
        cli = self.data.cli_type

        st.banner("TC_PL_001: Exact match – {} seq {} {} {}".format(
            name, entry["seq"], entry["action"], entry["prefix"]
        ))

        try:
            pl = _build_prefix_list(name, [entry], cli)
            if not pl.execute_command(dut, config="yes"):
                st.report_fail("msg", "TC_PL_001: Failed to configure prefix-list '{}'".format(name))

            # Verify via show ip prefix-list
            if not pl_api.verify_ip_prefix_list(dut, name, expected, cli_type=cli):
                st.report_fail(
                    "msg",
                    "TC_PL_001: Prefix-list '{}' entry seq={} not found via "
                    "'show ip prefix-list'".format(name, entry["seq"]),
                )

            # Verify via show running-configuration
            if not pl_api.verify_running_config_prefix_list(
                dut, name, expected, cli_type=cli
            ):
                st.report_fail(
                    "msg",
                    "TC_PL_001: Prefix-list '{}' entry seq={} not found via "
                    "'show running-configuration ip prefix-list'".format(
                        name, entry["seq"]
                    ),
                )

        finally:
            _remove_prefix_list(dut, name, cli)

        st.report_pass("test_case_passed")

    # ------------------------------------------------------------------
    # TC_PL_002 – Both ge and le bounds
    # ------------------------------------------------------------------

    @pytest.mark.inventory(feature="Regression", testcases=["TC_PL_002"])
    def test_prefix_list_ge_le_bounds(self) -> None:
        """
        TC_PL_002 – Configure a prefix-list entry with both ge and le
        bounds and verify the range is correctly stored.

        CLI equivalent from ip_prifix.md:
            sonic(config)# ip prefix-list Test seq 20 permit 170.0.0.0/8 ge 16 le 24
        """
        tc = self.data.testcases.get("TC_PL_002")
        if not tc:
            st.report_fail("msg", "Testcase TC_PL_002 not found in YAML")

        name = tc["prefix_list_name"]
        entry = tc["entry"]
        expected = [_entry_to_expected(entry)]
        dut = self.data.dut
        cli = self.data.cli_type

        st.banner("TC_PL_002: ge+le bounds – {} seq {} {} {} ge {} le {}".format(
            name, entry["seq"], entry["action"], entry["prefix"],
            entry.get("ge", ""), entry.get("le", "")
        ))

        try:
            pl = _build_prefix_list(name, [entry], cli)
            if not pl.execute_command(dut, config="yes"):
                st.report_fail("msg", "TC_PL_002: Failed to configure prefix-list '{}'".format(name))

            if not pl_api.verify_ip_prefix_list(dut, name, expected, cli_type=cli):
                st.report_fail(
                    "msg",
                    "TC_PL_002: Prefix-list '{}' ge/le entry not found via "
                    "'show ip prefix-list'".format(name),
                )

            if not pl_api.verify_running_config_prefix_list(
                dut, name, expected, cli_type=cli
            ):
                st.report_fail(
                    "msg",
                    "TC_PL_002: Prefix-list '{}' ge/le entry not found in "
                    "running-configuration".format(name),
                )

        finally:
            _remove_prefix_list(dut, name, cli)

        st.report_pass("test_case_passed")

    # ------------------------------------------------------------------
    # TC_PL_003 – Upper bound only (le)
    # ------------------------------------------------------------------

    @pytest.mark.inventory(feature="Regression", testcases=["TC_PL_003"])
    def test_prefix_list_le_only(self) -> None:
        """
        TC_PL_003 – Configure a prefix-list entry with only a le (upper
        bound) and verify the entry.

        CLI equivalent from ip_prifix.md:
            sonic(config)# ip prefix-list Test seq 30 permit 192.168.0.0/16 le 24
        """
        tc = self.data.testcases.get("TC_PL_003")
        if not tc:
            st.report_fail("msg", "Testcase TC_PL_003 not found in YAML")

        name = tc["prefix_list_name"]
        entry = tc["entry"]
        expected = [_entry_to_expected(entry)]
        dut = self.data.dut
        cli = self.data.cli_type

        st.banner("TC_PL_003: le-only – {} seq {} {} {} le {}".format(
            name, entry["seq"], entry["action"], entry["prefix"], entry.get("le", "")
        ))

        try:
            pl = _build_prefix_list(name, [entry], cli)
            if not pl.execute_command(dut, config="yes"):
                st.report_fail("msg", "TC_PL_003: Failed to configure prefix-list '{}'".format(name))

            if not pl_api.verify_ip_prefix_list(dut, name, expected, cli_type=cli):
                st.report_fail(
                    "msg",
                    "TC_PL_003: Prefix-list '{}' le-only entry not found via "
                    "'show ip prefix-list'".format(name),
                )

            if not pl_api.verify_running_config_prefix_list(
                dut, name, expected, cli_type=cli
            ):
                st.report_fail(
                    "msg",
                    "TC_PL_003: Prefix-list '{}' le-only entry not found in "
                    "running-configuration".format(name),
                )

        finally:
            _remove_prefix_list(dut, name, cli)

        st.report_pass("test_case_passed")

    # ------------------------------------------------------------------
    # TC_PL_004 – Lower bound only (ge)
    # ------------------------------------------------------------------

    @pytest.mark.inventory(feature="Regression", testcases=["TC_PL_004"])
    def test_prefix_list_ge_only(self) -> None:
        """
        TC_PL_004 – Configure a prefix-list entry with only a ge (lower
        bound) and verify the entry.

        CLI equivalent from ip_prifix.md:
            sonic(config)# ip prefix-list Test seq 40 permit 10.0.0.0/8 ge 24
        """
        tc = self.data.testcases.get("TC_PL_004")
        if not tc:
            st.report_fail("msg", "Testcase TC_PL_004 not found in YAML")

        name = tc["prefix_list_name"]
        entry = tc["entry"]
        expected = [_entry_to_expected(entry)]
        dut = self.data.dut
        cli = self.data.cli_type

        st.banner("TC_PL_004: ge-only – {} seq {} {} {} ge {}".format(
            name, entry["seq"], entry["action"], entry["prefix"], entry.get("ge", "")
        ))

        try:
            pl = _build_prefix_list(name, [entry], cli)
            if not pl.execute_command(dut, config="yes"):
                st.report_fail("msg", "TC_PL_004: Failed to configure prefix-list '{}'".format(name))

            if not pl_api.verify_ip_prefix_list(dut, name, expected, cli_type=cli):
                st.report_fail(
                    "msg",
                    "TC_PL_004: Prefix-list '{}' ge-only entry not found via "
                    "'show ip prefix-list'".format(name),
                )

            if not pl_api.verify_running_config_prefix_list(
                dut, name, expected, cli_type=cli
            ):
                st.report_fail(
                    "msg",
                    "TC_PL_004: Prefix-list '{}' ge-only entry not found in "
                    "running-configuration".format(name),
                )

        finally:
            _remove_prefix_list(dut, name, cli)

        st.report_pass("test_case_passed")

    # ------------------------------------------------------------------
    # TC_PL_005 – Full scenario: 4 entries, verify running-configuration
    # ------------------------------------------------------------------

    @pytest.mark.inventory(feature="Regression", testcases=["TC_PL_005"])
    def test_prefix_list_all_entries_running_config(self) -> None:
        """
        TC_PL_005 – Configure all four entries from ip_prifix.md in a
        single prefix-list 'Test' and verify them via
        'show running-configuration ip prefix-list | no-more'.

        CLI equivalent (all four sequences applied together):
            sonic(config)# ip prefix-list Test seq 10 permit 180.0.0.0/16
            sonic(config)# ip prefix-list Test seq 20 permit 170.0.0.0/8 ge 16 le 24
            sonic(config)# ip prefix-list Test seq 30 permit 192.168.0.0/16 le 24
            sonic(config)# ip prefix-list Test seq 40 permit 10.0.0.0/8 ge 24

        Expected running-config output:
            ip prefix-list Test seq 10 permit 180.0.0.0/16
            ip prefix-list Test seq 20 permit 170.0.0.0/8 ge 16 le 24
            ip prefix-list Test seq 30 permit 192.168.0.0/16 le 24
            ip prefix-list Test seq 40 permit 10.0.0.0/8 ge 24
        """
        tc = self.data.testcases.get("TC_PL_005")
        if not tc:
            st.report_fail("msg", "Testcase TC_PL_005 not found in YAML")

        name = tc["prefix_list_name"]
        entries = tc.get("entries") or []
        if not entries:
            st.report_fail("msg", "TC_PL_005: no entries defined in YAML")

        expected = [_entry_to_expected(e) for e in entries]
        dut = self.data.dut
        cli = self.data.cli_type

        st.banner("TC_PL_005: All 4 entries – verify via running-configuration")

        try:
            pl = _build_prefix_list(name, entries, cli)
            if not pl.execute_command(dut, config="yes"):
                st.report_fail(
                    "msg",
                    "TC_PL_005: Failed to configure prefix-list '{}' with all entries".format(name),
                )

            if not pl_api.verify_running_config_prefix_list(
                dut, name, expected, cli_type=cli
            ):
                st.report_fail(
                    "msg",
                    "TC_PL_005: One or more entries missing in "
                    "'show running-configuration ip prefix-list'",
                )

        finally:
            _remove_prefix_list(dut, name, cli)

        st.report_pass("test_case_passed")

    # ------------------------------------------------------------------
    # TC_PL_006 – Full scenario: 4 entries, verify show ip prefix-list
    # ------------------------------------------------------------------

    @pytest.mark.inventory(feature="Regression", testcases=["TC_PL_006"])
    def test_prefix_list_all_entries_show(self) -> None:
        """
        TC_PL_006 – Configure all four entries from ip_prifix.md and
        verify them via 'show ip prefix-list'.

        CLI equivalent (verification):
            sonic# show ip prefix-list

        Expected output (example):
            ip prefix-list Test:
               seq 10 permit 180.0.0.0/16
               seq 20 permit 170.0.0.0/8 ge 16 le 24
               seq 30 permit 192.168.0.0/16 le 24
               seq 40 permit 10.0.0.0/8 ge 24
        """
        tc = self.data.testcases.get("TC_PL_006")
        if not tc:
            st.report_fail("msg", "Testcase TC_PL_006 not found in YAML")

        name = tc["prefix_list_name"]
        entries = tc.get("entries") or []
        if not entries:
            st.report_fail("msg", "TC_PL_006: no entries defined in YAML")

        expected = [_entry_to_expected(e) for e in entries]
        dut = self.data.dut
        cli = self.data.cli_type

        st.banner("TC_PL_006: All 4 entries – verify via show ip prefix-list")

        try:
            pl = _build_prefix_list(name, entries, cli)
            if not pl.execute_command(dut, config="yes"):
                st.report_fail(
                    "msg",
                    "TC_PL_006: Failed to configure prefix-list '{}' with all entries".format(name),
                )

            if not pl_api.verify_ip_prefix_list(dut, name, expected, cli_type=cli):
                st.report_fail(
                    "msg",
                    "TC_PL_006: One or more entries missing in 'show ip prefix-list'",
                )

        finally:
            _remove_prefix_list(dut, name, cli)

        st.report_pass("test_case_passed")
