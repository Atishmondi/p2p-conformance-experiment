# Reproducibility Gate — P2P Conformance Experiment

Scope: this file (`docs/19-reproducibility.md`) is the reproducibility gate.
It owns no code and rewrites no data. All numbers below were verified by
READ-ONLY commands only (`ls -l`, `wc -l`, `md5` of small files, `make -n`,
`python3 --version`); the full field analyzer was NOT re-run (takes ~1 min
and rewrites ~23 MB — skipped per gate rule).

Audit date: 2026-09-23. Python verified: `3.9.6`.

---

## 1. Obtain data (canonical XES + samples)

Canonical field source — exactly ONE copy, never duplicated:

- File: `data/BPI_Challenge_2019.xes` — 728,558,522 bytes (`ls -l` verified).
- DOI: `10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1` (4TU.ResearchData;
  see `docs/07-real-dataset.md`, `docs/11-bpic2019-results.md:3-6`).
- MD5: `4eb909242351193a61e1c15b9c3cc814` (see `docs/14-data-stewardship.md` §5).
- Verify (read-only):
  ```bash
  ls -l data/BPI_Challenge_2019.xes   # expect 728558522
  md5 data/BPI_Challenge_2019.xes     # expect 4eb909242351193a61e1c15b9c3cc814
  find . -type f -iname '*.xes' -exec ls -lh {} \;
  find . -type f -size +50M -exec ls -lh {} \;   # expect exactly one line
  ```

Samples (all under the 4,000-row cap; `wc -l` verified, header included):

| file | rows (`wc -l`) | data rows | source |
|---|---|---|---|
| `data/bpic_sample.csv` | 301 | 300 | `src/fetch_bpic_sample.py` (LAB_PROXY fallback from first 300 events of `event-log-r1.csv`; never pulls the 728 MB XES, 5 MB cap) |
| `data/bpic2019_mapped_sample.csv` | 3999 | 3,998 | derived sample from XES |
| `data/bpic_mapping_demo.csv` | 201 | 200 | lab-proxy demo (first 200 events of `event-log-r1.csv`, NOT real BPIC data) |

Do NOT download the full XES to `/tmp`, `webpage/`, or backup suffixes
(`docs/14` no-duplicate policy).

## 2. Field analysis — command + expected outputs + durations

DO NOT run routinely. The full streamed scan rewrites ~23 MB and takes
~1 min. Re-run only when the XES, `src/analyze_bpic2019.py`, or R1–R5
proxies change.

```bash
make -n bpic
# verified output:
#   python3 src/analyze_bpic2019.py
#   python3 src/compare_lab_field.py
```

| step | command | inputs | outputs (sizes via `ls -l`) | duration |
|---|---|---|---|---|
| field scan | `python3 src/analyze_bpic2019.py [xes_path]` | `data/BPI_Challenge_2019.xes` (streamed via `iterparse`, constant memory, `elem.clear()` per trace) | `data/bpic2019_case_results.csv` (23,206,352 bytes; 251,734 case rows) + `data/bpic2019_results.json` (9,665 bytes; n_cases=251734, n_events_filtered=1595596, dropped=327, epsilon=0.01) | ~1 min (SKIPPED in this audit) |
| lab↔field compare | `python3 src/compare_lab_field.py` | `data/bpic2019_results.json` (field rates) + hardcoded lab anchors | `data/comparison.csv` (629 bytes; 4 comparison rows + header) | seconds |

Expected field result (from existing `data/bpic2019_results.json`, NOT recomputed):
n_cases=251,734; filters 2018-01-01–2019-01-27; falsifiers A INCONCLUSIVE /
B REFUTED / C REFUTED. See §7 for stratum denominators.

`src/analyze_bpic2019.py` CLI also accepts `--cases-out PATH --json-out PATH`;
defaults write to `data/` (see `src/analyze_bpic2019.py:56-58,72-75`).

## 3. Hypotheses analysis (`make hypo`)

Read-only registry check — safe to run any time (no data writes).

```bash
make -n hypo
# verified output:
#   echo "H1-H8 registry (data/hypotheses.csv): 5 supported / 2 nuanced / 1 open"
#   python3 -c "import csv; rows=list(csv.DictReader(open('data/hypotheses.csv'))); ..."
```

Live command:

```bash
make hypo
```

Expected: `hypotheses=8`; H1,H3,H4,H6,H7 supported / H2,H5 nuanced / H8 open
(`data/hypotheses.csv:2-9`, 9 lines via `wc -l` including header).
Small-file MD5 (verified): `hypotheses.csv c2697b1f54d36775701d2ab230fc29e0`,
`comparison.csv 1d4deea30300e019889d64c6d8e70e1a`,
`evaluation.csv d387e7f88f50a9c413675a7cd7fd9f91`.

`data/comparison.csv:2-5` cross-check: R2 20/20 vs 0/11128 diff 1.0;
R3-after 20/20 vs 1584/11128 diff 0.8577; R4-3way 20/20 vs 25197/236192
diff 0.8933; R1-2way 590/1044=0.5651. Note: R4-3way pooled denominator
(236,192) differs from the corrected overall (26,366/251,734 in `docs/11`);
cite the `docs/11` figure and state which denominator is used
(`docs/16-research-audit.md:149`).

## 4. Lab runs (`run_manager`, registry, seed recording)

Fast, small, reproducible. Canonical seeds: R1 seed 42 (2026-01-05,
120 cases / 740 events), R2 seed 7 (2026-02-02, 60 cases / 400 events)
(`docs/10-appendix.md:77-104`).

```bash
make -n data
# verified output:
#   python3 src/generate_log.py
#   python3 src/generate_log_r2.py

python3 src/generate_log.py                                # seed 42 -> data/event-log-r1.csv
python3 src/check_conformance.py data/event-log-r1.csv    # -> data/conformance-r1.csv + data/summary-r1.csv
python3 src/generate_log_r2.py                             # seed 7  -> data/event-log-r2.csv
python3 src/check_conformance.py data/event-log-r2.csv    # -> data/conformance-r2.csv + data/summary-r2.csv
python3 src/evaluate.py        # -> data/evaluation.csv (chi2=120 p=6.3e-28, Fisher p=2.1e-35, Welch t=-6.94 p=3.3e-08)
python3 src/noise_test.py      # -> data/robustness.csv (breakdown at 2%: FPR 0.117)
python3 src/mining_pm4py.py    # -> data/pm4py_results.json (fitness 1.0 vs discovered net, precision 0.9796)
```

Living runs (timestamped, registry-appended; preserves canonical files via
backup/restore in `src/run_manager.py:112-178`):

```bash
python3 src/run_manager.py --n 20 --era both
# --n: per-scenario cases (default 20); --era r1|r2|both (default both)
# --tag TAG (default UTC YYYYMMDD-HHMM); --seed / --seed-r1 / --seed-r2
# appends ONE row per era to data/runs.csv; snapshots to data/runs/<tag>/
```

Registry: `data/runs.csv` (9 lines via `wc -l`: header + 8 rows).
Current rows: `backfill-01..04-r1` (seeds 42/43/44/45, 120 cases, 740 events,
viol 0.50) + `backfill-05..08-r2` (seeds 7/8/9/10, 60 cases, 400 events,
viol 0.0), all `utc_time 2026-09-23T04:17:27+00:00`.
Per-run dirs hold `event-log-<era>.csv` + `conformance-<era>.csv` +
`summary-<era>.csv` (3 files each; `ls data/runs/backfill-01/` verified).

Full lab reproduction table: `docs/10-appendix.md:106-121` (steps 1–7).
Requirements: `requirements.txt` (pandas/numpy/scipy/matplotlib; pm4py
optional — step 7 skipped without it).

## 5. Output map (every `data/` file + what generates it)

Sizes via `ls -l`; line counts via `wc -l` where noted.

| file | bytes | generator | notes |
|---|---|---|---|
| `BPI_Challenge_2019.xes` | 728558522 | canonical download (DOI §1) | no — re-download only |
| `bpic2019_case_results.csv` | 23206352 | `src/analyze_bpic2019.py` (full streamed scan) | 251,734 data rows; rewrites on field re-run |
| `bpic2019_results.json` | 9665 | `src/analyze_bpic2019.py` | full-run summary |
| `bpic2019_mapped_sample.csv` | 560654 | derived sample from XES | 3,998 data rows |
| `bpic_sample.csv` | 34165 | `src/fetch_bpic_sample.py` | 300 data rows (LAB_PROXY) |
| `bpic_mapping_demo.csv` | 16752 | first 200 events of `event-log-r1.csv` | lab-proxy demo, not real BPIC |
| `event-log-r1.csv` | 55815 | `src/generate_log.py` (seed 42) | 120 cases / 740 events |
| `event-log-r2.csv` | 31221 | `src/generate_log_r2.py` (seed 7) | 60 cases / 400 events |
| `event-log-template.csv` | 175 | schema template | — |
| `conformance-r1.csv` | 12299 | `src/check_conformance.py data/event-log-r1.csv` | per-case violations |
| `conformance-r2.csv` | 6675 | `src/check_conformance.py data/event-log-r2.csv` | 0/60 violations |
| `summary-r1.csv` | 452 | `src/check_conformance.py` (side output) | per-scenario aggregates |
| `summary-r2.csv` | 295 | `src/check_conformance.py` (side output) | per-scenario aggregates |
| `evaluation.csv` | 973 | `src/evaluate.py` | 45 lines; chi2/Fisher/Welch/vendor strata |
| `robustness.csv` | 268 | `src/noise_test.py` | 0/2/5/10% sweep |
| `pm4py_results.json` | 605 | `src/mining_pm4py.py` | fitness 1.0 / precision 0.9796 (discovery-diagnostic) |
| `hypotheses.csv` | 2495 | authored pre-registration (H1–H8); checked by `make hypo` | 9 lines; 5/2/1 |
| `hypothesis_erp_mapping.csv` | 5307 | authored ERP mapping for `docs/17` | 9 lines |
| `comparison.csv` | 629 | `src/compare_lab_field.py` | 5 lines; Wilson CI + z-test |
| `runs.csv` | 652 | `src/run_manager.py` (append-only index) | 9 lines; header + 8 backfills |
| `runs/` (8 dirs) | 427202 file bytes (476K on disk via `du -sh`) | `src/run_manager.py` outputs | backfill-01…08; no `live-demo` (see §6) |

## 6. Run identification (UTC tags)

- Default tag: `datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")`
  (`src/run_manager.py:50-51`).
- Explicit tag: `python3 src/run_manager.py --tag <TAG> --seed <S> --era both`
  → dir `data/runs/<TAG>/`, rows `<TAG>-r1` + `<TAG>-r2` in `data/runs.csv`.
- Registry columns: `run_id,utc_time,era,n_per_scenario,seed,cases,events,viol_rate,mean_cycle`
  (`src/run_manager.py:44-45`).
- `utc_time` is ISO-8601 UTC (`timespec=seconds`); seeds are recorded per era
  (`--seed-r1/--seed-r2` override `--seed`; random `0..2**31-1` if omitted).
- Current registry: 8 backfilled rows sharing `2026-09-23T04:17:27+00:00`
  (seeds 42–45 for r1, 7–10 for r2). Backfill dirs each hold exactly the 3
  snapshotted files above. `live-demo` (cited in `docs/14` at prior audit)
  is ABSENT at this audit — 8 dirs (`backfill-01…08`), not 9.

## 7. Metric denominators table (applicable-n discipline)

Quote every rate as `n_true / n_applicable`. `None` = not applicable
(missing ts or wrong stratum); `False` = applicable and conformant.

Lab (frozen `src/check_conformance.py::check_case`, seeds 42/7):

| cohort | n | rate | reading |
|---|---|---|---|
| targeted applicable (S3→R2 20/20 + S4→R3 20/20 + S6→R4 20/20) pre | 60/60 = 1.0 | applicable-cohort | detector correctness |
| targeted applicable (S3R/S4R/S6R) post | 0/60 = 0.0 | applicable-cohort | config enforcement; abs_reduction=1 |
| overall R1 anchor | 60/120 = 0.50 | population | do not quote 1.0 without cohort scope |
| S1 false positives | 0/20 = 0.0 | compliant baseline | second clause needs /20 |
| R1/R5 targeted | 0 | by design | no signal |

Field (full corrected run, `data/bpic2019_results.json`; n_cases=251,734):

| rule | stratum rate (cite this) | overall / context | stratum n |
|---|---|---|---|
| R1 maverick | 590/1044 = 0.5651 (2-way) | overall 3450/251734 = 0.0137 | 2-way n=1044 |
| R2 ordering | 0/11128 = 0.0 (after-GR applicable) | of n_cases=15182; None=4054 (26.7%) | after-GR applicable 11128 |
| R3 value-proxy | 1584/11128 = 0.1423 (after-GR) vs 0/199564 = 0.0 (before-GR structural) | pooled 1584/210692 = 0.0075 — DO NOT quote alone | after 11128 / before 199564 (of 221010; None=21446) |
| R4 qty/price-only | 26366/251734 = 0.1047 | strata 10/1044, 1882/15182, 23315/221010, 1159/14498 | all 251734 |
| approval-change (EXCLUDED from R4) | 4290/251734 = 0.0170; approval-only 3301/251734 = 0.0131 | 2-way 1000/1044 = 0.9579 vs rework 10/1044 = 0.0096 | — |
| R5 clear w/o record | 408/251734 = 0.0016 | strata all < 0.01 | all 251734 |

Strata totals: 2-way 1044 + after-GR 15182 + before-GR 221010 + Consignment 14498 = 251734.
R2/R3 denominators are stratum-applicable by design (`docs/11`, `docs/13` §2).

## 8. Authoritative files (single sources of truth)

- `src/signatures.py` (80 lines via `wc -l`, 5,254 bytes via `ls -l`):
  single-source R1–R5 `lab_definition` / `field_proxy` / `applicable_scope` /
  `event_pattern` / `known_gaps` + `SCOPE_NOTES`. Lab =
  `check_conformance.py::check_case`; field = `analyze_bpic2019.py::evaluate_case`.
- `data/hypotheses.csv` (9 lines, 2,495 bytes): H1–H8 pre-registration with
  `predicted_signature, lab_rate, lab_n, field_rate, field_n, status, falsifier_ref`.
- `data/hypothesis_erp_mapping.csv` (9 lines, 5,307 bytes): H1-adapted,
  H2/H3/H5 directly-testable priorities, H6 negative control, H7 monitored-only,
  H4 excluded (structural zero), H8 frame stays open.
- `data/comparison.csv` (5 lines, 629 bytes): Wilson 95% CI + two-proportion
  z-test per rule (see `src/compare_lab_field.py:29-35` anchors).
- Protocols: `docs/04-odoo-execution-protocol.md` §6 (9-step backbone:
  define → signatures → execute → extract → detect → verify → modify →
  rerun → measure + hypotheses-first gate) and `docs/17-erp-experiment-protocol.md`
  (H8 preregistration; §§1–8; results section intentionally empty — no Odoo
  executed, no H8 closure).
- Reproduction table: `docs/10-appendix.md:106-121` (steps 1–7 + `make data &&
  make check && make eval`).

Language rule (`docs/16` G1–G7, `docs/17` §1): every efficacy sentence must
carry cohort + denominator + condition (e.g. "0/20 S3R under recorded-timestamp
definition"). Bare "eliminates violations" is forbidden.

## 9. Established vs open claims pointer (`docs/16` + H8)

- Established: `docs/16-research-audit.md` §A — **14 items** (E1–E14:
  normative model, S1–S6 design, synthetic stand-in, seeded stochastic
  generator, R1 60/60 + S1 0/20, R2 60/60→0/60, stats, throughput separation,
  variants, PM4Py-as-discovery, brittleness, full field run, recording gate,
  pre-registration + backbone).
- Proxy/lossy (do NOT quote as rule-to-rule): §B — **9 items** (P1–P9:
  scenario derivation, qty worth-proxies, R3 value-delta, R1 maverick scope,
  R2 recording times, R4 approval exclusion, R5 clear-vs-record, before-GR
  structural zero, pooled-rate warning).
- Lab-only demonstration (§C: C1–C5 under seeds 42/7 + frozen checker) and
  hypothesized-only (§D: D1–D5) vs field-contradicted (§E: S3-absent,
  R3-tolerance-0 refuted, R4-definition).
- Open: §F — **6 items (F1–F6) + 5 hypothesized-only (D1–D5) = 11**;
  H-status **5 supported (H1,H3,H4,H6,H7) / 2 nuanced (H2,H5) / 1 open (H8)**.
- Claims stronger than evidence: §G — **11 issues (G1–G11)** with per-claim
  corrections (no in-place rewrite).
- **H8 (redesign transfer): OPEN.** Lab pre 60/60=1.0 → post 0/60=0.0 licences
  only a pilot hypothesis; field n/a, UNTESTED, no intervention observed
  (`data/hypotheses.csv:9`; `docs/13-cross-validation.md:200-226`;
  `docs/17-erp-experiment-protocol.md`; `docs/18-defense-and-validity.md` Q10).
  Transfer verdict options (transferred / mechanism-confined / not transferred)
  are preregistered in `docs/17` §4 and require rerun + field-base comparison
  with FLAGs on S3-absent / tolerance-0 / R4-attribution.
- Defense companion: `docs/18-defense-and-validity.md` (10 Q&A + 6 threat
  families / 14 items) and thesis map `docs/15-thesis-outline.md` (Ch1–Ch8;
  Ch7 protocol-only, no results).

---

## Commands verified (read-only, this audit)

```bash
ls -l data/ docs/ src/signatures.py src/compare_lab_field.py src/analyze_bpic2019.py src/run_manager.py
ls -l data/runs/ data/runs/backfill-01/ ; du -sh data/runs
wc -l data/bpic_sample.csv data/bpic2019_mapped_sample.csv data/bpic_mapping_demo.csv \
      data/hypotheses.csv data/hypothesis_erp_mapping.csv data/comparison.csv data/evaluation.csv data/runs.csv
md5 data/hypotheses.csv data/comparison.csv data/evaluation.csv
make -n bpic ; make -n hypo ; make -n data
python3 --version   # 3.9.6
```

Full analyzer NOT run. `webpage/data.json` rebuild and `docker compose` live-Odoo
path (`sql/odoo_extract.sql → data/event-log-odoo.csv`) remain documented-only
(`README.md:41-45`).
