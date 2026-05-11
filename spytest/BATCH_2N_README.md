# Batch 2N - Two-Node Testbed Regression Suite

**Created**: 2026-05-11
**Purpose**: Dedicated regression testing for features requiring 2-node topology
**Testbed**: dlink_2node.yaml (all batches)
**Total Batches**: 8 (B, C, D, E, F, H, I, K)
**Total Test Scripts**: 32

---

## Overview

The `batch_2N.sh` script is a specialized test suite designed to run all regression tests that require a 2-node topology. This provides a faster alternative to the full regression suite when testing features that don't need 3-node, 4-node, or hardware-specific topologies.

All batches in this suite use the **dlink_2node.yaml** testbed configuration.

---

## Available Batches

### BGP Feature Tests (Batches B-F)

| Batch | Name | Tests | Purpose |
|-------|------|-------|---------|
| **B** | BGP_IPV4_FEATURES | 9 | IPv4 BGP iBGP/eBGP features |
| **C** | BGP_ISCLI_BESTPATH | 7 | BGP best path selection (isCLI) |
| **D** | BGP_ISCLI_CAPABILITY | 2 | BGP capability negotiation (isCLI) |
| **E** | BGP_ISCLI_EVPN | 1 | BGP EVPN type 5 routes (isCLI) |
| **F** | BGP_ISCLI_PG_ADV | 5 | BGP peer group advanced features (isCLI) |

**Subtotal**: 24 test scripts

### Switching & System Tests (Batches H, I, K)

| Batch | Name | Tests | Purpose |
|-------|------|-------|---------|
| **H** | PORTCHANNEL_ISCLI | 1 | Port channel isCLI functionality |
| **I** | VLAN_ISCLI | 2 | VLAN isCLI functionality |
| **K** | SYS_INTERFACE_EVENTS | 5 | System interface events & management |

**Subtotal**: 8 test scripts

---

## Usage

### Run All 2-Node Batches
```bash
./batch_2N.sh
```

### List Available Batches
```bash
./batch_2N.sh --list
```

### Run Specific Batches
```bash
# Run batches B, C, D
./batch_2N.sh --features B,C,D

# Run by full name
./batch_2N.sh --features BGP_IPV4_FEATURES,BGP_ISCLI_BESTPATH
```

### Run All BGP Batches
```bash
./batch_2N.sh --features BGP
```

### Run Switching Batches Only
```bash
./batch_2N.sh --features SWITCHING
```

### Run System Batches Only
```bash
./batch_2N.sh --features SYSTEM
```

### Show Help
```bash
./batch_2N.sh --help
```

---

## Output & Logs

All test logs are saved to:
```
./logs/<DATE>/<BATCH_NAME>/<TIME>/
```

Example:
```
./logs/20260511/BGP_IPV4_FEATURES/120000/
./logs/20260511/VLAN_ISCLI/120030/
```

Each batch run includes:
- `dlog-D1-*.log` - DUT1 command/output logs
- `dlog-D2-*.log` - DUT2 command/output logs
- `module_*.log` - Module-level test logs
- `results.html` - HTML test report
- `summary.txt` - Quick summary of results

---

## Testbed Information

**Testbed File**: `./testbeds/dlink_2node.yaml`

**Topology**:
```
┌─────────────┐                    ┌─────────────┐
│   DUT1      │                    │    DUT2     │
│             │                    │             │
│  D1 / Node1 │ ←→ Multiple Links ←→│ D2 / Node2 │
│             │                    │             │
└─────────────┘                    └─────────────┘
```

**Key Characteristics**:
- Back-to-back 2-device topology
- Multiple interconnect interfaces (Ethernet ports)
- Suitable for BGP, switching, and system tests
- Faster execution than multi-node topologies

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Typical Full Run Time** | 30-45 minutes |
| **Per Batch Average** | 4-7 minutes |
| **Setup/Teardown Time** | ~1-2 minutes |
| **Network Requirements** | 2 devices |
| **Resource Usage** | ~2 GB RAM, ~20% CPU |

---

## Batch Details

### BGP_IPV4_FEATURES (Batch B)
**Tests**: 9 test scripts
**Features**:
- Basic IPv4 BGP (loopback, interface, SVI)
- eBGP capabilities (eBGP, eBGP via SVI/PortChannel)
- Redistribution scenarios

**Sample Command**:
```bash
./batch_2N.sh --features B
```

---

### BGP_ISCLI_BESTPATH (Batch C)
**Tests**: 7 test scripts
**Features**:
- BGP best path selection criteria
- Local preference
- AS path length
- MED (Multi-Exit Discriminator)
- Origin codes
- Router ID tiebreak
- Next-hop reachability

**Sample Command**:
```bash
./batch_2N.sh --features C
```

---

### BGP_ISCLI_CAPABILITY (Batch D)
**Tests**: 2 test scripts
**Features**:
- BGP capability negotiation
- Extended nexthop capability

**Sample Command**:
```bash
./batch_2N.sh --features D
```

---

### BGP_ISCLI_EVPN (Batch E)
**Tests**: 1 test script
**Features**:
- EVPN type 5 (IP prefix) routes
- L2VPN/EVPN functionality in isCLI

**Sample Command**:
```bash
./batch_2N.sh --features E
```

---

### BGP_ISCLI_PG_ADV (Batch F)
**Tests**: 5 test scripts
**Features**:
- Peer group advanced capabilities
- Packet queue management
- Allow-as-in functionality
- Conflict detection
- Passive mode
- Route-map overrides

**Sample Command**:
```bash
./batch_2N.sh --features F
```

---

### PORTCHANNEL_ISCLI (Batch H)
**Tests**: 1 test script
**Features**:
- Port channel creation and configuration (isCLI)
- LAG/Link aggregation

**Sample Command**:
```bash
./batch_2N.sh --features H
```

---

### VLAN_ISCLI (Batch I)
**Tests**: 2 test scripts
**Features**:
- VLAN creation and management (isCLI)
- VLAN IP configuration
- VLAN membership

**Sample Command**:
```bash
./batch_2N.sh --features I
```

---

### SYS_INTERFACE_EVENTS (Batch K)
**Tests**: 5 test scripts
**Features**:
- Interface up/down events
- MTU change events
- Interface description changes
- IP address configuration events
- IPv6 address configuration events

**Sample Command**:
```bash
./batch_2N.sh --features K
```

---

## Quick Reference Commands

```bash
# Run all 2-node tests
./batch_2N.sh

# Run only BGP tests
./batch_2N.sh --features BGP

# Run only switching tests
./batch_2N.sh --features SWITCHING

# Run specific batches
./batch_2N.sh --features B,C,F,H

# List all available batches
./batch_2N.sh --list

# Show usage help
./batch_2N.sh --help
```

---

## Comparison: batch_2N.sh vs batch_full_run.sh

| Aspect | batch_2N.sh | batch_full_run.sh |
|--------|-------------|-------------------|
| **Purpose** | 2-node only tests | All tests (1-4 nodes) |
| **Batches** | 8 (B, C, D, E, F, H, I, K) | 104+ (A-CZ) |
| **Scripts** | 32 | 350+ |
| **Runtime** | 30-45 min | 4-8 hours |
| **Testbed** | dlink_2node.yaml | Multiple |
| **Use Case** | Quick BGP/switching validation | Full regression |
| **Best For** | Feature development & debugging | Pre-release validation |

---

## Troubleshooting

### Batch Fails to Run
1. Verify testbed exists: `ls testbeds/dlink_2node.yaml`
2. Check SSH connectivity to devices
3. Verify spytest is installed: `./bin/spytest --version`
4. Review batch script syntax: `bash -n batch_2N.sh`

### Individual Test Failures
1. Review logs in: `./logs/<DATE>/<BATCH>/<TIME>/`
2. Check device connectivity: `show interfaces` on DUT1/DUT2
3. Verify testbed configuration: `./testbeds/dlink_2node.yaml`

### Performance Issues
1. Reduce parallel tests: Modify `batch_2N.sh` if needed
2. Check system resources: `free -h` and `top`
3. Verify network stability between nodes

---

## Integration with CI/CD

To integrate batch_2N.sh into CI/CD pipelines:

```bash
#!/bin/bash
# Example CI/CD integration

set -e  # Exit on error

# Run 2-node regression
./batch_2N.sh --features BGP

# Check results
if [ $? -eq 0 ]; then
    echo "✅ 2-Node BGP tests passed"
    exit 0
else
    echo "❌ 2-Node BGP tests failed"
    exit 1
fi
```

---

## Statistics

**Created**: 2026-05-11
**Current Version**: 1.0
**Maintained By**: SpyTest Automation Team

**Batch Composition**:
- BGP Tests: 5 batches, 24 scripts
- Switching Tests: 2 batches, 3 scripts
- System Tests: 1 batch, 5 scripts
- **Total**: 8 batches, 32 test scripts

---

## Related Documentation

- **Full Regression Suite**: See `batch_full_run.sh`
- **Hardware Batch Suite**: See `batch_hw_full_run.sh`
- **Test Coding Guidelines**: See `Doc/spy_test_coding_guideline.md`
- **Testbed Configuration**: See `testbeds/dlink_2node.yaml`

---

## Support & Questions

For issues or questions regarding batch_2N.sh:

1. Check this README for common scenarios
2. Review batch script header comments: `head -50 batch_2N.sh`
3. Run help command: `./batch_2N.sh --help`
4. Check logs in: `./logs/`
5. Consult framework documentation: `Doc/`

---

**Status**: ✅ Ready for Production Use
