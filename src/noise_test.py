"""Noise robustness sweep for R1 conformance checker (R1-R5).

Loads data/event-log-r1.csv with pandas, sweeps drop-noise levels
[0, 0.02, 0.05, 0.10] x seeds [1, 2, 3] in-memory only (no event files written):
  - per (level, seed): drop `level` fraction of random events (seed=seed)
Re-runs the SAME R1-R5 logic via check_conformance.check_case on clean vs
noisy logs. Per (level, seed) computes:
  - recall on S3/S4/S6 ground-truth violations (60 cases)
  - false-positive rate on S1 (20 conformant cases)
Writes data/robustness.csv (columns noise_level,seed,recall,fpr), prints a
4-level mean table + one-line breakdown verdict (first noise where mean FPR
exceeds 10%). Only file written is data/robustness.csv. Stdlib + pandas only.
"""
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

# --- Reuse SAME R1-R5 logic -------------------------------------------------
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from check_conformance import check_case  # type: ignore
    _LOGIC_SOURCE = "imported check_conformance.check_case"
except Exception as e:  # fallback: exact copy of src/check_conformance.py logic
    _LOGIC_SOURCE = f"copied fallback logic (import failed: {e})"

    def check_case(evs):  # noqa: F811 - fallback copy
        by_act = defaultdict(list)
        for ev in evs:
            by_act[ev["activity"]].append(ev)

        def first(a):
            return by_act[a][0] if a in by_act else None

        viol = {}
        a, po = first("Purchase Request Approval"), first("Purchase Order")
        viol["R1"] = not (a and po and a["_ts"] < po["_ts"])
        r, inv = first("Goods Receipt"), first("Vendor Invoice")
        viol["R2"] = not (r and inv and r["_ts"] < inv["_ts"])
        qr = r["qty_received"] if r else evs[0]["qty_received"]
        qi = inv["qty_invoiced"] if inv else evs[0]["qty_invoiced"]
        viol["R3"] = not (qi <= qr)
        mods = by_act.get("PO Modification", [])
        if not mods:
            viol["R4"] = False
        else:
            approvals = [x for x in evs if "Approval" in x["activity"]]
            ok = True
            for m in mods:
                after = [x for x in approvals if m["_ts"] < x["_ts"] and (not po or x["_ts"] < po["_ts"])]
                if not after:
                    ok = False
            viol["R4"] = not ok
        pay = first("Payment")
        viol["R5"] = not (pay and inv and pay["_ts"] > inv["_ts"])
        t0, t1 = evs[0]["_ts"], evs[-1]["_ts"]
        cycle = (t1 - t0).total_seconds() / 86400
        appr_wait = ((a["_ts"] - evs[0]["_ts"]).total_seconds() / 86400) if a else None
        rec_wait = ((r["_ts"] - po["_ts"]).total_seconds() / 86400) if (r and po) else None
        variant = tuple(x["activity"] for x in evs)
        return viol, variant, cycle, appr_wait, rec_wait, qr, qi


def df_to_cases(df):
    """Convert DataFrame to {case_id: [event-dict sorted by _ts]} + {case_id: scenario}."""
    cases = defaultdict(list)
    scen_of = {}
    for row in df.to_dict(orient="records"):
        try:
            qr = int(row["qty_received"])
        except Exception:
            qr = 0
        try:
            qi = int(row["qty_invoiced"])
        except Exception:
            qi = 0
        try:
            ts = datetime.fromisoformat(str(row["timestamp"]))
        except Exception:
            ts = pd.to_datetime(row["timestamp"]).to_pydatetime()
        ev = {
            "case_id": row["case_id"],
            "activity": row["activity"],
            "timestamp": str(row["timestamp"]),
            "scenario": row["scenario"],
            "_ts": ts,
            "qty_received": qr,
            "qty_invoiced": qi,
        }
        cases[row["case_id"]].append(ev)
        scen_of[row["case_id"]] = row["scenario"]
    for cid in cases:
        cases[cid].sort(key=lambda r: r["_ts"])
    return dict(cases), scen_of


def eval_cases(cases):
    """Run check_case per case -> {cid: failed_rule_list}."""
    failed = {}
    full = {}
    for cid, evs in cases.items():
        if not evs:
            failed[cid] = ["EMPTY"]
            continue
        viol, *_ = check_case(evs)
        fl = [k for k in ("R1", "R2", "R3", "R4", "R5") if viol.get(k)]
        failed[cid] = fl
        full[cid] = viol
    return failed, full


def main():
    base = Path(__file__).resolve().parent.parent / "data"
    inp = base / "event-log-r1.csv"
    df = pd.read_csv(inp)  # read-only; never written back
    print(f"Loaded {len(df)} events, {df['case_id'].nunique()} cases from {inp.name}")
    print(f"Rule logic source: {_LOGIC_SOURCE}")

    clean_cases, clean_scen = df_to_cases(df)
    clean_failed, _ = eval_cases(clean_cases)

    target_scens = ("S3", "S4", "S6")
    target_cids = [c for c, s in clean_scen.items() if s in target_scens]
    s1_cids = [c for c, s in clean_scen.items() if s == "S1"]

    # ground-truth: S3/S4/S6 designed violations, S1 conformant; verify vs clean checker
    n_viol_clean = sum(1 for c in target_cids if clean_failed.get(c))
    n_s1_ok = sum(1 for c in s1_cids if not clean_failed.get(c))
    print(f"Ground truth: {len(target_cids)} S3/S4/S6 violation cases "
          f"(clean checker flags {n_viol_clean}); "
          f"{len(s1_cids)} S1 conformant cases (clean checker OK {n_s1_ok}).")

    levels = [0, 0.02, 0.05, 0.10]
    seeds = [1, 2, 3]

    rows = []  # (noise_level, seed, recall, fpr)
    for level in levels:
        for seed in seeds:
            # --- drop-noise IN-MEMORY on a copy only; never write data files ---
            if level == 0:
                noisy = df.copy(deep=True)
            else:
                drop_idx = df.sample(frac=level, random_state=seed).index
                noisy = df.drop(drop_idx)
            noisy_cases, _ = df_to_cases(noisy)
            noisy_failed, _ = eval_cases(noisy_cases)
            # missing case (all events dropped) counts as flagged/non-conformant
            tp = sum(1 for c in target_cids
                     if (c not in noisy_failed) or noisy_failed.get(c))
            fp = sum(1 for c in s1_cids
                     if (c not in noisy_failed) or noisy_failed.get(c))
            recall = tp / len(target_cids) if target_cids else 0.0
            fpr = fp / len(s1_cids) if s1_cids else 0.0
            rows.append((level, seed, recall, fpr))

    # write ONLY data/robustness.csv (in-memory sweep; no event files written)
    out = base / "robustness.csv"
    with open(out, "w", newline="") as f:
        f.write("noise_level,seed,recall,fpr\n")
        for level, seed, recall, fpr in rows:
            f.write(f"{level},{seed},{recall:.4f},{fpr:.4f}\n")
    print(f"Wrote {out} ({len(rows)} rows: {len(levels)} levels x {len(seeds)} seeds)")

    # per-level means
    print("\n== Robustness sweep (drop-noise, in-memory only) ==")
    print(f"{'noise_level':>11} | {'seeds':>5} | {'mean_recall':>11} | {'mean_fpr':>8}")
    print("-" * 46)
    means = {}
    for level in levels:
        rs = [r for (lv, _s, r, _f) in rows if lv == level]
        fs = [fl for (lv, _s, _r, fl) in rows if lv == level]
        mr = sum(rs) / len(rs)
        mf = sum(fs) / len(fs)
        means[level] = (mr, mf)
        print(f"{level:>11.2f} | {len(seeds):>5d} | {mr:>11.3f} | {mf:>8.3f}")

    # one-line verdict: breakdown = first noise where mean FPR exceeds 10%
    breakdown = next((lv for lv in levels if means[lv][1] > 0.10), None)
    if breakdown is None:
        print("Verdict: NO BREAKDOWN up to noise=0.10 - mean FPR never exceeds 10%.")
    else:
        mr, mf = means[breakdown]
        print(f"Verdict: BREAKDOWN at noise={breakdown:.2f} - mean FPR {mf:.1%} exceeds 10% "
              f"(mean recall {mr:.1%} on S3/S4/S6).")


if __name__ == "__main__":
    main()
