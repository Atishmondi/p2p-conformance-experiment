"""Compare lab vs field rates: Wilson 95% CI + two-proportion z-test."""
import csv
import numpy as np
from scipy import stats

Z = stats.norm.ppf(0.975)  # 1.9599... 95% two-sided

def wilson_ci(x, n, z=Z):
    if n is None or n == 0 or x is None:
        return (float("nan"), float("nan"))
    p = x / n
    denom = 1.0 + z * z / n
    center = p + z * z / (2.0 * n)
    delta = z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return ((center - delta) / denom, (center + delta) / denom)

def two_prop_z_p(x1, n1, x2, n2):
    if n1 is None or n2 is None or n1 == 0 or n2 == 0 or x1 is None or x2 is None:
        return float("nan")
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n1 + 1.0 / n2))
    if se == 0:
        return 1.0 if p1 == p2 else 0.0
    z = (p1 - p2) / se
    return float(2.0 * stats.norm.sf(abs(z)))

pairs = [
    # rule, lab_true, lab_n, field_true, field_n
    ("R2", 20, 20, 0, 11128),
    ("R3-after", 20, 20, 1584, 11128),
    ("R4-3way", 20, 20, 1882 + 23315, 15182 + 221010),
    ("R1-2way", None, None, 590, 1044),
]

out_path = "data/comparison.csv"
with open(out_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["rule", "lab_true", "lab_n", "field_true", "field_n",
                "lab_rate", "field_rate", "diff",
                "lab_ci_low", "lab_ci_high",
                "field_ci_low", "field_ci_high", "z_p"])
    for rule, lx, ln, fx, fn in pairs:
        lab_rate = (lx / ln) if (lx is not None and ln) else float("nan")
        field_rate = (fx / fn) if (fx is not None and fn) else float("nan")
        diff = abs(lab_rate - field_rate) if (np.isfinite(lab_rate) and np.isfinite(field_rate)) else float("nan")
        lab_low, lab_high = wilson_ci(lx, ln)
        field_low, field_high = wilson_ci(fx, fn)
        z_p = two_prop_z_p(lx, ln, fx, fn)
        w.writerow([rule, lx if lx is not None else "", ln if ln is not None else "",
                    fx, fn, lab_rate, field_rate, diff,
                    lab_low, lab_high, field_low, field_high, z_p])

print(f"wrote {out_path}")
for rule, lx, ln, fx, fn in pairs:
    lab_rate = (lx / ln) if (lx is not None and ln) else float("nan")
    field_rate = fx / fn
    diff = abs(lab_rate - field_rate) if np.isfinite(lab_rate) else float("nan")
    print(rule, f"lab={lx}/{ln}={lab_rate:.6f}", f"field={fx}/{fn}={field_rate:.6f}",
          f"diff={diff:.6f}", f"z_p={two_prop_z_p(lx, ln, fx, fn):.6g}")
