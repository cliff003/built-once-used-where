"""Pre-registered reuse analysis (PREREGISTRATION.md, Amendment 3).

Parses Duck-harness transcripts of the submitted configuration and reports
U1 (share of kept functions ever reused on a later level), U2 (uptake on S
minus N opportunity levels), the descriptive measures, and the Amendment 2
gate counts.

Usage:
  python3 -I analyze_reuse.py <transcript dir> <levels.csv> [--json report.json]

Every <game_id>_p<k>.txt file below <transcript dir> is one (game, pass) unit.
Transcript markers (Kaggle commit runs of the Franzen harness):
  'Current state: step N, level L.'   at the top of each turn's user prompt
  'Your retained functions from earlier Python calls in this game: f(a), g(). These are ...'
  '<parameter=code>' ... '</parameter>'  one python snippet
  '-> RUN COMPLETE' (single action) or a line starting 'WIN lvl N' (after a batch): all levels cleared
"""

import argparse
import ast
import csv
import glob
import json
import os
import random
import re
import statistics as st
from collections import defaultdict

B = 10_000
SEED = 20261025
LO, HI = 0.05, 0.95
RARE, COMMON, SELECTIVITY_MARGIN = 0.25, 0.50, 0.10
MIN_GAMES, MIN_LEVELS = 8, 15
GATE_GAMES = ("ft09", "sp80", "ls20", "vc33")

EVENTS = re.compile(
    r"<parameter=code>\n(?P<code>.*?)</parameter>"
    r"|Current state: step (?P<step>\d+), level (?P<level>\d+)\."
    r"|Your retained functions from earlier Python calls in this game: (?P<kept>.*?)\. These are"
    r"|(?P<done>-> RUN COMPLETE|^WIN lvl \d+)",
    re.S | re.M,
)
FILE_NAME = re.compile(r"(?P<game_id>[a-z0-9]+-[0-9a-f]+)_p(?P<k>\d+)\.txt$")


def defs_and_calls(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None, None
    defs = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    return defs, calls


def parse_transcript(text):
    level, reached, done = 1, 1, False
    defined_at = {}
    kept_ever = set()
    kept_at_start = {}             # level -> set of kept names before its first snippet
    snippet_seen = set()           # levels that already had a snippet
    redefined = defaultdict(set)   # level -> kept-at-start names redefined at that level
    carried = defaultdict(set)     # level -> names with a carried call at that level
    first_step = {}
    snippets = syntax_errors = 0
    for m in EVENTS.finditer(text):
        if m.group("level") is not None:
            level = int(m.group("level"))
            reached = max(reached, level)
            first_step.setdefault(level, int(m.group("step")))
        elif m.group("kept") is not None:
            names = set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\(", m.group("kept")))
            kept_ever |= names
            if level not in snippet_seen and level not in kept_at_start:
                kept_at_start[level] = names
        elif m.group("done") is not None:
            done = True
        else:
            snippet_seen.add(level)
            snippets += 1
            defs, calls = defs_and_calls(m.group("code"))
            if defs is None:
                syntax_errors += 1
                continue
            start = kept_at_start.get(level, set())
            for fn in defs:
                defined_at.setdefault(fn, level)
                if fn in start:
                    redefined[level].add(fn)
            for fn in calls - defs:
                if fn in start and fn not in redefined[level]:
                    carried[level].add(fn)
    return {
        "reached": reached, "run_complete": done, "defined_at": defined_at, "kept_ever": kept_ever,
        "kept_at_start": kept_at_start, "redefined": redefined, "carried": carried,
        "first_step": first_step, "snippets": snippets, "syntax_errors": syntax_errors,
    }


def load(transcript_dir, labels, n_levels):
    units = []
    for path in sorted(glob.glob(os.path.join(transcript_dir, "**", "*.txt"), recursive=True)):
        m = FILE_NAME.search(os.path.basename(path))
        if not m:
            continue
        game = m.group("game_id").split("-")[0]
        if game not in n_levels:
            continue
        p = parse_transcript(open(path, encoding="utf-8", errors="replace").read())
        n = n_levels[game]
        completed = n if p["run_complete"] else min(p["reached"] - 1, n)
        reused = set().union(*p["carried"].values()) if p["carried"] else set()
        eligible = {fn for fn in p["kept_ever"] if fn in p["defined_at"] and p["defined_at"][fn] < p["reached"]}
        levels = []
        for lv in range(2, min(p["reached"], n) + 1):
            start = p["kept_at_start"].get(lv, set())
            nxt = p["first_step"].get(lv + 1)
            approx = (nxt - p["first_step"][lv]) if (nxt is not None and lv in p["first_step"] and lv <= completed) else None
            levels.append({"level": lv, "label": labels.get((game, lv)), "kept": len(start),
                           "uptake": bool(p["carried"].get(lv)), "revised": bool(p["redefined"].get(lv)),
                           "approx_actions": approx})
        units.append({"path": os.path.relpath(path, transcript_dir), "game": game, "n_levels": n, "completed": completed,
                      "eligible": len(eligible), "reused": len(eligible & reused), "kept_ever": len(p["kept_ever"]),
                      "defined": len(p["defined_at"]), "carried_fns": len(reused), "levels": levels,
                      "snippets": p["snippets"], "syntax_errors": p["syntax_errors"]})
    return units


def boot(games, stat, rng):
    """Percentile interval of stat(sample of games) with games resampled as clusters."""
    if not games:
        return None, None, None
    est = stat(games)
    sims = []
    for _ in range(B):
        s = stat([rng.choice(games) for _ in games])
        if s is not None:
            sims.append(s)
    if not sims or est is None:
        return est, None, None
    sims.sort()
    return est, sims[int(LO * len(sims))], sims[int(HI * len(sims)) - 1]


def u1(units, rng):
    per_game = defaultdict(lambda: [0, 0])
    for u in units:
        per_game[u["game"]][0] += u["reused"]
        per_game[u["game"]][1] += u["eligible"]
    shares = {g: r / e for g, (r, e) in per_game.items() if e > 0}
    games = sorted(shares)
    est, lo, hi = boot(games, lambda gs: st.mean(shares[g] for g in gs), rng)
    if len(games) < MIN_GAMES:
        verdict = "insufficient data"
    elif hi < RARE:
        verdict = "rarely reused"
    elif lo > COMMON:
        verdict = "commonly reused"
    else:
        verdict = "intermediate"
    return {"estimate": est, "lo90": lo, "hi90": hi, "games": len(games), "verdict": verdict}


def opportunity_levels(units):
    by_game = defaultdict(list)
    for u in units:
        for lv in u["levels"]:
            if lv["kept"] > 0:
                by_game[u["game"]].append(lv)
    return by_game


def rate(levels, label):
    xs = [lv["uptake"] for lv in levels if lv["label"] == label]
    return (sum(xs) / len(xs)) if xs else None


def u2(units, rng):
    by_game = opportunity_levels(units)
    games = sorted(by_game)

    def diff(gs):
        pool = [lv for g in gs for lv in by_game[g]]
        s, n = rate(pool, "S"), rate(pool, "N")
        return None if s is None or n is None else s - n

    est, lo, hi = boot(games, diff, rng)
    pool = [lv for g in games for lv in by_game[g]]
    n_s = sum(1 for lv in pool if lv["label"] == "S")
    n_n = sum(1 for lv in pool if lv["label"] == "N")
    if len(games) < MIN_GAMES or n_s < MIN_LEVELS or n_n < MIN_LEVELS or est is None:
        verdict = "insufficient data"
    elif hi < 0:
        verdict = "reverse"
    elif lo > 0:
        verdict = "selective"
    elif hi < SELECTIVITY_MARGIN:
        verdict = "no meaningful selectivity"
    else:
        verdict = "inconclusive"
    return {"estimate": est, "lo90": lo, "hi90": hi, "games": len(games), "S_levels": n_s, "N_levels": n_n,
            "uptake_S": rate(pool, "S"), "uptake_N": rate(pool, "N"), "verdict": verdict}


def descriptive(units):
    all_levels = [lv for u in units for lv in u["levels"]]
    opp = [lv for lv in all_levels if lv["kept"] > 0]
    out = {"levels_reached_2plus": len(all_levels), "opportunity_rate": (len(opp) / len(all_levels)) if all_levels else None,
           "uptake_V": rate(opp, "V"), "revised_share": (sum(lv["revised"] for lv in opp) / len(opp)) if opp else None}
    pos = defaultdict(list)
    for u in units:
        for lv in u["levels"]:
            if lv["kept"] > 0:
                key = ("levels 2-3" if lv["level"] <= 3
                       else "last two" if lv["level"] >= u["n_levels"] - 1 else "middle")
                pos[key].append(lv["uptake"])
    out["uptake_by_position"] = {k: (sum(v) / len(v), len(v)) for k, v in pos.items() if v}
    s_up = [lv["approx_actions"] for lv in opp if lv["label"] == "S" and lv["uptake"] and lv["approx_actions"]]
    s_no = [lv["approx_actions"] for lv in opp if lv["label"] == "S" and not lv["uptake"] and lv["approx_actions"]]
    out["S_approx_actions_median"] = {"uptake": st.median(s_up) if s_up else None, "no_uptake": st.median(s_no) if s_no else None,
                                      "n_uptake": len(s_up), "n_no_uptake": len(s_no)}
    return out


def gate(units):
    g = {k: 0 for k in ("G1_kept", "G2_carried_fns", "G3_completed")}
    for u in units:
        if u["game"] in GATE_GAMES:
            g["G1_kept"] += u["kept_ever"]
            g["G2_carried_fns"] += u["carried_fns"]
            g["G3_completed"] += u["completed"]
    g["passes_gate"] = g["G1_kept"] >= 3 and g["G2_carried_fns"] >= 1 and g["G3_completed"] >= 2
    return g


def fmt(r):
    if r["estimate"] is None:
        return f"no data (games={r['games']})"
    if r["lo90"] is None:
        return f"{r['estimate']:+.3f} [no interval]  games={r['games']}"
    return f"{r['estimate']:+.3f} [{r['lo90']:+.3f}, {r['hi90']:+.3f}]  games={r['games']}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript_dir")
    ap.add_argument("levels_csv")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    labels, n_levels = {}, {}
    for r in csv.DictReader(open(args.levels_csv)):
        labels[(r["game"], int(r["level"]))] = r["label"]
        n_levels[r["game"]] = int(r["n_levels"])
    units = load(args.transcript_dir, labels, n_levels)
    games = sorted({u["game"] for u in units})
    passes = defaultdict(int)
    for u in units:
        passes[u["game"]] += 1
    print(f"transcripts: {len(units)} over {len(games)} games; passes per game: min {min(passes.values(), default=0)}, "
          f"max {max(passes.values(), default=0)}")
    print(f"snippets {sum(u['snippets'] for u in units)}, syntax errors {sum(u['syntax_errors'] for u in units)}, "
          f"functions defined {sum(u['defined'] for u in units)}, kept {sum(u['kept_ever'] for u in units)}")
    rng = random.Random(SEED)
    r1, r2 = u1(units, rng), u2(units, rng)
    print(f"U1 reuse share of kept functions: {fmt(r1)} -> {r1['verdict']}")
    print(f"U2 uptake S - N on opportunity levels: {fmt(r2)}  (S {r2['uptake_S']}, N {r2['uptake_N']}; "
          f"levels S={r2['S_levels']} N={r2['N_levels']}) -> {r2['verdict']}")
    d = descriptive(units)
    print("descriptive:", json.dumps(d, default=str))
    g = gate(units)
    print("Amendment 2 gate on", ",".join(GATE_GAMES), ":", g)
    if args.json:
        json.dump({"U1": r1, "U2": r2, "descriptive": d, "gate": g,
                   "units": [{k: v for k, v in u.items() if k != "levels"} for u in units]},
                  open(args.json, "w"), indent=1, default=str)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
