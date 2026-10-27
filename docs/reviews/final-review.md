# Final whole-branch review — 8293e29..800b29a

**Verdict: fixes requested before delivery.** The branch is close to the specified portable demonstration, but two input/relationship errors can produce misleading case outcomes. This is a source and integration review, not a live ERP, browser, or field-validity certification. Review included the spec, plan, ledger, verification and completion records, source diff, current checker/run manager/reporting/adapter/viewer code, tests, CI and README. Targeted in-memory/temporary-file reproductions below; no full suite, raw XES rerun, browser, server, or Docker retry.

## Strengths

- The v1 checker and historical results remain identifiable; v2 makes unknown rules and evaluated denominators explicit. Independent fixtures cover cumulative quantities, timestamp ties, invalid inputs and preserved canonical files.
- The normal demo builds without site packages or raw XES; generated summaries and viewer provenance derive from artifacts. Dashboard publication checks v1/v2 verdict agreement, and bundle downloads distinguish original input from transformed public bytes.
- The ERP contract fails closed on missing recorded action metadata, unsupported action codes and invalid quantity grain. The fixture and pilot text explicitly avoid presenting simulated records as live Odoo evidence.
- Portable tests and CI use the same standard-library verification command. Previous reviews document completed fixes and remaining runtime boundaries.

## Critical

None identified.

## Important

1. **`src/check_conformance.py:112-113`, `:53-59`, `:239-248` — whitespace-normalized case IDs split one trace into two cases.** `load()` groups events by the raw CSV `case_id`, while `normalize_events()` strips that value afterward. In a temporary CSV containing an approval under `x` and its PO under ` x `, `load()` returns two cases, both R1=`None`; checking their combined normalized trace returns R1=`False`. `write_results()` publishes two rows (`x` and ` x `) with inflated case counts and unknown outcomes. Group by the normalized case ID at load time, or reject input whose raw IDs collide after normalization. Add a literal regression showing the approval and PO belong to one case and preserve duplicate event-ID validation.

2. **`src/validate_erp_export.py:92-96`, `src/check_conformance.py:208-214` — R5 ignores the explicit invoice relationship in audited exports.** The adapter requires `invoice_event_id` and only checks that it refers to an invoice in the same case. The checker accepts *any* earlier invoice. A valid-format export with an invoice on January 6, a payment on January 7 linked to another invoice on January 8, is accepted by `validate_export()` and reports R5=`False` (compliant). This conflicts with the pilot's exact invoice mapping and lets a known payment-before-linked-invoice case appear clean. For source-linked rows, evaluate R5 against the referenced invoice event, with equal-time/absent evidence tri-state handling; alternatively reject a linked invoice that is not strictly earlier in the adapter and document how that failure enters results. Add a two-invoice fixture; keep ordinary lab R5 semantics where no explicit link exists.

## Minor

1. **`src/compare_lab_field.py:87-90` — a null optional stratum raises an unhandled `AttributeError`.** A summary containing `"three_way_strata": null` fails at `.get('after')`; the CLI catches `ValueError`/`OSError`, so readers see a Python traceback rather than explicit unavailable data or a clear validation error. Normalize null to an unavailable stratum or reject it with `ValueError`. Check `by_item_category` similarly before calling `.items()`.

## Recommendations

- Address the two Important findings together, then run focused fixtures and the project verification command. Refresh generated dashboard artifacts only if the accepted changes affect the checked-in sample.
- State in the delivery record that the HTTP check was skipped in the earlier restricted run but passed in the controller's newer 60-test Python 3.9/3.12 verification. Keep browser rendering and live Odoo execution explicitly unverified.

## DECLINED TO JUDGE

- **Live Odoo behavior, instrumented action authenticity, payments and operational control accuracy:** no running daemon, recorded pilot source trail or independently labeled outcomes were available. The adapter proves CSV shape and relationships only.
- **Desktop/mobile browser rendering and visual usability:** local-file navigation was rejected by browser policy; passing HTTP fetch tests do not establish rendering. No policy workaround was attempted.
- **Raw field provenance, license and operational transfer:** the historical BPI summary was separately reanalyzed in the verification record, but this review did not rerun the 728 MB XES, audit underlying source records or equate monetary proxies with synthetic item-quantity rules.
- **Causal impact, savings and external generalizability:** designed generated cohorts cannot support those claims; the branch appropriately avoids them.
- **Hosted CI execution and cross-process failure recovery beyond the documented lock behavior:** static workflow and tests were inspected; no hosted run or forced process-kill experiment was performed.
