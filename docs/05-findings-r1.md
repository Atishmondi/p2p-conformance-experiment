# Findings Round 1 (120 cases, 740 events)

> **Historical research note (superseded for current execution and claims).** This document retains its original analysis for provenance. Use [the current claim/evidence map](claim-evidence.md), [event contract](event-contract.md), and [ERP pilot](erp-pilot.md) for current limits and next steps. Old extraction SQL, causal/transfer wording, and hard-enforcement predictions here are not an executable or verified path; do not run the historical SQL.


Tool: `src/check_conformance.py` (rule-based R1-R5 + variants + performance; PM4Py-compatible CSV).

## 1. Discovery / variants (3)
- V1 normative order (80x): `PR -> Approval -> PO -> Receipt -> Invoice -> Payment` — covers S1, S2, S4, S5. S2/S4/S5 hide in attributes/time, not order.
- V2 swapped (20x, =S3): `... PO -> Invoice -> Receipt -> Pay`
- V3 rework (20x, =S6): `PR -> Approval -> PO Modification -> PO -> ...`
Fitness vs normative BPMN: 80/120 ordered-conformant (strict normative order; 100/120 if V3 rework insertion counted as order-preserving), 60/120 fully rule-conformant. Fitness = discovered-model scope (vs discovered inductive net, not normative BPMN).

## 2. Conformance (R1-R5)
- R1 approval<PO: 0 violations (approval always logged before PO in R1 data)
- R2 receipt<invoice: 20 violations — all S3
- R3 invoiced<=received: 20 violations — all S4 (over-billed +2/+5)
- R4 no unapproved PO mod: 20 violations — all S6
- R5 payment after invoice: 0 violations (control)
Detection rate: 60/60 injected behavioral deviations caught, 0 false positives in S1.

## 3. Performance (mean days, stochastic — from data/summary-r1.csv)
- S1 baseline: cycle 7.18, PR->approval 1.17, PO->receipt 2.76
- S2: cycle 10.03 (+2.84d vs S1), PO->receipt 5.61 — temporal deviation, no rule fire
- S5: cycle 9.71 (+2.53d vs S1), PR->approval 3.26 — bottleneck at approver handover
- S3 cycle 7.24 / S4 cycle 7.70 / S6 cycle 8.04 (behavioral, not slower) — speed hides non-compliance.

## 4. Deviation taxonomy
| Type | Cases | Temporal? | Design vs config | Log signature | Detection |
|---|---|---|---|---|---|
| Invoice-before-receipt (S3) | R2 | no, ordering | config: bill control not enforced | V2 swap | order check |
| Over-billing (S4) | R3 | no, data | config: tolerance/block missing | qi>qr | attribute check |
| Unapproved PO change (S6) | R4 | no, rework | design+config: no re-approval gate | V3 + mod event | rework check |
| Late receipt (S2) | — | yes waiting | design: no SLA/follow-up | long PO->receipt | performance |
| Late approval (S5) | — | yes handover | design: single approver, no delegation | long PR->approval | performance |

## 5. Flexibility vs undesirable deviation
S2/S5 delays are *tolerable variation* (slow but compliant) unless SLA-bound; S3/S4/S6 are *undesirable non-compliance* (control failures: 3-way match, spend control). Mining distinguishes them: ordering/attribute checks fire only on the latter; performance analysis catches the former. This answers the centerpiece question directly.
