"""Single-source-of-truth signatures for the 9-step P2P backbone, R1-R5.

Lab = src/check_conformance.py::check_case (synthetic log).
Field = src/analyze_bpic2019.py::evaluate_case (BPI 2019 XES proxies).
Stdlib only. Standalone: no imports from other src files.
"""
from copy import deepcopy

SIGNATURES = {
    "R1": {
        "name": "R1 approval-before-PO / maverick-buying proxy",
        "lab_definition": "First Purchase Request Approval ts < first Purchase Order ts; else violation.",
        "field_proxy": "min('Vendor creates invoice') < min('Create Purchase Order Item'); absent vendor invoice = False, None only if PO ts missing.",
        "applicable_scope": "Lab: all cases. Field: 2-way stratum only (F1-style denominator = all 2-way cases).",
        "event_pattern": "Lab: Purchase Request Approval -> Purchase Order. Field: Vendor creates invoice vs Create Purchase Order Item.",
        "known_gaps": "Lab tests approval order; proxy tests maverick buying (vendor acts before PO). Absent-invoice-as-False is a scope choice, not a pass.",
    },
    "R2": {
        "name": "R2 receipt-before-invoice / after-GR-only proxy",
        "lab_definition": "First Goods Receipt ts < first Vendor Invoice ts; else violation.",
        "field_proxy": "First 'Record Invoice Receipt' < first 'Record Goods Receipt'; needs both timestamps, else None.",
        "applicable_scope": "Lab: all cases. Field: 3-way-after-GR only (Item Cat has after+gr, or 3-way + GR-Based true).",
        "event_pattern": "Lab: Goods Receipt -> Vendor Invoice. Field: Record Goods Receipt vs Record Invoice Receipt.",
        "known_gaps": "Recording-vs-vendor-action nuance: field compares recording times, not physical receipt vs vendor send. Unblocked nuance tracked: violation + any GR ts > first invoice ts (blocked-then-cleared).",
    },
    "R3": {
        "name": "R3 invoiced-qty-within-received / value proxy",
        "lab_definition": "qty_invoiced <= qty_received (first GR / first invoice qtys); else violation.",
        "field_proxy": "max worth at 'Record Invoice Receipt' > PO worth at first 'Create Purchase Order Item' + 0.01; None if either missing.",
        "applicable_scope": "Lab: all cases. Field: 3-way only, reported for both after-GR and before-GR strata.",
        "event_pattern": "Lab: qty fields on Goods Receipt / Vendor Invoice. Field: Cumulative net worth at Create PO Item vs Record Invoice Receipt.",
        "known_gaps": "Qty lab vs value-proxy field (EUR net worth, EPSILON=0.01). Before-GR stratum is a structural near-zero (no GR gate at invoice time), so only after-GR is falsifiable.",
    },
    "R4": {
        "name": "R4 no-unapproved-modification / qty-price-only rework",
        "lab_definition": "Every PO Modification must be followed by a re-approval (any 'Approval' event) before PO; else violation.",
        "field_proxy": "Any 'Change Quantity'/'Change Price' with ts > 'Create Purchase Order Item' ts; None if PO ts missing.",
        "applicable_scope": "Lab: cases with PO Modification. Field: all PO-bearing cases (False when PO exists and no later Qty/Price change).",
        "event_pattern": "Lab: PO Modification -> Approval -> Purchase Order. Field: Change Quantity / Change Price after Create Purchase Order Item.",
        "known_gaps": "'Change Approval for Purchase Order' EXCLUDED from R4 (routine approval workflow, not rework; probe: 57/60 2-way vs Quantity 0/60, Price 1/60). Tracked separately as approval_change_after_po.",
    },
    "R5": {
        "name": "R5 payment-after-invoice / clear-after-record",
        "lab_definition": "First Payment ts > first Vendor Invoice ts; else violation.",
        "field_proxy": "No 'Clear Invoice' -> False; Clear without 'Record Invoice Receipt' -> True; else min(Clear) < min(Record), doc-order fallback.",
        "applicable_scope": "Lab: all cases. Field: all cases (both definitions need invoice + payment/clear present).",
        "event_pattern": "Lab: Vendor Invoice -> Payment. Field: Record Invoice Receipt -> Clear Invoice.",
        "known_gaps": "Lab Payment ~ cash outflow; field Clear Invoice ~ clearing doc. Missing-ts fallback uses document order, which can disagree with timestamps.",
    },
}

SCOPE_NOTES = (
    "Scopes via Item Category + GR-Based Inv. Verif.: 2-way (no GR gate, R1 stratum); "
    "3-way-after-GR (invoice verified after GR, R2+R3 stratum); "
    "3-way-before-GR (invoice before GR, R3-only, structural near-zero). "
    "None = not applicable (missing PO/GR/invoice ts or wrong stratum); "
    "False = applicable and conformant."
)


def describe(rule):
    """Return a copy of the signature dict for R1..R5 (KeyError otherwise)."""
    if rule not in SIGNATURES:
        raise KeyError("unknown rule %r; expected one of R1..R5" % (rule,))
    return deepcopy(SIGNATURES[rule])


def _fmt(rule, sig):
    lines = ["[%s] %s" % (rule, sig["name"])]
    for k in ("lab_definition", "field_proxy", "applicable_scope",
              "event_pattern", "known_gaps"):
        lines.append("  %s: %s" % (k, sig[k]))
    return "\n".join(lines)


if __name__ == "__main__":
    for r in ("R1", "R2", "R3", "R4", "R5"):
        print(_fmt(r, SIGNATURES[r]))
        print()
    print("SCOPE: " + SCOPE_NOTES)
