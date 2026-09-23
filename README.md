# From Intended Process to Executed Process: Conformance Analysis of P2P in an ERP-Based Controlled Experiment

## The story in 2–3 minutes
**RQ:** how do deviations between the normative P2P process and its ERP execution emerge, and what design/configuration changes reduce them? **Field grounding:** BPI Challenge 2019, n=251,734 cases (FULL corrected run), gives real-world base rates with applicable denominators — R1 maverick 590/1,044=56.5% (2-way); R2 0/11,128=0.0% (3-way after-GR); R3 value-proxy 1,584/11,128=14.2% after vs 0/199,564 structural zero before; R4 qty/price-only 26,366/251,734=10.5% (approval-change 4,290/251,734 excluded); R5 408/251,734=0.16%. **Lab causal control:** Odoo-protocol synthetic stand-in (seeds 42/7, 120+60 cases) with frozen R1–R5 checker isolates delay (S2/S5, performance-only) from failure (S3/S4/S6) and drives targeted-cohort violations 60/60=1.0 → 0/60=0.0 under lab conditions (overall anchor 60/120=0.50; S1 0/20 FP). **Contradictions:** S3-absent in field (lab S3 20/20=1.0 vs field after-GR 0/11,128 — recording gate absorbs vendor-early mass) and R3 value-match proxy artifact (tolerance-0 refuted as enforced norm; H3 holds only as directional proxy, H2/H5 nuanced). Registry: 5 supported / 2 nuanced / 1 open. **H8-open:** lab elimination licences only a pilot hypothesis — field transfer is UNTESTED. Next step is preregistered, not claimed: ERP transfer protocol `docs/17-erp-experiment-protocol.md` + `data/hypothesis_erp_mapping.csv` (Odoo Community 17, 3-way-after-GR recording stage; no Odoo executed, no results).

Controlled experimental study using open-source ERP (Odoo Community protocol). Odoo-protocol synthetic stand-in — no live Odoo export used; swap in real export row-for-row. External check: BPI Challenge 2019 P2P log, see `docs/07-real-dataset.md`.

Pipeline: Normative BPMN → Odoo configuration → controlled execution → event log → process mining → deviations → redesign → re-execution.

## Research question
How do deviations between the normative purchase-to-pay process and its execution in an ERP system emerge, and what process-design or ERP-configuration changes can reduce these deviations?

Subquestions: variants? temporal vs behavioral? design vs config cause? does redesign reduce deviations? See `docs/01-normative-model.md`.

## Combined backbone: lab causal-control + field grounding
Combined-backbone: lab provides causal-control (stochastic S1-S6 masters, R1-R5 rules, redesign S3R/S4R/S6R driving violations 60/60=1.0 applicable (overall 60/120=0.50) → 0/60=0.0) and field provides grounding (BPI Challenge 2019, n=251,734). Pre-registered H1-H8 registry (`data/hypotheses.csv`, signatures in `src/signatures.py`) yields 5 supported / 2 nuanced / 1 open (H1,H3,H4,H6,H7 supported; H2,H5 nuanced; H8 open). Key contradictions: S3-absent in field (lab S3 20/20=1.0 vs field after-GR R2 0/11128=0.0, S3 absent at recording gate) and R3 value-match proxy artifact (tolerance-0 refuted: after-GR 1584/11128=0.1423 routine vs before-GR 0/199564 structural zero, R3 value-match proxy artifact as enforced norm).

## Status: closed loop DONE — stochastic masters build (seeds 42/7; business hours + lognormal waits + vendor effects + resource pools)
- [x] Normative model R1-R5 + S1-S6 (`docs/01,02`, `docs/bpmn/normative.bpmn`)
- [x] Odoo execution protocol + multiline SQL extract (`docs/04`, `sql/odoo_extract.sql` line-grain + currency + single-company)
- [x] Round 1: 120 cases / 740 events stochastic (`data/event-log-r1.csv`, `src/generate_log.py`)
- [x] Mining: rules + PM4Py + performance (`src/check_conformance.py`, `src/mining_pm4py.py` fitness 1.0 / precision 0.98 / 3 variants vs discovered inductive model (not normative BPMN), `docs/05-findings-r1.md`)
  - 3 variants 80/20/20; R2:20 (S3), R3:20 (S4), R4:20 (S6); S1 7.2±1.2d, S2 10.0±1.4d, S5 approval 3.3d
- [x] Stats: targeted 60/60->0/60, chi2=120 p=6.3e-28, Fisher p=2.1e-35, Welch S1-vs-S2 t=-6.94 p=3.3e-08 (`src/evaluate.py`, `data/evaluation.csv`)
- [x] Robustness: recall 98.9%@2% noise but FPR 11.7% — breakdown at 2% (`src/noise_test.py`, `data/robustness.csv`)
- [x] Redesign + Round 2: 60 cases / 400 events, 0 violations (`docs/06`, `docs/bpmn/v2.bpmn`, S3R 8.4d / S4R 7.7d / S6R 9.19d (median 9.28) vs S1 7.18 (+2.0) / vs S6 8.04 (+1.15))
- [x] External check: BPIC 2019 mapping + falsifiers (`docs/07`, `data/bpic_mapping_demo.csv`); validity + appendix (`docs/00,09,10`)

## Reproduce
```
pip install -r requirements.txt   # pandas/numpy/scipy/matplotlib + pm4py 2.7 (installed)
python3 src/generate_log.py
python3 src/check_conformance.py data/event-log-r1.csv
python3 src/generate_log_r2.py
python3 src/check_conformance.py data/event-log-r2.csv
python3 src/evaluate.py           # chi2/Fisher/Welch/vendor strata -> data/evaluation.csv
python3 src/noise_test.py         # 0/2/5/10% sweep -> data/robustness.csv (breakdown at 2%)
python3 src/mining_pm4py.py       # inductive miner + fitness/precision/alignments -> data/pm4py_results.json
```
Stable targets (kept): `make bpic` (= `src/analyze_bpic2019.py` + `src/compare_lab_field.py` -> `data/comparison.csv`, `data/hypotheses.csv` check) and `make hypo` (= H1–H8 registry check: 5 supported / 2 nuanced / 1 open).
Web showcase: `python3 -m http.server 8000 --directory webpage` -> open http://localhost:8000 (KPIs, R1/R2 toggle, variant/violation/cycle/robustness + run-trend charts, run registry table, BPIC sample).
Living runs: `python3 src/run_manager.py --n 20 --era both` -> timestamped `data/runs/<UTC-tag>/` + appends `data/runs.csv` (8 backfilled runs: R1 viol 0.50, R2 0.0). Rebuild dashboard data: webpage/data.json includes runs + BPIC.
Real data: FULL corrected run `data/bpic2019_results.json` (n=251,734; DOI 10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1) — R1 maverick 590/1044=56.5% (2-way); R2 0/11128=0.0% (after-GR applicable); R3 value-match proxy 1584/11128=14.2% after vs 0/199564 before; R4 qty/price-only 26366/251734=10.5% (approval-change 4290/251734=1.7% excluded); R5 408/251734=0.16%. See `docs/11-bpic2019-results.md`.
XES canonical: `data/BPI_Challenge_2019.xes` MD5 4eb909242351193a61e1c15b9c3cc814 (728558522 bytes; DOI 10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1; see `docs/14-data-stewardship.md`).
Live Odoo path: `docker compose up -d`, then `psql -h localhost -U odoo p2p-exp -f sql/odoo_extract.sql -o data/event-log-odoo.csv --csv`.

## Layout
- `docs/` 00 abstract, 01 norm, 02 scenarios, 03 odoo-setup, 04 execution protocol, 05 findings-R1, 06 redesign+R2, 07 BPIC-2019 + falsifiers, 09 validity, 10 appendix (predicates + formulas + generator spec), 11-bpic2019-results, docs/13/14/15 (`docs/13-cross-validation.md`, `docs/14-data-stewardship.md`, `docs/15` reserved); `docs/bpmn/` normative + v2
- `data/` event-log-r1/r2.csv + conformance + summary + evaluation.csv + robustness.csv + pm4py_results.json + bpic_mapping_demo.csv + `data/hypotheses.csv` + `data/comparison.csv` (from `src/compare_lab_field.py`) + bpic2019_results.json + bpic2019_case_results.csv
- `src/` generate_log (stochastic), generate_log_r2, check_conformance, evaluate (Fisher/Welch/vendors), noise_test (sweep), mining_pm4py (installed), `src/signatures.py`, analyze_bpic2019.py, compare_lab_field.py
- `sql/` odoo_extract.sql (line-grain) | `webpage/` index.html + app.js + styles.css + data.json + `webpage/hypotheses.js` + figures/ (boxplot, variants, heatmap)
