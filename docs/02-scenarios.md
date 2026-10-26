# Controlled Scenarios S1-S6

> **Historical research note (superseded for current execution and claims).** This document retains its original analysis for provenance. Use [the current claim/evidence map](claim-evidence.md), [event contract](event-contract.md), and [ERP pilot](erp-pilot.md) for current limits and next steps. Old extraction SQL, causal/transfer wording, and hard-enforcement predictions here are not an executable or verified path; do not run the historical SQL.


Each case has: known injected deviation -> expected ERP behavior -> expected log signature.

- S1 Happy path: PR -> approve -> PO -> receipt -> invoice -> pay. No deviation. Baseline for cycle time.
- S2 Delayed receipt: receipt delayed +3d after PO. Tests temporal deviation, waiting-time detection.
- S3 Invoice before receipt: invoice recorded before receipt. Violates R2. Tests ordering violation.
- S4 Quantity mismatch: invoiced qty > received qty. Violates R3. Tests 3-way match.
- S5 Approval delay: approval delayed +2d. Tests handover/bottleneck attribution.
- S6 PO modification after approval: qty/vendor change post-approval without re-approval. Violates R4. Tests rework + config control.

## Execution plan
20 cases per scenario = 120 cases total for round 1 (S1-S6). Same master data (3 vendors, 5 products) for comparability.
Round 2 after redesign: rerun S3/S4/S6 with 20 each = 60 cases for round 2 to measure reduction.

## Log schema (minimal XES-like CSV)
case_id, activity, timestamp, resource, scenario, vendor, po_id, qty_ordered, qty_received, qty_invoiced
