# Task 1 independent review

Reviewed change range `8293e29..cc367ec` against the task brief and the binding
`docs/superpowers/specs/2026-10-25-project-completion.md`. Current checkout
`5795f6b` adds council documentation, with the reviewed implementation unchanged.
This review covers both specification compliance and code quality. No production
files were modified.

## Verdicts

- **Specification: changes requested.** The checker, explicit-output-root run
  flow, versioning, and independent fixture requirements are substantially met.
  The shipped default run-manager invocation is unusable against the checked-in
  registry and violates the task's caller-compatibility expectation (finding 1).
- **Code quality: changes requested.** The design is considerably safer and
  clearer than the baseline, but registry initialization has a reproducible
  concurrency failure (finding 2), and predictable registry incompatibility is
  detected only after generating artifacts (finding 1).

## Findings

### 1. High / P1: the default run-manager invocation always fails in a fresh checkout

**Locations:** `src/run_manager.py:40`, `src/run_manager.py:73-88`,
`src/run_manager.py:112-119`; checked-in `data/runs.csv:1`.

The default output root remains `data/`, whose checked-in `runs.csv` has the
historical nine-column header. Every run now requires the fourteen-column v2
header and raises `ValueError` on the existing registry. Consequently the existing
README command, `python3 src/run_manager.py --n 20 --era both`, cannot complete
in the delivered checkout. It reserves a new run directory and writes its event
log, conformance, and summary before raising an uncaught exception. With
`--era both`, execution stops after the first era. Retrying creates another
incomplete directory when using a default tag; a chosen tag is then unavailable.

**Reproduction:** copied the actual checked-in `data/runs.csv` into a temporary
root, assigned that root to `run_manager.DATA`, and invoked
`main(['--n', '1', '--era', 'r1', '--seed', '1', '--tag',
'default-root-repro'])` without `--output-dir`. The result was
`ValueError: runs.csv has an incompatible header; choose a fresh --output-dir`.
The reserved directory already contained `event-log-r1.csv`,
`conformance-r1.csv`, and `summary-r1.csv`. This preserves canonical data while
faithfully reproducing the default-path behavior.

The limitation is disclosed in the implementation report and event contract,
but disclosure does not make the supported default invocation work. A concrete
fix is to choose a fresh generated-data root for the default v2 workflow and
preserve the canonical historical registry. Alternatively provide an explicit,
lossless version-aware migration. Validate an explicitly supplied incompatible
root before reserving a tag or generating output, and report a concise CLI error.
Add a regression that starts with the actual historical header and proves the
selected default workflow succeeds without changing historical data.

### 2. Medium / P2: exclusive file creation publishes an empty registry before the header is ready

**Location:** `src/run_manager.py:81-88` (also relevant to append at `94-95`).

Opening `runs.csv` with mode `x` atomically reserves the pathname, but the
header is only visible after the writer flushes/closes. A second run with a
different safe tag can observe the file during that interval, open it, read no
header, and incorrectly fail with the incompatible-header exception. The
comment claiming exclusive creation prevents registry truncation is true, but
it does not provide a complete initialization protocol. Separate per-run
directories do not isolate the shared registry.

**Deterministic reproduction:** intercepted `Path.open` immediately after the
first worker successfully created the registry with mode `x`, delaying its
return until a second `run_era` worker checked the same file. Generator/checker
work was stubbed so this exercised only the actual registry code. The second
worker raised `ValueError: runs.csv has an incompatible header; choose a fresh
--output-dir`; after releasing the first worker it logged normally. This is a
valid process scheduling interleaving, not a malformed user file.

Serialize initialization and append using a portable standard-library protocol,
or atomically publish a fully written header without overwriting another
worker's registry. A competing run should wait correctly or fail explicitly as
busy before generation, rather than misdiagnosing a healthy registry. Include
a deterministic regression for two different tags sharing a newly created root.
Do not use a platform-specific locking dependency that breaks the required
stdlib portability.

## Strengths and requirements satisfied

- The historical snapshot is byte-for-byte identical to the base checker:
  both SHA-256 digests are
  `e599191578090a4cdebe01d9dda02c91742ecf330dbe41d0d5de223b5f7130ce`.
  The diff leaves generators and canonical input/result CSVs unchanged.
- Normalization has a clear boundary: required fields, finite nonnegative
  Decimal quantities, recorded datetime validation, UTC normalization, mixed
  timezone rejection, duplicate checks, item/unit conflicts, and unsupported
  return/reversal rejection. Direct `check_case` callers receive validation too.
- The seven-value tuple remains intact. Proven violations dominate unknown
  outcomes; missing evidence and timestamp ties do not establish compliance.
  Chronological cumulative R3 checks prevent receipt reuse and later-receipt
  repair. R1/R2/R5 check all target events, and R4 bounds each modification by
  its next PO.
- CSV reports identify v2, expose per-rule unknowns and exclusive case status,
  and derive evaluated denominators explicitly. The noise consumer imports the
  same checker and handles wholly dropped cases as unknown with visible counts.
- Explicit fresh output roots work, artifacts are generated directly in the
  reserved run directory, tags are validated, duplicate tags fail without
  clobbering, default tags have sufficient uniqueness, and seeded output bytes
  are deterministic across roots.
- Tests use small independent literal traces and real subprocess experiments.
  Baseline tests compare v1/v2 directly with the required 60/120 and 0/60 totals.
  The contract documents the R3 per-rule count difference without changing the
  historical headline totals. Helpers remain focused and use stdlib only.

## Verification evidence

- Read the task brief, binding specification, implementation plan, full changed
  source files, tests, event contract, implementation report, and review diff.
- Independently reran `python3 -S -m unittest discover -s tests -v`:
  **27 tests passed**, no skips (0.932 seconds in this environment).
- Independently compared the snapshot digest with
  `git show 8293e29:src/check_conformance.py`.
- Performed only the two targeted temporary-root reproductions described above.
  They left canonical files untouched. The working tree was clean before this
  review report was written.
- Parent reviewer separately reports a fresh successful run of all 27 tests
  under Python 3.9 with `-S`; this review's own test run used the available
  `python3` executable.

## Declined to judge / bounded review scope

- Did not independently witness historical RED runs. The report records their
  observed failures; committed fixtures and current GREEN results support the
  behavioral claims, but cannot prove chronology.
- Did not judge downstream evaluation/dashboard handling of the new output
  schema, fresh-clone CI, or final documentation claims; these are assigned to
  later tasks. Existing `evaluate.py` requires its planned evidence-aware update.
- Did not evaluate ERP extraction or live Odoo execution, scientific extras,
  field/raw-XES analysis, operational savings, or actual policy validity.
- Did not require the frozen v1 script's old relative default paths to be fixed:
  byte-for-byte preservation is explicit, and API reproduction with explicit
  input paths is tested and documented.
- Did not demand identical pandas-era noise samples: the revised seeded stdlib
  sampling is explicitly identified as v2 and this task requires a stdlib core.
- No demonstrated false conformance result was found in the reviewed core rule
  paths. This is a bounded review conclusion, not proof over all possible inputs.

Both findings should be resolved before Task 1 is accepted. No unrelated
refactoring is requested.
