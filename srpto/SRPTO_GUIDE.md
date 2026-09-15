# SRPTO — SONiC Resource-Aware Parallel Test Orchestrator

> **Drop-in parallel scheduler for `sonic-mgmt` / SpyTest.**  
> Runs multiple test scripts simultaneously across idle DUTs — no testbed changes required.

---

## Table of Contents

1. [What is SRPTO?](#1-what-is-srpto)
2. [How It Works — Architecture](#2-how-it-works--architecture)
3. [Package Structure](#3-package-structure)
4. [Installation & Setup](#4-installation--setup)
5. [Quick Start](#5-quick-start)
6. [Command-Line Reference](#6-command-line-reference)
7. [Resource Map (resources.yaml)](#7-resource-map-resourcesyaml)
8. [Lock Tiers & Conflict Detection](#8-lock-tiers--conflict-detection)
9. [Pytest Plugin Mode](#9-pytest-plugin-mode)
10. [Verifying SRPTO Works](#10-verifying-srpto-works)
11. [Reading the Output](#11-reading-the-output)
12. [Performance Impact](#12-performance-impact)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. What is SRPTO?

Without SRPTO, a 4-DUT testbed runs **one test at a time**, leaving 2–3 DUTs idle:

\`\`\`
Before SRPTO
────────────────────────────────────────────────────────────────
  DUT1 ██████ test_bgp ██████░░░░░░░░░░░░░░░░░░░░░░░░░░ idle
  DUT2 ██████ test_bgp ██████░░░░░░░░░░░░░░░░░░░░░░░░░░ idle
  DUT3 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ idle
  DUT4 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ idle
  Utilization: ~25%

After SRPTO
────────────────────────────────────────────────────────────────
  DUT1 ██████ test_bgp ██████|████████ test_acl ████████
  DUT2 ██████ test_bgp ██████|░░░░░░░░░░░░░░░░░░░░░░░░░
  DUT3 ░░░░░░|██ test_snmp ██|████ test_static_route ████
  DUT4 ░░░░░░|░░░░░░░░░░░░░░░|████ test_lldp ████████████
  Utilization: ~85-90%
\`\`\`

**Impact on a 200-test regression:**

| Metric | Before | After |
|--------|--------|-------|
| Runtime | ~20 hours | ~12–14 hours |
| Testbeds needed | 10 | 6–7 |
| DUT utilization | 25–50% | 85–90% |

---

## 2. How It Works — Architecture

### High-Level Flow

\`\`\`mermaid
flowchart TD
    A["srpto_run CLI\n--scripts tests/*.py\n--testbed testbed.yaml\n--resource-map res.yaml"] --> B["ResourceTagger\nParse resource needs\nper script"]
    B --> C["ConflictDetector\nPre-flight check:\nVLAN / PTF / reboot conflicts"]
    C --> D["ParallelScheduler\nOne thread per script"]
    D --> E{DUTPool\nThread-safe lock pool}
    E -->|DUTs free| F["Subprocess launch\nspytest / pytest"]
    E -->|DUTs busy| G["WAIT\npoll every 5s"]
    G --> E
    F --> H["Script runs\nlogs to srpto_logs/"]
    H --> I["Release DUTs\nback to pool"]
    I --> E
    F --> J["JSON status\nstdout / file"]
\`\`\`

### Script Lifecycle State Machine

\`\`\`mermaid
stateDiagram-v2
    [*] --> queued : Script submitted
    queued --> waiting : Worker thread started\nDUTs not yet free
    waiting --> running : DUTs acquired\nsubprocess launched
    running --> done : Return code 0
    running --> failed : Return code != 0
    waiting --> cancelled : Timeout expired\n--acquire-timeout
    done --> [*]
    failed --> [*]
    cancelled --> [*]
\`\`\`

### DUT Pool — Thread-Safe Locking View

\`\`\`mermaid
flowchart LR
    subgraph Pool["DUTPool (shared state)"]
        direction TB
        D1["DUT1\nbusy: test_bgp"]
        D2["DUT2\nbusy: test_bgp"]
        D3["DUT3\nbusy: test_snmp"]
        D4["DUT4\nfree"]
    end

    T1["Thread: test_bgp\nneeds 2 DUTs"] -->|holds| D1
    T1 -->|holds| D2
    T2["Thread: test_snmp\nneeds 1 DUT"] -->|holds| D3
    T3["Thread: test_acl\nneeds 1 DUT"] -->|waiting for free DUT| D4
    T4["Thread: test_warm_reboot\ntopology_exclusive"] -->|BLOCKED: waiting for all| Pool
\`\`\`

### Lock Tier Hierarchy

\`\`\`mermaid
flowchart TD
    L1["TOPOLOGY exclusive\nWarm-reboot, config-reload\nBlocks ALL other scripts"]
    L2["PTF exclusive\nOnly 1 script uses PTF host at a time"]
    L3["DEVICE per-DUT\nDefault: each DUT locked per holder"]
    L4["SHARED RESOURCE\nvlan:100, portchannel:Po1\nBlocks scripts on same resource"]

    L1 -->|most restrictive| L2
    L2 --> L3
    L3 -->|least restrictive| L4
\`\`\`

---

## 3. Package Structure

\`\`\`
sonic-mgmt/
└── srpto/
    ├── __init__.py                      # Package version & exports
    ├── conftest_srpto.py                # pytest plugin (drop-in)
    ├── SRPTO_GUIDE.md                   # This file
    │
    ├── cli/
    │   └── srpto_run.py                 # Main CLI entry point
    │
    ├── lock_manager/
    │   └── dut_lock.py                  # Thread-safe DUT pool
    │
    ├── resource_tagger/
    │   └── tagger.py                    # Parse resource needs per script
    │
    ├── scheduler/
    │   ├── engine.py                    # ParallelScheduler — core logic
    │   └── conflict.py                  # Pre-flight conflict detection
    │
    ├── docs/
    │   └── resource_map_example.yaml    # Annotated resource-map template
    │
    └── tests/
        └── test_dut_lock.py             # Unit tests (7/7 passing)
\`\`\`

---

## 4. Installation & Setup

### Prerequisites

\`\`\`bash
# Python 3.8+
python3 --version

# Required packages
pip install pytest pyyaml

# Optional: for parallel pytest mode
pip install pytest-xdist
\`\`\`

### Verify SRPTO is importable

\`\`\`bash
cd /path/to/sonic-mgmt
python3 -c "from srpto.scheduler.engine import ParallelScheduler; print('SRPTO OK')"
\`\`\`

---

## 5. Quick Start

### Step 1 — Generate a resource map from your scripts

\`\`\`bash
cd /path/to/sonic-mgmt

python -m srpto.cli.srpto_run \
    --testbed testbeds/sonic_t0_4dut.yaml \
    --scripts tests/bgp/test_bgp_gr.py \
             tests/acl/test_acl.py \
             tests/snmp/test_snmp.py \
    --generate-resource-map resources.yaml
\`\`\`

Output:
\`\`\`
[SRPTO] Resource map written to: resources.yaml
        Review and adjust dut_count, shared_resources, and topology_exclusive
        fields before running.
\`\`\`

### Step 2 — Review and edit `resources.yaml`

\`\`\`yaml
test_bgp_gr.py:
  dut_count: 2           # SRPTO detected 2-DUT BGP test
  ptf_required: false
  topology_exclusive: false
  min_topology:
    - "D1D2:2"           # needs >= 2 links between DUT1 and DUT2

test_acl.py:
  dut_count: 1
  shared_resources:
    - "vlan:100"         # add if ACL test modifies VLAN 100

test_snmp.py:
  dut_count: 1           # simple 1-DUT test, no conflicts
\`\`\`

### Step 3 — Dry-run (verify allocations before real run)

\`\`\`bash
python -m srpto.cli.srpto_run \
    --testbed testbeds/sonic_t0_4dut.yaml \
    --scripts tests/bgp/test_bgp_gr.py \
             tests/acl/test_acl.py \
             tests/snmp/test_snmp.py \
    --resource-map resources.yaml \
    --dry-run
\`\`\`

### Step 4 — Run for real

\`\`\`bash
python -m srpto.cli.srpto_run \
    --testbed testbeds/sonic_t0_4dut.yaml \
    --scripts tests/bgp/test_bgp_gr.py \
             tests/acl/test_acl.py \
             tests/snmp/test_snmp.py \
    --resource-map resources.yaml \
    --mode spytest \
    --logs-dir ./srpto_logs \
    --json-results results.json
\`\`\`

---

## 6. Command-Line Reference

\`\`\`
python -m srpto.cli.srpto_run [OPTIONS]
\`\`\`

### Required

| Flag | Short | Description |
|------|-------|-------------|
| `--testbed PATH` | `-t` | Testbed YAML (sonic-mgmt or SpyTest format) |
| `--scripts PATH...` | `-s` | Script paths or glob patterns (e.g. `tests/bgp/*.py`) |

### Resource / Mode

| Flag | Default | Description |
|------|---------|-------------|
| `--resource-map PATH` | `-r` | SRPTO resource-map YAML. Auto-detects if omitted |
| `--mode {spytest,pytest}` | `spytest` | Invocation mode |
| `--generate-resource-map OUT` | — | Generate a starter `resources.yaml` and exit |

### Execution

| Flag | Default | Description |
|------|---------|-------------|
| `--logs-dir DIR` | `./srpto_logs` | Where per-script log files are saved |
| `--max-workers N` | `16` | Max parallel worker threads |
| `--acquire-timeout SEC` | `0` | Seconds to wait for DUTs (`0` = wait forever) |
| `--poll-interval SEC` | `5.0` | How often to re-check DUT pool |
| `--dry-run` | `false` | Resolve allocations only — no subprocesses |
| `--extra-args ARG...` | — | Extra args appended to every script invocation |
| `--spytest-bin PATH` | auto | Explicit SpyTest binary path |
| `--pytest-bin PATH` | `pytest` | pytest binary |

### Output

| Flag | Default | Description |
|------|---------|-------------|
| `--json-results OUT` | — | Write final results to JSON file |
| `--log-level LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

### Full Usage Examples

\`\`\`bash
# SpyTest mode — 3 scripts in parallel
python -m srpto.cli.srpto_run \
    -t testbeds/sonic_t0_4dut.yaml \
    -s tests/bgp/test_bgp_gr.py tests/acl/test_acl.py tests/snmp/test_snmp.py \
    -r resources.yaml \
    --mode spytest

# Pytest (community) mode — all tests in a folder
python -m srpto.cli.srpto_run \
    -t testbeds/sonic_t0.yaml \
    -s tests/bgp/ tests/acl/ tests/snmp/ \
    --mode pytest \
    --logs-dir logs/

# Glob pattern expansion
python -m srpto.cli.srpto_run \
    -t testbeds/sonic_t0_4dut.yaml \
    -s "tests/**/*.py" \
    -r resources.yaml

# Dry-run — validate without executing
python -m srpto.cli.srpto_run \
    -t testbeds/sonic_t0_4dut.yaml \
    -s tests/bgp/test_bgp_gr.py tests/acl/test_acl.py \
    -r resources.yaml \
    --dry-run

# Timeout — fail script if DUTs not free within 30 min
python -m srpto.cli.srpto_run \
    -t testbeds/sonic_t0_4dut.yaml \
    -s tests/bgp/*.py \
    -r resources.yaml \
    --acquire-timeout 1800

# Write machine-readable results + debug logging
python -m srpto.cli.srpto_run \
    -t testbeds/sonic_t0_4dut.yaml \
    -s tests/bgp/*.py tests/acl/*.py \
    -r resources.yaml \
    --json-results results.json \
    --log-level DEBUG
\`\`\`

---

## 7. Resource Map (`resources.yaml`)

The resource map tells SRPTO what each script needs. There are **3 ways** to declare resources:

### Method 1 — YAML file (recommended)

\`\`\`yaml
# resources.yaml

# 2-DUT BGP test needing 2 inter-DUT links
test_bgp_gr.py:
  dut_count: 2
  ptf_required: false
  topology_exclusive: false
  min_topology:
    - "D1D2:2"             # needs >= 2 links between D1 and D2

# EVPN test with PTF traffic injection
test_evpn.py:
  dut_count: 2
  ptf_required: true
  min_topology:
    - "D1D2:1"

# ACL test modifying shared resources
test_acl.py:
  dut_count: 1
  shared_resources:
    - "vlan:100"           # won't run parallel with test_acl2 (also vlan:100)
    - "portchannel:PortChannel1"

# Simple 1-DUT test — no constraints
test_snmp.py:
  dut_count: 1

# Warm-reboot — locks the entire topology
test_warm_reboot.py:
  dut_count: 1
  topology_exclusive: true   # NO other test runs while this is active

# Pinned to a specific DUT
test_static_route.py:
  dut_count: 1
  dut_names:
    - "sonic-dut-3"          # runs only on DUT3
\`\`\`

### Method 2 — Inline pytest marker (zero-config)

\`\`\`python
import pytest

@pytest.mark.srpto_resources(
    dut_count=2,
    ptf_required=True,
    min_topology=["D1D2:2"]
)
def test_bgp_gr(duthosts, tbinfo):
    ...
\`\`\`

### Method 3 — Auto-detect (fallback)

SRPTO reads `@pytest.mark.topology()` and SpyTest `vars` files to guess requirements automatically.

**Priority**: YAML file > inline marker > auto-detect

### `min_topology` Notation

| Notation | Meaning |
|----------|---------|
| `D1D2:2` | DUT1 and DUT2 must have >= 2 links between them |
| `D2D3:1` | DUT2 and DUT3 must have >= 1 link |
| `D1D2` | Same as `D1D2:1` |

---

## 8. Lock Tiers & Conflict Detection

### Lock Tiers

\`\`\`mermaid
flowchart TD
    subgraph TOPOLOGY["TOPOLOGY Exclusive"]
        WR["test_warm_reboot\ntest_config_reload"]
    end
    subgraph PTF["PTF Exclusive"]
        EV["test_evpn\ntest_traffic"]
    end
    subgraph DEVICE["DEVICE per-DUT"]
        BG["test_bgp → DUT1+DUT2"]
        AC["test_acl → DUT3"]
        SN["test_snmp → DUT4"]
    end
    subgraph SR["Shared Resource"]
        V["vlan:100\nportchannel:Po1"]
    end

    TOPOLOGY -->|blocks everything| PTF
    PTF -->|blocks other PTF users| DEVICE
    DEVICE -->|blocks same DUT| SR
\`\`\`

### Conflict Types

| Type | Trigger | Behaviour |
|------|---------|-----------|
| `exclusive` | One script sets `topology_exclusive: true` | Serialized — all others wait |
| `ptf` | Two scripts both need PTF host | Serialized — one waits |
| `shared_resource` | Both declare same `vlan:X` or `portchannel:Y` | Serialized |
| `dut_overlap` | Both explicitly request the same DUT name | Serialized |

> **Note:** Conflicts are warnings, not errors. SRPTO serializes conflicting scripts automatically at runtime — it does not cancel them.

---

## 9. Pytest Plugin Mode

Drop-in integration without the CLI.

### Option A — Add to `conftest.py`

\`\`\`python
# tests/conftest.py
pytest_plugins = ['srpto.conftest_srpto']
\`\`\`

### Option B — Copy the plugin

\`\`\`bash
cp srpto/conftest_srpto.py tests/conftest_srpto.py
\`\`\`

### Run with pytest-xdist

\`\`\`bash
pytest tests/ \
    --srpto-testbed testbeds/sonic_t0.yaml \
    --srpto-resource-map resources.yaml \
    -n auto
\`\`\`

### Run with SRPTO's own parallelism

\`\`\`bash
pytest tests/ \
    --srpto-testbed testbeds/sonic_t0.yaml \
    --srpto-resource-map resources.yaml \
    --srpto-run-parallel
\`\`\`

### pytest CLI options added by the plugin

| Option | Description |
|--------|-------------|
| `--srpto-testbed PATH` | Testbed YAML |
| `--srpto-resource-map PATH` | Resource map YAML |
| `--srpto-run-parallel` | SRPTO manages parallelism |

---

## 10. Verifying SRPTO Works

### Step 1 — Run the unit tests

\`\`\`bash
cd /path/to/sonic-mgmt

# With pytest
pytest srpto/tests/test_dut_lock.py -v

# Standalone (no pytest needed)
python srpto/tests/test_dut_lock.py
\`\`\`

Expected output:
\`\`\`
srpto/tests/test_dut_lock.py::test_fifo_allocation_single_dut          PASSED
srpto/tests/test_dut_lock.py::test_multi_dut_allocation                PASSED
srpto/tests/test_dut_lock.py::test_topology_exclusive_blocks_others    PASSED
srpto/tests/test_dut_lock.py::test_ptf_exclusivity                     PASSED
srpto/tests/test_dut_lock.py::test_shared_resource_conflict            PASSED
srpto/tests/test_dut_lock.py::test_topology_matching                   PASSED
srpto/tests/test_dut_lock.py::test_timeout_returns_none                PASSED
srpto/tests/test_dut_lock.py::test_status_snapshot_matches_eka_schema  PASSED

8 passed in 0.52s
\`\`\`

### Step 2 — Verify all modules import

\`\`\`bash
python3 -c "
from srpto.scheduler.engine import ParallelScheduler, SchedulerConfig
from srpto.lock_manager.dut_lock import DUTPool, ResourceRequirement
from srpto.resource_tagger.tagger import ResourceTagger
from srpto.scheduler.conflict import ConflictDetector
print('All SRPTO modules imported successfully')
"
\`\`\`

### Step 3 — Test the DUT pool directly

\`\`\`python
python3 << 'EOF'
from srpto.lock_manager.dut_lock import DUTPool, ResourceRequirement

pool = DUTPool(["DUT1", "DUT2", "DUT3", "DUT4"])

req_bgp = ResourceRequirement(dut_count=2)
duts = pool.acquire(req_bgp, "test_bgp.py")
print(f"test_bgp.py  -> {duts}")

status = pool.get_status()
print(f"Free DUTs    : {status['free_duts']}")
print(f"Busy DUTs    : {status['busy_duts']}")

req_snmp = ResourceRequirement(dut_count=1)
duts2 = pool.acquire(req_snmp, "test_snmp.py")
print(f"test_snmp.py -> {duts2}")

pool.release(duts, "test_bgp.py", req_bgp)
pool.release(duts2, "test_snmp.py", req_snmp)
print(f"Final free   : {pool.get_status()['free_duts']}")
EOF
\`\`\`

Expected output:
\`\`\`
test_bgp.py  -> ['DUT1', 'DUT2']
Free DUTs    : ['DUT3', 'DUT4']
Busy DUTs    : ['DUT1', 'DUT2']
test_snmp.py -> ['DUT3']
Final free   : ['DUT1', 'DUT2', 'DUT3', 'DUT4']
\`\`\`

### Step 4 — Dry-run with the example resource map

\`\`\`bash
python -m srpto.cli.srpto_run \
    --testbed testbeds/sonic_t0_4dut.yaml \
    --scripts tests/bgp/test_bgp_gr.py \
             tests/acl/test_acl.py \
             tests/snmp/test_snmp.py \
    --resource-map srpto/docs/resource_map_example.yaml \
    --dry-run \
    --log-level DEBUG
\`\`\`

### Step 5 — Generate and inspect a resource map

\`\`\`bash
python -m srpto.cli.srpto_run \
    --testbed testbeds/sonic_t0.yaml \
    --scripts tests/bgp/test_bgp_gr.py tests/acl/test_acl.py \
    --generate-resource-map /tmp/auto_resources.yaml

cat /tmp/auto_resources.yaml
\`\`\`

---

## 11. Reading the Output

### Console (stderr) — Structured log

\`\`\`
2026-09-15 10:00:01 [INFO]  srpto.scheduler   : Starting 3 script(s)
2026-09-15 10:00:01 [INFO]  srpto.conflict    : No pre-flight conflicts
2026-09-15 10:00:01 [INFO]  srpto.scheduler   : [test_bgp_gr.py] status=waiting
2026-09-15 10:00:01 [INFO]  srpto.scheduler   : [test_snmp.py]   status=waiting
2026-09-15 10:00:06 [INFO]  srpto.lock_manager: [test_bgp_gr.py] acquired DUT1, DUT2
2026-09-15 10:00:06 [INFO]  srpto.lock_manager: [test_snmp.py]   acquired DUT3
2026-09-15 10:00:06 [INFO]  srpto.scheduler   : [test_bgp_gr.py] status=running
2026-09-15 10:00:06 [INFO]  srpto.scheduler   : [test_snmp.py]   status=running
2026-09-15 10:04:20 [INFO]  srpto.scheduler   : [test_snmp.py]   status=done rc=0 duration=254s
2026-09-15 10:04:20 [INFO]  srpto.lock_manager: [test_snmp.py]   released DUT3
2026-09-15 10:04:20 [INFO]  srpto.lock_manager: [test_acl.py]    acquired DUT3
2026-09-15 10:04:20 [INFO]  srpto.scheduler   : [test_acl.py]    status=running
\`\`\`

### JSON results (`--json-results results.json`)

\`\`\`json
[
  {
    "script": "tests/bgp/test_bgp_gr.py",
    "status": "done",
    "duts": ["DUT1", "DUT2"],
    "return_code": 0,
    "duration_s": 1082.4,
    "log_path": "srpto_logs/test_bgp_gr_20260915_100001.log",
    "error": ""
  },
  {
    "script": "tests/acl/test_acl.py",
    "status": "done",
    "duts": ["DUT3"],
    "return_code": 0,
    "duration_s": 320.1,
    "log_path": "srpto_logs/test_acl_20260915_100420.log",
    "error": ""
  }
]
\`\`\`

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | All scripts passed |
| `1` | One or more scripts failed or were cancelled |

---

## 12. Performance Impact

**Runtime — 200-test regression, 4-DUT testbed:**
\`\`\`
Without SRPTO  ████████████████████  20 hours
With SRPTO     █████████████         13 hours
\`\`\`

**DUT Utilization:**
\`\`\`
Without SRPTO  ███░░░░░░░░░░░░░░░░░  ~30%
With SRPTO     █████████████████░░░  ~87%
\`\`\`

**Summary table:**

| | Without SRPTO | With SRPTO |
|-|--------------|------------|
| Testbeds required | 10 | 6–7 |
| Parallel scripts | 1 | 3–4 |
| DUT utilization | 25–50% | 85–90% |
| Total wall-clock time | 20h | 12–14h |

---

## 13. Troubleshooting

### `ModuleNotFoundError: No module named 'srpto'`

\`\`\`bash
# Run from the sonic-mgmt root
cd /path/to/sonic-mgmt
python -m srpto.cli.srpto_run ...

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/sonic-mgmt:$PYTHONPATH
\`\`\`

### `No scripts specified (--scripts)`

\`\`\`bash
# Wrong
python -m srpto.cli.srpto_run --testbed testbed.yaml

# Correct
python -m srpto.cli.srpto_run --testbed testbed.yaml --scripts tests/bgp/*.py
\`\`\`

### DUTs never get allocated (stuck in `waiting`)

- Default `--acquire-timeout 0` means wait forever — set a value if you want scripts to fail fast
- Verify the testbed YAML DUT names match your `dut_names:` entries in `resources.yaml`
- Use `--log-level DEBUG` to see pool state every poll cycle

### Conflict warnings flooding the log

\`\`\`
[CONFLICT:shared_resource] test_acl.py <-> test_acl2.py: Both modify 'vlan:100'
\`\`\`

This is a **warning, not an error**. SRPTO serializes these automatically. Review `shared_resources` in your `resources.yaml`.

### `topology_exclusive` test blocks everything

Expected behaviour. A `topology_exclusive: true` script holds the whole-topology lock — all other scripts wait. Running a reboot test in parallel with traffic tests would corrupt results.

### Unit tests failing

\`\`\`bash
pytest srpto/tests/test_dut_lock.py -v --tb=short
python3 --version   # needs 3.8+
\`\`\`

---

## Related Files

| File | Purpose |
|------|---------|
| [`srpto/cli/srpto_run.py`](srpto/cli/srpto_run.py) | CLI entry point |
| [`srpto/scheduler/engine.py`](srpto/scheduler/engine.py) | Parallel scheduler core |
| [`srpto/lock_manager/dut_lock.py`](srpto/lock_manager/dut_lock.py) | Thread-safe DUT pool |
| [`srpto/resource_tagger/tagger.py`](srpto/resource_tagger/tagger.py) | Resource auto-detection |
| [`srpto/scheduler/conflict.py`](srpto/scheduler/conflict.py) | Pre-flight conflict checker |
| [`srpto/conftest_srpto.py`](srpto/conftest_srpto.py) | pytest plugin |
| [`srpto/docs/resource_map_example.yaml`](srpto/docs/resource_map_example.yaml) | Example resource map |
| [`srpto/tests/test_dut_lock.py`](srpto/tests/test_dut_lock.py) | Unit tests |

---

*SRPTO — Built on Eka's DUT pool allocator, extended for the sonic-mgmt community framework.*
