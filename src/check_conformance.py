"""Conformance checker for normative P2P: R1-R5 + variants + performance.
Input: data/event-log-r1.csv (or r2). Output: data/conformance-<round>.csv + stdout summary.
Stdlib only so it runs without PM4Py. PM4Py-compatible schema.
"""
import csv
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RULES = ["R1", "R2", "R3", "R4", "R5"]
NORM = ("Purchase Request", "Purchase Request Approval", "Purchase Order",
        "Goods Receipt", "Vendor Invoice", "Payment")

def parse_ts(s):
    return datetime.fromisoformat(s)

def load(path):
    cases = defaultdict(list)
    with open(path) as f:
        for row in csv.DictReader(f):
            # numeric fields
            for k in ("qty_ordered", "qty_received", "qty_invoiced"):
                try:
                    row[k] = int(row[k])
                except Exception:
                    row[k] = 0
            row["_ts"] = parse_ts(row["timestamp"])
            cases[row["case_id"]].append(row)
    for c in cases.values():
        c.sort(key=lambda r: r["_ts"])
    return cases

def check_case(evs):
    by_act = defaultdict(list)
    for e in evs:
        by_act[e["activity"]].append(e)
    def first(a):
        return by_act[a][0] if a in by_act else None
    viol = {}
    # R1 approval < PO
    a, po = first("Purchase Request Approval"), first("Purchase Order")
    viol["R1"] = not (a and po and a["_ts"] < po["_ts"])
    # R2 receipt < invoice
    r, inv = first("Goods Receipt"), first("Vendor Invoice")
    viol["R2"] = not (r and inv and r["_ts"] < inv["_ts"])
    # R3 invoiced <= received
    qr = r["qty_received"] if r else evs[0]["qty_received"]
    qi = inv["qty_invoiced"] if inv else evs[0]["qty_invoiced"]
    viol["R3"] = not (qi <= qr)
    # R4 no PO Modification without re-approval (approvals after mod, before PO)
    mods = by_act.get("PO Modification", [])
    if not mods:
        viol["R4"] = False
    else:
        # compliant iff every mod is followed by a (re-)approval before PO confirm
        approvals = [e for e in evs if "Approval" in e["activity"]]
        ok = True
        for m in mods:
            after = [x for x in approvals if m["_ts"] < x["_ts"] and (not po or x["_ts"] < po["_ts"])]
            if not after:
                ok = False
        viol["R4"] = not ok
    # R5 payment after invoice
    pay = first("Payment")
    viol["R5"] = not (pay and inv and pay["_ts"] > inv["_ts"])
    # performance
    t0, t1 = evs[0]["_ts"], evs[-1]["_ts"]
    cycle = (t1 - t0).total_seconds() / 86400
    appr_wait = ((a["_ts"] - evs[0]["_ts"]).total_seconds() / 86400) if a else None
    rec_wait = ((r["_ts"] - po["_ts"]).total_seconds() / 86400) if (r and po) else None
    variant = tuple(e["activity"] for e in evs)
    return viol, variant, cycle, appr_wait, rec_wait, qr, qi

def main():
    base = Path(__file__).resolve().parent.parent / "data"
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else base / "event-log-r1.csv"
    cases = load(inp)
    tag = "r1" if "r1" in inp.name else ("r2" if "r2" in inp.name else inp.stem)
    out = base / f"conformance-{tag}.csv"
    var_c = Counter()
    scen_viol = defaultdict(Counter)
    scen_cycle = defaultdict(list)
    scen_appr = defaultdict(list)
    scen_rec = defaultdict(list)
    n_viol_rule = Counter()
    n_ok_total = 0
    scen_ok = Counter()
    rows = []
    for cid in sorted(cases):
        evs = cases[cid]
        scen = evs[0]["scenario"]
        viol, variant, cycle, aw, rw, qr, qi = check_case(evs)
        var_c[variant] += 1
        scen_cycle[scen].append(cycle)
        if aw is not None:
            scen_appr[scen].append(aw)
        if rw is not None:
            scen_rec[scen].append(rw)
        failed = [k for k in RULES if viol[k]]
        for k in failed:
            n_viol_rule[k] += 1
            scen_viol[scen][k] += 1
        if not failed:
            n_ok_total += 1
            scen_ok[scen] += 1
        rows.append([cid, scen, "->".join(v[:12] for v in variant),
                     ";".join(failed) if failed else "OK",
                     f"{cycle:.1f}", qr, qi])
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "scenario", "variant_short", "violations", "cycle_days", "qty_received", "qty_invoiced"])
        w.writerows(rows)
    # summary
    n_cases = len(cases)
    overall_rate = (n_ok_total / n_cases) if n_cases else 0.0
    print(f"Cases: {len(cases)}, Events: {sum(len(v) for v in cases.values())}")
    print(f"Overall conformance rate: {overall_rate:.1%} ({n_ok_total}/{n_cases} cases with zero violations)")
    print(f"Wrote {out}\n")
    print("== Variants ==")
    for v, c in var_c.most_common():
        print(f"  {c:2d}x  {' -> '.join(v)}")
    print("\n== Violations by rule ==")
    for k in RULES:
        print(f"  {k}: {n_viol_rule[k]} cases")
    print("\n== Violations x scenario ==")
    for s in sorted(scen_cycle):
        d = dict(scen_viol[s])
        print(f"  {s}: {d if d else 'no rule violations'}")
    print("\n== Conformance rate x scenario ==")
    for s in sorted(scen_cycle):
        n_s = len(scen_cycle[s])
        rate_s = (scen_ok[s] / n_s) if n_s else 0.0
        print(f"  {s}: {rate_s:.1%} ({scen_ok[s]}/{n_s} conformant)")
    print("\n== Performance (mean days) ==")
    for s in sorted(scen_cycle):
        cy = sum(scen_cycle[s]) / len(scen_cycle[s])
        med = statistics.median(scen_cycle[s])
        aw = sum(scen_appr[s]) / len(scen_appr[s]) if scen_appr[s] else 0
        rw = sum(scen_rec[s]) / len(scen_rec[s]) if scen_rec[s] else 0
        n_s = len(scen_cycle[s])
        rate_s = (scen_ok[s] / n_s) if n_s else 0.0
        print(f"  {s}: cycle={cy:.1f} (median={med:.1f})  PR->approval={aw:.1f}  PO->receipt={rw:.1f}  conformance={rate_s:.1%}")
    # second summary file: per-scenario aggregates
    summary_out = base / f"summary-{tag}.csv"
    with open(summary_out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "n_cases", "conformance_rate", "mean_cycle",
                    "median_cycle", "mean_approval_wait", "mean_receipt_wait",
                    "R1_viol", "R2_viol", "R3_viol", "R4_viol", "R5_viol"])
        for s in sorted(scen_cycle):
            n_s = len(scen_cycle[s])
            rate_s = (scen_ok[s] / n_s) if n_s else 0.0
            mean_cy = sum(scen_cycle[s]) / n_s if n_s else 0
            med_cy = statistics.median(scen_cycle[s]) if n_s else 0
            mean_aw = sum(scen_appr[s]) / len(scen_appr[s]) if scen_appr[s] else 0
            mean_rw = sum(scen_rec[s]) / len(scen_rec[s]) if scen_rec[s] else 0
            w.writerow([s, n_s, f"{rate_s:.4f}", f"{mean_cy:.4f}", f"{med_cy:.4f}",
                        f"{mean_aw:.4f}", f"{mean_rw:.4f}",
                        scen_viol[s]["R1"], scen_viol[s]["R2"], scen_viol[s]["R3"], scen_viol[s]["R4"], scen_viol[s]["R5"]])
    print(f"\nWrote {summary_out}")

if __name__ == "__main__":
    main()
