"""Validity and cut rules of Amendment 4 section 6, applied to the Kaggle sessions of one data source before the frozen analysis.

DRAFT: frozen together with Amendment 4.

Reads only summary fields of each session's benchmark.json (game_id, state, final_generated_tokens,
final_wallclock_seconds); it never opens a transcript. Within a session, the k-th game_run with a given
game_id is that session's pass k: taaf/benchmark.py appends game_runs pass by pass, and the solver names
transcripts <game_id>_p<pass>.txt. Every pass is checked against the expected games (the games of
levels.csv, i.e. the 25 public games): an expected game with no game_run counts as missing, and a game
outside the expected set is an error.
  invalid  final_generated_tokens == 0 (no model output; covers zero turns)
  cut      state != "won" and final_wallclock_seconds < budget_s - 300
  missing  no game_run, or no transcript file, for an expected game
Passes are numbered in session order: the sessions are given in one call, and each session's passes
follow those of the sessions before it. A session given with a pass index K is a rerun: its passes
replace passes K, K+1, ... A rerun may replace only a pass that is incomplete, and each pass at most once.
A pass is complete when at most 20% of the expected games are invalid, cut or missing in it. The
transcripts of the remaining ("ok") game-runs of complete passes are linked, or decompressed if
gzipped, into <out_dir> as <game_id>_p<pass>.txt; an existing file there is an error.
<out_dir> is then the transcript directory for analyze_reuse.py and analyze_reuse_clearing.py.

Usage: python3 -I prepare_units.py <out_dir> --levels levels.csv --run RUN_DIR:BUDGET_S[:K] [--run ...] [--json manifest.json]
  BUDGET_S = round(532 * 60 * N / 110), N = game-runs played concurrently in that session
  (50 -> 14509; 25 -> 7255; 100 -> 29018)
"""

import argparse
import csv
import gzip
import json
import os
import shutil
import sys
from collections import defaultdict

CUT_MARGIN_S, MAX_BAD_SHARE = 300, 0.20


def session_passes(run_dir, budget_s, expected):
    """{in-session pass index: units}, one unit per expected game, with status."""
    bm = json.load(open(os.path.join(run_dir, "benchmark.json")))
    tdir = os.path.join(run_dir, "transcripts")
    seen, passes = defaultdict(int), defaultdict(dict)
    for r in bm["game_runs"]:
        game = r["game_id"].split("-")[0]
        if game not in expected:
            sys.exit(f"{run_dir}: game {r['game_id']} is not in the expected set")
        k = seen[r["game_id"]]
        seen[r["game_id"]] += 1
        stem = f"{r['game_id']}_p{k}"
        src = next((os.path.join(tdir, stem + s) for s in (".txt", ".txt.gz") if os.path.exists(os.path.join(tdir, stem + s))), None)
        tokens, wall, state = r.get("final_generated_tokens") or 0, float(r.get("final_wallclock_seconds") or 0.0), r.get("state")
        if src is None:
            status = "missing"
        elif tokens == 0:
            status = "invalid"
        elif state != "won" and wall < budget_s - CUT_MARGIN_S:
            status = "cut"
        else:
            status = "ok"
        passes[k][game] = {"game_id": r["game_id"], "state": state, "tokens": tokens, "wallclock_s": wall,
                           "status": status, "src": src, "run_dir": run_dir, "budget_s": budget_s}
    out = {}
    for k, by_game in passes.items():
        units = []
        for game in sorted(expected):
            units.append(by_game.get(game) or {"game_id": game, "state": None, "tokens": 0, "wallclock_s": 0.0,
                                               "status": "missing", "src": None, "run_dir": run_dir, "budget_s": budget_s})
        out[k] = units
    return out


def complete(units):
    return bool(units) and sum(u["status"] != "ok" for u in units) / len(units) <= MAX_BAD_SHARE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--levels", required=True, help="levels.csv; its games are the expected set")
    ap.add_argument("--run", action="append", required=True, help="RUN_DIR:BUDGET_S[:K], in session order")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    expected = {r["game"] for r in csv.DictReader(open(args.levels))}
    passes, reruns, next_pass = {}, defaultdict(int), 0
    for spec in args.run:
        parts = spec.rsplit(":", 2) if spec.count(":") >= 2 else spec.rsplit(":", 1)
        run_dir, budget_s = parts[0], float(parts[1])
        start = int(parts[2]) if len(parts) == 3 else None
        sess = session_passes(run_dir, budget_s, expected)
        n_sess = 1 + max(sess, default=-1)
        if start is None:
            for k in range(n_sess):
                passes[next_pass + k] = sess.get(k, [])
            next_pass += n_sess
            continue
        for k in range(n_sess):
            g = start + k
            if g not in passes:
                sys.exit(f"{spec}: a rerun may only replace passes already given (0..{next_pass - 1})")
            if complete(passes[g]):
                sys.exit(f"{spec}: pass {g} is complete; only an incomplete pass may be rerun")
            if reruns[g] >= 1:
                sys.exit(f"{spec}: pass {g} was already rerun once")
            reruns[g] += 1
            passes[g] = sess.get(k, [])
    done = {k: complete(us) for k, us in passes.items()}
    os.makedirs(args.out_dir, exist_ok=True)
    included = 0
    for k, us in sorted(passes.items()):
        for u in us:
            u["stem"] = f"{u['game_id']}_p{k}"
            u["included"] = done[k] and u["status"] == "ok"
            if not u["included"]:
                continue
            dst = os.path.join(args.out_dir, u["stem"] + ".txt")
            if os.path.lexists(dst):
                sys.exit(f"{dst} exists; give every session in one call and use a fresh out_dir")
            if u["src"].endswith(".gz"):
                with gzip.open(u["src"], "rb") as fi, open(dst, "wb") as fo:
                    shutil.copyfileobj(fi, fo)
            else:
                os.symlink(os.path.abspath(u["src"]), dst)
            included += 1
    by_pass = {k: {"expected_games": len(us), "not_ok": sum(u["status"] != "ok" for u in us), "complete": done[k],
                   "reruns": reruns[k], "run_dir": us[0]["run_dir"] if us else None} for k, us in sorted(passes.items())}
    all_units = [u for _, us in sorted(passes.items()) for u in us]
    n_complete = sum(done.values())
    print(f"game-runs {len(all_units)}; status counts", {s: sum(u['status'] == s for u in all_units) for s in ("ok", "invalid", "cut", "missing")})
    print("passes:", by_pass)
    print(f"complete passes {n_complete}; included transcripts {included}; "
          f"primary data exist (>= 2 complete passes): {'yes' if n_complete >= 2 else 'no'}")
    if args.json:
        json.dump({"cut_margin_s": CUT_MARGIN_S, "expected_games": sorted(expected), "passes": by_pass,
                   "units": [{k: v for k, v in u.items() if k != "src"} for u in all_units]}, open(args.json, "w"), indent=1)


if __name__ == "__main__":
    main()
