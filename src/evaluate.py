"""Masters-level evaluation: violation-rate reduction + throughput + vendor stratification.

Targeted cohorts (fixed experimental design):
  R1 targeted (S3/S4/S6): 60 violations / 60 cases (20+20+20)
  R2 targeted (S3R/S4R/S6R): 0 violations / 60 cases
  Overall context: R1 60/120 conformant, R2 60/60 conformant.

Methods:
  (a) Violation rates: chi-square (no Yates correction, 2x2), Fisher exact
      (two-sided, appropriate because cells contain 0), absolute + relative
      reduction, Cohen's h, 95% Wilson score CI per rate.
  (b) Throughput: per-case cycle time (days) derived DYNAMICALLY from
      data/event-log-r1.csv (max(timestamp)-min(timestamp) per case),
      S1 vs S2 Welch two-sample t-test (unequal variances), Welch-Satterthwaite
      df, Cohen's d (unequal-n, average-variance form). Cross-checked against
      data/summary-r1.csv mean_cycle values (read dynamically, never hardcoded).
  (c) Vendor stratification: case->vendor from data/event-log-r1.csv joined to
      case->violated from data/conformance-r1.csv (violations != "OK"),
      per-vendor n / violations / rate + 95% Wilson CI.

Writes data/evaluation.csv with columns metric,value.
Legacy metric names are preserved byte-identical.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.stats import chi2_contingency, fisher_exact, ttest_ind

BASE = Path(__file__).resolve().parent.parent / "data"
EVENT_R1 = BASE / "event-log-r1.csv"
SUMMARY_R1 = BASE / "summary-r1.csv"
CONF_R1 = BASE / "conformance-r1.csv"


def wilson_ci(k: int, n: int, z: float = 1.96):
    p = k / n if n else 0.0
    denom = 1.0 + z**2 / n if n else 1.0
    center = p + z**2 / (2 * n) if n else 0.0
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) if n else 0.0
    low = max(0.0, (center - margin) / denom)
    high = min(1.0, (center + margin) / denom)
    return float(low), float(high)


def load_case_cycles(event_path: Path):
    """Return {case_id: cycle_days}, {case_id: scenario} from event log."""
    case_ts: dict[str, list[datetime]] = defaultdict(list)
    case_scen: dict[str, str] = {}
    with event_path.open(newline="") as f:
        for row in csv.DictReader(f):
            cid = row["case_id"]
            case_ts[cid].append(datetime.fromisoformat(row["timestamp"]))
            case_scen[cid] = row["scenario"]
    cycles = {c: (max(v) - min(v)).total_seconds() / 86400.0 for c, v in case_ts.items()}
    return cycles, case_scen


def load_summary_means(summary_path: Path):
    """Return {scenario: mean_cycle} read dynamically from summary-r1.csv."""
    means: dict[str, float] = {}
    with summary_path.open(newline="") as f:
        for row in csv.DictReader(f):
            means[row["scenario"]] = float(row["mean_cycle"])
    return means


def load_vendor_map(event_path: Path):
    """Return {case_id: vendor} from event log."""
    mapping: dict[str, str] = {}
    with event_path.open(newline="") as f:
        for row in csv.DictReader(f):
            mapping[row["case_id"]] = row["vendor"]
    return mapping


def load_violated_map(conf_path: Path):
    """Return {case_id: violated_bool} (violations != 'OK')."""
    mapping: dict[str, bool] = {}
    with conf_path.open(newline="") as f:
        for row in csv.DictReader(f):
            mapping[row["case_id"]] = row["violations"].strip() != "OK"
    return mapping


def welch_df(a: np.ndarray, b: np.ndarray) -> float:
    v1, v2 = np.var(a, ddof=1), np.var(b, ddof=1)
    n1, n2 = len(a), len(b)
    num = (v1 / n1 + v2 / n2) ** 2
    den = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    return float(num / den) if den else float("nan")


def main() -> None:
    # ---- (a) Targeted violation-rate comparison (R1 S3+S4+S6 vs R2) ----
    r1_viol, r1_n = 60, 60
    r2_viol, r2_n = 0, 60

    r1_rate = r1_viol / r1_n
    r2_rate = r2_viol / r2_n

    abs_reduction = r1_rate - r2_rate
    rel_reduction = abs_reduction / r1_rate if r1_rate != 0 else 0.0

    # 2x2 contingency: rows=R1/R2, cols=[violations, non-violations]
    table = np.array([[r1_viol, r1_n - r1_viol], [r2_viol, r2_n - r2_viol]])
    chi2, p_value, _, _ = chi2_contingency(table, correction=False)

    # Fisher exact (two-sided): exact p for sparse/zero cells
    fisher_odds, fisher_p = fisher_exact(table, alternative="two-sided")

    # Cohen's h (magnitude)
    cohens_h = abs(2 * np.arcsin(np.sqrt(r2_rate)) - 2 * np.arcsin(np.sqrt(r1_rate)))

    r1_low, r1_high = wilson_ci(r1_viol, r1_n)
    r2_low, r2_high = wilson_ci(r2_viol, r2_n)

    # ---- (b) Throughput: Welch t-test S1 vs S2 cycle times ----
    cycles, case_scen = load_case_cycles(EVENT_R1)
    summary_means = load_summary_means(SUMMARY_R1)

    s1 = np.array(sorted(cycles[c] for c in cycles if case_scen[c] == "S1"), dtype=float)
    s2 = np.array(sorted(cycles[c] for c in cycles if case_scen[c] == "S2"), dtype=float)
    if len(s1) == 0 or len(s2) == 0:
        raise ValueError("S1/S2 cycle samples empty; check event-log-r1.csv")

    s1_n, s2_n = int(len(s1)), int(len(s2))
    s1_mean, s2_mean = float(np.mean(s1)), float(np.mean(s2))
    s1_std = float(np.std(s1, ddof=1)) if s1_n > 1 else 0.0
    s2_std = float(np.std(s2, ddof=1)) if s2_n > 1 else 0.0
    s1_med, s2_med = float(np.median(s1)), float(np.median(s2))

    # Summary cross-check (dynamically read, never hardcoded)
    s1_summary = float(summary_means.get("S1", float("nan")))
    s2_summary = float(summary_means.get("S2", float("nan")))

    t_res = ttest_ind(s1, s2, equal_var=False)  # Welch, two-sided
    welch_t = float(t_res.statistic)
    welch_p = float(t_res.pvalue)
    # Prefer scipy df when available, else manual Welch-Satterthwaite
    try:
        df_val = float(t_res.df)  # type: ignore[attr-defined]
    except Exception:
        df_val = welch_df(s1, s2)
    if not np.isfinite(df_val):
        df_val = welch_df(s1, s2)

    mean_diff = s2_mean - s1_mean  # S2 minus S1 (positive = S2 slower)
    pooled_sd = np.sqrt((s1_std**2 + s2_std**2) / 2.0) if (s1_std or s2_std) else float("nan")
    cohens_d = float(mean_diff / pooled_sd) if pooled_sd and np.isfinite(pooled_sd) else float("nan")

    # ---- (c) Vendor-stratified violation rates ----
    case_vendor = load_vendor_map(EVENT_R1)
    violated = load_violated_map(CONF_R1)
    vendor_stats: dict[str, tuple[int, int, float, float, float]] = {}
    for vendor in ("Vendor_A", "Vendor_B", "Vendor_C"):
        cases = [c for c, v in case_vendor.items() if v == vendor and c in violated]
        n = len(cases)
        nv = sum(1 for c in cases if violated[c])
        rate = nv / n if n else 0.0
        lo, hi = wilson_ci(nv, n) if n else (0.0, 0.0)
        vendor_stats[vendor] = (n, nv, rate, lo, hi)

    rows: list[tuple[str, object]] = [
        # Legacy (names identical)
        ("r1_viol_rate", r1_rate),
        ("r2_viol_rate", r2_rate),
        ("abs_reduction", abs_reduction),
        ("rel_reduction", rel_reduction),
        ("chi2", float(chi2)),
        ("p_value", float(p_value)),
        ("cohens_h", float(cohens_h)),
        ("r1_ci_low", float(r1_low)),
        ("r1_ci_high", float(r1_high)),
        ("r2_ci_low", float(r2_low)),
        ("r2_ci_high", float(r2_high)),
        # Fisher exact
        ("fisher_p", float(fisher_p)),
        ("fisher_oddsratio", float(fisher_odds)),
        # Throughput (Welch S1 vs S2)
        ("s1_n", s1_n),
        ("s2_n", s2_n),
        ("s1_mean_cycle", s1_mean),
        ("s2_mean_cycle", s2_mean),
        ("s1_std_cycle", s1_std),
        ("s2_std_cycle", s2_std),
        ("s1_median_cycle", s1_med),
        ("s2_median_cycle", s2_med),
        ("s1_summary_mean_cycle", s1_summary),
        ("s2_summary_mean_cycle", s2_summary),
        ("s1_s2_mean_diff", float(s1_mean - s2_mean)),
        ("s2_minus_s1_diff", float(mean_diff)),
        ("welch_t", welch_t),
        ("welch_df", float(df_val)),
        ("welch_p", welch_p),
        ("cohens_d_cycle", float(cohens_d)),
    ]
    for vendor in ("Vendor_A", "Vendor_B", "Vendor_C"):
        n, nv, rate, lo, hi = vendor_stats[vendor]
        pfx = vendor  # e.g. Vendor_A
        rows += [
            (f"{pfx}_n", n),
            (f"{pfx}_viol", nv),
            (f"{pfx}_viol_rate", rate),
            (f"{pfx}_ci_low", lo),
            (f"{pfx}_ci_high", hi),
        ]

    out_path = BASE / "evaluation.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        f.write("metric,value\n")
        for metric, value in rows:
            if isinstance(value, float):
                if np.isinf(value):
                    f.write(f"{metric},inf\n")
                elif np.isnan(value):
                    f.write(f"{metric},nan\n")
                else:
                    f.write(f"{metric},{value:.10g}\n")
            else:
                f.write(f"{metric},{value}\n")

    print(f"Wrote {out_path}")
    for metric, value in rows:
        if isinstance(value, float):
            print(f"{metric}={value:.10g}")
        else:
            print(f"{metric}={value}")


if __name__ == "__main__":
    main()
