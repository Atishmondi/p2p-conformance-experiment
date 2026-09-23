# ERP Experiment Protocol — Odoo Community Transferability (H8 Preregistration)

**Status: PROTOCOL ONLY — no Odoo executed, no results recorded, no claim made.**
**Owns-only: this file (`docs/17-erp-experiment-protocol.md`). Does not implement Odoo, does not modify controls, does not write `data/hypothesis_erp_mapping.csv`.**
**Gate: `docs/04-odoo-execution-protocol.md` §6 (hypotheses-first gate) + `src/signatures.py` + `SCOPE_NOTES` + `docs/16-research-audit.md` open items (D1–D5, F1–F6). Order is mandatory: preregister → execute → extract → detect → verify → compare to field base rates → only then modify + rerun.**
**H8 status: OPEN and stays open until field/ERP intervention is measured. Lab 60/60→0/60 (seeds 42/7) licences only pilot hypotheses.**

Preregistration date: TBD (fill before first Odoo step).
Detector freeze: `src/check_conformance.py::check_case` version/commit TBD (fill before execution; no post hoc tuning).
Run record location: TBD.

---

## 1. Research question (H8 transferability frame)

**RQ-H8:** Do the lab-demonstrated hard controls — S3R billing block (R2), S4R quantity cap (R3), S6R re-approval gate (R4) — enforce the same normative signatures when implemented at the **recording stage** of Odoo Community 17 Purchase/Inventory/Invoicing, under the 6-step P2P scope below, and under what scope/tolerance conditions do they fail to transfer?

Sub-questions (each maps to one ERP-adapted hypothesis in §4; H8 itself is the frame, not a per-arm claim):

- H1-ERP: does Odoo enforce approval-before-PO order when approval is bypassed?
- H2-ERP: does Odoo reproduce the S3 latent-vs-recorded gap — i.e., does a vendor-early bill become a recorded-early violation, or does Odoo's recording gate absorb it (field lesson: 5754/15182 vendor-early → 0/11128 recorded-early)?
- H3-ERP: does Odoo enforce invoiced ≤ received, and at what tolerance (lab tol-0 vs field 14.2% routine deltas)?
- H5/H6-ERP: does Odoo distinguish qty/price rework (R4 violation) from routine approval workflow (excluded, field 1000/1044 approval-change in 2-way vs 10/1044 rework)?
- H7-ERP (monitored only): is payment-before-invoice rare in Odoo as in lab (0/120) and field (408/251734 = 0.0016)?

Non-question (explicitly out of scope): whether these controls *should* be deployed in production, whether they preserve flexibility/SLA, whether they generalise beyond Odoo Community P2P. Those require separate SLA validation, tolerance sweep, and field pilot — all proposed-only per audit D1/D4/D5, none run here.

Language rule for this file and any future results: every efficacy sentence must carry cohort + denominator + condition (e.g., "0/20 S3R under lab/recorded-timestamp definition"). Bare "eliminates violations" is forbidden (audit G1–G7).

---

## 2. ERP scope

### 2.1 In scope

- **System:** Odoo Community 17, single company, single DB `p2p-exp`, via `docker compose` per `docs/04-odoo-execution-protocol.md` §1. Modules: Purchase, Inventory, Invoicing only.
- **Normative 6-step flow** (maps to BPMN, identical to 04 §3):
  1. `Purchase Request` (requester)
  2. `Purchase Request Approval` (approver_1/2, 2-step)
  3. `Purchase Order` confirm — RFQ → PO (buyer)
  4. `Goods Receipt` — Inventory → Receipts → Validate (warehouse)
  5. `Vendor Invoice` (Vendor Bill with Bill control, accountant)
  6. `Payment` — Register Payment (accountant)
- **Masters (fixed, per 04 §2):** 3 vendors (Vendor_A/B/C), 5 storable+purchaseable products (P-01..P-05), roles requester/approver_1/approver_2/buyer/warehouse/accountant, 1 purchase team, 2-step approval. Rotation round-robin for comparability.
- **Stratum:** Odoo configured as **3-way-after-GR** only (GR-Based Invoice Verification = true; bill control blocks Validate before receipt in S3R arm only — control arm leaves default). This is the R2+R3 stratum per `SCOPE_NOTES`. All rule evaluations use this stratum unless a hypothesis explicitly states otherwise.
- **Arms:** control S1–S6 (20 cases/scenario = 120) + intervention S3R/S4R/S6R (20 each = 60), staggered starts, same masters, per 04 §4. S2/S5 are slow-but-compliant performance arms; rule-silent, no intervention.

### 2.2 Explicit exclusions (not tested, not claimed)

1. No multi-company, no multi-currency, no custom valuation, no dropship/3-way-before-GR config, no service/non-storable products.
2. No 2-way (no-GR-gate) Odoo arm — therefore no direct maverick-buying replication; H1 is adapted to approval-order only (§3, H1 reason).
3. No credit-note, partial-receipt, tolerance-calibrated, or approval-SLA/delegation workflows (out-of-model by design; audit D1/D5). Tolerance sweep is a separate future trial.
4. No vendor-portal / EDI latent timestamps unless manually recorded as `occurred_*` (see §5.2); default analysis uses system recording timestamps only.
5. No S2/S5 delay-threshold or SLA intervention (audit D1, intentionally out of scope).
6. No live vendor-action enforcement claim: interventions target **recording/validation stage** only (field transferability constraint, audit F2). Any "blocks early billing" claim means "blocks *recording* early billing."
7. No production deployment, no cost-benefit, no residual-risk-zero claim (audit §C non-claims).
8. No redefinition of R1–R5: lab definitions frozen in `src/signatures.py:9-58`; field proxies listed for comparison only, not re-tested here.

---

## 3. H1–H8 ERP-testability classification

| H | Rule/track (CSV status) | ERP-testable? | Reason |
|---|---|---|---|
| H1 (R1, supported — 590/1044 = 0.5651 in 2-way only) | **Adapted-testable** | Odoo has no 2-way arm, so maverick-buying proxy (vendor acts before PO) cannot be replicated. Adapt to testable construct: approval-order (PR Approval ts < PO confirm ts) which Odoo *does* enforce via 2-step approval. Field 2-way rate quoted for comparison only. |
| H2 (R2, nuanced — lab S3 20/20 = 1.0 vs field after-GR 0/11128 = 0.0) | **Directly testable (priority: recording-gate)** | Core transferability risk. Odoo S3 injection (create/validate Bill before Validate receipt) directly tests whether Odoo reproduces lab pattern or field recording-gate absorption. Requires dual timestamps (§5.2). Falsifier A applies. |
| H3 (R3 after-GR, supported-as-proxy — lab 20/20 = 1.0 vs field 1584/11128 = 0.1423, tol-0 REFUTED) | **Directly testable (priority)** | Odoo S4 injection (bill qty = receipt qty + 2/5) tests qty rule at tol-0. Field analogue is value-delta proxy; magnitude gap (−0.8577) and correction-given-viol 0.1572 must be cited alongside any Odoo rate. Tolerance-0 is lab norm only, not a prescription (audit G9). |
| H4 (R3 before-GR, supported — field 0/199564 structural zero) | **Not testable in this protocol** | Structural near-zero by definition (no GR reference at invoice time). Odoo configured as after-GR only (§2.1); no before-GR arm is executed. Any before-GR reading would be vacuity, not enforcement (audit P8). |
| H5 (R4 qty/price rework, nuanced — lab 20/20 = 1.0 vs field 26366/251734 = 0.1047, above F2 base 0.0215) | **Directly testable (priority)** | Odoo S6 injection (edit qty/vendor post-approval, confirm without re-approval) tests `PO-Modification → Approval → PO` pattern. Attribution gap applies: lab −100% fix does not imply field excess is behavioural (audit E-contradiction 3). |
| H6 (R4-exclusion, supported — 2-way approval 1000/1044 = 0.9579 vs rework 10/1044 = 0.0096) | **Testable as negative control** | Odoo approval-step changes (`Change Approval`-equivalent: approver reassignment / approval-state transitions) must NOT fire R4. Probe-equivalent check required; naive any-change definition inflates ~50× in 2-way and is forbidden (audit G8). |
| H7 (R5, supported — lab 0/120, field 408/251734 = 0.0016, rarity < 0.01) | **Monitored only, not intervened** | Lab contributed no signal; Odoo arm records R5 passively in all scenarios. No S-arm injects early payment; no R-design arm. Confirms rarity threshold only. |
| H8 (redesign lab→field, open — lab 60/60 → 0/60, field UNTESTED) | **Frame, stays open** | This protocol *is* the H8 preregistration for the Odoo step. Odoo S3R/S4R/S6R outcomes, when measured, constitute ERP-transfer evidence only — not field/SAP generality. Until rerun + field-base comparison are recorded, H8 remains open. |

**Selected for per-hypothesis protocol (§4): H1-adapted, H2, H3, H5, H6 (as exclusion check), H7 (monitored). H4 excluded with reason above. H8 is the frame.**

---

## 4. Per-selected-hypothesis protocol

Common control parameters (all hypotheses): 20 cases/arm, staggered +5h starts, business-hours clock, fixed masters §2.1, extract per §6 schema, detect with frozen `check_case` (R1–R5), verify observed-vs-latent per signature (§4 gate step 5). Applicable-n excludes `None` (missing ts or wrong stratum). Report `n_viol / n_applicable` + overall anchor `n_viol / n_arm`.

Field base rates for comparison-before-redesign (gate step 6, do not quote pooled R3 alone): R1 590/1044 = 0.5651 2-way (overall 3450/251734 = 0.0137 for context); R2 0/11128 = 0.0 after-GR; R3 1584/11128 = 0.1423 after-GR (before-GR 0/199564 structural; pooled 1584/210692 = 0.0075 do-not-quote-alone); R4 corrected qty/price 26366/251734 = 0.1047 (approval-change 4290/251734 tracked separately, approval-only 3301/251734); R5 408/251734 = 0.0016.

### H1-ERP (R1 approval order — adapted)

- **Baseline (S1):** full 6-step flow in order; PR → Approval (≤1d) → PO confirm. Predicted: 0/20 R1 violations, 0/20 any-targeted.
- **Injection (S6-adjacent negative + dedicated H1 probe, n = 20):** confirm PO *before* PR Approval completes (or with approval skipped if Odoo permits via access-rights test user). Same masters; record whether Odoo blocks or warns.
- **Signature (`src/signatures.py` R1):** `lab_definition`: first Approval ts < first PO ts else violation. `event_pattern`: `Purchase Request Approval → Purchase Order`. `known_gap`: lab tests approval order, not maverick buying; absent-invoice-as-False N/A in Odoo (no vendor-invoice-before-PO proxy here).
- **Detection:** `check_case` R1 on recorded timestamps. `None` only if PO ts missing.
- **Intervention (no new R-design arm for H1):** existing 2-step approval is the control; if bypass succeeds, record as control gap — do NOT hot-fix mid-batch. Any approval-hardening proposal goes to a future preregistered arm, not this protocol.
- **Rerun:** n/a (no H1 redesign arm in 04 §4).
- **Outcome (preregistered, TBD):** `r1_viol / n_applicable` in probe arm; S1 FP `0/20` expected. Table in §8.
- **Falsifier:** n/a (no H1 falsifier band). Verdict options: enforced (0/20 viol when bypass attempted → blocked) / gap (≥1/20 bypass succeeds). Either verdict leaves 2-way maverick claim untouched.

### H2-ERP (R2 receipt-before-invoice + recording gate — priority)

- **Baseline (S1):** PO → Goods Receipt Validate → Vendor Bill Validate → Payment. Predicted: 0/20 R2 violations; PO→Receipt ≈ 2d.
- **Injection (S3, n = 20):** create Bill (enter vendor bill date = vendor-occurred-ts) *before* Validate receipt, then attempt Validate bill before Validate receipt. Record BOTH timestamps: `vendor_bill_date` (occurred, manual) and `bill_validate_ts` (recorded, system). This dual capture is the S3-lesson requirement (§5.2).
- **Signature (R2):** `lab_definition`: first Goods Receipt ts < first Vendor Invoice ts else violation. `event_pattern`: `Goods Receipt → Vendor Invoice`. `known_gap`: recording-vs-vendor-action nuance; unblocked nuance tracked (violation + any GR ts > first invoice ts = blocked-then-cleared).
- **Detection:** `check_case` R2 on **recorded** timestamps (`receipt_validate_ts` vs `bill_validate_ts`); needs both else `None`. Occurred timestamp (`vendor_bill_date`) is mechanism covariate only, never the verdict input.
- **Intervention (S3R, n = 20):** enable Bill control / "control billing with receipts" so Validate bill is blocked until receipt validated. Same masters, same extract-detect-verify.
- **Rerun outcome (preregistered, TBD):** control S3 `viol/applicable` (lab-synthetic anchor 20/20 = 1.0; Odoo value TBD) → S3R `viol/applicable`; absolute reduction; conformance rate. Compare to field after-GR 0/11128 BEFORE claiming relevance: if Odoo-control S3 fires but field stratum is 0/11128, S3R targets a non-problem in that stratum (audit E-contradiction 1) — record FLAG, do not drive field-control recommendation.
- **Falsifier A (R2 rate vs lab 16.7% anchor, band 0.10–0.25):** if Odoo S3 recorded-violation rate falls inside band → consistent-with-lab; if ≈ 0 with vendor-early present (occurred < receipt but recorded > receipt) → recording-gate absorption replicated (partial-contradiction of naive lab→field transfer, mechanism confirmed); cost/delay comparison null-null → INCONCLUSIVE on cost, do not claim savings.

### H3-ERP (R3 invoiced-within-received — priority)

- **Baseline (S1):** receipt qty = ordered qty; bill qty = receipt qty. Predicted 0/20 R3 violations.
- **Injection (S4, n = 20):** receipt qty = ordered; bill qty = ordered + 2 (half the arm) / + 5 (half). Attempt Bill Validate. Record `qty_ordered / qty_received / qty_invoiced` + unit price + net worth for field-proxy comparability.
- **Signature (R3):** `lab_definition`: `qty_invoiced ≤ qty_received` else violation. `event_pattern`: qty fields on Goods Receipt / Vendor Invoice. `known_gap`: qty-lab vs value-proxy-field (EUR net worth, epsilon 0.01); only after-GR falsifiable.
- **Detection:** `check_case` R3 on qty fields (tol-0). `None` if either qty missing. Separately compute value-delta (`bill_net − po_net > 0.01`) as comparison covariate, not verdict.
- **Intervention (S4R, n = 20):** quantity cap / over-billing block (bill qty capped at received; over-bill raises blocking exception). Same conditions.
- **Rerun outcome (preregistered, TBD):** S4 `viol/applicable` (anchor 20/20) → S4R `viol/applicable`; absolute reduction. Compare to field after-GR 1584/11128 = 0.1423 + correction-given-viol 0.1572: S4R tol-0 enforcement is NOT calibrated to field (14.2% routine mass) — record as lab-norm enforcement, not field prescription, unless tolerance-sweep arm is separately preregistered.
- **Falsifier B (zero-tolerance in both 3-way strata):** REFUTED as general norm (field after-GR 0.1423 > 0 with mass above 1.0/10.0 EUR, probe-confirmed non-rounding). Odoo tol-0 result therefore cannot be quoted as "correct tolerance" — only as "tol-0 enforcement under lab/Odoo conditions." Before-GR arm n/a (H4 excluded).

### H5-ERP (R4 no-unapproved-modification, qty/price — priority)

- **Baseline (S1):** no PO modification post-approval. Predicted 0/20 R4 violations.
- **Injection (S6, n = 20):** approve → change qty or vendor/price → confirm PO *without* re-approval. Log `PO-Modification` event with actor + old/new values.
- **Signature (R4):** `lab_definition`: every PO Modification must be followed by an Approval event before PO else violation. `event_pattern`: `PO-Modification → Approval → Purchase Order`. `known_gap`: `Change Approval`-equivalent EXCLUDED (see H6).
- **Detection:** `check_case` R4. `None` only if PO ts missing; cases with no modification → `False` (applicable and conformant).
- **Intervention (S6R, n = 20):** re-approval gate: any post-approval qty/vendor/price change resets approval state; PO cannot confirm until re-approved. Record overhead: cycle duration S6R vs S1 baseline AND vs S6 (two baselines — do not collapse to bare "+1d"; audit F5/G11).
- **Rerun outcome (preregistered, TBD):** S6 `viol/applicable` (anchor 20/20) → S6R `viol/applicable`; absolute reduction; duration penalty with both baselines + source lines.
- **Falsifier C (rework vs F2 base 0.0215, band 0.0015–0.0415):** REFUTED-on-rate (field corrected 0.1047 above base), NUANCED-on-attribution (case-definition + line-item-grain + date-filter non-identity unresolved). Odoo −100% therefore does NOT establish field behavioural excess or cost-benefit. Record delay penalty without re-estimated field counterpart.

### H6-ERP (R4-exclusion — negative control, runs inside H5 arms)

- **Baseline/injection:** same S1/S6/S6R cases as H5. No separate n.
- **Signature:** approval-workflow events (approver reassignment, approval-state transitions, `Change Approval`-equivalent) are NOT `PO-Modification` for R4 purposes.
- **Detection:** `check_case` R4 must return `False` for approval-only changes; separate counter `approval_change_after_po` (informational). Probe-equivalent: tally qty-change / price-change / approval-change separately per arm.
- **Intervention/rerun:** none; passes if S6R re-approval gate does not convert routine approvals into violations and S1 shows 0/20 R4 with approvals present.
- **Outcome (preregistered, TBD):** approval-change count vs qty/price-rework count per arm; R4 FP on approval-only must be 0.
- **Falsifier C-approval-exclusion:** supported if approval mass ≫ rework mass (field analogue 1000/1044 vs 10/1044) and exclusion holds in Odoo. If Odoo conflates them, record as detector-config defect, not as R4 violation mass.

### H7-ERP (R5 payment-after-invoice — monitored only)

- **Baseline/injection:** none. All S1–S6/S3R/S4R/S6R cases passively monitored.
- **Signature (R5):** `lab_definition`: first Payment ts > first Vendor Invoice ts else violation. `event_pattern`: `Vendor Invoice → Payment`. `known_gap`: lab Payment ≈ cash outflow; Odoo Register Payment vs field Clear Invoice differ — state which is used (here: Register Payment ts).
- **Detection:** `check_case` R5; needs invoice + payment ts else `None`.
- **Intervention/rerun:** none preregistered.
- **Outcome (preregistered, TBD):** `r5_viol / n_applicable` across all arms; rarity threshold < 0.01 (field 408/251734 = 0.0016; lab 0/120).
- **Falsifier:** rarity threshold only. No signal expected; any hit triggers case-level verify before any claim.

### H8 frame (verdict rule)

H8 remains **open** after Odoo control arms until ALL of: (a) S3R/S4R/S6R reruns recorded with pre/post `viol/applicable` + absolute reduction, (b) lab-to-field/Odoo-to-field base-rate comparison recorded (§4 gate step 6 + §7 metrics), (c) FLAGs on S3-absent / tolerance-0 / R4-attribution recorded. Odoo transfer verdict options preregistered: **transferred** (intervention eliminates recorded violations under identical conditions with zero S1 FP and no schema/None-rate anomaly) / **mechanism-confined** (eliminates only recorded-stage pattern while occurred-stage mass persists — the S3-gate outcome) / **not transferred** (violation persists or exclusion fails). "Transferred" means Odoo-recording-stage only, never SAP/field generality.

---

## 5. Event-log contract

### 5.1 Schema (column-for-column; reject exports that do not match)

| Column | Type | Odoo source | Required | Semantics |
|---|---|---|---|---|
| `case_id` | string | Purchase Request / PO origin (one PR → one PO → one case; split POs = new case_ids with `parent_case` in notes) | yes | Stable across 6 steps; 20/arm. |
| `activity` | enum | Step mapping §2.1 | yes | One of `Purchase Request`, `Purchase Request Approval`, `Purchase Order`, `PO-Modification`, `Goods Receipt`, `Vendor Invoice`, `Payment`. `PO-Modification` logged on any post-approval qty/vendor/price edit with actor. |
| `timestamp` | ISO-8601, tz-aware | **Recorded** ts by default (see §5.2) | yes | System recording time; rule verdicts use this column only. |
| `timestamp_occurred` | ISO-8601, tz-aware | Vendor bill date / GR scheduled date (manual entry) | conditional (mandatory in S3; optional elsewhere) | Latent/occurred time; mechanism covariate only, never verdict input. |
| `timestamp_kind` | enum | `recorded` / `occurred` / `both` | yes | Labels which semantics each row carries; verdict pipeline reads `recorded` only. |
| `resource` | string | `create_uid` / validator (`requester`, `approver_1/2`, `buyer`, `warehouse`, `accountant`) | yes | Actor at Validate/Create, not assignee. |
| `vendor` | enum | `res.partner` | yes | Vendor_A/B/C rotated round-robin. |
| `po_id` | string | `purchase.order` name | yes | Links modification + receipt + bill. |
| `receipt_id` | string | `stock.picking` name | yes when receipt exists | GR validation batch. |
| `invoice_id` | string | `account.move` (Vendor Bill) name | yes when bill exists | Bill validation batch. |
| `qty_ordered` | number | PO line qty | yes post-PO | Ordered reference. |
| `qty_received` | number | Validated picking qty | yes post-GR | Received reference. |
| `qty_invoiced` | number | Validated bill qty | yes post-Bill | Invoiced test value (S4 injects +2/+5). |
| `net_ordered` / `net_invoiced` | number (EUR) | PO net / Bill net | yes post-PO/Bill | Field-proxy comparability (value-delta covariate). |
| `source` | enum | `odoo-export` / `manual-entry` | yes | `manual-entry` only for `timestamp_occurred` + S6 modification old/new values; all verdict columns must be `odoo-export`. |
| `scenario` | enum | Run record | yes | S1–S6 / S3R / S4R / S6R. |
| `condition` | enum | `control` / `intervention` | yes | S1–S6 = control; S3R/S4R/S6R = intervention. |
| `doc_order_seq` | integer | Export order per case | yes | Document-order fallback audit trail; disagreements with ts flagged, ts prevails for verdict. |

### 5.2 Timestamp semantics (S3 latent-vs-recorded lesson — read before extracting)

Field lesson (audit E13 + E-contradiction 1): after-GR **vendor-early** (`Vendor Creates Invoice` < GR) occurred in 5754/15182 cases, yet **recorded-early** (`Record Invoice Receipt` < GR) occurred in 0/11128 applicable; D1 16356 all before-GR / 0 after-GR; D2/D4 89 each all before-GR; D3 1009 with 0 after-GR; probes 0/40 invoice<GR, 0/39 clear<GR. The recording gate absorbs latent earliness. Quoting vendor-action timestamps as system violations conflates mechanism with verdict (audit F4: 1704-definition ambiguity).

Odoo analogue: vendor sends bill (occurred, `vendor_bill_date` / paper date) vs accountant validates bill (recorded, `bill_validate_ts`); goods arrive (occurred, `scheduled_date`) vs warehouse validates receipt (recorded, `date_done`/`write_date`). Therefore:

1. **Verdict rule:** R2/R5 timing rules evaluate **recorded-vs-recorded** only (`bill_validate_ts` vs `receipt_validate_ts`; `payment_ts` vs `bill_validate_ts`). This matches `src/signatures.py` R2/R5 `lab_definition` + `known_gaps` (recording-vs-vendor-action nuance).
2. **Mechanism rule:** every S3 case records both `timestamp` (recorded) and `timestamp_occurred` (vendor bill date). Analysis reports the 2×2: occurred-early × recorded-early. Gate absorption = occurred-early with recorded-conformant.
3. **Missing-ts rule:** if either recorded ts is missing → R2/R5 = `None` (not applicable), never `False`. Doc-order fallback is logged (`doc_order_seq`) and flagged when it disagrees with timestamps; timestamps prevail.
4. **Stratum rule:** R2 evaluated only in after-GR stratum (all Odoo cases here); R3 reported with after-GR label; before-GR structural zero not imported.
5. **Citation rule:** any "early invoice" sentence must state which timestamp (vendor/occurred vs recorded) — ambiguous citation is a protocol violation.

---

## 6. Control-vs-intervention design

- **Control (R1 equivalent):** S1 (compliant baseline, n = 20) + S2/S5 (performance arms, n = 20 each, rule-silent) + S3/S4/S6 injections (n = 20 each). Total control N = 120. Expected: 60/60 targeted violations (S3→R2, S4→R3, S6→R4), 0/20 S1 FP, 0 R1/R5 targeted.
- **Intervention (R2 equivalent):** S3R (billing block) + S4R (qty cap) + S6R (re-approval gate), n = 20 each, N = 60, same masters, same staggered starts, same extract-detect-verify chain. Expected under lab synthetic anchor: 0/60 violations (abs_reduction = 1); Odoo values TBD — expectation is not a result.
- **Randomisation/rotation:** vendors × products round-robin (40 cases/vendor across R1 in lab; preserve rotation in Odoo); staggered +5h case starts to avoid batch artefacts.
- **Freezes:** detector version frozen before execution; masters frozen; no mid-batch control changes (gate step 2). Any deviation = protocol violation, arm discarded.

### 6.1 Metrics (report all, per arm and pooled intervention)

1. `violation_count` and `violation_rate = n_viol / n_applicable` per rule + `applicable_n` + overall anchor `n_viol / n_arm`.
2. `None`-rate (missing-ts / wrong-stratum share) — anomaly signal, not conformance.
3. `duration`: case cycle time (PR → Payment recorded ts) + leg durations (PR→Approval, PO→Receipt, Receipt→Bill); report median + IQR; S6R overhead with BOTH baselines (S1 and S6) + source.
4. `variants`: distinct activity-order variants per round (lab R1: 3 variants; R2: V1 + 8-event S6R chain — compare structurally, not as conformance).
5. `conformance`: targeted-cohort conformance = 1 − pooled targeted `viol/applicable` (S3/S4/S6 pooled pre vs S3R/S4R/S6R pooled post) + absolute reduction + relative reduction. Statistics (chi2/Fisher/Wilson/Cohen h) only if preregistered test plan is added; default is descriptive rates with denominators.
6. Comparison deltas: Odoo-control rate − field base rate per rule (R2 vs 0/11128; R3 vs 1584/11128; R4 vs 26366/251734; R1-adapted vs n/a with 2-way 590/1044 as context only).

### 6.2 Stopping / rejection criteria

- STOP and discard arm if: export schema ≠ §5.1 column-for-column; >10% rows missing recorded ts; S1 FP > 0/20 without assignable cause (triggers detector/masters audit, not threshold tuning); mid-batch control/master change detected; `source = manual-entry` appears in any verdict column.
- FLAG (continue but block field-control recommendation) if: lab-deviation-absent-in-field pattern (Odoo S3 fires while field after-GR = 0/11128); tolerance-0 enforcement would block >5% of S1-like compliant bills (calibration warning); approval-only changes fire R4 (exclusion failure).
- No interim efficacy lookups drive stopping; no threshold tuning post hoc. Stopping is for integrity, not for significance.

---

## 7. Threats to validity

- **Construct:** R1-lab (approval order) ≠ R1-field (maverick proxy); R3-lab (qty tol-0) ≠ R3-field (value-delta proxy); R2/R5-lab (system ts) vs field (recording ts) vs Odoo (validate ts) — each gap per `known_gaps`. Mitigation: quote rule + timestamp-kind + stratum in every result sentence; H1 labelled adapted; H4 excluded; H6 exclusion enforced.
- **Internal:** operator learning across arms (later cases faster/cleaner); batch effects (same-day validates); master drift (vendor/product substitution); mid-batch config edits. Mitigation: staggered starts, rotation, frozen masters/detector, run-record change log; any violation of freeze discards the arm.
- **External:** Odoo Community 17 single-config ≠ SAP / other ERPs / production Odoo (custom valuation, multi-company, EDI, tolerances). Lab→Odoo transfer ≠ field generality (H8 stays open; audit §C non-claims: no SAP generality, no adversarial/noisy-field effectiveness, no residual-risk zero, no SLA validity).
- **Data:** synthetic stand-in risk until live export replaces rows (README/E3); manual `timestamp_occurred` entry error; doc-order vs ts disagreement; stratum misassignment (before- vs after-GR). Mitigation: §5.1 `source` column, dual-ts 2×2, `None`-rate reporting, column-for-column rejection.
- **Measurement:** checker brittleness — recall ≥ 0.97 but FPR 0.117 at 2% noise, 0.233 at 5%, 0.50 at 10% (audit E11); PM4Py fitness/precision are discovery-diagnostics, not normative conformance (audit E10) — do not report them as verdicts. Mitigation: completeness-conditional claims only; normative verdict from frozen `check_case` alone.
- **Reproducibility:** `/tmp` probes ephemeral (audit F4); S6R overhead baseline ambiguity (8.0 vs 7.0 / 9.19 vs 8.04 — audit F5/G11); R4 denominator variants (25197/236192 vs 26366/251734 — cite `docs/11` corrected figure). Mitigation: §8 run record with versions, seeds/starts, full denominators, both S6R baselines; no `/tmp` citations; independent re-scan required for 1704 closure (out of scope here).

---

## 8. Reproducibility procedure + preregistration record (fill BEFORE results)

Backbone order (04 §6, 9 steps): 1 define (§2 + R1–R5) → 2 signatures (frozen) → 3 execute → 4 extract (`sql/odoo_extract.sql` → §5.1) → 5 detect (frozen `check_case`) → 6 verify (observed vs latent per signature) → 7 modify (only after field-base comparison) → 8 rerun → 9 measure (lab delta + field-base comparison, FLAG untransferred fixes).

Preregistration table (copy H1–H8 from `data/hypotheses.csv`, add Odoo prediction; `status` stays preregistered until rerun + comparison recorded):

| hypo_id | rule | predicted Odoo signature | lab anchor | field base | status |
|---|---|---|---|---|---|
| H1-ERP | R1-adapted | bypass-attempt blocked; S1 0/20 R1 | n/a (no 2-way lab arm) | 590/1044 = 0.5651 context only | preregistered |
| H2-ERP | R2 | S3 recorded-early fires; S3R 0/20 recorded; occurred-vs-recorded 2×2 recorded | S3 20/20 = 1.0 (anchor 20/120) | 0/11128 after-GR | preregistered |
| H3-ERP | R3 | S4 fires at tol-0; S4R 0/20 | S4 20/20 = 1.0 | 1584/11128 = 0.1423 (tol-0 refuted) | preregistered |
| H5-ERP | R4 | S6 fires without re-approval; S6R 0/20 + overhead vs both baselines | S6 20/20 = 1.0 | 26366/251734 = 0.1047 | preregistered |
| H6-ERP | R4-excl | approval-only → R4 False; 0 FP | n/a (S6 is qty/price) | approval 1000/1044 vs rework 10/1044 | preregistered |
| H7-ERP | R5 | <0.01 rare, monitored | 0/120 | 408/251734 = 0.0016 | preregistered |
| H8 | redesign | Odoo pre→post TBD; stays OPEN | 60/60 → 0/60 lab | n/a UNTESTED | open |

Run record fields (mandatory before execution): prereg date, detector commit, Odoo version/image hash, masters hash, arm start times, extract script hash, `None`-rates, verify log (observed vs latent per hit), field-base comparison sheet, FLAG sheet.

Results section: **INTENTIONALLY EMPTY — no Odoo executed under this protocol at time of writing. No outcome, no verdict, no H8 closure recorded here.**
