# Test Run Directory

This directory contains the test execution batch script and supporting files for the SPyTest test framework.

## Directory Structure

```
test_run/
├── run_testsuite_qa.sh          # Main batch execution script
├── support_files/               # Supporting configuration and test files
│   ├── feature_mapping.yaml     # Maps batches to features for consolidation
│   ├── verify_consolidation_setup.sh  # Verification script for setup
│   ├── test_timestamp_filtering.sh    # Test script for timestamp filtering
│   └── test_timestamp_filtering_v2.sh # Enhanced timestamp filtering test
└── README.md                    # This file
```

## Usage

### Running Tests

From the SPyTest root directory:

```bash
# Run all test batches
./test_run/run_testsuite_qa.sh

# List available batches
./test_run/run_testsuite_qa.sh --list

# Run specific batches (by letter code)
./test_run/run_testsuite_qa.sh --features LLDP

# Run multiple features
./test_run/run_testsuite_qa.sh --features LLDP,VLAN,BGP
```

### Verifying Setup

Before running tests, you can verify the configuration:

```bash
cd test_run
./support_files/verify_consolidation_setup.sh
```

### Testing Timestamp Filtering

To test the timestamp filtering functionality:

```bash
cd test_run
./support_files/test_timestamp_filtering.sh
./support_files/test_timestamp_filtering_v2.sh
```

## Supporting Files

### feature_mapping.yaml

This file maps batch names to feature categories for log consolidation. It defines:
- 19 feature categories (LLDP, VLAN, BGP, OSPF, etc.)
- 110+ batch-to-feature mappings
- Auto-mapping patterns for batch name recognition

**Location**: `test_run/support_files/feature_mapping.yaml`

**Note**: A symlink exists at the spytest root level for backward compatibility.

### verify_consolidation_setup.sh

Verification script that checks:
- Configuration files exist
- Python scripts are valid
- Feature mapping is correct
- Required directories are present

### test_timestamp_filtering.sh

Test script that validates timestamp filtering prevents old batch directories from being consolidated with new test runs.

### test_timestamp_filtering_v2.sh

Enhanced version of the timestamp filtering test with more comprehensive scenarios.

## How It Works

1. **Script Execution**: When you run `run_testsuite_qa.sh`, it:
   - Automatically navigates to the spytest root directory
   - Executes test batches based on your selection
   - Generates logs in `logs/<DATE>/<FEATURE>/`

2. **Feature Consolidation**: After tests complete:
   - Batch logs are consolidated by feature using `feature_mapping.yaml`
   - Consolidated results are placed in `logs/<DATE>/<FEATURE>/`
   - A consolidation summary is generated

3. **Dashboard Generation**: Finally:
   - A graphical dashboard is created showing results by **feature** (not batch)
   - Dashboard shows tabs like "LLDP (Link Layer Discovery Protocol)" instead of individual batch names
   - Saved to `logs/<DATE>/dashboard/`

## Example Workflow

```bash
# From spytest root directory
cd /home/sonic-claude/athira/sonic-mgmt/spytest

# Run LLDP tests
./test_run/run_testsuite_qa.sh --features LLDP

# Results will be in:
# - logs/20260607/LLDP/                    # Consolidated by feature
# - logs/20260607/dashboard/               # Dashboard HTML
# - logs/20260607/consolidation_summary.txt # Summary
```

## Maintenance

### Adding New Batches

To add a new test batch:

1. Edit `run_testsuite_qa.sh` to add the batch function
2. Add the batch name to `BATCH_NAMES` array
3. Update `support_files/feature_mapping.yaml` to map the batch to a feature
4. Update the statistics in the script header

### Modifying Feature Mappings

Edit `support_files/feature_mapping.yaml` to:
- Add new features
- Map batches to different features
- Add auto-mapping patterns

## Troubleshooting

### Script Can't Find Files

If the script can't find supporting files, ensure you're running it from the correct directory:

```bash
cd /home/sonic-claude/athira/sonic-mgmt/spytest
./test_run/run_testsuite_qa.sh --features LLDP
```

### Feature Mapping Not Working

Check that the symlink exists:

```bash
ls -la feature_mapping.yaml
# Should show: feature_mapping.yaml -> test_run/support_files/feature_mapping.yaml
```

If missing, recreate it:

```bash
ln -s test_run/support_files/feature_mapping.yaml feature_mapping.yaml
```

## Documentation

- **Main Documentation**: See `DASHBOARD_FEATURE_CONSOLIDATION_IMPLEMENTATION.md` in spytest root
- **LLDP Fixes**: See `LLDP_EXECUTION_FIXES.md` in spytest root
- **Framework Guide**: See `CLAUDE.md` in spytest root
