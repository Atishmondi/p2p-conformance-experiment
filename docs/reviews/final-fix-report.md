# Final combined fix wave report

Base: `800b29a`; implementation commit: `b15bfcf` (`Fix normalized case grouping and linked invoice R5 evidence`). No other checkout, historical v1, canonical data, or checked-in sample artifacts changed.

- V2 CSV load trims and validates required case IDs before grouping. Whitespace-equivalent events now form one case, with global event ID uniqueness and per-case product/unit checks retained. V2 dashboard examples use normalized case keys; historical v1 example handling remains as before.
- R5 matches a nonblank Payment `invoice_event_id` to only that same-case Vendor Invoice event ID. Earlier invoice means `False`, later invoice `True`, tie or missing match `None`. Unlinked lab payments retain any-earlier-invoice behavior; multiple payments retain proven-violation-over-unknown aggregation. The ERP adapter preserves and validates the exact link, and does not suppress well-formed adverse ordering.
- Optional `three_way_strata` and `by_item_category` containers are validated as objects before traversal. Absent sections remain accepted.
- Updated `docs/event-contract.md` and `docs/erp-pilot.md` and their checked-in `webpage/docs/` copies.

RED observations with new regression tests before implementation: `test_conformance.py` 24 tests, 3 failures; `test_erp_export.py` 9 tests, 3 failures; `test_reporting.py` 18 tests, 9 errors. GREEN: the same focused runs passed, respectively 24, 9, and 18 tests. Final required `./scripts/verify.sh`: 66 tests passed, 0 failures/errors. `git diff --cached --check` passed before commit.

Remaining scope boundaries: no live ERP execution, browser rendering, raw XES rerun, or hosted CI execution performed in this wave. Controller-owned `docs/verification.md` and `docs/completion-report.md` changes were left untouched and unstaged.
