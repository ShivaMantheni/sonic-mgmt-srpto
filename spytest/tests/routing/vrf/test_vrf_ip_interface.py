"""
VRF INTERFACE BINDING AND IP ASSIGNMENT
Author: Shiva
2026

How to run:
  ./bin/spytest  --tryssh 1  \
  --testbed ./testbeds/ztp_standalone.yaml  \
  tests/routing/vrf/test_vrf_ip_interface.py \
  --logs-path ./logs/test_vrf_ip_interface_$(date +%F_%H%M%S) \
  --log-level debug  --skip-init-config  --ifname-type native

Description:
  Validates VRF interface binding and IP address assignment on a standalone SONiC DUT.
  TC_VRF_IP_01 verifies that a physical interface can be cleanly bound to a new VRF,
  successfully assigned an IP address within that VRF context, and the state is
  correctly reflected in 'show ip interfaces | no-more' with the expected IP/mask,
  VRF name, and Admin/Oper state (up/up).

  The test follows the procedure defined in vrf_ip_interface.md:
    Step 1 – Create VRF Vrf111
    Step 2 – Remove any existing IP from the interface (pre-condition clean)
    Step 3 – Bind the interface to the VRF (ip vrf forwarding)
    Step 4 – Assign IP address 10.0.1.1/24
    Step 5 – Bring interface admin-up (no shutdown)
    Step 6 – Verify via 'show ip interfaces | no-more'

Pre-requisites:
  - Topology: Standalone (D1 only) | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - 1 node
        # +--------------------+
        # |    smic_sonic1     |
        # |   Ethernet8        |
        # +--------------------+

  - Minimum SONiC version: any with klish (IS-CLI) enabled
  - Required test variables (YAML): vars/routing/vrf/vars_vrf_ip_interface.yaml
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from spytest import SpyTestDict, st
import apis.routing.ip as ip_api
import apis.routing.vrf as vrf_api
import apis.system.interface as intf_api

# ---------------------------------------------------------------------------
# YAML variable file path
# ---------------------------------------------------------------------------
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[3]
    / "vars"
    / "routing"
    / "vrf"
    / "vars_vrf_ip_interface.yaml"
)

# ---------------------------------------------------------------------------
# Test Case IDs
# ---------------------------------------------------------------------------
TC_IDS = SpyTestDict(
    {
        "vrf_binding_ip_assignment": "TC_VRF_IP_01",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml_data() -> Dict[str, Any]:
    """Load testcase variables from YAML."""
    if not DEFAULT_VAR_FILE.is_file():
        raise FileNotFoundError(
            f"VRF IP interface variable file not found: {DEFAULT_VAR_FILE}"
        )
    with DEFAULT_VAR_FILE.open(encoding="utf-8") as fh:
        content = yaml.safe_load(fh) or {}
    if "testcases" not in content:
        raise ValueError("VRF IP interface YAML must contain key 'testcases'")
    return content


def _klish_intf_cmd(intf: str) -> str:
    """
    Convert an interface name like 'Ethernet8' or 'PortChannel10' into
    the klish 'interface <type> <number>' command string.

    klish requires a space between the type keyword and the port number,
    e.g. 'interface Ethernet 8'.
    """
    match = re.match(r"^([A-Za-z]+)(\d+.*)$", intf)
    if match:
        return "interface {} {}".format(match.group(1), match.group(2))
    return "interface {}".format(intf)


def _safe_delete_any_ip(dut: str, intf: str, cli_type: str) -> None:
    """
    Remove ALL IP addresses currently assigned to an interface, ignoring errors.

    For klish: issues 'no ip address' (no arguments) in interface sub-mode,
    which removes all IPv4 addresses in one command.
    For non-klish: reads current IPs via get_interface_ip_address and removes
    each one individually.
    """
    if cli_type != "klish":
        try:
            entries = ip_api.get_interface_ip_address(
                dut, interface_name=intf, family="ipv4", cli_type=cli_type
            ) or []
            for entry in entries:
                ip_cidr = entry.get("ipaddr", "")
                if "/" in ip_cidr:
                    ip_addr, subnet = ip_cidr.split("/", 1)
                    ip_api.delete_ip_interface(
                        dut, intf, ip_addr, subnet,
                        family="ipv4", cli_type=cli_type, skip_error=True,
                    )
        except Exception:  # noqa: BLE001
            pass
        return

    try:
        st.config(
            dut,
            [_klish_intf_cmd(intf), "no ip address", "exit"],
            type="klish",
            conf=True,
            skip_error_check=True,
        )
    except Exception:  # noqa: BLE001
        pass


def _safe_unbind(dut: str, vrf_name: str, intf: str, cli_type: str) -> None:
    """
    Remove VRF binding from interface, ignoring errors.

    For klish: uses 'configure terminal' -> interface sub-mode ->
    'no ip vrf forwarding' via st.config with conf=True.
    For non-klish: delegates to vrf_api.bind_vrf_interface.
    """
    if cli_type != "klish":
        try:
            vrf_api.bind_vrf_interface(
                dut,
                vrf_name=vrf_name,
                intf_name=intf,
                config="no",
                cli_type=cli_type,
                skip_error=True,
            )
        except Exception:  # noqa: BLE001
            pass
        return

    try:
        st.config(
            dut,
            [_klish_intf_cmd(intf), "no ip vrf forwarding {}".format(vrf_name), "exit"],
            type="klish",
            conf=True,
            skip_error_check=True,
        )
    except Exception:  # noqa: BLE001
        pass


def _safe_delete_vrf(dut: str, vrf_name: str, cli_type: str) -> None:
    """Delete a VRF instance, ignoring errors."""
    try:
        vrf_api.config_vrf(
            dut,
            vrf_name=vrf_name,
            config="no",
            cli_type=cli_type,
            skip_error=True,
        )
    except Exception:  # noqa: BLE001
        pass


def _verify_ip_on_interface(
    dut: str,
    intf: str,
    ip_cidr: str,
    vrf_name: str,
    cli_type: str,
    expected_status: str = "",
) -> bool:
    """
    Verify IP address, VRF assignment, and optionally Admin/Oper state on an interface.

    Uses 'show ip interfaces | no-more' for klish to avoid --more-- pagination
    that causes OSError: Prompt Not Detected when the output spans many lines.
    Falls back to 'show ip interface' for non-klish CLI types.

    Parsed TextFSM fields (show_ip_interfaces.tmpl):
      interface, ipaddr, vrf, status.

    Args:
        dut:             Device under test handle.
        intf:            Interface name (e.g. 'Ethernet8').
        ip_cidr:         Expected IP/prefix (e.g. '10.0.1.1/24').
        vrf_name:        Expected VRF name (e.g. 'Vrf111').
        cli_type:        CLI type ('klish' or 'click').
        expected_status: Optional Admin/Oper string to match (e.g. 'up/up').
                         Empty string means skip status check.

    Returns:
        True if all specified fields match; False otherwise.
    """
    try:
        cmd = "show ip interfaces | no-more" if cli_type == "klish" else "show ip interface"
        output = st.show(dut, cmd, type=cli_type)
        if not output:
            st.log(f"No output from '{cmd}'")
            return False

        for entry in output:
            intf_ok = entry.get("interface") == intf
            ip_ok = entry.get("ipaddr") == ip_cidr
            vrf_ok = entry.get("vrf", "") == vrf_name
            status_ok = (
                not expected_status
                or entry.get("status", "") == expected_status
            )
            if intf_ok and ip_ok and vrf_ok and status_ok:
                st.log(
                    f"Verified: {intf} has {ip_cidr} in VRF {vrf_name}"
                    + (f" with status {expected_status}" if expected_status else "")
                )
                return True

        st.log(
            f"Expected: interface={intf}, ipaddr={ip_cidr}, vrf={vrf_name}"
            + (f", status={expected_status}" if expected_status else "")
            + f". Not found in '{cmd}' output."
        )
        return False
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Test Class
# ---------------------------------------------------------------------------

@pytest.mark.topology("any")
class TestVrfIpInterface:
    """
    Suite covering VRF interface binding and IP address assignment.

    TC_VRF_IP_01 - Create VRF 'Vrf111', bind Ethernet8, assign 10.0.1.1/24,
                   bring the interface admin-up, and verify via
                   'show ip interfaces | no-more' that the IP, VRF, and
                   Admin/Oper state (up/up) are correctly reflected.
    """

    data = SpyTestDict()

    # ------------------------------------------------------------------
    # Class-level setup / teardown
    # ------------------------------------------------------------------

    @classmethod
    def setup_class(cls) -> None:
        """Load topology, YAML config, and perform pre-condition cleanup."""
        st.banner("SETUP_CLASS: TestVrfIpInterface - start")

        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        min_topology = defaults.get("min_topology") or ["D1"]
        topology = st.ensure_min_topology(*min_topology)

        cls.data.topology = topology
        cls.data.dut = topology.D1
        cls.data.cli_type = defaults.get("cli_type", "klish")
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))

        # Per-test bookkeeping — reset in setup_method / teardown_method
        cls.data.active_vrf = None
        cls.data.active_intf = None

        st.banner("SETUP_CLASS: TestVrfIpInterface - complete")

    @classmethod
    def teardown_class(cls) -> None:
        """Safety cleanup after the entire suite."""
        st.banner("TEARDOWN_CLASS: TestVrfIpInterface - start")
        if cls.data.cleanup_enabled:
            cls._full_cleanup()
        st.banner("TEARDOWN_CLASS: TestVrfIpInterface - complete")

    # ------------------------------------------------------------------
    # Method-level setup / teardown
    # ------------------------------------------------------------------

    def setup_method(self) -> None:
        """Pre-condition cleanup + reset per-test tracking before each test."""
        self.data.active_vrf = None
        self.data.active_intf = None
        # Run idempotent pre-condition cleanup before every test
        self._full_cleanup()

    def teardown_method(self) -> None:
        """Remove configuration created by the test method (config mode safe)."""
        if not self.data.cleanup_enabled:
            return
        st.banner("TEARDOWN_METHOD: cleaning up VRF IP interface test residue")
        dut = self.data.dut
        cli_type = self.data.cli_type

        # 1. Remove all IPs from the interface (must happen before VRF unbind)
        if self.data.active_intf:
            st.log(f"Removing all IPs from {self.data.active_intf}")
            _safe_delete_any_ip(dut, self.data.active_intf, cli_type)

        # 2. Unbind interface from VRF
        if self.data.active_vrf and self.data.active_intf:
            st.log(f"Unbinding {self.data.active_intf} from VRF {self.data.active_vrf}")
            _safe_unbind(dut, self.data.active_vrf, self.data.active_intf, cli_type)

        # 3. Delete VRF
        if self.data.active_vrf:
            st.log(f"Deleting VRF {self.data.active_vrf}")
            _safe_delete_vrf(dut, self.data.active_vrf, cli_type)

        self.data.active_vrf = None
        self.data.active_intf = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @classmethod
    def _full_cleanup(cls) -> None:
        """
        Idempotent cleanup for known test VRFs and their interface bindings.

        Steps (all use st.config with conf=True — safe from any session state):
          1. Remove ALL IPs from the test interface (covers pre-existing
             default-VRF addresses; SONiC rejects VRF binding with
             'L3 Configuration exists for Interface' when any IP is present).
          2. Unbind the test interface from each known test VRF.
          3. Delete each known test VRF.
        Order: IP removal -> unbind -> VRF delete — required by SONiC.
        """
        dut = cls.data.dut
        cli_type = cls.data.cli_type
        tc1 = cls.data.testcases.get("TC_VRF_IP_01", {})
        interface = tc1.get("interface", "Ethernet8")
        known_vrfs = [tc1.get("vrf_name", "Vrf111")]

        # Step 1 — Remove ALL IPs from the interface
        st.log(f"Pre-cleanup: removing all IPs from {interface} (if any)")
        _safe_delete_any_ip(dut, interface, cli_type)

        # Step 2 — Unbind interface from each known VRF
        for vrf_name in known_vrfs:
            st.log(f"Pre-cleanup: unbinding {interface} from VRF {vrf_name} (if bound)")
            _safe_unbind(dut, vrf_name, interface, cli_type)

        # Step 3 — Delete known VRFs
        for vrf_name in known_vrfs:
            st.log(f"Pre-cleanup: deleting VRF {vrf_name} (if exists)")
            _safe_delete_vrf(dut, vrf_name, cli_type)

    def _get_testcase(self, tcid: str) -> Dict[str, Any]:
        """Fetch testcase definition from YAML, fail immediately if missing."""
        tc = self.data.testcases.get(tcid)
        if not tc:
            st.report_fail("msg", f"Missing testcase definition for {tcid} in YAML")
        return tc

    # ------------------------------------------------------------------
    # TC_VRF_IP_01 — VRF Interface Binding and IP Assignment
    # ------------------------------------------------------------------

    @pytest.mark.inventory(feature="VRF", testcases=["TC_VRF_IP_01"])
    def test_vrf_binding_and_ip_assignment(self) -> None:
        """
        TC_VRF_IP_01 — Create VRF 'Vrf111', bind Ethernet8, assign 10.0.1.1/24,
        bring the interface admin-up, and verify:
          1. 'show ip interfaces | no-more' lists Ethernet8 with 10.0.1.1/24
             in VRF Vrf111.
          2. Admin/Oper state column shows up/up.

        Procedure follows vrf_ip_interface.md Test Case 1.
        """
        st.banner("TC_VRF_IP_01: VRF Interface Binding and IP Assignment - start")
        dut = self.data.dut
        cli_type = self.data.cli_type
        tc = self._get_testcase(TC_IDS.vrf_binding_ip_assignment)

        vrf_name = tc.get("vrf_name", "Vrf111")
        interface = tc.get("interface", "Ethernet8")
        ip_address = tc.get("ip_address", "10.0.1.1")
        subnet = str(tc.get("subnet", "24"))
        expected_status = tc.get("expected_status", "up/up")

        # Track for teardown
        self.data.active_vrf = vrf_name
        self.data.active_intf = interface

        # ------------------------------------------------------------------
        # Step 1 — Create VRF
        # sonic(config)# ip vrf Vrf111
        # ------------------------------------------------------------------
        st.log(f"Step 1: Creating VRF {vrf_name}")
        if not vrf_api.config_vrf(dut, vrf_name=vrf_name, config="yes", cli_type=cli_type):
            st.report_tc_fail(
                TC_IDS.vrf_binding_ip_assignment, "msg",
                f"Failed to create VRF {vrf_name}",
            )

        # ------------------------------------------------------------------
        # Step 2 — Remove any existing IP from interface before VRF binding.
        # SONiC rejects 'ip vrf forwarding' with:
        #   % Error: L3 Configuration exists for Interface: <intf>
        # when any IP is already assigned on the interface.
        # sonic(config-if-Ethernet8)# no ip address
        # ------------------------------------------------------------------
        st.log(f"Step 2: Clearing existing IP config from {interface} before VRF binding")
        _safe_delete_any_ip(dut, interface, cli_type)

        # ------------------------------------------------------------------
        # Step 3 — Bind interface to VRF
        # sonic(config-if-Ethernet8)# ip vrf forwarding Vrf111
        # ------------------------------------------------------------------
        st.log(f"Step 3: Binding {interface} to VRF {vrf_name}")
        if not vrf_api.bind_vrf_interface(
            dut, vrf_name=vrf_name, intf_name=interface, config="yes", cli_type=cli_type
        ):
            st.report_tc_fail(
                TC_IDS.vrf_binding_ip_assignment, "msg",
                f"Failed to bind {interface} to VRF {vrf_name}",
            )

        # ------------------------------------------------------------------
        # Step 4 — Assign IP address inside the VRF context
        # sonic(config-if-Ethernet8)# ip address 10.0.1.1/24
        # ------------------------------------------------------------------
        st.log(f"Step 4: Assigning IP {ip_address}/{subnet} to {interface}")
        if not ip_api.config_ip_addr_interface(
            dut,
            interface_name=interface,
            ip_address=ip_address,
            subnet=subnet,
            family="ipv4",
            config="add",
            cli_type=cli_type,
        ):
            st.report_tc_fail(
                TC_IDS.vrf_binding_ip_assignment, "msg",
                f"Failed to assign IP {ip_address}/{subnet} to {interface}",
            )

        # ------------------------------------------------------------------
        # Step 5 — Bring interface admin-up
        # sonic(config-if-Ethernet8)# no shutdown
        # Uses interface_noshutdown from apis/system/interface.py
        # ------------------------------------------------------------------
        st.log(f"Step 5: Bringing {interface} admin-up (no shutdown)")
        intf_api.interface_noshutdown(dut, [interface], cli_type=cli_type)

        # ------------------------------------------------------------------
        # Step 6 — Verify 'show ip interfaces | no-more'
        # Expected row: Ethernet8  10.0.1.1/24  Vrf111  up/up
        # Uses | no-more to suppress klish pagination (--more-- avoidance).
        # ------------------------------------------------------------------
        st.log(
            f"Step 6: Verifying 'show ip interfaces | no-more' shows "
            f"{ip_address}/{subnet} with VRF {vrf_name} on {interface}"
            + (f" and status {expected_status}" if expected_status else "")
        )
        if not st.poll_wait(
            _verify_ip_on_interface,
            self.data.verify_timeout,
            dut,
            interface,
            f"{ip_address}/{subnet}",
            vrf_name,
            cli_type,
            expected_status,
        ):
            st.report_tc_fail(
                TC_IDS.vrf_binding_ip_assignment, "msg",
                f"'show ip interfaces | no-more' does not show {ip_address}/{subnet} "
                f"with VRF {vrf_name} on {interface}"
                + (f" and status {expected_status}" if expected_status else ""),
            )

        st.report_tc_pass(TC_IDS.vrf_binding_ip_assignment, "test_case_passed")
        st.banner("TC_VRF_IP_01: VRF Interface Binding and IP Assignment - PASS")
        st.report_pass("test_case_passed")
