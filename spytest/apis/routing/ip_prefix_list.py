"""
IP Prefix-List Show / Verify APIs for SONiC (klish / vtysh)
Author: Shiva
2026

These APIs complement the existing PrefixList configuration class and
config_ip_prefix_list() function in apis/routing/ip.py.  They provide
show and verify helpers that return structured data and booleans so test
scripts can make clean assertions without embedding CLI parsing logic.

Supported CLI types: klish, vtysh (click maps to vtysh)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from spytest import st


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_cli_type(dut: str, cli_type: str) -> str:
    """Normalise CLI type; collapse click → vtysh."""
    resolved = st.get_ui_type(dut, cli_type=cli_type)
    return "vtysh" if resolved in ("click", "vtysh") else "klish"


def _parse_prefix_list_entries(output: str) -> List[Dict[str, str]]:
    """
    Parse the output of 'show ip prefix-list [NAME]' into a list of dicts.

    Handles both klish and vtysh output shapes:
        klish / vtysh:
            ip prefix-list Test:
               seq 10 permit 180.0.0.0/16
               seq 20 permit 170.0.0.0/8 ge 16 le 24

    Returns list of dicts with keys:
        name, seq, action, prefix, ge (optional), le (optional)
    """
    entries: List[Dict[str, str]] = []

    # Pattern to detect prefix-list header and capture the list name.
    # Klish outputs "IP prefix list <NAME>:" (space between prefix and list),
    # while vtysh uses "ip prefix-list <NAME>:" (hyphen).  Match both forms.
    header_re = re.compile(
        r'(?:ip|ipv6)\s+prefix[-\s]list\s+(\S+)\s*:', re.IGNORECASE
    )
    # Pattern for individual sequence entries
    seq_re = re.compile(
        r'seq\s+(\d+)\s+(permit|deny)\s+(\S+)'
        r'(?:\s+ge\s+(\d+))?'
        r'(?:\s+le\s+(\d+))?',
        re.IGNORECASE,
    )

    current_name: Optional[str] = None
    for line in output.splitlines():
        stripped = line.strip()

        hm = header_re.search(stripped)
        if hm:
            current_name = hm.group(1)
            continue

        sm = seq_re.search(stripped)
        if sm and current_name:
            entry: Dict[str, str] = {
                "name": current_name,
                "seq": sm.group(1),
                "action": sm.group(2).lower(),
                "prefix": sm.group(3),
            }
            if sm.group(4):
                entry["ge"] = sm.group(4)
            if sm.group(5):
                entry["le"] = sm.group(5)
            entries.append(entry)

    return entries


def _parse_running_config_entries(output: str) -> List[Dict[str, str]]:
    """
    Parse 'show running-configuration ip prefix-list | no-more' output.

    Expected format (one entry per line):
        ip prefix-list Test seq 10 permit 180.0.0.0/16
        ip prefix-list Test seq 20 permit 170.0.0.0/8 ge 16 le 24

    Returns same dict shape as _parse_prefix_list_entries().
    """
    entries: List[Dict[str, str]] = []

    rc_re = re.compile(
        r'(?:ip|ipv6)\s+prefix-list\s+(\S+)\s+seq\s+(\d+)\s+(permit|deny)\s+(\S+)'
        r'(?:\s+ge\s+(\d+))?'
        r'(?:\s+le\s+(\d+))?',
        re.IGNORECASE,
    )
    for line in output.splitlines():
        m = rc_re.search(line.strip())
        if m:
            entry: Dict[str, str] = {
                "name": m.group(1),
                "seq": m.group(2),
                "action": m.group(3).lower(),
                "prefix": m.group(4),
            }
            if m.group(5):
                entry["ge"] = m.group(5)
            if m.group(6):
                entry["le"] = m.group(6)
            entries.append(entry)

    return entries


# ---------------------------------------------------------------------------
# Public show APIs
# ---------------------------------------------------------------------------

def show_ip_prefix_list(
    dut: str,
    name: Optional[str] = None,
    family: str = "ipv4",
    cli_type: str = "",
) -> List[Dict[str, str]]:
    """
    Execute 'show ip prefix-list [NAME]' and return parsed entries.

    :param dut:      Device handle.
    :param name:     Optional prefix-list name to filter.
    :param family:   'ipv4' (default) or 'ipv6'.
    :param cli_type: CLI type override (klish, vtysh, click).
    :return:         List of entry dicts (name, seq, action, prefix, ge?, le?).
    """
    cli = _resolve_cli_type(dut, cli_type)
    ip_cmd = "ipv6" if family == "ipv6" else "ip"

    if cli == "klish":
        cmd = "show {} prefix-list{}".format(
            ip_cmd, " {}".format(name) if name else ""
        )
        output = st.show(dut, cmd, type="klish", skip_tmpl=True)
    else:
        cmd = "show {} prefix-list{}".format(
            ip_cmd, " {}".format(name) if name else ""
        )
        output = st.show(dut, cmd, type="vtysh", skip_tmpl=True)

    st.log("show {} prefix-list output:\n{}".format(ip_cmd, output))
    return _parse_prefix_list_entries(output)


def show_running_config_prefix_list(
    dut: str,
    name: Optional[str] = None,
    family: str = "ipv4",
    cli_type: str = "",
) -> List[Dict[str, str]]:
    """
    Execute 'show running-configuration ip prefix-list [NAME]' and return
    parsed entries.

    :param dut:      Device handle.
    :param name:     Optional prefix-list name to filter.
    :param family:   'ipv4' or 'ipv6'.
    :param cli_type: CLI type override.
    :return:         List of entry dicts (name, seq, action, prefix, ge?, le?).
    """
    cli = _resolve_cli_type(dut, cli_type)
    ip_cmd = "ipv6" if family == "ipv6" else "ip"

    if cli == "klish":
        cmd = "show running-configuration {} prefix-list{} | no-more".format(
            ip_cmd, " {}".format(name) if name else ""
        )
        output = st.show(dut, cmd, type="klish", skip_tmpl=True)
    else:
        # vtysh: use 'show running-config' and grep manually
        cmd = "show running-config | grep 'prefix-list{}'".format(
            " {}".format(name) if name else ""
        )
        output = st.show(dut, cmd, type="vtysh", skip_tmpl=True)

    st.log("running-config prefix-list output:\n{}".format(output))
    return _parse_running_config_entries(output)


# ---------------------------------------------------------------------------
# Public verify APIs
# ---------------------------------------------------------------------------

def verify_ip_prefix_list(
    dut: str,
    name: str,
    expected_entries: List[Dict[str, Any]],
    family: str = "ipv4",
    cli_type: str = "",
) -> bool:
    """
    Verify that a named prefix-list contains exactly the expected entries.

    Each dict in *expected_entries* must have 'seq', 'action', 'prefix'.
    Optionally include 'ge' and/or 'le' keys.

    :return: True if all expected entries are present, False otherwise.
    """
    actual = show_ip_prefix_list(dut, name=name, family=family, cli_type=cli_type)

    # Index actual entries by sequence number for fast lookup
    actual_by_seq: Dict[str, Dict[str, str]] = {e["seq"]: e for e in actual if e.get("name") == name}

    all_ok = True
    for exp in expected_entries:
        seq = str(exp["seq"])
        act = actual_by_seq.get(seq)
        if not act:
            st.error(
                "verify_ip_prefix_list: seq {} not found in '{}' (found seqs: {})".format(
                    seq, name, list(actual_by_seq.keys())
                )
            )
            all_ok = False
            continue

        mismatches: List[str] = []
        if act.get("action") != exp["action"].lower():
            mismatches.append(
                "action expected={} actual={}".format(exp["action"], act.get("action"))
            )
        if act.get("prefix") != exp["prefix"]:
            mismatches.append(
                "prefix expected={} actual={}".format(exp["prefix"], act.get("prefix"))
            )
        if "ge" in exp and act.get("ge") != str(exp["ge"]):
            mismatches.append(
                "ge expected={} actual={}".format(exp["ge"], act.get("ge"))
            )
        if "le" in exp and act.get("le") != str(exp["le"]):
            mismatches.append(
                "le expected={} actual={}".format(exp["le"], act.get("le"))
            )

        if mismatches:
            st.error(
                "verify_ip_prefix_list: seq {} mismatch in '{}': {}".format(
                    seq, name, "; ".join(mismatches)
                )
            )
            all_ok = False
        else:
            st.log(
                "verify_ip_prefix_list: seq {} OK in '{}'".format(seq, name)
            )

    return all_ok


def verify_running_config_prefix_list(
    dut: str,
    name: str,
    expected_entries: List[Dict[str, Any]],
    family: str = "ipv4",
    cli_type: str = "",
) -> bool:
    """
    Verify prefix-list entries via 'show running-configuration ip prefix-list'.

    Accepts the same *expected_entries* format as verify_ip_prefix_list().

    :return: True if all expected entries are present, False otherwise.
    """
    actual = show_running_config_prefix_list(
        dut, name=name, family=family, cli_type=cli_type
    )

    actual_by_seq: Dict[str, Dict[str, str]] = {
        e["seq"]: e for e in actual if e.get("name") == name
    }

    all_ok = True
    for exp in expected_entries:
        seq = str(exp["seq"])
        act = actual_by_seq.get(seq)
        if not act:
            st.error(
                "verify_running_config_prefix_list: seq {} not found in '{}' "
                "(found seqs: {})".format(seq, name, list(actual_by_seq.keys()))
            )
            all_ok = False
            continue

        mismatches: List[str] = []
        if act.get("action") != exp["action"].lower():
            mismatches.append(
                "action expected={} actual={}".format(exp["action"], act.get("action"))
            )
        if act.get("prefix") != exp["prefix"]:
            mismatches.append(
                "prefix expected={} actual={}".format(exp["prefix"], act.get("prefix"))
            )
        if "ge" in exp and act.get("ge") != str(exp["ge"]):
            mismatches.append(
                "ge expected={} actual={}".format(exp["ge"], act.get("ge"))
            )
        if "le" in exp and act.get("le") != str(exp["le"]):
            mismatches.append(
                "le expected={} actual={}".format(exp["le"], act.get("le"))
            )

        if mismatches:
            st.error(
                "verify_running_config_prefix_list: seq {} mismatch in '{}': {}".format(
                    seq, name, "; ".join(mismatches)
                )
            )
            all_ok = False
        else:
            st.log(
                "verify_running_config_prefix_list: seq {} OK in '{}'".format(seq, name)
            )

    return all_ok
