# Normative P2P Model

> **Historical research note (superseded for current execution and claims).** This document retains its original analysis for provenance. Use [the current claim/evidence map](claim-evidence.md), [event contract](event-contract.md), and [ERP pilot](erp-pilot.md) for current limits and next steps. Old extraction SQL, causal/transfer wording, and hard-enforcement predictions here are not an executable or verified path; do not run the historical SQL.


Scope strictly P2P only. No inventory valuation, no multi-company.

## Normative sequence
1. Purchase Request (create)
2. Purchase Request Approval (approve)
3. Purchase Order (confirm)
4. Goods Receipt (receive)
5. Vendor Invoice (record)
6. Payment (pay)

Rules:
- R1: Approval must precede PO confirm.
- R2: Receipt must precede invoice recording (3-way match).
- R3: Quantity invoiced <= quantity received (per line, tolerance 0).
- R4: No PO modification after approval without re-approval.
- R5: Payment only after invoice approval.

## Subquestions linked here
- Which variants emerge vs. this norm?
- Where do temporal vs. behavioral deviations occur?
- Design vs. configuration cause?
- What redesign reduces targeted deviations?
