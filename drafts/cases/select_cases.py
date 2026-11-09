"""Pick the three illustrative cases of Section 7.1 by a fixed rule, before reading them.

Rule (written before any case was read): shuffle the 50 R-06 game-runs with
random.Random(20261101); for each case type, take the first game-run in that order
that has a qualifying level, and in it the lowest qualifying level. Opportunity
levels and the flags come from the frozen parser (analysis/analyze_reuse.py,
parse_transcript), imported unchanged.
  used:      S level, kept > 0, a carried call, no kept function redefined
  not used:  S level, kept > 0, no carried call, no kept function redefined
  rewritten: N level, kept > 0, a kept function redefined at that level
Run from paper-track/: python3 -I drafts/cases/select_cases.py <R-06 transcripts dir>
Reads the sealed .txt.gz files without changing them.
"""
import csv, gzip, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "analysis"))
from analyze_reuse import FILE_NAME, parse_transcript  # noqa: E402

TYPES = {
    "used": lambda f: f["label"] == "S" and f["kept"] and f["uptake"] and not f["revised"],
    "not used": lambda f: f["label"] == "S" and f["kept"] and not f["uptake"] and not f["revised"],
    "rewritten": lambda f: f["label"] == "N" and f["kept"] and f["revised"],
}


def main(tdir):
    labels, n_levels = {}, {}
    for r in csv.DictReader(open(os.path.join(ROOT, "level_annotation", "levels.csv"), encoding="utf-8")):
        labels[(r["game"], int(r["level"]))] = r["label"]
        n_levels[r["game"]] = int(r["n_levels"])
    runs = sorted(f for f in os.listdir(tdir) if f.endswith(".txt.gz"))
    assert len(runs) == 50, len(runs)
    order = runs[:]
    random.Random(20261101).shuffle(order)
    picked = {}
    for i, name in enumerate(order):
        if len(picked) == len(TYPES):
            break
        game = FILE_NAME.search(name[:-3]).group("game_id").split("-")[0]
        p = parse_transcript(gzip.open(os.path.join(tdir, name), "rt", encoding="utf-8", errors="replace").read())
        for lv in range(2, min(p["reached"], n_levels[game]) + 1):
            start = p["kept_at_start"].get(lv, set())
            f = {"label": labels.get((game, lv)), "kept": len(start), "uptake": bool(p["carried"].get(lv)),
                 "revised": bool(p["redefined"].get(lv))}
            for t, ok in TYPES.items():
                if t not in picked and ok(f):
                    picked[t] = {"order_position": i, "run": name, "game": game, "level": lv, "n_levels": n_levels[game],
                                 **f, "kept_names": sorted(start), "carried": sorted(p["carried"].get(lv, ())),
                                 "redefined": sorted(p["redefined"].get(lv, ())),
                                 "first_step": p["first_step"].get(lv), "next_level_first_step": p["first_step"].get(lv + 1),
                                 "reached": p["reached"], "run_complete": p["run_complete"]}
    print(json.dumps({"order_first_10": order[:10], "picked": picked}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
