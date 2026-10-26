# Task 4 implementation report

Status: implementation complete. Base 0aad3e9; Task 2 and Task 3 integrated. Commit SHA recorded in parent handoff (the report is included in the Task 4 commit).

## Delivered

- A schema 2.0 static investigation interface with generated lab cohort and rule denominators, scenario duration, artifact-derived example cases, separate field strata/proxy definitions, source hashes/downloads, explicit ERP pilot status and limitations. No CDN/framework or static fallback counts. Readable labels, keyboard-native controls, horizontally scrollable mobile tables and visible load/error states.
- `src/demo.py` generates a matching `webpage/` directory with the run. `src/build_dashboard.py --site-dir` refreshes that static bundle after editing supplied artifacts. The builder maintains its existing `build(data_dir, output_path)` API. Sources are copied with displayed SHA-256 hashes; historical field JSON is sanitized by the demo before both hash and copy. Raw XES is excluded. Case trace quantity columns show values only on receipt/invoice event rows; the synthetic source repeats snapshot values elsewhere.
- The checked-in `webpage/` bundle was rebuilt from an isolated v2 demo with `n=20` and historical-field-proxies-v1 summary. Its source links resolve inside the bundle, including the ERP pilot/event contract documents. Obsolete hypotheses JavaScript and CDN dashboard implementation were removed.
- Concise README, business case, claim/evidence map, completion boundary, optional dependency list, historical supersession notices, and stdlib `scripts/verify.sh` invoked by CI. Historical numbered documents and handoff retain their original body; historical SQL is explicitly retired.

## RED/GREEN and verification

- `tests/test_portability.py` initially failed because no generated static bundle existed. It exercises a fresh repo copy with no optional BPI JSON or XES and `python3 -S`, the explicit unavailable field, real generated case traces, local content hashes, source downloads over HTTP where listeners are allowed, rebuild after a conformance artifact edit, and self-template-directory refresh.
- A later RED assertion found snapshot receipt quantity on non-receipt rows; production examples were narrowed to activity-specific deltas. Another RED run found `SameFileError` when regenerating the checked-in template directory; copying the same source/target is now skipped.
- `./scripts/verify.sh`: 59 tests passed, 1 skipped (HTTP listener denied by this sandbox). `node --check webpage/app.js` and `git diff --check` passed. Direct bundle integrity check: schema 2.0, 120 and 60 generated lab cases, historical field total 251,734, after-GR R3 numerator 1,584, all five source hashes match copied bytes, no author host path in JSON or field download. Canonical historical data and legacy checker were not edited.
- Browser desktop/mobile inspection was attempted by the parent reviewer but unavailable: `python3 -m http.server` loopback bind raises `PermissionError: Operation not permitted`, while CUA browser blocks local `file:` navigation by URL policy. No screenshot or visual/browser result is claimed. The HTTP assertions remain active in CI where loopback listening is available.
- Separate controller raw UTC reanalysis in `/tmp/p2p-validation/verification.md` found byte-identical field case CSV and unchanged aggregate counts; optional scientific versions there were NumPy 2.0.2, SciPy 1.13.1, pandas 2.3.3, matplotlib 3.9.4, PM4Py 2.7.23.7. These are not core requirements. Live Odoo remains unverified due absent Docker daemon/runtime permissions.

## Self-review and limits

The displayed sample is one deterministic case per observed scenario, not a universal event browser. An unversioned historical conformance row is labeled v1; field proxy version is never equated to lab v2. Null rate displays as unavailable. A source SHA identifies exact bundle bytes, not field completeness, license, or authoritativeness. The policy is fictional and not practitioner endorsed; field applicability, activity/value definitions, cutoff/censoring and incomplete cases prevent operational precision/recall or causal savings claims. No new video, push, deploy, raw XES copy, original-workspace overwrite, or live ERP claim. The unrelated pre-existing `task-1-report.md` modification remains untouched and outside this commit.
