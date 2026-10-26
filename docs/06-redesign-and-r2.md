# Redesign + Round-2 Evaluation

> **Historical research note (superseded for current execution and claims).** This document retains its original analysis for provenance. Use [the current claim/evidence map](claim-evidence.md), [event contract](event-contract.md), and [ERP pilot](erp-pilot.md) for current limits and next steps. Old extraction SQL, causal/transfer wording, and hard-enforcement predictions here are not an executable or verified path; do not run the historical SQL.


## 1. Revised normative BPMN (v2)
```
PR create -> Approval -> [PO changed? --yes--> Re-approval] -> PO confirm
  -> Goods Receipt -> [Received? --no--> BLOCK invoice] -> Invoice (qty<=received, tol.0)
  -> [Excess qty? --yes--> BLOCK / credit note] -> Payment
+ SLA timers: approval >2d -> delegate/escalate; receipt >3d overdue -> follow-up
```

## 2. ERP configuration changes (Odoo)
| Target | Change | Type |
|---|---|---|
| S3 invoice-early | Bill control = "On received quantities"; block Bill validation if no done Receipt | config |
| S4 over-bill | 0 tolerance on 3-way match; block Bill > received, force adjustment/credit note | config |
| S6 unapproved edit | Lock confirmed PO; any qty/vendor change resets approval state, requires re-approval | design+config |
| S2/S5 delays | Approval SLA 2d with delegation; receipt overdue alert + buyer follow-up task | design |

## 3. Round-2 rerun (S3R/S4R/S6R, 20 each = 60 cases, 400 events)
Script: `src/generate_log_r2.py` (same schema, simulates enforced controls).
- S3R: invoice held until receipt -> normative order
- S4R: bill capped at received qty
- S6R: `... Approval -> PO Modification -> Approval (re-approval) -> PO ...`

## 4. Result
Checker: `python3 src/check_conformance.py data/event-log-r2.csv`
- R1 baseline (targeted S3/S4/S6, n=60): 60 violations (R2:20, R3:20, R4:20)
- R2 (n=60): **0/60 violations (-100%)** across R1-R5. Targeted deviations eliminated (-100%).
- Cost: S6R cycle 9.19d (median 9.28) vs S1 7.18 (+2.0d) / vs S6 8.04 (+1.15d re-approval overhead) — control/efficiency trade-off to discuss.
- S2/S5 temporal issues intentionally out of scope for R2; addressed by SLA proposal, not hard block (flexibility preserved).

## 5. Thesis claim
Process mining distinguished tolerable temporal variation (S2/S5: compliant but slow, performance-only signal) from undesirable control failures (S3/S4/S6: rule fires). Hard ERP controls eliminate the latter with measurable effect; soft SLA/escalation handles the former without killing flexibility.
