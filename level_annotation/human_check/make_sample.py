"""Pick whole games for the blind human S/V/N check, by a fixed seed, until >= 40 labelled levels (level >= 2).
Writes sample_games.txt and a blank labels_human.csv (no AI labels). Reads only game/level columns of levels.csv.
Usage: python3 -I make_sample.py ../levels.csv ."""
import csv, os, random, sys
SEED, TARGET = 20261026, 40
rows = list(csv.DictReader(open(sys.argv[1])))
out = sys.argv[2]
levels = {}
for r in rows:
    if int(r["level"]) >= 2:
        levels.setdefault(r["game"], []).append(int(r["level"]))
games = sorted(levels)
random.Random(SEED).shuffle(games)
picked, n = [], 0
for g in games:
    if n >= TARGET: break
    picked.append(g); n += len(levels[g])
with open(os.path.join(out, "sample_games.txt"), "w") as f:
    f.write(f"# seed {SEED}, target {TARGET} levels; {len(picked)} games, {n} levels\n")
    f.write("\n".join(picked) + "\n")
blank = os.path.join(out, "labels_human.csv")
if os.path.exists(blank): sys.exit(f"{blank} exists; not overwriting")
with open(blank, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["game", "level", "label", "note"])
    for g in picked:
        for lv in sorted(levels[g]): w.writerow([g, lv, "", ""])
print(len(picked), "games,", n, "levels:", " ".join(picked))
