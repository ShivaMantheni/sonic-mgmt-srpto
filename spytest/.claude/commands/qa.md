---
description: QA MODE — Generate test plans, test cases, RTMs, and QA artifacts grounded in project docs
---

You are now in **QA MODE**. Follow these rules exactly for this entire response.

## Step 1 — Ingest (do this before responding)

Read and analyze all of the following before generating any artifact:
- `tests/QA-Docs/QA_Rule.md` — QA rules and standards (100% requirement coverage, networking 3-layer validation)
- `tests/QA-Docs/TestPlan_Template.md` — canonical template for test plans and test cases
- Any `tests/automation/<feature>/ProjDoc/` folder relevant to the user's request — platform-specific steps and requirements

If a feature is mentioned in the prompt, resolve its ProjDoc path and read it now.

## Step 2 — Ground every artifact

- Tie all test plans, cases, and matrices directly to requirements from the ingested docs.
- No generic filler. Every test case must reference a specific requirement, sprint item, or platform behavior from the project docs.
- Follow `QA_Rule.md` in full: 100% requirement coverage, networking 3-layer validation (CLI → control-plane → data-plane where applicable).

## Step 3 — TestBuilder pipeline (for plan/TC/RTM generation)

If the request involves generating a test plan, test cases, or RTM, follow Processes 1–4 from `TestBuilder.md` at the repo root (if present), including the validation pipeline and pre-requisites checklist.

## Step 4 — Emit artifacts

Save any new QA artifacts **only** under `reports/` using versioned, append-only naming (e.g., `reports/YYYY-MM-DD/<feature>/`). Never overwrite a prior run folder or file.

---

## User request

$ARGUMENTS
