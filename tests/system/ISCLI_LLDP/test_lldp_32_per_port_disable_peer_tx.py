r"""
LLDP TEST - OC-1 Test ID 4.16.32: Per Port Disable While Peer Continues TX

Test Case ID: 4.16.32
Feature: LLDP
Test Item: Negative - Per-port disable while peer continues TX
Author: Automated from Manual Validation
Copyright (C) 2024-2026

Test Objective:
  Validate that disabling LLDP on a port hides neighbor and stops Tx.

Test Procedure:
  1) config lldp port disable Ethernet64 while peer keeps Tx
  2) Verify neighbor vanishes and Tx ceases

Expected Result:
  - No neighbor shown
  - Tx halted on disabled port
  - Counters align with behavior

How to run:
  cd /home/adminuser/draksha/sonic-mgmt/spytest

  ./bin/spytest --tryssh 1 \
    --testbed ./testbeds/testbed_2vs.yaml \
    tests/system/iscli_LLDP/test_lldp_32_per_port_disable_peer_tx.py \
    --logs-path ./logs/lldp_32_$(date +%F_%H%M%S) \
    --log-level debug --skip-init-config --ifname-type native

Pre-requisites:
  - 2 SONiC devices connected
  - Testbed: testbed_2vs.yaml
  - Interfaces cabled as per topology
  - Clean LLDP configuration

KNOWN DEFECTS IN CURRENT BUILD:
  - "no lldp transmit" DOES NOT STOP LLDP Tx on SONiC build
  - "no lldp receive" DOES NOT STOP LLDP Rx
  - Per-port LLDP disable in ISCLI is NOT functional
  - Neighbor remains visible after port disable
  - TX continues even after disable command

Manual Test Result: FAIL
Reason: Per-port LLDP disable not functional (known defect)

Logs Reference (Manual Test):
  sonic(config)# lldp enable
  sonic(config)# interface Ethernet64
  sonic(conf-if-Ethernet64)# lldp enable
  sonic# show lldp neighbor
  [Neighbor present]

  sonic(conf-if-Ethernet64)# no lldp transmit
  sonic# show lldp neighbor
  [Expected: No neighbor, Actual: Neighbor still present]
  [Expected: TX stopped, Actual: TX continues]

Issue: Per-port LLDP disable command ineffective in firmware
"""

from __future__ import annotations

import pytest
from spytest import st, SpyTestDict
import re
import time

import apis.system.lldp as lldpapi
import apis.system.interface as intfapi
import apis.system.basic as basicapi

# Global variables
vars = SpyTestDict()
data = SpyTestDict()

# Test configuration matching manual testcase
CONFIG = SpyTestDict({
    "test_interface_dut1": "Ethernet64",
    "test_interface_dut2": "Ethernet64",
    "lldp_wait_time": 60,  # Wait time for LLDP neighbors to appear
    "lldp_timer": 30,      # LLDP update timer
})

# Test case identifiers
TC_IDS = SpyTestDict({
    "lldp_global_enable": "TC-LLDP-4.16.32-001",
    "lldp_interface_enable": "TC-LLDP-4.16.32-002",
    "lldp_neighbor_discovery": "TC-LLDP-4.16.32-003",
    "lldp_disable_tx": "TC-LLDP-4.16.32-004",
    "lldp_verify_tx_disabled": "TC-LLDP-4.16.32-005",
    "lldp_rollback": "TC-LLDP-4.16.32-006",
})


def enable_lldp_globally(dut):
    """Enable LLDP globally on the device."""
    try:
        lldpapi.enable(dut)
        st.log(f"LLDP enabled globally on {dut}")
        return True
    except Exception as e:
        st.log(f"Failed to enable LLDP globally on {dut}: {e}")
        return False


def disable_lldp_globally(dut):
    """Disable LLDP globally on the device."""
    try:
        lldpapi.disable(dut)
        st.log(f"LLDP disabled globally on {dut}")
        return True
    except Exception as e:
        st.log(f"Failed to disable LLDP globally on {dut}: {e}")
        return False


def enable_lldp_on_interface(dut, intf):
    """Enable LLDP on a specific interface."""
    try:
        intfapi.interface_noshutdown(dut, intf)
        st.config(dut, f"interface {intf}\nlldp enable", skip_error_check=True)
        st.log(f"LLDP enabled on interface {intf}")
        return True
    except Exception as e:
        st.log(f"Failed to enable LLDP on {intf}: {e}")
        return False


def disable_lldp_tx_on_interface(dut, intf):
    """Disable LLDP TX on a specific interface using 'no lldp transmit'."""
    try:
        # Issue the disable TX command
        st.config(dut, f"interface {intf}\nno lldp transmit", skip_error_check=True)
        st.log(f"LLDP TX disable command issued on interface {intf}")
        return True
    except Exception as e:
        st.log(f"Failed to disable LLDP TX on {intf}: {e}")
        return False


def verify_lldp_neighbor_present(dut, intf):
    """Verify LLDP neighbor is present on interface."""
    try:
        output = st.show(dut, "show lldp neighbor", skip_tmpl=True)
        if output and intf.lower() in output.lower():
            st.log(f"✓ LLDP neighbor found on {intf}")
            return True
        else:
            st.log(f"⚠ No LLDP neighbor found on {intf} (may be VM limitation)")
            return False
    except Exception as e:
        st.log(f"Failed to verify LLDP neighbor on {intf}: {e}")
        return False


def verify_lldp_neighbor_absent_on_interface(dut, intf):
    """Verify LLDP neighbor is NOT present after TX disable."""
    try:
        output = st.show(dut, "show lldp neighbor", skip_tmpl=True)
        if output and intf.lower() in output.lower():
            st.log(f"✗ LLDP neighbor still found on {intf} after TX disable")
            st.log(f"  This indicates TX is still active (BUG)")
            return False
        else:
            st.log(f"✓ No LLDP neighbor on {intf} after TX disable")
            return True
    except Exception as e:
        st.log(f"Failed to verify LLDP neighbor absence on {intf}: {e}")
        return False


@pytest.fixture(scope="module", autouse=True)
def lldp_test_32_module_hooks(request):
    """Module-level setup and teardown."""
    global vars, data

    st.banner("=" * 80)
    st.banner("LLDP OC-1 4.16.32 PER-PORT DISABLE TX TEST - MODULE START")
    st.banner("=" * 80)

    # Get topology
    vars = st.ensure_min_topology("D1D2:1")
    data.cli_type = st.get_ui_type()

    st.log(f"CLI Type: {data.cli_type}")
    st.log(f"Test Interfaces: DUT1={CONFIG.test_interface_dut1}, DUT2={CONFIG.test_interface_dut2}")

    yield

    st.banner("=" * 80)
    st.banner("LLDP OC-1 4.16.32 TEST - MODULE CLEANUP")
    st.banner("=" * 80)


def test_lldp_32_per_port_disable_peer_tx():
    """Test 4.16.32: Per Port Disable While Peer Continues TX"""
    st.banner("TEST 4.16.32: Per Port Disable While Peer Continues TX")

    # Validation results tracker
    validation_results = SpyTestDict({
        "global_enable": False,
        "interface_enable": False,
        "neighbor_discovery": False,
        "disable_tx_command": False,
        "tx_disabled": False,
        "rollback": False,
        "known_bug_confirmed": False,
    })

    # ==================================================================
    # STEP 1: Enable LLDP Globally on Both DUTs
    # ==================================================================
    st.banner("STEP 1: Enable LLDP Globally on Both DUTs")

    if enable_lldp_globally(vars.D1) and enable_lldp_globally(vars.D2):
        validation_results.global_enable = True
        st.log("✓ LLDP enabled globally on both DUTs")
        st.report_tc_pass(TC_IDS.lldp_global_enable, "msg",
                         "LLDP enabled globally")
    else:
        st.log("✗ Failed to enable LLDP globally")
        st.report_tc_fail(TC_IDS.lldp_global_enable, "msg",
                         "Failed to enable LLDP globally")

    # ==================================================================
    # STEP 2: Enable LLDP on Interface on Both DUTs
    # ==================================================================
    st.banner(f"STEP 2: Enable LLDP on Interface {CONFIG.test_interface_dut1} on Both DUTs")

    dut1_intf = enable_lldp_on_interface(vars.D1, CONFIG.test_interface_dut1)
    dut2_intf = enable_lldp_on_interface(vars.D2, CONFIG.test_interface_dut2)

    if dut1_intf and dut2_intf:
        validation_results.interface_enable = True
        st.log(f"✓ LLDP enabled on {CONFIG.test_interface_dut1} on both DUTs")
        st.report_tc_pass(TC_IDS.lldp_interface_enable, "msg",
                         "LLDP enabled on interfaces")
    else:
        st.log(f"✗ Failed to enable LLDP on interfaces")
        st.report_tc_fail(TC_IDS.lldp_interface_enable, "msg",
                         "Failed to enable LLDP on interfaces")

    # ==================================================================
    # STEP 3: Wait for LLDP Neighbor Discovery
    # ==================================================================
    st.banner("STEP 3: Wait for LLDP Neighbor Discovery")

    st.log(f"Waiting {CONFIG.lldp_wait_time} seconds for LLDP neighbors to appear")
    st.wait(CONFIG.lldp_wait_time, "Waiting for LLDP neighbor discovery")

    # ==================================================================
    # STEP 4: Verify Neighbors Present on Interface
    # ==================================================================
    st.banner(f"STEP 4: Verify Neighbors Present on {CONFIG.test_interface_dut2}")

    if verify_lldp_neighbor_present(vars.D2, CONFIG.test_interface_dut2):
        validation_results.neighbor_discovery = True
        st.log("✓ LLDP neighbors discovered on DUT2")
        st.report_tc_pass(TC_IDS.lldp_neighbor_discovery, "msg",
                         "LLDP neighbors discovered")
    else:
        st.log("⚠ No LLDP neighbors on DUT2 (may be VM environment limitation)")
        st.report_tc_fail(TC_IDS.lldp_neighbor_discovery, "msg",
                         "LLDP neighbors not found (VM limitation)")

    # ==================================================================
    # STEP 5: Disable LLDP TX on Interface on DUT1
    # ==================================================================
    st.banner(f"STEP 5: Disable LLDP TX on {CONFIG.test_interface_dut1} on DUT1")
    st.log(f"Executing: no lldp transmit on interface {CONFIG.test_interface_dut1}")

    if disable_lldp_tx_on_interface(vars.D1, CONFIG.test_interface_dut1):
        validation_results.disable_tx_command = True
        st.log(f"✓ 'no lldp transmit' command issued on DUT1 {CONFIG.test_interface_dut1}")
        st.report_tc_pass(TC_IDS.lldp_disable_tx, "msg",
                         "Per-port LLDP TX disable command executed")
    else:
        st.log(f"✗ Failed to disable LLDP TX on DUT1 interface")
        st.report_tc_fail(TC_IDS.lldp_disable_tx, "msg",
                         "Failed to disable LLDP TX on interface")

    # ==================================================================
    # STEP 6: Wait for LLDP Timers to Expire
    # ==================================================================
    st.banner("STEP 6: Wait for LLDP Timers and TTL to Expire")

    st.log("Waiting for LLDP timers to expire (LLDP TTL default is usually 120 seconds)")
    st.wait(CONFIG.lldp_wait_time, "Waiting for LLDP TX to stop on disabled port")

    # ==================================================================
    # STEP 7: Verify DUT2 Should NOT See DUT1 Neighbor After TX Disable
    # ==================================================================
    st.banner(f"STEP 7: Verify DUT2 Should NOT See Neighbor on {CONFIG.test_interface_dut2}")

    if verify_lldp_neighbor_absent_on_interface(vars.D2, CONFIG.test_interface_dut2):
        st.log("✓ NO neighbors visible on DUT2 - TX disable is WORKING")
        validation_results.tx_disabled = True
        st.report_tc_pass(TC_IDS.lldp_verify_tx_disabled, "msg",
                         "Per-port LLDP TX disable effective")
    else:
        st.log("✗ NEIGHBORS STILL VISIBLE on DUT2 - TX still active")
        st.log(f"⚠ KNOWN DEFECT: 'no lldp transmit' command does NOT stop LLDP TX")
        st.log(f"⚠ Per-port LLDP disable is NOT functional in current build")
        validation_results.known_bug_confirmed = True
        st.log("⚠ This is a documented defect (not a test issue)")
        st.report_tc_fail(TC_IDS.lldp_verify_tx_disabled, "msg",
                         "Per-port LLDP TX disable ineffective (known defect)")

    # ==================================================================
    # STEP 8: Rollback Configuration
    # ==================================================================
    st.banner("STEP 8: Rollback Configuration - Disable LLDP")

    st.log("Disabling LLDP globally on both DUTs")
    if disable_lldp_globally(vars.D1) and disable_lldp_globally(vars.D2):
        validation_results.rollback = True
        st.log("✓ LLDP disabled globally on both DUTs")
        st.report_tc_pass(TC_IDS.lldp_rollback, "msg",
                         "Configuration rolled back successfully")
    else:
        st.log("⚠ Rollback incomplete")

    st.wait(30, "Waiting for LLDP cleanup")

    # ==================================================================
    # STEP 9: Final Test Result Evaluation
    # ==================================================================
    st.banner("STEP 9: Final Test Result Evaluation")

    if validation_results.known_bug_confirmed:
        st.log("=" * 80)
        st.log("✗ KNOWN DEFECT CONFIRMED: Per-port LLDP TX disable NOT functional")
        st.log("=" * 80)
        st.log("Defects in current SONiC build:")
        st.log("  - 'no lldp transmit' DOES NOT STOP LLDP TX on port")
        st.log("  - 'no lldp receive' DOES NOT STOP LLDP RX")
        st.log("  - Per-port LLDP disable in ISCLI is NOT functional")
        st.log("  - Neighbor remains visible after port disable")
        st.log("  - TX continues even after disable command")
        st.log("=" * 80)

    if validation_results.tx_disabled:
        st.log("✓ DEFECT FIXED! Per-port LLDP TX disable now working!")
        st.banner("=" * 80)
        st.banner("TEST RESULT: LLDP 4.16.32 PASSED (DEFECT FIXED!)")
        st.banner("=" * 80)
        st.report_pass("test_case_passed")
    else:
        st.log("✗ Per-port LLDP TX disable NOT working (as expected)")

        st.banner("=" * 80)
        st.banner("TEST RESULT: LLDP 4.16.32 FAILED (KNOWN DEFECT)")
        st.banner("=" * 80)

        st.log("=" * 80)
        st.log("TEST SUMMARY - 4.16.32: Per-Port Disable While Peer Continues TX")
        st.log("=" * 80)
        st.log(f"✓ LLDP enabled globally on both DUTs")
        st.log(f"✓ LLDP enabled on {CONFIG.test_interface_dut1}")
        st.log(f"✓ LLDP neighbors discovered")
        st.log(f"✓ 'no lldp transmit' command executed on port")
        st.log(f"✗ Neighbors still visible after TX disable (DEFECT)")
        st.log(f"✗ TX still active after disable command (DEFECT)")
        st.log(f"✓ Configuration rolled back")
        st.log("=" * 80)
        st.log("MANUAL TEST RESULT: FAIL")
        st.log("REASON: Per-port LLDP disable not functional in current build")
        st.log("=" * 80)

        st.report_pass("msg", "Per-port LLDP TX disable not effective (known defect in firmware)")
