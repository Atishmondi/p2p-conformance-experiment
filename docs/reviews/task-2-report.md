# Task 2 implementation report

Status: complete. Base: 217c471. Commit: bc1f3615312f606489dbedd1790d38d70096b0a4 (owned source, Makefile, wrapper and tests only).

## What changed

- Replaced fixed-cohort and import-time scientific reporting with data-derived JSON reporting. Core evaluation, comparison, dashboard, and demo use Python >=3.9 standard library. Importing modules performs no report writes and imports no optional numerical library.
- Required lab artifacts are conformance-r1.csv, conformance-r2.csv, event-log-r1.csv, event-log-r2.csv under the selected data directory. Missing files and invalid or inconsistent case metadata fail visibly. No static data fallback.
- Conformance rows are counted directly. Historical unversioned rows are labeled v1, explicit tri-state rows retain v2. Mixed versions inside a cohort fail; a targeted cross-cohort rate difference is unavailable when rule versions differ.
- Case status rates divide by compliant + violating, excluding not_evaluable status. Per-rule rates divide by cases minus unknown outcomes for that rule. A violating case can still have unknown rules. Empty/unknown-only denominators produce JSON null, never artificial zero. Missing designed scenario strata are included with empty samples and null rates.
- Overall and targeted cohorts are separately exposed. Targeting selects design strata S3/S4/S6 versus S3R/S4R/S6R; counts never assume a cohort size. All observed scenario/vendor strata derive from source rows. Event timestamps supply cycle durations, means, medians and sample standard deviations.
- Optional --scientific imports SciPy only when explicitly requested and computes diagnostics from current targeted counts/cycle samples. Diagnostic labels prohibit causal interpretation. Without SciPy, explicit requests fail with a clear dependency message. Default mode needs no SciPy/NumPy.
- Field results derive numerators, denominators, rates and Wilson intervals from bpic2019_results.json counts. Cached rates, historical falsifier verdicts, source_xes paths, and fixed lab anchors are not copied into dashboard/comparison reports. Field activity/quantity definitions differ from lab controls, so contrasts are explicitly comparable=false and strata are never pooled or subjected to a two-proportion test.
- Field absence is explicit availability=false. Present but missing strata get availability=false and empty metrics; zero/unknown applicable denominators produce null rates. Field structural False/proxy outcomes are observational proxy outcomes, not proof of complete-case compliance.
- Deterministic dashboard embeds relative source filenames, SHA-256 content hashes, evidence class and analysis rule version. No absolute source paths or run timestamps appear in the payload.
- Demo reserves a fresh root, uses sys.executable for subprocesses and propagates -S, generates both logs, runs the v2 checker, builds descriptive reports/dashboard, and optionally copies the small existing historical field JSON with source_xes reduced to a basename. It never needs XES or ERP. Existing output roots fail without mutation; nonpositive n fails before creating a root.
- Makefile default/demo/all and run_demo.sh now use isolated outputs. The wrapper works from unrelated working directories. data/check/eval/dashboard targets accept DATA_DIR; demo accepts OUTPUT_DIR. Canonical inputs/results were not changed.

## Narrow raw-field analyzer changes

Only paths, timestamp handling and provenance were adjusted: fresh raw analysis defaults to output/field, source_xes is a basename, and the output declares field-proxies-utc-v2 plus observational_field_summary. Offset-aware XES timestamps normalize to UTC before the existing naive UTC filter/order computations, instead of discarding offsets. This can change counts for non-UTC offsets/window boundaries. The checked-in historical summary remains historical-field-proxies-v1. The raw analyzer still retains its historical proxy definitions, missing-event treatment, and falsifier registry; those do not become v2 lab conformance outcomes. JSON output parents are created independently.

A tiny independent XES fixture verifies equivalent offset representations and fresh provenance. The full raw 728 MB XES was not rerun by this task. Controller was explicitly told to rerun raw verification before claiming new analyzer counts reproduce the historical artifact. No raw data was copied or modified.

## Public interfaces and commands

- evaluate.evaluate(data_dir: Path, scientific=False) -> dict; pure read/derive, no report write.
- compare_lab_field.compare(data_dir: Path, lab=None) -> dict; read/derive optional field evidence. Passing lab avoids re-evaluation. Direct missing-field result is explicitly unavailable; CLI validates required lab inputs regardless of field availability.
- build_dashboard.build(data_dir: Path, output_path: Path) -> dict; writes deterministic strict JSON (allow_nan=False), returns the same payload.
- Each analysis CLI accepts --data-dir DIR --out FILE. evaluate additionally accepts --scientific. Defaults read historical data/ and write output/reports/*.json, preserving canonical results.
- python3 -S src/demo.py --output-dir FRESH_DIR [--n 20] [--seed-r1 42] [--seed-r2 7] [--without-field]. Default root is output/demo. A missing default field summary behaves like --without-field; malformed present field data fails instead of silently disappearing.
- make demo OUTPUT_DIR=FRESH_DIR; make test; ./run_demo.sh --output-dir FRESH_DIR.
- Optional raw analysis: src/analyze_bpic2019.py [XES] --cases-out FILE --json-out FILE. make bpic writes refreshed field artifacts into DATA_DIR and compares against its already-built lab artifacts.

Demo files (10 with optional field): event-log-r1.csv, event-log-r2.csv, conformance-r1.csv, conformance-r2.csv, summary-r1.csv, summary-r2.csv, bpic2019_results.json, evaluation.json, comparison.json, dashboard.json. Without field, nine files. Summary CSV is checker output; dashboard derives counts from per-case conformance, avoiding cached aggregates.

## Exact dashboard contract for Task 4

Top-level schema_version is "2.0". Old static webpage keys are intentionally not preserved. UI integration is Task 4; no UI assets/README were edited here.

- lab: evaluation payload, with evidence_class="synthetic_demonstration".
- lab.cohorts.r1 and .r2: {rule_version, evidence_class, overall, targeted, targeted_scenarios, scenarios}. scenarios maps scenario ID to a summary. Explicit version is v1/v2; an empty cohort has null rule_version.
- Every summary (overall, targeted, scenario, vendor): {cases, compliant, violating, not_evaluable, evaluated_cases, violation_rate, conformance_rate, wilson_95, rules}. Rates are fractions 0..1, not percentages. wilson_95=[lower,upper] describes violation rate. Unknown intervals are [null,null].
- summary.rules.R1 through R5: {violating, compliant, not_evaluable, evaluated_cases, violation_rate, wilson_95}. The rule evaluated denominator can differ from the case-status denominator.
- lab.throughput.r1/.r2: scenario -> {n, mean_days, median_days, stdev_days}; stdev is null for fewer than two observations, other aggregates null with none. These are first-to-last observed event durations in days, not business-calendar times.
- lab.vendors.r1/.r2: vendor name -> summary. Missing vendor metadata uses "(unknown)". Names are derived, not fixed to three vendors.
- lab.targeted_comparison: {comparable, absolute_rate_difference, relative_rate_difference, interpretation}. Difference is R1 targeted minus R2 targeted; relative divides by nonzero R1 targeted rate. Null if unavailable or versions differ. This is a generated-cohort descriptive comparison.
- lab.scientific in the default dashboard: {requested:false,available:false}. evaluate --scientific additionally exposes chi2, chi2_p, fisher_p, fisher_oddsratio, cohens_h, welch_t, welch_p, welch_df, cohens_d_cycle and interpretation, with undefined values null. The builder always uses descriptive mode.
- field: {available, source, evidence_class, rule_version, strata, contrasts, definitions, limitations}, plus unavailable_reason when absent. source="bpic2019_results.json". evidence_class="observational_field_summary". Default historical version is historical-field-proxies-v1; explicitly versioned raw analysis retains its own version, currently field-proxies-utc-v2. Do not call either field version lab v2.
- field.strata has overall, two_way, three_way_after, three_way_before and any "item_category:" + source category keys. Each is {available,n_cases,metrics}. n_cases can be null when not present at that source stratum. Each metric is {n_true,n_applicable,rate,wilson_95}; numerators/denominators may be null. Supported source metric names: r1_maverick, r2_viol, r3_viol, r4_rework, r5_viol, approval_change_after_po. A missing metric is absent, not zero.
- field.contrasts: separate contextual lab/field records {lab_era,lab_scenario,lab_rule,lab,field_stratum,field_metric,field,comparable:false,reason}. lab is the rule summary above, field is the field metric or null. No difference or pooled significance statistic is emitted because definitions are incompatible.
- field.definitions maps field metric names to plain-language proxy caveats. Present these with field results. field.available=false has strata={} and contrasts=[]; do not substitute static values.
- provenance: {builder:"build_dashboard.py",sources,path_base,historical_note}. sources is a filename-sorted array of {path,sha256,evidence_class,rule_version}. Paths are relative to selected input root, hashes use source bytes. Event source rule_version identifies the checker interpretation applied in the report; event logs themselves do not assert a checker version. Optional field source is included only when available.
- limitations: combined lab/field limitation strings for display. No run timestamps or source absolute paths are included.

## TDD and validation evidence

Tests were written and run RED before corresponding implementation. Initial reporting regression demonstrated the old unconditional NumPy import failing under -S; missing builder/API features also failed. Initial demo tests failed because demo.py did not exist. Later targeted RED checks caught absent v2 evidence columns, unguarded mixed-version comparison, and incorrect timezone-offset handling; all were fixed and rerun GREEN.

Focused GREEN commands:

- python3 -S -m unittest discover -s tests -p test_reporting.py — 13 passed.
- python3 -S -m unittest discover -s tests -p test_demo.py — 2 passed.

Full suite (project test command under stdlib-only interpreter):

- python3 -S -m unittest discover -s tests — 45 passed in 2.619 s, no failures/skips. This includes the prior 30 conformance/run tests.
- git diff --check — clean.

Independent manual verification ran make demo with PYTHON="<sys.executable> -S" and direct python3 -S demo in two fresh temp roots at default n=20. All 10 files were byte-identical, without ignoring any timestamps. Results: R1=120 total, 60 violating, R3=40; R2=60 total, 0 violating. Wrapper succeeded from an unrelated cwd. Historical canonical build retained v1 and R3=20. Automated demo tests independently hash all checked-in small CSV/JSON artifacts before/after and verify immutable canonical content, duplicate-root rejection, field omission and n validation.

SciPy is unavailable in this Python environment: the explicit dependency-failure path passed, and the optional dynamic diagnostics have a conditional fixture check for environments that install SciPy. Optional numerical result execution is therefore not claimed here.

## Self-review / limitations / handoff

- No canonical data, historical checker, ERP code, UI assets or README changed. Task 1 report modification was deliberately left untouched/uncommitted.
- Field source summary and lab source CSV are trusted local artifacts, with validation of counts/statuses and provenance hashes. Hashes identify bytes; they do not attest the historical source dataset's completeness.
- Dashboard generation is deterministic for unchanged inputs. Reports do not supply an atomic snapshot if another process edits source files concurrently; build from a stable run directory.
- Demo is intentionally fresh-directory only. Repeating the default root requires selecting a new root (OUTPUT_DIR or --output-dir); no silent output replacement.
- Raw analyzer's legacy missing-time/event policies remain observational proxy semantics. No claim of operational savings, Odoo execution, or common lab/field inferential denominator is made.
- Task 4 should build a default payload from canonical inputs for a historical v1 view or isolated demo inputs for explicit v2, use the contract above, render null as unavailable, display evidence classes/versions/denominators, and show separate field strata.

## Task 2 review fixes (after bc1f361)

All three findings in task-2-review.md were accepted. `field.definitions.r3_viol` now identifies the raw analyzer's Cumulative net worth monetary-value proxy: maximum invoice worth compared with first PO worth plus epsilon. It states explicitly that this differs from the lab's cumulative invoiced/received item quantities.

Each present field stratum now rejects a metric's `n_applicable` greater than its known `n_cases`; missing totals and zero denominators retain their prior unknown/null handling. The top-level field `n_cases` is validated and used for `field.strata.overall.n_cases`; a conflicting embedded `overall.n_cases` fails visibly. If the top-level total is absent/null, an embedded overall total is used when available. No new dashboard keys were added. The checked-in historical summary now yields `field.strata.overall.n_cases=251734` instead of null, so Task 4 can display the known cohort size. The optional `n_events_filtered` remains outside this reporting contract.

Independent literal regressions were added first and failed for each finding (3 failures among 16 reporting tests). After the fix, `python3 -S -m unittest discover -s tests -p test_reporting.py` passed all 16, and `python3 -S -m unittest discover -s tests` passed all 48 once. A read-only canonical comparison confirmed overall n_cases=251734 and the corrected definition; `git diff --check` passed. The modified Task 1 report was left untouched.
