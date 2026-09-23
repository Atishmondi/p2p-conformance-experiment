# Defense and Validity — P2P Conformance Experiment (owns-only: this file)

Scope: this file (`docs/18-defense-and-validity.md`) owns the defense Q&A set and the
threats-to-validity claim boundaries. It does not rewrite evidence; all numbers are
cited from linked artifacts. The outline keeps its own Q&A (`docs/15-thesis-outline.md:117-124`);
this file is the extended, evidence-anchored defense companion.

Status shorthand used throughout: lab R1 = 120 cases / 740 events, seed 42;
lab R2 = 60 cases / 400 events, seed 7 (`docs/10-appendix.md:77-104,106-116`).
Field = BPIC 2019 full corrected run, n = 251,734 cases, 1,595,596 filtered events,
327 dropped, epsilon 0.01 (`docs/11-bpic2019-results.md:3-12`; `data/bpic2019_results.json`).
H-status: 5 supported (H1,H3,H4,H6,H7) / 2 nuanced (H2,H5) / 1 open (H8)
(`data/hypotheses.csv:2-9`; `docs/16-research-audit.md:134-149`).

---

## Part 1 — Defense Q&A (10)

### Q1. Why synthetic data at all? (synthetic-data-why)

**Answer.** Because the research question requires known ground truth to separate
checker correctness from field diagnostic accuracy, and no real log provides it.
Each deviation was injected deliberately under a scripted protocol (20 cases per
scenario, fixed masters: 3 vendors, 5 products), so labels are perfect by
construction: 60/60 targeted deviations fire (R2:20 S3 + R3:20 S4 + R4:20 S6),
0 violations on R1/R5, 0/20 false positives in the S1 compliant baseline
(`docs/05-findings-r1.md:11-17`; `docs/09-validity-limitations.md:13-15`).
That measures detector correctness, not field accuracy — the audit premise
(`docs/16-research-audit.md:9`).

The design then isolates delay from failure: S2/S5 are slow-but-compliant
(S1 7.18d vs S2 10.03d, Welch t = −6.94, df = 37.15, p = 3.3e-08, d = 2.19)
while S3/S4/S6 are fast-but-noncompliant (7.24d/7.70d/8.04d), so ordering/attribute
checks fire only on the latter (`docs/05-findings-r1.md:19-23`; `data/evaluation.csv:15-30`).

**Acknowledged limit.** Perfect labels and fixed masters preclude any inference
about real-world detection precision/recall; the noise sweep shows the same checker
exceeds 10% false positives already at 2% missing events (mean FPR 0.117 from
0.050/0.200/0.100; 0.233 at 5%, 0.500 at 10%), so every causal claim is conditional
on log completeness (`docs/09-validity-limitations.md:15,32`).

### Q2. Why transform BPIC 2019 instead of using it raw? (BPI-transform-why)

**Answer.** The raw XES cannot be evaluated against R1–R5 without a schema and
scope decision: case IDs are already PurchasingDocument_Item composites (EXACT),
activities/timestamps/resources/vendors map by rename (EXACT, 327 events dropped
outside 2018-01-01–2019-01-27), but `scenario` has no native label (LOSSY derived
from Item Category) and quantity columns do not exist (LOSSY worth-proxies)
(`docs/11-bpic2019-results.md:18-36`; `docs/07-real-dataset.md:17-30`).

The transform is therefore the validity device: it declares per rule what is
EXACT (R1/R2/R4 ordering and event-presence, R5, subject to stratum scoping) and
what is proxy-to-rule not rule-to-rule (R3 value-match proxy), with applicable
denominators enforced — R2 11,128 of 15,182 after-GR; R3 11,128 after + 199,564
before (pooled 210,692, do-not-quote-alone); R4/R5 all 251,734
(`docs/11-bpic2019-results.md:45-101`; `docs/13-cross-validation.md:20-61`).

**Acknowledged limit.** Every cross-setting comparison inherits Q1 lossiness
(worth-proxies, derived scenario, value-for-quantity R3); pooled rates obscure
strata (pooled R3 1,584/210,692 = 0.0075 hides 0.1423 vs 0.0000), so only
rule-in-applicable-cohort comparisons are fair (`docs/13-cross-validation.md:80-84`).

### Q3. Isn't the R3 field proxy invalid — value for quantity? (R3-proxy-why)

**Answer.** It is a declared proxy, not a rule-to-rule test, and it is reported
as such. The lab enforces quantity `qi ≤ qr`, tolerance 0 (S4 over-bill +2/+5,
20/20 = 1.0); the field has no quantity columns, so the tested object is max
invoice worth − PO worth > 0.01 (`docs/11-bpic2019-results.md:28-36`;
`src/signatures.py:26-33` per audit P3). Direction replicates at lower magnitude:
after-GR 1,584/11,128 = 0.1423 vs lab 1.0 (diff −0.8577, `data/comparison.csv:3`),
with probe confirmation the mass is real (after-GR 1/40 > 10 EUR, max 549.0;
before-GR 0/80 > 0.01, max 0.0 — not rounding noise, epsilon 0.01)
(`docs/11-bpic2019-results.md:38-43`; `docs/13-cross-validation.md:141-149`).

Falsifier B verdict is REFUTED for tolerance-0 as an enforced norm (routine
14.2% with correction-given-violation 249/1,584 = 0.1572 < 0.50 threshold) while
H3 stays supported-as-proxy and H4 (before-GR 0/199,564) stays supported as a
structural zero (`docs/11-bpic2019-results.md:135-163`).

**Acknowledged limit.** Tolerance-0 describes neither field stratum (one routine
violation, one structural vacuity); any field-facing R3 sentence without the
"value-delta proxy; tolerance-0 refuted" qualifier overclaims (audit G9,
`docs/16-research-audit.md:171`).

### Q4. Why did S3 "disappear" in the field? (S3-disappeared-why)

**Answer.** It did not disappear — it never reaches the control point in this
field stratum. Lab S3 is 20/20 = 1.0 applicable (20/120 = 0.1667 overall anchor);
field after-GR R2 is 0/11,128 = 0.0 applicable (of 15,182 cases)
(`data/comparison.csv:2`; `data/hypotheses.csv:3`). The mechanism (§4 of the
cross-validation) explains the gap: vendor-early (`Vendor Creates Invoice` < GR)
occurs in 5,754/15,182 after-GR cases, yet recorded-early (`Record Invoice
Receipt` < GR) occurs in 0/11,128; probes 0/40 invoice < GR, 0/39 clear < GR;
full-scan D1 16,356 all before-GR / 0 after-GR, D2/D4 89 each all before-GR, D3
1,009 (322 before-GR + 687 2-way) 0 after-GR (`docs/13-cross-validation.md:86-124`;
`docs/11-bpic2019-results.md:182-214`).

Cost comparison is therefore null-null (block viol null vs compliant 0.2056;
delay viol null vs compliant median 26.32d; payment-signal compliant 0.8919), so
falsifier A is INCONCLUSIVE formally and a partial contradiction substantively:
the billing-block redesign targets a non-problem in this stratum
(`docs/07-real-dataset.md:108-113`; `docs/11-bpic2019-results.md:141-153`).

**Acknowledged limit.** The recording-gate explanation does not rescue relevance —
there is no recorded-early mass to block — and any citation of the published 1,704
without stating vendor-action vs system-recording timestamp semantics is ambiguous
(audit F4; `docs/16-research-audit.md:124`).

### Q5. How is the Round-1 → Round-2 reduction causal? (causality-how)

**Answer.** By frozen-detector, fixed-everything-else design on the targeted cohort.
The same `src/check_conformance.py::check_case` runs identically on R1 (120) and
R2 (60) with no rule edits; stochastic generation is seeded and fixed (42 for R1
dated 2026-01-05, 7 for R2 dated 2026-02-02) with documented business-hours clock
(+5h stagger, Sat/Sun → Mon 08:00) and lognormal-wait legs plus vendor shifts
(`docs/09-validity-limitations.md:13-15`; `docs/10-appendix.md:77-104`). The only
systematic difference between targeted cohorts is the enforced redesign (billing
block, quantity cap, re-approval gate), driving 60/60 = 1.0 → 0/60 = 0.0
(abs_reduction = 1; chi2 = 120, p = 6.3e-28; Fisher p = 2.1e-35, OR = inf; Wilson
[0.9398, 1.0] vs [0.0, 0.0602]; Cohen h = 3.14; `data/evaluation.csv:2-14`).

**Acknowledged limit.** Stagger is not randomisation (no random assignment, single
operator, learning/batch effects uncontrolled — see Threats, Internal); and the
claim is completeness-conditional (noise sweep breakdown at 2%: mean FPR 0.117;
recall stays ≥ 0.97), so missing events, not controls, could move the same checker
(`docs/09-validity-limitations.md:15`).

### Q6. Why Odoo — and why Community? (Odoo-why)

**Answer.** Odoo Community 17 supplies an open-source, inspectable ERP in which
the normative 6-step flow (request → approval → order → receipt → invoice →
payment) maps to real modules (Purchase / Inventory / Invoicing) with real control
points: bill control ("on received quantities"), zero-tolerance 3-way match, PO
lock + re-approval gate, plus soft SLA timers for S2/S5 (`docs/04-odoo-execution-protocol.md:5-22`;
`docs/06-redesign-and-r2.md:11-17`). Masters are fixed for comparability
(3 vendors, 5 products, 1 purchase team, 2-step approval), execution is scripted
(20 cases/scenario, staggered starts), and extraction is column-for-column
(`case_id,activity,timestamp,resource,scenario,vendor,po_id,qty_ordered,qty_received,qty_invoiced`)
via `sql/odoo_extract.sql`, so a live export swaps row-for-row when available
(`docs/04-odoo-execution-protocol.md:33-38`).

Crucially, the study is honest about what ran: the logs are Odoo-protocol
synthetic stand-ins — "no live Odoo export used" (`README.md:3`;
`docs/04-odoo-execution-protocol.md:38`; audit E3) — with the live path documented
but not executed (audit D3).

**Acknowledged limit.** Community single-company, single-team, no multi-currency /
custom valuation / dropship / service products; results do not generalise to SAP
or production Odoo without replication, and the row-for-row swap remains a
proposed follow-up, not evidence (`docs/09-validity-limitations.md:19-21,29-35`).

### Q7. What are the generalisation limits? (generalization-limits)

**Answer.** Three hard boundaries, each with numbers. (1) System: Odoo Community
single-config — no SAP replication, no configurable tolerances / partial receipts /
backdated documents / off-system approvals tested (`docs/09-validity-limitations.md:19`).
(2) Population: synthetic single-team lab (120 + 60) plus one field company
(coatings/paints, 60 subsidiaries, 1,975 vendors) — multi-actor operations and
workaround behaviour unobserved. (3) Norm: tolerance-0, no-credit-note,
no-partial-receipt model — field refutes tolerance-0 (14.2% routine deltas,
correction 0.1572) and persists rework above base (26,366/251,734 = 0.1047 vs F2
0.0215) under enforced regimes, so the Round-2 −100% fix does not transfer on
current evidence (falsifiers B REFUTED, C REFUTED-on-rate/NUANCED-on-attribution;
`docs/11-bpic2019-results.md:126-180`).

**Acknowledged limit (as boundary, not hedge).** The 0/60 demonstrates that the
enforced configuration blocks the injected paths in this set-up; it does not
establish effectiveness under adversarial or noisy field conditions, zero residual
risk, or cost-free control (S6R overhead +1d by design — see Q10/S6R note)
(`docs/09-validity-limitations.md:19-21,29-35`).

### Q8. How representative is the synthetic log? (synthetic-representativeness)

**Answer.** Representative of the mechanism under test, not of the field
population. Captured: business-hours clock, lognormal waits per leg with documented
μ/σ/clips, scenario shifts (S2 +3.0d PO→receipt; S5 +2.0d PR→approval), vendor
shifts (B +0.5d, C −0.3d), resource pools (req_01–03, approver_1/2, buy_01/02,
wh_01/02, acc_01/02), weighted quantity menu, round-robin vendor rotation
(40 cases/vendor, violation rates 0.475–0.525 with overlapping Wilson intervals —
no vendor drives the result) (`docs/10-appendix.md:77-104`;
`docs/09-validity-limitations.md:27`; `data/evaluation.csv:31-45`). Variant
structure matches the injected design (R1: V1 80× / V2 20× S3 / V3 20× S6;
R2: V1 S3R/S4R + 8-event S6R chain; 740 / 400 events; `docs/10-appendix.md:35-46`).

Not captured: adversarial behaviour, noisy/missing events (breakdown at 2%),
multi-actor handoffs, configurable tolerances, partial receipts, credit notes,
backdating, off-system approvals — all out-of-model by design
(`docs/09-validity-limitations.md:7`).

**Acknowledged limit.** Synthetic-validity bounds every claim to the lab unless
field-tested; the field check both grounds (H1 590/1,044 = 0.5651 reproduces F1
~0.56; H3 direction; H5 persistence) and contradicts (H2 absence; tolerance-0
refuted; R4 transfer not shown) the lab (`docs/13-cross-validation.md:126-199`).

### Q9. Is PM4Py a contribution or just a tool? (PM4Py-as-tool-not-contribution)

**Answer.** A tool — discovery, variant, and diagnostic triangulation only, never
the normative verdict. Fitness 1.0 (precision 0.9796; 6 sampled alignments 1.0)
is computed against the inductive-miner net *discovered from the same log*, which
by construction accommodates all three observed variants — hence per-scenario
alignment fitness is also 1.0 (`docs/10-appendix.md:21-33`;
`docs/09-validity-limitations.md:29-35`; audit E10). Listing it alongside
chi2/Fisher as "triangulated quantitative evidence" without the discovered-model
qualifier risks a normative-conformance misreading (audit G5).

What it validly contributes: variant confirmation (3 variants), the precision
penalty for the discovered model's extra behaviour (0.9796), and the alignment-cost
note (unit costs; `docs/10-appendix.md:21-33`). The hypothesis test comes
exclusively from the frozen R1–R5 checker plus chi2/Fisher/Wilson/Cohen h and the
independent Welch throughput test (`docs/09-validity-limitations.md:25-28`).

**Acknowledged limit.** PM4Py establishes nothing about compliance with the BPMN
normative model; any sentence quoting "fitness 1.0" without "vs model discovered
from same log" must be corrected (audit G5, `docs/16-research-audit.md:164`).

### Q10. What exactly is unproven about H8? (H8-unproven-what)

**Answer.** Everything beyond the lab cohort. Proven under lab control: targeted
60/60 = 1.0 (S3 20/20 + S4 20/20 + S6 20/20) → 0/60 = 0.0 (S3R/S4R/S6R) with full
stats (Q5 numbers). Unproven: any field transfer — field rate n/a, UNTESTED, no
intervention observed (`data/hypotheses.csv:9`; `docs/13-cross-validation.md:200-226`;
audit F1). Three specific blockers: (a) S3 billing-block targets a non-problem in
the BPIC after-GR stratum (0/11,128 recorded-early; gates must target recording,
not vendor action); (b) S4 tolerance-0 faces a calibration problem, not an
enforcement problem (14.2% routine mass, 15.7% correction — no calibrated-tolerance
trial run); (c) S6 re-approval's −100% does not transfer on current evidence
(rework persists 10.47% above F2 2.15% but with unresolved case-definition /
line-item-grain / date-filter gap and no re-estimated delay penalty)
(`docs/13-cross-validation.md:200-226`; audit F2/F3).

Efficiency cost is part of the unproven trade-off: S6R overhead is reported as
8.0d vs 7.0d baseline (`docs/06-redesign-and-r2.md:29`) and as 9.19d vs 8.04d
(`docs/09-validity-limitations.md:33`) — which baseline (S1 vs S6) and which sample
is unresolved, so no bare "+1d" without source lines (audit F5/G11).

**Acknowledged limit (as licence).** The lab effect licences only a pilot
hypothesis: a recording-stage intervention with pre-registered H8 test,
stratum-applicable denominators, tolerance sweep, and re-estimated delay penalty
(`docs/15-thesis-outline.md:110-113`; `docs/13-cross-validation.md:224-226`).

---

## Part 2 — Threats to validity (claim boundaries, not minimizations)

Each threat states what claim it *removes*, not how it is "handled."

### T1. Construct — signature vs concept (2 threats)

- **T1a. Signature–concept gaps per rule.** R1-lab (approval order) ≠ R1-field
  (maverick proxy, interpretable only in 2-way n = 1,044; lab has no 2-way arm);
  R2-field compares *recording* times, not physical receipt vs vendor send;
  R5-field is clear-vs-record, not cash outflow, with doc-order fallback that can
  disagree with timestamps; R2/R3 need both timestamps else None (audit P4/P5/P7;
  `src/signatures.py:9-58`). **Boundary:** no rule-to-rule sentence for R1/R3;
  R3 comparisons are proxy-to-rule; every timing sentence must name the timestamp
  kind (vendor/occurred vs recorded) and stratum.
- **T1b. R4-approval conflation + worth-proxy substitution.** Naive any-change R4
  conflates routine approval workflow with rework: 2-way approval-change
  1,000/1,044 = 0.9579 vs qty/price rework 10/1,044 = 0.0096 (two orders of
  magnitude; probe 57/60 approval vs 0/60 qty, 1/60 price); approval-only overall
  3,301/251,734 = 0.0131 excluded by corrected definition
  (`docs/11-bpic2019-results.md:79-86,165-180`). Worth stands in for quantity
  throughout R3 (no qty columns; `docs/11-bpic2019-results.md:28-36`).
  **Boundary:** quoting any-change as R4 inflates 2-way ~50× and is forbidden
  (audit G8); quoting value-delta as quantity match is forbidden (audit G9).

### T2. Internal — stagger / randomisation limits (2 threats)

- **T2a. No randomisation; stagger is not random assignment.** +5h staggered starts
  avoid batch artefacts but do not randomise; vendors/products rotate round-robin
  (40 cases/vendor) rather than randomly (`docs/10-appendix.md:77-104`).
  **Boundary:** the 60/60 → 0/60 contrast is a controlled before/after under
  frozen detector + fixed seeds, not a randomised trial; operator learning, batch
  effects, and master drift are uncontrolled.
- **T2b. Single-operator, single-batch rounds.** R1 seed 42 on 2026-01-05, R2 seed 7
  on 2026-02-02; no concurrent control arm during R2; S2/S5 arms out of R2 scope
  by design (`docs/06-redesign-and-r2.md:30`). **Boundary:** period effects cannot
  be separated from intervention effects except via the frozen-checker + fixed-schema
  argument; no claim about S2/S5 redesign (D1 soft-SLA proposal never executed).

### T3. External — Odoo-Community + synthetic + single-team (3 threats)

- **T3a. Odoo Community single-config.** Single company `p2p-exp`, no multi-company /
  multi-currency / custom valuation / dropship / before-GR config / service products
  (`docs/17-erp-experiment-protocol.md:48-58`). **Boundary:** no SAP / enterprise-ERP
  generality without replication (non-claim, `docs/09-validity-limitations.md:29-35`).
- **T3b. Synthetic stand-in, single team.** No live Odoo export ran; fixed masters,
  single purchase team, 2 approvers (`docs/04-odoo-execution-protocol.md:9-14,38`).
  **Boundary:** no multi-actor, adversarial, or noisy-field effectiveness claim.
- **T3c. Single field company.** BPIC 2019 = one coatings/paints multinational
  (60 subsidiaries); 2-way/3-way/consignment strata are that company's policy
  encoding. **Boundary:** field corroboration is existence-in-one-setting, not
  population generality; H1 reproduces F1 ~0.56 only in the matching 2-way stratum.

### T4. Data — BPI column losses (2 threats)

- **T4a. Lossy scenario derivation.** Item Category → S1–S6 mapping has no native
  label; Consignment and 2-way are out-of-scope for R2 by construction
  (`docs/11-bpic2019-results.md:27,45-50`). **Boundary:** scenario-conditioned
  field rates are approximations, not equivalences.
- **T4b. Quantity absence; worth-proxy dependence.** No qty columns in XES; R3 is
  max invoice worth − PO worth > 0.01 throughout, with multi-GR aggregation risk
  (rent/logistics) and cumulative-net-worth linear anonymisation
  (`docs/07-real-dataset.md:8,28-30`). **Boundary:** magnitude gaps (e.g. R3-after
  diff 0.8577, `data/comparison.csv:3`) cannot be read as behavioural shortfalls
  alone; epsilon/tolerance choice (0.01) is load-bearing and probe-checked, not
  practitioner-validated.

### T5. Measurement — latent vs recorded timestamps + None-rates (2 threats)

- **T5a. Latent-vs-recorded censoring.** The control-relevant behaviour (system
  records early) is censored by the recording gate: 5,754 vendor-early → 0
  recorded-early after-GR; lab S3 models latent vendor behaviour that is
  control-relevant only if it reaches recording (`docs/13-cross-validation.md:111-124`).
  **Boundary:** vendor-action earliness must never be quoted as an R2 violation;
  the 1704 must carry timestamp semantics or not be cited (audit F4).
- **T5b. None-rates (missing-ts / wrong-stratum share).** R2 after-GR: 4,054 of
  15,182 cases lack both recording timestamps (11,128 applicable → None 4,054,
  26.7%); R3 before-GR: 21,446 of 221,010 lack the worth/timestamp anchor
  (199,564 applicable → None 21,446, 9.7%) (`data/bpic2019_results.json:62-108`
  arithmetic: 15,182 − 11,128 = 4,054; 221,010 − 199,564 = 21,446).
  **Boundary:** None is not conformance — rates with undisclosed applicable-n are
  uninterpretable; the R2 zero is a stratum-applicable zero (0/11,128), not a
  population zero, and pooled R3 (1,584/210,692 = 0.0075) must not be quoted alone.

### T6. Reproducibility — seeds / registry / MD5 (3 threats)

- **T6a. Seed-and-version dependence.** R1 seed 42 → 120/740; R2 seed 7 → 60/400;
  detector frozen (`check_case`); reproduction table `make data && make check &&
  make eval` (`docs/10-appendix.md:106-121`). **Boundary:** any seed, master, or
  detector change voids the 60/60 → 0/60 comparison; S6R overhead ambiguity
  (8.0 vs 7.0 per `docs/06-redesign-and-r2.md:29` vs 9.19 vs 8.04 per
  `docs/09-validity-limitations.md:33`) must be cited with both source lines.
- **T6b. Registry dependence.** H1–H8 in `data/hypotheses.csv:1-9`, signatures in
  `src/signatures.py:9-58`, 9-step backbone in `docs/04-odoo-execution-protocol.md:40-60`.
  **Boundary:** results without preregistered hypo_id + predicted signature +
  lab/field rates are exploratory, not confirmatory; R4-definition change
  (approval excluded) supersedes `docs/07-real-dataset.md:47-48` steps 8–10 (audit G8);
  R4-3way denominator variants (25,197/236,192 in `data/comparison.csv:4` vs
  corrected 26,366/251,734 in `docs/11-bpic2019-results.md`) must state which is cited.
- **T6c. Provenance dependence.** Single XES copy: 728,558,522 bytes, MD5
  `4eb909242351193a61e1c15b9c3cc814` (`docs/14-data-stewardship.md:23-26,67-85`);
  probes `/tmp/bpic_probe_out.json` and `/tmp/bpic_1704_out.json` are ephemeral,
  not repo artifacts (`docs/14-data-stewardship.md:64-65`). **Boundary:** 1704
  closure requires independent re-scan; no `/tmp` citation carries reproducibility
  weight (audit F4).

---

## Counts (return)

- Defense Q&A: **10** (Q1 synthetic-data-why; Q2 BPI-transform-why; Q3 R3-proxy-why;
  Q4 S3-disappeared-why; Q5 causality-how; Q6 Odoo-why; Q7 generalization-limits;
  Q8 synthetic-representativeness; Q9 PM4Py-as-tool-not-contribution; Q10 H8-unproven-what).
- Threats: **6 families / 14 items** (T1 construct 2; T2 internal 2; T3 external 3;
  T4 data 2; T5 measurement 2; T6 reproducibility 3).
