# Task 4 provenance re-review, round 2

Reviewed only `7a88d2a..fd7f4d7`: the open standalone provenance P2 and regressions in changed files. **Verdict: addressed; no new concrete issue found in scope.** No full suite or browser/server retry. The implementer reports focused reporting/portability tests: 20 total, 19 passed, one HTTP skip; standalone canonical CLI and `node --check` passed.

`src/build_dashboard.py:95-120` now hashes the actual input bytes for standalone `build(data_dir, output_path)`; its `path` and `path_base` refer to those bytes and no `download` is asserted. `src/build_dashboard.py:139-153` verifies each input hash before copying, preserves it as `source_sha256`, then gives `sha256` the hash of the downloadable bytes. A transformed field summary gains an explicit `source_xes` basename note. `tests/test_portability.py:141-165` checks the canonical input hash, the sanitized site-copy hash, their difference, and the copied field's absence of the author's absolute path.

`webpage/app.js:90-101` renders the transformation and input hash for transformed copies; `webpage/index.html:53-56` describes the SHA-256 column as the download hash. The checked-in sample bundle was generated from an already sanitized demo field summary, so its source and download hashes are equal and no transformation note is appropriate. I independently checked all five displayed download hashes against checked-in artifact bytes and confirmed that sample field `source_xes` is only `BPI_Challenge_2019.xes`.

This review does not establish desktop/mobile rendering, HTTP behavior in the restricted sandbox, live Odoo outcomes, or raw XES reproducibility.
