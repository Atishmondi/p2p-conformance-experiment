# Task 2 review

Reviewed base `217c471` through head `bc1f361`, using the Task 2 brief/report and binding completion specification. Source review was read-only; only this review file was written. The supplied diff filename was absent, so the equivalent `git diff 217c471..bc1f361` was reviewed, with targeted source reads for reporting validation and field definitions.

## Spec verdict: changes requested

The main Task 2 contract is implemented: actual conformance rows drive case/rule denominators; unknown outcomes remain excluded from their applicable denominators; v1/v2 and field versions remain separate; scientific imports are optional; the dashboard is deterministic and contains relative source hashes; normal demo outputs are isolated. The schema change and Task 4 UI handoff are explicit. One emitted field definition is materially inaccurate and needs correction before the evidence contract is accepted.

## Quality verdict: changes requested

The implementation is readable and compact. Input case/scenario/vendor consistency, explicit missing-field availability, strict JSON, no import-time writes, seeded subprocess generation, and fresh-directory protection are sound. One field-count validation gap permits contradictory evidence to be published. Findings are bounded below; no full suite was rerun.

## Findings

1. **P2 — Describe field R3 as a monetary-value proxy, not a quantity proxy.** `src/compare_lab_field.py:21` emits “invoice/order quantity proxy.” The actual analyzer at `src/analyze_bpic2019.py:315`–`326` extracts event `worth` from **Cumulative net worth** and checks maximum invoice worth against the first PO worth plus epsilon. This distinction matters to the binding requirement that incompatible field/lab definitions remain truthful. A targeted reproduction passed a PO worth of 100 and invoice worth of 101, with no quantities, and obtained `r3_viol=True`; the emitted definition still called this a quantity proxy. Describe the observed monetary-value comparison, including the maximum invoice/first PO basis; retain the warning that it differs from cumulative invoiced/received item quantities.

2. **P2 — Reject impossible applicable counts when a field stratum total is known.** `src/compare_lab_field.py:45`–`51` validates `n_cases` and individual metric numerator/denominator pairs independently but never checks `n_applicable <= n_cases`. A targeted call `_stratum({'n_cases': 1, 'r3_viol': {'n_true': 2, 'n_applicable': 2}})` succeeds and publishes two applicable/violating cases and a 100% rate in a one-case stratum. These metrics are per-case outcomes in the source analyzer, so this is contradictory input rather than another legitimate denominator. Reject it with a visible validation error. Cover the known-total inconsistency with a literal fixture; continue allowing missing/unknown totals and zero denominators.

3. **P3 — Preserve the known overall field case count in the dashboard contract.** `src/compare_lab_field.py:78` passes only `source['overall']` into `_stratum`, although the analyzer stores the overall case count at top-level `source['n_cases']`. Canonical reproduction returned source `n_cases=251734` but emitted `field.strata.overall.n_cases=null`. Per-metric denominators remain correct, so this does not change rates; it needlessly removes the overall cohort size that Task 4 should display. Propagate and validate the top-level total for the overall stratum. The implementation report currently permits null for absent embedded totals, so this is a nonblocking contract/handoff improvement.

## Verification assessed

- Accepted the supplied full-suite evidence: `python3 -S -m unittest discover -s tests` — 45 passing, plus deterministic fresh-root demo and canonical immutability checks. The tests exercise literal changed cohorts, unknown denominators, versions, missing files/field data, content hashes, imports, and stdlib CLI behavior.
- Ran only targeted read-only Python reproductions under `-S` for the three findings. Imports and direct canonical comparison succeeded without optional scientific libraries.
- Accepted controller evidence in `/tmp/p2p-validation/verification.md`: full raw UTC analyzer rerun preserved the 251734-case/1595596-event case CSV byte-for-byte and all numerical aggregates; only provenance metadata changed. Did not repeat the 728 MB XES analysis.
- Accepted controller's explicit SciPy run on Python 3.9.6/SciPy 1.13.1: legacy diagnostic chi-square 120, Fisher p approximately 2.07007e-35, Welch p approximately 3.33627e-08. No optional-scientific execution was claimed from the agent environment.

## Declined to judge

- Task 1 checker rule semantics beyond the reporting interface and tri-state consumption; Task 1 has a separate review.
- Task 3 ERP event adapter and actual runtime execution.
- Task 4 UI rendering, README, business case, and old static dashboard compatibility, intentionally outside Task 2.
- Historical raw-field proxy correctness or completeness. The narrow UTC/path/provenance change and controller reproduction were assessed; historical missing-event policies remain separate from lab v2.
- Independent proof of RED-before-GREEN chronology; final diff and reported execution evidence do not independently establish development order.
- Concurrent mutation of a run directory during a build. The report explicitly documents that hashes/evaluation are not an atomic multi-file snapshot; use stable input artifacts.

No implementation changes or full-suite rerun were made by this review.
