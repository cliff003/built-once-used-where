"""Amendment 2 gate counts (G1-G3) for one smoke run. Not part of the frozen set.

Loads the frozen analyze_reuse.py from this directory unchanged and calls only its
load() and gate(); prints no U1/U2 and no descriptive reuse measures. Written for
RUN_REGISTER.md R-07 (Muse A0) before any Muse game data existed.

Usage:
  python3 -I gate_only.py <transcript dir> <levels.csv> [--json report.json]

Format check, applied before any verdict:
  - every gate game has units, all with the same number of passes, and every unit has
    'Current state: step' lines; otherwise all three conditions are undetermined;
  - parsed snippets are at least 90% of the '[TOOL CALL: python]' sections, in total;
    otherwise G2 is undetermined (G1 and G3 do not depend on snippets). Calls the model
    wrote without a code parameter are not snippets: 2 of 1,504 calls on the gate games
    of the parent-configuration data (Amendment 4 section 7).
"""

import argparse
import csv
import importlib.util
import json
import os

spec = importlib.util.spec_from_file_location(
    "analyze_reuse", os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyze_reuse.py"))
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)


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
    units = [u for u in ar.load(args.transcript_dir, labels, n_levels) if u["game"] in ar.GATE_GAMES]
    rows = []
    for u in units:
        text = open(os.path.join(args.transcript_dir, u["path"]), encoding="utf-8", errors="replace").read()
        rows.append({"path": u["path"], "game": u["game"], "snippets": u["snippets"],
                     "python_calls": text.count("[TOOL CALL: python]"),
                     "state_lines": text.count("Current state: step ")})
        print(rows[-1])
    passes = [sum(u["game"] == game for u in units) for game in ar.GATE_GAMES]
    units_ok = min(passes) > 0 and len(set(passes)) == 1 and all(r["state_lines"] > 0 for r in rows)
    snippets_ok = units_ok and sum(r["snippets"] for r in rows) >= 0.9 * sum(r["python_calls"] for r in rows)
    g = ar.gate(units)
    verdict = {
        "G1": ("pass" if g["G1_kept"] >= 3 else "fail") if units_ok else "undetermined",
        "G2": ("pass" if g["G2_carried_fns"] >= 1 else "fail") if snippets_ok else "undetermined",
        "G3": ("pass" if g["G3_completed"] >= 2 else "fail") if units_ok else "undetermined",
    }
    print("Amendment 2 gate on", ",".join(ar.GATE_GAMES), ":", g)
    print("format: units_ok", units_ok, "snippets_ok", snippets_ok, "->", verdict)
    if args.json:
        json.dump({"gate": g, "verdict": verdict, "units_ok": units_ok, "snippets_ok": snippets_ok, "format": rows},
                  open(args.json, "w"), indent=1)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
