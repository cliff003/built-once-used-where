#!/usr/bin/env python3
"""JGV-2 analysis (paper-track/JGV2_REGISTRATION.md §3), the post hoc follow-up of R-08 (JGV).

Runs on the 120 public eval tasks, all Qwen3.8-27B-FP8 with the FN27 Q27 settings:
text at max_turns 6: T1 (seed 0), T2 (seed 1), T3 (seed 2); image at max_turns 6: V (seed 0), V2 (seed 1);
max_turns 12, seed 0: T12 (text), V12 (image). Each run dir holds submission.json (attempt_1 / attempt_2 per test
input); a test input counts when an attempt matches exactly, and a task scores the fraction of its test inputs that
count (ARC scoring). S(X) sums task scores; S(X+Y) is the oracle union of the four attempts of X and Y.

    python3 -I jgv2_analyze.py --solutions SOL --t1 D --t2 D --t3 D --v D --v2 D [--t12 D --v12 D] --out OUT.json

D1  primary: mean S(t+v) over the 6 text-image pairs minus mean S(t+t') over the 3 text-text pairs (max_turns 6)
D2  turn cap: [S(V12) - S(V)] - [S(T12) - S(T1)]   (only with --t12 and --v12)
D4  mean single-run S of the image runs minus that of the text runs
D5  submittable pair, R-08 M3 rule: attempt_1 = first run's attempt_1, attempt_2 = second run's attempt_1
    (first run's attempt_2 if equal); text first in text-image pairs, both orders averaged in text-text pairs
CIs: one paired bootstrap over tasks (10,000, random.Random(20261030)); each replicate resamples the tasks once and
recomputes every statistic on that sample; percentile 2.5% / 97.5%.
Verdict on D1 (R-08's rule): WORTH_PURSUING if D1 >= +3 and CI lower bound > 0; NO if D1 <= 0; else UNDETERMINED.
"""
import argparse
import itertools
import json
import os
import random
import statistics

TEXT, IMAGE = ("T1", "T2", "T3"), ("V", "V2")
TT = list(itertools.combinations(TEXT, 2))
TV = [(t, v) for t in TEXT for v in IMAGE]


def load(d):
    return json.load(open(os.path.join(d, "submission.json")))


def att(sub, tid, j, k):
    try:
        return sub[tid][j].get(f"attempt_{k}")
    except (KeyError, IndexError, AttributeError, TypeError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solutions", required=True)
    for r in ("t1", "t2", "t3", "v", "v2"):
        ap.add_argument(f"--{r}", required=True)
    ap.add_argument("--t12")
    ap.add_argument("--v12")
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    a = ap.parse_args()
    sol = json.load(open(a.solutions))
    dirs = {r.upper(): getattr(a, r) for r in ("t1", "t2", "t3", "v", "v2", "t12", "v12") if getattr(a, r)}
    runs = {r: load(d) for r, d in dirs.items()}
    cap = "T12" in runs and "V12" in runs
    tids = sorted(sol)
    n_inputs = sum(len(sol[t]) for t in tids)

    def score(t, members):
        return sum(any(c is not None and c == truth for c in (att(runs[r], t, j, k) for r in members for k in (1, 2)))
                   for j, truth in enumerate(sol[t])) / len(sol[t])

    def pair(t, first, second):
        n = 0
        for j, truth in enumerate(sol[t]):
            a1, b1 = att(runs[first], t, j, 1), att(runs[second], t, j, 1)
            guesses = [a1, b1 if b1 != a1 else att(runs[first], t, j, 2)]
            n += any(c is not None and c == truth for c in guesses)
        return n / len(sol[t])

    per = {}
    for t in tids:
        p = {r: score(t, [r]) for r in runs}
        for x, y in TT + TV:
            p[f"{x}+{y}"] = score(t, [x, y])
        p["pair_tv"] = sum(pair(t, x, y) for x, y in TV) / len(TV)
        p["pair_tt"] = sum(pair(t, x, y) + pair(t, y, x) for x, y in TT) / (2 * len(TT))
        per[t] = p

    stat = {
        "D1": lambda p: sum(p[f"{x}+{y}"] for x, y in TV) / len(TV) - sum(p[f"{x}+{y}"] for x, y in TT) / len(TT),
        "D4": lambda p: sum(p[v] for v in IMAGE) / len(IMAGE) - sum(p[t] for t in TEXT) / len(TEXT),
        "D5": lambda p: p["pair_tv"] - p["pair_tt"],
    }
    if cap:
        stat["cap_V"] = lambda p: p["V12"] - p["V"]
        stat["cap_T"] = lambda p: p["T12"] - p["T1"]
        stat["D2"] = lambda p: (p["V12"] - p["V"]) - (p["T12"] - p["T1"])
    vals = {k: [f(per[t]) for t in tids] for k, f in stat.items()}
    est = {k: sum(v) for k, v in vals.items()}
    rng = random.Random(20261030)
    boots = {k: [] for k in stat}
    for _ in range(a.boot):
        idx = [rng.randrange(len(tids)) for _ in tids]
        for k in stat:
            boots[k].append(sum(vals[k][i] for i in idx))
    ci = {}
    for k, b in boots.items():
        b.sort()
        ci[k] = [round(b[int(0.025 * a.boot)], 3), round(b[int(0.975 * a.boot) - 1], 3)]

    d1, lo, hi = est["D1"], ci["D1"][0], ci["D1"][1]
    verdict = "WORTH_PURSUING" if d1 >= 3 and lo > 0 else "NO" if d1 <= 0 else "UNDETERMINED"
    totals = {r: round(sum(per[t][r] for t in tids), 3) for r in runs}
    unions = {f"{x}+{y}": round(sum(per[t][f"{x}+{y}"] for t in tids), 3) for x, y in TT + TV}

    def table(x, y):
        c = {"both": 0, f"{x}_only": 0, f"{y}_only": 0, "neither": 0}
        for p in per.values():
            sx, sy = p[x] > 0, p[y] > 0
            c["both" if sx and sy else f"{x}_only" if sx else f"{y}_only" if sy else "neither"] += 1
        return c

    def missing(r):
        return sum(att(runs[r], t, j, 1) is None for t in tids for j in range(len(sol[t])))

    res = {
        "tasks": len(tids), "test_inputs": n_inputs, "totals": totals, "unions": unions,
        "D1": {"estimate": round(d1, 3), "ci95": ci["D1"], "verdict": verdict, "gain_ge3_excluded": hi < 3,
               "mean_text_image_union": round(sum(unions[f"{x}+{y}"] for x, y in TV) / len(TV), 3),
               "mean_text_text_union": round(sum(unions[f"{x}+{y}"] for x, y in TT) / len(TT), 3)},
        "D3": {"text_scores": [totals[t] for t in TEXT], "text_sd": round(statistics.stdev(totals[t] for t in TEXT), 3),
               "text_range": round(max(totals[t] for t in TEXT) - min(totals[t] for t in TEXT), 3),
               "image_scores": [totals[v] for v in IMAGE], "tables_text_pairs": {f"{x}_x_{y}": table(x, y) for x, y in TT}},
        "D4": {"estimate": round(est["D4"], 3), "ci95": ci["D4"]},
        "D5": {"estimate": round(est["D5"], 3), "ci95": ci["D5"],
               "pair_tv": round(sum(p["pair_tv"] for p in per.values()), 3),
               "pair_tt": round(sum(p["pair_tt"] for p in per.values()), 3)},
        "missing_attempt_1": {r: missing(r) for r in runs},
        "void_by_missing_gt5pct": {r: missing(r) > 0.05 * n_inputs for r in runs},
        "boot": a.boot, "per_task": per,
    }
    if cap:
        res["D2"] = {"estimate": round(est["D2"], 3), "ci95": ci["D2"],
                     "cap_V": {"estimate": round(est["cap_V"], 3), "ci95": ci["cap_V"]},
                     "cap_T": {"estimate": round(est["cap_T"], 3), "ci95": ci["cap_T"]},
                     "reading": "cap_helped_image_more" if ci["D2"][0] > 0 else
                                "cap_helped_text_more" if ci["D2"][1] < 0 else "not_distinguishable"}
    for r, d in dirs.items():
        try:
            res.setdefault("run_summaries", {})[r] = json.load(open(os.path.join(d, "run.json")))["summary"]
        except (OSError, KeyError, ValueError):
            pass
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("totals", "D1", "D2", "D3", "D4", "D5", "missing_attempt_1") if k in res},
                     indent=1))


if __name__ == "__main__":
    main()
