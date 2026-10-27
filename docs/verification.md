# Verification record (2026-10-26 to 2026-10-27)

The controller reanalyzed the available raw BPI Challenge 2019 XES with `python3 -S src/analyze_bpic2019.py data/BPI_Challenge_2019.xes --cases-out /tmp/p2p-validation/field-utc-v2-cases.csv --json-out /tmp/p2p-validation/field-utc-v2-results.json`. It processed 251,734 cases and 1,595,596 filtered events. The case CSV was byte-identical to the saved CSV (SHA-256 `39c3c08a4587448fa4dbdd9597ceb6c96d169a44a9183788eacbd418e54e0810`). Aggregate numeric and proxy findings were unchanged; summary differences were metadata fields `evidence_class`, `rule_version`, `source_xes`, and `timestamp_basis`. The source XES MD5 was `4eb909242351193a61e1c15b9c3cc814`.

An optional scientific evaluation on generated cohorts completed under Python 3.9.6: chi-square statistic 120, Fisher p-value `2.070073888186964e-35`, Welch p-value `3.336269604633326e-08`. Installed optional versions were NumPy 2.0.2, SciPy 1.13.1, pandas 2.3.3, matplotlib 3.9.4, and PM4Py 2.7.23.7. These are descriptive diagnostics on generated samples, not operational effects.

Live ERP execution was unavailable: no Docker daemon, and Colima startup failed with an operation-not-permitted error writing its configuration. A static demo preview was generated, but loopback HTTP binding failed with `PermissionError`, and the local-file browser navigation was blocked by URL policy. Those were the initial restricted-environment results. In the resumed 2026-10-27 environment, the existing portable HTTP test passed normally; desktop/mobile browser rendering remains unverified. The raw XES and temporary reanalysis outputs are excluded from the portable bundle; the checked-in summary remains separate field evidence.

## Portable checks on the final implementation

At implementation commit `fd7f4d7`, `./scripts/verify.sh` on Python 3.9.6 and `.venv/bin/python -S -m unittest discover -s tests` on an empty Python 3.12.14 environment each ran **60 tests: 59 passed, one skipped**. The skipped check requires a loopback HTTP listener, denied in this session. The portable artifact assertions before that network boundary still ran. `node --check webpage/app.js` passed. CI configuration uses the same verification script; no hosted CI execution is claimed.

A source archive without the raw XES built the default demo under `python3 -S`: 120 first-round and 60 second-round cases, with field total 251,734. The five bundled source links existed and their download hashes matched their bytes. A later review tightened stale-verdict rejection and the distinction between original input and sanitized download hashes; regression tests cover both. Canonical tracked `data/` files and the historical v1 checker were preserved.

## Resumed delivery checks

At source commit `800b29a`, the controller reran `./scripts/verify.sh` with Python 3.9.6 and `.venv/bin/python -S -m unittest discover -s tests` with Python 3.12.14. Both ran **60 tests, all passing, no skips**. The existing HTTP integration test successfully fetched the viewer files and verified source-download hashes over loopback; no substitute browser or URL-policy workaround was used. This supersedes the earlier HTTP skip, but does not verify browser rendering.

A fresh `git archive` at the same commit, excluding raw XES, built the default demo twice with Python 3.12 under `-S`. All 22 generated files were byte-identical across the two output directories. Each of the five original input hashes and five public download hashes matched its actual bytes. The JavaScript syntax check passed. Tracked canonical `data/` remained unchanged from the preserved baseline, and the v1 checker matched the original source byte-for-byte.

## Final fix verification

At implementation commit `b15bfcf`, the controller independently ran `./scripts/verify.sh` on Python 3.9.6 and `.venv/bin/python -S -m unittest discover -s tests` on Python 3.12.14: **66 tests passed on each, with no skips**. This includes the new normalized-case, exact invoice-link and malformed optional-container regressions, and the HTTP bundle integration. `node --check webpage/app.js` and whitespace checks passed. Canonical data and the frozen v1 source remained unchanged. The final fix report preserves observed RED/GREEN results; the scoped review records its independent assessment.
