# Task 1 scoped re-review

**Reviewed:** fix `217c471` against base `5795f6b`, using
`review-5795f6b..217c471.diff`, current `src/run_manager.py`, the three added
regression tests, updated event contract, and appended implementation report.
Scope is the two original findings and regressions introduced by their fixes.
No production files changed and no full suite was rerun.

## Verdict

**Specification: approved within this scoped re-review.**
**Code quality: approved within this scoped re-review.**
Both previously blocking findings are addressed. No newly introduced concrete
blocking issue was found in the reviewed changes.

## Finding disposition

### P1: default workflow incompatible with historical registry — addressed

`DATA` now defaults to `ROOT / 'output' / 'experiments'`
(`src/run_manager.py:22`), leaving the historical `data/runs.csv` outside the
write path. The generated root is ignored by Git and the event contract names
the new default.

Registry compatibility is checked within `registry_session` before the caller
reserves its tag or invokes a generator (`src/run_manager.py:90-98`, `141-149`).
An incompatible existing header raises a concise `SystemExit`; the `finally`
block removes the acquired lock. This avoids the previous traceback, consumed
tag, and partial run artifacts caused by predictable header incompatibility.

The new temporary-checkout regression runs both eras without `--output-dir`,
requires both registry rows and summaries, and checks that historical registry
bytes and the contents of `data/` remain unchanged. The incompatible-root
regression repeats the same tag twice and verifies concise failure, unchanged
registry bytes, and no residual run/lock artifacts. These tests exercise the
failure mechanism identified in the original review.

### P2: empty registry published before its header — addressed

Atomic `mkdir` of `.runs.lock` precedes registry inspection and initialization
(`src/run_manager.py:82-98`). A competing invocation therefore fails explicitly
as busy before reading the in-progress header, reserving a tag, or generating
output. The main invocation holds this same session through both eras and all
appends; direct public `run_era` calls also acquire the session. The helper used
inside the held session is private and documents its lock precondition.

The added concurrency test forces the original scheduling boundary by pausing
`Path.open('x')` after the registry pathname exists but before its header is
written. It requires the competitor to report busy without creating its run,
then verifies the first invocation completes and a subsequent subprocess can
use the second tag and append a complete v2 row. This directly covers the
original race rather than relying on probabilistic concurrent timing.

## Evidence and accepted limits

- The implementation report records regression-first RED evidence and a final
  **30/30** passing suite under Python **3.9.6** with `-S`. That evidence was
  reviewed; the full suite was deliberately not repeated for this re-review.
- Locking uses only portable standard-library directory operations; no
  platform-specific locking dependency was introduced.
- Explicit busy failure while a root is active is the accepted controller
  design. Serializing generation for all eras is a bounded throughput tradeoff.
- The documented stale-lock behavior after process termination is accepted:
  verify no run is active before manually removing the empty lock directory.
  Ordinary exceptions and exits release the lock through `finally`.
- Final README/dashboard path integration remains within later project tasks;
  it does not reopen the now-fixed default execution failure.
- No broader checker, ERP, field-analysis, or dashboard review is claimed here.
