# PROJECT HANDOFF — P2P Conformance Experiment

> **Purpose of this file:** complete context package for a new agent/human continuing this project with zero prior conversation. FACT = verified in repo. INTERPRETATION = repo's stated reading. HYPOTHESIS = pre-registered, untested. PLANNED = protocol exists, not executed. OPEN = unresolved. Authorship: compiled by a reviewing agent from direct file inspection on 2026-09-23; every number below was read from the repository, not recalled.
>
> **How to use:** read §38 first for orientation, then the research chain (§4), then the area you will work on. Before changing anything, read §27 (invariants) and §32 (working rules).

---

# 1. PROJECT IDENTITY

- **Project name (title):** "From Intended Process to Executed Process: Conformance Analysis of P2P in an ERP-Based Controlled Experiment" (`README.md:1`).
- **Repository/folder name:** `p2p-conformance-experiment`.
- **Local path (FACT, at handoff creation):** `/Users/atishmondi/Documents/Default Project/p2p-conformance-experiment`. Paths elsewhere in this doc are relative to repo root unless stated.
- **Research domain:** Wirtschaftsinformatik / Information Systems — process mining + ERP.
- **Topic:** purchase-to-pay (P2P) process conformance: normative model vs executed process, deviation detection, control redesign, transferability.
- **Application domain:** ERP-based procurement (Odoo Community as experimental environment; BPI Challenge 2019 purchase-order-handling log as field reference).
- **Technologies:** Python 3.9.6 (env at handoff; webpage footer claims "3.10+" — DISCREPANCY, see §28), pandas/numpy/scipy/matplotlib, pm4py 2.7 (installed), Odoo Community 17 via Docker (documented, never executed here), PostgreSQL 15 image, Chart.js webpage, bash/Make.
- **Current phase (FACT):** research foundation FROZEN in git; ERP experiment PREREGISTERED but NOT executed.
- **Intended final deliverable:** masters thesis (~20,000 words, Ch1–Ch8 per `docs/15-thesis-outline.md`) + reproducible experiment codebase + showcase webpage.
- **Academic positioning:** hypotheses-driven IS research (falsifiable deviation hypotheses, controlled injection, signatures, transferability), NOT a PM4Py tutorial. PM4Py is a tool; Odoo is an environment (`docs/18` Q9, `docs/16` §C premise).

**One sentence:** A hypotheses-first P2P conformance study that pairs a controlled synthetic lab experiment (known ground truth, causal redesign evidence) with a full-stream analysis of the real BPI Challenge 2019 log (field base rates, documented contradictions), preregistered toward an Odoo ERP transferability experiment (H8, open).

**One paragraph:** The project defines a 6-step normative P2P model with five executable rules (R1–R5) and eight pre-registered hypotheses (H1–H8). It tests them two ways: (1) a stochastic lab experiment (Round 1: 120 cases/740 events, seed 42; Round 2 after redesign: 60/400, seed 7) proving a frozen checker catches 60/60 injected deviations and redesign drives them to 0/60 under lab conditions; (2) a streaming analysis of all 251,734 BPI Challenge 2019 cases establishing field base rates with applicable denominators — reproducing published maverick-buying (56.5% in 2-way) while contradicting two lab assumptions (S3 ordering failure absent: 0/11,128 after-GR; zero-tolerance R3 refuted: 14.2% routine deltas). The lab→field transfer claim (H8) is explicitly OPEN; the next phase (preregistered in `docs/17`, no Odoo executed) tests it in Odoo Community 17.

**Technical (detail):** see §4 chain, §6 model, §7–§8 hypotheses/signatures, §9–§11 field, §12–§14 lab/comparison, §16–§18 ERP/H8/validity, §21–§22 code/data architecture, §33 commands, §34 file map.

---

# 2. WHY THIS PROJECT EXISTS

- **Original motivation (INTERPRETATION from repo evolution):** apply process mining to P2P in a real ERP (Odoo) instead of only mining a public log — "I configured an ERP, executed transactions, extracted process data" vs "I mined this log" (`docs/04`, early README history per §2 of prompt; current README states Odoo-protocol synthetic stand-in).
- **Research motivation:** real-log conformance conflates tolerable delay with control failure because ground truth is unknown; a controlled experiment with known injected deviations separates checker correctness from field diagnostic accuracy (`docs/09-validity-limitations.md:3-15`, `docs/18` Q1).
- **Practical motivation:** distinguish slow-but-compliant (S2/S5) from fast-but-noncompliant (S3/S4/S6) so ERP controls target failures without killing flexibility (hard blocks vs soft SLAs; `docs/06` §5, `docs/05` §5).
- **Academic motivation:** closed-loop Wirtschaftsinformatik artifact — normative BPMN → Odoo config → execution → event log → mining → deviations → redesign → re-execution (`README.md:8`), plus falsifiable hypotheses + transferability (H8).
- **Why P2P/ERP conformance:** procurement is rule-dense (approvals, 3-way match, tolerances, rework) and ERP-enforceable — ideal for signature-based conformance.
- **Why process mining:** variant discovery, alignments/fitness diagnostics, performance (waiting-time) analysis triangulate the rule checker (`src/mining_pm4py.py`, `docs/10` §B).
- **Why ERP execution matters:** only an executable system lets you inject X → observe Y → change Z → measure (causal control), which observation alone cannot (`docs/13` §7, `docs/18` Q5).
- **Why Odoo:** open-source, inspectable, real control points (bill control on received quantities, PO lock + re-approval), single-company Community scope keeps it finishable (`docs/18` Q6, `docs/03`, `docs/17` §2).
- **Why PM4Py:** discovery/variant/alignment triangulation only — explicitly NOT the normative verdict and NOT the contribution (`docs/18` Q9, `docs/10` §B).
- **Why field + lab:** lab gives causal control with perfect labels; field (BPI 2019) gives external reference/base rates and falsification power. Either alone is insufficient (`docs/13`).
- **Why a controlled ERP experiment is still needed:** lab is synthetic (H8 open); field is observational (no intervention). Only an ERP intervention with pre/post measurement closes transferability (`docs/17`, H8).
- **Evolution (FACT from repo):** started as Odoo+P2P experiment idea (normative model + S1–S6); grew a synthetic lab with conformance checker + Round-2 redesign loop; added PM4Py/stats/robustness; then pivoted to field grounding via full BPI 2019 analysis (falsifiers A–C); contradictions found (S3-absent, R3-artifact, R4-definition); response was refinement (15-agent audit wave, QA 14/14) + preregistered ERP protocol — NOT scope inflation. Current state = frozen foundation + open H8.

---

# 3. RESEARCH QUESTION

**Current RQ (FACT, `README.md:11`, `docs/15` Ch1):** "How do deviations between the normative purchase-to-pay process and its execution in an ERP system emerge, and what process-design or ERP-configuration changes can reduce these deviations?" Subquestions (`docs/01:20-24`): which variants emerge; temporal vs behavioral deviations; design vs configuration causes; what redesign reduces deviations.

- **What it asks:** mechanism (how deviations emerge: ordering/attribute/rework signatures + delay) + intervention efficacy (do controls reduce targeted violations, at what cost).
- **What it does NOT ask (per repo):** whether controls *should* be deployed in production; cost-benefit; SLA validity; SAP generality; residual-risk-zero (all explicit non-claims, `docs/09:29-35`, `docs/17` §1 "Non-question").
- **Dependent variables:** violation counts/rates per rule with applicable-n; conformance rate; cycle/waiting durations; variant distribution.
- **Independent/intervention variables (lab):** injected deviation (S3/S4/S6) and redesign gates (S3R billing block, S4R qty cap, S6R re-approval). (INTERPRETATION: lab independent variables are scenario + round; no randomization — stagger ≠ random assignment, `docs/18` T2a.)
- **Observational component:** BPI 2019 field rates per stratum (no intervention observed).
- **Experimental components:** lab R1→R2 (frozen detector, fixed seeds); PLANNED ERP control-vs-intervention (`docs/17` §6).
- **RQ-H8 frame (`docs/17:16`):** "Do the lab-demonstrated hard controls enforce the same normative signatures when implemented at the recording stage of Odoo Community 17 P2P, and under what scope/tolerance conditions do they fail to transfer?"

---

# 4. CORE RESEARCH ARGUMENT

```
BPI Challenge 2019 field data (n=251,734, MD5-verified XES)
        ↓  controlled transformation (Q1: EXACT vs LOSSY columns)
field signatures + applicable denominators (R1–R5 proxies, strata)
        ↓  pre-registration
H1–H8 hypotheses (5 supported / 2 nuanced / 1 open) + falsifiers A–C
        ↓  stochastic lab experiment (seeds 42/7, frozen checker)
observed causal effects (60/60→0/60 targeted, stats, trade-off)
        ↓  cross-validation (docs/13)
contradictions + transferability gaps (S3-absent, R3-artifact, R4-definition)
        ↓  constraint + preregistration
ERP protocol docs/17 (controls target RECORDING; tolerance/attribution FLAGs)
        ↓  PLANNED, NOT EXECUTED
Odoo ERP experiment → H8 verdict (transferred / mechanism-confined / not transferred)
```

- **Why the sequence matters:** each stage can only establish what its design licences. Field observation cannot show causation (no intervention); lab causation cannot show field relevance (synthetic); the comparison is what constrains the redesign claim and motivates the ERP test. Skipping field → overclaims transfer; skipping lab → no causal evidence at all.
- **What each stage CAN establish:** field = existence + base rates in one setting; lab = detector correctness + config enforcement under control; comparison = directional support + contradictions; ERP (planned) = recording-stage transfer verdict.
- **What each stage CANNOT establish:** field ≠ intervention efficacy; lab ≠ SAP/generality, residual risk, noisy-field accuracy; comparison ≠ attribution where definitions differ (R4-vs-F2 gap); ERP-planned ≠ anything until executed.

---

# 5. KEY METHODOLOGICAL PRINCIPLE

**Principle (repo's own words, `docs/13`/`docs/17` gate):** do NOT start by assuming the process is broken. Pre-register falsifiable deviation hypotheses (H1–H8 + falsifiers A–C) with predicted event signatures, THEN look for evidence. The 9-step backbone (`docs/04:51-60`): define → signatures → execute → extract → detect → verify → modify → rerun → measure; gate order mandatory (no execution before preregistration, no modification before field comparison).

- **Falsifiability:** falsifiers A (band 0.10–0.25), B (refute if max rate >0.05 with correction <0.50), C (band 0.0015–0.0415) with exact verdict rules in code (`src/analyze_bpic2019.py:560-620`).
- **Controls:** S1 baseline; S2/S5 performance arms; frozen detector both rounds; fixed masters/seeds.
- **Interventions:** S3R/S4R/S6R gates (lab, demonstrated); ERP gates (planned, `docs/17` §4).
- **Observational vs causal evidence:** field rates = observational; lab 60/60→0/60 = causal-under-control (frozen checker + fixed everything else except redesign; NOT randomized — stagger only).
- **Transferability:** lab→field comparison (attenuated support + contradictions) + ERP test (open). Never claimed from lab alone.
- **Construct validity:** signatures vs concepts per rule; known gaps documented in `src/signatures.py` (R1 maverick≠approval-order; R3 value≠qty; R2 recording≠physical; R4 approval-exclusion; R5 clear≠cash).
- **Internal validity:** single-operator, single-batch rounds, no concurrent R2 control arm, period effects inseparable from intervention except via frozen-checker argument (`docs/18` T2).
- **External validity:** Odoo Community single-config + synthetic single-team + one field company = existence-in-settings, not population generality.
- **Measurement validity:** checker brittleness (FPR 0.117 at 2% missing events); PM4Py fitness is discovery-diagnostic; None-rates (R2 4,054/15,182 = 26.7%; R3-before None 21,446/221,010 = 9.7%) are not conformance.
- **Data validity:** XES column losses (no qty, no scenario labels); worth-proxy dependence; epsilon 0.01 load-bearing but probe-checked.
- **Reproducibility:** seeds 42/7, frozen checker, run registry, MD5, preregistration; `/tmp` probes ephemeral (not citable).

**Latent vs recorded (load-bearing distinction):** vendor-action timestamps (e.g. `Vendor creates invoice`, vendor bill date) = physical/latent arrival; system timestamps (`Record Invoice Receipt`, bill Validate) = recorded process behavior. Field proof: after-GR vendor-early 5,754/15,182 cases yet recorded-early 0/11,128 — the recording gate absorbs latent earliness. R2 verdicts use recorded-vs-recorded ONLY (`docs/17` §5.2). Never quote vendor-action earliness as an R2 violation.

---

# 6. NORMATIVE PROCESS MODEL

**Sequence (FACT, `docs/01:5-11`):** 1. Purchase Request (create) → 2. Purchase Request Approval (approve) → 3. Purchase Order (confirm) → 4. Goods Receipt (receive) → 5. Vendor Invoice (record) → 6. Payment (pay). Scope strictly P2P; no inventory valuation, no multi-company.

**Rules (FACT, `docs/01:13-18` + formal predicates `docs/10` §A):**
- R1: first Approval ts < first PO ts (else violation, incl. missing).
- R2: first GR ts < first Invoice ts (3-way-match ordering).
- R3: qty_invoiced ≤ qty_received, tolerance 0 (first GR/invoice qtys, fallback to first event).
- R4: every PO Modification needs a later Approval before PO (Round-2 `Purchase Request Approval (re-approval)` satisfies via `Approval` substring).
- R5: first Payment ts > first Invoice ts (control rule; 0 violations by design both rounds).

**BPMN (`docs/bpmn/`):** `normative.bpmn` (6 tasks in sequence) and `v2.bpmn` (adds re-approval gateway after PO change, receipt-required gateway before invoice, qty gate, SLA timers). Both valid BPMN 2.0 XML (verified parse). Normative = intended; discovered (PM4Py inductive net) = observed-model diagnostic — NEVER conflate (fitness 1.0 is vs discovered net by construction).

---

# 7. HYPOTHESES H1–H8

**Authority:** `data/hypotheses.csv` (9 lines: header + H1–H8). Status verified in repo (FACT): **5 supported (H1,H3,H4,H6,H7) / 2 nuanced (H2,H5) / 1 open (H8)**. Table first, then subsections. Rates below are FACT from repo files.

| H | Rule/track | Lab rate+n | Field rate+n | Status | Falsifier |
|---|---|---|---|---|---|
| H1 | R1/field | n/a (no 2-way lab arm) | 590/1044=0.5651 (overall 3450/251734=0.0137) | supported | n/a |
| H2 | R2/field | 20/20=1.0 S3 (anchor 20/120=0.1667) | 0/11128=0.0 after-GR | nuanced | A INCONCLUSIVE→partial contradiction |
| H3 | R3/field-after | 20/20=1.0 S4 | 1584/11128=0.1423 | supported-as-proxy | B REFUTED (tolerance-0) |
| H4 | R3/field-before | n/a (no before-GR arm) | 0/199564=0.0 structural | supported | B before-arm |
| H5 | R4/field | 20/20=1.0 S6 | 26366/251734=0.1047 | nuanced | C REFUTED-on-rate, NUANCED-on-attribution |
| H6 | R4-exclusion/field | n/a (S6 is qty/price) | approval 1000/1044=0.9579 vs rework 10/1044=0.0096 | supported | C-approval-exclusion |
| H7 | R5/field | 0/120 (no signal) | 408/251734=0.0016 | supported | rarity threshold |
| H8 | redesign lab→field | pre 60/60=1.0 → post 0/60=0.0 | n/a UNTESTED | open | UNTESTED |

- **H1 (R1 maverick, supported):** rationale = 2-way procurement without receipt gate concentrates unapproved spend. Operationalization: min(`Vendor creates invoice`) < min(`Create Purchase Order Item`) in 2-way stratum. Predicted: 2-way rate >0.5. Result 590/1044=0.5651 reproduces published F1 ~0.56 in matching stratum. Limitation: lab has no 2-way arm; 3-way readings (2.1%/1.1%) are not the construct. ERP: ADAPTED (approval-order test; maverick not replicable without 2-way arm). Evidence: results JSON `r1_two_way_stratum`, `docs/11` Q3, `docs/13` §5a.
- **H2 (R2 ordering, nuanced):** rationale = invoice-before-recording violates 3-way-after-GR policy. Predicted lab S3 rate ≈ field rate (band 0.10–0.25, anchor 0.167). Result: lab 20/20 vs field 0/11,128 → pattern absent where rule applies; cost comparison null-null → falsifier A INCONCLUSIVE formally, partial contradiction substantively (billing block targets non-problem in this stratum). ERP: ADAPTED priority (recording-gate test with dual timestamps). Evidence: `docs/11` Q4-A, `docs/13` §4/§6a, `docs/07:108-113`.
- **H3 (R3 after-GR proxy, supported-as-proxy):** rationale = over-billing detectable as value delta. Predicted >0 with low correction. Result 1584/11128=0.1423, correction-given-viol 249/1584=0.1572; probe mass above 1/10 EUR (max 549), not rounding. Tolerance-0 as enforced norm REFUTED (falsifier B). ERP: YES priority (tol-0 as lab norm only, not prescription). Evidence: `docs/11` Q4-B, `docs/13` §5b.
- **H4 (R3 before-GR structural zero, supported):** rationale = no GR reference at invoice time → vacuous satisfaction. Result 0/199,564; probe 0/80>0.01. INTERPRETATION: structural, not enforcement. ERP: EXCLUDED (no before-GR arm). Evidence: `docs/11` Q3, signatures R3 known_gaps.
- **H5 (R4 rework, nuanced):** rationale = post-PO changes persist above published F2 base 0.0215 (1.34%+0.78%). Result 26366/251734=0.1047 (strata 0.96%/12.4%/10.5%/8.0%). Falsifier C REFUTED-on-rate BUT attribution unresolved (publisher case definition vs line-item grain + date filter non-identity; delay penalty not re-estimated) → transfer NOT established. ERP: YES priority. Evidence: `docs/11` Q4-C, `docs/13` §5c/§7.
- **H6 (R4 exclusion, supported):** rationale = Change Approval is routine workflow, must be excluded. Result: 2-way approval 1000/1044=0.9579 vs rework 10/1044=0.0096 (two orders of magnitude); probe 57/60 vs 0/60+1/60. Exclusion load-bearing; naive transfer inflates ~50×. ERP: negative control (approver reassignment must NOT fire R4). Evidence: probes, `docs/13` §6c.
- **H7 (R5 rarity, supported):** rationale = payment-before-invoice rare (<0.01). Result 408/251734=0.0016 all strata; lab 0/120 no signal. ERP: monitored only. Evidence: results JSON, `docs/11` Q3.
- **H8 (redesign transfer, OPEN):** rationale = lab 60/60→0/60 licences pilot hypothesis only. Field transfer UNTESTED, no intervention observed. Verdict options preregistered (`docs/17` §4): transferred / mechanism-confined / not transferred. ERP: the frame itself. Evidence: `data/hypotheses.csv:9`, `docs/13` §7, `docs/17`.

# 8. FIVE CORE SIGNATURES / RULES

**Canonical location (FACT):** `src/signatures.py` (80 lines), `SIGNATURES` dict + `describe(rule)` + `SCOPE_NOTES`. Verified no divergence: lab `src/check_conformance.py::check_case` (165 lines) and field `src/analyze_bpic2019.py::evaluate_case` implement the canonical semantics; duplicate scan found 1 guarded fallback copy (`src/noise_test.py:29-63`, import-first, identical) + harmless mentions. Answer to "where is R4 defined": `src/signatures.py:34-41` (+ implementations check_conformance:52-64, analyze:320-329).

- **R1 (approval-before-PO / maverick proxy):** lab: first Approval < first PO. Field proxy: min(`Vendor creates invoice`) < min(`Create Purchase Order Item`); absent invoice = False; None only if PO ts missing. Applicable: lab all; field 2-way only. Gaps: approval-order ≠ maverick construct. ERP: approval-order testable; maverick needs adaptation.
- **R2 (receipt-before-invoice / after-GR-only):** lab: first GR < first Invoice. Field: first `Record Invoice Receipt` < first `Record Goods Receipt`; both ts required else None. Applicable: lab all; field after-GR only. Gaps: recording-vs-vendor-action; unblocked nuance tracked (0 violations → null). ERP: bill-create/validate vs receipt-Validate, dual timestamps.
- **R3 (qty / value-match proxy):** lab: qty_invoiced ≤ qty_received (tol 0). Field: max invoice worth > PO worth + 0.01; None if either missing. Applicable: lab all; field 3-way both strata. Gaps: qty-vs-value (EUR net worth, cumulative, linearly anonymized); before-GR structural near-zero; only after-GR falsifiable. ERP: qty directly observable → gap closes.
- **R4 (no-unapproved-mod / qty-price-only rework):** lab: every MOD needs later Approval before PO. Field: `Change Quantity`/`Change Price` ts > PO ts; None if PO ts missing. `Change Approval for Purchase Order` EXCLUDED (routine; tracked as `approval_change_after_po`, approval-only = approval∧¬R4). ERP: PO-Modification→Approval→PO directly testable; approval-equivalents must not fire R4 (negative control).
- **R5 (payment-after-invoice / clear-after-record):** lab: first Payment > first Invoice. Field: no Clear → False; Clear without Record → True; else min(Clear) < min(Record), doc-order fallback. Gaps: cash vs clearing-doc; fallback can disagree with ts. ERP: Register Payment vs Bill, monitored only.

---

# 9. BPI CHALLENGE 2019 FIELD DATA

- **Source (FACT):** coatings/paints multinational (Netherlands, 60 subsidiaries), via Boudewijn van Dongen (TU/e), 4TU.ResearchData 2019-01-31, DOI `10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1`. File `BPI_Challenge_2019.xes`, 728,558,522 bytes, MD5 `4eb909242351193a61e1c15b9c3cc814`. 76,349 purchase documents → 251,734 line-item cases → 1,595,596 filtered events (327 dropped outside 2018-01-01–2019-01-27), 42 activities, 627 users (607 human + 20 `batch_*`). IEEE-XES, no namespace on trace/event elements (parser uses local tag names — verified working).
- **Why selected:** same domain (P2P, 3-way matching, GR/invoice/value compliance), same deviation families, compliance-question framing, scale contrast (lab 120 vs field 251k), published findings to reproduce (F1/F2/F3).
- **Transformation:** streaming `iterparse` + `elem.clear()` (constant memory) in `src/analyze_bpic2019.py` (744 lines). Case attrs: concept:name (=PurchasingDocument_Item), Item Category, GR-Based Inv. Verif., Goods Receipt, Vendor, Purchasing Document. Event attrs: concept:name, time:timestamp, User (=org:resource; NONE→system), Cumulative net worth (EUR, cumulative per case).
- **Mapped sample:** `data/bpic2019_mapped_sample.csv` (3,999 lines = 3,998 rows, 211 cases; stratified 150/200/100/50 target, row-cap bound). Older small samples: `data/bpic_sample.csv` (301 lines, LAB_PROXY fallback — NOT real data), `data/bpic_mapping_demo.csv` (201 lines, lab-proxy demo — NOT real data). Do not confuse these with the real run.
- **EXACT columns:** case_id, activity, timestamp, resource, vendor, po_id (100%).
- **LOSSY:** scenario (stratum proxy, no native label); qty_* (worth-proxies; no qty columns in XES). R3 = value-match proxy ALWAYS. R1 = maverick proxy (2-way only). R2 = after-GR only. R4 = qty/price-only (approval excluded). R5 = clear-without-record.
- **Activity names (exact, case-sensitive):** `Create Purchase Order Item`, `Vendor creates invoice` (lowercase — a `Creates` variant once broke R1 to 0; fixed), `Record Goods Receipt`, `Record Invoice Receipt`, `Clear Invoice`, `Record Service Entry Sheet`, `Remove Payment Block`, `Change Quantity`, `Change Price`, `Change Approval for Purchase Order`, `SRM: …` family, `Create Purchase Requisition Item`, etc.
- **Not observable:** quantities, native scenarios, approval order in 2-way sense, cash payment, vendor-action timestamps as system events, tolerance/correction workflows as structured fields.

---

# 10. FIELD-DATA RESULTS (FACT, denominators mandatory)

Full corrected run `data/bpic2019_results.json` (n=251,734). Per-case flags: `data/bpic2019_case_results.csv` (251,735 lines).

| Rule | Overall | 2-way (1,044) | After-GR (15,182) | Before-GR (221,010) | Consignment (14,498) |
|---|---|---|---|---|---|
| R1 maverick | 3450/251734=1.37% | **590/1044=56.5%** | 319/15182=2.10% | 2541/221010=1.15% | 0/14498=0 |
| R2 ordering | **0/11128=0.0%** (applicable) | n/a (0) | 0/11128=0.0% | n/a (0) | n/a (0) |
| R3 value-proxy | 1584/210692=0.75% pooled (DO NOT quote alone) | n/a | **1584/11128=14.2%** | **0/199564=0.0%** | n/a |
| R4 qty/price | **26366/251734=10.47%** | 10/1044=0.96% | 1882/15182=12.4% | 23315/221010=10.5% | 1159/14498=8.0% |
| Approval-change (excluded) | 4290/251734=1.70% | 1000/1044=95.8% | 38/15182=0.25% | 3252/221010=1.47% | 0 |
| — approval-only | 3301/251734=1.31% | (990/1044=94.8% per recount) | — | — | — |
| R5 clear w/o record | 408/251734=0.16% | 0/1044=0 | 9/15182=0.06% | 399/221010=0.18% | 0 |

R2 co-signals: block-given-compliant 0.2056 (2,288/11,128); payment-signal compliant 0.8919 (9,925/11,128); invoice→clear median compliant 26.32d; viol-conditioned quantities null. R3 correction-given-viol after = 249/1584 = 0.1572. Falsifiers: A INCONCLUSIVE (0.0 off-anchor, cost null-null), B REFUTED (14.2% routine + 15.7% correction), C REFUTED-on-rate/NUANCED-on-attribution (10.47% persists; definitional gap unresolved; delay penalty not re-estimated).

---

# 11. IMPORTANT CONTRADICTIONS / SURPRISES

- **CONTRADICTION A — S3 absent:** lab S3 20/20=1.0 (anchor 20/120=0.1667) vs field after-GR 0/11,128=0.0 under every tested definition (timestamp + doc-order; probe 0/40 invoice<GR, 0/39 clear<GR). Billing-block redesign targets a non-problem in this stratum. Mechanism (not rescue): recording gate absorbs 5,754 vendor-early cases → 0 recorded-early. Vendor earliness is OBSERVED; recorded violation is ABSENT — latent vs control-relevant behavior.
- **CONTRADICTION B — tolerance-0 artifact:** after-GR deltas 14.2% routine with 15.7% correction refutes tolerance-0 as enforced norm; before-GR 0 is structural vacuity. Lab over-billing survives only as directional proxy (magnitude gap −0.8577). Never call field R3 "quantity mismatch."
- **CONTRADICTION C — published 1,704 non-reproduction:** exact full-scan (n=251,734): D1 invoice<GR = 16,356 ALL in compliant before-GR (0 after-GR); D2/D4 clear<GR = 89 each, all before-GR; D3 invoice-without-GR = 1,009 (322 before + 687 2-way), 0 after-GR. The 1,704 must use different scope/semantics (variant count, sample, document aggregation, or vendor-action timestamps). Cite it ONLY with timestamp semantics stated. (Note: `/tmp` probe JSONs are ephemeral, not repo artifacts — independent re-scan required for full closure; audit F4.)
- **SURPRISE (positive):** R1 reproduces F1 almost exactly (56.5% vs ~56%) in the matching stratum — the registry's denominator discipline working as designed.

---

# 12. LABORATORY EXPERIMENT

- **Purpose:** checker correctness + config-enforcement causality under known ground truth.
- **Generators:** `src/generate_log.py` (264 lines; R1: 20/scenario S1–S6 = 120 cases/740 events, seed 42, base 2026-01-05 Mon 09:00) and `src/generate_log_r2.py` (214 lines; S3R/S4R/S6R 20 each = 60/400, seed 7, base 2026-02-02). CLI: `--n/--seed/--out/--base` (defaults reproduce canonical files). Stochastic: business-hours clock (Sat/Sun→Mon 08:00), +5h stagger, lognormal waits per leg (PR→Approval 1.0/σ.35; Approval→PO handover 0.5; PO→Receipt 2.0/σ.45; Receipt→Invoice 0.8; Invoice→Pay 1.8; S2 +3.0d; S5 +2.0d; Vendor_B +0.5d, Vendor_C −0.3d; all clipped), resource pools (req_01–03, approver_1/2, buy_01/02, wh_01/02, acc_01/02), weighted qty menu [5,10,15,20,50], S4 over-bill +2/+5, S6 single-qty (R3 clean), S6R qo→qo2 change (R3 clean). Full leg table: `docs/10` §E.
- **Scenarios:** S1 happy baseline; S2 slow receipt (temporal); S3 invoice-before-receipt (R2); S4 over-bill (R3); S5 slow approval (temporal); S6 unapproved PO edit (R4). R2 arms: S3R (bill held to normative order), S4R (bill capped), S6R (MOD→re-approval→PO, 8 events).
- **Conformance:** `src/check_conformance.py::check_case` (165 lines), FROZEN both rounds. Outputs `data/conformance-r*.csv` (per-case variant_short/violations/cycle) + `data/summary-r*.csv` (means, medians, waits, R1–R5 counts).
- **Results (FACT):** R1: V1 80× / V2 20× (S3) / V3 20× (S6); R2:20, R3:20, R4:20, R1/R5:0; S1 FP 0/20. Means: S1 7.18 (appr 1.17, rec 2.76), S2 10.03, S3 7.24, S4 7.70, S5 9.71 (appr 3.26), S6 8.04. R2: 0/60; S3R 8.39, S4R 7.73, S6R 9.19 (median 9.28). Stats (`data/evaluation.csv`, 45 rows): χ²=120 p=6.326e-28; Fisher p=2.07e-35 OR=inf; Wilson [0.9398,1] vs [0,0.0602]; h=3.1416; Welch S1-vs-S2 t=−6.94 df=37.15 p=3.34e-08 d=2.19; vendors 19/40, 21/40, 20/40 (overlapping CIs). Robustness (`data/robustness.csv`): recall ≥0.97 all levels; FPR 0.117@2% (breakdown), 0.233@5%, 0.50@10%. PM4Py (`data/pm4py_results.json`): fitness 1.0 + precision 0.9796 + 3 variants + 6 alignments — vs DISCOVERED net, never normative.
- **Run manager:** `src/run_manager.py` (203 lines): `--n/--era/--tag/--seed[-r1/-r2]` → timestamped `data/runs/<tag>/` + appends `data/runs.csv` (8 backfill rows: r1 seeds 42–45 viol 0.50; r2 seeds 7–10 viol 0.0). try/finally backup/restore of central conformance files (fixed a real clobber bug; md5-verified). Snapshots per-run outputs for provenance.
- **Established result:** S3/S4/S6 20/20 → 0/60 after intervention (abs_reduction=1). Wording licence: "controlled laboratory evidence demonstrates causal efficacy under experimental conditions" — NEVER generalize to real ERP.
- **NOT established:** field accuracy, SAP generality, residual-risk zero, noisy-field effectiveness, S2/S5 SLA validity, cost-free control (S6R overhead: 9.19 vs S1 7.18 = +2.0; vs S6 8.04 = +1.15 — cite both, never bare "+1d").

---

# 13. EXPERIMENTAL DESIGN

Controls: S1 baseline + S2/S5 performance arms (rule-silent) + frozen detector + fixed masters/seeds/schema. Interventions: S3R/S4R/S6R gates. Negative controls: R1/R5 (0 by design both rounds); H6 approval-exclusion (approval-only must not fire R4); S1 0/20 FP. Repeated runs: 8 registry backfills (viol 0.50 r1 / 0.0 r2 across seeds). Seeds: 42/7 canonical (recorded per run). Falsifiers: A/B/C bands + verdict rules in code. Outcomes: viol count/rate/applicable-n, conformance, durations, variants. Circularity avoidance: detector frozen before R2; injection labels independent of detection (scenario ≠ checker input); field proxies defined before rates computed; preregistration precedes ERP execution. Causality basis: fixed-everything-except-redesign on targeted cohort (NOT randomized — stagger only; single-operator/batch limits in `docs/18` T2).

---

# 14. FIELD VS LAB COMPARISON

`src/compare_lab_field.py` (61 lines; lab anchors HARDCODED lines 29–35 — note: rerun if lab numbers change) → `data/comparison.csv` (5 lines): Wilson 95% CI + two-proportion z-test per rule, lab applicable-cohort vs field stratum ONLY (never pooled vs cohort).

| Rule | Lab | Field | Diff | z_p | Reading |
|---|---|---|---|---|---|
| R2 | 20/20=1.0 [0.839,1] | 0/11128=0.0 [0,0.00035] | 1.0 | 0.0 (underflow) | Absent in field; no cost comparison possible |
| R3-after | 20/20=1.0 | 1584/11128=0.1423 [0.136,0.149] | 0.8577 | 9.4e-28 | Direction replicates, magnitude gap |
| R4-3way | 20/20=1.0 | 25197/236192=0.1067 [0.105,0.108] | 0.8933 | 2.8e-38 | Persists; attribution open |
| R1-2way | n/a | 590/1044=0.5651 [0.535,0.595] | n/a | n/a | Reproduces F1 |

CAUTION (FACT): comparison.csv R4-3way denominator (236,192 = 3-way only) differs from `docs/11` corrected overall (26,366/251,734). Cite the `docs/11` figure unless comparing 3-way-only; always state which. Do not overclaim: tiny lab n=20 makes CIs wide ([0.839,1]); z_p≈0 reflects separation, not practical importance.

---

# 15. RESEARCH AUDIT / QUALITY CONTROL

15-agent refinement wave + QA 14/14 + author spot-checks green. Found and fixed: (1) run_manager central-file clobber → try/finally + md5 proof; (2) stale deterministic means in docs/05 → stochastic summary values; (3) S6R cost understatement → dual-baseline numbers; (4) approval_only_2way off-by-10 → 0.94827586 by recount (990/1044); (5) falsifier-C split → harmonized (refuted-on-rate, nuanced-on-attribution); (6) fitness scope → "vs discovered model" everywhere; (7) 9926→9925 typo; (8) README bare rates → denominatored. Audit record: `docs/16` (14 established / 9 proxy / 11 open / 11 G-issues, recommendations only — G1–G6 language in `docs/00` was FLAGGED but deliberately NOT rewritten in place; the handoff respects that: `docs/00` still contains unqualified "eliminate"/"+1 day" phrasing — see §28). Field rerun reproduces bitwise-identically (md5-verified); zeros classified genuine-zero (detector proven live: same code fires 1,584× in after-GR for R3; R2 denominator healthy, 4,054 None only).

---

# 16. ERP / ODOO PHASE — NOT EXECUTED

**FACT: no Odoo has been executed under this project. No live export exists. `data/event-log-*.csv` are synthetic stand-ins. `docker compose up` was never run here (Docker daemon unavailable in build env).** Everything Odoo is protocol + tooling.

- **Why Odoo Community 17:** open-source, inspectable, real control points (bill control on received quantities, PO lock + re-approval, SLA timers), finishable single-company scope.
- **Intended workflow (6 steps, `docs/04` §3 + `docs/17` §2):** Purchase Request → Approval (2-step) → PO confirm → Goods Receipt Validate → Vendor Bill Validate (Bill control) → Register Payment. Masters: 3 vendors, 5 products (P-01..P-05), fixed roles. Stratum: 3-way-after-GR only.
- **Injection → signature → detection → intervention → rerun → outcome → falsifier:** per-hypothesis in `docs/17` §4; dual timestamps (recorded verdict vs occurred covariate); control (S1–S6, N=120) vs intervention (S3R/S4R/S6R, N=60); H8 verdict rule (transferred / mechanism-confined / not transferred).
- **Purpose:** test transferability/H8 — the ONLY thing that can close it.

---

# 17. ERP EXPERIMENT PROTOCOL (summary; authority = `docs/17`, 241 lines)

Selected: H1-adapted (approval-order probe; maverick not replicable), H2 recording-gate priority (dual-ts 2×2, expect block; FLAG if field-absent), H3 tol-0 as lab norm (cite field 14.2% + 0.157 correction; no prescription), H5 rework vs H6 exclusion check (probe-equivalent tallies), H7 monitored (<0.01). Excluded: H4 (structural zero), H8 frame (stays open). Event-log contract: 18-column schema (`docs/17` §5.1) incl. `timestamp` (recorded, verdict) + `timestamp_occurred` (covariate) + `timestamp_kind` + receipt/invoice IDs + `condition` + `doc_order_seq`; column-for-column rejection; §5.2 timestamp semantics (recorded-vs-recorded verdicts; None-rate reporting; citation rule: every "early invoice" sentence states which timestamp). Metrics: viol/applicable + overall anchor + None-rate + durations (median+IQR, both S6R baselines) + variants + conformance + field deltas. Stopping (integrity: schema mismatch, >10% missing ts, S1 FP>0, mid-batch edits, manual-entry in verdict columns) and FLAGs (S3-absent, tolerance-calibration, approval-conflation). Threats §7; preregistration record §8 with EMPTY results table by design (fill date, detector commit, Odoo image hash BEFORE first step). Mapping: `data/hypothesis_erp_mapping.csv` (9 lines: hypothesis, field/lab evidence, testability, adaptation, signature, control, intervention, metric, falsifier, status).

---

# 18. H8 (OPEN)

**Definition:** do lab-demonstrated hard controls transfer to an executable ERP P2P process (recording stage)? Lab: 60/60→0/60. Field: UNTESTED, no intervention observed. **Stays open until:** (a) Odoo S3R/S4R/S6R reruns recorded, (b) field-base comparison with FLAGs recorded, (c) verdict via preregistered rule. Support = elimination under identical conditions + zero S1 FP + no anomalies (Odoo-recording-stage only, never SAP generality). Failure/refutation = violation persists, exclusion fails, or tolerance sweep shows tol-0 blocks >5% compliant bills. Mechanism-confined = eliminates recorded pattern while occurred mass persists (the S3-gate outcome). ERP must demonstrate; lab + field are insufficient by construction.

---

# 19. VALIDITY / THREATS (authority: `docs/18`, 10 Q&As + 6 families/14 items)

Construct (T1): signature–concept gaps per rule; R4-approval conflation + worth substitution (quoting either as the stronger construct forbidden). Internal (T2): no randomization (stagger only); single-operator/batch rounds; before/after, not RCT. External (T3): Odoo single-config; synthetic single-team; one field company. Data (T4): lossy scenario; no qty columns (epsilon 0.01 load-bearing, probe-checked). Measurement (T5): latent-vs-recorded censoring; None-rates (R2 26.7%, R3-before 9.7%) are not conformance. Reproducibility (T6): seed/version dependence; registry dependence; provenance (MD5; `/tmp` probes carry zero weight). Mitigations implemented: frozen detector, applicable-n discipline, stratum scoping, exclusion enforcement, completeness-conditional claims, preregistration. See also `docs/09` (lab-focused threats) and `docs/16` §F/G.

---

# 20. REPRODUCIBILITY (authority: `docs/19`; key excerpts verified)

Env: Python 3.9.6; requirements (pandas/numpy/scipy/matplotlib; pm4py≥2.7 installed). Commands: `make data && make check && make eval` (lab 1–5); `make bpic` (= analyze ~1 min + compare; rewrites ~23 MB — rerun only on change); `make hypo` (read-only registry check); `make web` (serve hint); `bash run_demo.sh` (lab demo); `python3 -m http.server 8000 --directory webpage`. Deterministic: seeds 42/7; frozen checker; run registry with UTC tags + per-era seeds. Outputs map in `docs/19` §5 (every data/ file + generator + bytes). Limits: full analyzer skipped routinely; webpage data.json rebuild manual; live-Odoo path documented-only. MD5s (small files): hypotheses.csv c2697b1f…, comparison.csv 1d4dee…, evaluation.csv d387e7f8….

# 21. CODE ARCHITECTURE (all files inspected)

- `src/analyze_bpic2019.py` (744 lines): streaming XES analyzer (iterparse + clear). CLI `[xes_path] [--cases-out] [--json-out]`. Analytical. Outputs case_results.csv + results.json + falsifier verdicts. Fragile points: activity-name casing (fixed once); Item-Category substring matching; docstring line 18 still shows capitalized 'Vendor Creates Invoice' (STALE vs fixed constant — cosmetic); line-4 namespaced-trace comment vs local_tag impl (works — cosmetic). ~1 min runtime.
- `src/check_conformance.py` (165 lines): frozen R1–R5 lab checker. CLI `file.csv` → conformance + summary CSVs + stdout (tag from filename: r1/r2/stem). Writes CENTRALLY (hence run_manager backup/restore). Analytical/canonical-lab.
- `src/compare_lab_field.py` (61 lines): Wilson + z-test from HARDCODED lab anchors (lines 29–35) + field JSON → comparison.csv. Analytical. WARNING: rerun after any lab-number change.
- `src/evaluate.py` (238 lines): lab stats (chi2/Fisher/Wilson/h + dynamic Welch t + vendor strata) → evaluation.csv. Derives cycles dynamically; cross-checks summaries. Analytical.
- `src/fetch_bpic_sample.py` (379 lines): tries <5MB public mirrors (60s timeout), falls back to LAB_PROXY 300-row remap → bpic_sample.csv. Utility. Current output is LAB_PROXY (never pulled real 728MB by design).
- `src/generate_log.py` (264) / `generate_log_r2.py` (214): stochastic generators, `--n/--seed/--out/--base`, full spec in docstrings + `docs/10` §E. Experimental. Defaults reproduce canonical files exactly.
- `src/mining_pm4py.py` (61): inductive miner + token fitness/precision + 6 alignments → pm4py_results.json. Requires pm4py. Diagnostic only.
- `src/noise_test.py` (190): drop-noise sweep 0/2/5/10% × seeds 1–3, imports check_case with EXACT fallback copy (guarded; no divergence per scan). In-memory only; writes robustness.csv. Analytical.
- `src/run_manager.py` (203): run orchestration + registry. try/finally central-file protection (fixed real bug). Infrastructure. DANGER (residual): tag collision overwrites same dir (no guard); random seeds when flags omitted (non-reproducible unless recorded — they are recorded in CSV).
- `src/signatures.py` (80): CANONICAL definitions + describe() + SCOPE_NOTES. Reference only; nothing imports it (standalone by design).

---

# 22. DATA ARCHITECTURE

Canonical (versioned, never regenerated blindly): `BPI_Challenge_2019.xes` (re-download only; NOT in git), `hypotheses.csv`, `hypothesis_erp_mapping.csv`, `signatures.py` (code), event logs (seeded regen OK). Derived (regenerable): everything else. Raw: XES only. Transformed: case_results.csv (23 MB), mapped_sample (3,998 rows), bpic_sample (LAB_PROXY), mapping_demo (lab-proxy demo). Event logs: r1 120/740, r2 60/400, template. Conformance: per-case + summaries. Stats: evaluation (45 rows), robustness (12), pm4py JSON, comparison (4). Registry: runs.csv (8 rows) + runs/ (8 dirs × 3 files). No-duplicate XES policy (`docs/14`): one copy, stream in place, samples ≤4,000 rows, runs/ ≤10 entries/≤1 MB. 728 MB XES excluded via `.gitignore:13` (git objects would bloat; reproducibly re-downloadable via DOI).

---

# 23. GIT / VERSION CONTROL STATE (FACT, verified)

- Initialized locally; branch `main`; NO remote (`git remote -v` empty).
- Exactly ONE commit: `5e48381` "checkpoint: freeze research foundation before ERP phase".
- 90 tracked files (`git ls-files | wc -l`). Working tree CLEAN (`git status --short` empty).
- `.gitignore`: macOS, Python (incl. venv/pytest/ruff caches — note: no pytest/ruff configs exist in repo), XES (`data/BPI_Challenge_2019.xes`), local ERP artifacts (`data/erp/`, `data/odoo/`, `*.sqlite`, `*.db`), `*.tmp/*.bak`.
- This checkpoint = frozen research foundation. ERP work belongs in NEW commits. This handoff file itself is UNTRACKED until the user commits it (do NOT commit unless asked).

---

# 24. WEBPAGE / DEMO

Purpose: research-story showcase (RQ → field → lab → contradictions → H8-open → ERP-next), NOT a production app. Files: `index.html` (298 lines; 11 numbered sections incl. Hypotheses table + next-exp H8-open note; footer reproduce block), `app.js` (796 lines; Chart.js doughnut/bar/line, roundToggle, filters, guarded missing keys), `hypotheses.js` (219 lines; hypoTable from data.json, status badges open→warn never ok), `styles.css` (922 lines; navy/gold academic theme), `data.json` (692 lines; keys meta/r1/r2/stats/pm4py/robustness/log_sample/runs/bpic/hypotheses/erp_next), figures (lab-vs-real comparison, cycle boxplot, variant bars, waiting heatmap). Serve: `python3 -m http.server 8000 --directory webpage` (all assets 200-verified). Validation: node --check ×2, json.tool. DISCREPANCIES (do not silently fix; flagged): footer references nonexistent `src/make_figures.py`; footer claims "Python 3.10+" vs env 3.9.6; hypoTable static fallback "No hypotheses available" renders only if data.json key missing (present now).

---

# 25. TESTING / VALIDATION STATUS (only what ran)

No pytest/ruff/test framework in repo (configs absent despite .gitignore entries). Validation = scripts + checks, all executed with recorded outcomes: field full-run + bitwise-identical rerun (md5 match); mini-XES 40/40 cell checks; probe quotas (250,750 scanned; 40-case + full-scan 1704 probes); `make -n` dry runs (bpic/hypo/data); `node --check` (app.js, hypotheses.js); `python3 -m json.tool` (data.json); `py_compile` (signatures/mining/evaluate/noise); BPMN XML parse; XES MD5 + tail; webpage HTTP 200s; run_manager probe (121 lines + registry restore); QA sweeps (14/14 twice; one QA FAIL was the QA agent's own file mix-up, re-verified correct). Do not invent further tests.

---

# 26. DISK / LARGE FILES

XES 728,558,522 bytes (695 MiB) excluded from git; single copy enforced. Disk at handoff brief: ~96% / ~8.7 GiB free (audit-time `df` showed 68%/5.7 GiB — treat as scarce either way; VERIFY with `df -h` before large operations). Rules: never copy/convert XES wholesale; stream in place; samples ≤4,000 rows; runs/ ≤10/≤1 MB (currently 8 dirs, 476K); no `/tmp`→repo copies; check `find . -size +50M` before adding >10 MB files.

---

# 27. THINGS THAT MUST NOT BE CHANGED CASUALLY (invariants)

1. Denominators: every rate keeps n_true/n_applicable + population; never quote pooled R3 alone.
2. Exclusions: Change Approval stays out of R4; before-GR stays out of R2 scope; H4 stays out of ERP arms.
3. Proxies stay proxies: value≠quantity; maverick≠approval-order; recording≠physical; clear≠cash. (G9-class edits forbidden.)
4. No lab→field generalization sentences without H8-open qualifier (G1/G4/G6 class).
5. H8 stays open until ERP rerun + field-base comparison recorded.
6. No post-hoc hypothesis edits without documenting change (registry is preregistration).
7. Never overwrite canonical result files without backup + verification (run_manager pattern).
8. Never duplicate the XES; never commit it.
9. Never weaken tests/checks to make QA green; fix the project, not the check.
10. Approval-workflow ≠ rework (50× inflation trap); structural zeros ≠ intervention evidence.
11. Discovered model ≠ normative BPMN (fitness-1.0 misreading forbidden).
12. `src/signatures.py` stays canonical; docs reference, never re-implement.
13. `docs/00` G-flagged language stays as-is unless the user explicitly authorizes a claims revision (audit recommended corrections only).
14. Falsifier bands/thresholds in code stay fixed unless preregistered change with rationale.

---

# 28. KNOWN LIMITATIONS (brutally honest)

Data: no qty/native-scenario/cash-payment/approval-order-in-2-way-sense in XES; 327 events date-dropped; epsilon 0.01 practitioner-unvalidated. Measurement: checker FPR>10% at ≥2% missing events; doc-order fallback; None-rates undisclosed = uninterpretable; latent censoring by recording gate. Construct: five documented signature–concept gaps; R4-vs-F2 definitional non-identity; delay-penalty side never re-estimated. Field: one company, policy-encoded strata, maverick concentrated in tiny 2-way (n=1,044). Lab: synthetic single-team, no randomization, single-batch rounds, period-confounded R2, seeds/version-locked comparison. ERP: nothing executed; row-for-row swap untested; tolerance/SLA/partial/credit-note arms excluded by design. Generalizability: no SAP, no adversarial/noisy-field, no residual-risk-zero, no cost-benefit. Tooling: PM4Py diagnostic-only; no test framework; footer dead command (`make_figures.py`); footer Python-version mismatch; analyzer docstring casing staleness; README "docs/15 reserved" staleness; numbering gaps (no docs/08, docs/12); comparison.csv R4 denominator differs from docs/11 (state which); S6R overhead dual-baseline ambiguity; `/tmp` probes ephemeral (1704 closure needs independent re-scan).

---

# 29. CURRENT STATUS TABLE

| Area | Status | Evidence | Next |
|---|---|---|---|
| RQ | FIXED | README:11, docs/15 Ch1 | Unchanged |
| Normative model | FROZEN | docs/01, bpmn/×2, docs/10 §A | Unchanged |
| Hypotheses H1–H8 | PREREGISTERED 5/2/1 | hypotheses.csv, QA | H8 via ERP |
| Field data | ANALYZED (full corrected run) | bpic2019_results.json n=251734 | Re-scan only on code change |
| Field analysis | REPRODUCIBLE (bitwise) | md5 match rerun | Rerun via make bpic if needed |
| Lab experiment | DONE, causal-under-control | logs/checker/stats | New runs via run_manager |
| Causal evidence | LAB-ONLY (60/60→0/60) | evaluation.csv | ERP replication |
| Contradictions | DOCUMENTED (A/B/C, 1704) | docs/11,13,16 | Constrain ERP claims |
| Validity | BOUNDED (18 + 09 + 16) | 10 Q&A, 6 families | Extend post-ERP |
| Reproducibility | GATED (19) | commands verified | Keep green |
| Git checkpoint | 5e48381, clean, main, no remote | git log/status | New commits for ERP |
| Odoo setup | DOCUMENTED ONLY (never ran) | docs/03, compose file | `docker compose up -d` |
| Odoo experiment | PREREGISTERED, EMPTY results | docs/17 §8 | Execute §1–§8 |
| H8 | OPEN | hypotheses.csv:9 | ERP verdict |
| Thesis | OUTLINED (Ch1–Ch8, ~20k) | docs/15 | Write post-ERP |
| Webpage | LIVE-READY (200s) | §24 | Add ERP results panel later |

---

# 30. WHAT REMAINS TO BE DONE

- **DONE:** RQ, normative model+BPMN, H1–H8 registry, signatures, lab R1/R2 + checker + stats + robustness + PM4Py diagnostics, full BPI analysis + probes, cross-validation + falsifiers, audit wave + fixes, stewardship, reproducibility gate, defense/validity, thesis outline, webpage, git freeze.
- **IN PROGRESS:** nothing (foundation frozen; this handoff is the only new artifact).
- **NEXT (in order, from `docs/17`):** (1) preserve freeze (new branch/commits only); (2) fill preregistration record (date, detector commit, Odoo image hash); (3) finalize §5.1 contract against live Odoo fields; (4) `docker compose up`, create `p2p-exp`, install Purchase/Inventory/Invoicing; (5) fixed masters; (6) control arms S1–S6; (7) injections per §4; (8) extract via sql script; (9) detect with frozen checker; (10) verify observed-vs-latent; (11) field-base comparison + FLAGs; (12) interventions S3R/S4R/S6R; (13) rerun; (14) H8 verdict; (15) update docs/15 + webpage; (16) re-run gates; (17) commit ERP checkpoint.
- **OPTIONAL:** tolerance-sweep arm; SLA/delay-threshold arm; partial-receipt/credit-note extensions; PM4Py alignment-cost study; vendor-action timestamp capture if Odoo exposes it.
- **NOT YET VALIDATED:** live row-for-row swap; S6R overhead single figure; R4-vs-F2 excess attribution; 1704 independent re-scan; any ERP number.
- **OPEN RESEARCH QUESTIONS:** H8 verdict; calibrated tolerance level; recording-gate generality beyond one company; delay-penalty re-estimation; SLA preservation under hard gates.

# 31. RECOMMENDED NEXT STEPS (derived from `docs/17` §8 + §30 NEXT)

1. `git status` clean-check; create branch `erp-experiment` (never work on frozen main directly).
2. Review `docs/17` fully; fill preregistration record (date, `check_conformance.py` commit = 5e48381 state, Odoo image hash).
3. Finalize §5.1 contract: map each column to live Odoo fields (PO name, picking name, bill name, validate timestamps, `create_uid` logins).
4. `docker compose up -d` → http://localhost:8069 → DB `p2p-exp` → install Purchase/Inventory/Invoicing.
5. Fixed masters (3 vendors, P-01..P-05, roles, 2-step approval); hash/record them.
6. Control arms S1–S6 (20 each, +5h stagger, business-hours discipline as applicable).
7. Injections per §4 (H1 probe, S3 dual-ts, S4 +2/+5, S6 edit-without-reapproval).
8. Extract via `sql/odoo_extract.sql` → column-for-column validation (reject mismatches).
9. Detect with frozen checker (record version; no tuning).
10. Verify each hit (observed vs latent; H6 exclusion tallies).
11. Field-base comparison + FLAG sheet (S3-absent? tolerance mass? approval conflation?).
12. Interventions S3R/S4R/S6R (bill control, qty cap, re-approval gate).
13. Rerun identical conditions; record pre/post + absolute reduction.
14. H8 verdict (transferred / mechanism-confined / not transferred) with denominators + both S6R baselines.
15. Update `docs/15` Ch7 (results now exist), webpage ERP panel, `data/runs.csv`-style ERP run record.
16. Re-run all gates (`make bpic` only if analyzer changed; lab gates; node/json checks).
17. Commit ERP checkpoint (never the XES; never `data/erp/` or `data/odoo/` per .gitignore).

---

# 32. HOW A NEW AGENT SHOULD WORK ON THIS PROJECT

1. Inspect before editing (read the file + its consumers first).
2. Read method docs (`docs/04` §6, `docs/16` E–G, `docs/17` gate) before touching methodology.
3. `src/signatures.py` = canonical definitions; `data/hypotheses.csv` = canonical metadata; `docs/17` = baseline plan.
4. Never retrofit hypotheses to results without documenting the change as a protocol deviation.
5. Never invent evidence, numbers, or file contents — read them.
6. Label every claim FACT / INTERPRETATION / HYPOTHESIS / PLANNED / OPEN.
7. Preserve denominators, provenance, seeds, MD5s, exact IDs/filenames/commands.
8. Prefer additive changes (new files/sections) over rewrites of frozen docs.
9. Run relevant checks after changes (py_compile, json.tool, node --check, targeted script runs); never rewrite canonical outputs by hand.
10. `git diff` before any commit; never commit XES/`data/erp/`/`data/odoo/`/`.tmp`/`.bak`; never force-push (no remote exists — do not create one unasked).
11. Keep claims scoped: cohort + denominator + condition on every efficacy sentence.
12. If uncertain, inspect the repo instead of guessing; if unresolvable, document as OPEN (§28-style honesty).

---

# 33. COMMAND CHEAT SHEET (all exist in repo; cwd = repo root)

```bash
cd "/Users/atishmondi/Documents/Default Project/p2p-conformance-experiment"
git status && git log --oneline && git branch --show-current
make -n data && make -n check && make -n eval && make -n bpic && make -n hypo
python3 src/generate_log.py            # seed 42 → event-log-r1.csv (120/740)
python3 src/check_conformance.py data/event-log-r1.csv
python3 src/generate_log_r2.py         # seed 7 → event-log-r2.csv (60/400)
python3 src/check_conformance.py data/event-log-r2.csv
python3 src/evaluate.py                # → evaluation.csv
python3 src/noise_test.py              # → robustness.csv
python3 src/mining_pm4py.py            # needs pm4py → pm4py_results.json
python3 src/run_manager.py --n 20 --era both   # timestamped runs/ + runs.csv
make hypo                              # read-only registry check
python3 src/signatures.py              # prints canonical R1–R5
python3 -m http.server 8000 --directory webpage
node --check webpage/app.js && node --check webpage/hypotheses.js
python3 -m json.tool webpage/data.json > /dev/null && echo JSON_OK
ls -l data/BPI_Challenge_2019.xes && md5 data/BPI_Challenge_2019.xes  # 728558522 / 4eb90924…
python3 src/analyze_bpic2019.py        # ~1 min, rewrites ~23 MB — only on change
python3 src/fetch_bpic_sample.py       # small mirrors only, else LAB_PROXY
docker compose up -d                   # Odoo stack (PLANNED use; never run here)
psql -h localhost -U odoo p2p-exp -f sql/odoo_extract.sql -o data/event-log-odoo.csv --csv  # PLANNED
```

---

# 34. FILE MAP

```
p2p-conformance-experiment/            # repo root; main branch; commit 5e48381
├── PROJECT_HANDOFF.md                 # THIS file (untracked until committed)
├── README.md                          # 2–3-min story + status + reproduce + layout
├── Makefile                           # data/check/eval/bpic/hypo/web/all
├── requirements.txt                   # pandas numpy scipy matplotlib pm4py>=2.7
├── run_demo.sh                        # lab demo (generate→check→evaluate)
├── docker-compose.yml                 # postgres:15 + odoo:17.0, DB p2p-exp :8069
├── .gitignore                         # XES, data/erp/, data/odoo/, *.sqlite/.db/.tmp/.bak
├── sql/odoo_extract.sql               # line-grain extractor → event-log-odoo.csv (UNEXECUTED)
├── src/                               # 11 files (§21): analyzer, checker, compare,
│                                      # evaluate, fetch-sample, 2 generators, mining,
│                                      # noise, run_manager, signatures (canonical)
├── docs/                              # 00 abstract … 19 reproducibility (no 08/12);
│                                      # 16 audit, 17 ERP protocol, 18 defense, 19 gate
├── docs/bpmn/                         # normative.bpmn + v2.bpmn (valid XML)
├── data/                              # XES (size-excluded) + 20 CSV/JSON;
│                                      # runs/ 8 backfill dirs; runs.csv 8 rows
└── webpage/                           # index/app/hypotheses + styles + data.json + figures/
```

Key per-file roles: see §21 (code), §22 (data), and `docs/19` §5 (output map with byte sizes).

---

# 35. GLOSSARY

- **P2P:** purchase-to-pay (request→approval→order→receipt→invoice→payment).
- **ERP:** enterprise resource planning system; here Odoo Community 17 (experimental env).
- **Process mining:** discovery/conformance/performance analysis from event logs.
- **Conformance checking:** normative-model vs log comparison (here: frozen R1–R5 rules; PM4Py alignments are diagnostic only).
- **Normative model:** intended process (docs/01, bpmn) — NOT ground truth of reality.
- **Discovered model:** PM4Py inductive net mined from the log — fitness 1.0 is tautological vs it.
- **Event log:** case_id/activity/timestamp (/resource/attrs) rows; lab 740+400; field 1.6M.
- **Variant:** distinct activity order (V1 80×, V2 20× S3, V3 20× S6; R2 S6R 8-event chain).
- **Deviation:** rule violation (behavioral) or delay (temporal, rule-silent).
- **Signature:** executable event pattern per rule (`src/signatures.py`).
- **R1–R5:** approval-order; receipt-before-invoice; qty/value-match tol-0; no-unapproved-mod; payment-after-invoice.
- **H1–H8:** pre-registered hypotheses (5 supported / 2 nuanced / 1 open).
- **BPI 2019:** real P2P log (251,734 line-item cases; strata 2-way/3-way/consignment).
- **Odoo:** open-source ERP; Community 17 single-company scope here.
- **PM4Py:** process-mining library; tool, not contribution.
- **Maverick buying:** vendor acts before PO (field proxy for R1, 2-way only).
- **Recording gate:** system-recording control absorbing vendor-earliness (5,754→0).
- **2-way/3-way matching:** invoice↔PO (2-way) vs invoice↔GR↔PO (3-way; after-GR = GR-based verification).
- **Goods receipt / vendor invoice:** GR Validate / Bill Validate events (recorded timestamps).
- **Falsifier:** pre-registered refutation condition (A: R2 band; B: tolerance-0; C: F2 base).
- **Construct/internal/external validity:** signature-vs-concept / causality-within-design / generalizability limits.
- **Transferability (H8):** lab-demonstrated controls working in executable ERP; OPEN.

---

# 36. THESIS POSITIONING (per repo, not generic advice)

Contribution (per `docs/00` + audit qualifications): executable normative semantics (R1–R5); controlled stochastic lab separating delay from failure; triangulated quantification (60/60→0/60 + full stats + robustness + PM4Py diagnostics); control-design distinction (hard gates vs soft SLAs) CONSTRAINED by field contradictions. Methodology: hypotheses-first + signatures + frozen detector + seeds + registry + falsifiers. Empirical: BPI 2019 full-stream field study with denominator discipline. Experimental: lab R1→R2 causal-under-control + preregistered ERP protocol. ERP component: Odoo as recording-stage transfer testbed (planned). Process-mining component: discovery/variants/performance triangulation (tool role). Limitations: §28 (synthetic, proxies, single settings, untested transfer). IS/Wirtschaftsinformatik fit: ERP configuration → execution → event data → mining → redesign → re-execution closed loop with falsification. Novel/useful (repo-grounded): recording-gate mechanism (latent vs recorded), R4-approval exclusion discipline, tolerance-0 refutation with numbers, preregistered transfer protocol. Do NOT claim: SAP generality, field-validated controls, residual-risk-zero, PM4Py-based conformance, quantity semantics in field R3, 1704 reproduction.

---

# 37. DEFENSE QUESTIONS (evidence-anchored; full set in `docs/18`)

- **Why BPI 2019?** Same-domain P2P with 3-way matching + compliance framing + published F1/F2/F3 to reproduce; scale contrast. Limit: one company, policy-encoded strata.
- **Why Odoo?** Inspectable real control points + finishable scope; synthetic stand-in disclosed, live path documented-not-executed.
- **Why PM4Py?** Discovery/variant/diagnostic triangulation only; normative verdict is the frozen checker (fitness 1.0 meaningless without "vs discovered net").
- **Why synthetic lab?** Known ground truth separates checker correctness from field accuracy; 60/60 + 0/20 S1 FP measures the detector.
- **Why not only real data?** No intervention → no causal or transfer evidence; H8 untestable.
- **Why not only Odoo?** Without field base rates, lab effects lack relevance check (S3 lesson).
- **What exactly is causal?** Targeted-cohort 60/60→0/60 under frozen detector + fixed seeds/masters (before/after, not RCT).
- **What is H8 / why open?** Lab→ERP transfer; no ERP intervention measured; verdict rule preregistered.
- **Why do field rates differ from lab?** Design: lab cohorts are deterministic 1.0 by injection; field strata are observational (R3 0.142, R4 0.105) — magnitude gaps expected, direction is the test.
- **Why is R3 only a proxy?** No qty columns in XES; worth-delta proxy with epsilon 0.01, probe-validated.
- **Why is R2 zero?** Recording gate: vendor-early mass (5,754) absorbed before recording (0/11,128); before-GR D1 (16,356) is compliant-by-design.
- **Why exclude Change Approval from R4?** Routine workflow: 95.8% in 2-way vs 0.96% rework; naive inclusion inflates ~50×.
- **Why structural zeros?** Before-GR R3 has no GR reference at invoice time — vacuity, not enforcement.
- **What does recording-gate mean?** Controls act at system-recording timestamps; vendor-action earliness never becomes a recorded violation there.
- **Why isn't normative BPMN ground truth?** It's the intended model under test, not reality; discovered model describes behavior.
- **Biggest validity threats?** Synthetic-validity, proxy gaps, single settings, untested transfer (`docs/18` T1–T6).
- **What would falsify the argument?** Falsifiers A/B/C bands; ERP verdict "not transferred"; tolerance sweep showing tol-0 blocks >5% compliant bills.
- **If Odoo doesn't reproduce the lab effect?** Then H8 → not-transferred/mechanism-confined per preregistered rule — still a result; update `docs/15` Ch7 with numbers, never retrofit hypotheses silently.

---

# 38. FINAL STATE-OF-PROJECT SUMMARY (read this first)

- **PROJECT:** Hypotheses-first P2P conformance study (Odoo + BPI 2019 + controlled lab), `p2p-conformance-experiment`.
- **CURRENT PHASE:** Research foundation frozen (git 5e48381, clean, main, no remote); ERP preregistered, unexecuted.
- **RESEARCH QUESTION:** How do P2P deviations emerge in ERP execution, and what design/configuration changes reduce them (lab-demonstrated; field-constrained; transfer-open)?
- **CORE FINDING SO FAR:** Frozen checker catches 60/60 injected deviations (0/20 S1 FP); redesign drives 60/60→0/60 under lab control (χ²=120, Fisher p=2.1e-35, h=3.14); S6R costs +2.0d vs S1.
- **FIELD EVIDENCE:** n=251,734: maverick 56.5% (2-way, reproduces F1); R2 0/11,128 after-GR; R3 value-proxy 14.2% after vs 0 before; R4 10.5% qty/price-only (approval excluded); R5 0.16%.
- **LAB EVIDENCE:** seeds 42/7; variants 80/20/20; throughput split (Welch p=3.3e-08); robustness breakdown at 2% noise; PM4Py diagnostics (discovery scope).
- **MAJOR CONTRADICTIONS:** S3 absent in field (recording gate 5,754→0); tolerance-0 refuted; published-1704 unreproduced as defined; R4 needs approval-exclusion.
- **HYPOTHESIS STATUS:** H1/H3/H4/H6/H7 supported; H2/H5 nuanced; H8 open.
- **H8:** Lab→ERP transfer UNTESTED; preregistered protocol + verdict rule exist; no Odoo executed.
- **ERP STATUS:** `docs/17` complete (scope, arms, contract, metrics, FLAGs, threats, empty results table); Docker/SQL tooling ready but never run here.
- **CURRENT GIT CHECKPOINT:** 5e48381 "checkpoint: freeze research foundation before ERP phase"; 90 files; clean tree; XES git-ignored.
- **NEXT TASK:** Branch `erp-experiment`; fill preregistration record; execute `docs/17` §1–§8 in gate order; verdict H8.
- **CRITICAL WARNINGS:** (1) Never quote rates without denominators. (2) Never upgrade proxies (value→quantity etc.). (3) Never generalize lab→field/ERP without H8 qualifier. (4) H8 stays open until measured. (5) One XES copy; never commit it. (6) Central result files: backup before regeneration. (7) `docs/00` still carries G-flagged unqualified language — quote it only with `docs/16` corrections. (8) Footer dead command + Python-version mismatch are known cosmetic discrepancies. (9) `/tmp` probes are not evidence. (10) Comparison.csv R4 row uses 3-way-only denominator — state which R4 figure you cite.



