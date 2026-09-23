# Real Dataset: BPI Challenge 2019

Source: purchase-order-handling log, large multinational coatings/paints company (Netherlands, 60 subsidiaries).
- Publisher: Boudewijn van Dongen, Eindhoven University of Technology, via 4TU.ResearchData, 31 Jan 2019.
- URL: https://doi.org/10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1 (mirror: https://data.4tu.nl/datasets/35ed7122-966a-484e-a0e1-749b64e3366d/1).
- Size: 76,349 purchase documents, 251,734 cases (PO line items), 1,595,923 events, 42 activities, 627 users (607 human + 20 batch_*). File: BPI_Challenge_2019.xes (~729 MB, IEEE-XES).
- Case attributes: concept:name, Purchasing Document, Item, Item Type, GR-Based Inv. Verif., Goods Receipt, Source, Doc. Category name, Company, Spend classification/area/sub-spend area text, Vendor, Name, Document Type, Item Category (2-way match / 3-way invoice-before-GR / 3-way invoice-after-GR / Consignment).
- Event attributes: Event ID, concept:name, time:timestamp, User / org:resource (identical, NONE = no user recorded), Cumulative net worth (EUR, linearly anonymized, cumulative per case not per-event atomic).

## Why it validates our synthetic experiment (external validity)

- Same domain: P2P with 3-way match, GR/invoice/value compliance checks. Our rules R1-R5 are the textbook subset of their compliance questions.
- Same deviation families: invoice-before-receipt, value mismatch, PO change/rework, maverick buying (S1-S6 all attested in real log).
- Scale contrast: our R1 120 cases/740 events + R2 60/400 is a controlled lab; BPIC 2019 is the noisy field (avg 6.3 events/case, max 990). Effect sizes that survive there are real.
- Ground-truth direction flips: synthetic gives known injected deviation -> expected log signature; real log gives observed signature -> inferred deviation. Agreement on R2/R3/R4 signatures cross-validates both.

## Column mapping: BPIC 2019 -> our schema

| Our column | BPIC 2019 source | Notes / transform |
|---|---|---|
| case_id | case concept:name | Already PurchasingDocument_Item composite, 1:1. |
| activity | event concept:name | Normalize: Create Purchase Order Item -> PO; Record Goods Receipt -> receipt; Record Invoice Receipt -> invoice; Clear Invoice -> pay; Vendor Creates Invoice -> vendor-invoice (no synthetic equivalent, keep or drop). |
| timestamp | event time:timestamp | Keep; filter junk stamps (1948-2017, post-Jan-2019 batch clears). |
| resource | event User (= org:resource) | Keep; batch_* -> system, NONE -> system. |
| scenario | derived from case Item Category | 2-way match / 3-way-before-GR / 3-way-after-GR / Consignment -> map to nearest S1-S6; no native scenario label. |
| vendor | case Vendor (+ case Name) | Anonymized IDs (1975 vendors); join Name for readability. |
| po_id | case Purchasing Document | Strip item suffix from case_id; 1 PO -> N cases. |
| qty_ordered | none (derive) | No qty columns; proxy via first Cumulative net worth at Create Purchase Order Item, or count = 1 per case. |
| qty_received | none (derive) | Proxy via count of Record Goods Receipt events per case, or net-worth delta; multi-GR cases (rent/logistics) need aggregation. |
| qty_invoiced | none (derive) | Proxy via count of Record Invoice Receipt events per case, or net-worth delta; value not quantity — R3 becomes value-match not qty-match. |

## Published findings on P2P deviations (3)

- F1 Maverick buying: ~56% of 2-way-match items start with Vendor Creates Invoice before Create Purchase Order Item (~45% most-common variant), ≈ 2.97M EUR unapproved spend. Maps to our R1/R4 family.
- F2 Rework on PO: Change Quantity 1.34% + Change Price 0.78% of cases (≈2.15% rework), +7 days throughput each; quantity change is top predictor of total delay. Maps to our S6/R4.
- F3 Invoice/GR ordering + payment blocks: 1,704 sequences record+clear invoice before goods receipt despite invoice-after-GR requirement; Remove Payment Block fires in ~26% of 3-way-after-GR cases; Record Invoice Receipt -> Clear Invoice averages ~45 days (69% of before-GR cases); Jan 2-7 2019 forced Clear Invoice by user None on 7,868 traces. Maps to our S3/R2 and S5.

## Sampling plan (500 cases)

1. Download XES, parse with pm4py; drop events with timestamp < 2018-01-01 or > 2019-01-27.
2. Keep only cases with valid end (Clear Invoice or Delete Purchase Order Item), ~75% survive.
3. Stratify by Item Category: 150x 3-way-after-GR, 200x 3-way-before-GR, 100x 2-way, 50x Consignment = 500.
4. Within strata, sample top-3 Spend areas proportionally; exclude Service/Consignment multi-GR monsters (>20 GR events).
5. Apply column mapping table above; derive qty_* proxies; tag scenario from Item Category.
6. Label R2 violation where Record Invoice Receipt precedes first Record Goods Receipt in after-GR stratum.
7. Label R3 violation where max Cumulative net worth delta (invoice vs PO creation) > 0 excl. rounding.
8. Label R4 proxy where Change Quantity/Price or Change Approval occurs after Create Purchase Order Item.
9. Compute conformance of 500-case sample against our R1-R5 normative model; compare violation mix to R1 synthetic.
10. Report delta table (synthetic R1 rate vs real-sample rate per rule) + keep PO IDs for audit replay.

## Masters addendum: 3-way-match mapping, base rates, falsification

Why BPIC 2019 Item-Category values map to R2/R3:
- R2 (receipt must precede invoice recording) is testable only where the policy requires it, i.e. the
  3-way-invoice-after-GR stratum. In the 3-way-invoice-before-GR stratum, invoice-before-receipt is
  compliant by design, so the same event order is a violation in one stratum and normal in the other.
  2-way-match cases (no receipt step) and Consignment cases are out of scope for R2.
- R3 (qty invoiced <= qty received, tolerance 0) maps to a value-match proxy in BPIC 2019 because the
  log carries no quantity columns: max Cumulative net worth delta (invoice vs PO creation) > 0 excl.
  rounding. It applies to both 3-way strata; 2-way-match cases have no receipt anchor and are excluded.
- Demo proxy: `data/bpic_mapping_demo.csv` (first 200 events of `data/event-log-r1.csv`, XES-like headers
  case_concept/concept_name/time_timestamp/org_resource/vendor_doc + note='lab-proxy-for-BPIC';
  vendor_doc preserves vendor|po_id). It demonstrates the rename only; it is not real BPIC data.

Known base rates (published BPIC 2019 findings, cf. F1-F3 above):
- Maverick buying: ~56% of 2-way-match items start with Vendor Creates Invoice before Create Purchase
  Order Item (~45% most-common variant), ≈ 2.97M EUR unapproved spend.
- Rework on PO: Change Quantity 1.34% + Change Price 0.78% of cases (≈ 2.15% combined), +7 days
  throughput each; quantity change is the top predictor of total delay.
- Invoice/GR ordering + payment blocks: 1,704 sequences record+clear invoice before goods receipt despite
  the invoice-after-GR requirement; Remove Payment Block fires in ~26% of 3-way-after-GR cases;
  Record Invoice Receipt -> Clear Invoice averages ~45 days.

What would falsify our lab findings:
- Falsifier 1 (R2/S3): in the 3-way-after-GR sample, invoice-before-receipt occurs at scale yet never
  co-occurs with rework, delay, or payment blocks — i.e. the lab's "ordering violation = control failure"
  signature has no real-world cost.
- Falsifier 2 (R3/S4): invoice-vs-PO value deltas > 0 are routine in both 3-way strata with no corrective
  action (no payment block, no credit memo, no price change) — i.e. zero-tolerance R3 does not describe the
  enforced norm, and the lab's over-billing effect is an artifact of tolerance 0.
- Falsifier 3 (R4/S6 redesign): PO-change rework at/above the ~2.15% base rate persists with the same
  delay penalty in settings that already enforce the R2 controls (approval gates, GR/invoice blocks) —
  i.e. the Round-2 "-100% violations" fix does not transfer outside the lab configuration.

### Masters addendum — supplement (lab-vs-field thresholds)

Lab anchors for comparison: R1 (n=120): R2 20/120 (16.7% overall; 20/20 in S3), R3 20/120
(S4 over-bill +2/+5), R4 20/120 (S6); R2 (n=60): 0/60 (-100%) with +1d re-approval cost
(S6R 8.0d vs 7.0d baseline).

- Falsifier A (R2 rate): if in the BPIC 3-way-after-GR stratum the invoice-before-GR base rate
  >> lab 16.7% (e.g. majority of cases) yet shows no excess delay, payment block, or rework vs
  compliant order, the lab claim "ordering violation = control failure" is overturned — the
  violation is tolerated practice, not a failure.
- Falsifier B (R3 tolerance): if invoice-vs-PO value deltas > 0 are routine in both 3-way strata
  with no block / credit-memo / price-change correction, zero-tolerance R3 is not the enforced
  norm and the lab over-billing effect is a tolerance-0 artifact.
- Falsifier C (rework cost / transfer): if PO-change rework at/above ~2.15% persists with ~+7d
  penalty (vs lab +1d) even where R2 bill/receipt blocks and re-approval gates are enforced,
  the Round-2 "-100% violations" fix does not transfer and its cost-benefit is overturned.

## Falsifier status after full corrected run (see docs/11-bpic2019-results.md)

Full run: `data/bpic2019_results.json` (n = 251,734; 1,595,596 events; filter
2018-01-01–2019-01-27; epsilon 0.01). Corrected R4 = Quantity/Price only;
approval-change tracked separately.

- Falsifier A (R2/S3): INCONCLUSIVE formally → partial contradiction
  substantively. After-GR R2 0/11,128 = 0.0% (applicable denominator);
  probe 0/40 invoice < GR, 0/39 clear < GR. Lab S3 pattern (20/120, 16.7%)
  is absent where the rule applies; cost signature untestable
  (viol = null vs compliant block 0.2056, delay median 26.32d).
  The billing-block redesign targets a non-problem in this stratum.
- Falsifier B (R3/S4): REFUTED. After-GR value deltas 1,584/11,128 = 14.2%
  with correction 0.157 (15.7%) given violation; before-GR 0/199,564 = 0.0%
  (structural, not enforcement). Zero-tolerance R3 is an artifact.
- Falsifier C (R4/S6): NUANCED; transferability NOT established.
  Corrected R4 26,366/251,734 = 10.47% (2-way 10/1,044 = 0.96%;
  after 1,882/15,182 = 12.4%; before 23,315/221,010 = 10.5%) persists above
  the published F2 base 2.15%, but the definitional gap (publishers' case
  definition vs any-Change-after-PO at line-item grain) is unresolved and
  the delay penalty was not re-estimated.
- 1704-reconciliation: exact scan finds D1 invoice < GR n = 16,356 all in
  compliant before-GR, 0 in after-GR; D2/D4 clear < GR n = 89 each, all in
  before-GR. After-GR R2 = 0/11,128 under all definitions.
  Vendor-invoice < GR in after-GR (5,754 cases) with zero record-invoice
  < GR shows the control acts at RECORDING, not vendor action.
