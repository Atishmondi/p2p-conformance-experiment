# Control investigation brief

## Decision and scope

A purchasing analyst needs to distinguish provable exception, insufficient event evidence, and acceptable delay before proposing a workflow change. This artifact makes that investigation reproducible for a portfolio reviewer. It does not validate a production control, diagnose an organization, or price a product.

| Evidence | Observation | Decision boundary |
|---|---|---|
| Generated lab, seeds 42/7, n=20 per scenario | 60/120 first-round cases violate; 0/60 second-round cases violate under the fictional v2 policy. | Deliberately designed traces show checker behavior. No random assignment, operational accuracy estimate, or causal savings claim. |
| Historical field summary | 590/1,044 two-way maverick proxy hits; 1,584/11,128 monetary-worth proxy hits in the after-GR stratum. | Separate activity and value definitions; do not compare these rates directly to lab approval and quantity rules. |
| ERP contract fixture | Recorded-action validation and checker smoke work on synthetic sample rows. | Installed Odoo controls, action instrumentation, and live transaction outcomes are unverified. |

## Investigation path

1. Select a scenario in the generated bundle and inspect the trace, status, each rule's evaluated count and unknown outcomes. Read the source CSV where a row's timing or delta is disputed.
2. Reconcile an exception with the intended policy and the recorded action source. Look for missing approvals, quantities, exact item/unit identity, event order, and cutoff before labeling it a control failure. Do not convert unknown into compliant.
3. Inspect the field stratum separately. Its applicable count may be much smaller than all cases, and its proxy may observe a different act altogether. A structural false can mean only that a signature was impossible in that stratum.
4. Pilot a proposed control with preregistered attempts, independent source-record verification, and explicit counters for blocked, posted, unsupported and unobserved outcomes. The [pilot protocol](erp-pilot.md) and [event contract](event-contract.md) define this next evidence step.

## Cost scenario framework

If a buyer later estimates exception-review labor, document local case volume, minutes of manual evidence review, fully loaded rate, potential false positives, and intervention cost. Compute a range only from measured organization-specific inputs. No monetary value is assigned here: case frequency, true loss, review time and proposed control side effects have not been measured in an operation. False positives can delay legitimate procurement; false negatives can leave a bypass undetected. A transparent unknown category can improve triage without proving savings.

## Limitations

The policy is fictional and has no practitioner endorsement. Laboratory cases are generated from scenario designs; field observations are filtered historical proxies with applicability differences, incomplete cases and censoring at the date boundary. No operational precision, recall, savings, or causal intervention effect follows. The raw XES is excluded and its exact redistribution license remains unverified. Existing promotional video is historical, not evidence of this build.
