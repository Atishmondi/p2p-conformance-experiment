# Data Stewardship (Disk-Constrained): BPI Challenge 2019 XES

Context: disk is constrained (~96% used / ~8.7 Gi free per project brief;
`df -h /` at audit time showed 68% / 5.7 Gi free — treat disk as scarce
either way). The 728 MB XES must be managed deliberately: exactly ONE copy,
never duplicated or converted wholesale, streamed in place.

Audit date: 2026-09-23. Scope: READ-ONLY audit; no data files were
written, modified, or deleted to produce this document.

## 1. Audit result

- Files > 50 MB under project: exactly ONE —
  `data/BPI_Challenge_2019.xes` (695 MiB / 728,558,522 bytes).
- Files > 10 MB: exactly TWO — the XES plus the derived
  `data/bpic2019_case_results.csv` (22 MiB / 23,206,352 bytes).
- XES copies: exactly ONE by filename (`*.xes`), by exact byte size
  (728558522), and by content (MD5 below). Duplicate wholesale copies: 0.
- No `.bak` / `*copy*` / `.xml` wholesale conversions of the XES found.
- `data/runs/`: 8 entries (backfill-01…08; `live-demo` absent at this audit),
  `du -sh` 476K, file-bytes sum 427,202.

Verification (all matched):

- `data/BPI_Challenge_2019.xes`: 728,558,522 bytes,
  MD5 `4eb909242351193a61e1c15b9c3cc814`.

## 2. Artifact inventory

| file | bytes | source | regenerable? |
|---|---|---|---|
| `data/BPI_Challenge_2019.xes` | 728558522 | 4TU.ResearchData, DOI `10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1` (see `docs/07-real-dataset.md`) | no — canonical, re-download only |
| `data/bpic2019_case_results.csv` | 23206352 | derived: full streamed scan of XES via `src/analyze_bpic2019.py` (251,734 data rows) | yes — re-stream XES |
| `data/bpic2019_mapped_sample.csv` | 560654 | derived sample (3,998 data rows) | yes — resample from XES |
| `data/bpic_sample.csv` | 34165 | derived sample (300 data rows) | yes — via `src/fetch_bpic_sample.py` |
| `data/bpic2019_results.json` | 9665 | derived: full-run summary (`src/analyze_bpic2019.py`) | yes |
| `data/bpic_mapping_demo.csv` | 16752 | derived lab-proxy demo (200 rows of `event-log-r1.csv`, not real BPIC data) | yes |
| `data/runs/` (total, 8 runs) | 427202 file bytes (476K on disk) | derived: `src/run_manager.py` outputs | yes — rerun |
| all other `data/*.csv`, `*.json` | each < 60K | derived lab logs / summaries | yes |
| `data/hypotheses.csv` | 2495 | authored pre-registration H1–H8 (checked by `make hypo`) | no — registry, versioned |
| `data/hypothesis_erp_mapping.csv` | 5307 | authored ERP mapping for `docs/17` | no — versioned |
| `data/comparison.csv` | 629 | derived: `src/compare_lab_field.py` (Wilson CI + z-test) | yes — rerun compare |
| `src/signatures.py` | 5254 (80 lines) | single-source R1–R5 signatures + `SCOPE_NOTES` | no — versioned |
| `docs/16-research-audit.md` | 22103 | audit record (owns-only) | no — versioned |
| `docs/17-erp-experiment-protocol.md` | 30250 | H8 preregistration (protocol-only, no results) | no — versioned |
| `docs/18-defense-and-validity.md` | 22359 | defense Q&A + threats (owns-only) | no — versioned |
| `docs/19-reproducibility.md` | new this audit | reproducibility gate (owns-only) | no — versioned |

Row-count check at audit: `bpic2019_mapped_sample.csv` 3,998 rows,
`bpic_sample.csv` 300 rows — both under the 4,000-row sample cap.

## 3. No-duplicate policy

1. Never copy or convert the XES wholesale: no second `.xes`, no
   uncompressed `.xml` dump, no full-CSV export of all 1.6M events, no
   copies under `/tmp`, `webpage/`, or backup suffixes.
2. Stream the XES in place (`pm4py` / iterative parse as in
   `src/analyze_bpic2019.py`); full scans write only small aggregates
   (`bpic2019_results.json`, `bpic2019_case_results.csv`).
3. Samples capped at 4,000 rows each (`bpic_sample.csv`,
   `bpic2019_mapped_sample.csv`, `bpic_mapping_demo.csv`). New samples
   replace rather than accumulate.
4. Before adding any file > 10 MB, check `find . -size +50M` and confirm
   the single-XES invariant still holds.

## 4. Retention: keep `runs/` capped

- Current count: 8 (`backfill-01`…`backfill-08`; `live-demo` absent at this audit).
- Cap: keep `data/runs/` at ≤ 10 entries / ≤ 1 MB total. New runs evict
  the oldest backfill first; `live-demo` is pinned.
- `data/runs.csv` is the index; prune it together with any eviction.
- Probes under `/tmp` (`bpic_probe_out.json`, `bpic_1704_out.json`) are
  ephemeral and must not be copied into the repo.

## 5. MD5 verification command

```bash
# macOS:
md5 data/BPI_Challenge_2019.xes
# expect: MD5 (data/BPI_Challenge_2019.xes) = 4eb909242351193a61e1c15b9c3cc814

# Linux:
md5sum data/BPI_Challenge_2019.xes
# expect: 4eb909242351193a61e1c15b9c3cc814

stat -f %z data/BPI_Challenge_2019.xes   # macOS → expect 728558522
stat -c %s data/BPI_Challenge_2019.xes   # Linux → expect 728558522

# duplicate check (expect exactly one line, zero duplicates):
find . -type f -iname '*.xes' -exec ls -lh {} \;
find . -type f -size 728558522c -exec ls -lh {} \;
find . -type f -size +50M -exec ls -lh {} \;
```
