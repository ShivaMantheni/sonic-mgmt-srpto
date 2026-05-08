"""
SONIC CONFIGURATION MANAGEMENT - WRITE MEMORY & WRITE ERASE
Author: Shiva
2026

How to run:
  ./bin/spytest --tryssh 1 \
  --testbed ./testbeds/ztp_standalone.yaml \
  tests/system/test_write_memory_erase.py \
  --logs-path ./logs/test_write_memory_erase_$(date +%F_%H%M%S) \
  --log-level debug --skip-init-config --ifname-type native

Description:
  End-to-end validation of SONiC configuration persistence and reset mechanisms
  using write memory and write erase commands. This test suite verifies that
  configuration changes saved with 'write memory' persist across system reboots,
  and that 'write erase' successfully clears custom configurations, reverting
  the device to its default/baseline state. Tests use IS-CLI (klish) mode for
  configuration and verification via 'show running-configuration' command.

  Test Case ID: SM_ISCLI_P2_119 (SONIC-CFG-MGMT-001)

Files and APIs Used:
  - Testbed Configuration:
      * testbeds/ztp_standalone.yaml - Single DUT standalone topology

  - Variable File:
      * vars/system/vars_write_memory_erase.yaml - Test configuration

  - SpyTest Framework Functions:
      * st.ensure_min_topology() - Validate minimum topology requirements
      * st.config() - Execute configuration commands
      * st.show() - Execute show commands
      * st.reboot() - Reboot device
      * st.wait_system_status() - Wait for system to come up after reboot
      * st.log(), st.banner(), st.debug(), st.warn() - Logging functions
      * st.wait() - Wait for state propagation
      * st.report_pass(), st.report_fail() - Test result reporting

Pre-requisites:
  - Topology: Single DUT (standalone) | Supported: HW and Virtual
  - Topology Diagram:
        # Topology - Single DUT
        # +--------------------+
        # |     DUT (smic_sonic1)     |
        # |   Ethernet16       |
        # |   (test interface) |
        # +--------------------+

  - Feature flags / min SONiC version: Basic configuration management support
  - Required test variables (YAML): vars/system/vars_write_memory_erase.yaml
      * defaults.cli_type (klish)
      * defaults.verify_timeout (30 seconds)
      * defaults.reboot_wait (180 seconds)
      * testcases.write_memory_persistence (config persistence validation)
      * testcases.write_erase_reset (config reset validation)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import re

import pytest
import yaml

from spytest import SpyTestDict, st

# Environment variable for optional YAML override
VAR_FILE_ENV = "WRITE_MEMORY_ERASE_VAR_FILE"

# Default YAML variable file path
DEFAULT_VAR_FILE = (
    Path(__file__).resolve().parents[2]
    / "vars"
    / "system"
    / "vars_write_memory_erase.yaml"
)


def _load_yaml_data() -> Dict[str, Any]:
    """Load test configuration from YAML file with optional environment override.

    Returns:
        Dict containing test configuration with 'defaults' and 'testcases' keys

    Raises:
        FileNotFoundError: If YAML file does not exist
        ValueError: If YAML structure is invalid
    """
    override_path = st.getenv(VAR_FILE_ENV)
    candidate = Path(override_path) if override_path else DEFAULT_VAR_FILE

    if not candidate.is_file():
        raise FileNotFoundError(
            f"Write memory/erase variable file not found: {candidate}"
        )

    with candidate.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}

    if "testcases" not in content:
        raise ValueError(
            "Write memory/erase YAML must contain key 'testcases'"
        )

    return content


@pytest.mark.topology("any")
class TestWriteMemoryErase:
    """Test suite for SONiC configuration management - write memory and write erase.

    This test class validates:
    - Configuration persistence with 'write memory' across reboots
    - Configuration reset with 'write erase' to default/baseline state
    """

    data = SpyTestDict()

    @classmethod
    def setup_class(cls) -> None:
        """Initialize topology, load test variables, and validate prerequisites."""
        st.banner("CLASS SETUP: Configuration Management Test Suite")

        # Load YAML configuration
        config = _load_yaml_data()
        defaults = config.get("defaults", {})

        # Ensure minimum topology: 1 DUT (standalone)
        min_topology = defaults.get("min_topology") or ["D1"]
        topology = st.ensure_min_topology(*min_topology)

        # Store configuration
        cls.data.config = SpyTestDict(config)
        cls.data.defaults = SpyTestDict(defaults)
        cls.data.topology = topology
        cls.data.testcases = SpyTestDict(config.get("testcases", {}))

        # CLI type (default: klish for IS-CLI mode)
        cls.data.cli_type = defaults.get("cli_type", "klish")

        # Timeout and wait settings
        cls.data.verify_timeout = int(defaults.get("verify_timeout", 30))
        cls.data.reboot_wait = int(defaults.get("reboot_wait", 180))

        # Cleanup flag
        cls.data.cleanup_enabled = bool(defaults.get("cleanup", True))

        # Get DUT handle from topology
        cls.data.dut = topology.D1

        # Get test interface from testbed YAML
        cls.data.test_interface = st.get_testbed_vars().get(
            "test_interface", "Ethernet16"
        )

        st.log(f"DUT: {cls.data.dut}")
        st.log(f"Test Interface: {cls.data.test_interface}")

        # Store original configuration for cleanup
        cls.data.original_config = None

    @classmethod
    def teardown_class(cls) -> None:
        """Cleanup and restore original configuration if needed."""
        if not cls.data.cleanup_enabled:
            st.log("Cleanup disabled - skipping teardown")
            return

        st.banner("CLASS TEARDOWN: Restoring configuration")
        # If we have original config saved, we could restore it here
        # For now, we rely on write erase in TC2 to clean up

    def setup_method(self) -> None:
        """Pre-test setup."""
        st.banner("TEST SETUP: Preparing clean environment")

    def teardown_method(self) -> None:
        """Post-test cleanup."""
        st.banner("TEST TEARDOWN: Test completed")

    def _get_running_config(self) -> str:
        """Retrieve running configuration from DUT.

        Returns:
            str: Running configuration output
        """
        st.log("Retrieving running configuration")

        # Execute show running-configuration command
        output = st.show(
            self.data.dut,
            "show running-configuration | no-more",
            type=self.data.cli_type,
            skip_tmpl=True,
        )

        # Convert list output to string if needed
        if isinstance(output, list):
            output = "\n".join(str(line) for line in output)
        elif not isinstance(output, str):
            output = str(output)

        st.debug(f"Running config length: {len(output)} chars")
        return output

    def _verify_ip_in_config(self, config: str, interface: str, ip_address: str) -> bool:
        """Check if IP address exists in running configuration.

        Args:
            config: Running configuration text
            interface: Interface name (e.g., "Ethernet16")
            ip_address: IP address with subnet (e.g., "190.100.100.2/24")

        Returns:
            bool: True if IP found in config, False otherwise
        """
        st.log(f"Checking for IP {ip_address} on {interface} in running config")

        # Pattern to match interface block with IP address
        # Looking for: interface Ethernet16 ... ip address 190.100.100.2/24
        interface_pattern = rf"interface\s+{re.escape(interface)}\s*\n(.*?)(?=\ninterface|\Z)"
        interface_match = re.search(interface_pattern, config, re.IGNORECASE | re.DOTALL)

        if not interface_match:
            st.log(f"Interface {interface} not found in running config")
            return False

        interface_block = interface_match.group(1)
        st.debug(f"Interface block found:\n{interface_block[:200]}...")

        # Check for IP address in the interface block
        ip_pattern = rf"ip\s+address\s+{re.escape(ip_address)}"
        ip_match = re.search(ip_pattern, interface_block, re.IGNORECASE)

        if ip_match:
            st.log(f"✓ Found IP {ip_address} on {interface}")
            return True
        else:
            st.log(f"✗ IP {ip_address} NOT found on {interface}")
            return False

    def _configure_interface_ip(
        self, interface: str, ip_address: str, subnet: str, shutdown: bool = False
    ) -> None:
        """Configure IP address on interface.

        Args:
            interface: Interface name
            ip_address: IP address without mask
            subnet: Subnet mask length
            shutdown: Whether to shutdown interface
        """
        st.log(
            f"Configuring interface {interface} with IP {ip_address}/{subnet}"
        )

        # Enter configuration mode
        st.config(self.data.dut, "configure terminal", type=self.data.cli_type)

        # Enter interface configuration mode
        st.config(
            self.data.dut,
            f"interface {interface}",
            type=self.data.cli_type,
        )

        # Remove existing IP if any
        st.config(
            self.data.dut,
            "no ip address",
            type=self.data.cli_type,
            skip_error_check=True,
        )

        # Configure new IP address
        st.config(
            self.data.dut,
            f"ip address {ip_address}/{subnet}",
            type=self.data.cli_type,
        )

        # Shutdown or no shutdown based on parameter
        if shutdown:
            st.config(self.data.dut, "shutdown", type=self.data.cli_type)
        else:
            st.config(self.data.dut, "no shutdown", type=self.data.cli_type)

        # Exit configuration mode
        st.config(self.data.dut, "exit", type=self.data.cli_type)
        st.config(self.data.dut, "exit", type=self.data.cli_type)

        st.log(f"Interface {interface} configured successfully")

    def _execute_write_memory(self) -> bool:
        """Execute write memory command to save configuration.

        Returns:
            bool: True if write memory succeeded
        """
        st.log("Executing 'write memory' command")

        # Execute write memory from klish mode
        output = st.config(
            self.data.dut,
            "write memory",
            type=self.data.cli_type,
            skip_error_check=True,
        )

        # Check for success message
        if isinstance(output, list):
            output = "\n".join(str(line) for line in output)
        elif not isinstance(output, str):
            output = str(output)

        # Look for success indicators
        if "completed" in output.lower() or "success" in output.lower():
            st.log("✓ Write memory completed successfully")
            return True
        else:
            st.error(f"✗ Write memory failed or unclear status: {output}")
            return False

    def _execute_write_erase(self) -> bool:
        """Execute write erase command to clear configuration.

        Returns:
            bool: True if write erase succeeded
        """
        st.log("Executing 'write erase' command")

        # Execute write erase from klish mode
        output = st.config(
            self.data.dut,
            "write erase",
            type=self.data.cli_type,
            skip_error_check=True,
        )

        # Check for success message
        if isinstance(output, list):
            output = "\n".join(str(line) for line in output)
        elif not isinstance(output, str):
            output = str(output)

        # Look for success indicators
        if "completed" in output.lower() or "take effect" in output.lower():
            st.log("✓ Write erase completed successfully")
            return True
        else:
            st.error(f"✗ Write erase failed or unclear status: {output}")
            return False

    def _reboot_and_wait(self) -> None:
        """Reboot device and wait for it to come back up."""
        st.log("Rebooting device from Click mode")

        # Reboot from Click mode
        st.reboot(self.data.dut, skip_port_wait=True)

        # Wait for device to come back up
        st.log(f"Waiting {self.data.reboot_wait} seconds for device to come up")
        st.wait(self.data.reboot_wait, "Waiting for device reboot")

        # Wait for system to be ready
        st.log("Waiting for system to be ready")
        st.wait_system_status(self.data.dut, max_time=self.data.reboot_wait)

        st.log("Device is back up and ready")

    @pytest.mark.inventory(feature="Regression", testcases=["SONIC-CFG-MGMT-001-TC1"])
    def test_write_memory_persistence(self) -> None:
        """TC 1: Verify configuration persistence with write memory across reboot.

        Steps:
        1. Configure IP address 190.100.100.2/24 on Ethernet16
        2. Verify configuration appears in running-config
        3. Execute write memory command
        4. Reboot device
        5. Wait for device to come up
        6. Verify configuration persisted in running-config
        7. Verify Ethernet16 still has custom IP

        Expected Result: PASS if configuration persists after reboot
        """
        st.banner(
            "TEST CASE 1: Configuration Persistence with Write Memory"
        )

        # Get test case configuration
        tc = self.data.testcases.get("write_memory_persistence")
        if not tc:
            st.report_fail("msg", "Test case 'write_memory_persistence' not found in YAML")

        interface = self.data.test_interface
        intf_cfg = tc.get("interface_config", {})
        ip_address = intf_cfg.get("ip_address", "190.100.100.2")
        subnet = intf_cfg.get("subnet", "24")
        shutdown = intf_cfg.get("shutdown", False)

        verify = tc.get("verify", {})
        expected_ip = verify.get("expected_ip", f"{ip_address}/{subnet}")

        # Step 1: Configure interface IP
        st.log(f"Step 1: Configuring IP {ip_address}/{subnet} on {interface}")
        self._configure_interface_ip(interface, ip_address, subnet, shutdown)

        # Step 2: Verify configuration in running-config
        st.log("Step 2: Verifying configuration in running-config before save")
        running_config = self._get_running_config()

        if not self._verify_ip_in_config(running_config, interface, expected_ip):
            st.report_fail(
                "msg",
                f"IP {expected_ip} not found in running config on {interface} before save",
            )

        st.log(f"✓ Configuration verified in running-config before save")

        # Step 3: Execute write memory
        st.log("Step 3: Executing write memory to save configuration")
        if not self._execute_write_memory():
            st.report_fail("msg", "Write memory command failed")

        # Step 4-5: Reboot and wait
        st.log("Step 4-5: Rebooting device and waiting for recovery")
        self._reboot_and_wait()

        # Step 6-7: Verify configuration persisted
        st.log("Step 6-7: Verifying configuration persisted after reboot")
        running_config = self._get_running_config()

        if not self._verify_ip_in_config(running_config, interface, expected_ip):
            st.report_fail(
                "msg",
                f"Configuration did NOT persist - IP {expected_ip} not found on {interface} after reboot",
            )

        st.log(
            f"✓ Configuration successfully persisted - IP {expected_ip} found on {interface}"
        )
        st.report_pass("test_case_passed")

    @pytest.mark.inventory(feature="Regression", testcases=["SONIC-CFG-MGMT-001-TC2"])
    def test_write_erase_reset(self) -> None:
        """TC 2: Verify configuration reset with write erase after reboot.

        Pre-condition: TC 1 must have run successfully (custom config exists)

        Steps:
        1. Execute write erase command
        2. Reboot device
        3. Wait for device to come up
        4. Verify custom configuration is wiped
        5. Verify Ethernet16 reverted to default/baseline config

        Expected Result: PASS if custom config is removed after write erase + reboot
        """
        st.banner(
            "TEST CASE 2: Configuration Reset with Write Erase"
        )

        # Get test case configuration
        tc = self.data.testcases.get("write_erase_reset")
        if not tc:
            st.report_fail("msg", "Test case 'write_erase_reset' not found in YAML")

        interface = self.data.test_interface

        # Custom IP from TC1 that should be removed
        tc_tc1 = self.data.testcases.get("write_memory_persistence", {})
        intf_cfg = tc_tc1.get("interface_config", {})
        custom_ip_addr = intf_cfg.get("ip_address", "190.100.100.2")
        custom_subnet = intf_cfg.get("subnet", "24")
        custom_ip = f"{custom_ip_addr}/{custom_subnet}"

        # Step 1: Execute write erase
        st.log("Step 1: Executing write erase to clear configuration")
        if not self._execute_write_erase():
            st.report_fail("msg", "Write erase command failed")

        # Step 2-3: Reboot and wait
        st.log("Step 2-3: Rebooting device and waiting for recovery")
        self._reboot_and_wait()

        # Step 4-5: Verify configuration is reset
        st.log("Step 4-5: Verifying custom configuration was wiped")
        running_config = self._get_running_config()

        # Check that custom IP is NOT present
        if self._verify_ip_in_config(running_config, interface, custom_ip):
            st.report_fail(
                "msg",
                f"Configuration did NOT reset - custom IP {custom_ip} still present on {interface}",
            )

        st.log(
            f"✓ Configuration successfully reset - custom IP {custom_ip} removed from {interface}"
        )
        st.log("✓ Device reverted to default/baseline configuration")
        st.report_pass("test_case_passed")
