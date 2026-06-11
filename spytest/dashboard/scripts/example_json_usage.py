#!/usr/bin/env python3
"""
Example: Using Feature JSON Summaries

Demonstrates how to read and analyze the JSON summary files
generated for each feature after consolidation.

Usage:
    python3 example_json_usage.py logs/20260604
"""

import sys
import json
from pathlib import Path


def load_feature_summary(json_file):
    """Load a feature summary JSON file"""
    with open(json_file, 'r') as f:
        return json.load(f)


def print_feature_health(summary):
    """Print a quick health summary for a feature"""
    # Capitalize module name for display
    module_display = summary['module_name'].upper()

    print(f"\n{'='*60}")
    print(f"Feature: {module_display}")
    print(f"{'='*60}")
    print(f"Execution: {summary['timestamp']}")
    print(f"\nTest Summary:")
    print(f"  Total Tests    : {summary['summary']['total_tests']}")
    print(f"  ✓ Passed       : {summary['summary']['passed']}")
    print(f"  ✗ Failed       : {summary['summary']['failed']}")
    print(f"  ⊘ Skipped      : {summary['summary']['skipped']}")
    print(f"  Pass Rate      : {summary['summary']['pass_rate_percentage']}%")
    print(f"  Total Duration : {summary['summary']['total_duration_seconds']}s")


def list_failed_tests(summary):
    """List all failed tests for a feature"""
    failed_tests = [
        tc for tc in summary['test_data']
        if tc['result'] == 'fail' or tc['result'] == 'failed'
    ]

    if failed_tests:
        print(f"\n  Failed Tests ({len(failed_tests)}):")
        for tc in failed_tests:
            print(f"    • {tc['tc_id']}: {tc['test_name']}")
            print(f"      {tc['description']}")
            print(f"      Duration: {tc['duration']}s")
    else:
        print("\n  ✓ No failed tests!")


def compare_features(log_root):
    """Compare health across all features"""
    log_root = Path(log_root)

    # Find all JSON summary files
    json_files = list(log_root.glob("*/*_summary.json"))

    if not json_files:
        print(f"No JSON summary files found in {log_root}")
        return

    print(f"\n{'='*80}")
    print(f"Feature Health Comparison - {log_root.name}")
    print(f"{'='*80}")
    print(f"\n{'Feature':<30} {'Total':<8} {'Passed':<8} {'Failed':<8} {'Pass Rate':<10}")
    print(f"{'-'*80}")

    # Load and display each feature
    features = []
    for json_file in sorted(json_files):
        summary = load_feature_summary(json_file)
        features.append(summary)

        stats = summary['summary']
        # Display module name in uppercase, truncate if too long
        feature_name = summary['module_name'].upper()[:28]

        print(f"{feature_name:<30} "
              f"{stats['total_tests']:<8} "
              f"{stats['passed']:<8} "
              f"{stats['failed']:<8} "
              f"{stats['pass_rate_percentage']:<10.1f}%")

    # Overall statistics
    total_tests = sum(f['summary']['total_tests'] for f in features)
    total_passed = sum(f['summary']['passed'] for f in features)
    total_failed = sum(f['summary']['failed'] for f in features)
    overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"{'-'*80}")
    print(f"{'OVERALL':<30} "
          f"{total_tests:<8} "
          f"{total_passed:<8} "
          f"{total_failed:<8} "
          f"{overall_pass_rate:<10.1f}%")
    print(f"{'='*80}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 example_json_usage.py <log-root>")
        print("Example: python3 example_json_usage.py logs/20260604")
        sys.exit(1)

    log_root = Path(sys.argv[1])

    if not log_root.exists():
        print(f"Error: Log root does not exist: {log_root}")
        sys.exit(1)

    # Example 1: Compare all features
    compare_features(log_root)

    # Example 2: Detailed view of each feature
    json_files = list(log_root.glob("*/*_summary.json"))

    print("\nDetailed Feature Analysis:")
    print("="*80)

    for json_file in sorted(json_files):
        summary = load_feature_summary(json_file)
        print_feature_health(summary)
        list_failed_tests(summary)

    # Example 3: Generate simple health badges
    print("\n\nFeature Health Badges:")
    print("="*80)
    for json_file in sorted(json_files):
        summary = load_feature_summary(json_file)
        pass_rate = summary['summary']['pass_rate_percentage']

        # Determine badge color
        if pass_rate >= 90:
            badge = "🟢 EXCELLENT"
        elif pass_rate >= 75:
            badge = "🟡 GOOD"
        elif pass_rate >= 50:
            badge = "🟠 NEEDS ATTENTION"
        else:
            badge = "🔴 CRITICAL"

        # Display module name in uppercase
        module_display = summary['module_name'].upper()
        print(f"  {badge:20} {module_display}: {pass_rate}%")

    print("\n")


if __name__ == '__main__':
    main()
