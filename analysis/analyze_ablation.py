"""Pre-registered analysis of the carried-code ablation (PREREGISTRATION.md).

Reads every results.json written by ARC-AGI-3/pace/harness/run_public_eval.py
below each arm directory, joins levels to the frozen S/V/N labels, and prints
the verdicts for P1/P2 and the secondary analyses S1-S5.

Usage:
  python3 -I analyze_ablation.py <runs root> <levels.csv> [--json report.json]

<runs root> holds one directory per arm: game-g1, levelup-g1 and, for the full
2x2, game-g0 and levelup-g0. Use a separate root per model.
"""

import argparse
import csv
import glob
import json
import math
import os
import random
import statistics as st
from collections import defaultdict

B = 10_000
SEED = 20261025
LO, HI = 0.05, 0.95  # 90% percentile interval
P1_EFFECT = math.log(0.90)
NONINF = math.log(1.10)
COMPLETION_MARGIN = -0.10
TOKEN_TOLERANCE = 0.10
MIN_GAMES, MIN_LEVELS = 8, 15
INVALID_PASS_SHARE = 0.20


def load_labels(path):
    labels, n_levels = {}, {}
    for r in csv.DictReader(open(path)):
        g, lv = r["game"], int(r["level"])
        labels[(g, lv)] = r["label"]
        n_levels[g] = int(r["n_levels"])
    return labels, n_levels


def load_arm(arm_dir):
    """Valid run rows of one arm, each tagged with a unique pass key."""
    runs, invalid, configs, pass_counts = [], [], [], defaultdict(lambda: [0, 0])
    for path in sorted(glob.glob(os.path.join(arm_dir, "**", "results.json"), recursive=True)):
        payload = json.load(open(path))
        configs.append(payload.get("config", {}))
        rel = os.path.relpath(path, arm_dir)
        for row in payload.get("runs", []):
            key = f"{rel}#{row.get('pass', 0)}"
            pass_counts[key][0] += 1
            if not row.get("generated_tokens") or not row.get("turns"):
                invalid.append((key, row.get("game")))
                pass_counts[key][1] += 1
                continue
            runs.append(dict(row, pass_key=key))
    bad_passes = sorted(k for k, (n, bad) in pass_counts.items() if n and bad / n > INVALID_PASS_SHARE)
    runs = [r for r in runs if r["pass_key"] not in bad_passes]
    return runs, invalid, bad_passes, configs, len(pass_counts) - len(bad_passes)


def per_level(runs, tokens_adjusted=False):
    """(game, level) -> reached, completed, log actions over passes that completed."""
    out = defaultdict(lambda: {"reached": 0, "completed": 0, "logs": []})
    dropped = []
    for r in runs:
        done, n = int(r["levels_completed"]), int(r["number_of_levels"])
        acts = r.get("actions_per_level") or []
        offset = math.log(r["generated_tokens"] / 1000) if tokens_adjusted else 0.0
        for lv in range(1, min(done + 1, n) + 1):
            cell = out[(r["game"], lv)]
            cell["reached"] += 1
            if lv <= done:
                a = acts[lv - 1] if lv - 1 < len(acts) else None
                if not a or a <= 0:
                    dropped.append((r["pass_key"], r["game"], lv))
                    continue
                cell["completed"] += 1
                cell["logs"].append(math.log(a) - offset)
    return out, dropped


def level_diffs(cells_a, cells_b, labels, stratum, kind):
    """Per-level differences A - B for one stratum; kind is 'eff' or 'comp'."""
    diffs = []
    for key, lab in labels.items():
        if lab != stratum:
            continue
        a, b = cells_a.get(key), cells_b.get(key)
        if not a or not b:
            continue
        if kind == "eff" and a["logs"] and b["logs"]:
            diffs.append((key, st.mean(a["logs"]) - st.mean(b["logs"])))
        elif kind == "comp" and a["reached"] and b["reached"]:
            diffs.append((key, a["completed"] / a["reached"] - b["completed"] / b["reached"]))
    return diffs


def by_game(diffs):
    g = defaultdict(list)
    for (game, _), d in diffs:
        g[game].append(d)
    return {k: st.mean(v) for k, v in g.items()}


def boot_mean(game_values, rng):
    games = sorted(game_values)
    if not games:
        return None, None, None
    est = st.mean(game_values[g] for g in games)
    sims = sorted(st.mean(game_values[rng.choice(games)] for _ in games) for _ in range(B))
    return est, sims[int(LO * B)], sims[int(HI * B) - 1]


def summary(diffs, rng):
    gv = by_game(diffs)
    est, lo, hi = boot_mean(gv, rng)
    return {"estimate": est, "lo90": lo, "hi90": hi, "games": len(gv), "levels": len(diffs)}


def enough(s):
    return s["games"] >= MIN_GAMES and s["levels"] >= MIN_LEVELS


def above(x, threshold):
    return x is not None and x > threshold


def below(x, threshold):
    return x is not None and x < threshold


def verdict_p1(s):
    if not enough(s):
        return "insufficient data"
    if below(s["hi90"], 0) and s["estimate"] <= P1_EFFECT:
        return "supported"
    if above(s["lo90"], 0):
        return "contradicted"
    return "inconclusive"


def verdict_p2(s):
    if not enough(s):
        return "insufficient data"
    if below(s["hi90"], NONINF):
        return "supported (no harm beyond 10%)"
    if above(s["lo90"], 0):
        return "harm"
    return "inconclusive"


def slope(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return None if sxx == 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def position_slope(diffs, n_levels, rng):
    pts = defaultdict(list)
    for (game, lv), d in diffs:
        pts[game].append((lv / n_levels[game], d))
    games = sorted(pts)
    flat = [p for g in games for p in pts[g]]
    est = slope(flat) if len(flat) > 2 else None
    if est is None:
        return {"estimate": None, "lo90": None, "hi90": None, "late_levels": 0, "verdict": "insufficient data"}
    sims = []
    for _ in range(B):
        sample = [p for _ in games for p in pts[rng.choice(games)]]
        s = slope(sample)
        if s is not None:
            sims.append(s)
    sims.sort()
    lo, hi = sims[int(LO * len(sims))], sims[int(HI * len(sims)) - 1]
    late = sum(1 for x, _ in flat if x > 2 / 3)
    verdict = "supported" if hi < 0 else "not supported"
    if late < 10:
        verdict += " (exploratory: <10 late S levels)"
    return {"estimate": est, "lo90": lo, "hi90": hi, "late_levels": late, "verdict": verdict}


def game_means(runs, field):
    vals = defaultdict(list)
    for r in runs:
        vals[r["game"]].append(float(r.get(field) or 0.0))
    return {g: st.mean(v) for g, v in vals.items()}


def paired_game_diff(a, b, rng):
    common = {g: a[g] - b[g] for g in a if g in b}
    est, lo, hi = boot_mean(common, rng)
    return {"estimate": est, "lo90": lo, "hi90": hi, "games": len(common)}


def contrast(arms, a, b, labels, n_levels, rng, tokens_adjusted=False):
    ca, drop_a = per_level(arms[a]["runs"], tokens_adjusted)
    cb, drop_b = per_level(arms[b]["runs"], tokens_adjusted)
    res = {"arms": f"{a} - {b}", "dropped_levels": drop_a + drop_b}
    for stratum in ("S", "N", "V"):
        res[f"eff_{stratum}"] = summary(level_diffs(ca, cb, labels, stratum, "eff"), rng)
        res[f"comp_{stratum}"] = summary(level_diffs(ca, cb, labels, stratum, "comp"), rng)
    res["P1"] = verdict_p1(res["eff_S"])
    res["P2"] = verdict_p2(res["eff_N"])
    res["S1_S"] = "helps" if above(res["comp_S"]["lo90"], 0) else "not shown"
    res["S1_N"] = "no harm beyond 10 points" if above(res["comp_N"]["lo90"], COMPLETION_MARGIN) else "not shown"
    res["S2_score"] = paired_game_diff(game_means(arms[a]["runs"], "score"), game_means(arms[b]["runs"], "score"), rng)
    res["S2"] = "improves" if above(res["S2_score"]["lo90"], 0) else "not shown"
    res["S3"] = position_slope(level_diffs(ca, cb, labels, "S", "eff"), n_levels, rng)
    ta, tb = game_means(arms[a]["runs"], "generated_tokens"), game_means(arms[b]["runs"], "generated_tokens")
    mean_a = st.mean(ta.values()) if ta else 0.0
    mean_b = st.mean(tb.values()) if tb else 0.0
    ratio = mean_a / mean_b if mean_b else None
    res["S4_tokens"] = {"mean_a": mean_a, "mean_b": mean_b, "ratio": ratio}
    res["S4_flag"] = ratio is not None and abs(ratio - 1) > TOKEN_TOLERANCE
    res["_cells"] = (ca, cb)
    return res


def guidance_interaction(c1, c0, labels, rng):
    """S5: compares the R contrast at G=0 with the R contrast at G=1."""
    out = {}
    for stratum in ("N", "S"):
        g1 = by_game(level_diffs(*c1["_cells"], labels, stratum, "eff"))
        g0 = by_game(level_diffs(*c0["_cells"], labels, stratum, "eff"))
        diff = {g: (g0[g] - g1[g]) if stratum == "N" else (g1[g] - g0[g]) for g in g1 if g in g0}
        est, lo, hi = boot_mean(diff, rng)
        out[stratum] = {"estimate": est, "lo90": lo, "hi90": hi, "games": len(diff)}
    out["N_verdict"] = "supported" if above(out["N"]["lo90"], 0) else "not supported"
    out["S_verdict"] = "supported" if below(out["S"]["hi90"], NONINF) else "not supported"
    return out


def fmt(s):
    if s["estimate"] is None:
        return f"no comparable data (games={s['games']})"
    return (f"{s['estimate']:+.3f} [{s['lo90']:+.3f}, {s['hi90']:+.3f}]"
            f"  games={s['games']} levels={s.get('levels', '-')}")


def within_arm_noise(runs):
    """Pooled SD of log actions across passes of the same arm (blinded check)."""
    by_level = defaultdict(list)
    for r in runs:
        acts = r.get("actions_per_level") or []
        for lv in range(1, int(r["levels_completed"]) + 1):
            if lv - 1 < len(acts) and acts[lv - 1] and acts[lv - 1] > 0:
                by_level[(r["game"], lv)].append(math.log(acts[lv - 1]))
    num = den = 0.0
    for v in by_level.values():
        if len(v) >= 2:
            num += st.variance(v) * (len(v) - 1)
            den += len(v) - 1
    return (math.sqrt(num / den) if den else None), int(den)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_root")
    ap.add_argument("levels_csv")
    ap.add_argument("--json", default=None)
    ap.add_argument("--noise-only", action="store_true",
                    help="print within-arm noise only, no between-arm comparison (pre-registered pass rule)")
    args = ap.parse_args()
    labels, n_levels = load_labels(args.levels_csv)
    rng = random.Random(SEED)

    arms = {}
    for name in ("game-g1", "levelup-g1", "game-g0", "levelup-g0"):
        d = os.path.join(args.runs_root, name)
        if os.path.isdir(d):
            runs, invalid, bad, configs, n_pass = load_arm(d)
            arms[name] = {"runs": runs, "invalid": invalid, "bad_passes": bad, "configs": configs, "passes": n_pass}
    print("arms found:", {k: f'{v["passes"]} valid passes, {len(v["runs"])} runs' for k, v in arms.items()})
    for k, v in arms.items():
        if v["invalid"] or v["bad_passes"]:
            print(f"  {k}: dropped {len(v['invalid'])} invalid runs; invalid passes {v['bad_passes']}")
        if v["passes"] < 2:
            print(f"  WARNING {k}: fewer than 2 valid passes (pre-registered minimum)")
        caps = {json.dumps((c.get("args") or {}).get("max_generated_tokens_per_game")) for c in v["configs"]}
        print(f"  {k}: max_generated_tokens_per_game values {sorted(caps)}")

    if args.noise_only:
        pooled = []
        for k, v in arms.items():
            sd, df = within_arm_noise(v["runs"])
            pooled.append((sd, df))
            print(f"  {k}: within-arm SD of log actions = {sd if sd is None else round(sd, 3)} (df={df})")
        num = sum(sd * sd * df for sd, df in pooled if sd is not None)
        den = sum(df for sd, df in pooled if sd is not None)
        if den:
            sd = math.sqrt(num / den)
            rule = "add a third pass to every arm if compute allows" if sd > 0.45 else "2 passes are enough"
            print(f"pooled within-arm SD = {sd:.3f} -> {rule} (rule: > 0.45)")
        return

    report = {}
    if "game-g1" in arms and "levelup-g1" in arms:
        c1 = contrast(arms, "game-g1", "levelup-g1", labels, n_levels, rng)
        print("\nPrimary contrast R at G=1 (game-g1 - levelup-g1); efficiency is a log action ratio, <0 is fewer actions")
        print(f"  P1  S levels efficiency: {fmt(c1['eff_S'])}  ->  {c1['P1']}")
        print(f"  P2  N levels efficiency: {fmt(c1['eff_N'])}  ->  {c1['P2']}")
        print(f"      V levels efficiency (descriptive): {fmt(c1['eff_V'])}")
        print(f"  S1  completion S: {fmt(c1['comp_S'])} -> {c1['S1_S']};  N: {fmt(c1['comp_N'])} -> {c1['S1_N']}")
        print(f"  S2  game score: {fmt(c1['S2_score'])} -> {c1['S2']}")
        s3 = c1["S3"]
        if s3["estimate"] is not None:
            print(f"  S3  position slope on S levels: {s3['estimate']:+.3f} [{s3['lo90']:+.3f}, {s3['hi90']:+.3f}] -> {s3['verdict']}")
        else:
            print(f"  S3  position slope: {s3['verdict']}")
        t = c1["S4_tokens"]
        ratio = f"{t['ratio']:.3f}" if t["ratio"] is not None else "n/a"
        print(f"  S4  tokens per game {t['mean_a']:.0f} vs {t['mean_b']:.0f} (ratio {ratio})"
              + ("  -> FLAG: repeating P1/P2 per 1k tokens" if c1["S4_flag"] else ""))
        if c1["S4_flag"]:
            adj = contrast(arms, "game-g1", "levelup-g1", labels, n_levels, rng, tokens_adjusted=True)
            print(f"      per-1k-token P1: {fmt(adj['eff_S'])} -> {adj['P1']};  P2: {fmt(adj['eff_N'])} -> {adj['P2']}")
            c1["token_adjusted"] = {k: adj[k] for k in ("eff_S", "eff_N", "P1", "P2")}
        if c1["dropped_levels"]:
            print(f"  dropped completed levels with missing/zero actions: {len(c1['dropped_levels'])}")
        report["R_at_G1"] = c1
        if "game-g0" in arms and "levelup-g0" in arms:
            c0 = contrast(arms, "game-g0", "levelup-g0", labels, n_levels, rng)
            s5 = guidance_interaction(c1, c0, labels, rng)
            print("\nS5 guidance (full 2x2)")
            print(f"  N: extra harm without guidance {fmt(s5['N'])} -> {s5['N_verdict']}")
            print(f"  S: benefit kept with guidance  {fmt(s5['S'])} -> {s5['S_verdict']}")
            report["R_at_G0"], report["S5"] = c0, s5
    else:
        print("primary arms game-g1 and levelup-g1 not both present; nothing to test")

    if args.json:
        for c in report.values():
            if isinstance(c, dict):
                c.pop("_cells", None)
        json.dump(report, open(args.json, "w"), indent=1, default=str)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
