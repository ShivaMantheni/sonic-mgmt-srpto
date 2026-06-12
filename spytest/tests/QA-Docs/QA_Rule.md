# QA_CoreRule — Test Case Writing Standards

**Applies when:** `/qa` is active and the task is test-case design or generation.  
**Authority:** `Projectdoc/` (requirements, topology, platform, sprint scope).  
**Output:** Versioned suites under `outputs/` only.

Non-compliance with any **MUST** rule blocks delivery.

---

## 1. Inputs (before writing any TC)

### 1.1 Ingest all `Projectdoc/` artifacts (project-specific)

Read everything available; content varies by project:

| Artifact | Use when generating TCs |
|----------|-------------------------|
| Requirement doc(s) | Acceptance criteria, feature behavior, IPv6/API/security scope |
| Sprint plan | In-scope modules, priorities, deadlines, exclusions |
| Screenshots / diagrams | Expected CLI output, UI/state, topology, packet flow |
| Existing test cases | Reuse, extend, or regression-link — avoid duplicate IDs; fill gaps only |

| Step | Rule |
|------|------|
| Identify | Platform (SONiC, Examon, etc.), modules in sprint scope, dependencies, cleanup |
| Map | Each requirement / story / config item → traceable TC-ID(s) |
| Decide | Which **test categories** apply per feature (§5) — generate only applicable ones |
| Gap | Unclear requirement → `⚠️ ASSUMPTION:` in TC; never invent out-of-scope behavior |

**Forbidden:** Generic TCs not tied to a named requirement, CLI, interface, protocol, or metric from `Projectdoc/`.  
**Forbidden:** Generating a conditional category (e.g. IPv6, packet capture) when requirements do not support it.

---

## 2. Platform & networking quality gate

Every suite MUST reflect the **actual NOS under test** from `Projectdoc/`:

| Check | MUST |
|-------|------|
| CLI syntax | Commands match platform (SONiC vs Examon vs vendor CLI — no mixed dialects) |
| Artifacts | Tables/counters named as on device (`show …`, Redis/AppDB, SDK paths per doc) |
| Topology | Peers, VLANs, PortChannels, ACLs, routes match documented lab diagram |
| Validation | 3-layer proof where applicable (see §6) — not ping-only for control-plane features |
| Scale | Limits from project doc (max members, ACL entries, MTU, prefix length), not generic defaults |

**Top-notch bar:** Steps name exact config lines, interfaces, IPs, ASNs, ACL lines, and measurable expected state — reproducible by another engineer without guessing.

---

## 3. Mandatory TC fields

```
TC-ID        : [MODULE]-[TYPE]-[NNN]     e.g. PO-CH-POS-001, BGP-NEG-003
Title        : Action + condition + measurable outcome
Module       : Feature from Projectdoc (PortChannel, BGP, ACL, …)
Priority     : P0 Blocker | P1 Critical | P2 Major | P3 Minor
Type         : Positive | Negative | Edge | Boundary | Regression | Smoke | E2E
Preconditions: Numbered setup (config, links up, neighbors established)
Test Steps   : Numbered, atomic, one action per step
Test Data    : Literal values only — no "valid IP" / "any VLAN"
Expected     : Observable CLI + traffic + counters (see §6)
Actual Result: [execution only]
Status       : Pass | Fail | Blocked | Skipped
Postcondition: Cleanup that restores deterministic baseline (§9)
```

### Title

- ✅ `Verify PortChannel stays up when one member link goes down on Ethernet12`
- ❌ `Test PortChannel` / `Check BGP`

### Test data

Explicit IPs, masks, VLAN IDs, ASNs, ACL rules, MTU, rates, packet sizes. Mark mocks for secrets.

---

## 4. Test design principles (enforce on every TC)

| Principle | Rule |
|-----------|------|
| Find defects | Design to expose failures, not only confirm happy path |
| Risk-first | P0/P1 on control/data-plane critical paths from `Projectdoc/` |
| Early test | Flag ambiguous requirements; document assumption |
| Defect clustering | Extra density on high-risk modules named in scope |
| Pesticide paradox | Vary data sets; no copy-paste TCs with title-only change |
| Context | Networking control + data plane — not web/mobile patterns unless in scope |
| No false confidence | Pass on TCs ≠ release ready; align to user/ops expectations in doc |

---

## 5. Networking test categories — applicability

Generate TCs **only for categories marked applicable** for that feature/requirement. Record decisions in the suite **Applicability** block (§5.1).

| Category | Applicability | Generate when |
|----------|---------------|---------------|
| **Positive scenarios** | **Always** | Every in-scope requirement — valid config → expected operational state |
| **Negative scenarios** | **Always** | Every in-scope requirement — ≥2 negatives per positive on same behavior (§7) |
| **Functional validation** | **Always** (networking) | Control + data plane behavior per requirement — core L2/L3/feature correctness (§6) |
| **Persistence / reboot** | Conditional | Feature is configurable and must survive save/reload, reboot, warm/cold restart per `Projectdoc/` |
| **Show commands** | Conditional | Feature exposes `show` / display / state CLI or equivalent (screenshots often define expected output) |
| **IPv6 support** | Conditional | Requirement or platform doc states IPv6 in scope for this feature |
| **Packet capture validation** | Conditional | Protocol/traffic path must be verified (e.g. TACACS+, RADIUS, sFlow, DHCP, SNMP, ACL hit path, tunnel encaps) |
| **Logging / syslog** | Conditional | Feature generates logs, traps, or audit events per requirements |
| **Security testing** | Conditional | AuthN/AuthZ, ACL policy, certificates, role/RBAC, or hardening in scope |
| **Scale / stress** | Conditional | Doc defines scale limits, max entries, throughput, or stress criteria |
| **Automation regression** | Conditional | Feature is covered by automation in sprint — link/reuse existing TCs; add missing regression TCs |
| **API testing** | Conditional | REST/gRPC/NETCONF/OpenAPI or automation API listed in requirements — apply §10 |

Also apply cross-cutting rules where relevant: **Boundary** (§8), **Edge** (§9), **Cleanup** (postcondition / §9), **Alternate flows** for distinct valid configs.

### 5.1 Applicability decision (per feature)

Before writing TCs for a module, fill:

```
Feature: [name]
Sources: [requirement doc § | sprint item | screenshot | existing TC file]
Always: Positive | Negative | Functional validation
Applicable: [list from table above]
Not applicable: [list + one-line reason from Projectdoc]
```

If a conditional category is **Applicable** but omitted from generated TCs → coverage **FAIL**.

### 5.2 100% coverage mandate

Coverage is **100% of in-scope requirements** from `Projectdoc/` (and test-plan in-scope table). Each requirement ID maps to ≥1 TC covering all **applicable** categories for that requirement; no orphan requirements, no orphan TCs.

Per requirement / feature — minimum:

| Category | Minimum |
|----------|---------|
| Positive | Always — happy path + alternate valid flows where relevant |
| Negative | Always — §7 |
| Functional validation | Always — §6 three-layer where applicable |
| Conditional (§5 table) | All rows marked Applicable for that feature |
| Boundary | BVA on every bounded field (§8) |
| Edge | §9 where applicable to feature type |
| Cleanup | Teardown or postcondition restoring baseline |

### 5.3 Per input / parameter — exercise

Empty/null, min−1, min, min+1, nominal, max−1, max, max+1, invalid format, out-of-range, duplicate/conflict, wrong config mode, special characters where CLI accepts strings.

### 5.4 Traceability matrix (required with suite)

| Req ID | Description | TC-IDs | Test categories covered | Priority | Status |
|--------|-------------|--------|-------------------------|----------|--------|

**Test categories covered** — use tags: `POS`, `NEG`, `FUNC`, `PERSIST`, `SHOW`, `IPv6`, `PCAP`, `LOG`, `SEC`, `SCALE`, `AUTO-REG`, `API`, `BVA`, `EDGE`, `CLEANUP`.

**Exit:** Matrix shows every in-scope requirement → TC(s) with all applicable category tags; every TC → requirement. Gaps = **FAIL**.

### 5.5 Suite summary (required header)

```markdown
## Test Suite: [Module] — [Feature from Projectdoc]
- Platform: [SONiC | Examon | …]
- Projectdoc sources: [files used]
- Requirements covered: N/N (100% required)
- Applicability: Always → POS, NEG, FUNC | Conditional → [list what was generated]
- Not generated (N/A): [category + reason]
- Total TCs: N | Positive: N | Negative: N | Functional: N | [conditional counts…]
- P0: N | P1: N | P2: N | P3: N
```

### 5.6 Conditional category — brief expectations

| Category | TC focus (when applicable) |
|----------|----------------------------|
| Persistence / reboot | Config retained after `write`/save, reload, reboot; operational state converges; no orphan state |
| Show commands | Output matches requirement/screenshot; keys, counters, state fields exact |
| IPv6 | Parallel IPv6 config/traffic/validation only where doc mandates dual-stack or v6-only |
| Packet capture | tcpdump/ERSPAN/scapy — verify protocol fields, ports, drop/permit, sampling |
| Logging / syslog | Message ID/text, severity, source; trap/inform for SNMP where in scope |
| Security | Deny/lockout, timeout, privilege, cert expiry, negative auth, policy violation |
| Scale / stress | At/max limits per doc; graceful reject beyond limit; stability under load |
| Automation regression | Align with existing automated TC IDs; new TCs automation-ready (steps/data/assertions) |
| API | Contract, auth, errors, idempotency per §10 |

---

## 6. Three-layer validation (networking)

Unless `Projectdoc/` marks N/A, expected results MUST state checks for:

| Layer | Examples |
|-------|----------|
| **1 — CLI / control plane** | `show interface status`, `show ip route`, `show ip access-lists`, `show PortChannel summary`, config DB state |
| **2 — Data plane** | ping, SCP/TCP/UDP, traffic gen, scapy/tcpdump, drop/permit behavior |
| **3 — Counters / telemetry** | `show interface counters`, ACL hit counts, MAC/ARP/forwarding tables |

**PASS** only if all applicable layers match expectation.

---

## 7. Negative testing (mandatory)

- Prefix type `NEG` in TC-ID where applicable.
- Categories: invalid config, out-of-range, wrong mode, duplicate/conflict, missing dependency, malformed CLI, scale exceeded, bad sequence, resource in use, protocol mismatch (LACP, BGP ASN, unreachable neighbor).
- Expect: explicit CLI error, no crash/restart, no unintended state, logs if specified, traffic drop/permit as designed.

---

## 8. Boundary & equivalence

**BVA:** min−1 (reject), min, min+1, nominal, max−1, max, max+1 (reject) for each bounded field (MTU, members, ACL depth, prefix length, timers, rates).

**EP:** One representative per valid/invalid partition per field; document partitions in suite notes when non-obvious.

---

## 9. Edge cases (networking — mandatory unless N/A in doc)

| Area | Examples |
|------|----------|
| State | Fresh/default, empty tables, single entry, max scale, duplicate/conflict, partial config |
| Concurrency | Parallel config on same/different resources; config during traffic |
| Load | Burst/sustained traffic; control-plane churn under load |
| Lifecycle | Delete → recreate; rapid enable/disable toggles |
| Timing | Post-config immediate vs convergence delay; race config vs traffic |
| Traffic | Low/high rate, mixed types, MTU variation, config change mid-stream |

Validate with §6 three layers. Include cleanup TCs: config removed, tables clear, counters baseline, idempotent re-run.

---

## 10. API testing (conditional)

Generate only when `Projectdoc/` lists API surface (REST, gRPC, NETCONF, OpenAPI, SDK, etc.) as in scope for the feature:

Apply when applicable:

- **API:** Method, headers, auth, schema, status codes, pagination, rate limits, no sensitive leakage in errors.
- **Retry/async jobs:** Attempt count, backoff, success on retry-N, exhaustion, idempotency, non-retryable errors.
- **Load:** Baseline, peak, burst, idle, ramp, timeout, backpressure per stated SLA.

If API is **Not applicable** — omit §10 TCs entirely.

---

## 11. Output format

```markdown
### TC-[MODULE]-[TYPE]-[NNN]
**Title:**
**Module:** | **Priority:** | **Type:**
**Requirement Ref:** [ID from Projectdoc]
**Test Category:** POS | NEG | FUNC | PERSIST | SHOW | IPv6 | PCAP | LOG | SEC | SCALE | AUTO-REG | API | …
**Preconditions:**
1.
**Test Steps:**
1.
**Test Data:** `key: value`
**Expected Result:** [CLI + traffic + counters]
**Postcondition/Cleanup:**
---
```

File naming: `outputs/<release-or-sprint>/TC_<module>_<date>.md` (append-only; new file per generation run).

---

## 12. Pre-generation checklist

```
[ ] Requirement doc, sprint plan, screenshots, existing TCs reviewed
[ ] Applicability block (§5.1) completed per feature
[ ] Always categories planned: Positive, Negative, Functional validation
[ ] Conditional categories only where Projectdoc supports them
[ ] Platform/NOS and topology confirmed
[ ] Coverage matrix will reach 100% with applicable category tags
```

---

## 13. Anti-patterns (reject)

| Do not | Why |
|--------|-----|
| Vague expected results | Untestable |
| Multiple unrelated checks in one TC | Ambiguous failure |
| Placeholder test data | Non-reproducible |
| Happy-path only | Misses defect clusters |
| Skip cleanup | Flaky suite |
| Generic SONiC/Examon wording without doc reference | Not project-specific |
| Web/mobile-only patterns on pure L2/L3 scope | Wrong context |
| IPv6 / PCAP / API / scale TCs without doc basis | Out-of-scope noise |
| Skipping always categories (POS/NEG/FUNC) | Incomplete networking coverage |

---

## 14. Definition of done (test-case generation)

1. `Projectdoc/` ingested (requirements, sprint, screenshots, existing TCs).  
2. Applicability decided per feature; only applicable conditional categories generated.  
3. Always: Positive, Negative, Functional validation — for every in-scope requirement.  
4. Traceability matrix at 100% with category tags for all applicable types.  
5. Structure, BVA/edge, 3-layer validation, and cleanup rules satisfied.  
6. Artifacts under `outputs/`; no generic or unjustified conditional TCs.

*Derived from QA Test Case Master Rules — operational core for SPYTest `/qa` test-case work.*
