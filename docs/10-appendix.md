# Appendix

## A. Formal R1–R5 predicates

Let a case be a timestamp-ordered event sequence `E = ⟨e_1, …, e_n⟩` with activity
`act(e)`, timestamp `ts(e)`, received quantity `qr(e)`, and invoiced quantity
`qi(e)`. Write `first(a)` for the earliest event with `act = a`, or ⊥ if absent.
Activity labels: PR = `Purchase Request`, AP = `Purchase Request Approval`,
PO = `Purchase Order`, GR = `Goods Receipt`, INV = `Vendor Invoice`,
PAY = `Payment`, MOD = `PO Modification`, RE-AP = `Purchase Request Approval (re-approval)`
(Round 2 only; `Approval` substring match covers both AP and RE-AP).

- **R1 (approval precedes order):** `first(AP) ≠ ⊥ ∧ first(PO) ≠ ⊥ ∧ ts(first(AP)) < ts(first(PO))`. Violation otherwise (covers missing approval or missing PO).
- **R2 (receipt precedes invoice; 3-way match ordering):** `first(GR) ≠ ⊥ ∧ first(INV) ≠ ⊥ ∧ ts(first(GR)) < ts(first(INV))`. Violation otherwise.
- **R3 (quantity match, tolerance 0):** let `qr = qr(first(GR))` if present else `qr(e_1)`, and `qi = qi(first(INV))` if present else `qi(e_1)`; compliant iff `qi ≤ qr`. Implemented per case on the quantity columns carried by every event.
- **R4 (no unapproved PO modification):** if no MOD event, compliant. Otherwise, for every MOD event `m`, there must exist an approval event `x` with `ts(m) < ts(x)` and (`first(PO) = ⊥` or `ts(x) < ts(first(PO))`). Round-1 S6 has exactly one MOD with one preceding approval and no intervening re-approval → violation; Round-2 S6R inserts RE-AP between MOD and PO → compliant.
- **R5 (payment after invoice; control rule):** `first(PAY) ≠ ⊥ ∧ first(INV) ≠ ⊥ ∧ ts(first(PAY)) > ts(first(INV))`. Zero violations in both rounds by design.

Checker: `src/check_conformance.py::check_case`; applied frozen to both rounds.

## B. Alignment cost note

`src/mining_pm4py.py` discovers a Petri net with the inductive miner on the full
Round-1 log, then reports token-based fitness/precision and per-case alignments
(one sampled case per scenario S1–S6). PM4Py alignment uses standard unit costs:
synchronous move 0; log-only or model-only move > 0. Because the net is
*discovered from* the same log, it accommodates all three observed variants, so
log fitness 1.0 (precision 0.9796; sampled alignment fitness 1.0 in all six cases;
`data/pm4py_results.json`) is expected and must NOT be read as normative
conformance against the BPMN model. The normative verdict comes exclusively from
the R1–R5 rule checker (Section A). PM4Py contributes variant confirmation (3
variants), diagnostic triangulation, and the precision penalty for the
discovered model's extra behaviour.

## C. Variant definitions

| Variant | Activity order | Frequency (R1) | Scenarios |
|---|---|---|---|
| V1 normative | PR → Approval → PO → Receipt → Invoice → Payment | 80× | S1, S2, S4, S5 (S2/S4/S5 hide in time/attributes, not order) |
| V2 swapped | PR → Approval → PO → Invoice → Receipt → Payment | 20× | S3 (= R2 violation) |
| V3 rework | PR → Approval → PO Modification → PO → Receipt → Invoice → Payment | 20× | S6 (= R4 violation) |

Round 2 (60 cases): S3R and S4R follow V1 (6 events each); S6R follows
PR → Approval → MOD → Approval (re-approval) → PO → Receipt → Invoice → Payment
(8 events; MOD strictly before re-approval strictly before PO). Total events:
R1 5×20×6 + 20×7 = 740; R2 20×6 + 20×6 + 20×8 = 400.

## D. Statistical formulas

Targeted comparison (fixed design): R1 S3+S4+S6 = 60 violations / 60 cases;
R2 S3R+S4R+S6R = 0 / 60. Contingency table rows R1/R2 × columns
[violations, non-violations] = [[60, 0], [0, 60]].

- **Pearson chi-square (no Yates correction):** χ² = Σ (Oᵢ − Eᵢ)² / Eᵢ, df = 1;
  reported χ² = 120, p = 6.326e-28 (`scipy.stats.chi2_contingency`, correction=False).
- **Fisher exact (two-sided; appropriate with zero cells):** hypergeometric
  probability of tables at least as extreme given fixed margins; reported
  p = 2.070e-35, odds ratio inf (`scipy.stats.fisher_exact`, alternative="two-sided").
- **Wilson 95% score interval (z = 1.96)** for k/n with p = k/n:
  (p + z²/2n ∓ z·√(p(1−p)/n + z²/4n²)) / (1 + z²/n);
  reported [0.9398, 1.0000] (R1) and [0.0000, 0.0602] (R2).
- **Cohen h (proportion magnitude):** h = |2·arcsin(√p₂) − 2·arcsin(√p₁)|;
  reported h = 3.1416 (= π for 1 vs 0).
- **Welch two-sample t (throughput, S1 vs S2 per-case cycle times, n = 20+20):**
  t = (x̄₁ − x̄₂) / √(s₁²/n₁ + s₂²/n₂); Welch–Satterthwaite df;
  reported t = −6.9402, df = 37.15, two-sided p = 3.336e-08,
  means 7.1838d vs 10.0257d (Δ = 2.8419d), medians 6.8438d vs 9.7675d.
- **Cohen d (throughput, average-variance form):** d = (x̄₂ − x̄₁) / √((s₁² + s₂²)/2);
  reported d = 2.1947 (s₁ = 1.1927, s₂ = 1.3896).

All values from `data/evaluation.csv` (`src/evaluate.py`); cycle times derived
dynamically as max(timestamp) − min(timestamp) per case and cross-checked against
`data/summary-r1.csv`.

## E. Stochastic generator specification

Business-hours clock (both rounds): base Monday 09:00 (R1 2026-01-05, seed 42;
R2 2026-02-02, seed 7); case start staggered +5h per case index; any timestamp
falling Saturday/Sunday rolled forward to Monday 08:00. Waits sampled via
`random.lognormvariate(μ, σ)` with μ = ln(mean) − σ²/2 (target mean in days),
then clipped; scenario/vendor shifts applied additively afterwards.

| Leg | Mean (d) | σ | Clip [lo, hi] (d) | Shifts / notes |
|---|---|---|---|---|
| PR → Approval | 1.0 | 0.35 | [0.3, 2.5] | S1-R1: +2.0 (S5 only, handover delay) |
| Approval → PO (handover) | 0.5 | 0.35 | [0.1, 1.5] | Keeps timestamps strictly increasing; not an activity |
| PO → Receipt | 2.0 | 0.45 | [0.5, 4.5] | S1-R1: +3.0 (S2 only); Vendor_B +0.5, Vendor_C −0.3 (floor 0.5) |
| Receipt → Invoice | 0.8 | 0.40 | [0.2, 2.5] | — |
| Invoice → Payment | 1.8 | 0.40 | [0.5, 4.0] | R1-S3 pay-after-receipt reuses this law |
| R1-S3 PO → Invoice | 0.6 | 0.40 | [0.2, 2.5] | Replaces PO → Receipt leg |
| R1-S3 Invoice → Receipt | 1.5 | 0.45 | [0.5, 4.5] | Replaces Receipt → Invoice leg |
| R1-S6 Approval → MOD; MOD → PO | 0.3; 0.3 | 0.35; 0.35 | [0.05, 1.0] each | Split of handover; single approval → R4 fires |
| R2-S6R Approval → MOD | 0.3 | 0.35 | [0.05, 1.0] | — |
| R2-S6R MOD → re-approval | 1.0 | 0.35 | [0.3, 2.5] | Full re-approval wait (≈ +1d control overhead) |
| R2-S6R re-approval → PO | 0.5 | 0.35 | [0.1, 1.5] | Same approver within case |

Resources (seeded draws per case): PR req_01–03; Approval approver_1/2
(R2-S6R same approver for both approvals); PO/MOD buy_01/02 (same buyer within
case); Receipt wh_01/02; Invoice/Payment acc_01/02. Quantities: ordered menu
[5, 10, 15, 20, 50] weights [35, 30, 15, 15, 5]; R1-S4: received = ordered,
invoiced = received + randint(2, 8); R1-S6 single quantity throughout (R3 clean);
R2-S3R/S4R capped (invoiced = received = ordered); R2-S6R ordered qo → qo2
(distinct menu value at MOD), received = invoiced = qo2 (R3 clean). Vendors
round-robin A/B/C by case number (40 cases each in R1).

## F. Reproduction table

| # | Command | Input | Output | Reported in |
|---|---|---|---|---|
| 1 | `python3 src/generate_log.py` | — (seed 42) | `data/event-log-r1.csv` (120 cases, 740 events) | §E; docs/05 |
| 2 | `python3 src/check_conformance.py data/event-log-r1.csv` | event-log-r1 | `data/conformance-r1.csv`, `data/summary-r1.csv` + stdout (variants, R1–R5, performance) | §§A, C; docs/05 |
| 3 | `python3 src/generate_log_r2.py` | — (seed 7) | `data/event-log-r2.csv` (60 cases, 400 events) | §E; docs/06 |
| 4 | `python3 src/check_conformance.py data/event-log-r2.csv` | event-log-r2 | `data/conformance-r2.csv`, `data/summary-r2.csv` (0/60 violations) | §A; docs/06 |
| 5 | `python3 src/evaluate.py` | event-log-r1, summary-r1, conformance-r1 | `data/evaluation.csv` (χ², Fisher, Wilson, h; Welch t, d; vendor strata) | §D; docs/00, 06 |
| 6 | `python3 src/noise_test.py` | event-log-r1 (read-only; in-memory drops) | `data/robustness.csv` (4 levels × 3 seeds; breakdown at 0.02) | docs/09 §2 |
| 7 | `python3 src/mining_pm4py.py` | event-log-r1 (requires pm4py) | `data/pm4py_results.json` (fitness 1.0, precision 0.9796, 3 variants, 6 alignments) | §B; docs/00 |

`make data && make check && make eval` runs steps 1–5. Requirements:
`requirements.txt` (pandas/numpy/scipy/matplotlib; pm4py optional, step 7 skipped
without it). Live-Odoo path (`docker compose up -d` + `sql/odoo_extract.sql`) is
documented in the README and swaps in row-for-row without schema change.
