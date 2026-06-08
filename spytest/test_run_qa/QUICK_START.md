# Feature-Based Test Runner - Quick Start

## Available Features (10 Total)

```
✓ ACL             : ACL (Access Control List)
✓ ARP             : ARP (Address Resolution Protocol)
✓ BGP             : BGP (Border Gateway Protocol)
✓ LLDP            : LLDP (Link Layer Discovery Protocol)
✓ NTP             : NTP (Network Time Protocol)
✓ OSPF            : OSPF (Open Shortest Path First)
✓ PORTCHANNEL     : PortChannel (LAG)
✓ QOS             : QoS (Quality of Service)
✓ STATIC_ROUTE    : Static Route (IPv4/IPv6)
✓ VLAN            : VLAN (Virtual LAN)
```

## Quick Commands

### Run All Features
```bash
./test_run/run_testsuite.sh
```

### Run Specific Features
```bash
# Single feature
./test_run/run_testsuite.sh --features LLDP

# Multiple features
./test_run/run_testsuite.sh --features LLDP,BGP,VLAN

# Routing features
./test_run/run_testsuite.sh --features BGP,OSPF,STATIC_ROUTE

# L2 features
./test_run/run_testsuite.sh --features VLAN,PORTCHANNEL,LLDP

# QoS and ACL features
./test_run/run_testsuite.sh --features QOS,ACL

# ARP and NTP
./test_run/run_testsuite.sh --features ARP,NTP
```

### List Available Features
```bash
./test_run/run_testsuite.sh --list
```

### Run Individual Feature Script
```bash
./test_run/features/lldp.sh
./test_run/features/bgp.sh
./test_run/features/vlan.sh
# ... etc
```

## Output Structure

Each feature creates:
```
logs/YYYYMMDD/
├── LLDP/
│   ├── BATCH_1__HHMMSS/          # Test results
│   ├── BATCH_2__HHMMSS/          # Test results
│   ├── dashboard_LLDP_*.html     # Feature dashboard
│   └── LLDP.json                 # Feature JSON
├── BGP/
│   ├── dashboard_BGP_*.html
│   └── BGP.json
├── VLAN/
│   ├── dashboard_VLAN_*.html
│   └── VLAN.json
└── dashboard/
    ├── master_dashboard_*.html   # All features consolidated
    └── master_results.json       # All features consolidated
```

## Feature Details

| Feature | Tests | Batches | Main Testbeds |
|---------|-------|---------|---------------|
| LLDP | 40+ | 3 | testbed_vs_2d.yaml |
| BGP | 50+ | 6 | testbed_vs_3rr.yaml, testbed_vs_2node.yaml |
| VLAN | 12+ | 2 | testbed_2node.yaml, testbed_vs_2d.yaml |
| OSPF | 40+ | 1 | testbed_4node.yaml |
| NTP | 5+ | 2 | testbed_vs_1node.yaml |
| ACL | 15+ | 4 | testbed_acl.yaml, ztp_standalone.yaml |
| STATIC_ROUTE | 30+ | 3 | testbed_vs_1node.yaml |
| PORTCHANNEL | 5+ | 2 | testbed_2node.yaml |
| QOS | 10+ | 5 | testbed_vs_2d.yaml, testbed_vs_1node.yaml |
| ARP | 30+ | 3 | testbed_2vs.yaml |

## Benefits

✅ **Modular**: Each feature script is independent
✅ **Feature-Specific Dashboards**: Consolidated HTML per feature
✅ **Feature-Specific JSON**: Structured JSON per feature
✅ **Master Consolidation**: All features in one dashboard with tabs
✅ **Selective Execution**: Run only what you need
✅ **No Changes to Original Scripts**: run_testsuite_qa.sh untouched

## Full Documentation

See `FEATURE_RUNNER_GUIDE.md` for:
- Complete architecture details
- How to add new features
- Troubleshooting guide
- Advanced usage examples
- Best practices
