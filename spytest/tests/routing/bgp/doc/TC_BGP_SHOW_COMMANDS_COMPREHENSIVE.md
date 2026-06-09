# BGP Show Commands - Test Plan (klish)

**Document Version:** 2.0
**Last Updated:** 2026-06-09
**Feature:** BGP Show Commands
**Module:** Routing / BGP
**Testbed:** testbed_vs_2d.yaml
**Topology:** 2-Node eBGP (D1 AS 65001 ↔ D2 AS 65002)
**CLI Type:** Klish (only)
**Automation:** `tests/routing/bgp/test_bgp_show_commands.py`

---

## 1. Scope

This plan covers the BGP `show` commands that are **supported by the SONiC klish
CLI**. Coverage is restricted to the klish-supported command set (Section 4).
FRR/vtysh-only commands (`cidr-only`, `regexp`, `paths`, `detail`, `dampening`,
`flap-statistics`, neighbor `advertised-routes`/`received-routes`/`routes`,
`statistics`/`memory`/`update-groups`/`nexthop`, JSON output, prefix lookups,
etc.) are **out of scope** because klish rejects them.

**Total Test Cases:** 43 (TC-001 … TC-043), all positive, all klish.
- TC-001 … TC-031: base commands
- TC-032 … TC-037: IPv4/IPv6 `community <filter>` variants
- TC-038 … TC-043: `running-configuration bgp <sub-option>` variants

Each test case ID maps 1:1 to the automation:
- Plan ID `TC-<nnn>`  →  inventory ID `BGP_SHOW_TC<nnn>`  →  function `test_bgp_show_tc<nnn>_*`.

---

## 2. Topology & Pre-requisites

```
+----------------------+                         +----------------------+
|   DUT1 (AS 65001)    |                         |   DUT2 (AS 65002)    |
| Eth32 10.0.24.1/24   |=========================| Eth32 10.0.24.2/24   |
|       2001:db8::1/64 |<-- IPv4 + IPv6 eBGP -->  |       2001:db8::2/64 |
+----------------------+                         +----------------------+
```

**Addressing / sessions**
- IPv4 eBGP: D1 `10.0.24.1` ↔ D2 `10.0.24.2` (neighbor on D1 = `10.0.24.2`)
- IPv6 eBGP: D1 `2001:db8::1` ↔ D2 `2001:db8::2` (neighbor on D1 = `2001:db8::2`)
- D2 advertises `10.10.10.0/24` (IPv4) and `2001:db8:20::/64` (IPv6)
- D1 has peer-group `SPINE_PEERS` and route-map `SET_COMMUNITY`

**Setup (performed by the suite, klish):**
1. `_ensure_base_bgp_session()` – configure/clear the IPv4 eBGP neighbor on both DUTs.
2. `_ensure_ipv6_bgp_session()` – add IPv6 link addressing, configure + activate the
   IPv6 neighbor on both DUTs, advertise the IPv6 test network, clear to converge.
3. `_verify_bgp_session_established()` – poll until D1↔D2 is Established.

---

## 3. Validation model

- A command that klish **rejects** (`% Error` / `Invalid input`) is treated as
  *unsupported* and the test **fails** (surfaces any whitelist drift).
- A command that is accepted but legitimately returns **no data** (empty table /
  "no neighbors" message) **passes** (command-supported assertion).
- Where data is known to exist, the test additionally asserts that the expected
  neighbor / network / AS is present in the parsed output.

---

## 4. Test Cases

| TC-ID | Inventory ID | Test function | Command | Validation |
|-------|--------------|---------------|---------|------------|
| TC-001 | BGP_SHOW_TC001 | `test_bgp_show_tc001_global_summary` | `show bgp summary` | IPv4 neighbor `10.0.24.2` present |
| TC-002 | BGP_SHOW_TC002 | `test_bgp_show_tc002_summary_established` | `show bgp summary established` | Established neighbor present |
| TC-003 | BGP_SHOW_TC003 | `test_bgp_show_tc003_summary_failed` | `show bgp summary failed` | Command supported (no failed nbrs) |
| TC-004 | BGP_SHOW_TC004 | `test_bgp_show_tc004_summary_neighbor` | `show bgp summary neighbor 10.0.24.2` | Neighbor present |
| TC-005 | BGP_SHOW_TC005 | `test_bgp_show_tc005_summary_remote_as` | `show bgp summary remote-as 65002` | Neighbor present |
| TC-006 | BGP_SHOW_TC006 | `test_bgp_show_tc006_summary_vrf` | `show bgp summary vrf default` | Neighbor present |
| TC-007 | BGP_SHOW_TC007 | `test_bgp_show_tc007_ipv4_unicast_summary` | `show bgp ipv4 unicast summary` | IPv4 neighbor present |
| TC-008 | BGP_SHOW_TC008 | `test_bgp_show_tc008_ipv6_unicast_summary` | `show bgp ipv6 unicast summary` | IPv6 neighbor `2001:db8::2` present |
| TC-009 | BGP_SHOW_TC009 | `test_bgp_show_tc009_ipv4_vrf` | `show bgp ipv4 unicast vrf default` | Command supported |
| TC-010 | BGP_SHOW_TC010 | `test_bgp_show_tc010_bgp_route` | `show bgp route` | Command supported |
| TC-011 | BGP_SHOW_TC011 | `test_bgp_show_tc011_ipv4_unicast` | `show bgp ipv4 unicast` | Test network `10.10.10.0` present |
| TC-012 | BGP_SHOW_TC012 | `test_bgp_show_tc012_ipv6_unicast` | `show bgp ipv6 unicast` | Command supported |
| TC-013 | BGP_SHOW_TC013 | `test_bgp_show_tc013_ipv4_community` | `show bgp ipv4 unicast community no-export` | Command supported |
| TC-014 | BGP_SHOW_TC014 | `test_bgp_show_tc014_ipv6_community` | `show bgp ipv6 unicast community no-export` | Command supported |
| TC-015 | BGP_SHOW_TC015 | `test_bgp_show_tc015_ipv4_neighbors` | `show bgp ipv4 unicast neighbors` | Neighbor `10.0.24.2` present |
| TC-016 | BGP_SHOW_TC016 | `test_bgp_show_tc016_ipv4_neighbor_specific` | `show bgp ipv4 unicast neighbors 10.0.24.2` | Neighbor present |
| TC-017 | BGP_SHOW_TC017 | `test_bgp_show_tc017_ipv4_neighbors_interface` | `show bgp ipv4 unicast neighbors interface Ethernet32` | Command supported |
| TC-018 | BGP_SHOW_TC018 | `test_bgp_show_tc018_ipv6_neighbors` | `show bgp ipv6 unicast neighbors` | Neighbor `2001:db8::2` present |
| TC-019 | BGP_SHOW_TC019 | `test_bgp_show_tc019_ipv6_neighbor_specific` | `show bgp ipv6 unicast neighbors 2001:db8::2` | Neighbor present |
| TC-020 | BGP_SHOW_TC020 | `test_bgp_show_tc020_ipv6_neighbors_interface` | `show bgp ipv6 unicast neighbors interface Ethernet32` | Command supported |
| TC-021 | BGP_SHOW_TC021 | `test_bgp_show_tc021_all_neighbors` | `show bgp all neighbors` | Neighbor `10.0.24.2` present |
| TC-022 | BGP_SHOW_TC022 | `test_bgp_show_tc022_ipv4_route_map` | `show bgp ipv4 unicast route-map SET_COMMUNITY` | Command supported |
| TC-023 | BGP_SHOW_TC023 | `test_bgp_show_tc023_ipv4_statistics` | `show bgp ipv4 unicast statistics` | Command supported |
| TC-024 | BGP_SHOW_TC024 | `test_bgp_show_tc024_ipv6_route_map` | `show bgp ipv6 unicast route-map SET_COMMUNITY` | Command supported |
| TC-025 | BGP_SHOW_TC025 | `test_bgp_show_tc025_ipv6_statistics` | `show bgp ipv6 unicast statistics` | Command supported |
| TC-026 | BGP_SHOW_TC026 | `test_bgp_show_tc026_ipv4_vrf_all` | `show bgp ipv4 unicast vrf all` | Command supported |
| TC-027 | BGP_SHOW_TC027 | `test_bgp_show_tc027_ipv6_vrf_all` | `show bgp ipv6 unicast vrf all` | Command supported |
| TC-028 | BGP_SHOW_TC028 | `test_bgp_show_tc028_ipv6_vrf` | `show bgp ipv6 unicast vrf default` | Command supported |
| TC-029 | BGP_SHOW_TC029 | `test_bgp_show_tc029_all_peer_group` | `show bgp all peer-group` | Command supported |
| TC-030 | BGP_SHOW_TC030 | `test_bgp_show_tc030_l2vpn_evpn` | `show bgp l2vpn evpn` | Command supported |
| TC-031 | BGP_SHOW_TC031 | `test_bgp_show_tc031_running_config` | `show running-configuration bgp` | `router bgp 65001` (AS) present |
| TC-032 | BGP_SHOW_TC032 | `test_bgp_show_tc032_ipv4_community_local_as` | `show bgp ipv4 unicast community local-as` | Command supported |
| TC-033 | BGP_SHOW_TC033 | `test_bgp_show_tc033_ipv4_community_no_advertise` | `show bgp ipv4 unicast community no-advertise` | Command supported |
| TC-034 | BGP_SHOW_TC034 | `test_bgp_show_tc034_ipv4_community_no_peer` | `show bgp ipv4 unicast community no-peer` | Command supported |
| TC-035 | BGP_SHOW_TC035 | `test_bgp_show_tc035_ipv6_community_local_as` | `show bgp ipv6 unicast community local-as` | Command supported |
| TC-036 | BGP_SHOW_TC036 | `test_bgp_show_tc036_ipv6_community_no_advertise` | `show bgp ipv6 unicast community no-advertise` | Command supported |
| TC-037 | BGP_SHOW_TC037 | `test_bgp_show_tc037_ipv6_community_no_peer` | `show bgp ipv6 unicast community no-peer` | Command supported |
| TC-038 | BGP_SHOW_TC038 | `test_bgp_show_tc038_running_config_as_path_list` | `show running-configuration bgp as-path-list` | Command supported |
| TC-039 | BGP_SHOW_TC039 | `test_bgp_show_tc039_running_config_community_list` | `show running-configuration bgp community-list` | Command supported |
| TC-040 | BGP_SHOW_TC040 | `test_bgp_show_tc040_running_config_extcommunity_list` | `show running-configuration bgp extcommunity-list` | Command supported |
| TC-041 | BGP_SHOW_TC041 | `test_bgp_show_tc041_running_config_vrf` | `show running-configuration bgp vrf default` | Command supported |
| TC-042 | BGP_SHOW_TC042 | `test_bgp_show_tc042_running_config_neighbor_vrf` | `show running-configuration bgp neighbor vrf default` | Command supported |
| TC-043 | BGP_SHOW_TC043 | `test_bgp_show_tc043_running_config_peer_group_vrf` | `show running-configuration bgp peer-group vrf default` | Command supported |

---

## 5. klish-supported command reference

The full klish BGP `show` command set this plan is restricted to:

```
show bgp
show bgp all neighbors
show bgp all peer-group
show bgp all vrf
show bgp ipv4 unicast
show bgp ipv4 unicast community
show bgp ipv4 unicast neighbors
show bgp ipv4 unicast neighbors interface
show bgp ipv4 unicast route-map
show bgp ipv4 unicast statistics
show bgp ipv4 unicast summary
show bgp ipv4 unicast vrf  /  vrf all
show bgp ipv6 unicast            (same sub-commands as ipv4)
show bgp l2vpn evpn             (+ es / es-evi / route / summary sub-trees)
show bgp route
show bgp summary
show bgp summary established / failed / neighbor / remote-as / vrf
show running-configuration bgp  (+ as-path-list / community-list /
                                 extcommunity-list / neighbor vrf /
                                 peer-group vrf / vrf)
```

> The `summary <filter>` and `community <filter>` and EVPN sub-trees are exercised
> at the base-command level (one TC each for `community`, `summary` variants,
> `l2vpn evpn`). Sub-filter variants can be added later as separate TCs if needed.

---

## 6a. Not supported by this device's klish (verified rejected)

The following appear in the full klish command-tree dump but are **rejected on
this DUT** (the device's klish is narrower than the dump), so they are not
covered as passing TCs:
- The entire `show bgp ipv4|ipv6 unicast summary <filter>` family (22 commands:
  `summary community[/exact-match/local-as/no-advertise/no-export/no-peer]`,
  `summary neighbors`, `summary neighbors interface`, `summary route-map`,
  `summary statistics`, `summary summary`) — `summary` is terminal here.
- `show bgp ipv4|ipv6 unicast community exact-match` — needs a community value.
- `show bgp all vrf` — non-terminal (needs an address-family/vrf token).
- `show bgp l2vpn evpn <sub-tree>` (es / es-evi / route / summary …, ~35) —
  klish-valid but require an EVPN/VxLAN config that is not present on this
  testbed; only base `show bgp l2vpn evpn` is covered (TC-030).

## 6. Out of scope (FRR/vtysh-only — rejected by klish)

`show ip bgp cidr-only`, `... regexp`, `... paths`, `... detail`, `... bestpath`,
`... longer-prefixes`, `... large-community`, `... community-info`,
`... as-path-access-list`, `... filter-list`, `... attribute-info`,
`... json`, `... summary-only`, `... summary wide`, neighbor
`advertised-routes`/`received-routes`/`routes`/`dampened-routes`/`flap-statistics`/
`capabilities`/`timers`/`prefix-counts`/`connection`, `show bgp statistics`,
`show bgp memory`, `show bgp nexthop`, `show bgp update-groups`,
`show bgp martian next-hop`, `show bgp l3vpn`, `show bgp ipv4 vpn labels`,
`show ip bgp <prefix>`.

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-03 | Initial comprehensive plan (90 cases, mixed CLI) |
| 2.0 | 2026-06-09 | Restricted to klish-supported command set; regenerated to 31 TCs (TC-001..TC-031), 1:1 with `test_bgp_show_commands.py` inventory IDs `BGP_SHOW_TC001..031` |
| 2.1 | 2026-06-09 | Added v4/v6 `community <filter>` (TC-032..037) and `running-configuration bgp <sub-option>` (TC-038..043) variants — all live-verified on the DUT. Documented the device-rejected `summary <filter>` family and EVPN sub-tree (Section 6a). Total 43 TCs. |
