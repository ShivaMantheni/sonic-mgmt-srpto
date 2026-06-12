# BGP Show Commands — Manual Execution Log (43 klish CLIs)

**Date:** 2026-06-09  
**Device:** D1 = `192.168.100.39` (sonic, AS 65001)  
**CLI:** klish (`sonic-cli`)  
**Peer:** D2 = `10.0.24.2` / `2001:db8::2` (AS 65002)  
**Result:** 43/43 PASS

Validation model: a command rejected by klish (`% Error` / `Invalid input` / `not completed`) = FAIL; `contains` checks also require the expected neighbor/marker in the output; `supported` checks pass on any accepted output (incl. empty).

## Summary

| TC | Command | Check | Result |
|----|---------|-------|--------|
| TC-001 | `show bgp summary` | contains `10.0.24.2` | **PASS** |
| TC-002 | `show bgp summary established` | contains `10.0.24.2` | **PASS** |
| TC-003 | `show bgp summary failed` | supported | **PASS** |
| TC-004 | `show bgp summary neighbor 10.0.24.2` | contains `10.0.24.2` | **PASS** |
| TC-005 | `show bgp summary remote-as 65002` | contains `10.0.24.2` | **PASS** |
| TC-006 | `show bgp summary vrf default` | contains `10.0.24.2` | **PASS** |
| TC-007 | `show bgp ipv4 unicast summary` | contains `10.0.24.2` | **PASS** |
| TC-008 | `show bgp ipv6 unicast summary` | contains `2001:db8::2` | **PASS** |
| TC-009 | `show bgp ipv4 unicast vrf default` | supported | **PASS** |
| TC-010 | `show bgp route` | supported | **PASS** |
| TC-011 | `show bgp ipv4 unicast` | contains `BGP table version` | **PASS** |
| TC-012 | `show bgp ipv6 unicast` | supported | **PASS** |
| TC-013 | `show bgp ipv4 unicast community no-export` | supported | **PASS** |
| TC-014 | `show bgp ipv6 unicast community no-export` | supported | **PASS** |
| TC-015 | `show bgp ipv4 unicast neighbors` | contains `10.0.24.2` | **PASS** |
| TC-016 | `show bgp ipv4 unicast neighbors 10.0.24.2` | contains `10.0.24.2` | **PASS** |
| TC-017 | `show bgp ipv4 unicast neighbors interface Ethernet32` | supported | **PASS** |
| TC-018 | `show bgp ipv6 unicast neighbors` | contains `2001:db8::2` | **PASS** |
| TC-019 | `show bgp ipv6 unicast neighbors 2001:db8::2` | contains `2001:db8::2` | **PASS** |
| TC-020 | `show bgp ipv6 unicast neighbors interface Ethernet32` | supported | **PASS** |
| TC-021 | `show bgp all neighbors` | contains `10.0.24.2` | **PASS** |
| TC-022 | `show bgp ipv4 unicast route-map SET_COMMUNITY` | supported | **PASS** |
| TC-023 | `show bgp ipv4 unicast statistics` | supported | **PASS** |
| TC-024 | `show bgp ipv6 unicast route-map SET_COMMUNITY` | supported | **PASS** |
| TC-025 | `show bgp ipv6 unicast statistics` | supported | **PASS** |
| TC-026 | `show bgp ipv4 unicast vrf all` | supported | **PASS** |
| TC-027 | `show bgp ipv6 unicast vrf all` | supported | **PASS** |
| TC-028 | `show bgp ipv6 unicast vrf default` | supported | **PASS** |
| TC-029 | `show bgp all peer-group` | supported | **PASS** |
| TC-030 | `show bgp l2vpn evpn` | supported | **PASS** |
| TC-031 | `show running-configuration bgp` | contains `65001` | **PASS** |
| TC-032 | `show bgp ipv4 unicast community local-as` | supported | **PASS** |
| TC-033 | `show bgp ipv4 unicast community no-advertise` | supported | **PASS** |
| TC-034 | `show bgp ipv4 unicast community no-peer` | supported | **PASS** |
| TC-035 | `show bgp ipv6 unicast community local-as` | supported | **PASS** |
| TC-036 | `show bgp ipv6 unicast community no-advertise` | supported | **PASS** |
| TC-037 | `show bgp ipv6 unicast community no-peer` | supported | **PASS** |
| TC-038 | `show running-configuration bgp as-path-list` | supported | **PASS** |
| TC-039 | `show running-configuration bgp community-list` | supported | **PASS** |
| TC-040 | `show running-configuration bgp extcommunity-list` | supported | **PASS** |
| TC-041 | `show running-configuration bgp vrf default` | supported | **PASS** |
| TC-042 | `show running-configuration bgp neighbor vrf default` | supported | **PASS** |
| TC-043 | `show running-configuration bgp peer-group vrf default` | supported | **PASS** |

---

## Captured output per testcase

### TC-001 — `show bgp summary`  → **PASS**

```
IPv4 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 210
RIB entries 7, using 896 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.24.2       4      65002      3858      4010      210    0    0 00:18:25            0        0 N/A

Total number of neighbors 1
Total number of neighbors established 1

IPv6 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 0
RIB entries 1, using 128 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
2001:db8::2     4      65002       411       434        0    0    0 00:17:54            0        0 N/A

Total number of neighbors 1
Total number of neighbors established 1
```

### TC-002 — `show bgp summary established`  → **PASS**

```
IPv4 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 210
RIB entries 7, using 896 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.24.2       4      65002      3858      4010      210    0    0 00:18:26            0        0 N/A

Displayed neighbors 1
Total number of neighbors 1
Total number of neighbors established 1

IPv6 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 0
RIB entries 1, using 128 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
2001:db8::2     4      65002       411       434        0    0    0 00:17:55            0        0 N/A

Displayed neighbors 1
Total number of neighbors 1
Total number of neighbors established 1
```

### TC-003 — `show bgp summary failed`  → **PASS**

```
IPv4 Unicast Summary:
% No failed BGP neighbors found

IPv6 Unicast Summary:
% No failed BGP neighbors found
```

### TC-004 — `show bgp summary neighbor 10.0.24.2`  → **PASS**

```
IPv4 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 210
RIB entries 7, using 896 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.24.2       4      65002      3858      4010      210    0    0 00:18:28            0        0 N/A

Displayed neighbors 1
Total number of neighbors 1
Total number of neighbors established 1

IPv6 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 0
RIB entries 1, using 128 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

% No matching neighbor
```

### TC-005 — `show bgp summary remote-as 65002`  → **PASS**

```
IPv4 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 210
RIB entries 7, using 896 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.24.2       4      65002      3858      4010      210    0    0 00:18:30            0        0 N/A

Displayed neighbors 1
Total number of neighbors 1
Total number of neighbors established 1

IPv6 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 0
RIB entries 1, using 128 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
2001:db8::2     4      65002       411       434        0    0    0 00:17:59            0        0 N/A

Displayed neighbors 1
Total number of neighbors 1
Total number of neighbors established 1
```

### TC-006 — `show bgp summary vrf default`  → **PASS**

```
IPv4 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 210
RIB entries 7, using 896 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.24.2       4      65002      3858      4010      210    0    0 00:18:31            0        0 N/A

Total number of neighbors 1
Total number of neighbors established 1

IPv6 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 0
RIB entries 1, using 128 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
2001:db8::2     4      65002       412       435        0    0    0 00:18:00            0        0 N/A

Total number of neighbors 1
Total number of neighbors established 1
```

### TC-007 — `show bgp ipv4 unicast summary`  → **PASS**

```
IPv4 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 210
RIB entries 7, using 896 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.24.2       4      65002      3858      4010      210    0    0 00:18:32            0        0 N/A

Total number of neighbors 1
Total number of neighbors established 1
```

### TC-008 — `show bgp ipv6 unicast summary`  → **PASS**

```
IPv6 Unicast Summary:
BGP router identifier 1.1.1.1, local AS number 65001 VRF default vrf-id 0
BGP table version 0
RIB entries 1, using 128 bytes of memory
Peers 1, using 24 KiB of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
2001:db8::2     4      65002       412       435        0    0    0 00:18:01            0        0 N/A

Total number of neighbors 1
Total number of neighbors established 1
```

### TC-009 — `show bgp ipv4 unicast vrf default`  → **PASS**

```
BGP table version is 210, local router ID is 1.1.1.1, vrf id 0
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     10.1.1.0/30      0.0.0.0                  0         32768 i
     100.1.0.0/16     0.0.0.0                  0         32768 i
     100.2.0.0/16     0.0.0.0                  0         32768 i
     100.3.0.0/16     0.0.0.0                  0         32768 i

Displayed 4 routes and 4 total paths
```

### TC-010 — `show bgp route`  → **PASS**

```
<no output / empty result>
```

### TC-011 — `show bgp ipv4 unicast`  → **PASS**

```
BGP table version is 210, local router ID is 1.1.1.1, vrf id 0
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     10.1.1.0/30      0.0.0.0                  0         32768 i
     100.1.0.0/16     0.0.0.0                  0         32768 i
     100.2.0.0/16     0.0.0.0                  0         32768 i
     100.3.0.0/16     0.0.0.0                  0         32768 i

Displayed 4 routes and 4 total paths
```

### TC-012 — `show bgp ipv6 unicast`  → **PASS**

```
BGP table version is 0, local router ID is 1.1.1.1, vrf id 0
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     2001:db8:1::/64  ::                       0         32768 i

Displayed 1 routes and 1 total paths
```

### TC-013 — `show bgp ipv4 unicast community no-export`  → **PASS**

```
<no output / empty result>
```

### TC-014 — `show bgp ipv6 unicast community no-export`  → **PASS**

```
<no output / empty result>
```

### TC-015 — `show bgp ipv4 unicast neighbors`  → **PASS**

```
BGP neighbor is 10.0.24.2, remote AS 65002, local AS 65001, external link
  Local Role: undefined
  Remote Role: undefined
Hostname: sonic
 Member of peer-group SPINE_PEERS for session parameters
  BGP version 4, remote router ID 192.168.100.40, local router ID 1.1.1.1
  BGP state = Established, up for 00:18:38
  Last read 00:00:38, Last write 00:00:38
  Hold time is 180 seconds, keepalive interval is 60 seconds
  Configured hold time is 180 seconds, keepalive interval is 60 seconds
  Configured tcp-mss is 0, synced tcp-mss is 9048
  Configured conditional advertisements interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
    Paths-Limit:
      IPv4 Unicast: advertised (0) and received (0)
    Long-lived Graceful Restart: advertised and received
      Address families by peer:
    Route refresh: advertised and received
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Hostname Capability: advertised (name: sonic,domain name: n/a) received (name: sonic,domain name: n/a)
    Version Capability: not advertised not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast
    End-of-RIB received: IPv4 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    N bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
      Configured LLGR Stale Path Time(sec): 0
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: Yes
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        LLGR Stale Path Time(sec): 0
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                124        117
    Notifications:        120          2
    Updates:              323        258
    Keepalives:          3403       3403
    Route Refresh:         40         78
    Capability:             0          0
    Total:               4010       3858

  Prefix statistics:
    Inbound filtered: 0
    AS-PATH loop: 0
    Originator loop: 0
    Cluster loop: 0
    Invalid next-hop: 0
    Withdrawn: 0
    Attributes discarded: 0

  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  SPINE_PEERS peer-group member
  Update group 128, subgroup 128
  Packet Queue length 0
  Inbound soft reconfiguration allowed
  Community attribute sent to this neighbor(all)
  0 accepted prefixes

  Connections established 112; dropped 111
  Last reset 00:18:40,  No AFI/SAFI activated for peer (n/a)
  Message received that caused BGP to send a NOTIFICATION:
    FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF
    00660104 FDEA00B4 C0A86428 49020601
    04000100 01020202 00020246 00020641
    040000FD EA020206 00020645 04000101
    0102074C 05000101 00000209 49070573
    6F6E6963 00020440 02407802 09470700
    01018000 0000
  External BGP neighbor may be up to 1 hops away.
Local host: 10.0.24.1, Local port: 179
Foreign host: 10.0.24.2, Foreign port: 43078
Nexthop: 10.0.24.1
Nexthop global: 2001:db8::1
Nexthop local: fe80::208b:dbff:feb0:b4f0
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 30
Estimated round trip time: 1 ms
Read thread: on  Write thread: on  FD used: 29

  BFD: Type: single hop
  Detect Multiplier: 3, Min Rx interval: 300, Min Tx interval: 300
  Status: Up, Last update: 0:07:39:57

BGP neighbor is 2001:db8::2, remote AS 65002, local AS 65001, external link
  Local Role: undefined
  Remote Role: undefined
Hostname: sonic
  BGP version 4, remote router ID 192.168.100.40, local router ID 1.1.1.1
  BGP state = Established, up for 00:18:07
  Last read 00:00:07, Last write 00:00:07
  Hold time is 180 seconds, keepalive interval is 60 seconds
  Configured hold time is 180 seconds, keepalive interval is 60 seconds
  Configured tcp-mss is 0, synced tcp-mss is 9028
  Configured conditional advertisements interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv6 Unicast: RX advertised and received
    Paths-Limit:
      IPv6 Unicast: advertised (0) and received (0)
    Long-lived Graceful Restart: advertised and received
      Address families by peer:
    Route refresh: advertised and received
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: sonic,domain name: n/a) received (name: sonic,domain name: n/a)
    Version Capability: not advertised not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv6 Unicast
    End-of-RIB received: IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    N bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
      Configured LLGR Stale Path Time(sec): 0
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: Yes
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        LLGR Stale Path Time(sec): 0
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                 24         24
    Notifications:         26          0
    Updates:               17         17
    Keepalives:           363        363
    Route Refresh:          5          8
    Capability:             0          0
    Total:                435        412

  Prefix statistics:
    Inbound filtered: 0
    AS-PATH loop: 0
    Originator loop: 0
    Cluster loop: 0
    Invalid next-hop: 0
    Withdrawn: 0
    Attributes discarded: 0

  Minimum time between advertisement runs is 0 seconds

 For address family: IPv6 Unicast
  Update group 129, subgroup 129
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  0 accepted prefixes

  Connections established 17; dropped 16
  Last reset 00:18:09,  User reset (n/a)
  Message received that caused BGP to send a NOTIFICATION:
    FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF
    007E0104 FDEA00B4 C0A86428 61020601
    04000100 01020601 04000200 01020202
    00020246 00020641 040000FD EA020206
    00020A45 08000101 01000201 01020C4C
    0A000101 00000002 01000002 09490705
    736F6E69 63000204 40024078 0210470E
    00010180 00000000 02018000 0000
  External BGP neighbor may be up to 1 hops away.
Local host: 2001:db8::1, Local port: 39692
Foreign host: 2001:db8::2, Foreign port: 179
Nexthop: 10.0.24.1
Nexthop global: 2001:db8::1
Nexthop local: fe80::208b:dbff:feb0:b4f0
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 30
Estimated round trip time: 2 ms
Read thread: on  Write thread: on  FD used: 28
```

### TC-016 — `show bgp ipv4 unicast neighbors 10.0.24.2`  → **PASS**

```
BGP neighbor is 10.0.24.2, remote AS 65002, local AS 65001, external link
  Local Role: undefined
  Remote Role: undefined
Hostname: sonic
 Member of peer-group SPINE_PEERS for session parameters
  BGP version 4, remote router ID 192.168.100.40, local router ID 1.1.1.1
  BGP state = Established, up for 00:18:39
  Last read 00:00:39, Last write 00:00:39
  Hold time is 180 seconds, keepalive interval is 60 seconds
  Configured hold time is 180 seconds, keepalive interval is 60 seconds
  Configured tcp-mss is 0, synced tcp-mss is 9048
  Configured conditional advertisements interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
    Paths-Limit:
      IPv4 Unicast: advertised (0) and received (0)
    Long-lived Graceful Restart: advertised and received
      Address families by peer:
    Route refresh: advertised and received
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Hostname Capability: advertised (name: sonic,domain name: n/a) received (name: sonic,domain name: n/a)
    Version Capability: not advertised not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast
    End-of-RIB received: IPv4 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    N bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
      Configured LLGR Stale Path Time(sec): 0
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: Yes
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        LLGR Stale Path Time(sec): 0
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                124        117
    Notifications:        120          2
    Updates:              323        258
    Keepalives:          3403       3403
    Route Refresh:         40         78
    Capability:             0          0
    Total:               4010       3858

  Prefix statistics:
    Inbound filtered: 0
    AS-PATH loop: 0
    Originator loop: 0
    Cluster loop: 0
    Invalid next-hop: 0
    Withdrawn: 0
    Attributes discarded: 0

  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  SPINE_PEERS peer-group member
  Update group 128, subgroup 128
  Packet Queue length 0
  Inbound soft reconfiguration allowed
  Community attribute sent to this neighbor(all)
  0 accepted prefixes

  Connections established 112; dropped 111
  Last reset 00:18:41,  No AFI/SAFI activated for peer (n/a)
  Message received that caused BGP to send a NOTIFICATION:
    FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF
    00660104 FDEA00B4 C0A86428 49020601
    04000100 01020202 00020246 00020641
    040000FD EA020206 00020645 04000101
    0102074C 05000101 00000209 49070573
    6F6E6963 00020440 02407802 09470700
    01018000 0000
  External BGP neighbor may be up to 1 hops away.
Local host: 10.0.24.1, Local port: 179
Foreign host: 10.0.24.2, Foreign port: 43078
Nexthop: 10.0.24.1
Nexthop global: 2001:db8::1
Nexthop local: fe80::208b:dbff:feb0:b4f0
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 30
Estimated round trip time: 1 ms
Read thread: on  Write thread: on  FD used: 29

  BFD: Type: single hop
  Detect Multiplier: 3, Min Rx interval: 300, Min Tx interval: 300
  Status: Up, Last update: 0:07:39:58
```

### TC-017 — `show bgp ipv4 unicast neighbors interface Ethernet32`  → **PASS**

```
% No such neighbor in this view/vrf
```

### TC-018 — `show bgp ipv6 unicast neighbors`  → **PASS**

```
BGP neighbor is 2001:db8::2, remote AS 65002, local AS 65001, external link
  Local Role: undefined
  Remote Role: undefined
Hostname: sonic
  BGP version 4, remote router ID 192.168.100.40, local router ID 1.1.1.1
  BGP state = Established, up for 00:18:10
  Last read 00:00:10, Last write 00:00:10
  Hold time is 180 seconds, keepalive interval is 60 seconds
  Configured hold time is 180 seconds, keepalive interval is 60 seconds
  Configured tcp-mss is 0, synced tcp-mss is 9028
  Configured conditional advertisements interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv6 Unicast: RX advertised and received
    Paths-Limit:
      IPv6 Unicast: advertised (0) and received (0)
    Long-lived Graceful Restart: advertised and received
      Address families by peer:
    Route refresh: advertised and received
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: sonic,domain name: n/a) received (name: sonic,domain name: n/a)
    Version Capability: not advertised not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv6 Unicast
    End-of-RIB received: IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    N bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
      Configured LLGR Stale Path Time(sec): 0
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: Yes
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        LLGR Stale Path Time(sec): 0
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                 24         24
    Notifications:         26          0
    Updates:               17         17
    Keepalives:           363        363
    Route Refresh:          5          8
    Capability:             0          0
    Total:                435        412

  Prefix statistics:
    Inbound filtered: 0
    AS-PATH loop: 0
    Originator loop: 0
    Cluster loop: 0
    Invalid next-hop: 0
    Withdrawn: 0
    Attributes discarded: 0

  Minimum time between advertisement runs is 0 seconds

 For address family: IPv6 Unicast
  Update group 129, subgroup 129
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  0 accepted prefixes

  Connections established 17; dropped 16
  Last reset 00:18:12,  User reset (n/a)
  Message received that caused BGP to send a NOTIFICATION:
    FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF
    007E0104 FDEA00B4 C0A86428 61020601
    04000100 01020601 04000200 01020202
    00020246 00020641 040000FD EA020206
    00020A45 08000101 01000201 01020C4C
    0A000101 00000002 01000002 09490705
    736F6E69 63000204 40024078 0210470E
    00010180 00000000 02018000 0000
  External BGP neighbor may be up to 1 hops away.
Local host: 2001:db8::1, Local port: 39692
Foreign host: 2001:db8::2, Foreign port: 179
Nexthop: 10.0.24.1
Nexthop global: 2001:db8::1
Nexthop local: fe80::208b:dbff:feb0:b4f0
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 30
Estimated round trip time: 2 ms
Read thread: on  Write thread: on  FD used: 28
```

### TC-019 — `show bgp ipv6 unicast neighbors 2001:db8::2`  → **PASS**

```
BGP neighbor is 2001:db8::2, remote AS 65002, local AS 65001, external link
  Local Role: undefined
  Remote Role: undefined
Hostname: sonic
  BGP version 4, remote router ID 192.168.100.40, local router ID 1.1.1.1
  BGP state = Established, up for 00:18:10
  Last read 00:00:10, Last write 00:00:10
  Hold time is 180 seconds, keepalive interval is 60 seconds
  Configured hold time is 180 seconds, keepalive interval is 60 seconds
  Configured tcp-mss is 0, synced tcp-mss is 9028
  Configured conditional advertisements interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv6 Unicast: RX advertised and received
    Paths-Limit:
      IPv6 Unicast: advertised (0) and received (0)
    Long-lived Graceful Restart: advertised and received
      Address families by peer:
    Route refresh: advertised and received
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: sonic,domain name: n/a) received (name: sonic,domain name: n/a)
    Version Capability: not advertised not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv6 Unicast
    End-of-RIB received: IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    N bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
      Configured LLGR Stale Path Time(sec): 0
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: Yes
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        LLGR Stale Path Time(sec): 0
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                 24         24
    Notifications:         26          0
    Updates:               17         17
    Keepalives:           363        363
    Route Refresh:          5          8
    Capability:             0          0
    Total:                435        412

  Prefix statistics:
    Inbound filtered: 0
    AS-PATH loop: 0
    Originator loop: 0
    Cluster loop: 0
    Invalid next-hop: 0
    Withdrawn: 0
    Attributes discarded: 0

  Minimum time between advertisement runs is 0 seconds

 For address family: IPv6 Unicast
  Update group 129, subgroup 129
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  0 accepted prefixes

  Connections established 17; dropped 16
  Last reset 00:18:12,  User reset (n/a)
  Message received that caused BGP to send a NOTIFICATION:
    FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF
    007E0104 FDEA00B4 C0A86428 61020601
    04000100 01020601 04000200 01020202
    00020246 00020641 040000FD EA020206
    00020A45 08000101 01000201 01020C4C
    0A000101 00000002 01000002 09490705
    736F6E69 63000204 40024078 0210470E
    00010180 00000000 02018000 0000
  External BGP neighbor may be up to 1 hops away.
Local host: 2001:db8::1, Local port: 39692
Foreign host: 2001:db8::2, Foreign port: 179
Nexthop: 10.0.24.1
Nexthop global: 2001:db8::1
Nexthop local: fe80::208b:dbff:feb0:b4f0
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 30
Estimated round trip time: 2 ms
Read thread: on  Write thread: on  FD used: 28
```

### TC-020 — `show bgp ipv6 unicast neighbors interface Ethernet32`  → **PASS**

```
% No such neighbor in this view/vrf
```

### TC-021 — `show bgp all neighbors`  → **PASS**

```
BGP neighbor is 10.0.24.2, remote AS 65002, local AS 65001, external link
  Local Role: undefined
  Remote Role: undefined
Hostname: sonic
 Member of peer-group SPINE_PEERS for session parameters
  BGP version 4, remote router ID 192.168.100.40, local router ID 1.1.1.1
  BGP state = Established, up for 00:18:43
  Last read 00:00:43, Last write 00:00:43
  Hold time is 180 seconds, keepalive interval is 60 seconds
  Configured hold time is 180 seconds, keepalive interval is 60 seconds
  Configured tcp-mss is 0, synced tcp-mss is 9048
  Configured conditional advertisements interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
    Paths-Limit:
      IPv4 Unicast: advertised (0) and received (0)
    Long-lived Graceful Restart: advertised and received
      Address families by peer:
    Route refresh: advertised and received
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Hostname Capability: advertised (name: sonic,domain name: n/a) received (name: sonic,domain name: n/a)
    Version Capability: not advertised not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast
    End-of-RIB received: IPv4 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    N bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
      Configured LLGR Stale Path Time(sec): 0
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: Yes
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        LLGR Stale Path Time(sec): 0
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                124        117
    Notifications:        120          2
    Updates:              323        258
    Keepalives:          3403       3403
    Route Refresh:         40         78
    Capability:             0          0
    Total:               4010       3858

  Prefix statistics:
    Inbound filtered: 0
    AS-PATH loop: 0
    Originator loop: 0
    Cluster loop: 0
    Invalid next-hop: 0
    Withdrawn: 0
    Attributes discarded: 0

  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  SPINE_PEERS peer-group member
  Update group 128, subgroup 128
  Packet Queue length 0
  Inbound soft reconfiguration allowed
  Community attribute sent to this neighbor(all)
  0 accepted prefixes

  Connections established 112; dropped 111
  Last reset 00:18:45,  No AFI/SAFI activated for peer (n/a)
  Message received that caused BGP to send a NOTIFICATION:
    FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF
    00660104 FDEA00B4 C0A86428 49020601
    04000100 01020202 00020246 00020641
    040000FD EA020206 00020645 04000101
    0102074C 05000101 00000209 49070573
    6F6E6963 00020440 02407802 09470700
    01018000 0000
  External BGP neighbor may be up to 1 hops away.
Local host: 10.0.24.1, Local port: 179
Foreign host: 10.0.24.2, Foreign port: 43078
Nexthop: 10.0.24.1
Nexthop global: 2001:db8::1
Nexthop local: fe80::208b:dbff:feb0:b4f0
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 30
Estimated round trip time: 1 ms
Read thread: on  Write thread: on  FD used: 29

  BFD: Type: single hop
  Detect Multiplier: 3, Min Rx interval: 300, Min Tx interval: 300
  Status: Up, Last update: 0:07:40:02

BGP neighbor is 2001:db8::2, remote AS 65002, local AS 65001, external link
  Local Role: undefined
  Remote Role: undefined
Hostname: sonic
  BGP version 4, remote router ID 192.168.100.40, local router ID 1.1.1.1
  BGP state = Established, up for 00:18:12
  Last read 00:00:12, Last write 00:00:12
  Hold time is 180 seconds, keepalive interval is 60 seconds
  Configured hold time is 180 seconds, keepalive interval is 60 seconds
  Configured tcp-mss is 0, synced tcp-mss is 9028
  Configured conditional advertisements interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv6 Unicast: RX advertised and received
    Paths-Limit:
      IPv6 Unicast: advertised (0) and received (0)
    Long-lived Graceful Restart: advertised and received
      Address families by peer:
    Route refresh: advertised and received
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: sonic,domain name: n/a) received (name: sonic,domain name: n/a)
    Version Capability: not advertised not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv6 Unicast
    End-of-RIB received: IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    N bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
      Configured LLGR Stale Path Time(sec): 0
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: Yes
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        LLGR Stale Path Time(sec): 0
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                 24         24
    Notifications:         26          0
    Updates:               17         17
    Keepalives:           363        363
    Route Refresh:          5          8
    Capability:             0          0
    Total:                435        412

  Prefix statistics:
    Inbound filtered: 0
    AS-PATH loop: 0
    Originator loop: 0
    Cluster loop: 0
    Invalid next-hop: 0
    Withdrawn: 0
    Attributes discarded: 0

  Minimum time between advertisement runs is 0 seconds

 For address family: IPv6 Unicast
  Update group 129, subgroup 129
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  0 accepted prefixes

  Connections established 17; dropped 16
  Last reset 00:18:14,  User reset (n/a)
  Message received that caused BGP to send a NOTIFICATION:
    FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF
    007E0104 FDEA00B4 C0A86428 61020601
    04000100 01020601 04000200 01020202
    00020246 00020641 040000FD EA020206
    00020A45 08000101 01000201 01020C4C
    0A000101 00000002 01000002 09490705
    736F6E69 63000204 40024078 0210470E
    00010180 00000000 02018000 0000
  External BGP neighbor may be up to 1 hops away.
Local host: 2001:db8::1, Local port: 39692
Foreign host: 2001:db8::2, Foreign port: 179
Nexthop: 10.0.24.1
Nexthop global: 2001:db8::1
Nexthop local: fe80::208b:dbff:feb0:b4f0
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 30
Estimated round trip time: 2 ms
Read thread: on  Write thread: on  FD used: 28
```

### TC-022 — `show bgp ipv4 unicast route-map SET_COMMUNITY`  → **PASS**

```
BGP table version is 210, local router ID is 1.1.1.1, vrf id 0
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     10.1.1.0/30      0.0.0.0                  0         32768 i
     100.1.0.0/16     0.0.0.0                  0         32768 i
     100.2.0.0/16     0.0.0.0                  0         32768 i
     100.3.0.0/16     0.0.0.0                  0         32768 i

Displayed 4 routes and 4 total paths
```

### TC-023 — `show bgp ipv4 unicast statistics`  → **PASS**

```
BGP IPv4 Unicast RIB statistics (VRF default)
Total Advertisements          :            4
Total Prefixes                :            4
Average prefix length         :        19.50
Unaggregateable prefixes      :            4
Maximum aggregateable prefixes:            0
BGP Aggregate advertisements  :            0
Address space advertised      :       196612
                  % announced :         0.00
                /8 equivalent :         0.01
               /24 equivalent :       768.02

Advertisements with paths     :            4
Longest AS-Path (hops)        :            0
Average AS-Path length (hops) :         0.00
Largest AS-Path (bytes)       :            0
Average AS-Path size (bytes)  :         0.00
Highest public ASN            :            0
Redistributed routes          :            0
Local aggregates              :            0
```

### TC-024 — `show bgp ipv6 unicast route-map SET_COMMUNITY`  → **PASS**

```
BGP table version is 0, local router ID is 1.1.1.1, vrf id 0
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     2001:db8:1::/64  ::                       0         32768 i

Displayed 1 routes and 1 total paths
```

### TC-025 — `show bgp ipv6 unicast statistics`  → **PASS**

```
BGP IPv6 Unicast RIB statistics (VRF default)
Total Advertisements          :            1
Total Prefixes                :            1
Average prefix length         :        64.00
Unaggregateable prefixes      :            1
Maximum aggregateable prefixes:            0
BGP Aggregate advertisements  :            0
Address space advertised      :  1.84467e+19
            /32 equivalent %s
:  2.32831e-10
            /48 equivalent %s
:  1.52588e-05

Advertisements with paths     :            1
Longest AS-Path (hops)        :            0
Average AS-Path length (hops) :         0.00
Largest AS-Path (bytes)       :            0
Average AS-Path size (bytes)  :         0.00
Highest public ASN            :            0
Redistributed routes          :            0
Local aggregates              :            0
```

### TC-026 — `show bgp ipv4 unicast vrf all`  → **PASS**

```
Instance default:
BGP table version is 210, local router ID is 1.1.1.1, vrf id 0
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     10.1.1.0/30      0.0.0.0                  0         32768 i
     100.1.0.0/16     0.0.0.0                  0         32768 i
     100.2.0.0/16     0.0.0.0                  0         32768 i
     100.3.0.0/16     0.0.0.0                  0         32768 i

Displayed 4 routes and 4 total paths

Instance Vrf-RED:
BGP table version is 0, local router ID is 10.100.1.1, vrf id -
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     10.100.0.0/16    0.0.0.0                  0         32768 i

Displayed 1 routes and 1 total paths

Instance Vrf-BLUE:
No BGP prefixes displayed, 0 exist
```

### TC-027 — `show bgp ipv6 unicast vrf all`  → **PASS**

```
Instance default:
BGP table version is 0, local router ID is 1.1.1.1, vrf id 0
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     2001:db8:1::/64  ::                       0         32768 i

Displayed 1 routes and 1 total paths

Instance Vrf-RED:
No BGP prefixes displayed, 0 exist

Instance Vrf-BLUE:
BGP table version is 0, local router ID is 10.200.1.1, vrf id -
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     2001:100::/32    ::                       0         32768 i

Displayed 1 routes and 1 total paths
```

### TC-028 — `show bgp ipv6 unicast vrf default`  → **PASS**

```
BGP table version is 0, local router ID is 1.1.1.1, vrf id 0
Default local pref 100, local AS 65001
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
     2001:db8:1::/64  ::                       0         32768 i

Displayed 1 routes and 1 total paths
```

### TC-029 — `show bgp all peer-group`  → **PASS**

```
BGP peer-group SPINE_PEERS, remote AS 65002
  Peer-group type is external
  Configured address-families: IPv4 Unicast;
  Peer-group members:
    10.0.24.2  Established
```

### TC-030 — `show bgp l2vpn evpn`  → **PASS**

```
No prefixes displayed, 0 exist
```

### TC-031 — `show running-configuration bgp`  → **PASS**

```
!
router bgp 65001
 router-id 1.1.1.1
 address-family ipv4 unicast
 exit
 address-family ipv6 unicast
  network 2001:db8:1::/64
 exit
 neighbor 10.0.24.2 remote-as 65002
  bfd
  address-family ipv4 unicast
   activate
  exit
 neighbor 2001:db8::2 remote-as 65002
  address-family ipv6 unicast
   activate
  exit
!
```

### TC-032 — `show bgp ipv4 unicast community local-as`  → **PASS**

```
<no output / empty result>
```

### TC-033 — `show bgp ipv4 unicast community no-advertise`  → **PASS**

```
<no output / empty result>
```

### TC-034 — `show bgp ipv4 unicast community no-peer`  → **PASS**

```
<no output / empty result>
```

### TC-035 — `show bgp ipv6 unicast community local-as`  → **PASS**

```
<no output / empty result>
```

### TC-036 — `show bgp ipv6 unicast community no-advertise`  → **PASS**

```
<no output / empty result>
```

### TC-037 — `show bgp ipv6 unicast community no-peer`  → **PASS**

```
<no output / empty result>
```

### TC-038 — `show running-configuration bgp as-path-list`  → **PASS**

```
<no output / empty result>
```

### TC-039 — `show running-configuration bgp community-list`  → **PASS**

```
<no output / empty result>
```

### TC-040 — `show running-configuration bgp extcommunity-list`  → **PASS**

```
<no output / empty result>
```

### TC-041 — `show running-configuration bgp vrf default`  → **PASS**

```
!
router bgp 65001
 router-id 1.1.1.1
 address-family ipv4 unicast
 exit
 address-family ipv6 unicast
  network 2001:db8:1::/64
 exit
 neighbor 10.0.24.2 remote-as 65002
  bfd
  address-family ipv4 unicast
   activate
  exit
 neighbor 2001:db8::2 remote-as 65002
  address-family ipv6 unicast
   activate
  exit
!
```

### TC-042 — `show running-configuration bgp neighbor vrf default`  → **PASS**

```
!
router bgp 65001
 router-id 1.1.1.1
 address-family ipv4 unicast
 exit
 address-family ipv6 unicast
  network 2001:db8:1::/64
 exit
 neighbor 10.0.24.2 remote-as 65002
  bfd
  address-family ipv4 unicast
   activate
  exit
 neighbor 2001:db8::2 remote-as 65002
  address-family ipv6 unicast
   activate
  exit
!
```

### TC-043 — `show running-configuration bgp peer-group vrf default`  → **PASS**

```
<no output / empty result>
```
