"""PM4Py mining for R1 P2P log: inductive miner + token fitness/precision + alignments."""
import json
from pathlib import Path

import pandas as pd
import pm4py

SCENARIOS = ["S1", "S2", "S3", "S4", "S5", "S6"]


def main():
    base = Path(__file__).resolve().parent.parent
    df = pd.read_csv(base / "data" / "event-log-r1.csv")
    df["case:concept:name"] = df["case_id"]
    df["concept:name"] = df["activity"]
    df["time:timestamp"] = pd.to_datetime(df["timestamp"])
    df["org:resource"] = df["resource"]
    log = pm4py.format_dataframe(df, case_id="case:concept:name",
                                 activity_key="concept:name",
                                 timestamp_key="time:timestamp")
    print(f"Cases: {log['case:concept:name'].nunique()}, Events: {len(log)}")
    net, im, fm = pm4py.discover_petri_net_inductive(log)
    print(f"Petri net: {len(net.places)} places, "
          f"{len(net.transitions)} transitions, {len(net.arcs)} arcs")
    fit = pm4py.fitness_token_based_replay(log, net, im, fm)
    prec = pm4py.precision_token_based_replay(log, net, im, fm)
    f = float(fit["log_fitness"] if isinstance(fit, dict) else fit)
    p = float(prec)
    print(f"Token-based fitness: {f:.4f}")
    print(f"Token-based precision: {p:.4f}")
    variants = pm4py.get_variants(log)
    n = len(variants)
    print(f"Variants: {n}")
    for v, cnt in sorted(variants.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cnt:2d}x  {' -> '.join(v)}")
    sampled = []
    for s in SCENARIOS:
        ids = sorted(df.loc[df["scenario"] == s, "case_id"].unique())
        if ids:
            sampled.append(ids[0])
    print(f"Alignment sample (1 per {SCENARIOS}): {sampled}")
    alignments_sample = []
    for cid in sampled:
        clog = log[log["case:concept:name"] == cid]
        diag = pm4py.conformance_diagnostics_alignments(clog, net, im, fm)[0]
        af = float(diag.get("fitness", 0.0))
        devs = [f"{lm}|{mm}" for lm, mm in diag.get("alignment", [])
                if lm != mm and lm is not None and mm is not None]
        alignments_sample.append({"case_id": cid, "fitness": af,
                                  "deviations": devs})
        print(f"  {cid}: fitness={af:.4f} deviations={len(devs)}")
    out = {"fitness": f, "precision": p, "variants_mined": n,
           "alignments_sample": alignments_sample}
    with open(base / "data" / "pm4py_results.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"Wrote data/pm4py_results.json fitness={f:.4f} "
          f"precision={p:.4f} variants={n}")


if __name__ == "__main__":
    main()
