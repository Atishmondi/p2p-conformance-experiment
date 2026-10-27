# Recorded-event contract and v2 conformance

The lab models a fictional purchasing policy, not a universal accounting rule.
Each case is one comparable product/item and unit. An incomplete export cannot
establish compliance. No timestamps, missing approvals, or quantities are inferred.
The original checker is preserved byte-for-byte at
`src/legacy/check_conformance_v1.py`; checked-in historical CSV results remain v1.

## Input

CSV requires nonblank `case_id`, `activity`, `timestamp`. Optional metadata includes
`scenario`, `resource`, `vendor`, `po_id`, `product_id`, `unit`, `event_id`, and
`invoice_event_id`. Leading and trailing whitespace is removed from case IDs
**before** events are grouped: `x` and ` x ` are one case in v2 outputs and
reports. Blank-after-trimming IDs fail. Event IDs and invoice links are also
trimmed before uniqueness checks and matching.
Missing optional metadata is allowed. Conflicting nonblank product IDs or units
within one case are rejected. Event IDs must be unique across the input; without
an ID, exact duplicate events within a case are rejected.

Timestamps must be ISO datetimes with a time component. Aware timestamps normalize
to UTC; naive timestamps are retained. Mixing aware and naive timestamps within a
case is rejected. Equal timestamps do not imply CSV row ordering.

`qty_ordered`, `qty_received`, and `qty_invoiced` accept finite nonnegative decimal
values; blank/absent means unknown. Malformed, negative, or nonfinite values fail
validation. Decimal arithmetic avoids binary floating-point comparisons.
`qty_received` on **Goods Receipt** is that event's receipt delta;
`qty_invoiced` on **Vendor Invoice** is that event's invoice delta. Values repeated
on other activities are snapshots and do not contribute to totals. The unchanged
lab generators have one receipt and one invoice per case, so their repeated
snapshot columns meet this interpretation without modifying frozen CSV inputs.
Returns, reversals, refunds, credit notes/memos, and cancellation activities are
unsupported and rejected, as are affirmative `is_return`/`is_reversal` flags.

## Rules and evidence

The accepted approval names are `Purchase Request Approval` and
`Purchase Request Approval (re-approval)`.

| Rule | Evaluated policy |
| --- | --- |
| R1 | Every `Purchase Order` has an earlier approval. |
| R2 | Every `Vendor Invoice` has an earlier `Goods Receipt`. |
| R3 | At each invoice timestamp, cumulative invoicing does not exceed received quantity available then. |
| R4 | Every `PO Modification` has a subsequent approval strictly before the next PO. No modifications is evaluated compliance. |
| R5 | Each unlinked `Payment` has an earlier `Vendor Invoice`; a linked payment is compared only with its referenced same-case invoice event. |

`True` is a proven violation, `False` evaluated compliance, and `None` insufficient
evidence. Missing predecessor/target events are unknown; a known predecessor
observed only later proves an ordering violation. A tied predecessor is unknown
when no strictly earlier predecessor exists. R4 without a subsequent PO or any
approval evidence is unknown; known approvals outside the required interval can
prove a violation. Boundary ties cannot establish a reapproval interval.
An optional nonblank `invoice_event_id` on a Payment selects exactly the
same-case `Vendor Invoice` with that `event_id`: invoice earlier than payment
is compliant, invoice later is a violation, and a timestamp tie or unmatched
reference is unknown at the checker boundary. A different earlier invoice
does not make a linked payment compliant. Multiple payment results use the
same proven-violation-over-unknown aggregation as other temporal rules.
Unlinked lab rows retain the any-earlier-invoice rule. The strict ERP export
adapter requires a resolvable same-case invoice link for every Payment and
preserves it in normalized CSV; ordering violations proceed to the checker.

R3 accumulates event deltas through each invoice timestamp. A later receipt never
repairs an earlier excess. Unknown relevant quantities prevent compliance; known
invoice quantities that already exceed every available known receipt can still
prove a violation despite unknown invoice quantities. Same-time receipt ordering
is unknown unless an excess is provable even with all tied receipts available,
or strictly earlier receipts already suffice. Any proven violation wins over
unknown outcomes when combining multiple targets within a rule.

## Python and CLI interfaces

- `load(path) -> dict[str, list[dict]]`: validated, sorted events, with parsed `_ts`
  and Decimal-or-None quantity fields. Invalid input raises `ValueError`.
- `check_case(events) -> (rules, variant, cycle_days, approval_wait,
  receipt_wait, qty_received, qty_invoiced)`: preserves the seven-item tuple.
  Empty traces return unknown rules except R4=False, empty variant, and missing
  performance/quantity values. Quantities are event totals, not first-event values.
- `write_results(cases, output_dir, tag) -> {'conformance': Path, 'summary': Path}`.
- `python3 src/check_conformance.py INPUT --output-dir DIR [--tag TAG]` writes
  `conformance-TAG.csv` and `summary-TAG.csv`; absent tag derives from the input name.

Conformance CSV columns:
`case_id,scenario,variant_short,violations,cycle_days,qty_received,qty_invoiced,not_evaluable,status,rule_version`.
`violations` contains semicolon-separated proven rule failures; only fully
compliant cases use `OK`. `not_evaluable` lists unknown rules. `status` is
`violating` if any rule fails, otherwise `not_evaluable` if any rule is unknown,
otherwise `compliant`. Version is `v2`. Missing scalar values serialize blank.

Summary CSV retains scenario, case count, conformance rate, cycle/wait aggregates,
and `R1_viol` through `R5_viol`. It adds `compliant`, `violating`, `not_evaluable`,
`evaluated_cases`, `rule_version`, and `R1_not_evaluable` through
`R5_not_evaluable`. Status cohorts are mutually exclusive; evaluated_cases is
compliant + violating. Conformance rate is compliant / evaluated_cases, blank
when that denominator is zero. Unknown rules on a violating case remain visible
in the per-rule unknown counts. Never infer compliance from an empty failure list.

## Isolated experiments

`python3 src/run_manager.py --n 2 --era both --seed 17 --tag example` uses
`output/experiments/` by default, leaving historical `data/runs.csv` untouched.
The generated root is ignored by Git. Add `--output-dir DIR` to select another
root. Under that root, the command reserves a fresh `runs/example/`, writes event logs and checker outputs
directly there, and appends era records to `runs.csv` at the root. It never writes or
backs up canonical outputs. A duplicate tag fails without modifying that run.
Tags are safe single path components; n must be positive. Default tags combine
UTC microseconds and a random suffix. Explicit seeds yield identical event,
conformance, and summary bytes across roots; timestamps/run IDs in registries
are execution metadata. Failures retain the reserved partial run for inspection.
An existing incompatible registry is rejected with a concise CLI error before
reserving a tag or generating artifacts; use a fresh output root.

A portable standard-library directory lock (`DIR/.runs.lock`) serializes registry
validation, initialization, run generation, and appends for all eras in one
invocation. A competing invocation fails explicitly as busy before reserving a
tag or generating artifacts; retry after the active run finishes. Normal exits
and exceptions release the lock. Process termination may leave a stale lock:
after verifying that no run is active, remove the empty `.runs.lock` directory
before retrying. Locks are never automatically stolen. The same serialization
protects direct `run_era` calls; their caller must first reserve the run directory.

Registry columns:
`run_id,utc_time,era,n_per_scenario,seed,cases,events,viol_rate,mean_cycle,compliant,violating,not_evaluable,evaluated_cases,rule_version`.
`viol_rate` is violating / evaluated_cases (blank with no evaluated cases).

`noise_test.py --input INPUT --output-dir DIR` uses the same checker without
copied fallback logic or pandas. Seeded stdlib drop sampling produces a v2
diagnostic; its samples need not match historical pandas sampling. Recall/FPR
exclude unknown cases and report `target_evaluated,target_not_evaluable,
s1_evaluated,s1_not_evaluable` alongside `noise_level,seed,recall,fpr,rule_version`.
A wholly dropped case is unknown, never a manufactured false positive.

## Frozen baseline comparison

| Input | Version | Violating cases | R1 | R2 | R3 | R4 | R5 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Round 1 | v1 | 60 / 120 | 0 | 20 | 20 | 20 | 0 |
| Round 1 | v2 | 60 / 120 | 0 | 20 | 40 | 20 | 0 |
| Round 2 | v1 | 0 / 60 | 0 | 0 | 0 | 0 | 0 |
| Round 2 | v2 | 0 / 60 | 0 | 0 | 0 | 0 | 0 |

V2 also flags R3 for S3 invoices preceding receipts. The case totals remain the
same; per-rule totals do not. These are generated cohorts, not operational or
causal evidence of savings.
