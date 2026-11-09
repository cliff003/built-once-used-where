"""Merge rendered-frame features with the manual labels into levels.csv and
print summary statistics plus a check of the labels against human baselines.

Usage: python3 -I build_table.py <level_annotation dir>
"""

import csv
import json
import math
import os
import random
import statistics as st
import sys
from collections import Counter, defaultdict


def main(d):
    games = json.load(open(os.path.join(d, "features.json")))
    labels = {(r["game"], int(r["level"])): r for r in csv.DictReader(open(os.path.join(d, "manual_labels.csv")))}
    rows = []
    for g in games:
        gid, n = g["game_id"][:4], g["n_levels"]
        total_w = n * (n + 1) / 2
        h = g["baseline_actions"]
        for e in g["levels"]:
            lv = e["level"]
            lab = labels.get((gid, lv))
            prev = h[:lv - 1]
            rows.append({
                "game": gid,
                "level": lv,
                "n_levels": n,
                "human_baseline": h[lv - 1],
                "score_weight": round(lv / total_w, 4),
                "baseline_ratio_to_earlier_median": round(h[lv - 1] / st.median(prev), 3) if prev else "",
                "label": lab["label"] if lab else ("first" if lv == 1 else "MISSING"),
                "note": lab["note"] if lab else "",
                "auto_new_colors": " ".join(map(str, e.get("new_colors", []))),
                "auto_new_object_types": e.get("new_object_types", ""),
            })
    out = os.path.join(d, "levels.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    later = [r for r in rows if r["level"] > 1]
    missing = [r for r in later if r["label"] == "MISSING"]
    print(f"levels: {len(rows)} total, {len(later)} after level 1, {len(missing)} missing labels")
    cnt = Counter(r["label"] for r in later)
    print("labels after level 1:", {k: f"{v} ({100 * v / len(later):.0f}%)" for k, v in sorted(cnt.items())})

    # share of each game's score weight that sits on S / V / N levels (level 1 separate)
    share = defaultdict(list)
    for gid in sorted({r["game"] for r in rows}):
        gr = [r for r in rows if r["game"] == gid]
        for lab in ("first", "S", "V", "N"):
            share[lab].append(sum(r["score_weight"] for r in gr if r["label"] == lab))
    print("mean share of game score weight:", {k: f"{100 * st.mean(v):.1f}%" for k, v in share.items()})

    per_game = {gid: "".join(r["label"] for r in rows if r["game"] == gid and r["level"] > 1)
                for gid in sorted({r["game"] for r in rows})}
    print("per game (levels 2..L):", " ".join(f"{g}:{s}" for g, s in per_game.items()))

    # check: do N levels need relatively more human actions than S levels?
    lr = {lab: [math.log(r["baseline_ratio_to_earlier_median"]) for r in later if r["label"] == lab]
          for lab in ("S", "V", "N")}
    for lab, v in lr.items():
        print(f"  {lab}: n={len(v):3d}  median ratio of human actions to earlier levels = {math.exp(st.median(v)):.2f}")
    obs = st.mean(lr["N"]) - st.mean(lr["S"])
    pooled, nN = lr["N"] + lr["S"], len(lr["N"])
    rng, hits, reps = random.Random(0), 0, 20000
    for _ in range(reps):
        rng.shuffle(pooled)
        if st.mean(pooled[:nN]) - st.mean(pooled[nN:]) >= obs:
            hits += 1
    print(f"  N vs S difference in mean log ratio = {obs:.3f} (x{math.exp(obs):.2f}); "
          f"one-sided permutation p = {(hits + 1) / (reps + 1):.4f}")

    # agreement of the crude automatic signal (any new color) with the manual N label
    tab = Counter((r["label"], bool(r["auto_new_colors"])) for r in later)
    print("auto new color vs manual label:", {f"{k[0]}/{'newcolor' if k[1] else 'none'}": v
                                              for k, v in sorted(tab.items())})
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
