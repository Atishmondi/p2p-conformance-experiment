# BPIC 2019 Full-Run Results: Lab Rules (R1–R5) Applied to Field Data

> **Historical research note (superseded for current execution and claims).** This document retains its original analysis for provenance. Use [the current claim/evidence map](claim-evidence.md), [event contract](event-contract.md), and [ERP pilot](erp-pilot.md) for current limits and next steps. Old extraction SQL, causal/transfer wording, and hard-enforcement predictions here are not an executable or verified path; do not run the historical SQL.


Source log: BPI Challenge 2019 purchase-order-handling XES
(`data/BPI_Challenge_2019.xes`), via 4TU.ResearchData,
DOI `10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1`.
Full corrected run: `data/bpic2019_results.json`
(n_cases = 251,734; n_events_filtered = 1,595,596;
n_events_dropped_out_of_range = 327;
filter: drop event if timestamp < 2018-01-01 or > 2019-01-27 23:59:59;
R3 epsilon = 0.01).
Probes: `/tmp/bpic_probe_out.json` (quota-capped, n_scanned = 250,750)
and `/tmp/bpic_1704_out.json` (exact full-scan, n_cases_scanned = 251,734).

This document answers Q1–Q4 for the field check pre-registered in
`docs/07-real-dataset.md`. All rates are reported with applicable
denominators. Stratum denominators differ by rule by design (see Q2).

## Q1 — Schema transform verdict per column

| Our column | BPIC 2019 source | Verdict | Notes |
|---|---|---|---|
| case_id | case `concept:name` | EXACT | Already PurchasingDocument_Item composite, 1:1. |
| activity | event `concept:name` | EXACT | Direct rename; no semantic recoding except documented proxies (below). |
| timestamp | event `time:timestamp` | EXACT | Kept; 327 events dropped outside 2018-01-01–2019-01-27. |
| resource | event `User` (= `org:resource`) | EXACT | Kept; `batch_*` / `NONE` mapped to system. |
| vendor | case `Vendor` (+ `Name`) | EXACT | Anonymised IDs (1,975 vendors); `Name` joined for readability. |
| po_id | case `Purchasing Document` | EXACT | Item suffix stripped from case_id; 1 PO → N cases. |
| scenario | derived from case `Item Category` | LOSSY (derived) | No native scenario label. Maps 2-way match / 3-way-before-GR / 3-way-after-GR / Consignment to nearest S1–S6. Approximation, not equivalence. |
| qty_ordered | none (derived) | LOSSY (worth-proxy) | No quantity columns. Proxy via first `Cumulative net worth (EUR)` at `Create Purchase Order Item`, or count = 1 per case. |
| qty_received | none (derived) | LOSSY (worth-proxy) | Proxy via count of `Record Goods Receipt` events per case or net-worth delta; multi-GR cases require aggregation. |
| qty_invoiced | none (derived) | LOSSY (worth-proxy) | Proxy via count of `Record Invoice Receipt` events or net-worth delta. Value, not quantity — **R3 becomes a value-match proxy, not a quantity match**. |
| R3 rule | value-match proxy: max invoice worth − PO worth > 0 (excl. rounding, epsilon 0.01) | LOSSY | Zero-tolerance quantity rule cannot be tested; tested object is invoice-vs-PO value delta (value-match proxy). |

Consequence: R1, R2, R4 (ordering / event-presence), and R5 map with
preserved semantics subject to stratum scoping (Q2). R3 value-match proxy does not transfer
as the same construct; any R3 value-match proxy comparison is proxy-to-rule, not rule-to-rule.

Probe confirmation (`/tmp/bpic_probe_out.json`):
before-GR deltas (n = 80) show > 0.01 in 0/80, > 1.0 in 0/80, > 10 in 0/80
(max delta 0.0) — the full-run before-GR zero (0/199,564) is not an epsilon
artifact. After-GR deltas (n = 40) show > 0.01 in 1/40, > 1.0 in 1/40,
> 10 in 1/40 (max delta 549.0) — after-GR over-billing mass above 1.0/10.0
confirms a real stratum effect, not rounding noise.

## Q2 — Which cases map to R1–R5

Item-Category strata (full run): 2-way match n = 1,044;
3-way invoice-after-GR n = 15,182; 3-way invoice-before-GR n = 221,010;
Consignment n = 14,498. Total n = 251,734.

Activity scope used (from `data/bpic2019_results.json`):

- R1: `Vendor creates invoice` vs `Create Purchase Order Item`.
- R2: `Record Invoice Receipt` vs `Record Goods Receipt`.
- R3 value-match proxy: `Create Purchase Order Item` vs `Record Invoice Receipt`
  (value-match proxy).
- R4 (corrected): `Change Quantity` / `Change Price` after
  `Create Purchase Order Item`. `Change Approval for Purchase Order`
  tracked separately as `approval_change_after_po` and EXCLUDED from R4.
- R5: `Clear Invoice` vs `Record Invoice Receipt`.

Mapping:

- R1 (maverick proxy): applicable in principle to all cases, interpreted
  only in the 2-way stratum (n = 1,044), where no receipt step exists and
  vendor-invoice-before-PO is the published F1 pattern. Field R1 in 3-way
  strata is reported for completeness but is not the maverick construct
  (after-GR: 319/15,182 = 2.1%; before-GR: 2,541/221,010 = 1.1%).
- R2 (receipt must precede invoice recording): applicable ONLY in the
  after-GR stratum where the policy requires it, and only where both
  timestamps exist: n_applicable = 11,128 of n_cases = 15,182.
  In the before-GR stratum invoice-before-receipt is compliant by design
  (n_applicable = 0); 2-way (no receipt) and Consignment are out of scope.
- R3 (value-match proxy for qty invoiced <= qty received, tolerance 0):
  applies to both 3-way strata with receipt/worth anchor:
  after-GR n_applicable = 11,128; before-GR n_applicable = 199,564;
  overall n_applicable = 210,692. Excluded: 2-way (no receipt anchor,
  n_applicable = 0) and Consignment (n_applicable = 0).
- R4 (corrected PO rework): `Change Quantity` / `Change Price` after PO,
  all cases (n_applicable = 251,734; strata denominators 1,044 / 15,182 /
  221,010 / 14,498). `Change Approval for Purchase Order` after PO is
  routine workflow and EXCLUDED; tracked as `approval_change_after_po`
  (overall 4,290/251,734) and `approval_only` (approval true AND R4 false;
  overall 3,301/251,734). Probe (60 2-way cases): Quantity 0/60,
  Price 1/60 (1.7%), Approval 57/60 (95.0%), any-change 57/60 —
  approval dominance in 2-way confirms the exclusion is load-bearing.
- R5 (clear without record): all cases (n_applicable = 251,734).

## Q3 — Rates with applicable denominators

Corrected full run. Percentages are n_true / n_applicable.

| Rule | Overall | 2-way (n=1,044) | After-GR (n=15,182) | Before-GR (n=221,010) | Consignment (n=14,498) |
|---|---|---|---|---|---|
| R1 maverick | 3,450/251,734 = 1.37% | 590/1,044 = 56.5% | 319/15,182 = 2.10% | 2,541/221,010 = 1.15% | 0/14,498 = 0.0% |
| R2 ordering viol. | 0/11,128 = 0.0% (applicable only) | n/a (0 applicable) | 0/11,128 = 0.0% | n/a (0 applicable) | n/a (0 applicable) |
| R3 value-match proxy > 0 | 1,584/210,692 = 0.75% | n/a (0 applicable) | 1,584/11,128 = 14.2% | 0/199,564 = 0.0% | n/a (0 applicable) |
| R4 qty/price-only | 26,366/251,734 = 10.47% | 10/1,044 = 0.96% | 1,882/15,182 = 12.4% | 23,315/221,010 = 10.5% | 1,159/14,498 = 8.0% |
| Approval change after PO (excluded from R4) | 4,290/251,734 = 1.70% | 1,000/1,044 = 95.8% | 38/15,182 = 0.25% | 3,252/221,010 = 1.47% | 0/14,498 = 0.0% |
| — of which approval-only (no qty/price rework) | 3,301/251,734 = 1.31% | (subset; see notes) | — | — | — |
| R5 clear w/o record | 408/251,734 = 0.16% | 0/1,044 = 0.0% | 9/15,182 = 0.06% | 399/221,010 = 0.18% | 0/14,498 = 0.0% |

R2 detail (after-GR): n_after_gr = 15,182; n_viol = 0; n_compliant = 11,128;
n_unblocked_blocked_then_cleared = 0.
Block rate given compliant = 0.2056; payment-signal rate given compliant =
0.8919; delay invoice-to-clear median compliant = 26.32 days;
viol quantities null (no violations to condition on).

Reading notes:

- R1 590/1,044 = 56.5% reproduces the published F1 maverick magnitude
  (~56% of 2-way items) within the same stratum and denominator.
- R2 0/11,128 = 0.0% is a stratum-applicable zero, not a population zero.
  The applicable denominator (11,128 with both timestamps of 15,182
  after-GR cases) must accompany the rate.
- R3 value-match proxy contrast is stratum-specific: 1,584/11,128 = 14.2% after-GR vs
  0/199,564 = 0.0% before-GR. The pooled 1,584/210,692 = 0.75% obscures
  this and should not be quoted alone.
- R4 corrected (qty/price-only) 26,366/251,734 = 10.47% persists at
  1,882/15,182 = 12.4% after-GR and 23,315/221,010 = 10.5% before-GR,
  with 2-way 10/1,044 = 0.96%. Approval-change 4,290/251,734 = 1.7%
  (2-way 1,000/1,044 = 95.8%) is excluded by definition; conflating the
  two inflates or deflates R4 by an order of magnitude in 2-way.
- R5 408/251,734 = 0.16% is rare in all strata.

## Q4 — Falsifier verdicts

Pre-registered falsifiers in `docs/07-real-dataset.md`, evaluated on the
full corrected run. Lab anchors: R1 (n = 120): R2 20/120 (16.7% overall;
20/20 in S3), R3 20/120, R4 20/120; R2 (n = 60): 0/60 with +1d re-approval
cost (S6R 8.0d vs 7.0d baseline). Published field bases: F1 ~56% maverick
in 2-way; F2 Change Quantity 1.34% + Change Price 0.78% (≈ 2.15% combined,
+7d each); F3 ordering/blocks (see 1704 reconciliation below).

| Falsifier | Pre-registered test | Observed | Verdict |
|---|---|---|---|
| A (R2 rate vs lab 16.7%) | Supported if after-GR rate in [0.10, 0.25]; refuted if > 0.50 with no excess block/delay/rework | 0/11,128 = 0.0% | INCONCLUSIVE (formal) → partial contradiction (substantive) |
| B (R3 value-match proxy zero-tolerance, both 3-way) | Supported if max rate ≤ 0.01; refuted if max rate > 0.05 with correction < 0.50 | After 1,584/11,128 = 14.2%, before 0/199,564 = 0.0%; correction given viol. after 0.157 (15.7%), before null | REFUTED |
| C (R4 rework vs 2.15% base) | Supported if in [0.0015, 0.0415]; Round-2 fix transfers | Corrected R4 26,366/251,734 = 10.47% (strata 0.96% / 12.4% / 10.5%) | REFUTED on rate (10.47% persists), NUANCED on attribution/transfer (H8 open) |

Falsifier A — INCONCLUSIVE formally, partial contradiction substantively.
The after-GR R2 rate 0/11,128 = 0.0% is off-anchor low relative to the lab
16.7% (20/120 overall; 20/20 in S3): the lab S3 pattern is absent in the
field stratum where the rule applies. Cost-signature comparison is
inconclusive because there are no violations to condition on
(block viol = null vs compliant 0.2056; delay viol = null vs compliant
median 26.32d). The pre-registered band therefore returns INCONCLUSIVE.
Substantively, this is a partial contradiction of relevance rather than a
clean pass: the Round-2 billing-block redesign targets a non-problem in
this field setting — there is no invoice-before-recording mass to block
(0/11,128 applicable; probe 0/40 invoice < GR and 0/39 clear < GR given
clear). The control cannot demonstrate value where the targeted behaviour
does not occur.

Falsifier B — REFUTED. Invoice-vs-PO value-match proxy deltas > 0 are routine in
after-GR (1,584/11,128 = 14.2%) with low correction (0.157 = 15.7% given
violation) and structurally absent in before-GR (0/199,564 = 0.0%).
Zero-tolerance R3 value-match proxy is therefore an artifact of tolerance 0 as an enforced
norm: it describes neither stratum (one routine violation, one structural
zero). The before-GR zero is structural — invoice-before-GR is compliant
there and worth deltas do not arise under that ordering — not evidence of
enforcement. The lab over-billing effect does not survive as a
tolerance-0 claim.

Falsifier C — REFUTED on rate (10.47% persists), NUANCED on attribution/transfer (H8 open) (key Q4 answer).
Corrected R4 (Quantity/Price only) 26,366/251,734 = 10.47% persists well
above the published F2 base 2.15% (1.34% + 0.78%), in both after-GR
(1,882/15,182 = 12.4%) and before-GR (23,315/221,010 = 10.5%), i.e. under
the enforced GR/invoice regime. Taken at face value this would refute the
Round-2 "-100% violations" transfer. However, a definitional gap must be
stated: the published 2.15% counts F2 Change Quantity / Change Price cases
under the publishers' case definition, while the present 10.47% counts any
`Change Quantity` / `Change Price` after `Create Purchase Order Item` at
line-item grain with the stated date filter and epsilon. The two
denominators and event-to-case mappings are not shown to be identical, so
the excess (10.47% vs 2.15%) cannot be attributed to behaviour alone.
The delay-penalty side (~+7d published vs +1d lab) was not re-estimated
here. Hence: rework persists at scale in the field, but whether the lab
redesign transfers — and at what cost-benefit — is NOT established by this
comparison.

### 1704-reconciliation (F3)

The published "1,704 sequences record+clear invoice before goods receipt
despite invoice-after-GR requirement" is not reproduced as an R2 timing
violation in the full scan (`/tmp/bpic_1704_out.json`, exact over 251,734
cases, no date filter):

- D1 invoice < GR (timestamp): n = 16,356, all in
  `3-way match, invoice before GR` (compliant stratum), 0 in after-GR.
  Doc-order variant: n = 16,360, same stratum.
- D2 clear < GR (timestamp and doc-order): n = 89, all in before-GR,
  0 in after-GR.
- D4 record AND clear before GR (timestamp): n = 89, all in before-GR,
  0 in after-GR.
- D3 invoice without GR: n = 1,009 (322 before-GR + 687 2-way), 0 in
  after-GR.
- R2 applicable after-GR: 0/11,128 under all definitions; probe (n = 40):
  0 invoice < GR, 0/39 clear < GR given clear.

The 16,356 D1 cases sit entirely in the before-GR stratum where
invoice-before-GR is compliant by design; they are not violations of the
after-GR policy. The only pre-GR payment signal (89 clear < GR, 89
record+clear < GR) is two orders of magnitude below 1,704 and likewise in
the compliant stratum.

Control-point reading: `Vendor Creates Invoice` < GR occurs in after-GR in
5,754 cases (of 127,731 overall; 121,977 before-GR + 5,754 after-GR), yet
`Record Invoice Receipt` < GR occurs in 0 after-GR cases. The control
therefore operates at RECORDING, not at vendor action: vendor-side early
invoicing is absorbed before the system records the invoice, leaving the
R2 ordering intact (0/11,128). Any comparison to the published 1,704 must
specify vendor-action vs system-recording semantics; under the
system-recording definition used by R2, after-GR compliance is exact.

## Limitations

Q1 lossiness (worth-proxies, derived scenario, R3 value-match proxy) bounds all
cross-setting claims. Denominators are stratum-applicable, not
population-wide, for R2 and R3. The R4-vs-F2 gap carries an unresolved
definitional component. See `docs/09-validity-limitations.md` and the
falsifier-status section in `docs/07-real-dataset.md`.
