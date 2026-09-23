"""Round 2: rerun S3/S4/S6 (20 each) AFTER redesign controls.
Simulates fixed ERP behavior: ordering enforced, qty blocked, re-approval required.

Stochastic realism (seed 7) mirrors R1 (src/generate_log.py):
  (1) business-hours clock: BASE 2026-02-02 09:00, stagger 5h per case,
      any timestamp falling Sat/Sun rolled forward to Monday 08:00.
  (2) stochastic waits via random.lognormvariate (days):
      PR->Approval: mean ~1.0, sigma .35, clipped [0.3, 2.5]
      Approval->PO: mean ~0.5, sigma .35, clipped [0.1, 1.5]
        (handover leg, same as R1)
      PO->Receipt: mean ~2.0, sigma .45, clipped [0.5, 4.5];
        then Vendor_B += 0.5d, Vendor_C -= 0.3d (floor 0.5d)
      Receipt->Invoice: mean ~0.8, sigma .4 (lognormal > 0, clipped positive)
      Invoice->Pay: mean ~1.8, sigma .4 (lognormal > 0, clipped positive)
      S6R splits Approval->PO around MOD + re-approval:
        Approval->MOD mean ~0.3 sigma .35 clipped [0.05, 1.0],
        MOD->re-approval mean ~1.0 sigma .35 clipped [0.3, 2.5]
          (full re-approval wait -> ~+1d control overhead),
        re-approval->PO mean ~0.5 sigma .35 clipped [0.1, 1.5].
  (3) resource pools (seeded draws per case):
      PR req_01..03, Approval approver_1/2 (same approver for re-approval),
      PO/MOD buy_01/02 (same buyer within a case),
      Receipt wh_01/02, Invoice/Pay acc_01/02.
  (4) qtys: qo weighted choice [5,10,15,20,50] (same weights as R1);
      S3R/S4R: qr = qi = qo (S4R bill capped at received qty, tolerance 0).
      S6R: initial qo, post-MOD qo2 (both in menu, qo2 != qo);
        qty_ordered shows qo -> qo2 change, qr = qi = qo2 throughout
        so R3 stays clean.

Redesign kept:
  S3R normative order PR->Approval->PO->Receipt->Invoice->Pay (6 events).
  S4R normative order, bill capped at received qty (6 events).
  S6R PR->Approval->MOD->Approval (re-approval)->PO->Receipt->Invoice->Pay
    (8 events, MOD strictly before re-approval strictly before PO).

Total events: 20x6 + 20x6 + 20x8 = 400. Cases C101-C160.
All 60 pass R1-R5.
"""
import argparse
import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

BASE = datetime(2026, 2, 2, 9, 0, 0)  # Monday 2026-02-02 09:00
VENDORS = ["Vendor_A", "Vendor_B", "Vendor_C"]
PR, AP, PO, REC, INV, PAY, MOD = ("Purchase Request", "Purchase Request Approval",
    "Purchase Order", "Goods Receipt", "Vendor Invoice", "Payment", "PO Modification")
REAPPR = "Purchase Request Approval (re-approval)"

REQ_POOL = ["req_01", "req_02", "req_03"]
APPR_POOL = ["approver_1", "approver_2"]
BUY_POOL = ["buy_01", "buy_02"]
WH_POOL = ["wh_01", "wh_02"]
ACC_POOL = ["acc_01", "acc_02"]

QO_VALS = [5, 10, 15, 20, 50]
QO_WEIGHTS = [35, 30, 15, 15, 5]


def parse_base(s: str) -> datetime:
    """Parse ISO base date/datetime; date-only defaults to 09:00."""
    dt = datetime.fromisoformat(s)
    if len(s.strip()) == 10:  # YYYY-MM-DD
        dt = dt.replace(hour=9, minute=0, second=0)
    return dt


def parse_args(argv=None):
    default_out = Path(__file__).resolve().parent.parent / "data" / "event-log-r2.csv"
    p = argparse.ArgumentParser(
        description="Generate Round 2 synthetic P2P event log (S3R/S4R/S6R).")
    p.add_argument("--n", type=int, default=20,
                   help="per-scenario cases (default: 20)")
    p.add_argument("--seed", type=int, default=7,
                   help="RNG seed (default: 7)")
    p.add_argument("--out", type=str, default=str(default_out),
                   help="output CSV path (default: data/event-log-r2.csv)")
    p.add_argument("--base", type=str, default="2026-02-02",
                   help="base date ISO (default: 2026-02-02)")
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
    """Sample lognormal with target mean (days); optionally clip (always > 0)."""
    mu = math.log(mean) - (sigma ** 2) / 2.0
    v = rng.lognormvariate(mu, sigma)
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return max(1e-6, v)


def advance(prev: datetime, wait_days: float) -> datetime:
    """prev + wait, then weekend roll."""
    return roll_weekend(prev + timedelta(days=wait_days))


def sample_approval_wait(rng: random.Random) -> float:
    return sample_lognormal(rng, 1.0, 0.35, 0.3, 2.5)


def sample_po_receipt_wait(rng: random.Random, vendor: str) -> float:
    w = sample_lognormal(rng, 2.0, 0.45, 0.5, 4.5)
    if vendor == "Vendor_B":
        w += 0.5
    elif vendor == "Vendor_C":
        w -= 0.3
    return max(0.5, w)


def ev(rows, cid, act, ts, res, scen, ven, po, qo, qr, qi):
    rows.append([cid, act, ts.isoformat(timespec="seconds"), res, scen, ven, po, qo, qr, qi])


def gen_case(idx: int, scen: str, rng: random.Random, base=BASE):
    n = 101 + idx
    cid, po = f"C{n}", f"PO{n}"
    ven = VENDORS[(n - 1) % len(VENDORS)]
    qo = rng.choices(QO_VALS, weights=QO_WEIGHTS, k=1)[0]
    t0 = roll_weekend(base + timedelta(hours=idx * 5))

    req = rng.choice(REQ_POOL)
    ap = rng.choice(APPR_POOL)
    buyer = rng.choice(BUY_POOL)
    wh = rng.choice(WH_POOL)
    acc_inv = rng.choice(ACC_POOL)
    acc_pay = rng.choice(ACC_POOL)

    rows = []
    if scen == "S6R":
        # qty change via MOD: qo -> qo2 (both in menu, different)
        candidates = [v for v in QO_VALS if v != qo]
        qo2 = rng.choice(candidates)
        qr = qi = qo2
        w_appr1 = sample_approval_wait(rng)
        w_appr_mod = sample_lognormal(rng, 0.3, 0.35, 0.05, 1.0)
        w_mod_reappr = sample_lognormal(rng, 1.0, 0.35, 0.3, 2.5)
        w_reappr_po = sample_lognormal(rng, 0.5, 0.35, 0.1, 1.5)
        w_po_rec = sample_po_receipt_wait(rng, ven)
        w_rec_inv = sample_lognormal(rng, 0.8, 0.4)
        w_inv_pay = sample_lognormal(rng, 1.8, 0.4)
        t_pr = t0
        t_ap1 = advance(t_pr, w_appr1)
        t_mod = advance(t_ap1, w_appr_mod)
        t_ap2 = advance(t_mod, w_mod_reappr)
        t_po = advance(t_ap2, w_reappr_po)
        t_rec = advance(t_po, w_po_rec)
        t_inv = advance(t_rec, w_rec_inv)
        t_pay = advance(t_inv, w_inv_pay)
        ev(rows, cid, PR, t_pr, req, scen, ven, po, qo, qr, qi)
        ev(rows, cid, AP, t_ap1, ap, scen, ven, po, qo, qr, qi)
        ev(rows, cid, MOD, t_mod, buyer, scen, ven, po, qo2, qr, qi)
        ev(rows, cid, REAPPR, t_ap2, ap, scen, ven, po, qo2, qr, qi)
        ev(rows, cid, PO, t_po, buyer, scen, ven, po, qo2, qr, qi)
        ev(rows, cid, REC, t_rec, wh, scen, ven, po, qo2, qr, qi)
        ev(rows, cid, INV, t_inv, acc_inv, scen, ven, po, qo2, qr, qi)
        ev(rows, cid, PAY, t_pay, acc_pay, scen, ven, po, qo2, qr, qi)
        return rows

    # S3R / S4R: normative order, capped qty (qi = qr = qo)
    qr = qi = qo
    w_appr = sample_approval_wait(rng)
    w_appr_po = sample_lognormal(rng, 0.5, 0.35, 0.1, 1.5)
    w_po_rec = sample_po_receipt_wait(rng, ven)
    w_rec_inv = sample_lognormal(rng, 0.8, 0.4)
    w_inv_pay = sample_lognormal(rng, 1.8, 0.4)
    t_pr = t0
    t_ap = advance(t_pr, w_appr)
    t_po = advance(t_ap, w_appr_po)
    t_rec = advance(t_po, w_po_rec)
    t_inv = advance(t_rec, w_rec_inv)
    t_pay = advance(t_inv, w_inv_pay)
    for a, t, r in [(PR, t_pr, req), (AP, t_ap, ap), (PO, t_po, buyer),
                    (REC, t_rec, wh), (INV, t_inv, acc_inv), (PAY, t_pay, acc_pay)]:
        ev(rows, cid, a, t, r, scen, ven, po, qo, qr, qi)
    return rows


def main(argv=None):
    args = parse_args(argv)
    rng = random.Random(args.seed)
    base = parse_base(args.base)
    rows = []
    idx = 0
    for scen in ["S3R", "S4R", "S6R"]:
        for _ in range(args.n):
            rows.extend(gen_case(idx, scen, rng, base))
            idx += 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "activity", "timestamp", "resource", "scenario",
                    "vendor", "po_id", "qty_ordered", "qty_received", "qty_invoiced"])
        w.writerows(rows)
    print(f"Wrote {len(rows)} events, {idx} cases -> {out}")

if __name__ == "__main__":
    main()
