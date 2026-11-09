"""Planning aid, not evidence: how often would the frozen P1/P2 rules reach a
verdict, for a given number of passes, under ASSUMED run-to-run noise?

Synthetic runs as in test_analyze_synthetic.py. The noise (SD of log actions
per level and run) and the 10% per-level failure rate are guesses until real
passes exist; rerun with the noise measured in the first real passes.

Usage: python3 -I power_synthetic.py <levels.csv> [reps]
"""

import csv
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # sibling modules; -I drops the script directory

import analyze_ablation as A  # noqa: E402
from test_analyze_synthetic import make_runs  # noqa: E402

A.B = 1000  # fewer resamples than the frozen 10,000; fine for a planning estimate


def verdicts(levels, labels, passes, noise, mult_game, seed):
    runs = {}
    for i, (arm, mult) in enumerate((("game-g1", mult_game), ("levelup-g1", {}))):
        rows = make_runs(levels, mult, passes, seed=seed * 10 + i, noise=noise)
        runs[arm] = [dict(r, pass_key=f"p{r['pass']}") for r in rows]
    ca, _ = A.per_level(runs["game-g1"])
    cb, _ = A.per_level(runs["levelup-g1"])
    rng = random.Random(seed)
    p1 = A.verdict_p1(A.summary(A.level_diffs(ca, cb, labels, "S", "eff"), rng))
    p2 = A.verdict_p2(A.summary(A.level_diffs(ca, cb, labels, "N", "eff"), rng))
    return p1, p2


def main(levels_csv, reps):
    rows = list(csv.DictReader(open(levels_csv)))
    levels = {(r["game"], int(r["level"])): (int(r["human_baseline"]), r["label"]) for r in rows}
    labels = {(r["game"], int(r["level"])): r["label"] for r in rows}
    truths = {"S 20% fewer, N unchanged": {"S": 0.8, "N": 1.0}, "no effect": {}}
    print(f"{reps} synthetic replications per cell; noise = SD of log actions per level and run (assumed)")
    for noise in (0.3, 0.6):
        for passes in (2, 3, 4):
            for name, mult in truths.items():
                res = [verdicts(levels, labels, passes, noise, mult, seed=s) for s in range(reps)]
                p1 = sum(v[0] == "supported" for v in res) / reps
                p2 = sum(v[1].startswith("supported") for v in res) / reps
                print(f"noise {noise}  passes {passes}  truth: {name:26}  P1 supported {p1:4.0%}   P2 supported {p2:4.0%}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40)
