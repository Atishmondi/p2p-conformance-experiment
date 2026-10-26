# P2P Project Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deliver an evidence-backed, reproducible P2P portfolio demonstration and honest ERP validation boundary.
**Architecture:** Keep Python scripts and static dashboard. Introduce explicit v2 evidence semantics while retaining v1 reproduction. Generate presentation data from artifacts, isolate runs, and validate recorded ERP events at a dedicated boundary.
**Tech Stack:** Python >=3.9 stdlib core and unittest, optional scientific dependencies, vanilla HTML/CSS/JS, optional Odoo 17/Postgres.
**Spec:** docs/superpowers/specs/2026-10-25-project-completion.md

## Global Constraints
- Preserve current original edits and canonical synthetic CSV inputs; do not overwrite raw BPI data or duplicate the 728 MB XES.
- Core demo and tests run using Python >=3.9 standard library. Scientific analysis/PM4Py are optional extras. No hosted services required.
- Existing check_case tuple interface remains usable. Rule dict values are True (violation), False (evaluated compliant), or None (insufficient evidence). Consumers MUST not count None as compliant.
- No manufactured ERP timestamps, no synthetic causal or savings claims, no publication/push.
- Use independent fixtures and observe RED then GREEN for behavioral changes. Full command: python3 -m unittest discover -s tests -v.

## Review Focus
- Partial receipts/invoices and temporal cumulative quantities: independent literal fixtures (Task 1).
- Invalid/unknown quantities, duplicate IDs, timezone ties and mixed-grain records: visible errors or unknown, never false compliance (Task 1).
- Custom run tags, collisions, partial failures and canonical immutability (Task 1).
- Changed input counts and missing/empty strata must propagate to evaluation/dashboard without stale values (Tasks 2 and 4).
- ERP rows without source proof or recorded time must fail contract validation, and tooling must never imply executed validation (Task 3).

### Task 1: Versioned conformance and safe run execution
**Files:** Create src/legacy/check_conformance_v1.py, tests/test_conformance.py, tests/test_runs.py, docs/event-contract.md; modify src/check_conformance.py, src/run_manager.py, src/noise_test.py as needed to use current shared checker without copied fallback. Preserve generators' existing behavior.
**Interfaces:** Consumes existing event CSV and gen CLI. Produces check_conformance.load(path)->dict, check_case(evs)->existing tuple with tri-state rules; write_results(cases, output_dir, tag)->paths (document exact result shape); check CLI INPUT --output-dir DIR; run_manager --output-dir DIR chooses isolated data root, unique per-run directory, registry at root/runs.csv.
- [x] Write unittest fixtures proving multiple invoices exceed receipt availability, multiple receipts resolve correct totals, invoice before later receipt is flagged, missing fields are unknown, malformed decimals/negative/nonfinite/duplicate/mixed-unit/return input rejected; ordering ties don't manufacture compliance; canonical v1 and v2 baseline expectations explicitly compared (R1 60/120 bad, R2 0/60 bad).
- [x] Run focused unittest discovery and record expected failures.
- [x] Snapshot historical checker unchanged; implement data-contract normalization and v2 rules/report status, all callers compatible, no silently skipped None. Keep audit/report helpers focused.
- [x] Write/run RED tests for duplicate tag, traversal tag, n=0, canonical files unchanged, separate roots and deterministic seeded run outcomes. Implement direct isolated output, collision rejection, unique IDs.
- [x] Run full suite, self-review, commit only owned files and write task report.

### Task 2: Data-derived analysis and deterministic report build
**Files:** Modify src/evaluate.py, src/compare_lab_field.py; create src/build_dashboard.py, src/demo.py, tests/test_reporting.py, tests/test_demo.py; modify Makefile/run_demo.sh and src/analyze_bpic2019.py only for required paths/time handling/provenance.
**Interfaces:** Consumes Task 1 checker/isolated run outputs; produces build_dashboard.build(data_dir:Path, output_path:Path)->dict and CLI --data-dir --out; evaluate and comparison CLI --data-dir --out; python3 src/demo.py --output-dir DIR builds synthetic logs, conformance, descriptive evaluation, dashboard payload in DIR without optional libraries or canonical mutations. Optional existing scientific workflow retains dynamic inferential diagnostics.
- [x] Write/run RED tests using small literal changed cohorts to prove rates/counts derive from files, unknown denominator handling, field JSON changed rates flow through, no writes on import, missing files fail visibly.
- [x] Implement descriptive stdlib analysis and optional scientific calculation, remove all fixed cohort anchors from calculations. Include actual targeted vs overall denominators and no causal label.
- [x] Write/run RED tests for deterministic dashboard JSON from fixture artifacts; missing optional field data explicitly unavailable, not stale fallback; inputs mutated -> output changes.
- [x] Implement deterministic builder with provenance (relative paths/content hashes/rule_version/evidence class), update demo CLI and Make targets. Keep default static payload compatible or document new contract for Task 4.
- [x] Run full suite and a fresh temp-dir demo twice; compare content ignoring expressly nondeterministic run timestamps. Self-review, commit, report interfaces and commands.

### Task 3: Auditable ERP event boundary and pilot readiness
**Files:** Create src/validate_erp_export.py, tests/test_erp_export.py, examples/erp-recorded-events.csv, docs/erp-pilot.md; modify sql/odoo_extract.sql, docker-compose.yml, docs/03-odoo-setup.md, docs/17-erp-experiment-protocol.md with clear supersession notice; add scripts/check_erp_runtime.sh if needed.
**Interfaces:** Consumes canonical v2 event contract. Produces validate_export(path:Path)->validated rows and CLI INPUT --out CSV; required additional fields event_id, source_model, source_id, timestamp_kind='recorded', product_id, uom; timestamp must be actual datetime, no date-only input. Example is explicitly synthetic contract fixture, never live Odoo evidence.
- [x] Write/run RED tests for valid source-linked events and rejected missing source IDs, occurred/date-only timestamps, duplicate events, mixed grains, missing quantity on receipt/invoice, unmapped payments, and known fixture outcomes through checker.
- [x] Implement strict adapter validation, deterministic normalized output and no output on invalid input. Remove unsafe recommended extraction: archive legacy SQL clearly and replace entry with explicit fail-closed instruction if a trustworthy actual table cannot be verified. Do not fake a generic executable extractor.
- [x] Provide exact bounded Odoo protocol: isolated demo DB, actors, controls/attempts, source proof, criteria, source IDs, mapping, instrumented-history requirement. Fix compose access guidance, bind loopback, no host postgres command unless exposed; no production credentials.
- [x] Read-only check existing docker/Colima, attempt bounded startup only if safe/available within permissions; record actual command/result. Do not install global tools or alter external config. If blocked, readiness complete/execution unverified must remain conspicuous.
- [x] Run full suite, self-review, commit, report with actual execution evidence and blockers.

### Task 4: Truthful usable dashboard, portfolio documentation and portable verification
**Files:** Modify webpage/index.html, app.js, hypotheses.js, styles.css, data.json; README.md, requirements.txt, run_demo.sh/Makefile only to integrate Task 2; create docs/business-case.md, docs/claim-evidence.md, docs/completion-report.md, .github/workflows/verify.yml, tests/test_portability.py; optional scripts/verify.sh. Keep historical docs but add supersession pointer where claims differ.
**Interfaces:** Consumes Task 2 builder payload and Task 3 validation state. Produces documented single demo/build/verify path, dashboard with explicit evidence tabs/labels, run provenance and interpretable cases; no PM4Py goodness-of-fit presented as business compliance.
- [x] Add/run RED integration tests: fresh temp checkout without XES or extra packages can run demo and serve valid payload; missing optional data marked unavailable; dataset edits reflect in report; no local absolute paths in generated public payload. Test observable outputs, never grep prose source to simulate tests.
- [x] Correct stale KPI narratives, bootstrap and Odoo execution claims; show cohort sizes, unknown cases, rule version, generated source links and source type. Use available screenshot/browser tools for desktop/mobile usability verification; if unavailable report exact limitation.
- [x] Write concise README explaining problem, scope, sample findings and commands; business case separates measured observations from assumptions/cost scenarios and includes investigation workflow. Claim/evidence table links code/results/limits. Link historical report caveats rather than rewriting all research.
- [x] Add CI using same verification command; dependencies optional for core. Record optional installed scientific versions separately from core requirements. Generate final dashboard from actual data.
- [x] Run full suite, isolated demo, field aggregate consistency, browser/manual smoke; self-review, commit and report. Completion report states tested/unverified boundaries and user edits preserved.

## Final gates
- [x] Council: five independent perspectives, randomized anonymous peer reviews, synthesis and disposition.
- [ ] Independent task reviews and fixes; final whole-branch review, one combined fix wave if needed.
- [ ] Fresh full verification, artifact hashes, clean diff, delivery checkout/patch with precise original location and application guidance. No push or merge into original.

## Council refinement
Task 4 must explicitly state fictional policy authority, field rule-applicability/denominators, incomplete-case limitations, no operational accuracy claim, and raw XES exclusion. See docs/council-review.md for complete disposition.
