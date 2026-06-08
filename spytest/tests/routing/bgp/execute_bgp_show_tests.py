#!/usr/bin/env python3
"""
BGP Show Commands Manual Test Executor
Executes all 91 test cases from TC_BGP_SHOW_COMMANDS_COMPREHENSIVE.md
and logs results to bgp_show_commands_log.md
"""

import subprocess
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Device connection details
D1_IP = "192.168.100.39"
D2_IP = "192.168.100.40"
PASSWORD = "root@123"
USERNAME = "admin"

LOG_FILE = "tests/routing/bgp/report/bgp_show_commands_log.md"

class BGPShowTester:
    def __init__(self):
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.skip_count = 0
        self.results = []

    def ssh_command(self, device_ip: str, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Execute SSH command on device"""
        ssh_cmd = f'timeout {timeout} sshpass -p "{PASSWORD}" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {USERNAME}@{device_ip} "{command}"'
        try:
            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout+5)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def vtysh_command(self, device_ip: str, vtysh_cmd: str) -> Tuple[int, str, str]:
        """Execute vtysh command"""
        command = f"sudo vtysh -c '{vtysh_cmd}'"
        return self.ssh_command(device_ip, command)

    def append_to_log(self, content: str):
        """Append content to log file"""
        with open(LOG_FILE, 'a') as f:
            f.write(content + "\n")

    def log_test_start(self, tc_id: str, title: str, description: str):
        """Log test case start"""
        content = f"""
---

### {tc_id}: {title}

**Description**: {description}
**Test Start**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        self.append_to_log(content)

    def log_test_result(self, tc_id: str, title: str, command: str, output: str,
                       expected: str, status: str, notes: str = ""):
        """Log detailed test result"""
        self.test_count += 1
        if status == "PASS":
            self.pass_count += 1
        elif status == "FAIL":
            self.fail_count += 1
        else:
            self.skip_count += 1

        # Store for summary
        self.results.append({
            "tc_id": tc_id,
            "title": title,
            "status": status
        })

        content = f"""
**Command Executed:**
```
{command}
```

**Device Output:**
```
{output[:2000]}  # Truncate if too long
{f'... (output truncated, total {len(output)} chars)' if len(output) > 2000 else ''}
```

**Expected Result:**
```
{expected}
```

**Test Status**: **{status}** ✅ {'PASSED' if status == 'PASS' else '❌ FAILED' if status == 'FAIL' else '⏭ SKIPPED'}

{f'**Notes**: {notes}' if notes else ''}

**Test End**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        self.append_to_log(content)

    def update_summary_table(self):
        """Update the summary table in the log file"""
        # Read current log
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()

        # Find summary table section
        summary_start = -1
        summary_end = -1
        for i, line in enumerate(lines):
            if "## Test Summary Table" in line:
                summary_start = i
            if summary_start > 0 and line.startswith("*(Summary will be updated"):
                summary_end = i + 1
                break

        if summary_start > 0 and summary_end > 0:
            # Build new summary table
            table_lines = [
                "\n",
                "| Test ID | Description | Status |\n",
                "|---------|-------------|--------|\n"
            ]

            for result in self.results:
                status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⏭"
                desc = result["title"][:50] + "..." if len(result["title"]) > 50 else result["title"]
                table_lines.append(f"| {result['tc_id']} | {desc} | {status_icon} {result['status']} |\n")

            table_lines.append(f"\n**Progress**: {self.test_count} / 91 tests completed\n")
            table_lines.append(f"**Pass**: {self.pass_count} | **Fail**: {self.fail_count} | **Skip**: {self.skip_count}\n")
            table_lines.append("\n*(Summary updated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ")*\n")

            # Replace summary section
            new_lines = lines[:summary_start+1] + table_lines + lines[summary_end:]

            with open(LOG_FILE, 'w') as f:
                f.writelines(new_lines)

    def test_bgp_summary(self):
        """TC-BGP-SHOW-001: Display global BGP summary"""
        tc_id = "TC-BGP-SHOW-001"
        title = "Display global BGP summary (all address families)"
        desc = "Execute 'show bgp summary' and verify output"

        self.log_test_start(tc_id, title, desc)

        command = "show bgp summary"
        rc, output, err = self.vtysh_command(D1_IP, command)

        expected = "Local AS number, Router ID, Neighbor entries, State/PfxRcd columns"

        # Simple validation
        if rc == 0 and "BGP router identifier" in output and "Neighbor" in output:
            status = "PASS"
            notes = "Command executed successfully, output contains expected fields"
        else:
            status = "FAIL"
            notes = f"Command failed or output missing expected content. RC={rc}, Error={err}"

        self.log_test_result(tc_id, title, command, output, expected, status, notes)
        self.update_summary_table()

    def test_bgp_ipv4_summary(self):
        """TC-BGP-SHOW-002: Display IPv4 unicast BGP summary"""
        tc_id = "TC-BGP-SHOW-002"
        title = "Display IPv4 unicast BGP summary"
        desc = "Execute 'show bgp ipv4 unicast summary' and verify IPv4 neighbors only"

        self.log_test_start(tc_id, title, desc)

        command = "show bgp ipv4 unicast summary"
        rc, output, err = self.vtysh_command(D1_IP, command)

        expected = "IPv4 neighbors only, Neighbor IP, Version, AS, MsgRcvd, MsgSent, State/PfxRcd"

        if rc == 0 and "IPv4 Unicast Summary" in output and "10.0.24.2" in output:
            status = "PASS"
            notes = "IPv4 summary displayed correctly"
        else:
            status = "FAIL"
            notes = f"Failed to display IPv4 summary. RC={rc}"

        self.log_test_result(tc_id, title, command, output, expected, status, notes)
        self.update_summary_table()

    def test_bgp_ipv6_summary(self):
        """TC-BGP-SHOW-003: Display IPv6 unicast BGP summary"""
        tc_id = "TC-BGP-SHOW-003"
        title = "Display IPv6 unicast BGP summary"
        desc = "Execute 'show bgp ipv6 unicast summary'"

        self.log_test_start(tc_id, title, desc)

        command = "show bgp ipv6 unicast summary"
        rc, output, err = self.vtysh_command(D1_IP, command)

        expected = "IPv6 neighbors displayed (if configured)"

        if rc == 0 and ("IPv6 Unicast Summary" in output or "No BGP neighbors" in output):
            # IPv6 may not be configured, which is acceptable
            if "No BGP neighbors" in output or "Total number of neighbors 0" in output:
                status = "PASS"
                notes = "No IPv6 neighbors configured (expected for current setup)"
            else:
                status = "PASS"
                notes = "IPv6 summary displayed"
        else:
            status = "FAIL"
            notes = f"Command failed. RC={rc}"

        self.log_test_result(tc_id, title, command, output, expected, status, notes)
        self.update_summary_table()

    def run_all_tests(self):
        """Execute all test cases"""
        print("=" * 80)
        print("BGP Show Commands - Comprehensive Manual Testing")
        print("=" * 80)
        print(f"Start Time: {datetime.now()}")
        print()

        # Initialize log
        self.append_to_log(f"\n\n## Test Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Run tests (starting with first 3 for demonstration)
        print("Running TC-BGP-SHOW-001...")
        self.test_bgp_summary()
        time.sleep(1)

        print("Running TC-BGP-SHOW-002...")
        self.test_bgp_ipv4_summary()
        time.sleep(1)

        print("Running TC-BGP-SHOW-003...")
        self.test_bgp_ipv6_summary()
        time.sleep(1)

        # Add more tests here...
        # TODO: Add remaining 88 test cases

        print()
        print("=" * 80)
        print("Test Execution Summary")
        print("=" * 80)
        print(f"Total Tests: {self.test_count}")
        print(f"Passed: {self.pass_count}")
        print(f"Failed: {self.fail_count}")
        print(f"Skipped: {self.skip_count}")
        print(f"End Time: {datetime.now()}")
        print(f"\nDetailed log: {LOG_FILE}")
        print("=" * 80)

if __name__ == "__main__":
    tester = BGPShowTester()
    tester.run_all_tests()
