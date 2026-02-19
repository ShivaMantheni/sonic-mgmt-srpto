"""
ARP TABLE VERIFICATION
Author: Shiva
2026

How to run:
  ./bin/spytest  --tryssh 1  \
  --testbed ./testbeds/ztp_standalone.yaml  \
  tests/routing/arp/test_arp_table_verification.py \
  --logs-path ./logs/test_arp_table_$(date +%F_%H%M%S) \
  --log-level debug  --skip-init-config  --ifname-type native

Description:
  Validates ARP table output formatting and entry integrity on a standalone SONiC DUT.
  TC_ARP_01 executes 'show ip arp | no-more' and verifies:
    Step 1 – Command executes and returns output.
    Step 2 – Table is non-empty (minimum entry count met).
    Step 3 – Every row conforms to standard formats:
               * Address    : valid IPv4 (e.g. 192.168.100.1)
               * MacAddress : valid 48-bit MAC (e.g. 7c:5a:1c:b1:f2:f6)
               * Iface      : non-empty interface name (Management0, PortChannel12, …)
               * Type       : Dynamic or Static
               * Action     : Fwd (or configured valid actions)
    Step 4 – Optionally verifies specific known IP→MAC→Interface mappings
             (controlled-environment check; disabled by default in YAML).

  The test is read-only — it does NOT modify DUT configuration.

Pre-requisites:
  - Topology: Standalone (D1 only) | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 1 node
        # +--------------------+
        # |    smic_sonic1     |
        # | ip: 192.168.100.101|
        # +--------------------+

  - Minimum SONiC version: any with klish (IS-CLI) enabled
  - DUT must have at least one active ARP entry (dynamic or static)
  - Required test variables (YAML): vars/routing/arp/vars_arp_table_verification.yaml
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.routing.arp as arp_api

# ---------------------------------------------------------------------------
# YAML variable file path
# ---------------------------------------------------------------------------
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "routing"
    / "arp"
    / "vars_arp_table_verification.yaml"
)

# ---------------------------------------------------------------------------
# Test Case IDs
# ---------------------------------------------------------------------------
TC_IDS = SpyTestDict(
    {
        "arp_table_formatting": "TC_ARP_01",
    }
)

# ---------------------------------------------------------------------------
# Compiled validation patterns (Step 3)
# ---------------------------------------------------------------------------
# Standard dotted-decimal IPv4
_IPV4_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

# 48-bit MAC address: six colon-separated hex octets (case-insensitive)
_MAC_RE = re.compile(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML."""
    if not DEFAULT_VAR_FILE.is_file():
        raise FileNotFoundError(
            f"ARP variable file not found: {DEFAULT_VAR_FILE}"
        )
    with DEFAULT_VAR_FILE.open(encoding="utf-8") as fh:
        content = yaml.safe_load(fh) or {}
    if "testcases" not in content:
        raise ValueError("ARP YAML must contain key 'testcases'")
    return content


def _is_valid_ipv4(addr: str) -> bool:
    """Return True if addr is a valid dotted-decimal IPv4 address."""
    if not _IPV4_RE.match(addr):
        return False
    return all(0 <= int(octet) <= 255 for octet in addr.split("."))


def _is_valid_mac(mac: str) -> bool:
    """Return True if mac matches xx:xx:xx:xx:xx:xx format."""
    return bool(_MAC_RE.match(mac))


def _validate_arp_rows(
    rows: List[Dict[str, str]],
    valid_types: List[str],
    valid_actions: List[str],
) -> List[str]:
    """
    Validate format of every parsed ARP row.

    Checks per row (Step 3 of apr_table.md):
      - address    : valid IPv4
      - macaddress : valid 48-bit MAC
      - iface      : non-empty string (interface name)
      - type       : one of valid_types (Dynamic / Static)
      - action     : one of valid_actions (Fwd …) — skipped if list is empty

    Returns a list of human-readable error strings.
    An empty list means all rows passed validation.
    """
    errors: List[str] = []
    valid_types_lower = {t.lower() for t in valid_types}
    valid_actions_lower = {a.lower() for a in valid_actions}

    for idx, row in enumerate(rows, start=1):
        address = row.get("address", "")
        mac = row.get("macaddress", "")
        iface = row.get("iface", "")
        entry_type = row.get("type", "")
        action = row.get("action", "")

        if not _is_valid_ipv4(address):
            errors.append(
                f"Row {idx}: invalid IPv4 address '{address}'"
            )
        if not _is_valid_mac(mac):
            errors.append(
                f"Row {idx}: invalid MAC address '{mac}' for IP {address}"
            )
        if not iface.strip():
            errors.append(
                f"Row {idx}: empty interface for IP {address}"
            )
        if valid_types_lower and entry_type.lower() not in valid_types_lower:
            errors.append(
                f"Row {idx}: unexpected Type '{entry_type}' for IP {address} "
                f"(expected one of {valid_types})"
            )
        if valid_actions_lower and action.lower() not in valid_actions_lower:
            errors.append(
                f"Row {idx}: unexpected Action '{action}' for IP {address} "
                f"(expected one of {valid_actions})"
            )

    return errors


# ---------------------------------------------------------------------------
# Test Class
# ---------------------------------------------------------------------------

@pytest.mark.topology("any")
class TestArpTableVerification:
    """
    Suite covering ARP table output formatting and entry integrity.

    TC_ARP_01 - Execute 'show ip arp | no-more', verify the table is
                non-empty, validate every row for correct IPv4/MAC/Interface/
                Type/Action format, and optionally verify specific known
                IP-to-MAC-to-Interface mappings.
    """

    data = SpyTestDict()

    # ------------------------------------------------------------------
    # Class-level setup / teardown
    # ------------------------------------------------------------------

    @classmethod
    def setup_class(cls) -> None:
        """Load topology and YAML config. No DUT configuration required."""
        st.banner("SETUP_CLASS: TestArpTableVerification - start")

        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        min_topology = defaults.get("min_topology") or ["D1"]
        topology = st.ensure_min_topology(*min_topology)

        cls.data.topology = topology
        cls.data.dut = topology.D1
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 10))
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))

        st.banner("SETUP_CLASS: TestArpTableVerification - complete")

    @classmethod
    def teardown_class(cls) -> None:
        """No teardown required — test is read-only."""
        st.banner("TEARDOWN_CLASS: TestArpTableVerification - complete (no-op)")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_testcase(self, tcid: str) -> Dict[str, Any]:
        """Fetch testcase definition from YAML, fail immediately if missing."""
        tc = self.data.testcases.get(tcid)
        if not tc:
            st.report_fail("msg", f"Missing testcase definition for {tcid} in YAML")
        return tc

    # ------------------------------------------------------------------
    # TC_ARP_01 — ARP Table Output Formatting and Mapping
    # ------------------------------------------------------------------

    @pytest.mark.inventory(feature="ARP", testcases=["TC_ARP_01"])
    def test_arp_table_formatting_and_mapping(self) -> None:
        """
        TC_ARP_01 — Execute 'show ip arp | no-more' and verify:
          Step 1 – Command returns non-empty output.
          Step 2 – Table meets minimum entry count.
          Step 3 – Every row has valid IPv4, MAC, Interface, Type, and Action.
          Step 4 – (Optional) Specific known IP→MAC→Interface entries are present.

        Command: show ip arp | no-more
        Expected output columns: Address, Hardware address, Interface,
                                  Egress Interface, Type, Action
        Template: show_ip_arp.tmpl
        Fields parsed: address, macaddress, iface, type, action
        """
        st.banner("TC_ARP_01: ARP Table Formatting and Mapping - start")
        dut = self.data.dut
        cli_type = self.data.cli_type
        tc = self._get_testcase(TC_IDS.arp_table_formatting)

        min_entries = int(tc.get("min_entries", 1))
        valid_types = tc.get("valid_types", ["Dynamic", "Static"])
        valid_actions = tc.get("valid_actions", ["Fwd"])
        verify_known = bool(tc.get("verify_known_entries", False))
        known_entries = tc.get("known_entries", [])

        # ------------------------------------------------------------------
        # Step 1 — Execute 'show ip arp | no-more'
        # Uses | no-more to suppress klish --more-- pagination.
        # Template index pattern 'show ip arp.*' matches this command
        # and routes output through show_ip_arp.tmpl for structured parsing.
        # ------------------------------------------------------------------
        st.log("Step 1: Executing 'show ip arp | no-more'")
        cmd = "show ip arp | no-more" if cli_type == "klish" else "show arp"
        arp_table = st.show(dut, cmd, type=cli_type)

        if not arp_table:
            st.report_tc_fail(
                TC_IDS.arp_table_formatting, "msg",
                f"Step 1 FAIL: '{cmd}' returned empty output — "
                "no ARP entries found on the DUT",
            )

        st.log(f"Step 1 PASS: Retrieved {len(arp_table)} ARP entries")

        # ------------------------------------------------------------------
        # Step 2 — Verify table has minimum expected entries
        # An empty ARP table on an active DUT indicates a connectivity or
        # configuration issue rather than a CLI format error.
        # ------------------------------------------------------------------
        st.log(
            f"Step 2: Verifying ARP table has at least {min_entries} "
            f"entr{'y' if min_entries == 1 else 'ies'}"
        )
        if len(arp_table) < min_entries:
            st.report_tc_fail(
                TC_IDS.arp_table_formatting, "msg",
                f"Step 2 FAIL: ARP table has {len(arp_table)} entries, "
                f"expected at least {min_entries}",
            )
        st.log(f"Step 2 PASS: {len(arp_table)} ARP entries found")

        # ------------------------------------------------------------------
        # Step 3 — Validate format of every row
        # Checks: valid IPv4 (Address), valid MAC (Hardware address),
        #         non-empty interface (Interface), allowed Type, allowed Action.
        # All errors are collected before reporting so the full picture is
        # available in a single failure message.
        # ------------------------------------------------------------------
        st.log(
            f"Step 3: Validating format of all {len(arp_table)} ARP rows "
            f"(valid_types={valid_types}, valid_actions={valid_actions})"
        )
        errors = _validate_arp_rows(arp_table, valid_types, valid_actions)

        if errors:
            error_summary = "; ".join(errors)
            st.log(f"Step 3 format errors: {error_summary}")
            st.report_tc_fail(
                TC_IDS.arp_table_formatting, "msg",
                f"Step 3 FAIL: {len(errors)} format error(s) in ARP table: "
                f"{error_summary}",
            )
        st.log(
            f"Step 3 PASS: All {len(arp_table)} ARP rows passed format validation"
        )

        # ------------------------------------------------------------------
        # Step 4 — (Optional) Verify specific known IP→MAC→Interface entries
        # Enabled via 'verify_known_entries: true' in YAML.
        # Uses arp_api.verify_arp() from apis/routing/arp.py which checks
        # a specific IP entry in the ARP table for the expected MAC and
        # interface values.
        # ------------------------------------------------------------------
        if verify_known:
            st.log(
                f"Step 4: Verifying {len(known_entries)} known ARP "
                f"entr{'y' if len(known_entries) == 1 else 'ies'}"
            )
            step4_errors: List[str] = []

            for entry in known_entries:
                ip_addr = entry.get("ip_address", "")
                mac_addr = entry.get("mac_address", "")
                interface = entry.get("interface", "")
                entry_type = entry.get("type", "")

                st.log(
                    f"  Checking: IP={ip_addr}, MAC={mac_addr}, "
                    f"Interface={interface}, Type={entry_type}"
                )
                result = arp_api.verify_arp(
                    dut,
                    ipaddress=ip_addr,
                    macaddress=mac_addr if mac_addr else None,
                    interface=interface if interface else None,
                    cli_type=cli_type,
                )
                if not result:
                    step4_errors.append(
                        f"IP={ip_addr} MAC={mac_addr} Iface={interface} "
                        f"not found in ARP table"
                    )

            if step4_errors:
                error_summary = "; ".join(step4_errors)
                st.log(f"Step 4 known-entry errors: {error_summary}")
                st.report_tc_fail(
                    TC_IDS.arp_table_formatting, "msg",
                    f"Step 4 FAIL: {len(step4_errors)} known ARP "
                    f"entr{'y' if len(step4_errors) == 1 else 'ies'} "
                    f"not found: {error_summary}",
                )
            st.log(
                f"Step 4 PASS: All {len(known_entries)} known ARP entries verified"
            )
        else:
            st.log(
                "Step 4: Skipped (verify_known_entries: false in YAML). "
                "Set to true and populate known_entries to enable."
            )

        st.report_tc_pass(TC_IDS.arp_table_formatting, "test_case_passed")
        st.banner("TC_ARP_01: ARP Table Formatting and Mapping - PASS")
        st.report_pass("test_case_passed")
