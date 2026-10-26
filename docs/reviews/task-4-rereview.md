# Task 4 scoped re-review

Reviewed `347767c..7a88d2a` against the accepted Task 4 findings and direct canonical field-copy risk. Read-only inspection and bounded hash/link checks; no full suite, browser, or HTTP retry. The implementer records 60 tests total, 59 passed and one HTTP skip.

## Addressed

- **Stale verdict (P1):** `src/build_dashboard.py:21-51,98-119` now recomputes per-rule failures and unknowns from each event trace using the declared v2 checker or frozen v1 checker and rejects mismatches before writing `dashboard.json`. `README.md:16-25` gives checker regeneration commands for edited v2 logs. `tests/test_portability.py:87-125` covers an event-only quantity mutation, unchanged published outputs after rejection, then regenerated conformance and changed R3 verdict. The manual conformance edit is also rejected at `tests/test_portability.py:127-140`.
- **Pilot fixture link (P2):** `src/build_dashboard.py:130-136` copies the synthetic fixture to `examples/erp-recorded-events.csv` within each site. The checked-in `webpage/docs/erp-pilot.md:3` relative target exists and its bytes match the source fixture. `tests/test_portability.py:54-60` checks bundled document links.
- **Durable verification record (P2):** `docs/claim-evidence.md:9` now links checked-in `docs/verification.md`, which preserves the reanalysis counts, hashes, optional versions, and runtime boundaries.
- **Canonical field summary privacy/hash:** `src/build_dashboard.py:54-65,103-110,141-149` strips the canonical absolute `source_xes` directory from public copied JSON and hashes the sanitized bytes. `tests/test_portability.py:141-151` covers direct canonical `--data-dir data --site-dir ...` and equality of the copied bytes with the displayed SHA-256. The canonical input remains intact. I independently confirmed the checked-in bundle's five source downloads match their SHA-256 values.

## Newly introduced, open

**P2 — `build()` without a site directory records a field hash that does not match its named source.** The preserved standalone API and default CLI path still support `build(data_dir, output_path)` with no `--site-dir` (`src/build_dashboard.py:95-120,152-161`). It now hashes sanitized field bytes at line 105, but only `build_site()` writes those bytes at lines 141-145. The standalone JSON lists `bpic2019_results.json` under a `path_base` that says paths are relative to the selected data directory (`src/build_dashboard.py:107-117`), where the canonical file is unsanitized. For canonical `data/`, the named file's SHA-256 is `5aee96cb05e25933abeed1d20d87a656a955cb018118551f24fea16c89a76dce`; the JSON records the sanitized-byte SHA-256 `f9e8577b029b3fa400c5c0586177b5212566d3877afd9a8da52b6804cdf8e16d`. The actual static site is correct. Make standalone provenance distinguish input and publishable-copy hashes/paths, or emit and point to a sanitized file when no site is requested. Add an assertion for the no-site public JSON path.

## Limits

Desktop/mobile rendering, HTTP loading in this sandbox, live Odoo, and raw XES processing were outside this re-review. The prior report's declared limitations remain appropriate.
