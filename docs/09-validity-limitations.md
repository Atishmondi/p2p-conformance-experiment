# Validity Threats and Limitations

> **Historical research note (superseded for current execution and claims).** This document retains its original analysis for provenance. Use [the current claim/evidence map](claim-evidence.md), [event contract](event-contract.md), and [ERP pilot](erp-pilot.md) for current limits and next steps. Old extraction SQL, causal/transfer wording, and hard-enforcement predictions here are not an executable or verified path; do not run the historical SQL.


This study is a controlled laboratory experiment with perfect ground truth by construction. The reported effects therefore measure checker correctness and configuration enforcement under controlled conditions, not diagnostic accuracy under operational uncertainty. Threats are organised following the construct–internal–external–conclusion validity taxonomy.

## 1. Construct validity: does R1–R5 measure compliance?

The normative model (six steps; R1–R5, see `docs/01-normative-model.md`) operationalises compliance as ordering constraints (R1, R2, R5), an attribute constraint (R3, tolerance 0), and a rework constraint (R4). Real P2P compliance additionally includes authorisation limits, segregation of duties, partial receipts, tolerances, and credit-note workflows, which this model deliberately reduces to binary rules. Temporal deviation is operationalised as mean transition delay without practitioner-agreed service-level thresholds.

Mitigations. (i) Each rule is traced explicitly to a scenario and an expected log signature (`docs/05-findings-r1.md`); (ii) rule and performance perspectives are reported separately, so slowness (S2, S5) cannot inflate non-compliance counts — S2/S5 are conformant by rule and deviant only in throughput; (iii) the zero-tolerance R3 setting is documented as an experimental design choice, not a general prescription, and its real-world counterpart is examined as a value-match proxy with explicit falsifiers in `docs/07-real-dataset.md`.

## 2. Internal validity: is the Round-1 to Round-2 reduction causal?

Cases were executed under controlled conditions with fixed master data (3 vendors, 5 products with weighted quantities), an identical schema across rounds, and a scripted scenario protocol (20 cases per scenario). Labels are perfect by construction: each deviation was injected deliberately, so the 60/60 Round-1 detection rate measures checker correctness against known ground truth. The Round-2 elimination (0/60) could in principle reflect generator artefacts rather than control effectiveness.

Mitigations. (i) A frozen checker (`src/check_conformance.py`) is applied identically to Round 1 (120 cases) and Round 2 (60 cases) with no rule edits between rounds; (ii) stochastic generation is seeded and fixed (seed 42 for Round 1, seed 7 for Round 2) with documented business-hours and lognormal-wait parameters (see `docs/10-appendix.md`, Section E), so the only systematic difference between targeted cohorts is the enforced redesign (billing block, quantity cap, re-approval gate); (iii) a drop-noise sweep (`src/noise_test.py`; levels 0, 0.02, 0.05, 0.10 × seeds 1, 2, 3, in-memory only) tests checker brittleness: mean recall on S3/S4/S6 remains ≥ 0.97 at all levels, but mean false-positive rate on S1 breaks down already at 2% noise (0.050, 0.200, 0.100 → mean 0.117, exceeding the 10% threshold; 0.233 at 5%, 0.500 at 10%). The causal claim is therefore conditional on log completeness: under missing events the same checker produces spurious violations.

## 3. External validity: does the lab transfer to real P2P?

The experiment uses synthetic data, a single team, and Odoo Community. This limits generalisation to multi-actor operations and enterprise systems (e.g. SAP) with configurable tolerances, partial receipts, backdated documents, off-system approvals, and workaround behaviour. The Round-2 result (0/60 violations) demonstrates that the enforced configuration blocks the injected paths in this set-up; it does not establish effectiveness under adversarial or noisy field conditions.

Mitigations. An external check against the BPIC 2019 purchase-order-handling log is documented in `docs/07-real-dataset.md` (76,349 documents; 251,734 line-item cases; 1,595,923 events; 42 activities). The mapping shows that all deviation families are attested in the field (maverick buying ≈ 56% of 2-way items; PO-change rework ≈ 2.15% with +7 days throughput penalty; 1,704 invoice-before-receipt sequences despite after-GR policy; payment-block removal in ≈ 26% of after-GR cases), with a stratified 500-case sampling plan and three explicit falsifiers (R2 ordering without cost; routine R3 deltas without correction; persistent R4 rework under enforced gates) that would overturn the lab's transfer claim if observed.

## 4. Conclusion validity: do the statistics support the inference?

With 60/60 vs 0/60, any standard test rejects the null; the risk is overstating precision (zero cells, perfect separation) and conflating discovery metrics with normative conformance.

Mitigations. (i) The primary comparison is reported with complementary tests: chi-square without Yates correction (χ² = 120, p = 6.3e-28) for the headline effect, Fisher exact two-sided (p = 2.1e-35, odds ratio inf) as the exact test appropriate to zero cells, Wilson 95% score intervals per rate ([0.940, 1.000] vs [0.000, 0.060]), and Cohen h = 3.14 for magnitude (see `docs/10-appendix.md`, Section D; values from `data/evaluation.csv`); (ii) throughput is tested independently of compliance via a Welch two-sample t-test on per-case cycle times (S1 mean 7.18d vs S2 mean 10.03d; t = −6.94, df = 37.15, p = 3.3e-08; Cohen d = 2.19), cross-checked against `data/summary-r1.csv`; (iii) vendor stratification (40 cases each; violation rates 0.475–0.525 with overlapping Wilson intervals) checks that no single vendor drives the result; (iv) PM4Py metrics are scoped correctly (see Non-claims below) and never substituted for the hypothesis test.

## 5. What this study does NOT claim

- It does not claim that Odoo Community results generalise to SAP or other ERP systems without replication.
- It does not claim real-world detection precision/recall; perfect labels and fixed master data preclude such inference, and the noise sweep shows false positives exceed 10% already at 2% missing events.
- It does not claim that zero violations in Round 2 imply zero residual risk, nor that hard blocks are cost-free (S6R cycle 9.19d vs S6 8.04d; +1 day re-approval overhead by design).
- It does not claim that temporal delays (S2/S5) are unimportant; they are classified as tolerable variation only relative to the stated rule set, pending SLA validation.
- It does not claim that the reported PM4Py fitness of 1.0 measures normative compliance. Fitness 1.0 (precision 0.98) is computed against the *discovered* inductive-miner Petri net, which by construction accommodates the observed variants — hence per-scenario alignment fitness is also 1.0. The normative test is the frozen R1–R5 rule checker; PM4Py provides discovery, variant, and diagnostic triangulation only.
