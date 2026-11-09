"""Engineering check of analyze_ablation.py on SYNTHETIC runs with known effects.

These are made-up numbers in the results.json layout of run_public_eval.py.
They test that the frozen analysis returns the verdicts it should; they are
not evidence about any agent.

Usage: python3 -I test_analyze_synthetic.py <levels.csv> <scratch dir>
"""

import csv
import json
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# action multiplier per label for each arm; levelup-g1 is the reference
SCENARIOS = {
    "effect": {"game-g1": {"S": 0.8, "N": 1.0, "V": 0.9}, "levelup-g1": {},
               "game-g0": {"S": 0.8, "N": 1.35, "V": 0.9}, "levelup-g0": {}},
    "harm": {"game-g1": {"S": 0.8, "N": 1.3, "V": 1.0}, "levelup-g1": {}},
    "null": {"game-g1": {}, "levelup-g1": {}},
}
# expected verdict (text after the last "->") for report lines starting with each key
EXPECT = {
    "effect": {"P1": "supported", "P2": "supported (no harm beyond 10%)", "N:": "supported", "S:": "supported"},
    "harm": {"P1": "supported", "P2": "harm"},
    "null": {"P1": "inconclusive"},
}


def verdicts(text):
    out = {}
    for line in text.splitlines():
        s = line.strip()
        for key in ("P1", "P2", "N:", "S:"):
            if s.startswith(key) and "->" in s:
                out[key] = s.rsplit("->", 1)[1].strip()
    return out


def make_runs(levels, mult, passes, seed, noise=0.1, p_fail=0.1):
    """Synthetic runs: actions = baseline * multiplier * lognormal(noise);
    each level is failed (ending the game) with probability p_fail. The low
    default noise makes the expected verdicts deterministic for this check."""
    rng = random.Random(seed)
    games = sorted({g for g, _ in levels})
    rows = []
    for p in range(passes):
        for g in games:
            n = max(lv for gg, lv in levels if gg == g)
            done, acts = 0, []
            for lv in range(1, n + 1):
                h, lab = levels[(g, lv)]
                a = max(1, round(h * mult.get(lab, 1.0) * math.exp(rng.gauss(0, noise))))
                acts.append(a)
                if rng.random() < p_fail:
                    break
                done = lv
            rows.append({"pass": p, "game": g, "game_id": g, "levels_completed": done, "number_of_levels": n,
                         "actions_per_level": acts, "score": rng.uniform(10, 40),
                         "generated_tokens": int(rng.gauss(150_000, 5_000)), "turns": 100})
    return rows


def main(levels_csv, scratch):
    levels = {(r["game"], int(r["level"])): (int(r["human_baseline"]), r["label"])
              for r in csv.DictReader(open(levels_csv))}
    failures = 0
    for name, arms in SCENARIOS.items():
        root = os.path.join(scratch, name)
        for i, (arm, mult) in enumerate(arms.items()):
            for p in range(2):
                d = os.path.join(root, arm, f"pass{p}")
                os.makedirs(d, exist_ok=True)
                payload = {"config": {"args": {"max_generated_tokens_per_game": 165000}},
                           "runs": make_runs(levels, mult, 1, seed=1000 * i + p + hash(name) % 97)}
                json.dump(payload, open(os.path.join(d, "results.json"), "w"))
        out = subprocess.run([sys.executable, "-I", os.path.join(HERE, "analyze_ablation.py"), root, levels_csv],
                             capture_output=True, text=True)
        text = out.stdout + out.stderr
        got = verdicts(text)
        wrong = {k: (v, got.get(k)) for k, v in EXPECT[name].items() if got.get(k) != v}
        print(f"== synthetic scenario '{name}': {'OK' if not wrong and out.returncode == 0 else 'FAILED'}")
        print("\n".join("   " + line for line in text.strip().splitlines() if line.strip().startswith(("P1", "P2", "N:", "S:"))))
        if wrong or out.returncode:
            failures += 1
            print("   expected vs got:", wrong)
            print(text)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
