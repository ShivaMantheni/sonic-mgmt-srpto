#!/usr/bin/env python3
"""
Feature-wise Log Consolidation Script

This script consolidates scattered test execution logs by feature.
Multiple batch executions for the same feature (e.g., BGP tests from different
paths/yamls) are grouped together.

Usage:
    python3 consolidate_feature_logs.py --log-root logs/20260604 --consolidate
    python3 consolidate_feature_logs.py --log-root logs/20260604 --dry-run

Output Structure:
    logs/20260604/
    ├── BGP/
    │   ├── BGP_NEG_FLAP_RR__123456/
    │   ├── BGP_IPV4_FEATURES__234567/
    │   ├── consolidated_functions.csv
    │   └── BGP_summary.json
    ├── OSPF/
    │   ├── OSPF_ISCLI_MASTER__123456/
    │   ├── consolidated_functions.csv
    │   └── OSPF_summary.json
    └── dashboard/
        └── feature_consolidated_dashboard.html
"""

import os
import sys
import csv
import json
import yaml
import shutil
import argparse
import glob
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Script directory
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]  # Go up to spytest/
FEATURE_MAPPING_FILE = PROJECT_ROOT / "feature_mapping.yaml"


class FeatureConsolidator:
    """Consolidates test logs by feature"""

    def __init__(self, log_root, dry_run=False, min_timestamp=None):
        self.log_root = Path(log_root)
        self.dry_run = dry_run
        self.min_timestamp = min_timestamp  # Epoch timestamp (seconds since 1970)
        self.feature_mapping = self.load_feature_mapping()
        self.batch_to_feature = self.create_batch_to_feature_map()

    def load_feature_mapping(self):
        """Load feature mapping from YAML file"""
        if not FEATURE_MAPPING_FILE.exists():
            print(f"Error: Feature mapping file not found: {FEATURE_MAPPING_FILE}")
            sys.exit(1)

        with open(FEATURE_MAPPING_FILE, 'r') as f:
            return yaml.safe_load(f)

    def create_batch_to_feature_map(self):
        """Create a reverse mapping: batch_name -> feature"""
        batch_map = {}

        for feature, config in self.feature_mapping.get('features', {}).items():
            for batch in config.get('batches', []):
                batch_map[batch] = feature

        return batch_map

    def get_feature_for_batch(self, batch_name):
        """
        Determine feature for a batch name
        Returns feature name or 'UNCATEGORIZED' if not found
        """
        # Direct mapping
        if batch_name in self.batch_to_feature:
            return self.batch_to_feature[batch_name]

        # Try pattern matching
        patterns = self.feature_mapping.get('auto_mapping_patterns', {})
        batch_upper = batch_name.upper()

        for feature, keywords in patterns.items():
            for keyword in keywords:
                if keyword in batch_upper:
                    return feature

        return 'UNCATEGORIZED'

    def scan_batch_directories(self):
        """
        Scan log root for batch directories
        Returns dict: {feature: [(batch_name, batch_path), ...]}
        """
        feature_batches = defaultdict(list)
        skipped_old = []

        if not self.log_root.exists():
            print(f"Error: Log root does not exist: {self.log_root}")
            return feature_batches

        # Find all directories that might be batch directories
        for item in self.log_root.iterdir():
            if not item.is_dir():
                continue

            # Skip dashboard and other utility directories
            if item.name in ['dashboard', 'consolidated', 'reports']:
                continue

            # Skip if older than min_timestamp (if specified)
            if self.min_timestamp:
                dir_mtime = item.stat().st_mtime
                if dir_mtime < self.min_timestamp:
                    skipped_old.append((item.name, dir_mtime))
                    continue

            batch_name = item.name
            feature = self.get_feature_for_batch(batch_name)
            feature_batches[feature].append((batch_name, item))

        # Report skipped directories
        if skipped_old and self.min_timestamp:
            print(f"\n⏭️  Skipped {len(skipped_old)} old batch directories:")
            min_time_str = datetime.fromtimestamp(self.min_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            print(f"   (modified before: {min_time_str})")
            for name, mtime in skipped_old:
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"     ⊘ {name} (modified: {mtime_str})")
            print()

        return feature_batches

    def find_functions_csv(self, batch_path):
        """Find all results_*_functions.csv files in batch directory"""
        pattern = str(batch_path / "**" / "results_*_functions.csv")
        return glob.glob(pattern, recursive=True)

    def consolidate_feature(self, feature, batches):
        """
        Consolidate all batches for a feature

        Args:
            feature: Feature name (e.g., 'BGP')
            batches: List of (batch_name, batch_path) tuples

        Returns:
            Number of test cases consolidated
        """
        feature_dir = self.log_root / feature

        if self.dry_run:
            print(f"\n[DRY-RUN] Would create feature directory: {feature_dir}")
            print(f"[DRY-RUN] Would consolidate {len(batches)} batches for {feature}")
            return 0

        # Create feature directory
        feature_dir.mkdir(parents=True, exist_ok=True)

        # Move/copy batch directories under feature
        all_test_cases = []
        moved_batches = []

        for batch_name, batch_path in batches:
            # Create unique name with timestamp from original path
            timestamp = batch_path.name if batch_path.name.isdigit() else "unknown"
            new_batch_name = f"{batch_name}__{timestamp}"
            new_batch_path = feature_dir / new_batch_name

            # Check if already moved
            if new_batch_path.exists():
                print(f"  ⚠️  Batch already exists: {new_batch_name}")
                batch_dir_to_scan = new_batch_path
            elif batch_path.parent == feature_dir:
                # Already in feature directory (might be from previous run)
                print(f"  ✓ Batch already in feature directory: {batch_name}")
                batch_dir_to_scan = batch_path
            else:
                # Move the batch directory
                try:
                    shutil.move(str(batch_path), str(new_batch_path))
                    print(f"  ✓ Moved: {batch_name} -> {feature}/{new_batch_name}")
                    batch_dir_to_scan = new_batch_path
                except Exception as e:
                    print(f"  ✗ Error moving {batch_name}: {e}")
                    continue

            moved_batches.append(new_batch_name)

            # Find and parse functions.csv files
            csv_files = self.find_functions_csv(batch_dir_to_scan)
            for csv_file in csv_files:
                test_cases = self.parse_functions_csv(csv_file, batch_name)
                all_test_cases.extend(test_cases)

        # Write consolidated CSV
        if all_test_cases:
            consolidated_csv = feature_dir / "consolidated_functions.csv"
            self.write_consolidated_csv(consolidated_csv, all_test_cases)
            print(f"  ✓ Created consolidated CSV: {consolidated_csv.name}")
            print(f"  📊 Total test cases: {len(all_test_cases)}")

            # Generate JSON summary
            json_file = feature_dir / f"{feature}_summary.json"
            self.generate_feature_json(feature, all_test_cases, json_file)
            print(f"  ✓ Created JSON summary: {json_file.name}")

        return len(all_test_cases)

    def parse_functions_csv(self, csv_file, batch_name):
        """Parse results_*_functions.csv file"""
        test_cases = []

        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    result = row.get('Result', '').strip()
                    # Skip rows without results (module prologue/epilogue)
                    if not result:
                        continue

                    test_case = {
                        'batch': batch_name,
                        'module': row.get('Module', '').strip(),
                        'test_function': row.get('TestFunction', '').strip(),
                        'result': result,
                        'time_taken': row.get('TimeTaken', '').strip(),
                        'executed_on': row.get('ExecutedOn', '').strip(),
                        'description': row.get('Description', '').strip(),
                        'devices': row.get('Devices', '').strip(),
                        'doc': row.get('Doc', '').strip()
                    }
                    test_cases.append(test_case)
        except Exception as e:
            print(f"  ⚠️  Error parsing {csv_file}: {e}")

        return test_cases

    def write_consolidated_csv(self, output_file, test_cases):
        """Write consolidated test cases to CSV"""
        if not test_cases:
            return

        fieldnames = ['batch', 'module', 'test_function', 'result', 'time_taken',
                     'executed_on', 'description', 'devices', 'doc']

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_cases)

    def extract_testcase_id(self, test_function, doc):
        """Extract test case ID from test function name or doc"""
        # Try to find TC_XXX_YYY_ZZZ pattern in doc
        if doc:
            tc_match = re.search(r'TC[_-][A-Z0-9]+[_-]\d+[_-]\d+', doc, re.IGNORECASE)
            if tc_match:
                return tc_match.group(0).upper()

        # Fallback: generate from test function name
        # test_bfd_001_single_hop_peer_ipv4 -> TC_BFD_001
        parts = test_function.split('_')
        if len(parts) >= 3:
            # Try to find test_<feature>_<number>_<name> pattern
            for i, part in enumerate(parts):
                if part.isdigit() and i > 0:
                    feature = parts[i-1].upper()
                    number = part
                    return f"TC_{feature}_{number}"

        # Last resort: use test function name
        return test_function

    def extract_test_name(self, test_function):
        """Extract readable test name from test function"""
        # Remove class prefix if present: TestBgpIpv4Basic.test_name -> test_name
        if '.' in test_function:
            test_function = test_function.split('.')[-1]

        # Remove 'test_' prefix
        if test_function.startswith('test_'):
            test_function = test_function[5:]

        # Convert underscores to spaces and capitalize
        return ' '.join(word.capitalize() for word in test_function.split('_'))

    def parse_time_duration(self, time_str):
        """Parse time string to seconds (float)"""
        if not time_str:
            return 0.0

        try:
            # Handle formats like "0:01:23" or "1:23" or "45.5"
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 3:  # H:M:S
                    h, m, s = parts
                    return float(h) * 3600 + float(m) * 60 + float(s)
                elif len(parts) == 2:  # M:S
                    m, s = parts
                    return float(m) * 60 + float(s)
            else:
                # Direct seconds
                return float(time_str)
        except (ValueError, AttributeError):
            return 0.0

    def generate_feature_json(self, feature, test_cases, output_file):
        """Generate JSON summary for feature from test cases"""
        if not test_cases:
            return

        # Get current timestamp
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # Use lowercase feature name as module_name
        module_name = feature.lower()

        # Calculate summary statistics
        total_tests = len(test_cases)
        passed = sum(1 for tc in test_cases if tc['result'].lower() in ['pass', 'passed'])
        failed = sum(1 for tc in test_cases if tc['result'].lower() in ['fail', 'failed'])
        skipped = sum(1 for tc in test_cases if tc['result'].lower() in ['skip', 'skipped'])

        # Calculate total duration
        total_duration = sum(self.parse_time_duration(tc['time_taken']) for tc in test_cases)

        # Calculate pass rate
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0.0

        # Build test data array
        test_data = []
        for idx, tc in enumerate(test_cases, start=1):
            # Extract test case ID
            tc_id = self.extract_testcase_id(tc['test_function'], tc.get('doc', ''))

            # Extract test name
            test_name = self.extract_test_name(tc['test_function'])

            # Build nodeid (module + test_function)
            nodeid = f"{tc['module']}::{tc['test_function']}"

            # Get description (prefer description field, fallback to first line of doc)
            description = tc.get('description', '')
            if not description and tc.get('doc'):
                # Get first line of doc
                description = tc['doc'].split('\n')[0].strip()

            # Parse duration to float
            duration = self.parse_time_duration(tc['time_taken'])

            test_entry = {
                "serial_no": idx,
                "tc_id": tc_id,
                "test_name": test_name,
                "description": description,
                "nodeid": nodeid,
                "result": tc['result'].lower(),
                "duration": round(duration, 1)
            }
            test_data.append(test_entry)

        # Build complete JSON structure
        json_data = {
            "module_name": module_name,
            "date": date_str,
            "time": time_str,
            "timestamp": timestamp_str,
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "total_duration_seconds": round(total_duration, 1),
                "pass_rate_percentage": round(pass_rate, 1)
            },
            "test_data": test_data
        }

        # Write JSON file
        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=4)

        return json_data

    def consolidate_all(self):
        """Consolidate all features in log root"""
        print(f"\n{'='*60}")
        print(f"Feature-wise Log Consolidation")
        print(f"{'='*60}")
        print(f"Log Root: {self.log_root}")
        print(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        print(f"{'='*60}\n")

        feature_batches = self.scan_batch_directories()

        if not feature_batches:
            print("No batch directories found in log root.")
            return

        print(f"Found {len(feature_batches)} features with batches:\n")

        total_tests = 0
        feature_stats = {}

        for feature in sorted(feature_batches.keys()):
            batches = feature_batches[feature]
            display_name = self.feature_mapping.get('features', {}).get(feature, {}).get('display_name', feature)

            print(f"\n🔷 {display_name} ({feature})")
            print(f"   Batches: {len(batches)}")
            for batch_name, batch_path in batches:
                print(f"     • {batch_name}")

            # Consolidate this feature
            test_count = self.consolidate_feature(feature, batches)
            total_tests += test_count
            feature_stats[feature] = {
                'batches': len(batches),
                'tests': test_count
            }

        # Print summary
        print(f"\n{'='*60}")
        print(f"Consolidation Summary")
        print(f"{'='*60}")
        print(f"Total Features: {len(feature_batches)}")
        print(f"Total Test Cases: {total_tests}")
        print(f"{'='*60}\n")

        # Create summary file
        if not self.dry_run:
            self.write_summary(feature_stats)

    def write_summary(self, feature_stats):
        """Write consolidation summary to file"""
        summary_file = self.log_root / "consolidation_summary.txt"

        with open(summary_file, 'w') as f:
            f.write("Feature-wise Log Consolidation Summary\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Log Root: {self.log_root}\n")
            f.write("="*60 + "\n\n")

            for feature in sorted(feature_stats.keys()):
                stats = feature_stats[feature]
                display_name = self.feature_mapping.get('features', {}).get(feature, {}).get('display_name', feature)
                f.write(f"{display_name} ({feature})\n")
                f.write(f"  Batches: {stats['batches']}\n")
                f.write(f"  Tests: {stats['tests']}\n\n")

            total_batches = sum(s['batches'] for s in feature_stats.values())
            total_tests = sum(s['tests'] for s in feature_stats.values())
            f.write(f"\nTotal Features: {len(feature_stats)}\n")
            f.write(f"Total Batches: {total_batches}\n")
            f.write(f"Total Tests: {total_tests}\n")

        print(f"Summary written to: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Consolidate test logs by feature',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Consolidate logs for a specific date
  python3 consolidate_feature_logs.py --log-root logs/20260604 --consolidate

  # Dry-run to see what would be done
  python3 consolidate_feature_logs.py --log-root logs/20260604 --dry-run

  # Consolidate current date
  python3 consolidate_feature_logs.py --log-root logs/$(date +%Y%m%d) --consolidate

  # Consolidate only directories modified after timestamp (prevents old dirs)
  python3 consolidate_feature_logs.py --log-root logs/20260604 --consolidate --min-timestamp 1735744800
        """
    )
    parser.add_argument('--log-root', required=True,
                       help='Root directory containing batch logs (e.g., logs/20260604)')
    parser.add_argument('--consolidate', action='store_true',
                       help='Perform consolidation (default: dry-run)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--min-timestamp', type=float, default=None,
                       help='Only process directories modified after this Unix timestamp (seconds since epoch)')

    args = parser.parse_args()

    # Default to dry-run unless --consolidate is specified
    dry_run = not args.consolidate or args.dry_run

    consolidator = FeatureConsolidator(args.log_root, dry_run=dry_run, min_timestamp=args.min_timestamp)
    consolidator.consolidate_all()


if __name__ == '__main__':
    main()
