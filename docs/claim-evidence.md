# Claim to evidence map

| Claim | Reproduce or inspect | Limit |
|---|---|---|
| v2 rule statuses are tri-state and source-derived | `src/check_conformance.py`, `tests/test_conformance.py`; generated `conformance-r*.csv` and dashboard rule denominators | Fictional policy, source evidence required; unknown is not clean. |
| Default lab sample has 60/120 versus 0/60 case violations | Run `python3 -S src/demo.py --output-dir output/new-demo`; `dashboard.json` cohort overall summaries and source hashes | Deliberately generated, unrandomized cohorts; no business efficacy or savings estimate. |
| A report updates when a supplied artifact changes | `tests/test_portability.py`, `src/build_dashboard.py`; checker regeneration and rebuild commands in README | Event edits require matching versioned conformance; mismatches fail before publishing. |
| Historical BPI proxies retain independent applicable counts | `data/bpic2019_results.json`, `src/compare_lab_field.py`, dashboard Field stratum selector | Field R3 worth is not lab R3 quantity; activity mappings, cutoff and incomplete cases limit meaning. |
| UTC raw reanalysis preserves the prior case CSV/counts on this source | [verification record](verification.md); `src/analyze_bpic2019.py` | Raw 728 MB XES is excluded from portable demo; historical summary remains versioned separately. |
| ERP export boundary validates recorded action rows | `src/validate_erp_export.py`, `tests/test_erp_export.py`, `examples/erp-recorded-events.csv`, `docs/event-contract.md` | Fixture is synthetic; no Odoo transactions/audited enforcement verified. |
| Static viewer is portable and sources match hashes | `tests/test_portability.py`; `./scripts/verify.sh`; generated `webpage/artifacts/` | HTTP check requires loopback permission; URLs reflect the bundle, not a raw XES download. |

The older numbered documents and PROJECT_HANDOFF record historical interpretations. Their hard enforcement predictions, transfer language, SQL extraction, and cached statistics are superseded by the current payload, [business case](business-case.md), [event contract](event-contract.md), and [ERP pilot](erp-pilot.md). PM4Py discovery fitness is not normative compliance.
