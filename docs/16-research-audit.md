# Research Audit — P2P Conformance Experiment (READ-ONLY, NO REWRITE)

Scope: audit only. No code changed, no claims rewritten in place. Recommendations only (Section G).
Inspected: `README.md`, `docs/00,01,02,04,05,06,07,09,10,11,13,14,15`, `data/hypotheses.csv`, `src/signatures.py` (all 80 lines), `data/bpic2019_results.json` (top-level), `data/comparison.csv`, `data/evaluation.csv` (lines 1–15 + throughput lines verified), `Makefile`.
Owns-only: this file (`docs/16-research-audit.md`).

Status verification: `data/hypotheses.csv:2-9` yields **5 supported (H1,H3,H4,H6,H7) / 2 nuanced (H2,H5) / 1 open (H8)** — matches expected. Detail in H-table below.

Blunt premise: lab demonstrates checker-correctness + config-enforcement under synthetic control. It does not demonstrate field detection accuracy, field control effectiveness, or ERP generality. Field work grounds and in two places contradicts the lab. Any sentence that drops those qualifiers overclaims.

---

## A. Established (with file:line evidence)

E1. Normative model exists and is executable: 6 steps + R1–R5 predicates. `docs/01-normative-model.md:6-18`, formalised `docs/10-appendix.md:3-19` (`src/check_conformance.py::check_case` frozen, `docs/09-validity-limitations.md:15`, `docs/10-appendix.md:19`).

E2. Controlled scenario design: S1–S6, 20 cases/scenario = 120 R1; S3R/S4R/S6R 20 each = 60 R2; same masters (3 vendors, 5 products). `docs/02-scenarios.md:5-14`, `docs/04-odoo-execution-protocol.md:9-14,33`.

E3. Lab logs are synthetic stand-ins, not live Odoo exports. `README.md:3` (“Odoo-protocol synthetic stand-in — no live Odoo export used; swap in real export row-for-row”), `docs/04-odoo-execution-protocol.md:38`, `docs/14-data-stewardship.md:8-9` (read-only audit).

E4. Generator is stochastic, seeded, specified: R1 seed 42 (2026-01-05), R2 seed 7 (2026-02-02); business-hours clock + `lognormvariate` + vendor shifts + resource pools; full leg table. `docs/10-appendix.md:77-104`, `docs/09-validity-limitations.md:15`.

E5. R1 detection under lab control: 60/60 targeted (R2:20 S3 + R3:20 S4 + R4:20 S6), 0 violations R1/R5, 0 false positives in S1 (0/20). `docs/05-findings-r1.md:11-17`, `docs/00-abstract.md:5`.

E6. R2 elimination under lab control: 60/60 pre (targeted) → 0/60 post (S3R/S4R/S6R), abs_reduction=1. `docs/06-redesign-and-r2.md:19-29`, `data/evaluation.csv:2-5` (`r1_viol_rate,1 / r2_viol_rate,0 / abs_reduction,1 / rel_reduction,1`), `docs/10-appendix.md:50-52`.

E7. Statistics for E6 are computed and reported with complementary tests: chi2=120 p=6.326e-28, Fisher p=2.07e-35 OR=inf, Wilson [0.9398,1.0] vs [0.0,0.0602], Cohen h=3.1416. `data/evaluation.csv:6-14`, `docs/10-appendix.md:54-63`, `docs/09-validity-limitations.md:27`.

E8. Throughput separation (performance, not conformance): S1 7.18d vs S2 10.03d, Welch t=-6.94 df=37.15 p=3.34e-08, d=2.19; vendor strata 0.475–0.525 overlapping CIs. `data/evaluation.csv:15-45`, `docs/10-appendix.md:64-69`, `docs/09-validity-limitations.md:27`.

E9. Variant structure R1: 3 variants (V1 80× S1/S2/S4/S5; V2 20× S3; V3 20× S6); R2: V1 S3R/S4R + 8-event S6R chain. `docs/05-findings-r1.md:5-9`, `docs/10-appendix.md:37-46` (event counts 740 / 400).

E10. PM4Py metrics are discovery-diagnostics, not normative conformance: fitness 1.0 vs *discovered* inductive-miner net (by construction accommodates variants), precision 0.9796, 6 sampled alignments 1.0. `docs/10-appendix.md:23-33`, `docs/09-validity-limitations.md:29-35`, `data/pm4py_results.json` via `docs/10-appendix.md:116`.

E11. Checker brittleness measured: recall ≥0.97 at all noise levels but mean FPR on S1 0.117 at 2% noise (0.05,0.20,0.10), 0.233 at 5%, 0.50 at 10% — breakdown at 2%. `docs/09-validity-limitations.md:15`.

E12. Field run exists, full corrected, with applicable denominators (n=251,734; filtered events 1,595,596; dropped 327; epsilon 0.01): R1 maverick 590/1044=0.5651 (2-way) vs 3450/251734=0.0137 overall; R2 0/11128=0.0 after-GR applicable (of 15182 cases); R3 value-proxy 1584/11128=0.1423 after vs 0/199564=0.0 before (pooled 1584/210692=0.0075, do not quote alone); R4 qty/price-only 26366/251734=0.1047 (strata 10/1044, 1882/15182, 23315/221010); approval-change 4290/251734=0.0170 excluded, approval-only 3301/251734=0.0131; R5 408/251734=0.0016. `data/bpic2019_results.json:overall,r1_two_way_stratum,three_way_strata,r2` (verified via execution), `docs/11-bpic2019-results.md:89-107`.

E13. Recording-gate mechanism is established as field fact: after-GR vendor-early (`Vendor Creates Invoice` < GR) 5754/15182 cases yet recorded-early (`Record Invoice Receipt` < GR) 0/11128; D1 16356 all before-GR / 0 after-GR; D2/D4 89 each all before-GR; D3 1009 (322 before-GR + 687 2-way) 0 after-GR; probes 0/40 invoice<GR, 0/39 clear<GR. `docs/13-cross-validation.md:88-109`, `docs/11-bpic2019-results.md:182-214`, `docs/07-real-dataset.md:123-127`.

E14. Pre-registration + signatures + backbone exist: H1–H8 in `data/hypotheses.csv:1-9`, single-source `src/signatures.py:9-58` (lab_definition / field_proxy / applicable_scope / event_pattern / known_gaps + SCOPE_NOTES), 9-step backbone `docs/04-odoo-execution-protocol.md:40-60`, `make hypo` target `Makefile:21-23`.

Count A: **14 established**.

---

## B. Proxy — what is lossy / value-proxy / derived (do NOT quote as rule-to-rule)

P1. `scenario` (BPIC → S1–S6): LOSSY derived, no native label. `docs/11-bpic2019-results.md:27`, `docs/07-real-dataset.md:25`.

P2. `qty_ordered / qty_received / qty_invoiced` (BPIC): LOSSY worth-proxies (first PO worth / GR counts or net-worth delta / invoice worth delta). No qty columns in XES. `docs/11-bpic2019-results.md:28-31`, `docs/07-real-dataset.md:28-30`.

P3. R3-field is value-delta proxy, not quantity match: max invoice worth − PO worth > 0.01. Lab qty rule cannot be tested in field. `docs/11-bpic2019-results.md:32,55-60,74-78`, `src/signatures.py:26-33`, `docs/13-cross-validation.md:38-46`.

P4. R1-field is maverick-buying proxy (vendor acts before PO), not approval-order test; absent-invoice-as-False is scope choice; interpretable only in 2-way (n=1044). Lab has no 2-way arm. `src/signatures.py:10-17`, `docs/13-cross-validation.md:26-30`, `docs/11-bpic2019-results.md:64-68`.

P5. R2-field compares *recording* times (`Record Invoice Receipt` vs `Record Goods Receipt`), not physical receipt vs vendor send; needs both ts else None; applicable only after-GR with both ts (11128/15182). `src/signatures.py:18-25`, `docs/11-bpic2019-results.md:69-73`.

P6. R4-field corrected = qty/price-only (`Change Quantity/Price` after PO); `Change Approval for Purchase Order` EXCLUDED as routine workflow, tracked separately. Probe 60×2-way: Qty 0/60, Price 1/60, Approval 57/60 — exclusion is load-bearing. `src/signatures.py:34-41`, `docs/11-bpic2019-results.md:57-60,79-86`.

P7. R5-field is clear-vs-record (`Clear Invoice` vs `Record Invoice Receipt`), not cash outflow; doc-order fallback when ts missing can disagree with timestamps. `src/signatures.py:42-49`, `docs/11-bpic2019-results.md:60`.

P8. Before-GR R3 zero is structural (no GR reference at invoice time), not enforcement. Only after-GR is falsifiable. `src/signatures.py:32`, `docs/13-cross-validation.md:42-46`, `docs/11-bpic2019-results.md:155-163`.

P9. Pooled rates obscure strata: pooled R3 1584/210692=0.0075 must not be quoted alone; R2 0/11128 is stratum-applicable zero, not population zero. `docs/13-cross-validation.md:80-84`, `docs/11-bpic2019-results.md:113-118`.

Count B: **9 proxy/lossy items**.

---

## C. Experimentally demonstrated — lab control conditions + seeds (and only there)

Demonstrated *under*: fixed masters (3 vendors, 5 products, weighted quantities, round-robin 40 cases/vendor), staggered +5h starts, business-hours clock (Sat/Sun → Mon 08:00), lognormal waits per `docs/10-appendix.md:77-95`, frozen `check_case` both rounds, seeds **42 (R1, 120 cases/740 events)** and **7 (R2, 60 cases/400 events)**, identical schema. `docs/09-validity-limitations.md:13-15`, `docs/10-appendix.md:77-104`, `docs/04-odoo-execution-protocol.md:33,44-49`.

C1. Checker correctness vs known injection: 60/60 targeted fires, 0/20 S1 FP. Measures detector, not field diagnostic accuracy. `docs/09-validity-limitations.md:13`.

C2. Config enforcement in lab: billing block (S3R normative order), qty cap (S4R capped), re-approval gate (S6R MOD→re-approval→PO) drives 60/60→0/60. `docs/06-redesign-and-r2.md:11-24`.

C3. Delay vs failure separation in lab: S2/S5 slow-but-compliant (rule-silent, performance-only); S3/S4/S6 fast-but-noncompliant. `docs/05-findings-r1.md:19-35`, `docs/06-redesign-and-r2.md:32`.

C4. Control–efficiency trade-off in lab: S6R +1d overhead (8.0d vs 7.0d baseline; `docs/09-validity-limitations.md:33` notes 9.19d vs 8.04d variant — ambiguity documented, do not collapse). `docs/06-redesign-and-r2.md:29`.

C5. Completeness-conditionality: same checker FPR >10% at 2% missing events. Causal claim conditional on log completeness. `docs/09-validity-limitations.md:15,32`.

What C does *not* demonstrate: SAP generality, adversarial/noisy-field effectiveness, residual-risk zero, SLA validity. Explicit non-claims `docs/09-validity-limitations.md:29-35`.

---

## D. Hypothesized only (no decisive test in either setting)

D1. Soft-SLA handling of S2/S5 preserves flexibility without killing compliance — proposed (approval SLA 2d + delegation; receipt overdue alert), never executed in R2 (“intentionally out of scope”). `docs/06-redesign-and-r2.md:17,30`.

D2. Temporal-deviation importance/thresholds — “tolerable variation only relative to stated rule set, pending SLA validation”; no practitioner-agreed thresholds. `docs/09-validity-limitations.md:7,34`.

D3. Live-Odoo row-for-row swap will reproduce synthetic effects — path documented (`docker compose` + `sql/odoo_extract.sql`), not executed with live export. `README.md:41`, `docs/04-odoo-execution-protocol.md:38`.

D4. Any field pilot of a hard control (billing block / tolerance calibration / re-approval gate) at recording stage with pre-registered H8 test — proposed in `docs/15-thesis-outline.md:113`, `docs/13-cross-validation.md:224-226`, not run.

D5. Credit-note / partial-receipt / tolerance-calibrated workflows as field-viable alternatives — out-of-model by design (`docs/09-validity-limitations.md:7`), hypothesised only.

---

## E. Contradicted by field (lab assumption fails or needs redefinition)

E-contradiction 1 — **S3-absent (H2 nuanced / falsifier A INCONCLUSIVE-formal → partial-contradiction substantive).**
Lab S3 20/20=1.0 applicable (20/120=0.1667 overall anchor) vs field after-GR 0/11128=0.0. Cost signature untestable (viol null vs compliant block 0.2056, delay median 26.32d, payment-signal 0.8919). Billing-block redesign targets a non-problem *in this stratum* — no recorded-early mass to block. `data/hypotheses.csv:3`, `docs/11-bpic2019-results.md:141-153`, `docs/13-cross-validation.md:72,118-124,166-173`, `docs/07-real-dataset.md:108-113`. Mechanism (§A-E13) explains absence (recording gate absorbs 5754 vendor-early → 0 recorded-early) but does not rescue relevance.

E-contradiction 2 — **R3-tolerance (falsifier B REFUTED; H3 supported-as-proxy + H4 structural-zero).**
Tolerance-0 enforced norm describes neither stratum: after-GR routine deltas 1584/11128=0.1423 with correction-given-viol 0.1572 (=249/1584, <0.50 threshold) refutes tolerance-0; before-GR 0/199564=0.0 is structural vacuity, not enforcement. Probe confirms mass above 1.0/10.0 EUR (max 549.0), not rounding (epsilon 0.01; before-GR probe 0/80>0.01). Lab over-billing effect does not survive as tolerance-0 claim; remaining claim is directional proxy with −0.8577 magnitude gap. `data/hypotheses.csv:4-5`, `docs/11-bpic2019-results.md:38-43,155-163`, `docs/13-cross-validation.md:175-184`.

E-contradiction 3 — **R4-definition (falsifier C NUANCED/REFUTED-on-rate; H5 nuanced; H6 supported-as-exclusion).**
Naive lab→field transfer conflates approval workflow with rework: 2-way approval-change 1000/1044=0.9579 vs qty/price rework 10/1044=0.0096 (two orders of magnitude); overall 4290/251734 vs 26366/251734, approval-only 3301/251734. Quoting any-change as R4 inflates 2-way ~50× (probe 57/60). Corrected rework persists 26366/251734=0.1047 (after-GR 1882/15182=0.1240, before-GR 23315/221010=0.1055) above F2 base 0.0215 (1.34%+0.78%), *but* excess cannot be attributed to behaviour alone — publishers’ case definition vs present line-item grain + date filter are not shown identical; delay penalty (+7d vs +1d lab) not re-estimated. So: rework is not lab artifact, yet Round-2 −100% fix transfer is NOT established. `data/hypotheses.csv:6-7`, `docs/11-bpic2019-results.md:165-180`, `docs/13-cross-validation.md:186-198`.

---

## F. Genuinely open (H8 + transferability + 1704-definition + gaps)

F1. **H8 redesign transfer: OPEN.** Lab pre 60/60=1.0 → post 0/60=0.0; field n/a, UNTESTED, no intervention observed. `data/hypotheses.csv:9`, `docs/13-cross-validation.md:78,200-226`.

F2. Transferability constraint: gates must target *recording*, not vendor action; value-delta gate faces tolerance-calibration (14.2% routine mass, 15.7% correction), not zero-tolerance enforcement. No calibrated-tolerance trial run. `docs/13-cross-validation.md:207-226`.

F3. R4-vs-F2 definitional gap unresolved: event-to-case mapping + denominator non-identity; delay-penalty side not re-estimated. Cannot claim behavioural excess or cost-benefit. `docs/11-bpic2019-results.md:171-180`, `docs/13-cross-validation.md:228-236`.

F4. **1704-definition open to semantics:** published “1704 record+clear before GR despite after-GR requirement” not reproduced as R2 timing violation under system-recording definition (exact full-scan n=251734: D1 16356 all before-GR / 0 after-GR; D2/D4 89 each all before-GR; R2 after-GR 0/11128 all definitions). Reconciliation offered: vendor-action vs system-recording semantics. Any citation of 1704 without stating which timestamp is ambiguous. `/tmp/bpic_1704_out.json` ephemeral (not in repo — reproducibility gap), summarised `docs/11-bpic2019-results.md:182-214`, `docs/07-real-dataset.md:123-127`, `docs/13-cross-validation.md:96-109`. Blunt note: `/tmp` probes are not repo artifacts (`docs/14-data-stewardship.md:64-65`); independent re-scan required to close.

F5. S6R overhead ambiguity: +1d reported as 8.0d vs 7.0d (`docs/06-redesign-and-r2.md:29`, `docs/07-real-dataset.md:88`) vs 9.19d vs 8.04d (`docs/09-validity-limitations.md:33`). Which baseline (S1 vs S6) and which sample is unresolved — do not quote single “+1d” without source line.

F6. Live-Odoo + SLA-validation + tolerance-sweep + re-estimated delay penalty: all proposed, none run. See D1–D5.

Count F (open): **6 items** (F1–F6). Count D (hypothesized-only): 5. Total open/hypothesized: 11.

---

## H1–H8 status table (verified from `data/hypotheses.csv:2-9`)

| H | Rule/track | Lab rate + n | Field rate + n | Status (CSV) | Falsifier | Reading (blunt) |
|---|---|---|---|---|---|---|
| H1 | R1 / field | n/a (no 2-way lab arm) | 590/1044=0.5651 (overall 3450/251734=0.0137) | supported | n/a | Reproduces F1 ~0.56 in matching stratum only; 3-way R1 readings are not maverick construct. |
| H2 | R2 / field | 20/20=1.0 S3 (anchor 20/120=0.1667) | 0/11128=0.0 after-GR | nuanced | A INCONCLUSIVE → partial contradiction | Lab pattern absent where rule applies; cost comparison null-null. |
| H3 | R3 / field (after) | 20/20=1.0 S4 | 1584/11128=0.1423 | supported (as-proxy) | B REFUTED (tolerance-0) | Direction replicates, magnitude −0.8577; tolerance-0 as norm refuted; correction 0.1572. |
| H4 | R3 / field (before) | n/a (no before-GR arm) | 0/199564=0.0 | supported | B before-arm 0.0 | Structural zero, not enforcement evidence. |
| H5 | R4 / field | 20/20=1.0 S6 | 26366/251734=0.1047 (strata 0.96%/12.4%/10.5%) vs F2 base 0.0215 | nuanced | C REFUTED-on-rate, NUANCED-on-attribution | Persists above base but definitional gap unresolved; transfer NOT established. |
| H6 | R4-exclusion / field | n/a (S6 is qty/price) | approval 1000/1044=0.9579 vs rework 10/1044=0.0096; approval-only 3301/251734=0.0131 | supported | C-approval-exclusion | Exclusion load-bearing; naive transfer inflates 50× in 2-way. |
| H7 | R5 / field | 0/120 lab (no signal) | 408/251734=0.0016 (all strata <0.01) | supported | rarity threshold | Rare confirmed; lab contributed no signal. |
| H8 | redesign / lab→field | pre 60/60=1.0 → post 0/60=0.0 | n/a UNTESTED | open | UNTESTED | Lab effect licences only pilot hypothesis. |

Tally: **5 supported / 2 nuanced / 1 open — confirmed.**

`data/comparison.csv:2-5` cross-check: R2 20/20 vs 0/11128 diff 1.0; R3-after 20/20 vs 1584/11128 diff 0.8577; R4-3way 20/20 vs 25197/236192 diff 0.8933; R1-2way 590/1044=0.5651. Note: R4-3way pooled denominator (236192) differs from corrected-overall (251734) — use `docs/11` corrected figure for citation, document which denominator is used.

---

## G. Claims stronger than evidence — each + recommended correction (no in-place rewrite)

G1. “whether targeted ERP configuration can **eliminate the latter** without sacrificing flexibility” — `docs/00-abstract.md:5` (research question framing). **Correction:** append “*under controlled lab conditions (targeted S3/S4/S6 cohort, 60/60→0/60, seeds 42/7); field transfer untested (H8 open)*”.

G2. “**All 60 targeted deviations are detected with zero S1 false positives**” — `docs/00-abstract.md:5`. Second clause missing denominator. **Correction:** “*60/60 targeted; 0/20 false positives in S1 (compliant baseline cohort)*”.

G3. “**elimination to 0/60 after redesign**” + “**violations fall 60/60 to 0/60**” without cohort scope in same sentence — `docs/00-abstract.md:5,15`. **Correction:** “*elimination to 0/60 in the targeted lab R2 cohort (S3R/S4R/S6R, n=60, seed 7); S2/S5 temporal arms out of scope*”.

G4. “**Transferable** control-design distinction. Evidence that hard ERP controls … **eliminate compliance failures**” — `docs/00-abstract.md:16` (strongest inflation: transferable + eliminate, H8 open, falsifiers A/B/C adverse). **Correction:** “*Lab-scoped control-design distinction: hard controls eliminated targeted violations under lab conditions; transferability not established — H8 open; S3 absent in field, tolerance-0 refuted, R4 transfer not shown*”.

G5. PM4Py “**fitness 1.0, precision 0.98**” listed under “Triangulated quantitative evidence” alongside chi2/Fisher — `docs/00-abstract.md:5,15`. Risks normative-conformance reading, explicitly disclaimed `docs/09-validity-limitations.md:35`, `docs/10-appendix.md:23-33`. **Correction:** “*fitness 1.0 / precision 0.9796 vs model discovered from same log (variant/triangulation only; normative verdict from frozen R1–R5 checker)*”.

G6. “**Targeted deviations eliminated (-100%)**” + “**Hard ERP controls eliminate the latter**” — `docs/06-redesign-and-r2.md:28,33`. No “under lab conditions” in sentence. **Correction:** “*eliminated in lab R2 cohort (0/60 targeted, seed 7); field transfer untested; R2 billing-block targets non-problem in BPIC after-GR stratum (0/11128)*”.

G7. “driving violations **1.0->0.0**” — `README.md:13`. Rate missing denominator. **Correction:** “*driving targeted-cohort violations 60/60=1.0 → 0/60=0.0 (lab, seeds 42/7)*”.

G8. Outdated R4 sampling instruction: “Label R4 proxy where **Change Quantity/Price or Change Approval** occurs” — `docs/07-real-dataset.md:47-48`. Contradicts corrected definition (approval excluded, `docs/11-bpic2019-results.md:57-60`, `src/signatures.py:40`). **Correction:** flag §38 steps 8–10 as superseded; point to corrected full-run definition (qty/price-only + separate `approval_change_after_po`).

G9. R3-as-quantity wording where field object is meant: `docs/01-normative-model.md:16` (“Quantity invoiced <= quantity received, tolerance 0”) is correct as *lab* definition but is cited without proxy qualifier wherever field R3 is discussed without “value-proxy” (notably `docs/00-abstract.md:5` “zero-tolerance matching” and `docs/06-redesign-and-r2.md:6` v2 “qty<=received, tol.0” if read as prescription). **Correction:** each field-facing R3 sentence must carry “*lab quantity rule; field analogue is value-delta proxy (H3 supported-as-proxy, tolerance-0 refuted per falsifier B)*”.

G10. Denominator-free published base rates in `docs/07-real-dataset.md:65-72` (“~56%”, “≈2.15%”, “1,704 sequences”, “~26%”) and `docs/05-findings-r1.md:17` (“0 false positives in S1” without /20). **Correction:** pair every rate with `n_true/n_applicable` (e.g., F1 590/1044 stratum, F2 1.34%+0.78% with publishers’ case denominator, 1704 with vendor-vs-recording definition, S1 0/20).

G11. S6R overhead single-figure “+1 day” without baseline — `docs/06-redesign-and-r2.md:29` (8.0d vs 7.0d) vs `docs/09-validity-limitations.md:33` (9.19d vs 8.04d). **Correction:** cite both with source lines and state which baseline (S1 baseline vs S6) until reconciled; do not quote bare “+1d”.

Count G: **11 issues** (G1–G11). Includes all mandated classes: ‘eliminates deviations’ without ‘under lab conditions’ (G1,G4,G6), rates missing denominators (G2,G7,G10), R3-as-quantity wording (G9).

---

## Counts (return)

- Established (A): **14**
- Proxy / lossy / derived (B): **9**
- Open: **6 (F) + 5 hypothesized-only (D) = 11 open/hypothesized**; H-status **5 supported / 2 nuanced / 1 open**
- G-issues stronger than evidence: **11**

## Ambiguities documented (not resolved)

1. S6R overhead baseline (F5/G11). 2. R4-3way denominator `data/comparison.csv:4` (25197/236192) vs corrected overall (26366/251734) — cite `docs/11` figure. 3. `/tmp` probes ephemeral — re-scan needed for 1704 closure. 4. `docs/07` sampling plan steps 8–10 superseded by corrected run — retained as history, flagged G8.
