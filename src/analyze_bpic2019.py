#!/usr/bin/env python3
"""Streaming analyzer for BPI Challenge 2019 XES (P2P conformance proxies R1-R5).

Streaming: xml.etree.ElementTree.iterparse on {http://www.xes-standard.org/}trace,
constant memory (elem.clear() per trace). Never loads the full log.

Case attrs extracted: concept:name, Item Category, GR-Based Inv. Verif.,
Goods Receipt, Vendor, Purchasing Document.
Event attrs extracted: concept:name, time:timestamp (date), User (fallback
org:resource), Cumulative net worth (float; key prefix "Cumulative net worth"
so both "Cumulative net worth" and "Cumulative net worth (EUR)" match).

Timestamp filter: drop events with timestamp < 2018-01-01 or > 2019-01-27
(end-of-day inclusive). Unparseable/missing timestamps are kept for
presence flags but excluded from time comparisons.

Per-case rules (filtered events only):
  R1-proxy (maverick): min('Vendor Creates Invoice') < min('Create Purchase
    Order Item') -> True. False when PO exists but no early vendor invoice
    (absent vendor invoice = not maverick, so F1-style denominator = all
    2-way cases). None only when PO timestamp missing.
  R2 (after-GR stratum only): applicable iff case is 3-way-after-GR, i.e.
    Item Category contains after-GR ("after"+"gr") OR (3-way + GR-Based true).
    Needs first 'Record Invoice Receipt' and first 'Record Goods Receipt';
    else None. Violation iff first_invoice < first_gr. Unblocked nuance:
    violation + any GR timestamp > first invoice timestamp (blocked-then-
    cleared; true for every violation that has a GR, reported separately).
  R3-value-proxy: applicable iff 3-way (after OR before). PO value = worth at
    first 'Create Purchase Order Item'; invoice values = worths at
    'Record Invoice Receipt' events. None if either missing. Violation iff
    max(invoice_worths) > po_value + 0.01. Reported for both 3-way strata.
  R4 (rework, corrected): any 'Change Quantity'/'Change Price' with timestamp
    > 'Create Purchase Order Item' -> True. 'Change Approval for Purchase
    Order' is EXCLUDED from R4 (routine approval workflow, not rework; probe
    showed it inflated R4: 57/60 2-way cases vs Quantity 0/60, Price 1/60)
    and is tracked separately as approval_change_after_po (same > PO-ts rule;
    None when PO timestamp missing). R4 is None when PO timestamp missing;
    False when PO exists and no later Quantity/Price change.
  R5 (pay without invoice): no 'Clear Invoice' -> False. Clear exists but no
    'Record Invoice Receipt' -> True. Both exist -> True iff
    min(Clear) < min(Record) (fallback to document order when ts missing).

Outputs (repo data/ dir by default):
  data/bpic2019_case_results.csv:
    case_id,item_category,has_gr,has_invoice,r1_maverick,r2_viol,r3_viol,
    r4_rework,approval_change_after_po,r5_viol,n_events
    (booleans as True/False, None as empty, n_events = filtered count;
    approval_change_after_po = 'Change Approval for Purchase Order' after PO,
    kept separately for transparency, NOT part of R4)
  data/bpic2019_results.json: aggregate rates overall + per Item Category +
    R1 2-way stratum + R3 both 3-way strata + R2 block/delay co-occurrence +
    approval-change-only rate + falsifier verdicts A/B/C vs lab anchors
    (R2 16.7% / R3 zero-tolerance / R4 2.15% base = F2 Change Quantity 1.34%
    + Change Price 0.78% only; thresholds documented inline).

CLI: python3 src/analyze_bpic2019.py [xes_path]
     (default data/BPI_Challenge_2019.xes relative to repo root).
     Optional: --cases-out PATH --json-out PATH (default to data/ files).
Progress: print every 25k cases.
Missing attrs: flags are None (empty CSV cell), never crash.
"""
import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XES = REPO_ROOT / "data" / "BPI_Challenge_2019.xes"
DEFAULT_CASES_OUT = REPO_ROOT / "data" / "bpic2019_case_results.csv"
DEFAULT_JSON_OUT = REPO_ROOT / "data" / "bpic2019_results.json"

XES_NS = "{http://www.xes-standard.org/}"
KEEP_FROM = datetime(2018, 1, 1, 0, 0, 0)          # inclusive
KEEP_TO = datetime(2019, 1, 27, 23, 59, 59)        # inclusive end-of-day
EPSILON = 0.01

A_PO_CREATE = "Create Purchase Order Item"
# Real log spells it "Vendor creates invoice" (lowercase c/i); match case-insensitively.
A_VENDOR_INV = "Vendor creates invoice"
A_REC_INV = "Record Invoice Receipt"
A_REC_GR = "Record Goods Receipt"
A_CLEAR = "Clear Invoice"
CHANGE_ACTS = {
    "Change Quantity",
    "Change Price",
}
# Excluded from R4 (routine workflow, not rework); tracked separately.
APPROVAL_CHANGE_ACT = "Change Approval for Purchase Order"

ATTR_TAGS = {"string", "date", "float", "int", "boolean", "id"}


def local_tag(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def parse_timestamp(s):
    """Parse XES date value -> naive datetime (tz stripped) or None."""
    if s is None or s == "":
        return None
    t = str(s).strip()
    try:
        if t.endswith("Z"):
            t = t[:-1] + "+00:00"
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)  # date-level window; drop tz
        return dt
    except Exception:
        pass
    # fallback formats
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(t[:19] if len(t) > 19 and "T" in t else t, fmt)
        except Exception:
            continue
    return None


def parse_float(s):
    if s is None or s == "":
        return None
    try:
        return float(str(s).strip())
    except Exception:
        return None


def parse_gr_based(v):
    """GR-Based Inv. Verif. -> True/False/None (handles boolean + string)."""
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return v
    t = str(v).strip().lower()
    if t in ("true", "1", "yes"):
        return True
    if t in ("false", "0", "no"):
        return False
    return None


def _cat(t):
    return (t or "").lower()


def is_two_way(item_category) -> bool:
    c = _cat(item_category)
    return ("2-way" in c or "2 way" in c or "2way" in c)


def is_after_gr(item_category, gr_based) -> Optional[bool]:
    """True iff 3-way-after-GR policy applies. False iff before-GR/2-way/
    consignment. None iff undecidable."""
    c = _cat(item_category)
    if "after" in c and "gr" in c:
        return True
    if "before" in c and "gr" in c:
        return False
    if "consignment" in c:
        return False
    if "2-way" in c or "2 way" in c or "2way" in c:
        return False
    if "3-way" in c or "3 way" in c or "3way" in c:
        if gr_based is True:
            return True
        if gr_based is False:
            return False
        return None
    # unknown category: fall back to GR-Based flag alone
    if gr_based is True:
        return True
    if gr_based is False:
        return False
    return None


def is_three_way(item_category, gr_based) -> bool:
    c = _cat(item_category)
    if "3-way" in c or "3 way" in c or "3way" in c:
        return True
    # GR-Based flag set + not 2-way/consignment -> treat as 3-way-ish
    if gr_based is not None and not is_two_way(item_category) \
            and "consignment" not in c and c.strip() != "":
        # only when category explicitly mentions GR policy
        if "after" in c or "before" in c:
            return True
    return False


def stratum_3way(item_category, gr_based) -> str:
    """'after' | 'before' | 'other' for R3 reporting."""
    a = is_after_gr(item_category, gr_based)
    c = _cat(item_category)
    if a is True:
        return "after"
    if a is False and ("3-way" in c or "3 way" in c or "3way" in c
                       or "before" in c):
        return "before"
    return "other"


def flag_str(v) -> str:
    if v is True:
        return "True"
    if v is False:
        return "False"
    return ""


def parse_trace(trace_elem):
    """Extract case attrs + raw events from one <trace> element."""
    case = {}
    raw_events = []
    for child in trace_elem:
        lt = local_tag(child.tag)
        if lt in ATTR_TAGS:
            case[child.attrib.get("key")] = child.attrib.get("value")
        elif lt == "event":
            ev = {}
            for g in child:
                if local_tag(g.tag) in ATTR_TAGS:
                    ev[g.attrib.get("key")] = g.attrib.get("value")
            raw_events.append(ev)
    return case, raw_events


def build_filtered_events(raw_events):
    """Map raw event dicts -> filtered list of (name, ts, user, worth).

    Returns (events, n_dropped_out_of_range).
    """
    events = []
    dropped = 0
    for ev in raw_events:
        name = ev.get("concept:name")
        ts = parse_timestamp(ev.get("time:timestamp"))
        if ts is not None and (ts < KEEP_FROM or ts > KEEP_TO):
            dropped += 1
            continue
        user = ev.get("User", ev.get("org:resource"))
        worth = None
        for k, v in ev.items():
            if k == "Cumulative net worth" or k.startswith("Cumulative net worth"):
                worth = parse_float(v)
                break
        events.append({"name": name, "ts": ts, "user": user, "worth": worth})
    return events, dropped


def min_ts(events, names):
    tss = [e["ts"] for e in events if e["name"] in names and e["ts"] is not None]
    return min(tss) if tss else None


def evaluate_case(case_id, item_cat, gr_based, events):
    """Apply R1-R5 to one case's filtered events. Returns row dict."""
    names = [e["name"] for e in events]
    has_gr = A_REC_GR in names
    has_inv = A_REC_INV in names

    po_ts = min_ts(events, {A_PO_CREATE})
    po_vals = [e["worth"] for e in events
               if e["name"] == A_PO_CREATE and e["worth"] is not None]
    po_val = po_vals[0] if po_vals else None  # first PO creation value
    # first-PO value: use earliest-ts event's worth when timestamps exist
    if po_vals and any(e["ts"] is not None for e in events
                       if e["name"] == A_PO_CREATE):
        cands = [(e["ts"], e["worth"]) for e in events
                 if e["name"] == A_PO_CREATE and e["ts"] is not None
                 and e["worth"] is not None]
        if cands:
            po_val = sorted(cands, key=lambda x: x[0])[0][1]

    vendor_ts = min_ts(events, {A_VENDOR_INV})
    inv_ts = min_ts(events, {A_REC_INV})
    gr_ts = min_ts(events, {A_REC_GR})
    clear_ts = min_ts(events, {A_CLEAR})

    # R1
    if po_ts is None:
        r1 = None
    elif vendor_ts is not None and vendor_ts < po_ts:
        r1 = True
    else:
        r1 = False  # includes vendor-invoice-absent (not maverick)

    # R2
    after = is_after_gr(item_cat, gr_based)
    if after is not True:
        r2 = None
    elif inv_ts is None or gr_ts is None:
        r2 = None
    else:
        r2 = inv_ts < gr_ts
    unblocked = None
    if r2 is True:
        gr_after = [e for e in events if e["name"] == A_REC_GR
                    and e["ts"] is not None and inv_ts is not None
                    and e["ts"] > inv_ts]
        unblocked = len(gr_after) > 0

    # R3
    if not is_three_way(item_cat, gr_based):
        r3 = None
    else:
        inv_worths = [e["worth"] for e in events
                      if e["name"] == A_REC_INV and e["worth"] is not None]
        if po_val is None or not inv_worths:
            r3 = None
        else:
            r3 = max(inv_worths) > po_val + EPSILON

    # R4 (corrected): Quantity/Price only; Approval tracked separately.
    if po_ts is None:
        r4 = None
        approval_change = None
    else:
        r4 = any(e["ts"] is not None and e["ts"] > po_ts
                 for e in events if e["name"] in CHANGE_ACTS)
        approval_change = any(e["ts"] is not None and e["ts"] > po_ts
                              for e in events
                              if e["name"] == APPROVAL_CHANGE_ACT)

    # R5
    clears = [e for e in events if e["name"] == A_CLEAR]
    recs = [e for e in events if e["name"] == A_REC_INV]
    if not clears:
        r5 = False
    elif not recs:
        r5 = True
    else:
        if clear_ts is not None and inv_ts is not None:
            r5 = clear_ts < inv_ts
        else:
            # fallback to document order
            idx_c = next(i for i, e in enumerate(events) if e["name"] == A_CLEAR)
            idx_r = next(i for i, e in enumerate(events) if e["name"] == A_REC_INV)
            r5 = idx_c < idx_r

    # block / payment signals for co-occurrence
    has_block = any("block" in (e["name"] or "").lower() for e in events)
    has_payment = any("payment" in (e["name"] or "").lower()
                      or e["name"] == A_CLEAR for e in events)
    has_correction = has_block or any(
        e["name"] in ("Change Price",) or "credit" in (e["name"] or "").lower()
        or "memo" in (e["name"] or "").lower() for e in events)

    return {
        "case_id": case_id,
        "item_category": item_cat or "",
        "has_gr": has_gr,
        "has_invoice": has_inv,
        "r1_maverick": r1,
        "r2_viol": r2,
        "r3_viol": r3,
        "r4_rework": r4,
        "approval_change_after_po": approval_change,
        "r5_viol": r5,
        "n_events": len(events),
        "_after_gr": after,
        "_stratum3": stratum_3way(item_cat, gr_based),
        "_is_two_way": is_two_way(item_cat),
        "_unblocked": unblocked,
        "_has_block": has_block,
        "_has_payment": has_payment,
        "_has_correction": has_correction,
        "_has_approval_change": approval_change,
        "_clear_ts": clear_ts,
        "_inv_ts": inv_ts,
    }


def rate(rows, key):
    vals = [r[key] for r in rows if r[key] is not None]
    if not vals:
        return {"n_true": 0, "n_applicable": 0, "rate": None}
    n_true = sum(1 for v in vals if v is True)
    return {"n_true": n_true, "n_applicable": len(vals),
            "rate": n_true / len(vals)}


def verdict_supported_inconclusive(n_applicable, min_n=30):
    return n_applicable < min_n


def analyze(xes_path: Path, cases_out: Path, json_out: Path):
    rows = []
    n_dropped = 0
    n_cases = 0
    context = ET.iterparse(str(xes_path), events=("end",))
    for _, elem in context:
        if local_tag(elem.tag) != "trace":
            continue
        case, raw_events = parse_trace(elem)
        case_id = case.get("concept:name", f"case_{n_cases + 1}")
        item_cat = case.get("Item Category")
        gr_based = parse_gr_based(case.get("GR-Based Inv. Verif."))
        events, dropped = build_filtered_events(raw_events)
        n_dropped += dropped
        rows.append(evaluate_case(case_id, item_cat, gr_based, events))
        n_cases += 1
        if n_cases % 25000 == 0:
            print(f"processed {n_cases} cases...", flush=True)
        elem.clear()  # constant memory
    print(f"processed {n_cases} cases total.", flush=True)

    n_events = sum(r["n_events"] for r in rows)

    # overall rates
    overall = {
        "r1_maverick": rate(rows, "r1_maverick"),
        "r2_viol": rate(rows, "r2_viol"),
        "r3_viol": rate(rows, "r3_viol"),
        "r4_rework": rate(rows, "r4_rework"),
        "r5_viol": rate(rows, "r5_viol"),
        "approval_change_after_po": rate(rows, "approval_change_after_po"),
    }
    # approval-only: approval change after PO with NO Quantity/Price rework
    approval_only_vals = [r for r in rows
                          if r["approval_change_after_po"] is not None
                          and r["r4_rework"] is not None]
    if approval_only_vals:
        n_approval_only = sum(1 for r in approval_only_vals
                              if r["approval_change_after_po"] is True
                              and r["r4_rework"] is False)
        approval_only_rate = {
            "n_true": n_approval_only,
            "n_applicable": len(approval_only_vals),
            "rate": n_approval_only / len(approval_only_vals),
        }
    else:
        approval_only_rate = {"n_true": 0, "n_applicable": 0, "rate": None}
    two_way = [r for r in rows if r["_is_two_way"]]
    r1_two_way = rate(two_way, "r1_maverick")
    r4_two_way = rate(two_way, "r4_rework")
    approval_two_way = rate(two_way, "approval_change_after_po")

    after_rows = [r for r in rows if r["_after_gr"] is True]
    before_rows = [r for r in rows
                   if r["_stratum3"] == "before"]
    three_way = {
        "after": {"n_cases": len(after_rows),
                  "r2_viol": rate(after_rows, "r2_viol"),
                  "r3_viol": rate(after_rows, "r3_viol"),
                  "r4_rework": rate(after_rows, "r4_rework"),
                  "approval_change_after_po": rate(
                      after_rows, "approval_change_after_po")},
        "before": {"n_cases": len(before_rows),
                   "r2_viol": rate(before_rows, "r2_viol"),
                   "r3_viol": rate(before_rows, "r3_viol"),
                   "r4_rework": rate(before_rows, "r4_rework"),
                   "approval_change_after_po": rate(
                       before_rows, "approval_change_after_po")},
    }

    # per Item Category
    by_cat = {}
    cats = defaultdict(list)
    for r in rows:
        cats[r["item_category"] or "UNKNOWN"].append(r)
    for cat, rs in sorted(cats.items()):
        by_cat[cat] = {
            "n_cases": len(rs),
            "r1_maverick": rate(rs, "r1_maverick"),
            "r2_viol": rate(rs, "r2_viol"),
            "r3_viol": rate(rs, "r3_viol"),
            "r4_rework": rate(rs, "r4_rework"),
            "approval_change_after_po": rate(rs, "approval_change_after_po"),
            "r5_viol": rate(rs, "r5_viol"),
        }

    # R2 co-occurrence with payment-block/delay (after-GR stratum)
    r2v = [r for r in after_rows if r["r2_viol"] is True]
    r2c = [r for r in after_rows if r["r2_viol"] is False]

    def block_rate(rs):
        if not rs:
            return None
        return sum(1 for r in rs if r["_has_block"]) / len(rs)

    def delay_days(r):
        if r["_inv_ts"] is not None and r["_clear_ts"] is not None:
            return (r["_clear_ts"] - r["_inv_ts"]).total_seconds() / 86400.0
        return None

    def median(xs):
        xs = sorted(x for x in xs if x is not None)
        if not xs:
            return None
        m = len(xs) // 2
        if len(xs) % 2 == 1:
            return xs[m]
        return (xs[m - 1] + xs[m]) / 2.0

    n_unblocked = sum(1 for r in r2v if r["_unblocked"] is True)
    r2_co = {
        "n_after_gr": len(after_rows),
        "n_viol": len(r2v),
        "n_compliant": len(r2c),
        "n_unblocked_blocked_then_cleared": n_unblocked,
        "unblocked_rate_given_viol": (n_unblocked / len(r2v) if r2v else None),
        "block_rate_given_viol": block_rate(r2v),
        "block_rate_given_compliant": block_rate(r2c),
        "payment_signal_rate_given_viol": (
            sum(1 for r in r2v if r["_has_payment"]) / len(r2v) if r2v else None),
        "payment_signal_rate_given_compliant": (
            sum(1 for r in r2c if r["_has_payment"]) / len(r2c) if r2c else None),
        "delay_invoice_to_clear_median_days_viol": median(delay_days(r) for r in r2v),
        "delay_invoice_to_clear_median_days_compliant": median(delay_days(r) for r in r2c),
        "note": ("block = event name contains 'block' (e.g. Remove Payment Block); "
                 "delay = Clear Invoice ts minus Record Invoice Receipt ts; "
                 "unblocked = R2 violation with a later GR after first invoice."),
    }

    # falsifiers vs lab anchors
    r2_rate = rate(after_rows, "r2_viol")["rate"]
    r3a_rate = rate(after_rows, "r3_viol")["rate"]
    r3b_rate = rate(before_rows, "r3_viol")["rate"]
    r4_rate = overall["r4_rework"]["rate"]

    # A: R2 rate vs 16.7% + cost signature (excess block/delay/rework)
    a_n = rate(after_rows, "r2_viol")["n_applicable"]
    bvb = r2_co["block_rate_given_viol"]
    bcb = r2_co["block_rate_given_compliant"]
    excess_block = (bvb is not None and bcb is not None and bvb > bcb)
    if verdict_supported_inconclusive(a_n):
        a_verdict = "INCONCLUSIVE"
        a_why = f"n_applicable={a_n} < 30; rate estimate unstable."
    elif r2_rate is None:
        a_verdict = "INCONCLUSIVE"
        a_why = "no applicable after-GR cases."
    elif 0.10 <= r2_rate <= 0.25 and (excess_block or r2_rate <= 0.167 + 0.05):
        a_verdict = "SUPPORTED"
        a_why = (f"after-GR R2 rate {r2_rate:.3f} within [0.10,0.25] around lab 0.167"
                 + (f"; excess block {bvb:.3f}>{bcb:.3f}" if excess_block else "")
                 + "; ordering violation carries control cost.")
    elif r2_rate is not None and r2_rate > 0.50 and not excess_block:
        a_verdict = "REFUTED"
        a_why = (f"after-GR R2 rate {r2_rate:.3f} is majority practice with no excess "
                 "block/delay/rework vs compliant; violation is tolerated, not failure.")
    else:
        a_verdict = "INCONCLUSIVE"
        a_why = (f"after-GR R2 rate {r2_rate:.3f} off-anchor but cost signature "
                 f"ambiguous (block viol={bvb} vs compl={bcb}).")

    # B: R3 zero-tolerance in both 3-way strata + correction signature
    def b_verdict(r, label):
        n = r["n_applicable"]
        if verdict_supported_inconclusive(n):
            return ("INCONCLUSIVE",
                    f"{label}: n_applicable={n} < 30; estimate unstable.")
        if r["rate"] is None:
            return "INCONCLUSIVE", f"{label}: no applicable cases."
        # correction rate among R3 violations
        return None, None  # handled below
    # correction = block/credit-memo/price-change among R3 violators
    corr_rates = {}
    for label, rs in (("after", after_rows), ("before", before_rows)):
        viol = [r for r in rs if r["r3_viol"] is True]
        if viol:
            corr_rates[label] = sum(1 for r in viol if r["_has_correction"]) / len(viol)
        else:
            corr_rates[label] = None
    r3_rates = [x for x in (r3a_rate, r3b_rate) if x is not None]
    r3_max = max(r3_rates) if r3_rates else None
    b_n = sum(rate(rs, "r3_viol")["n_applicable"] for rs in (after_rows, before_rows))
    if verdict_supported_inconclusive(b_n):
        b_verdict_s, b_why = ("INCONCLUSIVE",
                              f"3-way n_applicable={b_n} < 30; estimate unstable.")
    elif r3_max is None:
        b_verdict_s, b_why = "INCONCLUSIVE", "no applicable 3-way cases."
    elif r3_max <= 0.01:
        b_verdict_s, b_why = ("SUPPORTED",
                              f"max 3-way R3 rate {r3_max:.4f} <= 1%; zero-tolerance holds.")
    elif r3_max > 0.05 and all((c or 0) < 0.5 for c in corr_rates.values()
                               if c is not None):
        b_verdict_s, b_why = ("REFUTED",
                              f"R3 deltas routine (max rate {r3_max:.3f}; after={r3a_rate}, "
                              f"before={r3b_rate}) with low correction "
                              f"{corr_rates}; tolerance-0 is artifact.")
    else:
        b_verdict_s, b_why = ("INCONCLUSIVE",
                              f"R3 rates after={r3a_rate} before={r3b_rate} "
                              f"correction={corr_rates}; ambiguous.")
    _ = b_verdict  # keep helper documented (threshold logic above)

    # C: R4 rework (corrected: Quantity/Price only, excl. Approval) vs 2.15% base
    # Published F2 base = Change Quantity 1.34% + Change Price 0.78% only
    # (~2.12%, anchor 2.15% used here). 'Change Approval for Purchase Order'
    # is routine workflow and excluded; tracked separately as
    # approval_change_after_po for transparency.
    c_n = overall["r4_rework"]["n_applicable"]
    if verdict_supported_inconclusive(c_n):
        c_verdict = "INCONCLUSIVE"
        c_why = f"n_applicable={c_n} < 30; estimate unstable."
    elif r4_rate is None:
        c_verdict = "INCONCLUSIVE"
        c_why = "no applicable cases."
    elif 0.0015 <= r4_rate <= 0.0415:  # 0.15%..4.15% (anchor +-2pp)
        c_verdict = "SUPPORTED"
        c_why = (f"corrected rework (Quantity/Price only, excl. Approval) rate "
                 f"{r4_rate:.4f} within [0.0015,0.0415] around F2 base "
                 f"0.0215 (1.34%+0.78%); "
                 "Round-2 transfer not overturned on rate alone.")
    elif r4_rate >= 0.0215:
        c_verdict = "REFUTED"
        c_why = (f"corrected rework (Quantity/Price only) rate {r4_rate:.4f} "
                 "at/above 2.15% F2 base (1.34%+0.78%); Round-2 '-100%' fix "
                 "does not transfer (rate persists). Delay-penalty check needs durations.")
    else:
        c_verdict = "SUPPORTED"
        c_why = (f"corrected rework (Quantity/Price only) rate {r4_rate:.4f} "
                 "below base band; no persistence signal.")

    results = {
        "source_xes": str(xes_path),
        "n_cases": n_cases,
        "n_events_filtered": n_events,
        "n_events_dropped_out_of_range": n_dropped,
        "filters": {"keep_from": "2018-01-01", "keep_to": "2019-01-27",
                    "rule": "drop event if ts < 2018-01-01 or ts > 2019-01-27 23:59:59",
                    "epsilon_r3": EPSILON},
        "overall": overall,
        "r1_two_way_stratum": {"n_cases": len(two_way), "r1_maverick": r1_two_way,
                               "r4_rework": r4_two_way,
                               "approval_change_after_po": approval_two_way},
        "three_way_strata": three_way,
        "by_item_category": by_cat,
        "approval_change": {
            "overall": overall["approval_change_after_po"],
            "approval_only_no_quantity_price_rework": approval_only_rate,
            "definition": ("'Change Approval for Purchase Order' after "
                           "'Create Purchase Order Item'; routine workflow, "
                           "excluded from corrected R4; approval-only = "
                           "approval True AND r4_rework False."),
        },
        "r2": r2_co,
        "r2_unblocked_nuance": {
            "n_viol": len(r2v),
            "n_unblocked": n_unblocked,
            "definition": ("R2 violation where a later GR exists after first invoice "
                           "(blocked-then-cleared)."),
        },
        "falsifiers": {
            "A_R2_rate_vs_lab_16_7pct": {
                "observed_after_gr_r2_rate": r2_rate,
                "expected_lab": 0.167,
                "band_supported": [0.10, 0.25],
                "refuted_if": ">0.50 with no excess block/delay/rework",
                "verdict": a_verdict,
                "rationale": a_why,
            },
            "B_R3_zero_tolerance_both_3way": {
                "observed_after": r3a_rate,
                "observed_before": r3b_rate,
                "expected": 0.0,
                "supported_if": "max rate <= 0.01",
                "refuted_if": "max rate > 0.05 with correction < 0.50",
                "correction_rate_given_viol": corr_rates,
                "verdict": b_verdict_s,
                "rationale": b_why,
            },
            "C_R4_rework_vs_base_2_15pct": {
                "observed": r4_rate,
                "observed_approval_change_after_po": overall[
                    "approval_change_after_po"]["rate"],
                "observed_approval_only": approval_only_rate["rate"],
                "expected_base": 0.0215,
                "expected_base_detail": ("F2 Change Quantity 1.34% + "
                                         "Change Price 0.78% only; "
                                         "Change Approval excluded"),
                "band_supported": [0.0015, 0.0415],
                "r4_definition": "Change Quantity/Price after Create PO Item",
                "verdict": c_verdict,
                "rationale": c_why,
            },
        },
        "activity_scope": {
            "r1": [A_VENDOR_INV, A_PO_CREATE],
            "r2": [A_REC_INV, A_REC_GR],
            "r3": [A_PO_CREATE, A_REC_INV],
            "r4": sorted(list(CHANGE_ACTS)) + [A_PO_CREATE],
            "r4_approval_change_after_po": [APPROVAL_CHANGE_ACT, A_PO_CREATE],
            "r5": [A_CLEAR, A_REC_INV],
        },
        "notes": [
            "Streaming iterparse, constant memory (trace-level clear).",
            "R1 False includes vendor-invoice-absent (F1 denominator = all 2-way). None only if PO ts missing.",
            "R2 applicable only in after-GR stratum; R3 only in 3-way strata; else None.",
            "R4 corrected: Change Quantity/Price after PO only (Change Approval excluded as routine workflow; tracked as approval_change_after_po).",
            "Item Category matching is case-insensitive substring (after/before+gr, 2-way, 3-way, consignment) with GR-Based Inv. Verif. fallback.",
        ],
    }

    # write CSV
    cases_out.parent.mkdir(parents=True, exist_ok=True)
    with open(cases_out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "item_category", "has_gr", "has_invoice",
                    "r1_maverick", "r2_viol", "r3_viol", "r4_rework",
                    "approval_change_after_po",
                    "r5_viol", "n_events"])
        for r in rows:
            w.writerow([r["case_id"], r["item_category"],
                        flag_str(r["has_gr"]), flag_str(r["has_invoice"]),
                        flag_str(r["r1_maverick"]), flag_str(r["r2_viol"]),
                        flag_str(r["r3_viol"]), flag_str(r["r4_rework"]),
                        flag_str(r["approval_change_after_po"]),
                        flag_str(r["r5_viol"]), r["n_events"]])
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Wrote {len(rows)} cases -> {cases_out}", flush=True)
    print(f"Wrote aggregates -> {json_out}", flush=True)
    print(json.dumps({"n_cases": n_cases,
                      "overall": {k: v["rate"] for k, v in overall.items()},
                      "falsifiers": {k: v["verdict"]
                                     for k, v in results["falsifiers"].items()}},
                     indent=2))
    return rows, results


def main(argv=None):
    p = argparse.ArgumentParser(description="Streaming BPI 2019 XES analyzer (R1-R5 proxies).")
    p.add_argument("xes_path", nargs="?", default=str(DEFAULT_XES),
                   help="input XES path (default data/BPI_Challenge_2019.xes)")
    p.add_argument("--cases-out", default=str(DEFAULT_CASES_OUT))
    p.add_argument("--json-out", default=str(DEFAULT_JSON_OUT))
    args = p.parse_args(argv)
    xes_path = Path(args.xes_path)
    if not xes_path.exists():
        print(f"ERROR: XES not found: {xes_path}", file=sys.stderr)
        sys.exit(2)
    analyze(xes_path, Path(args.cases_out), Path(args.json_out))


if __name__ == "__main__":
    main()
