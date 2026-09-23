"""Run manager: generate + check + log runs to data/runs.csv.

Owns ONLY src/run_manager.py + data/runs.csv + data/runs/ dir.
Does NOT modify generators / checker / webpage.

Usage:
  python3 src/run_manager.py [--n N] [--era r1|r2|both] [--tag TAG] [--seed S]
                             [--seed-r1 S1] [--seed-r2 S2]

- --n: per-scenario cases (default 20)
- --era: r1 / r2 / both (default both)
- --tag: run id suffix, dir data/runs/<tag>/ (default UTC timestamp YYYYMMDD-HHMM)
- --seed: explicit seed (single-era runs; if era=both, applies to both
          unless --seed-r1/--seed-r2 override). If omitted, random per era.
- --seed-r1 / --seed-r2: per-era explicit seeds (override --seed).

Per era it:
  1. runs generate_log.py (r1) or generate_log_r2.py (r2) with
     --n X --seed <seed> --out data/runs/<tag>/event-log-<era>.csv
  2. runs check_conformance.py on that event log
     (checker writes data/conformance-<era>.csv + data/summary-<era>.csv;
     we snapshot copies into data/runs/<tag>/ for provenance)
  3. computes violation rate + mean cycle from the conformance CSV
  4. appends ONE row per era to data/runs.csv (creates with header if missing):
     run_id,utc_time,era,n_per_scenario,seed,cases,events,viol_rate,mean_cycle

Stdlib + subprocess only.
"""
import argparse
import csv
import random
import shutil
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DATA = ROOT / "data"
RUNS_CSV = DATA / "runs.csv"
RUNS_DIR = DATA / "runs"
HEADER = ["run_id", "utc_time", "era", "n_per_scenario", "seed",
          "cases", "events", "viol_rate", "mean_cycle"]

GEN = {"r1": SRC / "generate_log.py", "r2": SRC / "generate_log_r2.py"}


def default_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Generate + check + log runs.")
    p.add_argument("--n", type=int, default=20,
                   help="per-scenario cases (default: 20)")
    p.add_argument("--era", choices=["r1", "r2", "both"], default="both",
                   help="which era to run (default: both)")
    p.add_argument("--tag", type=str, default=None,
                   help="run id suffix, dir data/runs/<tag>/ "
                        "(default: UTC timestamp YYYYMMDD-HHMM)")
    p.add_argument("--seed", type=int, default=None,
                   help="explicit seed (single-era; or both eras if --era both "
                        "and no per-era override)")
    p.add_argument("--seed-r1", type=int, default=None,
                   help="explicit seed for r1 (overrides --seed)")
    p.add_argument("--seed-r2", type=int, default=None,
                   help="explicit seed for r2 (overrides --seed)")
    return p.parse_args(argv)


def run_cmd(cmd):
    print(f"+ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def compute_metrics(conformance_csv: Path, event_log_csv: Path):
    with open(conformance_csv, newline="") as f:
        rows = list(csv.DictReader(f))
    cases = len(rows)
    n_viol = sum(1 for r in rows if (r.get("violations", "").strip() not in ("", "OK")))
    viol_rate = (n_viol / cases) if cases else 0.0
    cycles = []
    for r in rows:
        try:
            cycles.append(float(r["cycle_days"]))
        except Exception:
            pass
    mean_cycle = statistics.fmean(cycles) if cycles else 0.0
    with open(event_log_csv, newline="") as f:
        events = sum(1 for _ in f) - 1  # minus header
    events = max(0, events)
    return cases, events, viol_rate, mean_cycle


def ensure_runs_csv():
    DATA.mkdir(parents=True, exist_ok=True)
    if not RUNS_CSV.exists():
        with open(RUNS_CSV, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(HEADER)


def run_era(era: str, n: int, seed: int, tag: str, utc_time: str):
    out_log = RUNS_DIR / tag / f"event-log-{era}.csv"
    out_log.parent.mkdir(parents=True, exist_ok=True)
    # 1. generate
    run_cmd([sys.executable, str(GEN[era]),
             "--n", str(n), "--seed", str(seed), "--out", str(out_log)])
    # 2.+3. check conformance + metrics, with backup/restore of central files.
    # Checker writes centrally to data/conformance-<era>.csv +
    # data/summary-<era>.csv, overwriting canonical files. Back up bytes
    # in memory before the call and restore in finally so canonical
    # files are preserved; per-run outputs are snapshotted into
    # data/runs/<tag>/ for provenance.
    central_orig = DATA / f"conformance-{era}.csv"
    summary_orig = DATA / f"summary-{era}.csv"
    alt = DATA / f"conformance-{out_log.stem}.csv"
    conf_backup = central_orig.read_bytes() if central_orig.exists() else None
    summ_backup = summary_orig.read_bytes() if summary_orig.exists() else None
    alt_existed = alt.exists()
    central = central_orig
    try:
        # 2. check conformance (writes central conformance + summary)
        run_cmd([sys.executable, str(SRC / "check_conformance.py"), str(out_log)])
        # 3. metrics from the conformance CSV
        if not central.exists():
            # fallback: checker may have used stem tag (only if filename lacked r1/r2)
            if alt.exists():
                central = alt
            else:
                raise FileNotFoundError(f"expected conformance CSV not found: {central}")
        cases, events, viol_rate, mean_cycle = compute_metrics(central, out_log)
        # snapshot central outputs into runs dir for provenance
        try:
            shutil.copy2(str(central), str(RUNS_DIR / tag / f"conformance-{era}.csv"))
        except Exception as e:
            print(f"warning: snapshot conformance failed: {e}", file=sys.stderr)
        if summary_orig.exists():
            try:
                shutil.copy2(str(summary_orig), str(RUNS_DIR / tag / f"summary-{era}.csv"))
            except Exception as e:
                print(f"warning: snapshot summary failed: {e}", file=sys.stderr)
        # 4. append ONE row per era
        ensure_runs_csv()
        run_id = f"{tag}-{era}"
        with open(RUNS_CSV, "a", newline="") as f:
            w = csv.writer(f)
            w.writerow([run_id, utc_time, era, n, seed, cases, events,
                        f"{viol_rate:.4f}", f"{mean_cycle:.4f}"])
        print(f"logged {run_id}: seed={seed} cases={cases} events={events} "
              f"viol_rate={viol_rate:.4f} mean_cycle={mean_cycle:.4f}")
        return run_id
    finally:
        # restore canonical central files; remove checker artifacts that
        # did not exist before this call.
        try:
            if conf_backup is not None:
                central_orig.write_bytes(conf_backup)
            elif central_orig.exists():
                central_orig.unlink()
        except Exception as e:
            print(f"warning: restore conformance failed: {e}", file=sys.stderr)
        try:
            if summ_backup is not None:
                summary_orig.write_bytes(summ_backup)
            elif summary_orig.exists():
                summary_orig.unlink()
        except Exception as e:
            print(f"warning: restore summary failed: {e}", file=sys.stderr)
        # Clean stray alt artifact if checker used a stem-named file
        # distinct from the standard central path.
        try:
            if alt != central_orig and alt.exists() and not alt_existed:
                alt.unlink()
        except Exception as e:
            print(f"warning: cleanup alt conformance failed: {e}", file=sys.stderr)


def main(argv=None):
    args = parse_args(argv)
    tag = args.tag if args.tag else default_tag()
    eras = ["r1", "r2"] if args.era == "both" else [args.era]
    utc_time = datetime.now(timezone.utc).isoformat(timespec="seconds")
    seeds = {}
    for era in eras:
        per = args.seed_r1 if era == "r1" else args.seed_r2
        if per is not None:
            seeds[era] = per
        elif args.seed is not None:
            seeds[era] = args.seed
        else:
            seeds[era] = random.randint(0, 2 ** 31 - 1)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / tag).mkdir(parents=True, exist_ok=True)
    for era in eras:
        run_era(era, args.n, seeds[era], tag, utc_time)
    print(f"done tag={tag} eras={eras}")


if __name__ == "__main__":
    main()
