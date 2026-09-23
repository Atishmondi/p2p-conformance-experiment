# Thesis Outline — Conformance Checking in P2P: Lab Experiment + BPIC 2019 Field Study

> Source skim: `docs/00-abstract.md`, `docs/10-appendix.md` (§A–C), `docs/13-cross-validation.md` (§1–2), `docs/16-research-audit.md` (§E–G), `docs/17-erp-experiment-protocol.md` (§§1–8, headings + H-table + gate order).
> This outline only. All evidence lives in linked artifacts — no numbers are re-argued here.
> 10-chapter canonical map (kept to 8 outline chapters, 10 max — no chapters added for appearance): Ch1=intro, Ch2=background, Ch3=problem+hypotheses+method, Ch4=lab, Ch5=field, Ch6=results (cross-validation), Ch7=ERP experiment (protocol-only), Ch8=limitations+conclusion. Defense Q&A + threats: `docs/18-defense-and-validity.md` (10 Q&As, 6 threat families).

## Research question (from README, `docs/01-normative-model.md`)

**RQ:** How do deviations between the normative purchase-to-pay process and its execution in an ERP system emerge, and what process-design or ERP-configuration changes can reduce these deviations?

Sub-questions: (1) which variants occur? (2) temporal vs behavioural deviations? (3) design vs configuration causes? (4) does redesign reduce deviations?

## Word-budget overview (target ~20,000; was ~18,500, +1,500 for protocol-only Ch7, no results)

| Chapter | Title | Budget |
|---|---|---|
| Ch1 | Introduction | 1,500 |
| Ch2 | Foundations: BPMN P2P + BPIC background | 3,000 |
| Ch3 | Method: 9-step backbone, signatures, hypothesis registry | 3,000 |
| Ch4 | Lab experiment: R1/R2 + checker + stats | 4,000 |
| Ch5 | Field study: XES stewardship, mapping, rates | 3,000 |
| Ch6 | Cross-validation: lab-vs-field, falsifiers (results) | 2,500 |
| Ch7 | ERP experiment: Odoo protocol, H8 preregistration (no results) | 1,500 |
| Ch8 | Conclusion: limitations + constrained claims, H8 open | 1,500 |

---

### Ch1 — Introduction (1,500 words)

**Artifacts used:**
- `README.md` (RQ + subquestions, closed-loop status)
- `docs/00-abstract.md` (60/60→0/60 headline, hard-vs-soft-controls contribution)
- `docs/01-normative-model.md` (R1–R5, S1–S6 preview)

**Writing prompts:**
1. Open with the confound: why does real-log conformance conflate tolerable delay with control failure, and why does your RQ need a controlled ERP experiment to separate them?
2. State RQ + 4 subquestions verbatim from README/`docs/01`, then map each to the chapter that answers it (Ch4 lab, Ch5 field, Ch6 comparison, Ch7 ERP protocol, Ch8 redesign limits).
3. Preview the operational distinction (hard controls for failures, soft SLAs for variation) without claiming field transfer — reserve H8 as open.

### Ch2 — Foundations: normative P2P and real-log background (3,000 words)

**Artifacts used:**
- `docs/bpmn/normative.bpmn` + `docs/bpmn/v2.bpmn` (6-step request–approval–order–receipt–invoice–payment)
- `docs/01-normative-model.md`, `docs/02-scenarios.md` (R1–R5, S1–S6)
- `docs/07-real-dataset.md` (BPIC 2019 background, falsifiers A–C pre-registration)
- `docs/09-validity-limitations.md`

**Writing prompts:**
1. Define the 6-step normative model and formalise R1–R5 as ordering/attribute/rework predicates — why is tolerance 0 for R3 a design choice, not an empirical rate?
2. Summarise BPIC 2019 (251,734 cases, 2-way/3-way/consignment strata, F1/F2/F3 patterns) and why population-wide rates are misleading without denominator discipline.
3. Position vs literature: mature detection (alignments, fitness/precision) vs rare causal isolation — where does this thesis sit?

### Ch3 — Method: 9-step backbone, single-source signatures, hypothesis registry (3,000 words)

**Artifacts used:**
- `docs/04-odoo-execution-protocol.md` §6 (9-step backbone: BPMN → config → execution → log → mining → deviations → redesign → re-execution)
- `src/signatures.py::describe` (single source of truth: lab `check_case` vs field `evaluate_case`)
- `data/hypotheses.csv` (H1–H8 pre-registration), `data/comparison.csv` schema
- `src/generate_log.py`, `src/generate_log_r2.py` (seeds 42/7, business-hours clock, lognormal waits)

**Writing prompts:**
1. Walk the 9-step backbone in order — at which step does temporal variation (S2/S5 waits) enter vs behavioural injection (S3/S4/S6), and how does the frozen checker guarantee comparability across rounds?
2. Explain `signatures.py` as validity device: lab definition vs field proxy + applicable scope + known gaps per rule — why is "rule-in-applicable-cohort" the only fair unit of comparison?
3. Present H1–H8 as pre-registered predictions with falsifiers A–C — which hypotheses have no lab rate by design (H1, H4, H6, H7) and why?

### Ch4 — Lab experiment: controlled stochastic rounds (4,000 words)

**Artifacts used:**
- `data/event-log-r1.csv` (120 cases / 740 events, seed 42) + `data/event-log-r2.csv` (60 cases / 400 events, seed 7)
- `src/check_conformance.py::check_case` (frozen R1–R5), `data/conformance-r1.csv`, `data/conformance-r2.csv`, `data/summary-r1.csv`, `data/summary-r2.csv`
- `src/mining_pm4py.py` → `data/pm4py_results.json` (fitness 1.0, precision 0.98, 3 variants; see `docs/10-appendix.md` §B–C alignment-cost note)
- `src/evaluate.py` → `data/evaluation.csv` (60/60→0/60, chi2=120 p=6.3e-28, Fisher p=2.1e-35, Wilson CIs, Cohen h=3.14, Welch S1-vs-S2 t=-6.94 p=3.3e-08), `src/noise_test.py` → `data/robustness.csv`
- `docs/05-findings-r1.md`, `docs/06-redesign-and-r2.md` (billing blocks, zero-tolerance match, re-approval gates; +1d S6R overhead)

**Writing prompts:**
1. Report R1 by scenario (S1 baseline 0 FP, S2/S5 delay-only, S3 R2 20/20, S4 R3 20/20, S6 R4 20/20, R5 0 by design) — how do throughput stats prove delays surface only in performance, not conformance?
2. Defend the PM4Py reading: why must fitness 1.0 on a model *discovered from the same log* NOT be cited as normative conformance, and what does it validly contribute (variants, triangulation, precision penalty)?
3. Quantify redesign: 60/60→0/60 with full stats + robustness breakdown at 2% noise (recall 98.9%, FPR 11.7%) + S6R +1d trade-off — what efficiency cost buys control? Cross-ref `docs/16-research-audit.md` E-contradiction 1 / F2: S3 billing-block targets a non-problem in the BPIC after-GR stratum (lab S3 20/20 vs field 0/11128) — do not present lab elimination as field relevance.

### Ch5 — Field study: BPIC 2019 stewardship, mapping, rates (3,000 words)

**Artifacts used:**
- `docs/14-data-stewardship.md` (728 MB XES, one-copy streamed-in-place, MD5 `4eb909242351193a61e1c15b9c3cc814`, `data/bpic2019_case_results.csv` 22 MB)
- `src/analyze_bpic2019.py::evaluate_case` + Q1 mapping questions (maverick, after-GR, value-delta, rework proxies)
- `data/bpic2019_results.json` (FULL corrected run n=251,734), `data/bpic_mapping_demo.csv`, `docs/11-bpic2019-results.md` (Q2–Q3 rates)
- Field rates: R1 maverick 590/1,044=56.5% (2-way); R2 0/11,128=0.0% after-GR; R3 value-proxy 1,584/11,128=14.2% after vs 0/199,564 before; R4 qty/price-only 26,366/251,734=10.5% (approval-change 4,290/251,734=1.7% excluded); R5 408/251,734=0.16%

**Writing prompts:**
1. Justify stewardship under disk constraint: why one-copy streaming + MD5 audit + thin `case_results.csv` is sufficient for reproducibility without wholesale conversion?
2. Walk each Q1 proxy mapping with denominator discipline: why does R2 apply ONLY to 3-way after-GR with both timestamps (n=11,128), and why is before-GR R3 structurally 0?
3. Report Q2–Q3 rates always as n_true/n_applicable — where does the field corroborate lab direction but not magnitude (esp. R3 1.0→0.142, R4 1.0→0.105)? Cross-refs `docs/16-research-audit.md` E-contradictions 2–3 / P3/P6/P8 / G8–G9: tolerance-0 refuted (after-GR 1,584/11,128 routine vs before-GR 0/199,564 structural zero, value-proxy) and R4 approval exclusion load-bearing (qty/price-only 26,366/251,734; approval-change 4,290/251,734 tracked separately).

### Ch6 — Cross-validation: lab-vs-field comparison and falsifiers (2,500 words)

**Artifacts used:**
- `docs/13-cross-validation.md` (§1 pre-registration, §2 mapping premise, H-table, falsifiers A–C verdicts)
- `src/compare_lab_field.py` → `data/comparison.csv`, `data/hypotheses.csv` (H1 supported, H2 nuanced, H3 supported-as-proxy, H4 supported, H5 nuanced, H6 supported, H7 supported, H8 open)
- `docs/07-real-dataset.md` (falsifier definitions) + `/tmp/bpic_1704_out.json` 1704-reconciliation (F3 exact full-scan n=251,734)

**Writing prompts:**
1. Compare only applicable cohorts (lab n=20/scenario vs field strata): which hypotheses survive as directional support despite magnitude gaps, and which are nuanced/partial-contradictions (H2 R2 1.0 vs 0.0; H5 field 10.5% above F2 base 2.15%)?
2. Adjudicate falsifiers A (R2 band 0.1–0.25, INCONCLUSIVE), B (tolerance-0 REFUTED-both-strata logic), C (rework-vs-base REFUTED with approval exclusion load-bearing at 95.8% in 2-way) — what would have falsified each? Cross-ref `docs/16-research-audit.md` §E (contradictions 1–3) + F1–F4 (H8 open, 1704 vendor-vs-recording semantics) + G4 language rule (no "transferable eliminates" without H8-open qualifier).
3. Reconcile F3/1704: what does the exact full-scan add over the sampled mapping, and why does it not rescue H2?

### Ch7 — ERP experiment: Odoo transfer protocol, H8 preregistration (1,500 words, PROTOCOL ONLY — no results)

**Artifacts used:**
- `docs/17-erp-experiment-protocol.md` §§1–8 (RQ-H8 frame, 3-way-after-GR stratum, per-hypothesis protocol, §5 event-log contract, §6 control-vs-intervention + FLAGs, §7 threats, §8 preregistration record — intentionally empty results)
- `data/hypothesis_erp_mapping.csv` (H1-adapted, H2/H3/H5 directly testable priorities, H6 negative control, H7 monitored-only, H4 excluded structural-zero, H8 frame stays open)
- `data/hypotheses.csv` H8 (`lab 60/60→0/60; field transfer UNTESTED, status open`)
- `docs/16-research-audit.md` F1–F6 + D1–D5 + G1–G7 language rules (cohort + denominator + condition on every efficacy sentence)

**Writing prompts:**
1. Frame RQ-H8: do S3R billing block / S4R qty cap / S6R re-approval gate enforce the same signatures at Odoo Community 17's **recording stage** (3-way-after-GR only), and under what scope/tolerance conditions do they fail to transfer? Why does H8 stay open until rerun + field-base comparison are recorded?
2. Walk testability per `data/hypothesis_erp_mapping.csv` + `docs/17` §4: H2 recording-gate dual-ts 2×2 (occurred-early × recorded-early; field anchor vendor-early 5,754/15,182 → recorded-early 0/11,128), H3 tol-0 as lab norm not field prescription (field after-GR 1,584/11,128 + correction 0.1572), H5/H6 rework vs approval-exclusion (field 10/1,044 vs 1,000/1,044), H1-adapted approval-order, H7 rarity-monitored — which FLAGs (§6.2) block any field-control recommendation?
3. State validity gates: frozen `check_case`, column-for-column schema (§5.1), recorded-vs-recorded verdicts + `None`-rate reporting, stopping/FLAG criteria, both S6R baselines (no bare "+1d"), no `/tmp` citations — what counts as transferred vs mechanism-confined vs not transferred (§4 H8 verdict rule)?

### Ch8 — Conclusion: limitations + constrained claims and open transfer (1,500 words, was Ch7)

**Artifacts used:**
- `docs/00-abstract.md` contributions + `docs/09-validity-limitations.md`
- `data/hypotheses.csv` H8 (`lab 60/60→0/60; field transfer UNTESTED, status open`)
- `docs/06-redesign-and-r2.md` (hard controls vs soft SLAs)

**Writing prompts:**
1. State only what the design licences: hard ERP controls eliminate targeted lab failures under lab conditions (60/60→0/60 targeted, seeds 42/7); soft SLAs preserve flexibility — why must any field-transfer sentence carry the H8-untested qualifier?
2. List load-bearing limits in one paragraph each: synthetic-validity, proxy gaps (R3 value-for-qty, R1 maverick), R4 approval exclusion, noise breakdown at 2%.
3. Propose exactly two follow-ups: (a) live-Odoo export swap row-for-row via `sql/odoo_extract.sql`; (b) field pilot of one hard control with pre-registered H8 test — what is the falsifier?

---

## Defense Q&A (7)

1. **Why is S3/R2 absent in most field strata?** — R2 is applicable only in 3-way invoice-after-GR with both timestamps (n=11,128); before-GR/2-way/consignment carry n_applicable=0 by design, not by omission.
2. **Isn't your R3 field proxy invalid (value for quantity)?** — It is a declared proxy (no qty fields in BPIC): lab S4 20/20=1.0 vs field after-GR 1,584/11,128=14.2% supports direction-as-proxy with lower magnitude, low correction rate 15.7%.
3. **Does your R4 fix transfer to the field?** — No: lab S6→S6R re-approval gate drives 20/20→0/20, but field qty/price rework stays 26,366/251,734=10.5% — H5 nuanced, Round-2 −100% does not transfer (H8 open).
4. **What does the 1704-reconciliation prove?** — Exact full-scan over 251,734 cases (`/tmp/bpic_1704_out.json`) confirms the F3 ordering/block pattern independently of sampling, without overturning the H2 partial-contradiction.
5. **Can hard controls transfer to real ERP?** — Untested: H8 is pre-registered open — lab elimination 60/60→0/60 licences only a pilot hypothesis, with +1d S6R overhead as the efficiency cost to test.
6. **Why trust synthetic logs at all?** — Seeds 42/7, business-hours clock, lognormal waits, vendor effects and frozen checker isolate delay from failure with zero S1 false positives — but synthetic-validity limits all claims to the lab unless field-tested.
7. **What does the ERP chapter claim?** — Nothing empirical: Ch7 is `docs/17` protocol-only (Odoo Community 17, 3-way-after-GR recording stage; H1-adapted/H2/H3/H5/H6/H7 per `data/hypothesis_erp_mapping.csv`, H4 excluded, H8 frame stays open). No Odoo executed, no H8 closure — see `docs/16-research-audit.md` F1–F2/D1–D5 for what remains open.
