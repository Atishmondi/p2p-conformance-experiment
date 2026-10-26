# Purchase-to-pay evidence desk

This portfolio demonstration asks a practical question: **which procurement control exceptions can the recorded events support, and what would an analyst inspect next?** It combines generated purchase-to-pay cases, a separate historical BPI Challenge 2019 field summary, and an ERP pilot contract. The five lab rules are a **fictional policy for the exercise**, not an endorsed purchasing policy or a production accuracy benchmark.

## Run in five minutes

Requires Python 3.9+; the core demo uses only the standard library. From a fresh clone or download:

```sh
python3 -S src/demo.py --output-dir output/my-first-demo
python3 -m http.server 8000 --bind 127.0.0.1 --directory output/my-first-demo/webpage
```

Open [http://localhost:8000](http://localhost:8000). Choose a new `--output-dir` for another demo; existing directories are protected. `--n 20` is the default cases per scenario; `--without-field` shows the explicit unavailable state. No raw XES, database, Odoo instance, or installed scientific package is required. The static viewer in `output/my-first-demo/webpage` includes its matching `data.json`, source downloads, and pilot documents. Host it as a directory over HTTP; opening `index.html` as `file:` can block `fetch`.

After editing a generated v2 event log, regenerate its matching conformance CSV before rebuilding. For example, after editing either or both logs:

```sh
python3 -S src/check_conformance.py output/my-first-demo/event-log-r1.csv --output-dir output/my-first-demo --tag r1
python3 -S src/check_conformance.py output/my-first-demo/event-log-r2.csv --output-dir output/my-first-demo --tag r2
python3 -S src/build_dashboard.py --data-dir output/my-first-demo --out output/my-first-demo/dashboard.json --site-dir output/my-first-demo/webpage
```

Run only the checker command for each edited log. The builder checks every supplied case verdict against its declared version before publishing, then derives rates and durations, hashes each input, and refreshes the viewer. It fails on missing or inconsistent required input; manually edited conformance verdicts must also match the trace. Historical v1 rows are checked with the frozen v1 checker and are not silently relabeled v2. The optional field summary is absent rather than silently replaced. `make demo OUTPUT_DIR=output/another-demo` is an equivalent generator path. `./run_demo.sh --output-dir output/another-demo` works from another working directory.

## Read the evidence

The default generated run (seeds 42 and 7, `n=20`) has 120 first-round and 60 second-round cases. Its case-level first-round violations are 60/120, and second-round violations are 0/60; generated cohorts show a checker response to designed scenarios, **not** an estimated control effect in a business operation. The dashboard always reads counts from its current source artifacts. An unknown outcome reduces its rule denominator; a case may violate one rule while another remains unknown. Scenario durations are first-to-last observed event spans, not business-calendar service times.

The included BPI field JSON is a **historical observational proxy summary** (251,734 cases); the demo does not rerun its raw XES. For example, the summary contains 590/1,044 maverick proxy hits in its two-way stratum, whereas the lab R1 tests approval ordering. The field R3 uses monetary worth, while the lab R3 uses cumulative item quantities. The activities, units, eligibility and censoring differ. Never pool those denominators or treat a field structural false as a fully conformant case. The exact redistribution license of the raw XES is unverified; raw XES is excluded from this delivery. The small summary and source records have SHA-256 hashes in the viewer.

Start an investigation by selecting a scenario and inspecting its trace, rule outcomes and unknowns; check quantity event deltas and ordering in the source CSV; then inspect the field stratum and its applicable count as separate context. Decide what source action record or missing event would resolve an unknown before proposing a control. [Business case](docs/business-case.md), [claim/evidence map](docs/claim-evidence.md), and [completion report](docs/completion-report.md) provide the decision boundaries.

## Verify and extend

```sh
./scripts/verify.sh
```

This runs the standard-library test suite under `python3 -S`, including isolated generation, source mutation and web-bundle assertions. The HTTP assertion runs where loopback listeners are permitted. CI invokes the same command. Optional numerical and process mining packages live in `requirements-optional.txt`; they are unnecessary for the demo. The scientific option is diagnostic on generated samples, and PM4Py discovery fitness is not a normative purchasing verdict.

For ERP work, read [the event contract](docs/event-contract.md) and [the isolated pilot protocol](docs/erp-pilot.md). `examples/erp-recorded-events.csv` is a **synthetic contract fixture**, not an Odoo export. The validator rejects dates substituted for recorded timestamps, unsupported reversals, ambiguous mapping, and quantities without one comparable item/unit. No live Odoo execution has been verified. Historical [numbered research notes](docs/04-odoo-execution-protocol.md), [handoff](PROJECT_HANDOFF.md), and the existing promotional video are retained as historical context; their older SQL and transfer/causal language is superseded by the current contract and evidence map. Do not execute the old extraction SQL.
