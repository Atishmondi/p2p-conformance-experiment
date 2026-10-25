# P2P project completion specification

## Problem and audience
How might we let a master's reviewer or consulting interviewer reproduce a purchasing-control analysis and understand exactly what its evidence supports? Primary user: Atish, CSE graduate moving toward information systems and technology consulting. Reader: a newcomer with Python and five minutes, not a process-mining specialist. Success is a truthful, testable demonstration and documented ERP readiness, never manufactured operational savings.

## Idea refinement
1. **Reproduction first — Simplification.** One command builds evidence and dashboard from checked-in small inputs; attacks the assumption that more features improve credibility.
2. **Try to disprove the checker — Inversion.** Independent counterexamples and unknown outcomes expose weak evidence; attacks generator/checker circularity.
3. **Control assurance brief — Audience shift.** Explain what an analyst should investigate and what false positives cost; attacks research-jargon-first presentation.
4. **Event contract plus ERP adapter — Combination.** Bind analysis to auditable source records; attacks the assumption that any timestamp/quantity export is adequate.
5. **Live Odoo experiment — Constraint removal.** Run bounded real transactions with recorded outcomes; highest practical value but requires a working daemon and audit instrumentation.
6. **Universal process platform — 10x version.** Many ERP systems and tenants would broaden use but dilute this portfolio demonstration; excluded.

Convergence: reproducible analysis (high value/high feasibility), honest ERP integration (high value/runtime constrained), universal platform (low present value/high cost). Choose first plus bounded second. Independent fixture correctness and reproducibility are essential; actual market demand is not asserted.

## Grilling decisions (recommended answers adopted per user instruction)
Round 1: audience = portfolio reviewers and Atish; completion = runnable evidence-backed demonstration; budget = existing local/open-source tools; historical findings = retain and explicitly version.
Round 2: checker input = one case represents one comparable item/unit, explicit event-delta quantities for receipt/invoice rows; malformed input = visible validation error, absent evidence = not evaluable; multiple events = chronological cumulative receipts/invoices; no inferred approval timing.
Round 3: actual Odoo = attempt only with existing runtime, record blocker honestly; publication = no push/deployment; baseline = immutable v1 script/results retained; v2 = explicit report version; documentation = concise front door with historical archive pointers.
Round 4: execution = isolated checkout due moved original and write limits; TDD plus task reviews; parallelism = independent council/review/exploration, sequential implementers; final = complete all verifiable deliverables and distinguish ERP runtime blocker. No unresolved design decisions requiring user input.

## Binding contract
- Preserve current original edits and canonical synthetic CSV inputs; do not overwrite raw BPI data or duplicate the 728 MB XES.
- Core demo and tests run using Python >=3.9 standard library. Scientific analysis/PM4Py are optional extras. No hosted services required.
- Preserve a v1 checker snapshot for historical reproducibility; new outputs identify rule version v2.
- Existing check_case tuple interface remains usable. Rule dict values are True (violation), False (evaluated compliant), or None (insufficient evidence). Consumers MUST not count None as compliant.
- Input CSV requires case_id, activity, timestamp; scenario/resource/vendor/po_id optional. Quantity fields accept finite nonnegative decimals; blanks are unknown, malformed/nonfinite/negative values rejected. Timestamp parsing accepts ISO, normalizes aware values to UTC; mixed naive/aware timestamps rejected per case. Never invent ordering.
- Receipt qty_received and invoice qty_invoiced are event deltas in one item/unit per case. R3 checks cumulative invoicing versus received quantity available at each invoice; unknown relevant quantity yields None unless a violation is already provable. Repeated same-event IDs must fail validation; without IDs reject exact duplicate events. Conflicting product_id/unit within a case fails validation; unsupported returns/reversals must be rejected, not silently accepted.
- R1: approval precedes each PO event; R2: each invoice has a prior receipt; R4: every modification has subsequent approval before next PO; R5: payment follows an invoice. Missing evidence/equal ambiguous timestamps is None where ordering cannot be determined. Empty trace must not crash.
- CLI allows explicit --output-dir. Outputs include per-case violations, not_evaluable rules, status and rule_version. Separate compliant/violating/not_evaluable denominators. No canonical clobber from run manager; validate n>0, safe single-component tag; duplicate tag fails rather than overwriting; unique default tag.
- Evaluation counts are derived from actual conformance rows; field comparison counts from bpic2019_results.json. Statistics remain diagnostic, no causal interpretation of generated cohorts. Missing input fails clearly.
- Dashboard JSON is built from artifacts, deterministic, includes provenance/versions/evidence classes, cohort denominators and limitations; no stale fallback numbers. Normal demo requires no XES or ERP.
- ERP adapter only consumes an explicit auditable recorded-event export; no invented +1s, no date-only substitute for recorded action, no heuristic payment matching. Unverified legacy SQL must not remain the recommended executable path. Validate strict contract and preserve source IDs. Record attempted runtime evidence; do not label fixture/simulation as Odoo execution.
- Fresh-clone commands, CI, integrity/portability tests, concise README and business case are deliverables. Raw field rerun optional and separate. No SaaS/auth/LLM integration; no new promotional video in this change.

## Assumptions and validation
- Adequate source evidence is not guaranteed: unknown outcomes expose gaps; independent tests pin semantics.
- Existing lab logs use one receipt/invoice per case: preserve baseline counts and compare v1/v2, explain any difference.
- Field proxies differ from lab rules: retain observational interpretation and strata, never pool incompatible denominators.
- Odoo may not expose history from snapshots: adapter requires recorded audit events; unsupported observations remain open.
