# Robustness check of the S/N labels against human baselines:
# log(h_l / h_{l-1}) and log(h_l / median earlier) ~ label + level index + game fixed effects.
import csv, sys, math
import numpy as np
rows = [r for r in csv.DictReader(open(sys.argv[1])) if int(r["level"]) > 1]
games = sorted({r["game"] for r in rows})
h = {}
for r in csv.DictReader(open(sys.argv[1])):
    h[(r["game"], int(r["level"]))] = int(r["human_baseline"])
def fit(ycol):
    X, y = [], []
    for r in rows:
        if r["label"] not in ("S", "N", "V"): continue
        lv = int(r["level"])
        if ycol == "prev":
            yv = math.log(h[(r["game"], lv)] / h[(r["game"], lv - 1)])
        else:
            yv = math.log(float(r["baseline_ratio_to_earlier_median"]))
        x = [1.0 if r["label"] == "N" else 0.0, 1.0 if r["label"] == "V" else 0.0, lv / int(r["n_levels"])]
        x += [1.0 if r["game"] == g else 0.0 for g in games]
        X.append(x); y.append(yv)
    X, y = np.array(X), np.array(y)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, p = X.shape
    sigma2 = resid @ resid / (n - p)
    cov = sigma2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    return beta[:3], se[:3], n
for ycol, name in (("prev", "log(h_l / h_(l-1))"), ("med", "log(h_l / median earlier)")):
    b, se, n = fit(ycol)
    print(f"{name}: n={n}  N-vs-S = {b[0]:+.3f} (se {se[0]:.3f}, x{math.exp(b[0]):.2f})  "
          f"V-vs-S = {b[1]:+.3f} (se {se[1]:.3f})  relative position = {b[2]:+.3f} (se {se[2]:.3f})")
# label mix by position
pos = {"early (2-3)": [], "middle": [], "last two": []}
for r in rows:
    lv, L = int(r["level"]), int(r["n_levels"])
    k = "early (2-3)" if lv <= 3 else ("last two" if lv >= L - 1 else "middle")
    pos[k].append(r["label"])
for k, v in pos.items():
    print(f"{k:12} n={len(v):3d}  N={v.count('N')/len(v):.0%}  S={v.count('S')/len(v):.0%}  V={v.count('V')/len(v):.0%}")
