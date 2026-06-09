#!/usr/bin/env python3
"""
Generate a single-module graphical dashboard from a *_summary.json file.

Unlike generate_graphical_dashboard.py -- which derives the feature/module for each
row from the test's path (so a test under system/SM_ISCLI/ is reported as
'SM_ISCLI') -- this script groups EVERY test under the JSON's module_name.

Run against tests/automation/lldp/reports/LLDP_summary.json (module_name "lldp"),
all scripts are reported under a single 'LLDP' module, regardless of where the
individual .py files live (system/lldp/, system/SM_ISCLI/, ...).

Usage:
    python3 generate_dashboard_from_json.py \
        --json reports/LLDP_summary.json \
        --out  reports/lldp_dashboard.html \
        --module-name LLDP \
        --name "LLDP (Link Layer Discovery Protocol)"
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Reuse the shared styling + helpers from the CSV-based dashboard generator.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from generate_graphical_dashboard import HTML_HEAD, HTML_TAIL, format_seconds_to_readable

PASS_RESULTS = {"pass", "passed"}
SKIP_RESULTS = {"skip", "skipped", "not_run", "notrun", "unsupported"}
# Everything else (fail, scripterror, topofail, configfail, envfail, dutfail, ...)
# is treated as a failure for colouring and counting.


def result_class(result):
    """Map a spytest result string to a CSS status class."""
    r = (result or "").strip().lower()
    if r in PASS_RESULTS:
        return "passed"
    if r in SKIP_RESULTS:
        return "skipped"
    return "failed"


def esc(value):
    """Minimal HTML escaping for text rendered into table cells."""
    return (str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def main():
    parser = argparse.ArgumentParser(
        description="Generate a single-module dashboard from a *_summary.json file")
    parser.add_argument("--json", required=True, help="Path to *_summary.json")
    parser.add_argument("--out", required=True, help="Output HTML file path")
    parser.add_argument("--name", help="Dashboard title (default: '<MODULE> Test Summary')")
    parser.add_argument("--module-name",
                        help="Force the module label shown for every row "
                             "(default: JSON module_name, uppercased)")
    args = parser.parse_args()

    with open(args.json, "r") as f:
        data = json.load(f)

    module = (args.module_name or data.get("module_name", "TESTS")).upper()
    title = args.name or f"{module} Test Summary"
    summary = data.get("summary", {})
    test_data = data.get("test_data", [])

    # Prefer the summary block; fall back to recomputing from test_data.
    total = summary.get("total_tests", len(test_data))
    passed = summary.get("passed",
                         sum(1 for t in test_data if result_class(t.get("result")) == "passed"))
    failed = summary.get("failed",
                         sum(1 for t in test_data if result_class(t.get("result")) == "failed"))
    skipped = summary.get("skipped",
                          sum(1 for t in test_data if result_class(t.get("result")) == "skipped"))
    runtime_seconds = int(round(summary.get(
        "total_duration_seconds",
        sum(float(t.get("duration", 0) or 0) for t in test_data))))

    pass_pct = (passed / total * 100) if total else 0
    fail_pct = (failed / total * 100) if total else 0
    skip_pct = (skipped / total * 100) if total else 0

    html = HTML_HEAD.format(batch_name=title)

    # Header
    html += f"""
    <div class="container">
        <div class="header">
            <h1>SONiC Test Dashboard</h1>
            <p>{esc(title)} - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
"""

    # Summary cards
    html += f"""
        <div class="summary-section">
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Total Tests</h3>
                    <div class="value total">{total}</div>
                    <div class="percentage">100%</div>
                </div>
                <div class="summary-card">
                    <h3>Passed</h3>
                    <div class="value passed">{passed}</div>
                    <div class="percentage">{pass_pct:.1f}%</div>
                </div>
                <div class="summary-card">
                    <h3>Failed</h3>
                    <div class="value failed">{failed}</div>
                    <div class="percentage">{fail_pct:.1f}%</div>
                </div>
                <div class="summary-card">
                    <h3>Skipped</h3>
                    <div class="value skipped">{skipped}</div>
                    <div class="percentage">{skip_pct:.1f}%</div>
                </div>
                <div class="summary-card">
                    <h3>Total Runtime</h3>
                    <div class="value runtime">{format_seconds_to_readable(runtime_seconds)}</div>
                    <div class="percentage">Execution Time</div>
                </div>
            </div>
            <div class="overall-progress">
                <h3>Overall Progress</h3>
                <div class="progress-bar">
"""
    if pass_pct > 0:
        html += f'                    <div class="progress-segment progress-pass" style="width: {pass_pct:.2f}%;">{pass_pct:.0f}%</div>\n'
    if fail_pct > 0:
        html += f'                    <div class="progress-segment progress-fail" style="width: {fail_pct:.2f}%;">{fail_pct:.0f}%</div>\n'
    if skip_pct > 0:
        html += f'                    <div class="progress-segment progress-skip" style="width: {skip_pct:.2f}%;">{skip_pct:.0f}%</div>\n'
    html += """
                </div>
            </div>
        </div>
"""

    # Single tab for the whole module
    safe_id = module.replace(" ", "_").replace("/", "_")
    html += f"""
        <div class="tabs">
            <button class="tab-button" onclick="openTab(event, '{safe_id}')">{esc(module)}</button>
        </div>
        <div id="{safe_id}" class="tab-content">
            <div class="module-summary">
                <h2>{esc(module)} - Test Results</h2>
                <div class="module-stats">
                    <span>&#10003; Pass: <strong style="color: #28a745;">{passed}</strong> <span style="font-size: 11px;">({pass_pct:.1f}%)</span></span>
                    <span style="margin: 0 15px;">&#10007; Fail: <strong style="color: #dc3545;">{failed}</strong> <span style="font-size: 11px;">({fail_pct:.1f}%)</span></span>
                    <span>&#8856; Skip: <strong style="color: #ffc107;">{skipped}</strong> <span style="font-size: 11px;">({skip_pct:.1f}%)</span></span>
                    <span style="margin-left: 15px;">Total: <strong>{total}</strong></span>
                </div>
                <div class="progress-bar" style="height: 20px;">
"""
    if pass_pct > 0:
        html += f'                    <div class="progress-segment progress-pass" style="width: {pass_pct:.2f}%; font-size: 10px;">{pass_pct:.0f}%</div>\n'
    if fail_pct > 0:
        html += f'                    <div class="progress-segment progress-fail" style="width: {fail_pct:.2f}%; font-size: 10px;">{fail_pct:.0f}%</div>\n'
    if skip_pct > 0:
        html += f'                    <div class="progress-segment progress-skip" style="width: {skip_pct:.2f}%; font-size: 10px;">{skip_pct:.0f}%</div>\n'
    html += """
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px;">S.No</th>
                        <th style="min-width: 100px;">Module</th>
                        <th style="min-width: 200px;">Script</th>
                        <th style="min-width: 200px;">Testcase_ID</th>
                        <th style="min-width: 300px;">Test_Description</th>
                        <th style="width: 80px;">Time_taken</th>
                        <th style="width: 90px;">Status</th>
                    </tr>
                </thead>
                <tbody>
"""

    for idx, tc in enumerate(test_data, 1):
        nodeid = tc.get("nodeid", "")
        script = nodeid.split("::")[0] if nodeid else ""
        rc = result_class(tc.get("result"))
        status = (tc.get("result", "") or "").upper()
        dur = float(tc.get("duration", 0) or 0)
        time_str = format_seconds_to_readable(int(round(dur))) if dur else "0s"
        tc_id = tc.get("tc_id", "")
        desc = tc.get("description", "") or tc.get("test_name", "")

        html += f"""
                    <tr>
                        <td style="text-align: center; font-size: 11px;">{idx}</td>
                        <td style="font-weight: 600; font-size: 11px; color: #667eea;">{esc(module)}</td>
                        <td class="module-name" style="font-size: 10px; word-break: break-all;">{esc(script)}</td>
                        <td class="testcase-id">{esc(tc_id)}</td>
                        <td style="font-size: 11px; color: #555;">{esc(desc)}</td>
                        <td style="text-align: center; font-size: 11px; font-weight: 500;">{time_str}</td>
                        <td class="result-cell {rc}">{esc(status)}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>
"""

    # Footer
    html += f"""
        <div class="footer">
            Generated by SPyTest JSON Dashboard Generator | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
"""

    # HTML_TAIL uses escaped braces ({{ }}) for the inline JS; .format() collapses
    # them to valid single braces.
    html += HTML_TAIL.format()

    with open(args.out, "w") as f:
        f.write(html)

    print(f"Dashboard generated: {args.out}")
    print(f"Module: {module} | Total: {total}  Pass: {passed}  Fail: {failed}  Skip: {skipped}")


if __name__ == "__main__":
    main()
