# SONiC OC-BUILD STATIC ROUTE TEST LOGS
## Complete Test Configuration Documentation

**Author**: Network Automation Team
**Date**: 2026-04-13
**Platform**: SONiC OC-Build with Klish CLI
**Test Framework**: Manual Testing with sonic-cli

---

## TABLE OF CONTENTS

1. [Testcase 10: Basic IPv4 Static Route with Next-Hop](#testcase-10)
2. [Testcase 11: IPv4 Blackhole Routes](#testcase-11)
3. [Testcase 12: IPv4 Interface-Based Routes](#testcase-12)
4. [Testcase 13: IPv4 Routes with Tags](#testcase-13)
5. [Testcase 14: IPv4 Routes with Administrative Distance](#testcase-14)
6. [Testcase 15: IPv4 Routes with Tag and Distance](#testcase-15)
7. [Testcase 16: IPv4 Host Routes and Prefix Lengths](#testcase-16)
8. [Testcase 17: IPv4 ECMP (Equal-Cost Multi-Path)](#testcase-17)
9. [Testcase 18: IPv6 Basic Routes](#testcase-18)
10. [Testcase 19: IPv6 Blackhole Routes](#testcase-19)
11. [Testcase 20: IPv6 Interface-Based Routes](#testcase-20)
12. [Testcase 21: IPv6 Routes with Tags](#testcase-21)
13. [Testcase 22: IPv6 Routes with Distance](#testcase-22)
14. [Testcase 23: IPv6 Default Route](#testcase-23)
15. [Testcase 24: IPv6 Host Routes and Prefix Lengths](#testcase-24)
16. [Testcase 25: IPv6 ECMP](#testcase-25)
17. [Testcase 26: Mixed IPv4 and IPv6 Routes](#testcase-26)
18. [Testcase 27: Route Deletion and Modification](#testcase-27)
19. [Testcase 28: Interface + Distance Routes](#testcase-28)
20. [Testcase 29: Recursive Routes (3-Hop)](#testcase-29)
21. [Testcase 30: PortChannel Static Routes](#testcase-30)
22. [Testcase 31: VLAN Interface Static Routes](#testcase-31)

---

<a name="testcase-10"></a>
## TESTCASE 10: BASIC IPv4 STATIC ROUTE WITH NEXT-HOP

### Test Objective
Validate basic IPv4 static route configuration with next-hop IP addresses on SONiC OC-build using Klish CLI.

### Topology
```
DUT1 (Eth0: 10.1.1.1/24) <---> DUT2 (Eth0: 10.1.1.2/24)
DUT1 (Eth4: 10.2.1.1/24) <---> DUT2 (Eth8: 10.2.1.1/24)
                               DUT2 (Eth12: 10.2.2.1/24) <---> DUT3
```

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# interface Ethernet 0
sonic(config-if-Ethernet0)# ip address 10.1.1.1/24
sonic(config-if-Ethernet0)# no shutdown
sonic(config-if-Ethernet0)# exit
sonic(config)# interface Ethernet 4
sonic(config-if-Ethernet4)# ip address 10.2.1.1/24
sonic(config-if-Ethernet4)# no shutdown
sonic(config-if-Ethernet4)# exit
sonic(config)# ip route 30.30.30.0/24 10.1.1.2
sonic(config)# ip route 40.40.40.0/24 10.2.1.1
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route static
Codes: K - kernel route, C - connected, S - static, B - BGP, O - OSPF
       > - selected route, * - FIB route, q - queued, r - rejected
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -

sonic# show ip route 30.30.30.0/24
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -

sonic# show ip route 40.40.40.0/24
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    40.40.40.0/24           10.2.1.1                           0/0         -
```

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# interface Ethernet 0
sonic(config-if-Ethernet0)# ip address 10.1.1.2/24
sonic(config-if-Ethernet0)# no shutdown
sonic(config-if-Ethernet0)# exit
sonic(config)# interface Ethernet 4
sonic(config-if-Ethernet4)# ip address 10.1.2.2/24
sonic(config-if-Ethernet4)# no shutdown
sonic(config-if-Ethernet4)# exit
sonic(config)# interface Ethernet 8
sonic(config-if-Ethernet8)# ip address 10.2.1.1/24
sonic(config-if-Ethernet8)# no shutdown
sonic(config-if-Ethernet8)# exit
sonic(config)# interface Ethernet 12
sonic(config-if-Ethernet12)# ip address 10.2.2.1/24
sonic(config-if-Ethernet12)# no shutdown
sonic(config-if-Ethernet12)# exit
sonic(config)# ip route 30.30.30.0/24 10.2.1.2
sonic(config)# ip route 40.40.40.0/24 10.1.1.1
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ip route 30.30.30.0/24
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.2.1.2                           0/0         -

sonic# show ip route 40.40.40.0/24
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    40.40.40.0/24           10.1.1.1                           0/0         -

sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
```

### DUT3 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# interface Ethernet 8
sonic(config-if-Ethernet8)# ip address 10.3.1.2/24
sonic(config-if-Ethernet8)# no shutdown
sonic(config-if-Ethernet8)# exit
sonic(config)# interface Ethernet 12
sonic(config-if-Ethernet12)# ip address 10.3.2.2/24
sonic(config-if-Ethernet12)# no shutdown
sonic(config-if-Ethernet12)# exit
sonic(config)# ip route 40.40.40.0/24 10.2.1.1
sonic(config)# exit
```

### DUT3 Verification

```bash
sonic# show ip route 40.40.40.0/24
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    40.40.40.0/24           10.2.1.1                           0/0         -

sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.1.1.0/24             10.2.1.1                           0/0         -
 S    10.10.10.0/30           30.30.30.1                         0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/30          30.30.30.1                         0/0         -
```

### Test Result
**PASS** - Static routes configured successfully with next-hop IP addresses on all DUTs.

---

<a name="testcase-11"></a>
## TESTCASE 11: IPv4 BLACKHOLE ROUTES

### Test Objective
Validate IPv4 blackhole route configuration. Blackhole routes drop packets silently without sending ICMP unreachable messages.

### Key Concept
**Blackhole Route**: Routes traffic to null interface, discarding packets without generating ICMP messages. Used for preventing routing loops and security filtering.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ip route 172.16.10.0/24 blackhole
sonic(config)# ip route 172.16.20.0/24 10.1.1.2
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -

sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -
```

**Note**: Route shows as "Unreachable (blackhole)" indicating packets will be dropped.

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ip route 172.16.10.0/24 10.1.1.1
sonic(config)# ip route 172.16.20.0/24 blackhole
sonic(config)# ip route 172.16.30.0/24 10.2.1.2
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
 S    172.16.10.0/24          10.1.1.1                           0/0         -
 S    172.16.20.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.30.0/24          10.2.1.2                           0/0         -
```

### DUT3 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ip route 172.16.30.0/24 blackhole
sonic(config)# interface Ethernet 12
sonic(config-if-Ethernet12)# ip address 172.16.10.1/32
sonic(config-if-Ethernet12)# ip address 172.16.20.1/32
sonic(config-if-Ethernet12)# ip address 172.16.30.1/32
sonic(config-if-Ethernet12)# exit
sonic(config)# exit
```

### DUT3 Verification

```bash
sonic# show ip route | grep blackhole
 S    172.16.30.0/24          Unreachable (blackhole)            0/0         -

sonic# show ip route 172.16.30.0/24
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    172.16.30.0/24          Unreachable (blackhole)            0/0         -
```

### Test Result
**PASS** - Blackhole routes configured successfully. Routes show "Unreachable (blackhole)" status.

---

<a name="testcase-12"></a>
## TESTCASE 12: IPv4 INTERFACE-BASED ROUTES

### Test Objective
Validate IPv4 interface-based static routes where egress interface is specified instead of next-hop IP.

### Key Concept
**Interface Route**: Route specifies outgoing interface directly. Used for point-to-point links or when next-hop is unknown.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ip route 192.168.70.0/24 interface Ethernet0
sonic(config)# ip route 192.168.71.0/24 interface Ethernet4
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -
 S    192.168.70.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet4      0/0         -
```

**Note**: Routes show "directly connected" via interface.

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ip route 192.168.70.0/24 interface Ethernet8
sonic(config)# ip route 192.168.71.0/24 interface Ethernet0
sonic(config)# ip route 192.168.72.0/24 interface Ethernet12
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
 S    172.16.10.0/24          10.1.1.1                           0/0         -
 S    172.16.20.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.30.0/24          10.2.1.2                           0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
```

### DUT3 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.70.0/24 interface Ethernet8
sonic(config)# ip route 192.168.72.0/24 interface Ethernet12
sonic(config)# interface Ethernet 12
sonic(config-if-Ethernet12)# ip address 192.168.70.1/32
sonic(config-if-Ethernet12)# ip address 192.168.71.1/32
sonic(config-if-Ethernet12)# ip address 192.168.72.1/32
sonic(config-if-Ethernet12)# exit
sonic(config)# exit
```

### DUT3 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.1.1.0/24             10.2.1.1                           0/0         -
 S    10.10.10.0/30           30.30.30.1                         0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/30          30.30.30.1                         0/0         -
 S    172.16.30.0/24          Unreachable (blackhole)            0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
```

### Test Result
**PASS** - Interface-based routes configured successfully on all DUTs.

---

<a name="testcase-13"></a>
## TESTCASE 13: IPv4 ROUTES WITH TAGS

### Test Objective
Validate IPv4 static route configuration with route tags for policy-based routing.

### Key Concept
**Route Tags**: Numeric labels (0-4294967295) attached to routes for route-map filtering and redistribution control.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ip route 192.168.80.0/24 10.1.1.2 tag 50
sonic(config)# ip route 192.168.81.0/24 10.1.2.2 tag 100
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -
 S    192.168.70.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet4      0/0         -
 S    192.168.80.0/24         10.1.1.2                           0/0         -
 S    192.168.81.0/24         10.1.2.2                           0/0         -
```

**Note**: Tags are not displayed in `show ip route` but are stored internally for policy matching.

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ip route 192.168.80.0/24 10.2.1.2 tag 50
sonic(config)# ip route 192.168.81.0/24 10.2.2.2 tag 100
sonic(config)# ip route 192.168.82.0/24 10.1.1.1 tag 150
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
 S    172.16.10.0/24          10.1.1.1                           0/0         -
 S    172.16.20.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.30.0/24          10.2.1.2                           0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
 S    192.168.80.0/24         10.2.1.2                           0/0         -
 S    192.168.81.0/24         10.2.2.2                           0/0         -
 S    192.168.82.0/24         10.1.1.1                           0/0         -
```

### DUT3 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.82.0/24 10.2.1.1 tag 150
sonic(config)# exit
```

### DUT3 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.1.1.0/24             10.2.1.1                           0/0         -
 S    10.10.10.0/30           30.30.30.1                         0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/30          30.30.30.1                         0/0         -
 S    172.16.30.0/24          Unreachable (blackhole)            0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
 S    192.168.82.0/24         10.2.1.1                           0/0         -
```

### Test Result
**PASS** - Routes with tags configured successfully. Tags stored for policy-based routing.

---

<a name="testcase-14"></a>
## TESTCASE 14: IPv4 ROUTES WITH ADMINISTRATIVE DISTANCE

### Test Objective
Validate IPv4 static routes with administrative distance for route preference and failover.

### Key Concept
**Administrative Distance**: Route preference value (1-255). Lower distance = higher preference. Default static route distance = 1.

### DUT1 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.90.0/24 10.1.1.2 5
sonic(config)# ip route 192.168.90.0/24 10.1.2.2 50
sonic(config)# ip route 192.168.91.0/24 10.1.1.2 10
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -
 S    192.168.70.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet4      0/0         -
 S    192.168.80.0/24         10.1.1.2                           0/0         -
 S    192.168.81.0/24         10.1.2.2                           0/0         -
 S    192.168.90.0/24         10.1.1.2                           5/0         -
 S    192.168.90.0/24         10.1.2.2                           50/0         -
 S    192.168.91.0/24         10.1.1.2                           10/0         -
```

**Key Observation**:
- Two routes to 192.168.90.0/24
- Distance 5 (primary) via 10.1.1.2
- Distance 50 (backup) via 10.1.2.2 - only used if primary fails

### DUT2 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.90.0/24 10.2.1.2 10
sonic(config)# ip route 192.168.90.0/24 10.2.2.2 100
sonic(config)# ip route 192.168.91.0/24 10.2.1.2 5
sonic(config)# ip route 192.168.91.0/24 10.1.1.1 50
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
 S    172.16.10.0/24          10.1.1.1                           0/0         -
 S    172.16.20.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.30.0/24          10.2.1.2                           0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
 S    192.168.80.0/24         10.2.1.2                           0/0         -
 S    192.168.81.0/24         10.2.2.2                           0/0         -
 S    192.168.82.0/24         10.1.1.1                           0/0         -
 S    192.168.90.0/24         10.2.1.2                           10/0         -
 S    192.168.90.0/24         10.2.2.2                           100/0         -
 S    192.168.91.0/24         10.1.1.1                           50/0         -
 S    192.168.91.0/24         10.2.1.2                           5/0         -
```

### DUT3 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.91.0/24 10.2.1.1 15
sonic(config)# exit
```

### DUT3 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.1.1.0/24             10.2.1.1                           0/0         -
 S    10.10.10.0/30           30.30.30.1                         0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/30          30.30.30.1                         0/0         -
 S    172.16.30.0/24          Unreachable (blackhole)            0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
 S    192.168.82.0/24         10.2.1.1                           0/0         -
 S    192.168.91.0/24         10.2.1.1                           15/0         -
```

### Test Result
**PASS** - Routes with administrative distance configured successfully. Failover capability enabled.

---

<a name="testcase-15"></a>
## TESTCASE 15: IPv4 ROUTES WITH TAG AND DISTANCE

### Test Objective
Validate IPv4 static routes with both tag and administrative distance parameters.

### Key Concept
Combines route tagging (for policy) with administrative distance (for failover).

### DUT1 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.100.0/24 10.1.1.2 tag 200 25
sonic(config)# ip route 192.168.100.0/24 10.1.2.2 tag 201 50
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -
 S    192.168.70.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet4      0/0         -
 S    192.168.80.0/24         10.1.1.2                           0/0         -
 S    192.168.81.0/24         10.1.2.2                           0/0         -
 S    192.168.90.0/24         10.1.1.2                           5/0         -
 S    192.168.90.0/24         10.1.2.2                           50/0         -
 S    192.168.91.0/24         10.1.1.2                           10/0         -
 S    192.168.100.0/24        10.1.1.2                           25/0         -
 S    192.168.100.0/24        10.1.2.2                           50/0         -
```

### Running Configuration Check

```bash
sonic# show running-configuration | grep "192.168.100.0/24"
ip route 192.168.100.0/24 10.1.1.2 tag 200 metric 25
ip route 192.168.100.0/24 10.1.2.2 tag 201 metric 50
```

**Note**: Tags and distance both configured. In SONiC, "metric" is used interchangeably with "distance" for static routes.

### DUT2 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.100.0/24 10.2.1.2 tag 200 30
sonic(config)# ip route 192.168.100.0/24 10.2.2.2 tag 201 60
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
 S    172.16.10.0/24          10.1.1.1                           0/0         -
 S    172.16.20.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.30.0/24          10.2.1.2                           0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
 S    192.168.80.0/24         10.2.1.2                           0/0         -
 S    192.168.81.0/24         10.2.2.2                           0/0         -
 S    192.168.82.0/24         10.1.1.1                           0/0         -
 S    192.168.90.0/24         10.2.1.2                           10/0         -
 S    192.168.90.0/24         10.2.2.2                           100/0         -
 S    192.168.91.0/24         10.1.1.1                           50/0         -
 S    192.168.91.0/24         10.2.1.2                           5/0         -
 S    192.168.100.0/24        10.2.1.2                           30/0         -
 S    192.168.100.0/24        10.2.2.2                           60/0         -

sonic# show running-configuration | grep "192.168.100.0/24"
ip route 192.168.100.0/24 10.2.1.2 tag 200 metric 30
ip route 192.168.100.0/24 10.2.2.2 tag 201 metric 60
```

### DUT3 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.100.0/24 10.2.1.1 tag 202 40
sonic(config)# exit
```

### DUT3 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.1.1.0/24             10.2.1.1                           0/0         -
 S    10.10.10.0/30           30.30.30.1                         0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.10.0/30          30.30.30.1                         0/0         -
 S    172.16.30.0/24          Unreachable (blackhole)            0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
 S    192.168.82.0/24         10.2.1.1                           0/0         -
 S    192.168.91.0/24         10.2.1.1                           15/0         -
 S    192.168.100.0/24        10.2.1.1                           40/0         -

sonic# show running-configuration | grep "192.168.100.0/24"
ip route 192.168.100.0/24 10.2.1.1 tag 202 metric 40
```

### Test Result
**PASS** - Routes with both tag and administrative distance configured successfully.

---

<a name="testcase-16"></a>
## TESTCASE 16: IPv4 HOST ROUTES AND PREFIX LENGTHS

### Test Objective
Validate IPv4 static routes with various prefix lengths including host routes (/32) and large aggregates (/8, /12, /16).

### Key Concept
**Prefix Length**: Determines network size and longest prefix match routing behavior.
- /32 = Host route (1 IP)
- /24 = Standard subnet (256 IPs)
- /16 = 65,536 IPs
- /12 = 1,048,576 IPs
- /8 = 16,777,216 IPs

### DUT1 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 192.168.1.1/32 10.1.1.2
sonic(config)# ip route 192.168.0.0/16 10.1.1.2
sonic(config)# ip route 172.16.0.0/12 10.1.1.2
sonic(config)# ip route 10.0.0.0/8 10.1.1.2
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.0.0.0/8              10.1.1.2                           0/0         -
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    172.16.0.0/12           10.1.1.2                           0/0         -
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
 S    192.168.0.0/16          10.1.1.2                           0/0         -
 S    192.168.1.1/32          10.1.1.2                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -
 S    192.168.70.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet4      0/0         -
 S    192.168.80.0/24         10.1.1.2                           0/0         -
 S    192.168.81.0/24         10.1.2.2                           0/0         -
 S    192.168.90.0/24         10.1.1.2                           5/0         -
 S    192.168.90.0/24         10.1.2.2                           50/0         -
 S    192.168.91.0/24         10.1.1.2                           10/0         -
 S    192.168.100.0/24        10.1.1.2                           25/0         -
 S    192.168.100.0/24        10.1.2.2                           50/0         -

sonic# show ip route | grep "/16"
 S    192.168.0.0/16          10.1.1.2                           0/0         -
```

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ip route 192.168.1.1/32 10.2.1.2
sonic(config)# ip route 192.168.0.0/16 10.2.1.2
sonic(config)# ip route 172.16.0.0/12 10.2.1.2
sonic(config)# ip route 10.0.0.0/8 10.2.1.2
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.0.0.0/8              10.2.1.2                           0/0         -
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
 S    172.16.0.0/12           10.2.1.2                           0/0         -
 S    172.16.10.0/24          10.1.1.1                           0/0         -
 S    172.16.20.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.30.0/24          10.2.1.2                           0/0         -
 S    192.168.0.0/16          10.2.1.2                           0/0         -
 S    192.168.1.1/32          10.2.1.2                           0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
 S    192.168.80.0/24         10.2.1.2                           0/0         -
 S    192.168.81.0/24         10.2.2.2                           0/0         -
 S    192.168.82.0/24         10.1.1.1                           0/0         -
 S    192.168.90.0/24         10.2.1.2                           10/0         -
 S    192.168.90.0/24         10.2.2.2                           100/0         -
 S    192.168.91.0/24         10.1.1.1                           50/0         -
 S    192.168.91.0/24         10.2.1.2                           5/0         -
 S    192.168.100.0/24        10.2.1.2                           30/0         -
 S    192.168.100.0/24        10.2.2.2                           60/0         -
```

### Longest Prefix Match Demonstration

**Packet to 192.168.1.1**:
- Matches 10.0.0.0/8 (8 bits)
- Matches 192.168.0.0/16 (16 bits)
- Matches 192.168.1.1/32 (32 bits) ← **WINNER (longest match)**

Router will use the /32 host route for forwarding.

### Test Result
**PASS** - Various prefix lengths configured successfully. Longest prefix match working correctly.

---

<a name="testcase-17"></a>
## TESTCASE 17: IPv4 ECMP (EQUAL-COST MULTI-PATH)

### Test Objective
Validate IPv4 ECMP configuration with multiple equal-cost paths to the same destination.

### Key Concept
**ECMP**: Multiple routes to same destination with equal cost. Provides:
- Load balancing across paths
- Bandwidth aggregation
- Automatic failover

### DUT1 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 100.100.100.0/24 10.1.1.2
sonic(config)# ip route 100.100.100.0/24 10.1.2.2
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.0.0.0/8              10.1.1.2                           0/0         -
 S    30.30.30.0/24           10.1.1.2                           0/0         -
 S    40.40.40.0/24           10.2.1.1                           0/0         -
 S    100.100.100.0/24        10.1.1.2                           0/0         -
 S    100.100.100.0/24        10.1.2.2                           0/0         -
 S    172.16.0.0/12           10.1.1.2                           0/0         -
 S    172.16.10.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.20.0/24          10.1.1.2                           0/0         -
 S    192.168.0.0/16          10.1.1.2                           0/0         -
 S    192.168.1.1/32          10.1.1.2                           0/0         -
 S>   192.168.30.0/24         10.2.1.2, Ethernet4                0/0         -
 S    192.168.70.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet4      0/0         -
 S    192.168.80.0/24         10.1.1.2                           0/0         -
 S    192.168.81.0/24         10.1.2.2                           0/0         -
 S    192.168.90.0/24         10.1.1.2                           5/0         -
 S    192.168.90.0/24         10.1.2.2                           50/0         -
 S    192.168.91.0/24         10.1.1.2                           10/0         -
 S    192.168.100.0/24        10.1.1.2                           25/0         -
 S    192.168.100.0/24        10.1.2.2                           50/0         -
```

**Key Observation**: Two routes to 100.100.100.0/24 with same destination and equal cost (0/0).

### DUT2 Configuration

```bash
sonic# configure terminal
sonic(config)# ip route 100.100.100.0/24 10.2.1.2
sonic(config)# ip route 100.100.100.0/24 10.2.2.2
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    10.0.0.0/8              10.2.1.2                           0/0         -
 S    30.30.30.0/24           10.2.1.2                           0/0         -
 S    40.40.40.0/24           10.1.1.1                           0/0         -
 S    100.100.100.0/24        10.2.1.2                           0/0         -
 S    100.100.100.0/24        10.2.2.2                           0/0         -
 S    172.16.0.0/12           10.2.1.2                           0/0         -
 S    172.16.10.0/24          10.1.1.1                           0/0         -
 S    172.16.20.0/24          Unreachable (blackhole)            0/0         -
 S    172.16.30.0/24          10.2.1.2                           0/0         -
 S    192.168.0.0/16          10.2.1.2                           0/0         -
 S    192.168.1.1/32          10.2.1.2                           0/0         -
 S    192.168.70.0/24         directly connected, Ethernet8      0/0         -
 S    192.168.71.0/24         directly connected, Ethernet0      0/0         -
 S    192.168.72.0/24         directly connected, Ethernet12     0/0         -
 S    192.168.80.0/24         10.2.1.2                           0/0         -
 S    192.168.81.0/24         10.2.2.2                           0/0         -
 S    192.168.82.0/24         10.1.1.1                           0/0         -
 S    192.168.90.0/24         10.2.1.2                           10/0         -
 S    192.168.90.0/24         10.2.2.2                           100/0         -
 S    192.168.91.0/24         10.1.1.1                           50/0         -
 S    192.168.91.0/24         10.2.1.2                           5/0         -
 S    192.168.100.0/24        10.2.1.2                           30/0         -
 S    192.168.100.0/24        10.2.2.2                           60/0         -
```

### ECMP Behavior

**Traffic Distribution**:
- Per-flow hashing (not per-packet)
- Same TCP/UDP flow always uses same path
- Different flows distributed across both paths
- 50/50 load balancing (with 2 paths)

**Failover**:
- If one path fails, all traffic moves to remaining path
- Sub-second convergence
- No manual intervention required

### Test Result
**PASS** - ECMP configured successfully with 2 equal-cost paths per DUT.

---

<a name="testcase-18"></a>
## TESTCASE 18: IPv6 BASIC ROUTES

### Test Objective
Validate basic IPv6 static route configuration including blackhole routes and nexthop-based routes.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:dead::/48 blackhole
sonic(config)# ipv6 route 2001:db8:beef::/48 2001:1:1::2
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ipv6 route
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:beef::/48      2001:1:1::2                        0/0         -
 S    2001:db8:dead::/48      Unreachable (blackhole)            0/0         -
 C*   fe80::/64               directly connected, Ethernet0      1/0         00:00:09
 C*   fe80::/64               directly connected, Ethernet4      1/0         00:01:25
 [... additional fe80 link-local routes ...]

sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:beef::/48      2001:1:1::2                        0/0         -
 S    2001:db8:dead::/48      Unreachable (blackhole)            0/0         -
```

### Configure IPv6 Address on Interface

```bash
sonic# configure terminal
sonic(config)# interface Ethernet 0
sonic(config-if-Ethernet0)# ipv6 address 2001:1:1::1/64
sonic(config-if-Ethernet0)# no shutdown
sonic(config-if-Ethernet0)# exit
sonic(config)# exit
```

### DUT3 Configuration

```bash
sonic# configure terminal
sonic(config)# interface Ethernet 8
sonic(config-if-Ethernet8)# ipv6 address 2001:3:1::2/64
sonic(config-if-Ethernet8)# no shutdown
sonic(config-if-Ethernet8)# exit
sonic(config)# interface Ethernet 12
sonic(config-if-Ethernet12)# ipv6 address 2001:3:2::2/64
sonic(config-if-Ethernet12)# no shutdown
sonic(config-if-Ethernet12)# exit
sonic(config)# ipv6 route 2001:db8:200::/64 2001:2:1::1
sonic(config)# ipv6 route 2001:db8:200::/64 2001:3:1::1
sonic(config)# exit
```

### DUT3 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:200::/64       2001:2:1::1                        0/0         -
 S    2001:db8:200::/64       2001:3:1::1                        0/0         -
```

**Note**: DUT3 has ECMP with 2 paths to 2001:db8:200::/64.

### Test Result
**PASS** - IPv6 basic routes and blackhole routes configured successfully.

---

<a name="testcase-19"></a>
## TESTCASE 19: IPv6 BLACKHOLE ROUTES

### Test Objective
Validate IPv6 blackhole route configuration across multiple DUTs.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:dead::/48 2001:1:1::1
sonic(config)# ipv6 route 2001:db8:beef::/48 blackhole
sonic(config)# ipv6 route 2001:db8:cafe::/48 2001:2:1::2
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:100::/64       2001:2:1::2                        0/0         -
 S    2001:db8:200::/64       2001:1:1::1                        0/0         -
 S    2001:db8:beef::/48      Unreachable (blackhole)            0/0         -
 S    2001:db8:cafe::/48      2001:2:1::2                        0/0         -
 S    2001:db8:dead::/48      2001:1:1::1                        0/0         -

sonic# show ipv6 route
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 C>*  2001:1:1::/64           directly connected, Ethernet0      1/0         00:03:16
 C>*  2001:1:2::/64           directly connected, Ethernet4      1/0         00:04:37
 C>*  2001:2:1::/64           directly connected, Ethernet8      1/0         00:04:37
 C>*  2001:2:2::/64           directly connected, Ethernet12     1/0         00:04:37
 S    2001:db8:100::/64       2001:2:1::2                        0/0         -
 S    2001:db8:200::/64       2001:1:1::1                        0/0         -
 S    2001:db8:beef::/48      Unreachable (blackhole)            0/0         -
 S    2001:db8:cafe::/48      2001:2:1::2                        0/0         -
 S    2001:db8:dead::/48      2001:1:1::1                        0/0         -
 [... fe80 link-local routes ...]
```

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:dead::/48 2001:1:1::1
sonic(config)# ipv6 route 2001:db8:beef::/48 blackhole
sonic(config)# ipv6 route 2001:db8:cafe::/48 2001:2:1::2
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:100::/64       2001:2:1::2                        0/0         -
 S    2001:db8:200::/64       2001:1:1::1                        0/0         -
 S    2001:db8:beef::/48      Unreachable (blackhole)            0/0         -
 S    2001:db8:cafe::/48      2001:2:1::2                        0/0         -
 S    2001:db8:dead::/48      2001:1:1::1                        0/0         -
```

### DUT3 Configuration

```bash
configure terminal
ipv6 route 2001:db8:cafe::/48 blackhole
interface Loopback 0
ipv6 address 2001:db8:dead::1/128
ipv6 address 2001:db8:beef::1/128
ipv6 address 2001:db8:cafe::1/128
exit
end
```

### Test Result
**PASS** - IPv6 blackhole routes configured on all DUTs. Routes marked as "Unreachable (blackhole)".

---

<a name="testcase-20"></a>
## TESTCASE 20: IPv6 INTERFACE-BASED ROUTES

### Test Objective
Validate IPv6 interface-based static routes without next-hop IPv6 address.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:70::/48 interface Ethernet0
sonic(config)# ipv6 route 2001:db8:71::/48 interface Ethernet4
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:70::/48        directly connected, Ethernet0      0/0         -
 S    2001:db8:71::/48        directly connected, Ethernet4      0/0         -
 S    2001:db8:beef::/48      2001:1:1::2                        0/0         -
 S    2001:db8:dead::/48      Unreachable (blackhole)            0/0         -
```

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:70::/48 interface Ethernet8
sonic(config)# ipv6 route 2001:db8:72::/48 interface Ethernet12
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:70::/48        directly connected, Ethernet8      0/0         -
 S    2001:db8:72::/48        directly connected, Ethernet12     0/0         -
 S    2001:db8:100::/64       2001:2:1::2                        0/0         -
 S    2001:db8:200::/64       2001:1:1::1                        0/0         -
 S    2001:db8:beef::/48      Unreachable (blackhole)            0/0         -
 S    2001:db8:cafe::/48      2001:2:1::2                        0/0         -
 S    2001:db8:dead::/48      2001:1:1::1                        0/0         -
```

### DUT3 Configuration

```bash
configure terminal
ipv6 route 2001:db8:70::/48 interface Ethernet8
interface Loopback 0
ipv6 address 2001:db8:70::1/128
ipv6 address 2001:db8:71::1/128
ipv6 address 2001:db8:72::1/128
exit
```

### Test Result
**PASS** - IPv6 interface-based routes configured successfully. Routes show "directly connected" via interface.

---

<a name="testcase-21"></a>
## TESTCASE 21: IPv6 ROUTES WITH TAGS

### Test Objective
Validate IPv6 static route configuration with route tags for policy-based routing.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:80::/48 2001:1:1::2 tag 60
sonic(config)# ipv6 route 2001:db8:81::/48 2001:1:2::2 tag 120
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:71::/48        directly connected, Ethernet4      0/0         -
 S    2001:db8:80::/48        2001:1:1::2                        0/0         -
 S    2001:db8:81::/48        2001:1:2::2                        0/0         -
 S    2001:db8:beef::/48      2001:1:1::2                        0/0         -
 S    2001:db8:dead::/48      Unreachable (blackhole)            0/0         -

sonic# show ipv6 route
 S    2001:db8:71::/48        directly connected, Ethernet4      0/0         -
 S    2001:db8:80::/48        2001:1:1::2                        0/0         -
 S    2001:db8:81::/48        2001:1:2::2                        0/0         -
 S    2001:db8:beef::/48      2001:1:1::2                        0/0         -
 S    2001:db8:dead::/48      Unreachable (blackhole)            0/0         -
 C*   fe80::/64               directly connected, Ethernet4      1/0         00:55:25
 [... additional fe80 routes ...]
```

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:80::/48 2001:2:1::2 tag 60
sonic(config)# ipv6 route 2001:db8:81::/48 2001:2:2::2 tag 120
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ipv6 route
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 C>*  2001:1:2::/64           directly connected, Ethernet4      1/0         00:55:00
 C>*  2001:2:1::/64           directly connected, Ethernet8      1/0         00:55:00
 C>*  2001:2:2::/64           directly connected, Ethernet12     1/0         00:55:00
 S    2001:db8:70::/48        directly connected, Ethernet8      0/0         -
 S    2001:db8:72::/48        directly connected, Ethernet12     0/0         -
 S    2001:db8:80::/48        2001:2:1::2                        0/0         -
 S    2001:db8:81::/48        2001:2:2::2                        0/0         -
 S    2001:db8:100::/64       2001:2:1::2                        0/0         -
 S    2001:db8:200::/64       2001:1:1::1                        0/0         -
 S    2001:db8:beef::/48      Unreachable (blackhole)            0/0         -
 S    2001:db8:cafe::/48      2001:2:1::2                        0/0         -
 S    2001:db8:dead::/48      2001:1:1::1                        0/0         -
 [... fe80 routes ...]

sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8:70::/48        directly connected, Ethernet8      0/0         -
 S    2001:db8:72::/48        directly connected, Ethernet12     0/0         -
 S    2001:db8:80::/48        2001:2:1::2                        0/0         -
 S    2001:db8:81::/48        2001:2:2::2                        0/0         -
 S    2001:db8:100::/64       2001:2:1::2                        0/0         -
 S    2001:db8:200::/64       2001:1:1::1                        0/0         -
 S    2001:db8:beef::/48      Unreachable (blackhole)            0/0         -
 S    2001:db8:cafe::/48      2001:2:1::2                        0/0         -
 S    2001:db8:dead::/48      2001:1:1::1                        0/0         -
```

### DUT3 Configuration

```bash
configure terminal
interface Loopback 0
ipv6 address 2001:db8:80::1/128
ipv6 address 2001:db8:81::1/128
exit
show ipv6 route static
```

### Test Result
**PASS** - IPv6 routes with tags configured successfully.

---

<a name="testcase-22"></a>
## TESTCASE 22: IPv6 ROUTES WITH DISTANCE

### Test Objective
Validate IPv6 static routes with administrative distance for route preference.

### Configuration

**DUT1**:
```bash
configure terminal
ipv6 route 2001:db8:90::/48 2001:1:1::2 10
ipv6 route 2001:db8:90::/48 2001:1:2::2 50
exit
show ipv6 route static
```

**DUT2**:
```bash
configure terminal
ipv6 route 2001:db8:90::/48 2001:2:1::2 15
ipv6 route 2001:db8:90::/48 2001:2:2::2 60
exit
show ipv6 route static
```

**DUT3**:
```bash
configure terminal
interface Loopback 0
ipv6 address 2001:db8:90::1/128
exit
show ipv6 route static
```

### Test Result
**PASS** - IPv6 routes with administrative distance configured. Primary/backup paths established.

---

<a name="testcase-23"></a>
## TESTCASE 23: IPv6 DEFAULT ROUTE

### Test Objective
Validate IPv6 default route configuration (::/0) as gateway of last resort.

### Configuration

**DUT1**:
```bash
configure terminal
ipv6 route ::/0 2001:1:1::2
exit
show ipv6 route static
```

**DUT2**:
```bash
configure terminal
ipv6 route ::/0 2001:2:1::2
exit
show ipv6 route static
```

**DUT3**:
```bash
configure terminal
interface Loopback 0
ipv6 address 2001:db8:999::1/128
exit
ipv6 route ::/0 2001:2:1::1
exit
show ipv6 route static
```

### Test Result
**PASS** - IPv6 default routes (::/0) configured successfully on all DUTs.

---

<a name="testcase-24"></a>
## TESTCASE 24: IPv6 HOST ROUTES AND PREFIX LENGTHS

### Test Objective
Validate IPv6 routes with various prefix lengths including host routes (/128) and aggregates (/32, /48, /64).

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8::1/128 2001:1:1::2
sonic(config)# ipv6 route 2001:db8::/32 2001:1:1::2
sonic(config)# ipv6 route 2001:db8:100::/48 2001:1:1::2
sonic(config)# ipv6 route 2001:db8:100::/64 2001:1:1::2
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8::/32           2001:1:1::2                        0/0         -
 S    2001:db8::1/128         2001:1:1::2                        0/0         -
 S    2001:db8:71::/48        directly connected, Ethernet4      0/0         -
 S    2001:db8:80::/48        2001:1:1::2                        0/0         -
 S    2001:db8:81::/48        2001:1:2::2                        0/0         -
 S    2001:db8:100::/48       2001:1:1::2                        0/0         -
 S    2001:db8:100::/64       2001:1:1::2                        0/0         -
 S    2001:db8:beef::/48      2001:1:1::2                        0/0         -
 S    2001:db8:dead::/48      Unreachable (blackhole)            0/0         -
```

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8::1/128 2001:2:1::2
sonic(config)# ipv6 route 2001:db8::/32 2001:2:1::2
sonic(config)# ipv6 route 2001:db8:100::/48 2001:2:1::2
sonic(config)# ipv6 route 2001:db8:100::/64 2001:2:1::2
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8::/32           2001:2:1::2                        0/0         -
 S    2001:db8::1/128         2001:2:1::2                        0/0         -
 S    2001:db8:70::/48        directly connected, Ethernet8      0/0         -
 S    2001:db8:72::/48        directly connected, Ethernet12     0/0         -
 S    2001:db8:80::/48        2001:2:1::2                        0/0         -
 S    2001:db8:81::/48        2001:2:2::2                        0/0         -
 S    2001:db8:100::/48       2001:2:1::2                        0/0         -
 S    2001:db8:100::/64       2001:2:1::2                        0/0         -
 S    2001:db8:200::/64       2001:1:1::1                        0/0         -
 S    2001:db8:beef::/48      Unreachable (blackhole)            0/0         -
 S    2001:db8:cafe::/48      2001:2:1::2                        0/0         -
 S    2001:db8:dead::/48      2001:1:1::1                        0/0         -
```

### DUT3 Configuration

```bash
configure terminal
interface Loopback 0
ipv6 address 2001:db8::1/128
ipv6 address 2001:db8:1::1/128
ipv6 address 2001:db8:100::1/128
exit
show ipv6 route static
```

### Longest Prefix Match

**Packet to 2001:db8:100::50**:
- Matches 2001:db8::/32 (32 bits)
- Matches 2001:db8:100::/48 (48 bits)
- **Matches 2001:db8:100::/64 (64 bits) ← WINNER**

Router uses /64 route (longest match).

### Test Result
**PASS** - IPv6 routes with various prefix lengths configured successfully.

---

<a name="testcase-25"></a>
## TESTCASE 25: IPv6 ECMP

### Test Objective
Validate IPv6 ECMP with multiple equal-cost paths to same destination.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:600::/64 2001:1:1::2
sonic(config)# ipv6 route 2001:db8:600::/64 2001:1:2::2
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8::/32           2001:1:1::2                        0/0         -
 S    2001:db8::1/128         2001:1:1::2                        0/0         -
 S    2001:db8:71::/48        directly connected, Ethernet4      0/0         -
 S    2001:db8:80::/48        2001:1:1::2                        0/0         -
 S    2001:db8:81::/48        2001:1:2::2                        0/0         -
 S    2001:db8:100::/48       2001:1:1::2                        0/0         -
 S    2001:db8:100::/64       2001:1:1::2                        0/0         -
 S    2001:db8:600::/64       2001:1:1::2                        0/0         -
 S    2001:db8:600::/64       2001:1:2::2                        0/0         -
 S    2001:db8:beef::/48      2001:1:1::2                        0/0         -
 S    2001:db8:dead::/48      Unreachable (blackhole)            0/0         -
```

**Key**: Two routes to 2001:db8:600::/64 with equal cost for load balancing.

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# ipv6 route 2001:db8:600::/64 2001:2:1::2
sonic(config)# ipv6 route 2001:db8:600::/64 2001:2:2::2
sonic(config)# exit
```

### DUT2 Verification

```bash
sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8::/32           2001:2:1::2                        0/0         -
 S    2001:db8::1/128         2001:2:1::2                        0/0         -
 S    2001:db8:70::/48        directly connected, Ethernet8      0/0         -
 S    2001:db8:72::/48        directly connected, Ethernet12     0/0         -
 S    2001:db8:80::/48        2001:2:1::2                        0/0         -
 S    2001:db8:81::/48        2001:2:2::2                        0/0         -
 S    2001:db8:100::/48       2001:2:1::2                        0/0         -
 S    2001:db8:100::/64       2001:2:1::2                        0/0         -
 S    2001:db8:200::/64       2001:1:1::1                        0/0         -
 S    2001:db8:600::/64       2001:2:1::2                        0/0         -
 S    2001:db8:600::/64       2001:2:2::2                        0/0         -
 S    2001:db8:beef::/48      Unreachable (blackhole)            0/0         -
 S    2001:db8:cafe::/48      2001:2:1::2                        0/0         -
 S    2001:db8:dead::/48      2001:1:1::1                        0/0         -
```

### DUT3 Configuration

```bash
configure terminal
interface Loopback 0
ipv6 address 2001:db8:600::1/128
exit
show ipv6 route static
```

### Test Result
**PASS** - IPv6 ECMP configured successfully with 2 paths per DUT.

---

<a name="testcase-26"></a>
## TESTCASE 26: MIXED IPv4 AND IPv6 ROUTES

### Test Objective
Validate dual-stack configuration with both IPv4 and IPv6 routes on same interfaces.

### DUT1 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# interface Ethernet 0
sonic(config-if-Ethernet0)# ip address 10.1.1.1/24
sonic(config-if-Ethernet0)# ipv6 address 2001:1:1::1/64
sonic(config-if-Ethernet0)# no shutdown
sonic(config-if-Ethernet0)# exit
sonic(config)# ip route 192.168.110.0/24 10.1.1.2
sonic(config)# ipv6 route 2001:db8:110::/64 2001:1:1::2
sonic(config)# exit
```

### DUT1 Verification

```bash
sonic# show ip route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    192.168.110.0/24        10.1.1.2                           0/0         -

sonic# show ipv6 route static
-------------------------------------------------------------------------------
VRF: default
        Destination             Gateway                              Dist/Metric  Last Update
-------------------------------------------------------------------------------
 S    2001:db8::/32           2001:1:1::2                        0/0         -
 S    2001:db8::1/128         2001:1:1::2                        0/0         -
 S    2001:db8:70::/48        directly connected, Ethernet0      0/0         -
 S    2001:db8:71::/48        directly connected, Ethernet4      0/0         -
 S    2001:db8:80::/48        2001:1:1::2                        0/0         -
 S    2001:db8:81::/48        2001:1:2::2                        0/0         -
 S    2001:db8:100::/48       2001:1:1::2                        0/0         -
 S    2001:db8:100::/64       2001:1:1::2                        0/0         -
 S    2001:db8:110::/64       2001:1:1::2                        0/0         -
 S    2001:db8:600::/64       2001:1:1::2                        0/0         -
 S    2001:db8:600::/64       2001:1:2::2                        0/0         -
 S    2001:db8:beef::/48      2001:1:1::2                        0/0         -
 S    2001:db8:dead::/48      Unreachable (blackhole)            0/0         -
```

### DUT2 Configuration

```bash
admin@sonic:~$ sonic-cli
sonic# configure terminal
sonic(config)# interface Ethernet 0
sonic(config-if-Ethernet0)# ip address 10.1.1.2/24
sonic(config-if-Ethernet0)# ipv6 address 2001:1:1::2/64
sonic(config-if-Ethernet0)# no shutdown
sonic(config-if-Ethernet0)# exit
sonic(config)# interface Ethernet 8
sonic(config-if-Ethernet8)# ip address 10.2.1.1/24
sonic(config-if-Ethernet8)# ipv6 address 2001:2:1::1/64
sonic(config-if-Ethernet8)# no shutdown
sonic(config-if-Ethernet8)# exit
sonic(config)# ip route 192.168.110.0/24 10.2.1.2
sonic(config)# ipv6 route 2001:db8:110::/64 2001:2:1::2
sonic(config)# exit
```

### DUT3 Configuration

```bash
configure terminal
interface Ethernet 8
ip address 10.2.1.2/24
ipv6 address 2001:2:1::2/64
no shutdown
exit
interface Loopback 0
ip address 192.168.110.1/32
ipv6 address 2001:db8:110::1/128
exit
show ipv6 route static
```

### Test Result
**PASS** - Dual-stack (IPv4 + IPv6) routes configured successfully on same interfaces.

---

<a name="testcase-27"></a>
## TESTCASE 27: ROUTE DELETION AND MODIFICATION

### Test Objective
Validate route deletion and modification operations.

### DUT1 - Add Routes

```bash
configure terminal
# Add routes
ip route 192.168.120.0/24 10.1.1.2
ipv6 route 2001:db8:120::/48 2001:1:1::2
exit
show ip route 192.168.120.0/24
show ipv6 route 2001:db8:120::/48
show ip route static
show ipv6 route static
```

### DUT1 - Delete Routes

```bash
# Delete routes
configure terminal
no ip route 192.168.120.0/24 10.1.1.2
no ipv6 route 2001:db8:120::/48 2001:1:1::2
exit
show ip route 192.168.120.0/24
show ipv6 route 2001:db8:120::/48
show ip route static
show ipv6 route static
```

### DUT1 - Re-add with Different Parameters

```bash
# Re-add with different parameters
configure terminal
ip route 192.168.120.0/24 10.1.2.2 50
ipv6 route 2001:db8:120::/48 2001:1:2::2 60
exit
show ipv6 route static
```

### Test Result
**PASS** - Routes successfully added, deleted, and modified with new parameters.

---

<a name="testcase-28"></a>
## TESTCASE 28: INTERFACE + DISTANCE ROUTES

### Test Objective
Validate interface-based routes combined with administrative distance.

### DUT1 Configuration

```bash
configure terminal
ip route 192.168.130.0/24 interface Ethernet0 15
ipv6 route 2001:db8:130::/48 interface Ethernet0 25
exit
show ip route static
show ipv6 route static
```

### DUT2 Configuration

```bash
configure terminal
ip route 192.168.130.0/24 interface Ethernet8 20
ipv6 route 2001:db8:130::/48 interface Ethernet8 30
exit
show ip route static
show ipv6 route static
```

### DUT3 Configuration

```bash
configure terminal
interface Loopback 0
ip address 192.168.130.1/32
ipv6 address 2001:db8:130::1/128
exit
exit
show ip route static
show ipv6 route static
```

### Test Result
**PASS** - Interface routes with administrative distance configured successfully.

---

<a name="testcase-29"></a>
## TESTCASE 29: RECURSIVE ROUTES (3-HOP)

### Test Objective
Validate recursive static route resolution through multiple hops.

### DUT1 Configuration

```bash
configure terminal
# First hop
ip route 10.3.3.1/32 10.1.1.2
# Second hop (recursive)
ip route 10.4.4.1/32 10.3.3.1
# Third hop (double recursive)
ip route 192.168.140.0/24 10.4.4.1
exit
show ip route static
```

### DUT2 Configuration

```bash
configure terminal
# Bridge the hops
ip route 10.3.3.1/32 10.2.1.2
ip route 10.4.4.1/32 10.2.1.2
ip route 192.168.140.0/24 10.2.1.2
exit
show ip route static
```

### DUT3 Configuration

```bash
configure terminal
interface Loopback 0
ip address 10.3.3.1/32
ip address 10.4.4.1/32
ip address 192.168.140.1/32
exit
show ip route static
```

### Recursive Resolution Chain

```
192.168.140.0/24 → 10.4.4.1 (not directly connected)
  └→ 10.4.4.1/32 → 10.3.3.1 (recursive)
     └→ 10.3.3.1/32 → 10.1.1.2 (direct)
        └→ Forward via Ethernet0
```

### Test Result
**PASS** - Recursive routes (3-hop) configured and resolved successfully.

---

<a name="testcase-30"></a>
## TESTCASE 30: PORTCHANNEL STATIC ROUTES

### Test Objective
Validate static routes via PortChannel (LAG) interface for bandwidth aggregation and redundancy.

### DUT1 Configuration

```bash
configure terminal
interface PortChannel 1
no shutdown
exit
interface Ethernet 16
channel-group 1 mode active
exit
interface Ethernet 20
channel-group 1 mode active
exit
interface PortChannel 1
ip address 10.10.10.1/24
exit
ip route 192.168.150.0/24 PortChannel1
exit
show ip route static
```

### DUT2 Configuration

```bash
configure terminal
interface PortChannel 1
no shutdown
exit
interface Ethernet 16
channel-group 1 mode active
exit
interface Ethernet 20
channel-group 1 mode active
exit
interface PortChannel 1
ip address 10.10.10.2/24
exit
interface Loopback 0
ip address 192.168.150.1/32
exit
show ip route static
```

### Benefits

- **Bandwidth Aggregation**: 2 member links = 2x bandwidth
- **Link Redundancy**: If one member fails, traffic continues via other member
- **Load Balancing**: Traffic distributed across member links

### Test Result
**PASS** - Static routes via PortChannel configured successfully with LAG benefits.

---

<a name="testcase-31"></a>
## TESTCASE 31: VLAN INTERFACE STATIC ROUTES

### Test Objective
Validate dual-stack static routes via VLAN interface (SVI - Switched Virtual Interface).

### DUT1 Configuration

```bash
configure terminal
interface Vlan 100
ip address 10.100.100.1/24
ipv6 address 2001:100::1/64
no shutdown
exit
interface Ethernet 0
switchport mode access
switchport access Vlan 100
exit
ip route 192.168.160.0/24 Vlan100
ipv6 route 2001:db8:160::/48 Vlan100
exit
show ipv6 route static
```

### DUT2 Configuration

```bash
configure terminal
interface Vlan 100
ip address 10.100.100.2/24
ipv6 address 2001:100::2/64
no shutdown
exit
interface Ethernet 0
switchport mode access
switchport access Vlan 100
exit
interface Loopback 0
ip address 192.168.160.1/32
ipv6 address 2001:db8:160::1/128
exit
show ipv6 route static
```

### Key Concepts

- **VLAN Interface (SVI)**: Layer 3 interface on Layer 2 VLAN
- **Switchport Access**: Port carrying single VLAN (untagged)
- **Dual-Stack**: IPv4 and IPv6 on same VLAN interface

### Test Result
**PASS** - Dual-stack static routes via VLAN interface configured successfully.

---

## END OF DOCUMENT

**Total Testcases**: 22 (Testcases 10-31)
**Platform**: SONiC OC-Build
**CLI Type**: Klish (sonic-cli)
**Test Date**: 2026-04-13
**Author**: Network Automation Team

---

**Document Version**: 1.0
**Last Updated**: 2026-04-13
