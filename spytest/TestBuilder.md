# TestBuilder — QA Artifact Pipeline

Orchestrates **Process 1 → 4**: test plan, test cases (.md + Excel), validation, traceability matrix.
Run under **`/qa`** (QA MODE per `spytest/CLAUDE.md`). Safe to re-run per sprint; write only to the
target feature folder (append-only).

---

## Folder structure (reference)

```
sonic-mgmt/
└── spytest/
    ├── CLAUDE.md                      # routing brain — /qa gate
    ├── TestBuilder.md                 # this file
    └── tests/
        ├── QA-Docs/
        │   ├── QA_Rule.md             # test case writing + applicability rules
        │   └── TestPlan_Template.md   # test plan structure + entry/exit gates
        └── automation/
            ├── <FEATURE>/             # e.g. LLDP, BGP
            │   ├── ProjDoc/           # INPUTS: requirements, sprint plans  → OUTPUTS: TP / TC / RTM
            │   ├── scripts/           # automation scripts
            │   ├── vars/              # variable / config files
            │   ├── reports/           # execution reports (logs, html, json)
            │   └── Run_All.sh         # feature execution script
            ├── Reports/               # consolidated reports (html, logs, json)
            └── Run_All.sh             # master test suite runner
```

**Path rule:** The prompt names the feature (and optionally an explicit output path).
- Feature root: `spytest/tests/automation/<FEATURE>/`
- Generated artifacts default to: `<FEATURE>/ProjDoc/`
- If the prompt gives an explicit path, that path wins — but it must be inside the feature folder.

---

## Pre-requisites (gate — run first)

Verify before any process. **Stop** if gate fails; report missing items and ask user to fix or confirm.

| Check | Pass condition |
|-------|----------------|
| QA docs | `tests/QA-Docs/QA_Rule.md` and `tests/QA-Docs/TestPlan_Template.md` exist |
| Routing | `spytest/CLAUDE.md` present (QA MODE rules) |
| Feature folder | `tests/automation/<FEATURE>/` exists with `ProjDoc/` sub-folder |
| Project inputs | At least one sprint- or requirement-specific file under `<FEATURE>/ProjDoc/` (not only `README.md`) |

```
IF QA-Docs files missing      → instruct: restore QA_Rule.md / TestPlan_Template.md under tests/QA-Docs/
IF feature folder missing     → ask user: create tests/automation/<FEATURE>/ skeleton? (ProjDoc, scripts, vars, reports)
IF ProjDoc empty              → ask user to add requirement / sprint files
```

**Requirement doc:** If no requirement file detected → ask user to place it under `<FEATURE>/ProjDoc/`
**or** confirm proceed **without** requirement doc (sprint-only mode; flag assumptions in all outputs).

---

## ProjDoc discovery (before Process 1 & 2)

Inventory all files under `<FEATURE>/ProjDoc/` and build a **source map**:

| Detected artifact | Typical patterns | Use for |
|-------------------|------------------|---------|
| Requirement doc(s) | `*req*`, `*requirement*`, `BRD`, `spec` | Scope, acceptance criteria, IDs |
| Sprint plan | `*sprint*`, `*plan*` | In-scope items, priorities, dates |
| Screenshots / diagrams | `.png`, `.jpg`, `.svg`, `screenshot` | Expected CLI/UI/state |
| Existing test cases | `*tc*`, `*test*case*`, `existing_tc` | Reuse, regression, dedup (Process 3) |
| Logs / captures | `*log*`, `.txt`, packet summaries | Behavior evidence |

Also scan `<FEATURE>/scripts/`, `vars/`, and `reports/` for evidence of existing automation and
prior runs — use for regression context, never as requirement source.

**Decision logic (dynamic):**

| Available inputs | Plan source | TC source |
|------------------|-------------|-----------|
| Requirement + sprint | Both — requirements drive scope; sprint drives schedule/priority | All applicable artifacts |
| Requirement only | Requirement doc | Requirement + any other files present |
| Sprint only | Sprint plan (note: no requirement doc — assumptions flagged) | Sprint + screenshots/logs/TCs if present |
| Multiple requirements | Merge IDs; dedupe scope; list conflicts for user | Per-module suites |

Record in each output header: **Sources used** + **Sources missing**.

---

## Process 1 — Test plan creation

| Item | Rule |
|------|------|
| Template | `tests/QA-Docs/TestPlan_Template.md` |
| Inputs | Source map from `<FEATURE>/ProjDoc/` |
| Output | `<FEATURE>/ProjDoc/TP_<feature-or-sprint>_<date>.md` |

**Steps:**

1. Apply discovery logic; confirm requirement doc handling with user if absent.
2. Fill template: scope, strategy, §6 entry/exit/traceability gates from template defaults unless `ProjDoc/` overrides.
3. In-scope table: every requirement/sprint item referenced by ID from source docs.
4. Out-of-scope: leave placeholder rows unless doc defines exclusions.
5. Save test plan; do not overwrite prior run — new file or versioned subfolder.

---

## Process 2 — Test case generation (.md + Excel)

| Item | Rule |
|------|------|
| Rules | `tests/QA-Docs/QA_Rule.md` (mandatory) |
| Inputs | Full depth read of **all** `<FEATURE>/ProjDoc/` files |
| Output 1 | `<FEATURE>/ProjDoc/TC_<feature>_<date>.md` |
| Output 2 | `<FEATURE>/ProjDoc/TC_<feature>_<date>.xlsx` (same content, same TC-IDs) |

**Steps:**

1. Re-scan `<FEATURE>/ProjDoc/` (requirements, sprint, screenshots, logs, existing TCs).
2. Per feature: complete **Applicability** block (always POS/NEG/FUNC; conditional categories per `QA_Rule.md` §5).
3. Generate TCs — platform-specific (SONiC, Examon, etc.); literal test data; 3-layer validation where applicable.
4. Link each TC to **Requirement Ref** or sprint item ID.
5. Write the `.md` file under `<FEATURE>/ProjDoc/`.
6. Export the **same** TCs to `.xlsx` (see Excel export rules below).

### Excel export rules

- Generate via Python (`openpyxl` or `pandas`); if neither is installed, write
  `TC_<feature>_<date>.csv` instead and tell the user to install `openpyxl` for native Excel.
- One workbook, two sheets:
  - **TestCases** — one row per TC, columns (in order):
    `TC ID | Title | Feature | Priority | Type (POS/NEG/FUNC/…) | Preconditions | Test Steps | Expected Results | Requirement Ref | Status`
  - **Summary** — counts by priority and type, sources used/missing, generation date.
- Multi-line cells (steps, expected results) use in-cell line breaks — numbered steps, one per line.
- `.md` and `.xlsx` must stay in lock-step: same TC-IDs, same count, same content.
  If TCs change after validation (Process 3), regenerate **both** files.

**Do not** run Process 3 until both Process 2 outputs exist.

---

## Process 3 — Validation pipeline

Run **after every** Process 2 TC generation. Execute steps **in sequence**; resolve failures before the next step.

### Step 1 — Coverage analysis

| Check | Pass |
|-------|------|
| Requirement coverage | ≥ 95% |
| Sprint item coverage | 100% |
| P1 requirements | 0 without a linked TC |

**Fail action:** Generate missing TCs for uncovered items; re-run Step 1.

### Step 2 — Relevance check

| Check | Pass |
|-------|------|
| Citations | Each TC cites verifiable requirement/sprint item (and screenshot if used) |
| Scope | 0 out-of-scope or fabricated assertions |

**Fail action:** Remove or rewrite invalid TCs; re-run Step 2.

### Step 3 — Authenticity validation

| Check | Pass |
|-------|------|
| Specifics | Topology, protocol, CLI, test data, expected results are measurable — no placeholders |
| Fabrication | 0 generic or invented references |

**Fail action:** Replace with values from `<FEATURE>/ProjDoc/`; re-run Step 3.

### Step 4 — Duplicate detection

| Check | Pass |
|-------|------|
| Intra-sprint | Jaccard similarity < 0.85 between any two TCs |
| Cross-sprint | Compare against `existing_tc.md` (or equivalent in `<FEATURE>/ProjDoc/`) |

**Fail action:** Merge or remove duplicates; keep the more specific TC; re-run Step 4.

### Step 5 — Final accuracy

| Sub-check | Pass |
|-----------|------|
| Schema | All mandatory fields per `QA_Rule.md` §3 |
| Citations | Present on every TC |
| Priority | Balanced distribution (no missing P0/P1 on critical paths) |
| Type balance | POS/NEG/conditional tags align with applicability |
| TC-ID | Ordered, unique, consistent naming |
| Format sync | `.md` and `.xlsx` contain identical TC-IDs and counts |

**Pass:** All sub-checks green → apply **APPROVED** stamp to the TC `.md` header and the
Excel **Summary** sheet.

**Fail action:** Fix issues in **both formats**; **re-run Step 5 only**.

> Do not mark TC batch complete until Step 5 returns **APPROVED**.

### Validation outcome — final test cases

Only after **all 5 steps pass** do the test cases become final:

1. Write the final, validated TC set to:
   - `<FEATURE>/ProjDoc/TC_<feature>_<date>_Final.md`
   - `<FEATURE>/ProjDoc/TC_<feature>_<date>_Final.xlsx`
2. Final files contain **only** TCs that survived validation (post coverage-fill, rewrite,
   and dedup) — with the **APPROVED** stamp and a validation summary (steps run, pass results, TC count).
3. The pre-validation draft files from Process 2 are kept untouched (append-only audit trail).
4. The **Final** files are the official deliverable — Process 4 and test execution use them,
   never the drafts.

---

## Process 4 — Traceability matrix

| Item | Rule |
|------|------|
| Inputs | **Final** TC file(s) (`TC_*_Final.md` / `.xlsx`) from Process 3 + same `<FEATURE>/ProjDoc/` sources |
| Output | `<FEATURE>/ProjDoc/RTM_<feature-or-sprint>_<date>.md` |

**Steps:**

1. Map every TC-ID from the **Final** TC files → requirement ID and/or sprint item (source column mandatory).
2. Map every in-scope requirement/sprint item → ≥1 TC (0 gaps for P1; 0 orphan TCs per test plan §6.3).
3. Include test category tags (`POS`, `NEG`, `FUNC`, conditional tags from `QA_Rule.md`).
4. Format: readable table + summary counts (requirements covered, TCs, orphans, P1 gaps).

**Accuracy rule:** Matrix must match approved TC files exactly — regenerate if TCs change
(and re-export the `.xlsx` so all three artifacts agree).

---

## End-to-end execution checklist

```
[ ] Pre-requisites pass (QA-Docs files + feature folder + ProjDoc inputs)
[ ] ProjDoc source map documented
[ ] Process 1 → TP_*.md in <FEATURE>/ProjDoc/
[ ] Process 2 → TC_*.md AND TC_*.xlsx (drafts) in <FEATURE>/ProjDoc/
[ ] Process 3 → Steps 1–5 pass (Coverage → Relevance → Authenticity → Duplicates → Final accuracy)
[ ] Process 3 → TC_*_Final.md AND TC_*_Final.xlsx written, stamped APPROVED
[ ] Process 4 → RTM_*.md in <FEATURE>/ProjDoc/ (built from Final TC files)
```

**Invocation examples:**

- `/qa Run TestBuilder for BGP — outputs under tests/automation/BGP/`
- `/qa Run TestBuilder Process 1 only for LLDP sprint-12`
- `/qa TestBuilder Process 2 only — feature LLDP` (still run Process 3 after)

**Partial runs:** If user requests a single process, run its pre-checks and dependencies;
warn if prior process outputs are missing.

---

## Output naming summary

| Process | File pattern |
|---------|----------------|
| 1 | `tests/automation/<FEATURE>/ProjDoc/TP_<name>_<date>.md` |
| 2 | `tests/automation/<FEATURE>/ProjDoc/TC_<feature>_<date>.md` (draft) |
| 2 | `tests/automation/<FEATURE>/ProjDoc/TC_<feature>_<date>.xlsx` (draft) |
| 3 | `tests/automation/<FEATURE>/ProjDoc/TC_<feature>_<date>_Final.md` |
| 3 | `tests/automation/<FEATURE>/ProjDoc/TC_<feature>_<date>_Final.xlsx` |
| 4 | `tests/automation/<FEATURE>/ProjDoc/RTM_<name>_<date>.md` |

Execution-time artifacts (logs, html, json) belong in `<FEATURE>/reports/` and the consolidated
`tests/automation/Reports/` — TestBuilder never writes there.

Do not edit prior generated artifacts in place — new run = new file or versioned subfolder.
