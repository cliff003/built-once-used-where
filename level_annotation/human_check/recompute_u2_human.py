#!/usr/bin/env python3
"""U2 on the 7 sample games with one annotator's labels: the second report line of PREREGISTRATION.md section 7b.
Estimate and interval only, no verdict, because seven games are below the 8-game floor.

Written 2026-11-05 by the paper session 466362ea before any human label existed. Not a frozen file. It changes no
frozen file and no sealed output, and it does not rerun the agent: the sealed R-06 run directory is only read.
Public copy (2026-11-07): RUN points at runs/arc3-paper-v1cfg-v1 in this repository instead of the project's own run folder;
nothing else differs from the copy that produced the paper's numbers.

Steps:
  1. Rebuild the R-06 unit directory in a temp folder with the frozen prepare_units.py.
  2. Write a temp levels file: the rows of the frozen levels.csv for the sample games, with the label column
     replaced by the given labels on levels >= 2. analyze_reuse.py skips every game not in that file.
  3. Run the frozen analyze_reuse.py on the units and that file, and print U2 only.

Usage:
  python3 -I recompute_u2_human.py --check
      Run the frozen analysis on the full frozen levels.csv and byte-compare its JSON with the sealed
      results/r06_v1cfg_v1/analyze_reuse.json. Prints only whether they match, no numbers.
  python3 -I recompute_u2_human.py <labels.csv> [--json out.json]
      <labels.csv> needs columns game, level, label and all 44 sample levels in S/V/N. Passing ../manual_labels.csv
      gives the AI labels on the same 7 games; that comparison is descriptive and is not part of section 7b.
"""
import csv
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PT = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(PT, "runs", "arc3-paper-v1cfg-v1")
SEALED = os.path.join(PT, "results", "r06_v1cfg_v1")
LEVELS = os.path.join(PT, "level_annotation", "levels.csv")
PREPARE = os.path.join(PT, "analysis", "prepare_units.py")
ANALYZE = os.path.join(PT, "analysis", "analyze_reuse.py")


def run_quiet(cmd):
    """Run a frozen script without letting its statistics reach this script's output."""
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        sys.exit(f"{os.path.basename(cmd[3])} failed with exit {p.returncode}: {p.stderr[-400:]}")


def build_units(tmp):
    """The same inputs as the R-06 analysis: benchmark.json decompressed, transcripts linked, the sealed budget."""
    manifest = json.load(open(os.path.join(SEALED, "units_manifest.json")))
    budgets = {u["budget_s"] for u in manifest["units"]}
    assert len(budgets) == 1, budgets
    run = os.path.join(tmp, "run")
    os.makedirs(run)
    with gzip.open(os.path.join(RUN, "benchmark.json.gz"), "rb") as fi, open(os.path.join(run, "benchmark.json"), "wb") as fo:
        shutil.copyfileobj(fi, fo)
    os.symlink(os.path.join(RUN, "transcripts"), os.path.join(run, "transcripts"))
    units = os.path.join(tmp, "units")
    budget = budgets.pop()
    budget = int(budget) if float(budget).is_integer() else budget
    run_quiet([sys.executable, "-I", "-B", PREPARE, units, "--levels", LEVELS, "--run", f"{run}:{budget}"])
    return units


def check():
    tmp = tempfile.mkdtemp(prefix="u2_check_")
    try:
        units = build_units(tmp)
        out = os.path.join(tmp, "report.json")
        run_quiet([sys.executable, "-I", "-B", ANALYZE, units, LEVELS, "--json", out])
        same = open(out, "rb").read() == open(os.path.join(SEALED, "analyze_reuse.json"), "rb").read()
        print("frozen analysis on rebuilt units vs sealed analyze_reuse.json:", "identical" if same else "DIFFERENT")
        return 0 if same else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def recompute(labels_path, json_out=None):
    games = [g.strip() for g in open(os.path.join(HERE, "sample_games.txt")) if g.strip() and not g.startswith("#")]
    given = {(r["game"], int(r["level"])): r["label"].strip().upper() for r in csv.DictReader(open(labels_path, encoding="utf-8"))}
    rows = [r for r in csv.DictReader(open(LEVELS)) if r["game"] in games]
    need = [(r["game"], int(r["level"])) for r in rows if int(r["level"]) >= 2]
    assert len(need) == 44, len(need)
    bad = [k for k in need if given.get(k) not in ("S", "V", "N")]
    if bad:
        sys.exit(f"{labels_path}: {len(bad)} of 44 sample levels have no S/V/N label, e.g. {bad[:3]}")
    tmp = tempfile.mkdtemp(prefix="u2_human_")
    try:
        units = build_units(tmp)
        lv = os.path.join(tmp, "levels_sample.csv")
        with open(lv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            for r in rows:
                k = (r["game"], int(r["level"]))
                w.writerow({**r, "label": given[k] if int(r["level"]) >= 2 else r["label"]})
        out = os.path.join(tmp, "report.json")
        run_quiet([sys.executable, "-I", "-B", ANALYZE, units, lv, "--json", out])
        u2 = json.load(open(out))["U2"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sha = hashlib.sha256(open(labels_path, "rb").read()).hexdigest()
    result = {"labels_file": os.path.basename(labels_path), "labels_sha256": sha,
              **{k: u2[k] for k in ("estimate", "lo90", "hi90", "games", "S_levels", "N_levels", "uptake_S", "uptake_N")}}
    fmt = lambda x: "none" if x is None else f"{x:+.3f}"
    print(f"{result['labels_file']} (sha256 {sha[:12]}): U2 uptake S - N on {u2['games']} games = {fmt(u2['estimate'])} "
          f"[{fmt(u2['lo90'])}, {fmt(u2['hi90'])}]; opportunity levels S={u2['S_levels']} N={u2['N_levels']}; "
          f"uptake S {fmt(u2['uptake_S'])} N {fmt(u2['uptake_N'])}. No verdict (section 7b).")
    if json_out:
        with open(json_out, "w") as f:
            json.dump(result, f, indent=1)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--check"]:
        sys.exit(check())
    if len(args) == 1:
        sys.exit(recompute(args[0]))
    if len(args) == 3 and args[1] == "--json":
        sys.exit(recompute(args[0], args[2]))
    sys.exit(__doc__)
