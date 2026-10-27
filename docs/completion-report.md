# Completion report

This project is a reproducible purchase-to-pay portfolio demonstration. Its value for an information-systems or technology-consulting portfolio is the connection between process rules, imperfect records, explainable exceptions, and a defensible investigation. It is not evidence of deployed ERP controls, operational detection accuracy, or financial savings.

## Delivered

- Versioned v2 rules use event-time cumulative quantities, explicit unknown outcomes, normalized case identities, exact invoice links when supplied, and isolated runs; v1 remains reproducible.
- Reports derive counts from supplied artifacts. Dashboard builds reject stale verdicts that contradict event traces, and distinguish original source hashes from sanitized downloadable copies.
- A standard-library demo builds a static viewer with case traces, field strata, rule explanations and local source downloads. No raw XES or optional numerical packages are required.
- A strict ERP export contract checks action codes, recorded timestamps, item/unit grain and source relationships. Unsafe extraction SQL fails explicitly; the example export is labeled synthetic.
- Concise README, investigation/business case, claim/evidence map, portable tests and CI configuration replace the old presentation as the current entry point. Historical research notes and the user's original edits remain preserved in history.

## Evidence and boundaries

The final implementation passed all 66 tests on both Python 3.9 and 3.12, with no skips or optional packages used for the core suite. The raw field reanalysis reproduced all 251,734 case rows byte-for-byte. See [verification](verification.md), [task review records](reviews/README.md), and [council decisions](council-review.md).

Live Odoo execution remains unverified: Docker had no running daemon, and starting the existing Colima runtime was denied by local permissions. Desktop/mobile rendering remains unverified: the browser rejected local-file URLs. Initial loopback binding was denied, but the existing HTTP integration test passed in the resumed environment. No screenshots, hosted CI results, production validation or control-effect claims are made. Static bundle data, links and hashes were checked independently.

The highest-value next evidence is a small audited Odoo pilot using the [recorded-event protocol](erp-pilot.md), followed by independently labeled cases and an assessment of investigation effort. Fixture tests do not substitute for that work. No new promotional video, raw XES redistribution, push or deployment is included.

## Delivery

Work is kept on the local `codex/p2p-completion` branch. The original moved checkout remains untouched; the delivery is a separate checkout plus source archive. Follow [README](../README.md) to generate and serve a fresh demo. Use a new output directory for each run. The whole-branch review found three issues; all were fixed and independently accepted in the [final scoped review](reviews/final-rereview.md). The delivery checks are recorded in [verification](verification.md).

The completed checkout is `p2p-delivery/p2p-conformance-experiment` inside the Default Project folder. The adjacent `p2p-completion-delivery.zip` contains the portable source. The final independent review accepted all fixes; 66 tests pass on both supported verification environments. Every scope decision and its tradeoff is preserved in [Rulings made during completion](reviews/decisions.md).
