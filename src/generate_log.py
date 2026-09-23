"""Generate Round 1 synthetic P2P event log: 120 cases, S1-S6 x 20 each.

Schema: case_id,activity,timestamp,resource,scenario,vendor,po_id,
        qty_ordered,qty_received,qty_invoiced
Normative: PR -> Approval -> PO -> Receipt -> Invoice -> Payment

Ground truth:
  S3 violates R2 only (invoice before receipt)
  S4 violates R3 only (qty mismatch, invoiced > received)
  S6 violates R4 only (single approval, PO Modification before PO, no re-approval)
  S1, S2, S5 clean (S2 = slow receipt, S5 = slow approval, timing only)

Stochastic realism (seed 42):
  (1) business-hours clock: BASE 2026-01-05 09:00, stagger 5h per case,
      any timestamp falling Sat/Sun rolled forward to Monday 08:00.
  (2) stochastic waits via random.lognormvariate (days):
      PR->Approval: mean ~1.0, sigma .35, clipped [0.3, 2.5]; S5 += 2.0d
      Approval->PO: mean ~0.5, sigma .35, clipped [0.1, 1.5]
        (handover leg to keep timestamps strictly increasing; not an
        activity, small delay to complete the chain)
      PO->Receipt: mean ~2.0, sigma .45, clipped [0.5, 4.5];
        then S2 += 3.0d, Vendor_B += 0.5d, Vendor_C -= 0.3d (floor 0.5d)
      Receipt->Invoice: mean ~0.8, sigma .4, clipped [0.2, 2.5]
      Invoice->Pay: mean ~1.8, sigma .4, clipped [0.5, 4.0]
      S3 replaces PO->Receipt & Receipt->Invoice with:
        PO->Invoice mean ~0.6 sigma .4 clipped [0.2, 2.5],
        Invoice->Receipt mean ~1.5 sigma .45 clipped [0.5, 4.5]
        Pay after Receipt reuses Invoice->Pay distribution.
      S6 Approval->MOD and MOD->PO: each mean ~0.3 sigma .35,
        clipped [0.05, 1.0] (split of the normal Approval->PO handover,
        keeps MOD strictly before PO with a single approval).
  (3) resource pools (seeded draws per case):
      PR req_01..03, Approval approver_1/2, PO/MOD buy_01/02 (same buyer
      within a case), Receipt wh_01/02, Invoice/Pay acc_01/02.
  (4) qtys: qo weighted choice [5,10,15,20,50] (weights below);
      S4: qr = qo, qi = qr + randint(2,8); else qr = qi = qo.
      S6 keeps a single qo across all events (no qty change) so R3 stays clean.

Variants stay 3: normative (S1/S2/S4/S5), S3 (invoice<receipt), S6 (+MOD).
Total events: 5 scen x 20 x 6 + 20 x 7 = 740.
"""
import argparse
import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

BASE = datetime(2026, 1, 5, 9, 0, 0)  # Monday 2026-01-05 09:00
VENDORS = ["Vendor_A", "Vendor_B", "Vendor_C"]
ACTS = {
    "pr": "Purchase Request",
    "approve": "Purchase Request Approval",
    "po": "Purchase Order",
    "receipt": "Goods Receipt",
    "invoice": "Vendor Invoice",
    "pay": "Payment",
    "mod": "PO Modification",
}

# resource pools
REQ_POOL = ["req_01", "req_02", "req_03"]
APPR_POOL = ["approver_1", "approver_2"]
BUY_POOL = ["buy_01", "buy_02"]
WH_POOL = ["wh_01", "wh_02"]
ACC_POOL = ["acc_01", "acc_02"]

# qty menu + weights (small orders more frequent)
QO_VALS = [5, 10, 15, 20, 50]
QO_WEIGHTS = [35, 30, 15, 15, 5]


def parse_base(s: str) -> datetime:
    """Parse ISO base date/datetime; date-only defaults to 09:00."""
    dt = datetime.fromisoformat(s)
    if len(s.strip()) == 10:  # YYYY-MM-DD
        dt = dt.replace(hour=9, minute=0, second=0)
    return dt


def parse_args(argv=None):
    default_out = Path(__file__).resolve().parent.parent / "data" / "event-log-r1.csv"
    p = argparse.ArgumentParser(
        description="Generate Round 1 synthetic P2P event log (S1-S6).")
    p.add_argument("--n", type=int, default=20,
                   help="per-scenario cases (default: 20)")
    p.add_argument("--seed", type=int, default=42,
                   help="RNG seed (default: 42)")
    p.add_argument("--out", type=str, default=str(default_out),
                   help="output CSV path (default: data/event-log-r1.csv)")
    p.add_argument("--base", type=str, default="2026-01-05",
                   help="base date ISO (default: 2026-01-05)")
    return p.parse_args(argv)


def roll_weekend(ts: datetime) -> datetime:
    """Roll Sat/Sun timestamps forward to Monday 08:00."""
    wd = ts.weekday()
    if wd == 5:  # Saturday
        ts = (ts + timedelta(days=2)).replace(hour=8, minute=0, second=0)
    elif wd == 6:  # Sunday
        ts = (ts + timedelta(days=1)).replace(hour=8, minute=0, second=0)
    return ts


def sample_lognormal(rng: random.Random, mean: float, sigma: float,
                     lo: Optional[float] = None, hi: Optional[float] = None) -> float:
    """Sample lognormal with target mean (days) via rng.lognormvariate; optionally clip."""
    mu = math.log(mean) - (sigma ** 2) / 2.0
    v = rng.lognormvariate(mu, sigma)
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


def advance(prev: datetime, wait_days: float) -> datetime:
    """prev + wait, then weekend roll."""
    return roll_weekend(prev + timedelta(days=wait_days))


def add_event(rows, case_id, act, ts, res, scen, vendor, po_id, qo, qr, qi):
    rows.append([case_id, act, ts.isoformat(timespec="seconds"), res, scen,
                 vendor, po_id, qo, qr, qi])


def sample_approval_wait(rng, scenario) -> float:
    w = sample_lognormal(rng, 1.0, 0.35, 0.3, 2.5)
    if scenario == "S5":
        w += 2.0
    return w


def sample_po_receipt_wait(rng, scenario, vendor) -> float:
    w = sample_lognormal(rng, 2.0, 0.45, 0.5, 4.5)
    if scenario == "S2":
        w += 3.0
    if vendor == "Vendor_B":
        w += 0.5
    elif vendor == "Vendor_C":
        w -= 0.3
    return max(0.5, w)


def sample_receipt_invoice_wait(rng) -> float:
    return sample_lognormal(rng, 0.8, 0.4, 0.2, 2.5)


def sample_invoice_pay_wait(rng) -> float:
    return sample_lognormal(rng, 1.8, 0.4, 0.5, 4.0)


def gen_case(idx, scenario, rng, base=BASE):
    n = idx + 1
    case_id = f"C{n:03d}"
    po_id = f"PO{n:03d}"
    vendor = VENDORS[(n - 1) % len(VENDORS)]
    qo = rng.choices(QO_VALS, weights=QO_WEIGHTS, k=1)[0]
    if scenario == "S4":
        qr = qo
        qi = qr + rng.randint(2, 8)
    else:
        qr, qi = qo, qo

    t0 = roll_weekend(base + timedelta(hours=(n - 1) * 5))

    req = rng.choice(REQ_POOL)
    approver = rng.choice(APPR_POOL)
    buyer = rng.choice(BUY_POOL)
    wh = rng.choice(WH_POOL)
    acc_inv = rng.choice(ACC_POOL)
    acc_pay = rng.choice(ACC_POOL)

    w_appr = sample_approval_wait(rng, scenario)
    w_appr_po = sample_lognormal(rng, 0.5, 0.35, 0.1, 1.5)
    w_rec_inv = sample_receipt_invoice_wait(rng)
    w_inv_pay = sample_invoice_pay_wait(rng)
    rows = []

    if scenario == "S3":
        # PR -> Approval -> PO -> Invoice -> Receipt -> Pay
        w_po_inv = sample_lognormal(rng, 0.6, 0.4, 0.2, 2.5)
        w_inv_rec = sample_lognormal(rng, 1.5, 0.45, 0.5, 4.5)
        t_pr = t0
        t_ap = advance(t_pr, w_appr)
        t_po = advance(t_ap, w_appr_po)
        t_inv = advance(t_po, w_po_inv)
        t_rec = advance(t_inv, w_inv_rec)
        t_pay = advance(t_rec, w_inv_pay)
        for a, t, r in [(ACTS["pr"], t_pr, req),
                        (ACTS["approve"], t_ap, approver),
                        (ACTS["po"], t_po, buyer),
                        (ACTS["invoice"], t_inv, acc_inv),
                        (ACTS["receipt"], t_rec, wh),
                        (ACTS["pay"], t_pay, acc_pay)]:
            add_event(rows, case_id, a, t, r, scenario, vendor, po_id, qo, qr, qi)
        return rows

    if scenario == "S6":
        # PR -> Approval -> MOD -> PO -> Receipt -> Invoice -> Pay (single approval)
        w_appr_mod = sample_lognormal(rng, 0.3, 0.35, 0.05, 1.0)
        w_mod_po = sample_lognormal(rng, 0.3, 0.35, 0.05, 1.0)
        w_po_rec = sample_po_receipt_wait(rng, scenario, vendor)
        t_pr = t0
        t_ap = advance(t_pr, w_appr)
        t_mod = advance(t_ap, w_appr_mod)
        t_po = advance(t_mod, w_mod_po)
        t_rec = advance(t_po, w_po_rec)
        t_inv = advance(t_rec, w_rec_inv)
        t_pay = advance(t_inv, w_inv_pay)
        for a, t, r in [(ACTS["pr"], t_pr, req),
                        (ACTS["approve"], t_ap, approver),
                        (ACTS["mod"], t_mod, buyer),
                        (ACTS["po"], t_po, buyer),
                        (ACTS["receipt"], t_rec, wh),
                        (ACTS["invoice"], t_inv, acc_inv),
                        (ACTS["pay"], t_pay, acc_pay)]:
            add_event(rows, case_id, a, t, r, scenario, vendor, po_id, qo, qr, qi)
        return rows

    # S1 / S2 / S4 / S5: normative order
    w_po_rec = sample_po_receipt_wait(rng, scenario, vendor)
    t_pr = t0
    t_ap = advance(t_pr, w_appr)
    t_po = advance(t_ap, w_appr_po)
    t_rec = advance(t_po, w_po_rec)
    t_inv = advance(t_rec, w_rec_inv)
    t_pay = advance(t_inv, w_inv_pay)
    for a, t, r in [(ACTS["pr"], t_pr, req),
                    (ACTS["approve"], t_ap, approver),
                    (ACTS["po"], t_po, buyer),
                    (ACTS["receipt"], t_rec, wh),
                    (ACTS["invoice"], t_inv, acc_inv),
                    (ACTS["pay"], t_pay, acc_pay)]:
        add_event(rows, case_id, a, t, r, scenario, vendor, po_id, qo, qr, qi)
    return rows


def main(argv=None):
    args = parse_args(argv)
    rng = random.Random(args.seed)
    base = parse_base(args.base)
    out = Path(args.out)
    header = ["case_id", "activity", "timestamp", "resource", "scenario", "vendor", "po_id",
              "qty_ordered", "qty_received", "qty_invoiced"]
    rows = []
    scenarios = ["S1", "S2", "S3", "S4", "S5", "S6"]
    idx = 0
    for s in scenarios:
        for _ in range(args.n):
            rows.extend(gen_case(idx, s, rng, base))
            idx += 1
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"Wrote {len(rows)} events, {idx} cases -> {out}")


if __name__ == "__main__":
    main()
