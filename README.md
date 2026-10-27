# Purchase-to-Pay Conformance Experiment

**Did a business follow its own purchasing rules?**

This project reads the recorded steps of a purchase, checks them against five example rules, and shows which cases need a closer look. It includes a Python checker, a browser dashboard, generated test cases, and a separate analysis of historical purchasing data.

*Purchase-to-pay (P2P)* means the journey from asking to buy something to paying the supplier. *Conformance checking* means comparing what happened with what the rules say should happen.

## A simple example

Imagine an office buying 10 chairs. Its expected process is:

1. Someone asks for the chairs.
2. A manager approves the request.
3. The office places an order.
4. The chairs arrive.
5. The supplier sends a bill.
6. The office pays.

Now suppose only **6 chairs have arrived**, but the supplier bills for **10**. Or the office places its order before approval. The checker uses the recorded events to flag these situations, and the dashboard lets you inspect the sequence behind the result.

If an important record is missing, the result can be **unknown**. Missing evidence should not quietly become a pass.

## What it checks

These five rules define a fictional policy for this experiment; organizations can have different purchasing policies.

| Rule | Question |
|---|---|
| R1 · Approval | Was each purchase order preceded by an approval? |
| R2 · Receipt | Was each invoice preceded by a goods receipt? |
| R3 · Quantity | At each invoice, had enough items arrived to cover everything billed so far? |
| R4 · Changes | After an order modification, was there another approval before the next purchase-order event? |
| R5 · Payment | Did the invoice come before payment? When an invoice link is supplied, was that exact invoice earlier? |

Each rule can be **compliant**, **violating**, or **unknown**. The dashboard shows counts, durations, example event sequences, and downloadable records so you can inspect the evidence behind a result.

## Try it locally

You need **Python 3.9 or newer**. The core demo requires no package installation, database, or Odoo setup.

From the project folder, run:

```sh
python3 -S src/demo.py --output-dir output/my-first-demo
python3 -m http.server 8000 --bind 127.0.0.1 --directory output/my-first-demo/webpage
```

Open **[localhost:8000](http://localhost:8000)**. Keep the terminal running; press `Ctrl+C` when finished.

Compare the two rounds, select a case, and inspect its events and rule results.

Use a **new output folder** for another run. Add `--n 5` for a smaller demo or `--without-field` to omit the historical summary. Use the HTTP server above; double-clicking `index.html` can prevent data from loading.

## Where the data comes from

| Part | What it contains | What it tells us |
|---|---|---|
| Generated lab | Repeatable purchasing scenarios, including deliberately broken rules | Whether the checker responds correctly to those examples |
| Historical field analysis | An included BPI Challenge 2019 summary covering 251,734 cases | How selected patterns appear in historical purchasing records |
| ERP preparation | A strict event-export validator, synthetic sample, and Odoo pilot protocol | What records a future live pilot needs to provide |

The default lab has **60 violating cases out of 120 in Round 1**, and **0 out of 60 in Round 2**. These outcomes come from deliberately designed scenarios. They do not measure a real company's improvement or prove financial savings.

Field checks use different definitions and eligible groups: its invoice comparison uses **monetary worth**, while the lab uses **item quantities**. Keep their percentages separate.

The raw XES event-log file is unnecessary for the demo and excluded from this repository. Its redistribution license has not been verified.

## How it works

Python generates example event logs, checks each case, and builds the reports. A static HTML/CSS/JavaScript dashboard reads the generated results.

| Location | Purpose |
|---|---|
| `src/check_conformance.py` | Current v2 rules and input validation |
| `src/demo.py` | Builds a complete isolated demo |
| `src/build_dashboard.py` | Checks result consistency and assembles the viewer |
| `src/validate_erp_export.py` | Validates recorded ERP events and source relationships |
| `webpage/` | Dashboard and an included sample bundle |
| `tests/` | Rule, reporting, export, and portability tests |
| `docs/` | Research notes, evidence boundaries, and pilot instructions |

Historical v1 results remain reproducible; new results are versioned. Download hashes identify source files, and dashboard builds reject verdicts that disagree with their event logs.

<details>
<summary><strong>After editing a generated event log</strong></summary>

Regenerate the matching conformance file, then rebuild the dashboard. For a changed Round 1 log:

```sh
python3 -S src/check_conformance.py output/my-first-demo/event-log-r1.csv --output-dir output/my-first-demo --tag r1
python3 -S src/build_dashboard.py --data-dir output/my-first-demo --out output/my-first-demo/dashboard.json --site-dir output/my-first-demo/webpage
```

For Round 2, use `event-log-r2.csv` and `--tag r2`. If both logs changed, run both checker commands before rebuilding. Refresh the browser afterward.

For your own data, follow the [event contract](docs/event-contract.md): required columns, quantities, timestamps, invoice links, and unsupported events.

</details>

## Verification and next step

Run the tests with:

```sh
./scripts/verify.sh
```

**66 tests passed on Python 3.9 and 3.12**, including HTTP bundle checks; see the [verification record](docs/verification.md). CI uses the same command. Hosted CI execution and desktop/mobile rendering remain unverified. Optional scientific packages are in `requirements-optional.txt`.

**Next: an audited live Odoo pilot.** The ERP sample is synthetic; live transactions, operational accuracy, and savings remain unverified.

For a business or technology-consulting discussion, the useful question is: **what happened, which rule does it conflict with, and what evidence should an analyst inspect before recommending a change?**

- [Business case and investigation workflow](docs/business-case.md)
- [Claims and supporting evidence](docs/claim-evidence.md)
- [ERP pilot protocol](docs/erp-pilot.md)
- [Completion report](docs/completion-report.md)

Older research notes and promotional material are historical. For ERP work, use the current pilot protocol; the unsafe old extraction SQL has been retired.
