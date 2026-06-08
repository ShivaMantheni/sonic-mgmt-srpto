#!/bin/bash

# ==========================================================
# Feature Consolidation Verification Script
# Tests that all components are in place and working
# ==========================================================

echo "=============================================="
echo " Feature Consolidation Setup Verification"
echo "=============================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check file existence
check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        return 0
    else
        echo -e "${RED}✗${NC} $description: $file NOT FOUND"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check directory existence
check_dir() {
    local dir=$1
    local description=$2

    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description: $dir"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $description: $dir (will be created on first run)"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

echo "1. Checking Core Configuration Files"
echo "--------------------------------------"
check_file "feature_mapping.yaml" "Feature mapping configuration"
check_file "dashboard/scripts/consolidate_feature_logs.py" "Consolidation script"
check_file "batch_full_run_qa.sh" "Batch execution script"
echo ""

echo "2. Checking Dashboard Scripts"
echo "--------------------------------------"
check_file "dashboard/scripts/generate_graphical_dashboard.py" "Dashboard generation script"
echo ""

echo "3. Checking Log Directory Structure"
echo "--------------------------------------"
check_dir "logs" "Base logs directory"
echo ""

echo "4. Testing Feature Mapping Configuration"
echo "--------------------------------------"
python3 -c "
import yaml
import sys

try:
    with open('feature_mapping.yaml', 'r') as f:
        config = yaml.safe_load(f)

    features = config.get('features', {})
    patterns = config.get('auto_mapping_patterns', {})

    print(f'  Features defined: {len(features)}')
    print(f'  Auto-mapping patterns: {len(patterns)}')

    total_batches = sum(len(f.get('batches', [])) for f in features.values())
    print(f'  Total batches mapped: {total_batches}')

    print('')
    print('  Top 5 features by batch count:')
    sorted_features = sorted(features.items(),
                            key=lambda x: len(x[1].get('batches', [])),
                            reverse=True)
    for name, config in sorted_features[:5]:
        batch_count = len(config.get('batches', []))
        display_name = config.get('display_name', name)
        print(f'    - {display_name}: {batch_count} batches')

    sys.exit(0)
except Exception as e:
    print(f'  Error reading feature_mapping.yaml: {e}', file=sys.stderr)
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Feature mapping configuration is valid"
else
    echo -e "${RED}✗${NC} Feature mapping configuration has errors"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "5. Testing Consolidation Script Syntax"
echo "--------------------------------------"
python3 -m py_compile dashboard/scripts/consolidate_feature_logs.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Consolidation script syntax is valid"
else
    echo -e "${RED}✗${NC} Consolidation script has syntax errors"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "6. Testing Consolidation Script Help"
echo "--------------------------------------"
python3 dashboard/scripts/consolidate_feature_logs.py --help > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Consolidation script is executable"
    echo ""
    echo "  Usage examples:"
    echo "    python3 dashboard/scripts/consolidate_feature_logs.py --log-root logs/20260604 --dry-run"
    echo "    python3 dashboard/scripts/consolidate_feature_logs.py --log-root logs/20260604 --consolidate"
else
    echo -e "${RED}✗${NC} Consolidation script cannot be executed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "7. Checking for Existing Log Directories"
echo "--------------------------------------"
if [ -d "logs" ]; then
    LOG_DIRS=$(find logs -maxdepth 1 -type d -name "202*" 2>/dev/null | wc -l)
    if [ $LOG_DIRS -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Found $LOG_DIRS date-based log directories"
        echo ""
        echo "  You can test consolidation on existing logs:"
        LATEST_LOG=$(find logs -maxdepth 1 -type d -name "202*" 2>/dev/null | sort -r | head -1)
        if [ -n "$LATEST_LOG" ]; then
            echo "    python3 dashboard/scripts/consolidate_feature_logs.py --log-root $LATEST_LOG --dry-run"
        fi
    else
        echo -e "${YELLOW}⚠${NC} No existing log directories found"
        echo "  Logs will be created when you run batch_full_run_qa.sh"
    fi
else
    echo -e "${YELLOW}⚠${NC} Logs directory doesn't exist yet"
    echo "  It will be created automatically on first run"
fi
echo ""

echo "=============================================="
echo " Verification Summary"
echo "=============================================="
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your feature consolidation setup is ready to use."
    echo ""
    echo "Next steps:"
    echo "  1. Run batch_full_run_qa.sh to execute tests"
    echo "  2. Logs will automatically be consolidated by feature"
    echo "  3. Dashboard will be generated from consolidated logs"
    echo ""
    echo "To test with existing logs (dry-run):"
    if [ -d "logs" ] && [ $(find logs -maxdepth 1 -type d -name "202*" 2>/dev/null | wc -l) -gt 0 ]; then
        LATEST_LOG=$(find logs -maxdepth 1 -type d -name "202*" 2>/dev/null | sort -r | head -1)
        echo "  python3 dashboard/scripts/consolidate_feature_logs.py --log-root $LATEST_LOG --dry-run"
    else
        echo "  python3 dashboard/scripts/consolidate_feature_logs.py --log-root logs/YYYYMMDD --dry-run"
    fi
    EXIT_CODE=0
else
    echo -e "${RED}✗ Found $ERRORS error(s)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ Found $WARNINGS warning(s)${NC}"
    fi
    echo ""
    echo "Please fix the errors above before proceeding."
    EXIT_CODE=1
fi

echo ""
echo "=============================================="

exit $EXIT_CODE
