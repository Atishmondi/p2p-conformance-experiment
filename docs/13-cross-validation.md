# Lab-vs-Field Cross-Validation: Synthetic P2P Experiment vs BPIC 2019

## 1. Purpose and pre-registration

This report cross-validates the laboratory P2P conformance findings
(R1–R5; scenarios S1–S6 and redesigns S3R/S4R/S6R) against field
observations from the BPI Challenge 2019 purchase-order-handling log
(n_cases = 251,734; n_events_filtered = 1,595,596; full corrected run
`data/bpic2019_results.json`; field report `docs/11-bpic2019-results.md`).

The comparison tests hypotheses H1–H8 pre-registered in
`data/hypotheses.csv` and the falsifiers A–C pre-registered in
`docs/07-real-dataset.md`. The unit of comparison is the
rule-in-applicable-cohort, not the population-wide rate: laboratory
applicable cohorts (n = 20 per scenario) are compared only to the field
stratum where the corresponding rule or proxy is defined as applicable
(see §2). All rates below are reported as n_true / n_applicable = rate.
No rate is quoted without its denominator.

## 2. Mapping premise and denominator discipline

Rule signatures are single-sourced in `src/signatures.py::describe`
(lab `src/check_conformance.py::check_case` vs field
`src/analyze_bpic2019.py::evaluate_case`). Applicable scopes:

- **R1 (maverick proxy).** Lab: approval order, all cases. Field:
  `Vendor creates invoice` < `Create Purchase Order Item`, interpreted
  only in the 2-way-match stratum (n = 1,044), where no receipt step
  exists and vendor-invoice-before-PO is the published F1 pattern. No
  laboratory 2-way arm exists; H1 therefore has no lab rate.
- **R2 (receipt must precede invoice recording).** Lab: Goods Receipt <
  Vendor Invoice, all cases; applicable cohort S3 (n = 20). Field:
  first `Record Invoice Receipt` < first `Record Goods Receipt`,
  applicable ONLY in 3-way-match invoice-after-GR where both timestamps
  exist (n_applicable = 11,128 of n_cases = 15,182). Before-GR
  (n_cases = 221,010), 2-way (n = 1,044), and Consignment
  (n = 14,498) carry n_applicable = 0 by design.
- **R3 (value-match proxy for qty invoiced ≤ qty received, tolerance 0,
  epsilon 0.01).** Lab: quantity fields, applicable cohort S4 (n = 20).
  Field: max worth at `Record Invoice Receipt` > PO worth at first
  `Create Purchase Order Item` + 0.01, applicable in both 3-way strata:
  after-GR n_applicable = 11,128; before-GR n_applicable = 199,564;
  pooled n_applicable = 210,692. The before-GR stratum is a structural
  near-zero (no GR reference at invoice time); only after-GR is
  falsifiable. R3 value-match proxy is proxy-to-rule, not rule-to-rule
  (`docs/11-bpic2019-results.md` Q1).
- **R4 (corrected: qty/price-only rework).** Lab: PO Modification without
  re-approval, applicable cohort S6 (n = 20). Field: any `Change
  Quantity` / `Change Price` with ts > `Create Purchase Order Item` ts,
  all PO-bearing cases (n_applicable = 251,734; strata denominators
  1,044 / 15,182 / 221,010 / 14,498). `Change Approval for Purchase
  Order` after PO is routine workflow, EXCLUDED from R4 and tracked
  separately as `approval_change_after_po` (overall 4,290/251,734) and
  `approval_only` (approval true AND R4 false; 3,301/251,734).
- **R5 (clear without record).** Lab: Payment vs Vendor Invoice, all
  Round-1 cases (0 violations in n = 120; no signal). Field: `Clear
  Invoice` without `Record Invoice Receipt`, all cases
  (n_applicable = 251,734).
- **Redesign (H8).** Lab: S3/S4/S6 (pre: 60/60 = 1.000) →
  S3R/S4R/S6R (post: 0/60 = 0.000). Field transfer UNTESTED (no field
  intervention observed).

## 3. Per-rule cross-validation table

Delta = field stratum rate − lab applicable-cohort rate. Field stratum
is the stratum where the rule is applicable (see §2), not the pooled
population. Falsifier verdicts (A/B/C) are from the full corrected run.

| H | Rule | Lab applicable-cohort rate + n | Field stratum rate + n | Delta | Verdict (H-status; falsifier) |
|---|---|---|---|---|---|
| H1 | R1 maverick | n/a (no 2-way lab arm) | 2-way: 590/1,044 = 0.5651 (overall for reference: 3,450/251,734 = 0.0137) | n/a | **supported** (field-stratum; reproduces F1 ~0.56) |
| H2 | R2 ordering viol. | S3: 20/20 = 1.0000 (overall Round-1 anchor: 20/120 = 0.1667) | after-GR applicable: 0/11,128 = 0.0000 (of n_cases = 15,182) | −1.0000 | **nuanced** (partial contradiction; falsifier A INCONCLUSIVE: block viol null vs compliant 0.2056) |
| H3 | R3 value-match proxy, after-GR | S4: 20/20 = 1.0000 | after-GR: 1,584/11,128 = 0.1423 (pooled for reference: 1,584/210,692 = 0.0075) | −0.8577 | **supported-as-proxy** (magnitude lower; falsifier B REFUTED tolerance-0; correction_given_viol after = 0.1572) |
| H4 | R3 value-match proxy structural zero, before-GR | n/a (no lab before-GR arm) | before-GR: 0/199,564 = 0.0000 (of n_cases = 221,010) | n/a (structural) | **supported** (structural zero; falsifier B before-arm 0.0) |
| H5 | R4 qty/price rework | S6: 20/20 = 1.0000 | overall: 26,366/251,734 = 0.1047; strata: after-GR 1,882/15,182 = 0.1240, before-GR 23,315/221,010 = 0.1055, 2-way 10/1,044 = 0.0096, Consignment 1,159/14,498 = 0.0799; base F2 = 0.0215 (0.0134 + 0.0078) | −0.8953 (overall) | **nuanced** (persists >> F2 base, but transferability NOT established; falsifier C REFUTED on rate (10.47% persists), NUANCED on attribution/transfer (H8 open)) |
| H6 | R4 approval exclusion | n/a (no lab approval arm; S6 rework is qty/price) | 2-way approval_change_after_po: 1,000/1,044 = 0.9579 vs R4-rework 10/1,044 = 0.0096; overall approval_only: 3,301/251,734 = 0.0131 (of approval 4,290/251,734 = 0.0170) | n/a | **supported** (routine workflow correctly excluded from corrected R4) |
| H7 | R5 rarity | Round-1: 0/120 = 0.0000 (no signal) | overall: 408/251,734 = 0.0016; strata: 2-way 0/1,044 = 0.0000, after-GR 9/15,182 = 0.0006, before-GR 399/221,010 = 0.0018 | +0.0016 | **supported** (rare, < 0.01 in all strata) |
| H8 | redesign transfer | pre 60/60 = 1.0000 (S3 20/20 + S4 20/20 + S6 20/20) → post 0/60 = 0.0000 (S3R/S4R/S6R conformance 1.0) | n/a (UNTESTED; no field intervention) | n/a | **open** (lab effect 1.0 → 0.0 does not license a field claim) |

Pooled-rate warning (from `docs/11-bpic2019-results.md` Q3): the pooled
R3 value-match proxy rate 1,584/210,692 = 0.0075 obscures the stratum contrast
(1,584/11,128 = 0.1423 after-GR vs 0/199,564 = 0.0000 before-GR) and
must not be quoted alone. The R2 zero 0/11,128 = 0.0000 is a
stratum-applicable zero, not a population zero.

## 4. Mechanism finding: the control operates at RECORDING

The central mechanism result reconciles the apparent tension between
vendor-side earliness and system-side compliance.

In the after-GR stratum (n_cases = 15,182), `Vendor Creates Invoice` <
GR occurs in 5,754 cases (of 127,731 such vendor-early cases overall:
121,977/221,010 before-GR + 5,754/15,182 after-GR), yet `Record Invoice
Receipt` < GR occurs in 0 after-GR cases (0/11,128 applicable; probe
n = 40: 0 invoice < GR; probe n = 39 with clear: 0/39 clear < GR given
clear). The full-scan 1704-reconciliation confirms the pattern: D1
invoice < GR n = 16,356 sits entirely in the compliant before-GR
stratum (0 in after-GR); D2 clear < GR n = 89 and D4 record+clear < GR
n = 89 likewise entirely before-GR; D3 invoice-without-GR n = 1,009
(322/221,010 before-GR + 687/1,044 2-way), 0 in after-GR.

Hence the enforced ordering control operates at RECORDING, not at
vendor action: vendor-side early invoicing (5,754/15,182 after-GR cases
at the vendor-action timestamp) is absorbed before the system records
the invoice, leaving R2 ordering at the recording timestamps intact
(0/11,128 = 0.0000). Any comparison to the published 1,704
record+clear-before-GR sequences must specify vendor-action vs
system-recording semantics; under the system-recording definition used
by R2, after-GR compliance is exact.

Analytical consequence — observed vs latent/control-relevant behaviour:
the laboratory S3 scenario (20/20 = 1.0000 invoice-before-recording
violations) models latent vendor behaviour that is control-relevant
only if it reaches the recording stage. In this field setting that
latent mass is censored by the recording gate: the behaviour the lab
manipulates (vendor sends early) is observed (5,754 after-GR vendor-early
cases), but the behaviour the control governs (system records early) is
absent (0/11,128). Falsifier A therefore returns INCONCLUSIVE formally
(block viol null vs compliant 2,288/11,128 = 0.2056; delay viol null vs
  compliant median 26.32 days; payment-signal compliant
  9,925/11,128 = 0.8919) while constituting a partial contradiction
substantively: the Round-2 billing-block redesign targets a non-problem
in this field setting because there is no invoice-before-recording mass
to block.

## 5. What the laboratory got right

Three laboratory regularities survive the field check in attenuated or
re-scoped form, each with denominators.

**(a) Maverick base rate (H1, supported).** The field 2-way stratum
reproduces the published F1 magnitude almost exactly: 590/1,044 =
0.5651 vs F1 ~0.56, against an overall background of 3,450/251,734 =
0.0137. The laboratory's premise that 2-way procurement without a
receipt gate concentrates maverick buying is therefore quantitatively
confirmed in the matching stratum and denominator. Field 3-way R1
readings (after-GR 319/15,182 = 0.0210; before-GR 2,541/221,010 =
0.0115) are reported for completeness but are not the maverick
construct.

**(b) R3 value-match proxy existence (H3, supported-as-proxy).** The laboratory S4
effect (20/20 = 1.0000 over-billing under tolerance 0) exists in the
field as a non-trivial after-GR value-match proxy mass: 1,584/11,128 =
0.1423, with probe confirmation that the mass sits above 1.0/10.0 EUR
(max delta 549.0; probe after-GR 1/40 > 10) and is therefore not
rounding noise (epsilon 0.01; probe before-GR 0/80 > 0.01, max delta
0.0). The direction replicates; the magnitude scales down
(delta −0.8577), as expected when moving from a deterministic 1.0 lab
cohort to a field stratum.

**(c) R4 strict persistence (H5, nuanced).** The laboratory S6 effect
(20/20 = 1.0000 unapproved-modification violations under the strict
lab definition) persists in the field as corrected qty/price-only
rework at 26,366/251,734 = 0.1047 — above the published F2 base 0.0215
(Change Quantity 1.34% + Change Price 0.78%) — in both enforced-regime
strata: after-GR 1,882/15,182 = 0.1240 and before-GR 23,315/221,010 =
0.1055 (2-way 10/1,044 = 0.0096; Consignment 1,159/14,498 = 0.0799).
Strict-construction rework is therefore not a laboratory artifact: it
occurs at scale under the field GR/invoice regime.

## 6. What the laboratory got wrong

Three laboratory assumptions fail or require redefinition in the field,
each with denominators.

**(a) S3 absent in field (H2, nuanced / partial contradiction).** The
laboratory S3 pattern — 20/20 = 1.0000 applicable-cohort violations,
20/120 = 0.1667 overall — has no counterpart in the field stratum where
R2 applies: 0/11,128 = 0.0000 after-GR. The §4 mechanism explains the
absence (recording gate absorbs 5,754 vendor-early cases to 0 recorded
early), but the cross-validation verdict stands: the lab's most
deterministic violation scenario describes behaviour that does not reach
the control point in this field setting.

**(b) Zero-tolerance R3 value-match proxy artifact (H3/H4; falsifier B REFUTED).** The
laboratory tolerance-0 quantity rule describes neither field stratum.
After-GR value deltas > 0 are routine (1,584/11,128 = 0.1423) with low
correction given violation (0.1572 = 249/1,584), refuting tolerance 0
as an enforced norm (refuted-if: max rate > 0.05 with correction <
0.50). Before-GR is a structural zero (0/199,564 = 0.0000) because no
GR reference exists at invoice time — compliant by design, not evidence
of enforcement. Tolerance 0 is thus an artifact of the lab as an
enforced norm: one stratum routinely violates it, the other vacuously
satisfies it.

**(c) Change-Approval conflation (H6, supported as exclusion).** The
laboratory R4 construct (PO Modification → re-approval) conflates, if
transferred naively, two field objects that differ by two orders of
magnitude in 2-way: `Change Approval for Purchase Order` after PO
1,000/1,044 = 0.9579 (probe 60 2-way cases: approval 57/60 = 0.9500)
vs corrected qty/price rework 10/1,044 = 0.0096 (probe: Quantity 0/60 =
0.0000, Price 1/60 = 0.0167). Overall the distinction is 4,290/251,734
= 0.0170 approval-change vs 26,366/251,734 = 0.1047 rework, with
approval-only (no qty/price rework) 3,301/251,734 = 0.0131. The
exclusion is load-bearing: quoting any-change (57/60 = 0.9500 in probe
2-way) as R4 inflates 2-way rework fifty-fold. The lab got the
direction of the fix right (re-approval gates) but the object of the
gate wrong unless approval workflow is separated from qty/price rework.

## 7. Constrained redesign claim (H8: open)

The laboratory redesign (S3/S4/S6 → S3R/S4R/S6R) drives applicable-cohort
violations from 60/60 = 1.0000 to 0/60 = 0.0000 (absolute reduction
1.0; conformance 1.0 post). No field transfer is established: H8 is
OPEN (field rate n/a; falsifier ref UNTESTED).

The constraint this cross-validation imposes on any redesign claim is
twofold. First, **gates must target the recording stage, not the vendor
action.** Because vendor earliness (5,754/15,182 after-GR) is already
absorbed to 0/11,128 recorded-early by the existing recording gate, a
billing-block gate modelled on lab S3 has no demonstrable marginal
value in this setting, and a value-match proxy gate modelled on lab S4 must
confront the 1,584/11,128 = 0.1423 routine-delta mass with its 0.1572
correction rate — i.e. a tolerance-calibration problem, not a
zero-tolerance enforcement problem. Second, **the Round-2 −100% rework
fix does not transfer on current evidence.** Corrected rework persists
at 26,366/251,734 = 0.1047 (strata 10/1,044; 1,882/15,182;
23,315/221,010) under the enforced regime, but the gap to the F2 base
0.0215 carries an unresolved definitional component (publishers' case
definition vs present line-item grain with date filter), and the
delay-penalty side (published ~+7d vs lab +1d: S6R 8.0d vs 7.0d
baseline) was not re-estimated. Rework persists at scale, but whether
the lab redesign transfers — and at what cost-benefit — is NOT
established. H8 therefore remains open pending a recording-stage
intervention evaluated on stratum-applicable denominators with a
re-estimated delay penalty.

## 8. Limitations

Q1 lossiness (worth-proxies, derived scenario, R3 value-match proxy) bounds
all cross-setting claims: R3 value-match proxy comparisons are proxy-to-rule. R2/R3
denominators are stratum-applicable (11,128; 11,128/199,564), not
population-wide, by design. The R4-vs-F2 excess (0.1047 vs 0.0215)
cannot be attributed to behaviour alone given non-identical
event-to-case mappings. See `docs/09-validity-limitations.md` and
`docs/11-bpic2019-results.md` (Limitations).
