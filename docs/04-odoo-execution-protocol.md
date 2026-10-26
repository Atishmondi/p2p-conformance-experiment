# Odoo Execution Protocol (ERP artifact)

> **Historical research note (superseded for current execution and claims).** This document retains its original analysis for provenance. Use [the current claim/evidence map](claim-evidence.md), [event contract](event-contract.md), and [ERP pilot](erp-pilot.md) for current limits and next steps. Old extraction SQL, causal/transfer wording, and hard-enforcement predictions here are not an executable or verified path; do not run the historical SQL.


Controlled experimental study using Odoo Community 17. P2P scope only.

## 1. Instance
- `docker compose up -d`, open http://localhost:8069, DB `p2p-exp`
- Install: Purchase, Inventory, Invoicing. No multi-company, no custom valuation.

## 2. Master data (fixed for comparability)
- 3 vendors: Vendor_A, Vendor_B, Vendor_C
- 5 products: storable + purchaseable (e.g. P-01..P-05)
- Users/roles: requester, approver_1, approver_2, buyer, warehouse, accountant
- 1 purchase team, 2 approvers, 2-step approval on PR/PO.

## 3. Normative Odoo flow (maps to BPMN)
1. Purchase Request = Purchase Agreement / internal request (`Purchase Request` activity, resource=requester)
2. Approval (`Purchase Request Approval`, approver_1/2)
3. Request for Quotation -> Purchase Order confirm (`Purchase Order`, buyer)
4. Receipt (`Goods Receipt`, warehouse, Inventory -> Receipts -> Validate)
5. Vendor Bill (`Vendor Invoice`, accountant, bill with `Bill control`)
6. Register Payment (`Payment`, accountant)

## 4. Controlled execution: injected -> ERP behavior -> log signature
| Scenario | Inject | Odoo steps | Expected log signature |
|---|---|---|---|
| S1 | none | full flow in order | `PR->Appr->PO->Receipt->Invoice->Pay`, cycle ~7d |
| S2 | receipt +3d | confirm PO, wait before Validate receipt | same order, PO->Receipt 5d vs 2d baseline |
| S3 | invoice early | create/validate Bill before Validate receipt | `...PO->Invoice->Receipt->Pay`, violates R2 |
| S4 | over-bill | receipt qty=qo, bill qty=qo+2/5 | same order, `qty_invoiced > qty_received`, violates R3 |
| S5 | approval +2d | hold approval 3d instead of 1d | same order, PR->approval 3d, cycle 9d |
| S6 | edit PO post-approval | approve, then change qty/vendor, confirm without re-approval | `PR->Appr->PO-Modification->PO...`, violates R4 |

20 cases/scenario = 120 cases R1 (S1-S6); 20 each S3R/S4R/S6R = 60 cases R2. Staggered starts, same vendors/products rotated. Record every step with timestamp+user.

## 5. Extraction to event log
Export per document (request, PO, picking, bill, payment) with create/write/validate dates + user, then pivot to:
`case_id,activity,timestamp,resource,scenario,vendor,po_id,qty_ordered,qty_received,qty_invoiced`
Round-1 synthetic file `data/event-log-r1.csv` follows this schema exactly and is used when Odoo is offline; replace with real export row-for-row.

## 6. Hypotheses-first gate (pre-register before executing)
No scenario SHALL execute before pre-registration is recorded. No control SHALL be modified before lab-to-field comparison is recorded. Order is mandatory.

1. Pre-register: copy H1-H8 from `data/hypotheses.csv` into the run record, with predicted signature per rule from `src/signatures.py` (`lab_definition`, `applicable_scope`, `event_pattern`, `known_gaps`, plus `SCOPE_NOTES` strata: 2-way = R1 stratum; 3-way-after-GR = R2+R3 stratum; 3-way-before-GR = R3-only structural near-zero). Record `hypo_id, rule, predicted_signature, lab_rate, field_rate, status`.
2. Execute S1-S6 per §4 (20 cases/scenario, staggered starts, fixed masters per §2, normative flow per §3). No mid-batch control changes.
3. Extract via `sql/odoo_extract.sql` to the §5 schema (`case_id,activity,timestamp,resource,scenario,vendor,po_id,qty_ordered,qty_received,qty_invoiced`). Reject exports that do not match column-for-column.
4. Detect with `src/check_conformance.py` (`check_case`, R1-R5). Freeze detector version in the run record; do not tune thresholds post hoc.
5. Verify each hit against its signature: observed log pattern vs latent control flaw. `None` = not applicable (missing ts or wrong stratum); `False` = applicable and conformant; `True` = violation only if the `lab_definition` / `event_pattern` is met. Discard hits that fail the signature (recording-time artefacts, wrong stratum, approval-workflow exclusions per R4 `known_gaps`).
6. Compare lab rates to BPI field base rates before any redesign: R1 56.5% 2-way (590/1044), R2 0 after-GR (0/11128), R3 14.2% after-GR (1584/11128), R4 ~10.5% corrected qty/price (26366/251734). FLAG any lab deviation absent in field — S3 lesson: lab S3 20/20 = 1.0 vs field after-GR 0/11128 = 0.0 (H2 partial-contradiction); such deviations SHALL NOT drive field controls without a field-applicable falsifier verdict.
7. Only then modify control (S3R/S4R/S6R candidates) and re-run: 20 cases/redesign arm, same masters, same extract-detect-verify chain, report pre 60/60 -> post conformance plus absolute reduction.

Backbone (9 steps, in order):
1. define (normative flow §3 + R1-R5)
2. signatures (`src/signatures.py` + `SCOPE_NOTES`)
3. execute (S1-S6, §4)
4. extract (`sql/odoo_extract.sql` -> §5 schema)
5. detect (`src/check_conformance.py`)
6. verify (observed vs latent per signature)
7. modify (control change, justified by verified hits + field comparison)
8. rerun (S3R/S4R/S6R under identical conditions)
9. measure (lab delta + field base-rate comparison, FLAG untransferred fixes per H8).
